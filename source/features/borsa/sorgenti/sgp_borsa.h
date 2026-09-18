/* Sacred Gold Plus 1.2.1 — `sgp.borsa`: indirizzi, offset e costanti.
 * SGP-1.2-BORSA-GEN-03. GPL-3.0-or-later.
 *
 * Gli indirizzi sono le pre/post-condizioni minime verificate sulle due
 * lingue e confrontate con pret/pokeheartgold commit 0985e87.
 *
 * Nulla e' parametrico tranne `SGP_BORSA_BASE`, che `tools/compila_borsa.py`
 * passa con -D perche' compaia nel comando registrato nel manifesto.
 */
#ifndef SGP_BORSA_H
#define SGP_BORSA_H

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int BOOL;

/* ================================================================= blocco ===
 * Riserva ARM9, zona 1.2, subito dopo `sgp.caramelle` (0x023DAC00+0x100).
 * `source/docs/arm9-reserve-map.json` assegna questo intervallo a `sgp.borsa`.
 *
 * 2048 B, non 1024. U §4.4 stimava 1024 «da un conteggio di istruzioni, non da
 * un assemblato» (U §7, che lo dichiara). L'assemblato misura **658 B** di
 * codice; con 480 B di tabella, 16 B di canarino e 32 B fra staffetta e
 * puntatori agli originali il totale e' 1186 B, che in 1024 non entra.
 * La riserva successiva inizia a 0x023DBD00, dopo `sgp.anim2`.
 *
 *   +0x000  sgp_borsa_cmd127   trampolino, 8 B   <- gScriptCmdTable[127]
 *   +0x008  sgp_borsa_cmd125   trampolino, 8 B   <- gScriptCmdTable[125]
 *   +0x010  corpo C                              fino a +0x5DF (1504 B in tutto)
 *   +0x5E0  originale 127 (u32)  |  +0x5E4 originale 125 (u32)  | 8 B a zero
 *   +0x5F0  staffetta (armata, item, chieste, entrate) + 8 B a zero
 *   +0x600  tabella permissiva: 120 voci u32 = 480 B
 *   +0x7E0  16 B a zero
 *   +0x7F0  canarino 0xCA5A1700|i, i = 0..3
 */
#ifndef SGP_BORSA_BASE
#define SGP_BORSA_BASE          0x023DAD00u
#endif

#define SGP_BORSA_MAX_CODICE    0x5E0u
#define SGP_BORSA_ORIG127_ADDR  (SGP_BORSA_BASE + 0x5E0u)
#define SGP_BORSA_ORIG125_ADDR  (SGP_BORSA_BASE + 0x5E4u)
#define SGP_BORSA_STAFFETTA     (SGP_BORSA_BASE + 0x5F0u)
#define SGP_BORSA_TAB_ADDR      (SGP_BORSA_BASE + 0x600u)
#define SGP_BORSA_TAB_N         120u
#define SGP_BORSA_CANARINO      (SGP_BORSA_BASE + 0x7F0u)

/* Campi della staffetta, relativi a SGP_BORSA_STAFFETTA. Tutti u16. */
#define SGP_ST_ARMATA           0x0u
#define SGP_ST_ITEM             0x2u
#define SGP_ST_CHIESTE          0x4u
#define SGP_ST_ENTRATE          0x6u

/* ================================================================= nativi ===
 * Bit 0 acceso = Thumb.
 *
 * I due originali. Sono i valori che gScriptCmdTable[125] e [127] portano
 * nelle ROM 1.2.1 EN e IT (letti: 0x020FAD00 + 4*125 e + 4*127). Servono solo
 * come RIPIEGO: il codice chiama l'originale attraverso il puntatore che
 * l'applicatore salva nel blocco, e usa questi letterali solo se quel
 * puntatore e' ancora zero (blocco non riempito).
 */
#define SGP_BORSA_VAN127        0x0204EA89u  /* ScrCmd_HasSpaceForItem */
#define SGP_BORSA_VAN125        0x0204E9D9u  /* ScrCmd_GiveItem        */

/* ScriptReadHalfword(ScriptContext*) -> u16, avanza script_ptr di 2.
 * 0x0203FE2C: `ldr r1,[r0,#8] ... ldrb/ldrb ... str r1,[r0,#8]` — letta. */
#define SGP_BORSA_READ_HW       0x0203FE2Du
/* GetVarPointer(FieldSystem*, u16 varId) -> u16*   (0x02040374)
 * < 0x4000 -> NULL (letterale); 0x4000..0x7FFF -> variabile di salvataggio;
 * >= 0x8000 -> FieldSysGetAttrAddr(fs, varId - 0x7FD6). Il letterale 0x7FD6
 * sta a 0x020403A8: letto. Quindi x800A -> campo 0x34, ed e' questa la via
 * con cui il C scrive una VAR speciale: la stessa che usa il gioco. */
#define SGP_BORSA_GET_VAR_PTR   0x02040375u
/* ScriptGetVar(FieldSystem*, u16 varId) -> u16     (0x020403AC)
 * GetVarPointer + ldrh, oppure il letterale se il puntatore e' NULL. */
#define SGP_BORSA_GET_VAR       0x020403ADu
/* Save_Bag_Get(SaveData*) -> Bag*                  (0x0207879C) */
#define SGP_BORSA_SAVE_BAG      0x0207879Du
/* Bag_GetItemPocket(Bag*, u16 id, ItemSlot **slots, u32 *count, u32 heap)
 *     -> u32 tasca                                 (0x02078240)
 * Rende il valore di GetItemAttr(id, ITEMATTR_FIELD_POCKET, heap): e' la
 * STESSA chiamata che `Bag_GetItemSlotForAdd` fa a 0x0207834E per scegliere
 * il tetto. */
#define SGP_BORSA_POCKET        0x02078241u
/* Bag_GetItemQuantity(Bag*, u16 id, u32 heap) -> u16   (0x02078550)
 * 0 se l'oggetto non e' in borsa, altrimenti slot->quantity. */
#define SGP_BORSA_QUANTITY      0x02078551u
/* Bag_HasSpaceForItem(Bag*, u16 id, u16 qty, u32 heap) -> BOOL (0x02078384) */
#define SGP_BORSA_HAS_SPACE     0x02078385u
/* Bag_AddItem(Bag*, u16 id, u16 qty, u32 heap) -> BOOL          (0x02078398) */
#define SGP_BORSA_ADD_ITEM      0x02078399u

/* ========================================================= ScriptContext ===
 * pret `include/script.h` struct ScriptContext, contato campo per campo:
 *   +0x00 u8 stackDepth / mode / comparisonResult / id
 *   +0x04 ScrCmdFunc native_ptr
 *   +0x08 const u8 *script_ptr        <- confermato da ScriptReadHalfword,
 *                                        che fa `ldr r1,[r0,#8]` a 0x0203FE2C
 *   +0x0C const u8 *stack[20]         (80 B)
 *   +0x5C const ScrCmdFunc *cmdTable
 *   +0x60 u32 cmd_count
 *   +0x64 u32 data[4]
 *   +0x74 TaskManager *taskman
 *   +0x78 MsgData *msgdata
 *   +0x7C u8 *mapScripts              <- inizio del MEMBRO caricato:
 *        `ctx->mapScripts = AllocAndReadWholeNarcMemberByIdPair(...)`
 *        (script_manager.c:213), cioe' il byte 0 del membro. Quindi
 *        script_ptr - mapScripts e' esattamente la coordinata del censimento.
 *   +0x80 FieldSystem *fieldSystem    <- confermato dai byte di entrambe le
 *        ScrCmd ganciate: `adds r1,#0x80 ; ldr r5,[r1]`
 */
#define SGP_CTX_SCRIPT_PTR      0x08u
#define SGP_CTX_MAP_SCRIPTS     0x7Cu
#define SGP_CTX_FIELD_SYSTEM    0x80u

/* FieldSystem +0x0C = SaveData*: `ldr r0,[r5,#0xc]` a 0x0204EACA / 0x0204EA1A,
 * subito prima di `bl Save_Bag_Get`. */
#define SGP_FS_SAVEDATA         0x0Cu

/* ============================================================== costanti ===
 * Tasche: pret `include/constants/items.h:4-11`. */
#define SGP_POCKET_TMHMS        3u
#define SGP_POCKET_MAIL         5u
#define SGP_POCKET_KEY_ITEMS    7u

/* I tetti, letti come li legge il gioco in `Bag_GetItemSlotForAdd`:
 *   0x02078352  cmp r0,#3          (la tasca resa da Bag_GetItemPocket)
 *   0x02078356  movs r0,#0x63      -> 99  per POCKET_TMHMS
 *   0x0207836A  ldr r0,[pc,#0x14]  -> la parola a 0x02078380 = 0x3E7 = 999
 * Entrambi riletti sui byte delle due ROM 1.2.1. */
#define SGP_TETTO_MTMN          99u
#define SGP_TETTO_NORMALE       999u

/* Heap. Non se ne apre nessuno: si passano quelli che passa il gioco.
 *   4  = `movs r3,#4` a 0x0204EAD4 e 0x0204EA24 (le due ScrCmd ganciate)
 *   11 = `movs r2,#0xb` a 0x0204EB6E (ScrCmd_GetItemQuantity) */
#define SGP_HEAP_CMD            4u
#define SGP_HEAP_QUANTITA       11u

/* Il flag «ho scartato qualcosa», letto dall'appendice di bytecode
 * (SGP-1.2-BORSA-GEN-09) con `CompareVarToValue <flag>, 1`.
 *
 * NON E' 0x800D. La 1.2.1 usava `VAR_SPECIAL_x800D` credendolo libero perche'
 * «le speciali sono 0x8000..0x800D e nessuno dei cinque membri lo scrive»
 * (U §3.4). Le due premesse sono vere e la conclusione e' falsa: 0x800D e'
 * `VAR_SPECIAL_LAST_TALKED` (pret include/constants/vars.h:402), cioe'
 * `specialVars[13]` / `SCRIPTENV_SPECIAL_VAR_LAST_INTERACTED`
 * (pret include/script.h:138). A scriverlo non e' lo script: e' il MOTORE,
 * che ci mette l'id dell'oggetto con cui si e' appena interagito — e per le
 * Poke Ball a terra quell'id vale 1. Il membro 141 lo legge pure
 * (`HidePerson VAR_SPECIAL_LAST_TALKED`, scr_seq_0141 @_1830). Misura al
 * banco: raccogliendo una Ball a terra la guardia dell'appendice era gia'
 * soddisfatta senza che niente fosse stato scartato, e il gioco mostrava
 * «The Bag is full! / It was picked up, but had to be left behind.» DOPO
 * aver messo l'oggetto in Borsa.
 *
 * 0x800A e' l'unica speciale che nessuno scrive: censimento sugli 82703
 * comandi degli script della ROM 1.2.x, 3 sole occorrenze, tutte letture
 * (`Wait x800A` nel membro 3), zero scritture; e il motore non la tocca
 * (scrive x8000..x8003 in FieldMove_SetArgs, x800C = RESULT, x800D =
 * LAST_TALKED). Non basta pero' che nessuno la scriva: la ScriptEnvironment
 * sta sull'heap e in partita contiene spazzatura (misurata: x800A = 11).
 * Percio' il contratto e': **il gancio del comando 125 la scrive SEMPRE**,
 * 0 quando non ha scartato nulla, 1 quando ha scartato; e ogni appendice e'
 * preceduta, nello stesso flusso, dal `GiveItem` a cui e' agganciata. */
#define SGP_VAR_SCARTATO        0x800Au

/* Lunghezza dell'istruzione dei due comandi ganciati: opcode (2 B) + tre
 * argomenti da 2 B ciascuno (`scrcmd.json`, e i tre `bl ScriptReadHalfword`
 * nei corpi originali) = 8 B. */
#define SGP_LUNG_ISTR           8u
/* Finestra dell'impronta: al piu' 32 byte che TERMINANO con l'istruzione. */
#define SGP_FINESTRA            32u

#endif /* SGP_BORSA_H */
