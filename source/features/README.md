# Feature ownership

Each folder owns one game behavior or a closely related group. Read its source,
installer, independent verification and local tests together. The exact folder
paths are pinned by historical build and source manifests; keep their names
stable during maintenance releases.

| Area | Feature folders |
| --- | --- |
| Story, field and events | `event-flags`, `npc`, `camera`, `field-guide`, `guide`, `shiny`, `traded-egg`, `rematch-variants` |
| Battles and Pokémon | `fairy-ai`, `type-consumers`, `trainer-strategy`, `modern-accuracy`, `anim`, `anim2`, `extended-levels`, `squadra-lotta`, `borsa-lotta` |
| Save, Bag and settings | `plus-chunk`, `borsa`, `capacita-borsa`, `training`, `training-native`, `portable-box`, `settings-ui`, `save-ui`, `options` |
| Native UI and presentation | `ui-native`, `plus-ui`, `guide-ui`, `summary-controls`, `title`, `credit`, `overlay`, `texts` |
| Build support and diagnosis | `native-core`, `reserve`, `manutenzione`, `debug`, `caramelle` |

Some features cross these areas. Follow the stage owner in `source/sgp13/` or
`source/sgp131/` and its reserve map before editing native addresses or shared
save data. For the overall build path and public/private boundary, use the
[repository map](../docs/architecture/README.md).

## Shared integration boundaries

Group analysis and regression checks by shared code, resources and lifetime.
Features appearing in the same menu can still have separate installers and
state. These examples identify source relationships, not new runtime acceptance:

| Boundary | Source and composition | Relevant checks |
| --- | --- | --- |
| Guide and Plus Settings | [`ui_compile.py`](../sgp131/ui_compile.py) compiles their scene/font/heap/resource units into overlay54; [`ui.py`](../sgp131/ui.py) installs separate templates with common bridge main/exit functions | A change to that common boundary needs both entry/exit paths and affected resource clients; reuse one baseline and add feature-specific controls only where behavior differs |
| Portable Box | [`portable-box`](portable-box/runtime.c), [`portable.py`](../sgp131/portable.py) and its [hook/lifetime contract](../docs/portable-box-1.3.1.md) own Party → native PC → Party | This is distinct from Bag inventory/capacity; Bag-return lazy binding is a dependency, not shared ownership of the two engines |
| Bag and training persistence | [`training.py`](../sgp13/training.py) verifies and coordinates Bag load/save wrappers; [`training-native`](training-native/README.md) describes admission and transactions | Changes at this boundary need coordinated Bag/training/save controls; an unrelated Guide-render change does not justify repeating the complete training backend campaign |

For a retail-to-Plus comparison, distinguish inherited patches, compiled Plus
code, script/data changes and container metadata. Decompression, relocation or
archive rebuilding can change physical bytes without changing every enclosed
function. Use the [source-to-ROM method](../docs/test-bench.md#linking-source-to-an-exact-rom)
and per-owner readback to establish the actual modified interval.
