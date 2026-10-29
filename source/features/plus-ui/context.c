/* Temporary native Window shares only VRAM with the original frame preview.
 * Complete this app's queued preview first; opz_chiudi restores its full buffer.
 * No persistent allocation, settings or save fields. GPL-3.0-or-later. */
#include "../options/sorgenti/sgp_ui.h"
#define LABELS ((const u16 *)0x023D7880u)
__attribute__((used, noinline, section(".text")))
void plus_context(void *app, u32 setting)
{
    Window w;
    Window *source;
    String *s;
    u32 line, i;
    if (!app || setting >= 5u) return;
    source = (Window *)((u8 *)app + 0x34u + 2u * sizeof(Window));
    if (!source->pixels || !source->bgConfig || source->bgId != 5u
        || source->w != 27u || source->h != 4u) return;
    s = String_New(64u, *(u32 *)app);
    if (!s) return;
    w.pixels = 0;
    AddWindowParameterized(source->bgConfig, &w, source->bgId,
        source->x, source->y, source->w, source->h, source->pal, source->baseTile);
    if (w.pixels) {
        u32 id = *((u8 *)app + 0x328u);
        if (id < 8u) {
            void *task = ((void **)0x021D1F74u)[id];
            if (task) {
                void *printer = FN(void *(*)(void *), 0x0201F988u)(task);
                if (printer && ((Window **)printer)[1] == source) {
                    /* Native TRUE path removes only the owned printer and
                     * completes the original caption for the close copy. */
                    FN(void (*)(void *, String *, u32), 0x021E61A8u)(app,
                        *(String **)((u8 *)app + 0x324u), 1u);
                }
            }
        }
        FillWindowPixelBuffer(&w, 0xFFu);
        for (line = 0; line < 2u; line++) {
            const u16 *text = (const u16 *)((const u8 *)LABELS + LABELS[setting * 2u + line]);
            for (i = 0; i < 63u && text[i] != SGP_EOS; i++) s->data[i] = text[i];
            s->data[i] = SGP_EOS;
            s->size = (u16)i;
            AddTextPrinterWithColor(&w, 0u, s, 0u, line * 16u, 0xFFu,
                (1u << 16) | (2u << 8) | 15u, 0);
        }
        CopyWindowToVram(&w);
        RemoveWindow(&w);
    }
    String_Delete(s);
}
