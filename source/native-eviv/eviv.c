/* GPL-3.0-or-later. Original bounded viewer for the identified HG/Plus ABI.
 * ABI cross-checked against pret assembly and hg-engine rom.ld; no game code
 * or external engine implementation is embedded in this payload.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned short u16;

#define CALL(address, type) ((type)(address))
#define FillWindow CALL(0x0201D979, void (*)(void *, u8))
#define CopyWindow CALL(0x0201D5C9, void (*)(void *))
#define GetMon CALL(0x0208A521, void *(*)(void *))
#define BoxData CALL(0x0206E641, u32 (*)(void *, int, void *))
#define Number CALL(0x0208C87D, void (*)(void *, u32, u32, u8, u8))
#define Print CALL(0x0208C779, void (*)(void *, void *, u32, u32))
#define Label CALL(0x0208C851, void (*)(void *, u32, u32, u32, u32))
#define Width CALL(0x0201EE91, u8 (*)(void *))
#define Ratio CALL(0x0208C8C9, void (*)(void *, u32, u32, u32, u32, u16, u16, u8, u8, u8))

__attribute__((used, noinline, section(".text")))
void reset_header(u8 *summary)
{
    void *header = summary + 4 + 2 * 16;
    FillWindow(header, 0);
    Label(summary, 2, 109, 0x000E0F00, 0);
    CopyWindow(header);
}

__attribute__((used, noinline, section(".text")))
int show_eviv(u8 *summary)
{
    u32 keys = *(volatile u32 *)0x021D1154; /* gSystem.newKeys */
    u32 repeated = *(volatile u32 *)0x021D1158; /* original directional input */
    if (!(keys & 0x304) || (keys & 3) || (repeated & 0xF0) || summary[0x7BC] != 1
            || (summary[0x7BF] >> 4) == 1)
        return 0;

    int normal = (keys & 4) != 0;
    void *mon = (void *)0;
    if (!normal) {
        mon = GetMon(summary);
        if (!mon || BoxData(mon, 76, (void *)0)) /* eggs have no skills page */
            return 0;
    }
    int ev = (keys & 0x200) != 0;
    u8 *windows = *(u8 **)(summary + 0x224);
    for (int row = 0; row < 6; row++) {
        /* Display order HP/Atk/Def/SpA/SpD/Spe; storage puts Spe fourth. */
        int stat = row;
        if (row == 3 || row == 4) stat = row + 1;
        if (row == 5) stat = 3;
        void *window = windows + row * 16;
        FillWindow(window, 0);
        if (normal && row == 0) {
            /* Use the game's cached display values, also valid for boxed mons.
             * Match the original HP current/max formatting and centering.
             */
            Ratio(summary, 0, 117, 119, 118, *(u16 *)(summary + 0x254),
                  *(u16 *)(summary + 0x256), 3, Width(window) * 4, 0);
        } else {
            u32 value = normal ? *(u16 *)(summary + 0x256 + row * 2)
                              : BoxData(mon, (ev ? 13 : 70) + stat, (void *)0);
            Number(summary, 119, value, 3, 0);
            Print(summary, window, 0x00010200, row ? 1 : 2);
        }
        CopyWindow(window);
    }
    void *header = summary + 4 + 2 * 16;
    FillWindow(header, 0);
    Label(summary, 2, normal ? 109 : ev ? EV_MSG_ID : IV_MSG_ID, 0x000E0F00, 0);
    CopyWindow(header);
    return 1;
}

/* Every normal redraw (page, Pokemon or Select) restores the matching title.
 * This also covers touch navigation, independently of the input hook.
 */
__attribute__((naked, used, section(".text")))
void stats_hook(void)
{
    __asm__ volatile(
        "push {r0-r3, lr}\n"
        "sub sp, #4\n"
        "bl reset_header\n"
        "add sp, #4\n"
        "pop {r0-r3}\n"
        "pop {r3}\n"
        "mov lr, r3\n"
        "push {r3-r5, lr}\n"
        "sub sp, #24\n"
        "movs r3, #0\n"
        "movs r1, #16\n"
        "ldr r2, 1f\n"
        "bx r2\n"
        ".balign 4\n"
        "1: .word 0x0208D181\n"
    );
}

/* Keep the original function prologue and input flow when no new key applies.
 * The public hook replaces exactly eight bytes at 02088B40. Stack remains
 * eight-byte aligned at the C call; the untouched function resumes at +8.
 */
__attribute__((naked, used, section(".text")))
void eviv_hook(void)
{
    __asm__ volatile(
        "push {r0-r3, lr}\n"
        "sub sp, #4\n"
        "bl show_eviv\n"
        "cmp r0, #0\n"
        "beq 1f\n"
        "add sp, #4\n"
        "pop {r0-r3}\n"
        "pop {r3}\n"
        "movs r0, #2\n"
        "bx r3\n"
        "1:\n"
        "add sp, #4\n"
        "pop {r0-r3}\n"
        "pop {r3}\n"
        "mov lr, r3\n"
        "push {r4-r6, lr}\n"
        "ldr r2, 2f\n"
        "movs r5, r0\n"
        "ldrb r1, [r5, r2]\n"
        "ldr r3, 3f\n"
        "bx r3\n"
        ".balign 4\n"
        "2: .word 0x000007BF\n"
        "3: .word 0x02088B49\n"
    );
}
