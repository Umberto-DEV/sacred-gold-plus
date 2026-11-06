#ifndef SGP_GUIDE_UI_CONTROLLER_H
#define SGP_GUIDE_UI_CONTROLLER_H
#include "../field-guide/sorgenti/controller_core.h"
#include "../ui-native/guide_resource.h"
#include "../ui-native/physical.h"
typedef GuideCursor GuideView;
typedef struct {
 GuideView cursor,back[8]; unsigned short back_count;
 unsigned release_gate,sample_ready,touch_armed,touch_target,touch_down,notice;
} GuideState;
typedef struct {
 const PhysicalSample *sample;
 unsigned freshness,mapped_pressed,mapped_repeated,button_mode;
 unsigned touch_x,touch_y,touch_down,busy;
} GuideInput;
enum { GUIDE_UI_NOOP,GUIDE_UI_CHANGED,GUIDE_UI_CLOSE };
/* Fresh zero state; the initial release gate requires fresh physical AND pen-up.
 * Main-thread only. Typed Guide outputs are live aligned SYS locals. No globals,
 * saved options, archive walkers, action queue or model changes while busy.
 * freshness is the actual physical_consume result supplied by Scene, never an
 * independently asserted readiness flag. sample belongs to this positively
 * fresh native keypad/lid/touch boundary.
 * NONE never reads touch. SUSPEND cancels ownership and requires fresh release.
 * mapped masks come from the SAME boundary as the supplied raw PhysicalSample. */
void guide_ui_init(GuideState *);
unsigned guide_ui_step(GuideState *,const UiGuideLease *,unsigned command);
unsigned guide_ui_input(GuideState *,const UiGuideLease *,const GuideInput *);
/* Shared semantic control table: target1..6, Window-local lower coordinates.
 * No upper tapping. Disabled controls have command0. State/lease are immutable. */
unsigned guide_ui_control(const GuideState *,const UiGuideLease *,unsigned target);
unsigned guide_ui_target(unsigned physical_x,unsigned physical_y);
_Static_assert(sizeof(GuideState)==116,"GuideState ARM32");
_Static_assert(sizeof(GuideInput)==36,"GuideInput ARM32");
#endif
