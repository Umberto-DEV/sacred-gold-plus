# Find the project files

| What you want to edit | Where it lives |
| --- | --- |
| Current illustrated player guides and original manuals | [`guides/`](guides/README.md) |
| Guide lettering, layout and current-data readers | [`source/distribution/illustrated_guides.py`](source/distribution/illustrated_guides.py), [`legacy_style.py`](source/distribution/legacy_style.py), [`move_changes.py`](source/distribution/move_changes.py) |
| Localized installation and news documents | [`source/distribution/reference_docs.py`](source/distribution/reference_docs.py), [`source/localization/locales/`](source/localization/locales/) |
| GitHub project overview | [`README.md`](README.md) |
| Release-page source and screenshots | [`source/distribution/RELEASE-NOTES-TEMPLATE.md`](source/distribution/RELEASE-NOTES-TEMPLATE.md), [`images/`](images/) |
| Complete editable ZIP contents | `package/contents/Sacred Gold Plus 1.3.2/` after the [one-time preparation](package/README.md) |
| One-command ZIP composition | [`package/README.md`](package/README.md) |
| Fresh patch generation and exact release contracts | [`source/distribution/`](source/distribution/README.md) |
| Game features and their tests | [`source/features/`](source/features/README.md) |
| Build commands | [`source/README.md`](source/README.md) |
| Technical documentation and validation | [`source/docs/`](source/docs/README.md) |

`package/contents/` is the actual assembled player tree, including every patch,
guide, cheat and developer input. It stays local because the public repository
contains source and documentation, while the release hosts the assembled ZIP.
Edit its named documents, then run the composition command. The tool protects
all other payloads and regenerates the package inventories automatically.

`inputs/` contains private original ROM inputs. `local/` contains build tools,
verified game inputs, save fixtures, outputs and dated evidence; its private
README identifies the current paths. `release/` retains historical packages.
These folders are excluded from Git. A historical filename is not proof that a
file is disposable: build contracts and regression tests still use older inputs.

Existing source paths remain stable because historical reconstruction manifests
and exact game identities depend on them. Navigation and the package workspace
provide clear editing entry points without invalidating those contracts.
