/* Recoverable touch-save refusal; state stays local to the native app. */
typedef unsigned int u32;
typedef unsigned short u16;
typedef unsigned char u8;
#define U32(p, n) (*(u32 *)((u8 *)(p) + (n)))
#define PTR(p, n) (*(void **)((u8 *)(p) + (n)))
#define CALL(a, t) ((t)((a) | 1u))
#define ENTRY __attribute__((used))

ENTRY int sgp_saveui_save(void *data) {
    int result = CALL(0x021F43E8, int (*)(void *))(PTR(data, 0x1C));
    U32(data, 0x0C) = result ? 13 : 16;
    return 0;
}

ENTRY int sgp_saveui_failure(void *data) {
    CALL(0x021F2FF0, void (*)(void *))(PTR(data, 0x68));
    PTR(data, 0x68) = (void *)0;
    CALL(0x0200F450, void (*)(void *))(PTR(data, 0x64));
    PTR(data, 0x64) = (void *)0;
    CALL(0x0201D978, void (*)(void *, u32))((u8 *)data + 0x4C, 255);
    PTR(data, 0x5C) = CALL(0x0200BBA0, void *(*)(void *, u32))(PTR(data, 0x38), 117);
    U32(data, 0x60) = CALL(0x020200A8, u32 (*)(void *, u32, void *, u32, u32, u32, void *))(
        (u8 *)data + 0x4C, 1, PTR(data, 0x5C), 0, 0,
        CALL(0x0202AD3C, u32 (*)(void *))(PTR(data, 0x44)), (void *)0);
    U32(data, 0x14) = 0;
    U32(data, 0x10) = 17;
    U32(data, 0x0C) = 2;
    return 0;
}

ENTRY int sgp_saveui_ack(void *data) {
    volatile u8 *system = (volatile u8 *)0x021D110C;
    u32 held = (*(volatile u32 *)(system + 0x44) & 3u) |
               *(volatile u16 *)(system + 0x66);
    u32 phase = U32(data, 0x14);
    if (phase == 0) {
        if (!held) U32(data, 0x14) = 1;
    } else if (phase == 1) {
        if ((*(volatile u32 *)(system + 0x48) & 3u) |
            *(volatile u16 *)(system + 0x64)) U32(data, 0x14) = 2;
    } else if (phase == 2 && !held) {
        return 1;
    }
    return 0;
}
