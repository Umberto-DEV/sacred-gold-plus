# Native payload support and attribution

This owner contains the earlier Plus/save/NPC/Wi-Fi C payloads, their compiler,
ARM harnesses and provenance checks. Current release composition also uses
other feature owners; this directory is not the entire native game source.

The [native move-getter case](../../docs/validation/native-move-callers-1.3.2.md)
adds a portable read-only tool for exact r4 EN/IT. It connects observed native
calls to their installed caller branches, exercises the max-PP switch and
checks the type-icon refresh predicate without distributing game data:

```sh
python3 source/features/native-core/tools/attribuisci_getter_mosse.py \
  --rom "$ROM_EN" --language EN --json "$PRIVATE_OUT/native-moves.json"
```

The optional `--trace` argument accepts a previously authenticated Work Party
CSV (or lossless `.gz`). Authenticate the observer and OFF/ON neutrality
separately; a CSV does not establish its own provenance. No game, save, default
or persistent layout is modified by this check.

Run the existing synthetic/compiled payload suite with:

```sh
python3 -m unittest discover -s source/features/native-core/test \
  -p test_qualita.py -v
```

It reports compiler-identity and private-data skips explicitly. Its successful
host contracts do not imply acceptance of an arbitrary ROM or every game path.
Some older investigation scripts in `tools/` retain historical workspace
placeholders and are source references rather than portable entry points.
The current standalone tool above does not depend on those placeholders.
