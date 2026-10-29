#ifndef SGP_TRAINING_H
#define SGP_TRAINING_H
/* Stored stat order: HP, Attack, Defense, Speed, Sp. Attack, Sp. Defense.
 * All output arguments are unchanged on error unless explicitly documented.
 * No function reads/writes native Pokemon, Bag, flash, or clock hardware.
 * Struct input/output buffers must not overlap; six-byte array previews may
 * use identical input/output addresses. Callers guarantee buffer sizes. */
typedef unsigned char sgp_train_u8;
typedef unsigned short sgp_train_u16;
typedef unsigned int sgp_train_u32;
typedef unsigned long long sgp_train_u64;
typedef signed int sgp_train_s32;
enum sgp_train_result { SGP_TRAIN_OK, SGP_TRAIN_INVALID, SGP_TRAIN_EGG,
    SGP_TRAIN_NO_CHANGE, SGP_TRAIN_PAYMENT, SGP_TRAIN_OVERFLOW,
    SGP_TRAIN_IDENTITY, SGP_TRAIN_BUSY };
enum sgp_train_policy { SGP_TRAIN_LEGACY, SGP_TRAIN_CLASSIC, SGP_TRAIN_UNLIMITED };
enum sgp_train_clock { SGP_TRAIN_PLAY, SGP_TRAIN_RTC };
enum sgp_train_iv_kind { SGP_TRAIN_IV_EXACT, SGP_TRAIN_IV_SILVER, SGP_TRAIN_IV_GOLD };
enum sgp_train_record { SGP_TRAIN_ERASED, SGP_TRAIN_VALID, SGP_TRAIN_CORRUPT,
    SGP_TRAIN_FOREIGN, SGP_TRAIN_MISMATCH };
#define SGP_TRAIN_LEVEL 1
#define SGP_TRAIN_EV 2
#define SGP_TRAIN_RECORD_SIZE 256
/* v2 flag: journal exists for shiny state while training is still unactivated. */
#define SGP_TRAIN_SHINY_ONLY 1u

typedef struct {
    sgp_train_u32 serial, personality, ot;
    sgp_train_u16 species;
    sgp_train_u8 active, clock, kinds, start_level, target_level, stat;
    sgp_train_u32 baseline_exp, steps_at_enrollment, level_quanta_settled;
    sgp_train_u64 anchor, credited;
    sgp_train_u8 baseline_evs[6], target_evs[6];
    sgp_train_u32 ev_period;
    sgp_train_u16 ev_points, reserved16;
    sgp_train_u32 ev_quanta_settled, reserved0, reserved1;
} sgp_train_job;
typedef struct {
    sgp_train_u32 generation;
    sgp_train_u16 main_crc, flags;
    sgp_train_u8 policy, default_clock, initialization_version, reserved;
    sgp_train_u32 next_serial;
    sgp_train_u64 played, last_rtc;
    sgp_train_u32 claims, league_seen;
    sgp_train_u16 pending_silver, pending_gold;
    sgp_train_job jobs[2];
    /* Wire v2 extension at224; v1 decodes with Classic/uninitialized defaults.
     * This is a private in-RAM representation, never dumped into the save. */
    sgp_train_u32 shiny_rng;
    sgp_train_u16 shiny_target;
    sgp_train_u8 shiny_chain, shiny_mode, shiny_initialized, shiny_reserved[7];
} sgp_train_journal;
typedef struct {
    sgp_train_u8 level, evs[6];
    sgp_train_u32 remaining_seconds;
} sgp_train_projection;

/* Cost is one of the selected cap; Gold ignores stat/value, Silver ignores value.
 * valid_data and is_egg must be booleans; native adapter validates checksums. */
int sgp_train_iv_preview(const sgp_train_u8 before[6], sgp_train_u8 kind,
    sgp_train_u8 stat, sgp_train_u8 value, sgp_train_u8 is_egg,
    sgp_train_u8 valid_data, sgp_train_u8 after[6], sgp_train_u8 *cost);
int sgp_train_payment(sgp_train_u16 available, sgp_train_u16 cost,
    sgp_train_u16 *remaining);
/* Positive Legacy vitamins cap at100, other Legacy gains at255; all negatives
 * touch only selected stat and clamp at0, even on an over-total Pokemon. */
int sgp_train_ev_delta(const sgp_train_u8 before[6], sgp_train_u8 policy,
    sgp_train_u8 stat, sgp_train_s32 delta, sgp_train_u8 vitamin,
    sgp_train_u8 after[6]);
int sgp_train_ev_allocate(const sgp_train_u8 target[6], sgp_train_u8 policy,
    sgp_train_u8 after[6]);
/* Predicate returns1/0, including0 for invalid policy/pointers. Storage adapter
 * must check party, PC, Day Care and all other owned storage before switch. */
int sgp_train_mode_fits(const sgp_train_u8 evs[6], sgp_train_u8 policy);
/* UI order HP/Atk/Def/SpA/SpD/Speed -> stored index, 255 for invalid index. */
sgp_train_u8 sgp_train_stat_from_ui(sgp_train_u8 index);

/* Active job validation, pure projection, bounded credit reconciliation.
 * v1 deferred settlement requires both settled counters=0. EV course uses
 * 32 points/3600s on one stat. Disabled EV targets/rates are canonical zero.
 * Clock changes settle old_now before anchoring new_now, preserving remainder. */
int sgp_train_job_validate(const sgp_train_job *job, sgp_train_u8 policy);
int sgp_train_project(const sgp_train_job *job, sgp_train_u8 policy,
    sgp_train_projection *out);
int sgp_train_advance(sgp_train_job *job, sgp_train_u8 policy, sgp_train_u64 now);
int sgp_train_switch_clock(sgp_train_job *job, sgp_train_u8 policy,
    sgp_train_u64 old_now, sgp_train_u8 new_clock, sgp_train_u64 new_now);
int sgp_train_identity(const sgp_train_job *job, sgp_train_u32 serial,
    sgp_train_u32 personality, sgp_train_u32 ot, sgp_train_u16 species);
/* Validate both slots; matching identity required before removing active job.
 * Native withdrawal of a non-enrolled slot uses an inactive expected identity.
 * Removing slot0 compacts slot1, matching native Day Care order. */
int sgp_train_withdraw(sgp_train_job jobs[2], sgp_train_u8 policy,
    sgp_train_u8 slot, const sgp_train_job *expected);

/* Defaults are in RAM only: Legacy, RTC, init1, next_serial1. */
void sgp_train_defaults(sgp_train_journal *out);
int sgp_train_encode(const sgp_train_journal *state, sgp_train_u8 out[256]);
int sgp_train_decode(const sgp_train_u8 bytes[256], sgp_train_u32 generation,
    sgp_train_u16 main_crc, sgp_train_journal *out);
/* VALID primary wins, else matching VALID mirror. Neither other generation nor
 * corrupt/foreign bytes become defaults. Both ERASED -> defaults + ERASED.
 * writable=1 only if BOTH records are understood VALID/MISMATCH/ERASED;
 * unknown/corrupt sibling forbids overwrite even if a valid copy was selected.
 * source is0 primary,1 mirror,255 no record. Output state changes only VALID or
 * ERASED. Decode/select statuses are sgp_train_record, not sgp_train_result. */
int sgp_train_select(const sgp_train_u8 primary[256], const sgp_train_u8 mirror[256],
    sgp_train_u32 generation, sgp_train_u16 main_crc, sgp_train_journal *out,
    sgp_train_u8 *source, sgp_train_u8 *writable);
/* Atomic queue additions; overflow rejects without claiming a reward.
 * claim_bit is0..17 (one-time) or255 (repeat); league_seen must not decrease.
 * Bit0..15 badges,16 first League,17 first Red. Reward amounts passed by adapter. */
int sgp_train_queue_reward(sgp_train_journal *state, sgp_train_u8 claim_bit,
    sgp_train_u16 silver, sgp_train_u16 gold, sgp_train_u32 league_seen);
/* Acknowledge ONLY after the native adapter atomically grants these items. */
int sgp_train_reward_delivered(sgp_train_journal *state,
    sgp_train_u16 silver, sgp_train_u16 gold);
#endif
