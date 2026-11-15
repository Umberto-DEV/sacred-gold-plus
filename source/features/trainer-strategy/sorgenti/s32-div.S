/* Recovered comparison recipe for MSL _s32_div_f, not an installer.
 * Pinned msl_fp_runtime.c @s32_div_f..@u32_div_f; original compiler absent.
 * The builder expands this sole .rept and compares every instruction/label
 * with that authenticated source before invoking the assembler. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_s32_div_recipe
.type native_s32_div_recipe,%function
native_s32_div_recipe:
    eor r12, r0, r1
    and r12, r12, #0x80000000
    cmp r0, #0
    rsblt r0, r0, #0
    addlt r12, r12, #1
    cmp r1, #0
    rsblt r1, r1, #0
    beq .L020F2B90
    cmp r0, r1
    movlo r1, r0
    movlo r0, #0
    blo .L020F2B90
    mov r2, #0x1c
    mov r3, r0, lsr #4
    cmp r1, r3, lsr #12
    suble r2, r2, #0x10
    movle r3, r3, lsr #0x10
    cmp r1, r3, lsr #4
    suble r2, r2, #8
    movle r3, r3, lsr #8
    cmp r1, r3
    suble r2, r2, #4
    movle r3, r3, lsr #4
    mov r0, r0, lsl r2
    rsb r1, r1, #0
    adds r0, r0, r0
    add r2, r2, r2, lsl #1
    add pc, pc, r2, lsl #2
    nop
    .rept 32
    adcs r3, r1, r3, lsl #1
    sublo r3, r3, r1
    adcs r0, r0, r0
    .endr
    mov r1, r3
.L020F2B90:
    ands r3, r12, #0x80000000
    rsbne r0, r0, #0
    ands r3, r12, #1
    rsbne r1, r1, #0
    bx lr
.size native_s32_div_recipe,.-native_s32_div_recipe
