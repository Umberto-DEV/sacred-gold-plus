#ifndef SGP_UI_SCENE_ADMISSION_H
#define SGP_UI_SCENE_ADMISSION_H
#include "bridge.h"
typedef enum { SCENE_ADMIT_WAIT,SCENE_ADMIT_REFUSE,SCENE_ADMIT_READY } SceneAdmission;
enum { SCENE_ADMIT_E_NONE,SCENE_ADMIT_E_OUTPUT,SCENE_ADMIT_E_CONTEXT,
 SCENE_ADMIT_E_EXECUTION,SCENE_ADMIT_E_FIELD,SCENE_ADMIT_E_ARGS,
 SCENE_ADMIT_E_FONT,SCENE_ADMIT_E_CALLBACK,SCENE_ADMIT_E_PRINTER,
 SCENE_ADMIT_E_DMA,SCENE_ADMIT_E_DISPLAY,SCENE_ADMIT_E_FADE,
 SCENE_ADMIT_E_BRIGHTNESS };
/* Pre-acquisition, read-only admission; compose after heap/resource/font/bg.c.
 * Bridge authenticates its resident USC2 context before and after this call.
 * Borrowed native child/Field/SaveData/Options/input and boot font stay live.
 * reason is a fresh aligned unsigned in the CURRENT live SYS caller frame;
 * invalid output refuses without any write. No app/prefix is required yet.
 * WAIT only defers an otherwise permitted IRQ/IME execution boundary. Unknown
 * active native producers REFUSE: no flag can manufacture their retirement.
 * READY means these finite observations pass, CONDITIONAL on the installer's
 * supported entry paths and runtime evidence excluding future foreign task,
 * FS/CARD, printer, OAM/VRAM/DMA, 3D and font writers throughout Scene ownership.
 * Empty slots/registers alone cannot establish that lifetime contract.
 * This routine neither establishes that contract nor allocates or retires any
 * owner. The reason output is its sole write outside its own live stack.
 */
SceneAdmission ui_scene_admit(const UiSceneContext *,unsigned *reason);
#endif
