    .syntax unified
    .thumb
    .section .text,"ax",%progbits

    /*
     * SG-AI02: GetTypeEffectivnessData over the Plus 18-type chart.
     *
     * ABI is the retail helper at 0x0225260C:
     *   r0 BattleSystem*, r1 index, r2 attack*, r3 defender*, [sp] effect*
     *   return 1 for a direct row, 0 for a random row.
     *
     * The modern table has 322 dense matrix rows (Normal/Fighting -> Ghost
     * are represented by the three control rows) plus those three controls:
     * exactly 325 selectable rows before the FF terminator.  The call to the
     * native RNG is patched by the guarded producer after object relocation.
     */
    .global conversion2_type_row
    .type conversion2_type_row,%function
    .thumb_func
conversion2_type_row:
    push    {r3, r4, r5, lr}
    adds    r5, r2, #0
    adds    r4, r3, #0
    movs    r2, #1
    ldr     r3, .Lrow_count
    cmp     r1, r3
    blo     1f
    .global conversion2_random_call
conversion2_random_call:
    .hword  0xf000, 0xf800
    ldr     r1, .Lrow_count
    ldr     r3, .Ldivmod
    blx     r3
    movs    r2, #0
1:
    lsls    r0, r1, #1
    adds    r0, r1, r0
    ldr     r3, .Lmodern_chart
    adds    r3, r3, r0
    ldrb    r1, [r3, #0]
    strb    r1, [r5, #0]
    ldrb    r1, [r3, #1]
    strb    r1, [r4, #0]
    ldrb    r1, [r3, #2]
    ldr     r0, [sp, #0x10]
    strb    r1, [r0, #0]
    adds    r0, r2, #0
    pop     {r3, r4, r5, pc}

    .balign 4
.Lrow_count:
    .word   325
.Ldivmod:
    /* ARM entry: BLX must clear T exactly like the retail BLX immediate. */
    .word   0x020f2ba4
.Lmodern_chart:
    .word   0x021fbe60
