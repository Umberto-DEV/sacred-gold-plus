#!/usr/bin/env python3
"""rileggi_appendici.py — rilettore INDIPENDENTE di SGP-1.2-BORSA-GEN-09.

Non importa nulla da `applica_appendici.py` ne' da `appendici_def.py`: ridefinisce
da zero la sequenza attesa, riconosce i comandi per NOME (letto da `scrcmd.json`
del pret, non per numero cablato) e ricammina i sei flussi sul bytecode della ROM
di arrivo. Del pacchetto 01 usa solo il disassemblatore validato-P1
(`scr_disasm.py`), in sola lettura: e' lo stesso strumento che ha gia' superato
il cancello di ri-serializzazione byte per byte.

CONTROLLI (tutti devono essere verdi):
  1. per ciascuno dei 6 flussi, la traccia attesa — dall'ancora del flusso fino
     alla fine — coincide istruzione per istruzione, argomenti compresi;
  2. il blocco del messaggio compare UNA volta per flusso, nella forma esatta
     (guardia sul flag, nome oggetto ricaricato, banco 199 messaggio 10, attesa,
     azzeramento del flag) e il salto di guardia scavalca esattamente il blocco;
  3. `scr_disasm --verifica` (ri-serializzazione) verde su TUTTO l'archivio, e
     i membri con errori di decodifica sono esattamente i 6 preesistenti;
  4. nessun membro dell'archivio cambia oltre i cinque previsti;
  5. la ROM ha la stessa lunghezza e nessun byte diverso fuori da `a/0/1/2` e
     dalla sua voce FAT di 8 byte;
  6. l'archivio resta dentro l'estensione che aveva nella 1.2.1 (crescita ROM 0).
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

import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402
import scr_disasm as SD  # noqa: E402

ARCHIVIO = "a/0/1/2"
N_MEMBRI = 965
ESTENSIONE_1_2_1 = 442616
MEMBRI_ATTESI = {3, 141, 145, 240, 938}
# I 6 membri che gia' nella 1.2.1 (e nella Sacred Gold Plus 1.03) portano coda
# morta non decodificabile: `U-borsa-progetto-esecutivo.md` §1.3.
ERRORI_PREESISTENTI = [225, 232, 243, 246, 938, 962]

VAR_ITEM = 0x8004
VAR_SCARTATO = 0x800A   # vedi sorgenti/sgp_borsa.h: NON e' 0x800D (LAST_TALKED)
BANCO = 199
MESSAGGIO = 10
COND_NE = 5


# --- la traccia attesa, scritta a mano, in termini di NOMI di comando -------
# ("i", nome, args)  -> l'istruzione successiva in ordine lineare
#                        (args None = non controllato)
# ("salta", k)       -> segui il ramo k dell'istruzione appena letta
# ("msg",)           -> il blocco del messaggio, espanso da `attesa_messaggio`
def attesa_messaggio():
    return [
        ("i", "CompareVarToValue", [VAR_SCARTATO, 1]),
        ("i", "GoToIf", [COND_NE, "@dopo_blocco"]),
        ("i", "BufferItemName", [1, VAR_ITEM]),
        ("i", "MsgBoxExtern", [BANCO, MESSAGGIO]),
        ("i", "WaitButton", []),
        ("i", "SetVar", [VAR_SCARTATO, 0]),
        ("@dopo_blocco",),
    ]


TRACCE = {
    "membro 3 / std 2008 std_obtain_item_verbose — ramo plurale": (3, 2110, [
        ("i", "GoToIf", None), ("salta", 0),
        ("i", "NPCMsg", [31]),
        ("i", "WaitButton", []),
        ("msg",),
        ("i", "Return", []),
    ]),
    "membro 3 / std 2008 std_obtain_item_verbose — ramo singolare": (3, 2117, [
        ("i", "NPCMsg", [30]),
        ("i", "GoTo", None), ("salta", 0),
        ("i", "WaitButton", []),
        ("msg",),
        ("i", "Return", []),
    ]),
    "membro 3 / std 2033 std_give_item_verbose": (3, 2176, [
        ("i", "CompareVarToValue", [0x800C, 7]),
        ("i", "GoTo", None), ("salta", 0),
        ("i", "CallIf", [COND_NE, 2211]),
        ("i", "NPCMsg", [89]),
        ("msg",),
        ("i", "Return", []),
    ]),
    "membro 141 — Poke Ball a terra (tutte)": (141, 6522, [
        ("i", "NPCMsg", [9]),
        ("i", "WaitButton", []),
        ("i", "GoTo", None), ("salta", 0),
        ("i", "SetVar", [0x800C, 1]),
        ("msg",),
        ("i", "GoTo", [6533]), ("salta", 0),
        ("i", "GoTo", [6186]), ("salta", 0),
        ("i", "CloseMsg", []),
        ("i", "ReleaseAll", []),
        ("i", "End", []),
    ]),
    "membro 145 — oggetti nascosti (tutti)": (145, 1418, [
        ("i", "NPCMsg", [9]),
        ("i", "WaitButton", []),
        ("i", "GoTo", None), ("salta", 0),
        ("i", "SetVar", [0x800C, 1]),
        ("msg",),
        ("i", "GoTo", [1429]), ("salta", 0),
        ("i", "GoTo", [1084]), ("salta", 0),
        ("i", "CloseMsg", []),
        ("i", "End", []),
    ]),
    "membro 240 — nascosto scritto a mano": (240, 913, [
        ("i", "NPCMsg", [3]),
        ("i", "WaitButton", []),
        ("i", "GoTo", None), ("salta", 0),
        ("i", "SetVar", [0x800C, 1]),
        ("msg",),
        ("i", "GoTo", [924]), ("salta", 0),
        ("i", "CloseMsg", []),
        ("i", "ReleaseAll", []),
        ("i", "End", []),
    ]),
    "membro 938 — nascosto a mano n.1 (@1705)": (938, 1745, [
        ("i", "NPCMsg", [34]),
        ("i", "WaitButton", []),
        ("i", "GoTo", None), ("salta", 0),
        ("i", "SetVar", [0x800C, 1]),
        ("msg",),
        ("i", "CloseMsg", []),
        ("i", "ReleaseAll", []),
        ("i", "End", []),
    ]),
    "membro 938 — nascosto a mano n.2 (@1856)": (938, 1896, [
        ("i", "NPCMsg", [34]),
        ("i", "WaitButton", []),
        ("i", "GoTo", None), ("salta", 0),
        ("i", "SetVar", [0x800C, 1]),
        ("msg",),
        ("i", "CloseMsg", []),
        ("i", "ReleaseAll", []),
        ("i", "End", []),
    ]),
}


def sha(b) -> str:
    return hashlib.sha256(bytes(b)).hexdigest()


def segui(membro, ancora, passi, problemi, nome_traccia):
    """Cammina la traccia. Torna la lista testuale delle istruzioni viste."""
    passi = [p for voce in passi for p in (attesa_messaggio() if voce[0] == "msg" else [voce])]
    pc = ancora
    visto = []
    etichette = {}
    attesa_etichette = {}
    ultima = None
    for passo in passi:
        if passo[0].startswith("@"):
            etichette[passo[0]] = pc
            continue
        if passo[0] == "salta":
            if ultima is None or len(ultima.rami) <= passo[1]:
                problemi.append("%s: atteso un ramo su %s @%d" % (nome_traccia, ultima.nome if ultima else "?", pc))
                return visto
            pc = ultima.rami[passo[1]][1]
            continue
        _, nome_atteso, args_attesi = passo
        ins = membro.istruzioni.get(pc)
        if ins is None:
            problemi.append("%s: nessuna istruzione decodificata a %d" % (nome_traccia, pc))
            return visto
        if ins.nome != nome_atteso:
            problemi.append("%s @%d: atteso %s, letto %s"
                            % (nome_traccia, pc, nome_atteso, ins.nome))
            return visto
        if args_attesi is not None:
            reali = []
            for v, t in zip(ins.args, ins.tipi):
                reali.append(v)
            # gli argomenti relativi si confrontano come DESTINAZIONI assolute
            dest = {i: d for i, d, _ in ins.rami}
            for k, atteso in enumerate(args_attesi):
                letto = dest.get(k, reali[k] if k < len(reali) else None)
                if isinstance(atteso, str) and atteso.startswith("@"):
                    attesa_etichette.setdefault(atteso, []).append((nome_traccia, pc, letto))
                    continue
                if letto != atteso:
                    problemi.append("%s @%d %s: argomento %d = %r, atteso %r"
                                    % (nome_traccia, pc, ins.nome, k, letto, atteso))
        visto.append("%5d  %s" % (pc, ins.testo()))
        ultima = ins
        pc = ins.fine
    for et, occorrenze in attesa_etichette.items():
        if et not in etichette:
            problemi.append("%s: etichetta %s mai raggiunta" % (nome_traccia, et))
            continue
        for _, off, letto in occorrenze:
            if letto != etichette[et]:
                problemi.append("%s @%d: il salto di guardia va a %r, atteso %d (%s)"
                                % (nome_traccia, off, letto, etichette[et], et))
    return visto


def rileggi(prima: Path, dopo: Path, pret: Path):
    esito = {"rom_prima": str(prima), "rom_dopo": str(dopo), "problemi": []}
    problemi = esito["problemi"]

    b_prima = prima.read_bytes()
    b_dopo = dopo.read_bytes()
    esito["byte_rom"] = {"prima": len(b_prima), "dopo": len(b_dopo)}
    if len(b_prima) != len(b_dopo):
        problemi.append("la ROM ha cambiato lunghezza")

    # --- 5. nessun byte diverso fuori da a/0/1/2 e dalla sua voce FAT --------
    fat_start, fat_size = struct.unpack_from("<II", b_dopo, 0x48)
    r_prima = ndspy.rom.NintendoDSRom(b_prima)
    idx = r_prima.filenames.idOf(ARCHIVIO)
    s0, e0 = struct.unpack_from("<II", b_prima, fat_start + idx * 8)
    s1, e1 = struct.unpack_from("<II", b_dopo, fat_start + idx * 8)
    esito["estensione_fat"] = {"prima": [s0, e0], "dopo": [s1, e1],
                               "voce_fat": fat_start + idx * 8}
    if s0 != s1:
        problemi.append("l'archivio e' stato rilocato: %d -> %d" % (s0, s1))
    if e1 - s1 > ESTENSIONE_1_2_1:
        problemi.append("l'archivio (%d B) sborda l'estensione della 1.2.1 (%d B)"
                        % (e1 - s1, ESTENSIONE_1_2_1))
    esito["archivio_byte"] = {"prima": e0 - s0, "dopo": e1 - s1,
                              "crescita": (e1 - s1) - (e0 - s0),
                              "tetto_1_2_1": ESTENSIONE_1_2_1}

    # Sono ammesse differenze soltanto nell'unione dell'estensione FAT prima e
    # dopo. Il margine fino al vecchio tetto 1.2.1 non appartiene al NARC
    # finale: esentarlo maschererebbe scritture fuori archivio.
    limite = max(e0, e1)
    voce = fat_start + idx * 8
    diversi = []
    n = min(len(b_prima), len(b_dopo))
    blocco = 1 << 16
    for a in range(0, n, blocco):
        b = min(a + blocco, n)
        if b_prima[a:b] == b_dopo[a:b]:
            continue
        for k in range(a, b):
            if b_prima[k] != b_dopo[k]:
                if s1 <= k < limite or voce <= k < voce + 8:
                    continue
                diversi.append(k)
                if len(diversi) > 32:
                    break
        if len(diversi) > 32:
            break
    esito["byte_diversi_fuori_archivio"] = len(diversi)
    esito["primi_byte_diversi"] = diversi[:8]
    if diversi:
        problemi.append("%d byte diversi fuori da %s e dalla sua voce FAT"
                        % (len(diversi), ARCHIVIO))

    # --- 4. quali membri cambiano ------------------------------------------
    f_prima = ndspy.narc.NARC(r_prima.getFileByName(ARCHIVIO)).files
    r_dopo = ndspy.rom.NintendoDSRom(b_dopo)
    f_dopo = ndspy.narc.NARC(r_dopo.getFileByName(ARCHIVIO)).files
    if len(f_prima) != N_MEMBRI or len(f_dopo) != N_MEMBRI:
        problemi.append("numero di membri inatteso: %d -> %d" % (len(f_prima), len(f_dopo)))
    cambiati = sorted(i for i in range(min(len(f_prima), len(f_dopo)))
                      if bytes(f_prima[i]) != bytes(f_dopo[i]))
    esito["membri_cambiati"] = cambiati
    esito["membri"] = {str(i): {"prima": len(f_prima[i]), "dopo": len(f_dopo[i]),
                                "crescita": len(f_dopo[i]) - len(f_prima[i]),
                                "sha256_dopo": sha(f_dopo[i])}
                       for i in cambiati}
    if set(cambiati) != MEMBRI_ATTESI:
        problemi.append("membri cambiati %r, attesi %r" % (cambiati, sorted(MEMBRI_ATTESI)))

    # --- 1/2/3. il bytecode -------------------------------------------------
    cmds = SD.Comandi(pret / "tools/py_scripts/scrcmd.json")
    membri = SD.disassembla_tutto(f_dopo, cmds)
    con_errori = [m.indice for m in membri if m.errori]
    esito["membri_con_errori_di_decodifica"] = con_errori
    if con_errori != ERRORI_PREESISTENTI:
        problemi.append("errori di decodifica %r, attesi i 6 preesistenti %r"
                        % (con_errori, ERRORI_PREESISTENTI))
    diversi_riass = [(m.indice, off) for m in membri
                     for ok, off in [m.riassembla()] if not ok]
    esito["cancello_riserializzazione"] = "VERDE" if not diversi_riass else "ROSSO"
    if diversi_riass:
        problemi.append("ri-serializzazione rossa: %r" % diversi_riass[:5])

    esito["tracce"] = {}
    for nome, (mi, ancora, passi) in TRACCE.items():
        visto = segui(membri[mi], ancora, passi, problemi, nome)
        esito["tracce"][nome] = visto

    esito["ok"] = not problemi
    return esito


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prima", required=True, type=Path, help="ROM prima delle appendici")
    ap.add_argument("--dopo", required=True, type=Path, help="ROM dopo le appendici")
    ap.add_argument("--pret", type=Path,
                    default=Path(os.environ["SGP_PRET_SOURCE"])
                    if os.environ.get("SGP_PRET_SOURCE") else None)
    ap.add_argument("--report", required=True, type=Path)
    a = ap.parse_args(argv)
    if a.pret is None:
        ap.error("--pret oppure SGP_PRET_SOURCE e' obbligatorio")
    esito = rileggi(a.prima, a.dopo, a.pret)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(esito, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in esito.items() if k != "tracce"},
                     indent=2, ensure_ascii=False))
    for nome, visto in esito["tracce"].items():
        print("\n--- %s" % nome)
        for riga in visto:
            print("   " + riga)
    return 0 if esito["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
