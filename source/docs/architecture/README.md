# Repository map

Sacred Gold Plus is a **ROM patch build**, not a web application. It has no
PostgreSQL database, server, API gateway or independent graphics engine. The
game's original code and assets come from a player's own HeartGold ROM at build
time and are not present in this repository. Project-owned JSON tables are
versioned build inputs, while persistent player data is the game's raw `.sav`.

| Need to change or inspect | Start here | Boundary |
| --- | --- | --- |
| Native game behavior or an event | [`source/features`](../../features/README.md) | One folder per feature, with its C/source, installer and tests where applicable. |
| Version composition | [`source/sgp131`](../../sgp131/README.md) | Applies current stages to authenticated predecessor ROMs and reads them back. |
| Earlier build stages | [`source/sgp12`](../../sgp12/README.md), [`source/sgp13`](../../sgp13/README.md) | Historical inputs and native feature plumbing; exact source paths and hashes are part of the build contract. |
| UI drawing and copy | `source/features/ui-native/`, `source/features/settings-ui/`, `source/features/guide-ui/`, `source/sgp131/data/ui-copy.json` | Native DS graphics hooks and text; no separate graphics engine. |
| Game data and translation | `source/sgp13/data/`, `source/sgp131/data/`, `source/translation/` | Authored tables and transforms. Cartridge NARC contents are read from a private input ROM. |
| Emulator measurements | [`source/runtime`](../../runtime/README.md), `source/features/debug/` | Headless melonDS and native field instrumentation; no ROM or save belongs in Git. |
| Player packages | [`source/distribution`](../../distribution/README.md) | Versioned contracts, source documents, patch generation and verification. |
| Tests and audits | `source/run_tests.py`, `source/verifiche/`, `source/quality-audit/`, feature-local `test/` folders | ROM-free CI and explicitly identified private-ROM checks. |
| Cheats | `source/cheats/` | Catalogue and revision checks; do not carry unverified codes to a new ROM. |

The build direction is **authenticated predecessor ROM → feature stages → UI
and mechanics composition → version identity → verified player patches**. A
release package contains patch differences and documentation, never a game ROM.
The [source build guide](../../README.md) documents the exact commands.

## Where a contributor starts

1. Identify the player-visible behavior and its owning feature folder. Record
   the input ROM identity, language, save state and a reproducible baseline.
2. Change the smallest owning source and its independent readback or focused
   regression. For new native memory, register the reservation and prove it does
   not overlap existing owners.
3. Run ROM-free checks, then private-ROM and save-copy checks appropriate to the
   change. A diagnostic savestate does not replace a raw-save Continue, native
   SAVE and cold restart.
4. Record measured results under `source/docs/validation/`. Update the public
   change register and the versioned distribution contract only after the exact
   candidate is known.

Existing stage paths are deliberately stable: historical bootstrap manifests,
source fingerprints and independent readbacks refer to them. New modules should
go in the owning feature folder. Any future physical move needs a separate
manifest/import/link migration and before/after byte comparison; a cosmetic move
must not silently change the built ROM or invalidate reproduction of a release.

## Security and provenance

The relevant trust boundary is the private ROM/save/compiler input entering the
build, not a network service. Build checks pin inputs, reject unexpected native
preimages and verify every owned byte after installation. Public file checks
prevent private ROMs, saves, extracted data and assistant notes from entering
Git. Review behavior and data ownership together: a correct folder name cannot
establish memory safety, save compatibility or release integrity.

The [Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
explains why importable code belongs below a clear source root. [OWASP SAMM](https://owasp.org/projects/samm)
supports documented design and verification practice. [OWASP ASVS 5.0](https://asvs.owasp.org/)
defines requirements for web applications and services; it is not a directory
layout specification or a certification of this ROM patch.
