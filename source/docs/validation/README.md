# Candidate validation

The [current 1.3.2 report](localization-1.3.2.md) owns the five candidate
identities, bounded New Game/Continue/native SAVE/cold-restart results and
their limits. The [release contract](../../distribution/release-1.3.2.json)
owns the five target hashes and 150 explicit patch routes. File reconstruction,
native save acceptance, translated UI checks and publication are separate results.

The [1.3.2 package revision r3 report](package-1.3.2-r3.md) covers the corrected
download layout, documents and patch reconstruction. Its [schema-3 contract](../../distribution/release-1.3.2-r3.json)
retains those same game targets while separating five primary clean-ROM patches
from 150 optional updaters. It does not claim a new game or save test campaign.

Add one report per candidate or investigation. Put the version or subject in
the filename, and include the exact ROM SHA-256, language, predecessor, save
copy hash, emulator/core build, input sequence, measured outcome and limits.
Keep screenshots and large private diagnostics outside Git; cite their private
receipt or a small public summary. Distinguish a component test, headless game
run, Android/device run and release acceptance.

Record the actual controls and visible result, not just a completed input
script. Changed target bytes need a new identity; any inherited result must
name its predecessor, the exact verified delta and the successor checks.
Earlier captures keep their original hashes.

For 1.3.2, the acceptance basis is bounded host/native-save testing. It does
not claim a physical handheld run, JIT/backend coverage, native-menu latency
equivalence or a full playthrough. Representative saves establish their
documented cases; 150 byte-exact patch reconstructions do not constitute 150
independent save fixtures or universal compatibility with modified ROMs.

Historical reports at `source/docs/` retain the results and limitations of the
candidates they tested. Do not relabel an older result as evidence for a new
ROM. See the [test bench](../test-bench.md) and [source guide](../../README.md).

The [New Game reset investigation](new-game-reset-1.3.2.md) is a historical
before/after diagnostic record. Its probe hashes and then-open release status
are retained; current acceptance belongs to the separate 1.3.2 report above.
