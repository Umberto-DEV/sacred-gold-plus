#ifndef SGP_UI_BG_H
#define SGP_UI_BG_H
#include "heap.h"
#include "native_abi.h"
/* One authoritative state, initially zero, caller-owned and live through destroy.
 * State/token bounds do not prove lifetime: a containing caller frame or owned
 * app allocation must remain live and separate from all acquired roots.
 * Pass the current authoritative UiHeap after any legal token MOVE.
 * Returns 1 on success (begin returns its Window address), 0 on refusal.
 * Nonzero owned flags after failure mean HOLD: retain state/roots/heap for
 * inspection or retry; never pretend cleanup succeeded or free the container.
 * All addresses/production deadline UNASSIGNED. Main-thread only; no IRQ/DMA
 * writer may touch these allocations. Entry additionally requires upstream
 * Field callbacks, auto-DMA, printers, fades and tasks retired/quiescent.
 * Register checks cannot establish that lifecycle precondition.
 */
typedef struct {
    unsigned magic, generation, owned, phase;
    void *roots[5];
    UiNativeWindow16 windows[2];
    unsigned version[2], front, pending, pendingVersion, preparing;
    unsigned rows, complete, fontReady, deadline, attached, callbackOwned, callbackGeneration;
    /* Transient recompiled ABI: first120 bytes remain unchanged. */
    void *lowerRoots[4]; /* map0,map1,pixels0,pixels1; Guide only */
    UiNativeWindow16 lowerWindows[2];
    unsigned lowerRows, role; /* immutable role0 Settings / role1 Guide */
} UiBg;
/* Distinct from every valid 22-row mask: exact native static image admitted. */
#define UI_BG_STATIC_BALL 0x42414c4cu
/* One pre-publication install: exact private native3552-byte compact payload,
 * pinnedCRC and geometry before any MMIO; source is readonly during the call.
 * No allocation. Scene retains its resource lease through BG retirement.
 * SUB BG0 mapF000/characters0/palette0 stay static across upper publication. */
unsigned ui_bg_install_ball(UiHeap *,UiBg *,unsigned,const void *compact,unsigned bytes);
enum { UI_BG_NONE=2, UI_BG_STORAGE=1, UI_BG_DISPLAY=2, UI_BG_CLOSING=3 };
unsigned ui_bg_create(UiHeap *, UiBg *, unsigned generation);
unsigned ui_bg_create_guide(UiHeap *, UiBg *, unsigned generation);
unsigned ui_bg_destroy(UiHeap *, UiBg *, unsigned generation);
typedef struct { unsigned first, count; } UiBgRows;
typedef struct {
    unsigned x,y,width,height;
    const void *tiles;
    unsigned tileBytes;
    const void *palette;
    unsigned paletteBytes;
} UiBgFrame;
/* Pixel/palette sources are caller-owned, readonly, 4-byte-aligned MAIN RAM.
 * Request descriptors may also be in live caller SYS DTCM. Their full declared
 * extent live until return. No resource identity/CRC assertion is made here.
 * begin returns the owned window only during a successful preparation lease;
 * callers must stop all writes when ready succeeds or retirement starts.
 * Normal begin is a complete recompose: fill/paint, upload all 22 rows,
 * exactly one explicit frame/unframed decision, then ready commits the final map. Further pixel edits
 * require uploading their rows again before ready. Retire precedes destroy;
 * re-entry requires destruction and a fresh create. No implicit cancellation.
 * Versions are nonzero and strictly increase across both canvases; wraparound
 * requires a new lifecycle. Callback retirement precedes containing-app free. */
unsigned ui_bg_enter(UiHeap *,UiBg *,unsigned,const void *fontPalette32);
/* Immutable entry backdrop: owned MAIN palette0 only; SUB remains black.
 * RGB555 >0x7fff refuses before display/owner mutation. Old entry defaults0. */
unsigned ui_bg_enter_backdrop(UiHeap *,UiBg *,unsigned,const void *fontPalette32,unsigned main_rgb555);
unsigned ui_bg_begin(UiHeap *,UiBg *,unsigned,unsigned index);
/* Retained begin preserves this hidden canvas's map, pixels, frame and palettes.
 * previous must exactly match its nonzero completed version; mask is nonzero
 * and contains only bits 0..21. The caller attests that its immutable per-buffer
 * render plan matches that version and edits only invalidated rows. A version
 * or pointer cannot prove that contract. Geometry/frame/style changes require
 * normal begin. No cancellation or reuse of a partially edited old version:
 * failure retires the entire lifecycle. ready still requires all rows uploaded.
 * Invalidate BEFORE further pixel writes, including writes after an upload;
 * fill invalidates all rows even inside a retained preparation. */
unsigned ui_bg_begin_retained(UiHeap *,UiBg *,unsigned generation,unsigned index,
                              unsigned expected_previous_version,unsigned dirty_row_mask);
/* Seed an unframed upper hidden canvas from the completed front, then edit
 * dirty rows. Caller binds its exact valid front render history/version.
 * No ring tiles/palettes or paired lower canvases; no allocation or front write.
 * Full hidden pixels are uploaded once before incremental painting. */
unsigned ui_bg_begin_copy(UiHeap *,UiBg *,unsigned generation,unsigned index,unsigned dirty_row_mask);
unsigned ui_bg_invalidate_rows(UiHeap *,UiBg *,unsigned generation,unsigned mask);
unsigned ui_bg_fill(UiHeap *,UiBg *,unsigned,unsigned color);
unsigned ui_bg_rows(UiHeap *,UiBg *,unsigned,const UiBgRows *);
unsigned ui_bg_frame(UiHeap *,UiBg *,unsigned,const UiBgFrame *);
/* Flat upper canvas decision; no native map/char/palette mutation. Exactly once
 * per full begin; retained preserves the previous decoration decision. */
unsigned ui_bg_unframed(UiHeap *,UiBg *,unsigned generation);
/* Guide uses the same index/version/preparing/pending for upper and lower.
 * begin prepares both; lower is always unframed. Lower Window lease and all
 * writes expire at ready/retirement. Settings refuses every lower operation.
 * Same invalidation-before-write/no-partial-cancellation caller contract. */
unsigned ui_bg_lower_window(UiHeap *,UiBg *,unsigned generation);
unsigned ui_bg_lower_fill(UiHeap *,UiBg *,unsigned generation,unsigned color);
unsigned ui_bg_lower_rows(UiHeap *,UiBg *,unsigned generation,const UiBgRows *);
unsigned ui_bg_lower_invalidate_rows(UiHeap *,UiBg *,unsigned generation,unsigned mask);
typedef struct { unsigned previous, upper_dirty, lower_dirty; } UiBgRetainedPair;
/* Both caller render plans must attest this buffer's exact previous version.
 * Each mask uses bits0..21; at least one is nonzero. Descriptor may live in the
 * admitted caller SYS stack. Old ui_bg_begin_retained is Settings-only. */
unsigned ui_bg_begin_guide_retained(UiHeap *,UiBg *,unsigned generation,unsigned index,
                                   const UiBgRetainedPair *);
unsigned ui_bg_ready(UiHeap *,UiBg *,unsigned,unsigned version);
/* Explicit calibrated deadline required; this primitive assigns no default. */
unsigned ui_bg_publish(UiBg *,unsigned generation,unsigned last_start_line);
unsigned ui_bg_register(UiBg *,unsigned generation,unsigned last_start_line);
unsigned ui_bg_retire(UiHeap *,UiBg *,unsigned generation);
#endif
