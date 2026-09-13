**Sacred Gold Plus Community 1: bounded runtime validation**

This kit contains the headless melonDS harness, observation hooks, input scripts and a sanitized account of the recorded tests. It contains no ROM, proprietary BIOS, save data, savestate, RAM dump, game screenshot or retail resource catalog. The synthetic player `TEST` save and the prepared Pokédex UI save used in the tests are not redistributed. Their hashes identify the original test inputs; reproducing the exact saved-file hashes requires those exact inputs.

`runtime-results.json` records the earlier game tests. `build-validation.json` records a separate clean build and synthetic instruction probe of this public kit, performed without opening a commercial ROM, save or state. The public input scripts preserve the tested guest input timelines after removing diagnostic exports and a discarded replay; they were checked statically against the private originals, not rerun as an additional game test.

**Source and build**

The required core is official [melonDS commit 906e9ebb27da8c6a715cd7abab4abfe8a8d29427](https://github.com/melonDS-emu/melonDS/tree/906e9ebb27da8c6a715cd7abab4abfe8a8d29427). Use a separate checkout: the patch adds observations to `src/ARM.cpp` and `src/NDS.cpp`. It neither patches ROM instructions nor changes guest registers, memory or cycle accounting. `patch_core.py` checks this exact commit and is idempotent on the instrumented checkout. `melonds-observation-hooks.patch` is the corresponding reviewable diff.

Requirements: Git, Python 3.9 or newer, CMake, Ninja and a C++17 compiler. The platform glue uses POSIX file and dynamic-library APIs. The build was verified on macOS ARM64 with AppleClang 21; Linux was not exercised and Windows platform glue is not implemented. No Qt, SDL or proprietary BIOS is required. The core's vendored dependencies are built from its checkout.

Run these commands from this kit directory. They place all generated files in `work/`; choose an empty output directory when rerunning.

```sh
git clone https://github.com/melonDS-emu/melonDS.git work/melonDS
git -C work/melonDS checkout --detach 906e9ebb27da8c6a715cd7abab4abfe8a8d29427
python3 patch_core.py --source work/melonDS
cmake -S . -B work/build -G Ninja \
  -DMELONDS_SOURCE="$PWD/work/melonDS" \
  -DHG_BUILD_WAIT_LOOP_TEST=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build work/build --target hg_runtime --parallel 8
```

`MELONDS_SOURCE` accepts any separate pinned checkout; there is no personal path in the sources. Set `CMAKE_MAKE_PROGRAM` if Ninja is outside `PATH`. The configuration forces the ARM interpreter, software renderer and no Qt/SDL, OpenGL renderer, GDB stub, JIT or release LTO.

The optional `hg_wait_loop_test` target depends on `../scripts/wait_loop_test.cpp`, distributed by the surrounding project rather than this folder. Its SHA-256 is `9305388c1590c42f08f178692b3b047e4a62596e3143c8749a70d6922d64fe99`. The target defaults to enabled, so standalone builds explicitly disable it above. To include it when the companion source is available:

```sh
cmake -S . -B work/build -G Ninja \
  -DMELONDS_SOURCE="$PWD/work/melonDS" \
  -DHG_BUILD_WAIT_LOOP_TEST=ON \
  -DHG_WAIT_LOOP_TEST_SOURCE="$PWD/../scripts/wait_loop_test.cpp" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build work/build --target hg_wait_loop_test --parallel 8
```

The compiled `hg_runtime` with no arguments reports usage and exits 1; `hg_wait_loop_test` reports usage and exits 2. A ROM-free instruction probe can be reproduced as follows. These temporary buffers consist only of zeros and two ordinary ARM instruction words; they are not ROM files.

```sh
python3 - <<'PYPROBE'
from pathlib import Path
import json, struct, subprocess
root = Path('work/build')
for label, word, expected in [('branch', 0x1AFFFFFC, 0),
                              ('endian-error', 0x0000A0E1, 1)]:
    data = bytearray(0xDE174)
    for offset in (0xD3FA8, 0xDE16C):
        struct.pack_into('<I', data, offset, word)
    fixture = root / ('synthetic-' + label + '.bin')
    fixture.write_bytes(data)
    result = subprocess.run([str(root / 'hg_wait_loop_test'), str(fixture)],
                            text=True, capture_output=True)
    assert result.returncode == expected, result.stderr
    entries = json.loads(result.stdout[result.stdout.index('[\n'):])
    assert len(entries) == 4
    assert all(x['status'] == ('PASS' if expected == 0 else 'FAIL')
               for x in entries)
    print(label, 'expected exit', expected, entries)
PYPROBE
```

The restored conditional branches preserve R10 and choose the expected next PC for idle and busy flags at both sites: four passes. The endian-error instruction produces four expected failures. This probe executes individual instructions through melonDS's actual interpreter table; it does not simulate the complete DMA or SPI transaction.

**Replaying the bounded UI paths with local inputs**

Supply your own ROM and disposable test save. The primary save script assumes a `TEST` save at New Bark Town, outside the starting house, with zero badges and the early-game menu layout. A different save or ROM can require different coordinates and waits. The recorded initial save is 524,288 bytes with SHA-256 `80f555b057cd2c339d5f6b515d8f4c80c263718791c058985e0ebf6ef09cfc40`.

Set `ROM`, `TEST_SAVE`, `DEX_TEST_SAVE` and `OUT_ROOT` to your local inputs/output area. Keep outputs separate from the input saves; the harness never searches for or automatically overwrites an adjacent save. From the kit directory:

```sh
work/build/hg_runtime --rom "$ROM" --out "$OUT_ROOT/save" \
  --sram "$TEST_SAVE" --trace-pc --script inputs/boot-save.script
work/build/hg_runtime --rom "$ROM" --out "$OUT_ROOT/reload" \
  --sram "$OUT_ROOT/save/after-save.sav" --trace-pc \
  --script inputs/cold-reload.script
cmp "$OUT_ROOT/save/after-save.sav" "$OUT_ROOT/reload/reloaded.sav"
```

Each invocation starts a new emulator process. Neither command loads a savestate. The first script reaches Continue, enters town, opens SAVE, accepts both save confirmations and exports cartridge SRAM. The second cold-boots the same ROM from that exported save, reaches Continue and town, and exports SRAM again. Inspect the generated captures as well as `cmp`; a script completing alone does not prove that the intended UI action occurred. `sram` exports current save bytes and does not itself trigger the game's SAVE operation.

| Input script | Required starting condition | Guest frames |
| --- | --- | ---: |
| `boot-smoke.script` | Fresh direct boot, any locally supplied supported ROM | 600 |
| `boot-save.script` | Fresh direct boot with the original town TEST save | 5,878 |
| `cold-reload.script` | Fresh direct boot with the newly exported same-ROM save | 3,246 |
| `newgame-keyboard.script` | Italian variant, no SRAM, initial `--frames 600` | 9,478 including initial 600 |
| `pokedex-cold-ui.script` | Fresh direct boot with prepared Pokédex UI save | 5,088 |

For the keyboard and Pokédex paths:

```sh
work/build/hg_runtime --rom "$ROM" --out "$OUT_ROOT/keyboard" \
  --frames 600 --script inputs/newgame-keyboard.script
work/build/hg_runtime --rom "$ROM" --out "$OUT_ROOT/pokedex" \
  --sram "$DEX_TEST_SAVE" --script inputs/pokedex-cold-ui.script
```

The naming script reaches the keyboard, removes a pre-existing `A` with B, and enters `ÀÉÈÌÒÙ` then `àéèìòù` using the six keys at x=34,50,66,82,98,114 and y=156. Each touch has a three-frame hold and a 30-frame pause. CANC removes the final uppercase Ù; FINE opens a yes/no name confirmation containing the lowercase sequence. Both Italian camera variants were checked, including the encoded input-buffer glyphs. The original diagnostic script saved and restored its own boot-600 state around a discarded 60-frame replay. The public script removes that replay and contains no state load; its diagnostic frame count is 60 lower while the subsequent guest inputs are equivalent.

The Pokédex fixture, SHA-256 `951a3478d49eac28c81a9afb311cad4a3287daa58553efb4c9d4e2d2e1e993c1`, was prepared on the EN Plus variant from the synthetic town TEST save. Five RAM bytes enabled the menu/Dex and marked Bulbasaur seen, caught and known in English, using the identified SaveData/VarsFlags/Pokédex structures. The National Dex flag was already enabled. After refreshing the menu, the game performed its actual SAVE operation. No ROM byte or party Pokémon was changed. This fixture and its preparation writes are not distributed with the safe input scripts.

EN Plus exercised the Dex while preparing that fixture using its own-ROM town state. EN Classic and both Italian variants then cold-booted solely from the saved fixture, with no RAM writes or state loads. The script opens the species page, moves both height cursors and both weight cursors, checks the summary, runs a restrictive search with zero results, resets it and obtains the one Bulbasaur result.

**Recorded final results**

These are the final builds covered by `runtime-results.json`. Earlier rejected Italian builds have different hashes and are retained as failures in that report.

| ROM basename | Bytes | SHA-256 |
| --- | ---: | --- |
| Sacred Gold Plus 1.03 Community 1 EN | 127038608 | `3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248` |
| Sacred Gold Plus 1.03 Community 1 EN - Classic Camera | 127038608 | `ef0e61bbcad07d732054a19a0b4ee64563bb2d7503ee9fd62348643fcb630760` |
| Sacred Gold Plus 1.03 Community 1 IT | 131840584 | `217daa45f4945abd3feda6f583f5163db029d1aa361c33c18f12b32ad4eca4a4` |
| Sacred Gold Plus 1.03 Community 1 IT - Classic Camera | 131840584 | `9dd0c98eb96b91037592bc30574210b191e9f2c2fca45f466733eeb5b9a12d0a` |

All four builds cold-booted from the original TEST SRAM, reached Continue and New Bark Town/Borgo Foglianova, completed both SAVE confirmations and cold-reloaded their newly saved SRAM. Each save changed 130,724 bytes; the save counter advanced 1 → 2 and remained 2 after cold reload. Continue advanced from TEST 0:01 to 0:02, with zero badges. Save and reload exports were byte-identical for each variant. Both English variants produced `6b7995dbb1edb083ee395334da18d4a359ba2c0c782f5d376859a287b0a94ca6`; both Italian variants produced `26dde6629c50fa8797e86811e8773d870e9d298a769ebce8fa3a9e5e99938c5f`.

The saved text was “TEST saved the game.” in English and “TEST ha salvato il gioco.” in Italian. A separate same-ROM town-state replay captured the complete Italian message later in its text animation and exported SRAM identical to the primary save. The primary save/reload tests themselves used no state load. The public save script adds a capture at that later point by splitting an existing 300-frame wait into 100+200; its total guest-frame count is unchanged.

At runtime, both wait sites `0x020D3FA8` and `0x020DE16C` contained `0x1AFFFFFC`. The language byte at `0x020F5670` was 2 in all four builds: the Italian variants localize resources while retaining this runtime identity. The English cheat identity is `IPKE F38C0335`; Italian is `IPKE D0186E6D`. All four files fit within 128 MiB with NDS capacity byte 10.

All four tested Dex UI paths passed. English Bulbasaur displayed 2 ft 4 in / 15.2 lbs, and Italian displayed 0,7 m / 6,9 kg. Search filters retain imperial units: the dragged height range was 2 ft 7 in to 13 ft 9 in; weight was 15.4 to 286.6 lbs (localized commas in Italian text windows). The height markers displayed feet/inches symbols, summary values matched the sliders, and searches returned the expected zero/one results. This verifies the restored UI asset path without claiming metric search filters.

**Observations and limitations**

The CLI supports scripted or `--interactive` stdin commands. `run` advances guest frames; `tap` presses/releases keys; `touch` uses bottom-screen coordinates; `release` ends a held touch. `--trace-pc` or `tracepc on` enables actual interpreter visit counters. The supplied scripts contain only key/touch inputs, bounded waits, reads, status and local capture/SRAM exports. They contain no ROM/RAM writes, cheats, freezes, dump commands or savestate loads. The source retains its original debugger commands for separately controlled investigations; loading a state from another ROM can restore old code and invalidate comparisons.

Each run writes local `frames.csv`, `commands.log`, `session.txt` and PPM captures. `session.txt` records the caller's ROM path at runtime, and captures/save files contain game data: those generated artifacts are not part of this public kit. Export commands are confined to `--out`. Choose a fresh output directory because existing files with the same names are overwritten. No background save callback writes an input file; export is explicit.

CSV `arm9_pc`/`arm7_pc` are end-of-frame samples, not visit counts. The two instruction counters observe visits, condition execution and R10 changes; `main_loop_jumps` counts branch targets at `0x02000DAC`. The IPKE guest counters at `0x021D1138` and `0x021D113C` can reset and are not universal monotonic frame numbers. Polygon/vertex values are instantaneous core fields sampled after `RunFrame`, so buffer swaps can affect them. Harness counters accumulate across state restores. Printed host throughput is not a device FPS measurement.

The test configuration uses the interpreter, software renderer, FreeBIOS, generated firmware and fixed initial RTC 2026-09-05 12:00:00. Audio is drained but not played; offline networking, peripherals and unused platform callbacks are inert. These tests cover the recorded boot, naming, SAVE/reload and Dex UI paths only. They do not establish full-game compatibility, party/battle behavior, foreign-language Dex cycling, fairy-type entries, multiplayer, audio output, JIT correctness, third-party Android builds or handheld performance.

`source-provenance.json` identifies unchanged runtime sources and the small path/build-configuration adjustments. `SHA256SUMS` covers the distributed files. Source in this kit is provided under GPL-3.0-or-later; the included `LICENSE` contains GPL version 3. melonDS retains its upstream licensing and notices.

**Follow-up on 6 September 2026**

`inputs/town-house-roundtrip.script` adds a bounded, cold-boot walking test using the same initial New Bark TEST save. It enters the starting house and returns outside in 3,774 guest frames, with captures at 3,510 and 3,774. It was run through the existing interpreter/software harness on US retail, exact Plus 1.03 and all four Community variants. Both screens were reviewed in every run. It exports SRAM but does not trigger a new game SAVE; it contains no RAM writes, cheat or savestate load. These are transition checks, not battle, campaign, GUI, performance or Android tests. The storage limitation discovered during this follow-up is recorded separately. The historical runtime/build JSON reports above remain unchanged.
