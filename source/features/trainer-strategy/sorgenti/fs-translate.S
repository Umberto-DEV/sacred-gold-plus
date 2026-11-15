/* Recovered native TranslateCommand, comparison recipe; no installer.
 * FS_command.c counterpart at cb614ad23449d5852b40321dc409c4143872b35c.
 * Instructions396 plus literal4; unselected callback/async paths retained.
 * External default table and handler bytes come from developer-owned ROM.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_translate_command_recipe
.type native_fs_translate_command_recipe,%function
native_fs_translate_command_recipe:
    push {r4, r5, r6, r7, r8, lr}
    mov r8, r0
    ldr r0, [r8, #0xc]
    ldr r5, [r8, #8]
    mov r7, r1
    mov r1, #1
    tst r0, #4
    lsl r6, r1, r7
    moveq r1, #0
    ldr r0, [r5, #0x1c]
    cmp r1, #0
    orrne r0, r0, #0x200
    orreq r0, r0, #0x100
    str r0, [r5, #0x1c]
    ldr r0, [r5, #0x58]
    tst r0, r6
    beq .Lpc_020d6968
    ldr r2, [r5, #0x54]
    mov r0, r8
    mov r1, r7
    blx r2
    mov r4, r0
    cmp r4, #8
    addls pc, pc, r4, lsl #2
    b .Lpc_020d696c
    b .Lpc_020d6948
    b .Lpc_020d6948
    b .Lpc_020d696c
    b .Lpc_020d696c
    b .Lpc_020d6948
    b .Lpc_020d696c
    b .Lpc_020d696c
    b .Lpc_020d696c
    b .Lpc_020d6950
.Lpc_020d6948:
    str r4, [r8, #0x14]
    b .Lpc_020d696c
.Lpc_020d6950:
    ldr r1, [r5, #0x58]
    mvn r0, r6
    and r0, r1, r0
    str r0, [r5, #0x58]
    mov r4, #7
    b .Lpc_020d696c
.Lpc_020d6968:
    mov r4, #7
.Lpc_020d696c:
    cmp r4, #7
    bne .Lpc_020d6988
    ldr r1, .Ldefault_table
    mov r0, r8
    ldr r1, [r1, r7, lsl #2]
    blx r1
    mov r4, r0
.Lpc_020d6988:
    cmp r4, #6
    bne .Lpc_020d6a00
    ldr r0, [r8, #0xc]
    tst r0, #4
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    beq .Lpc_020d6a44
    .inst 0xeb000000 | (((0x20d3a38-(0x020d69a8+8))>>2)&0xffffff)
    ldr r1, [r5, #0x1c]
    mov r7, r0
    tst r1, #0x200
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    beq .Lpc_020d69f0
    mov r4, #0
    mov r6, #1
.Lpc_020d69d0:
    add r0, r5, #0xc
    .inst 0xeb000000 | (((0x20d1e7c-(0x020d69d4+8))>>2)&0xffffff)
    ldr r0, [r5, #0x1c]
    tst r0, #0x200
    movne r0, r6
    moveq r0, r4
    cmp r0, #0
    bne .Lpc_020d69d0
.Lpc_020d69f0:
    mov r0, r7
    ldr r4, [r8, #0x14]
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d69f8+8))>>2)&0xffffff)
    b .Lpc_020d6a44
.Lpc_020d6a00:
    ldr r0, [r8, #0xc]
    tst r0, #4
    movne r0, #1
    moveq r0, #0
    cmp r0, #0
    bne .Lpc_020d6a34
    ldr r1, [r5, #0x1c]
    mov r0, r8
    bic r2, r1, #0x100
    mov r1, r4
    str r2, [r5, #0x1c]
    .inst 0xeb000000 | (((0x20d6864-(0x020d6a2c+8))>>2)&0xffffff)
    b .Lpc_020d6a44
.Lpc_020d6a34:
    ldr r0, [r5, #0x1c]
    bic r0, r0, #0x200
    str r0, [r5, #0x1c]
    str r4, [r8, #0x14]
.Lpc_020d6a44:
    mov r0, r4
    pop {r4, r5, r6, r7, r8, pc}
.Ldefault_table:
    .word 0x0210e124
.size native_fs_translate_command_recipe,.-native_fs_translate_command_recipe
