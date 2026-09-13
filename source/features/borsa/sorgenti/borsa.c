/* Sacred Gold Plus 1.2.1 — `sgp.borsa`: l'oggetto donato o raccolto quando lo
 * slot e' al tetto viene comunque "ricevuto" e scartato, invece di bloccare la
 * storia. SGP-1.2-BORSA-GEN-03. GPL-3.0-or-later.
 *
 * IL PROBLEMA (U-borsa-progetto-esecutivo.md §2.4). Il contesto — «questo
 * oggetto e' un dono gratuito o e' merce pagata?» — si conosce solo al comando
 * 127 `HasSpaceForItem`, che gira nel membro del sito. Il dono vero avviene al
 * comando 125 `GiveItem`, e per 103 siti su 110 avviene in DUE SOLI punti del
 * membro 3 (gli script comuni `std_obtain_item_verbose` 2008 e
 * `std_give_item_verbose` 2033), condivisi anche dall'Angolo dei Premi e dai
 * negozi. Decidere sul 125 e' impossibile; decidere sul 127 e non poter agire
 * sul 125 e' inutile. Serve una staffetta fra i due.
 *
 * COME SI RICONOSCE IL SITO. `ScriptContext` porta `script_ptr` (+0x08, il
 * program counter del bytecode) e `mapScripts` (+0x7C, il byte 0 del membro
 * caricato — `AllocAndReadWholeNarcMemberByIdPair`, script_manager.c:213).
 * All'ingresso della ScrCmd, `script_ptr` punta SUBITO DOPO l'opcode, perche'
 * `RunScriptCommand` legge l'opcode con `ScriptReadHalfword` prima di chiamare
 * la voce di tabella (script.c:75). Quindi
 *
 *     offset del sito = script_ptr - mapScripts - 2
 *
 * e' la stessa coordinata del censimento (`SGP-1.2-BORSA-GEN-01`). Il numero
 * del membro NON e' in `ScriptContext`: si supplisce con un'impronta FNV-1a a
 * 16 bit sui <= 32 byte che TERMINANO con l'istruzione. Il cancello
 * `chiavi_uniche` del censimento verifica in modo esaustivo che le 188+63
 * chiavi (offset, impronta) siano tutte distinte.
 *
 *     chiave = (offset << 16) | impronta        una parola u32
 *
 * `CallStd` costruisce un ScriptContext NUOVO con il proprio `mapScripts`
 * (scrcmd_c.c:352-369 + script_manager.c:213): percio' i due siti comuni del
 * membro 3 hanno anche loro un offset ben definito, e percio' la staffetta
 * deve vivere in RAM di riserva e non dentro `ScriptContext`.
 *
 * COME SI INSTALLANO I GANCI. `gScriptCmdTable` sta a 0x020FAD00 nell'ARM9
 * STATICO (segmento [0x02000000, 0x02111860), presente byte per byte nel file
 * .nds: verificato su EN e IT) — non in .bss. Si riscrivono le due sole parole
 * 0x020FAD00+4*125 e +4*127 facendole puntare ai due trampolini con il bit
 * Thumb acceso. Niente BL da rattoppare, nessun overlay toccato, nessuna
 * ricompressione BLZ; 851 voci su 853 restano bit per bit le originali. Gli
 * originali (0x0204E9D9 e 0x0204EA89) si chiamano attraverso i due puntatori
 * che l'applicatore salva a +0x5E0/+0x5E4: cosi', se un domani un'altra
 * modifica avesse gia' ripuntato una voce, si incatena invece di scavalcarla.
 * Se il puntatore e' ancora zero (blocco non riempito) si usa il letterale.
 *
 * PERCHE' LA VIA NON PERMISSIVA CHIAMA L'ORIGINALE. Non imita il vanilla: LO
 * ESEGUE. Tutto cio' che il wrapper fa prima di decidere e' non distruttivo
 * (legge `script_ptr` senza avanzarlo, sbircia i tre argomenti byte per byte,
 * chiama `ScriptGetVar` che non ha effetti), quindi l'originale trova il
 * contesto esattamente come lo avrebbe trovato senza di noi. Negozi, gettoni,
 * punti Pokeathlon, Battle Points e scambi restano rigorosi per costruzione,
 * non per attenzione.
 *
 * I TETTI si leggono come li legge il gioco: `Bag_GetItemPocket` (0x02078240)
 * rende la tasca, e `Bag_GetItemSlotForAdd` sceglie 99 se la tasca e' 3
 * (MT/MN) e altrimenti la parola a 0x02078380, che vale 999. Non si scrive mai
 * `slot->quantity`: si passa sempre da `Bag_AddItem` con una quantita' gia'
 * limitata, percio' nessuna tasca puo' finire oltre il tetto.
 *
 * OGGETTI CHIAVE (tasca 7) E POSTA (tasca 5) sono immuni: uscita anticipata,
 * comportamento vanilla in ogni caso. La Posta perche' ogni lettera porta dati
 * propri e non e' impilabile; gli oggetti chiave perche' scartarne uno
 * bloccherebbe la storia invece di sbloccarla.
 *
 * VINCOLI DI COMPILAZIONE: freestanding, niente libc, niente libgcc, nessuna
 * divisione, nessuna tavola di salto, nessun simbolo esterno, nessuna sezione
 * allocata oltre .text — `carica_text.py` rifiuta l'oggetto se ne trova. Per
 * questo la tabella, la staffetta e i due puntatori non sono variabili C ma
 * indirizzi assoluti dentro il blocco.
 */
#include "sgp_borsa.h"

typedef BOOL (*ScrCmdFn)(void *ctx);
typedef u16 (*ReadHwFn)(void *ctx);
typedef u16 (*GetVarFn)(void *fs, u16 id);
typedef u16 *(*GetVarPtrFn)(void *fs, u16 id);
typedef void *(*SaveBagFn)(void *save);
typedef u32 (*PocketFn)(void *bag, u16 item, void **slots, u32 *count, u32 heap);
typedef u16 (*QuantityFn)(void *bag, u16 item, u32 heap);
typedef BOOL (*BagOpFn)(void *bag, u16 item, u16 qty, u32 heap);

/* Accessi diretti, non composti byte per byte: ogni offset usato qui e'
 * allineato al proprio tipo, e il gioco stesso legge cosi' (`ldr r5,[r1]` su
 * ctx+0x80 a 0x0204EA90). `volatile` perche' la tabella e la staffetta le
 * scrive qualcun altro (l'applicatore, e l'altra meta' della staffetta). Il
 * blob gira solo su ARM946E-S little-endian. */
#define RD16(a)     (*(const volatile u16 *)(a))
#define RD32(a)     (*(const volatile u32 *)(a))
#define WR16(a, v)  (*(volatile u16 *)(a) = (u16)(v))
#define CAMPO(p, o) ((u32)(p) + (u32)(o))

BOOL sgp_borsa_has_space(void *ctx);
BOOL sgp_borsa_give_item(void *ctx);

/* ------------------------------------------------------------ trampolini ---
 * Sono la coppia di indirizzi che le due voci di `gScriptCmdTable` porteranno,
 * e sono i PRIMI due oggetti del blocco: +0x000 e +0x008. `compila_borsa.py`
 * lo pretende, cosi' l'applicatore puo' scrivere le due parole conoscendo solo
 * la base del blocco.
 *
 * `push {r4, lr}` / `pop {r4, pc}`: due parole, quindi l'allineamento a 8
 * della pila si conserva; r0 (il `ctx` in entrata, il BOOL in uscita) passa
 * intatto in entrambi i versi. Non servono a spostare argomenti — servono a
 * dare un indirizzo FISSO e a garantire che i registri callee-saved tornino al
 * chiamante come li ha lasciati, anche quando il corpo C li alloca. */
__attribute__((naked, used, section(".text")))
void sgp_borsa_cmd127(void)
{
    __asm__ volatile(
        "push {r4, lr}\n\t"
        "bl   sgp_borsa_has_space\n\t"
        "pop  {r4, pc}\n\t");
}

__attribute__((naked, used, section(".text")))
void sgp_borsa_cmd125(void)
{
    __asm__ volatile(
        "push {r4, lr}\n\t"
        "bl   sgp_borsa_give_item\n\t"
        "pop  {r4, pc}\n\t");
}

/* ------------------------------------------------------- l'originale vero ---
 * Il puntatore salvato nel blocco, o il letterale se il blocco non e' ancora
 * stato riempito. Il ripiego non e' un lusso: fa si' che un blob caricato in
 * un blocco a zero si comporti come il gioco nudo, invece di saltare a 0. */
static ScrCmdFn sgp_originale(u32 dove, u32 ripiego)
{
    u32 p = RD32(dove);
    return (ScrCmdFn)(p != 0u ? p : ripiego);
}

/* --------------------------------------------------- lettura del bytecode ---
 * Il bytecode non e' allineato: `script_ptr` puo' essere dispari, e su
 * ARM946E-S una `ldrh` su indirizzo dispari rende una parola ruotata. Si
 * compone byte per byte, esattamente come fa `ScriptReadHalfword`
 * (0x0203FE32: due `ldrb`). */
static u16 sgp_sbircia16(const u8 *p)
{
    return (u16)((u32)p[0] | ((u32)p[1] << 8));
}

/* ---------------------------------------------- la chiave del sito -------
 * Rende (offset << 16) | impronta, oppure 0 se il sito non e' rappresentabile
 * (puntatori assenti, offset oltre 16 bit). 0 non e' mai una chiave valida:
 * l'offset 0 di un membro e' dentro l'intestazione `u32 rel[i]`, non puo'
 * ospitare un'istruzione. */
static u32 sgp_chiave(void *ctx)
{
    u32 pc = RD32(CAMPO(ctx, SGP_CTX_SCRIPT_PTR));
    u32 base = RD32(CAMPO(ctx, SGP_CTX_MAP_SCRIPTS));
    u32 off, disp, n, h;
    const u8 *p;

    if (pc == 0u || base == 0u || pc < base + 2u) {
        return 0u;
    }
    off = pc - base - 2u;               /* offset dell'OPCODE nel membro */
    if (off > 0xFFFFu) {
        return 0u;
    }
    disp = pc - base + (SGP_LUNG_ISTR - 2u);   /* fine dell'istruzione */
    n = (disp > SGP_FINESTRA) ? SGP_FINESTRA : disp;  /* mai prima del membro */
    p = (const u8 *)(base + disp - n);
    h = 0x811C9DC5u;
    while (n != 0u) {
        h = (h ^ (u32)(*p)) * 0x01000193u;
        p++;
        n--;
    }
    return (off << 16) | (h & 0xFFFFu);
}

/* --------------------------------------------------- la tabella permissiva ---
 * Un array di parole in coda al blocco, riempito dall'applicatore
 * (SGP-1.2-BORSA-GEN-06) rileggendo la ROM che sta per patchare. Ricerca
 * lineare: al piu' 120 voci, e il confronto e' una parola. Uno slot a zero
 * chiude la tabella, percio' un blocco a zero significa «nessun sito
 * permissivo», cioe' gioco nudo: il modo di guastarsi e' il piu' innocuo che
 * ci sia. */
static int sgp_permesso(u32 chiave)
{
    u32 i;

    if (chiave == 0u) {
        return 0;
    }
    for (i = 0u; i < SGP_BORSA_TAB_N; i++) {
        u32 v = RD32(SGP_BORSA_TAB_ADDR + i * 4u);
        if (v == 0u) {
            return 0;
        }
        if (v == chiave) {
            return 1;
        }
    }
    return 0;
}

/* -------------------------------------------------- capienza residua reale ---
 * Quanta parte di `qty` entra davvero. Rende `qty` — cioe' «fai come il
 * vanilla» — ogni volta che il tetto non c'entra nulla. */
static u16 sgp_quanto_entra(void *bag, u16 item, u16 qty)
{
    void *slots = 0;
    u32 n = 0;
    u32 tasca;
    u16 tetto;
    u16 avute;
    u16 spazio;

    tasca = ((PocketFn)SGP_BORSA_POCKET)(bag, item, &slots, &n, SGP_HEAP_CMD);
    if (tasca == SGP_POCKET_KEY_ITEMS || tasca == SGP_POCKET_MAIL) {
        return qty;                 /* chiavi e Posta: MAI permissivo */
    }
    if (tasca > SGP_POCKET_KEY_ITEMS) {
        return qty;                 /* tasca ignota: non inventiamo un tetto */
    }
    tetto = (tasca == SGP_POCKET_TMHMS) ? SGP_TETTO_MTMN : SGP_TETTO_NORMALE;
    avute = ((QuantityFn)SGP_BORSA_QUANTITY)(bag, item, SGP_HEAP_QUANTITA);
    if (avute == 0u) {
        return qty;                 /* assente: decide lo SLOT, non il tetto */
    }
    if (avute >= tetto) {
        return 0u;                  /* al tetto: tutto scartato */
    }
    spazio = (u16)(tetto - avute);
    return (qty <= spazio) ? qty : spazio;
}

static void sgp_arma(u16 item, u16 chieste, u16 entrate)
{
    WR16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_ITEM), item);
    WR16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_CHIESTE), chieste);
    WR16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_ENTRATE), entrate);
    WR16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_ARMATA), 1u);
}

/* ==================================== il nucleo, uno solo per i due ganci ===
 * I due comandi hanno la STESSA forma — tre argomenti a 2 B, `*ret` come
 * risultato, `return FALSE` — e differiscono per quattro cose soltanto: quale
 * originale chiamare, se consultare la staffetta, quale funzione della Borsa
 * invocare (`Bag_HasSpaceForItem` contro `Bag_AddItem`) e cosa fare dell'esito.
 * Tenerli in una funzione sola non e' un risparmio di byte (lo e' anche: 260 B
 * su 1024 sono un quarto del blocco): e' cio' che rende IMPOSSIBILE che i due
 * ganci divergano nel modo di riconoscere il sito o di leggere gli argomenti.
 *
 * Vanilla del 127 (letto a 0x0204EA88..0x0204EADE):
 *     fs   = *(ctx + 0x80)
 *     item = ScriptGetVar(fs, ScriptReadHalfword(ctx))
 *     qty  = ScriptGetVar(fs, ScriptReadHalfword(ctx))
 *     ret  = GetVarPointer(fs, ScriptReadHalfword(ctx))
 *     *ret = Bag_HasSpaceForItem(Save_Bag_Get(*(fs+0x0C)), item, qty, 4)
 *     return FALSE
 * Vanilla del 125 (0x0204E9D8..0x0204EA2E): identico, con `Bag_AddItem`.
 */
static BOOL sgp_nucleo(void *ctx, int e125)
{
    void *fs;
    void *bag;
    u16 a;
    u16 item;
    u16 qty;
    u16 *ret;
    u16 entra;
    BOOL r;
    int permesso;
    int armata = 0;

    permesso = sgp_permesso(sgp_chiave(ctx));
    fs = (void *)RD32(CAMPO(ctx, SGP_CTX_FIELD_SYSTEM));

    if (e125) {
        /* Sbirciata NON distruttiva dei primi due argomenti: serve a sapere se
         * la staffetta e' per QUESTO oggetto e per QUESTA quantita'.
         * `script_ptr` non si muove, cosi' la via vanilla puo' ancora chiamare
         * l'originale e trovarlo intatto. */
        const u8 *pc = (const u8 *)RD32(CAMPO(ctx, SGP_CTX_SCRIPT_PTR));
        if (pc != 0 && fs != 0) {
            u16 item0 = ((GetVarFn)SGP_BORSA_GET_VAR)(fs, sgp_sbircia16(pc));
            u16 qty0 = ((GetVarFn)SGP_BORSA_GET_VAR)(fs, sgp_sbircia16(pc + 2));
            if (RD16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_ARMATA)) != 0u
                && RD16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_ITEM)) == item0
                && RD16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_CHIESTE)) == qty0) {
                armata = 1;
            }
        }
    }

    /* La staffetta si azzera SEMPRE e prima di ogni uscita: un 127 qualunque,
     * anche di un negozio, chiude quella eventualmente lasciata aperta, e ogni
     * 125 la consuma. E' monouso per costruzione, non per disciplina. */
    WR16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_ARMATA), 0u);

    if (!permesso && !armata) {
        /* I due puntatori stanno in due parole adiacenti, nell'ordine 127, 125:
         * e' per poterli scegliere cosi'. */
        return sgp_originale(SGP_BORSA_ORIG127_ADDR + (u32)e125 * 4u,
                             e125 ? SGP_BORSA_VAN125 : SGP_BORSA_VAN127)(ctx);
    }

    /* Tre letture in tre istruzioni separate: l'ordine di valutazione degli
     * argomenti di una chiamata non e' definito in C, quello delle istruzioni
     * si'. Sono anche i 6 byte di cui `script_ptr` deve avanzare, esattamente
     * come nel vanilla. */
    a = ((ReadHwFn)SGP_BORSA_READ_HW)(ctx);
    item = ((GetVarFn)SGP_BORSA_GET_VAR)(fs, a);
    a = ((ReadHwFn)SGP_BORSA_READ_HW)(ctx);
    qty = ((GetVarFn)SGP_BORSA_GET_VAR)(fs, a);
    a = ((ReadHwFn)SGP_BORSA_READ_HW)(ctx);
    ret = ((GetVarPtrFn)SGP_BORSA_GET_VAR_PTR)(fs, a);
    bag = ((SaveBagFn)SGP_BORSA_SAVE_BAG)((void *)RD32(CAMPO(fs, SGP_FS_SAVEDATA)));

    entra = sgp_quanto_entra(bag, item, qty);

    if (entra == 0u) {
        /* Al tetto. Sul 127 diciamo «c'e' spazio» e prendiamo l'impegno di
         * consegnare il nulla; sul 125 rendiamo «riuscito» senza aggiungere.
         * Lo slot esiste per forza: `entra == 0` implica `avute >= tetto`,
         * cioe' l'oggetto e' gia' in borsa. */
        if (!e125) {
            sgp_arma(item, qty, 0u);
        }
        r = 1;
    } else {
        if (!e125 && entra < qty) {
            sgp_arma(item, qty, entra);   /* parziale: 997 + 5 -> ne entrano 2 */
        }
        /* Mancanza di SLOT != tetto di quantita': sul primo resta il rifiuto
         * vanilla, e con esso `std_bag_is_full` (2009) come sempre. */
        r = ((BagOpFn)(e125 ? SGP_BORSA_ADD_ITEM : SGP_BORSA_HAS_SPACE))(
                bag, item, entra, SGP_HEAP_CMD);
        if (!e125 && r == 0) {
            WR16(CAMPO(SGP_BORSA_STAFFETTA, SGP_ST_ARMATA), 0u);
        }
    }

    if (ret != 0) {
        *ret = (u16)r;
    }

    if (e125 && entra < qty) {
        /* Qualcosa e' stato scartato: lo dice all'appendice di bytecode
         * (SGP-1.2-BORSA-GEN-09), che stampa il messaggio col nome
         * dell'oggetto. VAR_SPECIAL_x800D vive nella ScriptEnvironment: muore
         * con lo script, non finisce nel salvataggio, non puo' restare accesa. */
        u16 *v = ((GetVarPtrFn)SGP_BORSA_GET_VAR_PTR)(fs, SGP_VAR_SCARTATO);
        if (v != 0) {
            *v = 1u;
        }
    }
    return 0;
}

/* [127] al posto di ScrCmd_HasSpaceForItem (0x0204EA89) */
BOOL sgp_borsa_has_space(void *ctx)
{
    return sgp_nucleo(ctx, 0);
}

/* [125] al posto di ScrCmd_GiveItem (0x0204E9D9) */
BOOL sgp_borsa_give_item(void *ctx)
{
    return sgp_nucleo(ctx, 1);
}
