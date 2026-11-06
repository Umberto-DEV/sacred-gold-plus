#ifndef SGP_UI_PERSISTENT_H
#define SGP_UI_PERSISTENT_H
/* Private resident main-loop primitive; no production code placement assigned.
 * persistent.c compiles independently through heap_internal.h; it may also be
 * composed with heap.c in one translation unit without duplicate definitions.
 * Exactly one authoritative token/root exists for this UI subsystem. All token
 * storage is caller-owned, live, writable and 4-aligned in the native heap
 * envelope or a live SYS DTCM frame. Optional compile configuration
 * UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS=0x023D7B20u additionally admits exactly
 * that 40-byte slot; other values fail compilation. Default admits no reserve
 * addresses. This symbolic binding grants no installation/storage ownership:
 * the final map/installer must prove this slot and cold-initialize it once.
 * Bounds do not establish storage lifetime.
 * Initial token and every MOVE destination must be zeroed inactive storage;
 * never reset/copy a live token. Move ONLY through ui_persistent_move.
 *
 * Bootstrap alloc token must be OUTSIDE heap11's whole backing (including its
 * parent NNS header). A durable outside token can own the root for its whole
 * lifetime, without MOVE. Alternatively MOVE a live SYS/bootstrap token into
 * the root's requested payload, then MOVE back to live outside storage BEFORE
 * free. A configured resident token remains authoritative across callbacks.
 * The root itself never moves. Retire all callbacks/managers/leases, release
 * the resident module and prevent FieldSystem/heap11 teardown before free.
 * No IRQ/DMA/parallel allocator consumer or external Heap_Free may race or
 * bypass this record. Arbitrary forged/stale copies after address reuse are
 * not revocable capabilities; the caller enforces the single-owner contract.
 *
 * generation is a nonzero, monotonically assigned lifetime ID from the future
 * caller's authoritative resident counter, with no wrap. It may precede and
 * differ from physical-input activation. Reusing a released token requires a
 * greater generation; a new zeroed/moved token cannot prove global monotonicity.
 */
typedef struct {
    unsigned magic,self,generation,root,bytes,handle,parent,raw,backing,index;
} UiPersistent;
enum { UI_PERSISTENT_REFUSED=0, UI_PERSISTENT_RELEASED=1, UI_PERSISTENT_HOLD=2 };
/* NULL normally leaves token/count/native ownership unchanged. An unexpected
 * non-NULL lower NNS result instead retains UI_PERSISTENT_HELD_MAGIC and the
 * attempted root identity without touching it/counting/freeing it. Therefore
 * NULL alone NEVER authorizes abandoning a changed token or returning from its
 * last live stack frame. The caller must retain that bootstrap token until an
 * external ownership decision; no recovery/reset is provided here. A durable
 * token must remain live on HOLD across callback returns; never clear it or
 * fallback/free/MOVE it to escape uncertainty. Protecting heap11/FieldSystem
 * teardown is a future caller gate, not proved by this primitive. No mutable
 * global state or native failure/reset entry is used by this primitive.
 */
#define UI_PERSISTENT_HELD_MAGIC 0x48504955u
/* bytes1..0x4000, head allocation; payload rounded to4 and zeroed. Native used
 * extent includes16B GF+16B NNS and may absorb up to16B extra trailing slack.
 * IRQ-enabled IME1 admission; saved I restored, IME unchanged on every path.
 */
void *ui_persistent_alloc(UiPersistent *,unsigned bytes,unsigned generation);
/* 1 transfers ownership/self and clears source; 0 refuses unchanged; 2 holds
 * unchanged on uncertain ownership. Destination may be within requested root
 * payload or wholly outside its FULL native extent, never header/slack alias.
 */
unsigned ui_persistent_move(UiPersistent *destination,UiPersistent *source,unsigned generation);
/* 1 frees once and retains magic/self/generation with cleared ownership;
 * 0 invalid/stale/retired invocation; 2 uncertain ownership or token in the
 * allocation being freed. HOLD never retires owners or modifies heap/count.
 */
unsigned ui_persistent_free(UiPersistent *,unsigned generation);
#endif
