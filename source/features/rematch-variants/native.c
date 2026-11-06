/* Wrapper for the native trainer-party reader call at 0x0207363A.
 *
 * The seam is the BL to TrainerData_ReadTrPoke inside CreateNPCTrainerParty:
 * the host has just allocated the 108-byte transient party buffer and has not
 * interpreted any member yet. The wrapper calls the original reader exactly
 * once and then, only when every gate agrees, lets the core replace the whole
 * buffer with a complete authored party. Everything else is native.
 *
 * Gates (all must hold, any doubt leaves the native buffer untouched):
 *   - config image valid and its activation byte set (default 0 = pure forward);
 *   - Plus option byte 0x023D8700 == 1;
 *   - enemy party index in the config mask and BattleSetup.battleType equal to
 *     one of the exact whitelisted values (runtime values still to be proven);
 *   - the host frame agrees with the arguments (buffer pointer, trainer id);
 *   - trainer 712/713, type 3, six members and the exact baseline bytes (core).
 * The RNG is never read or advanced: the selector uses the seed the host has
 * already saved at [sp+0x68]. */
#include "variants.c"
#ifndef REMATCH_CONFIG_ADDR
#error "REMATCH_CONFIG_ADDR (assigned address of the config image) is required"
#endif
#ifndef REMATCH_CONFIG_BYTES
#error "REMATCH_CONFIG_BYTES (size of the config allocation, the bound enforced at runtime) is required"
#endif
#ifndef REMATCH_HOST_SP_OFFSET
#error "REMATCH_HOST_SP_OFFSET (host SP at the seam above the hook's own 32-byte frame; 32 + the resident stub's frame) is required"
#endif
#define RV_STR2(x) #x
#define RV_STR(x) RV_STR2(x)
/* Like the documented contract, the Plus byte is 0 or 1 and only 1 enables the variants. The native level
 * function treats every non-zero value as Plus; the byte is never written with another value. */
#define REMATCH_PLUS (*(const volatile rv_u8 *)0x023D8700u)

__attribute__((used,noinline))
void rematch_native(const rv_u8 *setup, const rv_u32 *host, rv_u32 trainer, rv_u8 *buffer) {
    const RvHeader *config = (const RvHeader *)REMATCH_CONFIG_ADDR;
    const rv_u8 *data;
    rv_u32 index, i, allowed = 0;
    if (config->magic != RV_MAGIC || config->active != 1u || config->battle_type_count > 2u ||
        REMATCH_PLUS != 1u || !setup || !host || !buffer) return;
    index = host[0x10 / 4];
    if (index >= 4u || !((config->enemy_index_mask >> index) & 1u) ||
        host[0x74 / 4] != (rv_u32)(rv_uptr)buffer ||
        *(const rv_u32 *)(setup + 0x18 + index * 4u) != trainer) return;
    for (i = 0; i < config->battle_type_count; i++)
        if (*(const rv_u32 *)setup == config->battle_types[i]) allowed = 1;
    if (!allowed) return;
    data = setup + 0x28 + index * 52u;
    rematch_apply(buffer, trainer, ((rv_u32)data[0] << 8) | data[3], REMATCH_PLUS,
                  host[0x68 / 4], config, REMATCH_CONFIG_BYTES);
}

/* Entered from the resident stub (which the BL at 0x0207363A reaches) with the loader's own arguments (r0 trainer id,
 * r1 buffer) and the host's r4/r6/r7 live. Eight words are pushed (SP stays 8-byte aligned); host SP at the seam is
 * therefore SP + 32 + the stub's own frame (REMATCH_HOST_SP_OFFSET). The native reader is called once, its r0 is
 * handed back to the stub, and execution resumes at 0x0207363E. */
__attribute__((naked,used))
void rematch_hook(void) {
    __asm__ volatile(
        "push {r0,r1,r2,r4,r5,r6,r7,lr}\n"
        "ldr r3,=0x020735E9\n"
        "blx r3\n"
        "movs r5,r0\n"
        "movs r0,r4\n"
        "mov r1,sp\n"
        "adds r1,#" RV_STR(REMATCH_HOST_SP_OFFSET) "\n"
        "ldr r2,[sp,#0]\n"
        "ldr r3,[sp,#4]\n"
        "bl rematch_native\n"
        "str r5,[sp,#0]\n"
        "pop {r0,r1,r2,r4,r5,r6,r7,pc}\n"
        ".ltorg\n");
}
