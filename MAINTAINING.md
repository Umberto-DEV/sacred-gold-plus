# Review and publish

## Approve a contribution

Open **Pull requests**, choose the contribution and read its explanation. In **Files changed**, check that it contains only the intended work and no private information. Read the tests and known limitations; try the affected game behaviour when needed.

Use **Review changes → Request changes** if something needs correcting, or **Approve** when it is ready. Resolve outstanding conversations, verify the local test results and use **Squash and merge**. Main requires an owner review for collaborator changes; administrators can handle their own changes when working alone, but must perform the same checks.

This repository currently runs its checks locally, before publication. It does not yet have an active GitHub Actions workflow. If one is added later, a message saying **workflows awaiting approval** will mean permission to run tests, not approval of the code or release. [GitHub's guide](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks).

## Add a collaborator

People can already open issues, join discussions and submit pull requests through a fork. Direct access is only needed for a trusted ongoing collaborator.

Open **Settings → Collaborators → Add people**, enter their GitHub username and send the invitation. A personal repository gives collaborators write access, so check the account carefully and retain the owner-review requirement. Remove access when it is no longer needed. An organization is an option later if the project needs more granular team roles. [GitHub's instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

## Publish an update

### What happens automatically?

| Action | Result in this repository today |
| --- | --- |
| Push a commit or merge a PR | Updates the repository files. It does not build patches or publish a release. |
| Add a version tag | Marks a commit. It does not run a build or create our four download packages. |
| Open a release page | GitHub offers **Source code (zip)** and **Source code (tar.gz)** archives of the tagged repository. These are not the player packages. |
| Publish a prepared release | Makes the attached patch packages and release notes available for players. |

There are currently no GitHub Actions workflows in this repository. Automated release notes, source archives, automated tests and building downloadable patches are separate features. [About GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

### Prepare and publish the packages

Use a dedicated checkout of this public repository. Never push the history of a private development workspace into it. Import only the reviewed source changes; game files, private notes and test recordings stay outside this checkout.

Run the source tests and `python3 .github/check_public.py`. Review the exact staged files with `git diff --cached` and check commit names and email addresses before committing. Use your public GitHub identity and its private noreply email, not a personal email or local computer name. Check every new commit, not only the final file tree.

Rebuild each advertised variant using the exact inputs, verify its output fingerprint and test the affected behaviour. Prepare one ZIP per language and camera containing the patch, Readme and Game Info files, credits, licence, file checks and the reviewed Extras references. The Preview 2 layout has 16 files per package; treat that as the current release format, not a fixed requirement for every future version. Check the contents and metadata of each ZIP, including PDFs and other attachments. Never upload a ROM or an entire build directory.

Create a draft under **Releases → Draft a new release**. Use a new version tag, attach the reviewed packages and write what changed, what remains unresolved and which input/save paths were checked. Mark previews as **pre-release**. Publish when the actual package has passed review, then download the uploaded assets and verify them again.

Never overwrite a released asset with different bytes. A correction needs a new release. Keep `README.md`, `PLAY.md`, `CHANGELOG.md` and the patch manifest consistent with the downloads.

### A future automation path

Start with automatic file checks and synthetic source tests on pushes and pull requests. These can run without game files. Keep the game build and playtesting in an isolated local environment with the required private inputs.

A separate, manually started packaging workflow could later validate approved patch files, assemble the guides and create a **draft** release for review. Publishing that draft would remain a deliberate maintainer action. Such a workflow would package already prepared patches; it would not build a new game from source. Full patch generation still needs the exact game inputs and is not implemented on GitHub here. Do not attach a personal development machine as a runner for untrusted pull requests.

Before enabling any workflow, review its permissions and outputs, verify a successful run and then update this guide to describe the behaviour actually available. [GitHub workflow triggers](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Community settings

Issues are for reproducible bugs; Discussions are for help and ideas. The file checks and synthetic source tests run locally without game files. If GitHub Actions is added later, use read-only permissions, require approval for external contributors and keep private game tests, secrets and logs out of its public output.
