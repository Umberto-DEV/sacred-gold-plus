/* Recovered SDK path-conversion wrapper; attribution artifact, no installer.
 * Source counterpart: FS_file.c::FS_ConvertPathToFileID at reference
 * cb614ad23449d5852b40321dc409c4143872b35c. Calls use explicit ARM PC+8 sites. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.equ CONVERT_RAM, 0x020d8180
.equ INIT_FILE, 0x020d7f98
.equ FIND_PATH, 0x020d7fc0
.macro sdk_bl target, site
    .inst 0xeb000000 | (((\target - (\site + 8)) >> 2) & 0xffffff)
.endm
.global native_fs_convert_recipe
.type native_fs_convert_recipe, %function
native_fs_convert_recipe:
    push {r3, r4, r5, lr}
    sub sp, sp, #72
    mov r5, r0
    add r0, sp, #0
    mov r4, r1
    sdk_bl INIT_FILE, (CONVERT_RAM + 0x14)
    add r0, sp, #0
    mov r1, r4
    mov r2, r5
    mov r3, #0
    sdk_bl FIND_PATH, (CONVERT_RAM + 0x28)
    cmp r0, #0
    movne r0, #1
    moveq r0, #0
    add sp, sp, #72
    pop {r3, r4, r5, pc}
.size native_fs_convert_recipe, .-native_fs_convert_recipe
