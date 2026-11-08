# Repeatable update and localization procedure

Use this page for 1.3.2 and later updates. Historical reports retain their original
candidate identities; add new evidence rather than relabelling an older test.
Proprietary inputs and private validation evidence remain outside the public
source tree.

The 1.3.2 contract defines one latest target for each of EN, IT, FR, ES and DE.
Every target accepts the same 30 recognized original/historical sources,
giving **150 direct routes**. Older target versions are not included in the
current player package. Unknown hashes and missing routes fail admission.
In package revision r3, the main ZIP contains five same-language clean-ROM
routes; the optional updater ZIP contains all 150 routes. Both produce the
unchanged accepted 1.3.2 targets.

| Change or evidence | Read and update |
| --- | --- |
| Player features and supported languages | root `README.md`, `CHANGELOG.md`, current change register |
| Locale ownership, original inputs and native presentation | `localization.md`, `localization/languages.json`, `localization/locales/<locale>/` |
| Shared core, compiler/input pins and activation | `source/README.md`, `sgp131/README.md`, actual workbench receipts |
| Save layout, migration and preserved fields | repository save requirements, event-bank/Plus/Bag owner sources, existing raw-save comparisons |
| Exact candidate acceptance | a new dated/versioned report under `docs/validation/` |
| Player PDFs and notices | each locale's `documents.json` (`p:r2:*` for current installation/news); `distribution/reference_docs.py`, `player_notices.py` and the clean-retail baseline |
| Cheat compatibility | each locale's `cheats.json`; `localization/cheats.py`, exact target identity and native preimages |
| Source routes and package identity | a new `distribution/release-<version>.json`; `distribution/README.md` |
| Player release page | `distribution/RELEASE-NOTES-TEMPLATE.md`; maintenance notes stay “Some bugs fixed.” |
| Public admission and CI | `.github/public-files.json`, `.github/check_public.py`, `source/run_tests.py` |

## Minimal release gates

1. Authenticate originals and historical sources by complete SHA-256 and size.
   Preserve original ROM/save inputs. Add a new recognized source explicitly;
   never infer compatibility from filenames, header language or version text.
2. Build one current target per language with the guarded tools. Keep source
   ownership explicit. Check translated-key coverage, command arguments, glyphs,
   context-specific text geometry, resource budgets and independent byte readback.
   Regional presentation must preserve unowned gameplay bytes and save structures.
   Freeze shared code, locale copy, generated C descriptors and explicit source
   pins together before building EN/IT cores and regional presentations. Record
   exact UI/mechanics configurations; changing them creates a new candidate.
   Ordinary field text, button-cap footers and confirmation action bars have
   different native geometry; check each context rather than one global limit.
3. Reuse the established bounded runtime scripts: cold first boot/New Game,
   completed Mom conversation and player movement. Use raw-save copies for
   Continue → native SAVE → process exit → cold Continue. Compare protected
   progress, Pokémon, inventory/Bag extensions and existing Plus settings.
   Record exact hashes, actual captures and limitations. No full-playthrough
   claim follows from this gate. Savestates do not replace raw saves. Check the
   affected localized UI with visible captures. Any inherited result needs an
   explicit byte-lineage explanation and separately identified successor checks;
   never relabel a predecessor's capture.
4. Cover save-format categories with representative existing fixtures, including
   saves without Plus data and saves with populated extensions/settings. Reuse
   owner/component regressions for migrations. A ROM-only patch never edits a
   `.sav`; every recognized source route must reconstruct the same complete
   target bytes for its chosen language.
5. Generate translated manuals from the final target and matching clean retail
   baseline. Verify numerical parity between languages and inspect representative
   rendered pages. Authenticate every PDF and cheat file by size/hash in the new
   contract. Recheck installation hashes whenever a target changes.
   Current package revision r3 outputs ten localized installation/news PDFs and
   seven shared English gameplay PDFs, plus each language's revision-bound cheat
   files. The older 45-PDF schema-2 renderer remains reproducible. Regenerate
   target-bound material after a target-hash change; use `render_player_documents`
   and `render_shared_guides` for the current layout.
   Admit cheat instructions only after complete target/native preimage checks;
   unresolved runtime pointers stay omitted with localized explanations.
6. Review the diff; explicitly admit new public files, run `git diff --check`,
   the public-file checker and relevant code tests. Inspect the entire outgoing
   history against `origin/main` for private artifacts before pushing. Wait for
   hosted CI, which does not build or accept commercial ROMs.
7. For 1.3.2, require all 30 source IDs exactly once in each of the five target
   lists. Encode all 150 routes and decode each with both xdelta3 and the pinned
   independent Rom Patcher JS implementation. Check full target hashes, ZIP
   members, per-language documents, manifests and all checksums. Publish a new
   version/tag/assets; preserve previously published assets and tags.
   For package-only corrections, pin the existing accepted game targets in a
   new package-revision contract. Verify both ZIPs: the main download has one
   patch per language, two visible localized PDFs, three cheat files, consistent
   notices/licenses, `START-HERE.txt` and exactly seven English PDFs in `Originals`.
   It has no JSON inventories or `Documents` folders. The separate optional ZIP
   keeps all 150 updaters, localized readable hash tables and technical manifests.

This release's game acceptance uses bounded host/native-save checks. Physical
device tests are a separate evidence class, not implied by those results or
green CI. Preparing or publishing a package does not install it on a device.

Universal routing means all explicitly recognized bases, not arbitrary damaged
or modified ROMs. Unknown inputs fail admission. Choose the destination language
explicitly; ordinary updates retain the existing language, variant, filename,
path, emulator association and current personal save. Installation on a device
also requires the current backup and exact-successor procedure in repository
instructions; preparing/publishing an update does not install it.
