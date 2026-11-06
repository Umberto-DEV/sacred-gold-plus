    .syntax unified
    .thumb
    .section .text,"ax",%progbits

    /*
     * HG-T12.  This replaces exactly the sprite-template builder call in
     * overlay 95.  The native builder still fills every field first.  We then
     * replace only bit 0 of palDataID with the shiny result computed from the
     * hatching player's profile and the egg PID.  The Pokémon and its memo are
     * deliberately left untouched until the retail post-animation path.
     *
     * Call-site ABI:
     *   r4 = Pokémon, r5 = overlay state, caller sp+0x3c = PokepicTemplate.
     * The single pushed word makes that template sp+0x40 in this helper.
     */
    .global traded_egg_palette_hook
    .type traded_egg_palette_hook,%function
    .thumb_func
traded_egg_palette_hook:
    push    {lr}

    .global traded_egg_sprite_call
traded_egg_sprite_call:
    .hword  0xf000, 0xf800

    adds    r0, r4, #0
    movs    r1, #0
    movs    r2, #0
    .global traded_egg_get_pid_call
traded_egg_get_pid_call:
    .hword  0xf000, 0xf800

    adds    r1, r0, #0
    ldr     r0, [r5]
    ldr     r0, [r0, #0x14]
    ldr     r0, [r0, #0x10]
    .global traded_egg_shiny_call
traded_egg_shiny_call:
    .hword  0xf000, 0xf800

    add     r1, sp, #0x40
    ldrh    r2, [r1, #4]
    movs    r3, #1
    bics    r2, r3
    orrs    r2, r0
    strh    r2, [r1, #4]
    pop     {pc}
    nop
