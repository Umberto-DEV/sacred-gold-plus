# ARM9 reserve — reservations

How to claim space in the ARM9 reserve for a new feature. The layout itself, the canary
mechanism and the checking tools are described in `docs/arm9-reserve-map.md`; the register is
`docs/arm9-reserve-map.json`.

## The rule that makes this a queue

No feature picks its own address. Addresses are handed out from one place, in one order, and
a feature reads the address it has been given from the reservation table below. Two features
that each choose "the first free block" both choose the same block.

The register is the truth; this page is the queue in front of it. The entry goes into
`docs/arm9-reserve-map.json` with the address written here, in the same logical commit as the
code that occupies it, and the state here is updated at the same time.

## Claiming space

1. Work out the size you need, rounded up to the `0x100` alignment, and include your canary
   in it. A block's canary lives *inside* the block, not past its end.
2. Take the next address from the reservation table below and add a row for it, with the
   state `reserved`.
3. Add the matching entry to `docs/arm9-reserve-map.json` before writing a single byte.
4. Run the overlap check before and after the applier:
   `python3 verifiche/riserva_arm9.py <rom.nds> --manifest docs/arm9-reserve-map.json`
   (from `source/`; the path used to be written `../docs/…`, which does not exist), and the register tests:
   `python3 -m unittest verifiche.test_riserva -v`.
5. Verify the canaries after the run. A changed `0xCA5A….` word means something overflowed,
   and the tool names the block.
6. Update the register entry with the real fingerprint and set the state here to `applied`.

## Naming

Blocks that hold a feature are named `sgp.<name>`, lowercase, with the feature's public name:
`sgp.plus`, `sgp.npc`, `sgp.anim`, `sgp.opzioni`, `sgp.wifi`, `sgp.salvataggio`. A block that
holds only data belonging to another block appends a qualifier: `sgp.opzioni.testi`. Guard
blocks are `canarino` or `canarino.<owner>`; alignment gaps are `padding.*`; unallocated
space is `libero.*`.

## What a reservation entry declares

Every entry, both in the table here and in the register, states:

- **address** — the start, aligned to `0x100`;
- **size** — in bytes, canary included;
- **owner** — who is responsible for the bytes; only the declared owner may change them;
- **anchor** — high or low (see below);
- **public** — yes if any shipped artefact names an address inside the block;
- **fingerprint** — the sha256 of the block's content as written, or an explicit "expected
  zero" fingerprint, or a partial fingerprint over the bytes that are stable. A block with no
  fingerprint at all cannot be verified, and the register check reports that rather than
  passing it.

Entries also list their **anchors**: every literal elsewhere in the ROM that points into the
block, with the address of the literal and the value it must hold. The anchor check is what
catches a block that was moved without its pointers being updated.

## Anchoring

A block with a public address **anchors to the high end**, `0x023E0000`. The high end is
fixed; the low end moves down every time a feature is added.

This is not a style preference. A cheat once anchored near the low end of the reserve kept
working right up to the moment the next feature lowered the base. After that, the address the
cheat had been shipped with no longer pointed at the data it was written for — it pointed
into live code, and the cheat's writes corrupted it. The failure was a runtime crash some
distance away from the cause, and it cost a day to find. Everything without a public address
anchors low and stacks upward from the base; everything with one lives in the frozen zone at
the top, which never moves and never changes size.

## Lowering the base

If the free space is not enough, the base is lowered. Two constraints:

- **One lowering at a time.** Not one per feature that needs room — one, covering all of
  them, in a written order.
- **Preimages are re-derived at each step.** Appliers designed against the same base will
  fail on the second step, because the first step has already changed the bytes they search
  for. Each step's preimage hashes are taken from the output of the previous step, not from
  the original.

Below `0x023D8000` the base is not reachable in place: the ROM padding before the overlay
table is smaller than the section growth a lower base would require, so a lower base needs
the overlay table and FAT moved first. The measured options are in the register's
`via_di_espansione` section.

## Reservation table

Zone 1.2, `0x023D8000` upward. All blocks are non-public.

| block | address | size | end (excl.) | used | state |
|---|---|---:|---|---|---|
| header + base canary | `0x023D8000` | `0x40` | `0x023D8040` | 64/64 | applied |
| camera exceptions + canary | `0x023D8040` | `0x40` | `0x023D8080` | 64/64 | applied |
| alignment padding | `0x023D8080` | `0x80` | `0x023D8100` | — | not assignable |
| `sgp.plus` (Plus difficulty code and tables, save-chunk blob) | `0x023D8100` | `0x800` | `0x023D8900` | 756/2048 | applied |
| `sgp.npc` + canary (NPC model cap) | `0x023D8900` | `0x200` | `0x023D8B00` | 288/512 | applied |
| `sgp.anim` (procedural battle animation, v4) | `0x023D8B00` | `0x400` | `0x023D8F00` | 1024/1024 — **full** | applied |
| `sgp.salvataggio` (save chunk buffer + canary) | `0x023D8F00` | `0x100` | `0x023D9000` | 48/256 | applied |
| `sgp.opzioni` (Options page + Continue prompt, v4) | `0x023D9000` | `0x1000` | `0x023DA000` | 4052/4096 | applied |
| `sgp.wifi` (per-service Wi-Fi slot) | `0x023DA000` | `0x800` | `0x023DA800` | 704/2048 | applied |
| `sgp.opzioni.testi` (EN/IT Options page text) | `0x023DA800` | `0x400` | `0x023DAC00` | 882 EN / 940 IT of 1024 | applied |
| `sgp.caramelle` (Rare Candy stays in the party menu) | `0x023DAC00` | `0x100` | `0x023DAD00` | 208/256 | applied |
| `sgp.borsa` (capped gifts and pickups) | `0x023DAD00` | `0x800` | `0x023DB500` | 2048 B reserved | integrated in 1.2.1 |
| `sgp.anim2` (continuous battle motion, v5) | `0x023DB500` | `0x800` | `0x023DBD00` | 2048 B reserved | integrated in 1.2.1 |
| `sgp.borsa_lotta` (Bag cache in battle) | `0x023DBD00` | `0x100` | `0x023DBE00` | 162/256 | applied |
| `sgp.squadra_lotta` (party move cache in battle) | `0x023DBE00` | `0x100` | `0x023DBF00` | 200/256 | applied |
| `sgp.capacita_borsa` (expanded Bag capacity) | `0x023DBF00` | `0x2C00` | `0x023DEB00` | 3184/11264 | applied |
| free (`libero.1.2.finale`) | `0x023DEB00` | `0x40` | `0x023DEB40` | — | **free** |

Zone 1.1, `0x023DEB40` to `0x023E0000`, is frozen: no block moves, no block changes size,
and the two public addresses it holds are never touched. It is not open for reservation.

### Free space

As of 18/09/2026, recomputed from `docs/arm9-reserve-map.json` (sum of the blocks typed
`libero` with `assegnabile: true` — the two `.md` pages used to disagree with the register and
with each other; the register is the source of truth):

- **304 B total**, in two disjoint blocks — nothing here is contiguous with anything else.
- **64 B** at `0x023DEB00` (`libero.1.2.finale`), up to the zone 1.1 canary at `0x023DEB40`.
  What used to be free from `0x023DBD00` has since been taken by `sgp.borsa_lotta` (256 B),
  `sgp.squadra_lotta` (256 B) and `sgp.capacita_borsa` (11 264 B), on top of the 256 B for Rare
  Candy, 2048 B for capped gifts and 2048 B for continuous battle motion already taken before
  this page's previous revision.
- **240 B** at `0x023D8A10` (`libero.1.2`), between the NPC canary and `sgp.anim`. Usable only
  for something that fits in it whole.
- Headroom inside blocks already allocated belongs to their owners, not to the free pool. The
  largest is 1 344 B in `sgp.wifi`; `sgp.plus` has 464 B free at `+0x630` and 236 B of growth
  margin at `+0x314`; `sgp.salvataggio` has 208 B. `sgp.anim` is full and any change to it
  has to fit in 1024 B or take a new block.

Alignment padding (`0x023D8080`, 128 B) and the zone 1.1 hole (`0x023DFFE8`, 20 B) are marked
not assignable in the register and are excluded from every free-space figure, including the
one `source/verifiche/riserva_arm9.py` reports.
