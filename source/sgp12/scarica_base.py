#!/usr/bin/env python3
"""sgp12.scarica_base — scarica i delta dello stadio 0 e li verifica.

    python3 -m sgp12.scarica_base --destinazione "$SGP_ROM_DIR"

E' l'UNICO punto di questo repository che apre una connessione di rete, ed e'
opt-in: niente lo chiama da solo, ne' `costruisci.py`, ne' `verifica.py`, ne'
i test. Chi preferisce non usarlo scarica i due file a mano dalla pagina della
release `base-1.1` e li mette in `$SGP_ROM_DIR` con lo stesso nome.

Cosa scarica: il `SHA256SUMS` della release (deposto come `SHA256SUMS-base-1.1`,
per non scrivere sopra quello delle ROM) e, per ogni lingua chiesta, il delta
dichiarato nel pin `sgp12/base11.json`. Sono file di DIFFERENZE fra una
HeartGold originale e la base 1.1 — non sono ROM, e senza la propria HeartGold
non servono a niente.

Cosa controlla, prima di lasciare un file sul disco:
  * `SHA256SUMS` scaricato e pin devono dire lo stesso sha256 per lo stesso
    nome (se non concordano non si scarica niente: il pin, che e' tracciato in
    git e firmato dalla storia del repository, non e' negoziabile da un file
    scaricato);
  * il file scaricato deve avere quello sha256 e quel numero di byte.
Se qualcosa non torna, il file parziale viene CANCELLATO e il comando rifiuta.
Un delta a meta' non resta mai in `$SGP_ROM_DIR` a farsi trovare dallo stadio 0.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from .rom import Rifiuto, carica_pin, esigi, sha_file

BLOCCO = 1 << 20
# Il nome sulla release...
SHA256SUMS = "SHA256SUMS"
# ...e il nome col quale viene depositato. NON e' lo stesso: `$SGP_ROM_DIR`
# ha gia' un proprio `SHA256SUMS`, quello delle ROM, che `sgp12/test_lib.py`
# legge per sapere che sha256 deve avere la 1.2.2. Scriverci sopra l'elenco
# dei delta avrebbe tolto a quei test il loro riferimento.
SHA256SUMS_DEPOSITO = "SHA256SUMS-base-1.1"


def _apri(url):
    """Aperto qui, in una funzione sola, perche' sia l'unico punto di rete e
    perche' i test possano sostituirlo (o puntare `--url-base` a un server
    locale) senza toccare il resto."""
    return urllib.request.urlopen(url, timeout=60)  # noqa: S310 — url dal pin o da --url-base


def _testo(url, apri) -> str:
    with apri(url) as risposta:
        return risposta.read().decode("utf-8")


def analizza_sha256sums(testo: str) -> dict:
    """`<sha256>  <nome>` per riga, come lo scrive `shasum -a 256`."""
    fuori = {}
    for riga in testo.splitlines():
        riga = riga.strip()
        if not riga:
            continue
        parti = riga.split(None, 1)
        esigi(len(parti) == 2, "SHA256SUMS: riga non interpretabile: %r" % riga[:80])
        impronta, nome = parti[0].lower(), parti[1].strip().lstrip("*")
        esigi(len(impronta) == 64 and all(c in "0123456789abcdef" for c in impronta),
              "SHA256SUMS: %r non e' uno sha256 esadecimale di 64 caratteri" % parti[0][:80])
        fuori[nome] = impronta
    esigi(fuori, "SHA256SUMS: nessuna riga")
    return fuori


def _scarica_file(url, destinazione: Path, atteso_sha: str, atteso_byte: int, apri) -> dict:
    parziale = Path(str(destinazione) + ".parziale")
    if parziale.exists():
        parziale.unlink()
    try:
        with apri(url) as risposta, open(parziale, "wb") as f:
            while True:
                pezzo = risposta.read(BLOCCO)
                if not pezzo:
                    break
                f.write(pezzo)
    except Exception as e:
        if parziale.exists():
            parziale.unlink()
        raise Rifiuto("scaricamento fallito (%s): %s: %s"
                      % (url, type(e).__name__, e)) from None
    letto, byte = sha_file(parziale), parziale.stat().st_size
    if letto != atteso_sha or byte != atteso_byte:
        parziale.unlink()
        raise Rifiuto("%s scaricato da %s non combacia: sha256 %s (%d B), atteso %s (%d B). "
                      "Il file e' stato CANCELLATO."
                      % (destinazione.name, url, letto, byte, atteso_sha, atteso_byte))
    parziale.replace(destinazione)
    return {"nome": destinazione.name, "url": url, "sha256": letto, "byte": byte}


def scarica(destinazione, lingue=None, pin: dict | None = None, url_base=None,
            apri=None, forza: bool = False) -> dict:
    pin = pin or carica_pin()
    apri = apri or _apri
    radice = (url_base or pin["url_base"])
    if not radice.endswith("/"):
        radice += "/"
    lingue = tuple(lingue) if lingue else tuple(pin["basi"])
    for l in lingue:
        esigi(l in pin["basi"], "lingua %r non nel pin (ci sono: %s)"
              % (l, ", ".join(sorted(pin["basi"]))))
    cartella = Path(destinazione)
    esigi(cartella.is_dir(), "--destinazione %s non e' una cartella esistente" % cartella)

    testo = _testo(radice + SHA256SUMS, apri)
    dichiarati = analizza_sha256sums(testo)
    for l in lingue:
        d = pin["basi"][l]["delta"]
        esigi(d["nome"] in dichiarati,
              "SHA256SUMS della release non nomina %s: non scarico niente" % d["nome"])
        esigi(dichiarati[d["nome"]] == d["sha256"],
              "SHA256SUMS della release dice %s per %s, il pin tracciato dice %s. "
              "Non scarico niente: o la release e' stata rifatta, o il file non e' quello."
              % (dichiarati[d["nome"]][:16], d["nome"], d["sha256"][:16]))

    fatti = []
    for l in lingue:
        d = pin["basi"][l]["delta"]
        bersaglio = cartella / d["nome"]
        if bersaglio.is_file() and not forza and sha_file(bersaglio) == d["sha256"]:
            fatti.append({"lingua": l, "esito": "gia presente", "nome": d["nome"],
                          "sha256": d["sha256"], "byte": d["byte"]})
            continue
        # Senza `--url-base` vale l'URL scritto nel pin, che e' quello che si
        # legge in `base11.json`; con `--url-base` (specchio o server di prova)
        # vale la radice data piu' il nome del pin.
        url = d["url"] if url_base is None else radice + d["nome"]
        fatti.append({"lingua": l, "esito": "scaricato",
                      **_scarica_file(url, bersaglio, d["sha256"], d["byte"], apri)})
    (cartella / SHA256SUMS_DEPOSITO).write_text(testo)
    return {"destinazione": str(cartella), "url_base": radice, "file": fatti,
            "sha256sums": str(cartella / SHA256SUMS_DEPOSITO)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--destinazione", required=True,
                    help="la cartella privata delle ROM, di solito $SGP_ROM_DIR")
    ap.add_argument("--lingua", choices=("EN", "IT"), action="append", default=None,
                    help="ripetibile; senza, tutte e due")
    ap.add_argument("--url-base", default=None,
                    help="sostituisce l'URL del pin (specchio, o un server locale nei test)")
    ap.add_argument("--forza", action="store_true",
                    help="riscarica anche un file gia' presente e gia' corretto")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    try:
        rapporto = scarica(a.destinazione, a.lingua, url_base=a.url_base, forza=a.forza)
    except Rifiuto as e:
        print("RIFIUTO: %s" % e, file=sys.stderr)
        return 2
    testo = json.dumps(rapporto, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    print(testo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
