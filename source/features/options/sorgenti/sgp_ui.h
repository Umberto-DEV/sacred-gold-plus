/* Sacred Gold Plus 1.2a — interfaccia v2 (cantiere D1 fase 3, pacchetto OPZIONI-03).
 * GPL-3.0-or-later, come il progetto.
 *
 * Questa e' la SECONDA stesura. La prima (SGP-1.2-OPZIONI-01) e' stata rivista in
 * `SGP-1.2-OPZIONI-01/REVISIONE-QUALITA.md` e valutata «circa 55 %» rispetto allo
 * standard di `02-COME-LAVORARE.md` §11. Le correzioni A1-A9 di quella revisione
 * sono applicate qui; il RAPPORTO di questo pacchetto dice quali, come e con che
 * prova.
 *
 * VINCOLI DEL CARICATORE (gli stessi di D1, non negoziabili):
 *   - il payload e' UNA sola unita' di traduzione (`ui_blob.c` include gli altri);
 *   - **nessuna sezione allocata oltre `.text`**: niente `.rodata`, quindi nessun
 *     array costante nel C. I testi e le tabelle stanno a indirizzi assegnati
 *     nella riserva ARM9 e si raggiungono per valore assoluto;
 *   - nessun simbolo esterno: le funzioni del gioco si chiamano per indirizzo
 *     assoluto, col bit Thumb impostato.
 *
 * INDIRIZZI. Due blocchi, entrambi parametrici (-D da `tools/compila.py`):
 *   `sgp.opzioni`        0x023D9000, 4096 B — assegnato dall'orchestratore
 *                        (`docs/arm9-reserve-reservations.md`, fonte unica).
 *                        Ci stanno codice, risorse, tabella, template, stato e
 *                        canarino: 3412 + 84 + 24 + 32 + 76 + 16 = 3644 su 4096.
 *   `sgp.opzioni.testi`  0x023DA800, 1024 B — **da ratificare**. Il blob dei
 *                        testi della lingua della ROM e' 946 B (IT) e non entra
 *                        nei 4096 insieme al codice. 0x023DA800 e' il primo
 *                        indirizzo libero dopo `sgp.wifi` (0x023DA000 + 0x800):
 *                        non sposta nessun blocco di nessun altro. Il conto e le
 *                        alternative sono in PIANO-INIEZIONE.md §1.
 */
#ifndef SGP_UI_H
#define SGP_UI_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;

/* --- indirizzi parametrici: il blocco sgp.opzioni -------------------------- */
#ifndef SGP_UI_ADDR
#define SGP_UI_ADDR 0x023D9000u          /* +0x000   codice Thumb, 3584 B */
#endif
#ifndef SGP_UI_TESTI_ADDR
#define SGP_UI_TESTI_ADDR 0x023D9E00u    /* +0xE00   blob dei testi, 1024 B */
#endif
#ifndef SGP_UI_RIS_ADDR
#define SGP_UI_RIS_ADDR 0x023D9E00u      /* +0xE00   banchi/modi/BgTemplate da ov054, 96 B */
#endif
#ifndef SGP_UI_TAB_ADDR
#define SGP_UI_TAB_ADDR 0x023D9E60u      /* +0xE60   tabella delle voci, 64 B */
#endif
#ifndef SGP_UI_TPL_ADDR
#define SGP_UI_TPL_ADDR 0x023D9EA0u      /* +0xEA0   due OverlayManagerTemplate, 32 B */
#endif
#ifndef SGP_UI_STATO_ADDR
#define SGP_UI_STATO_ADDR 0x023D9EC0u    /* +0xEC0   stato dell'interfaccia, 96 B */
#endif

/* --- indirizzi parametrici: gli stati DEGLI ALTRI cantieri ----------------- */
/* La pagina e' un CONSUMATORE: non possiede nessuno di questi byte. Ogni voce
 * legge la guardia del proprio proprietario e, se il proprietario non c'e',
 * non tocca un byte. Fonti:
 *   D1   `SGP-1.2-PLUS-01/CONTRATTO-D1.md` §2.2 — stato a blocco sgp.plus +0x600
 *   P2   `SGP-1.2-PRESTAZIONI-NPC-01/CONTRATTO-P2.md` §3 + NPC-02 (`0x023D89E0`)
 *   A1-B `SGP-1.2-ANIM-B-01/CONTRATTO-A1B.md` §4.1 + PIANO-INIEZIONE (stato a +0x340)
 *   W1   `SGP-1.2-WIFI-01/CONTRATTO-W1.md` §4.2 e §1b.4: `SgpW1Stato`, 16 B a
 *        **0x023DA240**, indirizzo che il contratto dichiara **fermo** proprio
 *        perche' e' questa pagina a leggerlo e scriverlo. La guardia di presenza
 *        e' il `magic` = 'W' (0x57): senza, il blob W1 e' inerte e la voce si
 *        disegna disattivata su «Originale», come chiede l'orchestratore.
 */
#ifndef SGP_STATO_D1_ADDR
#define SGP_STATO_D1_ADDR 0x023D8700u    /* sgp.plus 0x023D8100 + 0x600 */
#endif
#ifndef SGP_STATO_NPC_ADDR
#define SGP_STATO_NPC_ADDR 0x023D89E0u   /* sgp.npc 0x023D8900 + 0xE0 */
#endif
#ifndef SGP_STATO_ANIM_ADDR
#define SGP_STATO_ANIM_ADDR 0x023D8E40u  /* sgp.anim 0x023D8B00 + 0x340 */
#endif
#ifndef SGP_STATO_WIFI_ADDR
#define SGP_STATO_WIFI_ADDR 0x023DA240u  /* SgpW1Stato, CONTRATTO-W1 §4.2/§1b.4 */
#endif

/* Template dell'applicazione che il nostro Exit deve registrare al posto proprio:
 * sono i due valori ORIGINALI delle parole che il gancio B riscrive, letti dal
 * binario (prove/ancore.json → B_parole). */
#ifndef SGP_TPL_CONTINUA_SUCC
#define SGP_TPL_CONTINUA_SUCC 0x020FA16Cu   /* gApplication_ContinueFieldsys */
#endif
#ifndef SGP_TPL_NUOVA_SUCC
#define SGP_TPL_NUOVA_SUCC 0x020FA15Cu      /* gApplication_NewGameFieldsys */
#endif

/* --- il chunk di salvataggio 1.2, letto e scritto da questa interfaccia ----- */
/* `SGP-1.2-PLUS-03/CONTRATTO-CHUNK.md` §1-§2. La pagina NON tiene copie locali
 * delle opzioni: tocca **questi** byte, e al prossimo salvataggio del giocatore
 * li porta su flash il gancio S0 di PLUS-03. Ogni interruttore e' UN byte, non un
 * bit: due cantieri che scrivono due campi diversi non si corrompono a vicenda.
 *
 *   0x023D8700  active_plus   copia operativa di `plus` (la legge il gancio allenatori)
 *   0x023D8701  active_wild   copia operativa di `selvatici`
 *   0x023D8703  load_status   0 mai · 1 assente · 2 valido · 3 rifiutato
 *   0x023D8704  guard         0x5A quando la lettura all'avvio e' passata
 *   0x023D8710  magic u16 'SG' · +0x2 versione · +0x3 plus · +0x4 selvatici
 *               +0x5 oltre100 · +0x6 anim · +0x7 npc · +0x8 wifi_server · +0x9 picco
 *
 * Il contratto dice: «chi accende `plus` o `selvatici` deve aggiornare anche
 * `active_plus` / `active_wild`». Lo fa `opz_scrivi`. */
#define SGP_D1_ACTIVE_PLUS (*(volatile u8 *)(SGP_STATO_D1_ADDR + 0x00u))
#define SGP_D1_ACTIVE_WILD (*(volatile u8 *)(SGP_STATO_D1_ADDR + 0x01u))
#define SGP_D1_LOAD        (*(volatile u8 *)(SGP_STATO_D1_ADDR + 0x03u))
#define SGP_D1_GUARDIA     (*(volatile u8 *)(SGP_STATO_D1_ADDR + 0x04u))
#define SGP_CHUNK          ((volatile u8 *)(SGP_STATO_D1_ADDR + 0x10u))
#define C_VERSIONE  0x02u
#define C_PLUS      0x03u
#define C_SELVATICI 0x04u
#define C_OLTRE100  0x05u
#define C_ANIM      0x06u
#define C_NPC       0x07u
#define C_WIFI      0x08u
#define C_PICCO     0x09u
#define SGP_D1_GUARD  0x5Au
#define SGP_LOAD_MAI    0u
#define SGP_LOAD_ABSENT 1u
#define SGP_LOAD_VALID  2u
#define SGP_LOAD_REJECT 3u

/* Gli stati altrui, visti come byte. Nessuna struttura: solo i campi che servono,
 * agli offset che i rispettivi contratti dichiarano.
 * `SgpW1Stato` (CONTRATTO-W1 §4.2): magic +0x00, versione +0x01, modo +0x02,
 * slot_gts +0x03, slot_dono +0x04, flag +0x05. Lo slot 1 e' del Dono Segreto e
 * si sceglie da solo: la pagina mostra e scrive **solo** gli slot 2 e 3, piu'
 * «Originale» che spegne il modo. */
/* Di questi blocchi la pagina legge SOLO la guardia, per sapere se il
 * proprietario e' nella ROM: i VALORI stanno tutti nel chunk pubblico, e sono i
 * blocchi stessi a leggerli da li' (CONTRATTO-CHUNK §2). Una voce il cui
 * proprietario manca si vede disattivata (o non si vede affatto) invece di
 * lasciare accendere qualcosa che nessuno applica. */
#define SGP_NPC_GUARD   (*(volatile u8 *)(SGP_STATO_NPC_ADDR + 2u))
#define SGP_ANIM_GUARD  (*(volatile u8 *)(SGP_STATO_ANIM_ADDR + 1u))
#define SGP_W1_MAGIC    (*(volatile u8 *)(SGP_STATO_WIFI_ADDR + 0u))
#define SGP_W1_MAGIC_OK 0x57u          /* 'W', CONTRATTO-W1 §4.2 */

/* --- funzioni del gioco (ARM9, Thumb: bit 0 impostato) --------------------- */
/* Tutte risolte da `prove/simboli-arm9.json`, con preimmagine e sha256 letti da
 * entrambe le ROM. Nessun indirizzo e' stato dedotto dal nome. */
#define FN(t, a) ((t)((a) | 1u))

typedef struct Window {                       /* bg_window.h:68-79 — 16 B */
    void *bgConfig; u8 bgId, x, y, w, h, pal; u16 baseTile; void *pixels;
} Window;

typedef struct String {                       /* pm_string.h:9-14 */
    u16 maxsize; u16 size; u32 magic; u16 data[1];
} String;

#define AddWindowParameterized \
    FN(void (*)(void *, Window *, u32, u32, u32, u32, u32, u32, u32), 0x0201D40Cu)
#define RemoveWindow                 FN(void (*)(Window *), 0x0201D520u)
#define CopyWindowToVram             FN(void (*)(Window *), 0x0201D578u)
#define ClearWindowTilemapAndCopyToVram FN(void (*)(Window *), 0x0201D8C8u)
#define FillWindowPixelBuffer        FN(void (*)(Window *, u32), 0x0201D978u)
#define AddTextPrinterWithColor \
    FN(u32 (*)(Window *, u32, String *, u32, u32, u32, u32, void *), 0x020200FCu)
#define FontID_String_GetWidth       FN(u32 (*)(u32, String *, u32), 0x02002F30u)
#define String_New                   FN(String *(*)(u32, u32), 0x02026354u)
#define String_Delete                FN(void (*)(String *), 0x02026380u)
#define ToggleBgLayer                FN(void (*)(u32, u32), 0x0201BC28u)
#define Heap_Destroy                 FN(void (*)(u32), 0x0201A9C4u)
#define RegisterMainOverlay          FN(void (*)(u32, const void *), 0x02000EF4u)
#define PlaySE                       FN(void (*)(u32), 0x0200604Cu)

/* FillBgTilemapRect — la funzione con cui il gioco stesso disegna la CORNICE
 * (`0x0200E8A0` la chiama cinque volte con i tile della cornice). Verificata in
 * questo pacchetto disassemblando quel sito: r0=bgConfig, r1=bgId, r2=valore,
 * r3=x, pila: y, w, h, palette. E' la primitiva del «tile bianco condiviso»:
 * un solo tile riempie tutte le celle fra una riga e l'altra. */
#define FillBgTilemapRect \
    FN(void (*)(void *, u32, u32, u32, u32, u32, u32, u32), 0x0201C8C4u)

/* funzioni interne dell'overlay 54 (app Opzioni) */
#define OPZ_EVIDENZIA   FN(void (*)(void *, u32), 0x021E69D4u)

/* Cornice della finestra: la STESSA dell'app Opzioni, disegnata con le stesse due
 * funzioni e con il numero di cornice che il giocatore ha scelto nelle Opzioni
 * (campo `frame` del bitfield a OptionsApp_Data+0x18). Zero asset nuovi.
 * Le due funzioni leggono dalla `Window` SOLO bgConfig/bgId/x/y/w/h (verificato
 * disassemblando 0x0200E948 e i cinque accessori 0x0201EE8C…9C): la cornice si
 * puo' quindi disegnare intorno a un rettangolo che non e' una finestra vera. */
#define LoadUserFrameGfx2 \
    FN(void (*)(void *, u32, u32, u32, u32, u32), 0x0200E644u)
#define DrawFrameAndWindow2  FN(void (*)(Window *, u32, u32, u32), 0x0200E998u)
#define ClearFrameAndWindow2 FN(void (*)(Window *, u32), 0x0200E9BCu)
#define G_CORNICE_TILE 0x3DCu   /* 988: gli ultimi 36 tile rappresentabili */
#define G_CORNICE_PAL    15u    /* slot 15 del BG principale: non usato dal vanilla */

/* Suoni dell'app Opzioni, letti dai suoi pool letterali (0x021E6814/0x021E6818)
 * e dal ramo di annullamento (0x25 << 6). Non se ne inventano di nuovi. */
#define SE_SCORRI  1500u        /* cursore e cambio valore */
#define SE_SALVA   1562u        /* A: conferma */
#define SE_ANNULLA 2368u        /* B / SELECT: annulla */

/* --- testo ---------------------------------------------------------------- */
#define SGP_EOS 0xFFFFu
#define SGP_TESTI ((const u16 *)SGP_UI_TESTI_ADDR)

/* id nel blob dei testi — l'ordine e' fissato da tools/costruisci_testi.py e il
 * test `test_testi.py` confronta le due liste. Rispetto alla v1 sono SPARITI
 * `p_salvato`, `p_aiuto2`, `p_pagina1`, `p_pagina2`, `c_aiuto2` e i sei
 * indicatori `n/6`: erano testo morto o servivano allo scorrimento, che non
 * esiste piu' (REVISIONE-QUALITA A5). */
enum {
    T_TITOLO = 0, T_AIUTO_A, T_AIUTO_B, T_BLOCCATO, T_RIFIUTATO, T_SUGGERIMENTO,
    T_NOME0, T_NOME1, T_NOME2, T_NOME3, T_NOME4,
    T_X_OFF, T_X_ON, T_X_NORMALE, T_X_PLUS, T_N_NORM, T_N_FLUIDO,
    T_W0, T_W1, T_W2,
    T_C_TITOLO, T_C_RIGA1, T_C_RIGA2, T_C_RIGA1N, T_C_RIGA2N, T_C_NOTA, T_C_AIUTO,
    T_CURSORE, T_VUOTO,
    T_COUNT
};

/* --- tabella delle voci, 6 voci x 4 byte, a SGP_UI_TAB_ADDR ---------------- */
/* `modo`: bit0-3 = quale stato la voce comanda; bit4 = 1 se, mancando il
 * proprietario, la voce si NASCONDE invece di restare disattivata. */
typedef struct SgpVoce { u8 nome; u8 val0; u8 nval; u8 modo; } SgpVoce;
#define SGP_VOCI  ((const SgpVoce *)SGP_UI_TAB_ADDR)
#define SGP_MAX_VOCI 6u          /* capienza della tabella e del layout */
#define SGP_N_VOCI 5u            /* voci dichiarate dalla 1.2a */

#define V_QUALE(m) ((m) & 0x0Fu)
#define V_NASCONDI(m) (((m) >> 4) & 1u)
#define Q_D1_PLUS 0u
#define Q_D1_WILD 1u
#define Q_ANIM    2u
#define Q_NPC     3u
#define Q_WIFI    4u

/* --- geometria v2 --------------------------------------------------------- */
/* IL VINCOLO: la cella di una tilemap di testo ha **10 bit** di indice di
 * carattere, quindi nessun tile oltre 1023. Le 5 finestre vanilla arrivano a
 * 0x274 = 628, la cornice ne prende 36: restano **360 tile** per la pagina.
 * E' un'AREA, non una forma (REVISIONE-QUALITA §2). La v1 spendeva tutti e 360 i
 * tile in una sola finestra 30x12 e otteneva TRE voci visibili su sei, con passo
 * 20 px invece dei 24 px del gioco.
 *
 * La v2 usa la forma con piu' righe: **una finestra sottile (2 tile) per riga**,
 * piu' **un tile bianco condiviso** che riempie le celle fra una riga e l'altra
 * con `FillBgTilemapRect`. Conto, per costruzione (il cancello G7 lo rifa'):
 *     7 righe x 24 tile x 2 = 336   (titolo + 5 voci + aiuto)
 *   +   1 tile bianco       =   1
 *   +  36 cornice           =  36
 *                             ---
 *                             373  <=  396 disponibili, 23 di margine.
 * Passo verticale 24 px, cioe' quello del menu che la pagina imita. Nessuno
 * scorrimento: tutte le voci sono a schermo insieme. */
#define G_W_TILE     24u      /* larghezza di ogni riga, in tile (192 px) */
#define G_H_TILE      2u      /* altezza di ogni riga, in tile (16 px) */
#define G_RIGHE_MAX   7u      /* titolo + 5 voci + aiuto */
#define G_PASSO_TILE  3u      /* 24 px: il passo del menu Opzioni vanilla */
#define G_PANNELLO_X  4u      /* colonna del contenuto (la cornice sta a 3 e 28) */
#define G_PANNELLO_Y  2u      /* riga del contenuto (la cornice sta a 1 e 22) */
#define G_PANNELLO_H 20u      /* tile: 2 titolo + 1 + (5x3 - 1) + 1 + 2 = 20 */

#define G_BASETILE 0x274u     /* libero: le 5 finestre vanilla finiscono a 0x274 */
#define G_TILE_RIGA  (G_W_TILE * G_H_TILE)              /* 48 */
#define G_TILE_BIANCO (G_BASETILE + G_RIGHE_MAX * G_TILE_RIGA)   /* 0x3C4 */
#define G_TILE_FINE   (G_TILE_BIANCO + 1u)              /* 0x3C5 <= 0x3DC */
#define G_TILE_MAX 1024u      /* 10 bit di indice nella cella della tilemap */

/* Il suggerimento nel menu Opzioni vanilla (REVISIONE-QUALITA §6, proposta 3,
 * resa gratuita): vive nella banda libera in basso a sinistra (x 0..116, y
 * 172..191 — misurato sui fotogrammi vanilla EN e IT), e **non coesiste mai**
 * con la pagina, quindi riusa gli stessi tile. Costo netto: zero tile. */
#define G_SUGG_X     0u
#define G_SUGG_Y    22u
#define G_SUGG_W    14u       /* 112 px: i pulsanti OK/CHIUDI cominciano a 117 */
#define G_SUGG_H     2u
#define G_SUGG_TX    2u

/* coordinate del testo DENTRO una riga (finestra 192x16) */
#define G_X_CURSORE   4u
#define G_X_NOME     20u      /* A8: titolo, voci, aiuto e valore hanno lo STESSO
                               * margine sinistro; solo il cursore sporge */
#define G_X_VAL_DX  186u      /* i valori sono allineati a destra su questo bordo */
#define G_NOME_MAX  114u      /* etichetta: limite misurato, vedi prove/testi.json */
#define G_VAL_MAX    44u
#define G_RIGA_MAX  166u

/* --- bersagli del tocco (v3) ---------------------------------------------- */
/* Il menu Opzioni vanilla e' INTERAMENTE usabile con lo stilo: misurato in questo
 * cantiere toccando la pillola «Off» di «Battle Scene» sulla ROM base-1.1 e
 * osservando il riquadro rosso spostarsi (prove/tocco-vanilla-EN.png). La pagina
 * deve esserlo altrettanto, o non e' un'app del 2009.
 *   - il pannello occupa in pixel [G_PANNELLO_PX, G_PANNELLO_PX + G_PANNELLO_PW);
 *   - ogni riga occupa una banda alta G_PASSO_TILE*8 = 24 px, la stessa del menu;
 *   - dentro una voce, la META' DESTRA e' la colonna dei valori: toccarla cambia
 *     il valore (come toccare una pillola), toccare la meta' sinistra seleziona;
 *   - la riga di aiuto porta i due comandi nelle stesse due colonne delle voci
 *     (A a sinistra, B a destra): la meta' del pannello e' la linea di confine.
 */
#define G_PANNELLO_PX (G_PANNELLO_X * 8u)          /* 32  */
#define G_PANNELLO_PW (G_W_TILE * 8u)              /* 192 */
#define G_PASSO_PX    (G_PASSO_TILE * 8u)          /* 24  */
#define G_TOCCO_META  (G_PANNELLO_PX + G_PANNELLO_PW / 2u)   /* 128 */
#define G_TOCCO_VAL   (G_PANNELLO_PX + 132u)       /* 164: i valori finiscono a 218 */

#define G_PALETTE    13u
#define G_FONT        0u
#define G_ISTANTANEO  0xFFu   /* TEXT_SPEED_NOTRANSFER: niente copia per riga */
#define G_BG_MAIN2    2u      /* sfondo del menu: si SPEGNE mentre la pagina e' aperta */
#define G_BG_MAIN1    1u
#define G_BG_MAIN0    0u

/* Colori. Solo indici certi della palette 13 caricata da LoadFontPal0:
 * 1 = testo scuro, 2 = ombra, 15 = fondo. Niente indici inventati. */
#define G_RIEMPIMENTO     0xFFu                        /* colore 15 nei due nibble */
#define G_RIEMPIMENTO_SEL 0x11u                        /* colore 1 nei due nibble */
#define G_COLORE     ((1u << 16) | (2u << 8) | 15u)    /* normale */
#define G_COLORE_SEL ((15u << 16) | (2u << 8) | 1u)    /* riga selezionata: barra piena */
#define G_COLORE_OFF ((2u << 16) | (15u << 8) | 15u)   /* voce disattivata: grigia */

/* --- tasti ---------------------------------------------------------------- */
#define SYS ((volatile u8 *)0x021D110Cu)
#define K_NEW (*(volatile u32 *)(SYS + 0x48))
#define K_TOUCH_NEW (*(volatile u16 *)(SYS + 0x64))
/* v3: le coordinate del pennino. `struct System` (pokeheartgold, include/system.h)
 * mette touchX a +0x60, touchY a +0x62 e touchNew a +0x64: l'offset di touchNew
 * era gia' usato e verificato dalla v2, quindi gli altri due sono nella stessa
 * struttura e alla stessa base. MISURATI a runtime in questo cantiere
 * (prove/tocco-coordinate.json) prima di essere usati. */
#define K_TOUCH_X (*(volatile u16 *)(SYS + 0x60))
#define K_TOUCH_Y (*(volatile u16 *)(SYS + 0x62))
#define K_A 0x001u
#define K_B 0x002u
#define K_SELECT 0x004u
#define K_RIGHT 0x010u
#define K_LEFT 0x020u
#define K_UP 0x040u
#define K_DOWN 0x080u

/* --- stato dell'interfaccia, 208 B a SGP_UI_STATO_ADDR --------------------- */
#define SGP_UI_GUARD 0x55u
typedef struct SgpUiState {
    u8  aperta;        /* +0x00 1 = la pagina e' a schermo */
    u8  cursore;       /* +0x01 voce selezionata, indice nelle voci VISIBILI */
    u8  n_vis;         /* +0x02 quante voci sono visibili adesso */
    u8  guard;         /* +0x03 SGP_UI_GUARD */
    u8  vis[SGP_MAX_VOCI];  /* +0x04 indice reale di ogni voce visibile */
    u8  val[SGP_MAX_VOCI];  /* +0x0A valore in corso di modifica, per voce reale */
    u8  val0[SGP_MAX_VOCI]; /* +0x10 valore all'apertura, per annullare con B */
    u8  sugg;          /* +0x16 1 = il suggerimento e' disegnato */
    u8  ycont;         /* +0x17 geometria calcolata UNA volta in opz_visibili: */
    u8  altezza;       /*       riga e altezza del contenuto, in tile, e quante */
    u8  n_righe;       /*       righe ci sono. Ricalcolarle a ogni uso costava */
    u16 pad0;          /*       un chilobyte di codice. */
    u32 aperture;      /* +0x1C diagnostica: quante volte SELECT ha aperto */
    u32 eventi;        /* +0x20 diagnostica: tasti consumati dalla pagina */
    u32 salvataggi;    /* +0x24 diagnostica: quante volte A ha confermato */
    u32 esito;         /* +0x28 schermata Continua: vedi continua_domanda.c */
    void *app;         /* +0x2C OptionsApp_Data* proprietaria */
    String *stringa;   /* +0x30 buffer riusato per la stampa */
    void *bg_cont;     /* +0x34 BgConfig* della schermata al Continua */
    u32 pad1;          /* +0x38 */
    Window finestra;   /* +0x3C l'UNICA finestra viva: quella della schermata al
                        *       Continua, che deve sopravvivere fra un fotogramma
                        *       e l'altro. Le righe della pagina no: si creano, si
                        *       disegnano, si copiano in VRAM e si chiudono subito
                        *       (il trasferimento e' sincrono — 0x0201D7F4 alloca
                        *       un buffer temporaneo, scrive e lo libera dentro la
                        *       chiamata), e la tilemap tiene il disegno. Sette
                        *       `Window` vive sarebbero 112 B di stato e un
                        *       centinaio di byte di codice in uno scomparto dove
                        *       ogni byte e' contato. */
} SgpUiState;                                  /* 76 B su 96 */

#define SGP_UI ((SgpUiState *)SGP_UI_STATO_ADDR)
#define SGP_CONT_FIN (&SGP_UI->finestra)

/* --- interfaccia ---------------------------------------------------------- */
u32 sgp_ui_frame(void *app);
void sgp_opz_hook(void);

#endif /* SGP_UI_H */
