/* Party prompt suffix, physical R and touch for the portable box (included by runtime.c).
 *
 * The native prompt "Choose a Pokemon." (message 29, window 32, font 1, 160x16 at
 * (16,168) of the lower screen) is left untouched. After the native print the hook
 * adds the visible command "R: Box" at local x 112 with the same font, so the prompt
 * (97/98 px) and the suffix (33 px, ends at 145) fit with a 14-15 px gap and 15 px of
 * margin; Cancel starts at x 200 on the screen. The suffix is drawn only when the
 * message is 29 on window 32 and eligibility says ELIGIBLE; every other native
 * message overwrites the whole window, which hides it.
 * Touch hitbox: [124,172) x [168,184); no native party rectangle intersects it.
 */
#define N_PRINT_EX 0x0207DA65u
#define N_ADD_PRINTER 0x020200A9u
#define N_COPY_VRAM 0x0201D5C9u

#define PARTY_WINDOW32 0x204u
#define MSG_CHOOSE_POKEMON 29u
#define FONT_ID 1u
#define SUFFIX_X 112u
#define TEXT_SPEED_NOTRANSFER 0xFFu

#define SYS_BASE 0x021D110Cu /* gSystem */
#define SYS_HELD_RAW 0x38u
#define SYS_NEW_RAW 0x3Cu
#define SYS_NEW 0x48u
#define SYS_TOUCH_X 0x60u
#define SYS_TOUCH_Y 0x62u
#define SYS_TOUCH_NEW 0x64u
#define SYS_TOUCH_HELD 0x66u

#define KEY_A 0x001u
#define KEY_B 0x002u
#define KEY_SELECT 0x004u
#define KEY_START 0x008u
#define KEY_DIRECTIONS 0x0F0u
#define KEY_R 0x100u
#define KEY_L 0x200u
#define KEY_RESET_CHORD (KEY_START | KEY_SELECT | KEY_L | KEY_R)
#define HIT_X0 124u
#define HIT_X1 172u
#define HIT_Y0 168u
#define HIT_Y1 184u

/* A native String object: maxsize, size, magic, "R: Box", EOS (charmap codes). */
__asm__(".pushsection .text,\"ax\",%progbits\n.balign 4\n"
        ".local sgp_box_label\n.type sgp_box_label,%object\n"
        "sgp_box_label:\n.hword 6,6\n.word 0xB6F8D2EC\n"
        ".hword 0x013C,0x01C4,0x01DE,0x012C,0x0153,0x015C,0xFFFF,0\n"
        ".size sgp_box_label,24\n.popsection\n");
extern u8 sgp_box_label[24];

/* One new press of R, or one new touch in the box, and nothing native wants the frame. */
static int sgp_box_input_request(void)
{
    u32 held = rd32(SYS_BASE + SYS_HELD_RAW);
    u32 pressed_raw = rd32(SYS_BASE + SYS_NEW_RAW);
    u32 pressed = rd32(SYS_BASE + SYS_NEW); /* after the L=A mapping */
    u32 x, y;
    if (!S->prompt_shown)
        return 0;
    if ((held & KEY_RESET_CHORD) == KEY_RESET_CHORD)
        return 0;
    if (pressed & (KEY_A | KEY_B | KEY_DIRECTIONS))
        return 0; /* native selection and cancel always win */
    if (rd16(SYS_BASE + SYS_TOUCH_NEW)) {
        x = rd16(SYS_BASE + SYS_TOUCH_X);
        y = rd16(SYS_BASE + SYS_TOUCH_Y);
        return x >= HIT_X0 && x < HIT_X1 && y >= HIT_Y0 && y < HIT_Y1; /* elsewhere: native touch */
    }
    if (rd16(SYS_BASE + SYS_TOUCH_HELD))
        return 0; /* a touch that began earlier owns the frame */
    return (pressed_raw & KEY_R) != 0; /* raw: visible even when L=A hides R from the mapped words */
}

void sgp_box_prompt(void *party_, int reason)
{
    u32 window = (u32)party_ + PARTY_WINDOW32;
    if (reason != SGP_BOX_ELIGIBLE)
        return;
    ((void (*)(u32, u32, u32, u32, u32, u32, u32))N_ADD_PRINTER)(window, FONT_ID, (u32)sgp_box_label, SUFFIX_X, 0,
                                                                  TEXT_SPEED_NOTRANSFER, 0);
    ((void (*)(u32))N_COPY_VRAM)(window);
    S->prompt_shown = 1;
}

static int prompt_reason(u32 party)
{
    if (!ensure_bound(rd32(party + PARTY_ARGS)))
        return SGP_BOX_WRONG_OWNER;
    return sgp_box_eligibility((void *)S->field, (void *)S->owner);
}

void sgp_box_prompt_print(void *party, void *window, int msg, int frame)
{
    ((void (*)(void *, void *, int, int))N_PRINT_EX)(party, window, msg, frame);
    S->prompt_shown = 0; /* the native print rewrote the whole window */
    if ((u32)msg == MSG_CHOOSE_POKEMON && CFG->prompt && CFG->bridge && CFG->input && (u32)window == (u32)party + PARTY_WINDOW32)
        sgp_box_prompt(party, prompt_reason((u32)party));
}
