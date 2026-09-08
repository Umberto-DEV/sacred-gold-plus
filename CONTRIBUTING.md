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

First read [the known limits](CHANGELOG.md#known-limits) and search existing issues. For a bug, use [Report a bug](https://github.com/Umberto-DEV/sacred-gold-plus/issues/new/choose). Tell us which release, language and camera you chose, what you did, what you expected and what happened instead. Try the same steps with cheats off and from a normal game start.

For wording, quote only the short phrase that needs changing, explain where it appears and suggest a replacement. Keep Pokémon names, item meanings and on-screen button labels consistent. English does not need to be perfect: a short, understandable explanation is best.

Use [Discussions](https://github.com/Umberto-DEV/sacred-gold-plus/discussions) for questions, ideas and coordinating a new language. Please be considerate and address the work rather than the person.

## Developers

1. Start with one issue or a short proposal. Agree on the intended behaviour before a large change.
2. Fork this repository and create a branch for that contribution. The [source guide](source/README.md) explains how to build from your own required game files.
3. Change the source recipe or tool. Check the original problem before and after the change, then try the nearby menus, battles or save actions it could affect. For documentation-only contributions, review the wording, links and relevant forms; no game files or new gameplay run are needed.
4. Push your branch to your fork. On GitHub, select **Contribute → Open pull request**, or use **Pull requests → New pull request → compare across forks**. The base repository should be `Umberto-DEV/sacred-gold-plus`, branch `main`; the head should be your fork and contribution branch. Read **Files changed**, then use the description template to explain the player-visible change, the reason and what you tested. Mention checks you could not perform. Include credits and permissions for reused work. Choose **Create draft pull request** if you want feedback before the work is ready.
5. Address review comments. The maintainer reviews and merges the change, then prepares a separately numbered release. Opening or merging a PR does not automatically publish a game update.

Do not replace the released 1.04 patches. Propose source changes first; new patch files belong to the next release. Keep game changes separate from emulator changes. Follow the destination project's own guide for a melonDS contribution.

## What is safe to share

Share your proposed source changes, a concise test description and, when necessary, a small redacted log excerpt. Remove real names, account details, paths to personal folders, network addresses, device identifiers and unrelated application information. Review attachments manually before submitting them.

Do not upload ROMs, BIOS, firmware, saves, save states, memory dumps or raw device logs. Do not use personal gameplay captures as test attachments. Describe the steps and result in text; ask before adding a new kind of artifact.

AI assistance must be disclosed when it materially contributes to a change or its explanation. The contributor remains responsible for understanding the change, checking its output and accurately describing the tests. Do not claim another person's approval or testing that did not happen.

Run the local checks in the source guide before opening a PR. They help catch unexpected files and packaging errors. Passing them does not replace human review or in-game testing. There is no active GitHub Actions workflow in this initial repository.
