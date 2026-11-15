# Native trainer messages: encrypted archive to copied name and destruction

This case executes five native APIs in one CPU/RAM context: lazy MsgData
creation, packed String production, copy to an eight-word destination, String
deletion and MsgData destruction. It closes a specific boundary of the
[packed-name case](trainer-name-source-rom-1.3.2.md) and
[complete trainer31 caller](trainer-caller-source-rom-1.3.2.md), whose message
producer bodies were modeled. Those earlier reports retain their original scope.
This standalone result does not establish a combined caller/message execution.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Follow the encrypted bytes through table and payload decryption, native writes
to MsgData/String and both destructors. A correct destination alone does not
prove that the installed producer ran or that its temporary allocation died.
Separate code, pools and modeled SDK services; require exact ABI, instruction
coverage, allocation ownership and counterproofs. Review the raw instructions
and source independently before accepting runtime observations.

## Il materiale più grezzo da cui partire

Supply your own exact images. The whole-image hash identifies language/revision;
an internal game code or similar function name is insufficient.

| Input | EN SHA-256 / bytes | IT SHA-256 / bytes |
| --- | --- | --- |
| HeartGold retail | `65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105` / 134217728 | `013d04f5512b01ad98735a5f850dc039f0ee80bc57035b3a10e8b650be690ce1` / 134217728 |
| Inherited Plus1.1 | `281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d` / 127104144 | `7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077` / 131906120 |
| Plus1.3 V4 | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` / 147345256 | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` / 153228136 |
| Plus1.3.2 r4 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` / 152786844 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` / 159029760 |

Preparation of the existing images belongs to the
[project build instructions](../../README.md) and linked attribution cases.
Keep ROMs, extracted archives, reports and reference checkout local. No save,
BIOS, message text, extracted binary or retail fixture is distributed here.

Native source correspondence uses HGSS reference commit
`cb614ad23449d5852b40321dc409c4143872b35c`:
[msgdata.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/msgdata.c),
[pm_string.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/pm_string.c),
[filesystem.c](https://github.com/ctrl-cheeb-del/pokeheartgold/blob/cb614ad23449d5852b40321dc409c4143872b35c/src/filesystem.c).
Their SHA-256 values are respectively
`2fcd674561c88d39615407f204d21fab4420b5de9506e4fc78651b1c67a1c8d2`,
`051bd1380bec7d261c8d5772a0ae77cdb46a7531d74c5d0be4a5f6cb90433e82`,
`ee526fc2835b2c2259dd393087fb1a5ca036dbf467bcfbd7735b1476819c869d`.
This is inherited native HGSS code. Original compiler/linker objects are
unavailable: no original C-to-object reconstruction is claimed or attempted.
Plus compilation/composition attribution remains in the owner cases.

ARM9 code uses the decoded section map, independently checked against physical
ROM reads. In V4/r4 these uncompressed resident spans map as
`ROM offset = RAM address - 02000000 + 00004000`. Retail/base comparisons use
decoded sections without inventing compressed physical offsets. The ordinary
code spans are identical in seven input images; retail IT has a different
native layout and its corresponding addresses remain unattributed.

These spans reside in ARM9, with no overlay load or new payload insertion in
this case. The existing Plus composition inherits them from its input image;
the seven-image equality checks establish zero byte delta in the qualified
code spans through retail/base→V4→r4 where addresses are attributed. The current
trainer strategy installer changes the separately documented constructor hooks
and Plus owner, rather than recompiling these message routines. Decoded ARM9
sections handle the inherited compression/autoload mapping; physical offsets
above are asserted only for independently readable V4/r4 spans.

| API/helper | RAM entry | r4 physical entry |
| --- | --- | --- |
| NewMsgDataFromNarc | `0200BAF8` | `0000FAF8` |
| NewString_ReadMsgData | `0200BBA0` | `0000FBA0` |
| Lazy native producer | `0200B9F8` | `0000F9F8` |
| String_New | `02026354` | `0002A354` |
| CopyU16ArrayToStringN | `02026A04` | `0002AA04` |
| CopyStringToU16Array | `02026A68` | `0002AA68` |
| String_Delete | `02026380` | `0002A380` |
| DestroyMsgData | `0200BB44` | `0000FB44` |
| ARM memcpy | `020E5AD8` | `000E9AD8` |

The upstream native caller is `EnemyTrainerSet_Init` at`020733C0`: BL sites
`020733D2` and`02073426` reach NewMsgDataFromNarc and NewString_ReadMsgData;
its suffix destroys the message after trainer construction. Earlier caller
proofs record those high-level services as models. Here the explicit five-API
driver supplies heap11/type LAZY/bank729 and IDs21/31 directly, so caller state
and natural encounter conditions are not silently inherited as runtime evidence.

The verifier lists each qualified subspan, byte count, hash and physical offset
in `locations`. Eight new ordinary Thumb windows total332B/153 starts, plus75
previously qualified starts for copy/deletion/ARM memcpy:228 starts altogether.
Literal pools at`0200BAC8`, `02026378`, `02026A60`, `02026AA0`, `020263A4`
are data. Branches to DIRECT, fallback, allocation failure and invalid objects
are excluded; observed code cannot extend the admitted map automatically.

The archive is NARC27 `a/0/2/7`, bank729. The SDK path table independently
links pool`02007708`→table`0210F210`, row27`0210F27C`→path`0210F118`.
Bank EN14042B is at physical`08F8CD40`, SHA-256
`1be3c74b6cdea6cdb8028947c1187d63fda815163b507b7ff6c2df0ba7efb68b`;
IT14132B at`0956CF3C`, SHA-256
`1509b5a410db3e7d9e7c269687d8fe8d6d7b684acff75bce8fe15e7af7a4e6d0`.
Its header specifies738 entries/key`D00E`. Independent FAT/FNT/NARC and ndspy
readback agree; two source decoders agree on packed and expanded vectors.

The native producer reads three **encrypted** slices: header4B at0, table8B
at`4+8*ID`, and payload`2*N` bytes at its decrypted offset. Table mask is
`(key*765*(ID+1))&FFFF`, duplicated across32bits. Payload seed is
`((ID+1)*596947)&FFFF`, then XOR each u16 and advance18749 modulo65536.
Those operations execute installed instructions; the host never writes decoded
MsgData, String fields or name words after entry.

| Language / ID | Packed words including EOS | Payload bank offset / bytes |
| --- | ---: | --- |
| EN21 | 5 | 6142 / 10 |
| IT21 | 8 | 6150 / 16 |
| EN31 | 5 | 6248 / 10 |
| IT31 | 6 | 6262 / 12 |

MsgData is12B, with type1/heap11/NARC27/file729 and opaque handle. Native
String_New allocates`2*N+10`, writes capacity N, size0, magic and initial EOS;
native CopyN fills packed data and size N−1. The final spare u16 is untouched
heap content. IT21 has size7 and fits capacity8; substituting expanded text
would describe a different input. CopyTo borrows the String pointer and copies
through outer EOS. The destination tail remains unchanged.

## I metodi e gli strumenti da usare

Use the [owner](../../features/trainer-strategy/README.md),
[verifier](../../features/trainer-strategy/tools/attribuisci_messaggi.py),
[tests](../../features/trainer-strategy/test/test_message_attribution.py) and
[bench dependencies](../test-bench.md#linking-source-to-an-exact-rom).
Qualified environment: Python3.14.7, ndspy4.2.0, Unicorn2.1.4; Capstone package
5.0.9 reports module5.0.7. CPU model is Unicorn default17/Cortex-A15, retaining
the [qualified hook-width contract](trainer-caller-source-rom-1.3.2.md).
This does not establish full console hardware fidelity. No compiler is invoked.

From repository root, replace paths with your own inputs and fresh output:

```sh
python3 source/features/trainer-strategy/tools/attribuisci_messaggi.py \
  --language EN --rom /path/to/own-r4-EN.nds \
  --retail /path/to/own-retail-EN.nds --base /path/to/own-plus11-EN.nds \
  --v4 /path/to/own-v4-EN.nds --json /path/to/private/messages-EN.json.gz
```

Repeat for IT. Existing outputs/aliases and source-directory outputs are
refused. `.gz` selects deterministic gzip; other suffixes receive JSON.
Uncompressed output is bounded2MiB. Run one producer at a time, with180s,
1GiB RSS,2MiB log and8MiB case budgets; allow1GiB peak disk growth while retaining
at least10GiB free. Actual campaigns took about1.8s/language; OS peak RSS stayed
below1GiB (777322496B EN,804241408B IT). No ROM rebuild, capture or duplicate image is needed.

The five outer calls preserve SP and R4–R11 without restoring them between
APIs. Arguments are `(1,27,729,11)`, `(msg,ID)`, `(str,dest,8)`, `(str)` and
`(msg)`. Only Heap_Alloc`0201AA8C`, Heap_AllocAtEnd`0201AACC`,
Heap_Free`0201AB0C`, NARC_New`02007688`, NARC_ReadFromMember`0200782C`
and NARC_Delete`0200770C` are modeled. Their actual bodies do not execute.
The NARC token is opaque; its native84B filesystem object is not simulated.

Native read BLs`0200BA0C/BA26/BA70` pass `(handle,729,offset,size,dest)`;
dest is the fifth stack argument at SP=outerSP−56. Three heap allocations are
Msg12B, String`2*N+10`, temporary`2*N`. Temporary free at`0200BAAC` precedes
producer return; String dead-magic store`02026398` precedes free`0202639C`;
NARC deletion`0200BB60` precedes Msg free`0200BB66`. Every allocation has
canaries and freed-buffer poison. Guarded reads require live objects; unrelated
4MiB RAM and RNG remain unchanged. Static and observed maximum stack is80B
under a128B guard; finite run budget is20k instructions.

The oracle checks all228 native starts,11 SDK entries,5 nested native helpers,
five API returns and per-API liveness. It compares the entire ordered native
write transcript:38 stack stores plus`11+5*N` object/decrypt/copy stores,
including raw MAT decryption values. Hook counts are`217+34*N`:387 EN21/31,
489 IT21 and421 IT31. These are emulator hook counts, not performance timings.
Final RAM digests/freeze are producer evidence; replay does not reconstruct
4MiB RAM from a digest. Native object fields and writes are recomputed from
independent raw resources and source contracts.

Each language runs six positive cells (IDs21/31 × heap00/C7/39), two paired
observer OFF controls and two0/ones void-R0 controls. Copied output stays stable;
String spare follows heap fill. Defined pointer returns are checked; void R0
is not interpreted as status. Four completed counterproofs change the cipher
scratch, skip one XOR, skip output memcpy or omit temporary free. The leak
keeps the correct name but fails ownership. Five partial counterproofs skip
NARC deletion/invalidation, change read destination, enter a pool or return to
the wrong PC. Each must fail at its predicted stage, not any arbitrary error.

For the two compressed reports and private exact-ROM links named
`r4-EN.nds`/`r4-IT.nds`:

```sh
SGP_MESSAGE_ROM_DIR=/path/to/private/rom-links \
SGP_MESSAGE_REPORT_DIR=/path/to/private/reports \
python3 -m unittest discover -s source/features/trainer-strategy/test -p test_message_attribution.py
```

Eleven methods passed with both languages and no skips. Independent review
found a replay false green that ignored forged stack records; an archived
before/after calibration now requires exact stack writes and interleaving.
Counter replay also rejects unrelated failure causes. Original reports and
producer snapshots remain private and immutable; later pure-oracle checks do
not imply a new CPU campaign. Public tools/tests contain no extracted fixtures.

Documented provenance and native byte identity are established for these spans;
finite source-semantic correspondence and API activation are demonstrated under
the declared models. Original binary reconstruction, native heap/FS bodies,
full caller composition with this producer, general message/error paths,
natural encounter, rendering, SAVE/cold restart and physical hardware remain
outside coverage. No game source, ROM, save layout, ABI, ID or setting changed.
