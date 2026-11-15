# Native growth-table read inside the EXP caller

This case continues the [personal-data/EXP chain](native-personal-caller-source-rom-1.3.2.md).
The first growth-table read now executes the installed native parser in the
same initialized trainer31 caller CPU. The table bytes themselves feed the
native lookup and EXP setter, followed by all six Pokémon and caller return.
Other185 Normal/187 Plus ReadWhole calls remain explicit models. No gameplay
source, ROM, save layout, ABI or identifier is changed.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Qualify the404-byte payload bound rather than silently extending a108-byte
profile. Derive the direct caller's real saved registers, frame and volatile
residues again. Distinguish the getter's curve4 from a deliberately altered
reader member2; they test different links. A register-only counter must start
from the baseline RAM and stack preimage. Account for observer-only writes to
already-freed memory, with exact source-proven ranges rather than a broad mask.
Independently review addresses, ABI, transport, consumer and counter evidence.

## Il materiale più grezzo da cui partire

Use your own exact r4 ROM and retained/reproduced project objects from the
[parent input/build guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
ROM SHA-256 identities: EN `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`,
IT `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
Whole-image identity takes precedence over the IT image's inherited header.
No ROM, extracted growth table, save, BIOS, Pokémon packet or RAM dump is shipped.

FNT `a/0/0/3` is FAT file132:3348 bytes,8 members, whole SHA-256
`ce5c612e32e537da3cdf7808c3f21ab217e83a75ead56027d98a7d84bb1b55d6`.
The **entire archive** and both selected404-byte members are identical across
retail→base1.1→V4→r4 in both languages. This is inherited data, not a new patch
or proof of an original native compiler recipe.

Current EN/IT archive ROM offset is `0x003AE600`. BTAF starts16,size76;
BTNF starts92,size16; GMIF starts108. Manual FAT/FNT/NARC arithmetic and ndspy
agree:

| Member | BTAF row | Start/end | Archive offset | Current ROM offset | SHA-256 |
| --- | ---: | --- | ---: | --- | --- |
| 4, positive | 60 | 1616/2020 | 1732 | `0x003AECC4` | `d57547b2a55109f3b92e6c4214dc79c8f92688205f7460e7fe868c3c363012af` |
| 2, counter | 44 | 808/1212 | 924 | `0x003AE99C` | `f3a821d7e60596706c3194766b2f9e87795d45450712432a8a8399b41c5ee1e7` |

The reader's actual current table route is literal `0x02007520→0x0210F210`,
row3=`0x0210F21C→0x0210F1D8`, yielding `a/0/0/3`. Retail IT uses its own
`0x0210F1B0→0x0210F1BC→0x0210F178` route. All eight images have the same103
qualified reader instruction starts. Historical compressed/autoload sections
are decoded without inventing direct physical code offsets for those images.

The source counterpart is `LoadGrowthTable` and `GetExpByGrowthRateAndLevel`
in the reference `src/pokemon.c` pinned at `cb614ad23449d5852b40321dc409c4143872b35c`;
see the [native reader provenance](native-narc-reader-source-rom-1.3.2.md).
Reference names support qualified semantics. Original native MW objects and
compiler are unavailable; project object/readback correspondence comes from
the linked Plus build recipes and is checked again without new compilation.

## I metodi e gli strumenti da usare

[Verifier](../../features/trainer-strategy/tools/attribuisci_crescita_chiamante.py),
[profile/adapter](../../features/trainer-strategy/test/growth_narc_bench.py),
[portable checks](../../features/trainer-strategy/test/test_growth_narc_bench.py)
and [receipt replay](../../features/trainer-strategy/test/test_growth_caller_attribution.py)
compose this reader without changing qualified parents. Nine authenticated
source recipes plus a Close counter recipe preserve complete parent functions
and enumerate exact edits. NARC3/member4 is the positive domain, member2 an
explicit negative control. The FS service cap changes108→404 only in this
isolated profile; destination/file/cursor bounds and exact request checks remain.

```text
native personal byte19 → getter curve4
 → GetExpByGrowthRateAndLevel0206FD30
   → LoadGrowthTable0206FD14
     → direct BL at0206FD28 → ReadWhole02007508 → parser0200732C
     ← actual reader return0206FD2C
   → native LDR table[level]0206FD5C
 ← EXP0206DF7A → native SetBoxMonData attribute8 →0206DF86
 → six Pokémon → original seed restore → caller return
```

This direct call differs from the earlier personal-data tail. At reader entry,
`R0=arena+448`, `R1=3`, `R2=4`, `R3=OTIDlow`. R3 is not `0x02007509`.
Saved R4..R7 are table,curve4,curve4,`0xFFFF0000`; R8..R11 retain caller cookies.
R12 is arena+216, derived from the preceding nickname copy. LR=`0x0206FD2D`.
`LoadGrowthTable` pushes `{r3,r4,r5,lr}`,16 bytes: its entry SP is inner−304,
reader SP is inner−320. The reader adds136 bytes, reaching552 below outer SP;
its56-byte guard ends at608. Capture the actual preexisting frame and reconstruct
17 native stores/six metadata read writes over it. No standalone setup, new CPU,
register reset, frame initialization or output bridge is used.

Native normal return has R1=table,R2=404,LR=`0x02007409`; the old model left
R1=3,R2=curve4,LR=`0x0206FD2D`. The wrapper POP restores R5=level before the
lookup. The lookup must retain getter curve4 in R6 while receiving the actual
reader residues. The declared volatile-register control may leave R1/R2/IP
clobbered; those values are recorded rather than normalized back to the model.
Native reader R0 is ignored by the actual caller's next index calculation.
Current resident ARM9 physical offset is RAM−`0x02000000`+`0x4000`, e.g.
`0x0206FD28→0x73D28` and reader `0x02007508→0xB508`.

The native parser selects its own raw member through five opaque FS services.
Expected SET seeks are12,20,96,row60/44,payload1732/924. Reads are12/2,20/4,
24/2,96/4,row/4,row+4/4,payload/404. Final cursors are2136 and1328. No host-selected
404-byte member copy is supplied at the old high-level boundary. The remaining
185/187 original backends run once each; no artificial growth read event or
body model is inserted. Native header55, party56, personal2/355, messages and
six species names retain their separate owners.

## Reproduce

Use the parent's qualified Python3.14/ndspy4.2.0/Unicorn2.1.4/Capstone5 environment
and retained project objects. No emulator installation, ROM build, save or BIOS
is needed. Keep outputs outside `source`, and use fresh output names.

```sh
python source/features/trainer-strategy/tools/attribuisci_crescita_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" --readback-only \
  --json "$PRIVATE_OUTPUT/growth-readback-EN.json.gz"
python source/features/trainer-strategy/tools/attribuisci_crescita_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" \
  --json "$PRIVATE_OUTPUT/growth-caller-EN.json.gz"
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_growth_narc_bench.py
SGP_GROWTH_CALLER_ROM_DIR="$ROMS" \
SGP_GROWTH_CALLER_REPORT_DIR="$PRIVATE_OUTPUT" \
SGP_REMATCH_OBJECT_DIR="$REMATCH_CASE" \
SGP_STRATEGY_OBJECT_DIR="$STRATEGY_CASE" \
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_growth_caller_attribution.py
```

Repeat for IT. Replay naming follows the
[parent directory convention](native-party-caller-source-rom-1.3.2.md#reproduce-with-your-own-inputs).
Optionally add all three `--retail "$RETAIL" --base "$BASE11" --v4 "$V4"`
inputs to either mode for that language's four-image lineage. Readback mode
qualifies code/objects/routes/raw data without constructing an emulated CPU.
Bound commands to180s,1GiB OS RSS and2MiB logs; allow16MiB case output,1GiB peak
disk and10GiB free afterwards. Guest bound is3M hooks/608-byte stack. OS high-water
RSS/report size are checked; use an external wall-time/log limiter and one heavy
producer at a time.

## Counterproofs, observation and limits

The final20 executions passed, ten per language. Eight portable tests and nine
exact-input replay tests passed without skips. Independent raw/source/ABI,
counter and final EN/IT reviews found no unresolved blocker. All eight positive
parties, prepared Trainer52, final seeds and entire final4MiB main-RAM hashes
match the preceding case, with117 extra observed hooks. This is finite bench
equivalence under the named models, not a natural-game result.

EN took89.653s/581877760 bytes OS peak RSS; IT91.493s/591118336 bytes. Replay
took8.976s/701399040 bytes. Four-image readback took1.918s EN/1.957s IT, with
OS peaks221626368/227524608 bytes and no emulated CPU. The readback branch
avoids constructing unused runtime resource fixtures. The matrix has Plus0/1 × two
seeds, a second poison, two OFF pairs, one new FS volatile control and two
counterproofs per language. Observed EN totals are1040343 Normal/1056570 Plus;
IT adds34. Prefix604/638 remains unchanged, with117 extra hooks from replacing
one callback fetch with118 reader/FS fetches.

OFF has an additional lifetime effect: the personal44-byte buffer was freed
before this read. The constructor audit poisons it with `DD` only when ON;
the original OFF free leaves the raw personal bytes. Compare actual free and
allocation events/preimages. For this phase, project exactly eight8-byte
allocation canaries64B plus the dead44B,108 bytes total. Preserve every gap;
keep per-run freeze over everything except the reader's192-byte stack scope
and live404-byte destination. Do not treat dead-memory observer poison as a
new native mutation or mask the whole heap.

Close omission can preserve party/output while leaving an open file ledger.
Its real residual LR=`0x02007403` must reach the lookup instead of being replaced
with the old model LR. The separate wrong-member control changes only R2=4→2
at the reader entry, after the native caller prepared4. Getter result and R6
remain4. Native metadata arithmetic must now select member2, yielding EXP20974
instead of19511 for Plus29; later species-growth reads retain4, so level29 and
all statistics remain unchanged. The first packet is independently predicted
by changing only decrypted EXP, recomputing checksum and re-encrypting; all five
other packets must match. Normal27's16140 versus15746 is a source/raw prediction,
not an additional executed negative profile.

Both counter pre-states must equal the baseline RAM,136-byte frame,56-byte guard
and zeroed404-byte destination. Wrong member may change only the recorded entry
R2; allowing a coordinated fake preimage/hash would defeat the counter's premise.
First-name scope hashes precede the mutation and remain equal. Only later25
whole-RAM name-scope hashes may be excluded for the predicted changed Pokémon;
all name bytes, writes, ABI, lifetime and neutral transitions stay checked.

Documented provenance, project binary readback, finite native semantic execution
and initialized activation remain separate claims. Native FS/heap internals,
other reader calls, original native compiler reconstruction, natural encounters,
card I/O, full battle, UI, save/restart and hardware are outside this proof.
No game correction, speedup or recovered memory is claimed. Any production
error-policy or optimization change needs its own maintainer decision and checks.


On both languages the Close control has the same whole reader-phase RAM and
final4MiB main-RAM hash as its baseline, while its file ledger stays open and
its actual residual LR differs. Wrong member2 instead changes the delivered
404-byte table and reader-phase RAM before the predicted EXP/packet difference;
getter curve4 and later five packets remain intact.

| Conclusion | Evidence and limit |
| --- | --- |
| Documented provenance | Whole growth archive and members4/2 inherited unchanged across eight exact images; direct native caller and source counterpart identified. |
| Reconstructed binary correspondence | Retained project object/payload readback remains verified; no new compilation or original native MW reconstruction. |
| Demonstrated semantics | Native metadata selection and404-byte delivery, actual table lookup/EXP setter, complete valid packets and independently predicted wrong-table counter. |
| Observed activation | Initialized trainer31 caller, Plus0/1/two seeds/two poisons; Plus1/default-seed controls and counterproofs. |
| Unattributed links | Five native FS services, native heap,185/187 other ReadWhole calls, other formats/IDs/errors and natural/device execution. |
