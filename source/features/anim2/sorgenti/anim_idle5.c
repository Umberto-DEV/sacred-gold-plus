/* Sacred Gold Plus — ANIM2 v5d. GPL-3.0-or-later.
 * Clock di attesa, HUD fermo, continuita' menu, isolamento delle animazioni
 * native e accento di posa B ancorato al respiro. Ciclo di vita, layout e
 * cronologia delle versioni sono documentati in sgp_anim5.h.
 */
#include "sgp_anim5.h"

typedef void (*SetAttrFn)(void *pic, int attr, int value);
typedef void (*TaskFn)(void *task, void *data);
typedef void (*AvviaFn)(void *data, void *bs);
typedef void (*FermaFn)(void *data);

/* `noinline`: nove siti di chiamata, e ognuno inlineato si porterebbe dietro
 * la sua copia del letterale 0x020087A5. Una sola `BL` costa 4 B a sito. */
__attribute__((noinline)) static void setattr5(void *pic, int attr, int value)
{
    ((SetAttrFn)SGP_POKEPIC_SETATTR)(pic, attr, value);
}

/* I due accessi a `BattleSystem` che si ripetono in quattro posti: il numero
 * di lottatori (troncato a quattro, quante sono le voci) e il puntatore
 * all'`OpponentData` del lottatore i. Fuori linea perche' la lettura e'
 * `volatile` e non si fattorizza da sola. */
__attribute__((noinline)) static u32 nlott(u32 bs)
{
    u32 n;

    if (bs == 0u) {
        return 0u;
    }
    n = *(volatile u32 *)(bs + BS_MAXBATT);
    return n > (u32)SGP_SLOT ? (u32)SGP_SLOT : n;
}

__attribute__((noinline)) static u32 lott(u32 bs, u32 i)
{
    return *(volatile u32 *)(bs + BS_BATTLERS + i * 4u);
}

/* L'interruttore passa dall'accessore unico di `sgp_chunk.h`, che controlla la
 * guardia 0x5A e `load_status` prima di leggere il byte `anim` (S9 di
 * SGP-1.2-QUALITA-NATIVO-01). Spento = comportamento 1.2.1 esatto. */
static u32 abilitato(void)
{
    return sgp_chunk_opzione(SGP_CHUNK_ANIM_ADDR) != 0u;
}

static u32 par16(u32 off)
{
    return (u32)SGP_PAR[off] | ((u32)SGP_PAR[off + 1u] << 8);
}

/* Tavola [-16,16] interpolata in ottavi e inviluppo [0,16].
 * Mantiene la precisione fino all'ultimo arrotondamento al pixel/scala. */
static s32 scala_unita(s32 u, s32 k)
{
    return (u * k + 1024) >> 11;
}

/* La scala affine e' un canale conteso (99 siti la scrivono): ci si permette
 * di toccarla solo dentro una finestra stretta attorno a 1.0, cioe' quando
 * nessun altro sta scalando lo sprite — sia per SCRIVERE sia per RIMETTERE A
 * POSTO. Durante l'animazione della mossa `ov007` la prende: la sospensione
 * scatta 3 fotogrammi prima del primo pixel (misurato), quindi il ritorno a
 * 1.0 avviene mentre il canale e' ancora nostro. */
static u32 scala_nostra(u8 *pic)
{
    u32 dw = (u32)((s32)(*(volatile s16 *)(pic + PP_AFFINEW))
                   - (s32)SGP_SCALA_UNO + (s32)SGP_SCALA_FINESTRA);
    u32 dh = (u32)((s32)(*(volatile s16 *)(pic + PP_AFFINEH))
                   - (s32)SGP_SCALA_UNO + (s32)SGP_SCALA_FINESTRA);
    return (dw <= 2u * (u32)SGP_SCALA_FINESTRA
            && dh <= 2u * (u32)SGP_SCALA_FINESTRA) ? 1u : 0u;
}

/* L'indice del lottatore dentro `BattleSystem`. Serve al SECONDO cancello, che
 * — a differenza del primo — e' per lottatore. Si calcola una volta sola, alla
 * creazione della voce, non a ogni giro. 0xFF = non trovato (nessun secondo
 * cancello: si preferisce non sospendere piuttosto che sospendere a caso). */
static u32 indice_lottatore(u32 bs, u32 od)
{
    u32 n = nlott(bs), i;

    for (i = 0; i < n; i++) {
        if (lott(bs, i) == od) {
            return i;
        }
    }
    return 0xFFu;
}

static u32 lcg(SgpAnim5Slot *s)
{
    u32 r = s->rng * 1664525u + 1013904223u;
    s->rng = r;
    return r >> 8; /* i bit alti sono i buoni in un LCG */
}

/* v5d — «riarma l'accento»: nessuna posa B in corso e un'attesa PIENA, presa
 * a caso nella stessa fascia di ogni altra attesa.
 *
 * Tre siti di chiamata, e sono tre correzioni in una sola funzione:
 *   - alla creazione della voce (S2 di A1 §3.3): la v5c metteva `blink_wait =
 *     BLINK_MIN` nudo, cosi' quattro lottatori creati nello stesso tick
 *     facevano il primo accento all'unisono;
 *   - quando un cancello si alza (B3 di A1 §3.2, misurato in A2 §6.2): il
 *     residuo di `blink_left` si congelava e faceva riapparire la posa B nel
 *     tick successivo alla caduta del cancello — un lampo a ogni mossa;
 *   - a voce liberata, per non lasciare un residuo a chi riusa l'indirizzo.
 * `noinline`: il corpo costa piu' di una BL, e i siti sono tre. */
__attribute__((noinline)) static void riarma(SgpAnim5Slot *s)
{
    s->blink_left = 0u;
    s->blink_wait = (u8)((u32)SGP_PAR[PAR_BLINK_MIN]
                         + ((lcg(s) >> 4) & (u32)SGP_PAR[PAR_BLINK_MASK]));
}

/* Trova (o crea) la voce del lottatore. L'identita' e' il puntatore
 * all'OpponentData. La voce si riazzera anche quando lo STESSO `od` presenta
 * un `Pokepic` diverso: e' la terza guardia chiesta dal rapporto T1-2 §3.1
 * (la finestra del lancio della Ball, che nessuno dei due cancelli copre). */
static SgpAnim5Slot *slot_per(SgpAnim5State *st, u32 od, u32 pic, u32 *indice)
{
    SgpAnim5Slot *s;
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
    if (s->od != od || s->pic != pic || s->bs_visto != st->bs) {
        /* M2 (A8b): senza il confronto su `bs` una seconda lotta che riusa gli
         * stessi indirizzi ereditava idx, fase, inviluppo e rng della prima. */
        s->od = od;
        s->pic = pic;
        s->bs_visto = st->bs;
        s->rng = st->hits * 1103515245u + od + 12345u;
        /* tre parole intere della voce, azzerate insieme: {base76,last76},
         * {blink_left,blink_wait,blink_cnt,usato} e {idx,sospeso,pad}. */
        ((u32 *)s)[3] = 0u;
        ((u32 *)s)[4] = 0x01000000u; /* usato = 1 */
        ((u32 *)s)[5] = 0u;          /* idx = 0, sospeso = 0 */
        s->idx = (u8)indice_lottatore(st->bs, od);
        riarma(s);
    }
    return s;
}

/* ------------------------------------------------------------------------
 * A3 — i tre cancelli della sospensione.
 *
 *  SGP_G_MOSSA     `[[BattleSystem+0x8C] + 0x10]`  — moveActive, per LOTTA.
 *  SGP_G_INGRESSO  `[[[BattleSystem+0x1C8]+0] + i*0x1D0 + 0x20] == 0`
 *                  — animazione d'ingresso, per LOTTATORE.
 *  SGP_G_ANIMACT   `[pokepic + 0x58]` — l'interprete di a/1/8/0 (guardia v4).
 *
 * Costo: tre `ldr` e tre confronti per giro nel caso normale.
 * ------------------------------------------------------------------------ */
static u32 cancelli_alzati(SgpAnim5State *st, SgpAnim5Slot *s, u8 *pic)
{
    u32 g = 0u;
    u32 abil = (u32)SGP_PAR[PAR_CANCELLI];
    u32 bs = st->bs;
    u32 a, mgr, base, n;

    if ((abil & (u32)SGP_G_ANIMACT) != 0u
        && *(volatile u8 *)(pic + PP_ANIMACTIVE) != 0u) {
        g |= (u32)SGP_G_ANIMACT;
    }
    if (bs == 0u) {
        return g;
    }
    if ((abil & (u32)SGP_G_MOSSA) != 0u) {
        a = *(volatile u32 *)(bs + BS_ANIMSYS);
        if (a != 0u && *(volatile u32 *)(a + AS_MOVEACTIVE) != 0u) {
            g |= (u32)SGP_G_MOSSA;
        }
    }
    if ((abil & (u32)SGP_G_INGRESSO) != 0u && s->idx < (u8)SGP_SLOT) {
        mgr = *(volatile u32 *)(bs + BS_SPECIEMGR);
        if (mgr != 0u) {
            base = *(volatile u32 *)(mgr + MG_BASE);
            n = (u32)(*(volatile u8 *)(mgr + MG_COUNT));
            if (base != 0u && (u32)s->idx < n
                && *(volatile u32 *)(base + (u32)s->idx * MG_PASSO + MG_FLAG) == 0u) {
                g |= (u32)SGP_G_INGRESSO;
            }
        }
    }
    return g;
}

/* Riporta lo sprite allo stato di riposo sui QUATTRO canali che scriviamo noi.
 * Le regole sono quelle della v4, per non strappare un canale a chi l'ha preso
 * nel frattempo:
 *   - la posa torna a 0 solo se l'interprete di `a/1/8/0` non sta lavorando;
 *   - la scala torna a 1.0 solo dentro la stessa finestra in cui ci eravamo
 *     permessi di scriverla;
 *   - l'ombra torna al valore a riposo CATTURATO solo se il valore attuale e'
 *     ancora quello che abbiamo scritto noi.
 * `yOffset` invece si scrive sempre: e' un canale esclusivo di questo task
 * fuori dalle animazioni (nessun sito di `pret` scrive l'attributo 4), ed e'
 * quello che deve tornare a zero perche' gli effetti di `ov007`, ancorati a
 * coordinate fisse, non seguono lo sprite (artefatto E4b). */
static void riposo(SgpAnim5Slot *s, u8 *pic)
{
    setattr5(pic, POKEPIC_YOFFSET, 0);
    if (*(volatile u8 *)(pic + PP_ANIMACTIVE) == 0u) {
        setattr5(pic, POKEPIC_ANIM_STEP, 0);
    }
    if (scala_nostra(pic) != 0u) {
        setattr5(pic, POKEPIC_AFFINEW, (int)SGP_SCALA_UNO);
        setattr5(pic, POKEPIC_AFFINEH, (int)SGP_SCALA_UNO);
    }
    if ((s16)(*(volatile s16 *)(pic + PP_SHADOW_YOFF)) == s->last76) {
        setattr5(pic, POKEPIC_SHADOW_YOFF, (int)s->base76);
    }
}

/* La pulizia alla fermata VERA: riporta a riposo e LIBERA la voce. Chiamata
 * dalla testa di `ov12_02262014` **prima** che il gioco distrugga il task
 * (la v4 lo faceva dalla coda, dopo). Il cambio d'ordine e' voluto: cosi' la
 * stessa funzione vale anche per la fermata soppressa, dove il task non muore.
 *
 * A interruttore spento non esiste nessuna voce con questo `od` (il task
 * ritorna prima di crearla), quindi il ciclo non trova niente e **non scrive
 * un solo byte** nella memoria del gioco: e' il motivo per cui la
 * spegnibilita' resta byte-identica. */
void sgp_pulisci(void *data)
{
    SgpAnim5State *st = SGP_STATO5;
    SgpAnim5Slot *s;
    u32 *w;
    u32 i;

    for (i = 0; i < (u32)SGP_SLOT; i++) {
        s = &SGP_SLOTS[i];
        if (s->od != (u32)data) {
            continue;
        }
        if (s->pic != 0u && s->pic == *(volatile u32 *)((u8 *)data + OD_POKEPIC)
            && (*(volatile u8 *)s->pic & 1u) != 0u
            && s->sospeso == 0u) {
            riposo(s, (u8 *)s->pic);
        }
        w = (u32 *)s;
        w[0] = 0u; /* od: la voce torna LIBERA */
        w[3] = 0u;
        w[4] = 0u;
        w[5] = 0u;
        st->puliti = st->puliti + 1u;
    }
}

/* ------------------------------------------------------------------------
 * A1 — lo stub d'avvio, al posto della `BL ov12_02261FD4` di 0x0225DC8A.
 *
 * Firma identica alla funzione che sostituisce, `(od, battleSystem)`: la `BL`
 * si limita a cambiare bersaglio, i registri al sito restano quelli.
 * A interruttore spento fa **esattamente** la chiamata di prima, una sola
 * volta e con gli stessi argomenti.
 * ------------------------------------------------------------------------ */
void sgp_avvia_tutti(void *data, void *bs)
{
    SgpAnim5State *st = SGP_STATO5;
    u32 b = (u32)bs;
    u32 n, i, odi;

    st->bs = b;
    ((AvviaFn)SGP_OV12_AVVIA)(data, bs); /* quello che c'era prima */
    st->avvii = st->avvii + 1u;
    if (abilitato() == 0u) {
        return;
    }
    ((FermaFn)SGP_FERMA_HUD)((u8 *)data + OD_HPBAR);
    n = nlott(b);
    for (i = 0; i < n; i++) {
        odi = lott(b, i);
        if (odi == 0u || odi == (u32)data) {
            continue;
        }
        /* `ov12_02261FD4` rifiuta da sé se il task esiste già o se la lotta è
         * Safari/Parco Amici: non serve ripetere quei due controlli qui. */
        ((AvviaFn)SGP_OV12_AVVIA)((void *)odi, bs);
        st->avvii = st->avvii + 1u;
    }
}

/* Ferma tutti prima della cattura, mentre tutti gli OpponentData sono vivi.
 * Non viene chiamata dai destructor. `dentro` resta un indicatore di debug. */
static void estendi(void *data)
{
    SgpAnim5State *st = SGP_STATO5;
    u32 b = st->bs;
    u32 n = nlott(b), i, odi;

    for (i = 0; i < n; i++) {
        odi = lott(b, i);
        if (odi == 0u || odi == (u32)data) {
            continue;
        }
        if (*(volatile u32 *)(odi + OD_TASK) == 0u) {
            continue; /* niente task: la fermata sarebbe a vuoto */
        }
        ((FermaFn)SGP_OV12_FERMA)((void *)odi);
        st->estesi = st->estesi + 1u;
    }
}

/* G4: il task di cattura riusa i Pokepic per Pokédex e soprannome.
 * Ferma tutti PRIMA di schedularlo; una cattura fallita torna all'avvio
 * normale del menu. getterWork è condiviso con EXP: non è un segnale. */
void *sgp_avvia_cattura(TaskFn fn, void *data, u32 priorita)
{
    typedef void *(*CreaFn)(TaskFn, void *, u32);
    if (abilitato() != 0u) {
        SGP_STATO5->bs = *(u32 *)data;
        estendi(0);
    }
    return ((CreaFn)SGP_CREA_TASK)(fn, data, priorita);
}

/* ------------------------------------------------------------------------
 * A2 — la politica di fermata. Chiamata dalla trampolina in testa a
 * `ov12_02262014`, con `lr` del chiamante letto dalla pila.
 * Rende 1 = «non fermare» (la trampolina esegue l'epilogo del gioco),
 *       0 = «ferma» (la trampolina rientra nella funzione).
 * ------------------------------------------------------------------------ */
u32 sgp_stop_politica(void *data, u32 lr)
{
    SgpAnim5State *st = SGP_STATO5;
    u32 i, m;

    if (abilitato() == 0u) {
        sgp_pulisci(data); /* A8b-A1: vedi sgp_idle_task5 */
        return 0u;         /* SPENTO: la fermata avviene, come nella 1.2.1 */
    }
    for (i = 0; i < (u32)SGP_N_SITI; i++) {
        if (SGP_SITI[i] == lr) {
            break;
        }
    }
    if (i < (u32)SGP_N_SITI) {
        m = par16((u32)PAR_SOPPRIMI);
        if (((m >> i) & 1u) != 0u) {
            st->soppressi = st->soppressi + 1u;
            return 1u; /* soppressa: il task resta vivo, sospende da sé */
        }
    }
    sgp_pulisci(data);
    /* Ogni destructor ferma il proprio task. Non visitare gli altri od:
     * il teardown nativo può averli già liberati. */
    return 0u;
}

/* ------------------------------------------------------------------------
 * La trampolina del gancio G2, 4 byte scritti a **0x02262016**.
 *
 * NON sulla prima istruzione: `push {r4,lr}` a 0x02262014 deve restare, perché
 * è quello che mette `lr` del chiamante sulla pila — e `lr` è il discriminante
 * di tutta la politica. Una `BL` sulla prima istruzione lo distruggerebbe.
 *
 * Le due istruzioni sostituite sono:
 *   0x02262016  adds r4, r0, #0     (r4 = OpponentData*)
 *   0x02262018  movs r0, #0x66      (0x66<<2 = 0x198, l'offset del task)
 * e il ritorno è a 0x0226201A (`lsls r0,r0,#2`).
 *
 * Registri: al sito r0 = od e r4/r1/r2/r3 sono liberi (la funzione ha già
 * salvato r4 del chiamante). Alla ripresa servono r0 = 0x66 e r4 = od.
 * Nel ramo «soppressa» si esegue l'epilogo del gioco (`pop {r4,pc}` di
 * 0x0226203A) dopo aver scartato il nostro frame: la funzione ritorna al
 * chiamante senza aver toccato niente.
 * ------------------------------------------------------------------------ */
__attribute__((naked, used, section(".text")))
void sgp_stop_testa(void)
{
    __asm__ volatile(
        "push {r4, lr}\n\t"         /* sp -> [r4n, lrn, r4salvato, lrchiamante] */
        "adds r4, r0, #0\n\t"       /* r4 = od, callee-saved: sopravvive alla BL */
        "ldr  r1, [sp, #0xC]\n\t"   /* lr del chiamante, dal push del gioco      */
        "bl   sgp_stop_politica\n\t"
        "cmp  r0, #0\n\t"
        "bne  1f\n\t"
        "adds r0, r4, #0\n\t"       /* r0 = od                                   */
        "pop  {r3, r4}\n\t"         /* r3 = r4n (scarto), r4 = lr nostro         */
        "adds r1, r4, #0\n\t"
        "adds r4, r0, #0\n\t"       /* istruzione sostituita 1                   */
        "movs r0, #0x66\n\t"        /* istruzione sostituita 2                   */
        "bx   r1\n\t"               /* -> 0x0226201A                             */
        "1:\n\t"
        "add  sp, #8\n\t"           /* scarta il nostro frame                    */
        "pop  {r4, pc}\n\t");       /* epilogo del gioco: ritorna al chiamante   */
}

void sgp_idle_task5(void *task, void *data)
{
    SgpAnim5State *st = SGP_STATO5;
    SgpAnim5Slot *s;
    u8 *od = (u8 *)data;
    u8 *pic;
    u32 fase, idx, prossimo, cls, slot, g;
    s32 u, y;
    u8 flags;

    st->hits = st->hits + 1u;

    flags = abilitato() != 0u ? (u8)SGP_F_TUTTI : 0u;
    st->flags = flags;
    if ((flags & SGP_F_TUTTI) == 0u) {
        /* Spento: il task del gioco resta la sola operazione, con gli stessi
         * argomenti e nello stesso ordine della 1.2.1. A interruttore mai
         * acceso `sgp_pulisci` non trova nessuna voce e non scrive un byte
         * (byte-identita' preservata); se invece l'opzione e' stata spenta a
         * lotta in corso, e' quello che toglie dallo sprite scala, ombra e
         * posa che il task vanilla non sa rimettere a posto (A8b-A1). */
        sgp_pulisci(data);
        ((TaskFn)SGP_VANILLA_TASK)(task, data);
        return;
    }

    pic = *(u8 **)(od + OD_POKEPIC);
    if (pic == 0 || (*(volatile u8 *)pic & 1u) == 0u) {
        sgp_pulisci(data); /* niente ripristino su una pic inattiva */
        return;
    }

    s = slot_per(st, (u32)od, (u32)pic, &slot);
    st->last_slot = (u8)slot;

    /* 1. A3 — sospensione. Il controllo precede anche il task vanilla, che
     *    scrive yOffset: dopo il primo riposo nessun codice di moto deve
     *    toccare il Pokepic finche' i cancelli non cadono tutti. */
    g = cancelli_alzati(st, s, pic);
    if (scala_nostra(pic) == 0u || (*(volatile u16 *)(pic + 0x54) & 0x0803u) != 0u) {
        /* hasVanished, ritaglio (KO) o dontDraw: precedono il riuso. */
        g |= SGP_G_SCALA;
    }
    st->cancelli = (u8)g;
    if (g != 0u) {
        st->hits_busy = st->hits_busy + 1u;
        if (s->sospeso == 0u) {
            riposo(s, pic);
            riarma(s); /* B3: niente lampo residuo alla caduta del cancello */
            s->sospeso = 1u;
            s->inviluppo = 0u;
            st->last_y = 0;
            st->sospensioni = st->sospensioni + 1u;
        }
        return;
    }
    s->sospeso = 0u;

    /* Orologio privato: aggiorna ogni tick, interpolando la tavola, senza
     * richiamare il rimbalzo vanilla o rallentare il resto del gioco. */
    fase = (u32)s->fase + (u32)SGP_PAR[PAR_PASSO];
    if (fase >= (u32)SGP_FASI * 8u) {
        fase -= (u32)SGP_FASI * 8u;
    }
    s->fase = (u8)fase;
    idx = fase >> 3;
    if ((flags & SGP_F_FASE) != 0u) { /* idea 2: i lottatori non all'unisono */
        idx += (u32)SGP_PAR[PAR_FASE + slot];
        if (idx >= (u32)SGP_FASI) {
            idx -= (u32)SGP_FASI;
        }
    }
    st->last_idx = (u8)idx;

    /* idea 4: classe di taglia dai bit 5-6 di pokepic+0x6C (`shadow.size`). */
    cls = (flags & SGP_F_TAGLIA) != 0u
              ? (((u32)(*(volatile u16 *)(pic + PP_SHADOW_FLAGS))
                  >> PP_TAGLIA_SHIFT) & 3u)
              : 1u;
    st->last_cls = (u8)cls;

    prossimo = idx + 1u;
    if (prossimo == (u32)SGP_FASI) {
        prossimo = 0u;
    }
    if (s->inviluppo < 16u) {
        s->inviluppo++;
    }
    u = ((s32)SGP_TAB_U[idx] * (s32)(8u - (fase & 7u))
         + (s32)SGP_TAB_U[prossimo] * (s32)(fase & 7u)) * (s32)s->inviluppo;
    y = scala_unita(u, (s32)SGP_PAR[PAR_AMP + cls]);

    /* 3a. Respiro verticale. */
    if ((flags & SGP_F_RESPIRO) != 0u) {
        setattr5(pic, POKEPIC_YOFFSET, (int)y);
        st->last_y = (s16)y;

        /* 3a-bis. OMBRA ANCORATA: compensa in controfase la stessa yOffset che
         *         DrawAll somma alla Y dell'ombra. */
        if ((flags & SGP_F_OMBRA) != 0u) {
            s32 cur = (s32)(*(volatile s16 *)(pic + PP_SHADOW_YOFF));
            s32 v;
            if ((s16)cur != s->last76) {
                s->base76 = (s16)cur;
            }
            v = (s32)s->base76 - y;
            setattr5(pic, POKEPIC_SHADOW_YOFF, (int)v);
            s->last76 = (s16)v;
            st->last_s76 = (s16)v;
        }
    }

    /* 3b. Accento con la posa B. Non tutte le specie vi chiudono gli occhi. */
    if ((flags & SGP_F_POSA) != 0u) {
        u32 p = 0u;
        if (s->blink_left != 0u) {
            s->blink_left = (u8)(s->blink_left - 1u);
            p = 1u;
        } else if (s->blink_wait != 0u) {
            s->blink_wait = (u8)(s->blink_wait - 1u);
        } else if (((u32)st->last_idx - (u32)SGP_PICCO_IDX)
                   < (u32)SGP_PICCO_N) {
            /* v5d — ARMATO E AL PICCO. Quando l'attesa arriva a zero la voce
             * resta armata e l'accento parte solo nel tick in cui la fase e'
             * al massimo della tavola: il cambio di posa cade nell'istante di
             * quiete del respiro invece di sommarsi al suo spostamento.
             * Si rilegge `st->last_idx`, scritto poche righe sopra, invece di
             * tenere vivo `idx` fino a qui: misurato, costa 16 B in meno.
             * L'attesa si allunga al piu' di un ciclo di respiro. */
            u32 r = lcg(s);
            u32 dur = (u32)SGP_PAR[PAR_BLINK_DUR] + (r & 1u);
            s->blink_cnt = (u8)(s->blink_cnt + 1u);
            if (s->blink_cnt >= SGP_PAR[PAR_RARO_OGNI]) {
                s->blink_cnt = 0u;
                dur += (u32)SGP_PAR[PAR_RARO_PIU];
            }
            s->blink_left = (u8)(dur - 1u);
            s->blink_wait = (u8)((u32)SGP_PAR[PAR_BLINK_MIN]
                                 + ((r >> 4) & (u32)SGP_PAR[PAR_BLINK_MASK]));
            p = 1u;
        }
        setattr5(pic, POKEPIC_ANIM_STEP, (int)p);
        st->last_step = (u8)p;
    }

    /* 3c. Squash & stretch in controfase (idea 1). */
    if ((flags & SGP_F_SCALA) != 0u && scala_nostra(pic) != 0u) {
        s32 d = scala_unita(u, (s32)SGP_PAR[PAR_SCA + cls]);
        setattr5(pic, POKEPIC_AFFINEW, (int)((s32)SGP_SCALA_UNO + d));
        setattr5(pic, POKEPIC_AFFINEH, (int)((s32)SGP_SCALA_UNO - d));
    }

    st->hits_on = st->hits_on + 1u;
}
