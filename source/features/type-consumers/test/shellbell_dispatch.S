.syntax unified
.cpu arm946e-s
.thumb
.section .text,"ax",%progbits

/* Owned test driver. The table is a fixture in qualification and the read-only
 * native table in a separately qualified game probe. No ROM installer exists.
 * R0=opaque BattleSystem*, R1=context with command at +8. Stop before slot39.
 */
.global shellbell_dispatch
.type shellbell_dispatch,%function
.thumb_func
shellbell_dispatch:
    push {r4, r5, r6, lr}
    adds r4, r0, #0
    adds r5, r1, #0
    ldr r6, .Ltable
.Lloop:
    ldr r2, [r5, #8]
    cmp r2, #39
    beq .Ldone
    lsls r2, r2, #2
    ldr r3, [r6, r2]
    adds r0, r4, #0
    adds r1, r5, #0
    blx r3
    b .Lloop
.Ldone:
    pop {r4, r5, r6, pc}
.balign 4
.Ltable:
    .word 0x0226CA90
.size shellbell_dispatch, .-shellbell_dispatch

/* Owned handlers used only for ROM-free dispatcher qualification. */
.global shellbell_owned_first
.type shellbell_owned_first,%function
.thumb_func
shellbell_owned_first:
    movs r0, #29
    str r0, [r1, #8]
    bx lr
.size shellbell_owned_first, .-shellbell_owned_first

.global shellbell_owned_second
.type shellbell_owned_second,%function
.thumb_func
shellbell_owned_second:
    movs r0, #39
    str r0, [r1, #8]
    bx lr
.size shellbell_owned_second, .-shellbell_owned_second
