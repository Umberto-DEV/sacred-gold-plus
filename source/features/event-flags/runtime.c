/* Native event bank 3F00..3FFF plus the finite 612E..6139/619E..61A9
 * story-gate family. Save layout, chunk IDs and Chatot bytes stay unchanged.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define TAG1 0x31304648u /* little-endian "HF01" */
#define TAG2 0x32304648u /* little-endian "HF02" */
#define TAIL 0x2BCu
#define LEGACY 0xAC0u
#define CONFIG ((const u32 *)0x023CFEF0u)
#define ORIGINAL_FLAG ((u8 *(*)(void *, u16))0x023CFE81u)
#define ORIGINAL_VAR_GET ((u16 (*)(void *, u16))0x023CFE95u)
#define ORIGINAL_SET_VAR ((int (*)(void *))0x023CFEA9u)
#define ARRAY ((void *(*)(void *, int))0x020272C9u)
#define RESET ((void (*)(u32))0x020D3B84u) /* ARM entry, noreturn SDK */

/* These are unused native high-bank bits in the exact guarded inputs. The
 * installer rejects new literal owners in all field/event/Frontier archives. */
static unsigned family_bit(unsigned index) {
    if (!index) return 3;
    if (index < 3) return index + 5;
    if (index < 18) return index + 6;
    if (index < 21) return index + 11;
    return index + 17;
}

static unsigned chatot_offset(unsigned index) {
    if (index < 12) return 0x1CC + index * 2;
    return 0x2AC + (index - 12) * 2;
}

static int family_index(u16 id) {
    if (id >= 0x612E && id < 0x613A) return id - 0x612E;
    if (id >= 0x619E && id < 0x61AA) return id - 0x619E + 12;
    return -1;
}

__attribute__((noreturn)) static void refuse(void) {
    RESET(0);
    for (;;) {} /* Never resume an event if the SDK unexpectedly returns. */
}

/* Zero permits a pre-load/new-game migration. HF01 and HF02 are the only
 * owned versions. Every other nonzero encoding is foreign/future. */
int sgp_event_flags_valid(const void *state) {
    const volatile u8 *p = (const volatile u8 *)state + TAIL;
    u32 tag = *(const volatile u32 *)p;
    unsigned i;
    if (tag == TAG1 || tag == TAG2) return 1;
    for (i = 0; i < 36; ++i) if (p[i]) return 0;
    return 1;
}

static void set_bit(volatile u8 *bank, unsigned bit, int value) {
    u8 mask = (u8)(1u << (bit & 7));
    if (value) bank[bit >> 3] |= mask;
    else bank[bit >> 3] &= (u8)~mask;
}

static int get_bit(const volatile u8 *bank, unsigned bit) {
    return (bank[bit >> 3] >> (bit & 7)) & 1;
}

static void migrate(void *state, const void *chatot) {
    volatile u8 *p = (volatile u8 *)state + TAIL;
    u32 tag = *(volatile u32 *)p;
    unsigned i;
    if (tag == TAG2) return;
    if (tag != TAG1) {
        if (tag || !sgp_event_flags_valid(state)) refuse();
        for (i = 0; i < 32; ++i)
            p[4 + i] = ((const volatile u8 *)state)[LEGACY + i];
    }
    for (i = 0; i < 24; ++i) {
        u16 value = *(const volatile u16 *)((const volatile u8 *)chatot + chatot_offset(i));
        set_bit(p + 4, family_bit(i), value != 0);
    }
    *(volatile u32 *)p = TAG2; /* publish only after both imports complete */
}

/* New Game can read or set a story gate before touching any high event flag.
 * All three entry points must initialize the same bank on that first access. */
static void ensure_new_game_bank(void *state) {
    volatile u8 *p = (volatile u8 *)state + TAIL;
    unsigned i;
    if (*(volatile u32 *)p == TAG2) return;
    if (*(volatile u32 *)p == TAG1 || !sgp_event_flags_valid(state)) refuse();
    for (i = 0; i < 32; ++i)
        p[4 + i] = ((const volatile u8 *)state)[LEGACY + i];
    for (i = 0; i < 24; ++i) set_bit(p + 4, family_bit(i), 0);
    *(volatile u32 *)p = TAG2;
}

u8 *sgp_event_flags_get(void *state, u16 id) {
    volatile u8 *p;
    if (id < 0x3F00 || id >= 0x4000) return ORIGINAL_FLAG(state, id);
    p = (volatile u8 *)state + TAIL;
    ensure_new_game_bank(state);
    return (u8 *)(p + 4 + ((id - 0x3F00) >> 3));
}

u16 sgp_event_vars_get(void *state, u16 id) {
    int index = family_index(id);
    volatile u8 *p = (volatile u8 *)state + TAIL;
    if (index < 0) return 0xFFFF;
    ensure_new_game_bank(state);
    return get_bit(p + 4, family_bit(index)) ? 2 : 0;
}

int sgp_event_vars_set(void *state, u16 id, u16 value) {
    int index = family_index(id);
    volatile u8 *p = (volatile u8 *)state + TAIL;
    if (index < 0 || (value != 0 && value != 2)) return 0;
    ensure_new_game_bank(state);
    set_bit(p + 4, family_bit(index), value != 0);
    return 1;
}

u16 sgp_field_var_get(void *field, u16 id) {
    if (family_index(id) >= 0) {
        void *save = *(void **)((u8 *)field + 12);
        return sgp_event_vars_get(ARRAY(save, 4), id);
    }
    return ORIGINAL_VAR_GET(field, id);
}

int sgp_script_set_var(void *context) {
    const u8 *script = *(const u8 **)((u8 *)context + 8);
    u16 id = (u16)(script[0] | script[1] << 8);
    if (family_index(id) >= 0) {
        u16 value = (u16)(script[2] | script[3] << 8);
        void *field = *(void **)((u8 *)context + 0x80);
        void *save = *(void **)((u8 *)field + 12);
        if (!sgp_event_vars_set(ARRAY(save, 4), id, value)) refuse();
        *(const u8 **)((u8 *)context + 8) = script + 4;
        return 0;
    }
    return ORIGINAL_SET_VAR(context);
}

int sgp_event_flags_load(void *save) {
    void *state = ARRAY(save, 4);
    int result;
    if (!sgp_event_flags_valid(state)) return 0;
    result = ((int (*)(void *))CONFIG[0])(save);
    if (!result) return result;
    state = ARRAY(save, 4);
    if (!sgp_event_flags_valid(state)) return 0;
    migrate(state, ARRAY(save, 18));
    return result;
}
