/* Recovered ExecuteSync wrapper; attribution recipe, no installer.
 * FS_archive_prefix.c at cb614ad23449d5852b40321dc409c4143872b35c.
 * This binary contains an Async branch; the first runtime contract uses NextNULL.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_exec_sync_command_recipe
.type native_fs_exec_sync_command_recipe,%function
native_fs_exec_sync_command_recipe:
    push {r4, lr}
    mov r4, r0
    ldr r1, [r4, #0x10]
    .inst 0xeb000000 | (((0x20d68c0-(0x020d7750+8))>>2)&0xffffff)
    mov r1, r0
    mov r0, r4
    .inst 0xeb000000 | (((0x20d6864-(0x020d775c+8))>>2)&0xffffff)
    ldr r0, [r4, #8]
    .inst 0xeb000000 | (((0x20d749c-(0x020d7764+8))>>2)&0xffffff)
    cmp r0, #0
    beq .Lpc_020d7774
    .inst 0xeb000000 | (((0x20d76b0-(0x020d7770+8))>>2)&0xffffff)
.Lpc_020d7774:
    ldr r0, [r4, #0x14]
    cmp r0, #0
    moveq r0, #1
    movne r0, #0
    pop {r4, pc}
.size native_fs_exec_sync_command_recipe,.-native_fs_exec_sync_command_recipe
