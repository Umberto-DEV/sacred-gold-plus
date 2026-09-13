#!/usr/bin/env python3
"""SGP-1.2-RIFINITURA-01 (v3) — costruisce il blob dei testi e la tabella delle voci.

Formato del blob (lo stesso della guida EV/IV della 1.1, `guide_present.c`):

    u16 off[T_COUNT]     offset IN BYTE dall'inizio del blob, uno per id
    ...                  le stringhe, u16 nel charset HGSS, terminate 0xFFFF

L'ordine degli id e' quello dell'enum in `sorgenti/sgp_ui.h`: se cambia li',
cambia qui, e il test `test_testi.py` confronta le due liste.

Tabella delle voci: 6 record da 4 byte `{u8 nome; u8 tipo; u8 off; u8 on;}`.
  tipo 0 = interruttore su flags.b0 (difficolta' PLUS)
  tipo 1 = interruttore su wild_pct_idx (livelli selvatici)
  tipo 2 = riservata, disattivata: `off` e `on` puntano alla stessa etichetta

Uso: costruisci_testi.py --testi testi/testi.json --lingua IT --uscita DIR
     [--charmap <pret>/charmap.txt]
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from codifica_testo import carica_charmap, codifica            # noqa: E402

# id → chiave in testi.json. L'ordine E' l'enum di sgp_ui.h.
ORDINE = [
    "p_titolo", "p_aiuto_a", "p_aiuto_b", "p_bloccato", "p_rifiutato",
    "p_suggerimento",
    "v0_nome", "v1_nome", "v2_nome", "v3_nome", "v4_nome",
    "x_off", "x_on", "x_normale", "x_plus", "n_norm", "n_fluido",
    "w_0", "w_1", "w_2",
    "c_titolo", "c_riga1", "c_riga2", "c_riga1n", "c_riga2n", "c_nota", "c_aiuto",
    "@cursore", "@vuoto",
]
# le voci "@" sono generate, non tradotte
GENERATE = {"@cursore": "\u2192",   # 0x011E nella charmap: la freccia del gioco
            "@vuoto": ""}

# Voci della pagina, v2: (id_nome, id_primo_valore, quanti_valori, quale_stato,
# nascondi_se_assente). I valori di una voce sono id CONTIGUI nel blob: il
# controllo sotto lo verifica invece di fidarsi dell'ordine scritto a mano.
Q_D1_PLUS, Q_D1_WILD, Q_ANIM, Q_NPC, Q_WIFI = 0, 1, 2, 3, 4
VOCI = [
    ("v0_nome", "x_normale", 2, Q_D1_PLUS, 0),
    ("v1_nome", "x_normale", 2, Q_D1_WILD, 0),
    ("v2_nome", "x_off", 2, Q_ANIM, 1),
    ("v3_nome", "n_norm", 2, Q_NPC, 0),
    ("v4_nome", "w_0", 3, Q_WIFI, 0),
]
MAX_VOCI = 6


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--testi", type=Path, required=True)
    ap.add_argument("--lingua", required=True, choices=("EN", "IT"))
    ap.add_argument("--charmap", type=Path, default=None)
    ap.add_argument("--uscita", type=Path, required=True)
    args = ap.parse_args()
    args.uscita.mkdir(parents=True, exist_ok=True)

    tabella, fonte = carica_charmap(args.charmap)
    blocco = json.loads(args.testi.read_text(encoding="utf-8"))["testi"][args.lingua]

    testi = []
    for chiave in ORDINE:
        t = GENERATE[chiave] if chiave.startswith("@") else blocco[chiave]
        testi.append(codifica(t, tabella))

    intestazione = 2 * len(ORDINE)
    corpo, offsets = b"", []
    for parole in testi:
        offsets.append(intestazione + len(corpo))
        corpo += struct.pack("<%dH" % len(parole), *parole)
    if any(o > 0xFFFF for o in offsets):
        raise SystemExit("blob dei testi oltre 64 KiB: gli offset sono u16")
    blob = struct.pack("<%dH" % len(offsets), *offsets) + corpo

    idx = {c: i for i, c in enumerate(ORDINE)}
    # I valori di una voce devono essere id contigui: se qualcuno riordina
    # ORDINE, questo cancello lo ferma qui invece di far leggere alla ROM
    # l'etichetta sbagliata.
    for nome, primo, nval, _q, _n in VOCI:
        base = idx[primo]
        if base + nval > len(ORDINE):
            raise SystemExit(f"voce {nome}: i {nval} valori escono dal blob")
    voci = b"".join(bytes((idx[n], idx[v], nv, q | (h << 4)))
                    for n, v, nv, q, h in VOCI)
    voci += bytes(4 * (MAX_VOCI - len(VOCI)))

    (args.uscita / f"testi-{args.lingua}.bin").write_bytes(blob)
    (args.uscita / f"voci-{args.lingua}.bin").write_bytes(voci)
    manifesto = {
        "lingua": args.lingua, "charmap": fonte, "id": ORDINE,
        "testi_byte": len(blob), "testi_sha256": sha(blob),
        "voci_byte": len(voci), "voci_sha256": sha(voci),
        "voci": [{"nome": n, "val0": v, "nval": nv, "quale": q, "nascondi": h}
                 for n, v, nv, q, h in VOCI],
    }
    (args.uscita / f"testi-{args.lingua}.json").write_text(
        json.dumps(manifesto, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: manifesto[k] for k in
                      ("lingua", "testi_byte", "testi_sha256", "voci_byte",
                       "voci_sha256")}, indent=1))


if __name__ == "__main__":
    main()
