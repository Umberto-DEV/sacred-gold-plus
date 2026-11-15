/* Recovered Release wrapper; attribution recipe, no installer.
 * FS_command.c and inline CutFromList at cb614ad23449d5852b40321dc409c4143872b35c.
 * Void API: residual R0 is not a filesystem success result.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_release_command_recipe
.type native_fs_release_command_recipe,%function
native_fs_release_command_recipe:
    push {r4, r5, r6, lr}
    mov r5, r0
    mov r4, r1
    .inst 0xeb000000 | (((0x20d3a38-(0x020d6870+8))>>2)&0xffffff)
    ldr r1, [r5]
    mov r6, r0
    ldr r0, [r5, #4]
    cmp r1, #0
    strne r0, [r1, #4]
    cmp r0, #0
    strne r1, [r0]
    mov r0, #0
    str r0, [r5]
    str r0, [r5, #4]
    ldr r1, [r5, #0xc]
    add r0, r5, #0x18
    bic r1, r1, #0x4f
    str r1, [r5, #0xc]
    str r4, [r5, #0x14]
    .inst 0xeb000000 | (((0x20d1ecc-(0x020d68b0+8))>>2)&0xffffff)
    mov r0, r6
    .inst 0xeb000000 | (((0x20d3a4c-(0x020d68b8+8))>>2)&0xffffff)
    pop {r4, r5, r6, pc}
.size native_fs_release_command_recipe,.-native_fs_release_command_recipe
