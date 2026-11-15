/* Recovered cached Fast/Direct comparison recipes, no installer.
 * FS_command_default.c at cb614ad23449d5852b40321dc409c4143872b35c.
 * Original MWC code generation is not reconstructed. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
#ifdef BUILD_FAST_COMMAND
.global native_fs_cached_fast_command
.type native_fs_cached_fast_command,%function
native_fs_cached_fast_command:
    push {r3,r4,r5,lr}
    sub sp,sp,#16
    mov r5,r0
    ldr r1,[r5,#8]
    ldr r4,[r5,#52]
    ldr r0,[r1,#48]
    lsl r2,r4,#3
    cmp r0,r4,lsl #3
    addls sp,sp,#16
    movls r0,#1
    popls {r3,r4,r5,pc}
    str r1,[sp]
    ldr r1,[r1,#44]
    add r0,sp,#0
    add r3,r1,r2
    add r1,sp,#8
    mov r2,#8
    str r3,[sp,#4]
    .inst 0xeb000000 | (((0x020d6aa0-(0x020d7388+8))>>2)&0xffffff)
    cmp r0,#0
    addne sp,sp,#16
    popne {r3,r4,r5,pc}
    ldr r1,[sp,#8]
    mov r0,r5
    str r1,[r5,#48]
    ldr r2,[sp,#12]
    mov r1,#7
    str r2,[r5,#52]
    str r4,[r5,#56]
    .inst 0xeb000000 | (((0x020d68c0-(0x020d73b4+8))>>2)&0xffffff)
    add sp,sp,#16
    pop {r3,r4,r5,pc}
.size native_fs_cached_fast_command,.-native_fs_cached_fast_command
#endif
#ifdef BUILD_DIRECT_COMMAND
.global native_fs_cached_direct_command
.type native_fs_cached_direct_command,%function
native_fs_cached_direct_command:
    ldr r1,[r0,#48]
    str r1,[r0,#36]
    ldr r1,[r0,#48]
    str r1,[r0,#44]
    ldr r1,[r0,#52]
    str r1,[r0,#40]
    ldr r1,[r0,#56]
    str r1,[r0,#32]
    mov r0,#0
    bx lr
.size native_fs_cached_direct_command,.-native_fs_cached_direct_command
#endif
