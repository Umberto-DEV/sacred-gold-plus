/* Recovered FS_ReadFile veneer and FSi_ReadFileCore. Attribution only.
 * FS_file.c counterpart cb614ad23449d5852b40321dc409c4143872b35c.
 * Build twice with BUILD_WRAPPER=0/1; each object has one relocation-free text.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
#if BUILD_WRAPPER
.global native_fs_read_wrapper_recipe
.type native_fs_read_wrapper_recipe, %function
native_fs_read_wrapper_recipe:
    ldr ip, .Lcore_address
    mov r3, #0
    bx ip
.size native_fs_read_wrapper_recipe, .-native_fs_read_wrapper_recipe
.Lcore_address:
    .word 0x020D8104
#else
.global native_fs_read_core_recipe
.type native_fs_read_core_recipe, %function
native_fs_read_core_recipe:
    push {r3, r4, r5, r6, r7, lr}
    mov r7, r0
    ldr r4, [r7, #44]
    ldr r0, [r7, #40]
    mov r6, r2
    str r1, [r7, #48]
    sub r0, r0, r4
    cmp r6, r0
    movgt r6, r0
    cmp r6, #0
    movlt r6, #0
    str r2, [r7, #52]
    mov r5, r3
    str r6, [r7, #56]
    cmp r5, #0
    ldreq r0, [r7, #12]
    mov r1, #0
    orreq r0, r0, #4
    streq r0, [r7, #12]
    mov r0, r7
    /* Absolute site + ARM PC8, signed24; no external relocation. */
    .inst 0xEB000000 | (((0x020D7788 - (0x020D8154 + 8)) / 4) & 0xFFFFFF)
    cmp r5, #0
    bne .Ldone
    mov r0, r7
    .inst 0xEB000000 | (((0x020D82FC - (0x020D8164 + 8)) / 4) & 0xFFFFFF)
    cmp r0, #0
    ldrne r0, [r7, #44]
    subne r6, r0, r4
    mvneq r6, #0
.Ldone:
    mov r0, r6
    pop {r3, r4, r5, r6, r7, pc}
.size native_fs_read_core_recipe, .-native_fs_read_core_recipe
#endif
