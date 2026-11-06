# Battle-copy and field-input maintenance

This dependency remains in the **1.3.1** build chain. Originally introduced in
1.2.4, it repairs two code paths without changing the save format. The base
builder first reconstructs the SHA-256-pinned 1.2.3 intermediate, applies this
stage and updates the title; later stages advance the final version. The
standalone installer accepts only official 1.2.3 EN/IT images. Use the
[current composition guide](../../sgp131/README.md) for a complete 1.3.1 build.

## Battle sprite copies

Native effects use stationary OAM copies of Pokémon. ANIM2 previously moved the
original while a copy existed because `moveActive`, `animActive` and species
entry did not cover every producer, explaining doubled silhouettes during
switches and Ball throws.

The wrapper intercepts allocation in common constructor `ov07_0221FB90`, returns
all ANIM2 slots to rest before copy data is read and counts live owners. The
task waits until the last owner is destroyed; two native destructors decrement
after `Heap_Free`. No task is added. The counter remains coherent with the
option OFF. Enabling during a copy clears residual native-bounce `yOffset` but
leaves native scale, pose and shadow alone. Cleanup uses existing `sgp_pulisci`
ownership rules; resumption restarts phase, envelope and B-pose wait.

Coverage includes single, collective, Ball and `SpriteToOAM` copies. It does
not establish that every reported double image during fainting, dialogue, Bag
use or escape has that same cause.

## Waterfall search during movement

`FieldInput_Process` searched for a Waterfall user every update: up to six
Pokémon, checking egg status and four moves each. Individual `GetMonData` calls
may decrypt/re-encrypt the record. Its sole consumer, `ov01_021F24F4`, uses the
result only while Surfing (state 2) south (direction 1). The wrapper skips the
search elsewhere and calls the original with unchanged arguments/result in
that case. Other field-move searches remain native; no Party cache is added.
This removes CPU work. It is not an FPS/input-latency measurement, and earlier
NPC-load improvements do not establish a fix for continuous city slowdown.

## Memory and application

| Owner | Address | Size |
| --- | --- | --- |
| Copy wrapper | `0x023DBC60` |144 code bytes +16-byte canary, existing ANIM2 tail |
| Copy counter | `0x023DBBC0` |4 formerly reserved ANIM2 state bytes |
| Waterfall wrapper | `0x023D8040` |24 code +24 padding +16 canary bytes, former 1.2.3 free reserve |

The ARM9 reserve does not grow. The bundle contains code compiled from these
sources. Six file regions change: title, two ARM9 regions and three compressed
overlays; decompressed changes are confined to five declared hooks. EN/IT
recompression preserves exact file sizes, FAT, header, unrelated assets/scripts.

From the root, using the project environment:

```sh
.venv/bin/python3 source/features/manutenzione/compila.py \
  --uscita source/sgp12/build/manutenzione
PYTHONPATH=source .venv/bin/python3 -m sgp12.manutenzione \
  --base /private/path/sgp-1.2.3-IT.nds --verifica
```

`--verifica` writes no ROM. For the isolated base stage, replace it with
`--uscita /private/path/sgp-maintenance-IT.nds`. The input is preserved. Existing
output, wrong preimage, inconsistent bundle or insufficient space is rejected.
Writing streams 1 MiB blocks and rereads the full output without intermediate
ROMs. Personal variants are rejected; do not bypass the hash guard.

## Historical checks and their limits

```sh
.venv/bin/python3 -m unittest discover -s source/features/manutenzione -p 'test_*.py'
.venv/bin/python3 -B source/features/manutenzione/verifica_totem.py
```

Wrapper tests run real ARM and ANIM2 blobs on synthetic Unicorn memory with
heap/renderer seams; no game, emulator or firmware runs. macOS sandbox failure
at `mem_map` requires a JIT-capable environment, not reinstallation. Installer
tests use tiny synthetic files. Historical results: 8 wrapper tests (including 20
state/direction combinations), 9 installer tests and 7 totem/flag tests passing;
`sgp12.test_lib` 42 run/31 private-input skips, map checks 3 run/8 external-fixture
skips. Skips remain uncovered. Preparing both real ROMs checked preimages,
space, recompression and independent readback at about 1.1 seconds/language and
97 MiB peakRSS; it measured neither gameplay performance nor screens.

### Vermilion totem investigation

The read-only verifier streams necessary members using the existing decoder
and local pinned pret checkout; it saves no assets and installs nothing.
Six scenarios per language cover A→battle with/without Soul Dew and accept/
decline; 12 per language cover two species branches and six battle outcomes.
Targets, objects, movement and messages are structurally valid, Latios/Latias
level 40 is valid, the script reaches `ReleaseAll/End`, and loss/draw use
`WhiteOut`. Six RAM-mutant tests detect changed jumps, objects, species, levels
and unlocks.

These bytecode/flow checks assume native waits complete. They neither execute
the battle engine nor reproduce the freeze. `LockAll` can wait on unfinished
movement, and the battle task waits for the battle application; the original
blocked execution state was not captured, so no pending wait was identified.

The historical investigation found inherited high flags `0x3FCA` and `0x3FAF`
outside `SaveVarsFlags`, targeting PalPad `+0xDD` bit 2 and `+0xD9` bit 7 in Classic 1.04
and Plus 1.1. Six real native `Save_VarsFlags_SetFlagInArray` calls under Unicorn
(three flags/language, including a valid control) confirmed the offsets and
normal return with `_021D4150=0`; high flags reached `GF_AssertFail`, which then
returned. This was not the user's freeze state or all execution conditions.
No flag remap belonged to this maintenance stage. The later
[event-state module](../event-flags/README.md) provides the current HF 02 solution;
its evidence and compatibility constraints are separate.

### 24 October 2026 user report

After an explicitly requested in-place Android ROM update preserving the
current save and personal ROM settings, the user reported catching Latios and
no longer observing slowdown. They clarified the former freeze occurred after
battle started. That candidate succeeded in the reported case; it did not
identify the earlier cause or verify every animation-overlap scenario.

A subsequent roughly 30-second SurfaceFlinger sample had 16.763 ms median,
16.767 ms 95 th percentile and no interval above 25 ms. These are Android surface
presentation intervals, not DS logic FPS or input latency. The in-game location
was not recorded, so this is no controlled city/baseline comparison. An initial
log capture ended before gameplay; the app buffer and a new bounded capture
were collected during the sample. Neither reproduced the old freeze. Logs and
receipts remain private; no emulator/APK was installed for this check.

The later [1.3.1 validation](../../docs/ui-1.3.1-validation.md) retains newer
candidate identities. The historic Latios freeze is not established as fixed
by these observations or by the distinct battle type-loop repair.

## Reference sources

Pinned `pret/pokeheartgold` revision
`0985e8718df4f25e64d6507d89c0c97c0d288981`: `asm/overlay_07.s` (copy lifecycle),
`src/pokepic.c`, `src/field/field_control.c`, `asm/overlay_01_021F1AFC.s`
(Waterfall producer/consumer), and `src/script_pokemon_util.c`.

[2025 Goldenrod/Vermilion reports](https://www.reddit.com/r/PokemonHGSS/comments/1k79vaq)
describe slowdown in the original, but do not identify a shared cause. The
[author's FPS-unlock tool](https://github.com/ITotalJustice/pokemon-gen4-fps-unlocker)
is a separate speed-altering modification and is not included here.
