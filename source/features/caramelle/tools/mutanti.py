#!/usr/bin/env python3
"""`sgp.caramelle` — otto mutanti a UN BIT, e la suite deve ucciderli tutti.

Un test che non sa morire non prova niente. Ogni mutante spegne un cancello
cambiando un solo bit del blob, poi la ROM viene ri-costruita da zero con
l'applicatore vero e la suite vera (`test/test_caramelle.py`) girata contro di
essa: se resta verde, il mutante è SOPRAVVISSUTO e questo strumento fallisce.

DUE CONDIZIONI, prima di poter dire «ucciso»:

1. la **corsa di base**, sul blob non mutato, dev'essere VERDE e aver eseguito
   dei test (`Ran N tests`, N > 0). Una suite già rossa, o che non parte,
   ucciderebbe tutti gli otto mutanti senza aver provato niente;
2. la corsa del mutante dev'essere rossa **avendo eseguito dei test**. Rossa con
   zero test eseguiti è un guasto dello strumento (importazione fallita, ROM
   mancante, cartella `test/` vuota), non un cancello che ha funzionato: quel
   mutante è **NON VALUTABILE** e lo strumento esce diverso da zero.

La suite non viene copiata né adattata: è esattamente la stessa, invocata con
`SGP_CAR_BUILD`, `SGP_ROM_DIR` e `SGP_CAR_ROM_NOME` diversi
(`source/features/options/test/banco.py` usa la stessa convenzione).

LA ROM DI PARTENZA. L'applicatore pretende un blocco a zero e la preimmagine
vanilla al gancio, quindi non si può applicare un mutante su una ROM che ha già
il blocco. Le uniche ROM che `$SGP_ROM_DIR` contiene per definizione sono le
spedite, che ce l'hanno: questo strumento se ne costruisce quindi una copia
DISFATTA — blocco riazzerato e sei byte del gancio riportati alla preimmagine —
e ci applica sopra il blob mutato. La copia disfatta è verificata: se dopo il
disfacimento i cancelli dell'applicatore non passano, lo strumento si ferma.

Uso:
    python3 tools/mutanti.py --rom-dir $SGP_ROM_DIR [--uscita mutanti.json]
    python3 tools/mutanti.py --rom-dir DIR --nome 'sgp-1.2-%s.nds'   # ROM senza il blocco

GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# «Ran N tests»: l'unica prova che la suite figlia ha davvero ESEGUITO qualcosa.
# Senza, un figlio che muore per un errore di importazione, per una cartella
# `test/` vuota o per una ROM mancante esce comunque diverso da zero e passava
# per un mutante ucciso — cioe' un mutante ucciso da nessun cancello.
CONTA = re.compile(r"^Ran (\d+) tests?", re.M)


def corsa_suite(pac, amb):
    """Gira la suite vera e restituisce (returncode, test eseguiti, uscita)."""
    r = subprocess.run([PY, "-m", "unittest", "discover", "-s", "test"],
                       cwd=str(pac), capture_output=True, text=True, env=amb)
    uscita = r.stdout + r.stderr
    m = CONTA.search(uscita)
    return r.returncode, (int(m.group(1)) if m else 0), uscita

PAC = Path(__file__).resolve().parent.parent          # source/features/caramelle
SOURCE = PAC.parents[1]                               # source/
BUILD_DEFAULT = SOURCE / "sgp12" / "build" / "caramelle"
PY = sys.executable

sys.path.insert(0, str(SOURCE))
from sgp12.rom import Arm9, bl_decode                             # noqa: E402

GANCIO = 0x02081E96
GANCIO_PRE = bytes.fromhex("002801d00920")
BLOCCO_BASE, BLOCCO_N = 0x023DAC00, 0x100

# (nome, offset nel blob, byte atteso prima, byte dopo, cosa spegne)
# Ogni coppia prima/dopo differisce di UN SOLO bit: lo si verifica qui sotto.
MUTANTI = [
    ("M1-G3-evoluzione", 0x23, 0xD0, 0xD1,
     "beq -> bne dopo `cmp r0,#0`: con un'evoluzione in coda si resterebbe nel menu"),
    ("M2-G1-item-none", 0x2D, 0xD0, 0xD1,
     "beq -> bne dopo `cmp r1,#0` su itemId: si rientrerebbe SENZA oggetto (R1)"),
    ("M3-G2-contesto", 0x30, 0x05, 0x04,
     "`cmp r0,#5` -> `cmp r0,#4`: il contesto USE_ITEM non sarebbe piu' quello giusto"),
    ("M4-G4-scorta", 0x43, 0xD0, 0xD1,
     "beq -> bne sulla quantita': si resterebbe nel menu con la scorta finita"),
    ("M5-G5-slot", 0x6D, 0xD9, 0xD8,
     "bls -> bhi sul primo confronto di slot: la guardia di 0x02074644 si rovescia"),
    ("M6-stato-di-rientro", 0x9C, 0x04, 0x05,
     "`movs r4,#4` -> `movs r4,#5`: si renderebbe ITEM_USE_CB invece di SELECT_MON"),
    ("M7-messaggio", 0x8A, 0x21, 0x20,
     "`movs r1,#0x21` -> `#0x20`: si stamperebbe il messaggio 32, non il 33"),
    ("M8-heap", 0x3A, 0x0C, 0x0D,
     "`movs r2,#0xc` -> `#0xd`: Bag_GetItemQuantity chiamata sull'heap sbagliato"),
]


def un_bit(a, b):
    x = a ^ b
    return x != 0 and (x & (x - 1)) == 0


def disfa(sorgente: Path, destinazione: Path) -> str:
    """Riporta una ROM spedita allo stato PRIMA del blocco `sgp.caramelle`:
    blocco a zero e sei byte del gancio alla preimmagine vanilla. Rende
    'disfatta' se ha dovuto disfare, 'gia-pulita' se il blocco non c'era."""
    a = Arm9(sorgente)
    aveva = bl_decode(GANCIO, a.leggi(GANCIO, 4)) is not None
    if aveva:
        a.scrivi(BLOCCO_BASE, bytes(BLOCCO_N))
        a.scrivi(GANCIO, GANCIO_PRE)
    destinazione.write_bytes(bytes(a.raw))
    b = Arm9(destinazione)
    if b.leggi(GANCIO, len(GANCIO_PRE)) != GANCIO_PRE:
        raise SystemExit("%s: il gancio non e' tornato alla preimmagine" % sorgente.name)
    if b.leggi(BLOCCO_BASE, BLOCCO_N) != bytes(BLOCCO_N):
        raise SystemExit("%s: il blocco non e' tornato a zero" % sorgente.name)
    return "disfatta" if aveva else "gia-pulita"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom-dir", type=Path,
                    default=Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set")))
    ap.add_argument("--nome", default="sgp-1.2.1-%s.nds",
                    help="modello del nome della ROM dentro --rom-dir (un solo %%s: la lingua)")
    ap.add_argument("--build", type=Path, default=BUILD_DEFAULT)
    ap.add_argument("--uscita", type=Path, default=None)
    a = ap.parse_args()

    blob0 = (a.build / "blob.bin").read_bytes()
    esiti = []
    sopravvissuti = []
    non_valutabili = []

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        pulite = tmp / "pulite"
        pulite.mkdir()
        stato_base = {}
        for L in ("EN", "IT"):
            sorgente = a.rom_dir / (a.nome % L)
            if not sorgente.is_file():
                raise SystemExit("manca %s" % sorgente)
            stato_base[L] = disfa(sorgente, pulite / ("base-%s.nds" % L))
        print("ROM di partenza: %s" % stato_base)

        # --- LA CORSA DI BASE, prima di ogni mutante --------------------------
        # Senza di lei un mutante «ucciso» non vuol dire niente: se la suite
        # fosse rossa gia' sul blob SANO (o non girasse affatto), ogni mutante
        # risulterebbe ucciso e questo strumento direbbe 8 su 8 senza aver
        # provato nulla. La base dev'essere VERDE e aver eseguito dei test.
        amb_base = dict(os.environ, SGP_ROM_DIR=str(a.rom_dir),
                       SGP_CAR_BUILD=str(a.build), SGP_CAR_ROM_NOME=a.nome)
        rc_base, n_base, out_base = corsa_suite(PAC, amb_base)
        base = {"returncode": rc_base, "test_eseguiti": n_base,
                "verde": rc_base == 0 and n_base > 0}
        print("corsa di base (blob non mutato): rc=%d, %d test eseguiti — %s"
              % (rc_base, n_base, "VERDE" if base["verde"] else "NON VALUTABILE"))
        if not base["verde"]:
            if a.uscita:
                a.uscita.parent.mkdir(parents=True, exist_ok=True)
                a.uscita.write_text(json.dumps(
                    {"base": base, "esito": "NON VALUTABILE: la corsa di base non e' verde"},
                    indent=2, ensure_ascii=False) + "\n")
            raise SystemExit(
                "la corsa di base non e' verde (rc=%d, %d test eseguiti): finche' la "
                "suite non passa sul blob SANO, nessun mutante e' valutabile.\n%s"
                % (rc_base, n_base, out_base[-3000:]))

        for nome, off, prima, dopo, perche in MUTANTI:
            assert un_bit(prima, dopo), "%s: non è un guasto a un bit" % nome
            assert blob0[off] == prima, \
                "%s: a +%#x il blob ha %#x, non %#x (il blob è cambiato: " \
                "rifare gli offset)" % (nome, off, blob0[off], prima)

            d = tmp / nome
            d.mkdir()
            for f in ("manifesto.json", "canarino.bin"):
                shutil.copy(a.build / f, d / f)
            mutato = bytearray(blob0)
            mutato[off] = dopo
            (d / "blob.bin").write_bytes(bytes(mutato))
            man = json.loads((d / "manifesto.json").read_text())
            man["blob"]["sha256"] = hashlib.sha256(bytes(mutato)).hexdigest()
            man["mutante"] = {"nome": nome, "offset": hex(off),
                              "prima": hex(prima), "dopo": hex(dopo),
                              "spegne": perche}
            (d / "manifesto.json").write_text(json.dumps(man, indent=2,
                                                         ensure_ascii=False))

            romdir = d / "rom"
            romdir.mkdir()
            for L in ("EN", "IT"):
                r = subprocess.run(
                    [PY, str(PAC / "tools" / "applica_caramelle.py"),
                     "--rom", str(pulite / ("base-%s.nds" % L)),
                     "--uscita", str(romdir / ("mut-%s.nds" % L)),
                     "--build", str(d)],
                    capture_output=True, text=True)
                assert r.returncode == 0, "%s: l'applicatore ha rifiutato: %s" % (nome, r.stderr)

            amb = dict(os.environ, SGP_ROM_DIR=str(romdir), SGP_CAR_BUILD=str(d),
                       SGP_CAR_ROM_NOME="mut-%s.nds")
            rc, eseguiti, uscita = corsa_suite(PAC, amb)
            # Un mutante e' UCCISO solo se la suite ha girato davvero (test
            # eseguiti > 0) ed e' rossa. Rossa con ZERO test eseguiti vuol dire
            # che la suite non e' partita — un guasto dello strumento, non un
            # cancello che ha funzionato: NON VALUTABILE, e rc != 0.
            if eseguiti == 0:
                stato = "NON VALUTABILE"
                ucciso = None
                non_valutabili.append(nome)
            elif rc != 0:
                stato, ucciso = "UCCISO", True
            else:
                stato, ucciso = "SOPRAVVISSUTO", False
                sopravvissuti.append(nome)
            falliti = [x.split(" ")[1] for x in uscita.splitlines()
                       if x.startswith("FAIL: ") or x.startswith("ERROR: ")]
            esiti.append({"mutante": nome, "offset": hex(off),
                          "bit": "%#x -> %#x" % (prima, dopo), "spegne": perche,
                          "returncode": rc, "test_eseguiti": eseguiti,
                          "ucciso": ucciso, "stato": stato,
                          "test_che_lo_uccidono": falliti})
            print("%-22s %-14s %3d test eseguiti  (%s)"
                  % (nome, stato, eseguiti, ", ".join(falliti[:3]) or "—"))
            if eseguiti == 0:
                print("    la suite non ha eseguito nessun test:\n" + uscita[-1500:])

    rapporto = {"blob_sha256": hashlib.sha256(blob0).hexdigest(),
                "rom_di_partenza": stato_base,
                "corsa_di_base": base,
                "mutanti": esiti,
                "sopravvissuti": sopravvissuti,
                "non_valutabili": non_valutabili,
                "esito": ("tutti uccisi" if not sopravvissuti and not non_valutabili
                          else "CI SONO SOPRAVVISSUTI" if sopravvissuti
                          else "CI SONO MUTANTI NON VALUTABILI")}
    if a.uscita:
        a.uscita.parent.mkdir(parents=True, exist_ok=True)
        a.uscita.write_text(json.dumps(rapporto, indent=2, ensure_ascii=False) + "\n")
    if non_valutabili:
        raise SystemExit("mutanti NON VALUTABILI (la suite non ha eseguito test): %s"
                         % ", ".join(non_valutabili))
    if sopravvissuti:
        raise SystemExit("mutanti sopravvissuti: %s" % ", ".join(sopravvissuti))
    print("tutti e %d i mutanti sono stati uccisi (corsa di base: %d test verdi)"
          % (len(MUTANTI), base["test_eseguiti"]))


if __name__ == "__main__":
    main()
