/* Recovered SDK FS_OpenFileFast; attribution recipe, no installer.
 * Counterpart FS_file.c at cb614ad23449d5852b40321dc409c4143872b35c. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_fast_recipe
.type native_fs_fast_recipe, %function
native_fs_fast_recipe:
    push {r0, r1, r2, r3}
    push {r4, lr}
    ldr r1, [sp, #12]
    mov r4, r0
    cmp r1, #0
    moveq r0, #0
    popeq {r4, lr}
    addeq sp, sp, #16
    bxeq lr
    str r1, [r4, #8]
    str r1, [r4, #48]
    ldr r2, [sp, #16]
    mov r1, #6
    str r2, [r4, #52]
    .inst 0xeb000000 | (((0x020d7788 - (0x020d8240 + 8)) >> 2) & 0xffffff)
    cmp r0, #0
    moveq r0, #0
    popeq {r4, lr}
    addeq sp, sp, #16
    bxeq lr
    ldr r1, [r4, #12]
    mov r0, #1
    orr r1, r1, #16
    bic r1, r1, #32
    str r1, [r4, #12]
    pop {r4, lr}
    add sp, sp, #16
    bx lr
.size native_fs_fast_recipe, .-native_fs_fast_recipe
