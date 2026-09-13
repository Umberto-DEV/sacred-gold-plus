/* GPL-3.0-or-later. Small native-font presentation/input component.
 * Requires lease.c types. No SaveData, printer allocation, callbacks or host state.
 */
typedef struct { void *bg; u8 id,x,y,w,h,pal; u16 tile; void *pixels; } GuideWindow;
typedef struct { u8 pixels[128]; u8 width,height; } GuideGlyph;
#define GLYPH ((GuideGlyph *(*)(u32,u16))0x02002E7D)
#define COPY_GLYPH ((void (*)(GuideWindow *,void *,u32,u32,u32,u32,u32))0x0201DACD)
#define COLORS ((void (*)(u32,u32,u32))0x0202036D)
#ifndef GUIDE_TEXT_ADDRESS
#define GUIDE_TEXT_ADDRESS 0x01FF9B00
#endif
#define TEXT ((const u16 *)GUIDE_TEXT_ADDRESS)
#define SYS ((volatile u8 *)0x021D110C)

#ifndef GUIDE_COPY_DECL
#define GUIDE_COPY_DECL __attribute__((always_inline)) static inline
#endif
GUIDE_COPY_DECL void copy16(void *destination, const void *source, u32 bytes)
{
    volatile u16 *d=destination; const volatile u16 *s=source;
    for (u32 i=0;i<bytes/2;i++) d[i]=s[i];
}

static void fill32(void *destination,u32 value,u32 bytes)
{
    u32 *d=destination;
    for (u32 i=0;i<bytes/4;i++) d[i]=value;
}

/* IDs: three title/body triples (0..11), L=A body (12..14),
 * open/back/next/done/close/reopen (15..20), counters (21..23).
 * Builder only emits plain, individually bounded glyph lines, no controls. */
static void guide_line(GuideWindow *w,u32 id,u32 x,u32 y)
{
    const u16 *text=(const u16 *)((const u8 *)TEXT+TEXT[id]);
    while (*text!=0xFFFF) {
        GuideGlyph *g=GLYPH(0,*text++);
        COPY_GLYPH(w,g->pixels,g->width,g->height,x,y,0);
        x+=g->width;
    }
}

static void border(GuideWindow *w,u32 color)
{
    u8 *p=w->pixels;
    for (u32 y=0;y<w->h*8u;y++) for (u32 x=0;x<w->w*8u;x++) {
        if (y && y!=w->h*8u-1 && x && x!=w->w*8u-1) continue;
        u32 off=((y/8)*w->w+x/8)*32+(y&7)*4+(x&7)/2;
        u32 shift=(x&1)*4;
        p[off]=(p[off]&~(15u<<shift))|(color<<shift);
    }
}

static int in_rect(u32 x,u32 y,u32 w,u32 h)
{
    u32 tx=*(volatile u16 *)(SYS+0x60),ty=*(volatile u16 *)(SYS+0x62);
    return tx>=x && tx<x+w && ty>=y && ty<y+h;
}

__attribute__((unused)) static int released(void)
{
    return !*(volatile u32 *)(SYS+0x38) && !*(volatile u16 *)(SYS+0x66);
}

/* Physical keys are deliberately local: respects START=X without changing
 * player options/global input, and avoids L=A unexpectedly advancing a panel. */
__attribute__((unused)) static int guide_event(void)
{
    u32 key=*(volatile u32 *)(SYS+0x3c);
    u32 touch=*(volatile u16 *)(SYS+0x64);
    if ((key&2) || (touch && in_rect(176,160,64,16))) return 3;
    if ((key&32) || (touch && in_rect(16,160,72,16))) return 1;
    if ((key&17) || (touch && in_rect(96,160,64,16))) return 2;
    return 0;
}
