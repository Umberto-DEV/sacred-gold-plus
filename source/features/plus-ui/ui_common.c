/* 1.3 printer shared by the existing Options/Continue controllers.
 * Derived from options/sorgenti/ui_comune.c; GPL-3.0-or-later.
 * Keep one printer body so the native controller stays in its fixed compartment. */
#include "../options/sorgenti/sgp_ui.h"
__attribute__((used,noinline,section(".text")))
static u32 ui_copia(String *s,const u16 *src)
{
    u32 n=0;
    if (!s || !src) return 0;
    while (src[n]!=SGP_EOS && n+1u<s->maxsize) { s->data[n]=src[n]; n++; }
    s->data[n]=SGP_EOS; s->size=(u16)n; return n;
}
__attribute__((used,noinline,section(".text")))
static const u16 *ui_testo(u32 id)
{
    const u16 *t=SGP_TESTI;
    if (id >= T_COUNT) id=T_VUOTO;
    return (const u16 *)((const u8 *)t+t[id]);
}
__attribute__((used,noinline,section(".text")))
static void ui_stampa_m(Window *w,String *s,u32 id,u32 x,u32 y,u32 colore,u32 modo)
{
    u32 px;
    if (id==T_TITOLO) { x=G_W_TILE*8u; modo=2u; colore=(7u<<16)|(8u<<8)|15u; }
    if (id==T_SUGGERIMENTO) {
        FN(void (*)(Window *),0x023D7500u)(w);
        x=112u; y=6u; modo=2u; colore=(15u<<16)|(1u<<8)|7u;
    }
    if (id==T_CURSORE && SGP_UI->aperta && SGP_UI->app && SGP_UI->cursore<SGP_UI->n_vis)
        FN(void (*)(void *,u32),0x023D7700u)(SGP_UI->app,
            V_QUALE(SGP_VOCI[SGP_UI->vis[SGP_UI->cursore]].modo));
    if (!ui_copia(s,ui_testo(id))) return;
    if (modo) {
        px=FontID_String_GetWidth(G_FONT,s,0); if (px>x) px=x;
        x=(modo==1u)?x-px:(x-px)/2u;
    }
    AddTextPrinterWithColor(w,G_FONT,s,x,y,G_ISTANTANEO,colore,0);
}
#define ui_stampa_col(w,s,id,x,y,c) ui_stampa_m((w),(s),(id),(x),(y),(c),0u)
#define ui_stampa(w,s,id,x,y) ui_stampa_m((w),(s),(id),(x),(y),G_COLORE,0u)
#define ui_stampa_destra(w,s,id,x,y,c) ui_stampa_m((w),(s),(id),(x),(y),(c),1u)
#define ui_stampa_centro(w,s,id,lw,y) ui_stampa_m((w),(s),(id),(lw),(y),G_COLORE,2u)
