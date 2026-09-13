/* GPL-3.0-or-later. Private gate only: no guide UI or game-state writes.
 * The builder owns/zeros [0x01FF9F00,0x01FFA000), outside code, and raises
 * the actual ITCM arenaLow to 0x01FFA000. The first 64 bytes are test results.
 */
#include "lease.c"
#define RESULT ((volatile u32 *)0x01FF9F00)

enum { MAGIC,CYCLES,ALLOCS,FREES,NULLS,NOOPS,ERRORS,LIVE,WORDS,FIRST,HEAP,SUMMARY,
       COUNT_BEFORE,COUNT_AFTER,BYTES,LAST };

static void verify(volatile u32 *block, u32 seed)
{
    for (u32 i=0;i<LEASE_BYTES/4;i++) {
        if (block[i] != (seed ^ i)) RESULT[ERRORS] |= 4;
        RESULT[WORDS]++;
    }
}

__attribute__((used,noinline,section(".text")))
int probe_start(u8 *summary)
{
    u32 rawnew=*(volatile u32 *)0x021D1148;
    u32 keys=*(volatile u32 *)0x021D1154;
    u32 repeated=*(volatile u32 *)0x021D1158;
    if (!(rawnew&8) || (keys&0x307) || (repeated&0xF0)
        || summary[0x7BC]!=1 || (summary[0x7BF]>>4)==1) return 0;
    RESULT[MAGIC]=0x4C534531;
    RESULT[SUMMARY]=(u32)summary;
    RESULT[BYTES]=LEASE_BYTES;
    Lease first={summary_heap(),(volatile u32 *)0};
    Lease second={first.heap,(volatile u32 *)0};
    if (!first.heap) { RESULT[ERRORS]|=1; return 1; }
    RESULT[HEAP]=(u32)first.heap;
    u16 *counts=*(u16 **)0x021D1590;
    if (!ram_range((u32)counts,40)) { RESULT[ERRORS]|=1; return 1; }
    RESULT[COUNT_BEFORE]=counts[19];
    if (!lease_release(&first)) RESULT[NOOPS]++;
    if (!lease_acquire(&first)) { RESULT[ERRORS]|=2; return 1; }
    RESULT[ALLOCS]++;
    RESULT[LIVE]=(u32)first.block;
    if (!RESULT[FIRST]) RESULT[FIRST]=(u32)first.block;
    RESULT[LAST]=(u32)first.block;
    u32 start=*(u32 *)(first.heap+0x18),end=*(u32 *)(first.heap+0x1c);
    if (((u32)first.block&3) || (u32)first.block<start+16
        || (u32)first.block>end-LEASE_BYTES) RESULT[ERRORS]|=8;
    else {
        u32 seed=0xA56C1234 ^ RESULT[CYCLES];
        for (u32 i=0;i<LEASE_BYTES/4;i++) first.block[i]=seed ^ i;
        verify(first.block,seed);
        if (!lease_acquire(&second)) RESULT[NULLS]++;
        else { RESULT[ERRORS]|=16; lease_release(&second); }
        verify(first.block,seed);
    }
    if (lease_release(&first)) RESULT[FREES]++;
    RESULT[LIVE]=(u32)first.block;
    if (!lease_release(&first)) RESULT[NOOPS]++;
    RESULT[COUNT_AFTER]=counts[19];
    RESULT[CYCLES]++;
    return 1;
}

/* Wrap r5 input hook, preserving its code and ABI. Internal Thumb BL uses
 * the original strict .text loader; fallback tail-calls intact r5 entry. */
__attribute__((naked,used,section(".text")))
void eviv_hook(void)
{
    __asm__ volatile(
        "push {r0-r3, lr}\n"
        "sub sp, #4\n"
        "bl probe_start\n"
        "cmp r0, #0\n"
        "beq 1f\n"
        "add sp, #4\n"
        "pop {r0-r3}\n"
        "pop {r3}\n"
        "movs r0, #2\n"
        "bx r3\n"
        "1:\n"
        "add sp, #4\n"
        "pop {r0-r3}\n"
        "pop {r3}\n"
        "mov lr, r3\n"
        "ldr r3, 2f\n"
        "bx r3\n"
        ".balign 4\n"
        "2: .word 0x01FF883D\n"
    );
}
