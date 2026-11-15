/* Recovered full FindPath, ReadDir and StrNICmp comparison assembly.
 * Reference SDK cb614ad; no installer or original Metrowerks C rebuild. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
#if defined(BUILD_FINDPATH)
.global native_fs_cached_findpath
native_fs_cached_findpath:
.Lbegin:
    push {r3, r4, r5, r6, r7, r8, sb, sl, lr} /* 020D6DB0 */
    sub sp, sp, #0x94 /* 020D6DB4 */
    mov sb, r0 /* 020D6DB8 */
    ldr r5, [sb, #0x3c] /* 020D6DBC */
    mov r1, #2 /* 020D6DC0 */
    ldr r6, [sb, #0x40] /* 020D6DC4 */
    .inst 0xeb000000 | (((0x020d68c0 - (0x020d6dc8 + 8)) / 4) & 0xffffff) /* 020D6DC8 */
    ldrb r3, [r5] /* 020D6DCC */
    cmp r3, #0 /* 020D6DD0 */
    beq .Lbegin + (440) /* 020D6DD4 */
    mov r8, #0 /* 020D6DD8 */
    mov r0, #1 /* 020D6DDC */
    mov r1, r8 /* 020D6DE0 */
    b .Lbegin + (60) /* 020D6DE4 */
    add r8, r8, #1 /* 020D6DE8 */
    ldrb r7, [r5, r8] /* 020D6DEC */
    mov r2, r1 /* 020D6DF0 */
    cmp r7, #0 /* 020D6DF4 */
    cmpne r7, #0x2f /* 020D6DF8 */
    cmpne r7, #0x5c /* 020D6DFC */
    movne r2, r0 /* 020D6E00 */
    cmp r2, #0 /* 020D6E04 */
    bne .Lbegin + (56) /* 020D6E08 */
    cmp r7, #0 /* 020D6E0C */
    cmpeq r6, #0 /* 020D6E10 */
    movne r7, #1 /* 020D6E14 */
    cmp r8, #0 /* 020D6E18 */
    addeq sp, sp, #0x94 /* 020D6E1C */
    moveq r0, #1 /* 020D6E20 */
    popeq {r3, r4, r5, r6, r7, r8, sb, sl, pc} /* 020D6E24 */
    cmp r3, #0x2e /* 020D6E28 */
    bne .Lbegin + (208) /* 020D6E2C */
    cmp r8, #1 /* 020D6E30 */
    addeq r5, r5, #1 /* 020D6E34 */
    beq .Lbegin + (412) /* 020D6E38 */
    ldrb r0, [r5, #1] /* 020D6E3C */
    cmp r8, #2 /* 020D6E40 */
    moveq r1, #1 /* 020D6E44 */
    movne r1, #0 /* 020D6E48 */
    cmp r0, #0x2e /* 020D6E4C */
    moveq r0, #1 /* 020D6E50 */
    movne r0, #0 /* 020D6E54 */
    tst r1, r0 /* 020D6E58 */
    beq .Lbegin + (208) /* 020D6E5C */
    ldrh r0, [sb, #0x24] /* 020D6E60 */
    cmp r0, #0 /* 020D6E64 */
    beq .Lbegin + (200) /* 020D6E68 */
    ldr r1, [sb, #0x2c] /* 020D6E6C */
    mov r0, sb /* 020D6E70 */
    .inst 0xeb000000 | (((0x020d6b60 - (0x020d6e74 + 8)) / 4) & 0xffffff) /* 020D6E74 */
    add r5, r5, #2 /* 020D6E78 */
    b .Lbegin + (412) /* 020D6E7C */
    cmp r8, #0x7f /* 020D6E80 */
    addgt sp, sp, #0x94 /* 020D6E84 */
    movgt r0, #1 /* 020D6E88 */
    popgt {r3, r4, r5, r6, r7, r8, sb, sl, pc} /* 020D6E8C */
    add r1, sp, #0 /* 020D6E90 */
    mov r0, #0 /* 020D6E94 */
    str r1, [sb, #0x30] /* 020D6E98 */
    str r0, [sb, #0x34] /* 020D6E9C */
    add sl, sp, #0x14 /* 020D6EA0 */
    mov r4, #3 /* 020D6EA4 */
    mov r0, sb /* 020D6EA8 */
    mov r1, r4 /* 020D6EAC */
    .inst 0xeb000000 | (((0x020d68c0 - (0x020d6eb0 + 8)) / 4) & 0xffffff) /* 020D6EB0 */
    cmp r0, #0 /* 020D6EB4 */
    addne sp, sp, #0x94 /* 020D6EB8 */
    movne r0, #1 /* 020D6EBC */
    popne {r3, r4, r5, r6, r7, r8, sb, sl, pc} /* 020D6EC0 */
    ldr r0, [sp, #0xc] /* 020D6EC4 */
    cmp r7, r0 /* 020D6EC8 */
    ldreq r0, [sp, #0x10] /* 020D6ECC */
    cmpeq r8, r0 /* 020D6ED0 */
    bne .Lbegin + (248) /* 020D6ED4 */
    mov r0, r5 /* 020D6ED8 */
    mov r1, sl /* 020D6EDC */
    mov r2, r8 /* 020D6EE0 */
    .inst 0xeb000000 | (((0x020d6a50 - (0x020d6ee4 + 8)) / 4) & 0xffffff) /* 020D6EE4 */
    cmp r0, #0 /* 020D6EE8 */
    bne .Lbegin + (248) /* 020D6EEC */
    cmp r7, #0 /* 020D6EF0 */
    beq .Lbegin + (364) /* 020D6EF4 */
    add r0, sp, #0 /* 020D6EF8 */
    add r3, sb, #0x30 /* 020D6EFC */
    ldm r0, {r0, r1, r2} /* 020D6F00 */
    stm r3, {r0, r1, r2} /* 020D6F04 */
    mov r0, sb /* 020D6F08 */
    mov r1, #2 /* 020D6F0C */
    add r5, r5, r8 /* 020D6F10 */
    .inst 0xeb000000 | (((0x020d68c0 - (0x020d6f14 + 8)) / 4) & 0xffffff) /* 020D6F14 */
    b .Lbegin + (412) /* 020D6F18 */
    cmp r6, #0 /* 020D6F1C */
    addne sp, sp, #0x94 /* 020D6F20 */
    movne r0, #1 /* 020D6F24 */
    popne {r3, r4, r5, r6, r7, r8, sb, sl, pc} /* 020D6F28 */
    ldr r3, [sb, #0x44] /* 020D6F2C */
    ldr r2, [sp] /* 020D6F30 */
    ldr r1, [sp, #4] /* 020D6F34 */
    add sp, sp, #0x94 /* 020D6F38 */
    str r2, [r3] /* 020D6F3C */
    mov r0, #0 /* 020D6F40 */
    str r1, [r3, #4] /* 020D6F44 */
    pop {r3, r4, r5, r6, r7, r8, sb, sl, pc} /* 020D6F48 */
    ldrb r0, [r5] /* 020D6F4C */
    cmp r0, #0 /* 020D6F50 */
    movne r0, #1 /* 020D6F54 */
    moveq r0, #0 /* 020D6F58 */
    ldrb r3, [r5, r0]! /* 020D6F5C */
    cmp r3, #0 /* 020D6F60 */
    bne .Lbegin + (40) /* 020D6F64 */
    cmp r6, #0 /* 020D6F68 */
    addeq sp, sp, #0x94 /* 020D6F6C */
    moveq r0, #1 /* 020D6F70 */
    popeq {r3, r4, r5, r6, r7, r8, sb, sl, pc} /* 020D6F74 */
    ldr r3, [sb, #0x44] /* 020D6F78 */
    add r0, sb, #0x20 /* 020D6F7C */
    ldm r0, {r0, r1, r2} /* 020D6F80 */
    stm r3, {r0, r1, r2} /* 020D6F84 */
    mov r0, #0 /* 020D6F88 */
    add sp, sp, #0x94 /* 020D6F8C */
    pop {r3, r4, r5, r6, r7, r8, sb, sl, pc} /* 020D6F90 */
#endif

#if defined(BUILD_READ_DIR)
.global native_fs_cached_read_dir
native_fs_cached_read_dir:
.Lbegin:
    push {r4, r5, lr} /* 020D6C84 */
    sub sp, sp, #0xc /* 020D6C88 */
    mov r5, r0 /* 020D6C8C */
    ldr r4, [r5, #0x30] /* 020D6C90 */
    ldr r1, [r5, #8] /* 020D6C94 */
    add r0, sp, #4 /* 020D6C98 */
    str r1, [sp, #4] /* 020D6C9C */
    ldr r3, [r5, #0x28] /* 020D6CA0 */
    add r1, sp, #0 /* 020D6CA4 */
    mov r2, #1 /* 020D6CA8 */
    str r3, [sp, #8] /* 020D6CAC */
    .inst 0xeb000000 | (((0x020d6aa0 - (0x020d6cb0 + 8)) / 4) & 0xffffff) /* 020D6CB0 */
    cmp r0, #0 /* 020D6CB4 */
    addne sp, sp, #0xc /* 020D6CB8 */
    popne {r4, r5, pc} /* 020D6CBC */
    ldrb r1, [sp] /* 020D6CC0 */
    and r2, r1, #0x7f /* 020D6CC4 */
    asr r1, r1, #7 /* 020D6CC8 */
    str r2, [r4, #0x10] /* 020D6CCC */
    and r1, r1, #1 /* 020D6CD0 */
    str r1, [r4, #0xc] /* 020D6CD4 */
    ldr r2, [r4, #0x10] /* 020D6CD8 */
    cmp r2, #0 /* 020D6CDC */
    addeq sp, sp, #0xc /* 020D6CE0 */
    moveq r0, #1 /* 020D6CE4 */
    popeq {r4, r5, pc} /* 020D6CE8 */
    ldr r1, [r5, #0x34] /* 020D6CEC */
    cmp r1, #0 /* 020D6CF0 */
    bne .Lbegin + (160) /* 020D6CF4 */
    add r0, sp, #4 /* 020D6CF8 */
    add r1, r4, #0x14 /* 020D6CFC */
    .inst 0xeb000000 | (((0x020d6aa0 - (0x020d6d00 + 8)) / 4) & 0xffffff) /* 020D6D00 */
    cmp r0, #0 /* 020D6D04 */
    addne sp, sp, #0xc /* 020D6D08 */
    popne {r4, r5, pc} /* 020D6D0C */
    ldr r1, [r4, #0x10] /* 020D6D10 */
    mov r2, #0 /* 020D6D14 */
    add r1, r4, r1 /* 020D6D18 */
    strb r2, [r1, #0x14] /* 020D6D1C */
    b .Lbegin + (172) /* 020D6D20 */
    ldr r1, [sp, #8] /* 020D6D24 */
    add r1, r1, r2 /* 020D6D28 */
    str r1, [sp, #8] /* 020D6D2C */
    ldr r1, [r4, #0xc] /* 020D6D30 */
    cmp r1, #0 /* 020D6D34 */
    beq .Lbegin + (252) /* 020D6D38 */
    add r0, sp, #4 /* 020D6D3C */
    add r1, sp, #2 /* 020D6D40 */
    mov r2, #2 /* 020D6D44 */
    .inst 0xeb000000 | (((0x020d6aa0 - (0x020d6d48 + 8)) / 4) & 0xffffff) /* 020D6D48 */
    cmp r0, #0 /* 020D6D4C */
    addne sp, sp, #0xc /* 020D6D50 */
    popne {r4, r5, pc} /* 020D6D54 */
    ldr r2, [r5, #8] /* 020D6D58 */
    ldr r1, [pc, #0x48] /* 020D6D5C */
    str r2, [r4] /* 020D6D60 */
    ldrh r3, [sp, #2] /* 020D6D64 */
    mov r2, #0 /* 020D6D68 */
    and r1, r3, r1 /* 020D6D6C */
    strh r1, [r4, #4] /* 020D6D70 */
    strh r2, [r4, #6] /* 020D6D74 */
    str r2, [r4, #8] /* 020D6D78 */
    b .Lbegin + (280) /* 020D6D7C */
    ldr r1, [r5, #8] /* 020D6D80 */
    str r1, [r4] /* 020D6D84 */
    ldrh r1, [r5, #0x26] /* 020D6D88 */
    str r1, [r4, #4] /* 020D6D8C */
    ldrh r1, [r5, #0x26] /* 020D6D90 */
    add r1, r1, #1 /* 020D6D94 */
    strh r1, [r5, #0x26] /* 020D6D98 */
    ldr r1, [sp, #8] /* 020D6D9C */
    str r1, [r5, #0x28] /* 020D6DA0 */
    add sp, sp, #0xc /* 020D6DA4 */
    pop {r4, r5, pc} /* 020D6DA8 */
    .word 0x00000fff /* literal, not code */
#endif

#if defined(BUILD_STRNICMP)
.global native_fs_cached_strnicmp
native_fs_cached_strnicmp:
.Lbegin:
    push {r3, lr} /* 020D6A50 */
    cmp r2, #0 /* 020D6A54 */
    mov lr, #0 /* 020D6A58 */
    bls .Lbegin + (72) /* 020D6A5C */
    ldrb ip, [r0, lr] /* 020D6A60 */
    ldrb r3, [r1, lr] /* 020D6A64 */
    sub ip, ip, #0x41 /* 020D6A68 */
    cmp ip, #0x19 /* 020D6A6C */
    sub r3, r3, #0x41 /* 020D6A70 */
    addls ip, ip, #0x20 /* 020D6A74 */
    cmp r3, #0x19 /* 020D6A78 */
    addls r3, r3, #0x20 /* 020D6A7C */
    cmp ip, r3 /* 020D6A80 */
    subne r0, ip, r3 /* 020D6A84 */
    popne {r3, pc} /* 020D6A88 */
    add lr, lr, #1 /* 020D6A8C */
    cmp lr, r2 /* 020D6A90 */
    blo .Lbegin + (16) /* 020D6A94 */
    mov r0, #0 /* 020D6A98 */
    pop {r3, pc} /* 020D6A9C */
#endif
