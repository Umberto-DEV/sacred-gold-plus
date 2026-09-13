## What changes for the player?

Describe one concrete change in plain English. Link the issue or discussion.

## Why is the change needed?

Explain the previous result and the intended result.

## Tests

Class A (no game file) run by CI and reproducible with `python source/run_tests.py`:

- Class A result: <!-- e.g. "266 collected, 221 ran, 45 skipped, PASS" -->

Class B needs your own game file and never runs in CI, so this line is the only
record that the change was tried against a real ROM. Write what you ran and what
it said, or "not run" — see [source/README.md](../source/README.md).

- **Class B tests run locally:** <!-- e.g. "sgp12.costruisci + sgp12.verifica on EN and IT: byte-identical, all read-backs green, T1-T5 11/11" or "not run: documentation only" -->

State the exact version and language, the steps, the result before and after, and
any check you could not perform. Do not paste private logs or paths.

## Credits and review

- [ ] I reviewed every changed file and attachment for private information.
- [ ] I included no ROM, BIOS, save, save state, raw log, game text, game code or extracted game data.
- [ ] I updated `source/docs/arm9-reserve-map.json` and the reservations page in the same change, if this claims space in the ARM9 reserve.
- [ ] I documented reused work, its source and applicable permissions.
- [ ] I disclosed material AI assistance, if any.
- [ ] I left existing released patch files unchanged.
