# Build and contribute

This folder is for developers. To play, use the [downloads and installation guide](../PLAY.md).

The source build recreates the released patch outputs from three locally supplied game inputs. Game files are never downloaded by the tools and must stay outside this repository.

## Prepare the inputs

| File in your private input folder | Required SHA-256 |
| --- | --- |
| `Pokemon - Sacred Gold Plus.nds` — 1.03 English | `78b198fbad961970ef8563587fb2278ee957e6297589a847dbe78f73d12cc0c1` |
| `Pokemon - HeartGold Version.nds` — US reference | `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105` |
| `Pokemon - Versione Oro HeartGold.nds` — Italian reference | `013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1` |

The builder currently needs all three inputs, including for English. Players applying a downloaded delta need only the matching 1.03 English input.

Use Python 3.9 or newer and install `ndspy` from `source/requirements.txt` in an isolated environment. Obtain the character mapping from the official reference source:

```sh
git clone https://github.com/pret/pokeheartgold.git ../pokeheartgold
git -C ../pokeheartgold checkout --detach 0985e8718df4f25e64d6507d89c0c97c0d288981
python3 -m pip install -r source/requirements.txt
```

## Build one variant

Run from this repository's root, replacing the example input and output paths with private locations outside it:

```sh
python3 source/translation/build_release.py \
  --rom-dir /path/to/private-inputs \
  --pret-source ../pokeheartgold \
  --recipe source/recipes/recipe-it.json \
  --ui-manifest source/ui/ui-localization-manifest-it.json \
  --camera plus \
  --output /path/to/private-output/game.nds
```

Use `en` in both recipe and UI filenames for US English. `--camera classic` means **Normal Angle**; `--camera plus` means **New Angle**. These internal names are retained from the builder. Existing outputs are refused.

The two recipe files combine the original message-bank files without changing their loaded content. Their internal historical release identifier does not determine the public release name. Compare the output against [the patch manifest](../patches/manifest.json).

## Make a change

`recipes` contains text changes and references to locally supplied game data. `ui` describes the selected interface resources. `translation` and `scripts` contain the builder and validation helpers. There is no retail text catalogue or complete game source tree here.

Change one issue at a time. Preserve message controls, argument counts and expected input data. A recipe preimage mismatch is a reason to stop and investigate, not to remove the check. For a new translation, start with a small agreed set of screens and test it in context.

```sh
python3 -m unittest discover -s source/translation -p 'test_*.py' -v
python3 .github/check_public.py
```

The synthetic tests do not require ROMs. They check building blocks; gameplay, save compatibility and performance require separate, described tests. Generated `.build.json` reports are private outputs and must not be committed.

For a new release, the maintainer generates deltas from the exact supported input using xdelta3 with application-header filenames disabled (`-A`), decodes each result and compares the full output hash. [Release procedure](../MAINTAINING.md).
