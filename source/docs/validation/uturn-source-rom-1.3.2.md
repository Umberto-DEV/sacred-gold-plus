# U-turn attribution: exact bytes and two compatibility defects

The existing U-turn source reconstructs the current r4 EN/IT resident helper,
native call sites and pivot-script member. Executing those bytes finds two
defects: the unmarked modifier fallback corrupts its arguments, and the bit16
marker collides with negative native damage data. The verification CLI writes
its evidence and exits1 for these compatibility failures. No game repair,
ROM replacement or save modification is part of this case.

See the [owner](../../features/type-consumers/README.md),
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom),
[native RNG qualification](conversion2-source-rom-1.3.2.md) and
[signed arithmetic qualification](fairy-scalar-source-rom-1.3.2.md).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Link both artifacts: the script insertion that produces the word and the
compiled helper that consumes it. Follow source/ELF→placement/readback→native
parent/getters/data and reverse the installed bytes back to their recipes.
Check arguments at the original getter boundary, not just a mocked return value.
Check whether the shared word is already live native data before calling it
scratch. Distinguish a source reconstruction from successful gameplay behavior.

Independent Sol6.1 review read all eight input-role images, checked ABI,
resources and native field writers, and separately executed the fallback,
uncleared-word and negative-word cases. Historical private U-turn campaigns
remain attached to their older inputs and declared service models. They are
not repeated or relabelled current r4 coverage.

## Il materiale più grezzo da cui partire

Supply your own exact revision0 retail, Plus1.1, V1.3 V4 and r4 images.
Complete identities/preparation are linked in the
[flags input section](fairy-flags-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire),
[`baseline.py`](../../sgp131/baseline.py) and
[r4 contract](../../distribution/game-1.3.2-r4.json). Each run authenticates
size/SHA-256 of the four complete inputs for its selected language. No ROM,
save, BIOS, retail dump, extracted asset or private capture is supplied here.

Own code is [`uturn.S`](../../features/type-consumers/uturn.S), SHA-256
`e191b1c267282826beab3a20b18eb53375538b396dcdcbda2c6a12407e23422a`.
[`uturn_flinch.py`](../../sgp131/uturn_flinch.py) builds the helper, fixes two
external BLs, inserts it into its allocated tail, and changes two native getter
calls. [`uturn_script.py`](../../sgp131/uturn_script.py) inserts26 words in one
battle-script member and relocates two branches. The existing
[`mechanics_stages.py`](../../sgp131/mechanics_stages.py) registry composes the
script delta and native stage with the other owners; the overlay writer also
reconciles the derived UI y9 digest. No whole-ROM rebuild is repeated here.

Reference commit `cb614ad23449d5852b40321dc409c4143872b35c` supplies the native
source correspondence: `battle_controller_player.c::TryItemFlinch`,
`BattleControllerPlayer_AfterDamage`, the damage accumulation writers, and
`battle_util.c::{GetBattlerHeldItem,GetBattlerHeldItemEffect,GetHeldItemModifier}`.
`battle_command.c` explains the script commands and variable-pointer mapping.
The original native C/compiler/object/link map are not reconstructed. The own
assembly build is independently reconstructed below.

## I metodi e gli strumenti da usare

Recorded dependencies are Python3.14.7, ndspy4.2.0, Capstone5.0.9 and Unicorn2.1.4.
Fresh compilation uses protected Apple Clang21.0.0 (`clang-2100.4.1.1`), executable
SHA-256 `fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
Flags are `--target=armv5te-none-eabi -mcpu=arm946e-s -mthumb -ffreestanding
-fno-builtin -x assembler-with-cpp`, then `-c` source and `-o` object.
The [strict ELF loader](../../features/options/tools/carica_text.py) loads the
own ARM ELF32 text at its fixed address; no general linker is used.

With private input/artifact/report variables, use your dependency environment:

```sh
python3 source/features/type-consumers/tools/attribuisci_uturn.py --language EN \
  --rom "$R4_EN" --v4 "$V4_EN" --base "$BASE11_EN" --retail "$RETAIL_EN" \
  --work "$BUILD" --json "$CASE/uturn-EN.json"
python3 source/features/type-consumers/tools/attribuisci_uturn.py --language IT \
  --rom "$R4_IT" --v4 "$V4_IT" --base "$BASE11_IT" --retail "$RETAIL_IT" \
  --build "$BUILD" --json "$CASE/uturn-IT.json"
SGP_R4_ROM_DIR="$R4_DIR" SGP_R4_ROM_NOME='r4-%s.nds' PYTHONPATH=source \
  python3 -m unittest sgp131.test_type_consumers.CurrentCompositeUTurn -v
PYTHONPATH=source python3 -m unittest \
  sgp131.test_type_consumers.UTurnFlinchConsumer \
  sgp131.test_type_consumers.UTurnRetainedCompiler \
  sgp131.test_type_consumers.UTurnAttributionCLI -v
```

For the exact r4 inputs both CLI commands deliberately return1 after writing
their JSON: binary attribution passes, compatibility fails. An exception before
report generation indicates a different input/tool failure. Unit methods pass
by detecting the recorded defects; they do not certify corrected game behavior.
Missing private ROM unit inputs explicitly skip. Compiler methods require the
pinned compiler. `--build` verifies/reuses its retained artifact without compiling;
`--readback-only` explicitly omits compilation provenance. `--json` protects ROM
inputs and the three retained artifacts, including symlink/hardlink aliases.

Object retention is opt-in. Before/after checks prove the default receipt,
payload and object identities unchanged; the ASM remains unchanged. A different
retained artifact is preserved and rejected. Own ELF SHA-256 is
`fba7f63ad26ff8d7b55131b70a14ca0b190f3e62525c132558b73959515c8a93`.
The loader resolves the two Thumb entries; the builder replaces only the two
four-byte placeholders at helper+24 and+62 with calls to `02255830/02255844`.
Independent branch decoding verifies both targets and all other bytes.

### Installed bytes, ownership and resources

| Material | Exact current location / size | Verified scope |
| --- | --- | --- |
| Effect wrapper | `023D5A20`, entry Thumb | Frame4 B; low-byte result on marked path |
| Modifier wrapper | `023D5A40`, entry Thumb | Frame8 B; next-byte result and word clear |
| Own helper |68 B within128 B tail | SHA-256 below; remaining60 B zero |
| ARM9 physical mapping | Helper ROM`001252E0` | Raw autoload mapping agrees with ndspy sections, EN/IT |
| Shared allocation | `023D59E0`,192 B, ROM`001252A0` | First64 B foreign rematch stub, last128 B U-turn owner |
| Native parent | `0224E078–0224E130`,184 B |162 B code,2 B alignment,20 B literal pool |
| Source hooks | `0224E084`, `0224E090` | Only two getter BLs replaced |
| Outer caller links | `0224CB8A`, `0224CC64` | Static AfterDamage message-type0/1, state6 |
| Script | `a/0/0/1`,file130,member175 |696→800 B;104-byte insertion at`0x3C` |

Helper68 SHA-256 is
`8dfc3389b012ba046fd81df9c4a79119d1ffa4bf044b2462720a1868e0ea7f02`.
The complete current128-byte tail is reconstructed as helper+60 zeros, with
specific raw/ndspy ARM9 mapping checked at this address. The first64 bytes have
current SHA-256 `77844c84762bcdf84e64503a1e0996c871c8ca1027846b8059e5b5b86a8688ce`;
they belong to the [resident rematch stub](../rematch-variants-1.3.1.md), not
this helper. V4 has a zero192-byte allocation; its change to the final192 bytes
cannot be attributed to U-turn alone. That foreign stub is not rebuilt here.

Old parent184 SHA-256 is
`54d336b88e03483c19b485e578066bcdbdf53a64f8c632373d4eed6e2c89ac1c`;
current is
`80ca05b40b182b891deaba3163437aac063a6dd3c93916873407fb177c32fd29`.
Applying the two source edits to V4 reconstructs all184 current bytes. Retail
IT's actual old entry is`0224E018`: only its BLX field at function+`0x52` needs
comparison normalization, after verifying the same ARM division target/body.
Runtime bytes are not normalized. The outer caller window464 B is pinned and
the two BL targets checked; its outer state machine is not executed here.

The parent is in compressed overlay12/file12, base`022378C0`,226176 decoded
bytes, BSS0. Current BLZ streams are161600 B at EN`08314200–0833B940` or IT
`08800000–08827740`. Raw y9/FAT and project decompression agree with ndspy;
reports retain encoded/decoded identities and footer. Unlike the mapped ARM9
helper, a decoded overlay instruction has no simple linear physical ROM offset.

The script-member source recipe matches all800 current bytes, including its
shifted complement and two branch relocations. Before SHA-256 is
`b1c159eaba419c3ab00dc6f904037abbe8ecc67c1416f4ac4ab0baf59eb5e2f1`;
after is
`eaa254c435e16397b233c8f3e796f1655003358e4252bcc57352f3ca89b58c9a`.
Current whole archive SHA-256 is
`34e8770f83cccc06d250cbc1f4a0408a9160982d60a38d11aababdd312470cc9`.
Other owners also edit that archive, so the historical single-producer
`AFTER_ARCHIVE_SHA256` is not the expected current whole-archive digest.

Raw FNT/FAT/NARC reads are independently checked with ndspy. Item archive
`a/0/1/7`,file146 contains516 records of34 B. Native item-ID mapping sends
item221 to member199 and327 to305; both have effect56/modifier10. Item0 maps
to member0, effect0/modifier0. Treating item ID as member index would be wrong.
The prepared cache uses the native36-byte stride, appending two synthetic zero
padding bytes per raw record; native preload/heap construction is not proved.
Native GetItemVar, ID lookup, cache addressing and byte decoding for attributes
1/2 execute against that immutable cache. Move archive140 supplies the real
468-record battle-cache prefix: Tackle33 has the item-flinch eligibility bit;
Bite44 does not. No eligibility byte is invented for those controls.

### Producer, ABI and execution boundaries

The script sets marker`0x10000` in variable68. If the effective outgoing item
has effect56, it ORs56 and the modifier shifted8 into that word. Variable9 is
the temporary at ctx+`0x134`; variable68 maps to
`ctx+0x2EC+0x1C*attacker`. Actual native variable-table entries/case bodies bind
those addresses. A small source-word interpreter executes exactly the104-byte
insertion using real native item getters. It writes the resulting fixture
word, then models the item replacement. It does not execute native battle-script
dispatch, the switch UI or the full pivot subscript.

The late parent receives r0=BattleSystem, r1=context, frame24 B. Both wrappers
run before target/failure/damage gates. Thus the modifier clears a marked word
even on later failure. The effect wrapper's4-byte frame can enter native code
with SP mod8=4; the exercised private word-aligned paths are checked, rather
than assuming a universal8-byte alignment contract.

The bench executes installed parent/helper, native effective/raw item getters,
item lookup/decoder, RNG44 B and signed ARM divmod524 B. Only ability lookup
and script loading remain declared services. Klutz103 and Embargo state feed
the real effective-item branch. RNG uses its actual seed at BS+`0x2448`; each
transition, high16 result, modulo100 and final seed is checked. Seed fixtures
select boundary rolls; they are not observations of natural game randomness.

Actual PC/SP/Thumb returns, eight distinct saved-register cookies, nested native
return contracts, field/cache bounds, context/BS/code immutability, write ranges
and stack/caller/cache canaries are checked. Alignment, pools and jump tables
cannot execute. Observed parent-path stack maxima are32 B marked,64 B current
unmarked, and56 B old-hook baseline. Model internals are not included in those
native stack bounds.

### Defect1: unmarked modifier arguments

The modifier wrapper loads the word into r1 and puts`0x2EC` in r2. On its
unmarked branch it calls native `GetHeldItemModifier` without restoring
r1=attacker and r2=flag0. The raw getter accepts flags0/1/2; flag`0x2EC` skips
held-item selection and passes the scratchword as item ID to GetItemVar field2.
For word0 and held item221, the native data path returns modifier0 instead of10.
The native old-hook baseline flinches at roll9; the current helper does not.
All four attacker indices are checked with a different target index.

This is observed out-of-contract raw behavior, not a C-language guarantee for
an invalid switch flag. The old callback returned the requested modifier while
ignoring its arguments, hiding the fault. The shared FlinchBench now checks
effect/modifier arguments. Its regression distinguishes a valid original-parent
baseline from the currently rejected fallback; historical reports retain their
older, weaker coverage.

### Defect2: native damage mistaken for a marker

The same field is not generally spare storage. Four native writer windows,
ending in stores at`0224C74C`, `0224C794`, `0224CA2E`, `0224CA44`, accumulate
signed damage into `ctx+0x2EC+0x1C*attacker`. Their bytes match across all eight
input roles. The source records negative damage there. These writer links are
static; they are not a rendered end-to-end battle observation.

A controlled nonpivot case supplies native value−200 (`0xFFFFFF38`), empty
held item, physical damage−200, living target and actual Tackle data. Bit16 is
set, so the current helper treats that native value as effect56/modifier255
and clears it. At roll99 the current parent produces flinch and advances RNG
once; the old-hook baseline rejects flinch, consumes no RNG and retains the
native word. Neither current live getter is called, so this is independent of
the first argument bug. A bit16 test alone does not authenticate producer data.
Natural occurrence through the complete damage/pivot/controller chain remains
unverified.

### Coverage, counterexamples and next work

Per language,11 marked cases cover King's Rock/Razor Fang outgoing, empty
outgoing/held incoming, roll10, no damage, move failure, absent/KO target,
actual Bite ineligibility, Klutz and Embargo. They consume the word even on
later failure. Four current/old pairs expose the unmarked ABI defect; one
additional pair exposes the negative-word collision. A RAM-only NOP of the
word clear keeps the same first flinch result but fails the lifetime oracle.
A repeated parent entry without reinjecting the word checks one-time use.

Five current-image methods, six legacy consumer methods, two retention methods,
the18-case artifact-output method and33 structural/domain negatives detect the intended
properties and the known failures. Passing detection tests does not turn the
ordinary compatibility gates green. Canonical game ASM, ROMs and saves are
unchanged; optional object retention preserves the default build result.

Provenance and binary reconstruction are established for own68-byte helper,
128-byte tail,184-byte patched parent and800-byte script member. Native marked
consumption and the two incompatible ordinary behaviors are demonstrated for
their recorded inputs. Source-word producer semantics are checked; native
producer dispatch, full cache construction, ability lookup, natural pivot,
complete Shell Bell/item lifetime, SAVE/cold restart, device and timing remain
unqualified. No native C compilation or memory reclamation is claimed.

A future repair needs to preserve fallback arguments and give the marker a
namespace disjoint from native field values, preserving unmarked native data.
The likely source change is small, but requires fresh size/ABI/owner checks,
negative/native-word controls, getter/RNG/state comparisons, both languages
and full composition verification. A game change is a separate maintainer
decision. Native damage-writer→consumer reachability and native producer-command execution
remain separate unqualified links; the semantic interpreter is not native activation.

The [native HP continuation](hp-flinch-source-rom-1.3.2.md) subsequently executes
one damage writer and its HP script before an explicit AfterDamage state6.
It proves that bounded link; earlier states0..5 and natural battle activation
remain unqualified.

The [native snapshot producer](uturn-producer-source-rom-1.3.2.md) subsequently
executes the installed command table and handlers in a bounded copy of member175.
It qualifies that producer slice and CalcTemp preservation,with an explicit
synthetic stop and controlled replacement rather than a complete natural pivot.

In these native parent fixtures, `flinch` denotes the true TryItemFlinch result
and script14 request. Applying the target status bit or losing a turn requires
execution beyond that request.
