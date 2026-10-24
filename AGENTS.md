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
