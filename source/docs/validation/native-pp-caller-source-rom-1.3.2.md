# Native move PP through a borrowed stack buffer

This case extends the [initial friendship caller](native-friendship-caller-source-rom-1.3.2.md)
through the first **custom trainer move** PP lookup. Native file metadata selects
move310, the real16-byte stack buffer feeds the getter, and native arithmetic
and setter write the first Pokémon's PP. The complete trainer31 caller returns
with six valid Pokémon and its original seed. Other183 Normal/185 Plus
ReadWhole calls remain explicit models. No game code, ROM or save is changed.

## Cosa farebbe un professionista di alto livello che non sto chiedendo

Identify the actual caller before choosing a matching resource ID. Move310 is
read earlier during default learning and again in the custom trainer loop;
those occurrences have different frames and purposes. Derive the borrowed
buffer, saved registers, guard and lifetime from source and installed bytes.
Follow source/recipe→bytes/readback and ROM→caller→source in both directions.
Separate raw resource evidence from a counter's predicted semantic result.
Use an independent review of ABI, counterproofs and exact memory projections.

## Il materiale più grezzo da cui partire

Use your own exact r4 EN/IT ROM and project objects from the
[parent build/input guide](native-party-caller-source-rom-1.3.2.md#il-materiale-più-grezzo-da-cui-partire).
EN:152786844 bytes,SHA-256
`2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d`;
IT:159029760 bytes,SHA-256
`13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a`.
The IT image retains an English native header; textual language does not imply
native language constants or addresses. Runtime resources are read from the
actual image. Keep ROMs, extracted data, Pokémon packets, full RAM, saves and
BIOS private; none are included here.

Logical NARC11 is FNT `a/0/1/1`, FAT file140. Current EN/IT archive is at
`0x01093800`,11356 bytes,471 members, SHA-256
`beed8ddf861e575b9c38dfa65a6c0c51fb237305ddd73c393f5e2009fbc75260`.
BTAF starts16,size3780; BTNF3796,size16; GMIF3812,data3820.
Member310's row2508 contains start4960/end4976, giving archive offset8780
and physical ROM `0x01095A4C`. Its16 bytes have SHA-256
`85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8`.
The PP byte is offset6,physical `0x01095A52`,value15. Manual FAT/FNT/NARC
arithmetic and ndspy agree. The471 archive records and468-record battle-cache
prefix are different counts, as qualified in the
[move provider case](wonder-guard-source-rom-1.3.2.md#actual-archive-and-context-data).

The actual current path is literal `0x02007520→0x0210F210`,
row11=`0x0210F23C→0x0210F198→a/0/1/1`. Retail IT instead uses
`0x0210F1B0→0x0210F1DC→0x0210F138`. The
[offline lineage reader](../../features/trainer-strategy/tools/rileggi_pp.py)
authenticates retail→base1.1→V4→r4 separately per language. All eight images
have identical member310 and PP15, and the same172-byte native code/data window
at `0x02073314`, SHA-256
`99de7e2671a8c7730c644f2164710140e845378654db6072a88c5ad004289026`.
The whole archives differ: retail SHA
`654d7edd0b0be66f6189ee87026dd701a2b8d98afa19a3991c8417803c50faea`,
base/V4 SHA `744e04cad9270122e7961042a5e554461fc56169bd928940878fa465b8d810e4`,
r4 SHA above. Member equality does not imply whole-provider equality.
Historical compressed/autoload code is read through decoded sections, without
inventing physical offsets. No historical activation is claimed.

The source counterparts are `move.c::LoadMoveEntry`, `GetMoveAttr`,
`GetMoveTblAttr`, `GetMoveMaxPP`, and
`pokemon.c::MonSetMoveInSlot`/`BoxMonSetMoveInSlot`, called by the type3 loop
in `trainer_data.c`. Reference fork/pin are the same as the
[native reader provenance](native-narc-reader-source-rom-1.3.2.md):
`ctrl-cheeb-del/pokeheartgold`,commit `cb614ad23449d5852b40321dc409c4143872b35c`.
`MoveTbl` is16 bytes; `MOVEATTR_PP` is5 while its byte offset is6.
Original native MW compiler/objects remain unavailable. This proves source
correspondence, installed-byte execution and finite semantics; it does not
reconstruct the original native binary build. Retained Plus module/stub and
teams ELF objects, their toolchain recipes and installed readback are rechecked
through the linked parent verifier; no compiler or full ROM build is invoked.

## I metodi e gli strumenti da usare

[Verifier](../../features/trainer-strategy/tools/attribuisci_pp_chiamante.py),
[adapter](../../features/trainer-strategy/test/pp_narc_bench.py),
[portable tests](../../features/trainer-strategy/test/test_pp_narc_bench.py)
and [exact-input replay](../../features/trainer-strategy/test/test_pp_caller_attribution.py)
reuse the qualified parents. Eight authenticated function recipes and a Close
recipe check complete source hashes and exact edit occurrence counts. The35
runtime source identities include this tool and adapter. Parents remain unchanged.

```text
CreateMon returns02073A16
 → trainer custom slot0 BL02073A32 → MonSetMoveInSlot020714E8
   → veneer → BoxMonSetMoveInSlot020714F0
   → set move54; get PP-Up62 =0
   → GetMoveMaxPP0207332C(move310,0)
     → GetMoveAttr02073314(move310,attr5)
       → LoadMoveEntry020733B0 → native ReadWhole02007508/parser0200732C
       ← actual return02073320, borrowed16 bytes at SP
       → native LDRB02073390 reads byte6=15
     ← getter → u8 PP + floor(PP*20*0/100) →15
   → local byte → SetBoxMonData0206ED70(attr58)
     → native STRB0206F0FE writes BlockB+8,slot0 PP
 ← actual setter return0207152A → trainer return02073A36
 → other moves/capsule/form/owned helper → PartyAdd → six Pokémon/caller return
```

The earlier default-learnset310 occurs before CreateMon returns, with reader
SP=inner−392 and different saved registers. It is excluded. Selecting it would
incorrectly predict a624-byte stack peak. The custom role requires the first
native call `0x020714E8` with MON,310,slot0 and LR=`0x02073A37`, after the actual
CreateMon checkpoint and before the owned helper/PartyAdd. A matching move ID
or a historical event index alone is insufficient.

Outer SP=`0x023BF000`,inner=outer−96. The custom call starts at inner−152;
BoxMonSetMove pushes32 bytes, GetMoveMaxPP16, GetMoveAttr24. Reader SP and
destination are both inner−224=`0x023BEEC0`. Entry R0=SP,R1=11,R2=310,
R3=`0x02007509`; R4..R7=[5,0,MON,0],R8..R11 are caller cookies,R12=0,
LR=`0x02073321`. Derive R12 from the preceding CreateMon/caller path;
the division happens later. The reader adds136 bytes, reaching456 below outer;
its56-byte guard ends at512. Existing full-caller608/3M-hook bounds remain.

The56 guard bytes are read both before and after the parser and compared byte
for byte, in addition to the original write/freeze checks.

Frame `[SP−136,SP)`, immutable guard `[SP−192,SP−136)`, payload `[SP,SP+16)`
and saved caller pair `[SP+16,SP+24)` are distinct. Capture real preimages;
never initialize this buffer or place a heap canary at SP−8. Protect all upper16
bytes, including saved slot0/R4 and LR=`0x0207333D`. The existing CPU is borrowed
without setup, register resets, result bridges or artificial read events.
Reconstruct17 native stores and six FS metadata writes over the actual frame;
the final FS copy delivers only the16-byte live payload. The five opaque FS
services remain models. Expected seeks are12,20,3800,2508,8780; reads are
12/2,20/4,24/2,3800/4,2508/4,2512/4,8780/16.

The22-point consumer trace binds frames/callee-saved state and specific argument,
return and instruction transitions. At the PP load, the complete before/after
register vectors differ only in R0. The24-byte switch table
`[0x02073364,0x0207337C)` is data; its attr5 row leads to `0x02073390`.
A linear disassembler's apparent instructions there are not execution admission.
Native reader residues such as R2=16 and LR=`0x02007409` are preserved through
actual caller instructions, rather than normalized to the old model's residues.
Declared FS volatile clobbers are checked separately.

The PP setter uses attr58 and local pointer inner−184. Its internal frame is
still inner−304 at STRB `0x0206F0FE`: unlike the friendship setter, ADDSP80 occurs
**after** this store. The full store ABI, before15,value15/1,BlockB+8 and
flags0 are checked. R3=`0x0206ED8D` comes from this setter's decryption path;
friendship's R3 is not reused. Decode a full236-byte packet only after setter
return, when flags0/checksum are valid. Current physical code offsets use
RAM−`0x02000000`+`0x4000`,e.g. getter `0x77314`,load `0x77390`,store `0x730FE`.

## Reproduce with your own inputs

Use the parent's qualified Python3.14,ndspy4.2.0,Unicorn2.1.4 and Capstone5
environment. The inherited qualified Unicorn model17 is the bench configuration;
ARM946 hardware behavior and timing remain outside this evidence. Retained/reproduced objects follow the linked parent build recipe.
No save, BIOS, emulator installation or full ROM build is needed. Use fresh
output names outside `source` and retained object directories.

```sh
python source/features/trainer-strategy/tools/attribuisci_pp_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" --readback-only \
  --json "$PRIVATE_OUTPUT/pp-readback-EN.json.gz"
python source/features/trainer-strategy/tools/attribuisci_pp_chiamante.py \
  --rom "$ROM" --language EN --objects "$REMATCH_OBJECTS" \
  --strategy-object "$STRATEGY_OBJECTS/teams.o" \
  --json "$PRIVATE_OUTPUT/pp-caller-EN.json.gz"
python source/features/trainer-strategy/tools/rileggi_pp.py \
  --retail "$RETAIL" --base "$BASE11" --v4 "$V4" --rom "$ROM" \
  --language EN --json "$PRIVATE_OUTPUT/pp-lineage-EN.json"
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_pp_narc_bench.py
SGP_PP_CALLER_ROM_DIR="$ROMS" SGP_PP_CALLER_REPORT_DIR="$PRIVATE_OUTPUT" \
SGP_REMATCH_OBJECT_DIR="$REMATCH_CASE" SGP_STRATEGY_OBJECT_DIR="$STRATEGY_CASE" \
python -m unittest discover -s source/features/trainer-strategy/test \
  -p test_pp_caller_attribution.py
```

Repeat for IT. Replay uses `r4-EN.nds`/`r4-IT.nds`, reports `pp-caller-EN.json.gz`/
`pp-caller-IT.json.gz`,object subdirectories `public-build-EN/IT` and
`build-EN/IT/teams.o`,as in the
[parent convention](native-party-caller-source-rom-1.3.2.md#reproduce-with-your-own-inputs).
Readback and lineage modes construct no emulated CPU. Bound commands to180s,
1GiB OS high-water RSS,2MiB logs,16MiB case output and1GiB peak disk; keep10GiB
free after peak. Use an external wall/log limiter and one producer at a time.

## Verified results

Final20 executions passed,ten per language,on one frozen verifier/adapter.
Twelve portable tests and eleven exact-input replay tests passed without skips.
Independent raw/source,Driver,counter-scope,lineage and final EN/IT reviews
found no unresolved blocker. Replay testing exposed the missing explicit guard
after-image; the final producer now records56 actual bytes and checks equality
and width before/after. Earlier matrices and interrupted diagnostics remain
separate private evidence.

The matrix covers Plus0/1×two seeds,another stack poison,two OFF pairs,a volatile
FS control and two counters per language. Controls/counters use Plus1 with
seed `0x12345678`; broader PP-Up values and natural contexts are not exercised
by this case. All eight positive parties,Trainer52,final seeds and entire final
4MiB RAM hashes equal the preceding case,with117 extra hooks. EN totals are
1040577 Normal/1056804 Plus; IT adds34. Prefix604/638 remains unchanged. These
are observed hook counts,not cycle or performance measurements.

| Check | Wall time | OS peak RSS, bytes |
| --- | ---: | ---: |
| Final EN10 | 108.638s | 549945344 |
| Final IT10 | 108.279s | 628244480 |
| Portable12 | 0.597s | 60981248 |
| Replay11,both languages | 9.189s | 729153536 |
| Four-image lineage EN / IT,no CPU | 1.886s /1.653s | 219611136 /225755136 |
| Current readback EN / IT,no CPU | 0.599s /0.608s | 221331456 /227213312 |

On both languages the Close counter retains reader-phase and final whole-RAM
hashes while its file remains open. PP1 retains the exact reader-phase RAM and
raw delivery,then changes the predicted first packet and final RAM. First-name
evidence stays identical; only the declared later RAM-scope hashes differ.

## Counterproofs, observer effects and limits

PP1 changes only R0=15→1 at `0x02073392`, after the real LDRB. Raw16 bytes,
reader metadata/frame, default learnset and the full pre-state remain unchanged.
Observed PP-Up0 makes the native maximum calculation return1; the setter must
write1 and the first final packet must equal an independent one-field prediction:
decrypt128 bytes, change BlockB+8, recompute checksum−14 and re-encrypt128.
PID/flags,100-byte party data, other moves/PP-Ups and five other Pokémon match.

Keep raw archives separate from this counter's semantic expectation. Changing
the archive would falsify the earlier default310 model read. The verifier instead
clones only the complete constructor-result function, including its20-statement
guard block, and authenticates
its source SHA-256 `0199a89927cbbcb08ed8f13d2a124380cd16da6c8b4dd7dacf6a4b43117d9090`,
and retains identical bytecode/defaults/closure. Its sole globals change is a
local T proxy whose expected result changes only first-record PPslot0=1;
M decoding and all other APIs stay identical. The28-statement evidence function,
raw archives, original T module and dispatch stay unchanged. The positive oracle
refuses the counter flag's presence. Only a validated counter accepts strict
integer1, after proving the R0-only shadow, exact shared pre-state and predicted
whole packet. A matching final PP alone is insufficient.

CreateMon's earlier packet retains PP15/friend35. Subsequent friendship
checkpoints have PP1 and friend35 before the owned override,then friend255.
Only the first checkpoint gets a declared baseline expectation; observed packets
are never rewritten. All first-name scope hashes precede the mutation and remain
checked. For the later five names,only25 RAM-scope hashes may be projected;
all copied data,writes,ABI,lifetime and other transitions remain checked.
Close omission separately tests ownership even when payload,party and final RAM
stay unchanged; its open file ledger must be rejected with variant tags disguised.

OFF compares exactly224 bytes of28 allocation canaries plus900 bytes in12
already-freed buffers:ten44-byte buffers,one404-byte table and one56-byte Mail.
The14 actual allocations have only header108 and MON236 still live. Distinguish
personal44,learnset28+zeroed16 tail and Mail_Init56; they do not share a raw
preimage. Mail's language/version come from native state,not the textual ROM
label; both tested images use language2/version7. MailMsg_Init leaves msg_no
unwritten,so its zero here belongs to the modeled zero allocator. The predicted
56 bytes must also match the actual copied party-tail20..76. ON poisons freed
buffers withDD;OFF retains those source-specific bytes. Project only these1124
bytes,preserve gaps/live payload16/saved upper16,then compare phase RAM.
Per-run freeze still admits only the reader frame and live output,with an
immutable guard; no broad heap or new stack mask is introduced.

| Conclusion | Evidence and limit |
| --- | --- |
| Documented provenance | Record310/PP15 and172-byte native window match across eight images; whole archives differ. Custom and default callers are distinct. |
| Reconstructed binary correspondence | Existing Plus ELF/installation readback remains verified; original native MW build is unavailable. |
| Demonstrated semantics | Native resource selection,borrowed stack buffer,LDRB,PP-Up/division,setter and full-packet PP1 prediction under named models. |
| Observed activation | Initialized trainer31 caller,selected Plus flags,seeds,poisons and controls; no historical or natural encounter activation. |
| Unattributed links | Five native FS services,native heap,183/185 other reads,other IDs/errors/card/full battle/UI/SAVE/hardware. |

No game fix,speedup or recovered memory is claimed. A future reader error-policy
or performance change requires separate caller/error coverage and a maintainer
decision. This case qualifies the selected stack destination and PP path only.
