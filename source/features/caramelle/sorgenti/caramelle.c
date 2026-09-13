/* Sacred Gold Plus 1.2 — `sgp.caramelle`: la Caramella Rara resta nel menu
 * squadra dopo l'uso. GPL-3.0-or-later.
 *
 * IL PROBLEMA. La funzione «uso ripetuto» della 1.1 vive su quattro ganci, e i
 * due che decidono «resto o esco» (C e D) stanno dentro
 * `PartyMenu_ItemUseFunc_WaitTextPrinterThenExit` (0x02081378). La Caramella
 * Rara non passa mai di lì: `ItemId_GetPartyUseType` le assegna il tipo 2, la
 * tavola di `PartyMenu_SetItemUseFuncFromBagSelection` (0x020812E8) le installa
 * `PartyMenu_ItemUseFunc_LevelUp` (0x02081A74), e la catena finisce in
 * `PartyMenu_ItemUseFunc_LevelUpLearnMovesLoop` (0x02081C50), sotto-stato 6,
 * che rende BEGIN_EXIT di suo. Dimostrazione completa in
 * `M-borsa-riuso-caramelle.md` §1.4; controprova sui byte: le uniche parole di
 * pool dell'ARM9 che valgono 0x02081379 sono 0x0207C3CC, 0x0208143C,
 * 0x020815DC, 0x020817BC, 0x02081A54 — nessuna nella catena della caramella.
 *
 * IL RIMEDIO. Un solo gancio, a 0x02081E96, nell'ULTIMO punto utile del
 * sotto-stato 6: dopo `GetMonEvolution`, prima che `BEGIN_EXIT` smonti
 * l'applicazione. A quel punto il testo è chiuso, la finestra delle statistiche
 * è chiusa (sotto-stato 2), le mosse nuove sono già state gestite (3/5) e la
 * specie di evoluzione è già in `args->species`. Nessuno stato è «a metà».
 *
 * IL CONTRATTO AL SITO. Lette dai byte (0x02081E8C..0x02081EA6):
 *
 *     02081E8C  ldr  r1,[pc,#0x28]     ; r1 = 0x654 (offset di args)
 *     02081E8E  ldr  r2,[r4,r1]        ; r2 = args
 *     02081E90  strh r0,[r2,#0x3c]     ; args->species = GetMonEvolution(...)
 *     02081E92  ldr  r1,[r4,r1]        ; r1 = args
 *     02081E94  ldrh r0,[r1,#0x3c]     ; r0 = args->species
 *   > 02081E96  cmp  r0,#0             ; <-- il nostro gancio comincia qui
 *     02081E98  beq  0x02081E9E
 *     02081E9A  movs r0,#9
 *     02081E9C  b    0x02081EA0
 *     02081E9E  movs r0,#0
 *     02081EA0  adds r1,#0x27
 *     02081EA2  strb r0,[r1]           ; args->selectedAction
 *     02081EA4  movs r0,#0x20          ; PARTY_MENU_STATE_BEGIN_EXIT
 *     02081EA6  pop  {r3,r4,r5,pc}
 *
 * Quindi all'ingresso: r0 = args->species, r1 = args, r4 = PartyMenu, e il
 * valore di ritorno della funzione del gioco è ciò che sta in r0 quando si
 * esegue il `pop`. Il gancio scrive 6 byte a 0x02081E96: `BL` (4 B) verso
 * `sgp_caramelle_gancio` e `pop {r3,r4,r5,pc}` (2 B, `38bd`). I 10 byte
 * 0x02081E9A..0x02081EA3 restano come sono, ma diventano irraggiungibili.
 *
 * LA ROUTINE FA TUTTO IL LAVORO DEL CODICE SOSTITUITO: scrive lei
 * `args->selectedAction` e rende lei lo stato. Il caso «esci» è quindi
 * **identico al vanilla byte per byte nei suoi effetti**, non una imitazione.
 *
 * I CINQUE CANCELLI (M §3.2). Ognuno è capace di fallire, e ognuno ha un
 * mutante dedicato nei test:
 *   G3 evoluzione in coda  -> azione 9, uscita vanilla (si lascia fare al gioco)
 *   G1 itemId != ITEM_NONE -> altrimenti azione 0, uscita: è il rilancio dopo
 *      «dimentica mossa», e senza questo cancello si rientrerebbe nel menu
 *      SENZA oggetto (rischio R1, il vero rischio di blocco)
 *   G2 context == USE_ITEM -> lo stesso rilancio, visto dall'altro lato
 *   G4 scorta > 0          -> l'ultima caramella riporta alla Borsa
 *   G5 slot squadra valido -> è letteralmente la guardia che 0x02074644
 *      applica a se stesso prima di calcolare party+8+idx*0xEC; fuori da essa
 *      il gioco stesso finisce nell'assert 0x0202551C
 *
 * IL LIVELLO 100 non ha bisogno di un cancello: al rientro
 * `CanUseItemOnMonInParty` rifiuta, il gioco stampa «non avrà effetto» e si
 * esce attraverso 0x02081378, cioè attraverso il codice 1.1 già esistente.
 *
 * IL RIENTRO è la stessa sequenza di `UX105_BAG_Tail` (0x023DFC80), che è in
 * ROM e collaudata dalla 1.1 — letta dai byte, non dedotta:
 *     ClearFrameAndWindow2(&pm->windows[34], TRUE)
 *     PartyMenu_PrintMessageOnWindow32(pm, 33, TRUE)
 *     thunk_Sprite_SetPaletteOverride(pm->sprites[CURSOR], 0)
 *     return 4
 * Non riusiamo `borsa.text`: è congelato dalla regola della zona 1.1, e
 * dipenderne significherebbe legare due funzioni che devono poter morire da
 * sole. Ripetiamo la sequenza con letterali propri, 24 byte di pool.
 *
 * VINCOLI DI COMPILAZIONE: freestanding, niente libc, niente libgcc, nessuna
 * divisione, nessuna tavola di salto, nessun simbolo esterno — `carica_text.py`
 * rifiuta l'oggetto se ne trova.
 */
#include "sgp_caramelle.h"

typedef u16 (*BagQuantityFn)(void *bag, u16 item, u32 heap);
typedef u32 (*PartyNumFn)(void *party);
typedef void (*ClearWindowFn)(void *window, u32 draw);
typedef void (*PrintWin32Fn)(void *pm, u32 msg_id, u32 draw);
typedef void (*SpritePaletteFn)(void *sprite, u32 value);

/* Accessi diretti, non composti byte per byte. Sono leciti perché ogni offset
 * usato qui è allineato al proprio tipo (itemId +0x28 a 2, bag/party/search a
 * 4, sprites +0x678 a 4) e perché il gioco stesso li legge così, con `ldrh
 * r0,[r0,#0x28]` a 0x020812F0 e `ldr r2,[r4,r1]` a 0x02081E8E. Il blob gira
 * solo su ARM946E-S little-endian: non c'è un secondo bersaglio da cui
 * difendersi, e la composizione byte per byte costava 60 B di codice in più
 * senza rendere vero nulla che non fosse già vero.
 */
#define RD16(p, o)  (*(const volatile u16 *)((const u8 *)(p) + (o)))
#define RD32(p, o)  (*(const volatile u32 *)((const u8 *)(p) + (o)))
#define WR32(p, o, v) (*(volatile u32 *)((u8 *)(p) + (o)) = (u32)(v))

u32 sgp_caramelle_decidi(u32 species, u8 *args, u8 *pm);

/* La trampolina. Serve solo a portare r4 (PartyMenu) in r2, cosa che il C non
 * sa fare: r4 al sito è il primo argomento della funzione del gioco, salvato
 * dal suo `push {r3,r4,r5,lr}` a 0x02081C50.
 *
 * `push {r4, lr}` / `pop {r4, pc}`: due parole, quindi l'allineamento a 8 della
 * pila si conserva, e r4 torna al chiamante intatto anche se il corpo C lo
 * usasse (lo usa: è callee-saved e clang lo alloca). Il `pop {r3,r4,r5,pc}` che
 * il gioco esegue subito dopo il nostro ritorno ripristina comunque r4 dal suo
 * proprio frame, ma un contratto rispettato solo «perché tanto non si vede» non
 * è un contratto. */
__attribute__((naked, used, section(".text")))
void sgp_caramelle_gancio(void)
{
    __asm__ volatile(
        "push {r4, lr}\n\t"
        "adds r2, r4, #0\n\t"      /* r2 = PartyMenu               */
        "bl   sgp_caramelle_decidi\n\t" /* r0 = species, r1 = args  */
        "pop  {r4, pc}\n\t");
}

/* L'uscita vanilla, in un posto solo: scrive l'azione e rende BEGIN_EXIT.
 * Averla scritta una volta sola è ciò che rende impossibile che un cancello
 * esca «quasi» come il gioco. */
static u32 esci(u8 *args, u32 azione)
{
    args[SGP_CAR_ARG_ACTION] = (u8)azione;
    return SGP_CAR_STATE_EXIT;
}

/* `species` arriva in r0, `args` in r1, `pm` in r2 (ce lo mette la trampolina
 * prendendolo da r4). Rende il nuovo stato di PartyMenu. */
u32 sgp_caramelle_decidi(u32 species, u8 *args, u8 *pm)
{
    void *bag;
    void *party;
    u16 item;
    u32 slot;
    u32 n;
    u32 cap;

    /* Nessuno dei due puntatori può essere nullo al sito — il gioco li ha
     * appena dereferenziati — ma se lo fosse l'unica risposta onesta è
     * l'uscita, non una scrittura a zero. */
    if (!args || !pm) {
        return SGP_CAR_STATE_EXIT;
    }

    /* G3 — evoluzione in coda: comportamento vanilla, azione 9. La scena
     * dell'evoluzione resta intoccata, e da lì il gioco torna alla Borsa. */
    if (species != 0u) {
        return esci(args, SGP_CAR_ACTION_EVO);
    }

    /* G1 — l'oggetto deve esserci ancora. Il rilancio del menu dopo il
     * Riepilogo «dimentica mossa» porta ITEM_NONE. */
    item = RD16(args, SGP_CAR_ARG_ITEMID);
    if (item == 0u) {
        return esci(args, SGP_CAR_ACTION_0);
    }

    /* G2 — lo stesso rilancio, visto dal contesto: dev'essere USE_ITEM, non
     * REPLACE_MOVE_LEVELUP. */
    if (args[SGP_CAR_ARG_CONTEXT] != SGP_CAR_CTX_USE_ITEM) {
        return esci(args, SGP_CAR_ACTION_0);
    }

    /* G4 — scorta rimasta. È il «rifiuto 5» della 1.1: ciò che rende questa
     * modifica capace di uscire invece di restare per sempre. */
    bag = (void *)RD32(args, SGP_CAR_ARG_BAG);
    if (!bag) {
        return esci(args, SGP_CAR_ACTION_0);
    }
    if (((BagQuantityFn)SGP_CAR_BAG_QUANTITY)(bag, item, SGP_CAR_HEAP_PARTY) == 0u) {
        return esci(args, SGP_CAR_ACTION_0);
    }

    /* G5 — lo slot su cui il menu tornerà a lavorare dev'essere un bersaglio
     * vero: slot < Party_GetCount(party) E slot < Party_GetCapacity(party),
     * cioè le due condizioni che 0x02074644 pretende da sé. */
    party = (void *)RD32(args, SGP_CAR_ARG_PARTY);
    if (!party) {
        return esci(args, SGP_CAR_ACTION_0);
    }
    slot = (u32)pm[SGP_CAR_PM_SLOT];
    n = ((PartyNumFn)SGP_CAR_PARTY_COUNT)(party);
    cap = ((PartyNumFn)SGP_CAR_PARTY_CAPACITY)(party);
    if (slot >= n || slot >= cap) {
        return esci(args, SGP_CAR_ACTION_0);
    }

    /* Tutti i cancelli superati: si resta nel menu.
     *
     * `selectedAction` resta 0: se qualcosa a valle decidesse comunque di
     * uscire, uscirebbe come il vanilla senza evoluzione. Non lasciamo mai
     * l'azione al valore che aveva. */
    args[SGP_CAR_ARG_ACTION] = (u8)SGP_CAR_ACTION_0;

    /* `levelUpMoveSearchState` lo azzera già il gioco entrando nel sotto-stato
     * 2 (0x02081CDA), quindi questo non cambia il comportamento; lo scriviamo
     * perché il cammino «rientro -> LevelUp -> 0 -> 1 -> 2» non era mai stato
     * percorso due volte di fila (M §5, rischio R4) e un iteratore lasciato a
     * metà sarebbe l'unico modo in cui la seconda caramella differirebbe dalla
     * prima. */
    WR32(args, SGP_CAR_ARG_SEARCH, 0u);

    ((ClearWindowFn)SGP_CAR_CLEAR_WINDOW)((void *)(pm + SGP_CAR_PM_WINDOW34), 1u);
    ((PrintWin32Fn)SGP_CAR_PRINT_WIN32)((void *)pm, SGP_CAR_MSG_WHICH_MON, 1u);
    ((SpritePaletteFn)SGP_CAR_SPRITE_PALETTE)(
        (void *)RD32(pm, SGP_CAR_PM_SPR_CURSOR), 0u);

    return SGP_CAR_STATE_SELECT_MON;
}
