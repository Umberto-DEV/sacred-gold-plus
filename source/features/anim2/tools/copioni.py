#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2.1-ANIM-FASI-01 — generatore dei copioni a tocco per `hg_runtime-gdb`.

Un copione e' un file di testo, una riga per comando, che il banco esegue:
`run N [TASTI]`, `tap TASTI [PRESSIONE] [ATTESA]`, `touch X Y [FOTOGRAMMI]`,
`capture FILE.ppm`, `save FILE.state`, `load FILE`, `read IND [LARG] [QUANTI]`,
`write IND VAL [LARG]`, `watch ETICHETTA IND [LARG]`, `status`, `quit`.

Il percorso di avvio presuppone una fixture TEST nel Parco Nazionale:
un altro salvataggio richiede un copione adatto alla sua posizione. I puntatori
PIC0/PIC1 sono propri della fixture, da misurare di nuovo su altre squadre.
Nessun salvataggio è incluso.

Le coordinate sono quelle dello **schermo basso** e sono state lette sulle
catture del menu di lotta; sono **identiche in EN e IT** (verificato sulle corse
di questo pacchetto). Avvertenza misurata: dopo aver toccato il menu, `tap A`
**non** seleziona la mossa — serve il tocco.

Sottocomandi:

    menu    da ROM fredda: salta l'intro, carica la partita, cammina nell'erba
            fino all'incontro e **salva** lo stato al menu comandi
            (`menu.state`), cosi' le corse successive partono tutte dalla stessa
            riga di tempo
    fasi    la corsa E1/E2/E3: MENU, BORSA, SQUADRA, LISTA MOSSE, MOSSA, con
            `--fotogrammi` scatti consecutivi per fase (misura dei pixel vivi)
    borsa   MENU, BORSA, tasca Poke Ball, pannello del primo oggetto, ritorno
            alla lotta; non usa l'oggetto. Per misurare due cicli a 0.25x
            usare almeno --fotogrammi 300.
    turni   due turni completi, per vedere se il moto **riparte** al secondo
            turno (`start_effettivi >= 2`)
    finale  lotta portata fino alla fine, per far scattare i siti di
            distruzione del lottatore
    cambio  due turni veri in una lotta selvatica: al turno 1 si **cambia
            Pokemon** (l'avversario non sopravvive a un attacco), al turno 2 si
            attacca — e' la corsa che misura `start_effettivi >= 2`
    sino    lotta allenatore: dopo il KO del primo Pokemon avversario il gioco
            chiede «vuoi cambiare?» -> menu Si/No (sito 0x0225FC0A).
            Richiede una fixture con un allenatore non battuto e più Pokémon.
    siti    copione minimo: basta restare in lotta mentre `sonda_fasi.py
            --siti-finti` spara a CPU ferma il `bl` di tutti e nove i siti

Per difetto ogni sottocomando parte da **ROM fredda** (salta l'intro, carica la
partita, cammina nell'erba fino all'incontro); con `--stato FILE` parte invece da
un savestate gia' preso, che deve stare nella cartella `--out` della corsa. Le
corse che contano gli avvii del moto vanno fatte **a freddo**: un savestate preso
al menu comandi e' gia' oltre il primo `Start` della lotta.

Uso:  copioni.py SOTTOCOMANDO FILE.script [opzioni]
GPL-3.0-or-later.
"""
from __future__ import annotations

import argparse

# --- schermo basso, menu comandi della lotta ------------------------------
LOTTA = (137, 82)        # riquadro grande centrale (FIGHT / LOTTA)
BORSA = (38, 165)        # in basso a sinistra (BAG / BORSA)
FUGA = (127, 170)        # in basso al centro (RUN / FUGA)
SQUADRA = (217, 165)     # in basso a destra (POKeMON)
MOSSA_1 = (64, 115)      # prima mossa, in alto a sinistra della lista
MOSSA_4 = (192, 115)     # quarta mossa, in basso a destra
SI = (64, 130)           # menu Si/No: «SI» a sinistra
NO = (192, 130)          # menu Si/No: «NO» a destra
SQUADRA_2A = (190, 60)   # secondo riquadro della lista squadra (colonna destra)
SQUADRA_MANDA = (128, 110)  # «SHIFT / CAMBIA» nel pannello del Pokemon scelto
TASCA_BALL = (192, 50)
OGGETTO_1 = (128, 45)
BORSA_INDIETRO = (238, 165)

# --- indirizzi osservati dal banco (blocco v5, cfr. sonda_fasi.py) --------
HITS = 0x023DBBA4
HITS_ON = 0x023DBBA8
CHUNK_ANIM = 0x023D8716          # interruttore della funzione (1 = accesa)
PIC0 = 0x022F0C08                # Pokepic del lottatore del giocatore
PIC1 = 0x022F0CB4                # Pokepic del lottatore avversario


def watch(pic0=PIC0, pic1=PIC1):
    """Le colonne di `frames.csv`: contatori del moto e campi dei due Pokepic."""
    righe = ["watch hits       0x%08X 4" % HITS,
             "watch hits_on    0x%08X 4" % HITS_ON,
             "watch chunk_anim 0x%08X 1" % CHUNK_ANIM]
    for n, pic in (("a0", pic0), ("a1", pic1)):
        righe += ["watch %s_yoff    0x%08X 2" % (n, pic + 0x2E),
                  "watch %s_affw    0x%08X 2" % (n, pic + 0x34),
                  "watch %s_active  0x%08X 1" % (n, pic + 0x58),
                  "watch %s_step    0x%08X 1" % (n, pic + 0x5B)]
    return "\n".join(righe) + "\n"


PROLOGO_FREDDO = """run 1
run 1799
tap A 2 180
tap A 2 180
tap A 2 240
tap A 2 150
tap A 2 150
tap A 2 150
run 240
write 0x%08X 1 1
capture 00-overworld.ppm
run 240 DOWN
run 240 DOWN
run 600
capture 03-incontro.ppm
run 420
capture 04-menu.ppm
read 0x%08X 4 1
""" % (CHUNK_ANIM, HITS)


def prologo(a):
    """Prologo da ROM fredda o da savestate, secondo le opzioni."""
    if a.stato:
        return "load %s\nrun 60\ncapture 04-menu.ppm\nread 0x%08X 4 1\n" % (
            a.stato, HITS)
    return PROLOGO_FREDDO


def seq(pref, n):
    """n fotogrammi CONSECUTIVI, uno scatto per fotogramma: e' su questi che
    `misura_pixel.py` conta i pixel diversi fra fotogrammi adiacenti."""
    o = []
    for i in range(n):
        o.append("capture %s%03d.ppm" % (pref, i))
        o.append("run 1")
    return "\n".join(o) + "\n"


def tocca(punto, attesa, nome=None):
    s = "touch %d %d 8\nrun %d\n" % (punto[0], punto[1], attesa)
    if nome:
        s += "capture %s\n" % nome
    return s + "read 0x%08X 4 1\n" % HITS


def indietro(volte=2, attesa=60, dopo=120, nome=None):
    s = "".join("tap B 2 %d\n" % attesa for _ in range(volte))
    s += "run %d\n" % dopo
    if nome:
        s += "capture %s\n" % nome
    return s + "read 0x%08X 4 1\n" % HITS


# --------------------------------------------------------------------------
def corsa_menu(a):
    """Da ROM fredda fino al menu comandi, e salva lo stato."""
    return (watch() + PROLOGO_FREDDO +
            "save %s\nstatus\nquit\n" % a.stato_da_salvare)


def corsa_fasi(a):
    n = a.fotogrammi
    s = [watch(), prologo(a)]
    s.append("# --- MENU comandi (riferimento) ---\n")
    s.append(seq("m", n))
    s.append("read 0x%08X 4 1\ncapture 09-menu-fine.ppm\n" % HITS)
    s.append("# --- BORSA ---\n" + tocca(BORSA, 90, "10-borsa.ppm"))
    s.append(seq("b", n))
    s.append("read 0x%08X 4 1\ncapture 19-borsa-fine.ppm\n" % HITS)
    s.append(indietro(nome="20-ritorno.ppm"))
    s.append("# --- SQUADRA ---\n" + tocca(SQUADRA, 120, "30-squadra.ppm"))
    s.append(seq("p", n))
    s.append("read 0x%08X 4 1\ncapture 39-squadra-fine.ppm\n" % HITS)
    s.append(indietro(dopo=150, nome="40-ritorno2.ppm"))
    s.append("# --- LISTA MOSSE ---\n" + tocca(LOTTA, 120, "50-mosse.ppm"))
    s.append(seq("l", n))
    s.append("read 0x%08X 4 1\n" % HITS)
    s.append("# --- MOSSA ESEGUITA ---\n" + tocca(MOSSA_4, 20, "55-scelta.ppm"))
    s.append("run 40\ncapture 60-mossa-t60.ppm\n")
    for pref, fine in (("a", "69-a.ppm"), ("c", "75-c.ppm"), ("d", "76-d.ppm")):
        s.append(seq(pref, n))
        s.append("read 0x%08X 4 1\ncapture %s\n" % (HITS, fine))
    s.append("run 240\ncapture 80-dopo-mossa.ppm\nread 0x%08X 4 1\n" % HITS)
    s.append("run 300\ncapture 81-dopo2.ppm\nread 0x%08X 4 1\nstatus\nquit\n"
             % HITS)
    return "".join(s)


def corsa_borsa(a):
    """Sottomenu reali della Borsa: osserva senza consumare oggetti."""
    n = a.fotogrammi
    return (watch() + prologo(a) + seq("m", n) +
            tocca(BORSA, 160, "10-borsa.ppm") + seq("b", n) +
            tocca(TASCA_BALL, 120, "20-tasca.ppm") + seq("t", n) +
            tocca(OGGETTO_1, 120, "30-oggetto.ppm") + seq("o", n) +
            tocca(BORSA_INDIETRO, 120) * 3 + "capture 60-lotta.ppm\n" +
            "status\nquit\n")


def corsa_turni(a):
    """Due turni: menu -> mossa -> attesa -> menu -> mossa. Si guarda se il
    moto riparte al secondo turno (`start_effettivi >= 2`)."""
    n = a.fotogrammi
    s = [watch(), prologo(a)]
    for turno in (1, 2):
        s.append("# --- TURNO %d: menu ---\n" % turno)
        s.append(seq("t%d" % turno, n))
        s.append("read 0x%08X 4 1\ncapture t%d-00-menu.ppm\n" % (HITS, turno))
        s.append(tocca(LOTTA, 120, "t%d-10-mosse.ppm" % turno))
        s.append(tocca(MOSSA_1, 20, "t%d-20-scelta.ppm" % turno))
        # l'esecuzione del turno: si lascia scorrere e si guarda tornare il menu
        for k in range(a.attese):
            s.append("run 120\ncapture t%d-3%d-turno.ppm\nread 0x%08X 4 1\n"
                     % (turno, k, HITS))
    s.append("run 300\ncapture 90-fine.ppm\nread 0x%08X 4 1\nstatus\nquit\n"
             % HITS)
    return "".join(s)


def corsa_finale(a):
    """Lotta portata fino alla fine: la prima mossa basta a mettere KO
    l'avversario, poi si preme A finche' si torna in overworld."""
    s = [watch(), prologo(a)]
    s.append(tocca(LOTTA, 120, "50-mosse.ppm"))
    s.append(tocca(MOSSA_4, 20, "55-scelta.ppm"))
    for k in range(a.attese):
        s.append("run 120\ncapture f%02d.ppm\nread 0x%08X 4 1\n" % (k, HITS))
        s.append("tap A 2 60\n")
    s.append("run 600\ncapture 95-dopo-lotta.ppm\nread 0x%08X 4 1\n" % HITS)
    s.append("run 600\ncapture 96-overworld.ppm\nread 0x%08X 4 1\nstatus\nquit\n"
             % HITS)
    return "".join(s)


def corsa_sino(a):
    """Lotta allenatore: si attacca finche' il primo Pokemon avversario cade;
    con lo stile «cambio» il gioco apre allora il menu Si/No."""
    s = [watch(), prologo(a)]
    for giro in range(a.attese):
        s.append("# --- attacco %d ---\n" % giro)
        s.append(tocca(LOTTA, 120, "s%02d-mosse.ppm" % giro))
        s.append(tocca(MOSSA_1, 20, "s%02d-scelta.ppm" % giro))
        for k in range(4):
            s.append("run 120\ncapture s%02d-%d.ppm\nread 0x%08X 4 1\n"
                     % (giro, k, HITS))
    s.append("run 300\ncapture 99-fine.ppm\nread 0x%08X 4 1\nstatus\nquit\n"
             % HITS)
    return "".join(s)


def corsa_cambio(a):
    """Due turni veri in una lotta selvatica: al turno 1 si **cambia Pokemon**
    (l'avversario e' troppo debole per sopravvivere a un attacco), al turno 2 si
    attacca. Serve a vedere se il moto **riparte** al secondo turno
    (`start_effettivi >= 2`) e, insieme, il caso «il Pokepic cambia sotto il
    task» del rischio R2."""
    n = a.fotogrammi
    s = [watch(), prologo(a)]
    s.append("# --- TURNO 1: menu ---\n")
    s.append(seq("u", n))
    s.append("read 0x%08X 4 1\ncapture t1-00-menu.ppm\n" % HITS)
    s.append("# --- TURNO 1: cambio ---\n")
    s.append(tocca(SQUADRA, 150, "t1-10-squadra.ppm"))
    s.append(tocca(SQUADRA_2A, 90, "t1-20-scelto.ppm"))
    s.append(tocca(SQUADRA_MANDA, 120, "t1-30-manda.ppm"))
    for k in range(a.attese):
        s.append("run 120\ncapture t1-4%d-turno.ppm\nread 0x%08X 4 1\n"
                 % (k, HITS))
    s.append("# --- TURNO 2: menu ---\n")
    s.append(seq("v", n))
    s.append("read 0x%08X 4 1\ncapture t2-00-menu.ppm\n" % HITS)
    s.append(tocca(LOTTA, 120, "t2-10-mosse.ppm"))
    s.append(tocca(MOSSA_1, 20, "t2-20-scelta.ppm"))
    for k in range(4):
        s.append("run 120\ncapture t2-3%d-turno.ppm\nread 0x%08X 4 1\n"
                 % (k, HITS))
    s.append("status\nquit\n")
    return "".join(s)


def corsa_siti(a):
    """Copione minimo: basta stare nella lotta mentre la sonda `--siti-finti`
    spara a CPU ferma il `bl` di tutti e nove i siti."""
    s = [watch(), prologo(a)]
    s.append("capture 01-prima.ppm\nread 0x%08X 4 1\n" % HITS)
    for k in range(a.attese):
        s.append("run 120\ncapture n%02d.ppm\nread 0x%08X 4 1\n" % (k, HITS))
    s.append("status\nquit\n")
    return "".join(s)


CORSE = {"menu": corsa_menu, "fasi": corsa_fasi, "turni": corsa_turni,
         "finale": corsa_finale, "sino": corsa_sino, "siti": corsa_siti,
         "cambio": corsa_cambio, "borsa": corsa_borsa}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corsa", choices=sorted(CORSE))
    ap.add_argument("file")
    ap.add_argument("--fotogrammi", type=int, default=40,
                    help="scatti consecutivi per fase (misura dei pixel)")
    ap.add_argument("--attese", type=int, default=8,
                    help="blocchi di 120 fotogrammi di attesa per turno")
    ap.add_argument("--stato", help="savestate da cui partire (nella cartella "
                                    "--out della corsa)")
    ap.add_argument("--stato-da-salvare", default="menu.state")
    a = ap.parse_args()
    testo = CORSE[a.corsa](a)
    with open(a.file, "w") as f:
        f.write(testo)
    print("scritto %s (%d righe)" % (a.file, testo.count("\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
