#!/usr/bin/env python3
"""Rebuild `CORREZIONI.tsv` from your own ROM and the published edit rules.

The 1.2 text corrections change words inside messages that belong to the game.
The message text itself is therefore **not** in this repository. What is
published is `sgp12/build/testi/REGOLE.json`: for every correction, the message
it belongs to (bank + id), the SHA-256 of the text that must currently be
there, and the minimal edits that turn it into the corrected text. Together
they are enough to rebuild the table `applica_testi.py` consumes, and they
carry no game prose.

    python3 genera_correzioni.py --rom <your rom.nds> --lingua EN \
        --regole ../../sgp12/build/testi/REGOLE.json \
        --pret-source <pret checkout with charmap.txt> \
        --uscita CORREZIONI.tsv

A rule whose SHA-256 does not match the message found in the ROM is reported
and left out: it means that ROM is not the expected base, or the correction is
already applied. `--esigi-tutte` turns that into a non-zero exit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))

from applica_testi import MSG_ARCHIVE, decode_text, load_charmap  # noqa: E402

import ndspy.narc  # noqa: E402
import ndspy.rom  # noqa: E402

sys.path.insert(0, str(QUI.parents[1] / "translation"))
from message_codec import Bank  # noqa: E402


def applica_edit(testo: str, edit) -> str:
    fuori, pos = [], 0
    for i1, i2, nuovo in edit:
        fuori.append(testo[pos:i1])
        fuori.append(nuovo)
        pos = i2
    fuori.append(testo[pos:])
    return "".join(fuori)


def costruisci(rom_bytes: bytes, lingua: str, regole_path: Path, pret_source: Path):
    """Return (rows, report). `rows` are ready for a CORREZIONI.tsv writer."""
    manifesto = json.loads(Path(regole_path).read_text(encoding="utf-8"))
    chars, commands = load_charmap(Path(pret_source))
    rom = ndspy.rom.NintendoDSRom(rom_bytes)
    narc = ndspy.narc.NARC(rom.getFileByName(MSG_ARCHIVE))

    righe, saltate = [], []
    for regola in manifesto["regole"]:
        if regola["lingua"] != lingua:
            continue
        banco, messaggio = int(regola["banco"]), int(regola["id_messaggio"])
        chiave = "%s/%d/%d" % (regola["lingua"], banco, messaggio)
        if not (0 <= banco < len(narc.files)):
            saltate.append({"regola": chiave, "motivo": "banco fuori dal NARC"})
            continue
        try:
            parole = Bank(narc.files[banco]).words
        except ValueError as e:
            saltate.append({"regola": chiave, "motivo": "banco illeggibile: %s" % e})
            continue
        if not (0 <= messaggio < len(parole)):
            saltate.append({"regola": chiave, "motivo": "messaggio fuori dal banco"})
            continue
        attuale, ok = decode_text(parole[messaggio], chars, commands)
        if not ok:
            saltate.append({"regola": chiave, "motivo": "messaggio con codici sconosciuti"})
            continue
        impronta = hashlib.sha256(attuale.encode("utf-8")).hexdigest()
        if impronta != regola["sha256_attuale"]:
            saltate.append({"regola": chiave, "motivo": "impronta diversa: la ROM non e' la base "
                                                       "attesa, o la correzione c'e' gia'"})
            continue
        riga = {k: regola.get(k, "") for k in manifesto["campi_tsv"]}
        riga["testo_attuale"] = attuale
        riga["testo_proposto"] = applica_edit(attuale, regola["edit"])
        riga["variante_corta"] = (applica_edit(attuale, regola["edit_variante_corta"])
                                  if regola.get("edit_variante_corta") else "")
        righe.append(riga)
    return righe, {"lingua": lingua, "ricostruite": len(righe), "saltate": saltate,
                   "regole_totali": len(manifesto["regole"])}


def scrivi_tsv(righe, campi, destinazione: Path) -> None:
    """Scrive il TSV senza quoting: i testi portano `\\n` come due caratteri,
    mai un a capo vero, e nessun campo contiene una tabulazione — la stessa
    forma che `applica_testi.py::load_correzioni` si aspetta."""
    def campo(v):
        v = "" if v is None else str(v)
        if "\t" in v or "\n" in v or "\r" in v:
            raise ValueError("campo non rappresentabile in TSV: %r" % v[:60])
        return v

    with Path(destinazione).open("w", encoding="utf-8", newline="\n") as f:
        f.write("\t".join(campi) + "\n")
        for r in righe:
            f.write("\t".join(campo(r.get(k, "")) for k in campi) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--lingua", required=True, choices=("EN", "IT"))
    ap.add_argument("--regole", type=Path,
                    default=QUI.parents[1] / "sgp12/build/testi/REGOLE.json")
    ap.add_argument("--pret-source", required=True, type=Path)
    ap.add_argument("--uscita", required=True, type=Path)
    ap.add_argument("--esigi-tutte", action="store_true",
                    help="esce diverso da zero se una regola della lingua non e' ricostruita")
    a = ap.parse_args()

    manifesto = json.loads(a.regole.read_text(encoding="utf-8"))
    righe, rapporto = costruisci(a.rom.read_bytes(), a.lingua, a.regole, a.pret_source)
    scrivi_tsv(righe, manifesto["campi_tsv"], a.uscita)
    print(json.dumps(rapporto, indent=2, ensure_ascii=False))
    attese = sum(1 for r in manifesto["regole"] if r["lingua"] == a.lingua)
    return 1 if (a.esigi_tutte and len(righe) != attese) else 0


if __name__ == "__main__":
    raise SystemExit(main())
