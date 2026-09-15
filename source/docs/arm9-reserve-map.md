# ARM9 reserve map (1.2)

Human-readable view of `docs/arm9-reserve-map.json`, which is the file the tests actually
read. The JSON is the source of truth; this page is a summary of it.

## What the reserve is

Sacred Gold Plus places all of its native code and state in one region of the ARM9 autoload
section that the project owns outright:

| field | value |
|---|---|
| base | `0x023D8000` |
| end (exclusive) | `0x023E0000` |
| size | 32 768 B |

The upper bound is fixed by definition: `0x023E0000` is `HW_MAIN_MEM_MAIN_END`, and above it
sit the ARM7 work area and the ARM9/ARM7 shared area. The bound is held in practice by the
autoload section's base plus size (`0x023D8000 + 0x8000`).

The lower bound moved for 1.2: the arena-high literal at `0x020D2BB0` was lowered from
`0x023DEB40` (1.1) to `0x023D8000` (1.2). The literal at `0x020D2C64` (`mainex_lo`) is
unchanged and is *not* what holds the upper bound — on a 4 MiB console
`OSi_GetArenaLo(OS_ARENA_MAINEX)` returns early and never reads it. It is kept as a
non-regression check only.

The reserve is split in two zones:

| zone | range | bytes | rule |
|---|---|---:|---|
| 1.2 | `[0x023D8000, 0x023DEB40)` | 27 456 | new blocks stack upward from the base, each followed by a 16 B canary |
| 1.1 | `[0x023DEB40, 0x023E0000)` | 5 312 | no block moves and no block changes size; content changes only by the declared owner, only in the parts the register lists |

## Why it is a contended resource

Several independent work streams write into the same 32 KiB, and each of them is designed
against the same base addresses. Two things follow:

- "N bytes of section" is not "N bytes available". The section size, the occupied extent
  (how far the non-zero bytes reach) and the truly free space are three different numbers,
  and conflating them has already produced a situation where three ready features asked for
  more space than actually existed.
- Applying two features that were both designed against the same base is not safe in
  sequence: the first one changes what the second one expects to find.

## The two rules

1. **Anything with a public address anchors to the HIGH end (`0x023E0000`).** A public
   address is any address a user-visible artefact names: a shipped cheat code, or a literal
   that external material quotes. The low end moves every time a byte is added, so anything
   anchored low stops working at the next feature — and it does so by writing into live
   code, not by failing quietly. This has happened before: a cheat anchored near the low end
   kept its old address after the base was lowered by the next feature, and its writes
   landed inside executable bytes.
2. **Nothing new goes in without a register entry and an overlap check.** The entry goes
   into `docs/arm9-reserve-map.json` *before* a byte is written, in the same logical commit
   as the code that occupies it. The overlap check is automated and is run both before and
   after every applier.

Alignment is `0x100`. Every block closes with its own canary inside the block, never past
the block's end.

## Canaries

Each block is followed by a 16 B guard word pattern (`0xCA5A1nnn | index`, u32 LE). A 32 B
canary sits at the very base of the reserve, `0x023D8000`, because that is the first byte a
MAIN heap overflow meets after the base was lowered. Zone 1.1 keeps its own canary at
`0x023DEB40` with the older `0xCA5A0000…0xCA5A0007` pattern.

Checking the canaries after a run is part of applying a change: if a `0xCA5A….` word has
changed, something overflowed, and the check reports *which* block it was.

### Known limit: two pairs of canaries share a pattern

Measured on the shipped blobs (review R1, M9):

| region | address | pattern |
|---|---|---|
| `canarino.npc` | `0x023D8A00` | `0xCA5A1300` |
| `sgp.salvataggio +0xF0` | `0x023D8FF0` | **`0xCA5A1300`** |
| `sgp.anim +0x2F0` | `0x023D8DF0` | `0xCA5A1400` |
| `sgp.opzioni +0xFF0` | `0x023D9FF0` | **`0xCA5A1400`** |

The two patterns allocated since then are distinct: `sgp.opzioni.testi +0x3F0` uses
`0xCA5A1500` and `sgp.caramelle +0x0F0` uses `0xCA5A1600`.

Two guards with the same pattern cannot tell their two regions apart: `npc.rileggi` L5 and
`plus_chunk.rileggi` L6 would both stay green if the two 16 B guards were swapped, or each
written at the other's address; the same holds for anim and options. The guards still do their
main job — an overflow changes the words and the check names a block — but they do not
identify *which* of the two, and a check that reads only one of the pair cannot prove the other
is intact.

This is not a typo: it is a collision that stayed. Fixing it means changing sixteen bytes at
four addresses inside the reserve, so it changes the ROM: it belongs to 1.3, together with the
review of the patterns, not to a patch release that must rebuild byte for byte. Until then,
treat the two pairs as one guard each.

## Blocks allocated in 1.2

Zone 1.2 (`0x023D8000` upward):

| address | size | name | what it is | public |
|---|---:|---|---|---|
| `0x023D8000` | 32 | `canarino.basso` | base canary | no |
| `0x023D8020` | 32 | `intestazione` | `SGP2` header: magic, schema, base, end, 16 B fingerprint of the register's stable part | no |
| `0x023D8040` | 48 | `camera.eccezioni.1.2` | camera exception table (24 u16 LE entries, ascending) | no |
| `0x023D8070` | 16 | `canarino.camera` | canary | no |
| `0x023D8080` | 128 | `padding.allineamento.d1` | alignment padding, not assignable | no |
| `0x023D8100` | 2 048 | `sgp.plus` | Plus difficulty code and tables, plus the save-chunk code blob; 756 B used | no |
| `0x023D8900` | 256 | `sgp.npc` | NPC model cap; 160 B used (blob 144 B from 1.2.1, state 16 B) | no |
| `0x023D8A00` | 16 | `canarino.npc` | canary | no |
| `0x023D8A10` | 240 | `libero.1.2` | gap | no |
| `0x023D8B00` | 1 024 | `sgp.anim` | procedural battle animation (v4); block **full**, 1024/1024 | no |
| `0x023D8F00` | 256 | `sgp.salvataggio` | save chunk 32 B buffer plus canary (zero in ROM); 48 B used | no |
| `0x023D9000` | 4 096 | `sgp.opzioni` | Options page and the Continue prompt (v4); 4052 B used | no |
| `0x023DA000` | 2 048 | `sgp.wifi` | Wi-Fi per-service slot; 704 B used | no |
| `0x023DA800` | 1 024 | `sgp.opzioni.testi` | EN/IT text for the Options page (882 B EN, 940 B IT) | no |
| `0x023DAC00` | 256 | `sgp.caramelle` | Rare Candy stays in the party menu; blob 192 B plus a canary at `+0x0F0`. Also owns 6 bytes of static ARM9 at `0x02081E96` | no |
| `0x023DAD00` | 2 048 | `sgp.borsa` | full-stack gifts and pickups | no |
| `0x023DB500` | 2 048 | `sgp.anim2` | optional battle motion | no |
| `0x023DBD00` | 256 | `sgp.borsa_lotta` | battle item cache getter | no |
| `0x023DBE00` | 256 | `sgp.squadra_lotta` | battle move cache getters | no |
| `0x023DBF00` | 11 264 | `sgp.capacita_borsa` | expanded Bag code and state; state at +0x1800 | yes |
| `0x023DEB00` | 64 | `libero.1.2.finale` | free | no |

Zone 1.1, unchanged and frozen (`0x023DEB40` upward):

| address | size | name | what it is | public |
|---|---:|---|---|---|
| `0x023DEB40` | 32 | `canarino` | zone 1.1 canary | no |
| `0x023DEB60` | 12 | `padding` | padding | no |
| `0x023DEB6C` | 32 | `camera.eccezioni.dismessa` | retired camera exception table, kept byte-identical | no |
| `0x023DEB8C` | 84 | `camera.codice` | camera code (literal `0x0203B418`) | no |
| `0x023DEBE0` | 160 | `repellente.corpo` | repel fix body | **yes** (cheat guard) |
| `0x023DEC80` | 4 420 | `borsa.text` | Bag fix code | no |
| `0x023DFDC4` | 548 | `borsa.bss` | Bag fix state | no |
| `0x023DFFE8` | 20 | `buco` | hole, declared not assignable | no |
| `0x023DFFFC` | 4 | `camera.stato` | camera mode (1 = Plus, 0 = Classic) | **yes** (cheat) |

The zone 1.1 blocks hold the two public addresses in the project. They never move, and the
anchors their public consumers use are never touched.

Free space left in zone 1.2: 15 936 B contiguous at `0x023DAD00`, plus a 240 B gap at
`0x023D8A10`. It was 16 192 B until 1.2.1, when `sgp.caramelle` took the first 256 B from the
low end of the pool — anchoring low is allowed because nothing a user can see names that
address (no cheat, no literal quoted outside). Reservation procedure and the per-block internal headroom are in
`docs/arm9-reserve-reservations.md`.

Features that are *not* in the reserve — the title screen, the credit line and the guide
label — are listed in the register's `fuori_riserva` section so that a reader of the register
alone does not have to infer it.

## The machine-readable register

`docs/arm9-reserve-map.json` is the register. Top-level keys:

- `schema` — format version.
- `riserva` — base, end, size, and the arena literals, with the reason each bound is where it is.
- `zone` — the two zones, with their ranges and the rule that governs each.
- `blocchi` — one entry per block. Fields: `nome`, `base`, `bytes`, `proprietario`, `tipo`
  (`guardia` / `dati` / `codice` / `stato` / `padding` / `libero` / `reperto`), `zona`,
  `pubblico`, `assegnabile` (false marks space that is free but must not be handed out),
  `ancore` (each literal that points into the block, with its address and expected value),
  and a fingerprint — `sha256`, `sha256_atteso_a_zero`, or `impronte_parziali` for a partial
  one.
- `via_di_espansione` — the measured expansion options below `0x023D8000` and why each is
  not reachable in place.

The `SGP2` header written at `0x023D8020` carries the first 16 bytes of the sha256 of the
register's *stable part* only — `{schema, riserva, zone}` serialised as canonical JSON — so
that registering a new block does not change the header.

## Checking a ROM

Two tools, both under `source/`.

### `source/verifiche/test_riserva.py` — T1 to T5

| test | what it proves |
|---|---|
| T1 | Coverage: the zones cover the reserve, the blocks of each zone cover their zone, no pair of blocks overlaps, and the sizes add up. Pure Python, no ROM needed. |
| T2 | Every block with a declared fingerprint matches the bytes read from the ROM. A block with no fingerprint at all is reported, not silently passed. |
| T3 | Every anchor literal and every shipped public consumer lands inside the block that declares it, and the reserve has the declared base and size. |
| T4 | The reserve does not touch the heap: ArenaLo + the heap total + FNT + FAT + an 8 KiB margin stay below the reserve base. |
| T5 | The `SGP2` header written at `0x023D8020` agrees with the register. |

T1 always runs. **T2 to T5 skip when no ROM is given**, each with an explicit reason. Setting
`SGP_RISERVA_COMPLETA=1` turns a missing ROM into a failure instead of a skip, which is what
you want in CI so that an all-skipped run is not mistaken for a green one. T2 to T5 need
`ndspy` (`source/requirements.txt`); T1 does not.

Run from `source/`:

```sh
python3 -m unittest verifiche.test_riserva -v
SGP_RISERVA_ROM=<your rom.nds> python3 -m unittest verifiche.test_riserva -v
```

The register the tests read is `docs/arm9-reserve-map.json`; override it with `SGP_MAPPA`.
The shipped cheat files T3 checks are read from the folder named by `SGP_CHEATS` (the unpacked release ZIP); without it, T3 is skipped.

### `source/verifiche/riserva_arm9.py` — layout report

Reads the autoload section out of a ROM and prints the three numbers that get confused:

- **size** of the section;
- **occupied**, that is how far the non-zero bytes reach;
- **truly free**, the sum of the register's blocks that are typed `libero`, marked
  assignable, and actually zero in the ROM — not a zeroed tail minus a hard-coded constant.

Blocks that are zero at rest but are state, padding or guard space are *not* free, and a
`libero` block the register marks `assegnabile: false` is excluded too.

Run from `source/`:

```sh
python3 verifiche/riserva_arm9.py <your rom.nds>
python3 verifiche/riserva_arm9.py <your rom.nds> --manifest docs/arm9-reserve-map.json
```

The path used to be written `../docs/arm9-reserve-map.json`, which from `source/` is the
repository root, where there is no `docs/` folder: the command ended in a traceback. On the
shipped 1.2.1 EN ROM the corrected command reports **16 176 B assignable** — the 15 936 B
contiguous block plus the 240 B gap — and exits 0.

Without `--manifest` the tool prints the zeroed tail and states explicitly that the true free
space is unknown, rather than printing a zero that looks like a verdict. It exits non-zero if
a register block falls outside the section.

## The build input is a different file

`source/sgp12/build/riserva/MAPPA-RISERVA-ARM9.json` is **not** the register. It is a
separate, frozen build input consumed by `sgp12.costruisci` when it lays down the reserve
block. It is part of the reproducible build: editing it casually breaks the byte-identical
rebuild. Register changes go in `docs/arm9-reserve-map.json`.
