    .syntax unified
    .thumb
    .section .text,"ax",%progbits

    /*
     * SG-AI01: make the trainer AI see only the Fairy row/column that is
     * absent from its retail sparse type chart.  All non-Fairy pairs fall
     * through unchanged to the native result already computed by overlay 12.
     *
     * The two calls to the native flag combiner are deliberately emitted as
     * placeholders.  The guarded producer fixes them to 0x022521C9 after the
     * object loader has relocated the internal Thumb calls.
     */

    .global fairy_flags_hook
    .type fairy_flags_hook,%function
    .thumb_func
fairy_flags_hook:
    ldr     r4, [sp, #0x0c]
    ldr     r5, [sp, #0x30]
    push    {lr}

    adds    r0, r4, #0
    adds    r1, r5, #0
    bl      fairy_code
    cmp     r0, #2
    beq     1f
    movs    r2, #5
    muls    r0, r2
    adds    r1, r6, #0
    .global fairy_apply_call_1
fairy_apply_call_1:
    .hword  0xf000, 0xf800
1:
    ldr     r1, [sp, #0x38]
    cmp     r1, r5
    beq     2f
    adds    r0, r4, #0
    bl      fairy_code
    cmp     r0, #2
    beq     2f
    movs    r2, #5
    muls    r0, r2
    adds    r1, r6, #0
    .global fairy_apply_call_2
fairy_apply_call_2:
    .hword  0xf000, 0xf800
2:
    movs    r4, #0
    movs    r0, #0
    pop     {pc}

    .global fairy_scalar_tail
    .type fairy_scalar_tail,%function
    .thumb_func
fairy_scalar_tail:
    adds    r4, r1, #0
    ldr     r7, [sp]
    adds    r0, r7, #0
    adds    r1, r5, #0
    bl      fairy_code
    muls    r4, r0
    cmp     r5, r6
    beq     4f
    adds    r0, r7, #0
    adds    r1, r6, #0
    bl      fairy_code
    muls    r4, r0
    lsrs    r4, r4, #1
4:
    lsrs    r0, r4, #1
    pop     {r3, r4, r5, r6, r7, pc}

    .type fairy_code,%function
    .thumb_func
fairy_code:
    adr     r2, .Lfairy_codes
    cmp     r0, #9
    beq     5f
    cmp     r1, #9
    bne     6f
    adds    r0, #18
    b       7f

    /* Two 18-entry 2-bit vectors, packed into the control-flow hole. */
    .balign 4
.Lfairy_codes:
    .byte 0x6e,0xaa,0x99,0xaa,0x6f,0xae,0xb9,0xaa,0x4a
    .balign 2
5:
    adds    r0, r1, #0
7:
    adds    r3, r0, #0
    lsrs    r0, r0, #2
    ldrb    r0, [r2, r0]
    movs    r2, #3
    ands    r3, r2
    lsls    r3, r3, #1
    lsrs    r0, r3
    ands    r0, r2
    cmp     r0, #3
    bne     8f
    adds    r0, #1
8:
    bx      lr
6:
    movs    r0, #2
    bx      lr
