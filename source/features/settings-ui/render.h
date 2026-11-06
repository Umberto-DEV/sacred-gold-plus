#ifndef SGP_SETTINGS_RENDER_H
#define SGP_SETTINGS_RENDER_H
#include "controller.h"
#include "catalog.h"
/* Pure main-loop planner. No allocation, owner calls, MMIO or native printer.
 * All extents must be live caller-owned RAM. Catalogue root/directory/advances
 * are immutable borrowed views under an external resource lease; the directory
 * is the validated strictly increasing UIR1 (u16 id, u16 units, u32 offset)
 * table. Offset is relative to root; only referenced strings are remeasured.
 * identity is
 * caller-assigned and changes on language/catalogue/font replacement; bounds
 * and identity do not establish ownership. No concurrent writer is permitted.
 * Pool is a separate aligned4 4..4096-byte allocation. Retire ALL printer jobs
 * borrowing it before build, then publish it as UI_TEXT_BUFFER with pool_epoch.
 * Never mutate UIR1 or fabricate SGG1. Refusal leaves every output unchanged.
 * Output/pool must be disjoint from all inputs and each other. */
typedef struct {
 const void *root; unsigned bytes, directory, count;
 const unsigned char *widths; unsigned width_count, identity;
} SettingsRenderCatalog;
#define SETTINGS_RENDER_OPS 48u
#define SETTINGS_RENDER_FULL 0x003fffffu
#define SETTINGS_RENDER_MAGIC 0x31505253u
enum SettingsDrawKind { SETTINGS_DRAW_TEXT=1, SETTINGS_DRAW_NUMBER,
 SETTINGS_DRAW_BAND, SETTINGS_DRAW_LEFT, SETTINGS_DRAW_RIGHT,
 SETTINGS_DRAW_CHOICE, SETTINGS_DRAW_ACTION, SETTINGS_DRAW_LOCK,
 SETTINGS_DRAW_PREVIEW, SETTINGS_DRAW_FRAME, SETTINGS_DRAW_FOOTER };
enum SettingsDrawFlags { SETTINGS_DRAW_SELECTED=1, SETTINGS_DRAW_CHOSEN=2,
 SETTINGS_DRAW_DISABLED=4, SETTINGS_DRAW_READONLY=8,
 SETTINGS_DRAW_SELECTOR=16, SETTINGS_DRAW_HEADING=32,
 SETTINGS_DRAW_PENDING=64, SETTINGS_DRAW_PREFIX=128 };
/* TEXT id uses catalogue; NUMBER uses immutable a[/b] and pool offset/units.
 * PREFIX uses PREVIEW_TEXT id, a=prefix glyph units and an EOS-terminated pool
 * slice. x/y/w/h include the complete affected geometry, including band/mark.
 * CHOICE is a geometric chosen-value mark; ACTION/LOCK distinguish shapes.
 * SELECTOR means the displayed current value has an A-operated chooser, as
 * stated by the persistent A Choose footer. It never implies Apply.
 * Frame is ONLY the Info preview. choice is frame asset0..19 or choice index.
 * FOOTER: a=authored layout, b=run count, units=total EOS slice units.
 * row is stable SettingsRow, search row0..5, or255 for non-row content. */
typedef struct {
 unsigned a,b; unsigned short id,offset,units,flags;
 unsigned char x,y,w,h,kind,row,choice,reserved;
} SettingsDrawOp;
typedef struct {
 unsigned magic,identity,pool_epoch,pool_used,view,first,count,frame;
 SettingsDrawOp ops[SETTINGS_RENDER_OPS];
} SettingsRenderPlan;
typedef struct {
 const SettingsState *state; const SettingsRenderCatalog *catalog;
 SettingsRenderPlan *out; unsigned out_bytes;
 void *pool; unsigned pool_bytes,pool_epoch;
 unsigned first,selector_first,preview_units;
} SettingsRenderRequest;
/* first is a flattened item offset including headings, adjusted only enough
 * to keep the current stable row visible; caller retains returned first.
 * first/selector_first must be <=17/20, respectively (stale legal scroll
 * positions are clamped after mode changes). preview_units is glyph-prefix
 * length; 0 shows no text, UINT_MAX shows complete preview. */
unsigned settings_render_build(const SettingsRenderRequest *);
typedef struct {
 const SettingsRenderCatalog *catalog; void *pool;
 unsigned pool_bytes,pool_epoch,a,b,fraction;
} SettingsFormatRequest;
/* Exact unsigned32 decimal or a/b, EOS included in returned units; zero refuses.
 * Same immutable catalogue / retired pool contract as build; no other output.
 * FORMAT_POOL is trusted authored identity: first ten encoded words are 0..9,
 * then slash, colon, percent and space. No Unicode parsing/runtime glyph table. */
unsigned settings_render_format(const SettingsFormatRequest *);
/* Compare against EACH buffer's own last COMPLETED immutable plan. previous=0
 * or invalid_rows=FULL means unknown/partial history. A partial paint MUST pass
 * the union of all rows it touched (or FULL), even when cancelled. Never record
 * a desired plan as complete until all paint/transfer work retires. full output
 * is set for unknown history or changed frame geometry. Returns 22 tile rows.
 * Pool offsets/epochs are ignored; IDs/numeric operands are semantic identity. */
unsigned settings_render_dirty(const SettingsRenderPlan *previous,
 const SettingsRenderPlan *desired,unsigned invalid_rows,unsigned *full);
_Static_assert(sizeof(SettingsRenderPlan)<=2048,"bounded settings-only plan");
#endif
