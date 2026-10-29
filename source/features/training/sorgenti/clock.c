#include "internal.h"

typedef char job_layout_must_be_80_bytes[sizeof(sgp_train_job) == 80 ? 1 : -1];

static sgp_train_u32 duration(const sgp_train_job *job)
{
    sgp_train_u32 level = 0, ev = 0;
    if (job->kinds & SGP_TRAIN_LEVEL)
        level = (job->target_level - job->start_level) * 7200u;
    if (job->kinds & SGP_TRAIN_EV)
        ev = ((job->target_evs[job->stat] - job->baseline_evs[job->stat] + 31u) >> 5) * 3600u;
    return level > ev ? level : ev;
}

int sgp_train_job_validate(const sgp_train_job *job, sgp_train_u8 policy)
{
    unsigned i;
    if (!job || policy > SGP_TRAIN_UNLIMITED) return SGP_TRAIN_INVALID;
    if (!job->active)
        return sgp_train_is_zero(job, sizeof(*job)) ? SGP_TRAIN_OK : SGP_TRAIN_INVALID;
    if (job->active != 1 || !job->serial || !job->species || job->species > 493 ||
        job->clock > SGP_TRAIN_RTC || !job->kinds || job->kinds > 3 ||
        !job->start_level || job->start_level > 100 ||
        job->target_level < job->start_level || job->target_level > 100 ||
        job->reserved16 || job->reserved0 || job->reserved1 ||
        job->level_quanta_settled || job->ev_quanta_settled) return SGP_TRAIN_INVALID;
    if (!(job->kinds & SGP_TRAIN_LEVEL) && job->target_level != job->start_level)
        return SGP_TRAIN_INVALID;
    if (job->kinds & SGP_TRAIN_EV) {
        if (job->stat > 5 || job->ev_period != 3600 || job->ev_points != 32 ||
            !sgp_train_mode_fits(job->target_evs, policy) ||
            job->target_evs[job->stat] < job->baseline_evs[job->stat])
            return SGP_TRAIN_INVALID;
        for (i = 0; i < 6; i++) {
            if (job->target_evs[i] > 252 ||
                (i != job->stat && job->target_evs[i] != job->baseline_evs[i]))
                return SGP_TRAIN_INVALID;
        }
    } else if (job->stat != 255 || job->ev_period || job->ev_points ||
        !sgp_train_is_zero(job->target_evs, 6)) return SGP_TRAIN_INVALID;
    if (job->credited > duration(job)) return SGP_TRAIN_INVALID;
    return SGP_TRAIN_OK;
}

/* Bounded by99 level quanta /198 EV quanta: no ARM EABI division dependency. */
static sgp_train_u32 quanta(sgp_train_u32 seconds, sgp_train_u32 period)
{
    sgp_train_u32 n = 0;
    /* Keep Clang from replacing the bounded loop with __aeabi_uidiv. */
    volatile sgp_train_u32 remaining = seconds;
    while (remaining >= period) { remaining -= period; n++; }
    return n;
}

int sgp_train_project(const sgp_train_job *job, sgp_train_u8 policy,
    sgp_train_projection *out)
{
    unsigned i;
    sgp_train_u32 value;
    if (!out || sgp_train_job_validate(job, policy) != SGP_TRAIN_OK || !job->active)
        return SGP_TRAIN_INVALID;
    out->level = job->start_level;
    for (i = 0; i < 6; i++) out->evs[i] = job->baseline_evs[i];
    if (job->kinds & SGP_TRAIN_LEVEL) {
        value = job->start_level + quanta((sgp_train_u32)job->credited, 7200);
        out->level = (sgp_train_u8)(value > job->target_level ? job->target_level : value);
    }
    if (job->kinds & SGP_TRAIN_EV) {
        value = job->baseline_evs[job->stat] + quanta((sgp_train_u32)job->credited, 3600) * 32;
        out->evs[job->stat] = (sgp_train_u8)(value > job->target_evs[job->stat] ?
            job->target_evs[job->stat] : value);
    }
    out->remaining_seconds = duration(job) - (sgp_train_u32)job->credited;
    return SGP_TRAIN_OK;
}

int sgp_train_advance(sgp_train_job *job, sgp_train_u8 policy, sgp_train_u64 now)
{
    sgp_train_u32 remaining;
    sgp_train_u64 elapsed;
    if (sgp_train_job_validate(job, policy) != SGP_TRAIN_OK || !job->active)
        return SGP_TRAIN_INVALID;
    remaining = duration(job) - (sgp_train_u32)job->credited;
    elapsed = now > job->anchor ? now - job->anchor : 0;
    job->credited += elapsed > remaining ? remaining : elapsed;
    job->anchor = now;
    return SGP_TRAIN_OK;
}

int sgp_train_switch_clock(sgp_train_job *job, sgp_train_u8 policy,
    sgp_train_u64 old_now, sgp_train_u8 new_clock, sgp_train_u64 new_now)
{
    int result;
    if (new_clock > SGP_TRAIN_RTC) return SGP_TRAIN_INVALID;
    result = sgp_train_advance(job, policy, old_now);
    if (result != SGP_TRAIN_OK) return result;
    job->clock = new_clock;
    job->anchor = new_now;
    return SGP_TRAIN_OK;
}

int sgp_train_identity(const sgp_train_job *job, sgp_train_u32 serial,
    sgp_train_u32 personality, sgp_train_u32 ot, sgp_train_u16 species)
{
    return job && job->active == 1 && job->serial == serial &&
        job->personality == personality && job->ot == ot && job->species == species;
}

int sgp_train_withdraw(sgp_train_job jobs[2], sgp_train_u8 policy,
    sgp_train_u8 slot, const sgp_train_job *expected)
{
    if (!jobs || !expected || slot > 1 ||
        sgp_train_job_validate(&jobs[0], policy) != SGP_TRAIN_OK ||
        sgp_train_job_validate(&jobs[1], policy) != SGP_TRAIN_OK ||
        sgp_train_job_validate(expected, policy) != SGP_TRAIN_OK) return SGP_TRAIN_INVALID;
    if (jobs[slot].active != expected->active || (expected->active &&
        !sgp_train_identity(&jobs[slot], expected->serial, expected->personality,
            expected->ot, expected->species))) return SGP_TRAIN_IDENTITY;
    if (slot == 0) sgp_train_copy(&jobs[0], &jobs[1], sizeof(*jobs));
    sgp_train_zero(&jobs[1], sizeof(*jobs));
    return SGP_TRAIN_OK;
}
