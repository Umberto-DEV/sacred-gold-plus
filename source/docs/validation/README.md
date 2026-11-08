# Candidate validation

Add one report per candidate or investigation. Put the version or subject in
the filename, and include the exact ROM SHA-256, language, predecessor, save
copy hash, emulator/core build, input sequence, measured outcome and limits.
Keep screenshots and large private diagnostics outside Git; cite their private
receipt or a small public summary. Distinguish a component test, headless game
run, Android/device run and release acceptance.

Historical reports at `source/docs/` retain the results and limitations of the
candidates they tested. Do not relabel an older result as evidence for a new
ROM. See the [test bench](../test-bench.md) and [source guide](../../README.md).

The [1.3.2 New Game reset investigation](new-game-reset-1.3.2.md) records a
diagnostic before/after probe and explicitly leaves release acceptance open.
