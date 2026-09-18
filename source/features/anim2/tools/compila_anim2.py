#!/usr/bin/env python3
"""Compila ANIM2 v5d: moto lento, HUD fermo, ciclo di vita della cattura e
accento di posa B ancorato al respiro.

Blocco 2048 B a 0x023DB500, codice <=1536 B, dati agli indirizzi di v5b.
Cinque entrate: idle, stop/trampolina, avvio, politica e avvio cattura.
Il preset 5c sostituisce gli esperimenti 5a/5b: sette stop di menu soppressi,
nessuna estensione dei destructor. --passo 2/3/4 sceglie 0.25/0.375/0.5x.
--variante V1/V2/V3 sceglie la TARATURA dell'accento di posa B (solo par.bin,
stesso blob): V1 nativa 0,33 s, V2 leggibile 0,50 s, V3 lunga 1,0 s.
Gli artefatti e il manifesto sono verificati dall'applicatore indipendente.
GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
SORGENTI = QUI.parent / "sorgenti"
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "source" / "features" / "anim" / "tools"))
from carica_text import load_text  # noqa: E402

ENTRATE = ("sgp_idle_task5", "sgp_stop_testa", "sgp_avvia_tutti",
           "sgp_stop_politica", "sgp_avvia_cattura")
FASI = 18

# Pianta del blocco. Il tetto del codice (1536 B) e la dimensione del blocco
# (2048 B) sono MISURATI, non stimati: la v5 compila a ~1,4 kB perche' porta
# tre sottosistemi che la v4 non aveva (avvio su tutti, politica per `lr`,
# sospensione a tre cancelli), e la sola v4 gia' occupava 752 B. Il mandato
# stimava 1536 B di blocco; il coordinatore ha accettato 2048 B per conservare
# separati codice, canarino, tabelle e stato. Dopo `sgp.borsa` e questo
# blocco restano 11 840 B liberi in `libero.1.2.finale`.
DEF_BASE = 0x023DB500
OFF_CODICE = 0x000
MAX_CODICE = 0x600
OFF_CANARINO = 0x600
N_CANARINO = 16
OFF_TAB_U = 0x620
OFF_PAR = 0x640
OFF_SITI = 0x660
N_SITI_B = 64          # 9 parole + riempimento, per tenere lo stato allineato
OFF_STATO = 0x6A0
N_STATO = 64
OFF_SLOT = 0x6E0
N_SLOT = 128
BLOCCO = 0x800         # 2048 B

CANARINO_MOTIVO = 0xCA5A1800

# I nove siti di chiamata di `ov12_02262014`, nell'ordine in cui compaiono nel
# modulo. `lr = sito + 5` (BL di 4 B piu' il bit Thumb): misurato sui byte in
# SGP-1.2.1-ANIM-FASI-01 §3.2, identico EN e IT.
SITI = (
    ("DISTRUZIONE", 0x02258E98),        # BattlerData_Delete
    ("IO-BARRA", 0x02259338),           # BtlIOCmd_StopGaugeAnimation, ogni turno
    ("IO-SCHERMO-BASSO", 0x02259596),   # fine della fase di comando
    ("BORSA", 0x0225DFBE),
    ("SQUADRA", 0x0225E00A),
    ("SAFARI", 0x0225E0B2),
    ("CONFERMA-MOSSA", 0x0225E39E),
    ("BERSAGLIO", 0x0225E670),
    ("SI-NO", 0x0225FC0A),
)
LR = tuple(s + 5 for _n, s in SITI)
NOMI = tuple(n for n, _s in SITI)
IDX = {n: i for i, n in enumerate(NOMI)}


def maschera(nomi):
    m = 0
    for n in nomi:
        m |= 1 << IDX[n]
    return m


# Politica corrente: conserva i menu, rispetta distruzione e Safari.
LIVELLI = {
    "5c": {
        "sopprimi": maschera(("IO-BARRA", "IO-SCHERMO-BASSO", "BORSA", "SQUADRA",
                              "CONFERMA-MOSSA", "BERSAGLIO", "SI-NO")),
        # Il teardown nativo distrugge ciascun lottatore: estenderlo dalla
        # seconda chiamata leggerebbe gli OpponentData già liberati.
        "estendi": 0,
        "cancelli": 0x07,
    },
}

TAB_U_V3 = (0, 5, 9, 13, 16, 16, 13, 9, 5, 0, -5, -9, -13, -16, -16, -13, -9, -5)
DEF_AMP = (3, 3, 4, 4)
DEF_SCA = (4, 6, 6, 6)
DEF_FASE = (0, 9, 5, 14)
# v5d — le tre tarature dell'accento di posa B, tutte a parita' di codice.
# Un tick = 2 fotogrammi video = 33,3 ms (A1 §1.1, tre fonti indipendenti).
# Il gioco stesso, negli script `a/1/8/0`, tiene la posa B per una mediana di
# 10 chiamate = 0,33 s e piu' spesso di tutto 15 = 0,50 s (A1 §1.3); la v5c ne
# teneva 2-3 tick = 0,067-0,100 s (A2 §3: 4-6 fotogrammi misurati), da 3,3x a
# 7,5x meno di qualunque durata nativa. V1 e' la taratura che riporta l'accento
# dentro quell'intervallo; V2 e V3 servono al confronto a schermo.
VARIANTI = {
    "V1": {"blink_dur": 10, "raro_piu": 5},   # 0,33 s (raro 0,50 s) — nativa
    "V2": {"blink_dur": 15, "raro_piu": 5},   # 0,50 s (raro 0,67 s) — leggibile
    "V3": {"blink_dur": 30, "raro_piu": 0},   # 1,00 s — lunga, per confronto
}
DEF_VARIANTE = "V1"
DEF_BLINK_MIN = 120       # attesa 120..247 tick = 4,00..8,23 s
DEF_BLINK_MASK = 127
DEF_RARO_OGNI = 3

# Gli indici in cui `tab_u` vale il massimo: il blob li confronta con due sole
# istruzioni (`SGP_PICCO_IDX`/`SGP_PICCO_N` in sgp_anim5.h) e non puo'
# cercarli. Se la tavola cambia forma, il cancello qui sotto lo dice.
PICCO = (4, 5)

PAR_SOPPRIMI = 0x12
PAR_ESTENDI = 0x14
PAR_CANCELLI = 0x16
PAR_PASSO = 0x17


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def relativo(x):
    """Il comando registrato nel manifesto non deve portare il percorso della
    macchina che ha compilato: `.github/check_public.py` rifiuta i file
    pubblici che contengono una home o uno scratch, e un manifesto con dentro
    la cartella personale di chi compila non e' nemmeno confrontabile fra due
    macchine.

    Tocca SOLO i percorsi assoluti. La versione precedente chiamava
    `Path(x).resolve()` su ogni elemento di `comando`, flag compresi: da CWD
    `source/` un flag come `-Oz` si risolveva in `source/-Oz`, un nome
    comando come `clang` in `source/clang` (A8b A1). Un percorso assoluto
    dentro il repo diventa relativo; uno fuori (es. `--uscita` fuori
    dall'albero) resta ridotto al solo nome del file, mai al percorso
    assoluto intero."""
    p = Path(x)
    if not p.is_absolute():
        return x
    try:
        return str(p.resolve().relative_to(REPO))
    except (ValueError, OSError):
        return p.name


def tabella_u():
    v = list(TAB_U_V3)
    return bytes((x & 0xFF) for x in v) + bytes(32 - FASI), v


def scala_unita(u, k):
    return (u * k + 8) >> 4


def salti(vu, k):
    y = [scala_unita(u, k) for u in vu]
    return max(abs(y[(i + 1) % len(y)] - y[i]) for i in range(len(y)))


def par_bin(amp, sca, fase, blink_min, blink_mask, blink_dur, raro_ogni,
            raro_piu, sopprimi, estendi, cancelli, passo=3):
    b = bytearray(32)
    b[0x00:0x04] = bytes(amp)
    b[0x04:0x08] = bytes(sca)
    b[0x08:0x0C] = bytes(fase)
    b[0x0C] = blink_min
    b[0x0D] = blink_mask
    b[0x0E] = blink_dur
    b[0x0F] = raro_ogni
    b[0x10] = raro_piu
    struct.pack_into("<H", b, PAR_SOPPRIMI, sopprimi)
    struct.pack_into("<H", b, PAR_ESTENDI, estendi)
    b[PAR_CANCELLI] = cancelli
    b[PAR_PASSO] = passo
    return bytes(b)


def siti_bin():
    b = bytearray(N_SITI_B)
    for i, v in enumerate(LR):
        struct.pack_into("<I", b, i * 4, v)
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
    ap.add_argument("--livello", choices=sorted(LIVELLI), default="5c")
    ap.add_argument("--sopprimi", type=lambda x: int(x, 0), default=None)
    ap.add_argument("--estendi", type=lambda x: int(x, 0), default=None)
    ap.add_argument("--cancelli", type=lambda x: int(x, 0), default=None)
    ap.add_argument("--passo", type=int, choices=(2, 3, 4), default=3,
                    help="velocita: 2=0.25x, 3=0.375x, 4=0.5x")
    ap.add_argument("--amp", type=quattro, default=DEF_AMP)
    ap.add_argument("--sca", type=quattro, default=DEF_SCA)
    ap.add_argument("--fase", type=quattro, default=DEF_FASE)
    ap.add_argument("--variante", choices=sorted(VARIANTI), default=DEF_VARIANTE,
                    help="taratura dell'accento di posa B (solo par.bin)")
    ap.add_argument("--blink-min", type=int, default=DEF_BLINK_MIN)
    ap.add_argument("--blink-mask", type=int, default=DEF_BLINK_MASK)
    ap.add_argument("--blink-dur", type=int, default=None)
    ap.add_argument("--raro-ogni", type=int, default=DEF_RARO_OGNI)
    ap.add_argument("--raro-piu", type=int, default=None)
    args = ap.parse_args()
    for nome, valore in VARIANTI[args.variante].items():
        if getattr(args, nome) is None:
            setattr(args, nome, valore)
    # B3 — se un flag esplicito ha spostato un parametro che la variante
    # controlla (blink_dur/raro_piu) lontano dal suo preset, il manifesto non
    # puo' piu' etichettare la build come "V1"/"V2"/"V3" tal quale: sarebbe
    # una variante che non corrisponde ai propri numeri.
    variante_modificata = any(getattr(args, nome) != valore
                              for nome, valore in VARIANTI[args.variante].items())
    out = args.uscita
    out.mkdir(parents=True, exist_ok=True)

    liv = LIVELLI[args.livello]
    sopprimi = liv["sopprimi"] if args.sopprimi is None else args.sopprimi
    estendi = liv["estendi"] if args.estendi is None else args.estendi
    cancelli = liv["cancelli"] if args.cancelli is None else args.cancelli
    if estendi:
        raise SystemExit("R3 ROSSO: estendere le fermate visita lottatori gia liberati")
    if sopprimi & 1:
        raise SystemExit(
            "R3 ROSSO: il sito DISTRUZIONE (0x02258E98) non si puo' sopprimere: "
            "il SysTask punta alla struttura che quella funzione libera.")

    # --- cancello NEGATIVO, prima di ogni altro controllo (A8b B4) --------
    # Questi parametri finiscono impacchettati come byte non firmati in
    # `par_bin` (assegnazione diretta in un bytearray o `bytes(...)`): senza
    # questo cancello un valore negativo non dava un ROSSO leggibile ma un
    # ValueError di libreria a meta' scrittura di par.bin.
    negativi = {}
    for nome, valore in (("blink-min", args.blink_min),
                         ("blink-mask", args.blink_mask),
                         ("blink-dur", args.blink_dur),
                         ("raro-ogni", args.raro_ogni),
                         ("raro-piu", args.raro_piu)):
        if valore < 0:
            negativi[nome] = valore
    for nome, valori in (("amp", args.amp), ("sca", args.sca), ("fase", args.fase)):
        for i, v in enumerate(valori):
            if v < 0:
                negativi["%s%d" % (nome, i)] = v
    if negativi:
        raise SystemExit(
            "NEGATIVO ROSSO: questi parametri non possono essere negativi "
            "(diventano byte non firmati in par.bin): %s" % negativi)

    if args.raro_ogni < 2:
        raise SystemExit(
            "RARO ROSSO: --raro-ogni deve valere almeno 2. Con 0 o 1 "
            "`blink_cnt >= SGP_PAR[PAR_RARO_OGNI]` e' vero fin dal primo "
            "giro (blink_cnt parte da 0 e viene incrementato PRIMA del "
            "confronto): ogni accento diventerebbe raro, non uno su N.")

    codice = args.base + OFF_CODICE
    canarino = args.base + OFF_CANARINO
    tab_u = args.base + OFF_TAB_U
    par = args.base + OFF_PAR
    siti = args.base + OFF_SITI
    stato = args.base + OFF_STATO
    slot = args.base + OFF_SLOT

    tu, vu = tabella_u()

    # La guardia runtime considera nativa ogni scala fuori da 256 +/- 8.
    # Un'ampiezza maggiore farebbe sospendere per sempre il proprio idle.
    if any(x < 0 or x > 8 for x in args.sca):
        raise SystemExit("SCALA ROSSO: --sca deve restare fra 0 e 8, "
                         "entro la finestra di proprieta' dell'idle.")

    # --- cancelli dell'accento di posa B (A1 §6.2) ------------------------
    # Quattro difetti certi che il compilatore accettava in silenzio, piu' la
    # lettura fuori tabella di --fase (A8b M3). Costo in ROM: zero.
    if args.blink_dur < 1:
        raise SystemExit(
            "BLINK ROSSO: --blink-dur deve valere almeno 1. Con 0 il blob "
            "calcola `blink_left = (u8)(0 - 1) = 255`: una posa B di 8,5 s "
            "circa una volta su due (A1 §3.2 B2).")
    if not (0 <= args.blink_mask <= 255) or (args.blink_mask & (args.blink_mask + 1)):
        raise SystemExit(
            "BLINK ROSSO: --blink-mask deve essere della forma 2^n-1 "
            "(0,1,3,7,...,255): il blob la usa come MASCHERA, non come modulo, "
            "e un valore come 100 da' 36 valori su 101 con dei buchi "
            "(A1 §3.2 B4). Ricevuto %d." % args.blink_mask)
    if args.blink_min + args.blink_mask > 255:
        raise SystemExit(
            "BLINK ROSSO: blink_min + blink_mask = %d > 255. `blink_wait` e' "
            "un u8: la somma verrebbe troncata e un'attesa lunga diventerebbe "
            "brevissima, senza avvisi (A1 §3.2 B1)."
            % (args.blink_min + args.blink_mask))
    if args.blink_dur + 1 + args.raro_piu > 255:
        raise SystemExit(
            "BLINK ROSSO: blink_dur + 1 + raro_piu = %d > 255. La durata "
            "massima finisce in `blink_left`, che e' un u8."
            % (args.blink_dur + 1 + args.raro_piu))
    if any(not (0 <= f < FASI) for f in args.fase):
        raise SystemExit(
            "FASE ROSSO: ogni --fase deve stare fra 0 e %d. Il blob somma "
            "questo valore all'indice della tavola e con --fase 200 legge "
            "dentro lo STATO e la VOCE 0 (A8b M3, verificata). Ricevuto %s."
            % (FASI - 1, list(args.fase)))
    massimo = max(vu)
    if tuple(i for i, v in enumerate(vu) if v == massimo) != PICCO:
        raise SystemExit(
            "PICCO ROSSO: il massimo della tavola sta agli indici %s, il blob "
            "aspetta %s (SGP_PICCO_IDX/SGP_PICCO_N in sgp_anim5.h). L'accento "
            "di posa B partirebbe fuori dal punto di quiete del respiro."
            % (tuple(i for i, v in enumerate(vu) if v == massimo), PICCO))

    # --- cancello M-MONO, prima di compilare ------------------------------
    mono = {}
    for c in range(4):
        mono[f"amp{c}"] = salti(vu, args.amp[c])
        mono[f"sca{c}"] = salti(vu, args.sca[c])
    cattivi = [k for k, v in mono.items() if k.startswith("amp") and v > 1]
    if cattivi:
        raise SystemExit(
            "M-MONO ROSSO: con questa tavola e queste ampiezze la serie del "
            f"yOffset salta piu' di 1 px per fotogramma ({cattivi}, salti={mono}).")

    comando = [
        args.cc, "--target=armv5te-none-eabi", "-mcpu=arm946e-s", "-mthumb", args.opt,
        "-ffreestanding", "-fno-builtin", "-fno-stack-protector", "-fno-unwind-tables",
        "-fno-asynchronous-unwind-tables", "-fno-jump-tables", "-Wall", "-Wextra",
        f"-DSGP_ANIM5_BASE={args.base:#x}u",
        f"-DSGP_ANIM5_STATE_ADDR={stato:#x}u",
        f"-DSGP_ANIM5_TAB_ADDR={tab_u:#x}u",
        f"-DSGP_ANIM5_PAR_ADDR={par:#x}u",
        f"-DSGP_ANIM5_SITI_ADDR={siti:#x}u",
        f"-DSGP_ANIM5_SLOT_ADDR={slot:#x}u",
        "-c", str(SORGENTI / "anim_blob5.c"), "-o", str(out / "anim_blob5.o"),
    ]
    r = subprocess.run(comando, text=True, capture_output=True)
    (out / "compila.log").write_text(r.stdout + r.stderr)
    if r.returncode != 0:
        raise SystemExit("compilazione fallita; vedi compila.log\n" + r.stdout + r.stderr)
    avvisi = [x for x in (r.stdout + r.stderr).splitlines() if "warning:" in x]

    blob, simboli = load_text((out / "anim_blob5.o").read_bytes(), codice, ENTRATE)
    if len(blob) > MAX_CODICE:
        raise SystemExit(f"il blocco ({len(blob)} B) non entra nei {MAX_CODICE} B "
                         f"riservati prima del canarino")
    for nome in ENTRATE:
        if simboli[nome] & 1 == 0:
            raise SystemExit(f"{nome} non ha il bit Thumb: {simboli[nome]:#x}")
    (out / "blob.bin").write_bytes(blob)
    pb = par_bin(args.amp, args.sca, args.fase, args.blink_min, args.blink_mask,
                 args.blink_dur, args.raro_ogni, args.raro_piu,
                 sopprimi, estendi, cancelli, args.passo)
    can = canarino_bin()
    sb = siti_bin()
    (out / "tab_u.bin").write_bytes(tu)
    (out / "par.bin").write_bytes(pb)
    (out / "siti.bin").write_bytes(sb)
    (out / "canarino.bin").write_bytes(can)

    # Serie a regime, con la stessa unita' fissa del C; niente inviluppo.
    onda = [(vu[f >> 3] * (8 - (f & 7)) + vu[((f >> 3) + 1) % FASI]
             * (f & 7)) * 16 for f in range(0, FASI * 8, args.passo)]
    serie = {str(c): [(u * args.amp[c] + 1024) >> 11 for u in onda] for c in range(4)}
    serie_s = {str(c): [(u * args.sca[c] + 1024) >> 11 for u in onda] for c in range(4)}
    usati = OFF_SLOT + N_SLOT

    manifesto = {
        "pacchetto": "SGP-1.2.1-ANIM-MOTO-01",
        "fase": "v5d-accento-posa-b",
        "eredita": "SGP-1.2-ANIM-SOLIDO-01 (v4, blob in ROM a 0x023D8B00) + "
                   "SGP-1.2.1-ANIM-SEGNALE-01 (il segnale moveActive) + "
                   "SGP-1.2.1-ANIM-FASI-01 (i nove lr, misurati sui byte).",
        "comando": [relativo(x) for x in comando],
        "avvisi_compilatore": avvisi,
        "compilatore": subprocess.run([args.cc, "--version"], text=True,
                                      capture_output=True).stdout.splitlines()[0],
        "livello": args.livello,
        "indirizzi": {
            "base": hex(args.base), "codice": hex(codice), "canarino": hex(canarino),
            "tab_u": hex(tab_u), "par": hex(par), "siti": hex(siti),
            "stato": hex(stato), "slot": hex(slot), "blocco_byte": BLOCCO,
        },
        "blob": {"byte": len(blob), "sha256": sha(blob), "max": MAX_CODICE},
        "canarino": {"offset": hex(OFF_CANARINO), "byte": N_CANARINO,
                     "motivo": hex(CANARINO_MOTIVO), "sha256": sha(can)},
        "tabelle_bin": {
            "tab_u": {"byte": len(tu), "sha256": sha(tu), "valori": vu,
                      "origine": "tavola v3 di SGP-1.2-RIFINITURA-01 §B"},
            "par": {"byte": len(pb), "sha256": sha(pb),
                    "amp": list(args.amp), "sca": list(args.sca),
                    "fase": list(args.fase),
                    "variante": (args.variante + " (modificata)"
                                if variante_modificata else args.variante),
                    "variante_modificata": variante_modificata,
                    "blink_min": args.blink_min, "blink_mask": args.blink_mask,
                    "blink_dur": args.blink_dur, "raro_ogni": args.raro_ogni,
                    "raro_piu": args.raro_piu,
                    "posa_b_tick": [args.blink_dur, args.blink_dur + 1],
                    "posa_b_rara_tick": [args.blink_dur + args.raro_piu,
                                         args.blink_dur + args.raro_piu + 1],
                    "attesa_tick": [args.blink_min,
                                    args.blink_min + args.blink_mask],
                    "picco_tab_u": list(PICCO),
                    "passo": args.passo, "velocita_relativa": args.passo / 8,
                    "periodo_tick": FASI * 8 // args.passo,
                    "sopprimi": hex(sopprimi), "estendi": hex(estendi),
                    "cancelli": hex(cancelli)},
            "siti": {"byte": len(sb), "sha256": sha(sb),
                     "lr": [hex(v) for v in LR], "nomi": list(NOMI),
                     "origine": "SGP-1.2.1-ANIM-FASI-01 §3.2 (lr = sito + 5, EN=IT)"},
        },
        "politica": {
            "soppressi": [NOMI[i] for i in range(len(NOMI)) if (sopprimi >> i) & 1],
            "estesi": [NOMI[i] for i in range(len(NOMI)) if (estendi >> i) & 1],
            "passano": [NOMI[i] for i in range(len(NOMI))
                        if not ((sopprimi >> i) & 1)],
            "cancelli_sospensione": [n for b, n in
                                     ((1, "moveActive"), (2, "ingresso"),
                                      (4, "animActive")) if cancelli & b] + ["scala_nativa", "ritaglio_o_invisibile"],
        },
        "M_MONO": {"salti_massimi_tavola": mono, "esito": "verde",
                   "salti_massimi_interpolati_y": {
                       c: max(abs(y[(i + 1) % len(y)] - y[i]) for i in range(len(y)))
                       for c, y in serie.items()}},
        "serie_y_per_classe": serie,
        "serie_scala_per_classe": serie_s,
        "occupazione_totale_byte": usati,
        "blocco_richiesto_byte": BLOCCO,
        "simboli": {k: hex(v) for k, v in sorted(simboli.items())},
        "offset_relativi": {
            "codice": hex(OFF_CODICE), "canarino": hex(OFF_CANARINO),
            "tab_u": hex(OFF_TAB_U), "par": hex(OFF_PAR), "siti": hex(OFF_SITI),
            "stato": hex(OFF_STATO), "slot": hex(OFF_SLOT),
        },
        "ancore_del_gioco": {
            "Pokepic_SetAttr": "0x020087a5",
            "ov12_task_vanilla": "0x0226203d",
            "ov12_avvia": "0x02261fd5",
            "ov12_ferma": "0x02262015",
            "G3_sito_avvio": "ov012 0x0225dc8a (BL -> sgp_avvia_tutti)",
            "G1_letterale_task": "ov012 0x0226200c",
            "G2_testa_fermata": "ov012 0x02262016 (BL -> sgp_stop_testa)",
            "G2_coda_v4_ritirata": "ov012 0x02262032 torna vanilla (20 6a 04 21)",
            "G4_avvio_cattura": "ov012 0x0223ebd8 (BL -> sgp_avvia_cattura)",
        },
    }
    (out / "manifesto.json").write_text(json.dumps(manifesto, indent=2) + "\n")
    print(json.dumps({k: manifesto[k] for k in
                      ("blob", "simboli", "politica", "M_MONO",
                       "avvisi_compilatore", "occupazione_totale_byte")}, indent=2))


if __name__ == "__main__":
    main()
