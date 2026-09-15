#!/usr/bin/env python3
"""Rilettore indipendente del gancio ``sgp.squadra_lotta``.

Usa il decoder BLZ in avanti del rilettore anim, senza importare o chiamare
l'applicatore. API: ``rileggi(prima: bytes, dopo: bytes, build_dir)``.
"""
import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path


QUI = Path(__file__).resolve().parent
REPO = QUI.parents[3]
sys.path.insert(0, str(REPO / "source/features/anim/tools"))
from rileggi_anim4 import Arm9RO, tabelle, leggi_overlay, immagine_overlay  # noqa: E402


BASE, N_BLOCCO = 0x023DBE00, 0x100
MAX_CODICE, OFF_CANARINO, N_CANARINO = 0xF0, 0xF0, 16
OVERLAY = 8
HOOKS = [{'overlay': 8, 'sito': '0x221d3de', 'pre': '55f6a5ff', 'bersaglio': 'sgp_squadra_pp_hook'}, {'overlay': 8, 'sito': '0x221d3e8', 'pre': '55f694ff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d3f2', 'pre': '55f68fff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d3fc', 'pre': '55f68aff', 'bersaglio': 'sgp_squadra_attr_hook'}, {'overlay': 8, 'sito': '0x221d406', 'pre': '55f685ff', 'bersaglio': 'sgp_squadra_attr_hook'}]
SYMBOLS = ('sgp_squadra_attr_cache', 'sgp_squadra_attr_hook', 'sgp_squadra_pp_cache', 'sgp_squadra_pp_hook')
CANARINO_FISSO = b"".join(struct.pack("<I", 0xCA5A1A00 | i) for i in range(4))


def sha(dati):
    return hashlib.sha256(bytes(dati)).hexdigest()


def posizioni_diverse(a, b):
    n = min(len(a), len(b))
    diverse = []
    passo = 1 << 20
    for inizio in range(0, n, passo):
        fine = min(inizio + passo, n)
        if a[inizio:fine] != b[inizio:fine]:
            diverse.extend(i for i in range(inizio, fine) if a[i] != b[i])
    diverse.extend(range(n, max(len(a), len(b))))
    return diverse


def bersaglio_bl(sito, dati):
    if len(dati) != 4:
        return None
    hi, lo = struct.unpack("<HH", bytes(dati))
    if (hi & 0xF800) != 0xF000 or (lo & 0xF800) != 0xF800:
        return None
    delta = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if delta & (1 << 22):
        delta -= 1 << 23
    return (sito + 4 + delta) & 0xFFFFFFFF


def _arm9(raw):
    td = tempfile.TemporaryDirectory(prefix="squadra-lotta-ro-")
    p = Path(td.name) / "rom.nds"
    p.write_bytes(raw)
    return td, Arm9RO(p)


def _rosso_malformato(exc):
    return {
        "esito_finale": "ROSSO",
        "cancelli": [{"cancello": "M0", "esito": "ROSSO",
                      "dettaglio": "input o bundle malformato: %s" % exc}],
    }


def _rileggi(prima, dopo, build_dir):
    prima, dopo = bytes(prima), bytes(dopo)
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()

    esiti = []

    def ck(nome, ok, dettaglio):
        esiti.append({"cancello": nome, "esito": "verde" if ok else "ROSSO",
                      "dettaglio": dettaglio})

    forma = (man.get("base") == "0x023dbe00" and
             man.get("blocco_byte") == N_BLOCCO and
             man.get("canarino_offset") == OFF_CANARINO and
             isinstance(man.get("blob"), dict) and
             man["blob"].get("byte") == len(blob) and
             man["blob"].get("sha256") == sha(blob) and
             isinstance(man.get("canarino"), dict) and
             man["canarino"].get("byte") == len(canarino) and
             man["canarino"].get("sha256") == sha(canarino) and
             man.get("ganci") == HOOKS and
             isinstance(man.get("simboli"), dict) and
             set(man["simboli"]) == set(SYMBOLS))
    ck("B0", forma, "forma e impronte del bundle")

    simboli = {nome: int(man["simboli"][nome], 16)
               for nome in SYMBOLS}
    simboli_ok = all((valore & 1) == 1 and
                     BASE <= (valore & ~1) < BASE + len(blob)
                     for valore in simboli.values())
    ck("B1", len(blob) <= MAX_CODICE and simboli_ok,
       "blob %d/%d B; simboli Thumb interni" % (len(blob), MAX_CODICE))
    ck("B2", canarino == CANARINO_FISSO and len(canarino) == N_CANARINO,
       "canarino fisso sha256 " + sha(canarino))

    td0, arm0 = _arm9(prima)
    td1, arm1 = _arm9(dopo)
    try:
        zona0 = arm0.leggi(BASE, N_BLOCCO)
        zona1 = arm1.leggi(BASE, N_BLOCCO)
        ck("L0", zona0 == bytes(N_BLOCCO), "blocco di ingresso vergine")
        immagine_attesa = blob + bytes(OFF_CANARINO - len(blob)) + canarino
        ck("L1", zona1 == immagine_attesa,
           "intero blocco: codice, margine zero e canarino")

        stessa_arm9 = (arm0.off9 == arm1.off9 and arm0.siz9 == arm1.siz9)
        diff9 = ([i for i in range(arm0.siz9)
                  if arm0.raw[arm0.off9 + i] != arm1.raw[arm1.off9 + i]]
                 if stessa_arm9 else [])
        base_rel = arm0.off(BASE) - arm0.off9
        fuori9 = [i for i in diff9
                  if not base_rel <= i < base_rel + N_BLOCCO]
        ck("L2", stessa_arm9 and not fuori9,
           "%d byte ARM9 diversi; inattesi=%d" % (len(diff9), len(fuori9)))

        ta, tb = tabelle(prima), tabelle(dopo)
        oa, ob = leggi_overlay(prima, ta, OVERLAY), leggi_overlay(dopo, tb, OVERLAY)
        ia, ib = immagine_overlay(prima, oa), immagine_overlay(dopo, ob)
        valid_hooks = True
        finestra = set()
        for hook in HOOKS:
            site = int(hook['sito'], 16)
            off = site - oa['ram']
            pre = bytes.fromhex(hook['pre'])
            native = 0x0207332C if hook['bersaglio'] == 'sgp_squadra_pp_hook' else 0x02073314
            valid_hooks &= (ia[off:off+4] == pre and bersaglio_bl(site, pre) == native
                            and bersaglio_bl(site, ib[off:off+4]) == (simboli[hook['bersaglio']] & ~1))
            finestra.update(range(off, off + 4))
        ck("L3", valid_hooks, "cinque BL native e cache decodificate ai bersagli attesi")

        diffov = ([i for i, (x, y) in enumerate(zip(ia, ib)) if x != y]
                  if len(ia) == len(ib) else [])
        inattesi_ov = [i for i in diffov if i not in finestra]
        ck("L4", len(ia) == len(ib) and 5 <= len(diffov) <= 20 and not inattesi_ov,
           "%d byte overlay decompresso diversi; inattesi=%d"
           % (len(diffov), len(inattesi_ov)))

        inizi = [struct.unpack_from("<I", prima, ta["fat"] + i * 8)[0]
                 for i in range(ta["fat_len"] // 8)]
        successivi = [x for x in inizi if x > oa["inizio"]]
        fine_slot = min(successivi) if successivi else len(prima)
        struttura = (len(prima) == len(dopo) and ta == tb and
                     oa["id"] == ob["id"] == OVERLAY and
                     oa["file_id"] == ob["file_id"] and
                     oa["ram"] == ob["ram"] and
                     oa["ram_size"] == ob["ram_size"] and
                     oa["voce"] == ob["voce"] and
                     oa["fat_voce"] == ob["fat_voce"] and
                     oa["inizio"] == ob["inizio"] and oa["fine"] == ob["fine"])
        coda_ok = (struttura and oa["fine"] <= fine_slot and
                   prima[oa["fine"]:fine_slot] == dopo[oa["fine"]:fine_slot])
        ck("L5", struttura and coda_ok,
           "struttura/FAT stabili; coda FAT %d B intatta"
           % max(0, fine_slot - oa["fine"]))

        leciti = set(range(arm0.off(BASE), arm0.off(BASE) + N_BLOCCO))
        leciti.update(range(oa["inizio"], oa["fine"]))
        leciti.update(range(oa["fat_voce"], oa["fat_voce"] + 8))
        leciti.update(range(oa["voce"] + 28, oa["voce"] + 32))
        diff_file = posizioni_diverse(prima, dopo)
        fuori_file = [i for i in diff_file if i not in leciti]
        ck("L6", struttura and coda_ok and not fuori_file,
           "intero file confinato; byte inattesi=%d" % len(fuori_file))

        verde = all(e["esito"] == "verde" for e in esiti)
        return {"esito_finale": "verde" if verde else "ROSSO",
                "cancelli": esiti, "overlay_byte_diversi": len(diffov),
                "overlay_inattesi": len(inattesi_ov),
                "sha256_prima": sha(prima), "sha256_dopo": sha(dopo)}
    finally:
        td0.cleanup()
        td1.cleanup()


def rileggi(prima, dopo, build_dir):
    try:
        return _rileggi(prima, dopo, build_dir)
    except Exception as exc:
        return _rosso_malformato(exc)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("prima")
    ap.add_argument("dopo")
    ap.add_argument("--build", required=True)
    ap.add_argument("--json")
    args = ap.parse_args()
    risultato = rileggi(Path(args.prima).read_bytes(),
                        Path(args.dopo).read_bytes(), args.build)
    if args.json:
        Path(args.json).write_text(json.dumps(risultato, indent=2,
                                              ensure_ascii=False) + "\n")
    print(json.dumps(risultato, indent=2, ensure_ascii=False))
    return 0 if risultato["esito_finale"] == "verde" else 1


if __name__ == "__main__":
    raise SystemExit(main())
