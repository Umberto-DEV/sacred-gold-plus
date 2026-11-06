#ifndef SGP_UI_MODULE_H
#define SGP_UI_MODULE_H
/* Resident, main-thread UI-only loader; placement remains UNASSIGNED.
 * Caller owns a zeroed, 4-aligned, immovable heap11 record until RELEASED and
 * until every manager/bridge reference retires. Config is separately immutable
 * resident storage; finalize its full-y9/FAT/ROM identities AFTER composition.
 * No config inside overlay54, no self-CRC. CRC detects accidental corruption;
 * installer independently proves exact packed/expanded SHA and in-place BLZ.
 * Caller excludes foreign FS/CARD/direct-overlay producers, Field teardown,
 * native matching destructors and writes to admitted source/cache allocations.
 * Actual native AP-hook destination ownership and hardware timing are caller
 * gates. No timeout, cancellation or error result permits freeing a live file.
 * READY image is immutable. Check grants only a synchronous callback address.
 * Release requires scene Exit and complete sampler/BG/IRQ/DMA/font/FS/resource/
 * transaction/heap/destructor retirement, with no dynamic frame still active.
 */
typedef struct {
 unsigned magic,abi,role,generation,overlay_id,file_id,base,size;
 unsigned bss,sinit_start,sinit_end,packed,crc,init_offset,main_offset,exit_offset;
 unsigned packed_crc,y9_crc,y9_rom_offset,y9_bytes,rom_bytes,file_top,file_bottom,y9_entries;
} UiModuleConfig;
typedef struct {
 unsigned magic,self,phase,role,generation,config_address,slot,error;
 unsigned cancelled,read_kind,read_size,read_start,read_end,read_return;
 unsigned crc_cursor,crc_acc,close_attempts,started,wifi_done,registry_owned;
 unsigned file_bound,file_opened,y9_verified,image_verified;
 UiModuleConfig config;
 unsigned file[18],canary[2],info[11],archive[13],source[8],registry[16],table_storage[1040];
} UiModule;
typedef enum { UI_MODULE_REFUSED,UI_MODULE_MORE,UI_MODULE_READY,UI_MODULE_FAILED,
 UI_MODULE_RELEASED,UI_MODULE_HOLD } UiModuleResult;
enum { UI_MODULE_P_ZERO,UI_MODULE_P_META_OPEN,UI_MODULE_P_META_INVALIDATE,
 UI_MODULE_P_META_READ,UI_MODULE_P_META_WAIT,UI_MODULE_P_META_CLOSE,UI_MODULE_P_META_VERIFY,
 UI_MODULE_P_RESERVE,UI_MODULE_P_IMAGE_OPEN,UI_MODULE_P_IMAGE_CLEAR,UI_MODULE_P_IMAGE_READ,
 UI_MODULE_P_IMAGE_WAIT,UI_MODULE_P_IMAGE_CLOSE,UI_MODULE_P_PACKED_VERIFY,UI_MODULE_P_START,
 UI_MODULE_P_DECODED_VERIFY,UI_MODULE_P_WIFI,UI_MODULE_P_READY,UI_MODULE_P_ABORT_DRAIN,
 UI_MODULE_P_ABORT_CLOSE,UI_MODULE_P_ABORT_END,UI_MODULE_P_RELEASE_END,
 UI_MODULE_P_ABORT_UNRESERVE,UI_MODULE_P_RELEASE_UNRESERVE,UI_MODULE_P_FAILED,
 UI_MODULE_P_RELEASED,UI_MODULE_P_HOLD };
enum { UI_MODULE_SETTINGS=1,UI_MODULE_GUIDE=2 };
enum { UI_MODULE_E_NONE,UI_MODULE_E_CANCELLED,UI_MODULE_E_METADATA,UI_MODULE_E_OPEN,
 UI_MODULE_E_READ,UI_MODULE_E_PACKED,UI_MODULE_E_DECODED,UI_MODULE_E_SOURCE,
 UI_MODULE_E_REGISTRY,UI_MODULE_E_BOOT,UI_MODULE_E_OWNERSHIP };
/* Invalid identity/argument refuses without mutation. Masked service calls
 * defer with MORE without mutation. verify_bytes is 1..4096, not a deadline.
 * MORE/HOLD retain all possible owners. FAILED proves no file/reservation.
 * No API resets an initialized record; next begin requires newer generation.
 * READY cancel refuses: scene cleanup plus release is the only safe exit.
 */
unsigned ui_module_init(UiModule *);
UiModuleResult ui_module_begin(UiModule *,const UiModuleConfig *,unsigned,unsigned);
UiModuleResult ui_module_step(UiModule *,unsigned,unsigned,unsigned verify_bytes);
/* cap1..16; batch checked progress, yield on async submission, no progress,
 * before and after registry/decompression/Wi-Fi lifetime transitions. */
UiModuleResult ui_module_pump(UiModule *,unsigned,unsigned,unsigned verify_bytes,unsigned cap);
UiModuleResult ui_module_cancel(UiModule *,unsigned,unsigned);
unsigned ui_module_check(UiModule *,unsigned,unsigned,unsigned selector);
UiModuleResult ui_module_release(UiModule *,unsigned,unsigned);
#endif
