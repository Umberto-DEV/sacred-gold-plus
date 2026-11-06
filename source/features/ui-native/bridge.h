#ifndef SGP_UI_BRIDGE_H
#define SGP_UI_BRIDGE_H
#include "module.h"
#include "resource.h"
#include "guide_resource.h"
#include "persistent.h"
#include "heap.h"
#define UI_SCENE_CONTEXT_ABI 0x32435355u /* USC2; distinct from ModuleConfig ABI2. */
/* Resident native child adapter. Conditional B5 bindings are NOT installation
 * permission. Installer cold-initializes persistent40/control16 once, replaces
 * BOTH templates with ID_NONE, and excludes old54/Guide callbacks and all
 * competing child/FS/font owners for the complete lifetime. Never reset live
 * tokens or counters. Native manager40 and original Options args12 remain
 * separately owned by the native Field/outer task, never by the dynamic scene.
 */
typedef struct {
 unsigned abi,role,generation,field,options,input,args,app,physical_token;
 unsigned ui_config,guide_config,flags,error,heap_token,reserved[2];
} UiSceneContext;
typedef enum { UI_SCENE_MORE,UI_SCENE_READY,UI_SCENE_CLOSE,UI_SCENE_EXITED,
 UI_SCENE_HOLD } UiSceneResult;
/* All three dynamic entries: result(Context*, persistent scene-step*).
 * Context itself is the opaque physical owner; consume/ack use that same
 * pointer after native lid/keypad. Scene handles SUSPEND/release-only events.
 * Immutable identity/config words may never be changed by dynamic code.
 * app/flags/error are scene outputs; physical_token belongs to this Bridge.
 * heap_token is immutable: the sole UiHeap authority lives in this checked
 * heap11 root throughout the Scene, never in app or a returning SYS frame.
 * Create once on the fresh zero token; destroy successfully before EXITED.
 * After free(app), clear app immediately. Destroy refusal may return MORE
 * with the same live token, or terminal HOLD; neither permits root/code release.
 * app is a distinct checked heap38 root, Options+24/generation+28/SUI1+2C.
 * EXITED promises all owned jobs/resources/font/BG/FS/transactions/destructors
 * retired, app NULL and heap38 destroyed. No independent task/IRQ/native-printer
 * callback registration is permitted: only the reviewed BG callback protocol.
 * This unit checks observable native retirement, not opaque job/transaction
 * internals. The real Scene owner implementation must prove those barriers.
 * Deactivation precedes every dynamic Exit, including failed Init rollback.
 * No raw dynamic function pointer survives a synchronous checked call.
 */
typedef struct {
 unsigned callbacks[4],exec,proc,args,data,unknown20,unknown24;
} UiBridgeManager;
typedef struct {unsigned manager,generation,role,phase;} UiBridgeControl;
typedef struct {
 UiModule module;
 UiModuleConfig module_config;
 UiResourceConfig resource_config;
 UiGuideConfig guide_config;
 UiSceneContext context;
 unsigned stage,scene_step,fontwork,fontmanager,fontref,fontmode,fontdecoder,fontcache;
 UiHeap scene_heap;
} UiBridge;
unsigned ui_bridge_settings_init(UiBridgeManager *,unsigned *);
unsigned ui_bridge_guide_init(UiBridgeManager *,unsigned *);
unsigned ui_bridge_main(UiBridgeManager *,unsigned *);
unsigned ui_bridge_exit(UiBridgeManager *,unsigned *);
#endif
