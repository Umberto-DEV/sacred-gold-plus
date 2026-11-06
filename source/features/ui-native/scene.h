#ifndef SGP_UI_SCENE_H
#define SGP_UI_SCENE_H
#include "bridge.h"
#include "scene_admission.h"
#include "physical.h"
#include "../settings-ui/owners.h"
#include "../settings-ui/painter.h"
#include "../guide-ui/painter.h"
/* These are transient owned app layouts, never save formats. The one UiHeap
 * authority is context.heap_token in the resident Bridge, never in these apps. */
typedef struct { unsigned reserved[9],options,generation,magic; } ScenePrefix;
typedef struct {
 ScenePrefix prefix; UiSceneContext *context; UiHeap *heap;
 unsigned phase,acquired,error,close_kind,model_epoch,next_version,visible_epoch;
 unsigned submitted_epoch,preview_frames,preview_units,preview_due,suspended;
 UiResourceReader resource; UiBg bg; UiFontLease font;
 UiResourceLease chrome; UiTextOwner uir1_owner,pool_owner; void *pool;
 PhysicalSample sample;
} SceneCommon;
typedef struct {
 SceneCommon common; SettingsOwners owners; SettingsState model;
 SettingsRenderCatalog catalog; SettingsRenderPlan desired; SettingsPainter painter;
 unsigned first,selector_first,preview_speed,preview_origin;
} SettingsApp;
/* A gesture starts on an actually presented semantic cursor. This witness
 * authorizes only continuation of its own feedback paint, never new input. */
typedef struct { GuideView cursor; unsigned short back_count; unsigned visible_epoch; } SceneGesture;
typedef struct {
 SceneCommon common; UiGuideReader reader; UiGuideLease lease; GuideState model;
 GuidePlan desired; GuidePainter painter; SceneGesture gesture;
} GuideApp;
/* The only three dynamic Bridge callbacks; both roles share their offsets.
 * Runtime compilation MUST explicitly supply UI_SCENE_WORK_CALLS (1..4096,
 * implementation guard, not a measured safe duration), UI_SCENE_GLYPH_BUDGET
 * (1..8), UI_SCENE_LAST_START_LINE and the odd resident exports
 * SGP_UI_SCENE_PHYSICAL_CONSUME / SGP_UI_SCENE_PHYSICAL_ACK. No defaults.
 * Initial full painting caps work calls at32; interactive updates use the
 * explicit calibrated value. Work and preview active-frame ticks are independent. */
UiSceneResult ui_scene_init(UiSceneContext *,unsigned *);
UiSceneResult ui_scene_main(UiSceneContext *,unsigned *);
UiSceneResult ui_scene_exit(UiSceneContext *,unsigned *);
_Static_assert(__builtin_offsetof(ScenePrefix,options)==0x24 &&
 __builtin_offsetof(ScenePrefix,generation)==0x28 &&
 __builtin_offsetof(ScenePrefix,magic)==0x2c,"native owner prefix");
_Static_assert(sizeof(SceneCommon)==1184 && sizeof(SettingsApp)==6208 &&
 sizeof(GuideApp)==4996 && sizeof(SceneGesture)==16 &&
 __builtin_offsetof(GuideApp,gesture)==4980,"bounded real role apps ARM32");
#endif
