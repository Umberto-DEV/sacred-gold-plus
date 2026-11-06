@ Resident stub of the rematch module (64 bytes, lives in c8.module-stubs). The module is not resident: it is overlay 126,
@ loaded on demand, called and unloaded in the same call. Derived from the measured example of the memory proposal
@ (local/notes/cc-integration-regressions/memory-c8/stub-example.S, r2).
@
@ HandleLoadOverlay marks the registry entry active BEFORE loading and, when the load fails, returns 0 WITHOUT clearing it
@ (0x0200709C..A6): left active, it would stop any overlay touching the window (the battle, overlay 12) from loading until a
@ reset. The stub therefore calls UnloadOverlayByID(ID) on every path that did not run the module to completion, and also
@ after a successful run: refused (window busy), failed, inert and successful calls all leave the entry free.
@
@ Contract: the seam BL (0x0207363A) enters with r0 = trainer id, r1 = buffer, r4/r6/r7 live; r4-r7 are never written (r3 is the
@ scratch register: the module's hook reads the host's r4 = BattleSetup) and SP is restored; the native reader's result is in r0. Module refused or load failed -> the NATIVE reader runs, no variant.
@ The stub pushes 16 bytes; the module's hook adds them to its host-SP offset (REMATCH_HOST_SP_OFFSET).
@ Parameters: ID overlay id, ENTRY module entry (Thumb, bit 0 set), NATIVE reader thunk (Thumb), HLO HandleLoadOverlay (Thumb),
@ ULO UnloadOverlayByID (Thumb).
    .syntax unified
    .thumb
    .text
    .global c8_stub
    .thumb_func
c8_stub:
    push  {r0, r1, r2, lr}
    movs  r0, #ID
    movs  r1, #0                   @ OVY_LOAD_NORMAL
    ldr   r3, =HLO
    blx   r3
    cmp   r0, #0
    beq   1f
    ldr   r0, [sp, #0]             @ the host's trainer id and buffer, untouched
    ldr   r1, [sp, #4]
    ldr   r3, =ENTRY
    blx   r3                       @ module: the native reader (once) and, when every gate agrees, the variant
    b     2f
1:  ldr   r0, [sp, #0]             @ refused or failed: the native reader, no variant
    ldr   r1, [sp, #4]
    ldr   r3, =NATIVE
    blx   r3
2:  str   r0, [sp, #0]             @ the reader's result goes back to the seam
    movs  r0, #ID                  @ free the entry on every path (success, refusal, failure, inert module)
    ldr   r3, =ULO
    blx   r3
    pop   {r0, r1, r2, pc}
    .ltorg
