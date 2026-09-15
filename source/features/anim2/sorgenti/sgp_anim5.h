/* Sacred Gold Plus — ANIM2 v5c, GPL-3.0-or-later.
 *
 * Moto di attesa su fino a quattro lottatori, con clock privato in ottavi
 * (0.25x / 0.375x / 0.5x), interpolazione e ripresa graduale da riposo.
 * G3 avvia gli sprite e arresta il solo bounce della barra HP. G2 conserva
 * i task nei sette siti dei menu; ogni destructor pulisce soltanto il suo
 * lottatore, senza rileggere quelli gia' liberati. G4 ferma tutti prima del
 * task nativo di cattura che riusa i Pokepic per Pokédex e soprannome.
 *
 * moveActive, ingresso specie, animActive, scala nativa e flag di ritaglio/
 * invisibilita' sospendono l'idle: un riposo, poi nessuna scrittura. Il KO
 * imposta il ritaglio PRIMA della discesa. Un tick inattivo libera la voce;
 * il riuso dello stesso indirizzo riparte con fase/ombra/inviluppo puliti.
 *
 * Opzione spenta: chiamate native con stessi argomenti e stesso ritorno.
 * Opzione accesa: niente task vanilla nel tick idle. La v4 resta nella sua
 * riserva; il suo gancio di coda torna vanilla. Blocco, canarino e indirizzi
 * dei dati restano quelli di v5b (2048 B a 0x023DB500).
 * Vedi ../AUDIT-2026-09-14.md per cause, misure, fonti e limiti.
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
#define SGP_FERMA_HUD 0x02265DA1u      /* solo bounce: conserva la freccia   */
#define SGP_CREA_TASK 0x0200E321u      /* SysTask_CreateOnMainQueue          */

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
#define OD_HPBAR 0x28
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
/* Maschera sui nove siti, bit i = SGP_SITI[i]. */
#define PAR_SOPPRIMI 0x12 /* allineato a 2: u16 LE */
#define PAR_ESTENDI 0x14  /* riservato, zero in v5c: mai estendere teardown */
/* v5: cancelli della sospensione, un bit per cancello (per poterli spegnere
 * uno a uno nelle corse di misura, non per gusto di configurabilità). */
#define PAR_CANCELLI 0x16
#define PAR_PASSO 0x17 /* fase in ottavi: 2 = 0.25x, 3 = 0.375x, 4 = 0.5x */
#define SGP_G_MOSSA 0x01   /* moveActive            */
#define SGP_G_INGRESSO 0x02 /* gestore per specie   */
#define SGP_G_ANIMACT 0x04 /* animActive del Pokepic */
#define SGP_G_TUTTI 0x07
#define SGP_G_SCALA 0x08 /* trasformazione nativa: protezione sempre attiva */

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
    u8 dentro;     /* +0x3C debug: 1 mentre G4 ferma gli altri task       */
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
    u8 fase;      /* +0x16 fase privata in ottavi, 0..143                */
    u8 inviluppo; /* +0x17 ingresso/ripresa graduale, 0..16              */
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
void *sgp_avvia_cattura(void (*fn)(void *, void *), void *data, u32 priorita);

#endif /* SGP_ANIM5_H */
