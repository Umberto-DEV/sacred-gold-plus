/* Recovered OS_WakeupThread; attribution recipe, no installer.
 * os_thread.c at cb614ad23449d5852b40321dc409c4143872b35c.
 * Full body includes thread/scheduler work; empty-queue execution excludes it.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_os_wakeup_command_recipe
.type native_os_wakeup_command_recipe,%function
native_os_wakeup_command_recipe:
    push {r3, r4, r5, r6, r7, lr}
    mov r7, r0
    .inst 0xeb000000 | (((0x20d3a38-(0x020d1ed4+8))>>2)&0xffffff)
    ldr r1, [r7]
    mov r6, r0
    cmp r1, #0
    beq .Lpc_020d1f28
    beq .Lpc_020d1f18
    mov r5, #1
    mov r4, #0
.Lpc_020d1ef4:
    mov r0, r7
    .inst 0xeb000000 | (((0x20d1750-(0x020d1ef8+8))>>2)&0xffffff)
    str r5, [r0, #0x64]
    str r4, [r0, #0x78]
    str r4, [r0, #0x80]
    str r4, [r0, #0x7c]
    ldr r0, [r7]
    cmp r0, #0
    bne .Lpc_020d1ef4
.Lpc_020d1f18:
    mov r0, #0
    str r0, [r7, #4]
    str r0, [r7]
    .inst 0xeb000000 | (((0x20d18b0-(0x020d1f24+8))>>2)&0xffffff)
.Lpc_020d1f28:
    mov r0, r6
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d1f2c+8))>>2)&0xffffff)
    pop {r3, r4, r5, r6, r7, pc}
.size native_os_wakeup_command_recipe,.-native_os_wakeup_command_recipe
