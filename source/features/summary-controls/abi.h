/* GPL-3.0-or-later. ABI of the Summary controls legend for the exact V4 EN/IT
 * candidates. Every native address below is pinned by
 * source/sgp131/data/controls-native-abi.json and re-read from the ROM by
 * sgp131/controls.py; nothing here is inferred at run time.
 *
 * Nothing in this header selects a placement. The assigned base, window
 * rectangle, base tile and the activation flag arrive from the installer as
 * -D definitions (see runtime.c).
 */
#ifndef SGP_SUMMARY_CONTROLS_ABI_H
#define SGP_SUMMARY_CONTROLS_ABI_H

typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef unsigned int u32;

/* Native Thumb entry points (address | 1). Same in EN and IT. */
/* void *Heap_Alloc(heapId, size): NULL on failure, except that pret's AllocFail() resets the console when
 * link communication is active (sub_02037D78()). The legend asks 16 + 1024 bytes of heap 19. */
#define SGP_SC_HEAP_ALLOC 0x0201AA8Du
#define SGP_SC_ADD_WINDOW 0x0201D4F9u     /* void AddWindow(bg, window, template) */
#define SGP_SC_FILL_WINDOW 0x0201D979u    /* void FillWindowPixelBuffer(window, v) */
#define SGP_SC_COPY_WINDOW 0x0201D5C9u    /* void ScheduleWindowCopyToVram(window) */
#define SGP_SC_CLEAR_WINDOW 0x0201D8C9u   /* void ClearWindowTilemapAndCopyToVram(window) */
#define SGP_SC_DELETE_WINDOWS 0x0201D54Du /* void WindowArray_Delete(windows, n) */
#define SGP_SC_PRINT 0x020200FDu          /* AddTextPrinterParameterizedWithColor */
#define SGP_SC_GET_MON 0x0208A521u        /* void *sub_0208A520(summary) */
#define SGP_SC_GET_BOX_DATA 0x0206E641u   /* u32 GetBoxMonData(mon, id, NULL) */

#define SGP_SC_NATIVE_STATS_DRAW 0x0208D179u /* sub_0208D178: still entered through the inherited viewer hook */
#define SGP_SC_NATIVE_TEARDOWN 0x0208C4E1u   /* sub_0208C4E0 */
#define SGP_SC_BG 4u                         /* lower-screen text layer (window bgId) */

#define SGP_SC_SUMMARY_HEAP 19u
#define SGP_SC_FONT 0u
#define SGP_SC_TEXT_SPEED_NOTRANSFER 0xFFu
/* fg 14, shadow 15, background 0: same colours as the native "MOSSE LOTTA" and
 * EV/IV titles on palette 13. */
#define SGP_SC_COLOR 0x000E0F00u
#define SGP_SC_MON_DATA_IS_EGG 76u
#define SGP_SC_STRING_MAGIC 0xB6F8D2ECu

/* Summary object (heap 19, 0x7D8 bytes, zero-filled by PokemonSummary_Init). */
#define SGP_SC_OFF_WINDOWS_PTR 0x224u /* page window array, pinned in sub_0208C42C */
#define SGP_SC_OFF_ARGS 0x22Cu        /* PokemonSummaryArgs * */
#define SGP_SC_OFF_PAGE 0x7BCu        /* s8: 1 = Skills (Statistiche/EV/IV) */
#define SGP_SC_OFF_STATE 0x7BFu       /* high nibble 1 = leaving the screen */
#define SGP_SC_PAGE_SKILLS 1

/* PokemonSummaryArgs */
#define SGP_SC_ARGS_MODE 0x12u        /* 3 and 4 select the learn/forget pages */
#define SGP_SC_ARGS_MOVE_TO_LEARN 0x18u /* u16, 0 = not learning */

/* Window (16 bytes) */
typedef struct SgpWindow {
    void *bgConfig;
    u8 bgId, left, top, width, height, palette;
    u16 baseTile; /* bit 15 = colour mode */
    void *pixelBuffer;
} SgpWindow;

typedef struct SgpWindowTemplate {
    u8 bgId, left, top, width, height, palette;
    u16 baseTile;
} SgpWindowTemplate;

/* Native String as read by the text printer. */
#define SGP_SC_STRING_HEADER_BYTES 8u

/* Resident record at the first bytes of the assigned image. */
#define SGP_SC_STATE_BYTES 0x20u
typedef struct SgpSummaryControlsState {
    u32 owner;      /* Summary object that owns the window, 0 = none */
    u32 generation; /* incremented at every creation */
    u32 window;     /* SgpWindow * on heap 19, 0 = none */
    u32 redraws;    /* diagnostic: draws since creation */
    u32 enabled;    /* written by the installer: 0 = inert (default), 1 = draw */
    u32 reserved[3];
} SgpSummaryControlsState;

#endif
