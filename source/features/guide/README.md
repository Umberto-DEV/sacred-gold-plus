# Summary hint suppression

This owner suppresses the automatic START Guide badge in the native Pokémon
Summary. It is separate from the field Guide and the optional Summary control
legend. The production recipe replaces 96 bytes inside the inherited Plus
ITCM payload, preserving its root, return path and text.

The [repeatable attribution case](../../docs/validation/summary-hint-source-rom-1.3.2.md)
connects the recipe to exact base/r4 EN/IT bytes, callers, state flags and
isolated entry/gate checks. It distinguishes opening the modal state from
rendering the three panels in normal gameplay.

`tools/attribuisci.py` reads final images without writing ROMs or saves.
`tools/applica_guida.py` and `source/sgp12/blocchi/guida.py` contain the original
machine-code recipe. `tools/rileggi_guida.py` compares a Guide-only intermediate image; its whole-image delta requirement is not a
final r4 acceptance criterion. The historical combined-guide C/build remains
in `source/native-guide/`; this case does not rebuild that payload.
