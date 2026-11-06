/* Keen Eye ignores every change to the target's evasion; Unaware keeps its
 * native effect. Called from the single seam in the battle accuracy check
 * (overlay 12, 0x0224BD5C) in place of the call that tested Unaware alone.
 *
 * The native getter applies Gastro Acid and the other suppressions, so a
 * suppressed Keen Eye or Unaware returns 0 here exactly as before. Accuracy
 * drop protection lives elsewhere (stat-change command) and is untouched.
 */
#ifndef SGP_GET_BATTLER_ABILITY_ADDR
#error "SGP_GET_BATTLER_ABILITY_ADDR must name the native Thumb getter"
#endif

#define SGP_ABILITY_KEEN_EYE 51u
#define SGP_ABILITY_UNAWARE 109u

typedef int (*sgp_battler_ability_getter)(void *ctx, int battler);

unsigned sgp_ignore_target_evasion(void *ctx, unsigned attacker)
{
    unsigned ability = (unsigned)((sgp_battler_ability_getter)(SGP_GET_BATTLER_ABILITY_ADDR | 1u))(ctx, (int)attacker);
    return ability == SGP_ABILITY_KEEN_EYE || ability == SGP_ABILITY_UNAWARE;
}
