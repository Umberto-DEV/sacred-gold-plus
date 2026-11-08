# Technical documentation

Start with the [repository map](architecture/README.md) to find the owner of a
game change, the build path and the data boundary. The
[feature directory](../features/README.md) groups native and script changes by
game subsystem. The [validation index](validation/README.md) explains where new
candidate evidence belongs.

Historical versioned reports in this directory keep their original names and
claims. New release evidence goes into `validation/`; a new report must name the
exact ROM hash, language, save fixture and test limit. Release notes and package
instructions live under [`source/distribution`](../distribution/README.md).

The current source guide is [`source/README.md`](../README.md). Private saves,
ROMs, dumps and developer handoffs are not part of the public documentation.

For current language sources, use [localization](localization.md). The
[repeatable update procedure](update-workflow.md) identifies the documents,
source owners and bounded release gates to revisit for each successor.
