# 1.3-dev systematic playtest plan — 28 October 2026

**Goal:** find and fix reproducible gameplay, persistence and stability defects
before considering publication, with particular attention to wild caught icons
and the seven revised trainer teams.

**Architecture:** execute fixed-input campaigns against frozen EN/IT ROMs and
copies of raw saves; combine native melonDS observation with focused production
ARM tests and independent read-back gates. A successful emulator exit alone is
never a successful gameplay test.

**Tech stack:** pinned melonDS interpreter/software renderer, native game
functions for declared scene setup, Python observation/gates, Capstone and
Unicorn for bounded instruction-level checks. REA's evidence discipline applies;
its native engine is not connected in this session.

**Spec:** the maintainer's approved 1.3 features in
[the expansion plan](expansion-1.3-plan.md), followed by the explicit request for
deep playtesting, screenshots, minimal runtime overhead and fixes before release.

## Global constraints

- Work directly on `main`; preserve existing staged work and published 1.2.5.
- Freeze and hash each candidate, fixture, script and harness. Changes create a
  new candidate; do not relabel old evidence as a test of the new one.
- Never modify original saves. Distinguish ordinary inputs, scene setup through
  native functions, instruction-level seams and actual gameplay assertions.
- Preserve progress, Pokémon, Bag extensions and Plus settings. Verify native
  SAVE followed by cold Continue for persistence claims.
- Each defect needs reproduction, root cause, a failing regression check, a
  minimal correction and a passing repeat. Do not optimize speculatively.
- Record skipped, blocked and untested cases separately. Finite coverage cannot
  establish that every possible adventure or emulator configuration is safe.
- No publication, new release tag or replacement of published assets in this
  campaign. Screenshots must come from the real candidate.

## Execution and review gates

| Area | Procedure and assertions | Completion evidence |
| --- | --- | --- |
| 1. Baseline and method | Record hashes, existing staged diff and inputs; research primary testing and ROM-hack references; retain actual screens. | Reproducible manifest, plan and source links. |
| 2. Wild and trainer battle HUD | Reach real wild encounters with owned/unowned species; compare Dex flags and rendered HUD; exercise escape/KO/capture when reachable. Include both languages and special HUD paths at the ARM layer. | Encounter identity, HUD pixels/native state, field return, untouched fixtures, replay comparison. |
| 3. Trainer strategy | Read actual modified move/species/item/AI data for all nine substitutions; test native party construction and actual AI execution, level/stat correctness and intended synergies. Compare baseline/Normal/Plus with declared scenario setup. | Per-trainer rationale and observations; distinguish completed battles from construction or isolated damage tests. |
| 4. Menus and field | Exercise native menus, Guide categories/detail/link/back, Plus settings, movement and map transitions. Repeat high-risk open/close sequences and invalid/rapid input. | Reached-state assertions, screenshots, field input response, reserve guards and released Guide handles. |
| 5. Training and persistence | Expand IV/EV/courses to boundary values, rejection/cancellation, both slots, clock changes, withdrawal and old saves. | Transaction invariants, native SAVE/cold restart, no input fixture mutations; explicit runtime versus seam coverage. |
| 6. Stability and cost | Run crash gates plus state-specific progress checks, bounded stress, deterministic replay and matched baseline comparisons. Audit resident/code/content budgets. | No exception tail, expected terminal state, stable ownership/guards, measured costs with limits. |
| 7. Integration | Re-run applicable project suites with mandatory compiler and real private inputs; investigate every failure; fresh whole-change review. If code changes, rebuild and repeat affected native campaigns and save matrix. | Results ledger, exact candidate hashes, unresolved risks and release decision. |

Tasks 2, 3 and the runtime investigation in 5 may run independently in private
output directories. The main agent owns production corrections and integration.
After each area, evaluate actual observations before moving its status to done.

## Test design

Use equivalence classes (owned/unowned, enabled/disabled, sufficient/insufficient
resources), boundary values (0/31 IV, 252/510/1512 EV, time thresholds), transition
tests (open/cancel/reopen, enroll/advance/withdraw/save/reload), and negative
controls that prove a gate rejects an unmet prerequisite. Add cases when evidence
reveals a new risk rather than inflating counts with identical successful runs.

The existing [validation report](validation-1.3-dev.md) is prior evidence, not a
substitute for this campaign. In particular it explicitly lacks real wild battle
coverage and completed balance battles. Those gaps lead this pass.

## Review focus

Check false-positive test verdicts, deterministic setup, out-of-bounds native
access, allocation/printer lifetime, partial transactions, save ownership,
level/stat consistency, actual AI behavior and whether each claimed optimization
has a measured benefit. Report remaining scope honestly, including hardware,
wireless, long real-time play and adventure paths not exercised.
