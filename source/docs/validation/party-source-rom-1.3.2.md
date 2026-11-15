# Battle Party: source, installed bytes and native getters

The 1.3.2 r4 EN and IT images contain the Battle Party helper built from
[`squadra_cache.c`](../../features/squadra-lotta/sorgenti/squadra_cache.c).
A targeted rebuild reproduced its 200 code bytes and four public entry points.
The installed code, without replacement by a test blob, matched the native ARM
getters for all 468 admitted move records and the tested PP-Up values.
This is attribution and bounded equivalence evidence. It introduces no game
change, save format, performance repair or new release.

## Inputs and provenance

Supply your own exact image from the [r4 game contract](../../distribution/game-1.3.2-r4.json).
Its complete SHA-256 and size are mandatory; a filename or version label is
insufficient. Reconstruct it through the [composition guide](../../sgp131/README.md)
and [localization guide](../localization.md) using your own compatible inputs.
ROM images, patches, extracted data, saves and raw traces stay private.

| Image | Bytes | SHA-256 |
| --- | ---: | --- |
| r4 EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| r4 IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

The incremental comparison also authenticated retail and inherited 1.1 inputs
against the existing [base contract](../../sgp12/base11.json). EN retail and
both normalized 1.1 bases have the same 692-byte Party constructor at
`0x0221D184`, hash
`14f4c62e41f25d356782c0610187d1a65e69b93543fc1009a96cfa3daf78a1bd`.
Between each base and r4, exactly 20 bytes change in that constructor, confined
to its five BL instructions. The helper allocation is absent from the inherited
base's loaded sections. This distinguishes the Plus addition from native code.
Retail IT has a different core and overlay load address; the US addresses must
not be assigned to its functions without a separate attribution.

The [installer](../../sgp12/blocchi/squadra_lotta.py) checks native anchors,
blank reserve, branch preimages, source fingerprints and ownership. The
[`sgp12` composer](../../sgp12/costruisci.py) installs `squadra_lotta` after
`borsa_lotta` and before expanded Bag capacity. It is inherited through the
exact V4 input into the later composer; the r4 stage does not recompile it.
The final-image check below verifies that later composition preserved it.
It does not rerun or certify the entire historical build.

## Source, compilation and placement

The [compiler recipe](../../features/squadra-lotta/tools/compila.py) invokes
Clang for ARM946E-S Thumb with `--target=armv5te-none-eabi`, `-mthumb`, `-Oz`,
freestanding/no-builtin/no-stack-protector/no-unwind/no-jump-tables flags and
warnings as errors. The exact list is in its emitted `manifesto.json`.
There is no general linker: [`load_text`](../../features/anim/tools/carica_text.py)
loads ELF32 ARM `.text`, rejects external symbols and other allocated content,
and resolves only internal `R_ARM_THM_CALL` relocations. Literal pools remain
inside `.text`; symbol addresses retain the Thumb bit.

| Entry | Thumb symbol | Role |
| --- | --- | --- |
| `sgp_squadra_attr_cache` | `0x023DBE01` | Four admitted attributes, otherwise native fallback |
| `sgp_squadra_pp_cache` | `0x023DBE7D` | Max PP with three-PP-Up clamp and u8 result |
| `sgp_squadra_attr_hook` | `0x023DBEB5` | Read caller's app pointer from stack |
| `sgp_squadra_pp_hook` | `0x023DBEBF` | Same ABI for PP |

Code SHA-256:
`a9b56d5ea7fe8df1c9a91b4305b04512d329ac7f7ad51cc74cf24bff399912be`.
The 256-byte owner contains 200 code bytes, 40 zero bytes and a fixed 16-byte
canary; whole-owner hash:
`aa429ac30a0d519d1ca9aa060c63914834aaa752539ec0dae7be346fb3b76b40`.
There is no new heap allocation, mutable cache, save field or persistent pointer.

The historical manifest records Apple clang `2100.3.34.2`. The 11 November
rebuild used Apple clang `2100.4.1.1`, executable SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
It produced identical `.text` and public symbols. This is an observed exact
reconstruction with the current compiler, not authentication of the original
historical compiler executable. The manifest's compiler string consequently
differs. Preserve both identities rather than replacing the shipped manifest.

Current source hashes matched the bundle's origin receipt. That receipt names
C and `compila.py` only; it does not authenticate the transitive ELF loader or
compiler. Record those separately when repeating the rebuild. At this check,
C SHA-256 was `dc0abee488222a1f8119bf02a5c2cc19726f3746e6ef6a2ec5c834132a43a755`,
recipe `485487ad9b227d342eacc74df4e0560cf93b57e1396ce46d17cd138c58b3763a`,
and ELF loader `fff73b384cacedae6525b72a46665a05f3c9710a4ff789fd296568e82e2ce1a8`.

### Physical and logical coordinates

The final-image tool reports exact physical FAT/table/member coordinates for
each language. The following logical coordinates agree in r4 EN/IT:

| Component | Mapping |
| --- | --- |
| ARM9 owner | RAM `[0x023DBE00,0x023DBF00)`; initialized autoload section beginning `0x023C8000`, size `0x18000` |
| Owner physical bytes, EN | ROM `0x12B6C0`, length 256; not an offset relative to the ARM9 header |
| ARM9 module parameters | Offset `0xBA0` within ARM9; raw layout is cross-checked against ndspy sections |
| Overlay 8 | RAM `0x0221BE20`, decoded length 41248; FAT file 8, backward-LZ compressed |
| Overlay 12 | RAM `0x022378C0`, decoded length 226176; FAT file 12, backward-LZ compressed |
| Loader | `ov12:0x02248692` BL to `0x02073300`; literal at `0x022486A8` equals `0x3DE` |
| Move archive | NitroFS `a/0/1/1`, file 140; 471 physical contiguous records, 16 bytes each |
| Loaded table | First 468 records, 7488 bytes, stored inline at `BattleContext + 0x3DE` |

Compression prevents a simple physical-byte offset for an instruction inside
an overlay. Use its FAT extent, compressed length, decoded image hash and
RAM-relative offset together. For EN, overlay 8 is stored at ROM
`0x1C3800..0x1CAAA8`; the five RAM sites below are offsets
`0x15BE/0x15C8/0x15D2/0x15DC/0x15E6` in its decoded image.
The final tool emits equivalent physical coordinates for IT rather than
assuming EN filesystem positions apply there.

## Caller, ABI, state and resources

The native Party task sets up the menu and calls `ov08_0221D184`. That
constructor preserves the original app pointer in `[sp]`, scans occupied party
members and skips empty move slots. The relevant entry frame is 40 bytes
(including the register push), preserving 8-byte alignment. Its five BLs are:

| Site | Native target | Installed target, without Thumb bit | Input |
| --- | --- | --- | --- |
| `0x0221D3DE` | `0x0207332C` | `0x023DBEBE` | move, PP-Ups |
| `0x0221D3E8` | `0x02073314` | `0x023DBEB4` | move, attr 3/type |
| `0x0221D3F2` | `0x02073314` | `0x023DBEB4` | move, attr 1/category |
| `0x0221D3FC` | `0x02073314` | `0x023DBEB4` | move, attr 4/accuracy |
| `0x0221D406` | `0x02073314` | `0x023DBEB4` | move, attr 2/power |

Each shim pushes `{r3,lr}` (8 bytes), takes app from its new `[sp,#8]`,
passes it as `r2`, and restores `r3` and the native return path. The helper
borrows `app → args → [args+8] BattleSystem → [bs+0x30] BattleContext`.
It admits load status 1 or 2, guard `0x5A`, nonzero animations option at
`0x023D8716`, move IDs 0–467 and nonnull pointers. Attribute IDs 1–4 read
record bytes 2–5. All other conditions call the native getter. Max PP reads
byte 6, clamps PP-Ups to 3 and returns an 8-bit value.

`BattleContext_New` loads the inline table before Party is constructed;
`BattleContext_Delete` frees the containing context at battle teardown.
The helper retains no pointer across calls and has no callback of its own.
The native menu owns its app/context and graphics; it borrows the battle
system while its task runs. A nonnull chain alone does not prove lifetime.
The isolated tests construct that chain; they do not establish every
asynchronous menu/teardown interleaving, Safari, doubles or hardware behavior.

The pinned HGSS sources explain these native roles; they are reference source,
not a claim that the original commercial object was rebuilt here. Compare
`src/move.c`, `src/battle/battle_controller_player.c` and
`asm/overlay_08.s` at pret revision `0985e8718df4f25e64d6507d89c0c97c0d288981`.
The more recent source-only reference at `cb614ad23449d5852b40321dc409c4143872b35c`
also names `BattlePartyMenu` and its task lifecycle.

## Repeat the checks

Use an isolated Python environment with [project dependencies](../../requirements.txt),
including ndspy, Capstone and Unicorn, and an ARM-capable Clang. The measured
host used Python 3.14.7, ndspy 4.2.0, Capstone 5.0.9 and Unicorn 2.1.4.
Unicorn needs executable JIT memory. A different compiler may not reproduce
the binary; a mismatch remains a mismatch, not permission to refresh goldens.
Run from the repository root with the environment activated:

```sh
# Use a private, initially empty directory; do not replace the shipped bundle.
export SGP_ATTR_OUT=/path/to/private/party-check
mkdir -m 700 "$SGP_ATTR_OUT"
python3 source/features/squadra-lotta/tools/compila.py \
  --uscita "$SGP_ATTR_OUT/rebuilt"
python3 source/features/squadra-lotta/tools/attribuisci.py \
  --rom "$ROM_EN" --language EN --build "$SGP_ATTR_OUT/rebuilt" \
  --json "$SGP_ATTR_OUT/en.json"
python3 source/features/squadra-lotta/tools/attribuisci.py \
  --rom "$ROM_IT" --language IT --json "$SGP_ATTR_OUT/it.json"
python3 -m unittest discover -s source/features/squadra-lotta/test -p test_build.py -v
python3 -m unittest discover -s source/features/squadra-lotta/test -p test_blob.py -v
SGP_ROM_SQUADRA_DOPO="$ROM_EN" python3 -m unittest discover \
  -s source/features/squadra-lotta/test -p test_native_data.py -v
SGP_ROM_SQUADRA_DOPO="$ROM_IT" python3 -m unittest discover \
  -s source/features/squadra-lotta/test -p test_native_data.py -v
```

All commands must exit 0, without a skipped ROM-dependent comparison. The
readback checks final identity, complete owner, Thumb branch targets, raw
header/FAT mapping, both overlay decoders, loader offset and contiguous move
data. It emits hashes and coordinates, not extracted game bytes or input paths.
It also rejects source drift. The older `tools/rileggi.py` remains the separate
pre/post installer oracle, including whole-image confinement; using it directly
on a final r4 versus 1.1 pair would include many unrelated composition stages.

The native comparison executes installed code and native division, intercepting
only `LoadMoveEntry` transport to copy the actual private NARC member into its
native stack buffer. Tests check 468 × (four attributes + six PP-Up inputs:
0, 1, 2, 3, 4, 255) = 4680 comparisons per language, the five actual BLs,
return PC, Thumb state, SP, preserved r4–r11, shim r3, and guest writes confined
to the isolated stack. Null gates/pointers and out-of-cache but valid archive
records exercise real native fallback.

## Counterexamples and scope

The contiguous loader view must equal the per-member view. An aligned gap can
preserve every individual member while invalidating `LoadMoveTbl`; the raw
BTAF/GMIF walk rejects that case. EN/IT have identical current move archives;
record 261's accuracy is 85 in both views, reflecting the later
[`modern_moves` stage](../../sgp131/modern_moves.py).

The old equivalence test overwrote the installed helper with the shipped blob.
A private ROM clone with literal `0x3DE → 0x3E0` consequently passed that test.
The updated test first checks the installed block and leaves it in place; the
same clone is rejected. A separate isolated guest mutation demonstrates a
native/cache value difference with `0x3E0`. The original ROM stays unchanged.
Synthetic negatives also reject code, padding, canary, branch and record-layout
corruption. These are improvements to the verification tool, not a game fix.

Independent review confirmed installed addresses, ABI, loader, native
equivalence and counterexamples. The exact-rebuild receipt additionally records
the compiler executable, ELF hash, source hashes and flags. Historical opening
times in the owner README retain their historical scope and are not retested
or transferred to r4 as a speedup claim.

## Observed execution in the normal EN route

A new register-only `work on party` profile in the existing
[host runtime](../../runtime/README.md) resolved a question the old records
could not answer: whether the normal Party scan actually took these cache
branches. Old PC2/G06 records showed the menu and other components; they did
not record the Party helper sites. Their absence was not evidence of inactivity.

The exact E8 observer executable had SHA-256
`a3f7385510eec9f66f669a63743e99d5097f4f9aa044c9b61b6cd6d1d8e17381`,
core `906e9ebb27da8c6a715cd7abab4abfe8a8d29427`, interpreter/software renderer.
No core-hook change was needed beyond the already guarded Work/model variant.
The new layout records only eight pinned entry sites, r0–r7, SP/LR, CPSR,
parent/order and return values. It reads no guest memory or clock. A normal
cold boot and player-input route on a protected populated save copy reached
battle, two Bag openings, Party and return. Animations was already enabled;
no setting byte, game RAM or savestate was injected.

| Observation, exact EN r4 | Result |
| --- | --- |
| Complete constructor spans | 1, frames 7913–7919 |
| PP shim / four attribute shims | 20 / 80; each of five caller LRs observed 20 times |
| Cache-record returns | 100 nonnull pointers, each `ctx + 0x3DE + 16 × move` |
| Returned cache values | All 100 match the physical ROM move records |
| Native fallbacks inside this constructor | 0 |
| Native getter spans outside the constructor | 36, retained separately |
| Complete trace | 337 events, no open span or exhausted counter |
| Cross-build OFF and E8 OFF/ON neutrality | 8478 guest-frame rows, 2466 image samples, 10 RGB checkpoints, 11 full-RAM checkpoints and SRAM agree |

The active Party checkpoint independently confirms the app/args/battle-system/
context chain and all 7488 resident table bytes. Return values and record
pointers are captured at execution; the RAM comparison is one later endpoint,
not a memory sample at every instruction. The new observer captures r4–r7 at
entry, not r4–r11 at return: preserved-register ABI is the separate Unicorn
proof. Frame spans and dispatch counts are not CPU busy time, opening latency,
a performance comparison or a physical-device measurement. This runtime
observation covers EN and the exercised route; IT has exact-byte and isolated
native equivalence evidence, not an implied second runtime capture.

The [execution verifier](../../features/squadra-lotta/tools/rileggi_esecuzione.py)
checks complete System/Thumb spans, chronology, parents, five caller LRs,
constructor/shim/C stack frames, app transfer, each record pointer and value.
It requires a complete cache-hit scan, reports native events outside it, and
rejects eight raw-record counterexamples (pointer, LR, app, value, completion,
stack, parent and chronology). A synthetic test exercises the same rules.
The raw trace hash was
`68d109588d799b4f64d33c503632ee788b73115e8636084c210fbf589ab8d73f`.
Neither that hash nor a parser success attests the trace producer by itself.

### Reproduce an execution witness with your own save

Build the [runtime](../../runtime/README.md) from its pinned core using
`patch_core.py --work-observer --model-budget` and CMake
`-DHG_WORK_OBSERVER=ON -DHG_MODEL_BUDGET=ON`. Record executable/source/tool hashes
and settings. Use a verified private save copy with an ordinary party and valid
moves; preserve the original. Reach the normal battle command screen through
player inputs. This input fragment assumes that screen and the normal layout:

```text
sample on 0 16 256 128
work on party
touch 217 165 16
run 420
capture party.ppm
dump party-ram.bin
work off
sample off
```

`dump` here is a read-only private memory checkpoint, not a game modification.
Use the runtime's `--interactive` command input or append this fragment to your
own ordinary-input script. Store outputs in its fresh private `--out` directory.
Repeat the same route from a cold boot with the observer OFF. Compare complete
frame and sample rows excluding only their named host-timer columns, RGB
captures, full RAM and exported SRAM; a failed or incomplete comparison does
not qualify the trace. Do not load a savestate or compare end-frame PCs as if
they were function visits. Different saves may produce different move counts,
frames and context addresses; those counts are not universal success criteria.

After producer identity and neutrality are established:

```sh
python3 source/features/squadra-lotta/tools/rileggi_esecuzione.py \
  --rom "$ROM_EN" --language EN \
  --events "$TRACE_OUT/work-events.csv" --ram "$TRACE_OUT/party-ram.bin" \
  --json "$TRACE_OUT/party-attribution.json"
```

Raw inputs also accept lossless `.gz`. The JSON contains hashes, counts and
addresses, never ROM/save contents or personal paths. The verifier specifically
requires admitted cache hits; OFF/default fallback scenarios need their own
contract and must not be called a failed game merely because this narrower
cache-hit witness is absent.

## Result and remaining work

Documented provenance connects the project C, ELF loading recipe, installer and
inheritance chain. Exact reconstruction and readback cover the full 256-byte
owner and five branches in EN/IT. Isolated semantic/ABI checks cover the stated
move/PP and fallback domains. Normal EN execution additionally observes the
five callers, cache activation, returned values and the checkpoint table.

The original native object toolchain was not reconstructed. Original compiler
identity, all menu/teardown interleavings, natural IT activation, multiplayer,
hardware timing and universal save compatibility remain outside this case.
No save format changed and no new save acceptance is inferred. The old test's
payload replacement was corrected; no game optimization was proposed without
a measured cost. Future attribution can reuse final-image identity/mapping,
physical-table checks, installed-code execution and the existing Work collector.

The [native getter follow-up](native-move-callers-1.3.2.md) attributes the 36
external native spans using this same observation, without another game run.
