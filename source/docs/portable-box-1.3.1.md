# Portable storage in 1.3.1

**Portable storage is active in the current player profile.** R or its touch
command in the ordinary field Party menu opens native PC storage. The current
ROM identities and acceptance are maintained in
[the validation report](ui-1.3.1-validation.md); Summary controls and configurable
rematches remain separate, inactive owners. This document preserves the module's
ABI, activation safeguards and the exact scope of older component/runtime checks.

## Player behavior

The ordinary Party selection prompt includes `R: Box`. A new physical R press
(including L=A mode) or touch closes Party through native Cancel, opens PC mode 2
(Move Pokémon), then reconstructs Party with its cursor on the same slot,
clamped to the remaining count. B returns to the original field position.
Deposit, withdrawal, moving, last-usable-Pokémon, Mail, Ball Capsule and full-Box
rules remain native. The maintainer accepts native deposit/withdrawal healing of
HP, PP and status; it is not disabled. No save field or setting is added.

## Hook and lifetime contract

Technical baselines forward natively while activation words are zero. Active
builds enable the following installed hooks:

| Hook | V4 site, EN=IT | Helper |
| --- | --- | --- |
|Party launch|BL to `FieldSystem_LaunchApplication` in `PartyMenu_LaunchApp_Unk1`, `0x0203E572`|`sgp_box_launch_app`: launch and bind field/owner/args, generation++, for all five start-menu callers including Summary return|
|Other Party launch paths|No hook; lazy binding|`ensure_bound`: itemless Bag return (`start_menu.c:1074`) and refused held-item swap (`party_menu.c:2625`, context 10→0) require live identity|
|State 1|BL to `PartyMenu_Subtask_MainNormal`, `0x0207909C`|`sgp_box_party_main`: validate/input/request `RETURN_0`, state 32|
|Party return|Callback entry `0x0203CA9C`, eight-byte hook plus trampoline|`sgp_box_party_return`: consume request or run original callback|
|PC return|Module-owned callback|`sgp_box_pc_return`|
|Prompt|BL to `PrintMessageOnWindowEx` in `PrintMessageOnWindow32`, `0x0207DAD2`|`sgp_box_prompt_print`|

The instruction-aware callback trampoline re-encodes the BL at entry+6 and
resumes at entry+12. Resuming at+8 would enter the middle of that BL. With
`requested=0`, the gate returns before any native call: r4–r11, SP, return value
and observable memory match native behavior for all 32 `selectedAction` values
and 25 contexts under Unicorn.

Lazy binding occurs on message 29 rendering or first input-enabled state 1 when
context 0 has a completely live identity: `args->fieldSystem` and
`args->fieldMoveCheckData - 0x370` identify the field/owner; current field task
(`field+0x10`) has that owner environment; `owner+0x380` holds these args; owner
waits for the application (state 5) and native Party callback `0x0203CA9D`.
It never binds during a request or while PC is open. Itemless Bag return
therefore shows `R: Box`. Refused item-swap return becomes ordinary before its
context 0 prompt has printed, so R stays inactive until the next native message 29
print. A probe-written request before binding is discarded and counted as a
failure, never executed.

A valid request also requires the start-menu caller, no button animation and
`ELIGIBLE` access policy. Its sequence is:

1. Party state 1 chooses `RETURN_0`, state 32, native closing fade.
2. On return, allocate 12-byte `PCBoxArgs` on heap `0x0B` **before** freeing Party
   args. Failure drops the request and runs native callback with args still live.
   Otherwise free once, launch `PCBox_LaunchApp` and set `sgp_box_pc_return`.
3. PC return runs native full-Box notification `sub_02093070`, frees PC args once,
   calls `PartyMenu_CreateArgs` directly, checks NULL before all dereferences,
   initializes the three fields formerly set by its wrapper, and launches via
   the Plus wrapper to rebind ownership. Cursor is clamped; native callback returns.
4. Failed Party reconstruction calls `FieldSystem_LoadFieldOverlay` and chooses
   `RETURN`, exactly the native Cancel pair, without launching/dereferencing NULL.

The positional HM data at owner+`0x370` depends on avatar/front object/metatile.
`FieldMove_InitCheckData` is deliberately not called: native Party→Summary→Party
also preserves it. Reserved `refresh_field_data` stays 0 and has no reader.

## Access policy

Access needs positive evidence of an ordinary field from the verified caller;
unproven contexts remain denied until attested in the receipt.

| Signal | Required source/value | Denial |
| --- | --- | --- |
|Owner `inhibitIconFlags +0x34C`, `unk_350`|Ordinary StartMenu: SAVE enabled, entries 7/RETIRE inhibited, no bits outside {Pokédex, Pokémon, Bag, 7, RETIRE, Pokégear}|`SPECIAL_ACTIVITY`: Safari, Bug-Catching Contest, Pal Park, Battle Tower partner room, Colosseum, Union|
|`FieldSystem.mapLoadType +0x70`|`MAP_LOAD_TYPE_OVERWORLD=0`|`SPECIAL_ACTIVITY`, including special type 5|
|`FieldSystem.frontierFsys +0xA0`|NULL; nonnull during Frontier activity (`scrcmd_9.c`)|`SPECIAL_ACTIVITY`|
|`FieldSystem.linkBattleRuleset +0xA4`|No link ruleset|`SPECIAL_ACTIVITY`|
|Escort mode|`Save_VarsFlags_CheckHaveFollower(Save_VarsFlags_Get(saveData))`, same as `ScrCmd_CheckEscortMode`, flag `0x961`|`SPECIAL_ACTIVITY`|
|Avatar state +`0x18`|`travel_mask`, default `0b11` for walking/cycling|`UNPROVEN_TRAVEL`: Surf/other states|
|Context evidence|Installer-written `context_proof=1` from measured capture with `sha256`, `origin`, `capture_file`, played `capture_rom_sha256`, `build_id`|`UNPROVEN_CONTEXT=5`|

Context evidence covers limitations of static signals: Elite Four challenge
rooms, non-Frontier facilities, special maps using ordinary flags and travel.
Without it the installer refuses `bridge`, `input` and `prompt`. Synthetic proof
requires test-only `allow_synthetic_proof` and records `synthetic-for-test`.
Battle/trade/event selections, Bag/TM/HM, move learning and evolution do not
have a live ordinary start-menu context 0 and are not bound (`WRONG_OWNER`).
Denial draws no command and allocates nothing. There is no reason label.

## Native interface

Native prompt `Choose a Pokemon.` / `Scegli un Pokemon.` stays in window 32,
160×16 px at (16, 168), font 1. After printing it, the helper adds `R: Box` at local
x 112 with the same font/colors: native prompt 98/97 px, gap 14/15 px, suffix 33 px
ending 145 and 15 px right margin. It follows the Summary legend's button-label
style without new palette/frame. Native Cancel at x≥200 is separated by 28 px from
touch bounds `[124,172)×[168,184)`, disjoint from the real native rectangles at
`0x02110104/0x02110128`. It draws only for message 29/window 32 and `ELIGIBLE`.
Any other native message overwrites the whole window and removes it. Private
font renders are design artifacts, not runtime captures.

Accepted R/touch plays native `SEQ_SE_DP_SELECT` 1500, then the native Cancel
fade. The command is text rather than a sprite: it has no press animation or
drawn touch rectangle. Its visual feedback is immediate closure. A separate
frame/highlight would require another window/sprite and separate UI validation.

## Installer, allocation and receipts

```python
portable.prepare(data, language, work, *, allocation, preimage_sha256,
                 activation=None, context_proof=None, candidate_sha256=None,
                 allow_synthetic_proof=False)  # returns (rom, receipt)
portable.measure(work)
portable.verify(before, after, receipt)
```

The base must come from a `sgp131.reserve.allocate` receipt for
`portable-box.runtime`, rechecked against current policy, same-language V4,
unconditional owner names and exact allocation assignments; zero-looking memory
is not ownership. The conditional slot becomes grantable only after
`cold-ui-guide-retirement-v1` proves complete retirement of the old Guide.
`preimage_sha256` must match the replaced input bytes. Earlier UI stages are
accepted when consumed ranges match; `test_portable_rom.RealUiComposition`
uses actual UI output. Guards pin native functions/ranges/hooks, require aligned
single-segment ARM9 placement within the allocation and away from hooks, confine
all deltas to five owned regions, and independently recompile during `verify`.

Measured proof binds `capture_rom_sha256` to explicit `candidate_sha256` of the
captured inert candidate and to declared `language`. The receipt records both
hashes, `candidate_relation` (`stage-inert-output`/`composed-candidate`, recomputed
from bytes) and `function_state` (`inert`/`active`, recomputed from installed
words). Review/Android process status is not encoded as program state.

Defaults for `bridge`, `input`, `prompt`, `context_proof` are zero and
`travel_mask=3`, preserving native behavior. Installer **and runtime** enforce
input→bridge, prompt→bridge+input, and any enabled path→context proof. A visible
nonfunctional command is rejected. Users cannot set proof manually.
Reason 5 adds `UNPROVEN_CONTEXT` to 0–4 (`ELIGIBLE`, `WRONG_OWNER`, `BUSY`,
`SPECIAL_ACTIVITY`, `UNPROVEN_TRAVEL`); it is recorded, not interpreted elsewhere.
`verify(..., require_measured=True)` rejects test proof by default; tests alone
opt out. The module validates evidence shape/identity, not capture existence.

Clang 21 Thumb `-Oz` measurements: code/record/label 2908 bytes, trampoline 44,
total 2952 aligned 4, maximum stack 48, transient record 64 plus config 32 inside
that compartment, no extra allocated segment. PC args 12 bytes and native Party
args `0x44` use heap `0x0B`; PC args free before reconstruction, Party args live
with the rebuilt menu. The corrected 2952-byte payload fixes `SG-BOX-NULL`:
NULL reconstruction returns to field without launch or dereference. Internal
later overlay-manager allocations still need separate heap-pressure coverage.

## Validation boundaries

Host tests (`sgp131/test_portable.py`) cover pins/ABI/trampoline/compiler/installer.
`features/portable-box/test/` executes installed/native ARM on synthetic
FieldSystem/owner/Party/args with heavy services modeled.
`sgp131/test_portable_rom.py` checks EN/IT installation/readback and full-image
confinement in memory. None is physical-device coverage.

Historical checkpoints retain these identities:

- Before HG-T10: EN `5c561184…2f15` / IT `c5a45d16…77f97` reached `PC_RUNNING`
  in 4332 headless frames with unchanged copied save, 59/59 feature ARM,
  26/26 package and 26/26 ROM tests; that IT also had a separate Android SAVE/cold
  cycle on a copy.
- HG-T10 candidates: IT
  `35d459e3fcf7cf127d6ff0aec94a5f502accfce390b2455b83fe189a5ca088f4`
  (159029292 bytes), EN
  `02cccfbfc49b6addddba90385634ffdfde22b9ff3fbae3d85ae8f5603c5bf0af`
  (152786376 bytes). Exact IT melonDS Android on Mac smoke completed
  Continue→field→Party→R→native PC→field without SAVE. Exported copy and original
  fixture retained SHA-256
  `553925da5f1814b3ebba587f383b4197381d5bc040ba7b8d8208c1ca8a7fb3ce`.
  This pair also changed Lugia's map 244 scene resource version to 8 via three
  overlay 2 seams, preserving Ho-Oh/other maps at 7, geometry/reserve/save layout.
  Synthetic Lugia consumers/Ho-Oh control were not the full historical-freeze
  reproduction, complete scene or physical-device test.
- Older IT `420ec8b8…f059a` demonstrated physical Box use with the 3020-byte
  predecessor; subsequent installed IT `171b53b6…d64a0` belonged to a later
  historical checkpoint. Neither is a claim about today's installed files.

Newer accepted checkpoints are recorded only in the current validation report;
the above SAVE/cold/device results are not transferred to a successor hash.
The broader matrix still distinguishes R/touch, deposit/withdraw/move/cancel,
50 cycles per language, heap pressure, denied contexts, follower/HM/Surf policy,
SAVE/cold on preserved copies. Follower refresh uses native Party-close behavior
and requires its own observation. `prompt_shown` derives from window 32 printing;
a native clear without message 29 reprint could leave it set and needs a targeted
check. No reason text fits the 48 remaining pixels without a new design.

`features/portable-box/tools/run_probe.py` and `verify_probe.py` reproduce/check
the harness. The verifier recalculates verdicts from `runtime.log` hashes,
repeated READs and a third replay pass; input-R/touch require the same PC
observation block plus `tap R` or an in-bounds touch in the script. Coordinated
forged logs/observations cannot be distinguished offline from a genuine run;
only rerunning the same ROM/save/script establishes that. These probe results
are not Android runs.

The final builder must call `portable.candidate_gate(final_rom, receipt)`:
`portable.inert_view` zeros only its activation words, and the resulting final
hash must equal captured `candidate_sha256`. The relation label alone does not
attest this; invented-candidate tests pass prepare but fail the gate.
`portable.slot_preimage_from_v4(v4, language, allocation)` derives expected bytes
from exact V4 instead of hashing the current input's own slot. Legitimate
intermediate residue needs a fixed stage manifest hash as `preimage_sha256`.

Clang is pinned by version/hash. The separate controls verifier also pins its
charmap and rebuilds receipt geometry/variant/flags; that is not a portable-text
ownership shortcut. Caller census sees static Thumb BLs, not ARM BLX/literal-pool/
overlay calls. Pin audits run before installation; installed sites no longer
match old pins. Transitive native callees remain outside individual pins; safety
relies on the verified closed set of other-stage writes.
