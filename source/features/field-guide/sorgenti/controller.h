/* GPL-3.0-or-later. Native Guide navigation, independent of rendering. */
#ifndef GUIDE_CONTROLLER_H
#define GUIDE_CONTROLLER_H
#include "controller_core.h"
static int guide_touch(unsigned x,unsigned y) {
 if(x<16 || x>=240 || y<40 || y>=160) return -1;
 return y<64?0:y<88?1:y<112?2:y<136?3:4;
}
static unsigned guide_footer(unsigned x,unsigned depth,unsigned has_link) {
 if(x<80)return 2;
 if(depth==2)return x<120?32:x<160?16:has_link?1024:0;
 return x<112?64:x<152?128:1;
}
/* Header hitboxes use screen coordinates; the caller checks y < 24. */
static inline unsigned guide_header(unsigned x,unsigned depth,unsigned entries) {
 if(depth!=1 || entries<=5 || x<16 || x>=240)return 0;
 return x<48?512:x>=208?256:0;
}
#endif
