# Camera policy

The inherited Plus hook selects a camera type from a sorted exception table or
returns default 11. With the low state byte zero it uses native map headers.
The current composer changes the table and two literal-pool pointers, retaining
the original instructions, ABI, state address and save behavior.

[Source, exact-ROM attribution and repeatable checks](../../docs/validation/camera-source-rom-1.3.2.md)
cover the recovered assembly, both build layouts, native callers, independent
readback and isolated execution. Start there for input identities and commands.

- `sorgenti/camera.S`: recovered project assembly with technical comments.
- `tools/compila.py`: generate constants, assemble and load `.text`; no ROM output.
- `tools/attribuisci.py`: exact base/retail/r4 admission, two ARM9 readers,
  source-build readback, exception/canary and execution checks.
- `tools/oracolo.py`: execute installed hook bytes, check values, native bounds
  normalization, assertion count, return, ABI and stack writes.
- `source/sgp12/blocchi/camera.py`: production composition and stage readback.

The older `rileggi_camera.py`, `applica_camera.py` and `mutanti.py` describe a
camera-only intermediate stage. Their whole-image delta constraints do not
apply to the final r4 image, which contains other features. The final-image
attribution reader uses their address reader, with a separate ndspy crosscheck,
and limits its conclusions to the camera component. No allocation is reclaimed.
