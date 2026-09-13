/* Sacred Gold Plus 1.2 — il chunk di salvataggio, formato PUBBLICO, e lo stato
 * a runtime che lo ospita. GPL-3.0-or-later.
 *
 * Fonte unica degli indirizzi, degli offset e delle regole di lettura:
 * `SGP-1.2-PLUS-03/CONTRATTO-CHUNK.md`. Chi cambia qualcosa qui cambia il
 * contratto, e aggiorna quel documento nello stesso giro.
 *
 * Vincoli del caricatore (`carica_text.py`, modello della 1.1), ereditati da
 * ogni blob che include questo file: una sola unità di traduzione, nessun
 * simbolo esterno, nessuna sezione allocata oltre `.text`. Nessuna costante
 * tabellare: ogni indirizzo è un letterale del pool di `.text`.
 */
#ifndef SGP_CHUNK_H
#define SGP_CHUNK_H

typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned int   u32;
typedef signed short   s16;
typedef signed int     s32;

/* Una sola base parametrica per tutto il blocco `sgp.plus`: il valore qui è
 * quello vero di `source/docs/arm9-reserve-map.json`. Tutto il resto ne
 * discende, così un `-D` che sposta il blocco sposta anche le due tabelle —
 * prima erano letterali scollegati, e dimenticare un `-D` faceva leggere la
 * tabella dei livelli da memoria altrui invece di far fallire la build. */
#ifndef SGP_PLUS_BASE
#define SGP_PLUS_BASE 0x023D8100u
#endif
#define SGP_TAB_TRAINER_ADDR (SGP_PLUS_BASE + 0x400u)
#define SGP_TAB_WILD_ADDR    (SGP_PLUS_BASE + 0x500u)
#define SGP_STATO_ADDR       (SGP_PLUS_BASE + 0x600u)

#define SGP_CHUNK_ADDR       (SGP_STATO_ADDR + 0x10u)
#define SGP_LOAD_STATUS_ADDR (SGP_STATO_ADDR + 0x03u)

/* Offset dei campi dentro il chunk: gli stessi nomi che usa la pagina Opzioni
 * (`SGP-1.2-OPZIONI-03/sorgenti/sgp_ui.h`), così un `grep` li trova tutti. */
#define SGP_C_MAGIC     0x0u
#define SGP_C_VERSIONE  0x2u
#define SGP_C_PLUS      0x3u
#define SGP_C_SELVATICI 0x4u
#define SGP_C_OLTRE100  0x5u
#define SGP_C_ANIM      0x6u
#define SGP_C_NPC       0x7u
#define SGP_C_WIFI      0x8u
#define SGP_C_PICCO     0x9u
#define SGP_C_RISERVATO0 0xAu
#define SGP_C_RISERVATO1 0xBu

#define SGP_CHUNK_NPC_ADDR   (SGP_CHUNK_ADDR + SGP_C_NPC)
#define SGP_CHUNK_WIFI_ADDR  (SGP_CHUNK_ADDR + SGP_C_WIFI)

/* Gli stati degli altri blocchi, con i nomi che usa la pagina Opzioni. Stanno
 * qui perché sono indirizzi che DUE cantieri leggono: chi li sposta deve
 * trovarli in un posto solo. */
#ifndef SGP_STATO_NPC_ADDR
#define SGP_STATO_NPC_ADDR 0x023D89E0u     /* `sgp.npc` +0x0E0, 16 B */
#endif
#ifndef SGP_STATO_WIFI_ADDR
#define SGP_STATO_WIFI_ADDR 0x023DA240u    /* `sgp.wifi` +0x240, 16 B */
#endif

/* I 16 byte pubblici. Ogni interruttore è UN byte, non un bit: due cantieri che
 * scrivono campi diversi non si corrompono con una lettura-modifica-scrittura
 * non atomica. */
typedef struct SgpChunk {
    u16 magic;       /* +0x0  0x5347 'SG'                         D1   */
    u8  versione;    /* +0x2  2                                   D1   */
    u8  plus;        /* +0x3  0/1  difficoltà PLUS allenatori     D1   */
    u8  selvatici;   /* +0x4  0/1  livelli selvatici PLUS         D1   */
    u8  oltre100;    /* +0x5  0/1  riservato alla 1.2b            D1   */
    u8  anim;        /* +0x6  0/1  moto procedurale               A1-B */
    u8  npc;         /* +0x7  0/1  fluidità NPC                   P2   */
    u8  wifi_server; /* +0x8  0..3 scelta del server              W1   */
    u8  picco;       /* +0x9  1..cap, non decresce mai            D1   */
    u8  riservato0;  /* +0xA  = 0 */
    u8  riservato1;  /* +0xB  = 0 */
    u32 riservato2;  /* +0xC  = 0 */
} SgpChunk;          /* sizeof == 16 */

/* `active_plus` sta a offset 0 di proposito: i ganci leggono UN byte, e una
 * riserva azzerata o mai inizializzata vale 0 = comportamento 1.1. */
typedef struct SgpStato {
    u8  active_plus;  /* +0x00 */
    u8  active_wild;  /* +0x01 */
    u8  cap;          /* +0x02 */
    u8  load_status;  /* +0x03 SGP_LOAD_* */
    u8  guard;        /* +0x04 SGP_GUARD */
    u8  pad0;         /* +0x05 */
    u16 pad1;         /* +0x06 */
    u32 hits_trainer; /* +0x08 diagnostica */
    u32 hits_wild;    /* +0x0C diagnostica */
    SgpChunk chunk;   /* +0x10 */
} SgpStato;           /* sizeof == 32 */

#define SGP_STATO ((SgpStato *)SGP_STATO_ADDR)

#define SGP_MAGIC_CHUNK 0x5347u
#define SGP_VERSIONE    2u
#define SGP_CAP_1_2A    100u
#define SGP_CAP_1_2B    150u   /* il cap che `oltre100` dichiara: la 1.2a lo accetta e non lo applica */
#define SGP_CAP_DI(oltre100) ((oltre100) ? SGP_CAP_1_2B : SGP_CAP_1_2A)
#define SGP_GUARD       0x5Au  /* «blocco inizializzato»: la stessa convenzione per tutti i blocchi */

#define SGP_LOAD_NONE   0u   /* mai caricato in questa sessione */
#define SGP_LOAD_ABSENT 1u   /* salvataggio 1.1: comportamento 1.1 */
#define SGP_LOAD_VALID  2u
#define SGP_LOAD_REJECT 3u   /* presente ma invalido: non si riscrive mai */

/* --- come si legge un'opzione, per TUTTI i consumatori --------------------
 * D1 normalizza la copia in RAM a ogni avvio (`sgp_chunk_leggi`): chunk
 * assente → i default 1.2, chunk valido → quello che dice il salvataggio. Chi
 * legge deve quindi solo sapere se D1 è passato e se il chunk è utilizzabile:
 * `REJECT` e «non ancora letto» valgono 0, cioè comportamento 1.1
 * (CONTRATTO-CHUNK §4). Prima ogni cantiere si scriveva la sua guardia, e le
 * guardie non dicevano tutte la stessa cosa. */
static __inline u8 sgp_chunk_opzione(u32 indirizzo)
{
    const SgpStato *s = SGP_STATO;

    if (s->guard != SGP_GUARD) {
        return 0u;
    }
    if (s->load_status != SGP_LOAD_ABSENT && s->load_status != SGP_LOAD_VALID) {
        return 0u;
    }
    return *(volatile const u8 *)indirizzo;
}

/* --- scrivere un'istruzione in RAM ---------------------------------------
 * Regola generale della 1.2, non una consuetudine del WiFi: sull'ARM946E-S la
 * D-cache è write-back e la I-cache è separata, quindi senza queste due
 * chiamate la parola resta sporca e la CPU può prelevare ancora l'istruzione
 * vecchia. Invisibile in melonDS, che non modella le cache. Le due funzioni
 * NitroSDK stanno nell'ARM9 statico, sono ARM (bit 0 a zero) e hanno byte
 * identici nelle quattro ROM (prove/estratti/). */
#ifndef SGP_DC_FLUSH_RANGE
#define SGP_DC_FLUSH_RANGE 0x020D2894u      /* DC_FlushRange(void*, u32)      */
#endif
#ifndef SGP_IC_INVALIDATE_RANGE
#define SGP_IC_INVALIDATE_RANGE 0x020D28D0u /* IC_InvalidateRange(void*, u32) */
#endif

static __inline void sgp_scrivi_istruzione(u32 sito, u32 parola)
{
    *(volatile u32 *)sito = parola;
    ((void (*)(void *, u32))SGP_DC_FLUSH_RANGE)((void *)sito, 4u);
    ((void (*)(void *, u32))SGP_IC_INVALIDATE_RANGE)((void *)sito, 4u);
}

#endif /* SGP_CHUNK_H */
