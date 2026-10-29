#ifndef SGP_PLUS_EXTENDED_H
#define SGP_PLUS_EXTENDED_H
#include "../options/sorgenti/sgp_ui.h"
#include "../shiny/api.h"
#define XCFG ((const SgpShinyConfig *)SGP_SHINY_CONFIG)
#define XTEXT ((const u16 *)0x023CD800u)
#define XSTATE ((ExtendedState *)0x023CE800u)
#define K_R 0x100u
#define K_L 0x200u
#define K_X 0x400u
enum {
    X_PLUS,
    X_SHINY,
    X_HUNT_TITLE,
    X_TARGET_TITLE,
    X_RULES_TITLE,
    X_MODE,
    X_TARGET,
    X_SUCCESS,
    X_ODDS,
    X_HUNT,
    X_CLASSIC,
    X_PRO,
    X_NONE,
    X_UNAVAILABLE,
    X_CHOOSE,
    X_METHOD,
    X_CHARGE,
    X_SEARCH,
    X_RULES,
    X_LAND,
    X_SURF,
    X_OLD_ROD,
    X_GOOD_ROD,
    X_SUPER_ROD,
    X_APPLY,
    X_CANCEL,
    X_PICK,
    X_BACK,
    X_NEXT,
    X_QUEUED,
    X_CLASSIC_0,
    X_CLASSIC_1,
    X_PRO_0,
    X_PRO_1,
    X_TARGET_0,
    X_TARGET_1,
    X_CHAIN_0,
    X_CHAIN_1,
    X_ODDS_0,
    X_ODDS_1,
    X_HUNT_0,
    X_HUNT_1,
    X_LOCK_0,
    X_LOCK_1,
    X_FIELD_0,
    X_FIELD_1,
    X_CHARGE_0,
    X_CHARGE_1,
    X_PENDING_0,
    X_PENDING_1,
    X_ERROR_OK,
    X_ERROR_UNAVAILABLE,
    X_ERROR_STALE,
    X_ERROR_TARGET,
    X_ERROR_PRO,
    X_ERROR_CHARGE,
    X_ERROR_BUSY,
    X_ERROR_FAILED,
    X_NO_CANDIDATES,
    X_RESET,
    X_RULE_0,
    X_RULE_1,
    X_RULE_2,
    X_RULE_3,
    X_RULE_4,
    X_RULE_5,
    X_RULE_6,
    X_RULE_7,
    X_RULE_8,
    X_RULE_9,
    X_RULE_10,
    X_DIGITS,
    X_SLASH,
    X_LEFT,
    X_RIGHT,
    X_COUNT
};
typedef struct {
    void *app;
    SgpShinySnapshot snapshot;
    SgpShinyDraft draft;
    u8 page, panel, row, root_row, list, top, rules, error;
} ExtendedState;
_Static_assert(sizeof(ExtendedState)<=256,"Plus extension state allocation");
u32 extended_open(void *app);
u32 extended_frame(void *app);
#endif
