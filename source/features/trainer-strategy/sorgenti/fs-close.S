/* Recovered FS_CloseFile; attribution artifact, no installer.
 * FS_file.c counterpart at cb614ad23449d5852b40321dc409c4143872b35c. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_close_recipe
.type native_fs_close_recipe, %function
native_fs_close_recipe:
    push {r4, lr}
    mov r1, #8
    mov r4, r0
    .inst 0xeb000000 | (((0x020d7788 - (0x020d82cc + 8)) >> 2) & 0xffffff)
    cmp r0, #0
    mov r0, #0
    popeq {r4, pc}
    str r0, [r4, #8]
    mov r0, #14
    str r0, [r4, #16]
    ldr r1, [r4, #12]
    mov r0, #1
    bic r1, r1, #48
    str r1, [r4, #12]
    pop {r4, pc}
.size native_fs_close_recipe, .-native_fs_close_recipe
