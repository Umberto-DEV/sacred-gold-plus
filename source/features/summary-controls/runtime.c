/* GPL-3.0-or-later. Native legend "L:EV SELECT:Stat. R:IV" on the Summary skills page.
 *
 * The installed EV/IV viewer is not touched: L, R and SELECT keep being read by
 * its own raw-key reader (it survives L=A). This runtime draws one extra Window,
 * owned by the Summary object, and never reads the keys.
 *
 *   sgp_summary_controls_update(summary)   called before every native skills-page
 *                                          draw (sub_0208D178): create / redraw /
 *                                          remove according to the view
 *   sgp_summary_controls_destroy(summary)  called before the page windows are
 *                                          torn down (sub_0208C4E0): page change
 *                                          and Summary exit
 *
 * Placement (base, rectangle, base tile) and the activation flag come from the
 * installer as definitions in "sgp_sc_config.h"; nothing here is a reserve
 * assignment. The record at SGP_SC_BASE is the only resident state.
 */
#include "abi.h"
#include "sgp_sc_config.h"

#define STATE ((volatile SgpSummaryControlsState *)SGP_SC_BASE)

/* The legend String lives in the one .text section (the loader accepts no other
 * allocated section): native header (maxsize, size, magic) then the charmap codes. */
#define SGP_STR(x) #x
#define SGP_XSTR(x) SGP_STR(x)
__asm__(".text\n.balign 4\nsgp_sc_legend:\n"
        ".hword " SGP_XSTR(SGP_SC_TEXT_COUNT) ", " SGP_XSTR(SGP_SC_TEXT_COUNT) "\n"
        ".word 0xB6F8D2EC\n"
        ".hword " SGP_SC_TEXT_ASM "\n"
        ".balign 4\n");
extern const u8 sgp_sc_legend[];

typedef void *(*HeapAllocFn)(u32, u32);
typedef void (*AddWindowFn)(void *, SgpWindow *, const SgpWindowTemplate *);
typedef void (*FillWindowFn)(SgpWindow *, u32);
typedef void (*WindowFn)(SgpWindow *);
typedef void (*DeleteWindowsFn)(void *, int);
typedef u32 (*PrintFn)(SgpWindow *, u32, const void *, u32, u32, u32, u32, void *);
typedef void *(*GetMonFn)(void *);
typedef u32 (*GetBoxDataFn)(void *, u32, void *);
typedef void (*SummaryFn)(void *);

#define HeapAlloc ((HeapAllocFn)SGP_SC_HEAP_ALLOC)
#define AddWindow ((AddWindowFn)SGP_SC_ADD_WINDOW)
#define FillWindow ((FillWindowFn)SGP_SC_FILL_WINDOW)
#define CopyWindow ((WindowFn)SGP_SC_COPY_WINDOW)
#define ClearWindow ((WindowFn)SGP_SC_CLEAR_WINDOW)
#define DeleteWindows ((DeleteWindowsFn)SGP_SC_DELETE_WINDOWS)
#define Print ((PrintFn)SGP_SC_PRINT)
#define GetMon ((GetMonFn)SGP_SC_GET_MON)
#define GetBoxData ((GetBoxDataFn)SGP_SC_GET_BOX_DATA)

/* The view the installed reader serves: Skills page, not leaving, a real Pokemon
 * that is not an egg. The legend is stricter: never while learning a move. */
static int supported(u8 *summary)
{
    if (*(s8 *)(summary + SGP_SC_OFF_PAGE) != SGP_SC_PAGE_SKILLS || (summary[SGP_SC_OFF_STATE] >> 4) == 1)
        return 0;
    u8 *args = *(u8 **)(summary + SGP_SC_OFF_ARGS);
    if (!args || args[SGP_SC_ARGS_MODE] == 3 || args[SGP_SC_ARGS_MODE] == 4
            || *(u16 *)(args + SGP_SC_ARGS_MOVE_TO_LEARN))
        return 0;
    void *mon = GetMon(summary);
    return mon && !GetBoxData(mon, SGP_SC_MON_DATA_IS_EGG, (void *)0);
}

static void release(u8 *summary)
{
    /* Only the Summary that created the window may free it: a record left by an
     * earlier instance points into a heap that no longer exists. */
    if ((u32)summary != STATE->owner || !STATE->window)
        return;
    SgpWindow *window = (SgpWindow *)STATE->window;
    ClearWindow(window);
    DeleteWindows(window, 1);
    STATE->owner = 0;
    STATE->window = 0;
}

__attribute__((used, noinline))
void sgp_summary_controls_destroy(void *summary)
{
    release((u8 *)summary);
}

__attribute__((used, noinline))
void sgp_summary_controls_update(void *object)
{
    u8 *summary = (u8 *)object;
    if (!summary || !STATE->enabled)
        return;
    if (STATE->owner && STATE->owner != (u32)summary) {
        STATE->owner = 0; /* stale record of a destroyed Summary: forget, never free */
        STATE->window = 0;
    }
    if (!supported(summary)) {
        release(summary);
        return;
    }
    if (!STATE->window) {
        /* Not AllocWindows: it dereferences the result without a NULL check. */
        SgpWindow *created = (SgpWindow *)HeapAlloc(SGP_SC_SUMMARY_HEAP, sizeof(SgpWindow));
        if (!created)
            return;
        created->bgConfig = (void *)0; /* what InitWindow leaves: unallocated layer, no buffer */
        created->bgId = 0xFF;
        created->left = created->top = created->width = created->height = created->palette = 0;
        created->baseTile = 0;
        created->pixelBuffer = (void *)0;
        SgpWindowTemplate layout = {SGP_SC_BG, SGP_SC_LEFT, SGP_SC_TOP, SGP_SC_WIDTH, SGP_SC_HEIGHT,
                                    SGP_SC_PALETTE, SGP_SC_BASE_TILE};
        AddWindow(*(void **)summary, created, &layout);
        if (!created->pixelBuffer) { /* pixel buffer or layer unavailable: nothing was built */
            DeleteWindows(created, 1);
            return;
        }
        STATE->window = (u32)created;
        STATE->owner = (u32)summary;
        STATE->generation++;
        STATE->redraws = 0;
    }
    SgpWindow *window = (SgpWindow *)STATE->window;
    FillWindow(window, 0);
    Print(window, SGP_SC_FONT, sgp_sc_legend, 0, 0, SGP_SC_TEXT_SPEED_NOTRANSFER, SGP_SC_COLOR, (void *)0);
    CopyWindow(window);
    STATE->redraws++;
}

/* Redirected call sites. Both keep the native callee, argument and return. */
__attribute__((used, noinline))
void sgp_sc_redraw(void *summary)
{
    sgp_summary_controls_update(summary);
    ((SummaryFn)SGP_SC_NATIVE_STATS_DRAW)(summary);
}

__attribute__((used, noinline))
void sgp_sc_teardown(void *summary)
{
    sgp_summary_controls_destroy(summary);
    ((SummaryFn)SGP_SC_NATIVE_TEARDOWN)(summary);
}
