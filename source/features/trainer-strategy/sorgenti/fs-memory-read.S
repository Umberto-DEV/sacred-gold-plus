/* Recovered memory-archive Read/Close comparison objects, no installer.
 * FS_command_default.c/FS_archive_prefix.c at pinned cb614ad23449d5852b40321dc409c4143872b35c. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
#ifdef BUILD_READ_COMMAND
.global native_fs_cached_read_command
.type native_fs_cached_read_command,%function
native_fs_cached_read_command:
    push {r3,lr}
    ldr r2,[r0,#44]
    ldr r3,[r0,#56]
    ldr lr,[r0,#8]
    ldr r1,[r0,#48]
    add ip,r2,r3
    str ip,[r0,#44]
    ldr ip,[lr,#72]
    mov r0,lr
    blx ip
    pop {r3,pc}
.size native_fs_cached_read_command,.-native_fs_cached_read_command
#endif
#ifdef BUILD_READ_CALLBACK
.global native_fs_cached_read_callback
.type native_fs_cached_read_callback,%function
native_fs_cached_read_callback:
    push {r3,lr}
    ldr r0,[r0,#40]
    add r0,r0,r2
    mov r2,r3
    .inst 0xeb000000 | (((0x020d4a50-(0x020d7458+8))>>2)&0xffffff)
    mov r0,#0
    pop {r3,pc}
.size native_fs_cached_read_callback,.-native_fs_cached_read_callback
#endif
#ifdef BUILD_CLOSE_COMMAND
.global native_fs_cached_close_command
.type native_fs_cached_close_command,%function
native_fs_cached_close_command:
    mov r0,#0
    bx lr
.size native_fs_cached_close_command,.-native_fs_cached_close_command
#endif
