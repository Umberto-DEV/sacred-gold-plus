    .syntax unified
    .thumb
    .section .text,"ax",%progbits

    /*
     * HG-B08: preserve Transform's copied combat stats across a level-up.
     *
     * ABI is the retail BattleSystem_ReloadMonData at 0x0224EA14.  Transform
     * copies species, five stats, moves, types, form and ability, but not
     * level/friendship/HP.  Therefore only the five stat reads are skipped
     * while STATUS2_TRANSFORM is set.  The common fields still reload, and
     * the retail Transform and Mimic guards for moves/PP/experience remain.
     */
    .global reload_mon_data
    .type reload_mon_data,%function
    .thumb_func
reload_mon_data:
    push    {r4, r5, r6, r7, lr}
    sub     sp, #4
    adds    r4, r1, #0
    adds    r5, r2, #0
    str     r3, [sp]
    adds    r1, r5, #0
    ldr     r2, [sp]
    bl      .Lget_party_mon
    adds    r6, r0, #0
    movs    r3, #0xc0
    muls    r3, r5, r3
    ldr     r2, .Lbattle_mons
    adds    r7, r4, r3
    adds    r7, r7, r2

    ldr     r0, [r7, #0x70]
    movs    r1, #2
    lsls    r1, r1, #20
    tst     r0, r1
    bne     .Lcommon

    adds    r0, r6, #0
    movs    r1, #165
    movs    r2, #0
    bl      .Lget_mon_data
    strh    r0, [r7, #2]
    adds    r0, r6, #0
    movs    r1, #166
    movs    r2, #0
    bl      .Lget_mon_data
    strh    r0, [r7, #4]
    adds    r0, r6, #0
    movs    r1, #167
    movs    r2, #0
    bl      .Lget_mon_data
    strh    r0, [r7, #6]
    adds    r0, r6, #0
    movs    r1, #168
    movs    r2, #0
    bl      .Lget_mon_data
    strh    r0, [r7, #8]
    adds    r0, r6, #0
    movs    r1, #169
    movs    r2, #0
    bl      .Lget_mon_data
    strh    r0, [r7, #10]

.Lcommon:
    adds    r0, r6, #0
    movs    r1, #161
    movs    r2, #0
    bl      .Lget_mon_data
    adds    r3, r7, #0
    adds    r3, #52
    strb    r0, [r3]
    adds    r0, r6, #0
    movs    r1, #9
    movs    r2, #0
    bl      .Lget_mon_data
    adds    r3, r7, #0
    adds    r3, #53
    strb    r0, [r3]
    adds    r0, r6, #0
    movs    r1, #163
    movs    r2, #0
    bl      .Lget_mon_data
    str     r0, [r7, #76]
    adds    r0, r6, #0
    movs    r1, #164
    movs    r2, #0
    bl      .Lget_mon_data
    str     r0, [r7, #80]

    ldr     r0, [r7, #0x70]
    movs    r1, #2
    lsls    r1, r1, #20
    tst     r0, r1
    bne     .Ldone

    adds    r0, r7, #0
    adds    r0, #0x8c
    ldr     r5, [r0]
    lsls    r5, r5, #26
    lsrs    r5, r5, #28
    movs    r4, #0
.Lmove_loop:
    movs    r0, #1
    lsls    r0, r0, r4
    tst     r0, r5
    bne     .Lnext_move

    adds    r0, r6, #0
    adds    r1, r4, #0
    adds    r1, #54
    movs    r2, #0
    bl      .Lget_mon_data
    lsls    r3, r4, #1
    adds    r3, #12
    strh    r0, [r7, r3]

    adds    r0, r6, #0
    adds    r1, r4, #0
    adds    r1, #58
    movs    r2, #0
    bl      .Lget_mon_data
    adds    r3, r4, #0
    adds    r3, #44
    strb    r0, [r7, r3]

    adds    r0, r6, #0
    adds    r1, r4, #0
    adds    r1, #62
    movs    r2, #0
    bl      .Lget_mon_data
    adds    r3, r4, #0
    adds    r3, #48
    strb    r0, [r7, r3]

.Lnext_move:
    adds    r4, r4, #1
    cmp     r4, #4
    blt     .Lmove_loop
    adds    r0, r6, #0
    movs    r1, #8
    movs    r2, #0
    bl      .Lget_mon_data
    str     r0, [r7, #100]

.Ldone:
    add     sp, #4
    pop     {r4, r5, r6, r7, pc}

.Lget_party_mon:
    ldr     r3, .Lparty_target
    bx      r3
.Lget_mon_data:
    ldr     r3, .Ldata_target
    bx      r3

    .balign 4
.Lbattle_mons:
    .word   0x00002d40
.Lparty_target:
    .word   0x0223a881
.Ldata_target:
    .word   0x0206e541

    .space  340 - (. - reload_mon_data), 0
