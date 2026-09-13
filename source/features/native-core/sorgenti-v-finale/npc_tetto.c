/* Sacred Gold Plus 1.2 — P2: tetto di UN caricamento di modello NPC per
 * fotogramma. GPL-3.0-or-later. Unità di traduzione UNICA.
 *
 * MISURA CHE MOTIVA QUESTO FILE (prove/anatomia.json, prove/gap-*.json): il
 * gioco del 2009 ha GIÀ un tetto per fotogramma sui caricamenti di modello degli
 * oggetti mappa. La funzione a 0x021FA564 (overlay 1) è un SysTask della coda
 * principale che gira una volta per fotogramma (218 fermate su 218 fotogrammi
 * distinti) e drena una lista di richieste; il tetto è un `s16` all'offset +2
 * della lista e vale 10. Al confine Fiordoropoli → Percorso 34 le richieste
 * pendenti sono 10: entrano tutte in un fotogramma solo, ed è quello il giro da
 * gap 5. L'intervento è quindi un CLAMP di quel campo, non una riscrittura del
 * caricamento: rinvio, ripresa e fine della lista restano meccanismi del gioco.
 *
 * ATTIVAZIONE: si rilegge a ogni giro dal chunk pubblico di D1, con
 * l'accessore condiviso di `sgp_chunk.h`. Il default acceso del mandato P2 è
 * un default del FORMATO, messo da D1 nella copia in RAM quando il chunk è
 * assente: così sopravvive al primo salvataggio e la pagina Opzioni mostra lo
 * stesso stato che il gancio applica. Qui non c'è nessuna regola propria.
 *
 * SPENTO = BYTE-IDENTICO: senza la guardia 0x5A nel proprio stato non si legge e
 * non si scrive niente; con la guardia ma attivazione 0, le sole scritture sono
 * su due campi diagnostici che il gioco non legge mai.
 */
#include "sgp_chunk.h"

/* Offset del campo «tetto» dentro la lista delle richieste di modello: letto dal
 * binario (0x021FA854 `strh r0,[r4,#2]`, 0x021FA5AE confronta `[r4+4]` con
 * `[r4+2]`). Parametrico per non cablare un numero che una revisione smentirebbe. */
#ifndef SGP_NPC_OFF_TETTO
#define SGP_NPC_OFF_TETTO 2
#endif

/* 16 byte. `attivo` sta a offset 0 di proposito (una riserva azzerata legge 0).
 * Dalla fase 02b è uno SPECCHIO diagnostico, non un interruttore: lo riscrive
 * ogni giro l'attivazione calcolata dal chunk. */
typedef struct SgpNpcStato {
    /*+0x0*/ u8  attivo;
    /*+0x1*/ u8  tetto;      /* caricamenti di modello ammessi per fotogramma */
    /*+0x2*/ u8  guardia;    /* 0x5A quando lo stato è stato inizializzato */
    /*+0x3*/ u8  riservato;
    /*+0x4*/ s16 salvato;    /* il tetto originale del gioco, la prima volta che si vede */
    /*+0x6*/ u16 clamp;      /* quante volte il tetto è stato abbassato */
    /*+0x8*/ u32 giri;       /* quante volte il gancio è stato eseguito */
    /*+0xC*/ u32 riservato2;
} SgpNpcStato;

#define SGP_NPC_STATO ((volatile SgpNpcStato *)SGP_STATO_NPC_ADDR)

/* `lista` è il puntatore che il gioco tiene in r4. Gli unici accessi fuori dal
 * blocco `sgp.npc` sono i due byte del contratto di D1 e i due byte del tetto. */
__attribute__((used, noinline, section(".text")))
void sgp_npc_tetto(void *lista)
{
    volatile SgpNpcStato *st = SGP_NPC_STATO;
    volatile s16 *tetto;
    u8 attivo;
    s16 t;

    if (st->guardia != SGP_GUARD) {
        return;                       /* stato mai inizializzato: non tocco niente */
    }
    st->giri++;                       /* distingue «spento» da «mai raggiunto» */

    attivo = (u8)(sgp_chunk_opzione(SGP_CHUNK_NPC_ADDR) != 0u);
    st->attivo = attivo;              /* specchio diagnostico, non ingresso */

    if (attivo == 0u || st->tetto == 0u) {
        return;                       /* spento: tetto originale del gioco */
    }
    if (lista == 0) {
        return;
    }
    tetto = (volatile s16 *)((u8 *)lista + SGP_NPC_OFF_TETTO);
    t = *tetto;
    if (t > (s16)st->tetto) {
        if (st->salvato == 0) {
            st->salvato = t;          /* il valore originale, letto una volta */
        }
        *tetto = (s16)st->tetto;
        st->clamp++;
    }
}

/* Trampolina del gancio: sostituisce i 4 byte a 0x021FA570 — `adds r0,#0xe0` e
 * `ldr r0,[r0]` — con un `BL` verso qui.
 *
 * All'ingresso:  r4 = puntatore alla lista, r0 = sistema oggetti di campo,
 *                lr = libero (prologo dell'ospite a 0x021FA564:
 *                `push {r3,r4,r5,r6,r7,lr}`), sp allineato a 8.
 * All'uscita:    r0 = [r0+0xE0] come nell'originale, r1/r2 ripristinati,
 *                r4..r7 invariati, flag di `adds r0,#0xe0` come nell'originale
 *                (e la successiva `movs r6,#0` li riscrive comunque prima di
 *                leggerli). **r3 è CLOBBERATO** dalla chiamata C (AAPCS): al
 *                sito è morto — si arriva a `bl 0x020238F8` senza rileggerlo, e
 *                quel callee usa solo r0; il `push {r3,r4-r7,lr}` del prologo
 *                ospite usa r3 come riempitivo di allineamento e lo slot viene
 *                subito sovrascritto da `str r1,[sp]`
 *                (prove/estratti/disasm-npc-*.txt). Il contratto precedente
 *                diceva «r1..r7 invariati»: era falso.
 *
 * Il `push` di 4 parole conserva l'allineamento a 8 della pila; `sgp_npc_tetto`
 * rispetta AAPCS e quindi non tocca r4.
 */
__attribute__((naked, used, section(".text")))
void sgp_npc_hook(void)
{
    __asm__ volatile(
        "push  {r0, r1, r2, lr}\n"
        "adds  r0, r4, #0\n"
        "bl    sgp_npc_tetto\n"
        "pop   {r0, r1, r2}\n"
        "adds  r0, #0xe0\n"        /* istruzione sostituita 1 */
        "ldr   r0, [r0]\n"         /* istruzione sostituita 2 */
        "pop   {pc}\n"
    );
}
