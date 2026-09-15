/* Sacred Gold Plus: expanded inventory. Project-owned code, GPL-3.0-or-later. */
#ifndef SGP_CAP_CORE_H
#define SGP_CAP_CORE_H
#include <stdint.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef struct { u16 id, quantity; } CapSlot;
typedef struct { CapSlot slots[594]; u16 registered[2]; } CapBag;
u32 cap_count(u32 pocket);
u32 cap_old_count(u32 pocket);
u32 cap_old_offset(u32 pocket);
CapSlot *cap_pocket(CapBag *bag, u32 pocket);
void cap_import(CapBag *bag, const CapSlot *native);
void cap_export(const CapBag *bag, CapSlot *native);
void cap_reconcile(CapBag *bag, CapSlot *native, CapSlot *snapshot);
void cap_copy(const CapBag *src, CapBag *dst);
void cap_clear(CapBag *bag);
int cap_add(CapBag *bag, u32 pocket, u16 item, u16 quantity);
int cap_has_space(CapBag *bag, u32 pocket, u16 item, u16 quantity);
int cap_take(CapBag *bag, u32 pocket, u16 item, u16 quantity);
int cap_pocket_take(CapSlot *slots, u32 count, u16 item, u16 quantity);
u16 cap_quantity(CapSlot *slots, u32 count, u16 item);
void cap_move(CapSlot *slots, u32 count, u32 from, u32 to);
#endif
