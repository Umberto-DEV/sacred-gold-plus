#ifndef SGP_GUIDE_UI_RENDER_H
#define SGP_GUIDE_UI_RENDER_H
#include "controller.h"
#include "../settings-ui/catalog.h"
#define GUIDE_PLAN_MAGIC 0x31504753u
#define GUIDE_PLAN_OPS 32u
#define GUIDE_PLAN_FULL 0x003fffffu
enum { GUIDE_DRAW_TEXT=1,GUIDE_DRAW_BAND,GUIDE_DRAW_BUTTON,GUIDE_DRAW_UIR_TEXT };
enum { GUIDE_DRAW_FOCUS=1,GUIDE_DRAW_PRESSED=2,GUIDE_DRAW_DISABLED=4,
 GUIDE_DRAW_KEY_A=8,GUIDE_DRAW_KEY_B=16,GUIDE_DRAW_UP=32,
 GUIDE_DRAW_DOWN=64,GUIDE_DRAW_LEFT=128 };
/* TEXT color is its homogeneous background palette index. BUTTON color is the
 * command key (A/B/direction/L/R); flags describe state. Composite geometry
 * stays within the complete op envelope. screen0 upper,1 lower. */
typedef struct {
 UiTextSlice text; unsigned char x,y,w,h,screen,kind,flags,color;
} GuideDrawOp;
typedef struct {
 unsigned magic,epoch,pool_epoch,pool_used,view,count,entry,page;
 GuideDrawOp ops[GUIDE_PLAN_OPS];
} GuidePlan;
typedef struct { unsigned upper,lower,full; } GuideDirty;
/* Caller pins all immutable leases, widths509 and input state. A genuine
 * dedicated aligned pool1024 and out are disjoint from ALL inputs/roots.
 * No allocation/FS/MMIO. Refusal leaves out AND pool unchanged. The pool owner
 * is bound by painter; BUFFER descriptors use ownerNULL until then. Epoch
 * identifies Guide generation; pool_epoch must advance after job retirement. */
unsigned guide_ui_build(const GuideState *,const UiGuideLease *,
 const UiResourceLease *,const unsigned char *widths,GuidePlan *,
 void *pool1024,unsigned pool_epoch);
/* Retained history never dereferences an old BUFFER slice. Every old/new BUFFER
 * envelope is invalidated conservatively. FULL on view/entry/title change. */
unsigned guide_ui_dirty(const GuidePlan *,const GuidePlan *,unsigned bad_upper,
 unsigned bad_lower,GuideDirty *);
_Static_assert(sizeof(GuideDrawOp)==24 && sizeof(GuidePlan)==800,"Guide plan ARM32");
#endif
