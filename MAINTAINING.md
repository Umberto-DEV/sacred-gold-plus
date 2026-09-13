# Review and publish

The branching model and the two classes of test are described in [DEVELOPMENT.md](DEVELOPMENT.md). This page is the maintainer's side: reviewing a contribution, and cutting a release.

## Approve a contribution

Open **Pull requests**, choose the contribution and read its explanation. In **Files changed**, check that it contains only the intended work and no private information: no ROM, save, BIOS or dump; no game text, game code, extracted table, archive or graphic; no personal path or name; no file that belongs to a private workspace. Read the tests and the known limitations, and look at the **Class B tests run locally** line — that is the only evidence that anything was tried against a real game file, because CI cannot do it.

If the change claims space in the ARM9 reserve, check that `docs/arm9-reserve-map.json` and [docs/arm9-reserve-reservations.md](docs/arm9-reserve-reservations.md) were updated in the same change, that the new block does not overlap another, and that anything with a public address is anchored to the high end.

Use **Review changes → Request changes** if something needs correcting, or **Approve** when it is ready. Resolve outstanding conversations, verify the local test results and use **Squash and merge** — `main` keeps a linear history. `main` requires an owner review for collaborator changes; administrators can handle their own changes when working alone, but must perform the same checks.

The **Public checks** workflow checks the public file list and the release fingerprints, rebuilds the release ZIPs from the checked files, and runs the Class A tests. It uses no game files. A message saying **workflows awaiting approval** means permission to run tests, not approval of the code or release. [GitHub's guide](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks).

## Add a collaborator

People can already open issues, join discussions and submit pull requests through a fork. Direct access is only needed for a trusted ongoing collaborator.

Open **Settings → Collaborators → Add people**, enter their GitHub username and send the invitation. A personal repository gives collaborators write access, so check the account carefully and retain the owner-review requirement. Remove access when it is no longer needed. An organization is an option later if the project needs more granular team roles. [GitHub's instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

## Publish an update

### What happens automatically?

| Action | Result in this repository today |
| --- | --- |
| Push to any branch, or open/update a pull request against `main` | Runs **Public checks**: the public file contract, the release fingerprints, the ZIP rebuild and the Class A tests. It does not build a game and does not publish a release. |
| Add a version tag | Marks a commit. It does not run a build or create the player packages. |
| Open a release page | GitHub offers **Source code (zip)** and **Source code (tar.gz)** archives of the tagged repository. These are not the player packages. |
| Publish a prepared release | Makes the attached packages and release notes available for players. |

Automated release notes, source archives, the **Public checks** tests and building downloadable patches are separate features. [About GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

### Prepare and publish the packages

Use a dedicated checkout of this public repository. Never push the history of a private development workspace into it. Import only the reviewed source changes; game files, private notes and test recordings stay outside this checkout.

Rebuild the game from its base with `python3 -m sgp12.costruisci`, check it with `python3 -m sgp12.verifica` (which rebuilds internally and compares byte for byte, runs every block read-back and the reserve checks T1–T5), and confirm the output fingerprint matches the one the release manifest advertises. Regenerate the patches from that exact ROM, decode every published route back and compare the complete output SHA-256 and size against the built ROM — do not take the manifest's word for it. Verify that the cheat files still address the blocks the map marks public.

Then run, from the repository root:

```sh
.venv/bin/python source/run_tests.py
python3 .github/check_public.py
python3 -B release/1.2/build_zip.py
```

Review the exact staged files with `git diff --cached` and check commit names and email addresses before committing. Use your public GitHub identity and its private noreply email, not a personal email or local computer name. Check every new commit, not only the final file tree.

Each language package carries the patches for the recognized inputs, the cheat files, the manuals and the install guide, pinned by size and SHA-256 in `release/1.2/contenuto.json`; `check_public.py` refuses a folder that differs from that census. A documentation-only revision can reuse already reviewed patch bytes when their input and output fingerprints are unchanged; it does not establish new gameplay test results. Check the contents and metadata of each ZIP, including PDFs and other attachments. Never upload a ROM or an entire build directory.

Create a draft under **Releases → Draft a new release**. Use a new `vX.Y` tag, attach the reviewed packages and write what changed, what remains unresolved and which input and save paths were checked. Mark a preview as **pre-release** and tag it `vX.Y-rcN`. Publish when the actual package has passed review, then download the uploaded assets and verify them again.

Never overwrite a released asset with different bytes. A correction needs a new release. Keep `README.md`, `CHANGELOG.md` and the release manifests consistent with the downloads.

### A future automation path

The file checks and the Class A tests are configured in [Public checks](.github/workflows/public-checks.yml). Keep the game build and the playtesting in an isolated local environment with the required private inputs.

A separate, manually started packaging workflow could later validate approved patch files, assemble the guides and create a **draft** release for review. Publishing that draft would remain a deliberate maintainer action. Such a workflow would package already prepared patches; it would not build a new game from source. Full patch generation still needs the exact game input and is not implemented on GitHub here. Do not attach a personal development machine as a runner for untrusted pull requests.

For any workflow change, review its permissions and outputs, verify a successful run and update this guide to describe the behaviour available. [GitHub workflow triggers](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Community settings

Issues are for reproducible bugs; Discussions are for help and ideas. **Public checks** uses read-only repository permissions, pinned actions and no game files or repository secrets. Keep approval requirements for external contributors and keep private game tests and logs out of public output.

Keep `main` as the permanent branch, protected, with a linear history and one required review. Use a `feature/…` or `fix/…` branch, or a contributor's fork, for each pull request, then delete the temporary branch after merging. Keep version tags and release downloads; deleting a merged branch does not remove them.
