#include "physical.h"

#if !defined(SGP_PHYSICAL_SLOT_ADDR) || !defined(SGP_PHYSICAL_SYSTEM_ADDR) || \
    !defined(SGP_PHYSICAL_KEYINPUT_ADDR) || !defined(SGP_PHYSICAL_SHARED_ADDR) || \
    !defined(SGP_PHYSICAL_MAPPING_ADDR) || !defined(SGP_PHYSICAL_LID_ADDR)
#error "Physical sampler requires explicit slot and native address configuration"
#endif

typedef unsigned int u32;
typedef unsigned short u16;
struct PhysicalSlot {
    const void *owner;
    u32 generation, serial, consumed, suspend, acknowledged;
    u32 repeat_counter, flags;
    u16 previous, held, pressed, repeated, release_mask, reserved;
    u32 sample_suspend;
};
#define ASSERT(c) _Static_assert((c), #c)
ASSERT(sizeof(void *) == 4);
ASSERT(sizeof(struct PhysicalSlot) == 48);
ASSERT(__alignof__(struct PhysicalSlot) == 4);
ASSERT(sizeof(PhysicalSample) == 16);
ASSERT(__alignof__(PhysicalSample) == 4);
#define OFFSET(f, n) ASSERT(__builtin_offsetof(struct PhysicalSlot, f) == n)
OFFSET(owner,0); OFFSET(generation,4); OFFSET(serial,8); OFFSET(consumed,12);
OFFSET(suspend,16); OFFSET(acknowledged,20); OFFSET(repeat_counter,24);
OFFSET(flags,28); OFFSET(previous,32); OFFSET(held,34); OFFSET(pressed,36);
OFFSET(repeated,38); OFFSET(release_mask,40); OFFSET(reserved,42);
OFFSET(sample_suspend,44);
ASSERT(__builtin_offsetof(PhysicalSample, serial) == 0);
ASSERT(__builtin_offsetof(PhysicalSample, suspend) == 4);
ASSERT(__builtin_offsetof(PhysicalSample, held) == 8);
ASSERT(__builtin_offsetof(PhysicalSample, pressed) == 10);
ASSERT(__builtin_offsetof(PhysicalSample, repeated) == 12);
ASSERT(__builtin_offsetof(PhysicalSample, flags) == 14);
ASSERT((SGP_PHYSICAL_SLOT_ADDR & 3) == 0);
ASSERT(SGP_PHYSICAL_SLOT_ADDR >= 0x02000000u &&
       SGP_PHYSICAL_SLOT_ADDR <= 0x02400000u - 48);
#define SLOT ((volatile struct PhysicalSlot *)SGP_PHYSICAL_SLOT_ADDR)
#define READ16(a) (*(volatile u16 *)(a))
#define TIMER(n) (*(volatile u32 *)(SGP_PHYSICAL_SYSTEM_ADDR + (n)))
#define BARRIER() __asm__ volatile("" ::: "memory")
enum { ACTIVE=1, RELEASE=2, BASELINE=4, CLOSED=8, EXHAUSTED=16,
       CYCLE_STARTED=32, CYCLE_SAMPLE=64, RELEASE_FRAME=128 };

static unsigned valid_owner(const void *owner) {
    u32 p=(u32)owner;
    return !(p & 3) && p >= 0x02000000u && p < 0x02400000u &&
           !(p >= SGP_PHYSICAL_SLOT_ADDR && p < SGP_PHYSICAL_SLOT_ADDR+48);
}
static unsigned valid_out(PhysicalSample *out) {
    u32 p=(u32)out;
    return !(p & 3) &&
        ((p >= 0x0226EC40u && p <= 0x023C0000u-16) ||
         (p >= 0x027E0080u && p <= 0x027E3780u-16)) &&
        !(p < SGP_PHYSICAL_SLOT_ADDR+48 && p+16 > SGP_PHYSICAL_SLOT_ADDR);
}
static unsigned matches(const void *owner, PhysicalToken token) {
    return (SLOT->flags & ACTIVE) && token && SLOT->owner == owner &&
           SLOT->generation == token;
}
static unsigned folded(void) { return READ16(SGP_PHYSICAL_SHARED_ADDR) & 0x8000; }
static void invalidate(void) {
    SLOT->flags &= EXHAUSTED;
    SLOT->owner = (const void *)0;
    BARRIER();
}
static void rearm(void) {
    SLOT->consumed = SLOT->serial;
    SLOT->flags |= RELEASE|BASELINE;
}
static void observe_closed(void) {
    rearm();
    if (!(SLOT->flags & CLOSED)) {
        if (SLOT->suspend == 0xffffffffu) { invalidate(); return; }
        ++SLOT->suspend;
        SLOT->flags |= CLOSED;
    }
}
PhysicalToken physical_activate(const void *owner, u16 release_mask) {
    u32 generation;
    if (!valid_owner(owner) || !release_mask || (release_mask & ~0x2fffu) ||
        (SLOT->flags & ACTIVE)) return 0;
    if (SLOT->generation == 0xffffffffu) {
        SLOT->flags |= EXHAUSTED;
        return 0;
    }
    generation = SLOT->generation + 1;
    SLOT->serial=0; SLOT->consumed=0;
    SLOT->suspend=0; SLOT->acknowledged=0;
    SLOT->repeat_counter=0; SLOT->previous=0;
    SLOT->held=0; SLOT->pressed=0; SLOT->repeated=0;
    SLOT->release_mask=release_mask; SLOT->reserved=0; SLOT->sample_suspend=0;
    SLOT->generation=generation;
    SLOT->owner=owner;
    BARRIER();
    SLOT->flags=ACTIVE|RELEASE|BASELINE;
    return generation;
}
unsigned physical_deactivate(const void *owner, PhysicalToken token) {
    if (!matches(owner,token)) return 0;
    invalidate();
    return 1;
}
unsigned physical_ack_suspend(const void *owner, PhysicalToken token,
                              u32 observed_suspend) {
    if (!matches(owner,token)) return 0;
    if (folded()) { observe_closed(); return 0; }
    if (observed_suspend != SLOT->suspend) return 0;
    SLOT->acknowledged=observed_suspend;
    rearm();
    return 1;
}
unsigned physical_consume(const void *owner, PhysicalToken token,
                          PhysicalSample *out) {
    unsigned closed;
    if (!matches(owner,token) || !valid_out(out)) return PHYS_INVALID;
    /* Honor either volatile observation, including a close at the recheck. */
    closed=folded();
    if (!closed) closed=folded();
    if (closed) observe_closed();
    if (!matches(owner,token)) return PHYS_INVALID;
    if (SLOT->suspend != SLOT->acknowledged) {
        out->serial=0; out->suspend=SLOT->suspend;
        out->held=0; out->pressed=0; out->repeated=0; out->flags=0;
        return PHYS_SUSPEND;
    }
    if (closed) return PHYS_NONE;
    if (SLOT->serial == SLOT->consumed ||
        SLOT->sample_suspend != SLOT->acknowledged) {
        if ((SLOT->flags & (CYCLE_STARTED|CYCLE_SAMPLE)) == CYCLE_STARTED)
            rearm();
        return PHYS_NONE;
    }
    out->serial=SLOT->serial; out->suspend=SLOT->sample_suspend;
    out->held=SLOT->held; out->pressed=SLOT->pressed;
    out->repeated=SLOT->repeated;
    /* Publication carries the release-frame flag independently of the gate. */
    out->flags=(SLOT->flags & RELEASE_FRAME) ? PHYS_RELEASE_ONLY : 0;
    SLOT->consumed=SLOT->serial;
    return PHYS_FRESH;
}
void physical_after_native_mapping(void) {
    u16 held, pressed, repeated, shared, sample_flags=0;
    ((void (*)(void))SGP_PHYSICAL_MAPPING_ADDR)();
    if (!(SLOT->flags & ACTIVE)) return;
    held=READ16(SGP_PHYSICAL_KEYINPUT_ADDR);
    shared=READ16(SGP_PHYSICAL_SHARED_ADDR);
    held=((held|shared)^0x2fff)&0x2fff;
    if ((shared & 0x8000) || folded()) { observe_closed(); return; }
    SLOT->flags &= ~CLOSED;
    if (SLOT->suspend != SLOT->acknowledged) return;
    if (SLOT->serial == 0xffffffffu) { invalidate(); return; }
    pressed=held & (held ^ SLOT->previous);
    repeated=pressed;
    if (held && held == SLOT->previous) {
        --SLOT->repeat_counter;
        if (!SLOT->repeat_counter) {
            repeated=held;
            SLOT->repeat_counter=TIMER(0x54);
        }
    } else SLOT->repeat_counter=TIMER(0x58);
    SLOT->previous=held;
    if (SLOT->flags & (RELEASE|BASELINE)) {
        pressed=0; repeated=0; sample_flags=PHYS_RELEASE_ONLY;
        SLOT->flags &= ~BASELINE;
        if (!(held & SLOT->release_mask)) SLOT->flags &= ~RELEASE;
    }
    SLOT->held=held; SLOT->pressed=pressed; SLOT->repeated=repeated;
    SLOT->flags=(SLOT->flags & ~RELEASE_FRAME) |
                (sample_flags ? RELEASE_FRAME : 0);
    SLOT->sample_suspend=SLOT->suspend;
    SLOT->flags |= CYCLE_SAMPLE;
    BARRIER();
    ++SLOT->serial; /* LAST: same-main-thread publication, not IRQ atomicity. */
}
void physical_lid_action(void) {
    if (SLOT->flags & ACTIVE) {
        SLOT->consumed=SLOT->serial;
        SLOT->flags=(SLOT->flags|CYCLE_STARTED)&~CYCLE_SAMPLE;
        if (folded()) observe_closed();
    }
    ((void (*)(void))SGP_PHYSICAL_LID_ADDR)();
}
