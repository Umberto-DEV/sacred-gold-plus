#!/usr/bin/env python3
"""SGP-1.2-CARAMELLE-01 — applicatore del blocco `sgp.caramelle`.

Lavora SEMPRE su una copia: legge `--rom`, scrive `--uscita`, e non tocca mai
il file di partenza. Nove cancelli, ognuno capace di rifiutare; se uno vola,
NIENTE viene scritto.

    G0  idempotenza: una ROM che ha già il gancio viene RIFIUTATA, non
        ri-applicata. Riapplicare non è un no-op: è un errore di procedura.
    G1  l'ARM9 non è compresso (i module params a 0xBA0 si leggono e le
        sezioni di autoload coprono la riserva).
    G2  l'indirizzo del blocco cade nella zona 1.2 della riserva e il blocco
        intero sta dentro la sezione di autoload.
    G3  preimmagini: i 6 byte del gancio valgono `002801d00920`, e i 256 byte
        del blocco sono TUTTI a zero.
    G4  motivo unico: la preimmagine del gancio (con i 10 byte che la seguono,
        cioè la coda intera del sotto-stato 6) compare UNA volta sola
        nell'ARM9 statico. Controllo negativo: se comparisse due volte, non
        sapremmo di aver patchato il posto giusto.
    G5  invarianti della 1.1: `borsa.text` (0x023DEC80, 4420 B) ha lo sha
        atteso, i quattro `bl` storici della Borsa puntano dove devono, e il
        sito della correzione alla radice (0x023DFB10) è intatto.
    G6  controllo positivo: dopo la scrittura, il `bl` ridecodificato punta a
        `sgp_caramelle_gancio` e i byte riletti coincidono col blob.
    G7  un lettore con l'attesa sbagliata dice no: si ricontrolla la
        preimmagine del gancio DOPO la scrittura e deve NON combaciare più.
    G8  conteggio esatto: fra ROM di partenza e ROM prodotta cambiano
        esattamente 6 + len(blob) + 16 byte, e nessun altro.

Uso: applica_caramelle.py --rom IN.nds --uscita OUT.nds [--build DIR] [--log F]
GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

PAC = Path(__file__).resolve().parent.parent          # source/features/caramelle
SOURCE = PAC.parents[1]                               # source/
sys.path.insert(0, str(SOURCE))
BUILD_DEFAULT = SOURCE / "sgp12" / "build" / "caramelle"
from sgp12.rom import Arm9, Rifiuto, bl_decode, bl_thumb, esigi, sha  # noqa: E402

GANCIO = 0x02081E96
GANCIO_PRE = bytes.fromhex("002801d00920")
GANCIO_CODA = bytes.fromhex("002801d0092000e0002027310870202038bd")   # 18 B
POP_R3R4R5PC = bytes.fromhex("38bd")

BLOCCO_BASE = 0x023DAC00
BLOCCO_N = 0x100
OFF_CODICE = 0x000
OFF_CANARINO = 0x0F0
N_CANARINO = 16
MAX_CODICE = OFF_CANARINO

ZONA_1_2 = (0x023D8000, 0x023DEB40)

# Invarianti della 1.1 (M §2 e verifiche/indirizzi.md, misurati su tutte e
# quattro le ROM: base-1.1-{EN,IT} e sgp-1.2-{EN,IT}).
BORSA_TEXT = (0x023DEC80, 4420,
              "61e648a5c4d1de4235f1228331012487458b53e65c71d9d6f86ad5c6c817a331")
BORSA_BL = {0x0207C39A: 0x023DFD58, 0x0207C3A6: 0x023DFD24,
            0x02081380: 0x023DFD3C, 0x02081396: 0x023DFD6C}
RADICE_1_1 = (0x023DFB10, bytes.fromhex("0020c046"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--build", type=Path, default=BUILD_DEFAULT)
    ap.add_argument("--log", type=Path, default=None)
    a = ap.parse_args()

    man = json.loads((a.build / "manifesto.json").read_text())
    blob = (a.build / "blob.bin").read_bytes()
    canarino = (a.build / "canarino.bin").read_bytes()
    esigi(sha(blob) == man["blob"]["sha256"], "BUILD: blob.bin non è quello del manifesto")
    esigi(sha(canarino) == man["canarino"]["sha256"], "BUILD: canarino non è quello del manifesto")
    esigi(len(blob) <= MAX_CODICE, "BUILD: il blob non entra prima del canarino")
    esigi(len(canarino) == N_CANARINO, "BUILD: canarino di dimensione sbagliata")
    bersaglio = int(man["simboli"]["sgp_caramelle_gancio"], 16)
    esigi(bersaglio & 1 == 1, "BUILD: l'entrata non ha il bit Thumb")
    esigi(bersaglio & ~1 == BLOCCO_BASE + OFF_CODICE,
          "BUILD: l'entrata non è al primo byte del blocco")

    part = Arm9(a.rom)
    log = {"rom": str(a.rom), "sha_rom": sha(a.rom.read_bytes()),
           "blocco": hex(BLOCCO_BASE), "gancio": hex(GANCIO),
           "bersaglio": hex(bersaglio), "blob_byte": len(blob)}

    # --- G1: ARM9 leggibile e non compresso --------------------------------
    esigi(len(part.sezioni) >= 1, "G1: nessuna sezione di autoload")
    autoload = [s for s in part.segmenti if s[0] <= BLOCCO_BASE < s[0] + s[2]]
    esigi(len(autoload) == 1, "G1: il blocco non cade in una sezione di autoload")
    esigi(struct.unpack_from("<I", part.raw, part.off9 + 0xBB4)[0] == 0,
          "G1: l'ARM9 dichiara una dimensione compressa non nulla")
    log["autoload"] = ["%08X+%d" % (autoload[0][0], autoload[0][2])]

    # --- G2: il blocco sta nella zona 1.2 ----------------------------------
    esigi(ZONA_1_2[0] <= BLOCCO_BASE and BLOCCO_BASE + BLOCCO_N <= ZONA_1_2[1],
          "G2: il blocco esce dalla zona 1.2 della riserva")

    # --- G3: preimmagini ---------------------------------------------------
    pre = part.leggi(GANCIO, len(GANCIO_PRE))
    esigi(pre == GANCIO_PRE,
          "G3: preimmagine del gancio diversa: %s invece di %s"
          % (pre.hex(), GANCIO_PRE.hex()))
    zona = part.leggi(BLOCCO_BASE, BLOCCO_N)
    esigi(zona == bytes(BLOCCO_N), "G3: il blocco non è tutto a zero")

    # --- G0: idempotenza ---------------------------------------------------
    # (viene dopo G3 solo nell'ordine di scrittura: G3 fallisce per primo su una
    #  ROM già patchata, e questo messaggio dice perché.)
    gia = bl_decode(GANCIO, part.leggi(GANCIO, 4))
    esigi(gia is None, "G0: a %08X c'è già una BL (verso %s): questa ROM è già "
                       "stata patchata, e riapplicare non è previsto"
                       % (GANCIO, "%08X" % gia if gia else "?"))

    # --- G4: motivo unico nell'ARM9 statico --------------------------------
    base, off, size = part.segmenti[0]
    statico = bytes(part.raw[off:off + size])
    n = statico.count(GANCIO_CODA)
    esigi(n == 1, "G4: la coda del sotto-stato 6 compare %d volte nell'ARM9 "
                  "statico, non una" % n)
    log["occorrenze_motivo"] = n

    # --- G5: invarianti della 1.1 ------------------------------------------
    b_ram, b_n, b_sha = BORSA_TEXT
    esigi(sha(part.leggi(b_ram, b_n)) == b_sha,
          "G5: borsa.text non ha lo sha atteso: la 1.1 non è quella che crediamo")
    for sito, atteso in BORSA_BL.items():
        t = bl_decode(sito, part.leggi(sito, 4))
        esigi(t == atteso, "G5: il bl storico %08X punta a %s invece che a %08X"
              % (sito, "%08X" % t if t else "niente", atteso))
    esigi(part.leggi(RADICE_1_1[0], 4) == RADICE_1_1[1],
          "G5: il sito della correzione alla radice 1.1 è cambiato")

    # --- scrittura ---------------------------------------------------------
    part.scrivi(BLOCCO_BASE + OFF_CODICE, blob)
    part.scrivi(BLOCCO_BASE + OFF_CANARINO, canarino)
    part.scrivi(GANCIO, bl_thumb(GANCIO, bersaglio) + POP_R3R4R5PC)

    # --- G6: controllo positivo --------------------------------------------
    t = bl_decode(GANCIO, part.leggi(GANCIO, 4))
    esigi(t == (bersaglio & ~1), "G6: la BL scritta punta a %s, non a %08X"
          % ("%08X" % t if t else "niente", bersaglio & ~1))
    esigi(part.leggi(GANCIO + 4, 2) == POP_R3R4R5PC, "G6: il pop non è al suo posto")
    esigi(part.leggi(BLOCCO_BASE + OFF_CODICE, len(blob)) == blob, "G6: blob riletto diverso")
    esigi(part.leggi(BLOCCO_BASE + OFF_CANARINO, N_CANARINO) == canarino,
          "G6: canarino riletto diverso")

    # --- G7: il lettore con l'attesa sbagliata dice no ---------------------
    esigi(part.leggi(GANCIO, len(GANCIO_PRE)) != GANCIO_PRE,
          "G7: dopo la scrittura la preimmagine combacia ancora: non si è scritto nulla")

    # --- G8: conteggio esatto dei byte cambiati ----------------------------
    prima = a.rom.read_bytes()
    dopo = bytes(part.raw)
    esigi(len(prima) == len(dopo), "G8: la ROM ha cambiato dimensione")
    diversi = sorted(i for i in range(len(prima)) if prima[i] != dopo[i])
    # i byte del blob che valgono 0 non contano come «cambiati»
    attesi = set()
    for i in range(6):
        attesi.add(part.off(GANCIO) + i)
    for i in range(len(blob)):
        attesi.add(part.off(BLOCCO_BASE + OFF_CODICE) + i)
    for i in range(N_CANARINO):
        attesi.add(part.off(BLOCCO_BASE + OFF_CANARINO) + i)
    fuori = [i for i in diversi if i not in attesi]
    esigi(not fuori, "G8: %d byte cambiati FUORI dalle tre regioni dichiarate "
                     "(primo: %#x)" % (len(fuori), fuori[0] if fuori else 0))
    log["byte_cambiati"] = len(diversi)
    log["byte_cambiati_attesi_max"] = 6 + len(blob) + N_CANARINO

    a.uscita.write_bytes(dopo)
    log["uscita"] = str(a.uscita)
    log["sha_uscita"] = sha(dopo)
    log["esito"] = "applicato"
    testo = json.dumps(log, indent=2, ensure_ascii=False) + "\n"
    if a.log:
        a.log.write_text(testo)
    print(testo)


if __name__ == "__main__":
    try:
        main()
    except Rifiuto as e:
        print("RIFIUTO: %s" % e, file=sys.stderr)
        raise SystemExit(2)
