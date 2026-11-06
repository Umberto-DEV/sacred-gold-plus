# Wild nature and gender code validation

This is historical evidence from **15 September 2026** for the generators retained in the current source. It does not transfer played acceptance to a newer ROM.

## Cause and correction

`source/cheats/gender.py` regenerates groups 44, 45 and 46 for the authenticated EN/IT 1.2.1 inputs. The 25 nature names and catalogue order are preserved.

Old group 45 did not change the reproduced encounter's PID. With identical save/input, both no code and male + Adamant with L created level-19 Kakuna, PID `94332253`, nature 16, female. The old `020D3F60` hook instead changed `0227E98C` from `28B9` to `2056`; its `*0211186C + F710` address was outside observed creation. Its `8200*k + c` arithmetic also crossed both gender ranges. Old group 44 replaced a PID-building shift with a nature write. The replacement preserves native PID generation.

The generator acts before encryption in native `CreateMonWithNature` (`0206E108`) and `CreateMonWithGenderNatureLetter` (`0206E14C`, used by Cute Charm). Two Action Replay comparisons authenticate original prologues before writing.

- Group 44 is always active and replaces nature arguments while preserving native PID/gender generation.
- Groups 45/46 require L before the encounter. The standard path keeps the random PID upper half and uses low half `00FF` for male or `0000` for female; the native loop accepts only the requested `PID % 25`. The Cute Charm path replaces the native gender/nature arguments.
- Releasing L while 45/46 remains enabled restores the four original instructions. A new family entry first restores shared sites. Enable one entry from groups 44–46 at a time.

Existing Pokémon, encrypted data and checksums are untouched. No RAM payload, DMA hook or ROM modification is required. Fixed-gender/genderless species retain their biological gender. Groups 45/46 change PID and shiny distributions: do not combine them with shiny/PID codes. Restart after old codes or after disabling 44. Release L before disabling 45/46; otherwise restart.

## Evidence

`test_gender.py` passed six host tests. `test_gender_arm.py` passed one ARM test per language, executing original ARM9 selection in Unicorn for 1,200 cases per ROM: 25 natures × three modes × eight gender ratios × two routines. Tests check PID, nature, gender, final creation arguments, stack and preserved registers. RNG, gender-ratio lookup and final creation are declared stubs. A separate enumeration of all 65,536 upper halves for both genders proves every nature is reachable. XML migration rejects unknown layouts and is idempotent.

Real SRAM-start runs used the melonDS Action Replay engine:

| Run | Created PID | Nature | Gender | Result |
| --- | --- | --- | --- | --- |
| EN, old 45 Adamant | `94332253` | 16 | female | Identical to no-code control. |
| EN, new 45 Adamant | `B5B600FF` | 3 | male | Capture, Pokédex, storage, return to field and SAVE. |
| IT, new 46 Adamant | `0C4C0000` | 3 | female | Capture, Pokédex, storage, return to field and SAVE. |
| EN/IT, new 44 Adamant | `0C4C445C` | 3 | female | Encounter and native creation. |

Captures used a Master Ball already in the fixture. No Pokémon or capture routine was manually forced. The saved record at `10B40` had checksum `4ABB` (EN male) or `EF7F` (IT female) and the PID supplied to native creation. Cold SRAM reload without cheats preserved both records and checksums. Field-return dumps confirmed restoration after L release.

Played inputs, before expanded Bag capacity:

| Language | SHA-256 |
| --- | --- |
| EN | `30bbf4cf0105688218132c5aa4e8b9b3ec8de124961103f36cfbcb4c8e48a708` |
| IT | `8f991bdd7f8abb80aaf25855a1708203e2194c222fbcdf4f1f33d2bab93b2610` |

ROM/SRAM/dumps/fixture scripts/GDB traces remained private under `/tmp/sgp-final-20260915/gender/`.

After Bag expansion, both final 17-stage ROMs repeated six host tests plus one ARM test per language, again 1,200 native cases each. This was ARM revalidation; live encounters remain attached to the earlier hashes.

| Language | Final 17-stage SHA-256 |
| --- | --- |
| EN | `09528bd920609b14484bdf6d12fc9fe1c3239934dfdb92a3816a38fac6579d0b` |
| IT | `8a28781bcd8debab4a0bfe8c7f8c6b50361733f5a6cce2ffdf8835ab7d8ebe9a` |

Private logs: `/tmp/sgp-final-20260915/regression-17/gender-{EN,IT}.log`. Live coverage is Kakuna/Adamant; other natures, fixed ratios and Cute Charm are ARM evidence. This is not every species, gift, legendary or physical-console coverage. Emulator UI mutual exclusion is a separate integration.
