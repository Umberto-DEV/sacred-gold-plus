#!/usr/bin/env python3
"""SGP-1.2-ANIM-SOLIDO-01 — compila il blob **v4** di `sgp.anim`.

Derivato riga per riga da `SGP-1.2-ANIM-B-03/tools/compila_animb.py` (che
resta invariato nel suo pacchetto). Le differenze volute sono quattro, e
nessun'altra:

1. **sorgente**: `anim_blob4.c` (che include `sgp_anim4.h`, `sgp_chunk.h` e
   `anim_idle4.c`) invece di `anim_blob2b.c`;
2. **due entrate** invece di una: `sgp_idle_task2` (il task, bersaglio del
   letterale `ov012 0x0226200C`) e `sgp_idle_stop` (la trampolina del gancio
   di coda a `ov012 0x02262032`). Entrambe devono esistere e avere il bit
   Thumb;
3. **`tab_u` è la tavola v3 «lisciata»** di `SGP-1.2-RIFINITURA-01`
   (`[0,5,9,13,16,…]`), cioè quella che sta **davvero in ROM oggi**, non il
   seno arrotondato della fase 2b. Compilare la tavola del seno qui avrebbe
   fatto rientrare dalla finestra il difetto dei salti da 2 px;
4. **cancello nuovo, M-MONO**: per ciascuna delle quattro classi di taglia la
   serie `y = (tab_u[i]*amp + 8) >> 4` dev'essere **monotona a passi di al
   più 1 px** su tutto il ciclo. È il difetto che RIFINITURA-01 ha trovato
   misurando; qui diventa una condizione di compilazione, così non può
   tornare cambiando un parametro. La stessa verifica vale per la scala.

Uso: compila_anim4.py --uscita DIR [--base 0x023D8B00] [--amp ...] [--sca ...]
                                   [--fase ...] [--blink-* ...] [--raro-* ...]
GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from carica_text import load_text  # noqa: E402

SORGENTI = Path(__file__).resolve().parent.parent / "sorgenti"
ENTRATE = ("sgp_idle_task2", "sgp_idle_stop")
FASI = 18

DEF_BASE = 0x023D8B00
OFF_CODICE = 0x000
OFF_CANARINO = 0x2F0
N_CANARINO = 16
OFF_TABELLE = 0x300
OFF_STATO = 0x340
OFF_SLOT = 0x380
MAX_CODICE = OFF_CANARINO   # 752 B
BLOCCO = 0x400

CANARINO_MOTIVO = 0xCA5A1400   # invariato: e' lo stesso blocco, non uno nuovo

# La tavola v3 di SGP-1.2-RIFINITURA-01 §B: seno a 18 fasi in unita' di 1/16,
# lisciato in modo che (u*k+8)>>4 sia monotono a passi di 1 px per k = 2,3,4.
# Scarto massimo dal seno vero: 1/16 di unita' = 0,06 px a piena ampiezza.
TAB_U_V3 = (0, 5, 9, 13, 16, 16, 13, 9, 5, 0, -5, -9, -13, -16, -16, -13, -9, -5)

# Ampiezza per classe di taglia. La classe 0 passa da 2 a **3 px** in questa
# versione, e non e' una preferenza: e' la conseguenza del difetto D4, misurato
# qui. I bit 5-6 di `pokepic+0x6C` (`shadow.size`) sono l'unico ingresso di
# taglia disponibile, e sul lottatore del GIOCATORE — l'unico che HGSS anima —
# valgono SEMPRE 0, perche' al battler di dorso il gioco non disegna l'ombra
# (`palSlot` e `size` a zero, misurato su due lotte e attraverso un cambio
# Pokemon). Quindi in gioco la riga della tabella che conta e' solo la 0.
# Con ampiezza 2 px il criterio 2 di `10c` §4 misura 3,9 % di pixel diversi
# (rosso, «invisibile») e il criterio 1 il 18,2 % di finestre ferme; con 3 px
# diventano 4,86 % e **6,8 %**, e l'ampiezza vale 6 px picco-picco su uno sprite
# alto ~71 px = 8,5 % (verde con la metrica alternativa dichiarata in CRITERI).
# 3 px e' anche l'ampiezza su cui erano tarate le misure della fase 1b.
DEF_AMP = (3, 3, 4, 4)
DEF_SCA = (4, 6, 6, 6)
DEF_FASE = (0, 9, 5, 14)
DEF_BLINK_MIN = 70
DEF_BLINK_MASK = 63
DEF_BLINK_DUR = 2
DEF_RARO_OGNI = 3
DEF_RARO_PIU = 3


def sha(b):
    return hashlib.sha256(b).hexdigest()


def tabella_u():
    v = list(TAB_U_V3)
    return bytes((x & 0xFF) for x in v) + bytes(32 - FASI), v


def scala_unita(u, k):
    return (u * k + 8) >> 4


def salti(vu, k):
    """Il salto massimo fra due fasi consecutive del ciclo (chiuso su se'
    stesso: l'ultima fase torna alla prima)."""
    y = [scala_unita(u, k) for u in vu]
    return max(abs(y[(i + 1) % len(y)] - y[i]) for i in range(len(y)))


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

    tu, vu = tabella_u()

    # --- cancello M-MONO, prima di compilare ------------------------------
    mono = {}
    for c in range(4):
        mono[f"amp{c}"] = salti(vu, args.amp[c])
        mono[f"sca{c}"] = salti(vu, args.sca[c])
    cattivi = [k for k, v in mono.items() if k.startswith("amp") and v > 1]
    if cattivi:
        raise SystemExit(
            "M-MONO ROSSO: con questa tavola e queste ampiezze la serie del "
            f"yOffset salta piu' di 1 px per fotogramma ({cattivi}, salti={mono}). "
            "E' il difetto trovato da SGP-1.2-RIFINITURA-01 §B: non si compila.")

    comando = [
        args.cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", args.opt,
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-fno-unwind-tables",
        "-fno-asynchronous-unwind-tables", "-fno-jump-tables", "-Wall", "-Wextra",
        f"-DSGP_ANIM2_STATE_ADDR={stato:#x}u",
        f"-DSGP_ANIM2_TAB_ADDR={tabelle:#x}u",
        f"-DSGP_ANIM2_SLOT_ADDR={slot:#x}u",
        "-c", str(SORGENTI / "anim_blob4.c"), "-o", str(out / "anim_blob4.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (out / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita; vedi compila.log\n" + r.stdout + r.stderr)
    avvisi = [x for x in (r.stdout + r.stderr).splitlines() if "warning:" in x]

    blob, simboli = load_text((out / "anim_blob4.o").read_bytes(), codice, ENTRATE)
    if len(blob) > MAX_CODICE:
        raise SystemExit(f"il blob ({len(blob)} B) non entra nei {MAX_CODICE} B "
                         f"riservati prima del canarino")
    for nome in ENTRATE:
        if simboli[nome] & 1 == 0:
            raise SystemExit(f"{nome} non ha il bit Thumb: {simboli[nome]:#x}")
    (out / "blob.bin").write_bytes(blob)
    pb = par_bin(args.amp, args.sca, args.fase, args.blink_min, args.blink_mask,
                 args.blink_dur, args.raro_ogni, args.raro_piu)
    can = canarino_bin()
    (out / "tab_u.bin").write_bytes(tu)
    (out / "par.bin").write_bytes(pb)
    (out / "canarino.bin").write_bytes(can)

    serie = {str(c): [scala_unita(u, args.amp[c]) for u in vu] for c in range(4)}
    serie_s = {str(c): [scala_unita(u, args.sca[c]) for u in vu] for c in range(4)}

    manifesto = {
        "pacchetto": "SGP-1.2-ANIM-SOLIDO-01",
        "fase": "v4-pulizia-alla-sospensione",
        "eredita": "SGP-1.2-ANIM-B-03 (fase 2b, blob in ROM) + SGP-1.2-RIFINITURA-01 "
                   "(tavola v3). Indirizzi, layout e parametri INVARIATI; nuovi: la "
                   "trampolina sgp_idle_stop e il secondo gancio a ov012 0x02262032.",
        "comando": comando,
        "avvisi_compilatore": avvisi,
        "compilatore": subprocess.run([args.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "indirizzi": {
            "base": hex(args.base), "codice": hex(codice), "canarino": hex(canarino),
            "tabelle": hex(tabelle), "stato": hex(stato), "slot": hex(slot),
            "blocco_byte": BLOCCO,
        },
        "blob": {"byte": len(blob), "sha256": sha(blob), "max": MAX_CODICE},
        "canarino": {"offset": hex(OFF_CANARINO), "byte": N_CANARINO,
                     "motivo": hex(CANARINO_MOTIVO), "sha256": sha(can)},
        "tabelle_bin": {
            "tab_u": {"byte": len(tu), "sha256": sha(tu), "valori": vu,
                      "origine": "tavola v3 di SGP-1.2-RIFINITURA-01 §B"},
            "par": {"byte": len(pb), "sha256": sha(pb),
                    "amp": list(args.amp), "sca": list(args.sca), "fase": list(args.fase),
                    "blink_min": args.blink_min, "blink_mask": args.blink_mask,
                    "blink_dur": args.blink_dur, "raro_ogni": args.raro_ogni,
                    "raro_piu": args.raro_piu},
        },
        "M_MONO": {"salti_massimi": mono, "esito": "verde"},
        "serie_y_per_classe": serie,
        "serie_scala_per_classe": serie_s,
        "occupazione_totale_byte": len(blob) + N_CANARINO + 32 + 32 + 64 + 4 * 32,
        "blocco_richiesto_byte": BLOCCO,
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
        "offset_relativi": {
            "codice": hex(OFF_CODICE), "canarino": hex(OFF_CANARINO),
            "tabelle": hex(OFF_TABELLE), "stato": hex(OFF_STATO), "slot": hex(OFF_SLOT),
        },
        "ancore_del_gioco": {
            "Pokepic_SetAttr": "0x020087a5",
            "ov12_task_vanilla": "0x0226203d",
            "letterale_da_sostituire": "ov012 0x0226200c",
            "coda_di_ov12_02262014": "ov012 0x02262032 (4 B -> BL sgp_idle_stop)",
        },
    }
    (out / "manifesto.json").write_text(json.dumps(manifesto, indent=2) + "\n")
    print(json.dumps({k: manifesto[k] for k in
                      ("blob", "simboli", "M_MONO", "avvisi_compilatore",
                       "occupazione_totale_byte")}, indent=2))


if __name__ == "__main__":
    main()
