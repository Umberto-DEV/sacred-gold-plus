/* Recovered comparison assembly. Original SDK C/asm is the semantic reference.
 * Not an installer or the missing original Metrowerks C code generation. */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
#if defined(BUILD_SEEKDIR)
.global native_fs_cached_seekdir
native_fs_cached_seekdir:
.Lbegin:
    push {r4, r5, r6, lr} /* 020D6BEC */
    sub sp, sp, #0x10 /* 020D6BF0 */
    mov r6, r0 /* 020D6BF4 */
    ldr r4, [r6, #8] /* 020D6BF8 */
    add r5, r6, #0x30 /* 020D6BFC */
    str r4, [sp] /* 020D6C00 */
    ldrh r1, [r5, #4] /* 020D6C04 */
    ldr r2, [r4, #0x34] /* 020D6C08 */
    add r0, sp, #0 /* 020D6C0C */
    add r3, r2, r1, lsl #3 /* 020D6C10 */
    add r1, sp, #8 /* 020D6C14 */
    mov r2, #8 /* 020D6C18 */
    str r3, [sp, #4] /* 020D6C1C */
    .inst 0xeb000000 | (((0x020d6aa0 - (0x020d6c20 + 8)) / 4) & 0xffffff) /* explicit ARM BL PC8, no linker */
    movs r3, r0 /* 020D6C24 */
    bne .Lbegin + (136) /* 020D6C28 */
    add ip, r6, #0x20 /* 020D6C2C */
    ldm r5, {r0, r1, r2} /* 020D6C30 */
    stm ip, {r0, r1, r2} /* 020D6C34 */
    ldrh r0, [r5, #6] /* 020D6C38 */
    cmp r0, #0 /* 020D6C3C */
    ldreq r0, [r5, #8] /* 020D6C40 */
    cmpeq r0, #0 /* 020D6C44 */
    bne .Lbegin + (120) /* 020D6C48 */
    ldrh r0, [sp, #0xc] /* 020D6C4C */
    strh r0, [r6, #0x26] /* 020D6C50 */
    ldr r1, [r4, #0x34] /* 020D6C54 */
    ldr r0, [sp, #8] /* 020D6C58 */
    add r0, r1, r0 /* 020D6C5C */
    str r0, [r6, #0x28] /* 020D6C60 */
    ldrh r1, [sp, #0xe] /* 020D6C64 */
    ldr r0, [pc, #0x10] /* 020D6C68 */
    and r0, r1, r0 /* 020D6C6C */
    str r0, [r6, #0x2c] /* 020D6C70 */
    mov r0, r3 /* 020D6C74 */
    add sp, sp, #0x10 /* 020D6C78 */
    pop {r4, r5, r6, pc} /* 020D6C7C */
    .word 0x00000fff /* literal mask, not an instruction */
#endif

#if defined(BUILD_READ_TABLE)
.global native_fs_cached_read_table
native_fs_cached_read_table:
.Lbegin:
    push {r3, r4, r5, r6, r7, r8, sb, lr} /* 020D6AA0 */
    mov r7, r0 /* 020D6AA4 */
    ldr r4, [r7] /* 020D6AA8 */
    mov r6, r2 /* 020D6AAC */
    ldr r2, [r4, #0x1c] /* 020D6AB0 */
    mov r0, r4 /* 020D6AB4 */
    orr r2, r2, #0x200 /* 020D6AB8 */
    str r2, [r4, #0x1c] /* 020D6ABC */
    ldr r2, [r7, #4] /* 020D6AC0 */
    ldr r5, [r4, #0x50] /* 020D6AC4 */
    mov r3, r6 /* 020D6AC8 */
    blx r5 /* 020D6ACC */
    cmp r0, #0 /* 020D6AD0 */
    cmpne r0, #1 /* 020D6AD4 */
    beq .Lbegin + (72) /* 020D6AD8 */
    cmp r0, #6 /* 020D6ADC */
    beq .Lbegin + (88) /* 020D6AE0 */
    b .Lbegin + (176) /* 020D6AE4 */
    ldr r1, [r4, #0x1c] /* 020D6AE8 */
    bic r1, r1, #0x200 /* 020D6AEC */
    str r1, [r4, #0x1c] /* 020D6AF0 */
    b .Lbegin + (176) /* 020D6AF4 */
    .inst 0xeb000000 | (((0x020d3a38 - (0x020d6af8 + 8)) / 4) & 0xffffff) /* explicit ARM BL PC8, no linker */
    ldr r1, [r4, #0x1c] /* 020D6AFC */
    mov r5, r0 /* 020D6B00 */
    tst r1, #0x200 /* 020D6B04 */
    movne r0, #1 /* 020D6B08 */
    moveq r0, #0 /* 020D6B0C */
    cmp r0, #0 /* 020D6B10 */
    beq .Lbegin + (160) /* 020D6B14 */
    mov r8, #0 /* 020D6B18 */
    mov sb, #1 /* 020D6B1C */
    add r0, r4, #0xc /* 020D6B20 */
    .inst 0xeb000000 | (((0x020d1e7c - (0x020d6b24 + 8)) / 4) & 0xffffff) /* explicit ARM BL PC8, no linker */
    ldr r0, [r4, #0x1c] /* 020D6B28 */
    tst r0, #0x200 /* 020D6B2C */
    movne r0, sb /* 020D6B30 */
    moveq r0, r8 /* 020D6B34 */
    cmp r0, #0 /* 020D6B38 */
    bne .Lbegin + (128) /* 020D6B3C */
    mov r0, r5 /* 020D6B40 */
    .inst 0xeb000000 | (((0x020d3a4c - (0x020d6b44 + 8)) / 4) & 0xffffff) /* explicit ARM BL PC8, no linker */
    ldr r0, [r4, #0x24] /* 020D6B48 */
    ldr r0, [r0, #0x14] /* 020D6B4C */
    ldr r1, [r7, #4] /* 020D6B50 */
    add r1, r1, r6 /* 020D6B54 */
    str r1, [r7, #4] /* 020D6B58 */
    pop {r3, r4, r5, r6, r7, r8, sb, pc} /* 020D6B5C */
#endif

#if defined(BUILD_READ_MEMORY)
.global native_fs_cached_read_memory
native_fs_cached_read_memory:
.Lbegin:
    push {r3, lr} /* 020D7484 */
    mov r0, r2 /* 020D7488 */
    mov r2, r3 /* 020D748C */
    .inst 0xeb000000 | (((0x020d4a50 - (0x020d7490 + 8)) / 4) & 0xffffff) /* explicit ARM BL PC8, no linker */
    mov r0, #0 /* 020D7494 */
    pop {r3, pc} /* 020D7498 */
#endif

#if defined(BUILD_COPY)
.global native_fs_cached_copy
native_fs_cached_copy:
.Lbegin:
    cmp r2, #0 /* 020D4A50 */
    beq .Lbegin + (12) /* 020D4A54 */
    b .Lbegin + (16) /* 020D4A58 */
    bx lr /* 020D4A5C */
    tst r1, #1 /* 020D4A60 */
    beq .Lbegin + (104) /* 020D4A64 */
    ldrh ip, [r1, #-1] /* 020D4A68 */
    and ip, ip, #0xff /* 020D4A6C */
    tst r0, #1 /* 020D4A70 */
    bne .Lbegin + (44) /* 020D4A74 */
    b .Lbegin + (48) /* 020D4A78 */
    ldrh r3, [r0, #-1] /* 020D4A7C */
    bne .Lbegin + (56) /* 020D4A80 */
    b .Lbegin + (60) /* 020D4A84 */
    lsr r3, r3, #8 /* 020D4A88 */
    beq .Lbegin + (68) /* 020D4A8C */
    b .Lbegin + (72) /* 020D4A90 */
    ldrh r3, [r0] /* 020D4A94 */
    orr r3, ip, r3, lsl #8 /* 020D4A98 */
    strh r3, [r1, #-1] /* 020D4A9C */
    add r0, r0, #1 /* 020D4AA0 */
    add r1, r1, #1 /* 020D4AA4 */
    subs r2, r2, #1 /* 020D4AA8 */
    beq .Lbegin + (100) /* 020D4AAC */
    b .Lbegin + (104) /* 020D4AB0 */
    bx lr /* 020D4AB4 */
    eor ip, r1, r0 /* 020D4AB8 */
    tst ip, #1 /* 020D4ABC */
    beq .Lbegin + (196) /* 020D4AC0 */
    bic r0, r0, #1 /* 020D4AC4 */
    ldrh ip, [r0], #2 /* 020D4AC8 */
    lsr r3, ip, #8 /* 020D4ACC */
    subs r2, r2, #2 /* 020D4AD0 */
    blo .Lbegin + (160) /* 020D4AD4 */
    ldrh ip, [r0], #2 /* 020D4AD8 */
    orr ip, r3, ip, lsl #8 /* 020D4ADC */
    strh ip, [r1], #2 /* 020D4AE0 */
    lsr r3, ip, #0x10 /* 020D4AE4 */
    subs r2, r2, #2 /* 020D4AE8 */
    bhs .Lbegin + (136) /* 020D4AEC */
    tst r2, #1 /* 020D4AF0 */
    beq .Lbegin + (172) /* 020D4AF4 */
    b .Lbegin + (176) /* 020D4AF8 */
    bx lr /* 020D4AFC */
    ldrh ip, [r1] /* 020D4B00 */
    and ip, ip, #0xff00 /* 020D4B04 */
    orr ip, ip, r3 /* 020D4B08 */
    strh ip, [r1] /* 020D4B0C */
    bx lr /* 020D4B10 */
    tst ip, #2 /* 020D4B14 */
    beq .Lbegin + (240) /* 020D4B18 */
    bics r3, r2, #1 /* 020D4B1C */
    beq .Lbegin + (340) /* 020D4B20 */
    sub r2, r2, r3 /* 020D4B24 */
    add ip, r3, r1 /* 020D4B28 */
    ldrh r3, [r0], #2 /* 020D4B2C */
    strh r3, [r1], #2 /* 020D4B30 */
    cmp r1, ip /* 020D4B34 */
    blo .Lbegin + (220) /* 020D4B38 */
    b .Lbegin + (340) /* 020D4B3C */
    cmp r2, #2 /* 020D4B40 */
    blo .Lbegin + (340) /* 020D4B44 */
    tst r1, #2 /* 020D4B48 */
    beq .Lbegin + (280) /* 020D4B4C */
    ldrh r3, [r0], #2 /* 020D4B50 */
    strh r3, [r1], #2 /* 020D4B54 */
    subs r2, r2, #2 /* 020D4B58 */
    beq .Lbegin + (276) /* 020D4B5C */
    b .Lbegin + (280) /* 020D4B60 */
    bx lr /* 020D4B64 */
    bics r3, r2, #3 /* 020D4B68 */
    beq .Lbegin + (312) /* 020D4B6C */
    sub r2, r2, r3 /* 020D4B70 */
    add ip, r3, r1 /* 020D4B74 */
    ldr r3, [r0], #4 /* 020D4B78 */
    str r3, [r1], #4 /* 020D4B7C */
    cmp r1, ip /* 020D4B80 */
    blo .Lbegin + (296) /* 020D4B84 */
    tst r2, #2 /* 020D4B88 */
    bne .Lbegin + (324) /* 020D4B8C */
    b .Lbegin + (328) /* 020D4B90 */
    ldrh r3, [r0], #2 /* 020D4B94 */
    bne .Lbegin + (336) /* 020D4B98 */
    b .Lbegin + (340) /* 020D4B9C */
    strh r3, [r1], #2 /* 020D4BA0 */
    tst r2, #1 /* 020D4BA4 */
    beq .Lbegin + (352) /* 020D4BA8 */
    b .Lbegin + (356) /* 020D4BAC */
    bx lr /* 020D4BB0 */
    ldrh r2, [r1] /* 020D4BB4 */
    ldrh r0, [r0] /* 020D4BB8 */
    and r2, r2, #0xff00 /* 020D4BBC */
    and r0, r0, #0xff /* 020D4BC0 */
    orr r0, r2, r0 /* 020D4BC4 */
    strh r0, [r1] /* 020D4BC8 */
    bx lr /* 020D4BCC */
#endif
