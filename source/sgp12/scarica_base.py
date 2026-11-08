#!/usr/bin/env python3
"""sgp12.scarica_base — scarica i delta dello stadio 0 e li verifica.

    python3 -m sgp12.scarica_base --destinazione "$SGP_ROM_DIR"

E' l'UNICO punto di questo repository che apre una connessione di rete, ed e'
opt-in: niente lo chiama da solo, ne' `costruisci.py`, ne' `verifica.py`, ne'
i test. Chi preferisce non usarlo scarica i due file a mano dalla pagina della
release `base-1.1` e li mette in `$SGP_ROM_DIR` con lo stesso nome.

La consegna corrente usa il singolo Sacred-Gold-Plus-1.3.2.zip: il pin separato
distribution/build-input-delivery.json autentica l'intero ZIP e ogni membro.
--container riusa lo ZIP gia' scaricato. I soli delta richiesti sono copiati
da Developer-Inputs/, mai una ROM; i quattro input storici restano invariati.
Un file esistente diverso o un link viene preservato e rifiutato: scegliere una
cartella nuova. --forza riguarda la consegna diretta storica; nello ZIP un file
gia' autenticato viene riusato. Il downloader non e' chiamato dai builder.

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
import hashlib
import json
import os
import secrets
import stat
import sys
import time
import urllib.request
from pathlib import Path

from .rom import Rifiuto, carica_pin, esigi

BLOCCO = 1 << 20
MAX_SHA256SUMS_BYTE = 64 << 10
DURATA_MASSIMA_SCARICAMENTO = 30 * 60
# Il nome sulla release...
SHA256SUMS = "SHA256SUMS"
# ...e il nome col quale viene depositato. NON e' lo stesso: `$SGP_ROM_DIR`
# ha gia' un proprio `SHA256SUMS`, quello delle ROM, che `sgp12/test_lib.py`
# legge per sapere che sha256 deve avere la 1.2.2. Scriverci sopra l'elenco
# dei delta avrebbe tolto a quei test il loro riferimento.
SHA256SUMS_DEPOSITO = "SHA256SUMS-base-1.1"


def _apri_cartella_privata(destinazione) -> tuple[Path, int]:
    """Apre una volta la cartella di lavoro e ne conserva l'identita'."""
    cartella = Path(destinazione)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        dir_fd = os.open(cartella, flags)
    except OSError as e:
        raise Rifiuto("--destinazione %s non e' una cartella reale accessibile: %s"
                      % (cartella, e)) from None
    try:
        stato = os.fstat(dir_fd)
        esigi(stat.S_ISDIR(stato.st_mode),
              "--destinazione %s non e' una cartella" % cartella)
        esigi(stato.st_uid == os.getuid(),
              "--destinazione %s non appartiene all'utente corrente" % cartella)
        esigi(not (stato.st_mode & (stat.S_IWGRP | stat.S_IWOTH)),
              "--destinazione %s e' scrivibile da gruppo o altri; usa una cartella privata"
              % cartella)
    except Exception:
        os.close(dir_fd)
        raise
    return cartella, dir_fd


def _crea_temporaneo(dir_fd: int, nome_finale: str) -> tuple[str, int]:
    """Crea un file 0600 imprevedibile, esclusivo e relativo alla cartella trattenuta."""
    esigi(Path(nome_finale).name == nome_finale and nome_finale not in ("", ".", ".."),
          "nome di uscita non sicuro: %r" % nome_finale)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    for _ in range(128):
        nome = ".%s.parziale-%s" % (nome_finale, secrets.token_hex(12))
        try:
            return nome, os.open(nome, flags, 0o600, dir_fd=dir_fd)
        except FileExistsError:
            continue
    raise Rifiuto("impossibile creare un file temporaneo esclusivo per %s" % nome_finale)


def _elimina_temporaneo(dir_fd: int, nome: str) -> None:
    try:
        os.unlink(nome, dir_fd=dir_fd)
    except FileNotFoundError:
        pass


def _sha_regolare(dir_fd: int, nome: str) -> tuple[str, int] | None:
    """Legge una entry regolare senza seguire link; le altre non sono riusate."""
    try:
        prima = os.stat(nome, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(prima.st_mode):
        return None
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(nome, flags, dir_fd=dir_fd)
    except OSError:
        return None
    h = hashlib.sha256()
    totale = 0
    with os.fdopen(fd, "rb") as f:
        dopo = os.fstat(f.fileno())
        if (prima.st_dev, prima.st_ino) != (dopo.st_dev, dopo.st_ino):
            return None
        while True:
            pezzo = f.read(BLOCCO)
            if not pezzo:
                break
            h.update(pezzo)
            totale += len(pezzo)
    return h.hexdigest(), totale


def _scrivi_atomico(dir_fd: int, nome_finale: str, dati: bytes) -> None:
    temporaneo, fd = _crea_temporaneo(dir_fd, nome_finale)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(dati)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporaneo, nome_finale, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    except Exception as e:
        _elimina_temporaneo(dir_fd, temporaneo)
        raise Rifiuto("pubblicazione sicura di %s fallita: %s" % (nome_finale, e)) from None


def _apri(url):
    """Aperto qui, in una funzione sola, perche' sia l'unico punto di rete e
    perche' i test possano sostituirlo (o puntare `--url-base` a un server
    locale) senza toccare il resto."""
    return urllib.request.urlopen(url, timeout=60)  # noqa: S310 — url dal pin o da --url-base


def _esigi_content_length(risposta, massimo: int, url: str) -> None:
    headers = getattr(risposta, "headers", None)
    valore = headers.get("Content-Length") if headers is not None else None
    if valore is None:
        return
    try:
        dichiarato = int(valore)
    except (TypeError, ValueError):
        raise Rifiuto("Content-Length non valido da %s: %r" % (url, valore)) from None
    esigi(0 <= dichiarato <= massimo,
          "risposta da %s dichiara %d byte, limite %d" % (url, dichiarato, massimo))


def _esigi_tempo(orologio, inizio: float, url: str) -> None:
    esigi(orologio() - inizio <= DURATA_MASSIMA_SCARICAMENTO,
          "scaricamento da %s oltre il limite complessivo di %d secondi"
          % (url, DURATA_MASSIMA_SCARICAMENTO))


def _leggi_blocco(risposta, massimo: int) -> bytes:
    """HTTP ``read1`` limita ogni giro a una sola lettura del trasporto."""
    leggi = getattr(risposta, "read1", None)
    return (leggi if callable(leggi) else risposta.read)(massimo)


def _testo(url, apri, *, orologio=time.monotonic, inizio=None) -> str:
    inizio = orologio() if inizio is None else inizio
    dati = bytearray()
    try:
        with apri(url) as risposta:
            _esigi_content_length(risposta, MAX_SHA256SUMS_BYTE, url)
            while True:
                _esigi_tempo(orologio, inizio, url)
                rimanenti = MAX_SHA256SUMS_BYTE - len(dati)
                pezzo = _leggi_blocco(risposta, min(BLOCCO, rimanenti + 1))
                _esigi_tempo(orologio, inizio, url)
                if not pezzo:
                    break
                esigi(len(dati) + len(pezzo) <= MAX_SHA256SUMS_BYTE,
                      "SHA256SUMS da %s supera il limite di %d byte"
                      % (url, MAX_SHA256SUMS_BYTE))
                dati.extend(pezzo)
    except Rifiuto:
        raise
    except Exception as e:
        raise Rifiuto("scaricamento SHA256SUMS fallito (%s): %s: %s"
                      % (url, type(e).__name__, e)) from None
    try:
        return bytes(dati).decode("utf-8")
    except UnicodeDecodeError as e:
        raise Rifiuto("SHA256SUMS da %s non e' UTF-8 valido: %s" % (url, e)) from None


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


def _scarica_file(url, destinazione: Path, atteso_sha: str, atteso_byte: int,
                  apri, dir_fd: int, *, orologio=time.monotonic, inizio=None) -> dict:
    temporaneo, fd = _crea_temporaneo(dir_fd, destinazione.name)
    h = hashlib.sha256()
    byte = 0
    inizio = orologio() if inizio is None else inizio
    try:
        # Il file viene gestito per primo: se l'apertura di rete fallisce, il
        # descriptor locale viene comunque chiuso dal context manager esterno.
        with os.fdopen(fd, "wb") as f, apri(url) as risposta:
            _esigi_content_length(risposta, atteso_byte, url)
            while True:
                _esigi_tempo(orologio, inizio, url)
                pezzo = _leggi_blocco(risposta, min(BLOCCO, atteso_byte - byte + 1))
                _esigi_tempo(orologio, inizio, url)
                if not pezzo:
                    break
                esigi(byte + len(pezzo) <= atteso_byte,
                      "%s da %s supera i %d byte fissati dal pin"
                      % (destinazione.name, url, atteso_byte))
                f.write(pezzo)
                h.update(pezzo)
                byte += len(pezzo)
            f.flush()
            os.fsync(f.fileno())
    except Rifiuto as e:
        _elimina_temporaneo(dir_fd, temporaneo)
        raise Rifiuto("%s. Il file parziale e' stato CANCELLATO." % e) from None
    except Exception as e:
        _elimina_temporaneo(dir_fd, temporaneo)
        raise Rifiuto("scaricamento fallito (%s): %s: %s"
                      % (url, type(e).__name__, e)) from None
    letto = h.hexdigest()
    if letto != atteso_sha or byte != atteso_byte:
        _elimina_temporaneo(dir_fd, temporaneo)
        raise Rifiuto("%s scaricato da %s non combacia: sha256 %s (%d B), atteso %s (%d B). "
                      "Il file e' stato CANCELLATO."
                      % (destinazione.name, url, letto, byte, atteso_sha, atteso_byte))
    try:
        os.replace(temporaneo, destinazione.name,
                   src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
    except OSError as e:
        _elimina_temporaneo(dir_fd, temporaneo)
        raise Rifiuto("pubblicazione sicura di %s fallita: %s" % (destinazione.name, e)) from None
    return {"nome": destinazione.name, "url": url, "sha256": letto, "byte": byte}


def scarica(destinazione, lingue=None, pin: dict | None = None, url_base=None,
            apri=None, forza: bool = False, *, orologio=time.monotonic, container=None) -> dict:
    pin = pin or carica_pin()
    if pin.get('container_delivery'):
        return _scarica_contenitore(destinazione, lingue, pin, url_base, apri, container, orologio)
    esigi(container is None, '--container richiede un pin con consegna ZIP autenticata')
    apri = apri or _apri
    radice = (url_base or pin["url_base"])
    if not radice.endswith("/"):
        radice += "/"
    lingue = tuple(lingue) if lingue else tuple(pin["basi"])
    for l in lingue:
        esigi(l in pin["basi"], "lingua %r non nel pin (ci sono: %s)"
              % (l, ", ".join(sorted(pin["basi"]))))
    cartella, dir_fd = _apri_cartella_privata(destinazione)
    inizio = orologio()
    try:
        testo = _testo(radice + SHA256SUMS, apri, orologio=orologio, inizio=inizio)
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
            presente = _sha_regolare(dir_fd, d["nome"])
            if (presente == (d["sha256"], d["byte"]) and not forza):
                fatti.append({"lingua": l, "esito": "gia presente", "nome": d["nome"],
                              "sha256": d["sha256"], "byte": d["byte"]})
                continue
            # Senza `--url-base` vale l'URL scritto nel pin, che e' quello che si
            # legge in `base11.json`; con `--url-base` (specchio o server di prova)
            # vale la radice data piu' il nome del pin.
            url = d["url"] if url_base is None else radice + d["nome"]
            fatti.append({"lingua": l, "esito": "scaricato",
                          **_scarica_file(url, bersaglio, d["sha256"], d["byte"],
                                          apri, dir_fd, orologio=orologio, inizio=inizio)})
        _scrivi_atomico(dir_fd, SHA256SUMS_DEPOSITO, testo.encode("utf-8"))
        return {"destinazione": str(cartella), "url_base": radice, "file": fatti,
                "sha256sums": str(cartella / SHA256SUMS_DEPOSITO)}
    finally:
        os.close(dir_fd)


def _scarica_contenitore(destinazione, lingue, pin, url_base, apri, container, orologio):
    """The current single ZIP retains both immutable stage-zero deltas."""
    from distribution.download_inputs import fetch_inputs, load_delivery
    lingue = tuple(lingue) if lingue else tuple(pin['basi'])
    esigi(lingue and len(set(lingue)) == len(lingue)
          and all(l in pin['basi'] for l in lingue), 'lingue ZIP non valide o duplicate')
    try:
        delivery = load_delivery(Path(__file__).resolve().parent / pin['container_delivery'])
        names = []
        members = {row['name']: row for row in delivery['files']}
        for lingua in lingue:
            delta = pin['basi'][lingua]['delta']
            row = members.get(delta['nome'], {})
            esigi((row.get('sha256'), row.get('bytes')) == (delta['sha256'], delta['byte']),
                  'il pin ZIP cambia il delta storico ' + delta['nome'])
            names.append(delta['nome'])
        override = (url_base.rstrip('/') + '/' + delivery['url'].rsplit('/', 1)[-1]
                    if url_base is not None else None)
        rows = fetch_inputs(destinazione, delivery, names, container=container, opener=apri,
                            url_override=override, clock=orologio)
        testo = ''.join(row['sha256'] + '  ' + row['name'] + '\n' for row in rows)
        cartella, directory = _apri_cartella_privata(destinazione)
        try:
            _scrivi_atomico(directory, SHA256SUMS_DEPOSITO, testo.encode())
        finally:
            os.close(directory)
        return dict(destinazione=str(cartella), url_base=override or delivery['url'],
                    file=[dict(lingua=lingua, nome=row['name'], sha256=row['sha256'], byte=row['bytes'],
                               esito='gia presente' if row['status']=='present' else 'scaricato')
                          for lingua, row in zip(lingue, rows)],
                    sha256sums=str(cartella / SHA256SUMS_DEPOSITO))
    except (ValueError, OSError) as exc:
        raise Rifiuto('consegna ZIP autenticata rifiutata: ' + str(exc)) from None


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
    ap.add_argument('--container', type=Path,
                    help='usa lo ZIP giocatore gia scaricato, verificandone hash e membri')
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    try:
        rapporto = scarica(a.destinazione, a.lingua, url_base=a.url_base, forza=a.forza, container=a.container)
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
