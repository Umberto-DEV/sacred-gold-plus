/* Recovered Wait body and IRQ leaves from pinned NitroSDK counterparts.
 * Attribution only. BUILD_COMPONENT: 0 Wait, 1 DisableIRQ, 2 RestoreIRQ.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
#if BUILD_COMPONENT == 1
.global native_fs_wait_disable_recipe
.type native_fs_wait_disable_recipe, %function
native_fs_wait_disable_recipe:
    mrs r0, cpsr
    orr r1, r0, #0x80
    msr cpsr_c, r1
    and r0, r0, #0x80
    bx lr
.size native_fs_wait_disable_recipe, .-native_fs_wait_disable_recipe
#elif BUILD_COMPONENT == 2
.global native_fs_wait_restore_recipe
.type native_fs_wait_restore_recipe, %function
native_fs_wait_restore_recipe:
    mrs r1, cpsr
    bic r2, r1, #0x80
    orr r2, r2, r0
    msr cpsr_c, r2
    and r0, r1, #0x80
    bx lr
.size native_fs_wait_restore_recipe, .-native_fs_wait_restore_recipe
#else
.global native_fs_wait_core_recipe
.type native_fs_wait_core_recipe, %function
native_fs_wait_core_recipe:
    push {r4, r5, r6, r7, r8, lr}
    mov r6, r0
    mov r5, #0
    .inst 0xEB000000 | (((0x020D3A38 - (0x020D8308 + 8)) / 4) & 0xFFFFFF)
    ldr r1, [r6, #12]
    mov r4, r0
    tst r1, #1
    movne r0, #1
    moveq r0, r5
    cmp r0, #0
    beq .Lrestore
    ldr r0, [r6, #12]
    tst r0, #0x44
    moveq r5, #1
    movne r5, #0
    cmp r5, #0
    beq .Lwait_busy
    ldr r0, [r6, #12]
    orr r0, r0, #4
    str r0, [r6, #12]
.Lwait_owner:
    add r0, r6, #24
    .inst 0xEB000000 | (((0x020D1E7C - (0x020D8350 + 8)) / 4) & 0xFFFFFF)
    ldr r0, [r6, #12]
    tst r0, #0x40
    beq .Lwait_owner
    b .Lrestore
.Lwait_busy:
    mov r7, #0
    mov r8, #1
.Lsleep_busy:
    add r0, r6, #24
    .inst 0xEB000000 | (((0x020D1E7C - (0x020D8370 + 8)) / 4) & 0xFFFFFF)
    ldr r0, [r6, #12]
    tst r0, #1
    movne r0, r8
    moveq r0, r7
    cmp r0, #0
    bne .Lsleep_busy
.Lrestore:
    mov r0, r4
    .inst 0xEB000000 | (((0x020D3A4C - (0x020D8390 + 8)) / 4) & 0xFFFFFF)
    cmp r5, #0
    beq .Lsucceeded
    mov r0, r6
    .inst 0xEB000000 | (((0x020D7744 - (0x020D83A0 + 8)) / 4) & 0xFFFFFF)
    pop {r4, r5, r6, r7, r8, pc}
.Lsucceeded:
    ldr r0, [r6, #20]
    cmp r0, #0
    moveq r0, #1
    movne r0, #0
    pop {r4, r5, r6, r7, r8, pc}
.size native_fs_wait_core_recipe, .-native_fs_wait_core_recipe
#endif
