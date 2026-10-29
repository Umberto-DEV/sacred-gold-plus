#ifndef SGP_SHINY_API_H
#define SGP_SHINY_API_H
/* Explicit owner/UI contract. No native save pointer or other owner's state
 * layout is exported. Function addresses are installed by the guarded builder. */
#include "core.h"
#define SGP_SHINY_CONFIG 0x023CB100u
#define SGP_SHINY_MAGIC 0x594E4853u
#define SGP_SHINY_ABI 2u
#define SGP_SHINY_METHODS 5u
#define SGP_SHINY_MAX_CANDIDATES 12u
/* All errors retain unspent charge. Queued search is revalidated on the field. */
enum SgpShinyStatus { SGP_SHINY_OK, SGP_SHINY_UNAVAILABLE, SGP_SHINY_STALE,
    SGP_SHINY_NO_TARGET, SGP_SHINY_PRO_ONLY, SGP_SHINY_NEED_CHARGE,
    SGP_SHINY_BUSY, SGP_SHINY_GENERATION_FAILED };
typedef struct {
    SgpShinyU32 epoch, context, revision;
    SgpShinyU16 target, denominator;
    SgpShinyU8 available, mode, chain, charge, method_mask, status, method, reserved;
    SgpShinyU8 counts[5], padding[3];
} SgpShinySnapshot;
typedef struct {
    SgpShinyU32 epoch, context, revision;
    SgpShinyU16 target;
    SgpShinyU8 mode, method, search, reserved[3];
} SgpShinyDraft;
/* Public first20bytes; remaining entries are owner integration capabilities.
 * snapshot(app,out) fills32bytes, returns1 for current live owner,0 otherwise.
 * candidate(app,snapshot,method,index) returns species1..493 or0.
 * apply(app,draft) returns SgpShinyStatus. Never starts a battle from the UI. */
typedef struct {
    SgpShinyU32 magic;
    SgpShinyU16 abi, bytes;
    SgpShinyU32 snapshot, candidate, apply;
    SgpShinyU32 core_valid, core_denominator, core_select, core_complete;
    SgpShinyU32 core_draw, core_transform;
    SgpShinyU32 training_access, training_bind, training_read;
    SgpShinyU32 search_capture, search_dispatch;
    SgpShinyU32 legacy_frame, legacy_open, legacy_close, legacy_draw;
    SgpShinyU32 language;
    SgpShinyU16 species_count, species_reserved;
    /* Bit index equals species ID: only 1..493 may be set. */
    SgpShinyU8 species_bitmap[64];
} SgpShinyConfig;
_Static_assert(sizeof(SgpShinySnapshot)==32,"shiny snapshot ABI");
_Static_assert(sizeof(SgpShinyDraft)==20,"shiny draft ABI");
_Static_assert(__builtin_offsetof(SgpShinyConfig,species_count)==84,"shiny capability prefix");
_Static_assert(__builtin_offsetof(SgpShinyConfig,species_reserved)==86,"shiny reserved offset");
_Static_assert(__builtin_offsetof(SgpShinyConfig,species_bitmap)==88,"shiny bitmap offset");
_Static_assert(sizeof(SgpShinyConfig)==152,"shiny configuration ABI");
#endif
