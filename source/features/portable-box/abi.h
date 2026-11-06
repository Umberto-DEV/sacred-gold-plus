#ifndef SGP_PORTABLE_BOX_ABI_H
#define SGP_PORTABLE_BOX_ABI_H
/* Portable box ABI (Sacred Gold Plus 1.3.1). Native addresses and structure
 * offsets are pinned in sgp131/data/portable-native-abi.json (candidate V4
 * EN/IT, identical bytes). Nothing here is persistent: the state lives in the
 * installed compartment (RAM), never in the save.
 *
 * Pointers are kept as u32 addresses used only for IDENTITY comparison. The
 * record never holds a pointer to a Pokemon; party args are re-derived from
 * the live owner whenever they are used.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define SGP_BOX_STATE_MAGIC 0x31425053u /* "SPB1" little-endian */
#define SGP_BOX_CONFIG_MAGIC 0x31434253u /* "SBC1" */

/* phase */
#define SGP_BOX_PHASE_IDLE 0u
#define SGP_BOX_PHASE_BOUND 1u      /* ordinary party launched by the start menu */
#define SGP_BOX_PHASE_EXITING 2u    /* request accepted: native Cancel in progress */
#define SGP_BOX_PHASE_PC_RUNNING 3u /* native PC (mode 2) owns the field child */

/* sgp_box_eligibility() */
#define SGP_BOX_ELIGIBLE 0
#define SGP_BOX_WRONG_OWNER 1
#define SGP_BOX_BUSY 2
#define SGP_BOX_SPECIAL_ACTIVITY 3
#define SGP_BOX_UNPROVEN_TRAVEL 4
#define SGP_BOX_UNPROVEN_CONTEXT 5 /* additive extension of the plan's 0-4: no accepted context proof, deny by default */

/* Transient record, 64 bytes. The ONLY field a bench probe may write is
 * `requested`, after verifying owner/generation/args/phase (run_probe.py). */
typedef struct SgpBoxState {
    u32 magic;              /* 0x00 */
    u32 generation;         /* 0x04 incremented by every bind */
    u32 phase;              /* 0x08 */
    u32 requested;          /* 0x0C one pending request at most */
    u32 field;              /* 0x10 FieldSystem*  (identity) */
    u32 owner;              /* 0x14 StartMenuTaskData* (identity) */
    u32 args;               /* 0x18 PartyMenuArgs* (identity; may dangle) */
    u32 pc_args;            /* 0x1C PCBoxArgs* owned by this record */
    u32 selection;          /* 0x20 party slot kept across the PC visit */
    u32 reason;             /* 0x24 policy decision recorded at bind */
    u32 prompt_shown;       /* 0x28 suffix currently drawn */
    u32 request_generation; /* 0x2C generation captured when accepted */
    u32 allocs;             /* 0x30 balance counters for the 50-cycle probe */
    u32 frees;              /* 0x34 */
    u32 opens;              /* 0x38 completed PC launches */
    u32 failures;           /* 0x3C cancelled / failed requests */
} SgpBoxState;

/* Activation words (default all zero = byte-for-byte native behaviour). */
typedef struct SgpBoxConfig {
    u32 magic;              /* 0x00 */
    u32 bridge;             /* 0x04 allow requested -> PC -> new party */
    u32 input;              /* 0x08 physical R and touch raise a request */
    u32 prompt;             /* 0x0C draw the "R: Box" suffix */
    u32 refresh_field_data; /* 0x10 RESERVED: must stay 0 (see INTEGRATION.md) */
    u32 travel_mask;        /* 0x14 bit n = avatar state n allowed (default 3) */
    u32 context_proof;      /* 0x18 1 = the installer accepted a context proof (receipt) */
    u32 reserved;           /* 0x1C */
} SgpBoxConfig;

#define SGP_BOX_STATE_BYTES 64u
#define SGP_BOX_CONFIG_BYTES 32u

/* Public entries (all Thumb, AAPCS) */
void sgp_box_bind(void *field, void *args);
int sgp_box_party_main(void *party);
int sgp_box_party_return(void *task);
int sgp_box_pc_return(void *task);
int sgp_box_eligibility(void *field, void *owner);
void sgp_box_prompt(void *party, int reason);
#endif
