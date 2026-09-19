/* Sacred Gold Plus 1.2a — pagina «Sacred Gold Plus» dentro il menu OPZIONI, v2.
 * GPL-3.0-or-later.
 *
 * PERCHE' UNA PAGINA NOSTRA E NON UNA VOCE IN PIU'.
 * Il menu Opzioni di HG ha 7 voci FISSE (`options_app.c`: `MENU_ENTRY_COUNT = 7`,
 * `sMenuEntryBorderYCoords[7]` da -8 a -156, `sNumChoicesPerMenuEntry[7]`,
 * cursore a 3 bit in `data->unk10`, 16 hitbox di tocco, i nomi letti come
 * `msg_0045_00001 + i`). Aggiungere una voce significa allargare SEI tabelle, il
 * bitfield, il banco messaggi e il layout — su codice che oggi funziona, e con
 * 156 px gia' usati su 176. SELECT invece **non e' letto da nessuna riga**
 * dell'overlay 54 (verificato: l'unico decodificatore di maschere e'
 * `OptionsApp_HandleKeyInput`, che prova 0x10/0x20/0x40/0x80/0x01/0x02 e mai
 * 0x04): e' libero.
 *
 * CHE COSA CAMBIA RISPETTO ALLA v1 (SGP-1.2-OPZIONI-01), e perche'.
 *   A1  lo sfondo del menu (MAIN_2) si SPEGNE davvero all'apertura e si riaccende
 *       alla chiusura. La v1 lo prometteva nei commenti e non lo faceva: dietro
 *       il pannello si vedeva un menu mezzo cancellato.
 *   A2  la riga di aiuto dice «A: salva  B: annulla». Su/giu' e sinistra/destra
 *       sono ovvi; «B scarta» no, ed era l'unica riga che non veniva disegnata.
 *   A3  maiuscole scelte per lingua (IT tutto maiuscolo come OPZIONI, EN Title
 *       Case come Options): e' nei testi, non qui.
 *   A6  niente voci segnaposto con il numero di versione nella colonna dei
 *       valori. Le voci sono quelle vere, e una voce il cui proprietario non e'
 *       ancora nella ROM o si nasconde o resta disattivata — mai con un'etichetta
 *       «(1.3)».
 *   A8  titolo, voci, valori e aiuto hanno lo stesso margine sinistro (x = 20).
 *   B1/B2 sette righe visibili al passo vanilla di 24 px, senza scorrimento:
 *       una finestra sottile per riga piu' un tile bianco condiviso.
 *   C2  la riga selezionata e' una barra piena, come nel menu vanilla, non solo
 *       una freccia (la freccia resta: e' il cursore del gioco).
 *
 * v5 (19/09/2026, 1.2.2 aggiornata): il suggerimento «SELECT → PLUS» torna a
 *   OGNI ingresso nel menu Opzioni. Prima mancava dal secondo ingresso in poi
 *   (misurato sul banco melonDS, ROM 1.2.2 IT): l'app Opzioni rinasce allo
 *   stesso indirizzo di heap, quindi `u->app != app` non scattava, e il flag
 *   `sugg` restava a 1 mentre l'init vanilla aveva azzerato il layer. Ora
 *   `opz_suggerimento` chiede alla TILEMAP se la riga c'e', e il flag e' solo
 *   uno specchio per la diagnostica. Nello stesso giro: le tre `Window` sullo
 *   stack ricevono `pixels = 0` prima di `AddWindowParameterized`, che non le
 *   scrive quando fallisce — il controllo `!w.pixels` leggeva pila non
 *   inizializzata.
 */
#include "sgp_ui.h"

#define BgClearTilemapCommit   FN(void (*)(void *, u32), 0x0201CAE0u)
/* Gli sprite del menu (le «pillole» dei valori, le frecce del riquadro, i pulsanti
 * Confirm/Quit) hanno priorita' 2 e restano DIETRO al BG della pagina, ma sotto il
 * pannello continuerebbero a vedersi. Si spegne il piano OBJ del motore principale
 * con la stessa funzione che l'app usa per accenderlo
 * (`GfGfx_EngineATogglePlanes(0x10, 1)` a 0x021E6A82 e 0x021E5D74). */
#define TogglePianiA           FN(void (*)(u32, u32), 0x02022C60u)
#define PIANO_OBJ 0x10u

/* Campi dell'OptionsApp_Data (offset verificati sul binario + options_app.c) */
#define APP_HEAP(a)     (*(u32 *)((u8 *)(a) + 0x00))
#define APP_STATO(a)    (*(u32 *)((u8 *)(a) + 0x10))   /* bit0-1 uscita, bit2-4 cursore */
#define APP_BGCONFIG(a) (*(void **)((u8 *)(a) + 0x14))
#define APP_WINDOWS(a)  ((Window *)((u8 *)(a) + 0x34)) /* 5 Window contigue */
#define APP_NWINDOWS    5u
/* bitfield delle opzioni in lavorazione: textSpeed:4 soundMethod:2 battleScene:1
 * battleStyle:1 buttonMode:2 frame:5 dummy:1 — la cornice e' nei bit 10-14. */
#define APP_CORNICE(a)  ((*(u16 *)((u8 *)(a) + 0x18) >> 10) & 0x1Fu)

#define SCHERMO_TILE_Y 24u
/* Il suggerimento vive sopra lo sfondo del menu (fondo 0 = trasparente), in una
 * banda grigio-azzurra: testo BIANCO con ombra scura, come le etichette dei
 * pulsanti OK/CHIUDI che gli stanno accanto. Provato a 1x: con testo scuro e
 * ombra bianca la riga si perdeva sul fondo. */
#define G_COLORE_SUGG ((15u << 16) | (1u << 8) | 0u)

/* --- lo stato altrui: presenza, lettura, scrittura ------------------------- */
/* La pagina non possiede nessuno di questi byte. «Presente» vuol dire: il
 * proprietario ha scritto la sua guardia. Se non c'e', la voce non si tocca. */
__attribute__((used, noinline, section(".text")))
static u32 opz_presente(u32 quale)
{
    /* v4 (A1 della revisione R2). PRECONDIZIONE UNICA, per OGNI voce: la
     * pagina e' un consumatore del chunk di D1 come tutti gli altri, e applica
     * la STESSA regola dell'accessore unico `sgp_chunk_opzione`
     * (`native-core/sorgenti-v-finale/sgp_chunk.h`): serve la guardia di D1 E un
     * `load_status` utilizzabile, cioe' ASSENTE (1) o VALIDO (2).
     *
     * Fino alla v3 questa regola valeva solo per Q_D1_PLUS/Q_D1_WILD; le altre
     * tre voci guardavano la sola guardia del PROPRIETARIO — un byte che scrive
     * l'iniettore e che vale sempre 0x5A/0x57, quindi «presente» sempre.
     * Con `load_status = 3 RIFIUTATO` (chunk trovato ma con un'invariante
     * violata) o `= 0 NONE` (gancio L0 mai eseguito) i consumatori leggono 0 e
     * `sgp_chunk_scrivi` rifiuta di scrivere, ma la pagina mostrava lo stesso le
     * tre voci attive: il giocatore spostava il cursore, premeva A, sentiva la
     * conferma, vedeva il valore nuovo disegnato — e non succedeva niente, ne'
     * allora ne' mai. La mitigazione esisteva solo per il pennino (il tocco
     * sulla riga dei comandi era gia' disabilitato); A e B restavano attivi.
     *
     * Con la precondizione qui, `opz_visibili` non conta piu' quelle voci,
     * `opz_scrivi` esce subito, e la riga dei comandi resta quella di
     * T_RIFIUTATO: niente si lascia confermare. */
    if (SGP_D1_GUARDIA != SGP_D1_GUARD
        || (SGP_D1_LOAD != SGP_LOAD_ABSENT && SGP_D1_LOAD != SGP_LOAD_VALID)) {
        return 0u;
    }
    if (quale == Q_D1_PLUS || quale == Q_D1_WILD) {
        return 1u;
    }
    if (quale == Q_ANIM) {
        return SGP_ANIM_GUARD == SGP_D1_GUARD ? 1u : 0u;
    }
    if (quale == Q_NPC) {
        return SGP_NPC_GUARD == SGP_D1_GUARD ? 1u : 0u;
    }
    if (quale == Q_WIFI) {
        return SGP_W1_MAGIC == SGP_W1_MAGIC_OK ? 1u : 0u;
    }
    return 0u;
}

__attribute__((used, noinline, section(".text")))
static u32 opz_leggi(u32 quale)
{
    u32 s;
    if (quale == Q_D1_PLUS) {
        return SGP_CHUNK[C_PLUS] ? 1u : 0u;
    }
    if (quale == Q_D1_WILD) {
        return SGP_CHUNK[C_SELVATICI] ? 1u : 0u;
    }
    if (quale == Q_ANIM) {
        return SGP_CHUNK[C_ANIM] ? 1u : 0u;
    }
    if (quale == Q_NPC) {
        return SGP_CHUNK[C_NPC] ? 1u : 0u;
    }
    if (quale == Q_WIFI) {
        /* 0 Originale · 1 slot 2 · 2 slot 3. Lo slot 1 e' del Dono Segreto e si
         * sceglie da solo: non e' una voce (CONTRATTO-W1 §1b.5). Il dominio del
         * byte nel chunk e' 0..3 (CONTRATTO-CHUNK §2). */
        s = SGP_CHUNK[C_WIFI];
        if (s == 0u) {
            return 0u;
        }
        return (s == 3u) ? 2u : 1u;
    }
    return 0u;
}

__attribute__((used, noinline, section(".text")))
static void opz_scrivi(u32 quale, u32 v)
{
    if (!opz_presente(quale)) {
        return;
    }
    if (quale == Q_D1_PLUS) {
        SGP_CHUNK[C_PLUS] = (u8)v;
        SGP_D1_ACTIVE_PLUS = (u8)v;    /* la copia operativa che legge il gancio */
    } else if (quale == Q_D1_WILD) {
        SGP_CHUNK[C_SELVATICI] = (u8)v;
        SGP_D1_ACTIVE_WILD = (u8)v;
    } else if (quale == Q_ANIM) {
        SGP_CHUNK[C_ANIM] = (u8)v;
    } else if (quale == Q_NPC) {
        SGP_CHUNK[C_NPC] = (u8)v;
    } else if (quale == Q_WIFI) {
        SGP_CHUNK[C_WIFI] = (u8)(v ? (v + 1u) : 0u);   /* 1 → slot 2, 2 → slot 3 */
    }
}

/* --- quali voci si vedono -------------------------------------------------- */
/* Una voce il cui proprietario non e' nella ROM: o si NASCONDE (bit4 di `modo`,
 * il caso di A1-B finche' non viene spedito) o resta visibile e DISATTIVATA
 * (W1, P2). In nessun caso si mostra un numero di versione. */
__attribute__((used, noinline, section(".text")))
static void opz_visibili(void)
{
    SgpUiState *u = SGP_UI;
    u32 i, n = 0u;
    /* v3: nessuna inizializzazione qui. La copia in RAM del chunk arriva gia'
     * normalizzata ai default 1.2 da D1 (`sgp_chunk_leggi` del cantiere nativo
     * v-finale): la pagina LEGGE il valore effettivo e non lo riscrive mai di
     * sua iniziativa. Vedi il commento in cima a ui_comune.c. */
    for (i = 0u; i < SGP_N_VOCI; i++) {
        u32 m = SGP_VOCI[i].modo;
        u32 q = V_QUALE(m);
        u->val[i] = (u8)(opz_presente(q) ? opz_leggi(q) : 0u);
        u->val0[i] = u->val[i];
        if (!opz_presente(q) && V_NASCONDI(m)) {
            continue;
        }
        if (n < SGP_MAX_VOCI) {
            u->vis[n] = (u8)i;
            n++;
        }
    }
    u->n_vis = (u8)n;
    /* La geometria si calcola QUI, una volta sola, e sta nello stato: il
     * pannello cresce con le voci e si ricentra da solo. Ricalcolarla a ogni
     * uso costava piu' di un chilobyte di codice in un blocco da 4 KiB. */
    u->n_righe = (u8)(n + 2u);
    u->altezza = (u8)(G_PASSO_TILE * (n + 1u) + G_H_TILE);
    u->ycont = (u8)((SCHERMO_TILE_Y - ((u32)u->altezza + 2u)) / 2u + 1u);
}

/* Quale riga di aiuto va mostrata. Era in linea dentro `opz_disegna_riga`; la v3
 * la estrae perche' serve anche al TOCCO: i due comandi si possono toccare solo
 * quando sono davvero a schermo. */
__attribute__((used, noinline, section(".text")))
static u32 opz_aiuto_id(void)
{
    SgpUiState *u = SGP_UI;
    if (SGP_D1_LOAD == SGP_LOAD_REJECT) {
        return (u32)T_RIFIUTATO;
    }
    if (u->n_vis && !opz_presente(V_QUALE(SGP_VOCI[u->vis[u->cursore]].modo))) {
        return (u32)T_BLOCCATO;
    }
    return (u32)T_AIUTO_A;
}

/* --- geometria a runtime --------------------------------------------------- */
/* Tutto deriva da n_vis: il pannello cresce e si ricentra da solo, e il conto dei
 * tile e' fisso per costruzione (G_RIGHE_MAX righe al massimo, mai di piu'). */
#define OPZ_RIGHE(u)   ((u32)(u)->n_righe)
#define OPZ_ALTEZZA(u) ((u32)(u)->altezza)
#define OPZ_YCONT(u)   ((u32)(u)->ycont)

/* La cornice del gioco legge dalla `Window` solo bgConfig/bgId/x/y/w/h
 * (0x0200E948 + i cinque accessori): un rettangolo che non e' una finestra vera
 * basta, e non costa un tile in piu' di quelli della cornice stessa. */
__attribute__((used, noinline, section(".text")))
static void opz_rettangolo(Window *c, void *bg)
{
    SgpUiState *u = SGP_UI;
    c->bgConfig = bg;
    c->bgId = (u8)G_BG_MAIN1;
    c->x = (u8)G_PANNELLO_X;
    c->y = (u8)OPZ_YCONT(u);
    c->w = (u8)G_W_TILE;
    c->h = (u8)OPZ_ALTEZZA(u);
    c->pal = (u8)G_PALETTE;
    c->baseTile = 0u;
    c->pixels = 0;
}

/* --- disegno --------------------------------------------------------------- */
/* Una riga alla volta: si crea la finestra, si riempie, si stampa, si copia in
 * VRAM e si chiude. Il trasferimento e' SINCRONO (`CopyWindowToVram` →
 * 0x0201D7F4 → 0x0201C0EC: alloca un buffer temporaneo, scrive e lo libera
 * dentro la chiamata), quindi la finestra puo' sparire subito: restano la
 * tilemap e i caratteri in VRAM. Sette `Window` vive costerebbero 112 B di
 * stato e un centinaio di byte di codice in un blocco di byte contati. */
__attribute__((used, noinline, section(".text")))
static void opz_disegna_riga(void *bg, u32 r)
{
    SgpUiState *u = SGP_UI;
    Window w;
    String *s = u->stringa;
    u32 i, q, sel, colore;

    /* v5: `AddWindowParameterized` (bg_window.c:1560) NON tocca la Window se
     * il layer non ha tilemap o se Heap_Alloc fallisce: senza questo azzeramento
     * il controllo su `pixels` leggeva un byte di pila mai scritto. */
    w.pixels = 0;
    AddWindowParameterized(bg, &w, G_BG_MAIN1, G_PANNELLO_X,
                           (u32)u->ycont + G_PASSO_TILE * r,
                           G_W_TILE, G_H_TILE, G_PALETTE,
                           G_BASETILE + r * G_TILE_RIGA);
    if (!w.pixels) {
        return;
    }
    sel = (r >= 1u && r <= (u32)u->n_vis && (u32)u->cursore == r - 1u) ? 1u : 0u;
    colore = sel ? G_COLORE_SEL : G_COLORE;
    FillWindowPixelBuffer(&w, sel ? G_RIEMPIMENTO_SEL : G_RIEMPIMENTO);

    if (r == 0u) {
        ui_stampa(&w, s, (u32)T_TITOLO, G_X_NOME, 0u);
    } else if (r + 1u == (u32)u->n_righe) {
        /* La riga di aiuto, che cambia col contesto (A2). v3: quando dice i
         * comandi, le due meta' stanno nelle STESSE due colonne delle voci —
         * «A: salva» a sinistra come un'etichetta, «B: annulla» a destra come un
         * valore — e sono i due BERSAGLI del tocco, cioe' i Conferma/Chiudi del
         * menu vanilla. Un allineamento in piu' e un pulsante in piu', zero tile. */
        i = opz_aiuto_id();
        ui_stampa(&w, s, i, G_X_NOME, 0u);
        if (i == (u32)T_AIUTO_A) {
            ui_stampa_destra(&w, s, (u32)T_AIUTO_B, G_X_VAL_DX, 0u, G_COLORE);
        }
    } else {
        i = u->vis[r - 1u];
        q = V_QUALE(SGP_VOCI[i].modo);
        if (sel) {
            ui_stampa_col(&w, s, (u32)T_CURSORE, G_X_CURSORE, 0u, colore);
        }
        if (!opz_presente(q)) {
            colore = G_COLORE_OFF;
        }
        ui_stampa_col(&w, s, (u32)SGP_VOCI[i].nome, G_X_NOME, 0u, colore);
        ui_stampa_destra(&w, s, (u32)SGP_VOCI[i].val0 + (u32)u->val[i],
                         G_X_VAL_DX, 0u, colore);
    }
    CopyWindowToVram(&w);
    RemoveWindow(&w);
}

__attribute__((used, noinline, section(".text")))
static void opz_disegna(void *bg)
{
    u32 r, n = (u32)SGP_UI->n_righe;
    for (r = 0u; r < n; r++) {
        opz_disegna_riga(bg, r);
    }
}

/* --- il suggerimento nel menu vanilla -------------------------------------- */
/* REVISIONE-QUALITA §6: «non si scopre». Una riga nella banda libera in basso a
 * sinistra del menu Opzioni (x 0..116, y 172..191 — misurato sui fotogrammi
 * vanilla EN e IT: i pulsanti OK/CHIUDI cominciano a x=117) dice che SELECT
 * porta alla pagina. Sfondo trasparente: si vedono solo i glifi, sopra lo sfondo
 * del menu, come fa il gioco. Non coesiste mai con la pagina, quindi riusa gli
 * stessi tile: costo netto zero tile. */
__attribute__((used, noinline, section(".text")))
static void opz_suggerimento(void *app, u32 accendi)
{
    SgpUiState *u = SGP_UI;
    Window w;
    String *s;
    void *bg = APP_BGCONFIG(app);
    u16 *cella;
    u32 disegnato;

    if (!bg) {
        return;
    }
    /* v5. «E' a schermo?» lo dice la tilemap del layer, non un flag nostro.
     * Il flag `sugg` vive nella riserva ARM9 e sopravvive all'app Opzioni; l'app
     * invece muore e rinasce a ogni ingresso nel menu, il suo init azzera la
     * tilemap (`BgClearTilemapBufferAndCommit`), e l'allocatore le ridà lo
     * STESSO indirizzo: `u->app != app` non scattava, `sugg` diceva 1, e la riga
     * non tornava finche' la pagina non veniva aperta e chiusa. Misurato sul
     * banco melonDS (19/09/2026): seconda istanza a 0x022C0264 come la prima,
     * `sugg` = 1, banda vuota nei fotogrammi 20 e 21.
     * La cella (G_SUGG_X, G_SUGG_Y) contiene il tile G_BASETILE se e solo se la
     * riga e' disegnata: nessuna finestra vanilla arriva a quel tile (finiscono
     * a 0x274 escluso) e la pagina, che lo riusa, non coesiste mai con la riga.
     * Senza tilemap non c'e' niente da fare: `AddWindowParameterized` uscirebbe
     * a vuoto comunque (bg_window.c:1561). */
    cella = BG_TILEMAP(bg, G_BG_MAIN1);
    if (!cella) {
        return;
    }
    cella += G_SUGG_Y * BG_CELLE_RIGA + G_SUGG_X;
    disegnato = (CELLA_TILE(*cella) == G_BASETILE) ? 1u : 0u;
    u->sugg = (u8)disegnato;
    if (disegnato == accendi) {
        return;
    }
    w.pixels = 0;                          /* v5: vedi opz_disegna_riga */
    AddWindowParameterized(bg, &w, G_BG_MAIN1, G_SUGG_X, G_SUGG_Y,
                           G_SUGG_W, G_SUGG_H, G_PALETTE, G_BASETILE);
    if (!w.pixels) {
        return;
    }
    if (accendi) {
        s = String_New(64u, APP_HEAP(app));
        if (s) {
            FillWindowPixelBuffer(&w, 0x00u);
            ui_stampa_col(&w, s, (u32)T_SUGGERIMENTO, G_SUGG_TX, 0u,
                          G_COLORE_SUGG);
            CopyWindowToVram(&w);
            String_Delete(s);
            u->sugg = 1u;
        }
    } else {
        ClearWindowTilemapAndCopyToVram(&w);
        u->sugg = 0u;
    }
    RemoveWindow(&w);
}

/* --- apertura e chiusura --------------------------------------------------- */
/* Fallisce CHIUSA se una risorsa manca: non si apre mai una pagina a meta'.
 * `AddWindowParameterized` esce in silenzio se il BG non ha un buffer tilemap,
 * quindi il controllo e' su `pixels` DOPO la chiamata. */
__attribute__((used, noinline, section(".text")))
static u32 opz_apri(void *app)
{
    SgpUiState *u = SGP_UI;
    Window w;
    void *bg = APP_BGCONFIG(app);
    u32 heap = APP_HEAP(app);

    if (u->aperta || !bg) {
        return 0u;
    }
    opz_visibili();
    if ((u32)u->n_righe > G_RIGHE_MAX) {
        return 0u;                /* cancello G7 a runtime: mai oltre il budget */
    }
    u->stringa = String_New(64u, heap);
    if (!u->stringa) {
        return 0u;
    }
    opz_suggerimento(app, 0u);
    LoadUserFrameGfx2(bg, G_BG_MAIN1, G_CORNICE_TILE, G_CORNICE_PAL,
                      APP_CORNICE(app), heap);

    /* A1. La barra di evidenziazione vanilla (MAIN_0, priorita' 0) sta SOPRA la
     * nostra finestra e lo sfondo del menu (MAIN_2) si vedrebbe tutt'intorno:
     * si spengono ENTRAMBI, piu' il piano OBJ degli sprite. Alla chiusura si
     * riaccendono. Nella v1 la riga per MAIN_2 non esisteva, e dietro il
     * pannello restava un menu mezzo cancellato. */
    ToggleBgLayer(G_BG_MAIN0, 0u);
    ToggleBgLayer(G_BG_MAIN2, 0u);
    TogglePianiA(PIANO_OBJ, 0u);
    BgClearTilemapCommit(bg, G_BG_MAIN1);

    /* Il tile bianco condiviso: una finestra 1x1 riempita del colore di fondo.
     * Il suo unico tile riempie tutte le celle del pannello, comprese quelle
     * fra una riga e l'altra: e' cio' che permette il passo di 24 px senza
     * pagare 24 tile per ogni riga vuota. */
    w.pixels = 0;                          /* v5: vedi opz_disegna_riga */
    AddWindowParameterized(bg, &w, G_BG_MAIN1, G_PANNELLO_X, (u32)u->ycont,
                           1u, 1u, G_PALETTE, G_TILE_BIANCO);
    if (!w.pixels) {
        String_Delete(u->stringa);
        u->stringa = 0;
        ToggleBgLayer(G_BG_MAIN2, 1u);
        TogglePianiA(PIANO_OBJ, 1u);
        return 0u;
    }
    FillWindowPixelBuffer(&w, G_RIEMPIMENTO);
    CopyWindowToVram(&w);
    RemoveWindow(&w);
    FillBgTilemapRect(bg, G_BG_MAIN1, G_TILE_BIANCO, G_PANNELLO_X,
                      (u32)u->ycont, G_W_TILE, (u32)u->altezza, G_PALETTE);
    opz_rettangolo(&w, bg);
    DrawFrameAndWindow2(&w, 1u, G_CORNICE_TILE, G_CORNICE_PAL);

    u->app = app;
    u->guard = SGP_UI_GUARD;
    u->cursore = 0u;
    u->aperture++;
    u->aperta = 1u;
    opz_disegna(bg);
    PlaySE(SE_SCORRI);
    return 1u;
}

/* Chiusura. Azzerare l'intera tilemap del BG e ristampare le cinque finestre
 * vanilla e' l'unica strada che riporta il menu **identico**: la cornice scrive
 * celle anche fuori dal rettangolo, e nella v1 cancellare solo la finestra
 * lasciava 4865 byte di differenza su un fotogramma. La barra di evidenziazione
 * la rimette `ov54_021E69D4`, che sa se la riga corrente e' quella dei pulsanti
 * (in quel caso MAIN_0 resta spento): non lo decidiamo noi. */
__attribute__((used, noinline, section(".text")))
static void opz_chiudi(u32 conferma)
{
    SgpUiState *u = SGP_UI;
    void *app = u->app;
    void *bg = app ? APP_BGCONFIG(app) : 0;
    u32 i;

    if (!u->aperta) {
        return;
    }
    if (conferma) {
        for (i = 0u; i < SGP_N_VOCI; i++) {
            if (u->val[i] != u->val0[i]) {
                opz_scrivi(V_QUALE(SGP_VOCI[i].modo), u->val[i]);
                u->salvataggi++;
            }
        }
    }
    PlaySE(conferma ? SE_SALVA : SE_ANNULLA);
    if (bg) {
        BgClearTilemapCommit(bg, G_BG_MAIN1);
    }
    if (app) {
        for (i = 0u; i < APP_NWINDOWS; i++) {
            Window *v = &APP_WINDOWS(app)[i];
            if (v->pixels) {
                CopyWindowToVram(v);
            }
        }
    }
    TogglePianiA(PIANO_OBJ, 1u);
    ToggleBgLayer(G_BG_MAIN2, 1u);
    if (u->stringa) {
        String_Delete(u->stringa);
        u->stringa = 0;
    }
    u->aperta = 0u;
    u->sugg = 0u;
    if (app) {
        opz_suggerimento(app, 1u);
        OPZ_EVIDENZIA(app, (APP_STATO(app) >> 2) & 7u);
    }
}

/* --- comandi --------------------------------------------------------------- */
static void opz_muovi(s32 delta)
{
    SgpUiState *u = SGP_UI;
    s32 c;
    if (!u->n_vis) {
        return;
    }
    c = (s32)u->cursore + delta;
    if (c < 0) {
        c = (s32)u->n_vis - 1;
    } else if (c >= (s32)u->n_vis) {
        c = 0;
    }
    u->cursore = (u8)c;
}

/* Cambio valore. Una voce il cui proprietario manca NON cambia e NON suona: si
 * comporta come una voce disabilitata di un menu ufficiale, non come un tasto che
 * non fa niente. I valori non girano in tondo: si fermano ai due estremi, come i
 * cursori del menu vanilla. */
static u32 opz_cambia(s32 delta)
{
    SgpUiState *u = SGP_UI;
    u32 i, q, nval;
    s32 v;

    if (!u->n_vis) {
        return 0u;
    }
    i = u->vis[u->cursore];
    q = V_QUALE(SGP_VOCI[i].modo);
    nval = SGP_VOCI[i].nval;
    if (!opz_presente(q) || nval < 2u) {
        return 0u;
    }
    /* v3: `delta == 0` vuol dire CICLICO ed e' il gesto del tocco (toccare una
     * pillola del menu vanilla non ha un verso: porta al valore successivo e
     * ricomincia). Coi tasti sinistra/destra il valore continua a fermarsi agli
     * estremi, come nel vanilla. Un solo corpo invece di due quasi uguali: il
     * blocco e' di byte contati. */
    v = (s32)u->val[i] + (delta ? delta : 1);
    if (!delta) {
        if (v >= (s32)nval) {
            v = 0;
        }
    } else if (v < 0 || v >= (s32)nval) {
        return 0u;
    }
    u->val[i] = (u8)v;
    return 1u;
}

/* --- il tocco (v3) --------------------------------------------------------- */
/* Il menu che ospita la pagina si usa tutto con lo stilo (misurato, non dedotto:
 * `prove/tocco-vanilla-EN.png`). La pagina fa lo stesso, con le stesse regole:
 *   - toccare una voce attiva la seleziona (suono di scorrimento);
 *   - toccare la colonna dei valori la seleziona E cambia il valore, in un gesto
 *     solo, come toccare una pillola del vanilla;
 *   - una voce disattivata non risponde e non suona, esattamente come coi tasti;
 *   - la riga dei comandi e' divisa a meta': sinistra = A (salva), destra = B;
 *   - il titolo e tutto cio' che sta fuori dal pannello non sono bersagli, e un
 *     tocco a vuoto non chiude niente e non lascia la pagina in uno stato strano.
 * Ritorna sempre 1: l'evento e' della pagina, l'ospite non lo deve vedere. */
__attribute__((used, noinline, section(".text")))
static u32 opz_tocco(void *app)
{
    SgpUiState *u = SGP_UI;
    u32 x = (u32)K_TOUCH_X - G_PANNELLO_PX;
    u32 y = (u32)K_TOUCH_Y - ((u32)u->ycont << 3);
    u32 r, i, q, muovi = 0u;

    /* Un solo confronto per asse: le differenze sono senza segno, quindi un
     * tocco sopra o a sinistra del pannello diventa un numero enorme e cade
     * nello stesso ramo di uno troppo in basso o troppo a destra. */
    if (x >= G_PANNELLO_PW || y >= 192u) {
        return 1u;
    }
    /* Quale riga. 24 non e' una potenza di due: una divisione tirerebbe dentro
     * __aeabi_uidiv, che il caricatore rifiuta — e il cancello ha fermato davvero
     * questa riga due volte, prima con la divisione scritta e poi con un giro di
     * sottrazioni che LLVM ha ri-riconosciuto come divisione. Si usa la
     * reciproca esatta: 2731/65536 = 1/24 arrotondato per eccesso, corretto per
     * ogni d in [0, 191] (verificato su tutti i 192 valori dal test
     * test_tocco_riga_senza_divisione). */
    r = (y * 2731u) >> 16;
    if (r >= OPZ_RIGHE(u) || r == 0u) {
        return 1u;                      /* fuori dal pannello, o il titolo */
    }
    if (r + 1u == OPZ_RIGHE(u)) {
        if (opz_aiuto_id() != (u32)T_AIUTO_A) {
            return 1u;                  /* i comandi non sono a schermo */
        }
        opz_chiudi(x < G_PANNELLO_PW / 2u ? 1u : 0u);
        return 1u;
    }
    i = u->vis[r - 1u];
    q = V_QUALE(SGP_VOCI[i].modo);
    if (!opz_presente(q)) {
        return 1u;                      /* disattivata: niente suono, niente moto */
    }
    if ((u32)u->cursore != r - 1u) {
        u->cursore = (u8)(r - 1u);
        muovi = 1u;
    }
    if (x >= G_TOCCO_VAL - G_PANNELLO_PX && opz_cambia(0)) {
        muovi = 1u;            /* delta 0 = ciclico: il gesto sulla «pillola» */
    }
    if (muovi) {
        PlaySE(SE_SCORRI);
        opz_disegna(APP_BGCONFIG(app));
    }
    return 1u;
}

/* Un frame. Ritorna 1 se l'evento e' stato consumato dalla pagina: in quel caso
 * la trampolina esegue l'epilogo dell'ospite e il menu vanilla non vede niente.
 */
__attribute__((used, noinline, section(".text")))
u32 sgp_ui_frame(void *app)
{
    SgpUiState *u = SGP_UI;
    u32 k = K_NEW;

    if (!u->aperta) {
        if (u->app != app) {
            /* Un'altra istanza del menu Opzioni: le finestre di prima vivevano
             * su un heap che non c'e' piu'. Si abbandona lo stato SENZA liberare
             * niente di altrui (fail closed). */
            u->app = app;
            u->sugg = 0u;
            u->guard = SGP_UI_GUARD;
        }
        opz_suggerimento(app, 1u);
        if ((k & K_SELECT) && !K_TOUCH_NEW) {
            return opz_apri(app);
        }
        return 0u;
    }
    if (u->app != app) {
        u->aperta = 0u;
        u->stringa = 0;
        u->app = 0;
        u->sugg = 0u;
        return 0u;
    }

    u->eventi++;
    if (K_TOUCH_NEW) {
        return opz_tocco(app);
    }
    if (k & (K_B | K_SELECT)) {
        opz_chiudi(0u);
        return 1u;
    }
    if (k & K_A) {
        opz_chiudi(1u);
        return 1u;
    }
    if (k & K_UP) {
        opz_muovi(-1);
        PlaySE(SE_SCORRI);
    } else if (k & K_DOWN) {
        opz_muovi(1);
        PlaySE(SE_SCORRI);
    } else if (k & K_LEFT) {
        if (opz_cambia(-1)) {
            PlaySE(SE_SCORRI);
        }
    } else if (k & K_RIGHT) {
        if (opz_cambia(1)) {
            PlaySE(SE_SCORRI);
        }
    } else {
        return 1u;            /* tocco o tasto ignoto: consumato, niente ridisegno */
    }
    opz_disegna(APP_BGCONFIG(app));
    return 1u;
}

/* Trampolina del gancio A.
 *
 * Sito: `OptionsApp_HandleInput` + 4 (0x021E6820), DOPO il `push {r3,r4,r5,lr}`
 * dell'ospite (lr gia' salvato, sp ancora allineato a 8) e DOPO il
 * `ldr r1,[pc,#0x198]` che carica il letterale di gSystem — quest'ultimo e'
 * PC-relativo e NON e' rieseguibile da un'altra posizione, per questo il gancio
 * sta due byte dopo l'inizio della funzione e non all'inizio.
 *
 * Preimmagine sostituita (4 B): `04 1c 89 8c`
 *      adds r4, r0, #0        ; r4 = OptionsApp_Data*
 *      ldrh r1, [r1, #0x24]   ; r1 = gSystem.touchNew  (letterale + 0x24)
 *
 * REGISTRI VIVI AL SITO — la v1 aveva sbagliato questo conto, e il difetto e'
 * stato trovato ESEGUENDO, non leggendo. `SGP-1.2-OPZIONI-01/opzioni_pagina.c`
 * scrive: «r0 viene ricaricato dall'ospite a 0x021E682A». E' vero solo sul ramo
 * del TOCCO. L'ospite continua cosi':
 *      021E6824  cmp  r1, #0
 *      021E6826  bne  0x021E682A      ; ramo TOCCO: ricarica r0 da un letterale
 *      021E6828  b    0x021E6998      ; ramo TASTI: **NON tocca r0**
 *      ...
 *      021E69B0  bl   0x021E6624      ; OptionsApp_HandleKeyInput(r0, r1)
 * cioe' sul ramo dei tasti `r0` arriva fino alla chiamata con il valore che
 * aveva all'ingresso della funzione: il puntatore all'app. Una trampolina che
 * lascia in r0 il valore di ritorno di `sgp_ui_frame` (0 = «passa al vanilla»)
 * chiama `OptionsApp_HandleKeyInput(NULL, ...)`: eccezione dati, PC a
 * 0xFFFF0108, gioco morto. Succede al PRIMO tasto premuto nel menu Opzioni che
 * la pagina non consuma — per esempio B per uscire, che nessuna corsa della v1
 * aveva mai premuto. Misurato: fotogramma 3587 di `corse/P1-*`, identico sulla
 * ROM di prova della v1 e su quella della v2 prima di questa correzione, mentre
 * la ROM senza patch arriva viva in fondo.
 *
 * Quindi la trampolina salva e ripristina **r0, r1 e r2**, e usa r3 per il
 * ritorno. r3 e' l'unico davvero morto: l'ospite lo mette nel `push` solo per
 * allineare la pila e lo riscrive a 0x021E6830 (ramo tocco) o a 0x021E69A6
 * (ramo tasti) prima di leggerlo. r4 lo stabilisce la prima istruzione
 * sostituita e `sgp_ui_frame` lo conserva perche' e' una funzione C AAPCS — e
 * il test host lo verifica con i canarini invece di fidarsi.
 * Allineamento: al sito sp = (ingresso - 16) ≡ 0 mod 8; `push {r0,r1,r2,lr}`
 * aggiunge 16 B, quindi alla BL sp e' ancora ≡ 0 mod 8.
 * All'uscita «consumato»: si scarta il nostro frame e si esegue l'epilogo
 * dell'ospite (`pop {r3,r4,r5,pc}`), cioe' HandleInput ritorna senza fare nulla.
 */
__attribute__((naked, used, section(".text")))
void sgp_opz_hook(void)
{
    __asm__ volatile(
        "adds  r4, r0, #0\n"            /* 1a istruzione sostituita */
        "push  {r0, r1, r2, lr}\n"      /* 16 B: sp resta 0 mod 8 */
        "bl    sgp_ui_frame\n"          /* r0 = app; ritorna 0 passa / 1 consuma */
        "cmp   r0, #0\n"
        "bne   1f\n"
        "pop   {r0, r1, r2, r3}\n"      /* r0/r1/r2 come li voleva l'ospite; r3 = lr */
        "ldrh  r1, [r1, #0x24]\n"       /* 2a istruzione sostituita */
        "bx    r3\n"                    /* continua a 0x021E6824 */
        "1:\n"
        "add   sp, #16\n"               /* scarta i nostri salvataggi */
        "pop   {r3, r4, r5, pc}\n"      /* epilogo dell'ospite */
    );
}
