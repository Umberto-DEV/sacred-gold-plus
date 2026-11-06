    .syntax unified
    .thumb
    .section .text,"ax",%progbits

    /*
     * HG-B05 wrappers for the two pure held-item getters in TryItemFlinch.
     *
     * The pivot script saves one per-battle-context word in the outgoing
     * battler's SelfTurnData.shellBellDamage after Shell Bell/Life Orb have
     * already been processed. Bit 16 marks the snapshot; byte 0 is the
     * effective hold effect and byte 1 its modifier. The modifier wrapper
     * consumes the word. With no marker both wrappers pass through the exact
     * retail getters, preserving the ordinary call and RNG order.
     */
    .global uturn_snapshot_effect
    .type uturn_snapshot_effect,%function
    .thumb_func
uturn_snapshot_effect:
    push    {lr}
    movs    r2, #0x1c
    muls    r2, r1, r2
    adds    r2, r0, r2
    movs    r3, #0xbb
    lsls    r3, r3, #2
    ldr     r2, [r2, r3]
    lsls    r3, r2, #15
    bpl     .Leffect_live
    movs    r0, #0xff
    ands    r0, r2
    pop     {pc}
.Leffect_live:
    .global uturn_effect_live_call
uturn_effect_live_call:
    .hword  0xf000, 0xf800
    pop     {pc}

    .balign 4
    .global uturn_snapshot_modifier
    .type uturn_snapshot_modifier,%function
    .thumb_func
uturn_snapshot_modifier:
    push    {r4, lr}
    movs    r3, #0x1c
    muls    r3, r1, r3
    adds    r3, r0, r3
    movs    r2, #0xbb
    lsls    r2, r2, #2
    ldr     r1, [r3, r2]
    lsls    r4, r1, #15
    bpl     .Lmodifier_live
    movs    r4, #0
    str     r4, [r3, r2]
    lsrs    r0, r1, #8
    lsls    r0, r0, #24
    lsrs    r0, r0, #24
    pop     {r4, pc}
.Lmodifier_live:
    .global uturn_modifier_live_call
uturn_modifier_live_call:
    .hword  0xf000, 0xf800
    pop     {r4, pc}
