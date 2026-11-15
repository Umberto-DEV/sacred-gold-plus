/* Recovered SDK wrapper recipe for attribution, never installed by this tool.
 * Source counterpart: FS_file.c::FS_OpenFile at reference cb614ad23449d5852b40321dc409c4143872b35c.
 * Calls encode ARM PC+8-relative displacements at the stated installed VMA.
 * This avoids introducing an unqualified external ARM relocation/linker. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.equ OPEN_RAM, 0x020d8278
.equ CONVERT_PATH, 0x020d8180
.equ OPEN_FAST, 0x020d8208
.macro sdk_bl target, site
    .inst 0xeb000000 | (((\target - (\site + 8)) >> 2) & 0xffffff)
.endm
.global native_fs_open_recipe
.type native_fs_open_recipe, %function
native_fs_open_recipe:
    push {r4, lr}
    sub sp, sp, #8
    mov r4, r0
    add r0, sp, #0
    sdk_bl CONVERT_PATH, (OPEN_RAM + 0x10)
    cmp r0, #0
    beq .Lfalse
    add r1, sp, #0
    mov r0, r4
    ldm r1, {r1, r2}
    sdk_bl OPEN_FAST, (OPEN_RAM + 0x28)
    cmp r0, #0
    addne sp, sp, #8
    movne r0, #1
    popne {r4, pc}
.Lfalse:
    mov r0, #0
    add sp, sp, #8
    pop {r4, pc}
.size native_fs_open_recipe, .-native_fs_open_recipe
