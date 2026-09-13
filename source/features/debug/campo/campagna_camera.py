#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O4 — GATE-MAPPE a runtime con il warp robusto: base vs candidata, una mappa per volta.

Criteri in `CRITERI.md` §4. Per ogni bersaglio si esegue `warp.py` sulla ROM base e sulla
candidata con lo STESSO `--fotogramma` di iniezione, poi si confrontano i fotogrammi dello
schermo superiore. Una corsa il cui warp non si e' **assestato** non conta (O4.3): e'
esattamente l'errore che ha prodotto D5 (fotogrammi identici fra mappe diverse perche' il
warp non era mai avvenuto).

    campagna_camera.py --hg BIN --base ROM --cand ROM --sram SAV --script S
                       --out DIR --json F [--solo 116,247]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

QUI = Path(__file__).resolve().parent

# (mappa, warpId, atteso, perche') — identici a SGP-1.2-RUNTIME-02/tools/campagna_mappe.py
BERSAGLI = [
    (116, 0, "diversi", "Mogania, negozio souvenir: base=Plus 11, candidata=nativo 4"),
    (247, 0, "diversi", "covo Rocket B1F"),
    (248, 0, "diversi", "covo Rocket B2F"),
    (249, 0, "diversi", "covo Rocket B3F"),
    (119, 0, "diversi", "Monte Scodella 1F ingresso"),
    (250, 0, "diversi", "Monte Scodella 1F retro"),
    (251, 0, "diversi", "Monte Scodella 2F"),
    (252, 0, "diversi", "Monte Scodella B1F"),
    (61, 0, "uguali", "CONTROLLO: laboratorio di Elm, mappa NON in tabella"),
    (226, 0, "uguali", "CONTROLLO: Olivine PC 1F, eccezione con lo stesso valore su entrambe"),
]
SOGLIA_PIXEL = 0.01          # 1 % dei 49152 pixel dello schermo alto (CRITERI.md §4.1)


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


def alto(p):
    d = Path(p).read_bytes()
    i = d.index(b"255\n") + 4
    return d[i:i + 256 * 192 * 3]


def misura(p):
    top = alto(p)
    colori = len({top[j:j + 3] for j in range(0, len(top), 3)})
    med = sum(top) / len(top)
    var = sum((b - med) ** 2 for b in top) / len(top)
    return {"colori_distinti": colori, "media": round(med, 2), "dev": round(var ** 0.5, 2)}


def confronta(a, b):
    ta, tb = alto(a), alto(b)
    diversi = sum(1 for j in range(0, len(ta), 3) if ta[j:j + 3] != tb[j:j + 3])
    dist = sum(abs(x - y) for x, y in zip(ta, tb)) / len(ta)
    return {"sha_alto_uguali": hashlib.sha256(ta).hexdigest() == hashlib.sha256(tb).hexdigest(),
            "pixel_diversi_schermo_alto": diversi,
            "percento": round(100.0 * diversi / (256 * 192), 2),
            "distanza_media_per_canale": round(dist, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hg", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--etichetta-cand", default="sgp-1.2")
    ap.add_argument("--sram", required=True)
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--fotogramma", type=int, default=3600)
    ap.add_argument("--aggancio", default="0x0205C692")
    ap.add_argument("--porta0", type=int, default=4500)
    ap.add_argument("--solo", default=None)
    a = ap.parse_args()

    solo = {int(x) for x in a.solo.split(",")} if a.solo else None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    esito = {"base": Path(a.base).name, "candidata": Path(a.cand).name,
             "fotogramma_iniezione": a.fotogramma, "soglia_pixel_percento": SOGLIA_PIXEL * 100,
             "mappe": []}
    porta = a.porta0
    for mappa, warp, atteso, perche in BERSAGLI:
        if solo and mappa not in solo:
            continue
        riga = {"mappa": mappa, "atteso": atteso, "perche": perche}
        proc = []
        for etichetta, rom in (("base", a.base), (a.etichetta_cand, a.cand)):
            d = out / f"{etichetta}-{mappa}"
            d.mkdir(parents=True, exist_ok=True)
            sav = out / f"sav-{etichetta}-{mappa}.sav"
            shutil.copyfile(a.sram, sav)
            js = d / "warp.json"
            cmd = [sys.executable, str(QUI / "warp.py"), "--hg", a.hg, "--rom", rom,
                   "--sram", str(sav), "--out", str(d), "--script", a.script,
                   "--mappa", str(mappa), "--warp", str(warp), "--porta", str(porta),
                   "--fotogramma", str(a.fotogramma), "--aggancio", a.aggancio,
                   "--json", str(js)]
            porta += 1
            proc.append((etichetta, d, js,
                         subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)))
        for etichetta, d, js, p in proc:
            p.wait()
            try:
                j = json.loads(Path(js).read_text())
            except Exception as e:
                j = {"fine_sessione": f"json illeggibile: {e}"}
            riga[etichetta] = {"assestata": j.get("assestata"),
                               "dopo": j.get("dopo"), "fine": j.get("fine_sessione"),
                               "vblank": j.get("vblank_allineamento"), "dir": str(d)}
            f = d / "01-dopo-warp.ppm"
            if f.exists():
                riga[etichetta]["leggibilita"] = misura(f)
                ppm_png(f, d / "01-dopo-warp.png")
            f2 = d / "02-dopo-cammino.ppm"
            if f2.exists():
                ppm_png(f2, d / "02-dopo-cammino.png")

        fa = Path(riga["base"]["dir"]) / "01-dopo-warp.ppm"
        fb = Path(riga[a.etichetta_cand]["dir"]) / "01-dopo-warp.ppm"
        assestate = bool(riga["base"].get("assestata") and riga[a.etichetta_cand].get("assestata"))
        riga["entrambe_assestate"] = assestate
        if fa.exists() and fb.exists():
            riga["confronto"] = confronta(fa, fb)
        if not assestate:
            riga["verdetto"] = "NON MISURATO (warp non assestato: O4.3)"
        elif "confronto" not in riga:
            riga["verdetto"] = "NON MISURATO (fotogrammi mancanti)"
        elif atteso == "uguali":
            riga["verdetto"] = "VERDE" if riga["confronto"]["sha_alto_uguali"] else "ROSSO"
        else:
            diverso = (not riga["confronto"]["sha_alto_uguali"]
                       and riga["confronto"]["percento"] > SOGLIA_PIXEL * 100)
            riga["verdetto"] = "VERDE" if diverso else "ROSSO"
        esito["mappe"].append(riga)
        print(f"mappa {mappa:3d} atteso={atteso:8s} assestate={assestate} "
              f"verdetto={riga['verdetto']} confronto={riga.get('confronto')}", flush=True)

    bersagli = [r for r in esito["mappe"] if r["atteso"] == "diversi"]
    controlli = [r for r in esito["mappe"] if r["atteso"] == "uguali"]
    esito["riassunto"] = {
        "bersagli_verdi": sum(1 for r in bersagli if r["verdetto"] == "VERDE"),
        "bersagli_totali": len(bersagli),
        "controlli_verdi": sum(1 for r in controlli if r["verdetto"] == "VERDE"),
        "controlli_totali": len(controlli)}
    Path(a.json).write_text(json.dumps(esito, indent=2, ensure_ascii=False))
    print("\nRIASSUNTO", json.dumps(esito["riassunto"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
