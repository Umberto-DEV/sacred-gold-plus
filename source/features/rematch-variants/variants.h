#ifndef SGP_REMATCH_VARIANTS_H
#define SGP_REMATCH_VARIANTS_H
/* Plus-only complete-party variants for the two ordinary rematches (trainer IDs
 * 712 and 713). The core edits only the transient 108-byte party buffer that the
 * native constructor has just loaded; it allocates nothing, reads no player or
 * save data, never touches the RNG and calls no native function. */
typedef unsigned char rv_u8;
typedef unsigned short rv_u16;
typedef unsigned int rv_u32;
typedef __UINTPTR_TYPE__ rv_uptr;

#define RV_MAGIC 0x31564D52u          /* "RMV1" little endian */
#define RV_PARTY 108u                 /* six type-3 members, 18 bytes each */
#define RV_SLOT 18u
#define RV_TYPE_COUNT 0x0306u         /* (trainer format 3 << 8) | six members */
#define RV_MAX_TRAINERS 4u
#define RV_SPECIES_MAX 493u
#define RV_MOVE_MAX 467u
#define RV_ITEM_MAX 515u              /* highest member of the item-data archive a/0/1/7 */

/* Config image: header, trainer descriptors, then three 108-byte parties per
 * trainer (baseline, variant A, variant B). Offsets are relative to the header. */
typedef struct {
    rv_u32 magic;
    rv_u16 bytes;               /* total image size */
    rv_u8 active;               /* 0 = wrapper only forwards to the native loader */
    rv_u8 trainers;             /* 1..RV_MAX_TRAINERS */
    rv_u8 battle_type_count;    /* exact allowed battleType values, 0..2 */
    rv_u8 enemy_index_mask;     /* bit n = enemy party index n is allowed */
    rv_u16 reserved;            /* zero */
    rv_u32 battle_types[2];
} RvHeader;                     /* 20 bytes */

typedef struct {
    rv_u16 trainer;
    rv_u16 type_count;
    rv_u16 base, a, b;          /* offsets of the three parties */
    rv_u16 reserved;            /* zero */
    rv_u32 base_hash, a_hash, b_hash;  /* FNV-1a 32 of each party */
} RvTrainer;                    /* 24 bytes */

rv_u32 rematch_select(rv_u32 seed, rv_u32 trainer);
int rematch_apply(rv_u8 *buffer, rv_u32 trainer, rv_u32 type_count, rv_u32 plus,
                  rv_u32 seed, const void *config, rv_u32 config_bytes);
#endif
