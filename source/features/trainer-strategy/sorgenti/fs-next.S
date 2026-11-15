/* Recovered FSi_NextCommand; attribution recipe, no installer.
 * FS_archive_prefix.c at cb614ad23449d5852b40321dc409c4143872b35c.
 * Full body includes unqualified cancel/nonempty/callback/suspend paths. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_next_command_recipe
.type native_fs_next_command_recipe,%function
native_fs_next_command_recipe:
    push {r3, r4, r5, r6, r7, r8, r9, lr}
    sub sp, sp, #0x48
    mov r6, r0
    .inst 0xeb000000 | (((0x20d3a38-(0x020d74a8+8))>>2)&0xffffff)
    ldr r1, [r6, #0x1c]
    mov r4, r0
    tst r1, #0x20
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    beq .Lpc_020d7530
    ldr r0, [r6, #0x1c]
    bic r0, r0, #0x20
    str r0, [r6, #0x1c]
    ldr r0, [r6, #0x24]
    cmp r0, #0
    beq .Lpc_020d7530
    mov r8, #0
    mov r9, #1
    mov r7, #3
.Lpc_020d74ec:
    ldr r1, [r0, #0xc]
    ldr r5, [r0, #4]
    tst r1, #2
    movne r1, r9
    moveq r1, r8
    cmp r1, #0
    beq .Lpc_020d7524
    ldr r1, [r6, #0x24]
    cmp r1, r0
    mov r1, r7
    streq r5, [r6, #0x24]
    .inst 0xeb000000 | (((0x20d6864-(0x020d7518+8))>>2)&0xffffff)
    cmp r5, #0
    ldreq r5, [r6, #0x24]
.Lpc_020d7524:
    mov r0, r5
    cmp r5, #0
    bne .Lpc_020d74ec
.Lpc_020d7530:
    ldr r0, [r6, #0x1c]
    tst r0, #0x40
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    bne .Lpc_020d7620
    ldr r0, [r6, #0x1c]
    tst r0, #8
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    bne .Lpc_020d7620
    ldr r5, [r6, #0x24]
    cmp r5, #0
    beq .Lpc_020d7620
    ldr r0, [r6, #0x1c]
    tst r0, #0x10
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    moveq r7, #1
    movne r7, #0
    cmp r7, #0
    ldrne r0, [r6, #0x1c]
    orrne r0, r0, #0x10
    strne r0, [r6, #0x1c]
    mov r0, r4
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d759c+8))>>2)&0xffffff)
    cmp r7, #0
    beq .Lpc_020d75c4
    ldr r0, [r6, #0x58]
    tst r0, #0x200
    beq .Lpc_020d75c4
    ldr r2, [r6, #0x54]
    mov r0, r5
    mov r1, #9
    blx r2
.Lpc_020d75c4:
    .inst 0xeb000000 | (((0x20d3a38-(0x020d75c4+8))>>2)&0xffffff)
    ldr r1, [r5, #0xc]
    mov r4, r0
    orr r0, r1, #0x40
    str r0, [r5, #0xc]
    ldr r0, [r5, #0xc]
    tst r0, #4
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    beq .Lpc_020d760c
    add r0, r5, #0x18
    .inst 0xeb000000 | (((0x20d1ecc-(0x020d75f4+8))>>2)&0xffffff)
    mov r0, r4
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d75fc+8))>>2)&0xffffff)
    add sp, sp, #0x48
    mov r0, #0
    pop {r3, r4, r5, r6, r7, r8, r9, pc}
.Lpc_020d760c:
    mov r0, r4
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d7610+8))>>2)&0xffffff)
    add sp, sp, #0x48
    mov r0, r5
    pop {r3, r4, r5, r6, r7, r8, r9, pc}
.Lpc_020d7620:
    ldr r0, [r6, #0x1c]
    tst r0, #0x10
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    beq .Lpc_020d766c
    ldr r0, [r6, #0x1c]
    bic r0, r0, #0x10
    str r0, [r6, #0x1c]
    ldr r0, [r6, #0x58]
    tst r0, #0x400
    beq .Lpc_020d766c
    add r0, sp, #0
    .inst 0xeb000000 | (((0x20d7f98-(0x020d7654+8))>>2)&0xffffff)
    str r6, [sp, #8]
    ldr r2, [r6, #0x54]
    add r0, sp, #0
    mov r1, #0xa
    blx r2
.Lpc_020d766c:
    ldr r0, [r6, #0x1c]
    tst r0, #0x40
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    beq .Lpc_020d769c
    ldr r1, [r6, #0x1c]
    add r0, r6, #0x14
    bic r1, r1, #0x40
    orr r1, r1, #8
    str r1, [r6, #0x1c]
    .inst 0xeb000000 | (((0x20d1ecc-(0x020d7698+8))>>2)&0xffffff)
.Lpc_020d769c:
    mov r0, r4
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d76a0+8))>>2)&0xffffff)
    mov r0, #0
    add sp, sp, #0x48
    pop {r3, r4, r5, r6, r7, r8, r9, pc}
.size native_fs_next_command_recipe,.-native_fs_next_command_recipe
