# Localization architecture

The 1.3.2 multilingual work separates the shared game implementation from
locale-specific presentation. `source/localization/languages.json` records
the supported original HeartGold identities for English (USA), Italian,
French, Spanish (Spain) and German. The locale is separate from the cartridge
region, original revision and internal save identifiers.

## Current implementation checkpoint

Retail identity and structural admission, plus a resource/message inventory,
are implemented. The complete translated game builds, native locale readers,
manuals and multilingual release package are still being developed. A
recognized original is not an accepted Plus output or a compatibility claim.

The inventory compares the actual common-core image with its English retail
reference and each donor. It identifies changed messages and resource-member
conflicts without exporting the retail message corpus. The historical binary
Guide member inside the text archive is owned by the Guide compiler. Anonymous
overlay executables are not imported as presentation archives.

Project-authored translations live in `localization/locales/<locale>/`.
Retail dialogue, names, fonts and graphics are read from the matching owned
ROM at build time. Unmodified retail content can use the official translation;
Sacred Gold/Plus edits require an explicit translation decision. A matching
archive count alone never authorizes replacing a modified member.

## Development checks

Run from the repository root:

```sh
PYTHONPATH=source .venv/bin/python -m unittest localization.test_localization -v
```

These ROM-free checks cover tampered images, header/revision mismatches,
invalid FAT extents, changed-message donor selection and the binary Guide /
anonymous-overlay boundary. Actual-language parsing, build, runtime, native
SAVE/cold restart and final patch reconstruction have separate evidence.

All original ROMs, saves, extracted data and validation captures stay private.
The public README and technical documentation are English; translated player
manuals belong to the corresponding language in the eventual player package.
