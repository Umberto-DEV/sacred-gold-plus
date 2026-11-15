# Technical documentation

The current **1.3.3 development candidate** is described by its
[fix list](../../BUG-FIXES-1.3.3.md), [game identities](../distribution/game-1.3.3.json)
and [validation report](validation/uturn-fix-1.3.3.md). Evidence is scoped to
the documented components and checks; natural battle and device coverage remain
pending. Published 1.3.2 reports retain their original scope.

Start with the [repository map](architecture/README.md) to find the owner of a
game change, the build path and the data boundary. The
[feature directory](../features/README.md) groups native and script changes by
game subsystem. The [validation index](validation/README.md) explains where new
candidate evidence belongs. The [native-hardware procedure](native-hardware-validation.md)
sets out candidate/save identification, physical test cells and timing comparisons.

Historical versioned reports in this directory keep their original names and
claims. New release evidence goes into `validation/`; a new report must name the
exact ROM hash, language, save fixture and test limit. Release notes and package
instructions live under [`source/distribution`](../distribution/README.md).

The current source guide is [`source/README.md`](../README.md). Private saves,
ROMs, dumps and developer handoffs are not part of the public documentation.

Player-facing illustrated guides live in [`guides/`](../../guides/README.md).
The [file index](../../REPOSITORY.md) and [package workspace](../../package/README.md)
identify the editable guide, page and ZIP inputs.

For current language sources, use [localization](localization.md). The
[repeatable update procedure](update-workflow.md) identifies the documents,
source owners and bounded release gates to revisit for each successor.
