# Release 1.2.4 validation — 24 October 2026

The release includes the battle-copy animation barrier, the field Waterfall
search guard and the updated title. Public ROMs contain no private stat edits.
The event script and legacy flags of the Vermilion Latios/Latias totem remain
unchanged. A player caught Latios using the maintenance candidate and reported
that the previous slowdowns were no longer present; this does not isolate the
old freeze's cause or validate every animation/city scenario.

## File validation

- The published 1.2.3 EN/IT images were checked against their exact SHA-256s.
- The maintenance stage checked all preimages, compiled source/blob hashes,
  core hash, compressed overlays with two BLZ decoders, branch destinations,
  unchanged regions, and the full streamed outputs.
- 19 recognized source ROMs, including original HeartGold US/IT, generate both
  final languages: 38 routes. Each route was decoded with xdelta3 and pinned
  RomPatcher.js, compared with the target SHA-256, and discarded after checking.
- Both player ZIPs contain 40 members, including 19 patches, manifests, the
  original five PDF guides, trainer reference, Game Guide, historical illustrated
  guides, current two-page PDF guide, instructions, license and cheat files.
- Original reference documents retain their independently pinned bytes.
- Both final ROMs passed all 11 ARM9 reserve checks (22 total).
- Focused maintenance tests: 28 passed. Library tests: 42 executed, 31 skipped
  because the full-build fixtures were not enabled. Distribution tests: 4 passed.

Exact input/target pins are in `source/distribution/release.json`; the ZIP
member inventory and patch hashes are included in each archive. Release assets
have separate SHA256SUMS. The public sources include reproducible packaging.

## Construction and limits

The existing construction stages and their intermediate option-title blobs
remain unchanged. Their stable reserve-map header fields are unchanged too.
The builder and verifier append maintenance to the exact, hash-pinned 1.2.3
intermediate; `build/manutenzione/versione.json` specifies the final 1.2.4 title.
A mismatch refuses construction rather than silently accepting another baseline.

A fresh full build and full runtime campaign were intentionally not repeated
locally for this release. The lightweight incremental checks and patch round
trips establish the distributed file contents; they are not a claim that the
entire public builder was rerun from retail in this release session. CI runs
the ROM-free suites, including the new maintenance and distribution checks.
No game/emulator installation or save rewrite was performed for publication.

The brief Android presentation measurement after the player's report was
regular (median 16.763 ms, p95 16.767 ms, no interval over 25 ms). It is not a
measurement of DS logic FPS/input latency or a controlled before/after trial.
Raw logs and personal installation receipts are not distributed.

## Independent review

The read-only review found no confirmed blocking defect. It separately checked
both archive inventories and original-document hashes. Remaining coverage limits:
the final-stage reader shares its patch plan with the writer (the BLZ decoding
and output pins provide separate checks); seven totem tests need private ROM
metadata and are explicitly skipped in CI. Their classification in the runner
can be refined separately. No regression from concurrent native y-offset writes
was demonstrated, but all native animation overlaps have not been exercised.
