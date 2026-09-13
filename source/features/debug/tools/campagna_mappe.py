#!/usr/bin/env python3
"""Gate C1 — un warp per mappa, su due ROM, e il confronto dei fotogrammi.

Per ogni mappa bersaglio esegue `warp.py` sulla ROM base e sulla candidata, con lo STESSO
fotogramma di gioco di iniezione (`--fotogramma-iniezione`), cosi' le due corse sono
confrontabili pixel per pixel: ogni differenza e' attribuibile alla ROM, non al momento.

    python3 campagna_mappe.py --hg BIN --base ROM --cand ROM --out DIR --json F
"""
import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import zlib
from pathlib import Path

QUI = Path(__file__).resolve().parent

# (mappa, warpId, che cosa ci si aspetta dal confronto base/candidata, perche')
BERSAGLI = [
    (116, 0, "diversi", "Mogania, negozio souvenir: base=Plus 11, candidata=nativo 4"),
    (247, 0, "diversi", "covo Rocket B1F: base=Plus 11, candidata=nativo 4"),
    (248, 0, "diversi", "covo Rocket B2F: base=Plus 11, candidata=nativo 4"),
    (249, 0, "diversi", "covo Rocket B3F: base=Plus 11, candidata=nativo 4"),
    (119, 0, "diversi", "Monte Scodella 1F ingresso: base=Plus 11, candidata=nativo 0"),
    (250, 0, "diversi", "Monte Scodella 1F retro: base=Plus 11, candidata=nativo 0"),
    (251, 0, "diversi", "Monte Scodella 2F: base=Plus 11, candidata=nativo 0"),
    (252, 0, "diversi", "Monte Scodella B1F: base=Plus 11, candidata=nativo 0"),
    # controlli che possono fallire
    (61, 0, "uguali", "CONTROLLO: laboratorio di Elm, mappa NON in tabella: deve restare identica"),
    (226, 0, "uguali", "CONTROLLO: Olivine PC 1F, eccezione storica con lo stesso valore "
                       "(4) su base e candidata: deve restare identica"),
]


def ppm_png(src, dst):
    d = Path(src).read_bytes()
    i = d.index(b"255\n") + 4
    px, w, h = d[i:], 256, 384
    raw = b"".join(b"\x00" + px[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(t, data):
        c = t + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))
    Path(dst).write_bytes(b"\x89PNG\r\n\x1a\n"
                          + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                          + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def misura(src):
    """leggibilita' del fotogramma, in numeri: schermo SUPERIORE (256x192)"""
    d = Path(src).read_bytes()
    i = d.index(b"255\n") + 4
    top = d[i:i + 256 * 192 * 3]
    colori = len(set(top[j:j + 3] for j in range(0, len(top), 3)))
    med = sum(top) / len(top)
    var = sum((b - med) ** 2 for b in top) / len(top)
    return {"colori_distinti": colori, "media": round(med, 2), "dev": round(var ** 0.5, 2)}


def confronta(a, b):
    da, db = Path(a).read_bytes(), Path(b).read_bytes()
    ia, ib = da.index(b"255\n") + 4, db.index(b"255\n") + 4
    ta, tb = da[ia:ia + 256 * 192 * 3], db[ib:ib + 256 * 192 * 3]
    diversi = sum(1 for j in range(0, len(ta), 3) if ta[j:j + 3] != tb[j:j + 3])
    dist = sum(abs(x - y) for x, y in zip(ta, tb)) / len(ta)
    return {"sha_uguali": hashlib.sha256(da).hexdigest() == hashlib.sha256(db).hexdigest(),
            "pixel_diversi_schermo_alto": diversi,
            "percento": round(100.0 * diversi / (256 * 192), 2),
            "distanza_media_per_canale": round(dist, 3)}


def corsa(args, rom, etichetta, mappa, warp, porta):
    out = Path(args.out) / f"{etichetta}-{mappa}"
    out.mkdir(parents=True, exist_ok=True)
    sram = Path(args.out) / f"sav-{etichetta}-{mappa}.sav"
    sram.write_bytes(Path(args.sram).read_bytes())
    js = out / "warp.json"
    cmd = [sys.executable, str(QUI / "warp.py"), "--hg", args.hg, "--rom", rom,
           "--sram", str(sram), "--out", str(out), "--script", args.script,
           "--mappa", str(mappa), "--warp", str(warp), "--porta", str(porta),
           "--attesa-prologo", str(args.attesa_prologo),
           "--fotogramma-iniezione", str(args.fotogramma),
           "--json", str(js)]
    if args.aggancio:
        cmd += ["--aggancio", args.aggancio]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        return json.loads(js.read_text()), out
    except Exception as e:
        return {"fine_sessione": f"json illeggibile: {e}"}, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--etichetta-cand", default="cand")
    ap.add_argument("--sram", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--aggancio", default=None)
    ap.add_argument("--fotogramma", type=int, default=3400)
    ap.add_argument("--attesa-prologo", type=float, default=8.0)
    ap.add_argument("--porta0", type=int, default=3500)
    ap.add_argument("--solo", default=None, help="lista di mappe separate da virgola")
    a = ap.parse_args()

    solo = {int(x) for x in a.solo.split(",")} if a.solo else None
    os.makedirs(a.out, exist_ok=True)
    esito = {"base": os.path.basename(a.base), "candidata": os.path.basename(a.cand),
             "fotogramma_iniezione": a.fotogramma, "aggancio": a.aggancio, "mappe": []}
    porta = a.porta0
    for mappa, warp, atteso, perche in BERSAGLI:
        if solo and mappa not in solo:
            continue
        riga = {"mappa": mappa, "warpId": warp, "atteso": atteso, "perche": perche}
        for etichetta, rom in (("base", a.base), (a.etichetta_cand, a.cand)):
            j, out = corsa(a, rom, etichetta, mappa, warp, porta)
            porta += 1
            riga[etichetta] = {
                "mappa_raggiunta": j.get("mappa_raggiunta"),
                "rc": j.get("rc_hg_runtime"),
                "fine": j.get("fine_sessione"),
                "assestata": j.get("assestata"),
                "dir": str(out),
            }
            f = out / "01-dopo-warp.ppm"
            if f.exists():
                riga[etichetta]["leggibilita"] = misura(f)
                ppm_png(f, out / "01-dopo-warp.png")
            f2 = out / "02-dopo-cammino.ppm"
            if f2.exists():
                ppm_png(f2, out / "02-dopo-cammino.png")
        fa = Path(riga["base"]["dir"]) / "01-dopo-warp.ppm"
        fb = Path(riga[a.etichetta_cand]["dir"]) / "01-dopo-warp.ppm"
        if fa.exists() and fb.exists():
            riga["confronto"] = confronta(fa, fb)
            uguali = riga["confronto"]["sha_uguali"]
            riga["verdetto"] = "VERDE" if ((atteso == "uguali") == uguali) else "ROSSO"
        else:
            riga["verdetto"] = "NON MISURATO"
        esito["mappe"].append(riga)
        print(f"mappa {mappa:3d}  atteso={atteso:8s}  verdetto={riga['verdetto']}  "
              f"confronto={riga.get('confronto')}", flush=True)
    Path(a.json).write_text(json.dumps(esito, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
