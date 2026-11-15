# Sacred Gold Plus 1.3.3 — candidate fixes

This describes a candidate, not a published release. Five current candidate
identities passed scoped readback and seven bounded raw-save/cold cycles on five
original fixtures. Natural battle/pivot and physical-device validation remain
pending. Two earlier EN composition attempts stopped at resource guards before
the revised verifier was used.

## Onboarding version title

The active Continue/New Game prompt uses `Sacred Gold Plus V1.3.3`. The
1008-byte UI-owned bank changes its title entry 20 while preserving the other
28 raw strings and the adjacent 16-byte canary. Retired entry 0 remains inactive
and historical; the DS header/banner is unversioned. This is not a global
replacement of historical strings.

All five successor images were independently read back. A whole-file comparison
with the first, pre-onboarding candidate shows identical bytes outside that bank,
including unindexed gaps. EN and FR Continue prompts were visually reviewed on
host copies; the New Game path's shared title is supported by static evidence,
not a new visual run. The [technical validation](source/docs/validation/uturn-fix-1.3.3.md)
records the identities and limits.

## U-turn and flinch-item compatibility

Two defects were found in the existing U-turn/flinch helper:

- On an unmarked fallback, the modifier getter could receive altered battler
  and flag arguments. An incoming flinch item could therefore use the wrong
  modifier.
- A single-bit snapshot test could mistake a negative native damage value for
  an item snapshot. For example, −200 could be consumed as a snapshot and
  incorrectly enter the flinch/RNG path.

The candidate preserves the original getter arguments on fallback and recognizes
snapshots only when the upper 16 bits equal 1. The existing producer and save
format are unchanged. See the [technical validation](source/docs/validation/uturn-fix-1.3.3.md)
for the finite tests, native counterfactuals and important domain limits. A full
natural pivot has not yet been qualified. The five successor identities and the
limits of their readback are recorded in the technical validation.

These fixes concern the existing Plus helper. In the counterfactual cases,
the corrected decisions restore intended requests and avoid unintended ones
to a modeled flinch script. They do not prove that the script ran or a target
lost its turn; the player-visible effect depends on the actual battle sequence,
gates, immunities and turn order. No reduction in crashes or improvement in
gameplay speed, battery use or game memory has been demonstrated.
