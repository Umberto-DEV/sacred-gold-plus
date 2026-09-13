#!/usr/bin/env python3
"""Verifica statica delle ancore del warp nella ROM 1.1 (nessun byte di gioco stampato
oltre al disassemblato delle funzioni indicate, che e' codice, non contenuto).

Controlla che gli indirizzi che `pret/pokeheartgold` da' per HeartGold US valgano anche
sulla ROM Plus 1.1 EN, e ricava i puntatori globali che servono all'iniezione:

  * sub_02053E08(FieldSystem*, mapId, warpId)  -> crea il task di cambio mappa
  * sub_020538C0(FieldSystem*, mapId, warpId, x, y, dir)
  * sub_0203E2F4 / sub_0203E30C                -> contengono il letterale sFieldSysPtr
  * FieldSystem_TaskIsRunning / FieldSystem_RunTaskFrame: non cercati per nome

Uso: python3 ancore_warp.py <rom.nds> [--json out.json]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "SGP-1.2-CAMERA-01" / "tools"))
from arm9 import Arm9                                    # noqa: E402
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM   # noqa: E402

FUNZIONI = {
    "sub_02053E08": 0x02053E08,
    "sub_020538C0": 0x020538C0,
    "sub_020537A8": 0x020537A8,
    "sub_02052F94": 0x02052F94,
    "sub_0203E2F4": 0x0203E2F4,
    "sub_0203E30C": 0x0203E30C,
    "sub_0203DF34": 0x0203DF34,
    "MapHeader_GetCameraType": 0x0203B400,     # ancora gia' verificata da SGP-1.2-CAMERA-01
}


def dis(r, addr, n, thumb=True):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    md.detail = False
    dati = r.leggi(addr, n)
    return [(i.address, i.mnemonic, i.op_str) for i in md.disasm(dati, addr)]


def pool(r, addr, n):
    """parole del pool letterale nella finestra data (candidati puntatori a RAM)"""
    out = []
    for a in range(addr, addr + n, 4):
        try:
            v = r.u32(a)
        except KeyError:
            continue
        if 0x02000000 <= v < 0x02400000 or 0x027E0000 <= v < 0x02800000:
            out.append((a, v))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--json")
    ap.add_argument("--righe", type=int, default=30)
    a = ap.parse_args()
    r = Arm9(a.rom)
    esito = {"rom": str(Path(a.rom).name), "funzioni": {}}
    for nome, ind in FUNZIONI.items():
        try:
            righe = dis(r, ind, a.righe * 2)
        except KeyError as e:
            esito["funzioni"][nome] = {"indirizzo": "0x%08X" % ind, "errore": str(e)}
            print("%-26s 0x%08X  FUORI SEGMENTO" % (nome, ind))
            continue
        testo = ["0x%08X  %s %s" % (x[0], x[1], x[2]) for x in righe]
        esito["funzioni"][nome] = {
            "indirizzo": "0x%08X" % ind,
            "thumb": testo,
            "pool": ["0x%08X -> 0x%08X" % p for p in pool(r, ind, a.righe * 2)],
        }
        print("== %s @ 0x%08X" % (nome, ind))
        for t in testo[:a.righe]:
            print("   " + t)
        print()
    if a.json:
        Path(a.json).write_text(json.dumps(esito, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
