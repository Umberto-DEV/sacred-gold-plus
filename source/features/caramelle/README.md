# Repeat Rare Candy use

This owner returns to Pokémon selection after a Rare Candy when no evolution is
pending, the item/context remain valid, quantity remains and the party slot is
valid. Other paths retain native exit/action values. It does not decrement items
or alter save layouts itself.

[Exact source/ROM/caller attribution](../../docs/validation/candy-source-rom-1.3.2.md)
records current compilation, the complete256B owner, native parent revision and
language differences, ABI and isolated gate checks. It also records two repaired
false-success paths in the verification bench and the separate expanded-Bag
integration limitation.

`tools/compila.py` emits a fresh ELF/blob/canary and source/header/loader/builder/
compiler identity. `tools/attribuisci.py` requires that fresh build and exact
retail/base/r4 inputs. `test/banco.py` executes installed ROM bytes without
substitution; it models six external API transports. Return PC, SP, Thumb,
execution bounds and writes are checked in addition to result values.

Historical stage installers/readers remain intact. Their whole-image delta
constraints describe the Candy-only intermediate stage, not a final r4 image.
The two `ProveCaramellaBorsaIntegrate` tests need a capacity build matching the
current installed component; the old bundle does not satisfy that admission.
Do not bypass it or replace installed code to obtain a passing test.

Technical erratum in the preserved historical C commentary: the6-byte hook
rewrites `02081E96..02081E9B`, including the pop at1E9A. The unchanged skipped
range on that path is8B at1E9C..1EA3, rather than the10B stated in that comment.
This is a comment limitation, not a change to the installed instructions.

The [expanded-Bag dependency case](../../docs/validation/bag-quantity-source-rom-1.3.2.md)
closes the old-build admission gap with both source recipes and verifies actual
Medicine slots40/41 through native quantity and consume functions. The older
pocket0 integration fixture remains explicitly synthetic.
