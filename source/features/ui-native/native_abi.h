#ifndef SGP_UI_NATIVE_ABI_H
#define SGP_UI_NATIVE_ABI_H
/* ARM32 native layouts only. No product placement or native service bindings. */
typedef struct {
    void *map;
    unsigned size, baseTile;
    int hOffset, vOffset;
    unsigned char mode, screenSize, colorMode, tileSize;
    unsigned short rotation, padding;
    int xScale, yScale, centerX, centerY;
} UiNativeBackground44;
typedef struct {
    unsigned heapID;
    unsigned short scrollScheduled, transferScheduled;
    UiNativeBackground44 bgs[8];
} UiNativeBgConfig360;
typedef struct {
    UiNativeBgConfig360 *bg;
    unsigned char bgId, x, y, width, height, palette;
    unsigned short baseTile;
    void *pixels;
} UiNativeWindow16;
typedef struct {
    unsigned x, y, bufferSize, baseTile;
    unsigned char size, colorMode, screenBase, charBase;
    unsigned char bgExtPltt, priority, areaOver, dummy;
    unsigned mosaic;
} UiNativeBgTemplate28;
#define UI_ABI_OFFSET(t,f,n) _Static_assert(__builtin_offsetof(t,f)==(n), #t "." #f)
_Static_assert(sizeof(void *)==4 && sizeof(unsigned)==4, "ARM32 ABI required");
_Static_assert(__alignof__(UiNativeBackground44)==4 && __alignof__(UiNativeBgConfig360)==4 &&
               __alignof__(UiNativeWindow16)==4 && __alignof__(UiNativeBgTemplate28)==4, "ARM32 alignment");
_Static_assert(sizeof(UiNativeBackground44)==44, "Background44");
_Static_assert(sizeof(UiNativeBgConfig360)==360, "BgConfig360");
_Static_assert(sizeof(UiNativeWindow16)==16, "Window16");
_Static_assert(sizeof(UiNativeBgTemplate28)==28, "BgTemplate28");
UI_ABI_OFFSET(UiNativeBgConfig360,bgs,8);
UI_ABI_OFFSET(UiNativeBackground44,mode,20);
UI_ABI_OFFSET(UiNativeBackground44,rotation,24);
UI_ABI_OFFSET(UiNativeBackground44,xScale,28);
UI_ABI_OFFSET(UiNativeWindow16,bgId,4);
UI_ABI_OFFSET(UiNativeWindow16,baseTile,10);
UI_ABI_OFFSET(UiNativeWindow16,pixels,12);
UI_ABI_OFFSET(UiNativeBgTemplate28,size,16);
UI_ABI_OFFSET(UiNativeBgTemplate28,mosaic,24);
#undef UI_ABI_OFFSET
#endif
