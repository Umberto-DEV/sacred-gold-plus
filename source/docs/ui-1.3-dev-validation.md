# 1.3-dev interface integration validation

Aggiornamento del 29 ottobre 2026: la successiva
[verifica funzionale Android](android-1.3-dev-validation.md) conclude la campagna
corrente con 49 checkpoint accettati. Pin, conteggi, risultati e limiti di questa
tappa precedente restano quelli documentati sotto.

28 October 2026. Final private candidate **v8**, built from unchanged 1.2.5 EN/IT.
This records the interface follow-up to the [earlier systematic playtest](playtest-1.3-dev.md).
It does not replace that report or relabel its battle observations as new runs.
The [plan](ui-1.3-dev-plan.md) and [native interface contract](hgss-ui-contract.md)
record the approved scope and reference research.

| Language | Bytes | SHA-256 |
|---|---:|---|
| EN | 142207848 | `7673a1dfd520df0f2069165cf2120b79eed1f97b7016ffc9231ad64207e7e39f` |
| IT | 147732328 | `3bcd4570689f7576acfe963d3c8ce08236075d3973c9c21e965122009302f567` |

The EN build was repeated from its base and produced identical bytes. Both build
receipts match the final source snapshot. Previous v5, v6 and v7 files and
original save fixtures were preserved. No release, published file or save format
was changed.

## Player-visible result

- Guide uses the native 40×26 frame, normal/selected palette and centered book.
  Touch and X/D-pad/A reach the same nine-frame page-turn confirmation.
- Native fonts and frames surround a highlighted subject, spaced rows, page/entry
  counts, explicit back/page controls and contextual references. All 429 entries
  retain their IDs and facts; detail text wraps to 208px with inner margins.
- Plus has an always-visible button in native Options, supporting both touch and
  SELECT. This is the maintainer's approved fallback. Native Options and Plus
  retain separate pending-edit transactions; no misleading shared page counter
  or save-layout change was introduced.
- The consultant is an orange variation of the native delivery model, near the
  lower-left plant at (2,10) in Violet and Blackthorn Marts. It has a dedicated
  sprite ID. Original postmen and all existing NPC resources remain intact.

## Defects found and corrected before delivery

Independent review found two regressions in intermediate candidates. Both have
failing regression evidence followed by passing corrected tests.

1. The Guide's BG5 window replaced the lower tile row of the Options label.
   Drawing the icon on underlying BG4 preserves native BG5 labels. Native
   resource guards pin the shared tile allocation, solid background and palettes.
   Final native label and unrelated menu pixels compare exactly with 1.2.5.
2. B/X during touchscreen confirmation cleared custom selection but left native
   touch command 32 pending. The original input handler prioritizes touch commands
   and does not consume32, preventing normal closure. Cancellation and menu
   invalidation now release only that owned command, using the live FieldSystem.
   The actual original ARM input handlers reach native CLOSE after the fix.
   Tests cover all three dispatch orders, replacement/excluded menus and
   preservation of unrelated native touch commands.

## Final-candidate verification

| Area | Executed evidence | Result |
|---|---|---|
| Project runner | 780 collected: 633 executed, 147 explicitly skipped | All executed tests pass; every 1.3 suite runs |
| Italian native training | 25 additional compiled ARM/native-getter tests using v8 symbols | 25 pass |
| Complete Guide | 429 entries per language; 488 EN / 495 IT pages ; 117/122 reference roundtrips | 1594/1611 cursor assertions pass |
| Deterministic replay |Complete EN Guide campaign repeated |Trace and before/after RAM byte-identical |
| Guide stress | 64 open/close cycles per language, 8 actual native Options/Plus roundtrips each |All handles released, font restored, canaries/settings/Bag/SRAM unchanged |
| Controls and pixels |EN/IT touch, X/D-pad/A, B/X pending cancellation, normal/selected/pressed states |Pass; 3 distinct confirmation captures; native labels retained |
| Adjacent applications |Guide → party/Summary EV/IV → Bag → Pokégear → Options/Plus → field, EN/IT |Stats restored pixel-for-pixel; native data and SRAM preserved |
| Plus/first game |8 runs: navigation, active-printer race, fresh New Game/save and cold Continue ×2 languages | 86,432 frames; state, preview pixels and raw saves correct |
| Older saves |7 cases from 1.2.5 through ordinary Continue, in-game Save and cold restart |Profile, party, boxes, Bag/extensions, Pokédex, daycare, flags and Plus settings preserved |
| Existing training |2 existing active-course saves through ordinary Save and cold Continue |Jobs, daycare/party stats, wallet and valid journal CRCs preserved; cold SRAM identical |
| Consultant |2 Marts ×2 languages, south/east approaches, service, cancellation and normal exit |4 scenarios pass; native resource/event preservation verified |
| Wild caught icon |6 actual ordinary encounters after cold Continue from capture-derived raw saves | 5 uncaught show 0; caught Scyther shows 1; all 6 return to field |

All accepted final runtime traces pass the crash/liveness gate. The suite's 147
skips are historical/private-input cases and are not credited as executed
coverage. The expanded Guide installer also rejects modified native graphics
members 7/8/9/14 in both languages without writing an output.

The seven older-save cases comprise a save without Plus data in each language,
configured Plus and expanded-Bag saves in each language, and an advanced Italian
save. Original fixtures are unchanged. Two additional fresh-game save/cold
roundtrips use no old SRAM input. Two active-course cases use existing v5 saves,
one per language, with two playtime courses; these are not a universal migration
proof.

The trainer code/configuration, four hook sites, trainer/evolution/personal/item
archives and battle overlays 12/101 compare byte-for-byte with v5 in both languages.
Fresh native tests and the six wild encounters supplement that bridge. The prior
28 team constructions and detailed balance/AI scenarios remain prior evidence;
this UI follow-up does not claim new complete Gym or League battles.

## Footprint and optimization

Guide code is 5,978/8,192 bytes; state 224/240 bytes. Five bounded temporary icon draws
run during confirmation, with no retained icon allocation or idle-frame redraw.
The existing temporary font cache is released on exit. Its content is 113,518 bytes
EN  / 119,040 bytes IT, below 128 KiB. Shared icon tiles 390..421 use 1,024 bytes of existing
sub-screen character VRAM, below both native screen maps.

Plus keeps its original 3,776-byte compartment: 3,772 bytes used. Navigation uses 250
of a separately guarded 512-byte development reservation; context uses 352/384.
The temporary footer grows by 448 bytes while drawing and is then released.
Existing settings IDs and public addresses remain unchanged.

The consultant adds 88 bytes of native lookup code, 8 configuration bytes and a
6,760-byte texture with two orange palette edits. All 863 original texture members
and 901 native sprite records are unchanged. The append-only installer relocates
the 4,644,140-byte grown archive; the final cartridge grows 4,754,944 bytes over v5.
That is storage growth, not a new per-frame workload or permanent texture heap.
A broad ROM repack was not introduced for this UI change.

## Method and limits

The native layout/palette evidence and primary-source UI references are recorded
in the [contract](hgss-ui-contract.md). The earlier playtest records ISTQB test
methods, Redux comparisons and native AI references. This follow-up applies
boundary, ownership, state-transition, negative-input and deterministic-replay
checks to the changed surfaces, then exercises neighboring applications and
save persistence. Review findings are checked against actual ARM/native behavior.

Runtime uses the pinned melonDS interpreter/software renderer with copied raw
saves. Mart scenarios use debugger map setup followed by ordinary interaction;
Guide, Options, wild encounters, New Game and save/cold paths use ordinary input.
Active training uses the preserved RTC-capable interpreter frontend. No final
acceptance uses emulator savestates as a substitute for raw-save compatibility.

Very short two-emulator-frame cancellation pulses during the initial native
redraw were not sampled in four probes; those runs opened Guide normally and
are excluded from cancellation passes. Six-frame presses canceled before launch
in both languages. The passing ARM tests establish correct behavior once input
is sampled, not a guarantee for arbitrarily short button pulses. Native text
keeps layer priority: two existing English Options descender pixels lie above
the top frame row; all remaining visible border pixels match the native frame.

These finite checks do not certify an entire adventure, every team/status/RNG
combination, wireless/Pokéwalker, physical DS/mobile JIT, real multi-hour waits,
all RTC courses, or power interruption on hardware. See the previous report for
remaining balance coverage. This remains a private 1.3 DEV candidate; publication
is separate. ROMs, saves, graphics, raw traces and private evidence stay outside
Git.
