/* Sacred Gold Plus, GPL-3.0-or-later.
 * SOLO al sito ov001 0x021E6BBE: r4=FieldSystem, r7=direction.
 * Il consumatore del bit Cascata, ov01_021F24F4, può usarlo soltanto con
 * direzione 1 (sud) e PlayerAvatar.state 2 (Surf). Negli altri casi non
 * decifrare fino a sei Pokémon per un risultato che verrà ignorato.
 * Nessuna cache: Surf continua a leggere la squadra corrente.
 */
.syntax unified
.cpu arm946e-s
.thumb
.text
.balign 4
.global sgp_cerca_cascata
.thumb_func
sgp_cerca_cascata:
    cmp r7, #1
    bne 1f
    ldr r2, [r4, #0x40]  /* playerAvatar, vivo nel chiamante */
    ldr r2, [r2, #0x18]  /* state, verificato anche nel getter nativo */
    cmp r2, #2
    bne 1f
    ldr r3, =0x020542e9
    bx r3
1:
    movs r0, #255         /* sentinella nativa: nessun Pokémon con la mossa */
    bx lr
.ltorg
