#ifndef SGP_SHINY_CORE_H
#define SGP_SHINY_CORE_H

typedef unsigned char SgpShinyU8;
typedef unsigned short SgpShinyU16;
typedef unsigned int SgpShinyU32;

/* Owner-copied logical state. The persistent wire serializer is separate. */
typedef struct {
    SgpShinyU32 rng;
    SgpShinyU16 target;
    SgpShinyU8 chain, mode, initialized, reserved[7];
} SgpShinySaved;
typedef char SgpShinySavedSizeMustBe16[(sizeof(SgpShinySaved) == 16) ? 1 : -1];
typedef char SgpShinyWordSizeMustBe4[(sizeof(SgpShinyU32) == 4) ? 1 : -1];

int sgp_shiny_valid(const SgpShinySaved *s);
SgpShinyU32 sgp_shiny_denominator(const SgpShinySaved *s,
                                SgpShinyU32 species, SgpShinyU32 base_only);
int sgp_shiny_select(SgpShinySaved *s, SgpShinyU32 mode, SgpShinyU32 target);
/* Only the adapter admits an ordinary completed battle, exactly once. */
int sgp_shiny_complete(SgpShinySaved *s, SgpShinyU32 species, SgpShinyU32 result);
int sgp_shiny_draw(SgpShinySaved *s, SgpShinyU32 native_seed,
                   SgpShinyU32 full_ot, SgpShinyU32 species,
                   SgpShinyU32 base_only, SgpShinyU32 *shiny, SgpShinyU32 *offset);
int sgp_shiny_transform(SgpShinyU32 pid, SgpShinyU32 full_ot,
                       SgpShinyU32 shiny, SgpShinyU32 offset, SgpShinyU32 *out);
#endif
