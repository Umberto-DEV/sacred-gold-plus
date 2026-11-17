# Training menu advance checks

This read-only checker has two finite profiles. The default `stat7` checks
seven labels in banks 385, 557 and 630 and three matching stat menus per
script. `service6` checks six labels in the two Mart service scripts 858 and
942, corresponding to banks 557 and 630; it checks one matching main menu in
each. Bank 385 is not claimed as a six-choice caller. Each profile checks its
own window templates and script mapping. The service catalogue aliases are
385:21 and 385:24–28, and may have other uses outside this check.

Both profiles accept only the known overlay 27 renderer and font 4, pin selected
native dispatch/menu-handler spans and overlay 1, and measure advances in
96-pixel windows. Script patterns do not by themselves prove live reachability.
The checker rejects mismatched aliases and unsupported glyphs or controls. It
reports advance width, not pixel ink bounds or a visual/runtime result.

Use Python with the pinned `ndspy` dependency from `source/requirements.txt`.
Supply your own ROM and charmap; neither is distributed here. Prepare a local
identity JSON, for example `{"language":"DE","rom_sha256":"<64 lowercase hex>"}`,
from the build receipt and independently verify that the receipt identifies
that ROM and language. The identity asserts the language; this tool cannot
independently detect language from the shared game executable.

```
PYTHONPATH=source python -m localization.training_fit --rom /path/to/game.nds \
  --charmap /path/to/charmap.txt --identity /path/to/identity.json --language DE \
  --profile service6 --catalogue source/localization/locales/DE/messages.json > /path/to/report.json
PYTHONPATH=source python -m unittest localization.test_training_fit
```

Run both profiles to check both families; use `--profile stat7` for the stat menu.
For regional coverage, record both profiles for every relevant language and
the exact image identity of each cell. A pass in one language does not cover
another. Distinguish retained historical reports from fresh scans, and do not
extend these two profiles to other menu families or layouts.

The native pins qualify a specific binary path, not a complete source build or live execution.

The catalogue is optional and is only a proposal. `installed` comes exclusively
from the ROM, so a corrected catalogue cannot conceal an installed overflow.
Exit 0 means all requested advance checks pass; 1 means a measured overflow;
2 means an input, identity or qualification error. Each invocation writes a
new JSON report to stdout. A different renderer or font must be requalified,
not treated as a 96-pixel pass. Ink and clipping require a separately qualified
font-4 pixel renderer; even a 95/96 advance is not proof of visual fit.
