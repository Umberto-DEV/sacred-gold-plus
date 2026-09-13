/* Sacred Gold Plus 1.2.1 — `sgp.anim2` **v5**: contratto del blocco del moto
 * di attesa in lotta su TUTTI i lottatori e in TUTTE le fasi. GPL-3.0-or-later.
 *
 * Pacchetto SGP-1.2.1-ANIM-MOTO-01 (T1-4 + T1-5 + T1-6 del piano
 * `T-animazioni-progetto.md`, §4.1 Opzione 5, §5.7, §6.1).
 *
 * Discende da `source/features/anim/sorgenti/sgp_anim4.h` (la v4 che sta in
 * ROM nella 1.2.1, blocco `sgp.anim` 1024 B a 0x023D8B00). **La v4 non viene
 * toccata**: resta in ROM, con il suo canarino e i suoi 752 B di codice, ma
 * non è più raggiunta perché il letterale 0x0226200C punta al task v5. Il
 * blocco nuovo è `sgp.anim2`, 2048 B a **0x023DB500**, canarino 0xCA5A1800.
 *
 * ---------------------------------------------------------------------------
 * CHE COSA CAMBIA NELLA v5 — tre aggiunte, nessuna sottrazione
 * ---------------------------------------------------------------------------
 *
 * A1 — **avvio su tutti i lottatori** (Opzione 1b, T1-4). Il gioco chiama
 *      `ov12_02261FD4(od, battleSystem)` da UN solo sito, 0x0225DC8A, e solo
 *      per il lottatore del giocatore: in HGSS l'avversario non oscilla
 *      nemmeno nella 1.1. Il gancio G3 sostituisce quella `BL` con una `BL`
 *      alla nostra `sgp_avvia`, che (a) **cattura `BattleSystem*`** — è in
 *      `r1` al sito, misurato — e (b) ripete l'avvio su tutti i lottatori
 *      leggendo `BattleSystem->maxBattlers` (+0x44) e `battlers[i]` (+0x34).
 *      A interruttore spento la `BL` fa **esattamente** la chiamata che c'era
 *      prima, una sola volta e con gli stessi argomenti.
 *
 * A2 — **politica di fermata per `lr`** (Opzione 2, T1-5). `ov12_02262014`
 *      (la fermata) ha **nove** siti di chiamata, tutti noti e identici EN/IT.
 *      Il gancio G2 sta in TESTA alla funzione, dopo il `push {r4,lr}` del
 *      gioco, così `lr` del chiamante è già sulla pila e si legge da lì (una
 *      `BL` piazzata sulla PRIMA istruzione distruggerebbe proprio il
 *      discriminante). Per ciascuno dei nove siti la tabella `SGP_SITI` dice
 *      che cosa fare, e due maschere a 16 bit nei parametri lo rendono un
 *      dato e non una costante del codice:
 *        · `sopprimi` → la fermata non avviene (il task resta vivo);
 *        · `estendi`  → la fermata avviene e viene RIPETUTA su tutti gli altri
 *                       lottatori (cura dell'artefatto E3, quando serve).
 *      Il sito sconosciuto (nessuno dei nove) passa sempre: è la scelta
 *      conservativa.
 *
 * A3 — **sospensione durante la mossa** (livello 5b, T1-6), che SOSTITUISCE le
 *      fermate soppresse. A ogni esecuzione il task guarda tre cancelli:
 *        · `[[BattleSystem+0x8C] + 0x10] != 0`  — `BattleAnimSystem.moveActive`:
 *          «è in corso un'animazione di mossa». Uno per LOTTA (misurato in
 *          SGP-1.2.1-ANIM-SEGNALE-01: 11 animazioni, 0 falsi negativi, sale 3
 *          fotogrammi PRIMA del primo pixel e cade entro 1 fotogramma
 *          dall'ultimo).
 *        · `[[[BattleSystem+0x1C8]+0x00] + i*0x1D0 + 0x20] == 0` — il gestore
 *          delle animazioni per specie: 0 durante l'animazione d'INGRESSO di
 *          quel lottatore. Per LOTTATORE, e per questo la voce porta l'indice.
 *        · `[pokepic + 0x58] != 0` — `animActive`, la guardia della v4:
 *          l'interprete di `a/1/8/0` sta lavorando.
 *      Se uno qualunque è alzato: **si riporta lo sprite a riposo UNA SOLA
 *      VOLTA** (`riposo()`, gli stessi canali di `sgp_pulisci`) e poi non si
 *      scrive più niente finché tutti e tre non cadono. È il rimedio
 *      all'artefatto E4b (la fiamma di Lanciafiamme staccata dalla bocca,
 *      2 137 px su 9 216): le animazioni di `ov007` sono ancorate a coordinate
 *      fisse e non seguono `yOffset`.
 *      **Terza finestra** (§3.1 del rapporto T1-2): il lancio della Ball, dove
 *      nessuno dei due primi cancelli è alzato ma il `Pokepic` viene distrutto
 *      e ricreato. La copre la guardia già esistente sul cambio di `pic`:
 *      `slot_per()` riazzera la voce — e con essa `sospeso` — appena
 *      `od+0x20` rende un puntatore diverso.
 *
 * ---------------------------------------------------------------------------
 * CHE COSA NON CAMBIA DALLA v4
 * ---------------------------------------------------------------------------
 * A funzione spenta il task vanilla è chiamato subito e lo stato del gioco è
 * identico al byte. A funzione accesa il task vanilla precede il nostro moto
 * soltanto quando i tre cancelli sono bassi; durante una sospensione non deve
 * riscrivere `yOffset` dopo l'unico `riposo()`. L'interruttore passa da
 * `sgp_chunk_opzione()`; il divieto di scrivere `xOffset`; la finestra stretta
 * sulla scala; la tavola v3 lisciata e i parametri per classe di taglia
 * (M-MONO); il battito pseudo-casuale; lo sfasamento per slot; nessuna
 * rotazione. Un'unica unità di traduzione, nessun simbolo esterno.
 *
 * ---------------------------------------------------------------------------
 * IL GANCIO DI CODA DELLA v4 (0x02262032) VIENE **TOLTO**, non riusato
 * ---------------------------------------------------------------------------
 * La v4 puliva lo stato sporco da un gancio di 4 B sulla CODA di
 * `ov12_02262014`. La v5 ha un gancio in TESTA alla stessa funzione, che (a)
 * vede `lr`, (b) decide, e (c) può rientrare nella funzione per gli altri
 * lottatori. Tenere anche il gancio di coda significherebbe farlo scattare
 * una volta per ogni rientro, con un secondo contatore da riconciliare e una
 * seconda trampolina da mantenere, per fare una cosa che la testa fa già
 * meglio: la pulizia avviene **prima** che il gioco distrugga il task, non
 * dopo, e perciò vale anche per la fermata soppressa (dove il task non muore
 * affatto). Il sito 0x02262032 torna quindi **byte-identico al vanilla**, e
 * i byte diversi in `ov012` rispetto alla base 1.1 sono esattamente **12**:
 * G3 (avvio), G1 (letterale del task), G2 (testa della fermata).
 */
#ifndef SGP_ANIM5_H
#define SGP_ANIM5_H

#include "sgp_chunk.h"

typedef signed char s8;

/* ------------------------------------------------------------------ */
/* Indirizzi del gioco (letti dal binario, invariati EN/IT).           */
/* ------------------------------------------------------------------ */
#define SGP_POKEPIC_SETATTR 0x020087A5u /* void f(Pokepic*, int attr, int val) */
#define SGP_VANILLA_TASK 0x0226203Du    /* ov12_0226203C, idle bounce vanilla  */
#define SGP_OV12_AVVIA 0x02261FD5u      /* ov12_02261FD4(od, battleSystem)     */
#define SGP_OV12_FERMA 0x02262015u      /* ov12_02262014(od)                   */

/* `BattleSystem`, campi letti (i corpi degli accessori sono stati
 * disassemblati in SGP-1.2.1-ANIM-SEGNALE-01 §1.1, non supposti):
 *   ov12_0223A7E8  lsl r1,#2 ; add r0,r0,r1 ; ldr r0,[r0,#0x34]  -> +0x34[i]
 *   ov12_0223A7F0  ldr r0,[r0,#0x44]                             -> +0x44
 *   ov12_0223A8DC  add r0,#0x8c ; ldr r0,[r0]                    -> +0x8C
 *   ov12_0223B750  mov r1,#0x72 ; lsl r1,#2 ; ldr r0,[r0,r1]     -> +0x1C8
 * Si leggono in luogo invece di chiamare gli accessori: quattro `ldr` invece
 * di quattro `BL` dentro `ov012`, e una dipendenza in meno dall'overlay. */
#define BS_BATTLERS 0x34  /* BattlerData *battlers[4] */
#define BS_MAXBATT 0x44   /* int maxBattlers          */
#define BS_ANIMSYS 0x8C   /* BattleAnimSystem *       */
#define BS_SPECIEMGR 0x1C8 /* gestore animazioni per specie (sub_02017068)    */

/* `BattleAnimSystem` (pret/pokeplatinum, battle_anim_system.h:185-224;
 * campo per campo verificato a runtime in SGP-1.2.1-ANIM-SEGNALE-01 §1.2). */
#define AS_MOVEACTIVE 0x10

/* Gestore delle animazioni per specie (`sub_02017068`, asm/unk_02016EDC.s:259). */
#define MG_BASE 0x00  /* u32  base dell'array degli slot */
#define MG_COUNT 0x09 /* u8   numero di slot             */
#define MG_PASSO 0x1D0
#define MG_FLAG 0x20 /* 0 = animazione d'ingresso in corso */

/* Attributi di Pokepic_SetAttr (enum `PokepicAttr`). */
#define POKEPIC_XOFFSET 3      /* +0x2C — MAI scritto */
#define POKEPIC_YOFFSET 4      /* +0x2E */
#define POKEPIC_AFFINEW 12     /* +0x34 */
#define POKEPIC_AFFINEH 13     /* +0x36 */
#define POKEPIC_SHADOW_YOFF 22 /* +0x76 */
#define POKEPIC_ANIM_STEP 38   /* +0x5B */

/* OpponentData (ov012): il `data` del task. */
#define OD_POKEPIC 0x20
#define OD_TASK 0x198
#define OD_DEGREES 0x19C

/* Pokepic (ARM9, 0xAC B). */
#define PP_XOFFSET 0x2C
#define PP_YOFFSET 0x2E
#define PP_AFFINEW 0x34
#define PP_AFFINEH 0x36
#define PP_ANIMACTIVE 0x58
#define PP_ANIMSTEP 0x5B
#define PP_SHADOW_FLAGS 0x6C
#define PP_TAGLIA_SHIFT 5
#define PP_SHADOW_H 0x6E
#define PP_SHADOW_X 0x70
#define PP_SHADOW_Y 0x72
#define PP_SHADOW_XOFF 0x74
#define PP_SHADOW_YOFF 0x76

#define SGP_FASI 18
#define SGP_SCALA_UNO 0x100
#define SGP_SCALA_FINESTRA 8
#define SGP_SLOT 4

/* Bit di `flags`. Zero = comportamento 1.1 esatto. */
#define SGP_F_RESPIRO 0x01
#define SGP_F_POSA 0x02
#define SGP_F_SCALA 0x04
#define SGP_F_OMBRA 0x08
#define SGP_F_FASE 0x10
#define SGP_F_TAGLIA 0x20
#define SGP_F_TUTTI 0x3F

#define SGP_CHUNK_ANIM_ADDR (SGP_CHUNK_ADDR + SGP_C_ANIM)

/* ------------------------------------------------------------------ */
/* Pianta del blocco `sgp.anim2`, 2048 B a SGP_ANIM5_BASE.             */
/*   +0x000 codice Thumb          (max 1536 B)                         */
/*   +0x600 canarino 16 B         (0xCA5A1800|i)                       */
/*   +0x620 tab_u[18] s8          32 B                                 */
/*   +0x640 par[32]   u8          32 B                                 */
/*   +0x660 siti[9]   u32         36 B (i nove `lr`) + 28 B riempimento */
/*   +0x6A0 stato                 64 B                                 */
/*   +0x6E0 voci per lottatore    4 x 32 = 128 B                       */
/*                        fine    +0x760 (1888 B usati su 2048)        */
/* ------------------------------------------------------------------ */
#define SGP_TAB_U ((const s8 *)(SGP_ANIM5_TAB_ADDR))
#define SGP_PAR ((const u8 *)(SGP_ANIM5_PAR_ADDR))
#define SGP_SITI ((const u32 *)(SGP_ANIM5_SITI_ADDR))
#define SGP_N_SITI 9

#define PAR_AMP 0x00
#define PAR_SCA 0x04
#define PAR_FASE 0x08
#define PAR_BLINK_MIN 0x0C
#define PAR_BLINK_MASK 0x0D
#define PAR_BLINK_DUR 0x0E
#define PAR_RARO_OGNI 0x0F
#define PAR_RARO_PIU 0x10
/* v5: due maschere a 16 bit sui nove siti, bit i = SGP_SITI[i]. */
#define PAR_SOPPRIMI 0x12 /* allineato a 2: u16 LE */
#define PAR_ESTENDI 0x14  /* allineato a 2: u16 LE */
/* v5: cancelli della sospensione, un bit per cancello (per poterli spegnere
 * uno a uno nelle corse di misura, non per gusto di configurabilità). */
#define PAR_CANCELLI 0x16
#define SGP_G_MOSSA 0x01   /* moveActive            */
#define SGP_G_INGRESSO 0x02 /* gestore per specie   */
#define SGP_G_ANIMACT 0x04 /* animActive del Pokepic */
#define SGP_G_TUTTI 0x07

/* ------------------------------------------------------------------ */
/* Stato globale, 64 B. I primi 32 B sono IDENTICI alla v4: gli         */
/* strumenti di misura della v4 continuano a leggerlo senza cambiare.   */
/* ------------------------------------------------------------------ */
typedef struct SgpAnim5State {
    u8 flags;      /* +0x00 ultimo valore applicato (0 / SGP_F_TUTTI)      */
    u8 guard;      /* +0x01 0x5A quando l'iniettore l'ha inizializzato     */
    u8 ampiezza;   /* +0x02 ampiezza dichiarata dai parametri              */
    u8 rr;         /* +0x03 cursore di sfratto delle voci                  */
    u32 hits;      /* +0x04 esecuzioni del task                            */
    u32 hits_on;   /* +0x08 esecuzioni che hanno scritto                   */
    u32 hits_busy; /* +0x0C esecuzioni SOSPESE (v4: solo animActive)       */
    s16 last_y;    /* +0x10 ultimo yOffset scritto                         */
    u8 last_step;  /* +0x12 ultima posa scritta                            */
    u8 last_idx;   /* +0x13 ultima fase 0..17                              */
    u32 blinks;    /* +0x14 battiti di ciglia iniziati                     */
    u32 rari;      /* +0x18 battiti "rari" iniziati                        */
    s16 last_s76;  /* +0x1C ultimo shadow.yOffset scritto                  */
    u8 last_cls;   /* +0x1E ultima classe di taglia letta                  */
    u8 last_slot;  /* +0x1F ultimo slot usato                              */
    u32 stop_visti;/* +0x20 chiamate a ov12_02262014 intercettate          */
    u32 puliti;    /* +0x24 voci ripulite e liberate                       */
    u32 bs;        /* +0x28 v5: BattleSystem* catturato dallo stub d'avvio */
    u32 avvii;     /* +0x2C v5: avvii tentati dallo stub (tutti i lottatori)*/
    u32 soppressi; /* +0x30 v5: fermate soppresse                          */
    u32 estesi;    /* +0x34 v5: fermate ripetute su un altro lottatore     */
    u32 sospensioni;/*+0x38 v5: transizioni «in moto» -> «sospeso»         */
    u8 dentro;     /* +0x3C v5: 1 mentre siamo dentro l'estensione         */
    u8 maxbatt;    /* +0x3D v5: ultimo maxBattlers letto                   */
    u8 ultimo_sito;/* +0x3E v5: indice del sito dell'ultima fermata (0xFF = ignoto) */
    u8 cancelli;   /* +0x3F v5: quali cancelli hanno sospeso l'ultima volta */
} SgpAnim5State;   /* sizeof == 64 */

/* Una voce per lottatore, 32 B. */
typedef struct SgpAnim5Slot {
    u32 od;        /* +0x00 OpponentData* (0 = voce libera)               */
    u32 pic;       /* +0x04 Pokepic* visto l'ultima volta                 */
    u32 rng;       /* +0x08 stato dell'LCG                                */
    s16 base76;    /* +0x0C shadow.yOffset a riposo, catturato            */
    s16 last76;    /* +0x0E shadow.yOffset che abbiamo scritto noi        */
    u8 blink_left; /* +0x10 esecuzioni restanti con la posa B             */
    u8 blink_wait; /* +0x11 esecuzioni all'occhio chiuso successivo       */
    u8 blink_cnt;  /* +0x12 battiti comuni dall'ultimo raro               */
    u8 usato;      /* +0x13 1 se la voce è occupata                       */
    u8 idx;        /* +0x14 v5: indice del lottatore (0..3), 0xFF ignoto  */
    u8 sospeso;    /* +0x15 v5: 1 = già riportato a riposo, non scrivere  */
    u16 pad;       /* +0x16                                              */
    u32 coda[2];   /* +0x18 riservato                                    */
} SgpAnim5Slot;    /* sizeof == 32 */

#ifndef SGP_ANIM5_BASE
#error "SGP_ANIM5_BASE non definito"
#endif
#ifndef SGP_ANIM5_STATE_ADDR
#error "SGP_ANIM5_STATE_ADDR non definito"
#endif
#ifndef SGP_ANIM5_TAB_ADDR
#error "SGP_ANIM5_TAB_ADDR non definito"
#endif
#ifndef SGP_ANIM5_PAR_ADDR
#error "SGP_ANIM5_PAR_ADDR non definito"
#endif
#ifndef SGP_ANIM5_SITI_ADDR
#error "SGP_ANIM5_SITI_ADDR non definito"
#endif
#ifndef SGP_ANIM5_SLOT_ADDR
#error "SGP_ANIM5_SLOT_ADDR non definito"
#endif

#define SGP_STATO5 ((SgpAnim5State *)SGP_ANIM5_STATE_ADDR)
#define SGP_SLOTS ((SgpAnim5Slot *)SGP_ANIM5_SLOT_ADDR)

void sgp_idle_task5(void *task, void *data);
void sgp_stop_testa(void);
u32 sgp_stop_politica(void *data, u32 lr);
void sgp_avvia_tutti(void *data, void *bs);
void sgp_pulisci(void *data);

#endif /* SGP_ANIM5_H */
