# New Game reset: historical 1.3.2 investigation

**Historical diagnostic record:** this investigation preceded the formal
five-language 1.3.2 composition. Its source-only status and open release gate
describe that checkpoint. The hashes below identify specific predecessors and
diagnostic probes, not current player builds. Current identities and bounded
acceptance are recorded in the [1.3.2 report](localization-1.3.2.md) and
[release contract](../../distribution/release-1.3.2.json). The original
measurements and limitations below are unchanged.

## Measured cause

On a cold New Game, the first conversation with Mom runs the ordinary story
`SetVar(0x6130, 2)` before a high event flag is accessed. The 1.3.1 family
variable handler assumed that the `HF02` save-bank tag already existed. Its
refusal path called `OS_ResetSystem(0)`, returning the game to its opening
screen. The event script itself was unchanged: IT member 845 of `a/0/1/2`
has SHA-256 `7a488b793cf3d7ef76c51d74bca6a4224d4ea5d8abf3439ffc9fef8bb277d128`
in 1.04 and released 1.3.1. A native breakpoint on released IT observed the
zero-filled 36-byte reserved bank, variable `0x6130`, value `2`, the refusal
routine and then the SDK reset. No reset buttons were held.
The fault condition is general: any of the 24 redirected story variables can
be the first access to an empty New Game bank. Mom is the repeatable path that
exposed it, not the only possible script context.

Identical language-specific input sequences ran on the Mac headless melonDS
core with ARM interpreter, software rendering, FreeBIOS, no cheats, no JIT and
no saved state. VBlank counted forward in V1.3 V4 and in the corrected probe;
the released 1.3.1 counter dropped to zero at the Mom transition:

| Language | V1.3 V4 SHA-256 | Released 1.3.1 SHA-256 | Reset frame | Corrected probe SHA-256 |
| --- | --- | --- | ---: | --- |
| EN | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` | `185dc5c53a75652c021ced65157e1c3388cd661ebe90775e5b49314aee753b08` | 17427 | `ff37041bbba82a3e11fdc865512b4ae319e0a8fc8098aacf354dc0ca530644a8` |
| IT | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` | `b68ddd5691538c3895b75f3f20db5a163b2bd8376629f59d2a9d55dc05935bce` | 13738 | `97528b90da8da05fbee353d378f1bfc11b299875bb21f2c84056431cd85a141d` |

The probes replace only the owned event-flag payload and four hooks in copies
of 1.3.1, with independent byte readback. They are diagnostic artifacts and
were not used as player builds. The source change initializes an empty bank
on the first high-flag **or** family-variable access, imports the legacy high
bits once, starts the 24 story gates open and writes `HF02` last. HF01 and
foreign nonzero reservations still refuse access. The save layout, field IDs
and existing Plus settings are unchanged.

The ARM component regression was observed failing before the change and
passing afterward. Native SetVar, flag, coordinate and load-path checks passed
against both private V4 language inputs. Those component results establish
hook behavior; the probe runs establish the specific New Game transition.

## Latios control and limits

The Vermilion totem was exercised with the same copied raw-save input,
SHA-256 `84536ef9760569460d948302a8cac4c5e7e3a423a957e823185ac1dd516c2bfa`,
on V4 IT, released 1.3.1 IT and the corrected IT probe. Each reached the
inscription, choice, cry and rendered level-40 battle menu in 7,786 frames,
without a VBlank drop after frame 1,000 or a sampled data abort. This bounded
trial **did not reproduce** the older intermittent Latios freeze and does not
establish that the Mom defect caused it. Battle completion and post-battle
SAVE were outside this trial. The original save stayed unchanged.

No final 1.3.2 active ROM, raw-save Continue/native SAVE/cold restart matrix,
physical Android run, player ZIP or release acceptance is claimed here.
Historical 1.3.1 screenshots and package hashes remain attached to 1.3.1.
