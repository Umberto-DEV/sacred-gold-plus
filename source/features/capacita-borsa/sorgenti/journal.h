/* One inventory extension per native save bank, committed before its main data. */
#ifndef SGP_CAP_JOURNAL_H
#define SGP_CAP_JOURNAL_H
#include "core.h"
#define CAP_RECORD_MAGIC 0x32353242u /* B252 */
typedef struct {
    u32 magic;
    u16 version,size;
    u32 generation;
    u16 main_crc,reserved;
    CapSlot extra[108];
    u32 crc;
} CapRecord;
_Static_assert(sizeof(CapRecord)==452,"the on-flash extension record is 452 bytes");
_Static_assert(sizeof(CapBag)==2380,"the runtime Bag is 594 slots plus two registered items");
int cap_record_erased(const CapRecord *r);
/* 1 when all 452 bytes are identical: erased, zeroed or wiped with a pattern.
 * Such a destination holds no data and may be claimed by a write. */
int cap_record_uniform(const CapRecord *r);
int cap_record_owned_prefix(const CapRecord *r);
/* Slots the native pocket compaction can leave behind ({id,0}) and out-of-range
 * ids never reach flash: they are emptied IN PLACE, so every cell the player
 * filled keeps the index it had in the Bag. */
void cap_record_create(CapRecord *r,const CapBag *b,u32 generation,u16 main_crc);
/* -1 ours but damaged, 0 absent (erased or not ours at all), 1 matching,
 * 2 intact but stale. Nothing here is fatal: the caller degrades, never stops. */
int cap_record_restore(const CapRecord *r,CapBag *b,u32 generation,u16 main_crc);
#endif
