# Native FindPath in the complete trainer caller

This follows the [isolated Find wrapper](native-fs-find-source-rom-1.3.2.md) and
[complete Read/Wait caller](native-fs-read-caller-source-rom-1.3.2.md). It replaces
the selected Find model with the installed native body in the same initialized
CPU. SendCommand remains an explicit boundary. These tools attribute code; they
do not install a patch or change game behavior, ROMs, saves, ABI or identifiers.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Keep the original caller and the preceding native components. Reconstruct the
new Find stack lifetime, actual ABI, data reads and modeled writes in execution
order. Require both source/recipe→ELF→ROM and ROM→caller→source links. Compare
with the old Find model using the same declared BSS input. Record any residual
RAM differences; a matching party does not establish matching native execution.

Use an independently reviewed counter: Send4 returns2 after delivering the same
ID. Native Find preserves2, while Convert normalizes it to1. The positive oracle
must reject the observed Find return after policy metadata is disguised. Keep
the earlier Read error counter and OFF/volatile/preimage controls.

## Il materiale più grezzo da cui partire

Provide your own exact inputs. Current EN:152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`.
Current IT:159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both are IPKE revision0; the IT text is localized. ARM9 file offset`0x4000`,
load`0x02000000`. Find is in its uncompressed main section, with no overlay or
autoload lifetime. The linked wrapper guide documents retail→inherited base→V4→
Plus readback, including the different retail IT pool pointer.

| Item | Address or extent | Meaning |
| --- | --- | --- |
| Find body |`[0x020D7FC0,0x020D8100)`|320 ARM bytes/80 binary starts |
| Literal |`0x020D8100` / ROM`0x000DC100`|4-byte pointer to BSS |
| Current physical body | ROM`0x000DBFC0`,324 bytes | instructions plus pool |
| Root aggregate |`0x021E362C`,12 bytes | BSS; no initialized-ROM mapping |
| DIR |`0x023BEDD0`,72 bytes | temporary directory FSFile |
| Output ID |`0x023BEE28`,8 bytes | opaque archive token and file140 |
| Path |`0x0210F198`|`a/0/1/1\0` |
| TOP |`0x023BEEC0`| selected reader entry SP |
| Find minimum SP |`0x023BEDA8`|DIR−40; full reader frame280 |

The full324-byte SHA-256 is
`baf1c233ca8efcaa3ca58e996fe2f01e437fad5753dca7bbe1e6e782dd9abcf8`.
The retained recovered object SHA-256 is
`e46711e0cf7503284e908fb4b10216a3ed2d2a1d261a424a3d7ee8fc87cb34f6`.
The [wrapper guide](native-fs-find-source-rom-1.3.2.md) identifies the assembly,
compiler/flags,18 source headers/layout checks and definition-only C hash.
Original MW compiler/objects remain unavailable. Recovered binary correspondence
is separate from original compiler provenance.

The source counterpart is `lib/NitroSDK/src/fs/FS_file.c::FSi_FindPath` in
[the pinned reference](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c).
`FS_archive_suffix.c` and `FS_rom.c` explain first-archive root initialization.
The resource is NARC11, FAT file140,11356 bytes at current ROM
`[0x01093800,0x0109645C)`, SHA-256
`beed8ddf861e575b9c38dfa65a6c0c51fb237305ddd73c393f5e2009fbc75260`.
Member310 is16 bytes at archive offset8780/ROM`0x01095A4C`; PP15 is byte6.
Raw FNT, FAT, archive and member readbacks are inherited and checked again.

ROMs, extracted files, RAM, saves, BIOS and private captures remain local.
The public tests use synthetic inputs or require developer-supplied fixtures.

## I metodi e gli strumenti da usare

### Declared input, lifetime and ownership

The initialized bench starts with zero at the BSS root. Setup writes the declared
12-byte aggregate once: opaque token`0x021E3654`, then zero own_id/index/pos.
It compares all4MiB and all16 registers to require that exact setup delta. This
happens before seed/caller/getter APIs and before the original frozen snapshot.
Read-only fences check the root before and after all three APIs, with their
registers bound to actual API entries/returns. The root is never repaired between
APIs. This input is source-derived, not an observed natural boot or a reconstructed
FSArchive. The modeled baseline receives exactly the same root input.

The original Convert BL at`0x020D81A8` enters Find and returns to ARM
`0x020D81AC`. Find PUSH28 and local12 use40 bytes below DIR. The wrapper copies
the BSS aggregate, scans the prefix `a/`, fills DIR.arc/ARG.pos/path/mode/result
and calls Send4 at`0x020D80F4`. Its actual ARG pointers select raw FNT path
`a/0/1/1`→140. The model writes ID8 only; it does not model native command,
error/status, queue/list/card/archive or completion. DIR.command remains14 from
Init. The later Send0 payload/position/completion12 projection remains explicit.

Send4 returns at`0x020D80F8`; native POP restores R3–R8, SP and PC. Find leaves
LR=`0x020D80F8`, R1=4/R2=0/R3=0 normally; provider clobber changes R1/R2/IP,
while R3 is restored from the native stack. Convert CMP/MOV normalizes nonzero
R0 to1. The full contexts for Find1/2 converge at`0x020D81B4`. Open's ID load
then derives the actual Fast entry. Old synthetic volatile registers are never
restored to manufacture agreement.

Find's source oracle predicts47 hooks at42 unique starts,17 native word stores,
18 reads and the separate Send event from the actual contextual preimage. It
checks the complete4096-byte page and compares actual bytes outside that page.
The complete chronological native-store transcript inserts Find after the inner
Init and before Fast. Later stack reuse must not resurrect dead Find fields.

The new56-byte readonly guard is`[TOP−336,TOP−280)`. Its first48 bytes lie below
the existing global608-byte range; they are observed in their actual preimage,
not poisoned or excluded. The old reader restore range`[TOP−296,TOP)` already
contains the new280-byte frame and stays unchanged. Forty guard bytes remain
outside that restore range; the remaining16 are checked explicitly. The old
guard's final40 bytes are now source-owned stack, with before/after views retained.
Global608 and the existing1124-byte OFF heap projection do not grow.

### Reproduction

Use Python3, ndspy, Capstone and Unicorn2.1.4/model17 (Cortex-A15), plus the
project and recovered objects from the parent guides. Build `fs-find-path.o`
with [the wrapper builder](../../features/trainer-strategy/tools/compila_fs_find.py)
and retain its `manifesto.json`. The caller independently reads physical ROM,
decoded sections and ELF text, rejects text relocations and authenticates that
receipt. No new compilation or full ROM build is needed for this integration.

Set these paths to your own inputs and fresh private outputs outside `source/`.
Repeat with IT and the corresponding exact ROM/project objects.

```sh
python3 source/features/trainer-strategy/tools/attribuisci_fs_find_chiamante.py \
  --rom "$SGP_ROM" --language EN --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --recipe-dir "$SGP_FIND_RECIPE" \
  --readback-only --json "$SGP_OUT/find-caller-readback-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_find_chiamante.py \
  --rom "$SGP_ROM" --language EN --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --recipe-dir "$SGP_FIND_RECIPE" \
  --probe --raw-dir "$SGP_OUT/probe-raw" \
  --json "$SGP_OUT/find-caller-probe-EN.json.gz"

python3 source/features/trainer-strategy/tools/attribuisci_fs_find_chiamante.py \
  --rom "$SGP_ROM" --language EN --objects "$SGP_REMATCH_OBJECTS" \
  --strategy-object "$SGP_TEAMS_OBJECT" --read-recipe "$SGP_READ_RECIPE" \
  --wait-recipe "$SGP_WAIT_RECIPE" --recipe-dir "$SGP_FIND_RECIPE" \
  --raw-dir "$SGP_OUT/raw-EN" --json "$SGP_OUT/find-caller-EN.json.gz"

python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_find_caller_*.py' -v
```

Readback-only executes no guest CPU; it is mutually exclusive with probe.
Probe runs one positive caller and its matched modeled baseline. The full matrix
adds Plus/seed, OFF, alternate stack preimage, volatile, Close2, ReadSend0,
Read error1 and Find2 controls. Raw records precede semantic checks. Each language
retains one candidate/baseline full final4MiB pair, bound to actual run hashes,
so another developer can independently compare final bytes without a new CPU.
Keep argv, exit codes, source snapshots, logs and peak RSS locally. Use one
producer and explicit180s/1GiB RSS/2MiB log/16MiB case caps, with10GiB free after
peak. Never overwrite original fixtures.

### CPU-free replay and source revisions

For optional private replay, use report files `find-caller-EN.json.gz` and IT,
raw directories `raw-EN` and IT with thirteen numbered records and the two
`*-final.bin.gz` witnesses per language. Set the following inputs before running
the same test command:

```sh
SGP_FS_FIND_CALLER_REPORT_DIR="$SGP_CALLER_REPORTS" \
SGP_FS_FIND_CALLER_RAW_DIR="$SGP_CALLER_RAW" \
SGP_FS_FIND_CALLER_ROM_DIR="$SGP_ROM_LINKS" \
SGP_FS_FIND_CALLER_READ_RECIPE="$SGP_READ_RECIPE" \
SGP_FS_FIND_CALLER_WAIT_RECIPE="$SGP_WAIT_RECIPE" \
SGP_FS_FIND_CALLER_FIND_RECIPE="$SGP_FIND_RECIPE" \
SGP_REMATCH_OBJECT_DIR="$SGP_REMATCH_CAMPAIGN" \
SGP_STRATEGY_OBJECT_DIR="$SGP_STRATEGY_CAMPAIGN" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_find_caller_*.py' -v
```

ROM links must be named `r4-EN.nds` and IT. The project-object campaign directories
contain `public-build-EN`/IT and `build-EN`/IT as described by the parent guides.
Without private inputs the four replay tests explicitly skip; the nine portable
tests need no ROM. Qualification requires zero skips.

The acquired matrix capture runtime SHA-256 is
`90071ed9a1427119b4d9cb8af295805c678662f393aa1d83b0f5e77eeb2dcfeb`.
The stricter qualified verifier SHA-256 is
`a2c0b332d2d566537fe30b40cd3379576b5d54340a707e49204103d0279b5373`.
Python equality had accepted bool/int/float aliases in some Find metadata.
Regression tests reproduced them before the correction. Canonical JSON wire
comparisons now distinguish policy, register/flow/read/store/service and model
values, and model occurrence has a strict integer type.

The captured reports retain their original identities. To replay those historical
reports, additionally set `SGP_FS_FIND_CALLER_CAPTURE_SOURCE` to the exact retained
capture-runtime source. Tests authenticate its hash against each report, require
all other source identities unchanged, and compare the entire module AST except
`require_find`. Producer, composition, namespace recipes and all other functions
must remain identical. New captures made with the qualified verifier need no
historical-source exception. An oracle correction does not justify relabeling old
captures or repeating an unchanged guest campaign.

The replay checks all distinct cells, original parent oracles, raw/report equality,
source revisions, exact final RAM pairs and read-only root fences. Mutants cover
Find ABI/flow/reads/stores/Send, unowned page writes, guard changes, all three API
pre-fences and typed metadata aliases. Repeated semantic checks must preserve the
static namespace-binding receipt; temporary oracle bindings are not new source
composition events.

### Evidence and limits

The final matrices complete26 callers,13 per language:24 with native Find and
two matched modeled baselines. Each native reader has779 hooks,308 executed
starts and186 native stores (OFF omits the store log); Find contributes47 hooks,
42 unique starts,17 stores and18 reads. Ten remaining boundaries are all Send:
4,6,seven0,and8. The four Plus/seed cells per language, two OFF cases, alternate
preimage, clobber, Close2, ReadSend0, Read error1 and Find2 pass their finite
contracts. EN takes149.566s/642105344-byte peak RSS; IT152.707s/608944128 bytes.
No compiler was invoked. Source qualification covers64 identities and12 recipes,
with four static namespace bindings.

Find2 preserves native R0=2 and is rejected after metadata disguise with
`Find caller source returned`; Convert returns1 and later party/Trainer/RNG/PP
and final RAM match normal. Read error1 is independently rejected with
`Read caller source returned` while preserving the previously established
successful-delivery/ignored-result coverage. Neither is a natural filesystem
failure claim.

The representative Plus/seed`0x12345678` candidate/baseline final4MiB pairs are
identical byte for byte, without a mask. Common EN SHA-256:
`658e78bac3947391fd2e4f56ae67c21a311100920b86799335cb031a9853b166`;
IT:`1bf9ffc66bb308e6db9f412d3e958c529ac44c469aad537b7545ba235c37d873`.
This comparison covers those two representative pairs, not every future input.
The same whole caller adds47 hooks; matching final RAM does not make earlier
Find/Convert/Open contexts identical to the modeled baseline.

Thirteen tests pass: nine portable and four private replay, zero skips,
13.245s/898269184-byte peak RSS. Independent reviews cover source/raw/ABI,
root/guard, both final pairs, counters and the oracle-only revision.

| Conclusion | Evidence and coverage |
| --- | --- |
| Documented provenance | pinned HGSS counterpart, source/header/layout and eight-image lineage in the wrapper guide |
| Recovered binary correspondence |324-byte recipe/ELF/decoded/physical readback; original MW build remains unavailable |
| Finite source semantics | contextual Find47/17/18, chronological parent state, Find2 normalization and Read error counter |
| Observed activation |24 native initialized caller runs, two matched baselines, representative EN/IT final pairs |
| Unattributed links | native Send/FindPathCommand, queue/card/archive completion, natural root initialization and boot |

The remaining Send models do not establish native filesystem completion, boot,
full battle/UI, SAVE/cold restart, hardware or timing. CPU17 checks admitted
instruction semantics; it is not ARM946 silicon or interrupt-delivery evidence.

The [isolated Send case](native-fs-send-source-rom-1.3.2.md) attributes the next boundary while explicitly qualifying its additional stack and declared archive input separately.
