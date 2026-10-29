# 1.3-dev native interface refinement plan

> Execute the tasks using the existing autonomous mandate and scoped parallel
> workers. The maintainer requires main-only work; no branch, worktree or PR.

**Goal:** integrate the Guide and Plus controls into the native HGSS interface
and make the Cap consultant immediately recognizable, preserving behavior/saves.

**Architecture:** reuse guarded native palettes, font/window APIs and original
NPC animation. Keep visual changes in the 1.3 builder; private runtime campaigns
verify actual controls and resource lifetime. Preserve the previous v5 candidate.

**Tech Stack:** native Thumb C, guarded Python installers, Nitro resources,
Capstone/Unicorn and pinned headless melonDS.

**Spec:** [HGSS interface contract](hgss-ui-contract.md), from the maintainer's
explicit follow-up. Implementation choices within that scope are delegated.

## Global constraints

- main only; preserve preexisting staged work and all published files.
- No save-format or Plus-setting-ID change. Never modify original fixtures.
- Existing 1.2 pipeline stays unchanged. No extracted game graphics in Git.
- Guide code remains within 8192 bytes and state within240; no idle-frame heap
  work or retained icon allocations. Confirmation draws only five bounded frames
  through the existing temporary-window path. Keep the font cache and cleanup.
- Reassign only unused development reserve `0x023D7500..0x023D7700` (512 bytes)
  from training extension to the Plus button helper, with empty/read-back guards.
- Original native NPC graphics and resource IDs must remain intact.

## Tasks

### 1. Guide icon, hierarchy and inputs — root

Files: `features/field-guide/sorgenti/guide.c`, related tests,
`sgp13/guide.py`, `sgp13/content.py`, content-bound tests and feature README.
Interfaces: SGG1 entry IDs/pages and GuideCursor stay stable; text line width
becomes208px. Existing live-menu validation and input hooks remain authoritative.

- [x] Verify native frame/palette/confirmation timing and retain baseline captures.
- [x] Add failing native checks for delayed confirmation, cancellation and no
  native-item fallthrough; tighten meaningful text-width boundary tests.
- [x] Implement framed native-color icon, bounded page-turn feedback, subject
  hierarchy, readable row/detail margins and footer states.
- [x] Compile within owned ranges; run Guide suites and actual touch/D-pad,
  localized long-text, reference-return and repeated-exit campaigns.

### 2. Visible Plus access — scoped worker

Files: `features/plus-ui/*`, `sgp13/plus_ui.py`; root updates reserve manifest.
Interface: helper owns only512bytes at7500; existing pending options/Plus
transactions, settings and A/B/SELECT behavior are unchanged.

- [x] Verify native page feasibility and choose the authorized visible-button fallback.
- [x] Test touch bounds, native-row preservation and preview-printer ownership.
- [x] Implement native-footer button, guarded helper and exact installation read-back.
- [x] Verify actual EN/IT touch/SELECT open, cancel/apply and later native preview.

### 3. Recognizable consultant — scoped worker

Files: `sgp13/consultant.py`, `sgp13/training.py`, minimal native lookup helpers,
guards/tests. Root updates composition allowlist for overlay1 and`a/0/8/1`.
Interface: a dedicated unused sprite ID maps to an appended private-build orange
Delivery texture; existing sprite IDs and texture members remain unchanged.

- [x] Verify unused ID, native lookup/animation ABI and both Mart floor positions.
- [x] Add tests for original-table/member preservation, texture transform bounds
  and guarded native lookup fallback.
- [x] Install dedicated sprite and accessible consultant position.
- [x] Verify EN/IT ordinary interaction/cancel/market exit and original postmen.

### 4. Integrate, review and deliver — root

Files: builder/read-back/tests, reserve manifest, public-file allowlist,
new validation record; private ROMs/receipts/captures remain outside Git.

- [x] Build new EN/IT candidates from untouched1.2.5; freeze hashes and source receipt.
- [x] Run affected native tests, complete Guide/content and UI regressions, old-save
  SAVE/cold matrix, and bounded battle/training smoke after UI transitions.
- [x] Fresh independent review; fix reproducible defects, inspect real screenshots.
- [x] Run project runner, diff/public-file checks; deliver a distinct private build
  and updated screenshot gallery with explicit tested scope/limits.

## Review focus

Pending activation during B/X, fades, reused field menus or excluded modes must
never open a stale app. Added glyph margins must not truncate localized text.
Palette/tile changes must not affect native icons or registered-item slots.
Options must retain native pending-edit semantics and asynchronous preview
cleanup. A dedicated NPC must not recolor original postmen or obstruct movement.

Final acceptance and limits: [v8 validation](ui-1.3-dev-validation.md).
