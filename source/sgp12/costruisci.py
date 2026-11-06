#!/usr/bin/env python3
"""sgp12.costruisci — UN comando per costruire la ROM Sacred Gold Plus 1.2.5
dalla propria HeartGold ORIGINALE.

    stadio 0: HeartGold originale --(delta xdelta pubblico)--> base 1.1
    poi i diciannove stadi:
    riserva -> camera -> plus+chunk -> testi -> npc -> anim -> opzioni -> wifi
    -> titolo -> credito -> guida -> caramelle -> borsa -> anim2 -> borsa_lotta -> squadra_lotta -> capacita_borsa -> manutenzione -> versione

Uso:
    python3 -m sgp12.costruisci --base "Pokemon - HeartGold Version.nds" \\
            --uscita sgp-1.2.5-EN.nds
    python3 -m sgp12.costruisci --base "Pokemon - Versione Oro HeartGold.nds" \\
            --uscita sgp-1.2.5-IT.nds

`--base` e' la HeartGold originale: la lingua si DEDUCE dal suo sha256 (pin
`base11.json`) e, se `--lingua` c'e', deve coincidere. Lo stadio 0 cerca il
delta in `--delta`, altrimenti in `$SGP_ROM_DIR` col nome del pin
(`python3 -m sgp12.scarica_base --destinazione "$SGP_ROM_DIR"` lo scarica).
Serve `xdelta3` nel PATH. Se `--base` e' invece una base 1.1 gia' pronta, lo
stadio 0 si salta con un avviso.

`--build` (default: `sgp12/build/`) e' la cartella con i blob gia' validati di
ogni blocco (vedi README.md per la mappa) e `MAPPA-RISERVA-ARM9.json`.

Richiede `ndspy` (`source/requirements.txt`): riserva, plus e testi lo usano.
La ROM di partenza sta in una cartella privata, fuori da questo repository,
e si passa con `--base`. Nessuna ROM e' distribuita da questo repository.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import time
import unicodedata
import uuid
from pathlib import Path

from . import manutenzione, versione
from .rom import Rifiuto, prepara_base, sha
from .blocchi import (riserva, camera, plus_chunk, testi, npc, anim, opzioni, wifi,
                      titolo, guida, caramelle, borsa, anim2, borsa_lotta, squadra_lotta, capacita_borsa)

BUILD_DEFAULT = Path(__file__).resolve().parent / "build"
BLOCK_NAMES = ("riserva", "camera", "plus_chunk", "testi", "npc", "anim",
               "opzioni", "wifi", "titolo", "credito", "guida", "caramelle",
               "borsa", "anim2", "borsa_lotta", "squadra_lotta",
               "capacita_borsa", "manutenzione", "versione")


def _open_directory(path, *, create, require_private):
    original = Path(path).absolute()
    if original.is_symlink():
        raise Rifiuto('directory di output symlink')
    # macOS espone /tmp e /var come alias di sistema. Si normalizza una volta,
    # poi l'attraversamento effettivo resta descriptor-bound e no-follow.
    absolute = original.resolve(strict=False)
    parts = absolute.parts
    fd = os.open(parts[0], os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts[1:]:
            flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, 'O_NOFOLLOW', 0)
            try:
                child = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, 0o700, dir_fd=fd)
                child = os.open(part, flags, dir_fd=fd)
                os.fchmod(child, 0o700)
            os.close(fd)
            fd = child
        info = os.fstat(fd)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
                or (require_private and info.st_mode & 0o077)):
            raise Rifiuto('directory di output non privata o non posseduta')
        return fd
    except Exception:
        os.close(fd)
        raise


def _lstat_at(fd, name):
    try:
        return os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return None


class _PrivateDirectory:
    def __init__(self, path, *, require_private=False):
        original = Path(path).absolute()
        self.fd = _open_directory(original, create=True, require_private=require_private)
        self.path = original.resolve(strict=False)

    @property
    def identity(self):
        info = os.fstat(self.fd)
        return info.st_dev, info.st_ino

    @staticmethod
    def normalized_name(name):
        return unicodedata.normalize('NFD', name).casefold()

    def require_absent(self, name):
        if not name or '/' in name or name in ('.', '..'):
            raise Rifiuto('nome output non portabile')
        if _lstat_at(self.fd, name) is not None:
            raise Rifiuto('output gia presente: ' + str(self.path / name))

    def publish(self, name, data):
        self.require_absent(name)
        temporary = '.' + name + '.' + uuid.uuid4().hex
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(temporary, flags, 0o600, dir_fd=self.fd)
        linked = False
        temporary_info = None
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError('scrittura output incompleta')
                view = view[written:]
            os.fsync(fd)
            temporary_info = os.fstat(fd)
            if (not stat.S_ISREG(temporary_info.st_mode)
                    or temporary_info.st_uid != os.getuid()
                    or temporary_info.st_nlink != 1
                    or temporary_info.st_mode & 0o077):
                raise Rifiuto('temporaneo output con identita o permessi inattesi')
        except Exception:
            try:
                os.unlink(temporary, dir_fd=self.fd)
            except FileNotFoundError:
                pass
            os.fsync(self.fd)
            raise
        finally:
            os.close(fd)
        try:
            try:
                os.link(temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd,
                        follow_symlinks=False)
            except FileExistsError as exc:
                raise Rifiuto('output apparso durante la pubblicazione: '
                              + str(self.path / name)) from exc
            linked = True
            info = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or info.st_nlink != 2 or info.st_mode & 0o077
                    or (info.st_dev, info.st_ino) !=
                       (temporary_info.st_dev, temporary_info.st_ino)):
                raise Rifiuto('output pubblicato con identita o permessi inattesi')
        finally:
            try:
                os.unlink(temporary, dir_fd=self.fd)
            except FileNotFoundError:
                pass
            if linked:
                final = _lstat_at(self.fd, name)
                valid = (final is not None and stat.S_ISREG(final.st_mode)
                         and final.st_uid == os.getuid() and final.st_nlink == 1
                         and not final.st_mode & 0o077
                         and (final.st_dev, final.st_ino) ==
                             (temporary_info.st_dev, temporary_info.st_ino))
                if not valid:
                    if (final is not None and (final.st_dev, final.st_ino) ==
                            (temporary_info.st_dev, temporary_info.st_ino)):
                        os.unlink(name, dir_fd=self.fd)
                    raise Rifiuto('output finale con identita o permessi inattesi')
            os.fsync(self.fd)

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class _PrivateTarget:
    def __init__(self, path):
        path = Path(path).absolute()
        if path.name in ('', '.', '..'):
            raise Rifiuto('percorso output non valido')
        self.directory = _PrivateDirectory(path.parent)
        self.name = path.name
        try:
            self.directory.require_absent(self.name)
        except Exception:
            self.directory.close()
            raise

    @property
    def key(self):
        return self.directory.identity, self.directory.normalized_name(self.name)

    def publish(self, data):
        self.directory.publish(self.name, data)

    def close(self):
        self.directory.close()


def costruisci(base: bytes, lingua: str, build_dir: Path,
               log_dir: Path | _PrivateDirectory | None = None) -> tuple[bytes, dict]:
    if log_dir is not None and not isinstance(log_dir, _PrivateDirectory):
        owned = _PrivateDirectory(log_dir, require_private=True)
        try:
            return costruisci(base, lingua, build_dir, owned)
        finally:
            owned.close()
    build_dir = Path(build_dir)
    manifest = build_dir / "riserva" / "MAPPA-RISERVA-ARM9.json"
    passi = []
    log_sink = log_dir
    if log_sink:
        for index, name in enumerate(BLOCK_NAMES, 1):
            log_sink.require_absent("%02d-%s.json" % (index, name))
            log_sink.require_absent("%02d-%s.nds" % (index, name))

    def registra(nome, t0, out, extra=None):
        passi.append({"blocco": nome, "secondi": round(time.time() - t0, 2),
                      "sha256": sha(out), "bytes": len(out), **(extra or {})})
        if log_sink:
            log_sink.publish(
                "%02d-%s.json" % (len(passi), nome),
                (json.dumps(passi[-1], indent=2, ensure_ascii=False) + "\n").encode())
            # ROM intermedia: serve a `verifica.py` per i rilettori pensati
            # per un confronto PASSO-PASSO (base immediatamente precedente),
            # non contro la ROM finale con tutti i blocchi applicati.
            log_sink.publish("%02d-%s.nds" % (len(passi), nome), out)

    rom = base
    t0 = time.time()
    rom, _ = riserva.applica(rom, build_dir / "riserva", etichetta=lingua)
    registra("riserva", t0, rom)

    t0 = time.time()
    rom, _ = camera.applica(rom)
    registra("camera", t0, rom)

    t0 = time.time()
    rom, _ = plus_chunk.applica(rom, build_dir, manifest_path=manifest)
    registra("plus_chunk", t0, rom)

    t0 = time.time()
    rom, rep_testi = testi.applica(rom, build_dir / "testi", lingua)
    # A3 della revisione R1: `narc_modificato` da solo non distingue «tutte le
    # correzioni applicate» da «una sola applicata e 234 rifiutate». Il blocco
    # ora RIFIUTA in quei casi (vedi `blocchi/testi.py`); qui si registrano i
    # conteggi, cosi' il log dice quante regole sono passate davvero.
    registra("testi", t0, rom, {
        "narc_modificato": rep_testi.get("narc_modificato"),
        "righe_in_perimetro": rep_testi.get("righe_totali_in_perimetro"),
        "conteggi_esito": rep_testi.get("conteggi_esito"),
        "regole_ricostruite": (rep_testi.get("correzioni_ricostruite") or {}).get("ricostruite"),
    })

    t0 = time.time()
    rom, _ = npc.applica(rom, build_dir / "npc", manifest_path=manifest, attivo=1, tetto=1)
    registra("npc", t0, rom)

    t0 = time.time()
    rom, _ = anim.applica(rom, build_dir / "anim", manifest_path=manifest, flags=0)
    registra("anim", t0, rom)

    t0 = time.time()
    rom, _ = opzioni.applica(rom, build_dir / "opzioni", lingua=lingua, manifest_path=manifest)
    registra("opzioni", t0, rom)

    t0 = time.time()
    rom, _ = wifi.applica(rom, build_dir / "wifi", manifest_path=manifest)
    registra("wifi", t0, rom)

    t0 = time.time()
    rom, _ = titolo.applica(rom)
    registra("titolo", t0, rom)

    t0 = time.time()
    rom, _ = titolo.applica_credito(rom)
    registra("credito", t0, rom)

    t0 = time.time()
    rom, _ = guida.applica(rom)
    registra("guida", t0, rom)

    # Il blocco deve essere ancora a zero nella riserva.
    t0 = time.time()
    rom, _ = caramelle.applica(rom, build_dir / "caramelle", manifest_path=manifest)
    registra("caramelle", t0, rom)

    t0 = time.time()
    rom, _ = borsa.applica(rom, build_dir / "borsa", lingua,
                           manifest_path=manifest)
    registra("borsa", t0, rom)

    t0 = time.time()
    rom, _ = anim2.applica(rom, build_dir / "anim2", manifest_path=manifest)
    registra("anim2", t0, rom)

    t0 = time.time()
    rom, _ = borsa_lotta.applica(rom, build_dir / "borsa_lotta", manifest_path=manifest)
    registra("borsa_lotta", t0, rom)

    t0 = time.time()
    rom, _ = squadra_lotta.applica(rom, build_dir / "squadra_lotta", manifest_path=manifest)
    registra("squadra_lotta", t0, rom)

    t0 = time.time()
    rom, _ = capacita_borsa.applica(rom, build_dir / "capacita_borsa", manifest_path=manifest)
    registra("capacita_borsa", t0, rom)

    t0 = time.time()
    rom, _ = manutenzione.applica(rom, build_dir / "manutenzione")
    registra("manutenzione", t0, rom)

    t0 = time.time()
    rom, _ = versione.applica(rom)
    registra("versione", t0, rom)

    return rom, {"lingua": lingua, "base_sha256": sha(base), "uscita_sha256": sha(rom),
                "uscita_bytes": len(rom), "passi": passi}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True,
                    help="la HeartGold ORIGINALE (US o IT); una base 1.1 e' accettata e salta lo stadio 0")
    ap.add_argument("--uscita", required=True)
    ap.add_argument("--lingua", choices=("EN", "IT"),
                    help="facoltativa: dedotta dallo sha256 di --base, e se data deve coincidere")
    ap.add_argument("--delta", default=None,
                    help="il delta dello stadio 0; senza, cercato in $SGP_ROM_DIR col nome del pin")
    ap.add_argument("--build", default=str(BUILD_DEFAULT))
    ap.add_argument("--log-dir", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    resources = []
    try:
        output_target = _PrivateTarget(a.uscita)
        resources.append(output_target)
        report_target = _PrivateTarget(a.json) if a.json else None
        if report_target:
            resources.append(report_target)
        log_sink = (_PrivateDirectory(a.log_dir, require_private=True)
                    if a.log_dir else None)
        if log_sink:
            resources.append(log_sink)

        keys = [output_target.key]
        if report_target:
            keys.append(report_target.key)
        if log_sink:
            for index, name in enumerate(BLOCK_NAMES, 1):
                for suffix in ('json', 'nds'):
                    filename = "%02d-%s.%s" % (index, name, suffix)
                    log_sink.require_absent(filename)
                    keys.append((log_sink.identity, log_sink.normalized_name(filename)))
        if len(keys) != len(set(keys)):
            raise Rifiuto('collisione fra output, report e log intermedi')

        # Stadio 0 parte solo dopo il preflight di tutti i target. I descriptor
        # delle directory restano aperti fino alla pubblicazione finale.
        base, stadio0 = prepara_base(Path(a.base), a.lingua, a.delta)
        lingua = stadio0["lingua"]
        if stadio0.get("avviso"):
            print(stadio0["avviso"], file=sys.stderr)
        else:
            print("STADIO 0: %s -> %s (delta %s, %.2f s)"
                  % (stadio0["base_originale"]["nome"], stadio0["base_1_1"]["nome"],
                     stadio0["delta"]["nome"], stadio0["secondi"]), file=sys.stderr)

        rom, rapporto = costruisci(base, lingua, Path(a.build), log_sink)
        rapporto = {"stadio0": stadio0, **rapporto}
        testo = json.dumps(rapporto, indent=2, ensure_ascii=False) + "\n"
        output_target.publish(rom)
        if report_target:
            report_target.publish(testo.encode())
    except Rifiuto as e:
        print("RIFIUTO: %s" % e, file=sys.stderr)
        return 2
    finally:
        for resource in reversed(resources):
            resource.close()

    print(testo)
    print("COSTRUITA %s  sha256 %s" % (a.uscita, rapporto["uscita_sha256"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
