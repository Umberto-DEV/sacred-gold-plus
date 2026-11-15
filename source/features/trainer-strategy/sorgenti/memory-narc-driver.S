/* Project-owned synthetic test caller, NEVER installed in a game ROM.
 * Inputs: R0 source-initialized FSFile*, R1 actual pathname*,
 * R2 header destination16*, R3 member destination16*.
 * Returns the result-vector pointer. No host phase state reinjection.
 */
.syntax unified
.cpu arm946e-s
.arm
.text
.balign 4
.equ DRIVER_RAM,0x022f0800
.macro api_bl target,site
    .inst 0xeb000000 | (((\target-(\site+8))>>2)&0xffffff)
.endm
.global sgp_test_memory_narc_driver
.type sgp_test_memory_narc_driver,%function
sgp_test_memory_narc_driver:
    push {r4,r5,r6,r7,r8,lr}
    mov r4,r0
    mov r5,r2
    mov r6,r3
    ldr r7,.Lresults
    api_bl 0x020d8278,(DRIVER_RAM+0x14)
    str r0,[r7,#0]
    mov r0,r4
    mov r1,r5
    mov r2,#16
    api_bl 0x020d83cc,(DRIVER_RAM+0x28)
    str r0,[r7,#4]
    mov r0,r4
    ldr r1,.Lmember_offset
    mov r2,#0
    api_bl 0x020d83dc,(DRIVER_RAM+0x3c)
    str r0,[r7,#8]
    mov r0,r4
    mov r1,r6
    mov r2,#16
    api_bl 0x020d83cc,(DRIVER_RAM+0x50)
    str r0,[r7,#12]
    mov r0,r4
    api_bl 0x020d82c0,(DRIVER_RAM+0x5c)
    str r0,[r7,#16]
    mov r0,r7
    pop {r4,r5,r6,r7,r8,pc}
.size sgp_test_memory_narc_driver,.-sgp_test_memory_narc_driver
.Lresults:
    .word 0x022f0280
.Lmember_offset:
    .word 0x224c
