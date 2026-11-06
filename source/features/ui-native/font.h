#ifndef SGP_UI_FONT_H
#define SGP_UI_FONT_H
#include "resource.h"
#include "native_abi.h"
/* Main-only, nonreentrant, single app. All records are caller-owned persistent
 * allocations; zero fresh lease/job before first use, never reset live records.
 * Move-only ownership is a caller contract, not a registry/copy-proof capability.
 * No concurrent text/cache writer, mode switch, free, old Guide/Naming/Summary
 * lifecycle, or yielding delegate is allowed until release succeeds. HOLD is
 * nonterminal: keep app and roots alive, do not finish Exit or force cleanup.
 * HOLD with manager==0 retains an unpublished acquisition token only: no native
 * reference/tuple was acquired. Check/release remain HOLD and never decrement it.
 * No code/state placement assigned. Compose after heap.c and resource.c.
 */
typedef enum { UI_FONT_REFUSE, UI_FONT_READY, UI_FONT_ACTIVE, UI_FONT_DONE,
 UI_FONT_HOLD, UI_FONT_DEFER, UI_FONT_CANCELLED, UI_FONT_INVALID } UiFontStatus;
typedef struct { unsigned kind; const void *root; unsigned bytes,epoch,live; } UiTextOwner;
typedef struct { const UiTextOwner *owner; unsigned offset,units,policy; } UiTextSlice;
#define UI_TEXT_UIR1 1u
#define UI_TEXT_SGG1 2u
#define UI_TEXT_BUFFER 3u
#define UI_TEXT_SINGLE 0u
#define UI_TEXT_LINES 1u
/* A trusted identified external owner, not permission from a boolean. Scene
 * code may supply only a real immutable allocation with a no-free/no-mode-switch
 * contract for the whole lease. NULL is the production default: refuse direct
 * caches with unidentified owners. The CPU fixture tests this generic route;
 * no existing game scene is thereby admitted. */
typedef struct { const void *cache; unsigned bytes,epoch,live,owner_id; } UiFontCacheOwner;
typedef struct { unsigned char flags[2],colors[6],lookup[512],glyph[130],pad[2]; } UiFontScratch;
typedef struct UiFontPrintJob UiFontPrintJob;
typedef struct {
 unsigned state,owned; UiResourceLease resource;
 unsigned root,bytes,manager,widths,narc,gmif,prior_mode,prior_fn,prior_cache,cache;
 const UiFontCacheOwner *cache_owner; UiFontCacheOwner cache_snapshot;
 UiFontPrintJob *job;
} UiFontLease;
typedef struct {
 const unsigned short *current; UiNativeWindow16 *window;
 unsigned char pad,font,x,y; unsigned short current_x,current_y,letter,line;
 unsigned char unk14,fg,bg,shadow; unsigned short glyph_table;
 unsigned char unk1a,unk1b; void *callback; unsigned char sub[7],active;
 unsigned char state,speed,delay,scroll,id,unk2d; unsigned short unk2e; void *unk30;
} UiFontPrinter52;
struct UiFontPrintJob {
 UiFontPrinter52 printer; const unsigned short *text; unsigned units,consumed;
 UiFontLease *lease; unsigned phase,lines,cap; UiNativeWindow16 window;
 const UiTextOwner *owner; UiTextOwner owner_snapshot; unsigned policy;
 UiFontScratch *scratch; const void *front; unsigned pixel_bytes;
 unsigned expected_x,expected_y,start_x,start_y;
};
typedef struct {
 UiNativeWindow16 *window; const void *front; unsigned pixel_bytes;
 UiTextSlice text; UiFontScratch *scratch;
 unsigned char x,y,max_lines,fg,bg,shadow,letter_spacing,line_spacing;
} UiFontRequest;
UiFontStatus ui_font_acquire(UiFontLease *,UiResourceReader *,const UiFontCacheOwner *);
UiFontStatus ui_font_check(UiFontLease *);
/* UIR1 callers derive the slice from ui_res_text under lease.resource. SGG1
 * callers pin their separately validated <=128KiB root; plain lines <=128 units.
 * BUFFER is a dedicated ui_alloc38 root under the reader heap: aligned4 bytes
 * 4..4096, slices1..128 units. Caller formats before publication, sets nonzero
 * epoch/live=1, and pins root/owner/window until cancel or retirement. Never
 * mutate/free an active pool; retire before formatting or changing its epoch.
 * The bounded ledger/header checks do not make copied owners revocable.
 * owner.live=1 and address bounds do not establish semantic root ownership.
 * Request and slice are copied; only the explicitly live owner/window persist.
 * front/back are actual owned disjoint allocations. Only inactive back is drawn.
 */
UiFontStatus ui_font_begin(UiFontLease *,UiFontPrintJob *,const UiFontRequest *);
UiFontStatus ui_font_step(UiFontLease *,UiFontPrintJob *,unsigned budget);
UiFontStatus ui_font_cancel(UiFontLease *,UiFontPrintJob *);
UiFontStatus ui_font_release(UiFontLease *);
#endif
