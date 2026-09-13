/* Sacred Gold Plus 1.2 — `sgp.caramelle`: indirizzi, offset e costanti.
 * GPL-3.0-or-later.
 *
 * OGNI numero qui sotto è stato letto dai byte delle ROM di lavoro (Sacred
 * Gold Plus 1.2, EN e IT) e confrontato con il decomp `pret/pokeheartgold`
 * commit 0985e87. Gli indirizzi ARM9 statici sono **identici** nelle due
 * lingue: dimostrato confrontando gli sha256 dei byte di ciascuna funzione
 * nominata, su quattro ROM (1.1 EN/IT e 1.2 EN/IT).
 *
 * Niente è parametrico via -D tranne l'indirizzo di base del blocco: i cinque
 * indirizzi nativi stanno nell'ARM9 statico, che non si sposta.
 */
#ifndef SGP_CARAMELLE_H
#define SGP_CARAMELLE_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

/* --------------------------------------------------------------- nativi ---
 * Bit 0 acceso = Thumb. Sono gli stessi cinque letterali che la 1.1 tiene in
 * coda a `borsa.text` (0x023DFD94, 0x023DFD98, 0x023DFD9C, 0x023DFDB8,
 * 0x023DFDBC, 0x023DFDC0): li ripetiamo qui invece di leggerli da lì, perché
 * `borsa.text` è congelato e non vogliamo dipenderne.
 */

/* Bag_GetItemQuantity(Bag*, u16 itemId, u32 heapId) -> u16   (0x02078550) */
#define SGP_CAR_BAG_QUANTITY   0x02078551u
/* Party_GetCount(Party*) -> u32   : `ldr r0,[r0] ; bx lr`    (0x0207463C) */
#define SGP_CAR_PARTY_COUNT    0x0207463Du
/* Party_GetCapacity(Party*) -> u32: `ldr r0,[r0,#4] ; bx lr` (0x02074640) */
#define SGP_CAR_PARTY_CAPACITY 0x02074641u
/* ClearFrameAndWindow2(Window*, BOOL)                        (0x0200E9BC) */
#define SGP_CAR_CLEAR_WINDOW   0x0200E9BDu
/* PartyMenu_PrintMessageOnWindow32(PartyMenu*, int msgId, BOOL) (0x0207DAC4) */
#define SGP_CAR_PRINT_WIN32    0x0207DAC5u
/* thunk_Sprite_SetPaletteOverride(Sprite*, int)              (0x0200DD08) */
#define SGP_CAR_SPRITE_PALETTE 0x0200DD09u

/* ------------------------------------------------------------- PartyMenu ---
 * pret `include/party_menu.h`, struct PartyMenu. Window = 16 B, quindi
 * windows[34] = 0x004 + 34*16 = 0x224 — e infatti il gioco stesso calcola
 * quell'indirizzo come `movs r0,#0x89 ; lsls r0,#2 ; adds r0,r4,r0`
 * (0x0207C8C6 e 0x023DFC9E). sprites[6] = 0x660 + 24 = 0x678, e il gioco lo
 * calcola come `movs r0,#0xcf ; lsls r0,#3` (0x023DFCB8) o come letterale
 * 0x00000678 (0x0207C904).
 */
#define SGP_CAR_PM_ARGS        0x654u   /* PartyMenuArgs*                    */
#define SGP_CAR_PM_WINDOW34    0x224u   /* &windows[34]                      */
#define SGP_CAR_PM_SPR_CURSOR  0x678u   /* sprites[PARTY_MENU_SPRITE_ID_CURSOR] */
#define SGP_CAR_PM_SLOT        0xC65u   /* partyMonIndex (u8)                */

/* --------------------------------------------------------- PartyMenuArgs ---
 * pret `include/party_menu.h`, struct PartyMenuArgs. Confermati sui byte:
 * itemId a +0x28 (`ldrh r0,[r0,#0x28]` a 0x020812F0), context a +0x24
 * (`adds r0,#0x24 ; ldrb r2,[r0]` a 0x02078F10), selectedAction a +0x27
 * (`adds r1,#0x27 ; strb r0,[r1]` a 0x02081EA0), species a +0x3C
 * (`strh r0,[r2,#0x3c]` a 0x02081E90).
 */
#define SGP_CAR_ARG_PARTY      0x00u   /* Party*                             */
#define SGP_CAR_ARG_BAG        0x04u   /* Bag*                               */
#define SGP_CAR_ARG_CONTEXT    0x24u   /* u8  PartyMenuContext               */
#define SGP_CAR_ARG_ACTION     0x27u   /* u8  selectedAction                 */
#define SGP_CAR_ARG_ITEMID     0x28u   /* u16 itemId                         */
#define SGP_CAR_ARG_SEARCH     0x38u   /* int levelUpMoveSearchState         */

/* ------------------------------------------------------------- costanti --- */
#define SGP_CAR_CTX_USE_ITEM   5u      /* PARTY_MENU_CONTEXT_USE_ITEM        */
#define SGP_CAR_HEAP_PARTY     12u     /* HEAP_ID_PARTY_MENU, come al sito
                                        * 0x0207C346 (`movs r3,#0xc`)        */
#define SGP_CAR_MSG_WHICH_MON  33u     /* msg_0300_00033, «Su quale Pokémon
                                        * usarlo?»: il gioco lo stampa per i
                                        * context 5 e 0x10 a 0x02078F28      */

/* --------------------------------------------------------------- stati ---
 * pret `include/party_menu.h`, enum PartyMenuState.
 */
#define SGP_CAR_STATE_SELECT_MON 4u    /* PARTY_MENU_STATE_USE_ITEM_SELECT_MON */
#define SGP_CAR_STATE_EXIT      0x20u  /* PARTY_MENU_STATE_BEGIN_EXIT        */

/* -------------------------------------------------------------- azioni --- */
#define SGP_CAR_ACTION_0        0u     /* PARTY_MENU_ACTION_RETURN_0         */
#define SGP_CAR_ACTION_EVO      9u     /* ..._RETURN_EVO_RARE_CANDY          */

#endif /* SGP_CARAMELLE_H */
