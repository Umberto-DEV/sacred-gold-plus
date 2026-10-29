#include "transaction.h"

static void transaction_copy(void *to, const void *from) {
    volatile sgp_train_u8 *dest = to;
    const volatile sgp_train_u8 *src = from;
    unsigned i;
    for (i = 0; i < SGP_NATIVE_MON_BYTES; i++) dest[i] = src[i];
}

int sgp_training_transaction(const sgp_training_native_api *api, void *context,
    void *pokemon, const sgp_training_request *request, sgp_train_u32 *paid) {
    /* Words keep native data aligned, without importing a proprietary struct. */
    sgp_train_u32 clone[SGP_NATIVE_MON_BYTES / 4], cost = 0, currency;
    sgp_train_u8 before[6], target[6], cap_cost;
    unsigned i, field, changed = 0;
    int result;
    if (!api || !api->read || !api->write || !api->recalculate || !api->charge ||
        !pokemon || !request || !paid || request->reserved ||
        request->kind > SGP_TRANSACTION_EV || request->policy > SGP_TRAIN_UNLIMITED)
        return SGP_TRAIN_INVALID;
    transaction_copy(clone, pokemon);
    /* Reading a decrypted field makes native accessors check the checksum.
     * Even their 'bad egg' flag then affects only our disposable clone. */
    i = api->read(clone, 5, 0);
    if (!i || i > 493 || api->read(clone, 3, 0)) return SGP_TRAIN_INVALID;
    if (api->read(clone, 76, 0)) return SGP_TRAIN_EGG;
    if (i != request->species || api->read(clone, 0, 0) != request->personality ||
        api->read(clone, 7, 0) != request->ot) return SGP_TRAIN_IDENTITY;
    field = request->kind == SGP_TRANSACTION_IV ? 70 : 13;
    for (i = 0; i < 6; i++) {
        before[i] = (sgp_train_u8)api->read(clone, field + i, 0);
        if (before[i] != request->expected[i]) return SGP_TRAIN_IDENTITY;
    }
    if (request->kind == SGP_TRANSACTION_IV) {
        result = sgp_train_iv_preview(before, request->iv_kind, request->stat,
                                      request->value, 0, 1, target, &cap_cost);
        if (result != SGP_TRAIN_OK) return result;
        cost = cap_cost;
        currency = request->iv_kind == SGP_TRAIN_IV_GOLD ?
                   SGP_CURRENCY_GOLD : SGP_CURRENCY_SILVER;
    } else {
        result = sgp_train_ev_allocate(request->target, request->policy, target);
        if (result != SGP_TRAIN_OK) return result;
        for (i = 0; i < 6; i++) {
            changed |= target[i] != before[i];
            if (target[i] > before[i]) cost += (target[i] - before[i]) * 100u;
        }
        if (!changed) return SGP_TRAIN_NO_CHANGE;
        currency = SGP_CURRENCY_MONEY;
    }
    for (i = 0; i < 6; i++) api->write(clone, field + i, &target[i]);
    api->recalculate(clone);
    for (i = 0; i < 6; i++)
        if (api->read(clone, field + i, 0) != target[i]) return SGP_TRAIN_INVALID;
    if (api->read(clone, 3, 0)) return SGP_TRAIN_INVALID;
    if (cost && !api->charge(context, currency, cost)) return SGP_TRAIN_PAYMENT;
    transaction_copy(pokemon, clone);
    *paid = cost;
    return SGP_TRAIN_OK;
}
