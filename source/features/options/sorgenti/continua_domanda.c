/* Sacred Gold Plus 1.2a — schermata «attivo le nuove funzioni?» al primo avvio, v2.
 * GPL-3.0-or-later.
 *
 * DOVE, E PERCHE' LI'.
 * Il menu principale, scelto CONTINUA, registra l'overlay 36 con il template
 * `ov36_App_MainMenu_SelectOption_Continue` (0x021E5C04). Quell'app rilegge il
 * salvataggio dalla flash (`SaveData_TryLoadOnContinue`), avvia il contatore di
 * gioco, e nel suo Exit fa due sole cose:
 *      Heap_Destroy(75) ; RegisterMainOverlay(-1, gApplication_ContinueFieldsys)
 * Il puntatore al template successivo e' una PAROLA del pool letterale, a
 * **0x021E5A34**. In quel momento: salvataggio gia' in RAM, `FieldSystem` non
 * ancora creato, schermo gia' nero (il menu principale sbiadisce PRIMA di
 * uscire), nessun fotogramma dell'overworld mai disegnato. E' esattamente la
 * finestra chiesta: «dopo il caricamento del salvataggio e prima del primo
 * fotogramma di gioco».
 *
 * Il gancio e' quindi **una parola di dati**, non un'istruzione: si riscrive
 * quella parola col puntatore al NOSTRO template. Nessun byte di codice cambia
 * in ov036. Il nostro Exit registra a sua volta l'originale, e la catena
 * riprende identica.
 *
 * NUOVA PARTITA: la prima occasione equivalente e' il gemello strutturale,
 * `ov36_App_InitGameState_AfterOakSpeech` (template 0x021E5C14), il cui Exit
 * registra `gApplication_NewGameFieldsys` dal letterale **0x021E5998**.
 *
 * CHE COSA CAMBIA RISPETTO ALLA v1.
 *   A7  la nota dice **come** si tornano a cambiare: «dalle OPZIONI con SELECT».
 *       Era il solo punto del gioco in cui si poteva dirlo a costo zero, ed era
 *       l'unica cosa che mancava a una funzione altrimenti non scopribile.
 *   A8  nota e aiuto sono allineati al corpo (x = 20), non sporgono piu' a x = 8.
 *   A3  la prosa resta in tondo in tutte e due le lingue (in HGSS le frasi sono
 *       in tondo); le due etichette sono quelle della pagina, quindi in IT
 *       maiuscole come nel menu OPZIONI. Le due schermate dicono le stesse
 *       parole per la stessa cosa.
 *   §5  le due risposte partono dallo stesso valore (SI/SI): niente default
 *       asimmetrici non spiegati; il titolo e' centrato; il passo delle due
 *       righe e' 24 px come nel menu; una sola riga di aiuto invece di tre.
 *   B7  i valori sono la coppia del gioco (SI/NO in IT, On/Off in EN), la
 *       stessa che usa la pagina: una voce non cambia vocabolario da una
 *       schermata all'altra.
 *
 * RISORSE GRAFICHE. A quel punto NESSUNA grafica esiste: l'app deve accendersela.
 * Non si inventa un solo valore: banchi VRAM, modalita' e template del BG sono
 * **copiati byte per byte dall'overlay 54** (GraphicsBanks 0x021E6CD8/40 B,
 * GraphicsModes 0x021E6C48/16 B, BgTemplate del layer MAIN_1 0x021E6E3C/28 B)
 * dentro il blocco della riserva, dall'applicatore, e letti qui per valore
 * assoluto. Font 0, palette 13 (`LoadFontPal0` su SLOT_13): gli stessi della
 * pagina Opzioni. Zero asset nuovi.
 */
#include "sgp_ui.h"

/* --- altri simboli del gioco, risolti in prove/simboli-arm9.json ----------- */
#define Heap_Create            FN(void (*)(u32, u32, u32), 0x0201A910u)
#define GfGfx_SetBanks         FN(void (*)(const void *), 0x02022BE8u)
#define SetScreenModesDisable  FN(void (*)(const void *), 0x0201ACB0u)
#define BgConfig_Alloc         FN(void *(*)(u32), 0x0201AC88u)
#define InitBgFromTemplate     FN(void (*)(void *, u32, const void *, u32), 0x0201B1E4u)
#define FreeBgTilemapBuffer    FN(void (*)(void *, u32), 0x0201BB4Cu)
#define BG_ClearCharDataRange  FN(void (*)(u32, u32, u32, u32), 0x0201C1C4u)
#define LoadFontPal0           FN(void (*)(u32, u32, u32), 0x02003030u)
#define PaletteFadeBegin \
    FN(void (*)(u32, u32, u32, u32, u32, u32, u32), 0x0200FA24u)
#define PaletteFadeFinished    FN(u32 (*)(void), 0x0200FB5Cu)
#define SchermoNero            FN(void (*)(u32, u32), 0x0200FBF4u)

#define BgClearTilemapCommit   FN(void (*)(void *, u32), 0x0201CAE0u)

/* La schermata al primo avvio accende un BG tutto suo: i tile da 1 in su sono
 * liberi, quindi qui la finestra puo' essere grande (30x22 = 660 tile, dentro il
 * limite di 1024 della cella). La cornice sta a 0x3DC, fuori da quell'intervallo. */
/* §5: nella v1 il pannello toccava i bordi verticali dello schermo. Qui la
 * finestra e' 28x20 dentro una cornice che lascia un tile di margine su tutti e
 * quattro i lati (la cornice occupa le righe/colonne 1 e 22/30). */
#define C_FINESTRA_X  2u
#define C_FINESTRA_Y  2u
#define C_FINESTRA_W 28u
#define C_FINESTRA_H 20u
#define C_LARGHEZZA 224u      /* 28 tile: la larghezza utile della finestra */
#define C_BASETILE    1u

#define RIS ((const u8 *)SGP_UI_RIS_ADDR)
#define RIS_BANKS   (RIS + 0x00)      /* 40 B, da 0x021E6CD8 */
#define RIS_MODES   (RIS + 0x28)      /* 16 B, da 0x021E6C48 */
#define RIS_BGTMPL  (RIS + 0x38)      /* 28 B, da 0x021E6E3C (layer MAIN_1) */

#define HEAP_GENITORE 3u
#define HEAP_NOSTRO  75u              /* 0x4B: lo stesso id che ov036 ha appena distrutto */
#define HEAP_BYTE    0x20000u
#define PAL_MAIN_BG  0u
#define PAL_SLOT_13  0x1A0u           /* 13 * 32, come OptionsApp_SetupWindows */
#define BG_TIPO_TESTO 0u

/* geometria della schermata (pixel dentro la finestra 30x22).
 * Passo delle due righe di scelta: 24 px, quello del menu Opzioni. */
#define C_Y_TITOLO     6u
#define C_Y_RIGA1     34u
#define C_Y_RIGA2     50u
#define C_Y_SCELTA0   82u
#define C_PASSO       24u
#define C_Y_NOTA     128u
#define C_Y_AIUTO    144u
#define C_X_CURSORE    8u
#define C_X_VAL_DX   208u

/* stato aggiuntivo, dentro SgpUiState->esito:
 *   bit0-1  fase   0 chiusa/assente, 1 a schermo, 2 in uscita
 *   bit2    modo   0 Continua, 1 Nuova partita
 *   bit3    salta  1 = non si mostra niente
 */
#define F_FASE(e)  ((e) & 3u)
#define F_MODO(e)  (((e) >> 2) & 1u)
#define F_SALTA(e) (((e) >> 3) & 1u)

static u32 cont_deve_chiedere(void)
{
    /* Si chiede solo se il chunk non c'e' ancora o non e' mai stato visto.
     * Un chunk RIFIUTATO non fa apparire la domanda: il gioco resta in modo 1.1
     * e non si scrive niente (CONTRATTO-D1 §3.4). */
    if (SGP_D1_GUARDIA != SGP_D1_GUARD) {
        return 0u;
    }
    if (SGP_D1_LOAD == SGP_LOAD_REJECT) {
        return 0u;
    }
    /* Si chiede quando il chunk **manca** (`load_status = 1 ABSENT`, cioe' un
     * salvataggio 1.1). Con un chunk valido (2) la scelta c'e' gia'; con un
     * chunk rifiutato (3) il gioco resta in modo 1.1 e non si chiede niente.
     * CONTRATTO-CHUNK §4. Nota: `magic`, `versione` e `picco` sono di D1 e
     * questa pagina **non** li tocca — li scrive il gancio S0 di PLUS-03 al
     * primo salvataggio del giocatore, ed e' da quel momento che la domanda non
     * torna piu'. Finche' il giocatore non salva, la domanda si rifa' a ogni
     * avvio: e' corretto, perche' niente e' stato reso permanente. */
    return (SGP_D1_LOAD == 1u) ? 1u : 0u;
}

__attribute__((used, noinline, section(".text")))
static void cont_disegna(void)
{
    SgpUiState *u = SGP_UI;
    Window *w = SGP_CONT_FIN;
    String *s = u->stringa;
    u32 nuova = F_MODO(u->esito);
    u32 r, y;

    FillWindowPixelBuffer(w, G_RIEMPIMENTO);
    ui_stampa_centro(w, s, (u32)T_C_TITOLO, C_LARGHEZZA, C_Y_TITOLO);
    ui_stampa(w, s, nuova ? (u32)T_C_RIGA1N : (u32)T_C_RIGA1, G_X_NOME, C_Y_RIGA1);
    ui_stampa(w, s, nuova ? (u32)T_C_RIGA2N : (u32)T_C_RIGA2, G_X_NOME, C_Y_RIGA2);

    /* Le due righe sono le voci 0 e 1 della pagina: stessa etichetta, stessi
     * valori, stesso ordine. Chi le rivede nelle OPZIONI le riconosce. */
    for (r = 0u; r < 2u; r++) {
        y = C_Y_SCELTA0 + r * C_PASSO;
        if ((u32)u->cursore == r) {
            ui_stampa(w, s, (u32)T_CURSORE, C_X_CURSORE, y);
        }
        ui_stampa(w, s, (u32)SGP_VOCI[r].nome, G_X_NOME, y);
        ui_stampa_destra(w, s, (u32)SGP_VOCI[r].val0 + (u32)u->val[r],
                         C_X_VAL_DX, y, G_COLORE);
    }

    ui_stampa(w, s, (u32)T_C_NOTA, G_X_NOME, C_Y_NOTA);
    ui_stampa(w, s, (u32)T_C_AIUTO, G_X_NOME, C_Y_AIUTO);
    CopyWindowToVram(w);
}

__attribute__((used, noinline, section(".text")))
static u32 cont_init(void *manager, int *state, u32 modo)
{
    SgpUiState *u = SGP_UI;
    Window *w = SGP_CONT_FIN;
    void *bg;
    (void)manager;

    if (*state == 0) {
        u->guard = SGP_UI_GUARD;
        u->cursore = 0u;
        u->esito = (modo << 2);
        if (!cont_deve_chiedere()) {
            u->esito |= 8u;                     /* salta: nessuna grafica accesa */
            return 1u;
        }
        /* v3: niente default scritti qui. Li materializza D1 all'avvio
         * (v-finale, `sgp_chunk_leggi`), prima ancora che questa schermata
         * esista: quando si arriva qui il chunk in RAM e' gia' quello giusto e
         * questa schermata scrive solo le due scelte del giocatore. */
        /* §5: le due proposte partono dallo stesso valore. Chi preme A senza
         * leggere ottiene una scelta coerente, non una accesa e una spenta. */
        u->val[0] = 1u;
        u->val[1] = 1u;
        u->val0[0] = u->val[0];
        u->val0[1] = u->val[1];

        SchermoNero(0u, 0u);
        SchermoNero(1u, 0u);
        GfGfx_SetBanks(RIS_BANKS);
        SetScreenModesDisable(RIS_MODES);
        Heap_Create(HEAP_GENITORE, HEAP_NOSTRO, HEAP_BYTE);
        bg = BgConfig_Alloc(HEAP_NOSTRO);
        u->bg_cont = bg;
        if (!bg) {
            u->esito |= 8u;
            return 1u;
        }
        InitBgFromTemplate(bg, G_BG_MAIN1, RIS_BGTMPL, BG_TIPO_TESTO);
        BgClearTilemapCommit(bg, G_BG_MAIN1);
        BG_ClearCharDataRange(G_BG_MAIN1, 32u, 0u, HEAP_NOSTRO);
        LoadFontPal0(PAL_MAIN_BG, PAL_SLOT_13, HEAP_NOSTRO);

        u->stringa = String_New(64u, HEAP_NOSTRO);
        LoadUserFrameGfx2(bg, G_BG_MAIN1, G_CORNICE_TILE, G_CORNICE_PAL, 0u,
                          HEAP_NOSTRO);
        AddWindowParameterized(bg, w, G_BG_MAIN1,
                               C_FINESTRA_X, C_FINESTRA_Y, C_FINESTRA_W,
                               C_FINESTRA_H, G_PALETTE, C_BASETILE);
        if (!u->stringa || !w->pixels) {
            u->esito |= 8u;
            return 1u;
        }
        DrawFrameAndWindow2(w, 1u, G_CORNICE_TILE, G_CORNICE_PAL);
        cont_disegna();
        ToggleBgLayer(G_BG_MAIN1, 1u);
        u->esito = (u->esito & ~3u) | 1u;
        u->aperture++;
        PaletteFadeBegin(0u, 1u, 1u, 0u, 6u, 1u, HEAP_NOSTRO);
        *state = 1;
        return 0u;
    }
    return PaletteFadeFinished() ? 1u : 0u;
}

__attribute__((used, noinline, section(".text")))
static u32 cont_main(void *manager, int *state)
{
    SgpUiState *u = SGP_UI;
    u32 k = K_NEW;
    (void)manager;

    if (F_SALTA(u->esito)) {
        return 1u;
    }
    if (*state == 1) {
        return PaletteFadeFinished() ? 1u : 0u;
    }

    u->eventi++;
    if (k & (K_UP | K_DOWN)) {
        u->cursore = u->cursore ? 0u : 1u;
        PlaySE(SE_SCORRI);
        cont_disegna();
    } else if (k & (K_LEFT | K_RIGHT)) {
        u->val[u->cursore] = (u8)(u->val[u->cursore] ? 0u : 1u);
        PlaySE(SE_SCORRI);
        cont_disegna();
    } else if (k & (K_A | K_B)) {
        if (k & K_A) {
            /* A conferma: si scrive lo stato D1 e si alza continue_seen, cosi'
             * la domanda non torna. La persistenza nel chunk del salvataggio la
             * fa D1.2 con WriteExtraSaveChunk: qui si tocca solo la RAM. */
            if (SGP_D1_GUARDIA == SGP_D1_GUARD
                && SGP_D1_LOAD != SGP_LOAD_REJECT) {
                opz_scrivi(Q_D1_PLUS, u->val[0]);
                opz_scrivi(Q_D1_WILD, u->val[1]);
                u->salvataggi++;
            }
        }
        PlaySE((k & K_A) ? SE_SALVA : SE_ANNULLA);
        /* B = «dopo»: non scrive nulla e NON alza continue_seen — la domanda
         * riappare al prossimo avvio, come prescrive 13 §3.4(b). */
        u->esito = (u->esito & ~3u) | 2u;
        PaletteFadeBegin(0u, 0u, 0u, 0u, 6u, 1u, HEAP_NOSTRO);
        *state = 1;
    }
    return 0u;
}

__attribute__((used, noinline, section(".text")))
static u32 cont_exit(void *manager, int *state, const void *successivo)
{
    SgpUiState *u = SGP_UI;
    Window *w = SGP_CONT_FIN;
    (void)manager;
    (void)state;

    if (!F_SALTA(u->esito)) {
        if (w->pixels) {
            ClearFrameAndWindow2(w, 0u);
            ClearWindowTilemapAndCopyToVram(w);
            RemoveWindow(w);
        }
        if (u->stringa) {
            String_Delete(u->stringa);
            u->stringa = 0;
        }
        if (u->bg_cont) {
            FreeBgTilemapBuffer(u->bg_cont, G_BG_MAIN1);
            u->bg_cont = 0;
        }
        Heap_Destroy(HEAP_NOSTRO);
    }
    u->esito = 0u;
    RegisterMainOverlay(0xFFFFFFFFu, successivo);
    return 1u;
}

/* --- le sei entrate registrate nei due template della riserva -------------- */
__attribute__((used, noinline, section(".text")))
int sgp_cont_init(void *m, int *s) { return (int)cont_init(m, s, 0u); }
__attribute__((used, noinline, section(".text")))
int sgp_cont_main(void *m, int *s) { return (int)cont_main(m, s); }
__attribute__((used, noinline, section(".text")))
int sgp_cont_exit(void *m, int *s)
{
    return (int)cont_exit(m, s, (const void *)SGP_TPL_CONTINUA_SUCC);
}

__attribute__((used, noinline, section(".text")))
int sgp_new_init(void *m, int *s) { return (int)cont_init(m, s, 1u); }
__attribute__((used, noinline, section(".text")))
int sgp_new_main(void *m, int *s) { return (int)cont_main(m, s); }
__attribute__((used, noinline, section(".text")))
int sgp_new_exit(void *m, int *s)
{
    return (int)cont_exit(m, s, (const void *)SGP_TPL_NUOVA_SUCC);
}
