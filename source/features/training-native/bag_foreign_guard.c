/* SG-BAG-FOREIGN: lossless-save guard without moving the Training ABI.
 *
 * The installed V4 hooks and Settings/Shiny descriptors retain every Training
 * entry address.  The stage therefore redirects only the first eight bytes of
 * training_save to this appended Thumb payload.  The assembly entry reproduces
 * those displaced instructions exactly, runs the new read-only veto, and then
 * resumes at training_save+8.  No Bag byte, save layout or public capability
 * address changes.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define R32(p,o) (*(volatile u32 *)((u8 *)(p)+(o)))
#define BAG_STATE ((void *)0x023DD700u)
#define BAG_SLOTS ((volatile u16 *)0x023DD714u)
#define BAG_STATUS ((void *)0x023DE9C4u)
#define BAG_MAGIC 0x43415042u

static __attribute__((used,noinline)) int bag_foreign_should_block(void *manager)
{
    u32 index;
    u32 status;

    if (R32(manager, 0x14) || R32(manager, 8)) {
        return 0;
    }
    status = R32(BAG_STATUS, 0);
    /* 2: foreign destination; 3: no usable copy; 4: unreadable flash.
     * Each leaves no durable destination copy for live extra cells.  Status 5
     * is deliberately allowed because one verified copy survived. */
    if (R32(BAG_STATE, 0) != BAG_MAGIC || status < 2u || status > 4u) {
        return 0;
    }
    for (index = 0; index < 594u; index++) {
        if ((index >= 165u && index < 252u) ||
            (index >= 292u && index < 294u) ||
            (index >= 318u && index < 324u) || index == 425u ||
            (index >= 490u && index < 492u) ||
            (index >= 584u && index < 594u)) {
            if (BAG_SLOTS[index * 2u] || BAG_SLOTS[index * 2u + 1u]) {
                return 1;
            }
        }
    }
    return 0;
}

__attribute__((naked,used)) void bag_foreign_guard(void)
{
    __asm__ volatile(
        "push {r4,r5,r6,r7,lr}\n"
        "sub sp,#60\n"
        "movs r4,r1\n"
        "str r0,[sp,#24]\n"
        "movs r0,r4\n"
        "bl bag_foreign_should_block\n"
        "cmp r0,#0\n"
        "beq 1f\n"
        "movs r0,#3\n"
        "add sp,#60\n"
        "pop {r4,r5,r6,r7,pc}\n"
        "1:\n"
        "ldr r0,[sp,#24]\n"
        "ldr r3,=0x023D14E5\n"
        "bx r3\n"
        ".ltorg\n"
    );
}
