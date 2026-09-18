#!/usr/bin/env python3
"""`sgp.borsa` — dodici mutanti a UN BIT, e la suite deve ucciderli tutti.

Un test che non sa morire non prova niente. Ogni mutante spegne un cancello
cambiando un solo bit del blob, poi il banco del nucleo (`test_borsa_nucleo.py`) viene
girata contro il blob mutato: se resta verde, il mutante e' SOPRAVVISSUTO e
questo strumento fallisce.

DUE CONDIZIONI, prima di poter dire «ucciso» — e' il metodo di
`source/features/caramelle/tools/mutanti.py`, ripreso riga per riga:

1. la **corsa di base**, sul blob non mutato, dev'essere VERDE e aver eseguito
   dei test (`Ran N tests`, N > 0). Una suite gia' rossa, o che non parte,
   ucciderebbe tutti i mutanti senza aver provato niente;
2. la corsa del mutante dev'essere rossa **avendo eseguito dei test**. Rossa con
   zero test eseguiti e' un guasto dello strumento (importazione fallita, ROM
   mancante, cartella `test/` vuota), non un cancello che ha funzionato: quel
   mutante e' **NON VALUTABILE** e lo strumento esce diverso da zero.

La suite non viene copiata ne' adattata: e' esattamente la stessa, invocata con
`SGP_BORSA_BUILD` diverso.

Il banco carica il blob dalla cartella indicata da `SGP_BORSA_BUILD`; percio'
ogni mutante usa gli stessi casi ARM reali senza ricostruire le ROM complete.

Uso dalla radice del repository:
    python3 source/features/borsa/tools/mutanti.py [--uscita mutanti.json]

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

PAC = Path(__file__).resolve().parent.parent      # .../source/features/borsa
REPO = PAC.parents[2]
BUILD_DEFAULT = REPO / "source" / "sgp12" / "build" / "borsa"
PY = sys.executable

# «Ran N tests»: l'unica prova che la suite figlia ha davvero ESEGUITO qualcosa.
CONTA = re.compile(r"^Ran (\d+) tests?", re.M)

# (nome, offset nel blob, byte atteso prima, byte dopo, cosa spegne)
# Ogni coppia prima/dopo differisce di UN SOLO bit: lo si verifica qui sotto.
MUTANTI = [
    ("M0-staffetta-item", 0x0EB, 0xD1, 0xD0,
     "bne -> beq sul confronto dell'oggetto della staffetta: un 127 permissivo "
     "su un oggetto armerebbe la consegna di un ALTRO oggetto"),
    ("M1-tabella-ignorata", 0x026, 0x00, 0x01,
     "`movs r2,#0` -> `#1` sull'inizializzazione di `permesso`: permissivo "
     "ovunque, negozi e Angolo dei Premi compresi"),
    ("M2-tetto-mt-mn", 0x1B4, 0x03, 0x02,
     "`cmp r7,#3` -> `#2` sulla tasca: le MT/MN userebbero il tetto 999 invece "
     "del loro 99"),
    ("M3-entra-non-limitata", 0x205, 0xD3, 0xD2,
     "blo -> bhs sul confronto fra quantita' chiesta e spazio residuo: la "
     "quantita' non verrebbe piu' limitata a `tetto - avute`"),
    ("M4-chiavi-e-posta", 0x15C, 0x07, 0x05,
     "`cmp r0,#7` -> `#5` su `(tasca|2)`: il confronto non e' piu' soddisfatto "
     "da nessuna tasca, e ne' gli oggetti chiave ne' la Posta restano immuni"),
    ("M5-posta", 0x158, 0x02, 0x00,
     "`movs r0,#2` -> `#0`: il confronto collassa su `tasca == 7`, cioe' la "
     "Posta (tasca 5) smette di essere immune"),
    ("M6-scorta-ignorata", 0x1B3, 0xD0, 0xD1,
     "beq -> bne sul controllo `avute == 0`: la scorta gia' in borsa non "
     "conterebbe piu' e nessun oggetto risulterebbe mai al tetto"),
    ("M7-staffetta-monouso", 0x0F4, 0x00, 0x01,
     "`movs r0,#0` -> `#1` nell'azzeramento della staffetta dopo un 125 armato: "
     "la staffetta non sarebbe piu' monouso"),
    ("M8-gancio-125", 0x28A, 0x01, 0x00,
     "`movs r1,#1` -> `#0` in sgp_borsa_give_item: il gancio del 125 si "
     "comporterebbe come quello del 127, cioe' non consegnerebbe nulla"),
    ("M9-rifiuto-non-disarma", 0x1EF, 0xD0, 0xD1,
     "beq -> bne sul rifiuto della Borsa: una staffetta parziale resterebbe "
     "armata anche quando lo SLOT manca e il 127 ha detto no"),
    ("M10-finestra-impronta", 0x052, 0x15, 0x55,
     "`ldrb r5,[r2]` -> `[r2,#1]`: la finestra dell'impronta scivola di un "
     "byte e nessuna chiave calcolata combacia piu' con la tabella"),
    ("M11-flag-scartato", 0x237, 0xD2, 0xD3,
     "bhs -> blo sul confronto `entra < qty`: il flag «scartato» verrebbe "
     "alzato quando NON si e' scartato nulla e taciuto quando si e' scartato"),
    ("M12-flag-mai-azzerato", 0x09C, 0x00, 0x01,
     "`movs r1,#0` -> `#1` nell'azzeramento del flag in testa al 125: il flag "
     "resterebbe sempre alto e il messaggio «Borsa piena» uscirebbe su ogni "
     "dono riuscito — e' il difetto 1.2.1 nella sua forma peggiore"),
]


def corsa_suite(amb):
    """Gira il banco che consuma il blob e rende (rc, test eseguiti, uscita).

    Il test composto ricostruisce due ROM complete ma non carica
    ``SGP_BORSA_BUILD``: ripeterlo per ciascun mutante sarebbe lavoro duplicato
    e non potrebbe uccidere un mutante. Qui si esegue soltanto il consumatore
    diretto del blob.
    """
    r = subprocess.run([PY, "-m", "unittest", "discover", "-s", "test",
                        "-p", "test_borsa_nucleo.py"],
                       cwd=str(PAC), capture_output=True, text=True, env=amb)
    uscita = r.stdout + r.stderr
    m = CONTA.search(uscita)
    return r.returncode, (int(m.group(1)) if m else 0), uscita


def un_bit(a, b):
    x = a ^ b
    return x != 0 and (x & (x - 1)) == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", type=Path, default=BUILD_DEFAULT)
    ap.add_argument("--uscita", type=Path, default=None)
    a = ap.parse_args()

    blob0 = (a.build / "blob.bin").read_bytes()
    esiti, sopravvissuti, non_valutabili = [], [], []

    # --- LA CORSA DI BASE, prima di ogni mutante -----------------------------
    amb_base = dict(os.environ, SGP_BORSA_BUILD=str(a.build))
    rc_base, n_base, out_base = corsa_suite(amb_base)
    base = {"returncode": rc_base, "test_eseguiti": n_base,
            "verde": rc_base == 0 and n_base > 0}
    print("corsa di base (blob non mutato): rc=%d, %d test eseguiti — %s"
          % (rc_base, n_base, "VERDE" if base["verde"] else "NON VALUTABILE"))
    if not base["verde"]:
        if a.uscita:
            a.uscita.parent.mkdir(parents=True, exist_ok=True)
            a.uscita.write_text(json.dumps(
                {"base": base,
                 "esito": "NON VALUTABILE: la corsa di base non e' verde"},
                indent=2, ensure_ascii=False) + "\n")
        raise SystemExit(
            "la corsa di base non e' verde (rc=%d, %d test eseguiti): finche' la "
            "suite non passa sul blob SANO, nessun mutante e' valutabile.\n%s"
            % (rc_base, n_base, out_base[-3000:]))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for nome, off, prima, dopo, perche in MUTANTI:
            assert un_bit(prima, dopo), "%s: non e' un guasto a un bit" % nome
            assert blob0[off] == prima, \
                "%s: a +%#x il blob ha %#x, non %#x (il blob e' cambiato: " \
                "rifare gli offset)" % (nome, off, blob0[off], prima)

            d = tmp / nome
            d.mkdir()
            shutil.copy(a.build / "canarino.bin", d / "canarino.bin")
            mutato = bytearray(blob0)
            mutato[off] = dopo
            (d / "blob.bin").write_bytes(bytes(mutato))
            man = json.loads((a.build / "manifesto.json").read_text())
            man["blob"]["sha256"] = hashlib.sha256(bytes(mutato)).hexdigest()
            man["mutante"] = {"nome": nome, "offset": hex(off),
                              "prima": hex(prima), "dopo": hex(dopo),
                              "spegne": perche}
            (d / "manifesto.json").write_text(json.dumps(man, indent=2,
                                                         ensure_ascii=False))

            amb = dict(os.environ, SGP_BORSA_BUILD=str(d))
            rc, eseguiti, uscita = corsa_suite(amb)
            if eseguiti == 0:
                stato, ucciso = "NON VALUTABILE", None
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
            print("%-24s %-14s %3d test eseguiti  (%s)"
                  % (nome, stato, eseguiti, ", ".join(falliti[:3]) or "—"))
            if eseguiti == 0:
                print("    la suite non ha eseguito nessun test:\n" + uscita[-1500:])

    rapporto = {"blob_sha256": hashlib.sha256(blob0).hexdigest(),
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
