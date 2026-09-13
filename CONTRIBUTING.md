# Contribute

You can help by playing, reporting a problem, improving a translation or developing a fix. You do not need direct access to this repository to contribute.

## Choose where to start

Sign in to a free GitHub account to post. Reading the guides and downloading a release do not require an account.

| What you want to do | Where to go | What to select |
| --- | --- | --- |
| Report something that went wrong | [Issues](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose) | **New issue → Report a bug**; complete the required fields and select **Create**. |
| Ask for help | [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) | **New discussion → Q&A**. Include the release and explain where you got stuck. |
| Suggest an idea or translation | [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) | **New discussion → Ideas**. Describe one improvement and why it would help players. |
| Propose a change to files | [Pull requests](https://github.com/Umberto-DEV/sacred-gold-plus/pulls) | Follow the developer steps below. |

An issue describes a problem; a pull request proposes file changes for review. Neither gives another person permission to change the main project directly.

## Players and translators

First read [the known limits](CHANGELOG.md#known-limits) and search existing issues. For a bug, use [Report a bug](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose). Tell us which release and language you chose, what you did, what you expected and what happened instead. Try the same steps with cheats off and from a normal game start.

For wording, quote only the short phrase that needs changing, explain where it appears and suggest a replacement. Keep Pokémon names, item meanings and on-screen button labels consistent. English does not need to be perfect: a short, understandable explanation is best.

Use [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) for questions, ideas and coordinating a new language. Please be considerate and address the work rather than the person.

## Developers

The full picture — branching model, release cycle, the two classes of test, how the repository is laid out — is in [DEVELOPMENT.md](DEVELOPMENT.md). The short version:

1. Start with one issue or a short proposal. Agree on the intended behaviour before a large change.
2. Fork this repository and create a `feature/…` or `fix/…` branch for that contribution. The [source guide](source/README.md) explains how to build the game from your own required game file, and [docs/rebuilding-1.2.md](docs/rebuilding-1.2.md) walks through it step by step.
3. Make the change. Run the Class A tests — the same ones CI runs, and they need no game file:

   ```sh
   python3 -m venv .venv
   .venv/bin/pip install -r source/requirements.txt
   .venv/bin/python source/run_tests.py
   ```

   If your change touches the game, also rebuild and check a ROM locally (Class B) and check the original problem before and after, then try the nearby menus, battles or save actions it could affect. For documentation-only contributions, review the wording and links; no game file and no gameplay run are needed.
4. Push your branch to your fork. On GitHub, select **Contribute → Open pull request**, or use **Pull requests → New pull request → compare across forks**. The base repository should be `Umberto-DEV/sacred-gold-plus`, branch `main`; the head should be your fork and contribution branch. Read **Files changed**, then fill in the description template: what changes for the player, why, and — on the **Class B tests run locally** line — which game-file tests you ran and what they said. Mention checks you could not perform. Include credits and permissions for reused work. Choose **Create draft pull request** if you want feedback before the work is ready.
5. Address review comments. The maintainer reviews and merges the change, then prepares a separately numbered release. Opening or merging a pull request does not automatically publish a game update.

Do not replace the released 1.2 patches. Propose source changes first; new patch files belong to the next release. If your feature needs space in the ARM9 reserve, claim it in [docs/arm9-reserve-reservations.md](docs/arm9-reserve-reservations.md) in the same change — two features writing to the same address is the failure this register exists to prevent. Keep game changes separate from emulator changes; follow the destination project's own guide for a melonDS contribution.

## What is safe to share

Share your proposed source changes, a concise test description and, when necessary, a small redacted log excerpt. Remove real names, account details, paths to personal folders, network addresses, device identifiers and unrelated application information. Review attachments manually before submitting them.

Do not upload ROMs, BIOS, firmware, saves, save states, memory dumps or raw device logs. Do not commit game text, game code, extracted tables, archives or graphics: this repository carries the tools and our own compiled code, and reads everything else from the player's own file at build time. Do not use personal gameplay captures as test attachments. Describe the steps and result in text; ask before adding a new kind of artifact.

AI assistance must be disclosed when it materially contributes to a change or its explanation. The contributor remains responsible for understanding the change, checking its output and accurately describing the tests. Do not claim another person's approval or testing that did not happen.

Run the local checks above before opening a pull request. The **Public checks** GitHub Actions workflow also checks the public file list and the release fingerprints and runs the Class A tests, on pushes to any branch and on pull requests, without game files. Passing it does not replace human review or in-game testing. A first contribution from a fork may need maintainer approval before the workflow runs.
