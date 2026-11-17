# Repeatable update and localization procedure

Use this page for 1.3.2 and later updates. Historical reports retain their original
candidate identities; add new evidence rather than relabelling an older test.
Proprietary inputs and private validation evidence remain outside the public
source tree.

Current game identities belong to [game-1.3.3.json](../distribution/game-1.3.3.json).
The [1.3.3 package contract](../distribution/release-1.3.3.json) selects five
targets, 40 recognized sources and 200 direct updater routes in one ZIP, with
five primary clean-ROM patches, ten localized PDFs, eight shared English
guides, 15 cheat files and four preserved builder inputs. The original 35 source
IDs retain their hashes; five distinct IDs cover corrected 1.3.2 installations.
Unknown hashes and missing routes fail admission. Older targets are source
inputs, not additional destination versions. See the
[correction and acceptance report](validation/fixes-1.3.3.md).

The [r4 package contract](../distribution/release-1.3.2-r4.json),
[documentation-only contract](../distribution/documentation-1.3.2.json) and
[editable workspace](../../package/README.md) retain the historical 1.3.2
identities and document-only workflow. Preserve their frozen hashes and reports.

| Change or evidence | Read and update |
| --- | --- |
| Player features and supported languages | root `README.md`, `CHANGELOG.md`, current change register |
| Locale ownership, original inputs and native presentation | `localization.md`, `localization/languages.json`, `localization/locales/<locale>/` |
| Shared core, compiler/input pins and activation | `source/README.md`, `sgp131/README.md`, actual workbench receipts |
| Save layout, migration and preserved fields | repository save requirements, event-bank/Plus/Bag owner sources, existing raw-save comparisons |
| Exact candidate acceptance | a new dated/versioned report under `docs/validation/`; [physical test method](native-hardware-validation.md) |
| Player PDFs and notices | each locale's `documents.json` for installation/news; `guides/catalogue.json`, `distribution/package_workspace.py`, original guide helpers and the clean-retail baseline |
| Cheat compatibility | each locale's `cheats.json`; `localization/cheats.py`, exact target identity and native preimages |
| Source routes and package identity | game/package contracts under `distribution/`; documentation-only identity in `documentation-1.3.2.json`; `distribution/README.md` |
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
   Current delivery has ten localized installation/news PDFs and eight shared
   English gameplay guides, plus each language's revision-bound cheat files.
   Use the explicit versioned packager for 1.3.3; the seeded package workspace
   retains the historical 1.3.2 document-only recomposition workflow.
   Historical renderers remain reproducible. Regenerate target-bound material
   after a target-hash change, updating the corresponding document authorities.
   Admit cheat instructions only after complete target/native preimage checks;
   unresolved runtime pointers stay omitted with localized explanations.
6. Review the diff; explicitly admit new public files, run `git diff --check`,
   the public-file checker and relevant code tests. Inspect the entire outgoing
   history against `origin/main` for private artifacts before pushing. Wait for
   hosted CI, which does not build or accept commercial ROMs.
7. Require every recognized source ID from the applicable package contract
   exactly once in each target's route list. Encode all routes and decode each
   with both xdelta3 and the pinned independent Rom Patcher JS implementation.
   Check complete target hashes, ZIP members, per-language documents, manifests
   and checksums. Verify the single ZIP against its applicable authority: the
   1.3.3 package, frozen r4 baseline and historical documentation-only delivery
   are different archive identities. The [workspace procedure](../../package/README.md)
   verifies document changes while protecting the non-document members,
   including the existing patches, cheats, updaters and developer inputs.
   A package-only successor pins the accepted game identities; a changed game
   needs its own candidate acceptance. Publication is a separate authorized step:
   use a new release for corrections and preserve published assets and tags.

The [Guide correction report](validation/guide-opening-1.3.2.md) separates
bounded host/native-save results from the reported Android UI check. Nintendo
hardware tests use the [native-hardware procedure](native-hardware-validation.md)
and are a separate evidence class, not implied by those results or green CI.
Preparing or publishing a package does not install it on a device.

Universal routing means all explicitly recognized bases, not arbitrary damaged
or modified ROMs. Unknown inputs fail admission. Choose the destination language
explicitly; ordinary updates retain the existing language, variant, filename,
path, emulator association and current personal save. Installation on a device
also requires the current backup and exact-successor procedure in repository
instructions; preparing/publishing an update does not install it.
