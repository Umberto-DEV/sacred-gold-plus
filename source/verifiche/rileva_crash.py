#!/usr/bin/env python3
"""Dice se una corsa di hg_runtime e' finita in crash.

Nasce da un difetto rimasto invisibile per ore l'11/09/2026: allo scadere di un
repellente il gioco prendeva un'eccezione, ma `rc` restava 0, l'emulatore
continuava a produrre fotogrammi e le catture erano byte-identiche. Sembrava una
schermata ferma. La colonna che lo rivelava era `arm9_pc`.

Due segni, entrambi necessari perche' il verdetto sia CRASH:
  - `arm9_pc` inchiodato nel vettore di eccezione ARM9 (0xFFFF0000..0xFFFF01FF);
  - `game_vblank_counter` che smette di avanzare.
Il secondo da solo non basta: il contatore si ferma anche durante un caricamento
bloccante legittimo, che in questo progetto e' gia' stato scambiato per un guasto.

Uso:   python3 rileva_crash.py <corsa>/frames.csv [...]
Esce 1 per crash, cappio fisso o traccia inutilizzabile. STALLO resta
inconclusivo: servono anche verifiche dello stato di gioco raggiunto.
"""
import csv
import sys

VETTORE_LO = 0xFFFF0000
VETTORE_HI = 0xFFFF0200
SOGLIA_CODA = 60  # fotogrammi consecutivi senza avanzamento: sotto, e' rumore


def num(s):
    s = s.strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s)


def esamina(percorso):
    with open(percorso) as fh:
        righe = list(csv.DictReader(fh))
    if not righe:
        return "VUOTO", "il file non ha righe: una corsa che non ha prodotto nulla non e' una corsa riuscita"
    for c in ("arm9_pc", "game_vblank_counter", "frame"):
        if c not in righe[0]:
            return "INCOMPLETO", f"manca la colonna {c}: non posso dire se il gioco fosse vivo"

    vb = [num(r["game_vblank_counter"]) for r in righe]

    # La CPU passa dal vettore BIOS anche in funzionamento normale: "PC nel vettore"
    # da solo NON discrimina (misurato: 12.451 fotogrammi su una corsa sana).
    # Il segno del crash e' la CODA: da un certo punto in poi il contatore del gioco
    # non avanza piu' E il PC resta lo stesso. Cerco l'ultimo avanzamento del vblank.
    ultimo_avanzamento = 0
    for i in range(1, len(righe)):
        if vb[i] != vb[i - 1]:
            ultimo_avanzamento = i
    coda = righe[ultimo_avanzamento:]
    if len(coda) < SOGLIA_CODA:
        return "VIVO", (f"{len(righe)} fotogrammi; il contatore avanzava ancora a {len(coda)} "
                        f"fotogrammi dalla fine (vblank da {vb[0]} a {vb[-1]})")

    # Il vblank puo' fermarsi durante il caricamento PRIMA dell'eccezione.
    # Quei primi PC variabili non devono nascondere un successivo cappio fisso.
    pc = num(righe[-1]["arm9_pc"])
    inizio_fisso = len(righe) - 1
    while inizio_fisso > ultimo_avanzamento and num(righe[inizio_fisso - 1]["arm9_pc"]) == pc:
        inizio_fisso -= 1
    fissa = righe[inizio_fisso:]
    frame_stop = num(fissa[0]["frame"])
    if len(fissa) >= SOGLIA_CODA and VETTORE_LO <= pc < VETTORE_HI:
        return "CRASH", (f"dal fotogramma {frame_stop}: PC fisso a {pc:#x} per {len(fissa)} fotogrammi, "
                         f"vblank congelato a {vb[-1]}")
    if len(fissa) >= SOGLIA_CODA:
        return "BLOCCATO", (f"dal fotogramma {frame_stop}: PC fisso a {pc:#x} (fuori dal vettore) "
                            f"per {len(fissa)} fotogrammi, vblank congelato: cappio, non eccezione")
    pc_distinti = {num(r["arm9_pc"]) for r in coda}
    return "STALLO", (f"dal fotogramma {num(coda[0]['frame'])}: vblank fermo per {len(coda)} fotogrammi ma "
                      f"{len(pc_distinti)} PC distinti; esito inconclusivo: verificare stato e avanzamento")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    peggiore = 0
    for p in argv:
        try:
            esito, dettaglio = esamina(p)
        except OSError as e:
            esito, dettaglio = "ILLEGGIBILE", str(e)
        print(f"{esito:12s} {p}\n             {dettaglio}")
        if esito in ("CRASH", "BLOCCATO", "ILLEGGIBILE", "VUOTO", "INCOMPLETO"):
            peggiore = 1
    return peggiore


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
