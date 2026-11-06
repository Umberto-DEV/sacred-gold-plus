#ifndef SGP_UI_RESOURCE_H
#define SGP_UI_RESOURCE_H
#include "heap.h"
/* Internal main-loop API; no placement assigned. Reader must remain in a live
 * app allocation while active, never a returning stack frame. One authoritative
 * heap token, fixed in place from begin through release; moves only outside that
 * interval. Caller owns records and readable config storage: bounds do not prove
 * lifetime/ownership. No concurrent caller, callback, IRQ or DMA consumer.
 * init is for fresh unowned storage only, not a reset or cancellation API.
 * Config is 16 little-endian words in live readable main RAM or SYS DTCM; begin
 * copies it before FS use. Caller records must be writable native-heap or SYS
 * storage; reader itself must be in the app heap. A lease/slice record must not
 * alias this reader, the authoritative token, resource, native headers/tables.
 * Internal fields are private; callers must not alter them while live.
 * Leases are move-only, initially zero, must be returned exactly once; copies
 * are not capabilities. Every borrowed slice expires when its lease is dropped.
 * font=1 additionally pins the glyph view; the later font owner must retain its
 * lease across native tuple identity loss. This reader only observes the known
 * font0 cache at release, never installs, restores or forcibly detaches it.
 */
typedef struct { unsigned word[16]; } UiResourceConfig;
typedef enum { UI_RES_ZERO, UI_RES_OPEN, UI_RES_PREFIX, UI_RES_MEMBER,
 UI_RES_CLOSE, UI_RES_VERIFY, UI_RES_READY, UI_RES_FAILED,
 UI_RES_RELEASED, UI_RES_OWNERSHIP_HOLD } UiResPhase;
typedef enum { UI_RES_MORE, UI_RES_OK, UI_RES_ERROR, UI_RES_HELD } UiResPoll;
typedef struct {
 unsigned fs[20], prefix[117]; UiResourceConfig config;
 unsigned magic, phase, generation, owned, failed, cancelled, root;
 UiHeap *heap;
 unsigned crc, cursor, verify, entry, unit, text_cursor, previous, species;
 unsigned refs, font_refs, published, close_attempts;
 unsigned archive[13];
} UiResourceReader;
typedef struct { UiResourceReader *reader; unsigned generation, font; } UiResourceLease;
typedef struct { const void *data; unsigned bytes; } UiResourceSlice;
unsigned ui_res_init(UiResourceReader *);
UiResPoll ui_res_begin(UiResourceReader *, const UiResourceConfig *, UiHeap *);
UiResPoll ui_res_step(UiResourceReader *);
/* cap1..16; batch verification only, no repeated I/O retry in one call. */
UiResPoll ui_res_pump(UiResourceReader *,unsigned cap);
void ui_res_cancel(UiResourceReader *);
unsigned ui_res_can_release(const UiResourceReader *);
unsigned ui_res_release(UiResourceReader *);
unsigned ui_res_acquire(UiResourceReader *, UiResourceLease *, unsigned font);
unsigned ui_res_drop(UiResourceLease *);
unsigned ui_res_frame(const UiResourceLease *, unsigned frame, unsigned palette, UiResourceSlice *);
unsigned ui_res_glyphs(const UiResourceLease *, UiResourceSlice *);
unsigned ui_res_ball(const UiResourceLease *,UiResourceSlice *);
unsigned ui_res_font_palette(const UiResourceLease *, UiResourceSlice *);
/* text slice bytes includes final u16 FFFF; only restricted game glyphs/LF. */
unsigned ui_res_text(const UiResourceLease *, unsigned id, UiResourceSlice *);
#endif
