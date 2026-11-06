#ifndef SGP_UI_HEAP_H
#define SGP_UI_HEAP_H
/* Private ARM9 main-loop primitive, no production code/state placement assigned.
 * Caller owns a live aligned writable token in the native heap envelope or a
 * live SYS DTCM frame. The bounds checks establish neither ownership nor life.
 * Exactly ONE authoritative token exists: copying is a MOVE, after which the
 * old copy must never be used. Move stack->app after allocating app; move back
 * to live stack BEFORE freeing app. Never pass a freed containing allocation.
 * generation is nonzero caller lifecycle identity, not a global allocation grant.
 * Callers must retire callbacks/tasks and all other consumers before teardown.
 * No concurrent UI allocator consumer, IRQ allocator or DMA may touch this heap.
 * All allocations must be released through ui_free38; external Heap_Free is ABI
 * compatible but bypasses this ledger and is not an admitted lifecycle operation.
 */
typedef struct {
    unsigned int magic, generation, parent, raw, handle, backing, index;
    unsigned int acquired[16];
} UiHeap;
/* create preserves token on refusal; successful destroy zeroes the token.
 * Only 0x30000 (Options) and 0x40000 (Guide) are approved backing sizes.
 * An inactive caller token may contain arbitrary bytes. Do not create over a
 * live authoritative token. Copies are not revocable capabilities: native heap
 * metadata has no lifecycle generation; stale copies after address reuse are
 * excluded by the single-authoritative-token precondition above.
 */
unsigned ui_heap38_create(UiHeap *, unsigned int backing, unsigned int generation);
void *ui_alloc38(UiHeap *, unsigned int bytes, unsigned int tail);
unsigned ui_free38(UiHeap *, void *);
unsigned ui_heap38_destroy(UiHeap *);
#endif
