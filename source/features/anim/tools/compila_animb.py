#!/usr/bin/env python3
"""SGP-1.2-ANIM-B-02 — compila il blob della FASE 2b (`anim_idle2b.c`) per lo
STESSO blocco VERO della riserva: `sgp.anim`, 1024 B a 0x023D8B00
(`docs/arm9-reserve-reservations.md`: fine 0x023D8F00, "868 B su 1024").

Derivato riga per riga da `compila_anim.py` (fase 2/2a, che RESTA invariato:
compila ancora `anim_blob2.c`). L'UNICA differenza voluta e' il sorgente
compilato: `anim_blob2.c` -> `anim_blob2b.c` (che include `anim_idle2b.c` e
`sgp_anim2b.h`), dove l'abilitazione del task si legge dal chunk di
salvataggio di PLUS-03 (0x023D8716) invece che da `st->flags` scritto
dall'iniettore. Indirizzo di base, offset RELATIVI del layout — codice a
+0x000, canarino a +0x2F0, tabelle a +0x300, stato a +0x340, quattro voci per
lottatore a +0x380, fine a +0x400 — e motivo del canarino sono IDENTICI alla
fase 2/2a: cambiano SOLO i byte del blob compilato (poche istruzioni in piu'
per leggere l'indirizzo assoluto del chunk invece del campo locale).

Uso: compila_animb.py --uscita DIR [--base 0x023D8B00] [--amp ...] [--sca ...]
                                    [--fase ...] [--blink-* ...] [--raro-*...]
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carica_text import load_text  # noqa: E402

SORGENTI = Path(__file__).resolve().parent.parent / "sorgenti"
ENTRATE = ("sgp_idle_task2",)
FASI = 18

# Blocco `sgp.anim`, riservato in docs/arm9-reserve-reservations.md:
# 0x023D8B00, 1024 B, fine (esclusa) 0x023D8F00. Layout identico a fase 1b:
# codice / tabelle / stato / slot; il canarino e' NUOVO qui (dentro il
# margine del codice, non oltre il blocco: la riserva non lascia spazio dopo).
DEF_BASE = 0x023D8B00
OFF_CODICE = 0x000     # fino a 0x2F0: 752 B, blob reale 612 B
OFF_CANARINO = 0x2F0   # 16 B, DENTRO il margine del codice (752..768)
N_CANARINO = 16
OFF_TABELLE = 0x300    # tab_u 32 B + par 32 B
OFF_STATO = 0x340      # 64 B
OFF_SLOT = 0x380       # 4 x 32 B, fino a 0x400
MAX_CODICE = OFF_CANARINO  # 752 B: il blob non deve MAI toccare il canarino
BLOCCO = 0x400          # 1024 B, nessuno spazio libero fuori dal blocco

CANARINO_MOTIVO = 0xCA5A1400  # ...1000 F0, ...1100 CAMERA-01, ...1200 PLUS-02,
                              # ...1300 NPC-02 (canarino.npc): 1400 e' il primo
                              # motivo libero per un canarino DENTRO un blocco.

DEF_AMP = (2, 3, 4, 4)
DEF_SCA = (4, 6, 6, 6)
DEF_FASE = (0, 9, 5, 14)
DEF_BLINK_MIN = 70
DEF_BLINK_MASK = 63
DEF_BLINK_DUR = 2
DEF_RARO_OGNI = 3
DEF_RARO_PIU = 3


def sha(b):
    return hashlib.sha256(b).hexdigest()


def _round_half_away(x):
    return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))


def seno(i):
    return math.sin(math.radians(i * (360.0 / FASI)))


def tabella_u():
    v = [_round_half_away(seno(i) * 16.0) for i in range(FASI)]
    return bytes((x & 0xFF) for x in v) + bytes(32 - FASI), v


def scala_unita(u, k):
    return (u * k + 8) >> 4


def par_bin(amp, sca, fase, blink_min, blink_mask, blink_dur, raro_ogni, raro_piu):
    b = bytearray(32)
    b[0x00:0x04] = bytes(amp)
    b[0x04:0x08] = bytes(sca)
    b[0x08:0x0C] = bytes(fase)
    b[0x0C] = blink_min
    b[0x0D] = blink_mask
    b[0x0E] = blink_dur
    b[0x0F] = raro_ogni
    b[0x10] = raro_piu
    return bytes(b)


def canarino_bin():
    return b"".join(
        (CANARINO_MOTIVO | i).to_bytes(4, "little") for i in range(N_CANARINO // 4)
    )


def quattro(s):
    v = tuple(int(x, 0) for x in s.split(","))
    if len(v) != 4:
        raise argparse.ArgumentTypeError("servono quattro valori separati da virgola")
    return v


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--cc", default="clang")
    ap.add_argument("--opt", default="-Oz")
    ap.add_argument("--base", type=lambda x: int(x, 0), default=DEF_BASE)
    ap.add_argument("--amp", type=quattro, default=DEF_AMP)
    ap.add_argument("--sca", type=quattro, default=DEF_SCA)
    ap.add_argument("--fase", type=quattro, default=DEF_FASE)
    ap.add_argument("--blink-min", type=int, default=DEF_BLINK_MIN)
    ap.add_argument("--blink-mask", type=int, default=DEF_BLINK_MASK)
    ap.add_argument("--blink-dur", type=int, default=DEF_BLINK_DUR)
    ap.add_argument("--raro-ogni", type=int, default=DEF_RARO_OGNI)
    ap.add_argument("--raro-piu", type=int, default=DEF_RARO_PIU)
    args = ap.parse_args()
    out = args.uscita
    out.mkdir(parents=True, exist_ok=True)

    codice = args.base + OFF_CODICE
    canarino = args.base + OFF_CANARINO
    tabelle = args.base + OFF_TABELLE
    stato = args.base + OFF_STATO
    slot = args.base + OFF_SLOT

    comando = [
        args.cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", args.opt,
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-fno-unwind-tables",
        "-fno-asynchronous-unwind-tables", "-fno-jump-tables", "-Wall", "-Wextra",
        f"-DSGP_ANIM2_STATE_ADDR={stato:#x}u",
        f"-DSGP_ANIM2_TAB_ADDR={tabelle:#x}u",
        f"-DSGP_ANIM2_SLOT_ADDR={slot:#x}u",
        "-c", str(SORGENTI / "anim_blob2b.c"), "-o", str(out / "anim_blob2.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (out / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita; vedi compila.log\n" + r.stdout + r.stderr)

    blob, simboli = load_text((out / "anim_blob2.o").read_bytes(), codice, ENTRATE)
    if len(blob) > MAX_CODICE:
        raise SystemExit(f"il blob ({len(blob)} B) non entra nei {MAX_CODICE} B "
                         f"riservati prima del canarino")
    (out / "blob.bin").write_bytes(blob)
    tu, vu = tabella_u()
    pb = par_bin(args.amp, args.sca, args.fase, args.blink_min, args.blink_mask,
                 args.blink_dur, args.raro_ogni, args.raro_piu)
    can = canarino_bin()
    (out / "tab_u.bin").write_bytes(tu)
    (out / "par.bin").write_bytes(pb)
    (out / "canarino.bin").write_bytes(can)

    serie = {str(c): [scala_unita(u, args.amp[c]) for u in vu] for c in range(4)}
    serie_s = {str(c): [scala_unita(u, args.sca[c]) for u in vu] for c in range(4)}

    manifesto = {
        "pacchetto": "SGP-1.2-ANIM-B-02",
        "fase": "2b-chunk-plus03",
        "eredita": "SGP-1.2-ANIM-B-02 fase 2/2a (indirizzi/layout invariati); ""anim_idle2b.c legge l'abilitazione dal chunk PLUS-03 (0x023D8716) invece di st->flags",
        "comando": comando,
        "compilatore": subprocess.run([args.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "indirizzi": {
            "base": hex(args.base), "codice": hex(codice), "canarino": hex(canarino),
            "tabelle": hex(tabelle), "stato": hex(stato), "slot": hex(slot),
            "blocco_byte": BLOCCO,
            "nota": "sgp.anim e' riservato in docs/arm9-reserve-reservations.md "
                    "a 0x023D8B00, 1024 B, fine 0x023D8F00 (il blocco successivo, "
                    "riserva D1, comincia esattamente li': nessuno spazio libero fuori "
                    "dal blocco per un canarino separato, quindi il canarino sta DENTRO, "
                    "nel margine del codice).",
        },
        "blob": {"byte": len(blob), "sha256": sha(blob)},
        "canarino": {"offset": hex(OFF_CANARINO), "byte": N_CANARINO,
                     "motivo": hex(CANARINO_MOTIVO), "sha256": sha(can)},
        "tabelle_bin": {
            "tab_u": {"byte": len(tu), "sha256": sha(tu), "valori": vu},
            "par": {"byte": len(pb), "sha256": sha(pb),
                    "amp": list(args.amp), "sca": list(args.sca), "fase": list(args.fase),
                    "blink_min": args.blink_min, "blink_mask": args.blink_mask,
                    "blink_dur": args.blink_dur, "raro_ogni": args.raro_ogni,
                    "raro_piu": args.raro_piu},
        },
        "serie_y_per_classe": serie,
        "serie_scala_per_classe": serie_s,
        "occupazione_totale_byte": len(blob) + N_CANARINO + 32 + 32 + 64 + 4 * 32,
        "blocco_richiesto_byte": BLOCCO,
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
        "offset_relativi": {
            "codice": hex(OFF_CODICE), "canarino": hex(OFF_CANARINO),
            "tabelle": hex(OFF_TABELLE), "stato": hex(OFF_STATO), "slot": hex(OFF_SLOT),
            "identici_a": "SGP-1.2-ANIM-B-01/prove/build-1b/manifesto2.json (fase 1b)",
        },
        "ancore_del_gioco": {
            "Pokepic_SetAttr": "0x020087a5",
            "ov12_task_vanilla": "0x0226203d",
            "letterale_da_sostituire": "ov012 0x0226200c",
        },
    }
    (out / "manifesto.json").write_text(json.dumps(manifesto, indent=2) + "\n")
    print(json.dumps({k: manifesto[k] for k in
                      ("blob", "canarino", "indirizzi", "occupazione_totale_byte")}, indent=2))


if __name__ == "__main__":
    main()
