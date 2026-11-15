# Native NARC member selection on the exact ROM

This case executes `ReadWholeNarcMemberByIdPair` and its native parser for
trainer31's header55/31 and party56/31. Five FS services expose an entire raw
archive and cursor. Native instructions select the member and close the file.
The [complete caller](species-name-caller-source-rom-1.3.2.md) still uses its
previous high-level read boundary; composing this parser there is separate work.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Replace the precise unexplained boundary, rather than treating a host copy as
native archive selection. Follow source, installed instructions, path table,
NARC metadata, ABI and resource lifetime in both directions. A correct payload
does not prove file closure. Seek a close omission with identical output/RAM,
and a partial read that returns normally. Review regional pointer differences
and distinguish modeled file state from a reconstructed native SDK structure.

## Il materiale più grezzo da cui partire

Use your own exact r4 Plus1.3.2 images:

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Whole-image pins establish revision/language; the IT Plus internal header uses
IPKE and does not independently identify the language. Historical input identity
and preparation are documented in the [rematch case](rematch-source-rom-1.3.2.md)
and [species-name case](species-name-source-rom-1.3.2.md). ROMs, raw archives,
extracted members, reports, saves and BIOS remain private. No build or capture
is needed. The verifier reads only your own inputs.

Reference source is [filesystem.c at the pinned HGSS commit](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/filesystem.c#L7),
SHA-256 `ee526fc2835b2c2259dd393087fb1a5ca036dbf467bcfbd7735b1476819c869d`.
The whole-member wrapper passes the path indexed by NARC ID, member ID, offset0
and size0. The native parser reads BTAF/BTNF/GMIF metadata, derives the payload
position and reads `end-start` bytes. Source correspondence and installed-byte
identity are established; original native compiler/objects and exact C-to-object
reconstruction remain unavailable. No new Plus payload is compiled or inserted.
These final native code spans are identical across the eight inspected images.

| Ordinary Thumb span, end excluded | Bytes / starts | r4 physical offset | SHA-256 |
| --- | --- | --- | --- |
| `02007508..0200751E` | 22 / 10 | `0000B508` | `35f4ac50be98a10b0c0ebd562ed4d45e5bdffa88ca7ff0134f0c09090a8df196` |
| `0200732C..0200738E` | 98 / 42 | `0000B32C` | `0f2890f6d5c533785bd464399a496a780ab21162dabc4829f3c878c5049f379c` |
| `02007392..020073F4` | 98 / 43 | `0000B392` | `5353169e22ee79de93dfe32d757e89feea1ef586b9fba01e30fdf6dc2fdbbf47` |
| `020073F8..0200740C` | 20 / 8 | `0000B3F8` | `7740a174f812ba014226329d5680a4a9cff0cb216fc4c37180ab3392adba6262` |

These238B contain103 qualified starts. Assert bodies, adjacent allocating
functions, alignment and literal pools are excluded. Pool`02007520` points to
`0210F210` in r4; rows55/56 at`0210F2EC/F2F0` point to paths
`0210F038/F030`: `a/0/5/5` and `a/0/5/6`.
Independent raw ARM9 and decoded-section reads must agree. These r4/V4 spans
are uncompressed and resident. Legacy compressed/autoload sections are read
logically; no direct physical offset is inferred for their decoded bytes.

The optional retail→base1.1→V4→r4 comparison verifies both languages. Retail IT
has the same four code spans at the same addresses but a different pool/table:
`02007520 → 0210F1B0`, rows`0210F28C/F290 → 0210EFD8/EFD0`.
Following those actual pointers gives the same two paths. Comparing only current
absolute data addresses would leave a false gap. This result concerns this
reader, not earlier unrelated functions whose retail IT addresses remain open.
The retail IT FS SDK block differs; the current SDK body identity cannot be
transferred to it. No historical execution is claimed.

The native wrapper calls the parser at`02007516`, LR`0200751B`, with
R0..R3`[destination,path,31,0]` and fifth size0 at the wrapper SP.
The parser crosses to these ARM SDK entries:

| FS model | ARM entry | Calls |
| --- | --- | ---: |
| Init | `020D7F98` | 1 |
| Open | `020D8278` | 1 |
| Seek, origin SET | `020D83DC` | 5 |
| Read | `020D83CC` | 7 |
| Close | `020D82C0` | 1 |

The SDK block`020D7F98..020D8448` has SHA-256
`85827bd31be4e7418e46bf4715e60ca1d4287b4243ff129973febadeac343b0c`
in both current images. This proves the identity of modeled bodies, not their
execution. The [existing native FS bench](../../features/ui-native/test/test_resource_rom.py)
can lower that boundary in a future qualified case.

[Nitro's reference FSFile declaration](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/lib/include/nitro/fs/file.h#L173)
contains a size80B comment; the installed parser's apparent local region is72B.
The [later Init extension](native-fs-init-source-rom-1.3.2.md) compiles the actual
declarations as72B under ARM32 and identifies the comment as stale. This older
opaque-handle reader does not reconstruct native SDK layout or execute Init.
The earlier size discrepancy therefore does not
establish matching structure layouts or an overflow. Here FS state is an opaque
host ledger: Init/Open/Close write no guest FSFile fields. The parser only passes
its address to the five models. No80B clear or native SDK layout is fabricated.
Wrapper frame16B + parser frame120B gives136B peak. The file pointer is at
`outerSP-112`; all FS entries occur at `outerSP-136`, with R4..R11/SP preserved.
ARM model entries require width4/ThumbFalse; their LR returns to Thumb. BLX at
`020073FE` crosses a1KiB boundary and remains one4B start. A split halfword at
`02007400` is not admitted.

| r4 archive, same EN/IT | Whole bytes / SHA-256 | FAT ID / physical start |
| --- | --- | --- |
| 55 | 20716 / `4de9e541894f6573c5b52e338de911a71fcf82c206ebf041bccb81e817c13299` | 184 / `01F91A00` |
| 56 | 31286 / `964a3efd40d83ecb196035f257264ba0e76a55818ed0d13aadde15b890451da9` | 185 / `01F96C00` |

Both have738 members, BTAF at16/size5916, BTNF at5932/size16 and GMIF at5948.
Row31 at276 contains start/end620/640 for55 and1596/1704 for56.
The seven read positions/sizes are12/2,20/4,24/2,5936/4,276/4,280/4,
then6576/20 or7552/108. Five seeks are12,20,5936,276 and the payload position.
Native code computes these values; models only copy requested raw slices and
advance the cursor. Member55/31 is physical`01F933B0`, SHA-256
`db2e0fa9e4d0b97a0d1721e878001bcddafe1e379827adccc37844cdbce13fff`;
56/31 is`01F98980`, SHA-256
`2096c9d5a3943dca51dec0ea9b0b006387f2fb5b0d6778a49f58c2803806395c`.

Retail56/31 has72B; base1.1 onward has108B. Whole archive56 changes again
between V4 and r4, despite member31 remaining identical. A matching selected
payload never authorizes substitution of a different whole archive. The tool
records both identities and each image's physical offsets.

## I metodi e gli strumenti da usare

Use the [verifier](../../features/trainer-strategy/tools/attribuisci_lettore_narc.py),
[portable/replay tests](../../features/trainer-strategy/test/test_narc_reader_attribution.py),
[owner](../../features/trainer-strategy/README.md) and
[test bench](../test-bench.md#linking-source-to-an-exact-rom).
Verified dependencies are Python3.14.7, ndspy4.2.0, Unicorn2.1.4 and Capstone
distribution5.0.9/module5.0.7. Use the qualified default17/Cortex-A15 hook
contract; it is not a console hardware timing model.

```sh
python3 source/features/trainer-strategy/tools/attribuisci_lettore_narc.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --json /path/to/private/narc-reader-EN.json.gz
```

Repeat for IT. To reproduce lineage in the same report, provide all three
historical inputs as well:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_lettore_narc.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --retail /path/to/own-retail-EN.nds \
  --base /path/to/own-base1.1-EN.nds --v4 /path/to/own-v4-EN.nds \
  --json /path/to/private/narc-reader-EN-with-history.json.gz
```
 Missing historical material does not prevent
the current exact-ROM API check. Existing outputs/aliases and outputs inside
source are refused. Expanded report is limited4MiB/stored2MiB. Use one producer,
180s/1GiB OS RSS/2MiB log/8MiB case,1GiB disk peak and at least10GiB remaining.
The CLI audits Mac/Linux peak-RSS units before/after acquisition and encoding.

The model never preselects member31 for delivery. Open chooses the whole raw
archive from the actual native path; Seek and Read implement a bounded cursor.
Native parser stores, its six raw metadata copies, full136B frame, all103 starts,
fifteen FS entries/returns and exact raw read provenance are required. There
are seventeen native stores. All other RAM, destination/stack canaries and RNG
remain unchanged. No heap, callback, overlay, post-entry payload insertion or
saved-context restoration is used.

The finite matrix has four positive calls (two archives × two stack poisons),
two volatile-register controls, two OFF pairs and two executed falsifiers per
language. Controls poison R1/R2/R3/R12/NZCV at FS returns while retaining the declared
model R0 policy and callee-saved registers: output and whole RAM must remain identical.
OFF disables only the native write log and compares every other receipt field,
including whole final RAM. Counts118/136 establish path/frame coverage, not speed.

Skipping native Close BLX`02007404` leaves the same payload and entire RAM but
an open ledger, fourteen FS events and117 hooks. All103 native starts remain
visited, demonstrating why code coverage alone is insufficient. Full counter
return vectors, CPU/ISA and source-derived residuals remain required.
A short final Read delivers/returns107 of108 bytes; the native function returns
normally, leaving the last destination byte at its initial A5 value. The oracle
must reject that exact partial output. Source does not check IO return values;
this is not safe error handling or an observed cartridge failure. Final R0 is a
Close residual in a void API, not a success status.

```sh
SGP_NARC_READER_ROM_DIR=/path/to/private/rom-links \
SGP_NARC_READER_REPORT_DIR=/path/to/private/reports \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_narc_reader_attribution.py
```

Use links`r4-EN.nds`/`r4-IT.nds` and reports`narc-reader-EN.json.gz`/IT.
`SGP_NARC_READER_LANGUAGES` selects a comma-separated diagnostic subset.
Without private inputs only six portable methods run; nine replay methods skip.
Replay reads raw inputs and receipts without executing the guest.

Both language campaigns passed ten runs: EN0.836s/OS492584960B,
IT1.317s/OS505184256B. Fifteen portable/replay methods passed with both inputs
and no skips,0.392s/OS656457728B. Independent reviews checked source/raw ABI,
regional pointers, current execution and counter causes. Review found that a
completed counter did not bind its entire return ISA/helper context; the gate
was tightened before campaigns and mutations on the actual counter are now
rejected. No game source, ROM, save, ABI, identifier or default changed.

Documented provenance, installed-byte identity and finite source semantics are
established separately from exact native compilation. Activation is observed
only at initialized standalone APIs under five FS models. Actual caller
composition, native FS/card/SDK layout, other members/partial-offset APIs,
assert/error paths, natural encounters, SAVE/cold restart and hardware remain
outside coverage. No memory saving or game speedup is claimed.
