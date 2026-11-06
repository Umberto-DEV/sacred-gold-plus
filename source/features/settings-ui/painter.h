#ifndef SGP_SETTINGS_PAINTER_H
#define SGP_SETTINGS_PAINTER_H
#include "render.h"
#include "../ui-native/bg.h"
#include "../ui-native/font.h"
/* Main-only Settings pixel consumer; compose after heap.c,resource.c,font.c,
 * bg.c,state.c,render.c in one TU to reuse their checked private helpers.
 * No placement, deadline, controller action, FS or allocation authority here.
 * Fresh zero records live in a caller-owned app; never copy/reset live records.
 * Pointer/epoch/bounds checks are not lifetime or revocation capabilities. */
typedef enum { SETTINGS_PAINT_REFUSED, SETTINGS_PAINT_MORE,
 SETTINGS_PAINT_PREPARED, SETTINGS_PAINT_UNCHANGED,
 SETTINGS_PAINT_FAILED, SETTINGS_PAINT_HOLD } SettingsPaintStatus;
typedef struct {
 SettingsRenderPlan plan; unsigned version,valid,invalid_rows;
} SettingsPaintHistory;
typedef struct {
 UiHeap *heap; UiBg *bg; UiFontLease *font;
 const SettingsRenderCatalog *catalog; const SettingsRenderPlan *desired;
 const UiTextOwner *uir1_owner,*pool_owner;
 unsigned generation,index,version;
} SettingsPaintRequest;
typedef struct {
 unsigned magic,self,generation,phase,index,version;
 unsigned initial_rows,paint_rows,touched_rows,row_cursor,op_cursor;
 unsigned upload_cursor,full,replay_stage,error,reserved;
 UiHeap *heap; UiBg *bg; UiFontLease *font;
 const SettingsRenderCatalog *catalog; const SettingsRenderPlan *desired;
 const UiTextOwner *uir1_owner,*pool_owner;
 SettingsPaintHistory history[2];
 UiFontPrintJob job; UiFontScratch scratch;
 unsigned short palette[16];
} SettingsPainter;
/* init accepts fresh zero unowned MAIN storage only. Pass its immutable owned
 * palette to ui_bg_enter_backdrop(...,0x564c) before painting. Index1 paper,
 * 2 ink,3 blue,4 choice contour,5 disabled,6 action,8 focus,10 light,13 neutral.
 * Index0 transparent; SUB stays black. The old BG entry still defaultsblack.
 * Desired/catalogue/owner records/pool stay immutable until PREPARED/UNCHANGED
 * or successful retire. Pool MUST be a genuine dedicated ui_alloc38 BUFFER.
 * Exactly one authoritative heap/font/BG owner, no concurrent writer/publisher
 * or mode switch. Jobs borrow the actual hidden Window, never a subwindow.
 * PREPARED is complete pending content, not published; parent owns publication.
 * Partial failure needs font retirement AND BG lifecycle retirement before
 * release/reuse; HOLD keeps all containers/roots live. Never cancel DONE jobs. */
unsigned settings_paint_init(SettingsPainter *,unsigned bytes,unsigned generation);
SettingsPaintStatus settings_paint_begin(SettingsPainter *,const SettingsPaintRequest *);
/* Each step does one finite admission/closure pass, up to four row clears, one
 * contiguous upload, geometric op or native job operation; glyph budget1..8.
 * Unchanged ops are skipped in one finite scan. No per-frame allocations/FS.
 * Retained masks close all intersecting desired envelopes in <=22 passes;
 * clear all admitted rows, replay ALL intersecting ops in original order. */
SettingsPaintStatus settings_paint_step(SettingsPainter *,unsigned glyph_budget);
SettingsPaintStatus settings_paint_retire(SettingsPainter *);
_Static_assert(sizeof(SettingsPaintHistory)==1196,"history ARM32");
_Static_assert(sizeof(SettingsPaintRequest)==40,"request ARM32");
_Static_assert(sizeof(SettingsPainter)==3320,"bounded Settings painter ARM32");
#endif
