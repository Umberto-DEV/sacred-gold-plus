# Review and publish

## Approve a contribution

Open **Pull requests**, choose the contribution and read its explanation. In **Files changed**, check that it contains only the intended work and no private information. Read the tests and known limitations; try the affected game behaviour when needed.

Use **Review changes → Request changes** if something needs correcting, or **Approve** when it is ready. Resolve outstanding conversations, verify the local test results and use **Squash and merge**. Main requires an owner review for collaborator changes; administrators can handle their own changes when working alone, but must perform the same checks.

This repository currently runs its checks locally, before publication. It does not yet have an active GitHub Actions workflow. If one is added later, a message saying **workflows awaiting approval** will mean permission to run tests, not approval of the code or release. [GitHub's guide](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks).

## Add a collaborator

People can already open issues, join discussions and submit pull requests through a fork. Direct access is only needed for a trusted ongoing collaborator.

Open **Settings → Collaborators → Add people**, enter their GitHub username and send the invitation. A personal repository gives collaborators write access, so check the account carefully and retain the owner-review requirement. Remove access when it is no longer needed. An organization is an option later if the project needs more granular team roles. [GitHub's instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository).

## Publish an update

Use a dedicated checkout of this public repository. Never push the history of a private development workspace into it. Import only the reviewed source changes; game files, private notes and test recordings stay outside this checkout.

Run the source tests and `python3 .github/check_public.py`. Review the exact staged files with `git diff --cached` and check commit names and email addresses before committing. Use your public GitHub identity and its private noreply email, not a personal email or local computer name. Check every new commit, not only the final file tree.

Rebuild each advertised variant using the exact inputs, verify its output fingerprint and test the affected behaviour. Prepare one ZIP per language and camera containing only the patch, plain instructions, credits and file checks. Check the contents of each ZIP and the patch metadata. Never upload a ROM or an entire build directory.

Create a draft under **Releases → Draft a new release**. Use a new version tag, attach the reviewed packages and write what changed, what remains unresolved and which input/save paths were checked. Mark previews as **pre-release**. Publish when the actual package has passed review, then download the uploaded assets and verify them again.

Never overwrite a released asset with different bytes. A correction needs a new release. Keep `README.md`, `PLAY.md`, `CHANGELOG.md` and the patch manifest consistent with the downloads.

## Community settings

Issues are for reproducible bugs; Discussions are for help and ideas. The file checks and synthetic source tests run locally without game files. If GitHub Actions is added later, use read-only permissions, require approval for external contributors and keep private game tests, secrets and logs out of its public output.
