sgp_chunk.h
    Copy of the canonical Plus chunk layout and sgp_chunk_opzione accessor.
sgp_anim4.h / anim_idle4.c / anim_blob4.c
    Historical v4 implementation. Its 752 code bytes remain resident in 1.3.2
    r4, but ANIM2 and the copy barrier replace the two original motion roots.
    Current motion is documented in source/features/anim2/README.md.
    The legacy allocation still contains a state guard referenced by Settings;
    resident code, active motion and removable space are different conclusions.
    See source/docs/validation/anim-v4-source-rom-1.3.2.md for exact rebuild,
    final-image readback, reference-scan coverage and remaining uncertainty.
    Earlier v3 sources are not distributed. Historical v4 design comments and
    tests retain their original scope; they do not establish current activation.
