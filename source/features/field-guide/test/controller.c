#include <assert.h>
#if __has_include("../sorgenti/controller.h")
#include "../sorgenti/controller.h"
#else
int main(void) { assert(!"Guide controller missing"); }
#endif
#ifdef GUIDE_CONTROLLER_H
int main(void) {
 GuideCursor c={0};
 assert(guide_step(&c,1,3,12,2)==1 && c.depth==1);
 for(int i=0;i<8;i++) guide_step(&c,128,3,12,2);
 assert(c.row==8 && c.scroll==4);
 guide_step(&c,1,3,12,2); assert(c.depth==2 && c.page==0);
 guide_step(&c,16,3,12,2); assert(c.page==1);
 guide_step(&c,16,3,12,2); assert(c.page==1);
 guide_step(&c,2,3,12,2); assert(c.depth==1 && c.row==8 && c.scroll==4);
 guide_step(&c,2,3,12,2); assert(c.depth==0);
 assert(guide_step(&c,2,3,12,2)==2);
 assert(guide_touch(16,40)==0 && guide_touch(239,159)==4);
 assert(guide_touch(240,40)==-1 && guide_touch(16,160)==-1);
 GuideCursor full={1,0,0,0,0};
 for(int i=0;i<500;i++)guide_step(&full,128,3,229,1);
 assert(full.row==228 && full.scroll==224);
 assert(guide_step(&full,128,3,229,1)==0);
 guide_step(&full,1,3,229,1);guide_step(&full,2,3,229,1);
 assert(full.row==228 && full.scroll==224);
 assert(guide_footer(20,0,0)==2);
 assert(guide_footer(100,0,0)==64);
 assert(guide_footer(132,1,0)==128);
 assert(guide_footer(180,1,0)==1);
 assert(guide_footer(100,2,1)==32);
 assert(guide_footer(132,2,1)==16);
 assert(guide_footer(180,2,1)==1024);
 assert(guide_footer(180,2,0)==0); /* No invisible next-page control. */
 GuideCursor training={0};
 for(int i=0;i<4;i++)guide_step(&training,128,4,6,1);
 assert(training.category==3);
 guide_step(&training,1,4,6,1);
 assert(training.depth==1 && training.category==3 && training.row==0);
 GuideCursor jump={1,0,0,0,0};
 assert(guide_step(&jump,16,4,229,3)==1 && jump.row==5 && jump.scroll==5);
 jump.row=8;jump.scroll=4;
 assert(guide_step(&jump,256,4,229,3)==1 && jump.row==13 && jump.scroll==9);
 assert(guide_step(&jump,512,4,229,3)==1 && jump.row==8 && jump.scroll==4);
 jump.row=223;jump.scroll=219;
 assert(guide_step(&jump,256,4,229,3)==1 && jump.row==228 && jump.scroll==224);
 assert(guide_step(&jump,256,4,229,3)==0 && jump.row==228 && jump.scroll==224);
 assert(guide_step(&jump,512,4,229,3)==1 && jump.row==223 && jump.scroll==219);
 jump.row=3;jump.scroll=2;
 assert(guide_step(&jump,32,4,229,3)==1 && jump.row==0 && jump.scroll==0);
 jump=(GuideCursor){1,0,0,0,0};
 assert(guide_step(&jump,16|256,4,6,3)==1 && jump.row==5 && jump.scroll==1);
 for(unsigned count=0;count<=5;count++) {
  jump=(GuideCursor){1,0,0,0,0};
  assert(guide_step(&jump,16|256,4,count,3)==0 && jump.row==0 && jump.scroll==0);
 }
 jump=(GuideCursor){0,1,0,0,0};
 assert(guide_step(&jump,256,4,229,3)==0 && jump.category==1);
 jump=(GuideCursor){2,0,8,4,0};
 assert(guide_step(&jump,256,4,229,3)==1 && jump.page==1 && jump.row==8);
 assert(guide_step(&jump,512,4,229,3)==1 && jump.page==0);
 jump=(GuideCursor){1,0,8,4,0};
 assert(guide_step(&jump,2|256,4,229,3)==1 && jump.depth==0 && jump.row==8);
 jump=(GuideCursor){1,0,8,4,0};
 assert(guide_step(&jump,1|256,4,229,3)==1 && jump.depth==1 && jump.row==13 && jump.scroll==9);
 assert(guide_step(&jump,1|512|256,4,229,3)==0 && jump.depth==1 && jump.row==13 && jump.scroll==9);
 unsigned edges[]={15,16,47,48,207,208,239,240};
 unsigned actions[]={0,512,512,0,0,256,256,0};
 for(unsigned i=0;i<8;i++) {
  assert(guide_header(edges[i],1,229)==actions[i]);
  assert(guide_header(edges[i],1,5)==0);
  assert(guide_header(edges[i],0,229)==0);
  assert(guide_header(edges[i],2,229)==0);
 }
 return 0;
}
#endif
