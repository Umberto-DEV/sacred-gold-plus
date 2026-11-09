# Illustrated player guides

Current English gameplay guides use the original manuals' embedded lettering
and illustrations. Original files remain separately available for future edits.
Installation and news PDFs stay inside each language folder of the player ZIP.

| Current guide | Contents |
| --- | --- |
| [Pokemon Changes](current/Pokemon-Changes-1.3.2-EN.pdf) | Compact type, ability, stat and level-up changes |
| [Pokemon Locations](current/Pokemon-Locations-1.3.2-EN.pdf) | Original illustrated area lists with current fishing corrections |
| [Evolution Changes](current/Evolutions-1.3.2-EN.pdf) | Current altered evolution methods and conditions |
| [Important Item Locations](current/Items-TMs-1.3.2-EN.pdf) | Current TMs, evolution items and other important items |
| [Special Event Guide](current/Special-Events-1.3.2-EN.pdf) | Current instructions and the original illustrated walkthrough |
| [Move Changes](current/Move-Changes-1.3.2-EN.pdf) | All 52 changed moves, including types, power, accuracy, PP and effects |
| [Trainer Teams](current/Trainers-1.3.2-EN.pdf) | Base and optional Plus levels, items and moves |
| [Game Guide](current/Game-Guide-1.3.2-EN.pdf) | Current controls, settings and training features |

Magical Leaf is Ice-type in the actual game. The move guide explains this and
other inherited and later changes. It reports the actual values, including
cases which differ from familiar later-generation moves.

## Original manuals

These Drayano manuals are preserved byte for byte from the historical 1.2.3
package; the same bytes appear in the 1.2.4 packages. They are historical design
and content references. Use the current guides above for Plus rules.

- [Pokemon Changes](originals/Pokemon%20Changes.pdf)
- [Pokemon Locations](originals/Pokemon%20Locations.pdf)
- [Evolution Changes](originals/Evolution%20Changes.pdf)
- [Important Item Locations](originals/Important%20Item%20Locations.pdf)
- [Special Event Guide](originals/Special%20Event%20Guide.pdf)

The original manuals credit Drayano and, for location pictures, Serebii.net.
Original cover art, fonts and illustrated pages remain attributed to their
creators. The font helper reconstructs usable mappings from existing embedded
subsets in memory; no replacement font or separate font download is distributed.

## Maintain the documents

[`illustrated_guides.py`](../source/distribution/illustrated_guides.py) reads
authenticated current and retail inputs in memory. Original PDF inputs and
current generated PDFs are versioned here for direct reading on GitHub.
[`catalogue.json`](catalogue.json) pins each admitted PDF by size and SHA-256;
the public-file check still refuses arbitrary binary files.

After reviewing new PDFs, update the catalogue, copy the guides to the complete
[package workspace](../package/README.md), and compose a new ZIP. Technical
validation records exact candidate identities and coverage separately.

Regenerate into a new directory from your own exact current English game and
unmodified retail baseline:

```sh
PYTHONPATH=source .venv/bin/python source/distribution/illustrated_guides.py \
  --candidate /path/to/current-EN.nds --retail /path/to/retail-EN.nds \
  --charmap /path/to/pokeheartgold/charmap.txt \
  --location-notes source/distribution/documentation-1.3.2.json \
  --output /path/to/new-guide-candidate
```

The command authenticates the game and all five original PDFs before writing.
The [current document contract](../source/distribution/documentation-1.3.2.json)
records the selected game contract and output identities.
