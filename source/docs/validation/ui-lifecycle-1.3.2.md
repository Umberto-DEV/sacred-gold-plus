# Options and Guide lifecycle — 9 November 2026

This investigation qualifies both UI paths on the accepted 1.3.2 EN/IT images.
The selected case is **unnecessary resource loading while navigating an already
open Guide**. The source path, observed resource identities and compiled owner
tests contradict that hypothesis in the exercised cases. No game correction,
persistent cache, new ROM, version change or performance improvement is claimed.

## Exact inputs and assurance

Baseline and investigation candidate are the same accepted bytes from the
[current game contract](../../distribution/game-1.3.2-r4.json):

| Language | Bytes | SHA-256 |
| --- | ---: | --- |
| EN | 152786844 | `2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d` |
| IT | 159029760 | `13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a` |

Source starts at `a912b3e155150e604d1bf5cb5bd5a18b8cf13b8a` on main, with a
clean working tree. Whole-ROM hashes were checked against that contract.
Independent static analyses also checked the actual templates, native ABI
preimages, compiled Scene/Bridge/Fieldbook/Physical payloads and their consumed
source fingerprints against the existing construction receipts. No new
composition or ROM build was needed for unchanged game sources.

The ARM layout query and seven focused compiled owner tests use authenticated
Apple clang 21.0.0, `clang-2100.4.1.1`, binary SHA-256
`fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66`.
The interpreter is Python 3.14.7, executable SHA-256
`87d4df53fd91304be5bac391fb204643c36b7df2023c04a0953bcbc7d4fdf634`.

The inherited headless executable has SHA-256
`81e58a86e3d055696d7a661eca9e91e9e23f7a06a1dcd862badd78d4c58877e1`.
Its session metadata names melonDS `906e9ebb27da8c6a715cd7abab4abfe8a8d29427`,
ARM interpreter, software renderer, FreeBIOS, generated firmware and fixed
RTC `2026-09-05 12:00:00`. Its historical CMake source paths no longer exist;
this campaign does not attest a fresh source rebuild of that executable.
Its older CSV has no `host_runframe_ns` column: no RunFrame-only host CPU
timing or guest CPU-tick result is available. Instruction counters stayed zero;
no breakpoint, savestate load, RAM write, cheat or freeze was used.

The external HGSS source-only checkout is pinned at
`cb614ad23449d5852b40321dc409c4143872b35c`. The borrowed production reference
directory's current HEAD differs from its documented metadata pin; selected
files and candidate-native byte ranges were checked individually. Directory
names and equal symbol names were not used as compatibility evidence.

## Functional qualification

| Path | Caller and activation | Init, update/draw and retirement |
| --- | --- | --- |
| Options | Native Field child call and ARM9 template `0x020FA354`; `sgp131/ui.py` installs resident Bridge callbacks with overlay ID NONE. Shiny capture/owner checks remain part of admission. | Bridge role 1 loads the common dynamic Scene in overlay 54. `settings-ui` owns model/drafts/transactions/painter. Scene creates heap38 with 196608-byte backing, captures settings, loads UIR2, leases the font/chrome, allocates pool/BG and publishes the first canvas. Physical input changes the model; dirty/history planning drives subsequent paint. Exit cancels or rolls back drafts, retires paint/font/BG/FS/leases, frees app and destroys heap38 before the Bridge releases module/root. |
| Guide | Fieldbook ARM9 hook `0x0203BFE4`, overlay27 frame callback and template `0x023D7B10`; the same composer activates Bridge role 2. | The same Scene creates heap38 with 262144-byte backing and loads UIR2 plus the typed Guide member. `guide-ui` owns category/list/topic/page state and painter. Guide/font leases retain their separate roots through all paint jobs. Exit retires jobs and BG callback before dropping leases, closing/releasing readers, destroying heap38 and releasing the module/root. |

The owner files remain in `features/ui-native`, `features/settings-ui` and
`features/guide-ui`; the fieldbook binding is `features/ui-native/fieldbook.c`.
`ui_scene_init/main/exit` are shared by both roles. Old overlay54 callbacks and
the retired Guide are excluded from these installed entries; there is no old
UI fallback in the measured lifecycle. The dynamic Scene payload is 62516 bytes,
SHA-256 `68caffb30b245d2a14d5426a6e0b178f958053120bc9db7cf2051dd968cfe551`.

HGSS counterparts were checked for the actual native OverlayManager, heap,
FS, font manager and decoder ABI. In particular, the native lazy font initializer
writes its decoder and leaves its unused cache word untouched. The existing
[Guide correction](guide-opening-1.3.2.md) preserves that word and restores the
native font tuple. This investigation changes none of those guards or layouts.
Installer, independent readback and test constants remain separate authorities.

## Timing method and results

Each primary path cold-boots normally from a read-only copy of the same
populated raw fixture, SHA-256
`84536ef9760569460d948302a8cac4c5e7e3a423a957e823185ac1dd516c2bfa`.
EN orders Options then Guide; IT orders Guide then Options. Each role has a
first opening and two reopenings after full retirement, with Down/Up and idle
intervals. Guide also exercises category → list → topic → list → category.

Units are **guest frames**, sampled between frames with one-frame resolution.
Reads stop host advancement between commands; they do not measure uninterrupted
wall-clock presentation. Entry ends at logical input readiness: Scene IDLE14,
matching submitted/visible epochs and an active physical-input token. Native
Bag entry ends at its identified manager exec2/proc1 after its fade. Model input
acceptance, BG publication and software framebuffer appearance are distinct.

| Path | First logical entry EN / IT | Reopen entries EN / IT | Down/Up model acceptance | UI BG publication after Down/Up | Resource/child retirement after B |
| --- | --- | --- | --- | --- | --- |
| Options | 97 / 98 | 97,97 / 99,98 | 1 | 5 | 7 |
| Guide | 99 / 98 | 98,98 / 98,98 | 1 | 5 | 7 |
| Native Bag in the same Plus ROM | 90 / 89 | 87,87 / 87,87 | 1–2 | Separate OAM/BG path | 36 |

The Bag comparison is the native HGSS application **inside Plus**. Its lifecycle
and cursor instructions match the checked native implementation, while Plus
expands its allocation/item handling. It is not an untouched retail-ROM baseline.
Its item-grid cursor and the Plus row painter have different presentation work;
the model timings alone do not establish equal visual responsiveness.

Closing is also measured through Field readiness, separately from resource
retirement. From B to the returned menu gate: Options 76 frames, Guide 77,
Bag 105. Options IT and Bag have three samples per language/path; the additional
EN Options and EN/IT Guide closure checks have one each. The gate accepts a
completed native menu task or its input state, bottom app/state `{0,1}` and a
rearmed Fieldbook with no pending press. Returned screens were inspected.
These closing numbers refer to the primary and closure-only runs. The later
Plus framebuffer probes shift input phase and record retirement8/menu77–78;
they do not establish a universal fixed closing duration.

Two initial observer attempts remain recorded as harness failures: a fixed
60-frame return wait sent the next touch during Field restoration; requiring
menu task state3 forever then rejected the normal completed-task/null state.
Neither failure is counted as a game defect. Targeted closure checks corrected
those criteria without rerunning a complete game campaign.

The logical publication witness precedes the software framebuffer result.
Targeted frame-by-frame captures qualify that boundary separately; an initial
black capture at first publication is not treated as a failed UI opening.
In one additional first-opening probe per role/language, Options is readable
at frame98 EN /99 IT and Guide at100 EN /99 IT, one frame after the logical
witness. Down and Up highlight changes appear at frame7 in both Plus roles
and languages in those visual probes. Their additional capture frames shift
the next input to the other native sampling phase: model acceptance is2 and
publication6, versus1 and5 in the primary replay. A six-frame display estimate
from the primary publication witness was not directly photographed and is
not an accepted result. The native Bag probes show Down at5 and Up at7, against model
acceptance at1 and2 respectively. Its highlight appears four/five frames after
the model update. Consecutive captures and the red selection-border region
confirm those changes; a model write is not relabelled as visible response.
These are bounded software framebuffer samples, not statistical equivalence
or a declaration of normal handheld responsiveness.
Guide list/topic transitions in the primary sequence publish in 8,11,4,7 frames;
these are publication timings, not CPU execution durations or hardware latency.

## Loading and memory

Each new generation loads the overlay metadata and image, then its role's
resources. The installed module config describes 4128 metadata bytes, 60876
packed image bytes and 65228 expanded bytes. UIR2 reads a 468-byte archive
prefix and a 68040-byte EN / 68672-byte IT member. Guide additionally reads a
91756-byte EN / 92668-byte IT member. The Guide's recorded async read count,
return count and final CRC cursor match those exact member lengths.

During the measured Guide navigation and idle periods, the module remains
READY17, UIR2 READY6 and Guide READY9; resource tuples, roots and reader state
stay identical within each generation. Stable allocation ledgers before and
after navigation match in all three cycles per language. Source `ui_scene_main`
does not re-enter resource initialization/loading; the compiled reader tests
also check views without filesystem work. Per-frame observations do not count
every substage inside a pump or physical CARD/cache transaction, so exact
hardware I/O-call counts are not claimed.

| Stable scene | Reserved heap backing | Live blocks | Occupied native blocks, including their NNS/GF headers |
| --- | ---: | ---: | ---: |
| Options EN | 196608 | 8 | 121456 |
| Options IT | 196608 | 8 | 122088 |
| Guide EN | 262144 | 9 | 212800 |
| Guide IT | 262144 | 9 | 214344 |

These are steady-state heap38 observations, not total game RAM or a measured
allocation peak. Bridge's 5036-byte requested root and the module's fixed code
region are separate. Stack, VRAM occupancy, transient peak and fragmentation
were not measured. Targeted final closure probes additionally read zero heap38
allocation count, inactive index28, cleared persistent ownership and empty
Bridge control after retirement. No growing retained allocation was observed.

Reopening deliberately repeats loading after destroying that generation's heap
and releasing the dynamic module. Turning those lifetimes into a resident cache
would change ownership and memory budgets. The measured reopening cost alone
does not justify that change. Possible CPU amplification in font/topology checks
is a separate, unmeasured hypothesis; no validation guard was removed for it.

## Save, settings and focused regression evidence

Seven existing compiled ARM owner tests passed, with zero failures or skips:
UIR lease/release, lazy-cache residue retirement, failed-close ownership,
Guide bounded pumping/no spin on pending I/O, lease/view lifetime, read-only
views without new FS calls, and failed-close recovery. Their synthetic lower-FS
seams are explicit; they are not full native scheduling or hardware tests.

Fresh raw-save checks use two original fixtures in both EN and IT: the legacy
fixture without Plus data (`80f555b057cd2c339d5f6b515d8f4c80c263718791c058985e0ebf6ef09cfc40`)
and the populated Plus/expanded-Bag fixture identified above. Each sequence is
Continue → native SAVE → process exit → cold Continue → Options/Guide
open/close/reopen, with separate output SRAM and visual review. Original fixtures
are never written or replaced. Protected comparisons cover party/storage,
Bag/expanded slots, settings, progress, Pokédex and applicable journal data.
Native playtime and the exact native storage dirty-bitmap reset retain their
documented allowances; no broad storage mask or save migration is introduced.
All four case/language pairs passed protected comparisons and visual review.
The legacy fixture has no party or stored Pokémon; the populated fixture has
five party Pokémon,113 boxed Pokémon and three occupied expanded slots.
Native save generations advance1→2 and113→114 respectively. In every pair,
after-SAVE, after-cold and after-UI raw exports are byte-identical. Existing
settings are preserved; this is not a new exhaustive Apply/cancel transaction
campaign. These are two unique original fixtures, not four independent saves.

## Evidence and limits

The sole private campaign is
`local/validation/sviluppo-1.3.2/ui-lifecycle-2026-11-09/`: preflight/protocol,
independent functional analyses, observer commands, raw frame/read logs,
measurement JSON, captures, bounded-process receipts, save comparisons and
separate final review. Generated builds remain untouched in their canonical
workbench paths; no ROM tree is duplicated.

Environment and census checks passed before the investigation. Processes use
the shared heavy-job lock, sampled RSS/output/disk guards and bounded logs;
the 10 GiB free-space reserve is retained. This is a scoped investigation,
not a complete Class A/B rerun or a replacement for historical validation.

No Android device was present in the fresh ADB inventory. No new Android run, Nintendo
DS/DSi/3DS run, JIT/backend result, hardware timing, five-language save campaign
or full playthrough is established. FR/ES/DE retain their earlier bounded
acceptance. No personal installation, publication, tag or release was changed.
