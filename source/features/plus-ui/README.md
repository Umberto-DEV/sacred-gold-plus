# Native Plus presentation

This layer reuses the existing Options/Continue controller and save layout. It
changes the Plus title and selection colors and supplies a two-line explanation
in the native Options frame preview. An always-visible footer button opens Plus
by touch, and SELECT remains the controller shortcut. No game graphics or
extracted text assets are stored here.

The context helper owns code at `0x023D7700..0x023D7880`; encoded labels occupy
`0x023D7880..0x023D7B00`. The installer checks both bounds, the original controller
and template preimages, the native font palette and the native preview-printer
ABI. The main controller remains in its existing 3776-byte compartment.

The navigation helper owns `0x023D7500..0x023D7700` (250 compiled bytes in a
512-byte compartment). Its painter uses the checked native font palette,
white text and an inset blue button with a dark border and light upper edge.
The existing temporary hint Window is now 14 by 3 tiles at `(0,21)`, beside the
native Confirm/Quit buttons. It reuses the Plus page's tile allocation while
Plus is closed, creates no persistent allocation, and redraws after the native
app reuses its heap address. The touch bounds are `4 <= x < 112` and
`172 <= y < 192`; outside or held touches follow the original native handler.
The native cursor, pending Options values and Confirm/Quit semantics stay with
the native controller. Plus retains its separate A-apply and B-cancel transaction.

Native Options has fixed row, sprite and touch tables, and its pending options
are committed separately from Plus settings. The visible button is the chosen
entry point. The two pages inside Plus share one pending Plus transaction;
vanilla Options remains separate. `ui_common.c` folds the 1.3 visual overrides into a single printer
body to keep the original controller compartment within its fixed bound.
Stable 1.2.5 controller source and save identifiers remain unchanged.

Before replacing the preview tiles, the helper checks the current app's printer
ID, its active task and that task's target Window. Only a printer bound to this
app's original preview is completed through the native immediate-render path.
This removes that queued printer and finishes the original pixel buffer. The
existing close path then restores the complete preview; a later Text Speed
change can start a new asynchronous preview normally. Foreign printer tasks
remain untouched. Acquisition occurs after the helper's temporary allocations
succeed, so failed context allocation leaves the preview running.

Run the focused tests from the repository root:

```sh
.venv/bin/python -m unittest discover -s source/features/plus-ui/test -v
```

These execute the compiled ARM helper with native API seams, checking owned and
foreign printers, inactive/invalid IDs, allocation failures, original Window
fields, completed original pixels and all five context rows. Unicorn requires
an executable JIT environment. The navigation tests also execute both native
hook return paths, including their stack/register contract, touch boundaries,
pixel-allocation guards, re-entry and separate native/Plus settings transactions.
Native runtime acceptance additionally needs
Text Speed change followed immediately by SELECT, delayed context captures,
B/SELECT restoration and a subsequent animated speed preview in both languages.
Settled-preview navigation and normal Options return must continue to work.

The active-preview race was verified with this sequence on both EN and IT.
This focused UI coverage does not establish raw-save migration, Continue prompt,
rejected Plus data or whole-release compatibility; those require the integrated
release campaign.

## Shiny second page

`extended.c` and `hunt_panel.c` reuse the old controller through the versioned
shiny owner API. Code at 0x023CB800 (8192-byte bound), EN/IT text at 0x023CD800
(4096-byte bound) and transient state at 0x023CE800 (256-byte bound) have separate
reserved owners. The legacy five-setting state and Continue templates stay fixed.
L/R and header touch navigate clamped pages; each page retains its cursor.
B/SELECT cancels first, then fresh touch takes precedence over physical navigation
and apply. Allocation failure cancels pending changes and releases owned resources.

The second page shows Classic/Pro, target, completed successes, next-target odds
and Hunt. Hunt provides current eligible species, method, step charge, staged
search and three rules pages. A on the root applies the whole draft; a method-only
change also reaches the owner without resetting chain. The owner launches a queued
search only after Options closes and the field is idle. Ineligible locations and
missing seen candidates have explicit feedback; absent storage never displays
a valid shiny rate. All 493 native species names and both authored text banks
are measured against the native font during installation.

See [mechanics and integration evidence](../../docs/shiny-species-1.3.md).
