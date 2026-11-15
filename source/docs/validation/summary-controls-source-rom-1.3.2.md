# Summary controls: exact bytes and conditional inertness

The exact r4 EN/IT images contain the current source's 484-byte Summary-controls
payload, reconstructed with its authenticated compiler. All three call sites
reach the expected wrappers. The initial resident record is zero, including
enabled, owner and window. Cold OFF update does no Summary read or state write;
cold teardown forwards native work without freeing a legend window.

OFF alone does not make every path inert: a matching owner and nonzero window
cause destroy to release that window even with enabled0. This is a verified
ownership condition, not a newly discovered game defect or an activation change.
See the [owner](../../features/summary-controls/README.md) and
[source-to-ROM method](../test-bench.md#linking-source-to-an-exact-rom).

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish a historical stage receipt from the final installed image, and
configuration from lifetime-dependent effects. Trace source/recipe→payload→BL
sites and ROM→wrapper→update/destroy/native continuation. Authenticate toolchain,
String/configuration and ABI dependencies; derive entries from the installed
branches, then compare compiled symbols. Test a counterexample to flag-only
inertness and require ABI/write-set checks. Independent Sol6.1 review read both
ROMs and exercised its own ownership/forwarding cases before reviewing the tool.

## Il materiale più grezzo da cui partire

Use your own exact EN/IT r4 images identified by full hashes and sizes in the
[game contract](../../distribution/game-1.3.2-r4.json). No historical receipt is
required by the new reader. Also supply your own `charmap.txt` from pret
pokeheartgold revision `0985e8718df4f25e64d6507d89c0c97c0d288981`, SHA
`58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded`.
This small source dependency is checked, not copied into the public tree.

Raw material is the ARM9 header/autoload map, resident state/code/String,
three BL encodings, wrappers and their native literals, and the
[ABI pin file](../../sgp131/data/controls-native-abi.json). That file records
V4 provenance for native spans; final r4 bytes are checked afresh. Native code,
viewer data and tables are not distributed as extracted fixtures. No save,
BIOS, game capture or private ROM derivative is needed.

## I metodi e gli strumenti da usare

Reuse [controls.py](../../sgp131/controls.py) for protected compilation,
Thumb BL decoding and raw mapping, crosschecked with ndspy. Derive entries
from the final BLs and wrapper prologues. Rebuild from
[runtime.c](../../features/summary-controls/runtime.c),
[abi.h](../../features/summary-controls/abi.h), explicit proposal geometry,
enabled0 and the String read from ROM, separately checked against the pinned
charmap and public legend text. Compare all484 bytes, not just the code prefix.

The pinned compiler is the root-protected Apple Clang21.0.0
(`clang-2100.4.1.1`) executable SHA
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
[compiler.py](../../sgp13/compiler.py) authenticates the executable, ownership,
ancestor permissions and ACLs and supplies a controlled environment before
launch. This is the actual CLT compiler, distinct from the system launcher.
Exact reconstruction currently requires that supported macOS toolchain; a
missing/mismatched compiler is an explicit limitation, not a passing reduced
check. It does not require a ROM build or installation.

From the repository root, using the Python dependencies in
[requirements.txt](../../requirements.txt):

```sh
.venv/bin/python3 source/features/summary-controls/tools/attribuisci.py \
  --language EN --rom /path/to/exact-r4-en.nds \
  --charmap /path/to/pret/charmap.txt --work /tmp/sgp-controls-rebuild \
  --json /tmp/sgp-controls-en.json
PYTHONPATH=source/features/summary-controls/test .venv/bin/python3 -m unittest \
  test_hooks.FinalImageRecord -v
```

Repeat the reader for IT with its exact image. Exit0 means full input identity,
40 raw/ndspy range comparisons, cold state/tail, source rebuild, native/viewer
pins and seven isolated cases passed. JSON stores sanitized hashes, addresses,
compiler flags/symbols and observations. The work directory retains one
484-byte **newly compiled project payload** and per-language manifests; scratch
ELF/configuration/stack-usage files are removed by the existing compiler helper.
No ROM, save, native bytes or extracted String is written there.

## Composition, addresses and calling convention

The existing production `prepare` builds32B state plus452B aligned code/String,
installs it in the assigned512B `summary-controls.runtime` slot and rewrites
three Thumb BLs. The final reader does not choose a new allocation or call an
installer. The historical field-guide parent and its conditional reserve policy
remain defined in the [reserve map](../../sgp131/data/reserve-map.json); this
attribution grants no new allocation or activation.

| Component | RAM / Thumb entry | Physical r4 EN/IT |
| --- | --- | --- |
| Slot512B, image484B | `023D4C10` | `001244D0` |
| Enabled word | `023D4C20` | `001244E0` |
| Update entry | `023D4CA5` | derived inside slot |
| Destroy entry | `023D4C69` | derived inside slot |
| Redraw wrapper | `023D4DCD` | derived inside slot |
| Teardown wrapper | `023D4DE1` | derived inside slot |
| Skills redraw BL | `0208CC5A` | `00090C5A` |
| Page-change teardown BL | `02089D78` | `0008DD78` |
| Exit teardown BL | `0208C564` | `00090564` |

The slot is initialized ARM9 autoload main RAM, directly stored in the exact
uncompressed base/r4 layout. It is not overlay code. Addresses above with bit0
set denote Thumb entries; physical lookup uses the even instruction address.
The reader derives mapping from header/module parameters and compares sections
with ndspy. Both project readers share layout validation; they are not wholly
independent parsers.

The record holds owner+0, generation+4, window+8, redraws+C and enabled+10
(hex offsets), then reserved words. All32 bytes and the28-byte slot tail are
zero initially. Update/destroy take the Summary pointer in r0. Update tests
null and enabled before accessing the Summary. Destroy tests matching ownership
and a nonzero window, without reading enabled. Its release calls ClearWindow
and WindowArray_Delete(window,1), then clears owner/window.

Wrappers preserve the Summary argument across the helper. Redraw forwards to
native `0208D178`, teardown to `0208C4E0`. The installed EV/IV viewer still owns
its inherited redraw hook at `0208D178`; it is not reconstructed or replaced by
this reader. The wrapper tests stub the destination transport, so they do not
exercise the viewer/native rendering body. r4–r11, SP/canary, Thumb and the
observed native return sentinel are checked.

For native provenance,14 bounded spans include the viewer, wrappers and Summary
functions; ten native APIs, four window tables, two BG descriptors, two hooks
and four literals are pinned. Only the three known BL encodings are restored
to their original native calls in **small comparison copies** before hashing
spans containing them. Actual CPU execution uses the unmodified final image.
This normalization checks preserved surrounding bytes; it does not mask the
separately derived/verified installed branches. No global caller completeness
or universal ISA classification is claimed.

## Results, counterexamples and coverage

**Documented provenance and binary match:** current source/ABI/compiler recipe
reconstructs484B identically in both languages, SHA
`59f08b81ac5a3d32a0925ae7cf98bd8e0af6ff886a41abb39f25b2f9f333cec2`.
The whole512B slot SHA is
`043065188eadbd011d528aa65e8f3de010038e2bd90c3eff874148aa15325fd7`.
Compiler manifest records flags, source/header hashes, geometry, symbol values
and static stack usage. The legend is the compact23-code String including EOS;
its text encoding matches the pinned charmap. Geometry is recovered through an
exact rebuild, not accepted as visually correct.

**Demonstrated isolated semantics:** seven cases per language execute installed
code with `Bench(payload=None)`. Update(null) reads no state; update(poison1)
reads enabled only and returns without dereferencing the pointer. Destroy with
zero owner or a different owner has no nonstack writes/native calls. Matching
owner/window with OFF calls clear/delete and zeroes both fields: this falsifies
flag-only inertness. Cold redraw/teardown each forward once with the same r0
and preserve native sentinel `76543210`.

Only four native boundaries are stubbed on these paths: ClearWindow,
WindowArray_Delete, native stats redraw and native teardown. No other bench
transport may execute. Code stays inside the installed payload or those declared
boundaries; guest writes must stay within a128B stack allowance or the32B state.
Observed deepest SP use was56B for cold redraw; matching destroy reached24B.
No active legend creation, allocator failure, real window cleanup or render is
qualified by these cases. Static compiler update48B and wrapper8B are distinct
from measured combined stack depth.

**Counterexamples and test coverage:** two unit methods reject nonzero flag,
owner, window/reserved bytes, short records, outside wrapper targets and malformed
prologue/callee BL. These are static rejection tests. The matching-owner OFF
case is a separately executed dynamic counterexample. Neither one is a game
modification. Historical active-geometry/V4 tests are not rerun or relabelled
as final r4 acceptance.

**Activation and lifetime not observed:** the final initial record is proven;
its entire natural runtime lifetime is not. A cold path cannot exclude every
possible later writer of owner/window. Full native Summary dispatch, all viewer
panels, active geometry, visual output, timing, hardware and save compatibility
remain outside this attribution. No setting or feature was enabled, no ROM or
personal save was written, and no CPU bottleneck was measured.

Final commands used ndspy4.2.0/Unicorn2.1.4 and took about0.29/0.30s EN/IT,
OS peak RSS about454/466MiB. Periodic samples underreport these short tasks;
peak figures come from `time -l`. There is no retained whole-ROM output.
Future changes to cleanup or activation would need owner/window lifetime,
native transport, allocator/geometry and natural Summary checks. No such game
change or optimization is proposed from these observations.
