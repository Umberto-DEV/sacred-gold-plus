/* Sacred Gold Plus 1.2 — W1: corpo del blob. GPL-3.0-or-later.
 *
 * TRE ganci:
 *   G1  sgp_wfc_trampolino / sgp_wfc_on_overlay
 *       ARM9 0x020070A8, epilogo di successo di Overlay_Load. Installa i due
 *       veneer nella copia RAM di ov000, e azzera la forzatura quando entra
 *       l'utility di configurazione WFC (ov013).
 *   G3  sgp_wfc_on_connect — il trigger preciso
 *       ov000 0x021EC4A4, ingresso di DWC_ConnectInetAsync. `lr` è il sito del
 *       chiamante, cioè il servizio: letto, non dedotto.
 *   G2  sgp_wfc_nibble
 *       ov000 0x021FC150, DWCi_BuildApSearchList: scrive il nibble selettore di
 *       slot in work[0xD0C].
 *
 * Regola di versione: con `versione != SGP_W1_VERSIONE` nessuna funzione scrive
 * un byte — un blob di un'altra versione nello stesso scomparto non viene mai
 * eseguito da questo, e viceversa.
 *
 * G1 non è gated su `modo`: installa sempre (magic/versione soli), perché è G3
 * che deve poter scattare per sincronizzare `modo` dal chunk, e G3 ha bisogno
 * che il veneer sia già installato. L'installazione è innocua di per sé: decide
 * di forzare qualcosa solo `pending`, scritto esclusivamente da G3.
 */
#include "wifi_slot4.h"

/* ------------------------------------------------------------------ */
/* lettura degli slot dalla copia RAM dentro il work buffer DWC        */
/* ------------------------------------------------------------------ */

/* Il cancello di versione, in un posto solo: la regola «con versione diversa
 * nessuna funzione scrive un byte» era affidata a tre copie. */
static s32 w1_pronto(void)
{
    return SGP_W1S->magic == SGP_W1_MAGIC_OK
        && SGP_W1S->versione == SGP_W1_VERSIONE;
}

static s32 work_valido(const u8 *work)
{
    u32 a = (u32)work;
    if (a < 0x02000000u || a >= 0x02400000u) return 0;
    if (a & 3u) return 0;
    return 1;
}

s32 sgp_wfc_slot_configurato(const u8 *work, s32 slot)
{
    if (slot < 0 || slot > 2) return 0;            /* tre slot: indice sempre 0..2 */
    if (!work_valido(work)) return 0;
    return work[(u32)slot * AP_STRIDE + AP_STATUS] != AP_NON_CONFIG ? 1 : 0;
}

/* ------------------------------------------------------------------ */
/* G3 — quale servizio sta avviando il DWC, e con quale slot           */
/* ------------------------------------------------------------------ */

s32 sgp_wfc_servizio_da_lr(u32 lr)
{
    if (lr == LR_DONO) return SGP_SERV_DONO;
    if (lr == LR_GTS || lr == LR_CLUB || lr == LR_WFCSCHERM ||
        lr == LR_TORRE || lr == LR_BACHECA) return SGP_SERV_ONLINE;
    return SGP_SERV_NESSUNO;
}

/* Legge FRESCO `wifi_server` dal chunk (accessore condiviso: un chunk che D1
 * non ha validato vale 0) e lo traduce: 2 o 3 → quello slot per i servizi
 * online; qualunque altro valore → Originale. `SgpW1Stato` è solo la cache di
 * lavoro che G2 rilegge; la decisione qui è presa sempre sul valore appena
 * letto, perché la pagina Opzioni può cambiarlo durante la partita. */
static u8 sgp_wfc_sincronizza_da_chunk(void)
{
    u8 v = sgp_chunk_opzione(SGP_CHUNK_WIFI_ADDR);
    u8 attivo = (v == 2u || v == 3u) ? 1u : 0u;
    SGP_W1S->modo = attivo;
    SGP_W1S->slot_gts = attivo ? v : 0u;
    return attivo ? v : 0u;
}

void sgp_wfc_on_connect(u32 lr)
{
    s32 serv;
    u8  slot_gts;

    if (!w1_pronto()) return;

    serv = sgp_wfc_servizio_da_lr(lr);
    SGP_W1->n_connect++;
    SGP_W1->ultimo_lr = lr;

    if (serv == SGP_SERV_NESSUNO) {
        /* Sono i due siti interni di ov000 (wifi_slot4.h): non sono servizi e
         * possono rientrare qui DOPO che il servizio vero ha deciso. Contarli e
         * basta: azzerare `pending` cancellerebbe la scelta del giocatore. */
        SGP_W1->n_ignoti++;
        return;
    }

    SGP_W1->servizio = (u8)serv;
    slot_gts = sgp_wfc_sincronizza_da_chunk();     /* 0 = Originale, 2/3 = attivo */
    if (slot_gts == 0u) {
        SGP_W1->pending = 0u;                      /* Originale: nessuna forzatura */
    } else if (serv == SGP_SERV_DONO) {
        SGP_W1->pending = 1u;                      /* Dono Segreto: slot fisso 1 */
    } else {
        SGP_W1->pending = slot_gts;                /* GTS/lotta/scambio: 2 o 3 */
    }
}

/* ------------------------------------------------------------------ */
/* G2 — scrittura del nibble selettore di slot                          */
/* ------------------------------------------------------------------ */

/* Primo slot configurato, in ordine 1,2,3 (0 = nessuno). Solo come RIPIEGO
 * quando lo slot designato non è configurato. */
static s32 sgp_wfc_primo_configurato(const u8 *work)
{
    s32 i;
    for (i = 0; i < 3; i++) {
        if (sgp_wfc_slot_configurato(work, i)) return i + 1;
    }
    return 0;
}

void sgp_wfc_nibble(u8 *work)
{
    u8 p, v;
    s32 alt;

    if (!w1_pronto()) return;
    if (SGP_W1S->modo == 0u) return;               /* Originale: inerte */
    if (!work_valido(work)) return;

    SGP_W1->ultimo_work = (u32)work;

    p = SGP_W1->pending;
    if (p == 0u || p > 3u) return;                 /* nessuna forzatura */

    if (!sgp_wfc_slot_configurato(work, (s32)p - 1)) {
        alt = sgp_wfc_primo_configurato(work);
        if (alt == 0) return;                      /* nessuno configurato: vanilla */
        p = (u8)alt;
        SGP_W1->n_fallback++;
    }

    v = work[DWC_WORK_NIBBLE];
    work[DWC_WORK_NIBBLE] = (u8)((v & 0xf0u) | p);
    SGP_W1->n_forzature++;
}

/* ------------------------------------------------------------------ */
/* installazione dei veneer nella copia RAM di ov000                    */
/* ------------------------------------------------------------------ */

/* Le due preimmagini, parametriche come tutto il resto. */
#ifndef G2_PREIMMAGINE
#define G2_PREIMMAGINE 0xe92d4070u    /* 0x021FC150: push {r4,r5,r6,lr} */
#endif
#ifndef G3_PREIMMAGINE
#define G3_PREIMMAGINE 0xe92d4000u    /* 0x021EC4A4: stmdb sp!, {lr}    */
#endif

static u32 arm_b(u32 sito, u32 dst)
{
    s32 off = (s32)(dst - (sito + 8u)) >> 2;
    return 0xea000000u | ((u32)off & 0x00ffffffu);
}

/* Idempotente per costruzione: la preimmagine c'è una volta sola. Quando
 * Overlay_Load rilegge ov000 dalla cartuccia la preimmagine torna, e allora la
 * scrittura si rifà — una volta. */
__attribute__((always_inline))
static inline void installa_uno(u32 sito, u32 preimmagine, u32 veneer, u8 bit)
{
    volatile u32 *p = (volatile u32 *)sito;

    if (*p != preimmagine) return;      /* già installato, o non è ov000 */
    sgp_scrivi_istruzione(sito, arm_b(sito, veneer));
    SGP_W1->installato |= bit;
    SGP_W1->n_installa++;
}

/* ------------------------------------------------------------------ */
/* G1 — un overlay è appena stato caricato: SOLO installazione          */
/* ------------------------------------------------------------------ */

void sgp_wfc_on_overlay(u32 id)
{
    if (!w1_pronto()) return;

    SGP_W1->n_overlay++;

    if (id == OVL_DWC) {
        SGP_W1->installato = 0u;            /* la copia RAM di ov000 è nuova */
        installa_uno(SGP_DWC_LISTA_SITE, G2_PREIMMAGINE, SGP_W1_VENEER_ADDR, 1u);
        installa_uno(SGP_DWC_CONNECT_SITE, G3_PREIMMAGINE, SGP_W1_VENEER3_ADDR, 2u);
        return;
    }

    if (id == OVL_WFC) {
        SGP_W1->servizio = SGP_SERV_NESSUNO;
        SGP_W1->pending = 0u;
    }
}

/* ------------------------------------------------------------------ */
/* G1 — trampolino Thumb che sostituisce l'epilogo di Overlay_Load      */
/*                                                                      */
/* Sito: ARM9 0x020070A8, 4 byte: `movs r0,#1` + `pop {r3,r4,r5,r6,r7,pc}`.  */
/* All'ingresso r5 = id dell'overlay appena caricato. Questo trampolino NON  */
/* torna al BL: esegue l'epilogo dell'ospite e ritorna al chiamante di       */
/* quello, quindi r0..r3 sono morti e `push {r4,lr}` serve solo a tenere     */
/* la pila allineata a 8.                                                    */
/* ------------------------------------------------------------------ */
__attribute__((naked, used)) void sgp_wfc_trampolino(void)
{
    __asm__ volatile(
        "push {r4, lr}\n\t"
        "adds r0, r5, #0\n\t"        /* id dell'overlay */
        "bl   sgp_wfc_on_overlay\n\t"
        "pop  {r4}\n\t"
        "pop  {r1}\n\t"              /* lr del trampolino: scartato */
        "movs r0, #1\n\t"            /* istruzione originale */
        "pop  {r3, r4, r5, r6, r7, pc}\n\t"   /* epilogo originale */
    );
}
