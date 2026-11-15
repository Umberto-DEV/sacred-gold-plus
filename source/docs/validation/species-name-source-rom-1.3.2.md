# Native species-name production and borrowed String lifetime

This case executes `GetSpeciesName(species,0)`→native CopyTo(capacity11)→native
String_Delete in one CPU/RAM context. It checks six species used by trainer31
against the existing constructor model, extending the
[native message method](trainer-message-source-rom-1.3.2.md). The
[complete caller case](trainer-message-caller-source-rom-1.3.2.md) retains its
species-name model; this standalone result does not retroactively execute a
native species producer inside that earlier constructor.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Start at the observed caller and establish its real heap, bank, representation
and borrowed-pointer contract. Separate a correct returned String from correct
Msg/NARC teardown. Test the longest selected name and nonzero heap fills;
unused String spare is not a guaranteed zero. Require raw readback, source
correspondence, instruction/ABI/write evidence and causal counterproofs. Review
those conclusions independently before reusing a model outside its scope.

## Il materiale più grezzo da cui partire

Use your own exact retail, inherited Plus1.1, V4 and final r4 inputs listed in
the [message input table](trainer-message-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Final images are EN152786844B SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`
and IT159029760B SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Whole-image pins establish language/revision; a similar function name or header
alone does not. Keep ROMs, extracted banks, reports, saves and BIOS local.
The repository supplies developer code/tests and metadata, without retail fixtures.

Source correspondence uses HGSS reference
`cb614ad23449d5852b40321dc409c4143872b35c`:
[msgdata.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/msgdata.c),
[pokemon.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pokemon.c),
[heap.h](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/include/constants/heap.h).
Their SHA-256 values are respectively
`2fcd674561c88d39615407f204d21fab4420b5de9506e4fc78651b1c67a1c8d2`,
`1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3`,
`a656807d4e304b89064d034139c3b57aea3a31d078cdfa92de26354eee21589e`.
The parent case also identifies String/filesystem source. Original native MW
compiler and objects remain unavailable: source/byte/semantic correspondence
does not establish an original C-to-object reconstruction. No native compiler or ROM
build is invoked; the existing composition inherits these native spans.

The `MON_DATA_SPECIES_NAME` case in `SetBoxMonDataInternal` calls
`GetSpeciesName(blockA->species,HEAP_ID_DEFAULT)`. That heap enum is0,
distinct from heap11 used by trainer-message production. Raw caller span
`0206F4AE..0206F4CA` is28B, physical`000734AE`, SHA-256
`d86015b43ee5d6fc684af1db99217d61f2a812d5bfdb7bb69e16fb9d1f36d870`.
BL sites`0206F4B2/0206F4BC/0206F4C2` call producer/CopyTo/Delete;
the native caller loads heap0 and copy capacity11. Earlier constructor receipts
observe six modeled producer calls at SP`023BEE10`, returning to`0206F4B6`.
Those observations identify the caller boundary, not the previously unexecuted body.

Native wrapper `0200BCDC..0200BD02` is38B/16 ordinary Thumb starts,
physical`0000FCDC`, SHA-256
`ebd9e75544b5604322265445535b367d06926905f6a741b762746cb27e59e93e`.
It pushes16B, creates lazy MsgData for NARC27/bank237, produces a String,
destroys MsgData and returns that still-live String. Internal BLs at
`0200BCE8/0200BCF2/0200BCFA` reach native NewMsgData/NewString/Destroy
with LR`0200BCED/0200BCF7/0200BCFF`. Wrapper NULL path`0200BD02..0200BD06`
and alignment are excluded. There is no wrapper literal pool.

The wrapper plus the parent's228 qualified message/copy/delete starts gives244.
ARM9 physical mapping in V4/r4 is `RAM - 02000000 + 4000`, independently
checked against decoded sections. Retail/base comparisons use decoded sections;
no compressed physical offsets are invented. Wrapper, caller and ordinary message
code match across seven address-attributed images; retail IT addresses remain
unattributed. Fixed native code and pools remain separate from SDK body identities.

Resource bank237 is in NARC27 `a/0/2/7`. Independent FAT/FNT/NARC and ndspy reads
agree, as do two message decoders. Current banks contain496 entries/key`D00E`:

| Language | Bank bytes | r4 physical offset | SHA-256 |
| --- | ---: | --- | --- |
| EN | 12180 | `08D99C50` | `3cd76df795a79b5cd5f9129a1fdc4163f72189d9430fcdd9eb7c631b10c1bcee` |
| IT | 12188 | `093525AC` | `4b9c30a450a2bf7ffafbe448865ec2cadeade4af7b328c25c90ccb465d60f594` |

Both retail banks use key`782C`; base1.1/V4/r4 use`D00E`. Full bank bytes
change at retail→base and then remain identical through V4→r4 per language.
All six EN raw vectors change at retail→base; the six IT vectors remain equal
despite changed encrypted bank bytes. Current-header assumptions are not applied
to historical inputs. Message table decryption uses the actual header key.
This identifies the inherited data transformation by readback; the original
base1.1 bank-generation recipe is not reconstructed in this case.

| Species ID | Words including EOS | Native logical size | Copy bytes |
| --- | ---: | ---: | ---: |
| 355 | 8 | 7 | 16 |
| 353 | 8 | 7 | 16 |
| 93 | 8 | 7 | 16 |
| 200 | 11 | 10 | 22 |
| 302 | 8 | 7 | 16 |
| 94 | 7 | 6 | 14 |

These six records are not packed: raw and expanded words agree in both current
languages. The trainer729 packed-name result cannot be substituted for bank237.
Three encrypted reads provide header4B, table8B at`4+8*species`, then payload2N.
Native instructions decrypt and populate Msg12B, String`2*N+10` and temporary2N.
String capacity is N, not a hardcoded11; capacity11 belongs to the consumer.
Species200 exercises exact fit, including EOS. Remaining destination bytes retain
their initial fill. String spare u16 is excluded from that copied payload.

## I metodi e gli strumenti da usare

Use the [owner](../../features/trainer-strategy/README.md),
[verifier](../../features/trainer-strategy/tools/attribuisci_nome_specie.py),
[SDK profile](../../features/trainer-strategy/test/species_name_bench.py),
[profile tests](../../features/trainer-strategy/test/test_species_name_bench.py)
and [receipt tests](../../features/trainer-strategy/test/test_species_name_attribution.py).
Dependencies follow the [bench](../test-bench.md#linking-source-to-an-exact-rom):
Python3.14.7, ndspy4.2.0, Unicorn2.1.4/default17 and Capstone package5.0.9
(module5.0.7). Qualified RSS accounting supports macOS/Linux. No B.run or
high-level GetSpeciesName stub is installed in this standalone CPU.

From repository root, substitute your own images and fresh private output:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_nome_specie.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --retail /path/to/own-retail-EN.nds --base /path/to/own-plus11-EN.nds \
  --v4 /path/to/own-v4-EN.nds --json /path/to/private/species-EN.json.gz
```

Repeat for IT. Source-directory outputs, existing files and aliases are refused.
Expanded output is bounded4MiB/stored2MiB. Run one language per process and one
producer at a time, with180s/1GiB RSS/2MiB log/8MiB case budget. Allow1GiB peak
disk growth while retaining10GiB free. The CLI checks OS high-water RSS before
analysis and after output encoding, with correct macOS-byte/Linux-KiB units.

An eight-image diagnostic process exceeded1GiB OS RSS while a sampled monitor
reported a smaller peak. That run is retained as an exceeded-budget acquisition,
not a within-budget pass. Separate language processes and collection of preceding
sandbox cycles keep the final campaigns bounded. OS peak, rather than a short
polling sample, is required; a test rejects the observed1102741504B overrun.

The SDK profile authenticates the unchanged message parent and exactly changes
one fixture-ID tuple, two heap-expectation constants11→0 and one bank expectation
729→237. Reversing those edits must restore whole function ASTs, including
signatures/wrappers; all other method code remains identical. Native instructions
are never transformed and no species is disguised as a trainer ID. Six heap/NARC
models supply heap fill, opaque handle, encrypted slices and free poison;
they never serialize decoded String or MsgData fields after entry.

Three outer APIs share one initialized CPU without SP/cookie resets between
calls. Three internal message APIs use `outerSP-16`; outer CopyTo/Delete use
outerSP. Scoped observer metadata changes require unchanged CPU/RAM. Source-derived
ABI checks use actual LR and saved registers, including GetSpeciesName's final
LR`0200BB6B`: POP PC restores the return address without restoring the LR register.
The unified native transcript includes42 stack stores and`11+5*N` object/decrypt/
copy stores. All244 starts,11 SDK entries, five nested helpers and three internal
returns are required. Exact hook count is`233+34*N`:505/607/471 for N8/11/7,
with96B maximum stack under128B guard. These are emulator counts, not hardware cost.

At getter return only String is live: Msg, NARC handle and temporary are already
closed. CopyTo borrows String, then native invalidation precedes its final free.
Canaries, precise read/write ranges, frozen unrelated4MiB RAM and unchanged RNG
check ownership. Test heap addresses are synthetic fixtures, not installed heap
assignments or real NARC filesystem-object layouts.

Each language runs18 positives (six species × fills00/C7/39), three OFF pairs
covering N7/8/11, two void-R0 controls on the N11 wrapper and six causal falsifiers.
Skipping native Msg destruction or final String free keeps the correct returned
String/copy but leaks the specific resource. Heap11/bank729 substitutions violate
the qualified caller/profile; they are not claims that the library rejects those
parameters universally. Short capacity10 for species200 stops at the excluded
assertion path; its body/safe return is not qualified. Wrong return PC is rejected.
Each failure must match its predicted stage, count, resources and mutation evidence.

For the two compressed reports and private links `r4-EN.nds`/`r4-IT.nds`:

```sh
SGP_SPECIES_ROM_DIR=/path/to/private/rom-links \
SGP_SPECIES_REPORT_DIR=/path/to/private/reports \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_species_name_attribution.py
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_species_name_bench.py
```

Fourteen receipt/portable methods and three profile methods passed with both
inputs and no skips. Final campaigns took2.321s EN/2.866s IT with OS RSS777928704B/
804503552B; the CLI and external OS measurements agree. Independent raw/source
review and replay confirm that, for these six current inputs under zero-fill
heap policy, returned native String bytes exactly match the constructor model.
With C7/39, only the spare differs; copied name bytes remain identical.
This is finite returned-data/consumer equivalence, not equivalence of the model's
allocation/filesystem internals or native execution in the earlier caller campaign.

Documented provenance, installed-byte identity, initialized API activation and
finite source semantics are established separately. Original compiler reconstruction,
native heap/NARC/FS bodies, constructor integration, other species/eggs/failure
paths, natural encounters, rendering, SAVE/cold restart and hardware remain outside
coverage. No game, ROM, save layout, ABI, identifier, setting or default changed;
no memory reclaim or game speedup is demonstrated. Private receipts preserve
commands, exits, hashes, source snapshots and diagnostic limitations.
