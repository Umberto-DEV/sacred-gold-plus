# Offline installer source

Each player ZIP embeds this application in one `Install-or-update.html`, fixed to its language and camera. Open the extracted HTML in a current browser, select a supported `.nds`, and click **Check and create game** (**Controlla e crea il gioco** in Italian). When verification finishes, click **Download the verified game** (**Scarica il gioco verificato**). Selecting a file alone does not start processing. An already-current file produces a status message without a new download. It does not load files from the network or open a save. The original game file is read through the browser File API and never overwritten.

The application requires native `crypto.subtle` SHA-256, Blob workers and `File.arrayBuffer`. If these APIs are unavailable when opening a local HTML file, it displays an explicit compatibility message. Browser support and large-file memory use need testing on the platforms declared by the release; Node tests alone do not establish Android or Safari compatibility.

## Rendering contract

The Python packager replaces these tokens in `template.html`:

- `__LANG__`: `it` or `en`.
- `__TITLE__`: escaped title for this fixed variant, used in the document title and heading.
- `__DATA_JSON__`: HTML-safe JSON in `script#release-data[type="application/json"]`.
- `__APP_JS__`: unchanged `app.js`.
- `__WORKER_JSON__`: an HTML-safe JSON string containing the concatenation of `vendor/HashCalculator.js`, `vendor/BinFile.js`, `vendor/RomPatcher.format.vcdiff.js`, then `worker.js`, with newlines between files.

Keep the leading semicolon in `worker.js`: the unchanged preceding vendor file ends in a function assignment without a semicolon. Escape `<` in both JSON payloads so embedded strings cannot close their script element. The full MIT license is already included in the template.

The release data has schema `1`, version `1.04`, `target` and exactly four `sources`. The target contains `id`, `language` (`IT` or `US`), `camera` (`Normal Angle` or `New Angle`), `sha256`, `bytes`, and `output_name` such as `Sacred Gold Plus - New Angle - IT.nds`. The source IDs are `clean-us` for unmodified US HeartGold and `plus-1.01`, `plus-1.02`, `plus-1.03` for the supported English Plus versions; each has `label`, `sha256`, `bytes`, and `patch: {sha256, bytes, data}` with base64 data. Labels are display text, never an identification mechanism. The reviewed packager pins the real source and target fingerprints; this generic client validates the embedded contract rather than asserting that arbitrary metadata is an official release.

## Verification and worker messages

`app.js` first checks the selected file size against the embedded sources and target, before reading any bytes. It then checks the complete SHA-256. An exact target is a no-op; unknown inputs produce no download. For a source, it transfers the input buffer and selected metadata to a Blob worker. Other embedded deltas are not sent to the worker.

`worker.js` accepts `{input: ArrayBuffer, source, target}`. It rechecks the input hash/size, patch base64 size, patch SHA-256 and VCDIFF header, then uses the unchanged decoder. It checks full output SHA-256 and size before transferring `{type: 'ready', buffer}`. Progress messages have `{type: 'progress', stage}`; failures have `{type: 'error', code}` and no result buffer. The application only offers a download after `ready`.

The pinned VCDIFF module's optional legacy Adler check calls an external helper absent from these three files. The wrapper uses `apply(..., false)` and enforces complete SHA-256 plus byte count on both inputs and the final output instead. The vendor source is unchanged. Its historical sloppy-mode globals live only in the dedicated worker, which the application terminates after each operation. The application's own functions are scoped in an IIFE.

## Tests and provenance

Run with Node.js 20 or newer, without installing packages:

```sh
node --test source/installer/test_worker.cjs
```

In the development repository use `publishing/installer/test_worker.cjs`. Tests use only synthetic byte arrays and an embedded delta originally generated with xdelta3 3.1.0 (`-e -A -S none -D`). They exercise the real vendor decoder inside an isolated VM, source selection, an already-current file, rejection before reading, absent native crypto, altered hashes/sizes, immutable source bytes, and page-history interruption using a small DOM fixture. Those interruption tests cover pending reads, stopped workers, stale callbacks, restored controls and revoked downloads. They do not run a ROM, check gameplay, or prove behavior in an actual browser.

`vendor-manifest.json` records the exact four copied files from Marc Robledo's RomPatcher.js commit `3183884086825c3a57c72026234debcef1e2240c`. JS and LICENSE bytes were compared with that Git revision before copying. The MIT license applies to those vendor files; original application code follows the project's GPL-3.0-or-later license. No game data is present in these source files or tests.
