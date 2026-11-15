/* Recovered FSi_FindPath wrapper, attribution artifact with no installer.
 * FS_file.c counterpart at cb614ad23449d5852b40321dc409c4143872b35c.
 * The current-directory literal names BSS, not initialized bytes in the ROM.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.global native_fs_find_path_recipe
.type native_fs_find_path_recipe,%function
native_fs_find_path_recipe:
    push {r3,r4,r5,r6,r7,r8,lr}
    sub sp,sp,#12
    mov r7,r1
    ldrb r1,[r7]
    mov r8,r0
    mov r6,r2
    cmp r1,#47
    mov r5,r3
    cmpne r1,#92
    bne .Lrelative
    ldr r0,.Lcurrent
    mov r1,#0
    ldr r0,[r0]
    strh r1,[sp,#4]
    str r0,[sp]
    str r1,[sp,#8]
    strh r1,[sp,#6]
    add r7,r7,#1
    b .Largs
.Lrelative:
    ldr r0,.Lcurrent
    add r3,sp,#0
    ldm r0,{r0,r1,r2}
    stm r3,{r0,r1,r2}
    mov r4,#0
.Lscan:
    ldrb r0,[r7,r4]
    cmp r0,#0
    cmpne r0,#47
    cmpne r0,#92
    beq .Largs
    cmp r0,#58
    bne .Lnext
    mov r0,r7
    mov r1,r4
    .inst 0xeb000000 | (((0x020d7958-(0x020d8044+8))>>2)&0xffffff)
    cmp r0,#0
    addeq sp,sp,#12
    moveq r0,#0
    popeq {r3,r4,r5,r6,r7,r8,pc}
    ldr r1,[r0,#28]
    tst r1,#2
    movne r1,#1
    moveq r1,#0
    cmp r1,#0
    addeq sp,sp,#12
    moveq r0,#0
    popeq {r3,r4,r5,r6,r7,r8,pc}
    mov r1,#0
    str r0,[sp]
    str r1,[sp,#8]
    strh r1,[sp,#6]
    strh r1,[sp,#4]
    add r0,r4,#1
    ldrb r0,[r7,r0]!
    cmp r0,#47
    cmpne r0,#92
    addeq r7,r7,#1
    b .Largs
.Lnext:
    add r4,r4,#1
    cmp r4,#3
    ble .Lscan
.Largs:
    ldr r1,[sp]
    add r0,sp,#0
    str r1,[r8,#8]
    str r7,[r8,#60]
    add r3,r8,#48
    ldm r0,{r0,r1,r2}
    stm r3,{r0,r1,r2}
    cmp r5,#0
    moveq r0,#0
    streq r0,[r8,#64]
    streq r6,[r8,#68]
    beq .Lsend
    mov r0,#1
    str r0,[r8,#64]
    str r5,[r8,#68]
.Lsend:
    mov r0,r8
    mov r1,#4
    .inst 0xeb000000 | (((0x020d7788-(0x020d80f4+8))>>2)&0xffffff)
    add sp,sp,#12
    pop {r3,r4,r5,r6,r7,r8,pc}
.size native_fs_find_path_recipe,.-native_fs_find_path_recipe
.Lcurrent:
    .word 0x021e362c
