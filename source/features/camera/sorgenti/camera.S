/* Plus camera policy. GPL-3.0-or-later.
 * Recovered instruction body; constants select inherited or current table.
 * Entry/return: Thumb, r0=map ID/result. r4-r11 and sp preserved.
 * The native entry shim already clobbers caller-saved r3.
 */
.syntax unified
.cpu arm946e-s
.thumb
.include "indirizzi.inc"
.section .text
.global cam_hook
.thumb_func
cam_hook:
 push {r3,lr}
 ldr r3,=CAM_VALIDATE
 blx r3
 ldr r3,=CAM_STATE
 ldrb r3,[r3]
 cmp r3,#0
 beq .Lclassic
 lsls r0,r0,#4
 ldr r2,=CAM_EXC
 ldr r1,=CAM_EXC_END
.Lscan:
 cmp r2,r1
 bhs .Lplus
 ldrh r3,[r2]
 adds r2,r2,#2
 cmp r3,r0
 blo .Lscan
 subs r3,r3,r0
 cmp r3,#16
 bhs .Lplus
 movs r0,r3
 pop {r3,pc}
.Lplus:
 movs r0,#CAM_PLUS_DEFAULT
 pop {r3,pc}
.Lclassic:
 movs r1,#CAM_STRIDE
 muls r1,r0,r1
 ldr r0,=CAM_TABLE
 adds r0,r0,r1
 ldr r0,[r0,#CAM_WORD_OFF]
 lsls r0,r0,#CAM_LSL
 lsrs r0,r0,#CAM_LSR
 pop {r3,pc}
.ltorg
