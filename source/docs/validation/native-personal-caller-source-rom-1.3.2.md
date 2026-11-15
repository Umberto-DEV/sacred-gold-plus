# Native personal-data read, growth rate and EXP

The first modeled personal-data read in the [complete caller](native-party-caller-source-rom-1.3.2.md)
is replaced by the installed native reader, in the same CPU. This finite case
follows Duskull/species355's personal record through attribute21, growth table,
EXP setter and the completed trainer31 party. It leaves186 Normal/188 Plus
other ReadWhole calls as explicit models. No gameplay source or ROM is changed.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Follow the data into a real consumer, distinguishing a getter's attribute ID
from a structure offset. Reconstruct native call frames and volatile residues
from code rather than copying a prior callback's register values. Check both
source→installed-byte and raw-member→native-field paths. A deliberate change
to one loaded value must cause the predicted later effect, while unchanged
payload alone cannot prove consumption. Independently review instruction/data
boundaries, ABI, remaining SDK owners and false-success counterexamples.

## Il materiale più grezzo da cui partire

Use your own exact r4 ROM and retained/reproduced rematch/stub/teams project
objects. The [preceding case](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire)
lists their SHA-256 identities, sizes, languages and build guides. Required ROM
SHA-256: EN `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Whole-image identity takes precedence over the IT image's inherited header.
No ROM, personal-data dump, Pokémon packet, RAM image, BIOS or save is provided.

The FNT owner is `a/0/0/2`, FAT file131,508 members. Member355 is44 bytes,
SHA-256 `1954a12fbe5fe597e544784d31c7f0a89b98b73c5e53ca1d768d481043749270`.
It is identical in both languages across retail→base1.1→V4→r4, including
growth byte19=4. Whole archives differ:

| Revision | Archive bytes | SHA-256 |
| --- | ---: | --- |
| Retail | 26468 | `6e533889d97eee45db41affe61ceec2e05d7e8dac54126adefbb65eb1f664197` |
| Base1.1 | 26468 | `5f193d2eacddf0ffef9daf7acebd35dcdb21c30f59ab497759c3b7cc335f2d40` |
| V4/r4 | 26472 | `91cd5b2bbd5d161f66aeec5b1b2122ee18946557fea1415c3ed433755960e3db` |

Current BTAF starts16,size4076; BTNF starts4092,size20; GMIF starts4112.
Row355 is at2868, with start15620/end15664. The member is at archive offset19740.
BTNF was16 bytes in the older images; member placement moves by4 bytes without
changing its content. This proves the member's inherited content, not an author
or complete recipe for changes elsewhere in the archive.

| Exact image | Archive ROM offset | Member ROM offset |
| --- | --- | --- |
| EN retail | `0x012B1800` | `0x012B6518` |
| IT retail | `0x012B1600` | `0x012B6318` |
| Base1.1 EN/IT | `0x00397E00` | `0x0039CB18` |
| EN V4/r4 | `0x087FB200` | `0x087FFF1C` |
| IT V4/r4 | `0x08D3E800` | `0x08D4351C` |

Manual FAT/FNT/NARC arithmetic agrees with ndspy. All eight images have the
same103 qualified reader instruction starts. Each image's actual table route
is followed: current literal `0x02007520→0x0210F210`, row2 at `0x0210F218`
points to `0x0210F1E0`; retail IT instead uses `0x0210F1B0→0x0210F1B8→0x0210F180`.
Both resolve to `a/0/0/2`. Historical compressed/autoload sections are decoded;
current direct physical code offsets are not invented for older compressed data.

The source counterpart is `src/pokemon.c` in the reference fork pinned at
`cb614ad23449d5852b40321dc409c4143872b35c` (see the
[native reader provenance](native-narc-reader-source-rom-1.3.2.md)). Relevant
functions: `GetMonBaseStat`, `AllocAndLoadMonPersonal`, `LoadMonPersonal`,
`GetPersonalAttr`, `GetMonExpBySpeciesAndLevel`, `LoadGrowthTable` and
`GetExpByGrowthRateAndLevel`. Constants define attribute21 as growth rate;
`BASE_STATS.growthRate` is at offset `0x13`. Source names support this qualified
semantic correspondence; the original native compiler/object is unavailable.

## I metodi e gli strumenti da usare

[Verifier](../../features/trainer-strategy/tools/attribuisci_personale_chiamante.py),
[finite profile](../../features/trainer-strategy/test/personal_narc_bench.py),
[portable checks](../../features/trainer-strategy/test/test_personal_narc_bench.py)
and [receipt replay](../../features/trainer-strategy/test/test_personal_caller_attribution.py)
reuse the qualified reader and caller without changing their sources.

The first selected native chain is:

```text
CreateBoxMon 0206DED0
  → GetMonExpBySpeciesAndLevel 0206FD00
    → GetMonBaseStat 0206FBE8 (species355, attribute21)
      → AllocAndLoadMonPersonal 0206FA8C (heap0,44 bytes)
        → LoadMonPersonal 020725A4
          → ReadWhole 02007508 → parser0200732C
        ← 0206FAA2
      → GetPersonalAttr 0206FAA8
        → LDRB at0206FB74 reads byte19
      ← 0206FBFA; frees personal; returns0206FD0A
    → GetExpByGrowthRateAndLevel 0206FD30
      → LoadGrowthTable 0206FD14 → modeled ReadWhole3/4/404 bytes
      → LDR at0206FD5C reads table[level]
  ← EXP at0206DF7A → native SetBoxMonData attribute8 → 0206DF86
```

The table entry at `0x0206FAF0` is data, not executable code. Its native dispatch
selects `0x0206FB74`. These getters and consumers are already within the parent's
qualified body map; live-byte and instruction-width/ISA checks remain active.
Current resident ARM9 physical offset is RAM−`0x02000000`+`0x4000`, e.g.
`0x0206FB74→0x73B74`; reader `0x02007508→0xB508`. No overlays contain this
personal getter. The project rematch overlay/source composition remains as
qualified by the preceding case.

Reader entry: `R0=0x02200180`, `R1=2`, `R2=355`, `R3=0x02007509`,
LR=`0x0206FAA3`. Saved R4..R7 are destination,355,`0xFFFF0000`,`0xFFFF0000`;
R8..R11 retain caller cookies. SP is inner SP−320, derived from constructor152,
CreateMon80,CreateBoxMon48,EXP wrapper8,base-stat getter16,allocator16.
The reader adds136 bytes, reaching552 below outer SP; its56-byte guard ends
at the existing608-byte bound. The actual preexisting frame is captured and
17 native stores/six metadata reads are reconstructed over it. No standalone
setup, new CPU, register reset or frame initialization occurs.

R12=`0x022000D8` is derived from the preceding native nickname copy: PID
`0x0098D188` gives block order `(1,0,2,3)`, nickname destination arena+200;
16 copied bytes leave IP at arena+216. This is a path-specific volatile residue.
Reader R0 is ignored by the allocator's real MOV after return, while native
R2=44 persists into the getter/free/allocation chain. The former model left355;
its obsolete unused-register values are not forced back into the guest.

The native parser chooses the raw archive slices. Expected SET seeks are
12,20,4096,2868,19740; reads are `(12,2),(20,4),(24,2),(4096,4),(2868,4),
(2872,4),(19740,44)`. Five FS services remain opaque models. This profile admits
only NARC2/member355, its actual path/table data and44-byte destination; it does
not broaden the trainer55/56 profile or claim all78 personal reads are native.
The existing original backends handle the remaining186/188 reads exactly once.
No artificial personal-read event or body model is inserted.

The sampled native flow binds frames, Thumb state and high caller cookies.
The LDRB before/after vectors must differ only in R5. Register values at the
EXP lookup must agree with its table pointer, offset, selected curve and raw
word, rather than merely agreeing with separately written metadata. The actual
EXP local/pointer, native setter return and final packet complete the link.

## Reproduce

Use the parent's qualified Python3.14/ndspy4.2.0/Unicorn2.1.4/Capstone5
requirements, retained project objects and initialized fixtures. No emulator,
ROM build, save or BIOS is needed. Keep outputs outside `source`.

```sh
python source/features/trainer-strategy/tools/attribuisci_personale_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" \
  --readback-only --json "$PRIVATE_OUTPUT/personal-readback-EN.json.gz"
python source/features/trainer-strategy/tools/attribuisci_personale_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" \
  --json "$PRIVATE_OUTPUT/personal-caller-EN.json.gz"
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_personal_narc_bench.py
SGP_PERSONAL_CALLER_ROM_DIR="$ROMS" \
SGP_PERSONAL_CALLER_REPORT_DIR="$PRIVATE_OUTPUT" \
SGP_REMATCH_OBJECT_DIR="$REMATCH_CASE" \
SGP_STRATEGY_OBJECT_DIR="$STRATEGY_CASE" \
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_personal_caller_attribution.py
```

Repeat with IT. Replay directory naming follows the
[parent instructions](native-party-caller-source-rom-1.3.2.md#reproduce-with-your-own-inputs).
Optionally add all three `--retail "$RETAIL" --base "$BASE11" --v4 "$V4"`
inputs to either verifier mode to reproduce the four-image lineage for that
language. Their identities are listed in the linked native reader guide.
Readback mode creates no CPU and makes no activation claim. Output must be fresh.
Bound each command to180s,1GiB OS RSS and2MiB logs; reserve1GiB temporary disk,
16MiB retained case output and10GiB free after peak. Guest bound is3M hooks/608B
stack. OS RSS/report-size checks are built in; use an external wall-time/log
limiter and run only one heavy producer.

## Results, counterproofs and limitations

The final20 executions passed, ten per language. Eight portable tests and nine
exact-input replay tests passed without skips. Independent raw/source/ABI and
final EN/IT reviews found no unresolved blocker. All eight positive parties,
prepared Trainer52, final seeds and entire final4MiB main-RAM hashes match the
preceding case, with117 additional observed hooks each. This is finite bench
equivalence, not a natural-game or arbitrary-call result.

EN took88.941s with OS peak RSS567853056 bytes; IT89.190s/581697536 bytes.
Replay took9.234s/723828736 bytes. Offline four-image readback took1.642s EN/
1.948s IT, with OS peaks509231104/522895360 bytes and no CPU creation.

The finite matrix is Plus0/1 × two seeds, a second poison, two OFF pairs, one
FS volatile-register control and two counterproofs per language. Observed
positive EN totals are1040226 Normal/1056453 Plus, IT adds34: +117 from replacing
one callback fetch with118 reader/FS fetches. The prefix remains604/638.

OFF differs in six8-byte allocation canaries: four preceding prefix canaries
and two for the44-byte personal allocation. Compare those actual preimages
separately, project exactly48 bytes for reader-phase RAM and keep every other
ABI/stack/transport/flow check. Parent final scratch projections remain explicit.

The semantic counter changes only R5 at `0x0206FB76`, after the real LDRB has
loaded4 from the unchanged raw44-byte personal record. Native code then returns
curve2 and selects growth table2. Both indices are valid; later personal reads
retain4. The source/raw prediction is below. The actual counter runs exercise Plus29
with seed `0x12345678`; Normal27 is a raw/source prediction, not an additional
executed counter profile:

| First level | Curve4 EXP | Curve2 counter EXP | Delta |
| --- | ---: | ---: | ---: |
| Normal27 | 15746 | 16140 | +394 |
| Plus29 | 19511 | 20974 | +1463 |

Curve4 thresholds keep the final levels27/29, so statistics and learnsets need
no new branch domain. The counter's first packet is predicted independently by
changing only EXP in the baseline decrypted block, recomputing checksum and
re-encrypting. The other five packets, seed, names and resources must remain
valid. All five scope hashes for the first nickname precede the mutation and
remain equal; only the25 RAM scope hashes of later names are excluded from
comparison because they include the changed Pokémon. Their complete writes,
ABI, objects, lifetime and neutral transitions are still verified. A Close-leak
counter is separate and requires all name receipts unchanged.

Documented provenance and source/byte correspondence do not reconstruct the
original native compiler. Native activation is observed only in the initialized
caller under explicit FS/heap/other-reader models. No natural encounter, SDK
internals, other personal members/forms, error handling, full battle, UI,
save/restart or hardware coverage is implied. No game fix, speedup or recovered
memory is delivered. Any production change to data handling needs a separate
maintainer decision and its own gameplay/ABI/error-path validation.


The separate Close-leak control completes the whole caller with the same party
and whole final RAM hash, while its file ledger remains open. Native R0 is still
forwarded from the parser and then ignored by the allocator's actual MOV.
Equal output and final RAM therefore do not prove resource closure.

| Conclusion | Evidence and limit |
| --- | --- |
| Documented provenance | Native personal record355 inherited unchanged through eight exact images; native getter/reference source and actual caller path identified. |
| Reconstructed binary correspondence | Retained project payload/object/readback checks inherited from the linked build recipes; no new compilation or original native MW reconstruction. |
| Demonstrated semantics | Actual byte19 load, getter21 result, selected raw growth table, native lookup/setter and complete source-valid packets under declared SDK models. |
| Observed activation | Initialized complete caller, Plus0/1, two seeds/two poisons; Plus1/default-seed counter and volatile controls. |
| Unattributed links | Native FS/heap internals and186/188 other ReadWhole calls, other forms/IDs/errors and natural or physical-device execution. |
