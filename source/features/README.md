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
