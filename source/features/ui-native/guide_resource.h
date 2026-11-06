#ifndef SGP_UI_GUIDE_RESOURCE_H
#define SGP_UI_GUIDE_RESOURCE_H
#include "font.h"
/* Main-thread exclusive reader. Fresh records are zero; never reset a live one.
 * Reader and lease are persistent fields of the SAME checked heap38 app root.
 * One authoritative immovable heap token, config and app remain live until
 * RELEASED; native FSFile80 stays here through delayed reads/failed close/HOLD.
 * Installer binds existing a/0/2/7 member829 to the final immutable FAT/file
 * properties and CRC. This detects corruption, not malicious CRC collisions.
 * No foreign FS/CARD/cache writer, mode switch, allocator or app teardown.
 * Views are temporary SYS DTCM outputs copied by the caller before return.
 * One move-only Guide lease pins the text root separately from the UIR1 font
 * lease. ALL font jobs must retire/cancel before drop; this reader does not
 * discover generic font jobs. No copying/resetting owners as capabilities.
 * All slices expire at drop. No timeout/error permits freeing a bound file.
 */
typedef struct {
 unsigned magic,abi,language,generation,file_id,file_top,file_bottom,rom_bytes;
 unsigned file_bytes,member_offset,member_bytes,member_crc,categories,entries,reserved[2];
} UiGuideConfig;
typedef struct {
 unsigned fs[20]; UiGuideConfig config; unsigned archive[13],source[4];
 unsigned magic,self,phase,generation,config_address; UiHeap *heap;
 unsigned root,failed,cancelled,file_bound,file_opened,read_offset,read_count,read_return;
 unsigned crc,cursor,close_attempts,lease_address,epoch,verify_entry;
} UiGuideReader;
typedef struct {
 UiGuideReader *reader; unsigned self,generation,epoch; UiTextOwner owner;
} UiGuideLease;
typedef struct { unsigned id,first,count,total; UiTextSlice title; } UiGuideCategory;
typedef struct { unsigned id,category,pages,index; UiTextSlice title; } UiGuideEntry;
typedef struct { unsigned entry,page,lines,reference; } UiGuidePage;
typedef enum { UI_GUIDE_REFUSED,UI_GUIDE_MORE,UI_GUIDE_READY,UI_GUIDE_FAILED,
 UI_GUIDE_RELEASED,UI_GUIDE_HOLD } UiGuideResult;
enum { UI_GGR_ZERO,UI_GGR_OPEN,UI_GGR_SEEK,UI_GGR_ALLOC,UI_GGR_READ,UI_GGR_WAIT,
 UI_GGR_CLOSE,UI_GGR_CRC,UI_GGR_DIRECTORY,UI_GGR_READY,UI_GGR_ABORT_DRAIN,
 UI_GGR_ABORT_CLOSE,UI_GGR_FAILED,UI_GGR_RELEASED,UI_GGR_HOLD };
unsigned ui_guide_init(UiGuideReader *);
UiGuideResult ui_guide_begin(UiGuideReader *,const UiGuideConfig *,UiHeap *);
/* Budget1..4096 CRC bytes; directory validation at most64 records per step.
 * Masked services defer unchanged. One async member read is <=131072; WAIT polls,
 * never FS_WaitAsync. Caller returns to the native scheduler while pending. */
UiGuideResult ui_guide_step(UiGuideReader *,unsigned budget);
/* cap1..16 checked steps. Yield immediately after submitting an async read,
 * or on no progress/failed close/cancellation; never spin on pending I/O. */
UiGuideResult ui_guide_pump(UiGuideReader *,unsigned budget,unsigned cap);
UiGuideResult ui_guide_cancel(UiGuideReader *);
UiGuideResult ui_guide_release(UiGuideReader *);
unsigned ui_guide_acquire(UiGuideReader *,UiGuideLease *);
unsigned ui_guide_drop(UiGuideLease *);
/* Known immutable aliases and cyclic references are legal. Lookup does not
 * assume ID sorting. Each string has 1..127 glyphs then EOS, <=128 u16 units.
 * Native font-width/rectangle admission belongs to ui_font_begin, not here.
 * Refusal leaves output unchanged. No full-root rescan/hash during painting. */
unsigned ui_guide_category(const UiGuideLease *,unsigned,UiGuideCategory *);
unsigned ui_guide_entry(const UiGuideLease *,unsigned,unsigned,UiGuideEntry *);
unsigned ui_guide_find(const UiGuideLease *,unsigned,unsigned *);
unsigned ui_guide_page(const UiGuideLease *,unsigned,unsigned,UiGuidePage *);
unsigned ui_guide_line(const UiGuideLease *,unsigned,unsigned,unsigned,UiTextSlice *);
#endif
