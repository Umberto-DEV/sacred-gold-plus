#ifndef SGP_SETTINGS_CONTROLLER_H
#define SGP_SETTINGS_CONTROLLER_H
#include "../shiny/api.h"

typedef SgpShinyU8 SettingsU8;
typedef SgpShinyU16 SettingsU16;
typedef SgpShinyU32 SettingsU32;
enum SettingsRow {
    SETTINGS_TEXT, SETTINGS_SCENE, SETTINGS_STYLE, SETTINGS_AUDIO,
    SETTINGS_BUTTON, SETTINGS_FRAME, SETTINGS_DIFFICULTY, SETTINGS_WILD,
    SETTINGS_ANIMATION, SETTINGS_NPC, SETTINGS_WIFI, SETTINGS_SHINY_MODE,
    SETTINGS_TARGET, SETTINGS_SEARCH_PRO, SETTINGS_ROW_COUNT
};
enum SettingsKeys {
    SETTINGS_A=1, SETTINGS_B=2, SETTINGS_RIGHT=16, SETTINGS_LEFT=32,
    SETTINGS_UP=64, SETTINGS_DOWN=128, SETTINGS_R=256, SETTINGS_L=512,
    SETTINGS_X=1024, SETTINGS_Y=2048
};
enum SettingsGroup { SETTINGS_NATIVE=1, SETTINGS_PLUS=2, SETTINGS_SHINY=4 };
enum SettingsView {
    SETTINGS_ROOT, SETTINGS_SELECTOR, SETTINGS_INFO, SETTINGS_SEARCH,
    SETTINGS_EXIT_CONFIRM, SETTINGS_APPLY_CONFIRM, SETTINGS_ERROR
};
enum SettingsResult {
    SETTINGS_NOOP, SETTINGS_CHANGED, SETTINGS_REQUEST_APPLY,
    SETTINGS_CLOSE_DISCARD, SETTINGS_CLOSE_APPLIED
};
typedef enum SettingsResult SettingsResult;
enum SettingsNotice {
    SETTINGS_NOTICE_NONE, SETTINGS_NOTICE_UNAVAILABLE,
    SETTINGS_NOTICE_EMPTY_CANDIDATES, SETTINGS_NOTICE_PRO_ONLY,
    SETTINGS_NOTICE_NO_TARGET, SETTINGS_NOTICE_METHOD,
    SETTINGS_NOTICE_NEED_CHARGE, SETTINGS_NOTICE_OWNER_REJECTED
};
enum SettingsSearchRow {
    SETTINGS_SEARCH_TARGET, SETTINGS_SEARCH_METHOD, SETTINGS_SEARCH_PREPARE
};
/* Exit choices Apply/Discard/Continue; Apply choices Apply/Cancel. */
enum { SETTINGS_EXIT_APPLY=0, SETTINGS_EXIT_DISCARD=1, SETTINGS_EXIT_CONTINUE=2,
       SETTINGS_CONFIRM_APPLY=0, SETTINGS_CONFIRM_CANCEL=1 };
/* selector_row uses stable SettingsRow values, or this Method-only field. */
enum SettingsSelectorRow { SETTINGS_SELECTOR_METHOD = SETTINGS_ROW_COUNT };
_Static_assert(SETTINGS_TARGET == 12 && SETTINGS_SEARCH_PRO == 13 &&
               SETTINGS_ROW_COUNT == 14, "stable root row identifiers");
#define SETTINGS_ALL_ROWS ((1u << SETTINGS_ROW_COUNT)-1u)
#define SETTINGS_FIELD_METHOD (1u << 14)
#define SETTINGS_FIELD_SEARCH (1u << 15)

typedef struct {
    SettingsU8 text, scene, style, audio, button, frame;
} SettingsNativeDraft;
typedef struct {
    SettingsU8 difficulty, wild, animation, npc, wifi;
} SettingsPlusDraft;
/* Logical values only: no native Options/Plus bitfield/save layout aliasing.
 * Native text0..2, scene/style/audio/button0..1, frame0..19; Plus first4
 * fields0..1, wifi0..2. Owner keeps any raw/reserved encoding separately. */
typedef struct {
    SettingsNativeDraft native;
    SettingsPlusDraft plus;
    SgpShinyDraft shiny;
} SettingsDraft;
typedef struct {
    SettingsNativeDraft native;
    SettingsPlusDraft plus;
    SgpShinySnapshot shiny;
    SettingsU16 candidates[SGP_SHINY_METHODS][SGP_SHINY_MAX_CANDIDATES];
    /* Bit per stable SettingsRow; absent owner controls stay readable. */
    SettingsU32 editable_rows;
} SettingsSnapshot;
typedef struct {
    SettingsSnapshot snapshot;
    SettingsDraft draft;
    SettingsU32 dirty_fields;
    SettingsU16 row, selector_cursor, selector_pending, selector_origin;
    SettingsU8 view, return_view, info_origin, selector_row, search_row;
    SettingsU8 choice, dirty_groups, notice, owner_status;
    SettingsU8 release_gate, sample_ready, awaiting_apply;
} SettingsState;

/* Init only copies supplied logical snapshots; it never initializes owners.
 * Snapshot candidate counts are bounded to12 by queries; species are1..493. */
void settings_init(SettingsState *, const SettingsSnapshot *);
/* Software provenance, never a physical key: preserve through step arbitration. */
#define SETTINGS_KEYS_CANCELLED (1u << 31)
/* Local normalization: button_mode is saved/UI 1 or runtime3 for L=A,
 * otherwise normal. mapped contributes other buttons; raw supplies physical
 * A/L/R. Physical A survives L+A. Opposite axes and L+R cancel. No global
 * button mode writes. Call separately for native new and repeated masks and
 * pass both results UNCHANGED to settings_step. Opposed physical pairs are
 * removed, but SETTINGS_KEYS_CANCELLED preserves that new input existed so
 * cancellation cannot revive a repeat. This metadata is not an action; repeat
 * metadata cannot act either. Unknown mapped/raw bits never generate it. */
unsigned settings_keys(unsigned mapped, unsigned raw, unsigned button_mode);
/* Mandatory once before each step, using PHYSICAL held keys and positively
 * established fresh keypad sampling. Each sample is consumed by one step.
 * fresh=0 cannot release a gate; lid_closed=1 arms it even with stale raw bits.
 * Opening/returning/resuming requires a fresh release of all physical action
 * keys A/B/X/Y/L/R. Directions may remain held. Adapter must establish freshness
 * after lid resume; zero raw masks without a fresh sample prove nothing. */
void settings_sample(SettingsState *, unsigned held, unsigned fresh,
                     unsigned lid_closed);
SettingsResult settings_step(SettingsState *, unsigned new_keys,
                             unsigned repeated_keys);
unsigned settings_visible_rows(const SettingsState *);
unsigned settings_row_enabled(const SettingsState *, unsigned row);
/* Current SELECTOR queries: count0 outside a selector; values only for
 * cursor<count (out-of-range returns0). Target0 is None; sparse methods are
 * enumerated in ascending order. Renderers must not duplicate cache filtering. */
unsigned settings_selector_count(const SettingsState *);
unsigned settings_selector_value(const SettingsState *, unsigned cursor);
unsigned settings_effective_charge(const SettingsState *);
unsigned settings_can_prepare(const SettingsState *);
/* On owner success returns CLOSE_APPLIED, never pretends to write an owner.
 * Failure retains complete draft/snapshot and opens ERROR; B recovers ROOT.
 * Status uses SgpShinyStatus; called only for a pending REQUEST_APPLY. */
SettingsResult settings_apply_result(SettingsState *, unsigned status);
/* Implemented by Task2b's transactional owner adapter, intentionally not in
 * pure state.c. It must validate dirty groups only and prove atomic refusal. */
typedef struct SettingsOwners SettingsOwners;
SettingsResult settings_apply(SettingsState *, const SettingsOwners *);
#endif
