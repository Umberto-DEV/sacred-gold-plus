/* Native event bank 3F00..3FFF. SaveVarsFlags vars 415E..416F are reserved.
 * No side-sector/journal dependency, save-layout change or Pal Pad writes.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define TAG 0x31304648u /* little-endian "HF01", exact version 1 */
#define TAIL 0x2BCu
#define LEGACY 0xAC0u
#define CONFIG ((const u32 *)0x023CFEF0u)
#define ORIGINAL ((u8 *(*)(void *, u16))0x023CFE81u)
#define ARRAY ((void *(*)(void *, int))0x020272C9u)
#define RESET ((void (*)(u32))0x020D3B84u) /* ARM entry, noreturn SDK */

/* Read-only ownership check. Zero permits first-access migration; HF01 owns
 * the complete bitmap. Every other nonzero encoding is foreign/future. */
int sgp_event_flags_valid(const void *state) {
    const volatile u8 *p = (const volatile u8 *)state + TAIL;
    unsigned i;
    if (*(const volatile u32 *)p == TAG) return 1;
    for (i = 0; i < 36; ++i) if (p[i]) return 0;
    return 1;
}

__attribute__((noreturn)) static void refuse(void) {
    RESET(0);
    for (;;) {} /* Never resume an event even if the SDK unexpectedly returns. */
}

u8 *sgp_event_flags_get(void *state, u16 id) {
    volatile u8 *p;
    unsigned i;
    if (id < 0x3F00 || id >= 0x4000) return ORIGINAL(state, id);
    p = (volatile u8 *)state + TAIL;
    if (*(volatile u32 *)p != TAG) {
        if (!sgp_event_flags_valid(state)) refuse();
        /* Snapshot every legacy bit before the caller's first Set/Clear.
         * Volatile stores keep the exact tag publication after the full copy. */
        for (i = 0; i < 32; ++i)
            p[4 + i] = ((const volatile u8 *)state)[LEGACY + i];
        *(volatile u32 *)p = TAG;
    }
    return (u8 *)(p + 4 + ((id - 0x3F00) >> 3));
}

int sgp_event_flags_load(void *save) {
    int result;
    if (!sgp_event_flags_valid(ARRAY(save, 4))) return 0;
    result = ((int (*)(void *))CONFIG[0])(save);
    if (!result) return result;
    return sgp_event_flags_valid(ARRAY(save, 4)) ? result : 0;
}
