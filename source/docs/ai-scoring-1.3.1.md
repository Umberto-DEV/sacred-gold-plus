# Post-KO AI: replacement scoring and immunity (1.3.1)

The implemented module and regressions are in `source/sgp131/ai_scoring.py`,
revision 5, integrated into the builder after UI and move changes. Evidence
below separates native unit execution, the later battle-loop correction and
bounded Android scenes. A unit pass does not establish natural execution of
every AI branch in a rendered battle.

## Type-calculation battle freeze — 6 November 2026

The preceding candidate could freeze while returning to the move menu, with
audio held on one note. The defect is in the `fairy_ai` integration at
`ov12_02252054`, rather than the save format. The Thumb BL installed at
`0x022520C6` also occupies `0x022520C8`; the loop backedge at `0x02252138`
still targeted retail address `0x022520C8`. From the second iteration it
therefore executed only the BL suffix with an unrelated LR. The first-error
trace shows a jump into data at `0x023D7836`, followed by a data abort in the
ability consumer at `0x0223AB22`.

The correction changes only byte `C6` to `C8` in the BNE at `0x02252138`
(`D1C6` → `D1C8`), targeting `0x022520CC`. The loop tail already computes
`r1 = 3*r4`, including its sentinel path: re-entry reuses that index and skips
both halves of the initial call. Resident payload, ABI, type table, ROM
geometry and save layout remain unchanged. The producer also authenticates
the complete loop tail, and independent readback checks the branch.

The public regression executes the complete native function in Unicorn on
V4 EN/IT, without replacing the loop with a stub. Ten cases per language cover
resistance, weakness, immunity, neutrality, dual typing and Fairy. Before the
fix all twenty cases reach the BL suffix; afterward they return with expected
flags, preserved stack/registers and exactly one helper call. A mutant that
restores the old branch is rejected even when its ROM hash is updated.
A separate experiment uses the melonDS interpreter, without JIT or cheats,
and a copied raw save loaded through Continue. A natural battle reproduces
the same fault chain; changing only that byte in the same state restores the
menu. This RAM mutation is a causal control, not acceptance of the formal
build or its save compatibility.

The cause does not depend on Houndoom or the League map: it is in the shared
AI type-check loop. On the IT candidate, eight direct BLs target `0x02252054`:
seven in overlay 10 (`0x0221F78E`, `0x0221FA3A`, `0x0221FAC8`, `0x0221FC44`,
`0x0221FCD4`, `0x0222017C`, `0x02220210`) and one in overlay 12's post-KO
replacement selection (`0x022589FC`). The first seven belong to
`ov10_0221F62C`, `ov10_0221F7F0` and `ov10_02220010`; all share the corrected
callee. Decoded-BL scanning agrees with the decompilation's callsites. Once
the faulty loop is reached, its second iteration executes the suffix; a Fairy
Pokémon is not required. Early exits, such as Struggle or Ground against
Levitate, are distinct paths. The twenty tests establish the shared callee,
not eight separate natural encounters, overworld-freeze causes, older-ROM
behavior or every possible emulator hang.

This diagnosis concerns the 1.3.1 candidate's League battle freeze. It does
not establish the same cause for the historical Latios freeze, reported on
versions predating the `fairy_ai` integration. **Latios is not proven fixed.**

The subsequent physical test used exact IT `c63cf9e9…afbedb`, retaining the
existing JIT and Compute settings. A raw-save copy completed SAVE/cold,
passed Weavile and Honchkrow, played one turn against Houndoom and reopened
the move menu. At that checkpoint the installed ROM was updated in place and
the current personal save returned to the field. The
[validation report](ui-1.3.1-validation.md) separates this scene from four
host EN/IT compatibility cells and historical checkpoints. Neither this IT
scene nor the later bounded EN Android smoke proves every AI behavior below.

## Scoring and immunity defects

After an opposing Pokémon faints, `ov12_02258800` (overlay 12,
`0x02258800..0x02258BA0`) chooses a replacement in two stages. Stage one sums
two `CalculateTypeEffectiveness` results (`0x0225264C`): attacks of the
candidate's first and second types against both visible target types
(40 neutral, 160 for 4×). It then truncates the sum to eight bits using
`lsls r0,#24; lsrs r0,#24` (`0x02258938`, `0x0225893A`) before comparing it
with the best score.

A candidate whose two types both hit the target for 4× scores
160 + 160 = 320, which becomes 64. This includes a duplicated monotype and
combinations such as Fighting/Ground against Rock/Steel. The strongest type
candidate can therefore lose to a weaker one. Across real helper types 0..17,
142 of 104,976 candidate-pair × target-pair combinations overflow, all at
exactly 320; every other sum is ≤255. This matches pokeplatinum's documented
“Post-KO switch-in AI scoring overflow” in `bugs_and_glitches.md`, but is
established here by bytes and execution, not resemblance. The V4 type table
has no type-9 (Fairy) rows, so that helper treats type 9 as neutral; the tests
still read the actual table.

The same switching routine calls `ov12_02252054` to test whether a move is
super-effective. If one type grants immunity and a later row makes the second
type weak, retail retains both `NO_EFFECT|SUPER_EFFECTIVE`. Examples include
Gligar/Electric, Aerodactyl or Skarmory/Ground, and Girafarig/Ghost. The
consumer can consequently choose a Thunderbolt reserve against Gligar instead
of an Ice Beam reserve.

## Switch admission and absorption abilities

A separate defect affected gate `ov10_022203A4`. Before deciding to switch,
the AI repeated partial checks for binding, Shadow Tag, Arena Trap and Magnet
Pull instead of using the normal contract. Arena Trap therefore blocked
Flying, Levitate and Magnet Rise; Shed Shell did not override the four
branches. Revision 4 replaces 16 bytes at `0x022203B4` with preservation of
`r0/r1`, the battler in `r2`, a Thumb BL to `BattlerCanSwitch` (`0x02255920`)
and branches to the original blocked/allowed continuations. The 536-byte
function is pinned by SHA-256 `2cc6ca06…5d1c0`; afterward it is
`17cdabc8…f0db4`.

The private reproducer really executes overlay 10 and overlay 12's authoritative
routine on six EN/IT images. Its 96 cases expose the false blocks while
retaining grounded, Iron Ball, Gravity, Shadow Tag, Magnet Pull, binding,
Sand Veil and no-trap controls. The 42 divergences also include Shed Shell
against the other branches; canonical digest `0a464755…3cf0a`. Stubs are
limited to leaf ability/type/item queries. This is not a rendered battle.

HG-B15 was another defect in `ov10_0221FE8C`: active/reserve ability checks
recognized only Flash Fire, Water Absorb and Volt Absorb. Two Thumb BLs at
`0x0221FF10` and `0x0221FFC6` now call a 20-byte helper at `0x0222B26C`,
after the static-init table `0x0222B268..26C`. It preserves exact matches and
adds only the Volt Absorb/Motor Drive and Water Absorb/Dry Skin pairs; Flash
Fire does not enter the normalized branch. The native matrix passes 96 cases
on six EN/IT inputs, with 24 pre-fix divergences and none afterward
(`2fd8a4fd…db778`). Existing RNG flow, scan order and fainted/Egg checks are
unchanged.

## AI script corrections

AI-WEB-03 affected Facade's Expert sequence in member 0 of `a/0/9/9`.
The status opcode used token 0 (target), whereas the move's damage script
reads the attacker. Native overlay-10 interpreter tests on EN/IT candidates
show a statused target receiving `+1` and a statused user receiving zero before
the correction. Only the token at `+0x5B68` changes 0→1; afterward the matrix
follows the user. Mask `0xD8` and delta `+1` remain identical; sleep and freeze
are negative controls. Falkner's Plus rematch has AI flags 7 and Swellow with
Flame Orb and Facade in variants A/B. The proof isolates the sequence:
natural dispatch, move choice, SAVE/cold and physical-device execution remain
outside that unit's acceptance.

AI-WEB-04 affected Expert dispatch. The table listed effect 151 (SolarBeam)
twice and failed to send effect 152 to the intact Thunder routine at
`+0x58A4`. Native EN/IT dispatch tests show Thunder missing that routine before
the fix. One word at `+0x2C00` changes 151→152. Afterward rain gives `+1`,
sun with RNG 50 gives `-3`, the 49/50 boundary is preserved and clear weather
is neutral. SolarBeam and Thunderbolt are negative controls and do not enter
the routine. Seven real trainers with Thunder have the Expert bit. Precomputed
resistance/immunity, natural selection, SAVE/cold and physical-device
execution remain outside that unit's acceptance.

AI-WEB-02 affected Metal Burst's Basic sequence. Before final
`CheckSortSpeed`, the script tried to predict order with two Stall checks and
two comparisons against item ID 107. That item is Shiny Stone, not delaying
item effect 107. The Stall shortcuts also contradict Lagging Tail/Full Incense
and two Stall users. The reproducer executes the real overlay-10 interpreter,
overlay-12 `CheckSortSpeed` and authenticated EN/IT item data. Thirty scenarios
per language include no effect, Shiny Stone, mixed combinations, double Stall,
two delaying items, ties/RNG, Trick Room, Quick Claw and Custap Berry. The
correction does not replace the ordering engine: it zeros the four relative
jumps at `+0x1DFC`, `+0x1E0C`, `+0x1E20` and `+0x1E30`, leaving opcodes intact
so every case reaches the existing final command. Before/after EN/IT matrices
also check cursor and termination. Natural encounters, move selection,
priority in full battle context, SAVE/cold and physical-device execution
remain outside that unit's acceptance.

## Before/after proof with native CPU instructions

The real function runs from its entry in Unicorn with V4 EN/IT overlay 12 and
ARM9. The synthetic scenario is inspired by the test plan, rather than a
natural encounter: a trainer has Rhyperior (Ground/Rock, slot 2) and Machamp
(Fighting/Fighting, slot 4), against Bastiodon (Rock/Steel). Types are read from
the ROM's personal NARC `a/0/0/2`. Both have a super-effective move through a
declared stub.

| Version | Scores observed at the real CMP | Choice |
| --- | --- | --- |
| Native | Rhyperior 180, Machamp 64 (320 & 0xFF) | Slot 2 |
| Patched | Rhyperior 180, Machamp 320 (`[sp,#0x4c]` remains 64) | Slot 4 |

Regressions are in `source/sgp131/test_ai_scoring_rom.py` (Class B) and
`test_ai_scoring.py` (Class A). Original RED identities, the rejected two-NOP
variant and GREEN logs remain in the maintainer's private evidence. The two
test modules contain the reproducing commands.

## Exact delta: revision 3, ten declared bytes and five instructions

Decoded overlay 12: base `0x022378C0`, length `0x37380` bytes. Before the
correction, `r0` holds the sum, which is truncated and later reloaded.

| Address | Before | After |
| --- | --- | --- |
| `0x02258938` | `0006` `lsls r0,r0,#24` | `0106` `lsls r1,r0,#24` |
| `0x0225893A` | `000e` `lsrs r0,r0,#24` | `090e` `lsrs r1,r1,#24` |
| `0x0225893C` | `1390` `str r0,[sp,#0x4c]` | `1391` `str r1,[sp,#0x4c]` |
| `0x02258944` | `1398` `ldr r0,[sp,#0x4c]` | `c046` `nop` |
| `0x02252202` | `0420` `movs r0,#4` | `0c20` `movs r0,#12` |

- `r0` retains the wide 32-bit sum. The following unsigned `cmp r1,r0` / `bhs`
  compares it with the best score; `str r0,[sp,#0x48]` stores the wide new best.
- `[sp,#0x4c]` receives the same eight-bit truncated value as before. Stage two
  reuses it when a move has no damage evaluation (ID 0 or
  `ctx[0x3E1+16*move]==1`), retaining the native-width value. An earlier two-NOP
  version (`0006000e`→`c046c046`) also left the wide sum in that word and was
  rejected: mutant `superseded_two_nop` fails readback and tests.
- `r1` is not live: after the store it is reloaded with `ldr r1,[sp,#0x48]`,
  used only by CMP, and neither the taken `bhs` branch
  (`0x02258960`: `ldr r0,[sp,#0x40]`…) nor fallthrough reads it before rewriting
  it. Eight bytes are declared for this part; five change value
  (`0x02258938`, `…3A`, `…3D`, `…44`, `…45`).
- The fifth halfword widens the check from `NOT_VERY_EFFECTIVE` to
  `NOT_VERY_EFFECTIVE|NO_EFFECT`. Weakness/resistance cancellation remains
  unchanged, while immunity takes precedence. Of its two declared bytes only
  the immediate at `0x02252202` changes. Six logical bytes change in total.
- Guards cover 20 bytes at `0x02258934`, 32 at `0x022521F8`, and both function
  SHA-256 values (`45b8c7da…69da84`, `eb5c3828…52a5`). Post-fix values are
  `d2cfa7a4…7369c2` and `11d5bacf…a9a2e0`; patched overlay
  `daa14016…fdef19` is identical in EN/IT.
- `sgp12.overlay.applica` recompresses BLZ in place. On V4 the stream remains
  161,572 bytes in a 161,792-byte slot. y9 word `0x01027724`, FAT entry, ROM
  length and header CRC16 remain unchanged. Only the compressed overlay stream
  changes: 93,419 differing file bytes, with no FAT/y9/header change. Resulting
  EN ROM hash `61f75f65…d59cf`, IT `16083d75…e6c37`.
- `verify(before, after, receipt)` independently reads the bytes rather than
  trusting the applier's verdict: project and ndspy BLZ decoders agree;
  preimage, exactly ten declared bytes and zero other logical changes,
  consistent y9/FAT, no other NitroFS/ARM9 entry changes, `0xFF` padding and
  header CRC are checked.

## Preserved behavior

The same `Battler_GetRandomOpposingBattlerId` RNG call occurs once, with the
same accessors, call sequence and arguments for non-overflow decisions
(400 random scenarios). Ties still favor the first candidate. Fainted, Egg,
empty, current and pending slots (`ctx+0x219C`, `+0x21A4`, including a partner)
retain their exclusions. Super-effective-move checks, fallback to the second
candidate and damage stage, and zero/one replacement cases are preserved.
This common arithmetic correction adds no AI knowledge, allocation or
Normal/Plus gate.

Stage-two eight-bit damage truncation (`CalcMoveDamage`, damage >255) is
**outside this correction**; see
`test_stage_two_damage_conversion_is_not_part_of_the_fix`.

Leaving any of the five instructions unchanged, or using the two-NOP variant,
fails a behavioral control
(`test_each_instruction_of_the_delta_is_load_bearing`). The Keen Eye correction
uses disjoint windows and produces the same image in either composition order
(`test_composes_with_keen_eye_seam_in_either_order`, test-only owner address).

## Stage two and the stale word

`[sp,#0x4c]` always holds the last evaluated candidate's eight-bit value, as in
native code; the test checks equality at each comparison. That last candidate
still depends on stage-one elimination order. Correcting an overflow changes
that order because elimination now uses the true score. For Rhyperior 180 and
Machamp 320, with no super-effective moves and Rhyperior's first move lacking
damage, native leaves 64 (Machamp), whereas the correction leaves 180
(Rhyperior); stage two then chooses slot 2 rather than 4
(`test_stage_two_inherits_the_new_stage_one_elimination_order`). With two
320-score candidates, native and corrected order match and stage two remains
native; the rejected two-NOP version chose differently
(`test_stage_two_stale_word_and_choice_stay_native`). A 1,500-decision random
differential with move ID 0, `ctx` flag 1, damage, immunity, fainted/Egg/current/
pending cases matches the model “wide stage one, narrow `[sp,#0x4c]`”.

## Callers and global scope

BL/BLX and literal-pointer scanning for `0x02258800` in ARM9 and all 129
overlays finds only two callers resident with overlay 12: `ov010` at
`0x022205FE` (trainer AI, around line 9207 of pret assembly) and `ov012` at
`0x0225F8E8` (opponent controller `ov12_0225F8AC`, around line 14203).
Singles, doubles, partner/multi and facilities therefore use the same function.
Other raw matches in overlays 045, 049, 091, 092 and 093 occupy overlay 12's
RAM range and are never resident with it.

## Execution boundaries

Python stubs at native entries: `0x0223A7E4` GetBattleContext,
`0x0223A7E0` GetBattleType, `0x0223AB6C` GetBattlerIdPartner,
`0x02253DA0` GetRandomOpposingBattlerId, `0x0223A834` GetPartySize,
`0x0223A880` GetPartyMon, `0x0206E540` GetMonData, `0x0224EDE0` GetBattlerVar,
`0x02258BB4` move type, `0x022527CC` GetBattlerAbility,
`0x02255830` GetBattlerHeldItemEffect, `0x02252054` super-effective check,
`0x0223AB1C` GetFieldSide, `0x02256FF8` CalcMoveDamage and `0x02251D28`
modifiers/immunity. The general consumer retains its `0x02252054` stub;
HG-B13 tests separately execute the original/corrected function and forward
its result to the consumer. Native execution includes the selection function,
`CalculateTypeEffectiveness` (`0x0225264C`) with divisor `0x020F2998`, and
`MaskOfFlagNo` (`0x020726C0`). Every run checks r4–r11, SP, caller area,
unchanged battle context and compare carry equal to unsigned best ≥ score.

## Limits and later evidence

The scoring/script matrices are CPU proofs on synthetic scenarios, not
rendered natural battles. Logical Keen Eye composition and the EN/IT ROM
pipeline do not substitute for those battles. Unit tests do not measure
decision duration on a device, validate every older save through
Continue → SAVE → cold restart, or establish stage-two damage correctness.
Wins or greater damage are not measurements of AI intelligence.

The later twenty-case type-loop regression and the named IT battle scene
above address that separate integration freeze. The exact-current EN Android
copied-save smoke in [Android validation](android-validation.md) preserves its
own candidate/APK identity and 25 semantic checks; it does not execute or
accept every AI unit. Historical Latios remains unisolated.

## BLZ verifier integration correction

Previously, a modified footer that decoded to the same logical bytes could
pass after receipt hashes were updated. The reader now requires both hashes
and the project's canonical BLZ encoding, derived from ROM bytes and the
original FAT limit. Focused data/receipt, native, caller and mutant suites
passed without skips; the footer negative covers EN and IT. These are the
recorded suite results, not new runs performed for this English revision.
