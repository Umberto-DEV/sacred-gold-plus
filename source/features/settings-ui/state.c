#include "controller.h"

#define DIRECTIONS (SETTINGS_UP|SETTINGS_DOWN|SETTINGS_LEFT|SETTINGS_RIGHT)
#define ACTIONS (SETTINGS_A|SETTINGS_B|SETTINGS_X|SETTINGS_Y|SETTINGS_L|SETTINGS_R)
#define KNOWN (DIRECTIONS|ACTIONS)
#define METHOD_ROW SETTINGS_SELECTOR_METHOD

static unsigned cancel_opposites(unsigned keys) {
    if ((keys & (SETTINGS_L|SETTINGS_R)) == (SETTINGS_L|SETTINGS_R))
        keys &= ~(SETTINGS_L|SETTINGS_R);
    if ((keys & (SETTINGS_UP|SETTINGS_DOWN)) == (SETTINGS_UP|SETTINGS_DOWN))
        keys &= ~(SETTINGS_UP|SETTINGS_DOWN);
    if ((keys & (SETTINGS_LEFT|SETTINGS_RIGHT)) == (SETTINGS_LEFT|SETTINGS_RIGHT))
        keys &= ~(SETTINGS_LEFT|SETTINGS_RIGHT);
    return keys & KNOWN;
}

unsigned settings_keys(unsigned mapped, unsigned raw, unsigned button_mode) {
    unsigned normalized, keys = mapped & ~(SETTINGS_L|SETTINGS_R);
    if (button_mode == 1 || button_mode == 3) keys &= ~SETTINGS_A;
    keys |= raw & (SETTINGS_A|SETTINGS_L|SETTINGS_R);
    keys &= KNOWN;
    normalized = cancel_opposites(keys);
    return normalized | (keys != normalized ? SETTINGS_KEYS_CANCELLED : 0);
}

static void copy_bytes(void *out, const void *in, unsigned length) {
    unsigned i;
    unsigned char *to = (unsigned char *)out;
    const unsigned char *from = (const unsigned char *)in;
    for (i = 0; i < length; ++i) to[i] = from[i];
}

static void reset_draft(SettingsState *s) {
    const SgpShinySnapshot *p = &s->snapshot.shiny;
    copy_bytes(&s->draft.native, &s->snapshot.native, sizeof(s->draft.native));
    copy_bytes(&s->draft.plus, &s->snapshot.plus, sizeof(s->draft.plus));
    s->draft.shiny.epoch = p->epoch;
    s->draft.shiny.context = p->context;
    s->draft.shiny.revision = p->revision;
    s->draft.shiny.target = p->target;
    s->draft.shiny.mode = p->mode;
    s->draft.shiny.method = p->method;
    s->draft.shiny.search = 0;
}

void settings_init(SettingsState *s, const SettingsSnapshot *snapshot) {
    unsigned i;
    unsigned char *bytes = (unsigned char *)s;
    for (i = 0; i < sizeof(*s); ++i) bytes[i] = 0;
    copy_bytes(&s->snapshot, snapshot, sizeof(s->snapshot));
    reset_draft(s);
    s->release_gate = 1;
}

unsigned settings_visible_rows(const SettingsState *s) {
    return s->draft.shiny.mode == 1 ? SETTINGS_ROW_COUNT : SETTINGS_TARGET;
}

unsigned settings_row_enabled(const SettingsState *s, unsigned row) {
    if (row >= settings_visible_rows(s)) return 0;
    if (!(s->snapshot.editable_rows & (1u << row))) return 0;
    return row < SETTINGS_SHINY_MODE || s->snapshot.shiny.available;
}

void settings_sample(SettingsState *s, unsigned held, unsigned fresh,
                     unsigned lid_closed) {
    s->sample_ready = 0;
    if (lid_closed) { s->release_gate = 1; return; }
    if (!fresh) return;
    /* The release frame itself cannot act on contradictory/stale edge masks. */
    if (s->release_gate) {
        if (!(held & ACTIONS)) s->release_gate = 0;
        return;
    }
    s->sample_ready = 1;
}

static unsigned logical_value(const SettingsNativeDraft *n,
                              const SettingsPlusDraft *p, unsigned row) {
    switch (row) {
    case SETTINGS_TEXT: return n->text;
    case SETTINGS_SCENE: return n->scene;
    case SETTINGS_STYLE: return n->style;
    case SETTINGS_AUDIO: return n->audio;
    case SETTINGS_BUTTON: return n->button;
    case SETTINGS_FRAME: return n->frame;
    case SETTINGS_DIFFICULTY: return p->difficulty;
    case SETTINGS_WILD: return p->wild;
    case SETTINGS_ANIMATION: return p->animation;
    case SETTINGS_NPC: return p->npc;
    case SETTINGS_WIFI: return p->wifi;
    default: return 0;
    }
}

static unsigned current_value(const SettingsState *s, unsigned row) {
    if (row == SETTINGS_SHINY_MODE) return s->draft.shiny.mode;
    if (row == SETTINGS_TARGET) return s->draft.shiny.target;
    if (row == METHOD_ROW) return s->draft.shiny.method;
    return logical_value(&s->draft.native, &s->draft.plus, row);
}

static void refresh_dirty(SettingsState *s) {
    unsigned row, fields = 0, groups = 0;
    for (row = 0; row < SETTINGS_SHINY_MODE; ++row) {
        if (current_value(s, row) != logical_value(&s->snapshot.native,
                                                   &s->snapshot.plus, row))
            fields |= 1u << row;
    }
    if (s->draft.shiny.mode != s->snapshot.shiny.mode)
        fields |= 1u << SETTINGS_SHINY_MODE;
    if (s->draft.shiny.target != s->snapshot.shiny.target)
        fields |= 1u << SETTINGS_TARGET;
    if (s->draft.shiny.method != s->snapshot.shiny.method)
        fields |= SETTINGS_FIELD_METHOD;
    if (s->draft.shiny.search) fields |= SETTINGS_FIELD_SEARCH;
    if (fields & 0x3fu) groups |= SETTINGS_NATIVE;
    if (fields & 0x7c0u) groups |= SETTINGS_PLUS;
    if (fields & 0xd800u) groups |= SETTINGS_SHINY;
    s->dirty_fields = fields;
    s->dirty_groups = (SettingsU8)groups;
}

static unsigned scalar_max(unsigned row) {
    if (row == SETTINGS_TEXT || row == SETTINGS_WIFI) return 2;
    if (row == SETTINGS_FRAME) return 19;
    return 1;
}

static SettingsResult set_value(SettingsState *s, unsigned row, unsigned value) {
    if (current_value(s, row) == value) return SETTINGS_NOOP;
    switch (row) {
    case SETTINGS_TEXT: s->draft.native.text = (SettingsU8)value; break;
    case SETTINGS_SCENE: s->draft.native.scene = (SettingsU8)value; break;
    case SETTINGS_STYLE: s->draft.native.style = (SettingsU8)value; break;
    case SETTINGS_AUDIO: s->draft.native.audio = (SettingsU8)value; break;
    case SETTINGS_BUTTON: s->draft.native.button = (SettingsU8)value; break;
    case SETTINGS_FRAME: s->draft.native.frame = (SettingsU8)value; break;
    case SETTINGS_DIFFICULTY: s->draft.plus.difficulty = (SettingsU8)value; break;
    case SETTINGS_WILD: s->draft.plus.wild = (SettingsU8)value; break;
    case SETTINGS_ANIMATION: s->draft.plus.animation = (SettingsU8)value; break;
    case SETTINGS_NPC: s->draft.plus.npc = (SettingsU8)value; break;
    case SETTINGS_WIFI: s->draft.plus.wifi = (SettingsU8)value; break;
    case SETTINGS_SHINY_MODE: s->draft.shiny.mode = (SettingsU8)value; break;
    case SETTINGS_TARGET: s->draft.shiny.target = (SettingsU16)value; break;
    case METHOD_ROW: s->draft.shiny.method = (SettingsU8)value; break;
    default: return SETTINGS_NOOP;
    }
    if (row == SETTINGS_SHINY_MODE || row == SETTINGS_TARGET || row == METHOD_ROW)
        s->draft.shiny.search = 0;
    if (s->row >= settings_visible_rows(s)) s->row = SETTINGS_SHINY_MODE;
    s->notice = SETTINGS_NOTICE_NONE;
    refresh_dirty(s);
    return SETTINGS_CHANGED;
}

static unsigned move_clamped(unsigned value, unsigned max, int delta) {
    if (value > max) return max;
    if (delta < 0) return value ? value - 1 : 0;
    return value < max ? value + 1 : max;
}

/* Snapshot cache only. Invalid species/counts cannot escape this boundary.
 * index0 is None; out-of-range queries also return None. */
static unsigned target_at(const SettingsState *s, unsigned index) {
    unsigned method = s->draft.shiny.method, i, count;
    if (!index || method >= SGP_SHINY_METHODS) return 0;
    count = s->snapshot.shiny.counts[method];
    if (count > SGP_SHINY_MAX_CANDIDATES) count = SGP_SHINY_MAX_CANDIDATES;
    for (i = 0; i < count; ++i) {
        unsigned species = s->snapshot.candidates[method][i];
        if (species && species <= 493 && !--index) return species;
    }
    return 0;
}

static unsigned method_available(const SettingsState *s, unsigned method) {
    return method < SGP_SHINY_METHODS &&
           (s->snapshot.shiny.method_mask & (1u << method));
}

unsigned settings_effective_charge(const SettingsState *s) {
    if (s->draft.shiny.mode != s->snapshot.shiny.mode ||
        s->draft.shiny.target != s->snapshot.shiny.target) return 0;
    return s->snapshot.shiny.charge;
}

static unsigned prepare_notice(const SettingsState *s) {
    unsigned i;
    if (!settings_row_enabled(s, SETTINGS_SEARCH_PRO))
        return s->draft.shiny.mode != 1 ? SETTINGS_NOTICE_PRO_ONLY :
                                        SETTINGS_NOTICE_UNAVAILABLE;
    if (!method_available(s, s->draft.shiny.method)) return SETTINGS_NOTICE_METHOD;
    if (!s->draft.shiny.target || s->draft.shiny.target > 493)
        return SETTINGS_NOTICE_NO_TARGET;
    for (i = 1; i <= SGP_SHINY_MAX_CANDIDATES; ++i)
        if (target_at(s, i) == s->draft.shiny.target) break;
    if (i > SGP_SHINY_MAX_CANDIDATES) return SETTINGS_NOTICE_NO_TARGET;
    if (settings_effective_charge(s) < 40) return SETTINGS_NOTICE_NEED_CHARGE;
    return SETTINGS_NOTICE_NONE;
}

unsigned settings_can_prepare(const SettingsState *s) {
    return prepare_notice(s) == SETTINGS_NOTICE_NONE;
}

static SettingsResult transition(SettingsState *s, unsigned view) {
    s->view = (SettingsU8)view;
    s->release_gate = 1;
    s->sample_ready = 0;
    return SETTINGS_CHANGED;
}

static unsigned selector_count(const SettingsState *s) {
    unsigned i, count = 0;
    if (s->selector_row == SETTINGS_TARGET) {
        for (i = 1; i <= SGP_SHINY_MAX_CANDIDATES; ++i)
            if (target_at(s, i)) ++count;
        return count + 1;
    }
    if (s->selector_row == METHOD_ROW) {
        for (i = 0; i < SGP_SHINY_METHODS; ++i)
            if (method_available(s, i)) ++count;
        return count;
    }
    return scalar_max(s->selector_row) + 1;
}

static unsigned selector_value(const SettingsState *s, unsigned cursor) {
    unsigned i;
    if (s->selector_row == SETTINGS_TARGET) return target_at(s, cursor);
    if (s->selector_row == METHOD_ROW) {
        for (i = 0; i < SGP_SHINY_METHODS; ++i)
            if (method_available(s, i) && !cursor--) return i;
        return 0;
    }
    return cursor;
}

unsigned settings_selector_count(const SettingsState *s) {
    return s->view == SETTINGS_SELECTOR ? selector_count(s) : 0;
}

unsigned settings_selector_value(const SettingsState *s, unsigned cursor) {
    return cursor < settings_selector_count(s) ? selector_value(s, cursor) : 0;
}

static SettingsResult open_selector(SettingsState *s, unsigned row) {
    unsigned i, count;
    s->return_view = s->view;
    s->selector_row = (SettingsU8)row;
    s->selector_origin = (SettingsU16)current_value(s, row);
    s->selector_cursor = 0;
    count = selector_count(s);
    for (i = 0; i < count; ++i)
        if (selector_value(s, i) == s->selector_origin) s->selector_cursor = (SettingsU16)i;
    s->selector_pending = (SettingsU16)selector_value(s, s->selector_cursor);
    s->notice = row == SETTINGS_TARGET && count == 1 ?
                SETTINGS_NOTICE_EMPTY_CANDIDATES : SETTINGS_NOTICE_NONE;
    if (!count) s->notice = SETTINGS_NOTICE_METHOD;
    return transition(s, SETTINGS_SELECTOR);
}

static SettingsResult step_selector(SettingsState *s, unsigned key) {
    unsigned count = selector_count(s), cursor;
    if (key == SETTINGS_B) {
        s->selector_pending = s->selector_origin;
        return transition(s, s->return_view);
    }
    if (key == SETTINGS_A && count) {
        set_value(s, s->selector_row, s->selector_pending);
        return transition(s, s->return_view);
    }
    if (!(key & DIRECTIONS) || !count) return SETTINGS_NOOP;
    cursor = move_clamped(s->selector_cursor, count - 1,
                         key & (SETTINGS_UP|SETTINGS_LEFT) ? -1 : 1);
    if (cursor == s->selector_cursor) return SETTINGS_NOOP;
    s->selector_cursor = (SettingsU16)cursor;
    s->selector_pending = (SettingsU16)selector_value(s, cursor);
    return SETTINGS_CHANGED;
}

static SettingsResult open_info(SettingsState *s) {
    s->info_origin = s->view;
    return transition(s, SETTINGS_INFO);
}

static SettingsResult change_method(SettingsState *s, int delta) {
    int method = s->draft.shiny.method;
    if (method >= (int)SGP_SHINY_METHODS) method = delta < 0 ? SGP_SHINY_METHODS : -1;
    for (method += delta; method >= 0 && method < (int)SGP_SHINY_METHODS; method += delta)
        if (method_available(s, (unsigned)method)) return set_value(s, METHOD_ROW, (unsigned)method);
    return SETTINGS_NOOP;
}

static SettingsResult step_search(SettingsState *s, unsigned key) {
    unsigned row;
    if (key == SETTINGS_B) return transition(s, SETTINGS_ROOT);
    if (key == SETTINGS_Y) return open_info(s);
    if (key == SETTINGS_UP || key == SETTINGS_DOWN) {
        row = move_clamped(s->search_row, SETTINGS_SEARCH_PREPARE,
                           key == SETTINGS_UP ? -1 : 1);
        if (row == s->search_row) return SETTINGS_NOOP;
        s->search_row = (SettingsU8)row;
        return SETTINGS_CHANGED;
    }
    if (s->search_row == SETTINGS_SEARCH_METHOD) {
        if (!settings_row_enabled(s, SETTINGS_SEARCH_PRO)) return SETTINGS_NOOP;
        if (key == SETTINGS_LEFT || key == SETTINGS_RIGHT)
            return change_method(s, key == SETTINGS_LEFT ? -1 : 1);
        if (key == SETTINGS_A) return open_selector(s, METHOD_ROW);
    }
    if (key != SETTINGS_A) return SETTINGS_NOOP;
    if (s->search_row == SETTINGS_SEARCH_TARGET) {
        if (!settings_row_enabled(s, SETTINGS_TARGET)) return SETTINGS_NOOP;
        return open_selector(s, SETTINGS_TARGET);
    }
    if (s->search_row == SETTINGS_SEARCH_PREPARE) {
        s->notice = (SettingsU8)prepare_notice(s);
        if (s->notice) return SETTINGS_CHANGED;
        s->draft.shiny.search = 1;
        refresh_dirty(s);
        s->row = SETTINGS_SEARCH_PRO;
        return transition(s, SETTINGS_ROOT);
    }
    return SETTINGS_NOOP;
}

static SettingsResult request_apply(SettingsState *s) {
    s->awaiting_apply = 1;
    s->release_gate = 1;
    return SETTINGS_REQUEST_APPLY;
}

static SettingsResult step_confirmation(SettingsState *s, unsigned key) {
    unsigned choice, max = s->view == SETTINGS_EXIT_CONFIRM ? 2 : 1;
    if (key == SETTINGS_B) return transition(s, SETTINGS_ROOT);
    if (key & DIRECTIONS) {
        choice = move_clamped(s->choice, max,
                             key & (SETTINGS_UP|SETTINGS_LEFT) ? -1 : 1);
        if (choice == s->choice) return SETTINGS_NOOP;
        s->choice = (SettingsU8)choice;
        return SETTINGS_CHANGED;
    }
    if (key != SETTINGS_A) return SETTINGS_NOOP;
    if (s->choice == SETTINGS_CONFIRM_APPLY) return request_apply(s);
    if (s->view == SETTINGS_EXIT_CONFIRM && s->choice == SETTINGS_EXIT_DISCARD) {
        reset_draft(s);
        refresh_dirty(s);
        transition(s, SETTINGS_ROOT);
        return SETTINGS_CLOSE_DISCARD;
    }
    return transition(s, SETTINGS_ROOT);
}

static SettingsResult step_root(SettingsState *s, unsigned key) {
    unsigned row = s->row;
    if (key == SETTINGS_B) {
        if (!s->dirty_groups) return SETTINGS_CLOSE_DISCARD;
        s->choice = SETTINGS_EXIT_CONTINUE;
        return transition(s, SETTINGS_EXIT_CONFIRM);
    }
    if (key == SETTINGS_X) {
        s->choice = SETTINGS_CONFIRM_CANCEL;
        return transition(s, SETTINGS_APPLY_CONFIRM);
    }
    if (key == SETTINGS_Y) return open_info(s);
    if (key == SETTINGS_L) row = row >= SETTINGS_SHINY_MODE ? SETTINGS_DIFFICULTY :
                                    row >= SETTINGS_DIFFICULTY ? SETTINGS_TEXT : row;
    else if (key == SETTINGS_R) row = row < SETTINGS_DIFFICULTY ? SETTINGS_DIFFICULTY :
                                         row < SETTINGS_SHINY_MODE ? SETTINGS_SHINY_MODE : row;
    else if (key == SETTINGS_UP || key == SETTINGS_DOWN)
        row = move_clamped(row, settings_visible_rows(s) - 1, key == SETTINGS_UP ? -1 : 1);
    else if (key == SETTINGS_A || key == SETTINGS_LEFT || key == SETTINGS_RIGHT) {
        if (!settings_row_enabled(s, row)) {
            if (s->notice == SETTINGS_NOTICE_UNAVAILABLE) return SETTINGS_NOOP;
            s->notice = SETTINGS_NOTICE_UNAVAILABLE;
            return SETTINGS_CHANGED;
        }
        if (key == SETTINGS_A) {
            if (row != SETTINGS_SEARCH_PRO) return open_selector(s, row);
            s->search_row = SETTINGS_SEARCH_TARGET;
            return transition(s, SETTINGS_SEARCH);
        }
        if (row >= SETTINGS_TARGET) return SETTINGS_NOOP;
        return set_value(s, row, move_clamped(current_value(s, row), scalar_max(row),
                                             key == SETTINGS_LEFT ? -1 : 1));
    }
    if (row == s->row) return SETTINGS_NOOP;
    s->row = (SettingsU16)row;
    s->notice = SETTINGS_NOTICE_NONE;
    return SETTINGS_CHANGED;
}

static unsigned choose_key(unsigned keys) {
    if (keys & SETTINGS_B) return SETTINGS_B;
    if (keys & SETTINGS_A) return SETTINGS_A;
    if (keys & SETTINGS_X) return SETTINGS_X;
    if (keys & SETTINGS_Y) return SETTINGS_Y;
    if (keys & SETTINGS_L) return SETTINGS_L;
    if (keys & SETTINGS_R) return SETTINGS_R;
    if (keys & SETTINGS_UP) return SETTINGS_UP;
    if (keys & SETTINGS_DOWN) return SETTINGS_DOWN;
    if (keys & SETTINGS_LEFT) return SETTINGS_LEFT;
    if (keys & SETTINGS_RIGHT) return SETTINGS_RIGHT;
    return 0;
}

SettingsResult settings_step(SettingsState *s, unsigned new_keys, unsigned repeated_keys) {
    unsigned keys, before;
    if (!s->sample_ready) return SETTINGS_NOOP;
    s->sample_ready = 0;
    if (s->release_gate || s->awaiting_apply) return SETTINGS_NOOP;
    before = s->row;
    if (s->row >= settings_visible_rows(s)) s->row = SETTINGS_SHINY_MODE;
    refresh_dirty(s);
    /* New keys dominate repeats; an opposed new directional family cancels
     * rather than resurrecting the same family's repeat. */
    keys = cancel_opposites(new_keys);
    if (!(new_keys & (KNOWN|SETTINGS_KEYS_CANCELLED)))
        keys = cancel_opposites(repeated_keys & DIRECTIONS);
    keys = choose_key(keys);
    if (!keys) return s->row == before ? SETTINGS_NOOP : SETTINGS_CHANGED;
    switch (s->view) {
    case SETTINGS_ROOT: return step_root(s, keys);
    case SETTINGS_SELECTOR: return step_selector(s, keys);
    case SETTINGS_SEARCH: return step_search(s, keys);
    case SETTINGS_INFO:
        return keys == SETTINGS_B ? transition(s, s->info_origin) : SETTINGS_NOOP;
    case SETTINGS_EXIT_CONFIRM: case SETTINGS_APPLY_CONFIRM:
        return step_confirmation(s, keys);
    case SETTINGS_ERROR:
        return keys == SETTINGS_B ? transition(s, SETTINGS_ROOT) : SETTINGS_NOOP;
    default: return SETTINGS_NOOP;
    }
}

SettingsResult settings_apply_result(SettingsState *s, unsigned status) {
    if (!s->awaiting_apply) return SETTINGS_NOOP;
    s->awaiting_apply = 0;
    s->owner_status = (SettingsU8)status;
    if (status == SGP_SHINY_OK) return SETTINGS_CLOSE_APPLIED;
    s->notice = SETTINGS_NOTICE_OWNER_REJECTED;
    return transition(s, SETTINGS_ERROR);
}
