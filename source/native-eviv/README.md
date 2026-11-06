# Native Summary EV/IV reader

This reader is retained by the **1.3.1** build chain. On the Summary Stats page,
L shows EVs, R shows IVs, and SELECT restores ordinary stats. It requires no
cheat or new save fields. Changing page/Pokémon restores a coherent title and
values. The shared Summary/New Game presentation is documented in
[the native Guide module](../native-guide/README-combined.md).

## Implementation and boundaries

The guarded standalone builder accepts only four pinned Community 1 hashes,
checks two ARM9 prologues, autoload sections and ITCM arena constant, and emits
the r5 **592-byte Thumb payload** in a **608-byte** reserve. It raises ITCM's
lower arena limit while preserving DTCM, BSS and stack; the explicit ceiling is
`0x01FFA000`. ARM9 stays in its original compressed slot. ARM7, overlays and
unselected files remain intact. Only message bank 302 changes, with title 109
and two added strings.

The secure-area CRC is updated relative to its original value, preserving the
encrypted `0x800`-byte prefix. A synthetic independent-prefix test checks the
XOR property. No proprietary encryption implementation, keys or BIOS are
included; direct boot is not a complete hardware-boot test.

ABI references are [pret/pokeheartgold](https://github.com/pret/pokeheartgold/tree/0985e8718df4f25e64d6507d89c0c97c0d288981)
and [hg-engine](https://github.com/BluRosie/hg-engine/tree/1febb90b856745f8648c8a4fa059e7499a3cca3f).
Their authors receive credit for decompilation, symbols and research. Some
hg-engine helper comments retain Platinum addresses; the implementation checks
HG `rom.ld`, assembly and actual preimages rather than trusting those comments.
This is project-authored code using those interfaces, without incorporating the
whole engine or external assets. It is GPL-3.0-or-later under the
[project license](../../LICENSE); reference works retain their authors' rights.

## Historical validation and profiling

The 7 September 2026 EN/IT Plus pilot tested values, button/touch navigation, held
keys, exit/re-entry, native SAVE and cold boot. The original fixture was one TEST
starter with distinct EVs, not every Pokémon/save. Expanded r5 checks used one
and three slots, two distinct Chikorita, a synthetic egg and nonfull HP. All 708
three-party bytes remained identical through SAVE/cold boot. Clipped EV/IV titles
were shortened and reviewed in both languages; a native-redraw hook also restores
the title after button/touch page changes.

R4 redrew the whole Stats page on SELECT, including ability/descriptions. R5
restores only the six values and title with native data/formatting:

| EN Plus path | r4 | r5 |
| --- | ---: | ---: |
| SELECT, mean ARM9 cycles over 8 presses |1295291.75|286318.375|
| Observed alloc/free per SELECT |45/45|25/25|
| No-new-key cycles per call |270|269|

SELECT costs fell 77.9% in that measured path, with unchanged numeric/title
regions. Native control without the pilot costs 224 idle cycles, so r5 adds 45.
EV/IV samples cost about 237000/273000 cycles per press. Counts include callees
and possible IRQ time, but exclude later scheduled VRAM transfer. These are
not FPS, GUI timing or Android measurements.

The EN/IT Box case passed EV/IV, restore, exit, SAVE and cold boot with Party/Box
data unchanged. `run_box_probe.py` uses a normally deposited fixture SHA-256
`5208191f489232908c41d160c0782d945bbf0084897c0465d809b9a41d7527d7`.
An initial script omitted closing a PC menu and did not reach SAVE; it was
retained, corrected and rerun. The synthetic egg cases are not egg acquisition,
trade or hatch coverage. Classic native variants, other species/forms/languages,
interactions and hardware were not covered by this campaign. Historical results
retain their original identities; see [current 1.3.1 validation](../docs/ui-1.3.1-validation.md).

## Reproduce

Use a fresh private directory outside Git/synchronization. Generated ROMs,
captures, dumps and saves remain local. Install `source/requirements.txt` into
the project environment and provide an ARM-capable Clang plus the pinned pret
charmap. The builder installs no dependencies. The historical environment used
Python 3.9.6 and ndspy 4.2.0 with Pillow/capstone; system Python without those
packages fails imports rather than exercising the suites.

```sh
.venv/bin/python3 -m unittest discover -s source/native-eviv -p 'test_*.py'
.venv/bin/python3 source/native-eviv/build_test_rom.py \
  --rom /private/path/Community1-EN.nds \
  --charmap /path/to/pret/charmap.txt \
  --out /private/path/new-build
.venv/bin/python3 source/native-eviv/run_probe.py \
  --build /private/path/new-build/build.json \
  --fixture /private/path/EV-distinct-TEST.sav \
  --harness /private/path/hg_runtime \
  --out /private/path/new-run
```

The reproducer checks hashes, Pokémon checksum/data, restored graphics, save and
cold boot. Raw visual review remains `pending`; human image review is recorded
separately. Never transfer savestates between ROM revisions. The
[TEST decoder](inspect_test_mon.py) retains its original one-member mode;
multiple slots require explicit count/index.

`run_party_probe.py` uses the same arguments and fixture SHA-256
`966338cfff49cd214479adce11f113df4085c357634b1febce1d89638e1ac583`, also checking
708 independently prepared party bytes. An early IT sample stopped inside temporary
egg decryption in `GetBoxMonData`: the data was already plaintext/checksum-valid
although that function had not set the flag. Later dumps were intact. The tool
now samples the stable screen before L/R and during cold reload, preserving its
strict decoder and earlier attempt rather than calling the intermediate sample
save corruption.

For profiling, `prepare_profile.py --core /path/to/observer-core --out
/private/path/new-profile` requires the exact runner revision/two hook hashes.
It copies tracked files only and leaves the original checkout untouched.
Configure CMake from `frontend/` with `MELONDS_SOURCE` pointing at the copied
`core/`, `HG_BUILD_WAIT_LOOP_TEST=OFF`, then build `hg_runtime`. This is a separate
observation frontend, not an upstream melonDS contribution.

`run_profile.py` requires `--rom`, `--fixture`, `--harness`, `--harness-sha256`
and `--out`, binding the reviewed observer binary. It measures 600 idle DS frames
and eight presses each of L/R/SELECT, checks completed calls and input/Pokémon/
SRAM integrity. A public-reproducer rerun matched r5 aggregates exactly.
The historical `build_test_rom.py --baseline-r4` comparison required the local
`history/eviv-r4.c` source and its measured 480-byte payload; that source is not
distributed in this checkout, so this optional comparison is not reproducible
from the public tree alone. The recorded earlier run reproduced the old payload
and full EN ROM exactly.
The default builds r5. Host `profile_trace.h`/C++ tests do not enter the ROM.
