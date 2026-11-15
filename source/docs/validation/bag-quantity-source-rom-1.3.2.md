# Expanded Bag successor and Rare Candy quantity

The current expanded-Bag core is exactly reproducible as a 3,584-byte
compilation followed by two source recipes. Independent readback verifies the
complete 11,264-byte initial owner in r4 EN/IT. Installed native quantity and
consume functions reach that core through its pocket dispatcher. Isolated
execution verifies native and extra Medicine slots before Rare Candy re-entry.
No game, save layout, setting or installed ROM changed.

See the [owner](../../features/capacita-borsa/README.md), the
[Rare Candy caller](candy-source-rom-1.3.2.md) and the
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Keep the strict bench's rejection of an old build: a matching historical
manifest cannot certify different current code. Compile the project baseline,
identify every later owner, and reconstruct expected bytes before comparing the
ROM. Then follow the reverse direction from the native API through the installed
dispatcher to its source. Separate project code, native HGSS windows, item data,
initial state and padding. Challenge the actual item pocket, fourth/fifth
arguments, NULL allocation, return, callee registers and write bounds.

The initial constructor-only hypothesis was falsified: a Training save hook
also changes the core. Independent Sol 6.1 review inspected raw images and source,
repeated the resource and quantity cases, and checked the dispatcher ABI. This
case closes the old-build admission gap; it does not replace earlier save tests.

## Il materiale più grezzo da cui partire

Use your own exact retail HeartGold, Plus 1.1 and r4 image for each language.
Full retail/base identities and preparation requirements are in the
[camera input table](camera-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire);
r4 identities are in the [game contract](../../distribution/game-1.3.2-r4.json).
The reader checks all three complete hashes and sizes before attribution.
No save, BIOS, extracted item record, asset or personal capture is needed or
redistributed. JSON results contain hashes, addresses and observations, not
retail instruction or asset dumps.

Project material:

- [Core, runtime and journal sources](../../features/capacita-borsa/sorgenti/),
  [compiler](../../features/capacita-borsa/tools/compila.py), its strict ELF loader
  and [historical manifest](../../sgp12/build/capacita_borsa/manifesto.json).
- [Bag installer](../../sgp12/blocchi/capacita_borsa.py),
  [allocation recipe](../../sgp131/bag_alloc.py),
  [Training hook recipe](../../sgp13/training.py) and its preservation in
  [bag-foreign](../../sgp131/bag_foreign.py).
- [Strict capacity bench](../../features/capacita-borsa/test/banco.py) and
  [Candy adapter](../../features/caramelle/test/test_caramelle.py).

The separately obtained pret/pokeheartgold reference at commit
`cb614ad23449d5852b40321dc409c4143872b35c` supplies `src/bag.c`, `src/item.c`,
`include/item.h`, `include/constants/items.h` and `src/party_menu_items.c` as
source hypotheses and data-format references. It is not required by the CLI.
No original native MW compiler/linker reconstruction is claimed. Equality of
bounded native windows across input revisions proves byte continuity, not
independent compilation of that reference source.

## I metodi e gli strumenti da usare

Run from repository root with dependencies from the
[build guide](../../README.md). This case used Python 3.14.7, ndspy 4.2.0,
Capstone 5.0.9, Unicorn 2.1.4 and Apple Clang 21.0.0
`clang-2100.4.1.1`. The actual CLT compiler executable SHA-256 was
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`;
`/usr/bin/clang` is a separate launcher. The old bundle records Clang
`clang-2100.3.34.2`; its original executable is not authenticated here. Current
Clang reproduces its complete code and symbols. Compiler flags are retained in
the generated manifest; origin checks bind all project C/headers and the builder.

For example, set these variables to private input and output locations. Record
`clang --version` and the selected executable's SHA-256 with your build receipt.
Use an explicit compiler directory in `PATH` when more than one Clang is present.
Other toolchains must pass the same exact-byte and symbol gates.

```sh
python3 source/features/capacita-borsa/tools/compila.py --uscita "$CASE/base-build"
python3 source/features/capacita-borsa/tools/attribuisci.py \
  --language EN --rom "$R4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --base-build "$CASE/base-build" --work "$CASE" --json "$CASE/report-EN.json"
python3 source/features/capacita-borsa/tools/attribuisci.py \
  --language IT --rom "$R4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --base-build "$CASE/base-build" --work "$CASE" --json "$CASE/report-IT.json"
python3 -m unittest discover -s source/features/capacita-borsa/test -p test_build.py -v
```

Use the Python environment containing those dependencies (`.venv/bin/python3`
in the recorded run). Do not use the resulting bridge as an installer build.
Its deliberately different schema and origin are rejected by the production
loader. It contains expected project bytes derived from the compilation and two
recipes, rather than an arbitrary extraction of the ROM. The strict execution
bench still requires its entire blob to equal the bytes already in the ROM.

### Compilation, composition and independent readback

| Material | RAM / extent | SHA-256 or relation |
| --- | --- | --- |
| Baseline compilation | `023DBF00`, 3584 B | `e41d95a3a7f57e504697c83f754c6fbb57745291d149dcb9d94b4dcde5f3c1fb` |
| Allocation successor | `023DC8B0`, 28 B | 23 changed bytes; exact preimage and postimage in `bag_alloc.py` |
| Training save hook | `023DCC9C`, 8 B | 7 changed bytes; `push/BL/pop`, BL target `023D14DC` |
| Current composite | `023DBF00`, 3584 B | `88a6736f0cecbc681864ac765c6309ad8480c406f3150fb54b6d1743f3468448` |
| Complete initial owner | `023DBF00`, 11264 B | `76aee681528b78832b570e7a74bbfe46f4f522782cb17d634f6eb26a7a07f01e` |

The physical owner starts at `0012B7C0` in both r4 images. All 7,680 bytes after
the code are initially zero, including padding, the 4,808-byte state at
`023DD700` and final padding. This initial-ROM result does not mean live state
remains zero. Raw ARM9/autoload address mapping and ndspy sections agree.
The current ARM9/autoload sections are uncompressed; retail ARM9 comparison
uses ndspy's decompression. JSON records each checked RAM and physical range.

The 28-byte allocation recipe retains `sgp_cap_new` at `023DC8B1`, allocates
2,380 bytes through `0201AA8C`, skips the clear when NULL, and otherwise calls
the real clear routine at `023DBFEC`. The Training hook is attributed as a
separate composition owner; this case neither rebuilds nor executes its whole
SAVE target.

### Native callers, ABI, state and resource

Native `Bag_New` (`02078188`), `Save_Bag_Get` (`0207879C`) and `Bag_GetSlot`
(`02078724`) have 8-byte literal/tail dispatchers to the manifest's Thumb
entries. `Bag_GetPocket` at `02078240` uses a **16-byte r3-preserving dispatcher**:
r0=Bag, r1=item ID, r2=slot-output pointer, r3=count-output pointer, stacked
fifth argument=heap. The core entry `023DC995` keeps both output pointers and
reads heap from the correct stack slot. Treating live r3 as disposable would
corrupt this ABI even though r3 is caller-saved.

The native quantity window `02078550 + 244 B` has SHA-256
`aea7fd2ef700c2f9de79d86ba798a6e630b4eb3a1159cc59a9953ff06789838e`;
take/compaction `02078434 + 144 B` has SHA-256
`5981cc0c9f3602f243f69062b35afa3dddff822f5b9c9b852d1d536cb89d250f`.
Both windows are identical across all six retail/base/r4 inputs. Quantity calls
the installed pocket dispatcher once; take calls it for lookup and compaction.
The Candy tail calls the real quantity API, then real Party count/capacity leaf
functions when quantity remains. Project routing reconciles the shadow Bag with
its native mirror; native layout remains 1,948 bytes, expanded Bag 2,380 bytes.

The real item lookup literal at `02077D34` names table `02100194`; row 50 at
`02100324` selects NARC member 50. The archive `a/0/1/7` is file ID 146 with
516 members; member 50 is 34 bytes with SHA-256
`60fdc4574595c465a91aa999bb35ed33290f66fc74242de8ad35b5f7e429e0d7`.
Raw FAT/BTAF/GMIF readback agrees with ndspy. The installed full `GetItemAttr`
entry `02077D88`, lookup and preloaded decoder execute for attributes 5 and
14–58: 46 calls per language. Only NARC allocation/read `02007524` and explicit
free `0201AB80` are modeled. They must receive NARC17/member50/heap12 and
heap12/the returned buffer respectively; record lifetime, bounds, canary,
stack-only writes and return ABI are checked.

Pocket is **1, Medicine**: 40 native slots, 42 expanded. Party-use, revive and
level-up flags are all set in this exact record. The old Candy integration
fixture deliberately used item50→pocket0/native165. Its two methods now pass
with the attested current bridge, but remain a synthetic Items-pocket fixture.
They do not establish the actual Candy pocket.

### Execution coverage and counterproofs

Per language, two actual native-constructor cases exercise NULL/nonNULL:
allocation size2380, r4–r11, SP, Thumb, real return, no NULL heap writes,
exact2380-byte clear and 16-byte canary. The nonNULL clear takes7157 instructions
under the20000-instruction ceiling; stopping after5000 is a failed proof.

Eight integration cases per language cover Medicine indices0,40,41 with
quantity2→1 and1→0, plus level99/100 predicates. They execute native get/pocket/
slot/quantity/take, the installed core and Candy tail without replacing ROM code.
Re-entry returns state4 when one remains and state32 when empty, with action0;
move-search reset occurs only on re-entry. The tail consumes no additional item.
Level99 allows use and100 rejects it; quantity stays1. These calls require real
returns, r4–r11/SP/Thumb preservation, bounded writes and no assert, native SAVE
or flash write. Maximum observed stack depth is200 bytes; the broader8KiB
stack and64KiB modeled heap write allowances are fixture limits, not universal
resource bounds.

The quantity route's item-pocket reader returns the separately measured native
value. Mon data/level, item-load/preloaded attributes, save-array/flash, heap and
UI transports remain declared models in the integration bench. The full item
file lookup/free is a separate isolated proof; this is not one continuous native
file-I/O/gameplay execution or an encrypted personal-Pokémon test.

Eight build/oracle tests pass: exact compilation/symbols, source/blob/manifest
integrity, both required recipes, in-range symbol/flag drift rejection, bridge
rejection by the installer, and rejection
of result-matching loops, r4 clobbers and foreign writes. The existing17 Candy
methods also pass after the adapter's optional explicit-build argument; default
behavior is retained. Independent review repeated46 getter and8 flow cases per
language from the raw inputs and checked the ABI separately.

Recorded reader runs exited0 in2.35/2.36 seconds, with OS peak RSS
756,613,120/777,338,880 bytes EN/IT, under the1GiB budget. Logs were bounded to2MiB;
no full ROM build, save write or new natural capture was needed. Subsecond RSS
sampling is not used as the peak measurement.

### Conclusions and remaining work

- **Documented provenance:** project C/headers/compiler recipe, two later source
  owners and bounded native-window continuity are linked to exact input receipts.
- **Reconstructed binary correspondence:** all3584 composite code bytes and the
  complete11264-byte initial owner, four dispatchers, Training BL and resource row.
- **Demonstrated semantics:** bounded constructor and quantity/consume/re-entry
  outcomes and ABI, on the installed instructions with declared models.
- **Observed activation:** isolated invocation only; no new natural gameplay or
  physical-device observation.
- **Unattributed links:** original native compiler/linker provenance, full Training
  SAVE execution here, natural item file I/O, heap pressure, personal save and
  cold-restart coverage remain outside this case.

The useful correction was to the verification setup: retain strict identity,
reconstruct both composition owners, and distinguish synthetic pocket0 from the
real Medicine dependency. No evidence here calls for a game optimization. A
broader integration campaign would cost a new natural runtime/save scenario and
must preserve the exact successor, raw-save copies and existing acceptance limits.
