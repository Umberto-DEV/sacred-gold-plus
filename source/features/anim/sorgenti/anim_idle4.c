/* Sacred Gold Plus 1.2 — `sgp.anim` **v4**: il task del moto di attesa in
 * lotta, più la pulizia alla sospensione. GPL-3.0-or-later.
 *
 * Discende da `SGP-1.2-ANIM-B-03/sorgenti/anim_idle2b.c`. Le differenze, e il
 * perché di ciascuna, stanno in cima a `sgp_anim4.h` (D1 stato sporco, D2 voci
 * mai liberate, D3 interruttore letto senza guardia).
 *
 * Il ciclo di vita del moto è tutto del gioco, ed è stato letto sul binario e
 * confermato a runtime:
 *   - `ov12_02261FD4` (0x02261FD4) avvia il task. **Un solo sito di chiamata**,
 *     0x0225DC8A, dentro la selezione del comando del giocatore; il letterale
 *     0x0226200C che contiene l'indirizzo del task è **l'unico in tutta la
 *     ROM** (scansione dei 130 moduli). Rifiuta di avviarlo se il task esiste
 *     già o se il tipo di lotta è Safari/Parco Amici.
 *   - `ov12_02262014` (0x02262014) lo ferma. **Nove siti di chiamata.**
 * Conseguenza misurata, e da dire con chiarezza: in HGSS il rimbalzo di attesa
 * **non gira per tutta la lotta**, gira mentre il giocatore sceglie il comando;
 * e **gira solo per i lottatori del giocatore** (in lotta selvatica: uno solo;
 * l'avversario non oscilla nemmeno nella 1.1). Questo blob non cambia il ciclo
 * di vita: ne sostituisce il contenuto.
 *
 * Le cinque migliorie restano quelle della fase 1b/2 (doc `10c` §3.1 idee
 * 1,2,3,4 e riparazione 7), invariate nel comportamento misurato.
 */
#include "sgp_anim4.h"

typedef void (*SetAttrFn)(void *pic, int attr, int value);
typedef void (*TaskFn)(void *task, void *data);

static void setattr2(void *pic, int attr, int value)
{
    ((SetAttrFn)SGP_POKEPIC_SETATTR)(pic, attr, value);
}

/* deg e' sempre uno dei 18 multipli di 20 in [0,340]: (deg*205)>>12 e'
 * esattamente deg/20 su quell'insieme, e non costa una divisione. */
static u32 fase_da_gradi(u32 deg)
{
    u32 idx = (deg * 205u) >> 12;
    if (idx >= (u32)SGP_FASI) {
        idx = (u32)SGP_FASI - 1u;
    }
    return idx;
}

/* Arrotondamento al piu' vicino di (u * k / 16) con u in [-16,16].
 * Con k = 3 riproduce ESATTAMENTE la tab_y della fase 1. */
static s32 scala_unita(s32 u, s32 k)
{
    return (u * k + 8) >> 4;
}

/* La scala affine e' un canale conteso (99 siti la scrivono): ci si permette
 * di toccarla solo dentro una finestra stretta attorno a 1.0, cioe' quando
 * nessun altro sta scalando lo sprite. La stessa condizione vale per SCRIVERE
 * (3c del task) e per RIMETTERE A POSTO (pulizia): se qualcun altro ha preso
 * il canale, non glielo si strappa. */
static u32 scala_nostra(u8 *pic)
{
    /* |x| <= W scritto come (unsigned)(x + W) <= 2W: un confronto invece di
     * due piu' il valore assoluto, e la stessa condizione esatta. */
    u32 dw = (u32)((s32)(*(volatile s16 *)(pic + PP_AFFINEW))
                   - (s32)SGP_SCALA_UNO + (s32)SGP_SCALA_FINESTRA);
    u32 dh = (u32)((s32)(*(volatile s16 *)(pic + PP_AFFINEH))
                   - (s32)SGP_SCALA_UNO + (s32)SGP_SCALA_FINESTRA);
    return (dw <= 2u * (u32)SGP_SCALA_FINESTRA
            && dh <= 2u * (u32)SGP_SCALA_FINESTRA) ? 1u : 0u;
}

/* Trova (o crea) la voce del lottatore. L'identita' e' il puntatore
 * all'OpponentData: ogni lottatore ne ha uno suo, e sono stabili per tutta
 * la lotta. Quattro voci bastano: quattro e' il massimo di lottatori, e dalla
 * v4 una voce torna LIBERA quando il gioco ferma il moto di quel lottatore
 * (`sgp_pulisci`), quindi lo sfratto a giro e' davvero l'ultima spiaggia e non
 * piu' il caso normale della seconda lotta. */
static SgpAnim2Slot *slot_per(SgpAnim2State *st, u32 od, u32 pic, u32 *indice)
{
    SgpAnim2Slot *s;
    u32 i;

    for (i = 0; i < (u32)SGP_SLOT; i++) {
        if (SGP_SLOTS[i].od == od) {
            break;
        }
    }
    if (i >= (u32)SGP_SLOT) {
        for (i = 0; i < (u32)SGP_SLOT; i++) {
            if (SGP_SLOTS[i].od == 0u) { /* un OpponentData non e' mai a 0 */
                break;
            }
        }
        if (i >= (u32)SGP_SLOT) { /* tutte occupate: sfratto a giro */
            i = (u32)st->rr & 3u;
            st->rr = (u8)(i + 1u);
        }
    }
    *indice = i;
    s = &SGP_SLOTS[i];
    if (s->od != od || s->pic != pic) {
        /* lottatore nuovo, o stesso lottatore con un Pokepic nuovo: il valore
         * a riposo dell'ombra va ripreso dal gioco, e il battito riparte.
         * LCG seminato dal contatore di esecuzioni (il "contatore di
         * fotogrammi" del task) mescolato col puntatore, cosi' due lottatori
         * creati nello stesso fotogramma non condividono la sequenza. */
        s->od = od;
        s->pic = pic;
        s->rng = st->hits * 1103515245u + od + 12345u;
        /* {base76,last76} e {blink_left,blink_wait,blink_cnt,usato} sono due
         * parole intere della voce: si azzerano insieme (little-endian, `usato`
         * e' il byte piu' significativo della seconda) con due `str` invece di
         * sei accessi stretti. Stessa struttura, stessi valori finali. */
        ((u32 *)s)[3] = 0u;
        ((u32 *)s)[4] = 0x01000000u;
    }
    return s;
}

static u32 lcg(SgpAnim2Slot *s)
{
    u32 r = s->rng * 1664525u + 1013904223u;
    s->rng = r;
    return r >> 8; /* i bit alti sono i buoni in un LCG */
}

/* ------------------------------------------------------------------------
 * D1/D2 — la pulizia alla sospensione.
 *
 * Chiamata dalla CODA di `ov12_02262014`, cioe' quando il gioco ha appena
 * distrutto il task di QUESTO lottatore e sta per rimettere `yOffset = 0` da
 * sé. Rimette a posto i tre canali che il gioco NON ripulisce e che scriviamo
 * noi, e libera la voce.
 *
 * Regole, tutte per non strappare un canale a chi l'ha preso nel frattempo:
 *   - la posa torna a 0 solo se l'interprete di `a/1/8/0` non sta lavorando
 *     (`animActive == 0`); se sta lavorando la posa e' sua e la riscrive lui;
 *   - la scala torna a 1.0 solo dentro la stessa finestra in cui ci eravamo
 *     permessi di scriverla;
 *   - l'ombra torna al valore a riposo CATTURATO solo se il valore attuale e'
 *     ancora quello che abbiamo scritto noi.
 *
 * A interruttore spento non esiste nessuna voce con questo `od` (il task
 * ritorna prima di crearla), quindi il ciclo non trova niente e **non scrive
 * un solo byte** nella memoria del gioco: e' il motivo per cui la
 * spegnibilita' resta byte-identica anche con il gancio di coda installato.
 * ------------------------------------------------------------------------ */
void sgp_pulisci(void *data)
{
    SgpAnim2State *st = SGP_STATO2;
    SgpAnim2Slot *s;
    u8 *od = (u8 *)data;
    u8 *pic;
    u32 *w;
    u32 i;

    /* `od` non puo' essere nullo qui: `ov12_02262014` l'ha gia' dereferenziato
     * a 0x0226201C (`ldr r0,[r4,#0x198]`) prima di arrivare alla coda. */
    st->stop_visti = st->stop_visti + 1u;
    for (i = 0; i < (u32)SGP_SLOT; i++) {
        s = &SGP_SLOTS[i];
        if (s->od != (u32)od) {
            continue;
        }
        pic = (u8 *)s->pic;
        if (pic != 0) {
            if (*(volatile u8 *)(pic + PP_ANIMACTIVE) == 0u) {
                setattr2(pic, POKEPIC_ANIM_STEP, 0);
            }
            if (scala_nostra(pic) != 0u) {
                setattr2(pic, POKEPIC_AFFINEW, (int)SGP_SCALA_UNO);
                setattr2(pic, POKEPIC_AFFINEH, (int)SGP_SCALA_UNO);
            }
            if ((s16)(*(volatile s16 *)(pic + PP_SHADOW_YOFF)) == s->last76) {
                setattr2(pic, POKEPIC_SHADOW_YOFF, (int)s->base76);
            }
        }
        /* la voce torna LIBERA: `od` a 0 e' la condizione che `slot_per()`
         * cerca. Le tre parole azzerate insieme coprono, nell'ordine della
         * struttura, {od}, {base76,last76} e {blink_left,blink_wait,blink_cnt,
         * usato}: sono byte del NOSTRO blocco, non del gioco. */
        w = (u32 *)s;
        w[0] = 0u;
        w[3] = 0u;
        w[4] = 0u;
        st->puliti = st->puliti + 1u;
    }
}

/* Trampolina del gancio di coda, 4 byte scritti a 0x02262032.
 *
 * Registri vivi al sito, letti sul disassemblato di `ov12_02262014`:
 *   r4 = OpponentData*      (impostato a 0x02262016, `adds r4,r0,#0`)
 *   r2 = 0                  (impostato a 0x02262028, `movs r2,#0`)
 *   r0, r1, r3 = morti      (r0 e' stato il task, letto e usato a 0x02262022)
 *   lr = morto              (la funzione l'ha gia' salvato con `push {r4,lr}`
 *                            a 0x02262014 e ritorna con `pop {r4,pc}`)
 * Percio' una `BL` puo' clobberare lr senza danno, e r4 viene comunque
 * ripristinato dal `pop` del gioco.
 *
 * Le due istruzioni sostituite sono ripetute in coda, prima del ritorno:
 *   0x02262032  ldr r0,[r4,#0x20]   (il Pokepic)
 *   0x02262034  movs r1,#4          (POKEPIC_YOFFSET)
 * piu' `movs r2,#0`, perche' r2 valeva 0 al sito e noi lo clobberiamo.
 * Il `push`/`pop` di due parole conserva l'allineamento a 8 della pila. */
__attribute__((naked, used, section(".text")))
void sgp_idle_stop(void)
{
    __asm__ volatile(
        "push {r4, lr}\n\t"
        "adds r0, r4, #0\n\t"
        "bl   sgp_pulisci\n\t"
        "ldr  r0, [r4, #0x20]\n\t" /* istruzione sostituita 1 */
        "movs r1, #4\n\t"          /* istruzione sostituita 2 */
        "movs r2, #0\n\t"          /* r2 era 0 al sito: lo rimettiamo */
        "pop  {r4, pc}\n\t");
}

void sgp_idle_task2(void *task, void *data)
{
    SgpAnim2State *st = SGP_STATO2;
    SgpAnim2Slot *s;
    u8 *od = (u8 *)data;
    u8 *pic;
    u32 deg, idx, cls, slot;
    s32 u, y;
    u8 flags;

    /* 1. Il task vanilla, per primo e sempre: fa avanzare `degrees` e scrive
     *    il rimbalzo +-1 px. Cosi' lo stato del gioco a funzione spenta e'
     *    identico al byte, e `degrees` resta la sorgente di fase. */
    ((TaskFn)SGP_VANILLA_TASK)(task, data);

    st->hits = st->hits + 1u;

    /* D3: l'abilitazione passa dall'accessore unico di `sgp_chunk.h`, che
     * controlla la guardia 0x5A del blocco di D1 e `load_status` (RIFIUTATO e
     * «non ancora letto» valgono 0 = comportamento 1.1) prima di leggere il
     * byte `anim`. Prima si leggeva quel byte alla cieca: segnalazione S9 di
     * SGP-1.2-QUALITA-NATIVO-01. `st->flags` resta il byte diagnostico
     * (l'ultimo valore applicato), riletto da `tools/rileggi_anim.py` (L4). */
    flags = sgp_chunk_opzione(SGP_CHUNK_ANIM_ADDR) != 0u ? (u8)SGP_F_TUTTI : 0u;
    st->flags = flags;
    if ((flags & SGP_F_TUTTI) == 0u) {
        return; /* SPENTO: fine. Nessuna scrittura oltre il vanilla. */
    }

    pic = *(u8 **)(od + OD_POKEPIC);
    if (pic == 0) {
        return;
    }

    /* 2. L'interprete di a/1/8/0 comanda quando animActive != 0: non tocchiamo
     *    NIENTE, e spegniamo un eventuale battito in corso, cosi' che la posa B
     *    non possa MAI essere scritta da noi mentre l'interprete lavora. */
    if (*(volatile u8 *)(pic + PP_ANIMACTIVE) != 0u) {
        st->hits_busy = st->hits_busy + 1u;
        return;
    }

    /* Il vanilla ha appena fatto il wrap di `degrees` in [0,360): la sola
     * guardia che serve e' il tetto sull'indice, ed e' dentro
     * `fase_da_gradi()`. Due guardie per la stessa cosa erano una di troppo. */
    deg = (u32)(*(volatile u16 *)(od + OD_DEGREES));

    s = slot_per(st, (u32)od, (u32)pic, &slot);
    st->last_slot = (u8)slot;

    idx = fase_da_gradi(deg);
    if ((flags & SGP_F_FASE) != 0u) { /* idea 2: i lottatori non all'unisono */
        idx += (u32)SGP_PAR[PAR_FASE + slot];
        if (idx >= (u32)SGP_FASI) {
            idx -= (u32)SGP_FASI;
        }
    }
    st->last_idx = (u8)idx;

    /* idea 4: classe di taglia dai bit 5-6 di pokepic+0x6C (`shadow.size`,
     * attributo 46), che l'allestimento del lottatore scrive dai dati di lotta
     * della SPECIE. NON sono i bit 0-1, che sono `palSlot`. */
    cls = (flags & SGP_F_TAGLIA) != 0u
              ? (((u32)(*(volatile u16 *)(pic + PP_SHADOW_FLAGS))
                  >> PP_TAGLIA_SHIFT) & 3u)
              : 1u;
    st->last_cls = (u8)cls;

    u = (s32)SGP_TAB_U[idx];
    y = scala_unita(u, (s32)SGP_PAR[PAR_AMP + cls]);

    /* 3a. Respiro verticale. yOffset (+0x2E) e' un canale ESCLUSIVO di questo
     *     task fuori dalle animazioni: la scansione di tutti i file `asm` di
     *     pret non trova un solo sito che scriva l'attributo 4 con immediato,
     *     nemmeno nell'overlay 7 (le animazioni delle mosse), che muove lo
     *     sprite con X/Y (attributi 0/1) e con la scala affine. */
    if ((flags & SGP_F_RESPIRO) != 0u) {
        setattr2(pic, POKEPIC_YOFFSET, (int)y);
        st->last_y = (s16)y;

        /* 3a-bis. OMBRA ANCORATA: compensa in controfase la stessa yOffset che
         *         DrawAll somma alla Y dell'ombra (`pokepic.c:425`, sotto
         *         `shadow.shouldAdjustY`). Il valore a riposo si cattura dal
         *         gioco e si ri-cattura appena il gioco lo riscrive. */
        if ((flags & SGP_F_OMBRA) != 0u) {
            s32 cur = (s32)(*(volatile s16 *)(pic + PP_SHADOW_YOFF));
            s32 v;
            if ((s16)cur != s->last76) {
                s->base76 = (s16)cur;
            }
            v = (s32)s->base76 - y;
            setattr2(pic, POKEPIC_SHADOW_YOFF, (int)v);
            s->last76 = (s16)v;
            st->last_s76 = (s16)v;
        }
    }

    /* 3b. Battito di ciglia con la posa B (idea 3). */
    if ((flags & SGP_F_POSA) != 0u) {
        u32 p;
        if (s->blink_left != 0u) {
            s->blink_left = (u8)(s->blink_left - 1u);
            p = 1u;
        } else if (s->blink_wait != 0u) {
            s->blink_wait = (u8)(s->blink_wait - 1u);
            p = 0u;
        } else {
            u32 r = lcg(s);
            u32 dur = (u32)SGP_PAR[PAR_BLINK_DUR] + (r & 1u); /* 2 o 3 */
            s->blink_cnt = (u8)(s->blink_cnt + 1u);
            if (s->blink_cnt >= SGP_PAR[PAR_RARO_OGNI]) { /* "comune x3 poi rara" */
                s->blink_cnt = 0u;
                dur += (u32)SGP_PAR[PAR_RARO_PIU];
                st->rari = st->rari + 1u;
            }
            s->blink_left = (u8)(dur - 1u);
            s->blink_wait = (u8)((u32)SGP_PAR[PAR_BLINK_MIN]
                                 + ((r >> 4) & (u32)SGP_PAR[PAR_BLINK_MASK]));
            st->blinks = st->blinks + 1u;
            p = 1u;
        }
        setattr2(pic, POKEPIC_ANIM_STEP, (int)p);
        st->last_step = (u8)p;
    }

    /* 3c. Squash & stretch in controfase (idea 1). */
    if ((flags & SGP_F_SCALA) != 0u && scala_nostra(pic) != 0u) {
        s32 d = scala_unita(u, (s32)SGP_PAR[PAR_SCA + cls]);
        /* in basso (y > 0) -> piu' largo e piu' basso */
        setattr2(pic, POKEPIC_AFFINEW, (int)((s32)SGP_SCALA_UNO + d));
        setattr2(pic, POKEPIC_AFFINEH, (int)((s32)SGP_SCALA_UNO - d));
    }

    st->hits_on = st->hits_on + 1u;
}
