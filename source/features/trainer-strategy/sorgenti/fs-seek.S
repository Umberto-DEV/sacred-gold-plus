/* Recovered FS_SeekFile; attribution artifact, no installer.
 * FS_file.c counterpart at cb614ad23449d5852b40321dc409c4143872b35c. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_seek_recipe
.type native_fs_seek_recipe, %function
native_fs_seek_recipe:
    cmp r2, #0
    beq .Lset
    cmp r2, #1
    beq .Lcur
    cmp r2, #2
    beq .Lend
    b .Linvalid
.Lset:
    ldr r2, [r0, #36]
    add r1, r1, r2
    b .Lclamp
.Lcur:
    ldr r2, [r0, #44]
    add r1, r1, r2
    b .Lclamp
.Lend:
    ldr r2, [r0, #40]
    add r1, r1, r2
    b .Lclamp
.Linvalid:
    mov r0, #0
    bx lr
.Lclamp:
    ldr r2, [r0, #36]
    cmp r1, r2
    movlt r1, r2
    ldr r2, [r0, #40]
    cmp r1, r2
    movgt r1, r2
    str r1, [r0, #44]
    mov r0, #1
    bx lr
.size native_fs_seek_recipe, .-native_fs_seek_recipe
