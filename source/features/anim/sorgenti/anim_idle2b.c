/* SGP-1.2-ANIM-B-02 — FASE 2b: il task di idle della 1.2, terzo giro.
 *
 * Copiato da `anim_idle2.c` (fase 2/2a, invariato da ANIM-B-01 fase 1b):
 * STESSO gancio (ov012 0x0226200C, valore 0x0226203D sostituito con
 * l'indirizzo di `sgp_idle_task2`), STESSO ciclo di vita/priorita'/coda.
 *
 * UNICA differenza (mandato 02b): l'abilitazione non si legge piu' da
 * `st->flags` (un byte che l'iniettore scriveva una volta sola in QUESTO
 * blocco), ma dal campo `anim` del chunk di salvataggio di PLUS-03
 * (`SGP-1.2-PLUS-03/CONTRATTO-CHUNK.md` §2, 0x023D8716), ricalcolata a OGNI
 * esecuzione: 0 o chunk assente (che D1 garantisce leggere 0 in quello
 * stesso byte, §4) -> si chiama SOLO il task vanilla, byte-identico; diverso
 * da 0 -> tutte le migliorie della fase 1b/2 (SGP_F_TUTTI). Vedi il commento
 * in cima a `sgp_anim2b.h` e il punto 1 piu' sotto.
 *
 * Regola d'oro, invariata: con l'abilitazione spenta questa funzione chiama
 * il task vanilla e ritorna; nessun byte della memoria del gioco cambia
 * rispetto alla 1.1.
 *
 * LE QUATTRO MIGLIORIE A COSTO QUASI ZERO (doc 10c §3.1, idee 1,2,3,4) e la
 * RIPARAZIONE DELL'OMBRA (idea 7, rischio n. 1 del RAPPORTO §10):
 *
 *  0. OMBRA ANCORATA. PokepicManager_DrawAll ricalcola a ogni disegno, se
 *     il bit 3 di pokepic+0x6C e' acceso (0x02008462..0x02008482 del binario
 *     della 1.1):
 *          shadow.Y (+0x72) = shadow.yOffset (+0x76) + yCenter (+0x26)
 *                             + yOffset (+0x2E)
 *     La Y del CORPO invece vale (0x0200838C..0x020083AA):
 *          corpo.Y = yCenter (+0x26) - altezzaScalata/2 + yOffset (+0x2E)
 *                    - shadow.height (+0x6E)
 *     Cioe' yOffset entra in TUTTI E DUE. Scrivendo, nello stesso passo,
 *          yOffset      = y
 *          shadow.yOff  = base76 - y
 *     la somma dell'ombra torna costante (base76 + yCenter) mentre il corpo
 *     si muove di y. `base76` e' il valore a riposo, CATTURATO dal gioco e
 *     ri-catturato ogni volta che il gioco lo riscrive (l'unico scrittore in
 *     lotta e' l'allestimento del lottatore, ov012 0x0226137C).
 *
 *  1. SQUASH & STRETCH in controfase: affineW = 0x100 + d, affineH = 0x100 - d
 *     con d proporzionale al seno e di segno opposto a y. Volume quasi
 *     costante: in basso schiacciato e largo, in alto allungato e stretto.
 *
 *  2. SFASAMENTO FRA I LOTTATORI: `degrees` parte da 180 per tutti, quindi in
 *     vanilla i battler respirano all'unisono. La fase viene ruotata di
 *     par[PAR_FASE + slot] passi: slot 0 = 0, slot 1 = mezzo giro.
 *
 *  3. BATTITO DI CIGLIA: la posa B non e' piu' un intervallo fisso, ma dura
 *     2..3 esecuzioni a intervalli pseudo-casuali estratti da un LCG a 32 bit
 *     seminato dal contatore di esecuzioni. Ogni PAR_RARO_OGNI battiti
 *     comuni ne arriva uno "raro", piu' lungo: e' la cadenza "comune x3 poi
 *     rara" della Gen 5 (10c §1.5). MAI durante animActive, per costruzione:
 *     l'unica scrittura della posa sta dopo la guardia su animActive, e il
 *     task si astiene da tutto quando l'interprete lavora.
 *
 *  4. AMPIEZZA PER TAGLIA: i bit 5-6 di pokepic+0x6C sono la TAGLIA
 *     dell'ombra. Li scrive l'allestimento del lottatore (ov012 0x02261358,
 *     attributo 46) da un campo dei dati di lotta della SPECIE (a/1/8/0,
 *     "Shadow"), e DrawAll li usa per scegliere la cella dell'ombra
 *     (0x02008484: `lsls #0x19; lsrs #0x1e; lsls r2,r0,#4`, cioe' indice
 *     (bit5-6)*16 nella tavola delle celle). E' la misura di taglia della
 *     specie gia' presente nel Pokepic: costa una `ldrh`, uno shift e una
 *     `and`. Ampiezza e scala si leggono da par[PAR_AMP + classe] e
 *     par[PAR_SCA + classe].
 *
 *     ATTENZIONE, e' un errore che ho fatto e corretto misurando: i bit 0-1
 *     dello stesso campo (attributo 42) NON sono la taglia ma il LATO del
 *     lottatore (ov012 0x0226134E: posizione del battler, dimezzata), e
 *     scelgono la cella dello sprite. A runtime valgono 0 per il nostro
 *     Pokemon e 1 per l'avversario, in qualunque lotta.
 *
 * NON si fa (10c §3.1 idea 5): nessuna rotazione. Il DS campiona le texture a
 * punto singolo: ruotare pixel art allineata alla griglia sdoppia i contorni,
 * ed e' esattamente il difetto della Gen 5 che non vogliamo importare.
 */
#include "sgp_anim2b.h"

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

/* Trova (o crea) la voce del lottatore. L'identita' e' il puntatore
 * all'OpponentData: ogni lottatore ne ha uno suo, e sono stabili per tutta
 * la lotta. Quattro voci bastano: quattro e' il massimo di lottatori. */
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
        s->base76 = 0;
        s->last76 = 0;
        s->blink_left = 0u;
        s->blink_wait = 0u;
        s->blink_cnt = 0u;
        s->usato = 1u;
    }
    return s;
}

static u32 lcg(SgpAnim2Slot *s)
{
    u32 r = s->rng * 1664525u + 1013904223u;
    s->rng = r;
    return r >> 8; /* i bit alti sono i buoni in un LCG */
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

    /* FASE 2b: l'abilitazione viene dal chunk di salvataggio di PLUS-03
     * (0x023D8716, "anim"), non piu' da un byte scritto una volta in questo
     * blocco. 0 o chunk assente (che D1 legge gia' 0 in quello stesso byte,
     * CONTRATTO-CHUNK.md §4) -> SPENTO; diverso da 0 -> tutte le migliorie
     * (SGP_F_TUTTI, come fase 1b). `st->flags` resta un byte diagnostico
     * (l'ultimo valore applicato), riletto senza modifiche da
     * `tools/rileggi_anim.py` (L4). */
    flags = (*(volatile u8 *)SGP_CHUNK_ANIM_ADDR != 0u) ? (u8)SGP_F_TUTTI : 0u;
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

    deg = (u32)(*(volatile u16 *)(od + OD_DEGREES));
    if (deg >= 360u) {
        return; /* difensiva: il vanilla ha gia' fatto il wrap */
    }

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

    /* idea 4: classe di taglia dal Pokepic (bit 0-1 di +0x6C). */
    cls = (flags & SGP_F_TAGLIA) != 0u
              ? (((u32)(*(volatile u16 *)(pic + PP_SHADOW_FLAGS))
                  >> PP_TAGLIA_SHIFT) & 3u)
              : 1u;
    st->last_cls = (u8)cls;

    u = (s32)SGP_TAB_U[idx];
    y = scala_unita(u, (s32)SGP_PAR[PAR_AMP + cls]);

    /* 3a. Respiro verticale. yOffset (+0x2E) e' un canale ESCLUSIVO di questo
     *     task fuori dalle animazioni. */
    if ((flags & SGP_F_RESPIRO) != 0u) {
        setattr2(pic, POKEPIC_YOFFSET, (int)y);
        st->last_y = (s16)y;

        /* 3a-bis. OMBRA ANCORATA: compensa in controfase la stessa yOffset che
         *         DrawAll somma alla Y dell'ombra. Il valore a riposo si
         *         cattura dal gioco e si ri-cattura appena il gioco lo
         *         riscrive (confronto con quello che abbiamo scritto noi). */
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

    /* 3c. Squash & stretch in controfase (idea 1). affineW/H sono per-sprite
     *     e contesi (99 siti): si scrive solo dentro una finestra stretta
     *     attorno a 1.0, cioe' se nessun altro sta scalando lo sprite. */
    if ((flags & SGP_F_SCALA) != 0u) {
        s32 w = (s32)(*(volatile s16 *)(pic + PP_AFFINEW));
        s32 h = (s32)(*(volatile s16 *)(pic + PP_AFFINEH));
        s32 dw = w - (s32)SGP_SCALA_UNO;
        s32 dh = h - (s32)SGP_SCALA_UNO;
        if (dw < 0) {
            dw = -dw;
        }
        if (dh < 0) {
            dh = -dh;
        }
        if (dw <= (s32)SGP_SCALA_FINESTRA && dh <= (s32)SGP_SCALA_FINESTRA) {
            s32 d = scala_unita(u, (s32)SGP_PAR[PAR_SCA + cls]);
            /* in basso (y > 0) -> piu' largo e piu' basso */
            setattr2(pic, POKEPIC_AFFINEW, (int)((s32)SGP_SCALA_UNO + d));
            setattr2(pic, POKEPIC_AFFINEH, (int)((s32)SGP_SCALA_UNO - d));
        }
    }

    st->hits_on = st->hits_on + 1u;
}
