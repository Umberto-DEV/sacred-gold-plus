# Complete-party rematch variants

The owner contains the authored C core, native seam hook and resident overlay
loader stub. [Design and activation requirements](../../docs/rematch-variants-1.3.1.md)
and the [installer/compiler](../../sgp131/rematches.py) describe composition.

The [exact r4 attribution case](../../docs/validation/rematch-source-rom-1.3.2.md)
reconstructs the installed inert module, its shared resident allocation and
native load/unload lifetime. It includes portable commands, input identities,
independent ELF/ROM readback, bounded CPU paths and counterproofs.
[The verifier](tools/attribuisci.py) reads your private ROM inputs; [tests](test/test_attribution.py)
check retention, output protection, ABI, data/code and same-output teardown failures.
The installed activation byte is0; natural phone/Dojo activation remains unqualified.

The [active RAM continuation](../../docs/validation/rematch-active-source-rom-1.3.2.md)
executes native gates, seed selection and the108-byte copy in named RAM shadows.
Its107-store counter has the same output hash, so the verifier also requires the
complete native store trace. It does not change the installed activation byte.

The [native first-record continuation](../../docs/validation/rematch-consumer-source-rom-1.3.2.md)
follows the actual selected buffer through native RNG/IV calculation, trainer
strategy exclusion and the Plus level hook to the first CreateMon entry. It
reconstructs the strategy dependency and checks arguments rather than claiming
a completed Pokémon or party.

The [first native Pokémon continuation](../../docs/validation/rematch-firstmon-source-rom-1.3.2.md)
executes creation, encrypted fields/statistics, item/four-move application, the
owned post-form repair and actual PartyAdd return. Its zero-item counter has
identical final output but a missing native setter. The qualified SDK name model,
allocation lifetime, sparse instruction/data map and independent resource oracle
are reusable; complete parties and natural activation remain outside that case.

The [complete constructor case](../../docs/validation/rematch-complete-source-rom-1.3.2.md)
follows all six native creations, nonzero items/capsules, persistent PID state,
original seed restoration and both final frees through the actual return.
The verifier and tests separate identical-party teardown counterproofs from
raw capsule seals, cleared PartyExtra bytes and modeled SDK handle lifetime.
Installed activation remains0; natural phone/Dojo activation is unobserved.

The [void SDK return case](../../docs/validation/sdk-void-return-source-rom-1.3.2.md)
follows R0 from four modeled void services to the first actual native overwrite,
including return-stack continuations. Its independent raw reader, zero/ones
controls and live-pointer calibration qualify the body/teardown paths; the
loader prefix and native SDK internals remain separate questions.

The [native party-reader caller case](../../docs/validation/native-party-caller-source-rom-1.3.2.md)
follows `native.c`'s `rematch_hook` BLX through the native party parser, actual
return value and overlay unload to the constructor seam in one CPU context.

The [personal-data/EXP case](../../docs/validation/native-personal-caller-source-rom-1.3.2.md)
continues the first constructor personal read through its actual getter and
EXP consumer while preserving the native rematch/header owners.

The [native404-byte growth-table case](../../docs/validation/native-growth-caller-source-rom-1.3.2.md)
continues the same constructor through its first table read and real EXP consumer,
with a separate finite payload bound and source-derived ABI.

The [initial friendship/owned Plus override case](../../docs/validation/native-friendship-caller-source-rom-1.3.2.md)
extends the same trainer31 caller through the next personal read, two native
setter transactions and six packet checkpoints. A changed initial value is
later overwritten, preserving the final party; native FS and other reads retain
their declared models.

The [native custom-PP continuation](../../docs/validation/native-pp-caller-source-rom-1.3.2.md)
distinguishes the trainer loop from default learning, follows a real stack
buffer through native PP arithmetic/setter and verifies a one-field packet
counter. Source/compiler, FS/heap and natural-execution limits remain explicit.
