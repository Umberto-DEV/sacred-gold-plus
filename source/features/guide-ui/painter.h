#ifndef SGP_GUIDE_UI_PAINTER_H
#define SGP_GUIDE_UI_PAINTER_H
#include "render.h"
#include "../ui-native/bg.h"
typedef enum { GUIDE_PAINT_REFUSED,GUIDE_PAINT_MORE,GUIDE_PAINT_PREPARED,
 GUIDE_PAINT_UNCHANGED,GUIDE_PAINT_FAILED,GUIDE_PAINT_HOLD } GuidePaintStatus;
typedef struct { GuidePlan plan; unsigned version,valid,upper_invalid,lower_invalid; } GuideHistory;
typedef struct {
 UiHeap *heap; UiBg *bg; UiFontLease *font; const UiGuideLease *guide;
 const GuidePlan *desired; const UiTextOwner *uir1_owner,*pool_owner;
 unsigned generation,index,version;
} GuidePaintRequest;
typedef struct {
 unsigned magic,self,generation,phase,index,version,upper_rows,lower_rows;
 unsigned touched_upper,touched_lower,op_cursor,row_cursor,full,error;
 UiHeap *heap; UiBg *bg; UiFontLease *font; const GuidePlan *desired;
 const UiGuideLease *guide; const UiTextOwner *uir1_owner,*pool_owner;
 GuideHistory history[2]; UiFontPrintJob job; UiFontScratch scratch;
 unsigned short palette[16];
} GuidePainter;
/* Compose after accepted heap/resource/guide_resource/font/BG + Settings state/
 * render/painter, then Guide controller/render. Real roots/owners only. Init
 * accepts zero MAIN-owned storage. Pin plan, pool and leases until prepared or
 * retired. Prepared means complete pending pair, never display/Scene readiness.
 * Request may be a live aligned SYS local: begin copies it synchronously and
 * retains only its admitted owned actors, never the descriptor address.
 * Each step performs one finite admission/closure scan, up to four row clears,
 * a contiguous upload or a text/geometry operation; font budget1..8.
 * Unchanged ops are skipped in one finite scan. No allocation or FS.
 * On partial failure retire the BG lifecycle BEFORE retire can release painter;
 * histories become unknown/FULL. No partial reuse, front/pending writes or
 * semantic model action. A new lifecycle needs fresh storage/painter history. */
unsigned guide_paint_init(GuidePainter *,unsigned bytes,unsigned generation);
GuidePaintStatus guide_paint_begin(GuidePainter *,const GuidePaintRequest *);
GuidePaintStatus guide_paint_step(GuidePainter *,unsigned glyph_budget);
GuidePaintStatus guide_paint_retire(GuidePainter *);
_Static_assert(sizeof(GuidePaintRequest)==40 && sizeof(GuideHistory)==816 && sizeof(GuidePainter)==2552,"Guide painter ARM32");
#endif
