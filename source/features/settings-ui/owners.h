#ifndef SGP_SETTINGS_OWNERS_H
#define SGP_SETTINGS_OWNERS_H
#include "controller.h"
#include "../shiny/ui_api.h"
/* Private transient data, never a save layout. Addresses are ARM32 wire words.
 * Native Init owns app[0..0x30): Options+24, nonzero generation+28,SUI1+2c.
 * Capture/preview/rollback return SgpShinyStatus (OK0, BUSY6, STALE2,
 * UNAVAILABLE1). Entry requires native Main with IME1 and CPSR.I0.
 * Keep app/resources alive until rollback returns OK; BUSY means retry once on
 * the next normal frame, never spin or free. A stale lease must be reconciled
 * without overwriting external audio. OK means the latest target was queued
 * (not heard), or the intact untouched baseline needs no command.
 * Call preview after every CHANGED (including selector B), and once per frame
 * while BUSY; it coalesces the latest effective selector/draft audio target.
 * If the first request never queued, rollback may cancel that pending intent
 * with ever_previewed0 and exact original raw: accepted history stays untouched,
 * pending generation stays monotonic. After any accepted preview, rollback
 * requires a newly accepted exact original target before resources are freed.
 * Apply only follows REQUEST_APPLY in an actual Apply/Exit confirmation.
 * It never attempts an audio command itself; preview must be current first.
 * A failed Apply changes only the reducer error state; the preview lease stays.
 * Capture outputs are disjoint, aligned full heap/SYSTEM-stack extents. App's
 * prefix, live FieldSystem/SaveData and resident state are excluded. Storage
 * may follow app+30. Capture publishes both outputs only after full success.
 * Missing/invalid clean Plus or Shiny disables only its rows. No owner is
 * initialized. Call settings_init(state,snapshot) exactly after capture OK;
 * own the reducer sample/release policy in controller.h. Process CHANGED with
 * preview; REQUEST_APPLY with settings_apply; CLOSE_DISCARD or forced close
 * enters a retained closing state and calls/retries rollback. CLOSE_APPLIED
 * proceeds to cleanup without rollback. Preserve these records until cleanup.
 * No renderer, heap/resource cleanup, frame loop or audio draining lives here.
 */
typedef struct {
    SettingsU32 original_raw, expected_raw, accepted_target, accepted_generation;
    SettingsU32 pending_target, pending_generation, app_generation, ever_previewed;
    /* Distinguishes changed UI intent from original-raw baseline when their
     * numeric raw targets happen to coincide; prevents generation reuse. */
    SettingsU32 pending_changed;
} SettingsAudioPreview;
struct SettingsOwners {
    SettingsU32 magic, bytes, app, generation, fs, save, options;
    SettingsU16 native_raw;
    SettingsU8 plus_raw[5], plus_guard[5], plus_load, reserved;
    SettingsU8 mirrors[2];
    SettingsU32 button_raw;
    SettingsAudioPreview audio;
    SettingsSnapshot opened;
};
SettingsU32 settings_owner_capture(void *app, SettingsOwners *, SettingsSnapshot *);
SettingsU32 settings_owner_preview(SettingsOwners *, const SettingsState *);
SettingsU32 settings_owner_rollback(SettingsOwners *);
/* Required known compiled readonly gate. NativeApp compiler loads this unit
 * (including accepted state.c in the same freestanding translation unit)
 * first, then passes this exact odd symbol as SGP_SETTINGS_UI_FINAL_CHECK to
 * the accepted Shiny compiler. Descriptor ABI/reserved words remain unchanged.
 */
SettingsU32 settings_final_check(void *);
#endif
