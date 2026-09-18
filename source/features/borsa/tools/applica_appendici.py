#!/usr/bin/env python3
"""applica_appendici.py — SGP-1.2-BORSA-GEN-09.

Innesta nel NARC `a/0/1/2` le 6 appendici di bytecode che, quando il gancio
ARM9 del comando 125 ha dovuto scartare l'oggetto (il flag di
`appendici_def.VAR_SCARTATO` vale 1),
mostrano il messaggio 199#10 «La Borsa è piena! Non c'è posto per X…» subito
dopo l'ultimo riquadro del dono/della raccolta e prima che il flusso finisca.

ORDINE OBBLIGATORIO DELLA CATENA (su COPIE, mai sulla sorgente):
    1. `source/features/borsa/tools/premi_disfa.py` -> toglie REWARD-01, `a/0/1/2`
       scende da 442 616 a 442 264 B e libera i byte che servono qui;
    2. `source/features/borsa/tools/applica_199.py` -> aggiunge il messaggio 199#10
       in `a/0/2/7` (archivio diverso, nessuna interferenza);
    3. QUESTO programma.
Il passo 2 e il passo 3 sono indipendenti fra loro; il passo 1 e' un prerequisito
di questo (senza, l'archivio non ci sta in luogo e la ROM crescerebbe).

CRESCITA ROM: ZERO. Le appendici stanno dentro l'estensione che `a/0/1/2` aveva
nella 1.2.1 rilasciata (442 616 B) — cioe' dentro i 352 B liberati da premi_disfa
— e l'archivio viene riscritto IN LUOGO. Nessun byte oltre la nuova fine FAT
viene modificato.

IDEMPOTENZA: una seconda esecuzione sulla propria uscita risponde
`GIA_APPLICATA` e non scrive nulla.

SOLA LETTURA salvo `--out`: non sovrascrive mai l'ingresso.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO = QUI.parents[3]
sys.path.insert(0, str(QUI))
sys.path.insert(0, str(REPO / "source" / "translation"))

import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402
from rom_container import append_files  # noqa: E402

import appendici_def as D  # noqa: E402

GOTO = 22


class Rifiuto(Exception):
    """Nessun byte viene scritto quando questo vola."""


class GiaApplicata(Rifiuto):
    pass


def sha(b) -> str:
    return hashlib.sha256(bytes(b)).hexdigest()


# ---------------------------------------------------------------------------
def costruisci_membro(asm: D.Assemblatore, membro: int, dati: bytes):
    """Torna (nuovi_byte, verbale). Non tocca `dati`."""
    spec = D.FLUSSI[membro]
    out = bytearray(dati)
    base = len(out)
    verbale = {"membro": membro, "nota": spec["nota"], "byte_prima": len(dati),
               "appendici": [], "innesti": [], "ritocchi": []}

    # 1. le appendici, accodate in fondo al membro (le etichette sono globali
    #    fra le appendici dello stesso membro: qui non servono, ma non nuoce)
    etichette = {}
    for nome, programma in spec["appendici"]:
        inizio = len(out)
        blob = asm.assembla(programma, inizio)
        out += blob
        etichette[nome] = inizio
        # le posizioni delle etichette interne: stessa prima passata
        # dell'assemblatore, rifatta qui perche' servono agli innesti
        off = inizio
        for voce in programma:
            if voce[0] == "label":
                etichette[str(voce[1])] = off
            else:
                off += asm.lunghezza(voce[0])
        verbale["appendici"].append({"nome": nome, "offset": inizio,
                                     "byte": len(blob), "sha256": sha(blob)})

    # 2. gli innesti: GoTo scritto IN LUOGO sopra una finestra verificata
    for off, pre_hex, label in spec["innesti"]:
        pre = bytes.fromhex(pre_hex)
        letto = bytes(dati[off:off + len(pre)])
        if letto != pre:
            raise Rifiuto("membro %d @%d: preimmagine della finestra diversa "
                          "(letti %s, attesi %s)" % (membro, off, letto.hex(), pre_hex))
        goto = asm.goto(D.Assoluto(etichette[label]), off)
        if len(goto) > len(pre):
            raise Rifiuto("membro %d @%d: il GoTo (%d B) non entra nella finestra (%d B)"
                          % (membro, off, len(goto), len(pre)))
        out[off:off + len(pre)] = goto + bytes(len(pre) - len(goto))
        verbale["innesti"].append({"offset": off, "finestra_byte": len(pre),
                                   "preimmagine": pre_hex, "verso": label,
                                   "destinazione": etichette[label],
                                   "byte_morti": len(pre) - len(goto)})

    # 3. i ritocchi: solo il campo relativo a 4 byte di un ramo esistente
    for off_ins, idx_arg, pre_hex, label in spec["ritocchi"]:
        op = struct.unpack_from("<H", dati, off_ins)[0]
        larg, tipi = asm.larghezze(op)
        if tipi[idx_arg] not in D.RELATIVE:
            raise Rifiuto("membro %d @%d arg %d: non e' un campo relativo"
                          % (membro, off_ins, idx_arg))
        off_arg = off_ins + 2 + sum(larg[:idx_arg])
        fine_arg = off_arg + larg[idx_arg]
        letto = bytes(dati[off_arg:fine_arg])
        if letto != bytes.fromhex(pre_hex):
            raise Rifiuto("membro %d @%d: preimmagine del ramo diversa "
                          "(letti %s, attesi %s)" % (membro, off_arg, letto.hex(), pre_hex))
        vecchia_dest = int.from_bytes(letto, "little") + fine_arg
        nuova = (etichette[label] - fine_arg) & 0xFFFFFFFF
        out[off_arg:fine_arg] = nuova.to_bytes(larg[idx_arg], "little")
        verbale["ritocchi"].append({
            "istruzione": off_ins, "comando": asm.nome(op), "campo": off_arg,
            "destinazione_prima": vecchia_dest,
            "destinazione_dopo": etichette[label], "verso": label})

    verbale["byte_dopo"] = len(out)
    verbale["crescita"] = len(out) - len(dati)
    verbale["sha256_prima"] = sha(dati)
    verbale["sha256_dopo"] = sha(out)
    return bytes(out), verbale


# ---------------------------------------------------------------------------
def _regioni_occupate(rom: bytes, escluso: int):
    """Ogni byte di una ROM DS appartiene a una di queste regioni: intestazione,
    ARM9/ARM7 (+ le loro tabelle di overlay), FNT, FAT, banner, o un file della
    FAT. Le elenchiamo tutte per poter dire, senza congetture, fin dove arriva
    lo spazio che segue `a/0/1/2` senza appartenere a nessun altro."""
    reg = [(0, 0x200, "intestazione")]
    for off, nome in ((0x20, "arm9"), (0x30, "arm7")):
        rom_off, _, _, size = struct.unpack_from("<IIII", rom, off)
        if size:
            reg.append((rom_off, rom_off + size, nome))
    for off, nome in ((0x50, "arm9_ovl_tab"), (0x58, "arm7_ovl_tab"),
                      (0x40, "fnt"), (0x48, "fat")):
        a, n = struct.unpack_from("<II", rom, off)
        if n:
            reg.append((a, a + n, nome))
    ban = struct.unpack_from("<I", rom, 0x68)[0]
    if ban:
        reg.append((ban, ban + 0xA00, "banner"))
    fat_start, fat_size = struct.unpack_from("<II", rom, 0x48)
    for i in range(fat_size // 8):
        if i == escluso:
            continue
        a, b = struct.unpack_from("<II", rom, fat_start + i * 8)
        if b > a:
            reg.append((a, b, "file %d" % i))
    return reg


def _limite_in_luogo(rom: bytes, indice: int, inizio: int):
    """Il primo byte dopo `inizio` che appartiene a qualcun altro."""
    lim = len(rom)
    for a, b, _ in _regioni_occupate(rom, indice):
        if b > inizio and a >= inizio:
            lim = min(lim, a)
        elif a < inizio < b:
            raise Rifiuto("l'estensione di %s si sovrappone a [%d,%d)" % (D.ARCHIVIO, a, b))
    return lim


# ---------------------------------------------------------------------------
def scrcmd_da_ambiente() -> Path:
    pret = os.environ.get("SGP_PRET_SOURCE")
    if not pret:
        raise Rifiuto("manca SGP_PRET_SOURCE: serve il checkout pret/pokeheartgold")
    return Path(pret) / "tools/py_scripts/scrcmd.json"


def applica(rom_bytes: bytes, scrcmd_json: Path | None = None):
    scrcmd_json = Path(scrcmd_json) if scrcmd_json is not None else scrcmd_da_ambiente()
    if not scrcmd_json.is_file():
        raise Rifiuto("scrcmd.json assente: %s" % scrcmd_json)
    asm = D.Assemblatore(scrcmd_json)
    rom = ndspy.rom.NintendoDSRom(bytes(rom_bytes))
    try:
        archivio = rom.getFileByName(D.ARCHIVIO)
    except Exception as exc:
        raise Rifiuto("%s assente dalla ROM: %s" % (D.ARCHIVIO, exc)) from exc
    narc = ndspy.narc.NARC(archivio)
    if len(narc.files) != D.N_MEMBRI:
        raise Rifiuto("%s: %d membri, attesi %d" % (D.ARCHIVIO, len(narc.files), D.N_MEMBRI))

    if len(archivio) == D.ARCHIVIO_1_2_1:
        raise Rifiuto("%s e' ancora di %d B: tools/premi_disfa.py non e' "
                      "stato eseguito. Senza i 352 B che libera, le appendici non stanno "
                      "in luogo e la ROM crescerebbe." % (D.ARCHIVIO, len(archivio)))

    # --- preimmagini / idempotenza -----------------------------------------
    stati = {}
    for m, (taglia, firma) in D.PREIMMAGINI.items():
        d = bytes(narc.files[m])
        if (len(d), sha(d)) == (taglia, firma):
            stati[m] = "vergine"
        elif all(struct.unpack_from("<H", d, off)[0] == GOTO
                 for off, _, _ in D.FLUSSI[m]["innesti"]) and len(d) > taglia:
            stati[m] = "applicato"
        else:
            raise Rifiuto("membro %d: preimmagine inattesa (%d B, sha256 %s...). "
                          "Questa ROM non e' la 1.2.1 per cui il pacchetto e' scritto."
                          % (m, len(d), sha(d)[:16]))
    if all(v == "applicato" for v in stati.values()):
        raise GiaApplicata("tutti e cinque i membri portano gia' le appendici")
    if any(v == "applicato" for v in stati.values()):
        raise Rifiuto("stato misto: %r" % stati)

    # --- costruzione --------------------------------------------------------
    verbali = []
    for m in sorted(D.FLUSSI):
        nuovo, verbale = costruisci_membro(asm, m, bytes(narc.files[m]))
        narc.files[m] = nuovo
        verbali.append(verbale)

    nuovo_archivio = narc.save()
    crescita = len(nuovo_archivio) - len(archivio)

    # --- riscrittura in luogo ----------------------------------------------
    src = bytearray(rom_bytes)
    fat_start, fat_size = struct.unpack_from("<II", src, 0x48)
    indice = rom.filenames.idOf(D.ARCHIVIO)
    inizio, fine = struct.unpack_from("<II", src, fat_start + indice * 8)
    if fine - inizio != len(archivio):
        raise Rifiuto("estensione FAT incoerente con il payload letto")
    limite = _limite_in_luogo(bytes(src), indice, inizio)
    tetto = inizio + D.ARCHIVIO_1_2_1   # l'estensione che l'archivio aveva nella 1.2.1
    if tetto > limite:
        raise Rifiuto("l'estensione della 1.2.1 (%d B) sborda su un'altra regione" % D.ARCHIVIO_1_2_1)
    if len(nuovo_archivio) > D.ARCHIVIO_1_2_1:
        raise Rifiuto(
            "le appendici non ci stanno: archivio %d B, tetto %d B (l'estensione che "
            "a/0/1/2 aveva nella 1.2.1). Servono %d B in piu': FERMARSI e riferire."
            % (len(nuovo_archivio), D.ARCHIVIO_1_2_1, len(nuovo_archivio) - D.ARCHIVIO_1_2_1))

    # `append_files` puo' riusare l'estensione solo se i nuovi byte risultano
    # gia' assegnati al file e sono 00/FF. Estendiamo quindi la voce FAT e
    # azzeriamo ESATTAMENTE i `crescita` byte che diventeranno parte del NARC.
    # I `margine_residuo` byte dopo la nuova fine FAT restano fuori dal file e
    # devono rimanere byte-per-byte uguali alla ROM d'ingresso.
    fine_nuova = inizio + len(nuovo_archivio)
    if fine_nuova != fine + crescita:
        raise Rifiuto("calcolo incoerente della nuova fine FAT")
    src[fine:fine_nuova] = bytes(fine_nuova - fine)
    struct.pack_into("<II", src, fat_start + indice * 8, inizio, fine_nuova)

    risultato, changes = append_files(bytes(src), {D.ARCHIVIO: nuovo_archivio},
                                      reuse_existing=True)
    if len(changes) != 1 or not changes[0]["reused_extent"]:
        raise Rifiuto("rom_container non ha riscritto %s in luogo: %r" % (D.ARCHIVIO, changes))
    if len(risultato) != len(rom_bytes):
        raise Rifiuto("la ROM ha cambiato lunghezza: %d -> %d" % (len(rom_bytes), len(risultato)))
    ns, ne = struct.unpack_from("<II", risultato, fat_start + indice * 8)
    if (ns, ne - ns) != (inizio, len(nuovo_archivio)):
        raise Rifiuto("voce FAT finale inattesa: %d..%d" % (ns, ne))

    rapporto = {
        "esito": "APPLICATA",
        "catena": ["premi_disfa (BORSA-GEN-05)", "applica_199 (BORSA-GEN-08)",
                   "applica_appendici (BORSA-GEN-09)"],
        "archivio": {
            "nome": D.ARCHIVIO,
            "prima": {"byte": len(archivio), "sha256": sha(archivio)},
            "dopo": {"byte": len(nuovo_archivio), "sha256": sha(nuovo_archivio)},
            "crescita": crescita,
            "tetto_in_luogo": D.ARCHIVIO_1_2_1,
            "margine_residuo": D.ARCHIVIO_1_2_1 - len(nuovo_archivio),
            "riempimento_oltre_il_tetto_non_usato": limite - tetto,
            "estensione_fat": [inizio, inizio + len(nuovo_archivio)],
        },
        "rom": {
            "prima": {"byte": len(rom_bytes), "sha256": sha(rom_bytes)},
            "dopo": {"byte": len(risultato), "sha256": sha(risultato)},
        },
        "membri": verbali,
        "crescita_per_membro": {str(v["membro"]): v["crescita"] for v in verbali},
        "rom_container_changes": changes,
    }
    return risultato, rapporto


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--scrcmd", type=Path, default=None,
                    help="scrcmd.json; default: $SGP_PRET_SOURCE/tools/py_scripts/scrcmd.json")
    a = ap.parse_args(argv)
    if a.out.exists():
        ap.error("%s esiste gia': scegliere un percorso di uscita fresco" % a.out)

    try:
        risultato, rapporto = applica(a.rom.read_bytes(), a.scrcmd)
    except GiaApplicata as exc:
        rapporto = {"esito": "GIA_APPLICATA", "motivo": str(exc)}
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(rapporto, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(rapporto, indent=2, ensure_ascii=False))
        return 3
    except Rifiuto as exc:
        rapporto = {"esito": "RIFIUTO", "motivo": str(exc)}
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(rapporto, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(rapporto, indent=2, ensure_ascii=False), file=sys.stderr)
        return 2

    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("xb") as f:
        f.write(risultato)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(rapporto, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(rapporto, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
