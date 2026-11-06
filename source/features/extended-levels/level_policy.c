#include "level_policy.h"

static int raw_valid(sgp_level_state state)
{
    if (state.over100 > 1u || state.peak < 1u) {
        return 0;
    }
    if (!state.over100 && state.peak > SGP_LEVEL_CLASSIC_CAP) {
        return 0;
    }
    return state.over100 ? state.peak <= SGP_LEVEL_EXTENDED_CAP : 1;
}

static int canonical(sgp_level_state state)
{
    if (!raw_valid(state)) {
        return 0;
    }
    if (state.over100) {
        return state.peak >= SGP_LEVEL_UNLOCK;
    }
    return state.peak < SGP_LEVEL_UNLOCK;
}

int sgp_level_normalize(sgp_level_state in, sgp_level_state *out)
{
    sgp_level_state next;

    if (!out || !raw_valid(in)) {
        return SGP_LEVEL_INVALID;
    }
    next = in;
    if (next.over100 || next.peak >= SGP_LEVEL_UNLOCK) {
        next.over100 = 1u;
        if (next.peak < SGP_LEVEL_UNLOCK) {
            next.peak = SGP_LEVEL_UNLOCK;
        }
    }
    *out = next;
    return next.over100 == in.over100 && next.peak == in.peak
        ? SGP_LEVEL_UNCHANGED : SGP_LEVEL_CHANGED;
}

int sgp_level_observe(sgp_level_state in, unsigned level,
                      unsigned flags, sgp_level_state *out)
{
    sgp_level_state next;

    if (!out || !canonical(in) || level < 1u ||
        level > SGP_LEVEL_EXTENDED_CAP || (flags & ~SGP_LEVEL_OBS_MASK)) {
        return SGP_LEVEL_INVALID;
    }
    next = in;
    if (!(flags & SGP_LEVEL_OBS_PERMANENT) || (flags & SGP_LEVEL_OBS_EGG)) {
        *out = next;
        return SGP_LEVEL_UNCHANGED;
    }
    if (level > next.peak) {
        next.peak = (sgp_level_u8)level;
    }
    if (level >= SGP_LEVEL_UNLOCK) {
        next.over100 = 1u;
        if (next.peak < SGP_LEVEL_UNLOCK) {
            next.peak = SGP_LEVEL_UNLOCK;
        }
    }
    *out = next;
    return next.over100 == in.over100 && next.peak == in.peak
        ? SGP_LEVEL_UNCHANGED : SGP_LEVEL_CHANGED;
}

unsigned sgp_level_cap(sgp_level_state state)
{
    if (!canonical(state)) {
        return 0u;
    }
    return state.over100 ? SGP_LEVEL_EXTENDED_CAP : SGP_LEVEL_CLASSIC_CAP;
}
