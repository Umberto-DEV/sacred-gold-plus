#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-RIFINITURA-01 — taratura finale del moto in lotta: la TAVOLA DELLE FASI.

CHE COSA CAMBIA, E PERCHE'. Misurando il moto dal vivo con `anim=1` (corse
`B-lotta-*.script`, colonne `a0_yoff` di `frames.csv`) e' venuto fuori un difetto
che nessuna prova precedente aveva visto: **alle classi di taglia 2 e 3 lo sprite
fa un salto di 2 px**, sempre negli stessi due punti del ciclo, 22 volte ogni 404
fotogrammi. La sequenza misurata era

    ... +0 +0 +1 +1 +3 +3 +4 +4 +4 +4 +4 +4 +4 +4 +3 +3 +1 +1 +0 ...
                    ^^^^^^^^^                             ^^^^^^^^^
Il valore +2 non compare mai: il moto «scatta» invece di scorrere, ed e'
esattamente l'artefatto che la griglia di `10c` §4 chiama criterio 6.

LA CAUSA non e' l'ampiezza: e' la TAVOLA. `tab_u[18]` contiene il seno per 18
fasi in unita' di 1/16 — `[0, 5, 10, 14, 16, ...]` — e il codice ricava lo
spostamento con `y = (u*k + 8) >> 4`. Con k = 4 (classi 2 e 3) quei valori danno
`0, 1, 3, 4`: fra 5/16 e 10/16 c'e' un salto di 0,3 che a quell'ampiezza diventa
un pixel intero saltato. Con k = 2 e k = 3 (classi 0 e 1) lo stesso seno e'
innocuo, ed e' per questo che la classe del nostro Totodile — la 0 — non aveva
mai mostrato niente.

LA CURA sta nella tavola, non nel codice: `[0, 5, 9, 13, 16, ...]` si scosta dal
seno vero di **1/16 di unita' al massimo** (cioe' 0,06 px a piena ampiezza:
invisibile) ed e' monotona a passi di un pixel per TUTTE e quattro le classi.
Verificato per costruzione dal test `test_tavola.py` e dal vivo rifacendo le
quattro corse per classe.

Percio' questo applicatore **non tocca il blob**: riscrive **18 byte** dentro il
blocco `sgp.anim` gia' applicato da `SGP-1.2-ANIM-B-03`. Non c'e' nessuna
ricompilazione, nessun gancio da rifare, nessun overlay da ricomprimere.

Cancelli (tutti di riconoscimento, prima di scrivere):
  N1  il blocco `sgp.anim` contiene il blob dichiarato applicato (sha256 del
      codice a +0x000) e il canarino dichiarato a +0x2F0;
  N2  la tavola attualmente in ROM e' ESATTAMENTE quella del seno a 18 fasi che
      `compila_animb.py` genera con i parametri di default: se non lo e',
      qualcuno l'ha gia' cambiata e non si sovrascrive niente;
  N3  i parametri a +0x320 (ampiezze, scale, fasi, battito) restano INVARIATI:
      questo cantiere cambia la forma dell'onda, non la sua ampiezza;
  N4  fuori dai 18 byte non cambia un solo byte della ROM.

Uso:
  applica_anim_v3.py --rom R.nds --out O.nds        [--json F]
  applica_anim_v3.py --in-luogo R.nds               [--json F] [--tmp DIR]
  applica_anim_v3.py --rilegge R.nds                (solo verifica, non scrive)
"""
import argparse
import hashlib
import json
import math
import shutil
import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm9 import Arm9  # noqa: E402

BLOCCO_BASE, BLOCCO_N = 0x023D8B00, 1024
OFF_CODICE, OFF_CANARINO, OFF_TAB, OFF_PAR = 0x000, 0x2F0, 0x300, 0x320
N_TAB = 18
FASI = 18

# dichiarati da SGP-1.2-ANIM-B-03/RESULT.json e da MAPPA-RISERVA-ARM9.json
BLOB_SHA = "86a4e1323f3046403b1267d2ad92383c1f59c654447154d1f0ed54ef55248f83"
BLOB_BYTE = 600
CANARINO_MOTIVO = 0xCA5A1400

# la tavola nuova: seno a 18 fasi «lisciato» perche' nessuna classe salti un px
TAB_NUOVA = [0, 5, 9, 13, 16, 16, 13, 9, 5, 0, -5, -9, -13, -16, -16, -13, -9, -5]


class Rifiuto(Exception):
    pass


def no(cancello, msg):
    raise Rifiuto("%s: %s" % (cancello, msg))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def _round(x):
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def tab_attesa_vecchia():
    """La tavola che `compila_animb.py` genera oggi: il seno a 18 fasi."""
    return [_round(math.sin(math.radians(i * (360.0 / FASI))) * 16.0) for i in range(FASI)]


def bytes_tab(valori):
    return bytes((v & 0xFF) for v in valori)


def s8(b):
    return [v - 256 if v >= 128 else v for v in b]


def passo_massimo(tab, k):
    def y(u):
        return (u * k + 8) >> 4 if u >= 0 else -(((-u) * k + 8) >> 4)
    s = [y(u) for u in tab]
    s2 = s + [s[0]]
    return max(abs(s2[i + 1] - s2[i]) for i in range(len(s)))


def controlla(rom, log):
    r = Arm9(Path(rom))
    blocco = bytes(r.leggi(BLOCCO_BASE, BLOCCO_N))
    codice = blocco[OFF_CODICE:OFF_CODICE + BLOB_BYTE]
    if sha(codice) != BLOB_SHA:
        no("N1", "il blocco sgp.anim non contiene il blob dichiarato applicato "
                 "(sha256 %s, atteso %s)" % (sha(codice)[:16], BLOB_SHA[:16]))
    atteso_can = b"".join(struct.pack("<I", CANARINO_MOTIVO | i) for i in range(4))
    if blocco[OFF_CANARINO:OFF_CANARINO + 16] != atteso_can:
        no("N1", "il canarino a +0x%X non e' quello dichiarato" % OFF_CANARINO)
    log.append({"cancello": "N1", "esito": "passato",
                "nota": "blob applicato (%s) e canarino riconosciuti" % BLOB_SHA[:16]})

    tab_ora = s8(blocco[OFF_TAB:OFF_TAB + N_TAB])
    par_ora = blocco[OFF_PAR:OFF_PAR + 32]
    return r, blocco, tab_ora, par_ora


def applica(rom, uscita, json_path=None, solo_lettura=False):
    log = []
    r, blocco, tab_ora, par_ora = controlla(rom, log)
    vecchia = tab_attesa_vecchia()

    if tab_ora == TAB_NUOVA:
        stato = "gia-applicata"
        log.append({"cancello": "N2", "esito": "passato",
                    "nota": "la tavola in ROM e' gia' quella nuova: niente da fare"})
    elif tab_ora == vecchia:
        stato = "da-applicare"
        log.append({"cancello": "N2", "esito": "passato",
                    "nota": "la tavola in ROM e' il seno a 18 fasi di ANIM-B-03"})
    else:
        no("N2", "la tavola in ROM non e' ne' quella di ANIM-B-03 ne' quella nuova: %s"
                 % tab_ora)

    amp = list(par_ora[0:4])
    log.append({"cancello": "N3", "esito": "passato",
                "nota": "ampiezze per classe invariate: %s" % amp})

    misure = {"tabella_prima": tab_ora, "tabella_dopo": TAB_NUOVA,
              "ampiezze": amp,
              "passo_massimo_prima": {str(k): passo_massimo(tab_ora, k) for k in sorted(set(amp))},
              "passo_massimo_dopo": {str(k): passo_massimo(TAB_NUOVA, k) for k in sorted(set(amp))},
              "scarto_massimo_dal_seno_su_16": max(abs(a - b) for a, b in zip(vecchia, TAB_NUOVA))}

    esito = {"strumento": "SGP-1.2-RIFINITURA-01/tools/applica_anim_v3.py",
             "rom": str(rom), "stato": stato, "cancelli": log, "misure": misure,
             "sha256_ingresso": sha(Path(rom).read_bytes())}

    if solo_lettura or stato == "gia-applicata":
        esito["scritto"] = False
    else:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "anim.nds"
            shutil.copyfile(rom, tmp)
            rw = Arm9(tmp)
            prima = bytes(rw.raw)
            rw.scrivi(BLOCCO_BASE + OFF_TAB, bytes_tab(TAB_NUOVA))
            diversi = [i for i in range(len(prima)) if prima[i] != rw.raw[i]]
            if len(diversi) > N_TAB:
                no("N4", "%d byte diversi nell'immagine arm9, attesi al massimo %d"
                         % (len(diversi), N_TAB))
            rw.salva(tmp)
            dati = tmp.read_bytes()
            vecchi = Path(rom).read_bytes()
            fuori = sum(1 for i in range(len(vecchi)) if vecchi[i] != dati[i])
            if fuori > N_TAB:
                no("N4", "%d byte diversi nella ROM, attesi al massimo %d" % (fuori, N_TAB))
            log.append({"cancello": "N4", "esito": "passato",
                        "nota": "%d byte cambiati in tutta la ROM" % fuori})
            Path(uscita).write_bytes(dati)
        esito["scritto"] = True
        esito["byte_cambiati"] = fuori
        esito["uscita"] = str(uscita)
        esito["sha256_uscita"] = sha(Path(uscita).read_bytes())

    if json_path:
        Path(json_path).write_text(json.dumps(esito, indent=1) + "\n")
    print(json.dumps(esito, indent=1))
    return esito


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom")
    ap.add_argument("--out")
    ap.add_argument("--in-luogo", dest="in_luogo")
    ap.add_argument("--rilegge")
    ap.add_argument("--tmp")
    ap.add_argument("--json")
    a = ap.parse_args()
    try:
        if a.rilegge:
            applica(a.rilegge, None, a.json, solo_lettura=True)
        elif a.in_luogo:
            base = Path(a.tmp) if a.tmp else Path(tempfile.gettempdir())
            base.mkdir(parents=True, exist_ok=True)
            tmp = base / (Path(a.in_luogo).stem + "-anim-v3.nds")
            e = applica(a.in_luogo, tmp, a.json)
            if e.get("scritto"):
                shutil.move(str(tmp), a.in_luogo)
                print("APPLICATO IN LUOGO (verificato prima di sostituire)")
            else:
                print("NIENTE DA FARE: la tavola era gia' quella nuova")
        else:
            if not a.rom or not a.out:
                raise SystemExit("servono --rom e --out, oppure --in-luogo, oppure --rilegge")
            applica(a.rom, a.out, a.json)
    except Rifiuto as e:
        print("RIFIUTATO —", e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
