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
| Add a version tag | Marks a commit. It does not run a build or create our four download packages. |
| Open a release page | GitHub offers **Source code (zip)** and **Source code (tar.gz)** archives of the tagged repository. These are not the player packages. |
| Publish a prepared release | Makes the attached patch packages and release notes available for players. |

Automated release notes, source archives, the **Public checks** tests and building downloadable patches are separate features. [About GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

### Prepare and publish the packages

Use a dedicated checkout of this public repository. Never push the history of a private development workspace into it. Import only the reviewed source changes; game files, private notes and test recordings stay outside this checkout.

Run the translation tests, `node --test source/installer/test_worker.cjs`, and `python3 .github/check_public.py`. The installer tests use synthetic files and require no ROMs or extra Node packages. Review the exact staged files with `git diff --cached` and check commit names and email addresses before committing. Use your public GitHub identity and its private noreply email, not a personal email or local computer name. Check every new commit, not only the final file tree.

Rebuild each advertised variant using the exact inputs, verify its output fingerprint and test the affected behaviour. The [source builder](source/README.md) still uses English Plus 1.03 and the US/Italian references. The player installer selects from four exact supported inputs: unmodified US HeartGold and English Plus 1.01, 1.02 and 1.03. Its language and camera are fixed by the chosen ZIP. Changing or adding an input requires a verified route and manifest fingerprints even when the resulting games stay identical. Before publishing, decode all 16 routes and require complete output hashes and sizes to match the existing four 1.04 builds. Verify file recognition, automatic route selection, already-current handling, refusal of unknown inputs, and output validation before download. Test the actual generated HTML offline, preserving the distinction between automated logic tests, browser GUI checks and Android tests.

Prepare one ZIP per language and camera with one **Install-or-update.html**, README.txt, LICENSE, Manual and Cheats. The HTML contains the four verified routes for that target, the required browser decoder components and their licence. It must process files locally without network requests or ROM uploads. Keep the 16 individual deltas in the public repository for advanced manual use, not as extra ZIP members. The 1.04 layout has 13 files: six unchanged original references plus Game Guide.txt and Project Notes.txt in Manual, and two files for the same seven optional cheats in Cheats (MCH and XML). Project Notes combines credits, the changelog and file checks. Check the language, game identity, exact member list and fingerprints against the release manifest. A documentation-only revision can reuse already reviewed patch bytes when their input and output fingerprints remain unchanged; it does not establish new gameplay test results. Check the contents and metadata of each ZIP, including PDFs and other attachments. Never upload a ROM or an entire build directory.

Create a draft under **Releases → Draft a new release**. Use a new version tag, attach the reviewed packages and write what changed, what remains unresolved and which input/save paths were checked. Mark previews as **pre-release**. Publish when the actual package has passed review, then download the uploaded assets and verify them again.

Never overwrite a released asset with different bytes. A correction needs a new release. Keep `README.md`, `PLAY.md`, `CHANGELOG.md` and the patch manifest consistent with the downloads.

### A future automation path

Automatic file checks and synthetic source tests are configured in [Public checks](.github/workflows/public-checks.yml). Keep the game build and playtesting in an isolated local environment with the required private inputs.

A separate, manually started packaging workflow could later validate approved patch files, assemble the guides and create a **draft** release for review. Publishing that draft would remain a deliberate maintainer action. Such a workflow would package already prepared patches; it would not build a new game from source. Full patch generation still needs the exact game inputs and is not implemented on GitHub here. Do not attach a personal development machine as a runner for untrusted pull requests.

For any workflow change, review its permissions and outputs, verify a successful run and update this guide to describe the behaviour available. [GitHub workflow triggers](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Community settings

Issues are for reproducible bugs; Discussions are for help and ideas. **Public checks** uses read-only repository permissions, pinned actions and no game files or repository secrets. Keep approval requirements for external contributors and keep private game tests and logs out of public output.

Keep `main` as the permanent branch. Use a temporary branch or a contributor's fork for each PR, then delete the temporary branch after merging. Keep version tags and release downloads; deleting a merged branch does not remove them.
