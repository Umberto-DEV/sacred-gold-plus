/* Recovered native SDK recipe for attribution, never installed by this tool.
 * FS_InitFile counterpart: FS_file.c at reference cb614ad23449d5852b40321dc409c4143872b35c.
 * This is not a reconstruction of the original compiler invocation. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_init_recipe
.type native_fs_init_recipe, %function
native_fs_init_recipe:
    mov r2, #0
    str r2, [r0, #0]
    str r2, [r0, #4]
    str r2, [r0, #0x1c]
    str r2, [r0, #0x18]
    str r2, [r0, #8]
    mov r1, #14
    str r1, [r0, #0x10]
    str r2, [r0, #0xc]
    bx lr
.size native_fs_init_recipe, .-native_fs_init_recipe
