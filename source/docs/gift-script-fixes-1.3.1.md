# Gift script fixes in 1.3.1

Gift and egg delivery directly to storage was abandoned: players use the portable Box to free a party slot. Two script repairs remain in `a/0/1/2`. They add no ARM code, reserve allocation, message or ARM9 changes.

## Ribbon award tails

Members 225, 232, 243, 246, 938 and 962 contained `4E00 1400 D907 3500 6100 0200` after `GiveRibbon`. An editor had pasted the full-Bag branch's `CallStd 2009` over the award tail. The native dispatcher has 853 entries and rejects opcode 2009, stopping before `CloseMsg`/`ReleaseAll`.

`gifts_scripts.patch_member` replaces only `4E00 1400 D907` with the retail `PlayFanfare; WaitFanfare; SetFlag <daily flag>; WaitButton` sequence: six additional bytes per member, with entry and branch relocation. The independent `verify_member` checks the result.

## Full-party guard for Eevee

Entry 11 of member 227 gives a level-5 Eevee. Previously it ran `GetPartyCount` and `GiveMon` without a guard. With six party members, `GiveMon` failed silently, but `SetFlag 16220` and `HidePerson 15` still removed the NPC and permanently consumed the gift.

The repair follows Bill's retail Eevee script (`scr_seq_0892_T25R0401.s`): count the party, compare with six and branch to an existing full-party message before the monologue.

```text
PlaySE; LockAll; FacePlayer                 unchanged, entry 11 at 442
GetPartyCount 0x8005                        17-byte guard inserted at 450
CompareVarToValue 0x8005, 6
GoToIf EQ -> FULL
BufferPlayersName ... NPCMsg 14..19 ...     unchanged relative sequence
FULL, appended 14-byte block:
  MsgBoxExtern 25, 39; WaitButton; CloseMsg; ReleaseAll; End
```

The native message is bank 25, entry 39: EN `Your party is full!`, IT `La tua squadra è completa!`. `MsgBoxExtern` reads that bank directly; no message bank is changed. The producer authenticates the EN/IT bank hashes.

With six Pokémon, the script shows the message and returns control without `GiveMon`, flag 16220, `HidePerson 15` or a nickname offer. The NPC remains and the interaction is repeatable. With fewer than six, the executed V4 commands are unchanged except for the additional guard count; the real dispatcher test observes identical final variables. The original `GetPartyCount` at 471 rewrites borrowed variable `0x8005` before use. The verifier requires only `BufferPlayersName`/`NPCMsg` between those writes, with no jumps or reads of the variable. `verify_party_guard` checks every entry and branch. Member growth is 31 bytes: 17 for the guard and 14 for its tail.

## Composition and evidence

`sgp131/gifts_archives.py` declares `gifts-scripts` as hash-bound V4 `ArchiveDelta` changes to the seven members 225, 227, 232, 243, 246, 938 and 962. The UI stage applies them in its sole archive write through `archives.py`; nothing is appended after UI. Guide members 131, 132, 152, 196 and 890 are rejected.

Tests use real EN/IT V4 bytes and the cartridge dispatcher at `0x0203FD6C` in Unicorn. Native `End`, `GoTo`, `GoToIf`, `SetVar`, `CopyVar` and `CompareVarToValue` handlers execute; other handlers are recording stubs. They do not execute the message window, fades, actual `GiveMon` or nickname screen. The field appearance, text speed and final empty page of bank 25 remain untested on device.

Remaining rendered tests require an unclaimed Eevee fixture with flag 16220 clear: party five must receive the gift normally; party six must show the full-party message twice with no gift or persistent change; freeing a slot through the portable Box must then permit delivery. Continue → native SAVE → cold restart is required after both refusal and delivery. A ribbon member, such as 225, must reach `CloseMsg`/`ReleaseAll` without trapping the player. These are coverage requirements, not completed tests.
