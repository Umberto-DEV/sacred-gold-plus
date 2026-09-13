/* Sacred Gold Plus 1.2a — difficoltà PLUS sui Pokémon selvatici.
 * GPL-3.0-or-later.
 *
 * Regola (doc 13 §2.2):
 *     p_wild(B) = min(8, 5 + B/25)
 *     L         = max(B, min(cap, R(B, p_wild(B))))     [tabella SGP_TAB_WLD]
 * Precalcolata per ogni B in 0..255: a runtime è un solo `ldrb`.
 *
 * Il gancio sta DOPO la convergenza dei cinque tipi di incontro (terra,
 * frantumaroccia, surf, pesca, testata) e PRIMA dei filtri Unown,
 * Sguardofermo/Prepotenza e Repellente (doc 13 §4 P5): il Repellente valuta
 * quindi il livello EFFETTIVO, non quello nativo.
 */
#include "sgp_plus.h"

__attribute__((used, noinline, section(".text")))
u32 sgp_wild_level(u32 base)
{
    SgpStato *s = SGP_STATO;
    u32 v;

    s->hits_wild++;
    if (!s->active_wild) {
        return base;                       /* byte-identico alla 1.1 */
    }
    if (base == 0u || base > 255u) {
        return base;                       /* la tabella ha 256 voci: indice sempre un byte */
    }
    v = SGP_TAB_WLD[base];
    if (v > s->cap) {
        v = s->cap;                        /* prima il cap… */
    }
    if (v < base) {
        v = base;                          /* …poi il pavimento NATIVO, che vince (R-CAP) */
    }
    return v;
}

/* Trampolina per il sito selvatico.
 * Sostituisce esattamente 4 byte ("add r0,sp,#0x10" ; "ldrb r0,[r0]") con un BL.
 *
 * All'ingresso:  r7 = livello tirato (0..255), r4/r5/r6 vivi, r1..r3 morti,
 *                lr = libero, sp = frame dell'ospite, allineato a 8.
 * All'uscita:    r7 = livello effettivo, r0 = indice di slot (come prima),
 *                r4..r6 invariati. r1..r3 sono CLOBBERATI dalla chiamata C
 *                (AAPCS): il sito lo consente perché lì sono morti — la prima
 *                istruzione successiva è `lsls r0,r0,#3` e r1..r3 non vengono
 *                riletti (prove/estratti/disasm-wild-*.txt).
 *
 * Le due istruzioni sostituite non toccavano i flag; le `adds` di qui sì. Il
 * sito lo consente: vedi prove/estratti/disasm-wild-*.txt, l'istruzione che
 * segue riscrive i flag prima di leggerli.
 */
__attribute__((naked, used, section(".text")))
void sgp_wild_hook(void)
{
    __asm__ volatile(
        "add   r0, sp, #0x10\n"       /* istruzioni sostituite: sp è ancora quello dell'ospite */
        "ldrb  r0, [r0]\n"
        "push  {r0, lr}\n"
        "adds  r0, r7, #0\n"
        "bl    sgp_wild_level\n"
        "adds  r7, r0, #0\n"
        "pop   {r0, pc}\n"
    );
}
