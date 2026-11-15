/* Recovered native SendCommand, attribution artifact with no installer.
 * fs_send_command.c counterpart at cb614ad23449d5852b40321dc409c4143872b35c.
 * Includes unexercised paths: runtime qualification must name its finite gates.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_send_command_recipe
.type native_fs_send_command_recipe,%function
native_fs_send_command_recipe:
    push {r3, r4, r5, r6, r7, lr}
    mov r6, r0
    ldr r4, [r6, #8]
    mov r2, #1
    str r1, [r6, #0x10]
    mov r0, #2
    str r0, [r6, #0x14]
    ldr r0, [r6, #0xc]
    lsl r7, r2, r1
    orr r0, r0, #1
    str r0, [r6, #0xc]
    .inst 0xeb000000 | (((0x20d3a38-(0x020d77b4+8))>>2)&0xffffff)
    ldr r1, [r4, #0x1c]
    mov r5, r0
    tst r1, #0x80
    beq .Lpc_020d77e4
    mov r0, r6
    mov r1, #3
    .inst 0xeb000000 | (((0x20d6864-(0x020d77d0+8))>>2)&0xffffff)
    mov r0, r5
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d77d8+8))>>2)&0xffffff)
    mov r0, #0
    pop {r3, r4, r5, r6, r7, pc}
.Lpc_020d77e4:
    tst r7, #0x1fc
    ldrne r0, [r6, #0xc]
    orrne r0, r0, #4
    strne r0, [r6, #0xc]
    ldr r1, [r6]
    ldr r2, [r6, #4]
    cmp r1, #0
    strne r2, [r1, #4]
    cmp r2, #0
    add r0, r4, #0x20
    strne r1, [r2]
    ldr r1, [r0, #4]
    cmp r1, #0
    beq .Lpc_020d782c
.Lpc_020d781c:
    mov r0, r1
    ldr r1, [r1, #4]
    cmp r1, #0
    bne .Lpc_020d781c
.Lpc_020d782c:
    str r6, [r0, #4]
    str r0, [r6]
    mov r1, #0
    str r1, [r6, #4]
    ldr r0, [r4, #0x1c]
    tst r0, #8
    movne r1, #1
    cmp r1, #0
    bne .Lpc_020d78dc
    ldr r0, [r4, #0x1c]
    tst r0, #0x10
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    bne .Lpc_020d78dc
    ldr r1, [r4, #0x1c]
    mov r0, r5
    orr r1, r1, #0x10
    str r1, [r4, #0x1c]
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d7878+8))>>2)&0xffffff)
    ldr r0, [r4, #0x58]
    tst r0, #0x200
    beq .Lpc_020d7898
    ldr r2, [r4, #0x54]
    mov r0, r6
    mov r1, #9
    blx r2
.Lpc_020d7898:
    .inst 0xeb000000 | (((0x20d3a38-(0x020d7898+8))>>2)&0xffffff)
    ldr r1, [r6, #0xc]
    orr r1, r1, #0x40
    str r1, [r6, #0xc]
    ldr r1, [r6, #0xc]
    tst r1, #4
    movne r1, #1
    moveq r1, #0
    cmp r1, #0
    bne .Lpc_020d78d4
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d78c0+8))>>2)&0xffffff)
    mov r0, r6
    .inst 0xeb000000 | (((0x20d76b0-(0x020d78c8+8))>>2)&0xffffff)
    mov r0, #1
    pop {r3, r4, r5, r6, r7, pc}
.Lpc_020d78d4:
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d78d4+8))>>2)&0xffffff)
    b .Lpc_020d7920
.Lpc_020d78dc:
    ldr r0, [r6, #0xc]
    tst r0, #4
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    bne .Lpc_020d7904
    mov r0, r5
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d78f8+8))>>2)&0xffffff)
    mov r0, #1
    pop {r3, r4, r5, r6, r7, pc}
.Lpc_020d7904:
    add r0, r6, #0x18
    .inst 0xeb000000 | (((0x20d1e7c-(0x020d7908+8))>>2)&0xffffff)
    ldr r0, [r6, #0xc]
    tst r0, #0x40
    beq .Lpc_020d7904
    mov r0, r5
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d791c+8))>>2)&0xffffff)
.Lpc_020d7920:
    mov r0, r6
    .inst 0xeb000000 | (((0x20d7744-(0x020d7924+8))>>2)&0xffffff)
    pop {r3, r4, r5, r6, r7, pc}
.size native_fs_send_command_recipe,.-native_fs_send_command_recipe
