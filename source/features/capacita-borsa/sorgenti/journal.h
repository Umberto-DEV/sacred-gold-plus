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
int cap_record_erased(const CapRecord *r);
int cap_record_owned_prefix(const CapRecord *r);
/* Slots the native pocket compaction can leave behind ({id,0}) and out-of-range
 * ids never reach flash: they are zeroed and pushed to the tail of their pocket. */
void cap_record_create(CapRecord *r,const CapBag *b,u32 generation,u16 main_crc);
/* -1 ours but damaged, 0 absent (erased or not ours at all), 1 matching,
 * 2 intact but stale. Nothing here is fatal: the caller degrades, never stops. */
int cap_record_restore(const CapRecord *r,CapBag *b,u32 generation,u16 main_crc);
#endif
