# Native type consumers

[`native.S`](native.S) replaces the64-byte Conversion2 row reader in place.
[`sgp131/type_consumers.py`](../../sgp131/type_consumers.py) compiles it,
fixes its external RNG BL and supplies edits to the shared AI overlay writer.
The same module owns separate Grounding, Fire Fang and Rage edits; those are
outside the [Conversion2 source-to-ROM case](../../docs/validation/conversion2-source-rom-1.3.2.md).
`reload_transform.S` and `uturn.S` belong to their separate consumers and are
not qualified by that case.

`tools/attribuisci.py` reconstructs the current helper, reads the compressed
final overlay independently and executes actual native RNG/divmod, helper and
command with five declared external controls. Its complete325-row check and
same-output/wrong-seed counterexample distinguish domain and state correctness.
The observed command entries are synthetic; dispatch opcode93 is linked statically.

Run `python3 tools/attribuisci.py --help` from this directory, or the full path
from the repository root. `--work DIR` compiles and retains the own-project ELF;
`--build DIR` verifies/reuses it without compiling; `--readback-only` explicitly
omits build provenance. Compiler API retention is opt-in; its production default
still leaves no object and preserves the existing receipt/payload behavior.

The [Grounding case](../../docs/validation/grounding-source-rom-1.3.2.md) attributes
the two column pointers through the actual native damage/multiplier/math chain.
`tools/attribuisci_grounding.py` executes finite state cases and old-column
counterexamples without a compiler. The five external queries remain models;
other same-owner repairs retain their separate coverage.

The [Wonder Guard case](../../docs/validation/wonder-guard-source-rom-1.3.2.md)
links the existing effect-gate repair to actual move records and both current
native consumers. `tools/attribuisci_wonder_guard.py` uses bounded charge states,
separate status oracles and old-literal/branch counterexamples. It reuses the
historical evidence without repeating its campaign; natural controller and
Power Herb behavior remain outside the case.

The [Rage case](../../docs/validation/rage-source-rom-1.3.2.md) follows the existing
two-byte status repair through the complete pre-turn controller and its three
native leaf functions. `tools/attribuisci_rage.py` checks bit preservation,
actual selected-move data and RNG state without service stubs. It starts from
a controlled Rage state; natural battle and later PartyMon transport remain
separate questions.

The [Transform transport case](../../docs/validation/transform-transport-source-rom-1.3.2.md)
uses `tools/attribuisci_transform.py` to carry the Rage result through an actual
native packet emitter and consumer. It verifies exact state transport and
records PartyMon write requests through declared services; encrypted mutation
and SAVE remain unqualified. A same-output/wrong-status counterexample checks
the intermediate state independently.

The [Transform reload case](../../docs/validation/transform-reload-source-rom-1.3.2.md)
links `reload_transform.S` through a retained ELF and the exact340-byte installed
replacement. `tools/attribuisci_reload.py` offers fresh/reuse/readback-only modes,
checks the preserved native pool and separates copied stats, common fields and
Mimic slots. The compiler retention option leaves its production default intact.

The [U-turn attribution](../../docs/validation/uturn-source-rom-1.3.2.md) links the
68-byte helper,128-byte tail, two native calls and pivot-script insertion.
`tools/attribuisci_uturn.py` reports two historical r4 compatibility failures: the
unmarked modifier arguments and a marker collision with negative native damage.
Its CLI exits1 after writing the historical evidence. The [1.3.3 candidate fix](../../docs/validation/uturn-fix-1.3.3.md) has separate bounded regression and counterfactual evidence, five-candidate scoped readback and seven bounded host save cycles. A full natural pivot and physical-device validation remain pending. The candidate report includes the exact artifact and counterfactual reproduction commands.

The [pivot/Shell Bell order check](../../docs/validation/uturn-shellbell-order-source-rom-1.3.2.md)
links command213 to its exact native handler and the installed member175 prefix.
The item command precedes the snapshot and later flinch consumer, rejecting an
unsupported late-consumer healing-loss premise. It is static evidence, with
owned parser counterexamples; no new healing execution or game repair is claimed.

For the ordinary path, the [controlled input preparation](../../docs/validation/ordinary-shellbell-source-rom-1.3.2.md#controlled-input-before-the-damage-writer)
uses `tools/prepara_shellbell_ordinary.py` to authenticate an exact image and
prepare private pre-HpCalc arenas with typed fields and actual cached resources.
It executes no game code and supplies no forecast or healing result. The
stdlib input tests need neither ROM bytes nor a compiler/emulator.

The [native HP continuation case](../../docs/validation/hp-flinch-source-rom-1.3.2.md)
executes the damage writer, HP script interpreter and state6 flinch caller.
`tools/attribuisci_hp_flinch.py` finds the negative-word collision after real HP
updates; it retains explicit service boundaries and unqualified earlier states.

The [native snapshot producer](../../docs/validation/uturn-producer-source-rom-1.3.2.md)
uses `tools/attribuisci_uturn_producer.py` and actual script handlers/variable
lookup. A bounded RAM stop keeps its scope explicit; CalcTemp preservation and
same-flinch/wrong-packing counterexamples check the intermediate state.

The [AfterDamage state0 case](../../docs/validation/afterdamage-source-rom-1.3.2.md)
uses `tools/attribuisci_afterdamage.py` to execute the earlier controller states
and required neutral scripts. It reaches the erroneous script14 request without
host state6 injection; the effect script itself remains outside this case.

In the native parent reports, `flinch` means a successful script14 request;
execution of that effect and loss of a turn are separate coverage questions.

The [native flinch effect](../../docs/validation/flinch-effect-source-rom-1.3.2.md)
uses `tools/attribuisci_flinch_effect.py` to execute script14,real ability gates
and the target setter. It proves the bit write and controls which block it;
turn loss remains a distinct consumer beyond the effect.

The [native flinch consumer](../../docs/validation/flinch-consumer-source-rom-1.3.2.md)
uses `tools/attribuisci_flinch_consumer.py` to preserve that actual bit across a
controlled next-action boundary and execute TryMove/status checks/script15 to
command39. It proves the clear and cancellation route;action-end bookkeeping
and natural turn selection remain separate coverage questions.

The [native action-end continuation](../../docs/validation/action-end-source-rom-1.3.2.md)
uses `tools/attribuisci_actionend.py` to execute ordinary history/action-end gates,
mark the selected action40,advance its index and reset temporary data natively.
A same-command wrong-order counter prevents treating command8 as sufficient
proof. Reaching command8 does not execute natural next-action selection.

The [native next-action dispatch](../../docs/validation/next-action-source-rom-1.3.2.md)
uses `tools/attribuisci_next_action.py` to execute8→13→23 and initialize the next
attacker/move/target. Native speed sorting and a stale-actor same-command counter
keep handler selection distinct from complete handler execution.

The [ordinary Shell Bell static readback](../../docs/validation/ordinary-shellbell-source-rom-1.3.2.md)
links controller37 to its real native consumer, separates456 profile bytes into
code/table/padding/pool and authenticates item253→member231→effect88/modifier8.
`tools/rileggi_shellbell_ordinary.py` needs no compiler or guest CPU. Its static
result does not prove a successful caller boundary, healing loss or a repair.

Its optional `--include-neutral` mode reads the supporting static profiles and
source definitions. TryUseHeldItem admits only90 selected code bytes for effect0
or88; its following function is excluded. Neutral outcomes still permit native
scratch-field/RNG changes, and earlier API-query entry resets do not compose a
continuous controller execution.

The same guide now includes the [owned continuous dispatch qualification](../../docs/validation/ordinary-shellbell-source-rom-1.3.2.md#owned-continuous-dispatcher-qualification).
The authored ASM, authenticated compiler/ELF reader and retained source/CPU
interpreters check two owned callbacks without stack/register reinitialization.
Owned ON/OFF succeeds, but no original controller or healing behavior is implied.
