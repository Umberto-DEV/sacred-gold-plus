# Unified settings behavior in 1.3.1

Settings use one continuous Game/Plus/Shiny list on the upper screen and a static native Poké Ball on the lower screen. Settings accept physical buttons. The 30 October revision replaced the black lower screen and unified A/B/X/Y symbols while retaining their actions. Composition evidence is in [UI validation](ui-1.3.1-validation.md).

## List and input

The list contains six native settings (text, battle effects, battle style, sound, controls and frame), five Plus settings and Shiny mode. Pro adds Target and Pro Hunt. Section headings are not selectable. Stable row IDs, the item/total counter, title, version and position have separate areas under one renderer. Classic hides Pro controls while preserving the target. Existing chain/charge resets happen at commit; no persistent IDs are added.

| Button | Action |
| --- | --- |
| Up/Down | Previous/next row, without wrap; native directional repeat. |
| Left/Right | Previous/next value, clamped at the ends; never changes section. |
| L/R | First control in the previous/next section, without wrap. Up/Down still reaches every row. |
| A | Opens a selector or confirms a local choice. An ordinary row never globally applies changes. |
| B | Back; at the root, handles exit with pending changes. |
| X | Explicit Apply confirmation from the root; ignored in selectors and Info. |
| Y | Upper-screen Info; B returns to the same row. |
| Touch | Ignored in every settings state. |

The local normalizer recovers raw L/R and distinguishes physical A from synthetic L=A. It leaves global input mode intact; a changed Controls value takes effect after Apply. One press produces one action, in this priority: B, real A, X, Y, L/R, direction. L+R and opposing directions cancel; new input overrides repeat in the same family. L+A preserves physical A. Entry and return wait for confirm-button release. Lid/resume tests must not reuse stale raw masks.

## Target and hunt

Target lists locally seen species for the current method, plus None. An empty list explains recovery rather than claiming save corruption. A changes the draft and returns to Target; B discards only the selector's local choice and returns to that same row.

Pro Hunt shows Pokémon, Method, Successes, Odds and Steps x/40. The last three are read-only state. Method and Target are editable; the command is **Prepare hunt**. It requires Pro, a valid species and 40 steps. A mode/target change that has not been applied has effective charge zero. A prepares only the draft, returns to Pro Hunt in the main list and marks it pending. X Apply lists changed groups and any prepared hunt. Only after confirmation, exit and an available field does the owner start the encounter under its existing conditions. Changing mode, species or method invalidates a prepared hunt. Rules are explained in Guide/Info rather than a separate settings row.

## Transaction

Native, Plus and Shiny have separate temporary snapshots/drafts and a dirty mask. Validate only changed groups: an absent Plus owner must not prevent native audio changes. Its controls remain readable but disabled.

Check application/generation, snapshot, value domains, owners and context. Prepare without side effects. Run the fallible Shiny part with refusal atomicity, then commit Native/Plus under valid preconditions with deterministic writes that cannot fail. If an adapter cannot establish this contract, it needs prepare/commit support before integration. Comparing all group bytes on refusal prevents partial application.

Refusal preserves menu and draft, explains recovery and applies no other group. A clean root exits immediately with B. A dirty root offers Apply/Discard/Continue with Continue selected. Discard restores snapshot and preview; Continue retains the draft. Apply updates RAM/operating state; disk persistence follows normal SAVE.

## Graphics lifecycle

Intercept before the first native presentation: input hook `0x021E6820` is too late. Authenticate lifecycle and entry through preimages, symbols and EN/IT bytes. One owner controls LCD swap, BG/OBJ, palettes, VBlank, Window, font and printer. The lower Poké Ball remains static in selectors, Info, confirmations and errors. Restore field/callback state and free only owned resources.

Text/frame previews belong above; audio and preview changes are reversible. Printers must not write reassigned tiles. Allocation failure closes without Apply. Compose before transfer and update changed rows/values rather than clearing the visible panel for each move; no stale-title or partial-row frames are acceptable. The legacy payload used 3,772/3,776 bytes; the extension budget is 8,192. Measure before installation and reallocate only with a map, guards and composition proof.

## Acceptance requirements

Cover EN/IT, every option/transition, edges/sections, normal/L=A, simultaneous/held input, empty/full lists, Classic↔Pro, absent/refusing owners, rollback/preview and inert touch. Native settings must work without Plus, without clearing or initializing settings to expose UI.

Final validation uses melonDS Android on the Mac, before/after, both languages and copies of older raw saves: Continue → UI → SAVE → cold startup, comparing progress, options and expanded Bag data. Record APK, profile, ROM and tool identities. Rounded capped FPS and headless throughput do not establish zero cost; use comparable scenes/samples and explicit limits. Repeat UI on the composed 1.3.1 after mechanics integration. Requirements are not evidence of completed coverage.
