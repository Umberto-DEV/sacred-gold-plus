#include "training.h"

int sgp_train_iv_preview(const sgp_train_u8 before[6], sgp_train_u8 kind,
    sgp_train_u8 stat, sgp_train_u8 value, sgp_train_u8 is_egg,
    sgp_train_u8 valid_data, sgp_train_u8 after[6], sgp_train_u8 *cost)
{
    sgp_train_u8 target[6], changed = 0;
    unsigned i;
    if (!before || !after || !cost || kind > SGP_TRAIN_IV_GOLD ||
        is_egg > 1 || valid_data != 1 ||
        (kind != SGP_TRAIN_IV_GOLD && stat > 5) ||
        (kind == SGP_TRAIN_IV_EXACT && value > 31)) return SGP_TRAIN_INVALID;
    for (i = 0; i < 6; i++) {
        if (before[i] > 31) return SGP_TRAIN_INVALID;
        target[i] = before[i];
    }
    if (is_egg) return SGP_TRAIN_EGG;
    if (kind == SGP_TRAIN_IV_GOLD) {
        for (i = 0; i < 6; i++) target[i] = 31;
    } else target[stat] = kind == SGP_TRAIN_IV_SILVER ? 31 : value;
    for (i = 0; i < 6; i++) changed |= before[i] != target[i];
    if (!changed) return SGP_TRAIN_NO_CHANGE;
    for (i = 0; i < 6; i++) after[i] = target[i];
    *cost = 1;
    return SGP_TRAIN_OK;
}

int sgp_train_payment(sgp_train_u16 available, sgp_train_u16 cost,
    sgp_train_u16 *remaining)
{
    if (!remaining) return SGP_TRAIN_INVALID;
    if (cost > available) return SGP_TRAIN_PAYMENT;
    *remaining = available - cost;
    return SGP_TRAIN_OK;
}

int sgp_train_mode_fits(const sgp_train_u8 evs[6], sgp_train_u8 policy)
{
    unsigned i, total = 0, cap = policy == SGP_TRAIN_LEGACY ? 255 : 252;
    if (!evs || policy > SGP_TRAIN_UNLIMITED) return 0;
    for (i = 0; i < 6; i++) {
        if (evs[i] > cap) return 0;
        total += evs[i];
    }
    return total <= (policy == SGP_TRAIN_UNLIMITED ? 1512u : 510u);
}

int sgp_train_ev_delta(const sgp_train_u8 before[6], sgp_train_u8 policy,
    sgp_train_u8 stat, sgp_train_s32 delta, sgp_train_u8 vitamin,
    sgp_train_u8 after[6])
{
    unsigned i, total = 0, current, next, room, cap, total_cap;
    if (!before || !after || policy > SGP_TRAIN_UNLIMITED || stat > 5 || vitamin > 1)
        return SGP_TRAIN_INVALID;
    current = before[stat];
    next = current;
    if (delta < 0) {
        /* Compare before negation: INT_MIN must never be negated. */
        next = delta <= -(sgp_train_s32)current ? 0 : current + delta;
    } else if (delta > 0) {
        cap = policy == SGP_TRAIN_LEGACY ? (vitamin ? 100 : 255) : 252;
        total_cap = policy == SGP_TRAIN_UNLIMITED ? 1512 : 510;
        for (i = 0; i < 6; i++) total += before[i];
        if (current < cap && total < total_cap) {
            room = cap - current;
            if (room > total_cap - total) room = total_cap - total;
            if ((sgp_train_u32)delta < room) room = (sgp_train_u32)delta;
            next += room;
        }
    }
    if (next == current) return SGP_TRAIN_NO_CHANGE;
    for (i = 0; i < 6; i++) after[i] = before[i];
    after[stat] = (sgp_train_u8)next;
    return SGP_TRAIN_OK;
}

int sgp_train_ev_allocate(const sgp_train_u8 target[6], sgp_train_u8 policy,
    sgp_train_u8 after[6])
{
    unsigned i;
    if (!after || !sgp_train_mode_fits(target, policy)) return SGP_TRAIN_INVALID;
    for (i = 0; i < 6; i++) if (target[i] > 252) return SGP_TRAIN_INVALID;
    for (i = 0; i < 6; i++) after[i] = target[i];
    return SGP_TRAIN_OK;
}

sgp_train_u8 sgp_train_stat_from_ui(sgp_train_u8 index)
{
    if (index < 3) return index;
    if (index < 5) return index + 1;
    return index == 5 ? 3 : 255;
}
