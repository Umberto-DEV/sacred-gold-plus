/* Recovered prefix of FSi_FindPathCommand, comparison only; no installer.
 * Counterpart: FS_command_default.c at cb614ad23449d5852b40321dc409c4143872b35c.
 * Stops before nested Translate(SEEKDIR); no FSResult or path lookup yet.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_default_findpath_command_recipe
.type native_fs_default_findpath_command_recipe,%function
native_fs_default_findpath_command_recipe:
    push {r3, r4, r5, r6, r7, r8, r9, r10, lr}
    sub sp, sp, #148
    mov r9, r0
    ldr r5, [r9, #60]
    mov r1, #2
    ldr r6, [r9, #64]
    .inst 0xeb000000 | (((0x020d68c0-(0x020d6dc8+8))>>2)&0xffffff)
.size native_fs_default_findpath_command_recipe, .-native_fs_default_findpath_command_recipe
