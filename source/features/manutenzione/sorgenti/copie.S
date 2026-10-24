/* Sacred Gold Plus, GPL-3.0-or-later.
 * Estensione della sola ANIM2 v5d identificata dal manifesto.
 * +0x20 dello stato era riservato: contatore dei proprietari di copie OAM.
 * Il costruttore comune alloca un proprietario anche con zero sprite:
 * contiamo allocazioni/distruzioni, non il numero di sprite al suo interno.
 * Chiamate su coda principale, non interrupt; nessun task aggiuntivo.
 */
.syntax unified
.cpu arm946e-s
.thumb
.text
.balign 4
.global sgp_copia_inizio
.thumb_func
sgp_copia_inizio:
    /* Hook della BL Heap_Alloc nel costruttore: conserva heap/size, poi
     * neutralizza tutti gli slot PRIMA che siano lette coordinate/grafica.
     * sgp_pulisci verifica identità e canali nativi e libera lo slot.
     * Alla ripresa ANIM2 ricrea fase/inviluppo/attesa senza posa residua. */
    push {r0, r1, r4, lr}
    ldr r4, =0x023dbbe0
1:
    ldr r0, [r4]
    cmp r0, #0
    beq 2f
    ldr r3, =0x023db501  /* sgp_pulisci v5d */
    blx r3
2:
    adds r4, #32
    ldr r3, =0x023dbc60
    cmp r4, r3
    blo 1b
    ldr r2, =0x023dbbc0
    ldr r3, [r2]
    adds r3, #1
    str r3, [r2]
    pop {r0, r1}
    ldr r3, =0x0201aa8d
    blx r3
    pop {r4, pc}
.global sgp_copia_fine
.thumb_func
sgp_copia_fine:
    /* Un hook per ciascuno dei due distruttori; decrementa DOPO Heap_Free.
     * Non azzerare quando cambia BattleSystem: copie ancora vive devono
     * restare contate. Il teardown nativo passa da questi distruttori. */
    push {r4, lr}
    ldr r3, =0x0201ab0d
    blx r3
    ldr r2, =0x023dbbc0
    ldr r3, [r2]
    cmp r3, #0
    beq 3f
    subs r3, #1
    str r3, [r2]
3:
    pop {r4, pc}
.global sgp_idle_copie
.thumb_func
sgp_idle_copie:
    push {r0, r1, r4, lr}
    ldr r4, =0x023dbbc0
    ldr r4, [r4]
    cmp r4, #0
    beq 4f
    ldr r3, =0x023db621  /* accessore opzione v5d: guardia e load_status */
    blx r3
    cmp r0, #0
    beq 4f
    /* OFF->ON: il task vanilla può aver lasciato il proprio yOffset.
     * Neutralizza quel solo canale se non zero e il Pokepic è vivo.
     * SetAttr(4) è precisamente questo store, senza altri effetti.
     * Nessun altro canale nativo viene toccato; dopo il reset non scrive. */
    ldr r1, [sp, #4]
    ldr r1, [r1, #0x20]
    cmp r1, #0
    beq 5f
    ldrb r2, [r1]
    lsls r2, #31
    beq 5f
    ldrh r2, [r1, #0x2e]
    cmp r2, #0
    beq 5f
    movs r0, #0
    strh r0, [r1, #0x2e]
5:
    pop {r0, r1, r4, pc}
4:
    pop {r0, r1}
    ldr r3, =0x023db72d
    blx r3
    pop {r4, pc}
.ltorg
