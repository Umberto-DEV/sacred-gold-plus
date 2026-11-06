#include "controller.h"
#include "../settings-ui/controller.h"
/* Typed outputs must be SYS locals: never pass persistent app fields to GGR. */
static unsigned gu_view(const GuideState *s,const UiGuideLease *g,
 UiGuideCategory *c,UiGuideEntry *e,UiGuidePage *p) {
 if(!s || s->cursor.depth>2 || s->back_count>8 ||
 !ui_guide_category(g,s->cursor.category,c))return 0;
 if(!s->cursor.depth)return !s->back_count;
 if(!ui_guide_entry(g,s->cursor.category,s->cursor.row,e) ||
 s->cursor.scroll>s->cursor.row || s->cursor.row>=s->cursor.scroll+5 ||
 s->cursor.scroll>(c->count>5?c->count-5:0))return 0;
 return s->cursor.depth==1?!s->back_count:
  ui_guide_page(g,e->index,s->cursor.page,p);
}
static void gu_cursor(GuideView *to,const GuideView *from) {
 unsigned short *d=(unsigned short *)to;const unsigned short *v=(const unsigned short *)from;
 for(unsigned i=0;i<5;++i)d[i]=v[i];
}
void guide_ui_init(GuideState *s) {
 unsigned *p=(unsigned *)s;for(unsigned i=0;i<sizeof(*s)/4;++i)p[i]=0;
 s->release_gate=1;
}
unsigned guide_ui_step(GuideState *s,const UiGuideLease *g,unsigned key) {
 UiGuideCategory c;UiGuideEntry e;UiGuidePage p;
 if(!gu_view(s,g,&c,&e,&p))return GUIDE_UI_NOOP;
 key=settings_keys(key,key,0)&~SETTINGS_KEYS_CANCELLED;
 if(key&2)key=2;else if(key&1)key=1;else if(key&512)key=512;
 else if(key&256)key=256;else if(key&64)key=64;else if(key&128)key=128;
 else if(key&32)key=32;else if(key&16)key=16;else return GUIDE_UI_NOOP;
 if(s->cursor.depth==2) {
  if(key==2 && s->back_count){gu_cursor(&s->cursor,&s->back[--s->back_count]);return GUIDE_UI_CHANGED;}
  if(key==1) {
   unsigned index;UiGuideCategory dest;UiGuideEntry target;
   if(s->back_count==8 || !p.reference || !ui_guide_find(g,p.reference,&index))return GUIDE_UI_NOOP;
   for(unsigned i=0;i<c.total;++i) {
    if(!ui_guide_category(g,i,&dest))return GUIDE_UI_NOOP;
    if(index>=dest.first && index-dest.first<dest.count) {
     unsigned row=index-dest.first;
     UiGuidePage first;
     if(!ui_guide_entry(g,i,row,&target) || !ui_guide_page(g,target.index,0,&first))return GUIDE_UI_NOOP;
     gu_cursor(&s->back[s->back_count++],&s->cursor);
     s->cursor.category=i;s->cursor.row=row;
     s->cursor.scroll=row<5?0:row-4;
     if(s->cursor.scroll>(dest.count>5?dest.count-5:0))s->cursor.scroll=dest.count>5?dest.count-5:0;
     s->cursor.page=0;return GUIDE_UI_CHANGED;
    }
   }return GUIDE_UI_NOOP;
  }
 }
 GuideView next;gu_cursor(&next,&s->cursor);
 unsigned result=guide_step(&next,key,c.total,c.count,s->cursor.depth==2?e.pages:0);
 if(result==GUIDE_UI_CHANGED && next.depth==2 && !ui_guide_page(g,e.index,next.page,&p))return GUIDE_UI_NOOP;
 if(result==GUIDE_UI_CHANGED)gu_cursor(&s->cursor,&next);return result;
}
unsigned guide_ui_control(const GuideState *s,const UiGuideLease *g,unsigned target) {
 UiGuideCategory c;UiGuideEntry e;UiGuidePage p;
 if(!target || target>6 || !gu_view(s,g,&c,&e,&p))return 0;
 if(s->cursor.depth==2) {
  if(target==1)return s->cursor.page?512:0;
  if(target==2)return s->cursor.page+1<e.pages?256:0;
  if(target==3)return 2;
  if(target==4)return p.reference && s->back_count<8?1:0;
  return 0;
 }
 unsigned row=s->cursor.depth?s->cursor.row:s->cursor.category;
 unsigned count=s->cursor.depth?c.count:c.total;
 if(target==1)return row?64:0;
 if(target==2)return row+1<count?128:0;
 if(target==3)return s->cursor.depth && c.count>5 && row?512:0;
 if(target==4)return s->cursor.depth && c.count>5 && row+1<count?256:0;
 return target==5?2:1;
}
/* ABI retained for callers; the entire lower LCD is intentionally inert. */
unsigned guide_ui_target(unsigned x,unsigned y) {(void)x;(void)y;return 0;}
unsigned guide_ui_input(GuideState *s,const UiGuideLease *g,const GuideInput *in) {
 s->touch_target=s->touch_armed=s->touch_down=s->sample_ready=0;
 if(in->freshness==PHYS_SUSPEND || in->freshness==PHYS_INVALID) {
  s->release_gate=1;return GUIDE_UI_NOOP;
 }
 if(in->freshness!=PHYS_FRESH || !in->sample)return GUIDE_UI_NOOP;
 const PhysicalSample *p=in->sample;s->sample_ready=1;
 if(in->busy || (p->flags&PHYS_RELEASE_ONLY)) {s->release_gate=1;return GUIDE_UI_NOOP;}
 if(s->release_gate) {
  if(!(p->held&(1|2|256|512|1024|2048)))s->release_gate=0;
  return GUIDE_UI_NOOP;
 }
 unsigned fresh=settings_keys(in->mapped_pressed,p->pressed,in->button_mode);
 unsigned repeats=settings_keys(in->mapped_repeated,p->repeated,in->button_mode);
 return guide_ui_step(s,g,fresh?fresh:repeats&(16|32|64|128|256|512));
}
