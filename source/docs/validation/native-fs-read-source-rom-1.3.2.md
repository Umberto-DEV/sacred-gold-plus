# Native Read veneer and synchronous core

This follows the [Seek case](native-fs-seek-source-rom-1.3.2.md) into the installed
`FS_ReadFile` veneer and `FSi_ReadFileCore`. It reconstructs seven baseline ABI
inputs from the authenticated parent receipts, then runs each in a separate
bounded native CPU. It does **not** continue the complete parent caller CPU.
The native core writes arguments and SYNC state that the former model excluded;
those differences must be resolved before integration. No game changes.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish compiler veneer instructions from its literal pool and attribute
both directions: source/recipe→ELF→ROM and ROM→caller→core→source. Attribute the
input memory with the same care as code. A post-copy frame is not an entry
snapshot; derived registers must be labeled as such. Keep native instructions,
modeled SDK boundaries and actual completed filesystem state separate. Seek
counterexamples where copied bytes and file position remain identical but the
native return changes. Review ABI, stack reuse, model exclusions and readback
independently before claiming integration or natural activation.

## Il materiale più grezzo da cui partire

Use developer-owned inputs and project objects from the
[parent input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
Current EN:152786844 bytes, SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes, SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Both headers are IPKE revision0; IT is text-localized. ARM9 file offset`0x4000`,
load`0x02000000`. These bodies reside in the main ARM9 section, with no overlay,
compression or autoload lifetime. Full boot/ARM7 is outside this experiment.
ROMs, extracted retail data, RAM, packets, saves and BIOS stay private.

| Component | RAM range | Current ROM offset | SHA-256 |
| --- | --- | --- | --- |
| Core,124 bytes/31 ARM instructions | `[0x020D8104,0x020D8180)` | `0x000DC104` | `10e97eb8d4fed727a55cf2ac3f9851ff0abd332b427a67189ad13b5b9d4008ae` |
| Veneer,16 bytes | `[0x020D83CC,0x020D83DC)` | `0x000DC3CC` | `501741a75e11deaadaf8bd6856124771f09fa272502e3fa6752c1340d19c0aa3` |

Only the first12 veneer bytes are instructions: LDR IP, MOV R3,#0, BX IP.
The last4 bytes at`0x020D83D8` are the address`0x020D8104`, never an ARM start.
The veneer tail-calls the core without changing LR or SP. Core BL sites
`0x020D8154` and`0x020D8164` target Send`0x020D7788` and Wait`0x020D82FC`,
with return addresses`0x020D8158` and`0x020D8168`. Signed24 displacement uses PC+8.

The counterpart is `lib/NitroSDK/src/fs/FS_file.c::FSi_ReadFileCore`/`FS_ReadFile`
at [ctrl-cheeb-del/pokeheartgold](https://github.com/ctrl-cheeb-del/pokeheartgold/tree/cb614ad23449d5852b40321dc409c4143872b35c),
pin`cb614ad23449d5852b40321dc409c4143872b35c`, file SHA-256
`7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f`.
The original headers verify FSFile72, bottom40/pos44, read argument fields
48(dst)/52(original length)/56(clamped length), FSReadFileInfo12,
READFILE command0 and SYNC bit4. The recovered assembly matches bytes;
the original MW compiler/object provenance is unavailable. A counterpart and
recovered recipe do not establish the historical original compilation.

## I metodi e gli strumenti da usare

The finite question is whether native veneer/core consume seven reconstructed
inputs, write the declared argument/SYNC fields, call Send0 then Wait, preserve
callee-saved state and return the position advance when the abstract Wait returns
TRUE. The counter returns FALSE from Wait after the same raw delivery: R0 must
be`0xFFFFFFFF`, although payload, position and complete RAM remain identical.
Another control returns FALSE from Send while retaining the raw delivery and
TRUE Wait; the core ignores Send's return. This is an intentional ABI control,
not an observation of real SDK failure policy.

### Input derivation and resources

Generate the complete Seek report using its linked guide. The new preparer
checks the full ROM, parent47 source identities, seven recipes, five namespace
bindings, complete source/ROM proof and all four parent positives without running
a parent CPU. It selects Plus1/seed`0x12345678`, without backend clobbering.
Read entry16 is **derived**, not captured: the old backend preserved all registers
except R0 and the return mode, so restore R0=FILE and clear T from the recorded
post-model projection. The inversion is checked against recorded args, saved
registers, SP, LR and IP.

The true pre-copy240-byte frames come from Seek returns for reads0/1/3/4;
reads2/5 use the preceding read's post-projection frame. Read6 uses the last Seek
return plus the native size16 store at`0x020073EE`. Its destination lies beyond
the frame and comes from the parent's destination preimage. Applying the raw
payload must reproduce each recorded post-copy/pre-projection frame. The tool
rejects a mismatch. Unspecified RAM is synthetic canary data; this is not an
original full4MiB CPU snapshot. Each run starts from a fresh copy, so repeated
reads are independent replays rather than cumulative native filesystem state.

| Read | NARC-relative position | Destination | Bytes | Original Thumb caller LR |
| --- | --- | --- | --- | --- |
| 0 | 12 | TOP−116 | 2 | `0x02007367` |
| 1 | 20 | TOP−116 | 4 | `0x0200737D` |
| 2 | 24 | TOP−128 | 2 | `0x02007387` |
| 3 | 3800 | TOP−116 | 4 | `0x020073AB` |
| 4 | 2508 | TOP−120 | 4 | `0x020073C5` |
| 5 | 2512 | TOP−124 | 4 | `0x020073CF` |
| 6 | 8780 | TOP | 16 | `0x02007403` |

TOP=`0x023BEEC0`, FILE=`0x023BEE50`, SP=TOP−136. Core PUSH24 stays inside
the existing240-byte frame; it does not expand the parent's global560/608-byte
stack coverage. The raw resource is NARC11/FNT`a/0/1/1`, FAT file140, current
physical top`0x01093800`/bottom`0x0109645C`,11356 bytes, SHA-256
`beed8ddf861e575b9c38dfa65a6c0c51fb237305ddd73c393f5e2009fbc75260`.
The last read delivers member310,16 bytes, SHA-256
`85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8`;
byte6 is PP15. Parent independent FAT/FNT/NARC readback is retained.

### Explicit SDK boundaries and ABI

Send0 copies exactly the bounded raw bytes to the native dst field and advances
FILE.pos. Wait supplies a declared BOOL. These two boundaries preserve saved
registers/SP; a control clobbers R1/R2/R3/IP/NZCV. They do not reconstruct archive,
thread/IRQ/queue/command/error or completed SDK state. In the actual SDK,
ReleaseCommand clears CANCEL|BUSY|SYNC|ASYNC|OPERATING mask`0x4F` and writes
error SUCCESS0. **Those known completion effects are excluded here.** The native
SYNC store remains observable: stat16 becomes20 decimal(`0x10`→`0x14`),
not bit`0x20`. Wait success is an abstract boundary, not derived from the old
synthetic error word.

Core makes ten native word stores: six PUSH words, three read arguments and one
SYNC store. The pure source/dataflow oracle checks every admitted observation,
all sixteen registers, owned reads, stores, output and the exact full4MiB RAM
hash. CPU17 is qualified to deliver all34 native hooks, including false conditional
starts; replay requires their complete order and37 total steps, also with
observation OFF. A hook alone does not prove an effect.
The literal cannot execute. The guest is bounded to100 hooks and one second.

The normal return preserves R4–R11/SP, restores R3=0, leaves IP=`0x020D8104`,
LR=`0x020D8168` and returns Thumb with CPSR`0x2000003F`. Wait FALSE returns
CPSR`0x6000003F`. These volatile/ARG/stat differences from the older opaque Read
model are recorded, not normalized away. They preclude claiming an unchanged
complete parent execution from these isolated results.

### Reproduction

Dependencies are Python3, ndspy, Capstone and Unicorn, plus an ARMv5TE-capable
Clang for the recovered recipe. Use the parent guide for authenticated rematch
objects, strategy teams.o and the Seek report. The pinned SDK reference is
optional for assembly but required to reproduce header/layout provenance.
Create fresh output directories; no command below installs or patches a ROM.

```sh
python3 source/features/trainer-strategy/tools/compila_fs_read.py \
  --cc "$SGP_CLANG" --reference "$SGP_REFERENCE" --uscita "$SGP_OUT/recipe"

python3 source/features/trainer-strategy/tools/attribuisci_fs_read.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_SEEK_REPORT" \
  --objects "$SGP_REMATCH_OBJECTS" --strategy-object "$SGP_TEAMS_OBJECT" \
  --prepare-only --json "$SGP_OUT/prepared.json"

python3 source/features/trainer-strategy/tools/attribuisci_fs_read.py \
  --rom "$SGP_ROM" --language EN --parent-report "$SGP_SEEK_REPORT" \
  --objects "$SGP_REMATCH_OBJECTS" --strategy-object "$SGP_TEAMS_OBJECT" \
  --raw-dir "$SGP_OUT/raw" --json "$SGP_OUT/fs-read-EN.json.gz"

python3 source/features/trainer-strategy/tools/rileggi_fs_read.py \
  --retail "$SGP_RETAIL" --base "$SGP_BASE11" --v4 "$SGP_V4" \
  --rom "$SGP_ROM" --language EN --recipe-dir "$SGP_OUT/recipe" \
  --json "$SGP_OUT/lineage-EN.json"

python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_read_bench.py' -v

SGP_FS_READ_ROM_DIR="$SGP_ROM_LINKS" \
SGP_FS_READ_REPORT_DIR="$SGP_REPORTS" \
SGP_FS_READ_PARENT_DIR="$SGP_SEEK_REPORTS" \
SGP_REMATCH_OBJECT_DIR="$SGP_REMATCH_CAMPAIGN" \
SGP_STRATEGY_OBJECT_DIR="$SGP_STRATEGY_CAMPAIGN" \
python3 -m unittest discover -s source/features/trainer-strategy/test \
  -p 'test_fs_read*.py' -v
```

Repeat with IT and its own exact input, object/report paths and output names.
Replay ENV directories contain`r4-EN.nds`/`r4-IT.nds`,
`fs-read-EN.json.gz`/IT,`fs-seek-EN.json.gz`/IT,
`public-build-EN`/IT and`build-EN/teams.o`/IT respectively, matching the parent
convention. Without private inputs the replay tests explicitly skip; a release
verification must report zero skips. Raw per-run gzip observations are saved
before semantic evaluation. Keep them private alongside argv, exit codes,
source snapshots, hashes and OS peak RSS. Run one producer with explicit time,
RSS, log and storage caps; preserve10GiB after peak. No full ROM build is needed.

### Results and limits

Recipe and header assertions are qualified. Independent lineage covers both
bodies in retail→base1.1→V4→exact current EN/IT, with direct raw/decoded agreement
for V4/current and section-aware legacy readback. It parses ELF section bounds
and rejects text relocations independently of the builder loader. Current
physical offsets are not generalized to legacy compressed/autoload sections.
Finite CPU results and review metrics are recorded here after qualification.
No natural activation, full parent integration, completed SDK, original MW,
EOF/negative-length/overflow/async, card timing, SAVE/cold/hardware or speedup is
claimed. Those are distinct follow-on questions.

A concrete follow-on is completion-state modeling and integration of this core
in the parent CPU: cost is source/ABI/temporal-oracle work; risk is false
attribution through ARG/stat/volatile normalization; verification requires full
parent positive/OFF/counter comparison without enlarging RAM exclusions.
This is a tooling opportunity, not an authorized gameplay optimization.

The qualified final matrix passed98 isolated runs: seven inputs × seven policies
(normal, OFF, Wait FALSE, Send FALSE, volatile clobber, alternate fill, truthy
Wait2) × two languages. EN1.941s/558792704 bytes OS peak RSS;
IT1.960s/572243968 bytes. Eleven tests (six portable, five private replay)
passed with zero skips,3.170s/726974464 bytes OS peak. These costs describe
host verification, not game responsiveness. The CPU collector observes34 native
starts plus two modeled SDK boundaries and the original caller return,37 steps.
Each normal trace includes three false conditional data-processing hooks with
no effect; the conditional branch is not taken. Wait
FALSE changes the conditional effects without changing the admitted starts.

The runner selects CPSR mode before initializing banked SP/LR. It preserves
fault/halt state in the raw result before applying semantic checks; a fault,
timeout, missing return or altered literal/field/stack/data/whole-RAM identity
fails verification. Parent coverage requires the four distinct ordered
Plus/seed cells; repeated copies of a valid cell cannot satisfy it. Trace
falsifiers also remove a false hook and forge an OFF step count: both fail.

| Conclusion class | Proven coverage | Remaining gap |
| --- | --- | --- |
| Documented provenance | Pinned C counterpart, original header layouts, project recipe and authenticated inputs | Original MW compiler/object history |
| Reconstructed binary match | Core124 plus veneer16, independent ELF/raw/decoded readback, eight images | Other revisions or body extents |
| Demonstrated semantic equivalence | Seven finite synchronous inputs under the declared Send/Wait boundaries, exact ABI and memory delta | EOF/negative/overflow/async and real SDK completion |
| Observed activation | Isolated native CPUs with derived parent ABI inputs | Natural activation and complete parent CPU integration |
| Unattributed links | Explicit Send/Wait/archive/thread/IRQ/queue/error/command/completion boundaries | Native completed filesystem and hardware behavior |

Independent source/raw/recipe, input/ABI, observer, counter and public CLI reviews
are retained with the private receipts. The qualified verifier requires the actual34/37 hook policy; conditional
hook delivery is never counted as proof of an executed effect. No prior completed gameplay campaign is rerun by these tools.
