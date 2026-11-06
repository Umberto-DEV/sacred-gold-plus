#include "render.h"
/* Pure planner reuses the accepted checked RAM/copy/decimal primitives. */
typedef struct { GuidePlan plan; unsigned short words[512]; } GuBuild;
static unsigned gr_width(const UiTextSlice *s,const unsigned char *widths,unsigned limit,unsigned *out) {
 if(!s->units || s->units>128 || s->offset&1 || !s->owner || !s->owner->live ||
 s->offset>s->owner->bytes || s->units*2>s->owner->bytes-s->offset)return 0;
 const unsigned short *t=(const unsigned short *)((unsigned)s->owner->root+s->offset);unsigned w=0;
 for(unsigned i=0;i<s->units;++i) {
  unsigned c=t[i];if(c==65535){if(i+1!=s->units)return 0;*out=w;return 1;}
  if(!c || c>509 || !widths[c-1] || widths[c-1]>16 || w+widths[c-1]>limit)return 0;
  w+=widths[c-1];
 }return 0;
}
static GuideDrawOp *gr_op(GuBuild *b,unsigned kind,unsigned screen,unsigned x,unsigned y,unsigned w,unsigned h,unsigned flags,unsigned color) {
 if(b->plan.count>=32 || !w || !h || x+w>240 || y+h>176)return 0;
 GuideDrawOp *o=&b->plan.ops[b->plan.count++];o->kind=kind;o->screen=screen;
 o->x=x;o->y=y;o->w=w;o->h=h;o->flags=flags;o->color=color;return o;
}
static unsigned gr_buffer(GuBuild *b,GuideDrawOp *o,const unsigned short *t,unsigned n) {
 if(!o || !n || n>128 || b->plan.pool_used+n*2>1024)return 0;
 o->text.offset=b->plan.pool_used;o->text.units=n;o->text.policy=UI_TEXT_SINGLE;
 for(unsigned i=0;i<n;++i)b->words[(b->plan.pool_used>>1)+i]=t[i];
 b->plan.pool_used+=n*2;return 1;
}
static unsigned gr_text(GuBuild *b,UiTextSlice *s,const unsigned char *widths,unsigned screen,unsigned x,unsigned y,unsigned limit,unsigned color) {
 unsigned w;if(!gr_width(s,widths,limit,&w) || !w)return 0;
 GuideDrawOp *o=gr_op(b,GUIDE_DRAW_TEXT,screen,x,y,w,16,0,color);if(!o)return 0;
 sr_copy(&o->text,s,sizeof(*s));return 1;
}
static unsigned gr_uir(GuBuild *b,const UiResourceLease *r,const unsigned char *widths,unsigned id,unsigned screen,unsigned x,unsigned y,unsigned limit,unsigned color) {
 UiResourceSlice a;UiTextOwner owner;UiTextSlice s;unsigned w;
 if(!ui_res_text(r,id,&a) || (a.bytes&1))return 0;
 owner.kind=UI_TEXT_UIR1;owner.root=(const void *)r->reader->root;owner.bytes=r->reader->config.word[7];owner.epoch=r->generation;owner.live=1;
 s.owner=&owner;s.offset=(unsigned)a.data-(unsigned)owner.root;s.units=a.bytes>>1;s.policy=UI_TEXT_SINGLE;
 if(!gr_width(&s,widths,limit,&w))return 0;
 GuideDrawOp *o=gr_op(b,GUIDE_DRAW_UIR_TEXT,screen,x,y,w,16,0,color);if(!o)return 0;
 sr_copy(&o->text,&s,sizeof(s));o->text.owner=0;return 1;
}
static unsigned gr_title(GuBuild *b,UiTextSlice *s,const unsigned char *widths,unsigned space) {
 unsigned w;if(!gr_width(s,widths,208,&w))return 0;
 if(w<=160)return gr_text(b,s,widths,0,8,0,160,3);
 const unsigned short *t=(const unsigned short *)((unsigned)s->owner->root+s->offset);
 unsigned at=0,split=0,wide=0,last_space=0,space_width=0;
 while(at+1<s->units && wide+widths[t[at]-1]<=160) {wide+=widths[t[at]-1];++at;if(t[at-1]==space){last_space=at;space_width=wide;}}
 split=last_space && w-space_width<=160?last_space:at;if(!split || split+1>=s->units)return 0;
 unsigned start=0;unsigned short text[128];
 for(unsigned line=0;line<2;++line) {
  unsigned end=line?s->units-1:split,n=end-start;wide=0;
  for(unsigned i=0;i<n;++i){text[i]=t[start+i];wide+=widths[text[i]-1];}
  text[n]=65535;if(wide>160 || !wide || !gr_buffer(b,gr_op(b,GUIDE_DRAW_TEXT,0,8,line*16,wide,16,0,3),text,n+1))return 0;
  start=end;
 }return 1;
}
static unsigned gr_counter(GuBuild *b,const unsigned short *alphabet,const unsigned char *widths,unsigned a,unsigned total,unsigned screen) {
 unsigned short text[22];unsigned n=sr_digits(a,total,1,alphabet,text),wide=0;
 for(unsigned i=0;i+1<n;++i)wide+=widths[text[i]-1];
 if(wide>56)return 0;
 return gr_buffer(b,gr_op(b,GUIDE_DRAW_TEXT,screen,232-wide,screen?12:0,wide,16,0,screen?13:3),text,n);
}
/* Four stable upper hint cells. Keys retain the native font0 advances; the
 * inventoried up/down glyphs are 011C/011D, not hand-drawn button artwork. */
static unsigned gr_rail(GuBuild *b,const GuideState *s,const UiGuideLease *g,const UiResourceLease *r,const unsigned char *widths,const unsigned short *alpha,unsigned left,unsigned right) {
 for(unsigned slot=0;slot<4;++slot) {
  unsigned id,enabled,x=slot&1?120:8,y=slot<2?144:160,n=0,wide=0;
  unsigned short key[4];
  if(slot>=2) {
   key[n++]=alpha[slot==2?14:15];
   id=slot==2?(s->cursor.depth==2?SGP_UI_GUIDE_LINK:SGP_UI_GUIDE_OPEN):s->cursor.depth?SGP_UI_GUIDE_BACK:SGP_UI_GUIDE_CLOSE;
   enabled=guide_ui_control(s,g,s->cursor.depth==2?(slot==2?4:3):(slot==2?6:5));
  } else if(s->cursor.depth==2) {
   key[n++]=slot?right:left;id=slot?SGP_UI_GUIDE_NEXT:SGP_UI_GUIDE_PREVIOUS;
   enabled=guide_ui_control(s,g,slot+1);
  } else if(slot) {
   key[n++]=left;key[n++]=alpha[10];key[n++]=right;id=SGP_UI_GUIDE_PAGING;
   enabled=guide_ui_control(s,g,3)|guide_ui_control(s,g,4);
  } else {
   key[n++]=0x11C;key[n++]=0x11D;id=SGP_UI_GUIDE_SELECT;
   enabled=guide_ui_control(s,g,1)|guide_ui_control(s,g,2);
  }
  for(unsigned i=0;i<n;++i){if(!widths[key[i]-1] || widths[key[i]-1]>16)return 0;wide+=widths[key[i]-1];}
  if(wide>24)return 0;key[n++]=65535;
  unsigned flags=enabled?0:GUIDE_DRAW_DISABLED;
  if(!gr_buffer(b,gr_op(b,GUIDE_DRAW_TEXT,0,x,y,wide,16,flags,2),key,n) ||
     !gr_uir(b,r,widths,id,0,x+28,y,84,2))return 0;
  b->plan.ops[b->plan.count-1].flags=flags;
 }return 1;
}
static unsigned gr_build(GuBuild *b,const GuideState *s,const UiGuideLease *g,const UiResourceLease *r,const unsigned char *widths) {
 UiGuideCategory c;UiGuideEntry e;UiGuidePage page;UiResourceSlice format,footer;
 if(!gu_view(s,g,&c,&e,&page) || !ui_res_text(r,SGP_UI_FORMAT_POOL,&format) || format.bytes<38 || format.bytes>258 ||
 !ui_res_text(r,SGP_UI_GUIDE_LIST,&footer) || footer.bytes<8 || footer.bytes>258)return 0;
 const unsigned short *f=format.data,*h=footer.data;unsigned short alpha[18];unsigned left=0,right=0;
 for(unsigned i=0;i<14;++i)alpha[i]=f[i];
 unsigned n=format.bytes/2;alpha[14]=f[n-5];alpha[15]=f[n-4];alpha[16]=f[n-3];alpha[17]=f[n-2];
 for(unsigned i=1;i+2<footer.bytes/2;++i)if(h[i]==alpha[10]){left=h[i-1];right=h[i+1];break;}
 for(unsigned i=0;i<18;++i)if(!alpha[i] || alpha[i]>509 || !widths[alpha[i]-1] || widths[alpha[i]-1]>16)return 0;
 if(!left || left>509 || !right || right>509)return 0;
 b->plan.magic=GUIDE_PLAN_MAGIC;b->plan.epoch=g->generation;b->plan.view=s->cursor.depth;
 b->plan.entry=s->cursor.depth==2?e.index+1:s->cursor.depth?s->cursor.category+1:0;b->plan.page=s->cursor.page;
 if(!s->cursor.depth) {if(!gr_uir(b,r,widths,SGP_UI_GUIDE_TITLE,0,8,0,160,3))return 0;}
 else {UiTextSlice *title=s->cursor.depth==1?&c.title:&e.title;if(!gr_title(b,title,widths,alpha[13]))return 0;}
 unsigned pos=s->cursor.depth==2?s->cursor.page+1:s->cursor.depth?s->cursor.row+1:s->cursor.category+1;
 unsigned total=s->cursor.depth==2?e.pages:s->cursor.depth?c.count:c.total;
 if(!gr_counter(b,alpha,widths,pos,total,0))return 0;
 if(s->cursor.depth==2) {
  if(page.lines>7)return 0;
  for(unsigned i=0;i<page.lines;++i){UiTextSlice line;
   if(!ui_guide_line(g,e.index,s->cursor.page,i,&line) || !gr_text(b,&line,widths,0,16,32+16*i,208,1))return 0;
  }
 } else {
  unsigned count=s->cursor.depth?c.count:c.total,start=s->cursor.depth?s->cursor.scroll:0;
  unsigned selected=s->cursor.depth?s->cursor.row:s->cursor.category;
  for(unsigned i=0;i<5 && start+i<count;++i){UiTextSlice text;
   if(s->cursor.depth){UiGuideEntry item;if(!ui_guide_entry(g,s->cursor.category,start+i,&item))return 0;sr_copy(&text,&item.title,sizeof(text));}
   else {UiGuideCategory item;if(!ui_guide_category(g,start+i,&item))return 0;sr_copy(&text,&item.title,sizeof(text));}
   unsigned chosen=start+i==selected;
   if(chosen && !gr_op(b,GUIDE_DRAW_BAND,0,4,36+20*i,232,20,GUIDE_DRAW_FOCUS,1))return 0;
   if(!gr_text(b,&text,widths,0,16,40+20*i,208,chosen?1:3))return 0;
  }
 }
 return gr_rail(b,s,g,r,widths,alpha,left,right);
}
unsigned guide_ui_build(const GuideState *s,const UiGuideLease *g,const UiResourceLease *r,const unsigned char *widths,GuidePlan *out,void *pool,unsigned epoch) {
 if(!sr_ram(s,sizeof(*s),4) || !sr_ram(g,sizeof(*g),4) || !ggr_lease(g) || !rlease(r) ||
 !sr_ram(widths,509,1) || !sr_ram(out,sizeof(*out),4) || !sr_ram(pool,1024,4) || !epoch)return 0;
 unsigned a[11],n[11];a[0]=(unsigned)s;n[0]=sizeof(*s);a[1]=(unsigned)g;n[1]=sizeof(*g);
 a[2]=(unsigned)g->reader;n[2]=sizeof(*g->reader);a[3]=(unsigned)g->owner.root;n[3]=g->owner.bytes;
 a[4]=(unsigned)r;n[4]=sizeof(*r);a[5]=(unsigned)r->reader;n[5]=sizeof(*r->reader);
 a[6]=r->reader->root;n[6]=r->reader->config.word[7];a[7]=(unsigned)widths;n[7]=509;
 a[8]=(unsigned)g->reader->heap;n[8]=sizeof(UiHeap);a[9]=g->reader->config_address;n[9]=64;
 a[10]=(unsigned)r->reader->heap;n[10]=sizeof(UiHeap);
 if(sr_overlap(out,sizeof(*out),pool,1024))return 0;
 for(unsigned i=0;i<11;++i)if(ro((unsigned)out,sizeof(*out),a[i],n[i]) || ro((unsigned)pool,1024,a[i],n[i]))return 0;
 GuBuild b;sr_zero(&b,sizeof(b));b.plan.pool_epoch=epoch;
 if(!gr_build(&b,s,g,r,widths))return 0;
 sr_copy(pool,b.words,b.plan.pool_used);sr_copy(out,&b.plan,sizeof(*out));return 1;
}
static unsigned gr_rows(const GuideDrawOp *o) {
 unsigned mask=0,first=o->y>>3,last=(o->y+o->h-1)>>3;
 while(first<=last)mask|=1u<<first++;return mask;
}
static unsigned gr_plan(const GuidePlan *p) {
 if(p->magic!=GUIDE_PLAN_MAGIC || !p->epoch || !p->pool_epoch || p->pool_used>1024 || (p->pool_used&1) || p->view>2 || p->count>32)return 0;
 for(unsigned i=0;i<p->count;++i){const GuideDrawOp *o=&p->ops[i];
  if(!o->w || !o->h || o->x+o->w>240 || o->y+o->h>176 || o->screen>1 || !o->kind || o->kind>GUIDE_DRAW_UIR_TEXT)return 0;
 }return 1;
}
static unsigned gr_same(const GuideDrawOp *a,const GuideDrawOp *b) {
 return a->text.owner==b->text.owner && a->text.offset==b->text.offset && a->text.units==b->text.units && a->text.policy==b->text.policy &&
 a->x==b->x && a->y==b->y && a->w==b->w && a->h==b->h && a->screen==b->screen && a->kind==b->kind && a->flags==b->flags && a->color==b->color;
}
unsigned guide_ui_dirty(const GuidePlan *old,const GuidePlan *now,unsigned upper,unsigned lower,GuideDirty *d) {
 if(!sr_ram(d,sizeof(*d),4) || !sr_ram(now,sizeof(*now),4) || sr_overlap(d,sizeof(*d),now,sizeof(*now)) ||
 (old && (!sr_ram(old,sizeof(*old),4) || sr_overlap(d,sizeof(*d),old,sizeof(*old)))) || !gr_plan(now))return 0;
 d->upper=upper&GUIDE_PLAN_FULL;d->lower=lower&GUIDE_PLAN_FULL;d->full=1;
 if(!old || !gr_plan(old) || old->epoch!=now->epoch || old->view!=now->view || old->entry!=now->entry ||
 d->upper==GUIDE_PLAN_FULL || d->lower==GUIDE_PLAN_FULL)goto full;
 for(unsigned i=0;i<2;++i){const GuidePlan *p=i?now:old,*q=i?old:now;
  for(unsigned j=0;j<p->count;++j){const GuideDrawOp *o=&p->ops[j];unsigned found=0;
   if(o->kind!=GUIDE_DRAW_BAND && !o->text.owner && o->kind!=GUIDE_DRAW_UIR_TEXT)found=0;
   else for(unsigned k=0;k<q->count;++k)if(gr_same(o,&q->ops[k])){found=1;break;}
   if(!found){if(!o->screen && o->y<32 && o->x<176)goto full;if(o->screen)d->lower|=gr_rows(o);else d->upper|=gr_rows(o);}
  }
 }
 d->full=0;return 1;
 full:d->upper=GUIDE_PLAN_FULL;d->lower=0;return 1;
}
