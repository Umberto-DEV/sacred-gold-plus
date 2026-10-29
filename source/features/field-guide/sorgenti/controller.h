/* GPL-3.0-or-later. Native Guide navigation, independent of rendering. */
#ifndef GUIDE_CONTROLLER_H
#define GUIDE_CONTROLLER_H
typedef struct { unsigned short depth,category,row,scroll,page; } GuideCursor;
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
static int guide_jump(GuideCursor *s,unsigned key,unsigned entries) {
 unsigned forward=key&(16|256),back=key&(32|512);
 if(s->depth!=1 || entries<=5 || (forward!=0)==(back!=0))return 0;
 int target=(int)s->row+(forward?5:-5),slot=(int)s->row-(int)s->scroll;
 if(target<0)target=0;
 if((unsigned)target>=entries)target=entries-1;
 if(target==s->row)return 0;
 int scroll=target-slot,max=(int)entries-5;
 if(scroll<0)scroll=0;
 if(scroll>max)scroll=max;
 s->row=target;s->scroll=scroll;return 1;
}
/* 0 unchanged, 1 redraw, 2 close. B takes priority over simultaneous A. */
static int guide_step(GuideCursor *s,unsigned key,unsigned cats,unsigned entries,unsigned pages) {
 unsigned count=s->depth?entries:cats;
 unsigned short *row=s->depth?&s->row:&s->category;
 if(key&2) {if(!s->depth)return 2; --s->depth; return 1;}
 if(s->depth==2) {
  if((key&(16|256)) && s->page+1<pages) {s->page++;return 1;}
  if((key&(32|512)) && s->page) {s->page--;return 1;}
  return 0;
 }
 if(s->depth==1 && entries>5 && (key&(16|32|256|512)))return guide_jump(s,key,entries);
 if((key&64) && *row) --*row;
 else if((key&128) && *row+1<count) ++*row;
 else if((key&1) && count) {
  s->depth++;
  if(s->depth==1) s->row=s->scroll=0;
  s->page=0;return 1;
 } else return 0;
 if(s->depth==1) {
  if(s->row<s->scroll)s->scroll=s->row;
  if(s->row>=s->scroll+5)s->scroll=s->row-4;
 }
 return 1;
}
#endif
