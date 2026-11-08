# Build and verify the 1.3 composition line

**Source status, 8 November 2026:** this directory now contains the unreleased
V1.3.2 title/Options text and the New Game event-bank correction. The 1.3.1
output hashes and package contract below describe the published release, not
an output expected from this development source. No 1.3.2 player package has
been built or accepted. See the [specific validation](../docs/validation/new-game-reset-1.3.2.md).

The build path is **your retail HeartGold → 1.2.5 → historical V1.3 V4 →
current source composition**. The legacy V4 step is reconstructed from authenticated,
already-published sources. The composer installs the UI and mechanical stages, independently reads
them back and records the complete output identity. Compilation and file
reconstruction are separate from runtime or release acceptance.

The current player profile activates **portable storage only**. The additional
Summary controls and configurable rematch owners remain inert. The existing
EV/IV summary tools are retained from earlier versions.

## Exact identities

| Language | Historical V1.3 V4 input SHA-256 | Bytes |
| --- | --- | ---: |
| EN | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` | 147345256 |
| IT | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` | 153228136 |

| Language | Published 1.3.1 player-profile SHA-256 | Bytes |
| --- | --- | ---: |
| EN | `185dc5c53a75652c021ced65157e1c3388cd661ebe90775e5b49314aee753b08` | 152786376 |
| IT | `b68ddd5691538c3895b75f3f20db5a163b2bd8376629f59d2a9d55dc05935bce` | 159029292 |

The [player-package contract](../distribution/release-1.3.1.json) pins the
second table. A version label or filename does not establish byte identity.
The composer admits only the first table; do not relax `baseline.py` to accept
a similar ROM.

## Toolchain and external data

Follow the [source setup](../README.md) for dependencies and the retail-to-1.2.5
build. Production 1.3.1 compilation additionally authenticates:

- Python **3.14.7**, executable SHA-256
  `87d4df53fd91304be5bac391fb204643c36b7df2023c04a0953bcbc7d4fdf634`;
- Apple clang **21.0.0, clang-2100.4.1.1**, binary SHA-256
  `fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`;
- library/source fingerprints in [ui_compile.py](ui_compile.py), and protected
  compiler ownership/environment checks in [compiler.py](../sgp13/compiler.py);
- `charmap.txt` SHA-256
  `58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded`,
  plus `tools/py_scripts/scrcmd.json` SHA-256
  `fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a`,
  from `pret/pokeheartgold` revision
  `0985e8718df4f25e64d6507d89c0c97c0d288981`.

Use a complete Git clone containing published ancestor
`d2bb1f24dad5f88d39325089cf461643d5f99a1a`; a shallow source snapshot alone
does not supply the historical objects. The bootstrap does not fetch history
or change refs. No game, save, BIOS or external reference data is redistributed.
A host-contract test on another interpreter/compiler is not a reproduction
of these production bytes; preserve identity failures rather than bypassing them.

## Reconstruct the historical V4 base

The current `sgp13.build` already uses HF02. To reproduce the older HF01 V4
input, use [bootstrap_13.py](../distribution/bootstrap_13.py) and its
[208-file manifest](../distribution/bootstrap-13-v4.json). The bootstrap reads
only pinned blobs from the already-published commit, verifies Git-object and
SHA-256 identities, and stages only the declared source paths in a private
temporary directory. It authenticates Python, the protected compiler, your
1.2.5 input, charmap and command metadata before the historical build.
No checkout, branch, worktree or game-source edit is needed.

Run from the repository root. Replace the example paths with absolute private
paths and create a new private working directory. Keep at least **10 GiB free
plus the 4 GiB sequential build budget**. Output and report files must be new.

```sh
export SGP_PRIVATE=/path/to/private-sgp131
export SGP_PRET_SOURCE=/path/to/pokeheartgold
mkdir -m 700 "$SGP_PRIVATE"
mkdir -m 700 "$SGP_PRIVATE/work"

.venv/bin/python -B source/distribution/bootstrap_13.py build \
  --language EN --base "$SGP_PRIVATE/sgp-1.2.5-EN.nds" \
  --charmap "$SGP_PRET_SOURCE/charmap.txt" \
  --output "$SGP_PRIVATE/v4-EN.nds" \
  --report "$SGP_PRIVATE/v4-EN.json" --work-dir "$SGP_PRIVATE/work"

.venv/bin/python -B source/distribution/bootstrap_13.py build \
  --language IT --base "$SGP_PRIVATE/sgp-1.2.5-IT.nds" \
  --charmap "$SGP_PRET_SOURCE/charmap.txt" \
  --output "$SGP_PRIVATE/v4-IT.nds" \
  --report "$SGP_PRIVATE/v4-IT.json" --work-dir "$SGP_PRIVATE/work"
```

Each command refuses an output that differs from the V4 table and cleans its
staged sources and intermediate ROMs. Fresh EN and IT reconstructions from
1.2.5 reproduced both V4 hashes and compared byte-for-byte with the canonical
inputs; all 208 source fingerprints matched, with no extra dependencies.
The original 1.2.5 and canonical V4 files remained unchanged. The retail-to-1.2.5
step was not rerun as part of that specific bootstrap check.

HF01 is used **only as a compatibility build intermediate**. The current
1.3.1 chain upgrades it to HF02 before producing the player profile. Do not
install the intermediate V4 as an update, replace a personal save or claim
new runtime acceptance from the bootstrap's file comparison.

## Current UI and owner configuration

Write this exact UI object to a private `ui.json`:

```json
{
  "schema": 1,
  "kind": "test-candidate",
  "scene_work_calls": 64,
  "scene_glyph_budget": 8,
  "scene_last_start_line": 240
}
```

`test-candidate` is the schema's required literal, not an acceptance verdict.
The older [reproduction recipe](../distribution/reproduction-1.3.1.json) uses
work budget 4 and six manual activation fields for a historical trial. It is
retained for that identity and must not be relabelled as the current recipe.

For an initial all-inert build, write this EN mechanics configuration to
`mechanics-EN-inert.json`; use `"language": "IT"` for the other language:

```json
{
  "schema": 1,
  "language": "EN",
  "stage_options": {
    "controls": {
      "mode": "inert",
      "geometry": {
        "bgId": 4, "left": 1, "top": 18, "width": 16,
        "height": 2, "palette": 13, "baseTile": 955
      },
      "variant": "compact"
    },
    "portable": {
      "mode": "inert",
      "activation": {"bridge": 0, "input": 0, "prompt": 0, "travel_mask": 3}
    },
    "rematches": {"mode": "inert"}
  }
}
```

## Compose through the final identity stage

Config files and the managed root must be new. Store UI/mechanics files
outside the managed root. Review each mechanics file and pass its **file-byte**
SHA-256 explicitly; this differs from the canonical `options_sha256` recorded
inside a receipt.

```sh
PYTHONPATH=source .venv/bin/python -B -m sgp131.workbench init \
  --config "$SGP_PRIVATE/managed/workbench.json" \
  --base-en "$SGP_PRIVATE/v4-EN.nds" --base-it "$SGP_PRIVATE/v4-IT.nds" \
  --root "$SGP_PRIVATE/managed"

SGP_MECHANICS_SHA256="$(shasum -a 256 "$SGP_PRIVATE/mechanics-EN-inert.json" | cut -d ' ' -f 1)"

PYTHONPATH=source .venv/bin/python -B -m sgp131.workbench build \
  --config "$SGP_PRIVATE/managed/workbench.json" --language EN --through identity \
  --charmap "$SGP_PRET_SOURCE/charmap.txt" --ui-config "$SGP_PRIVATE/ui.json" \
  --mechanics-config "$SGP_PRIVATE/mechanics-EN-inert.json" \
  --mechanics-config-sha256 "$SGP_MECHANICS_SHA256"

PYTHONPATH=source .venv/bin/python -B -m sgp131.workbench inspect \
  --config "$SGP_PRIVATE/managed/workbench.json"
```

Repeat the build with IT and its own mechanics file/digest. The resulting
`managed/<language>/pending.nds` and `pending.json` describe an all-inert
composition, distinct from the player-profile outputs:

| Language | All-inert projection SHA-256 |
| --- | --- |
| EN | `949aafe759ab110a16d3d1fe17246bb7817c66c5b1257a20a69f9e50183d404e` |
| IT | `e74f2368656010c420596ab222fd4cea4cffa217bd55d36c8968425ee31e4372` |

## Native menu input correction and static lineage

The current outputs also correct Guide/Options input sampling: `System+0x48`
is newKeys, and `System+0x4C` is newAndRepeatedKeys. The predecessor read heldKeys
as a new press, bypassing the native initial hold delay. Native start/continue
repeat timers and button remapping are retained; no fixed delay is introduced.

The prior measured all-inert roots remain EN
`d2101c0e812802e03caa2fe9013d0bfbf947d19698b9cbc0bf62e36121d1b068`
and IT `fd347c3887fee90cd817cb3634cc120ce40ff3418dfa2d538ac9044800ae6da5`.
They are not captures of the new outputs. For these two exact player profiles,
[input_lineage.py](input_lineage.py) admits a **static** derivation: exactly two
LDR immediate bytes and two Module96 CRC32 words change. Restoring only those
four closed byte windows must reproduce the whole measured inert predecessor.
The gate additionally binds the exact new active/inert hashes, length, language,
options digest, Portable-only profile and scene source pin. Unknown mutations
still fail. The schema-2 receipt says `runtime_acceptance: not-run`; the original
schema-1 identity gate and measured capture files remain unchanged.

No new gameplay/input timing or SAVE/cold campaign was run for this small
successor at the maintainer's request. Earlier runtime evidence below keeps its
original identity and scope. Reproducing this exact static successor uses the
same old measured Portable configuration and proof, without changing its root.
Other candidates require their own measured evidence; this is not a generic
permission to reuse captures.

## Portable activation requires measured evidence

For the player profile, keep `controls` and `rematches` inert. The portable
owner uses mode `active`, `bridge`, `input` and `prompt` set to 1, and
`travel_mask` set to 3. Its `candidate_sha256` must identify the matching
**all-inert** projection, not the active result.

Copy each inert mechanics file to a new active file. Change only that
portable entry to the active values above and add `candidate_sha256` and
`context_proof`. The proof has exactly seven fields: `status` (`measured`),
`sha256` (the reviewed capture file's digest), `origin` (what was observed),
`capture_file` (the actual capture path), `capture_rom_sha256` (the matching
all-inert hash), `build_id` and `language`. Do not add `accepted_as`; the
installer derives it. Keep the JSON's top-level language aligned with the
proof and input ROM.

The exact configuration/proof fields are defined in
[activation.py](activation.py) and [portable.py](portable.py). This is an
operator attestation: collect and review the actual evidence for that
identity; do not fabricate it or reuse another candidate's capture. [Portable storage](../docs/portable-box-1.3.1.md)
records the native entry, exclusions and evidence limits.

Use a fresh workbench to compose through `identity` with the reviewed active
mechanics files and the same UI64 config:

```sh
PYTHONPATH=source .venv/bin/python -B -m sgp131.workbench init \
  --config "$SGP_PRIVATE/managed-active/workbench.json" \
  --base-en "$SGP_PRIVATE/v4-EN.nds" --base-it "$SGP_PRIVATE/v4-IT.nds" \
  --root "$SGP_PRIVATE/managed-active"

SGP_MECHANICS_SHA256="$(shasum -a 256 "$SGP_PRIVATE/mechanics-EN-active.json" | cut -d ' ' -f 1)"

PYTHONPATH=source .venv/bin/python -B -m sgp131.workbench build \
  --config "$SGP_PRIVATE/managed-active/workbench.json" --language EN --through identity \
  --charmap "$SGP_PRET_SOURCE/charmap.txt" --ui-config "$SGP_PRIVATE/ui.json" \
  --mechanics-config "$SGP_PRIVATE/mechanics-EN-active.json" \
  --mechanics-config-sha256 "$SGP_MECHANICS_SHA256"
```

Repeat with IT and its active mechanics file/digest. The gate checks the common
inert projection and independent owner readbacks. Compare the full active output
with the player-profile table. A manual edit of descriptor words is not an
accepted build receipt. A `pending` receipt is not runtime acceptance;
workbench promotion requires separately reviewed candidate-bound evidence.

## Battle-loop repair and save coverage

The current [Fairy AI producer](fairy_ai.py) changes the BNE at `0x02252138`
from `D1C6` to `D1C8`, targeting `0x022520CC` after the initial Thumb BL. The
old backedge entered the BL suffix on iteration two. The helper, type matrix,
save layout and persistent IDs remain unchanged. Twenty native EN/IT cases
exercise the full function, and readback rejects the stale branch.
[AI investigation](../docs/ai-scoring-1.3.1.md) preserves the causal trace,
caller coverage and limits of natural battle/device checks.

Fresh host headless checks on the two exact player-profile hashes completed
four Continue/field/native SAVE/process-exit/cold Continue cycles: the same
early no-Plus save and authentic 1.2.2 save were each loaded by EN and IT.
The latter retained five party Pokemon, 113 boxed Pokemon, non-default Plus
settings and three live expanded-Bag slots. Protected semantic comparison and
bounded exact-delta audit passed; each cold SRAM export equalled its completed
SAVE byte-for-byte.

These are **two unique fixtures**, not every historical version or save.
The early save has no Pokemon; active courses, positive hunts, a distinct
advanced EN-origin fixture and the last expanded slot are outside these four
runs. Strict audits remain non-PASS for finite HF02 import, native map-object
movement and PC dirty-bitmap reset; the separately reviewed exact changes are
explicit in the bounded result. Native RTC/IGT and console bookkeeping are
also declared. These host checks are not Android or physical-device results.
See [validation](../docs/ui-1.3.1-validation.md) and the
[bug register](../../BUG-FIXES-1.3.1.md) for exact checkpoint scope.

Keep original fixtures and rollback records. Retain only the current verified
candidate, verified fallback and a temporary pending output per language.
[Distribution](../distribution/README.md) covers the two-decoder patch checks
and player PDFs; those file checks do not add gameplay/save acceptance.
