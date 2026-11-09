# Candidate validation

Current accepted game identities are in the
[game contract](../../distribution/game-1.3.2-r4.json). The
[Guide opening correction](guide-opening-1.3.2.md) records those successor
identities, bounded font/game/save results and the separate Android UI check.
The [original 1.3.2 report](localization-1.3.2.md) retains its predecessor
identities and original test limits; its results must not be relabelled as
successor tests.

The [corrected package report](package-1.3.2-corrected.md) and
[frozen r4 package contract](../../distribution/release-1.3.2-r4.json) describe
the single-ZIP baseline and all recognized-source routes. The current
[illustrated documentation report](illustrated-guides-1.3.2.md) and
[documentation contract](../../distribution/documentation-1.3.2.json) identify
the later document-only delivery; the game patches remain unchanged. Earlier
[r3 packaging evidence](package-1.3.2-r3.md) and its
[contract](../../distribution/release-1.3.2-r3.json) preserve their historical
two-download layout.

Use the [native-hardware procedure](../native-hardware-validation.md) to test
an exact candidate on a verified Nintendo model/loader configuration and raw-save
copies. This is a method, not a new support or performance claim. Runner JSON
records suite progress and verdicts; candidate identities, hardware settings,
measurements and save evidence belong in the relevant validation report.

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

Current acceptance is bounded by the cases and evidence classes in the reports
above. The Android UI observation does not establish Nintendo-hardware CPU
timing, a physical native SAVE/cold-restart cycle, other languages on device,
JIT/backend coverage, native-menu latency equivalence or a full playthrough.
Representative saves establish their documented cases; byte-exact patch routes
do not constitute independent save fixtures or universal compatibility with
modified ROMs.

Historical reports at `source/docs/` retain the results and limitations of the
candidates they tested. Do not relabel an older result as evidence for a new
ROM. See the [test bench](../test-bench.md) and [source guide](../../README.md).

The [New Game reset investigation](new-game-reset-1.3.2.md) is a historical
before/after diagnostic record. Its probe hashes and then-open release status
are retained; current acceptance belongs to the successor report above.
