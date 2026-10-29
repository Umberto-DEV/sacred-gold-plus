/* Only the transient trainer-party buffer is edited; the archive stays intact. */
#include "strategy.c"
#define STRATEGY_CONFIG ((const StrategyHeader *)0x023D6600u)
#define PLUS_ACTIVE (*(const volatile st_u8 *)0x023D8700u)
__attribute__((used,noinline))
void strategy_native(void *battle, st_u32 trainer_offset, st_u8 *buffer) {
    st_u32 index = 0, offset = trainer_offset;
    const st_u8 *bytes = battle;
    if (!battle || trainer_offset > 3u * 52u) return;
    while (offset >= 52) { offset -= 52; index++; }
    if (offset) return;
    const st_u8 *data = bytes + 0x28 + trainer_offset;
    st_u32 id = *(const st_u32 *)(bytes + 0x18 + index * 4);
    strategy_apply(buffer, id, data[0] | (data[3] << 8), PLUS_ACTIVE, STRATEGY_CONFIG);
}

/* Same host stack and live registers as the original level hook. The latter
 * still calculates levels and finishes with the original flag-setting ADD. */
__attribute__((naked,used))
void strategy_hook(void) {
    __asm__ volatile(
        "push {r0,r1,r2,r3,r4,r5,r6,lr}\n"
        "movs r0,r4\n"
        "movs r1,r5\n"
        "ldr r2,[sp,#0x94]\n"
        "bl strategy_native\n"
        "ldr r0,[sp,#28]\n"
        "mov lr,r0\n"
        "pop {r0,r1,r2,r3,r4,r5,r6}\n"
        "add sp,#4\n"
        "ldr r0,=0x023D8195\n"
        "bx r0\n");
}
