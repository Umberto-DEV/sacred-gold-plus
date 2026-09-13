/* Sacred Gold Plus 1.2a — helper comuni dell'interfaccia, v2. GPL-3.0-or-later.
 *
 * Nessuna costante in `.rodata`: i testi arrivano dal blob nella riserva.
 * Nessuna allocazione propria oltre a quelle dichiarate dal chiamante.
 */
#include "sgp_ui.h"

/* Un `String` del gioco e' {u16 maxsize; u16 size; u32 magic; u16 data[]}.
 * Lo alloca String_New (che imposta `magic` e `maxsize`): qui si riempie solo il
 * corpo. Mai scrivere oltre `maxsize`: e' l'invariante che String_New dichiara e
 * che il printer del gioco assume.
 */
__attribute__((used, noinline, section(".text")))
static u32 ui_copia(String *s, const u16 *src)
{
    u32 n = 0;
    if (!s || !src) {
        return 0;
    }
    while (src[n] != SGP_EOS && n + 1u < s->maxsize) {
        s->data[n] = src[n];
        n++;
    }
    s->data[n] = SGP_EOS;
    s->size = (u16)n;
    return n;
}

/* Puntatore al testo `id` dentro il blob: gli offset stanno in testa, in byte,
 * esattamente come il blob della guida EV/IV della 1.1 (`guide_present.c`). */
__attribute__((used, noinline, section(".text")))
static const u16 *ui_testo(u32 id)
{
    const u16 *t = SGP_TESTI;
    if (id >= (u32)T_COUNT) {
        id = (u32)T_VUOTO;
    }
    return (const u16 *)((const u8 *)t + t[id]);
}

/* Stampa un testo del blob dentro `w`, con il colore e l'ALLINEAMENTO dati.
 *   modo 0  x e' il bordo sinistro
 *   modo 1  x e' il bordo destro (valori delle voci, indicatori)
 *   modo 2  x e' la larghezza utile e il testo si centra (titoli)
 * La larghezza si MISURA col font del gioco, non si stima: e' lo stesso percorso
 * di misura di tools/misura_v2.py sul Mac. Una funzione sola invece di tre: il
 * payload sta in uno scomparto di byte contati.
 * TEXT_SPEED_NOTRANSFER: nessuna copia in VRAM per riga, una sola alla fine.
 */
__attribute__((used, noinline, section(".text")))
static void ui_stampa_m(Window *w, String *s, u32 id, u32 x, u32 y, u32 colore,
                        u32 modo)
{
    u32 px;
    if (!ui_copia(s, ui_testo(id))) {
        return;
    }
    if (modo) {
        px = FontID_String_GetWidth(G_FONT, s, 0);
        if (px > x) {
            px = x;
        }
        x = (modo == 1u) ? (x - px) : ((x - px) / 2u);
    }
    AddTextPrinterWithColor(w, G_FONT, s, x, y, G_ISTANTANEO, colore, 0);
}

#define ui_stampa_col(w, s, id, x, y, c) ui_stampa_m((w), (s), (id), (x), (y), (c), 0u)
#define ui_stampa(w, s, id, x, y)        ui_stampa_m((w), (s), (id), (x), (y), G_COLORE, 0u)
#define ui_stampa_destra(w, s, id, x, y, c) ui_stampa_m((w), (s), (id), (x), (y), (c), 1u)
#define ui_stampa_centro(w, s, id, lw, y)  ui_stampa_m((w), (s), (id), (lw), (y), G_COLORE, 2u)

/* --- il default effettivo del tetto NPC: NON si fa qui (v3, allineamento) ---
 * Il difetto trovato nell'AVD (SGP-1.2-AVD-02, prova 4) era reale: con un
 * salvataggio 1.1 il chunk e' ASSENTE, il byte `npc` leggeva 0 e la pagina
 * mostrava «NO» su una funzione ACCESA (`sgp_npc_tetto` tratta «assente» come
 * acceso); confermando, il chunk veniva scritto con npc=0 e il tetto si
 * spegneva davvero.
 *
 * La cura NON sta in questa pagina. `SGP-1.2-QUALITA-NATIVO-01`
 * (`sorgenti-v-finale/salva_blob.c`, `sgp_chunk.h`) la mette dove il contratto
 * dice che deve stare — in D1, che possiede il formato: `sgp_chunk_leggi`
 * NORMALIZZA la copia in RAM a ogni avvio e, con chunk assente, ci scrive
 * `picco = 1` e `npc = 1`, cioe' i default 1.2. Da li' in poi il byte del chunk
 * E' il valore effettivo, per tutti i consumatori, e la pagina deve fare una
 * cosa sola: mostrarlo.
 *
 * Una prima stesura della v3 inizializzava il chunk qui dentro. E' stata tolta:
 * due cantieri che scrivono lo stesso default sono due posti dove sbagliarlo, e
 * il secondo non saprebbe distinguere «il giocatore l'ha spento» da «nessuno
 * l'ha ancora acceso». La pagina resta un LETTORE del chunk e uno scrittore
 * solo di cio' che il giocatore sceglie. Il legame e' dichiarato: questa v3
 * pretende il D1 v-finale sotto di se', e i due si applicano insieme.
 *
 * Offset verificati contro il contratto nuovo (`sorgenti-v-finale/sgp_chunk.h`)
 * e INVARIATI rispetto a quelli che questa pagina gia' usava: chunk a
 * 0x023D8710 (stato 0x023D8700 + 0x10), plus +0x3, selvatici +0x4, oltre100
 * +0x5, anim +0x6, npc +0x7, wifi_server +0x8; load_status +0x03, guard +0x04;
 * guardie degli altri blocchi 0x023D89E2 (P2), 0x023D8E41 (A1-B), 0x023DA240
 * (W1). La «nuova pianta» del cantiere nativo riguarda la DIMENSIONE dei blob
 * (salvataggio 500 B, plus 256 B), non gli offset del chunk.
 */
