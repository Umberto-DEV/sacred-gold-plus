#!/usr/bin/env python3
"""SGP-1.2-RISERVA-01 — abbassa la base della riserva ARM9 da 0x023DEB40 a 0x023D8000.

Un solo cambiamento verificabile (04-RISERVA-ARM9-F0.md §4, §6 passo 1):
  - il letterale d'arena 0x020D2BB0 passa da 0x023DEB40 a 0x023D8000;
  - l'ultima sezione di autoload ARM9 (la riserva) diventa 0x8000 (32768) B invece di
    0x14C0 (5312), con questo contenuto, dal basso:
      +0x0000  canarino basso     32 B   0xCA5A1000..0xCA5A1007 (u32 LE)
      +0x0020  intestazione       32 B   magic 'SGP2', schema, base, fine,
                                         primi 16 B di sha256(MAPPA-RISERVA-ARM9.json)
      +0x0040  libero 1.2      27392 B   tutto zero (nessun blocco assegnato qui)
      +0x6B40  zona 1.1         5312 B   IDENTICA byte per byte alla riserva letta
                                         dall'ingresso (sha256 43cdd97e...)
  - il letterale mainex_lo (0x020D2C64 = 0x023E0000, estremo alto immobile) NON cambia.

Uso:
    python3 applica_riserva12.py <ingresso.nds> <uscita.nds> <EN|IT> [--json out.json]
                                  [--manifest MAPPA-RISERVA-ARM9.json]

G0 IDEMPOTENZA per primo: se l'ingresso e' gia' (in parte) nello stato d'uscita, si
RIFIUTA (uscita 2) invece di produrre un secondo abbassamento.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[3]
# Richiede l'interprete python3 (vedi source/requirements.txt) (ndspy 4.2.0),
# NON il python3 di sistema: e' li' che ndspy e' installato.

ARENA_HI_LIT = 0x020D2BB0
ARENA_LO_LIT = 0x020D2C5C
MAINEX_LO_LIT = 0x020D2C64
ARENA_LO_ATTESA = 0x0226EC40
ARENA_FINE = 0x023E0000          # estremo alto immobile

BASE_1_1 = 0x023DEB40             # cima della riserva 1.1 (diventa il confine di zona)
RISERVA_1_1_BYTES = 0x14C0        # 5312
RISERVA_1_1_SHA256 = "43cdd97ebb48ad43590274ae90d06352bbc5f5a85c8cb65c651d7f8b35e3e2d2"

BASE_1_2 = 0x023D8000              # nuova cima
RISERVA_TOTALE_BYTES = ARENA_FINE - BASE_1_2   # 32768
CANARINO_BASSO_BYTES = 32
INTESTAZIONE_BYTES = 32
LIBERO_1_2_BYTES = RISERVA_TOTALE_BYTES - CANARINO_BASSO_BYTES - INTESTAZIONE_BYTES - RISERVA_1_1_BYTES
assert LIBERO_1_2_BYTES == 27392

MANIFEST_DEFAULT = Path(os.environ.get("SGP_MAPPA", REPO / "source/docs/arm9-reserve-map.json"))


class Rifiuto(Exception):
    pass


def esigi(cond, msg):
    if not cond:
        raise Rifiuto(msg)


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def canarino(motivo_alto):
    return b"".join(struct.pack("<I", motivo_alto | i) for i in range(8))


def parte_stabile_mappa(manifest_path):
    """REVISIONE 02 (corregge D1 di REVISIONE-OPUS.md): l'intestazione NON porta piu' lo sha
    dell'intero MAPPA-RISERVA-ARM9.json (che cambia a ogni blocco registrato, rompendo il
    legame ROM<->manifest quattro minuti dopo la scrittura, come misurato dalla revisione),
    ma solo di {schema, riserva, zone}: la parte che NON cambia quando un pacchetto successivo
    registra un blocco nuovo dentro una zona gia' esistente. Cambia solo per un cambiamento
    strutturale vero (dimensione/confini della riserva, regole di zona)."""
    m = json.loads(Path(manifest_path).read_text())
    parte = {"schema": m["schema"], "riserva": m["riserva"], "zone": m["zone"]}
    blob = json.dumps(parte, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).digest()[:16]


def costruisci_intestazione(manifest_path):
    manifest_sha = parte_stabile_mappa(manifest_path)
    hdr = bytearray(32)
    hdr[0:4] = b"SGP2"
    struct.pack_into("<I", hdr, 4, 1)               # schema
    struct.pack_into("<I", hdr, 8, BASE_1_2)         # base
    struct.pack_into("<I", hdr, 12, ARENA_FINE)      # fine
    hdr[16:32] = manifest_sha
    return bytes(hdr)


def applica(p_in, p_out, etichetta, manifest_path):
    import ndspy.code
    import ndspy.rom
    from ndspy import _common

    sorgente = Path(p_in).read_bytes()
    parsed = ndspy.rom.NintendoDSRom(sorgente)
    main = parsed.loadArm9()

    r = {"strumento": "SGP-1.2-RISERVA-01/tools/applica_riserva12.py", "rom": etichetta,
         "ingresso": str(p_in), "ingresso_sha256": sha(sorgente), "ingresso_bytes": len(sorgente),
         "cancelli": {}}

    ris = main.sections[-1]

    # ===================== G0: IDEMPOTENZA, prima di ogni scrittura =========
    segni = []
    lit_hi = struct.unpack_from("<I", main.sections[0].data, ARENA_HI_LIT - main.sections[0].ramAddress)[0]
    if lit_hi == BASE_1_2:
        segni.append("il letterale d'arena a 0x%08X vale gia' 0x%08X" % (ARENA_HI_LIT, BASE_1_2))
    if ris.ramAddress == BASE_1_2 or len(ris.data) == RISERVA_TOTALE_BYTES:
        segni.append("l'ultima sezione e' gia' 0x%08X/%d B" % (ris.ramAddress, len(ris.data)))
    esigi(not segni, "G0 IDEMPOTENZA: la ROM in ingresso e' GIA' (in parte) nello stato "
                     "d'uscita. Segni: " + "; ".join(segni) + ". Si rifiuta invece di "
                     "abbassare la base una seconda volta.")
    r["cancelli"]["G0_idempotenza"] = {"segni_esaminati": 2, "segni_gia_in_uscita": [],
                                       "rifiuto_se_uno_solo": True}

    # ===================== G1: preimmagine attesa (base 1.1) ================
    esigi(len(main.sections) == 4, "G1: sezioni di autoload %d, attese 4" % len(main.sections))
    esigi(lit_hi == BASE_1_1, "G1: il letterale d'arena vale 0x%08X, atteso 0x%08X"
                              % (lit_hi, BASE_1_1))
    lit_mainex = struct.unpack_from("<I", main.sections[0].data,
                                    MAINEX_LO_LIT - main.sections[0].ramAddress)[0]
    esigi(lit_mainex == ARENA_FINE, "G1: mainex_lo vale 0x%08X, atteso 0x%08X"
                                    % (lit_mainex, ARENA_FINE))
    esigi(ris.ramAddress == BASE_1_1 and len(ris.data) == RISERVA_1_1_BYTES and ris.bssSize == 0,
          "G1: l'ultima sezione e' 0x%08X/%d/%d, attesa 0x%08X/%d/0: questa non e' una "
          "ROM base 1.1" % (ris.ramAddress, len(ris.data), ris.bssSize, BASE_1_1, RISERVA_1_1_BYTES))
    riserva_1_1 = bytes(ris.data)
    esigi(sha(riserva_1_1) == RISERVA_1_1_SHA256,
          "G1: la riserva 1.1 ha sha256 %s, atteso %s" % (sha(riserva_1_1), RISERVA_1_1_SHA256))
    r["cancelli"]["G1_preimmagine"] = {
        "letterale_arena_hi": "0x%08X" % lit_hi, "letterale_mainex_lo": "0x%08X" % lit_mainex,
        "riserva_1_1_sha256": sha(riserva_1_1), "riserva_1_1_bytes": len(riserva_1_1)}

    # ===================== G2: nessuna overlay nella futura riserva =========
    t = parsed.arm9OverlayTable
    n = len(t) // 32
    overlay = [struct.unpack_from("<8I", t, i * 32) for i in range(n)]
    coll = [(o[0], o[1], o[1] + o[2] + o[3]) for o in overlay
            if o[1] < ARENA_FINE and o[1] + o[2] + o[3] > BASE_1_2]
    esigi(not coll, "G2: %d overlay intersecano [0x%08X,0x%08X): %s"
                    % (len(coll), BASE_1_2, ARENA_FINE, coll))
    r["cancelli"]["G2_nessuna_overlay"] = {"overlay_totali": n, "in_collisione": 0}

    # ===================== costruzione della nuova riserva ===================
    manifest_path = manifest_path or MANIFEST_DEFAULT
    esigi(Path(manifest_path).exists(), "manifest non trovato: %s" % manifest_path)
    can = canarino(0xCA5A1000)
    hdr = costruisci_intestazione(manifest_path)
    libero = bytes(LIBERO_1_2_BYTES)
    nuova_riserva = can + hdr + libero + riserva_1_1
    esigi(len(nuova_riserva) == RISERVA_TOTALE_BYTES,
          "la riserva nuova misura %d B, attesi %d" % (len(nuova_riserva), RISERVA_TOTALE_BYTES))
    # la zona 1.1 non e' cambiata di un bit dentro il blob che stiamo per scrivere
    esigi(nuova_riserva[-RISERVA_1_1_BYTES:] == riserva_1_1, "la coda 1.1 e' stata alterata in memoria")
    r["nuova_riserva"] = {"bytes": len(nuova_riserva), "sha256": sha(nuova_riserva),
                          "canarino_basso_sha256": sha(can), "intestazione_sha256": sha(hdr),
                          "manifest_usato": str(manifest_path),
                          "manifest_sha256_file_intero": hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
                          "manifest_parte_stabile_sha256_primi16": parte_stabile_mappa(manifest_path).hex()}

    # ===================== scritture =========================================
    struct.pack_into("<I", main.sections[0].data, ARENA_HI_LIT - main.sections[0].ramAddress, BASE_1_2)
    main.sections[-1] = ndspy.code.MainCodeFile.Section(nuova_riserva, BASE_1_2, 0)
    r["scritture"] = [
        {"cosa": "letterale d'arena", "sito": "0x%08X" % ARENA_HI_LIT,
         "prima": "0x%08X" % BASE_1_1, "dopo": "0x%08X" % BASE_1_2, "bytes": 4},
        {"cosa": "sezione di autoload 4 SOSTITUITA",
         "prima": "0x%08X/%d B" % (BASE_1_1, RISERVA_1_1_BYTES),
         "dopo": "0x%08X/%d B" % (BASE_1_2, RISERVA_TOTALE_BYTES)},
    ]

    # ===================== riserializzazione dell'ARM9 in luogo =============
    arm9_in = bytes(parsed.arm9)
    nuovo = main.save(compress=False)
    inizio9 = struct.unpack_from("<I", sorgente, 0x20)[0]
    esigi(inizio9 == 0x4000, "area sicura in posizione inattesa")
    confini = [struct.unpack_from("<I", sorgente, o)[0] for o in (0x30, 0x40, 0x48, 0x50, 0x58, 0x68)]
    fat_off, fat_size = struct.unpack_from("<II", sorgente, 0x48)
    confini += [struct.unpack_from("<II", sorgente, fat_off + i * 8)[0] for i in range(fat_size // 8)]
    est = min(c for c in confini if c > inizio9) - inizio9
    dati9 = nuovo + bytes(parsed.arm9PostData)
    esigi(len(dati9) <= est,
          "G3: ARM9+footer %d B non entra nei %d B liberi prima del prossimo blocco della "
          "ROM (tabella overlay/FAT/FNT): servirebbe un pacchetto che sposti quei blocchi"
          % (len(dati9), est))
    va, na = arm9_in[:0x800], nuovo[:0x800]
    esigi(va == na, "G4: il prefisso cifrato dell'area sicura (primi 0x800 B dell'ARM9) e' cambiato")

    risultato = bytearray(sorgente)
    risultato[inizio9:inizio9 + len(dati9)] = dati9
    struct.pack_into("<I", risultato, 0x2C, len(nuovo))
    crc = parsed.secureAreaChecksum ^ _common.crc16(va) ^ _common.crc16(na)
    struct.pack_into("<H", risultato, 0x6C, crc)
    struct.pack_into("<H", risultato, 0x15E, _common.crc16(bytes(risultato[:0x15E])))
    r["arm9"] = {"prima": len(arm9_in), "dopo": len(nuovo), "crescita": len(nuovo) - len(arm9_in),
                 "riserva_immagine": est, "residua": est - len(dati9),
                 "secure_area_invariata": True}

    esigi(len(risultato) == len(sorgente), "G5: la dimensione del file e' cambiata "
                                           "(%d -> %d)" % (len(sorgente), len(risultato)))
    r["cancelli"]["G3_spazio_arm9"] = {"disponibile": est, "usato": len(dati9), "residuo": est - len(dati9)}
    r["cancelli"]["G4_area_sicura_invariata"] = True
    r["cancelli"]["G5_dimensione_file_invariata"] = len(risultato)

    diversi = [i for i in range(len(sorgente)) if sorgente[i] != risultato[i]]
    r["byte_cambiati_totali"] = len(diversi)
    r["byte_cambiati_intervallo"] = ["0x%08X" % min(diversi), "0x%08X" % max(diversi)] if diversi else []

    Path(p_out).parent.mkdir(parents=True, exist_ok=True)
    Path(p_out).write_bytes(bytes(risultato))
    r["uscita"] = str(p_out)
    r["uscita_sha256"] = sha(risultato)
    r["uscita_bytes"] = len(risultato)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ingresso")
    ap.add_argument("uscita")
    ap.add_argument("etichetta")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--manifest", type=Path, default=None)
    a = ap.parse_args()
    try:
        rap = applica(a.ingresso, a.uscita, a.etichetta, a.manifest)
    except Rifiuto as e:
        print("RIFIUTO: %s" % e, file=sys.stderr)
        raise SystemExit(2)
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(rap, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(rap, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
