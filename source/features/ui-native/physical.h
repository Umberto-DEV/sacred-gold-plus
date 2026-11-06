#ifndef SGP_UI_PHYSICAL_H
#define SGP_UI_PHYSICAL_H
/* Internal ARM9 main-thread interface. No IRQ, ARM7, DMA or other task may
 * access the slot. Owner is opaque: activate after Init, deactivate before
 * teardown/free. A recycled address needs a new token. Hooks never dereference
 * owner. Addresses/code reservation remain UNASSIGNED; build config is required.
 * Before the first call, the configured resident slot must be cold-initialized
 * to 48 zero bytes. Never clear it during an executable session to recycle
 * exhausted counters. Native config pins and code/slot placement are installer
 * responsibilities; the synthetic test addresses are not reservations.
 * out must be an actual aligned, writable, caller-owned 16-byte object in the
 * audited heap or a live caller frame in the SYS DTCM envelope (outside the
 * callee stack). It must not overlap owner/app state,
 * globals or the sampler. Range checks do not establish lifetime/ownership.
 * Consume belongs after the native lid/keypad pair. NONE/INVALID preserve out.
 * SUSPEND is a control event; rearm the consumer then explicitly acknowledge.
 */
typedef unsigned int PhysicalToken;
typedef struct {
    unsigned int serial, suspend;
    unsigned short held, pressed, repeated, flags;
} PhysicalSample;
enum { PHYS_NONE, PHYS_FRESH, PHYS_SUSPEND, PHYS_INVALID };
enum { PHYS_RELEASE_ONLY = 1 };
PhysicalToken physical_activate(const void *, unsigned short);
unsigned physical_deactivate(const void *, PhysicalToken);
unsigned physical_consume(const void *, PhysicalToken, PhysicalSample *);
unsigned physical_ack_suspend(const void *, PhysicalToken, unsigned int);
void physical_after_native_mapping(void);
void physical_lid_action(void);
#endif
