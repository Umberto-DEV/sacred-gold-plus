/* Sacred Gold Plus 1.2a — lettura all'avvio e scrittura al salvataggio del
 * chunk 1.2 (cantiere D1). GPL-3.0-or-later. Unità di traduzione UNICA.
 *
 * Due ganci; tutti e due sostituiscono una `BL` esistente con una `BL` a una
 * nostra funzione che rifà la chiamata originale e poi aggiunge la sua parte: il
 * flusso del gioco non cambia mai, nemmeno nel valore di ritorno.
 *
 *   L0  0x020271F8, in `SaveData_Init`: dopo che il gioco ha letto e validato il
 *       salvataggio, leggiamo il nostro settore. L'esito originale finisce in r5
 *       e comanda lo `switch` che segue: lo restituiamo intatto.
 *   S0  0x02027456, in coda a `SaveData_Save`: se torna 2 il salvataggio è
 *       riuscito, ed è lì che scriviamo.
 *
 * Perché NON si aggiunge una settima voce a `gExtraSaveChunkHeaders[]`: la
 * tabella è `const` in ROM e andrebbe rilocata, ma soprattutto non basterebbe —
 * in HGSS gli extra chunk non li scrive il salvataggio normale, ognuno ha il suo
 * involucro chiamato da un evento. Servirebbe comunque un gancio nel percorso di
 * salvataggio, e con quel gancio la tabella non serve (CONTRATTO-CHUNK §7).
 *
 * Due copie, non una: settore 47 e settore 111, la stessa distanza di 64 settori
 * che il gioco usa per i suoi. Alla lettura si prende la prima copia valida; se
 * una scrittura viene interrotta a metà, l'altra regge.
 */
#include "sgp_salva.h"

/* -------------------------------------------------------------- validazione */

/* Le invarianti di CONTRATTO-CHUNK §6 si controllano per PAROLE, non per campi:
 * ogni cancello diventa una maschera e ci sta nel blocco.
 *   w0 = magic(2) | versione<<16 | plus<<24
 *   w1 = selvatici | oltre100<<8 | anim<<16 | npc<<24
 *   w2 = wifi_server | picco<<8 | riservato0<<16 | riservato1<<24
 *   w3 = riservato2
 */
static int sgp_valido(const u8 *b)
{
    const SgpFooter *f = (const SgpFooter *)(b + SGP_PAYLOAD);
    const u32 *w = (const u32 *)b;
    u32 w0 = w[0];
    u32 w1 = w[1];
    u32 w2 = w[2];
    u32 ver = (w0 >> 16) & 0xFFu;
    u32 picco = (w2 >> 8) & 0xFFu;

    /* `size` e `idx` non si controllano a parte: stanno dentro i 30 byte che il
     * CRC copre, quindi un CRC giusto li ha già verificati. */
    if (f->magic != SGP_MAGIC_FOOTER) {
        return 0;
    }
    if (f->crc != CHIAMA_CRC(b, SGP_CRC_LEN)) {
        return 0;
    }
    if ((w0 & 0xFFFFu) != SGP_MAGIC_CHUNK) {
        return 0;
    }
    if (ver != SGP_VERSIONE) {
        return 0;                       /* SOLO la versione corrente: una pianta
                                         * diversa letta con questa sarebbe il caso
                                         * peggiore, un chunk accettato e letto storto */
    }
    if ((w0 >> 24) > 1u || (w1 & 0xFEFEFEFEu)) {
        return 0;                       /* plus/selvatici/oltre100/anim/npc in {0,1} */
    }
    if ((w2 & 0xFFu) > 3u) {
        return 0;                       /* wifi_server in 0..3 */
    }
    if ((w2 & 0xFFFF0000u) | w[3]) {
        return 0;                       /* riservato0, riservato1, riservato2 = 0 */
    }
    /* la 1.2a accetta il cap dichiarato dal chunk ma non lo applica. */
    if ((picco - 1u) >= SGP_CAP_DI((w1 >> 8) & 1u)) {
        return 0;
    }
    return 1;
}

/* ------------------------------------------------------------------ lettura */

/* Legge il settore 47 e, se non va, il 111, e lascia `load_status` aggiornato. Lo
 * stato torna sempre ai valori 1.1 prima di leggere: chunk mancante o rifiutato
 * ⇒ il gioco si comporta come la 1.1. I due contatori `hits_*` NON si azzerano:
 * servono a distinguere «PLUS spento» da «gancio mai eseguito». */
static void sgp_chunk_leggi(void)
{
    SgpStato *s = SGP_STATO;
    u8 *b = SGP_BUF;
    SgpFooter *f = (SgpFooter *)(b + SGP_PAYLOAD);
    u32 *z = (u32 *)s;
    u32 off = SGP_SETTORE_A;
    u32 i;

    z[0] = 0;                              /* active_plus, active_wild, cap, load_status */
    z[1] = 0;                              /* guard, pad. z[2] e z[3] sono gli hits_*: non si toccano */
    z[4] = 0;                              /* i 16 byte del chunk */
    z[5] = 0;
    z[6] = 0;
    z[7] = 0;
    s->cap = (u8)SGP_CAP_1_2A;
    s->guard = SGP_GUARD;
    s->load_status = SGP_LOAD_ABSENT;
    /* I DEFAULT 1.2, tutti qui: chi possiede il formato è chi li materializza.
     * Un cantiere che vuole la propria opzione accesa di partenza aggiunge una
     * riga a questo elenco, non un caso speciale nel proprio gancio. Non rompono
     * «chunk assente = comportamento 1.1» per le opzioni di D1, che restano 0. */
    s->chunk.picco = 1u;    /* mai 0: un chunk con picco 0 sarebbe rifiutato */
    s->chunk.npc = 1u;      /* fluidità NPC accesa di default (mandato P2) */

    for (i = 0; i < 2u; i++) {
        /* Il buffer è RAM persistente e l'esito di ReadBackup non è nel
         * contratto del gioco: si azzera il magic del footer, così una lettura
         * fallita non può far passare per valido quello che c'era prima. */
        f->magic = 0u;
        CHIAMA_RB(off, b, SGP_RECORD);
        if (sgp_valido(b)) {
            u32 j;
            for (j = 0; j < 4u; j++) {
                z[4u + j] = ((const u32 *)b)[j];
            }
            s->active_plus = b[SGP_C_PLUS];
            s->active_wild = b[SGP_C_SELVATICI];
            s->load_status = SGP_LOAD_VALID;
            return;
        }
        /* un settore col NOSTRO magic ma non valido non è «assente»: è un chunk
         * rotto, e un chunk rotto non va mai riscritto. */
        if (f->magic == SGP_MAGIC_FOOTER) {
            s->load_status = SGP_LOAD_REJECT;
        }
        off = SGP_SETTORE_B;
    }
}

/* ---------------------------------------------------------------- scrittura */

/* Costruisce il chunk dallo stato, ci mette il footer del gioco, lo scrive in
 * tutte e due le copie. Non scrive niente con lo stato mai inizializzato o con un
 * chunk rifiutato: un chunk rifiutato non si riscrive mai, altrimenti si perde
 * per sempre quello che c'era. */
static void sgp_chunk_scrivi(void)
{
    SgpStato *s = SGP_STATO;
    u8 *b = SGP_BUF;
    SgpFooter *f = (SgpFooter *)(b + SGP_PAYLOAD);
    u32 *dst = (u32 *)b;
    const u32 *src = (const u32 *)&s->chunk;
    u32 off = SGP_SETTORE_A;
    u32 i, cap;

    if (s->guard != SGP_GUARD || s->load_status == SGP_LOAD_REJECT) {
        return;
    }
    /* si parte dal chunk che sta in RAM (lì scrivono gli altri cantieri) e si
     * riscrivono i campi di cui D1 è proprietario, più i riservati. */
    for (i = 0; i < 4u; i++) {
        dst[i] = src[i];
    }
    b[SGP_C_MAGIC] = (u8)(SGP_MAGIC_CHUNK & 0xFFu);
    b[SGP_C_MAGIC + 1u] = (u8)(SGP_MAGIC_CHUNK >> 8);
    b[SGP_C_VERSIONE] = (u8)SGP_VERSIONE;
    b[SGP_C_PLUS] = s->active_plus ? 1u : 0u;
    b[SGP_C_SELVATICI] = s->active_wild ? 1u : 0u;
    b[SGP_C_RISERVATO0] = 0;
    b[SGP_C_RISERVATO1] = 0;
    dst[3] = 0;
    /* I campi degli altri cantieri si riportano NEL DOMINIO prima di scrivere.
     * Senza questo, un solo byte fuori posto (anim = 2, wifi_server = 5) rende
     * il chunk non valido al prossimo avvio: il gioco parte in modo 1.1 e — poiché
     * un chunk rifiutato non si riscrive mai — le impostazioni 1.2 sono perse per
     * sempre. Il chunk scritto è sempre un chunk che `sgp_valido` accetta. */
    b[SGP_C_OLTRE100] = b[SGP_C_OLTRE100] ? 1u : 0u;      /* D1   */
    b[SGP_C_ANIM] = b[SGP_C_ANIM] ? 1u : 0u;              /* A1-B */
    b[SGP_C_NPC] = b[SGP_C_NPC] ? 1u : 0u;                /* P2   */
    if (b[SGP_C_WIFI] > 3u) {
        b[SGP_C_WIFI] = 0u;                               /* W1   */
    }
    cap = SGP_CAP_DI(b[SGP_C_OLTRE100]);
    if (b[SGP_C_PICCO] == 0u) {
        b[SGP_C_PICCO] = 1u;                              /* D1   */
    } else if (b[SGP_C_PICCO] > cap) {
        b[SGP_C_PICCO] = (u8)cap;
    }

    f->saveno++;
    f->magic = SGP_MAGIC_FOOTER;
    f->size = SGP_PAYLOAD;
    f->idx = (u16)SGP_IDX;
    f->crc = CHIAMA_CRC(b, SGP_CRC_LEN);

    for (i = 0; i < 2u; i++) {
        CHIAMA_WB(off, b, SGP_RECORD);
        off = SGP_SETTORE_B;
    }
    s->load_status = SGP_LOAD_VALID;
}

/* -------------------------------------------------------------------- ganci */

/* L0: sostituisce `bl 0x020277D4` a 0x020271F8. r0 = SaveData*. */
__attribute__((used, noinline, section(".text")))
u32 sgp_gancio_carica(void *save)
{
    u32 esito = CHIAMA_ORIG_LOAD(save);

    sgp_chunk_leggi();
    return esito;
}

/* S0: sostituisce `bl 0x02027DB4` a 0x02027456. r0 = SaveData*.
 * L'originale torna 2 quando il salvataggio è riuscito: solo allora si scrive. */
__attribute__((used, noinline, section(".text")))
u32 sgp_gancio_salva(void *save)
{
    u32 esito = CHIAMA_ORIG_SAVE(save);

    if (esito == 2u) {
        sgp_chunk_scrivi();
    }
    return esito;
}
