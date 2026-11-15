# Fairy support in the AI type consumers

`native.S` is the148-byte resident helper installed by
[`sgp131/fairy_ai.py`](../../sgp131/fairy_ai.py) in the named
`fairy-ai.code` subdivision of `training.extension`. It supplements the native
sparse chart only for type9 and shares its packed row/column decoder between
the flags hook and scalar tail.

The [flags source-to-ROM case](../../docs/validation/fairy-flags-source-rom-1.3.2.md)
reconstructs the ELF and two external BL fixes, reads the compressed final
overlay independently, and executes the complete flags function in exact r4
EN/IT. It attributes the additional HG-B13 immunity mask to AI scoring; testing
the Fairy payload alone would miss that dependency. The [scalar case](../../docs/validation/fairy-scalar-source-rom-1.3.2.md) follows
the complete native parent through real ARM division and the inline tail return:324
monotypes,25 literals and a duplicate-defender counterexample per language. It
records two inherited sparse/dense policy differences without changing policy.

Run `tools/attribuisci.py --help`. Use `--work DIR` for the protected compiler
and retained own-project ELF, or `--readback-only` to inspect installed bytes
and execution without claiming a local rebuild. A differing existing ELF or
build artifact is preserved and rejected; use a fresh work directory.
Production compilation still leaves no retained ELF unless requested explicitly.

The proof uses synthetic context, Move1, no abilities/items and bounded type
cases. Eight upstream callers are linked statically. This is neither eight
natural AI encounters nor a new performance, save or device qualification.

Run `tools/attribuisci_scalare.py --help`. Its `--build DIR` verifies and reuses
the canonical flags build; it never compiles or copies it. `--readback-only`
explicitly omits that provenance claim. Scalar inputs use type IDs0–17, no
allocated game context or save state; three upstream callers are static links.

The [post-KO caller case](../../docs/validation/postko-source-rom-1.3.2.md) links
`sgp131/ai_scoring.py` to the complete current selector, scalar calls, narrow
scratch and two native flags integrations. `tools/attribuisci_postko.py` reuses
the same canonical build and declared query models. Its per-move oracle rejects
a wrong immunity result even when the final slot is unchanged.
