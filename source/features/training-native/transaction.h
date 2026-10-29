#ifndef SGP_TRAINING_TRANSACTION_H
#define SGP_TRAINING_TRANSACTION_H
#include "../training/sorgenti/training.h"
#define SGP_NATIVE_MON_BYTES 236
enum sgp_transaction_kind { SGP_TRANSACTION_IV, SGP_TRANSACTION_EV };
enum sgp_currency { SGP_CURRENCY_SILVER, SGP_CURRENCY_GOLD, SGP_CURRENCY_MONEY };
typedef struct {
    sgp_train_u32 personality, ot;
    sgp_train_u16 species;
    sgp_train_u8 kind, policy, iv_kind, stat, value, reserved;
    sgp_train_u8 expected[6], target[6];
} sgp_training_request;
typedef struct {
    sgp_train_u32 (*read)(void *, int, void *);
    void (*write)(void *, int, const void *);
    void (*recalculate)(void *);
    /* All-or-nothing debit. Must not yield or change the target Pokemon.
     * Return 1 only after successful payment, 0 without changing the wallet. */
    int (*charge)(void *context, sgp_train_u32 currency, sgp_train_u32 amount);
} sgp_training_native_api;
/* Native party Pokemon only, never a smaller BoxPokemon. The UI supplies the
 * identity and six values shown at confirmation; stale selections are rejected.
 * Previews and checksum validation operate on a stack copy. Debit is the final
 * fallible step, followed immediately by a byte copy, without scheduling work.
 * Both success and failure preserve output cost unless committed successfully. */
int sgp_training_transaction(const sgp_training_native_api *api, void *context,
    void *pokemon, const sgp_training_request *request, sgp_train_u32 *paid);
#endif
