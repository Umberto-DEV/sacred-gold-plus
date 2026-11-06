/* Portable box bridge: ordinary party -> native PC (mode 2) -> rebuilt party.
 *
 * Hooks (installed by sgp131/portable.py, all inert until the activation words
 * in the compartment are set):
 *   sgp_box_launch_app   BL inside PartyMenu_LaunchApp_Unk1 (every start-menu party launch)
 *   sgp_box_party_main   BL to PartyMenu_Subtask_MainNormal in the party state-1 handler
 *   sgp_box_party_return entry gate of Task_StartMenu_HandleReturn_Pokemon (via trampoline)
 *   sgp_box_pc_return    exit callback installed while the native PC owns the field child
 *   sgp_box_prompt_print BL inside PartyMenu_PrintMessageOnWindow32 (party_ui.c)
 *
 * Lifecycle (native services only; pins in data/portable-native-abi.json):
 *   1 launch  -> bind (generation++, identity of field/owner/args)
 *   2 state 1 -> request accepted only for the bound, eligible, idle party: the
 *                normal Cancel action (RETURN_0, state 32) is used
 *   3 return  -> PCBoxArgs allocated BEFORE the party args are freed; failure =
 *                native Cancel with the args still alive. Then free the args once,
 *                launch PC mode 2 and install sgp_box_pc_return
 *   4 PC done -> native post-processing (Bill notification), free PC args once,
 *                call the pinned PartyArgs constructor directly, check its return,
 *                then relaunch through the guarded wrapper with a clamped cursor. If it
 *                cannot be rebuilt: LoadFieldOverlay + START_MENU_STATE_RETURN, the
 *                native Cancel exit, never a launcher call with NULL.
 * The record holds identities only (u32 addresses), never a Pokemon pointer.
 * FieldMove_InitCheckData is NOT called: the check data is position-only and is
 * kept in the owner exactly as the native Summary round trip keeps it.
 */
#include "abi.h"

__asm__(".pushsection .text,\"ax\",%progbits\n.balign 4\n"
        ".local sgp_box_area\n.type sgp_box_area,%object\n"
        "sgp_box_area:\n.word 0x31425053\n.space 60\n"
        ".word 0x31434253,0,0,0,0,3,0,0\n"
        ".size sgp_box_area,96\n.popsection\n");
extern u8 sgp_box_area[96];
#define S ((volatile SgpBoxState *)sgp_box_area)
#define CFG ((volatile SgpBoxConfig *)(sgp_box_area + 64))

/* Native services (Thumb, address | 1). */
#define N_GET_FIELD 0x0205064Du
#define N_GET_ENV 0x02050651u
#define N_HEAP_ALLOC 0x0201AA8Du
#define N_HEAP_FREE 0x0201AB0Du
#define N_LAUNCH_APP 0x0203DFB5u
#define N_PC_LAUNCH 0x0203E869u
#define N_PARTY_CREATE 0x0203E4FDu
#define N_BILL 0x02093071u
#define N_LOAD_FIELD 0x020505C1u
#define N_MAIN_NORMAL 0x02079309u
#define N_PARTY_COUNT 0x02074641u
#define N_PLAY_SE 0x0200604Du
#define N_NATIVE_CALLBACK 0x0203CA9Du
#define N_VARS_FLAGS_GET 0x020503D1u    /* Save_VarsFlags_Get(SaveData) */
#define N_CHECK_FOLLOWER 0x02066645u    /* Save_VarsFlags_CheckHaveFollower(flags): escort mode */
#define PARTY_TEMPLATE 0x0210159Cu

#define HEAP_FIELD2 0x0Bu
#define PCBOX_ARGS_BYTES 0x0Cu
#define PARTY_ARGS_BYTES 0x44u
#define PC_MODE_MOVE 2u
#define STATE_BEGIN_EXIT 0x20
#define START_MENU_WAIT_APP 5u
#define START_MENU_RETURN 0x0Fu

/* Structure offsets (pinned). */
#define OWNER_STATE 0x26u
#define OWNER_FLAGS 0x34Cu
#define OWNER_UNK350 0x350u
#define OWNER_EXIT_FUNC 0x354u
#define OWNER_CHECK_DATA 0x370u
#define OWNER_EXIT_ENV 0x380u
#define PARTY_ARGS 0x654u
#define PARTY_INDEX 0xC65u
#define PARTY_BUTTON_ANIM 0xC9Cu
#define ARGS_PARTY 0x00u
#define ARGS_CHECK 0x18u
#define ARGS_FIELD 0x1Cu
#define ARGS_CONTEXT 0x24u
#define ARGS_SLOT 0x26u
#define ARGS_ACTION 0x27u
#define FIELD_SAVE 0x0Cu
#define FIELD_TASKMAN 0x10u
#define FIELD_AVATAR 0x40u
#define FIELD_LOAD_TYPE 0x70u
#define FIELD_FRONTIER 0xA0u
#define FIELD_LINK_RULESET 0xA4u
#define FIELD_MENU_INPUT 0x10Cu
#define AVATAR_STATE 0x18u

#define SE_DECIDE 1500u /* SEQ_SE_DP_SELECT */

static inline u32 rd32(u32 a) { return *(volatile u32 *)a; }
static inline u32 rd16(u32 a) { return *(volatile u16 *)a; }
static inline u32 rd8(u32 a) { return *(volatile u8 *)a; }
static inline void wr32(u32 a, u32 v) { *(volatile u32 *)a = v; }
static inline void wr16(u32 a, u32 v) { *(volatile u16 *)a = (u16)v; }
static inline void wr8(u32 a, u32 v) { *(volatile u8 *)a = (u8)v; }

static inline u32 heap_alloc(u32 size)
{
    return ((u32(*)(u32, u32))N_HEAP_ALLOC)(HEAP_FIELD2, size);
}
static inline void heap_free(u32 p) { ((void (*)(u32))N_HEAP_FREE)(p); }

static int sgp_box_input_request(void);
static int ensure_bound(u32 args);
static int bound_ok(u32 args);

/* ------------------------------------------------------------ record helpers */

static void reset_request(void)
{
    S->requested = 0;
    S->request_generation = 0;
}

static void cancel_request(void)
{
    reset_request();
    S->phase = SGP_BOX_PHASE_IDLE;
    S->failures++;
}

/* Identity of the live, bound ordinary party. Never trusts a pointer alone. */
static int bound_ok(u32 args)
{
    u32 owner = S->owner;
    if (S->phase != SGP_BOX_PHASE_BOUND || args == 0 || S->args != args || owner == 0)
        return 0;
    if (rd8(args + ARGS_CONTEXT) != 0 || rd32(args + ARGS_FIELD) != S->field)
        return 0;
    if (rd32(args + ARGS_CHECK) != owner + OWNER_CHECK_DATA)
        return 0;
    return rd32(owner + OWNER_EXIT_ENV) == args;
}

/* Deny by default. Reads only data the start menu and the field computed:
 *  - inhibitIconFlags/unk_350 of the owner (StartMenu_Init variants: ordinary = SAVE enabled, entries 7 and
 *    RETIRE inhibited, nothing outside {POKEDEX, POKEMON, BAG, 7, RETIRE, POKEGEAR}; Safari, Bug Contest, Pal
 *    Park, Battle Tower partner room, Colosseum and Union all inhibit SAVE);
 *  - FieldSystem: mapLoadType must be OVERWORLD (0), no frontierFsys (Battle Frontier facility run), no
 *    linkBattleRuleset (link / Colosseum rules);
 *  - the avatar state against travel_mask;
 *  - an installer-accepted context proof for what a static read cannot show (see INTEGRATION.md). */
static int policy_static(u32 field, u32 owner)
{
    u32 flags = rd32(owner + OWNER_FLAGS);
    u32 avatar, state;
    if ((flags & 0x10u) || (flags & 0x180u) != 0x180u || (flags & ~0x387u) || rd32(owner + OWNER_UNK350))
        return SGP_BOX_SPECIAL_ACTIVITY;
    if (rd32(field + FIELD_LOAD_TYPE) != 0 || rd32(field + FIELD_FRONTIER) != 0 || rd32(field + FIELD_LINK_RULESET) != 0)
        return SGP_BOX_SPECIAL_ACTIVITY;
    avatar = rd32(field + FIELD_AVATAR);
    if (avatar == 0)
        return SGP_BOX_UNPROVEN_TRAVEL;
    state = rd32(avatar + AVATAR_STATE);
    if (state > 7u || !((CFG->travel_mask >> state) & 1u))
        return SGP_BOX_UNPROVEN_TRAVEL;
    if (CFG->context_proof != 1u)
        return SGP_BOX_UNPROVEN_CONTEXT;
    return SGP_BOX_ELIGIBLE;
}

static int escorting(u32 field)
{
    u32 flags = ((u32(*)(u32))N_VARS_FLAGS_GET)(rd32(field + FIELD_SAVE));
    return ((int (*)(u32))N_CHECK_FOLLOWER)(flags) != 0;
}

int sgp_box_eligibility(void *field_, void *owner_)
{
    u32 field = (u32)field_, owner = (u32)owner_;
    int reason;
    if (field == 0 || owner == 0 || S->phase != SGP_BOX_PHASE_BOUND || S->field != field || S->owner != owner)
        return SGP_BOX_WRONG_OWNER;
    if (rd16(owner + OWNER_STATE) != START_MENU_WAIT_APP)
        return SGP_BOX_BUSY; /* identity of the args against the owner is bound_ok()'s job, not repeated here */
    reason = policy_static(field, owner);
    if (reason == SGP_BOX_ELIGIBLE && escorting(field))
        return SGP_BOX_SPECIAL_ACTIVITY; /* escort mode: the companion is mandatory */
    return reason;
}

/* ---------------------------------------------------------------------- bind */

static void bind_identity(u32 field, u32 args, u32 owner)
{
    if (S->requested)
        S->failures++; /* a pending request never survives a relaunch */
    S->generation++;
    S->requested = 0;
    S->request_generation = 0;
    S->prompt_shown = 0;
    S->pc_args = 0;
    S->field = field;
    S->args = args;
    S->owner = owner;
    S->phase = SGP_BOX_PHASE_BOUND;
    S->reason = (u32)policy_static(field, owner);
}

/* Launch hook (PartyMenu_LaunchApp_Unk1): the owner is not wired yet, identity comes from the args alone. */
void sgp_box_bind(void *field_, void *args_)
{
    u32 field = (u32)field_, args = (u32)args_;
    u32 check;
    S->phase = SGP_BOX_PHASE_IDLE;
    S->args = args;
    S->field = field;
    S->owner = 0;
    S->reason = SGP_BOX_WRONG_OWNER;
    if (args == 0 || rd8(args + ARGS_CONTEXT) != 0 || rd32(args + ARGS_FIELD) != field)
        return;
    check = rd32(args + ARGS_CHECK);
    if (check < OWNER_CHECK_DATA)
        return;
    bind_identity(field, args, check - OWNER_CHECK_DATA);
}

/* Context-0 parties the hook never saw (Bag return without an item, item swap declined): bind by LIVE identity.
 * The args name their owner and field; the field's running task must have exactly that owner as environment,
 * the owner must hold exactly these args, wait for the application and return through the native party
 * callback. Never while a request is in flight or the PC is running. */
static int ensure_bound(u32 args)
{
    u32 field, check, owner, task;
    if (bound_ok(args))
        return 1;
    if (S->phase == SGP_BOX_PHASE_EXITING || S->phase == SGP_BOX_PHASE_PC_RUNNING)
        return 0;
    if (args == 0 || rd8(args + ARGS_CONTEXT) != 0)
        return 0;
    field = rd32(args + ARGS_FIELD);
    check = rd32(args + ARGS_CHECK);
    if (field == 0 || check < OWNER_CHECK_DATA)
        return 0;
    owner = check - OWNER_CHECK_DATA;
    task = rd32(field + FIELD_TASKMAN);
    if (task == 0 || ((u32(*)(u32))N_GET_ENV)(task) != owner)
        return 0;
    if (rd32(owner + OWNER_EXIT_ENV) != args || rd32(owner + OWNER_EXIT_FUNC) != N_NATIVE_CALLBACK
        || rd16(owner + OWNER_STATE) != START_MENU_WAIT_APP)
        return 0;
    bind_identity(field, args, owner);
    return 1;
}

void sgp_box_launch_app(void *field, void *template_, void *args)
{
    ((void (*)(void *, void *, void *))N_LAUNCH_APP)(field, template_, args);
    sgp_box_bind(field, args);
}

/* --------------------------------------------------------------- state 1 hook */

int sgp_box_party_main(void *party_)
{
    u32 party = (u32)party_;
    u32 args, wanted;
    if (S->requested || CFG->input) {
        args = rd32(party + PARTY_ARGS);
        if (!CFG->bridge) {
            if (S->requested)
                reset_request();
        } else if (!ensure_bound(args)) {
            if (S->requested && S->phase != SGP_BOX_PHASE_EXITING)
                reset_request();
        } else if (rd32(party + PARTY_BUTTON_ANIM) == 0) {
            wanted = S->requested;
            if (!wanted && CFG->input && sgp_box_input_request())
                wanted = 1;
            if (wanted && sgp_box_eligibility((void *)S->field, (void *)S->owner) == SGP_BOX_ELIGIBLE) {
                S->requested = 1;
                S->request_generation = S->generation;
                S->selection = rd8(party + PARTY_INDEX);
                S->phase = SGP_BOX_PHASE_EXITING;
                wr8(args + ARGS_ACTION, 0); /* PARTY_MENU_ACTION_RETURN_0: the normal Cancel */
                ((void (*)(u32))N_PLAY_SE)(SE_DECIDE);
                return STATE_BEGIN_EXIT;
            }
            if (wanted)
                reset_request();
        }
    }
    return ((int (*)(void *))N_MAIN_NORMAL)(party_);
}

/* ------------------------------------------------------- party return callback */

/* Returns 1 when the callback was consumed (it then returns FALSE), 0 to run the
 * native callback unchanged (the trampoline restores r0/lr and re-executes it). */
int sgp_box_party_return(void *task)
{
    u32 field, owner, args, pc;
    if (!S->requested)
        return 0;
    if (!CFG->bridge || S->phase != SGP_BOX_PHASE_EXITING || S->request_generation != S->generation) {
        cancel_request();
        return 0;
    }
    field = ((u32(*)(void *))N_GET_FIELD)(task);
    owner = ((u32(*)(void *))N_GET_ENV)(task);
    args = S->args;
    if (field != S->field || owner != S->owner || rd32(owner + OWNER_EXIT_ENV) != args
        || rd8(args + ARGS_CONTEXT) != 0 || rd8(args + ARGS_ACTION) != 0
        || rd32(args + ARGS_FIELD) != field) {
        cancel_request();
        return 0;
    }
    pc = heap_alloc(PCBOX_ARGS_BYTES);
    if (pc == 0) {
        cancel_request(); /* native Cancel, party args still alive */
        return 0;
    }
    S->allocs++;
    wr32(pc + 0, rd32(field + FIELD_SAVE));
    wr32(pc + 4, field + FIELD_MENU_INPUT);
    wr32(pc + 8, PC_MODE_MOVE);
    S->selection = rd8(args + ARGS_SLOT);
    heap_free(args); /* exactly once; the native callback never runs on this path */
    wr32(owner + OWNER_EXIT_ENV, pc);
    S->pc_args = pc;
    S->args = 0;
    ((void (*)(u32, u32))N_PC_LAUNCH)(field, pc);
    wr32(owner + OWNER_EXIT_FUNC, (u32)sgp_box_pc_return);
    wr16(owner + OWNER_STATE, START_MENU_WAIT_APP);
    S->phase = SGP_BOX_PHASE_PC_RUNNING;
    S->opens++;
    reset_request();
    return 1;
}

/* ------------------------------------------------------------- PC return callback */

__attribute__((noinline)) static void return_to_field(u32 field, u32 owner)
{
    /* Same two statements as the native callback's default branch. */
    ((void (*)(u32))N_LOAD_FIELD)(field);
    wr16(owner + OWNER_STATE, START_MENU_RETURN);
    S->phase = SGP_BOX_PHASE_IDLE;
    S->pc_args = 0;
    S->args = 0;
}

int sgp_box_pc_return(void *task)
{
    u32 field = ((u32(*)(void *))N_GET_FIELD)(task);
    u32 owner = ((u32(*)(void *))N_GET_ENV)(task);
    u32 pc = S->pc_args, args, count, slot;
    if (S->phase != SGP_BOX_PHASE_PC_RUNNING || field != S->field || owner != S->owner
        || pc == 0 || rd32(owner + OWNER_EXIT_ENV) != pc) {
        S->failures++;
        return_to_field(field, owner); /* never free what this record does not own */
        return 0;
    }
    ((void (*)(u32))N_BILL)(field); /* the script flow's post-PC notification */
    heap_free(pc);
    S->frees++;
    S->pc_args = 0;
    wr32(owner + OWNER_EXIT_ENV, 0);
    /* Bypass PartyMenu_LaunchApp_Unk1: it writes through NULL when its
       CreateArgs allocation fails.  Call the pinned constructor directly,
       validate it, then reproduce Unk1's three initializations and launch. */
    args = ((u32(*)(u32, u32, u32, u32))N_PARTY_CREATE)(HEAP_FIELD2, field, 0, 0);
    if (args == 0) {
        S->failures++;
        return_to_field(field, owner);
        return 0;
    }
    count = ((u32(*)(u32))N_PARTY_COUNT)(rd32(args + ARGS_PARTY));
    slot = S->selection;
    if (slot >= 6u)
        slot = 0;
    else if (slot >= count)
        slot = count ? count - 1 : 0;
    wr32(args + ARGS_CHECK, owner + OWNER_CHECK_DATA);
    wr8(args + ARGS_SLOT, slot); /* before the overlay manager runs the party init */
    /* Route through our guarded launch wrapper exactly as Unk1's BL hook did,
       so the rebuilt Party owner is rebound before the overlay runs. */
    sgp_box_launch_app((void *)field, (void *)PARTY_TEMPLATE, (void *)args);
    S->selection = slot;
    wr32(owner + OWNER_EXIT_ENV, args);
    wr32(owner + OWNER_EXIT_FUNC, N_NATIVE_CALLBACK);
    wr16(owner + OWNER_STATE, START_MENU_WAIT_APP);
    return 0;
}

#include "party_ui.c"
