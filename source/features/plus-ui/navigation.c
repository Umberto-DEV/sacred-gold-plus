/* Native Options Plus button. No allocations, save fields or input synthesis.
 * GPL-3.0-or-later. */
#include "../options/sorgenti/sgp_ui.h"
#define API __attribute__((used,noinline,section(".text")))
API void plus_button(Window *w)
{
    /* The caller already owns a 112x24 4bpp Window. Its first four pixel rows
     * stay transparent, matching the native footer controls at y172. */
    for (u32 y=4; y<23; y++) for (u32 x=4; x<112; x++) {
        u32 c=7;
        if (x==4 || x==111 || y==4 || y==22) c=1;
        else if (x==5 || y==5) c=8;
        u32 off=((y>>3)*14+(x>>3))*32+(y&7)*4+((x&7)>>1);
        u8 *pixels=w->pixels, v=pixels[off];
        pixels[off]=(x&1)?((v&15)|(c<<4)):((v&240)|c);
    }
}
API u32 plus_navigation(void *app)
{
    if (!SGP_UI->aperta && K_TOUCH_NEW && K_TOUCH_X>=4u && K_TOUCH_X<112u
        && K_TOUCH_Y>=172u && K_TOUCH_Y<192u)
        return FN(u32 (*)(void *),SGP_OPZ_APRI)(app);
    return FN(u32 (*)(void *),SGP_FRAME)(app);
}
/* Same native HandleInput register/stack contract as the existing Plus hook. */
__attribute__((naked,used,section(".text")))
void plus_navigation_hook(void)
{
    __asm__ volatile(
        "adds r4,r0,#0\n"
        "push {r0,r1,r2,lr}\n"
        "bl plus_navigation\n"
        "cmp r0,#0\n"
        "bne 1f\n"
        "pop {r0,r1,r2,r3}\n"
        "ldrh r1,[r1,#0x24]\n"
        "bx r3\n"
        "1:\n"
        "add sp,#16\n"
        "pop {r3,r4,r5,pc}\n");
}
