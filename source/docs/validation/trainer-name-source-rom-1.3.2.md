# Packed trainer names and the native copy boundary

Trainer21 IT has nine decoded characters, but its producer representation is
an eight-word packed vector including EOS. Treating the decoded vector as the
native String would incorrectly predict a capacity failure. This case verifies
raw message provenance and two native copy APIs; it does not execute the outer
lazy loader or a natural encounter.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Distinguish encrypted bytes, decrypted packed words, expanded glyph codes and
String.size. Follow both source and installed instructions before choosing a
fixture. Test the hypothesis by retaining packed and expanded representations
as separate inputs, with independent decoders, exact destinations and native
branch evidence. Review addresses, ABI, lifetime and counterproofs independently.

The initial static capacity hypothesis was rejected: it used expanded length
where the native lazy producer retains packed words. No gameplay fix follows
from that hypothesis. A source correspondence is distinct from executing the
whole producer, and successful copying does not establish rendering behavior.

## Il materiale più grezzo da cui partire

Use your own exact retail, inherited base1.1, v4 and r4 images identified in the
[lineage case](rematch-source-rom-1.3.2.md). Current r4 EN is152786844B,
SHA-256`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT159029760B,
SHA-256`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Full hashes establish language/revision; the IT internal header alone does not.
Keep ROMs, raw messages, String buffers and detailed reports private.

NARC27 is `a/0/2/7`, member729, with738 entries. Current EN bank14042B,
SHA-256`1be3c74b6cdea6cdb8028947c1187d63fda815163b507b7ff6c2df0ba7efb68b`,
physical`08F8CD40`; IT14132B,
SHA-256`1509b5a410db3e7d9e7c269687d8fe8d6d7b684acff75bce8fe15e7af7a4e6d0`,
physical`0956CF3C`. Base1.1→v4→r4 banks are identical per language despite
relocation. Retail whole banks differ, but selected21/31 decrypted vectors
match their later counterparts. This establishes selected content continuity,
not the unavailable original authoring recipe for other messages.

| Record | Raw words including EOS | Expanded words including EOS | Native size |
| --- | ---: | ---: | ---: |
| EN21 | 5 | 6 | 4 |
| IT21 | 8 | 10 | 7 |
| EN31 | 5 | 6 | 4 |
| IT31 | 6 | 7 | 5 |

IT21 raw16B SHA-256
`ff9a444adf90563af3be48c0581f767613d94faf43bdf3a013c3a89a2e5861b9`;
EN21 raw10B SHA-256
`013e05da38137427d409c0b13b27df24d22deeac8aa420f59f5628a1d175928d`.
The report retains encrypted allocation offsets, payload offsets, hashes and
both representations. No extracted names are included in this repository.

Native HGSS reference is pinned to
`cb614ad23449d5852b40321dc409c4143872b35c`:
[msgdata.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/msgdata.c),
[pm_string.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pm_string.c),
[trainer_data.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/trainer_data.c).
`EnemyTrainerSet_Init` at`020733C0` calls the loader at`02073426`, then
`CopyStringToU16Array` at`02073430` with capacity8. Its176B code/alignment/pool
span at physical`000773C0` has SHA-256
`76912054c0a5f1183697cc83d7fa853fffd712b1620b9b6054e06314968e867b`.
The loader`0200BBA0` dispatches lazy`0200B9F8`, allocates String capacity from
MAT.length, decrypts raw words and calls`02026A04` without expanding F100.
These source/byte correspondences do not reconstruct the original compiler.

String ABI: u16 capacity at+0, u16 size at+2, magic at+4, data at+8.
`CopyU16ArrayToStringN` (`02026A04`, physical`0002AA04`) copies length*2 bytes
and derives size from the first outer EOS. `CopyStringToU16Array`
(`02026A68`, physical`0002AA68`) copies (size+1)*2 only when it fits.
Their ARM memcpy is`020E5AD8`, physical`000E9AD8`. The verifier binds exact
code windows, literal pools, ARM/Thumb state and independent physical readback.
Neither function returns a status: R0 is not an oracle. R4–R11/SP are preserved.

## I metodi e gli strumenti da usare

Reuse the [owner](../../features/trainer-strategy/README.md),
[verifier](../../features/trainer-strategy/tools/attribuisci_nome.py) and
[tests](../../features/trainer-strategy/test/test_name_attribution.py).
Prepare the Python environment as described in the
[test bench](../test-bench.md#linking-source-to-an-exact-rom): tested Python3.14.7,
ndspy4.2.0, Capstone distribution5.0.9 (module version5.0.7), Unicorn2.1.4. No compiler, BIOS, emulator installation,
ROM build or original save is needed. From the repository root:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_nome.py \
  --language IT --rom /path/to/own-r4-IT.nds \
  --retail /path/to/own-retail-IT.nds --base /path/to/own-base11-IT.nds \
  --v4 /path/to/own-v4-IT.nds --json /path/to/private/fresh-name-IT.json
```

Repeat for EN with corresponding inputs. Existing files/aliases and outputs
under source are refused. Reports are bounded2MiB. Two independent bank decoders
must agree before expansion. A valid String_New header/allocation is an explicit
host fixture: capacity=MAT.length, size0, magic, initial EOS and spare fixtureword.
The guest then executes CopyN→CopyTo on the **same String RAM**, with no host
payload rewrite between APIs. Raw input stays readonly; String mutations belong
to CopyN, destination writes to CopyTo. Borrowed String is not freed by these APIs.
Outer heap/FS/decryption/loader/destructor and caller preparation remain outside
executed coverage, even where source correspondence is documented.

Each language checks21/31 packed and expanded, two synthetic boundary lengths,
an expanded-capacity counterfactual and a short-capacity counterfactual:8 paths.
Six primary paths have paired observer OFF/ON with identical functional RAM and
registers. Capacity8 copies the IT21 packed16B. Expanded IT21 has size9 and takes
the native refusal path; capacity10 with its own20B destination is a calibration,
not a proposed change to the16B Trainer field.

Capacity refusal calls actual GF_ASSERT`0202551C`. With explicit CommState0 at
`021D4150`, predicate`02037D78` returns0 and assertion returns normally: one
assertion, no destination write. Nonzero communication and invalid magic/pointer
paths are excluded; an assertion is not assumed to abort. Strict PC/read/write
maps,128B stack bound, saved-register cookies, complete frozen unrelated RAM,
canaries and10k instruction bound check both APIs. Observed max is282instructions
and24B stack across these finite paths, not hardware WCET or speedup evidence.

Five executed negative calibrations per language reject skipped copy, wrong
return, live communication, literal-pool execution and oversized write into a
smaller destination. Replay also rejects wrong representation, missing native
calls/writes/PCs, changed destinations, absent assertion and register clobber.
The initial replay exposed two oracle details now covered: LDRSB values in
Unicorn write events retain32-bit sign extension, and requiring only a subset of
PCs could miss an omitted final memcpy return. Captured guest bytes were correct;
producer snapshots and failures are retained privately without rewriting history.

To replay with your generated reports named `name-EN.json`/`name-IT.json`, place
symlinks `r4-EN.nds`/`r4-IT.nds` in a private directory, then:

```sh
SGP_NAME_ROM_DIR=/path/to/private/rom-links \
SGP_NAME_REPORT_DIR=/path/to/private/reports \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_name_attribution.py
```

Eight test methods passed with no skips using both exact inputs. Independent
review checked raw resources, source/native correspondence, ABI and counterproofs.
This proves finite binary identity and copy semantics/activation inside isolated
APIs; natural encounters, complete lazy-loader execution, rendering/consumer use,
full caller lifetime, saves and hardware remain unqualified. No game behavior,
ROM, ABI, IDs or save format changed. The next reusable step is upstream caller
preparation with actual packed name provenance; capacity/overflow fixes would
require evidence from the real producer and consumer, plus maintainer decision.
