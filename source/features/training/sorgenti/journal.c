#include "internal.h"

static sgp_train_u16 get16(const sgp_train_u8 *p)
{
    return (sgp_train_u16)(p[0] | ((sgp_train_u16)p[1] << 8));
}
static sgp_train_u32 get32(const sgp_train_u8 *p)
{
    return (sgp_train_u32)get16(p) | ((sgp_train_u32)get16(p + 2) << 16);
}
static sgp_train_u64 get64(const sgp_train_u8 *p)
{
    return (sgp_train_u64)get32(p) | ((sgp_train_u64)get32(p + 4) << 32);
}
static void put16(sgp_train_u8 *p, sgp_train_u16 v)
{
    p[0] = (sgp_train_u8)v; p[1] = (sgp_train_u8)(v >> 8);
}
static void put32(sgp_train_u8 *p, sgp_train_u32 v)
{
    put16(p, (sgp_train_u16)v); put16(p + 2, (sgp_train_u16)(v >> 16));
}
static void put64(sgp_train_u8 *p, sgp_train_u64 v)
{
    put32(p, (sgp_train_u32)v); put32(p + 4, (sgp_train_u32)(v >> 32));
}
static sgp_train_u32 crc32(const sgp_train_u8 *p)
{
    sgp_train_u32 crc = 0xffffffffu;
    unsigned i, bit;
    for (i = 0; i < 252; i++) {
        crc ^= p[i];
        for (bit = 0; bit < 8; bit++)
            crc = (crc >> 1) ^ ((0u - (crc & 1)) & 0xedb88320u);
    }
    return ~crc;
}
static int valid(const sgp_train_journal *s)
{
    unsigned i;
    if (!s || s->flags > SGP_TRAIN_SHINY_ONLY || s->policy > SGP_TRAIN_UNLIMITED ||
        s->default_clock > SGP_TRAIN_RTC || s->initialization_version != 1 ||
        s->reserved || !s->next_serial || s->claims & ~0x3ffffu ||
        s->pending_silver > 999 || s->pending_gold > 999 ||
        s->shiny_target > 493 || s->shiny_chain > 40 || s->shiny_mode > 1 ||
        s->shiny_initialized > 1 || (!s->shiny_initialized && s->shiny_rng) ||
        ((!s->shiny_target || !s->shiny_mode) && s->shiny_chain) ||
        !sgp_train_is_zero(s->shiny_reserved, 7)) return 0;
    if (s->flags && (s->policy || s->claims || s->league_seen ||
        s->pending_silver || s->pending_gold || s->jobs[0].active || s->jobs[1].active)) return 0;
    for (i = 0; i < 2; i++) {
        if (sgp_train_job_validate(&s->jobs[i], s->policy) != SGP_TRAIN_OK ||
            (s->jobs[i].active && s->jobs[i].serial >= s->next_serial)) return 0;
    }
    return !s->jobs[0].active || !s->jobs[1].active ||
        s->jobs[0].serial != s->jobs[1].serial;
}
void sgp_train_defaults(sgp_train_journal *out)
{
    if (!out) return;
    sgp_train_zero(out, sizeof(*out));
    out->default_clock = SGP_TRAIN_RTC;
    out->initialization_version = 1;
    out->next_serial = 1;
}
static void encode_job(const sgp_train_job *j, sgp_train_u8 *p)
{
    put32(p, j->serial); put32(p + 4, j->personality); put32(p + 8, j->ot);
    put16(p + 12, j->species); p[14] = j->active; p[15] = j->clock;
    p[16] = j->kinds; p[17] = j->start_level; p[18] = j->target_level; p[19] = j->stat;
    put32(p + 20, j->baseline_exp); put32(p + 24, j->steps_at_enrollment);
    put32(p + 28, j->level_quanta_settled); put64(p + 32, j->anchor);
    put64(p + 40, j->credited);
    sgp_train_copy(p + 48, j->baseline_evs, 6); sgp_train_copy(p + 54, j->target_evs, 6);
    put32(p + 60, j->ev_period); put16(p + 64, j->ev_points);
    put16(p + 66, j->reserved16); put32(p + 68, j->ev_quanta_settled);
    put32(p + 72, j->reserved0); put32(p + 76, j->reserved1);
}
static void decode_job(const sgp_train_u8 *p, sgp_train_job *j)
{
    j->serial = get32(p); j->personality = get32(p + 4); j->ot = get32(p + 8);
    j->species = get16(p + 12); j->active = p[14]; j->clock = p[15];
    j->kinds = p[16]; j->start_level = p[17]; j->target_level = p[18]; j->stat = p[19];
    j->baseline_exp = get32(p + 20); j->steps_at_enrollment = get32(p + 24);
    j->level_quanta_settled = get32(p + 28); j->anchor = get64(p + 32);
    j->credited = get64(p + 40);
    sgp_train_copy(j->baseline_evs, p + 48, 6); sgp_train_copy(j->target_evs, p + 54, 6);
    j->ev_period = get32(p + 60); j->ev_points = get16(p + 64);
    j->reserved16 = get16(p + 66); j->ev_quanta_settled = get32(p + 68);
    j->reserved0 = get32(p + 72); j->reserved1 = get32(p + 76);
}
int sgp_train_encode(const sgp_train_journal *s, sgp_train_u8 out[256])
{
    if (!out || !valid(s)) return SGP_TRAIN_INVALID;
    /* No fallible operation after output mutation starts. Buffers must not alias. */
    sgp_train_zero(out, 256);
    put32(out, 0x31524e54); put16(out + 4, 2); put16(out + 6, 256);
    put32(out + 8, s->generation); put16(out + 12, s->main_crc);
    put16(out + 14, s->flags); out[16] = s->policy; out[17] = s->default_clock;
    out[18] = s->initialization_version;
    put32(out + 20, s->next_serial); put64(out + 24, s->played);
    put64(out + 32, s->last_rtc); put32(out + 40, s->claims);
    put32(out + 44, s->league_seen); put16(out + 48, s->pending_silver);
    put16(out + 50, s->pending_gold);
    encode_job(&s->jobs[0], out + 64); encode_job(&s->jobs[1], out + 144);
    put32(out + 224, s->shiny_rng); put16(out + 228, s->shiny_target);
    out[230] = s->shiny_chain; out[231] = s->shiny_mode;
    out[232] = s->shiny_initialized;
    put32(out + 252, crc32(out));
    return SGP_TRAIN_OK;
}
int sgp_train_decode(const sgp_train_u8 bytes[256], sgp_train_u32 generation,
    sgp_train_u16 main_crc, sgp_train_journal *out)
{
    sgp_train_journal s;
    unsigned i, version;
    int all_zero = 1, all_ff = 1;
    if (!bytes || !out) return SGP_TRAIN_CORRUPT;
    for (i = 0; i < 256; i++) { all_zero &= bytes[i] == 0; all_ff &= bytes[i] == 255; }
    if (all_zero || all_ff) return SGP_TRAIN_ERASED;
    version = get16(bytes + 4);
    if (get32(bytes) != 0x31524e54 || (version != 1 && version != 2) ||
        get16(bytes + 6) != 256) return SGP_TRAIN_FOREIGN;
    if (get32(bytes + 252) != crc32(bytes) ||
        !sgp_train_is_zero(bytes + 52, 12) ||
        (version == 1 ? !sgp_train_is_zero(bytes + 224, 28) :
                        !sgp_train_is_zero(bytes + 233, 19)))
        return SGP_TRAIN_CORRUPT;
    sgp_train_zero(&s, sizeof(s));
    s.generation = get32(bytes + 8); s.main_crc = get16(bytes + 12);
    s.flags = get16(bytes + 14); s.policy = bytes[16]; s.default_clock = bytes[17];
    s.initialization_version = bytes[18]; s.reserved = bytes[19];
    s.next_serial = get32(bytes + 20); s.played = get64(bytes + 24);
    s.last_rtc = get64(bytes + 32); s.claims = get32(bytes + 40);
    s.league_seen = get32(bytes + 44); s.pending_silver = get16(bytes + 48);
    s.pending_gold = get16(bytes + 50);
    decode_job(bytes + 64, &s.jobs[0]); decode_job(bytes + 144, &s.jobs[1]);
    if (version == 2) {
        s.shiny_rng = get32(bytes + 224); s.shiny_target = get16(bytes + 228);
        s.shiny_chain = bytes[230]; s.shiny_mode = bytes[231];
        s.shiny_initialized = bytes[232];
    }
    if ((version == 1 && s.flags) || !valid(&s)) return SGP_TRAIN_CORRUPT;
    if (s.generation != generation || s.main_crc != main_crc) return SGP_TRAIN_MISMATCH;
    sgp_train_copy(out, &s, sizeof(s));
    return SGP_TRAIN_VALID;
}
int sgp_train_select(const sgp_train_u8 primary[256], const sgp_train_u8 mirror[256],
    sgp_train_u32 generation, sgp_train_u16 main_crc, sgp_train_journal *out,
    sgp_train_u8 *source, sgp_train_u8 *writable)
{
    sgp_train_journal a, b;
    int x, y;
    if (!primary || !mirror || !out || !source || !writable) return SGP_TRAIN_CORRUPT;
    x = sgp_train_decode(primary, generation, main_crc, &a);
    y = sgp_train_decode(mirror, generation, main_crc, &b);
    *source = 255;
    *writable = x != SGP_TRAIN_CORRUPT && x != SGP_TRAIN_FOREIGN &&
        y != SGP_TRAIN_CORRUPT && y != SGP_TRAIN_FOREIGN;
    if (x == SGP_TRAIN_VALID || y == SGP_TRAIN_VALID) {
        *source = x == SGP_TRAIN_VALID ? 0 : 1;
        sgp_train_copy(out, *source ? &b : &a, sizeof(*out));
        return SGP_TRAIN_VALID;
    }
    if (x == SGP_TRAIN_FOREIGN || y == SGP_TRAIN_FOREIGN) return SGP_TRAIN_FOREIGN;
    if (x == SGP_TRAIN_CORRUPT || y == SGP_TRAIN_CORRUPT) return SGP_TRAIN_CORRUPT;
    if (x == SGP_TRAIN_MISMATCH || y == SGP_TRAIN_MISMATCH) return SGP_TRAIN_MISMATCH;
    sgp_train_defaults(out);
    return SGP_TRAIN_ERASED;
}
int sgp_train_queue_reward(sgp_train_journal *state, sgp_train_u8 claim_bit,
    sgp_train_u16 silver, sgp_train_u16 gold, sgp_train_u32 league_seen)
{
    sgp_train_u32 mask = 0;
    if (!valid(state) || state->flags || (claim_bit > 17 && claim_bit != 255) ||
        (!silver && !gold) || league_seen < state->league_seen) return SGP_TRAIN_INVALID;
    if (claim_bit != 255) {
        mask = 1u << claim_bit;
        if (state->claims & mask) return SGP_TRAIN_NO_CHANGE;
    } else if (league_seen == state->league_seen) return SGP_TRAIN_NO_CHANGE;
    if ((sgp_train_u32)state->pending_silver + silver > 999 ||
        (sgp_train_u32)state->pending_gold + gold > 999) return SGP_TRAIN_OVERFLOW;
    state->pending_silver += silver; state->pending_gold += gold;
    state->claims |= mask; state->league_seen = league_seen;
    return SGP_TRAIN_OK;
}
int sgp_train_reward_delivered(sgp_train_journal *state,
    sgp_train_u16 silver, sgp_train_u16 gold)
{
    if (!valid(state)) return SGP_TRAIN_INVALID;
    if (silver > state->pending_silver || gold > state->pending_gold) return SGP_TRAIN_PAYMENT;
    if (!silver && !gold) return SGP_TRAIN_NO_CHANGE;
    state->pending_silver -= silver; state->pending_gold -= gold;
    return SGP_TRAIN_OK;
}
