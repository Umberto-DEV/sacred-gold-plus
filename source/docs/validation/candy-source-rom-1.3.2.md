# Rare Candy: current source, native tail and exact ROM

Current source reconstructs the installed192-byte Rare Candy helper exactly in
r4 EN/IT. The whole256-byte owner,6-byte hook and bounded native caller match
readback. Thirteen cases from both hook and helper entry qualify26 isolated
invocations per language. Two false-success paths in the bench were reproduced
and corrected; no game code, item quantity, setting or save was changed.

See the [owner](../../features/caramelle/README.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).
This follows the Summary cases while investigating a separate Party-menu item
path. It does not repeat a natural Candy/save campaign.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Separate own-project helper code from native HGSS control flow and from later
Plus Bag implementations behind the native API. Reconstruct source→ELF→owner,
then follow ROM hook→shim→decision code→native transports. Verify both the
shim ABI and parent pop: the parent can hide a clobbered r4 if only the final
return is checked. Test actual loaded bytes and require a real return after
the instruction budget; matching result values alone are insufficient.
Independent Sol6.1 review checked raw ROMs, callers, ABI, gate cases, counterproofs
and the integrated reader separately.

## Il materiale più grezzo da cui partire

Use your own exact EN/IT r4 images from the
[game contract](../../distribution/game-1.3.2-r4.json), plus corresponding
HeartGold retail and Plus1.1 images. Full retail/base hashes, sizes and
preparation requirements are in the [camera input table](camera-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
The reader authenticates all three complete inputs. No save, BIOS, extracted
asset or personal game capture is required or redistributed.

The raw material is the ARM9 autoload mapping, hook, helper/code/pool/padding/
canary, native parent instructions, signed jump-table entry and literal values,
plus the project [C source](../../features/caramelle/sorgenti/caramelle.c),
[ABI header](../../features/caramelle/sorgenti/sgp_caramelle.h),
[compiler recipe](../../features/caramelle/tools/compila.py), strict ELF loader
and fresh build metadata. The historical
[bundle manifest](../../sgp12/build/caramelle/manifesto.json) identifies the
original192-byte payload and older Clang version; it is preserved as history.

## I metodi e gli strumenti da usare

Compile only this helper, read back the complete owner with the existing raw
reader and ndspy, decode the BL independently with Capstone, compare the native
600-byte window retail→base→r4 and check its20-byte continuation/literal range
separately. Execute installed bytes with the existing Banco; never substitute
a bundle for the helper. Six external quantity/Party/UI APIs are modeled.

From the repository root, using [requirements.txt](../../requirements.txt):

```sh
.venv/bin/python3 source/features/caramelle/tools/compila.py \
  --cc /path/to/clang --uscita /tmp/sgp-candy-build
.venv/bin/python3 source/features/caramelle/tools/attribuisci.py \
  --language EN --rom /path/to/exact-r4-en.nds \
  --base /path/to/plus-1.1-en.nds --retail /path/to/retail-en.nds \
  --build /tmp/sgp-candy-build --json /tmp/sgp-candy-en.json
```

Repeat the reader for IT with its own three images; the same compiled helper
applies. This reconstruction used the actual Apple CLT Clang21.0.0
(`clang-2100.4.1.1`), executable SHA
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
The historical manifest names `clang-2100.3.34.2`; its executable is not
reauthenticated here. Matching output proves the current reconstruction, not
that the two toolchains are identical. A different compiler must reproduce the
pinned bytes or the exact-match claim fails.

The compiler uses ARMv5TE/ARM946E-S Thumb, `-Oz`, freestanding/no-builtin,
no stack protector, unwind tables or jump tables, with warnings rejected. No
linker or external symbol is needed. A wrong-base manifest is rejected even if its position-independent object
happens to match the ROM bytes. Fresh metadata binds source, header,
loader, builder and invoked compiler hashes; the reader rejects stale/missing
bindings. Its strict loader extracts `.text` from `caramelle.o` and compares it
with `blob.bin` and installed code. JSON removes personal command paths while
retaining flags and identity. A build receipt and the source command establish
compilation provenance; a supplied object alone is not proof of its origin.

Exit0 means exact inputs, owner, BL/pop, compiled entries, source bindings,
parent/table/literals and26 isolated invocations passed. JSON contains hashes,
offsets and gate/call/write coverage, with no ROM output. Keep compiler ELF,
logs and local manifests in your own work directory; they are small project
code artifacts, not retail dumps.

The existing isolated suite can also use two private symlinks named
`r4-EN.nds` and `r4-IT.nds` pointing to the exact current images:

```sh
SGP_ROM_DIR=/path/to/private-alias-directory SGP_CAR_ROM_NOME='r4-%s.nds' \
  PYTHONPATH=source/features/caramelle/test .venv/bin/python3 -m unittest \
  test_caramelle.ProveCaramelle test_caramelle.ProveBancoContratto -v
```

These names are test aliases, not a second installed game or renamed save.
Identity admission belongs to the reader above, not those filenames.

## Composition, addresses and native caller

[The production block](../../sgp12/blocchi/caramelle.py) installs192B code,
48B zero padding and16B canary in the reserved256B owner. It writes a Thumb BL
to the helper followed by `pop {r3,r4,r5,pc}` at the native tail. No allocation,
ID, persistent field or existing Bag layout is added by this helper.

| Range | RAM | Physical r4 EN/IT |
| --- | --- | --- |
| Complete owner256B | `023DAC00` | `0012A4C0` |
| Canary16B | `023DACF0` | `0012A5B0` |
| Hook6B | `02081E96` | `00085E96` |
| Native window600B | `02081C50` | `00085C50` |
| Continuation/pool20B | `02081EA8` | `00085EA8` |

The slot is initialized ARM9 autoload main RAM; caller code is ARM9 static.
These r4 ranges are directly stored and uncompressed. Retail ARM9 is read
through ndspy decompression; those physical offsets must not be applied to a
compressed retail image. The raw project reader shares layout validation;
ndspy is the separate mapping check.

Native parent `PartyMenu_ItemUseFunc_LevelUpLearnMovesLoop` starts02081C50,
pushes16B (`r3,r4,r5,lr`) and keeps PartyMenu in r4. Its substate byte is at
PM+C67. Signed halfword table entry6 uses table base02081C68 but PC-add base
02081C6A, reaching02081E54. Treating both bases as identical is off by2B.
That handler calls GetMonEvolution at02081E88→02070E34, stores the result in
args+3C and reloads it as u16. At the hook r0 is species, r1 is args, r4 is PM.

BL02081E96 reaches023DAC00; the shim preserves r4/LR, moves PM to r2 and calls
`sgp_caramelle_decidi` at023DAC0D. It returns the next Party-menu state in r0;
the parent pop restores the caller frame. Direct-helper tests separately check
r4 remains PM, which the parent pop could otherwise conceal.

The decision code returns native exit32/action9 when evolution is pending.
With species0 it requires nonzero item, context5, nonzero Bag and remaining
quantity, nonzero Party and slot<count/capacity. Success sets action0, resets
move-search state, calls ClearFrameAndWindow2, prints native message33, resets
cursor palette and returns selection state4. Rejected valid-pointer gates
return32/action0. Null args/PM tests cover robustness outside the native site's
normal preconditions; they do not establish equivalence with a vanilla null
pointer path.

The six API addresses are Bag_GetItemQuantity02078550, Party_GetCount0207463C,
Party_GetCapacity02074640, ClearFrameAndWindow2/0200E9BC,
PartyMenu_PrintMessageOnWindow32/0207DAC4 and cursor-palette thunk0200DD08.
The current Bag entry can route into expanded Plus code. Stubbing that entry
models its result; it does not execute or certify the expanded-Bag component.
Source-only HGSS reference `cb614ad23449d5852b40321dc409c4143872b35c`,
`src/party_menu_items.c` and `include/party_menu.h`, supports function/enum
names, not an original native C-to-object reconstruction.

## Results, counterexamples and unresolved links

**Documented provenance / reconstructed binary:** source plus current recipe
reconstructs192B SHA
`9acfd1fdbcb72f0f9d28efc0042e0ca46fac4229ce569ad786eadfd2ad2f264f`.
The helper's two entries,48B padding and CA5A1600|0..3 canary all match exact
r4 EN/IT. Source/header/loader/builder/compiler identities are checked against
the fresh manifest. No historical release asset or bundle was overwritten.

**Native inheritance and language counterproof:** the600-byte original window
SHA is `f4bfaf599f81577817b6a6dc51e71ac81f39cdc7e29ceceb4f44ab4ac77eb466`
in retail EN/IT and both1.1 bases. Current SHA is
`8810122415e8b85bdb4ef161a7399d3d8ad8ecb5d5147bd20ff43686ff861c8a`, with
exactly the6 hook bytes changed. The separate20B range is not identical in
all inputs: retail IT has input-system-base word021D10AC at02081EB0; base/r4
IT and EN use021D110C. The other four words match. The reader first rejected
this mismatch, then gained an exact per-revision schema; it does not silently
ignore differing pools or generalize code equality into data equality.

**Demonstrated isolated semantics:**13 cases×2 entry modes per language,
covering success/boundary, evolution, item/context/quantity/count/capacity/slot
gates and null args/PM/Bag/Party. State/action, native sequence/arguments,
move-search reset and callee-saved registers are checked. Return PC, SP, Thumb,
code bounds and writes are mandatory. Guest writes stay in the declared stack
allowance and args action/search fields; no save or ROM is written. The maximum
observed depth including the synthetic parent frame was56B; native transports
are stubbed, so this is not total game stack usage.

**False-success counterproofs:** the former “hook is BL” test checked only
manifest metadata and passed after loaded hook bytes were replaced by NOPs.
The corrected test reads/disassembles the actual loaded hook and compares the
complete owner. Separately, replacing only the final pop by B-self preserved
expected action/result/calls, and the former bench returned after its instruction
budget with a false success. The corrected bench requires the real return PC,
SP and Thumb. Both old successes and new rejections were recorded; public
regression tests reproduce the RAM-only counterexamples with users' own inputs.

**Coverage and pending dependency:**15 existing isolated methods and2 new
counterexample methods pass on current EN/IT aliases, with no skips. This does
not turn all17 historical tests into passes: the separate2 expanded-Bag
integration methods reject the legacy capacity blob's identity on current r4
(10 subcases). That admission failure is retained, not bypassed or called a
Candy gameplay bug. A follow-up must attribute the current capacity successor
and its quantity path before claiming real native/extra-slot consumption or
level100 behavior from those tests.

**Activation not observed:** no new natural Party visit, actual item consumption,
move-learning/evolution scene, full native parent execution, SAVE/cold restart,
UI timing or physical run. Six native transports are modeled, and the source
compiler's exact bytes do not certify those unexercised conditions. A historical
C comment also overstates the untouched old tail by2B; the owner README records
the precise erratum without changing the preserved C snapshot.

Final reader commands took about0.46/0.48s with OS peak RSS about712/732MiB
EN/IT; the isolated legacy/regression suite peaked about345MiB. Periodic RSS
samples are not valid peak estimates for these short commands. No whole-ROM
output was retained. No game optimization is proposed; a future change to the
re-entry gates would need native Bag, move-learning/evolution, level100 and
natural save-copy regression coverage.
