# Instructions for coding assistants

These instructions apply to the entire repository and to all current and future
chats and sessions, including Codex and Claude Code.

## Work only on main

The maintainer has explicitly chosen this workflow: **work directly on `main`;
do not create branches or pull requests.** This is a standing instruction until
the maintainer explicitly changes it.

- Check the current branch and working-tree status before editing. Preserve
  existing work; never discard changes to move to `main`.
- Make, review and validate changes on `main`. When publication is part of the
  requested task, commit and push directly to `main`.
- Do not create development branches, pull requests, or separate worktrees as
  part of this workflow. Generic skill recommendations to use branches or PRs
  do not override this explicit repository instruction.
- Keep history linear. Do not force-push, rewrite published history, or change
  repository protections without explicit maintainer authorization.
- Release tags identify published versions and are not development branches.
  Never overwrite published release files; corrections require a new release.

This workflow applies to the maintainer and their assistants. Independent
community contributors may still submit pull requests under the existing review
requirements.

## Project references and checks

Read [source/README.md](source/README.md) for build instructions, validation and
release procedures. Run checks appropriate to the change; documentation-only
edits do not require an emulator installation or a full ROM build.

Before committing, review the diff and run `git diff --check` and
`python3 .github/check_public.py`. Add new public files explicitly to
`.github/public-files.json` and the Git index before running the public-file
check. Never commit ROMs, saves, BIOS, dumps, extracted game data or private
workspace notes.

## Continuity between sessions

For 1.3 work, read [the current handoff](source/docs/HANDOFF-1.3.md), the linked
change register and validation report before editing. Do not assume a new chat
inherits earlier conversations or that local changes are already committed.
Keep `source/docs/novita-1.3.0.md`, `CHANGELOG.md` and the handoff current when
behavior or validation status changes. Record new test evidence with the exact
candidate identity; preserve historical reports and their limitations.

## Preserve existing saves

Forward compatibility with `.sav` files from previous patches is a release
requirement. Updating must preserve progress, Pokémon, inventory (including
expanded Bag slots) and existing Plus settings. Never require a new game,
reset a save or clear settings to expose a new feature or version label.

Keep save layouts and identifiers stable. Any necessary format change must
include a lossless, tested migration that preserves older save data. Validate updates
on copies of older saves through normal Continue, an in-game save and cold
restart; include both languages, saves without Plus data and saves with Plus
settings and Bag extensions. Preserve the original fixtures. Emulator savestates
are not a substitute for these raw-save tests. Record the tested coverage and
any limitations; do not infer universal compatibility from a single fixture.

## Release-page format

Use `source/distribution/RELEASE-NOTES-TEMPLATE.md` for player-facing GitHub
releases. Present the game as a whole: current features, screenshots, downloads,
community contributions and credits. Keep maintenance notes to **Some bugs fixed.**
Detailed per-version changes and validation belong in the changelog and source
documentation. Update the overview when gameplay features change. Editing release
descriptions must not replace published ZIPs, checksums or tags.

## Keep local storage bounded

- Keep at most two retained generated builds per required language/target: the
  current verified candidate and the previous verified fallback. Replace the
  fallback only after the new candidate passes its checks. A pending candidate
  may exist temporarily during validation; prune it or promote it when done.
- Coordinate shared output paths with other active chats before cleanup. Do not
  duplicate ROM/APK trees or whole evidence folders across temporary, local and
  Downloads directories. Reference a canonical copy instead.
- Delete reproducible intermediate ROMs, extracted build data and obsolete build
  directories after each run, including failed runs. Keep small reports, hashes
  and reproducer scripts; retain a large diagnostic only while it is necessary.
- Before a large build or capture, check free space and expected peak usage. Keep
  at least 10 GiB free after the planned work; if the budget cannot be met, clean
  known disposable outputs first or report the limitation. Bound log/dump runs.
- Never remove original ROM inputs, BIOS, original saves, save fixtures, unique
  evidence, source changes or Git history to meet this limit. Published release
  assets remain immutable. Stop producers before deleting their outputs.
