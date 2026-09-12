# Review and publish

## Approve a contribution

Open **Pull requests**, choose the contribution and read its explanation. In **Files changed**, check that it contains only the intended work and no private information. Read the tests and known limitations; try the affected game behaviour when needed.

Use **Review changes → Request changes** if something needs correcting, or **Approve** when it is ready. Resolve outstanding conversations, verify the local test results and use **Squash and merge**. Main requires an owner review for collaborator changes; administrators can handle their own changes when working alone, but must perform the same checks.

The **Public checks** GitHub Actions workflow checks the public file list, reviewed media, cheat files and patch fingerprints, then runs the synthetic translation and offline installer tests on pushes to main and pull requests. It uses no game files. A message saying **workflows awaiting approval** means permission to run tests, not approval of the code or release. [GitHub's guide](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks).

## Add a collaborator

People can already open issues, join discussions and submit pull requests through a fork. Direct access is only needed for a trusted ongoing collaborator.

Open **Settings → Collaborators → Add people**, enter their GitHub username and send the invitation. A personal repository gives collaborators write access, so check the account carefully and retain the owner-review requirement. Remove access when it is no longer needed. An organization is an option later if the project needs more granular team roles. [GitHub's instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

## Publish an update

### What happens automatically?

| Action | Result in this repository today |
| --- | --- |
| Push to main or open/update a PR targeting main | Runs **Public checks** on the public files and synthetic tests. It does not build patches or publish a release. |
| Add a version tag | Marks a commit. It does not run a build or create our download packages. |
| Open a release page | GitHub offers **Source code (zip)** and **Source code (tar.gz)** archives of the tagged repository. These are not the player packages. |
| Publish a prepared release | Makes the attached patch packages and release notes available for players. |

Automated release notes, source archives, the **Public checks** tests and building downloadable patches are separate features. [About GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

### Rebuild the 1.2 game and packages

The private lab this project is developed in (`local/`, not part of this public repository) keeps its own build tools. `local/rom-tools/sgp12/costruisci.py` rebuilds the 1.2 game from the finished, unchanging 1.1 game: same recipe every time, checked against the fingerprints already declared for 1.2, so a rebuild either reproduces the same bytes or the build stops. It never starts from source assets directly; 1.2 is 1.1 plus the reviewed 1.2 changes applied in place.

Once the 1.2 game is rebuilt (or has not changed), one command regenerates the player-facing patches and the two ZIPs from it:

```sh
python3 -B local/publishing/matrice-1.2/rigenera.py
python3 -B local/publishing/build_zip_1_2.py --destination local/releases/1.2-zip-<new folder>
```

`rigenera.py` runs the local publishing test suite as part of regenerating the patch matrix and stops before producing anything if a check fails; always give `build_zip_1_2.py` a destination folder that does not exist yet, since it never overwrites or deletes. Only the output of this command — the patches, the ZIPs and the package texts — is meant to leave the private lab; the game files it was built from never do.

### Prepare and publish the packages

Use a dedicated checkout of this public repository. Never push the history of a private development workspace into it. Import only the reviewed source changes; game files, private notes and test recordings stay outside this checkout.

Run the translation tests, `node --test source/installer/test_worker.cjs`, and `python3 .github/check_public.py`. The installer tests use synthetic files and require no ROMs or extra Node packages. Review the exact staged files with `git diff --cached` and check commit names and email addresses before committing. Use your public GitHub identity and its private noreply email, not a personal email or local computer name. Check every new commit, not only the final file tree.

Rebuild each advertised target using the exact inputs, verify its output fingerprint and test the affected behaviour. The [source builder](source/README.md) still uses English Plus 1.03 and the US/Italian references for the parts of the game that predate 1.2; 1.2 itself is rebuilt from 1.1 as described above. The 1.2 installer selects from 11 exact recognized inputs — unmodified US and Italian HeartGold, and English Plus 1.01 through 1.1 — and produces one of two outputs, IT or EN; there is no separate camera choice at this stage, since 1.2 has one camera scheme per language. Changing or adding an input requires a verified route and manifest fingerprints even when the resulting game stays identical. Before publishing, decode every recognized route and require the complete output hash and size to match the declared 1.2 fingerprint for that language. Verify file recognition, already-current handling, refusal of unknown inputs, and output validation before download.

Prepare one ZIP per language with the real patch files for that language, an installation guide, a document describing what 1.2 changes, README.txt, LICENSE, Manual and Cheats — no embedded browser installer. Check the language, game identity, exact member list and fingerprints against the release manifest before publishing. A documentation-only revision can reuse already reviewed patch bytes when their input and output fingerprints remain unchanged; it does not establish new gameplay test results. Check the contents and metadata of each ZIP, including PDFs and other attachments. Never upload a ROM or an entire build directory.

Create a draft under **Releases → Draft a new release**. Use a new version tag, attach the reviewed packages and write what changed, what remains unresolved and which input/save paths were checked. Mark previews as **pre-release**. Publish when the actual package has passed review, then download the uploaded assets and verify them again.

Never overwrite a released asset with different bytes. A correction needs a new release. Keep `README.md`, `PLAY.md`, `CHANGELOG.md` and the patch manifest consistent with the downloads.

### A future automation path

Automatic file checks and synthetic source tests are configured in [Public checks](.github/workflows/public-checks.yml). Keep the game build and playtesting in an isolated local environment with the required private inputs.

A separate, manually started packaging workflow could later validate approved patch files, assemble the guides and create a **draft** release for review. Publishing that draft would remain a deliberate maintainer action. Such a workflow would package already prepared patches; it would not build a new game from source. Full patch generation still needs the exact game inputs and is not implemented on GitHub here. Do not attach a personal development machine as a runner for untrusted pull requests.

For any workflow change, review its permissions and outputs, verify a successful run and update this guide to describe the behaviour available. [GitHub workflow triggers](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Community settings

Issues are for reproducible bugs; Discussions are for help and ideas. **Public checks** uses read-only repository permissions, pinned actions and no game files or repository secrets. Keep approval requirements for external contributors and keep private game tests and logs out of public output.

Keep `main` as the permanent branch. Use a temporary branch or a contributor's fork for each PR, then delete the temporary branch after merging. Keep version tags and release downloads; deleting a merged branch does not remove them.
