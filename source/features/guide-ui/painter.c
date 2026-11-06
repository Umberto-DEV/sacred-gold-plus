#include "painter.h"
#define GP_MAGIC 0x31545047u
enum { GP_IDLE,GP_ADMIT,GP_CLOSE,GP_ACQUIRE,GP_CLEAR,GP_REPLAY,GP_FONT,
 GP_DECORATE,GP_UPLOAD,GP_READY,GP_PREPARED,GP_FAILED,GP_HOLD };
static unsigned gp_record(const GuidePainter *p) {
 return fspan((unsigned)p,sizeof(*p)) && rwritable((unsigned)p,sizeof(*p)) &&
 p->magic==GP_MAGIC && p->self==(unsigned)p && p->generation && p->phase<=GP_HOLD;
}
static void gp_unbind(GuidePainter *p) {
 p->heap=0;p->bg=0;p->font=0;p->desired=0;p->guide=0;p->uir1_owner=0;p->pool_owner=0;
}
unsigned guide_paint_init(GuidePainter *p,unsigned bytes,unsigned generation) {
 if(bytes!=sizeof(*p) || !generation || !fspan((unsigned)p,sizeof(*p)) || !rwritable((unsigned)p,sizeof(*p)))return 0;
 const unsigned *q=(const unsigned *)p;for(unsigned i=0;i<sizeof(*p)/4;++i)if(q[i])return 0;
 p->magic=GP_MAGIC;p->self=(unsigned)p;p->generation=generation;
 p->palette[0]=0;p->palette[1]=0x7bdf;p->palette[2]=0x2508;p->palette[3]=0x51a4;
 p->palette[4]=0x6f19;p->palette[5]=0x45ac;p->palette[6]=0x3372;p->palette[7]=0x1d67;
 p->palette[8]=0x1cbb;p->palette[9]=0x63b8;p->palette[10]=0x7fff;p->palette[11]=0x564c;
 p->palette[12]=0x3adf;p->palette[13]=0x6b7a;p->palette[14]=0x28f6;p->palette[15]=0x5ef5;
 return 1;
}
static unsigned gp_binding(GuidePainter *p,const GuidePaintRequest *r,const GuidePaintRequest *origin) {
 UiFontLease *f=r->font;UiBg *b=r->bg;UiHeap *h=r->heap;const UiGuideLease *g=r->guide;
 if(!fspan((unsigned)f,sizeof(*f)) || ui_font_check(f)!=UI_FONT_READY || f->job || !ggr_lease(g) ||
 !hlive(h) || h->generation!=r->generation || g->generation!=r->generation ||
 g->reader->heap!=h || f->resource.reader->heap!=h || !bg_owned(h,b,r->generation) ||
 b->role || b->lowerRows!=UI_BG_STATIC_BALL || b->phase!=UI_BG_DISPLAY || !bg_begin_allowed(h,b,r->generation,r->index) ||
 !r->version || r->version<=b->version[0] || r->version<=b->version[1])return 0;
 const GuidePlan *d=r->desired;const UiTextOwner *u=r->uir1_owner,*v=r->pool_owner;unsigned pool_extent;
 unsigned a[11],n[11];a[0]=(unsigned)p;n[0]=sizeof(*p);a[1]=(unsigned)b;n[1]=sizeof(*b);
 a[2]=(unsigned)f;n[2]=sizeof(*f);a[3]=(unsigned)g;n[3]=sizeof(*g);a[4]=(unsigned)d;n[4]=sizeof(*d);
 a[5]=(unsigned)u;n[5]=20;a[6]=(unsigned)v;n[6]=20;a[7]=(unsigned)f->resource.reader;n[7]=sizeof(UiResourceReader);
 a[8]=(unsigned)h;n[8]=sizeof(*h);a[9]=(unsigned)origin;n[9]=sizeof(*origin);a[10]=(unsigned)g->reader;n[10]=sizeof(*g->reader);
 /* origin is a copied synchronous descriptor admitted by rr, including SYS;
  * persistent actors/owners alone require foutput MAIN storage. */
 for(unsigned i=0;i<11;++i) {
  if(i!=2 && i!=7 && i!=8 && i!=9 && !foutput(f,a[i],n[i]))return 0;
  for(unsigned j=0;j<i;++j)if(ro(a[i],n[i],a[j],n[j]))return 0;
 }
 if(!gr_plan(d) || d->epoch!=g->generation || u->kind!=UI_TEXT_UIR1 || !fowner(f,u,0,1,UI_TEXT_SINGLE) ||
 v->kind!=UI_TEXT_BUFFER || !fowner(f,v,0,1,UI_TEXT_SINGLE) || !fbuffer(f,v,&pool_extent) ||
 v->bytes!=1024 || v->epoch!=d->pool_epoch || d->pool_used>v->bytes)return 0;
 unsigned roots[12],sizes[12];roots[0]=f->root;sizes[0]=f->bytes;
 for(unsigned i=0;i<5;++i){roots[i+1]=(unsigned)bg_ptr(b,i);sizes[i+1]=bg_size(i);}
 roots[6]=(unsigned)v->root;sizes[6]=v->bytes;roots[7]=(unsigned)g->owner.root;sizes[7]=g->owner.bytes;
 for(unsigned i=0;i<8;++i) {
  unsigned bytes=sp_root(h,roots[i],sizes[i]);
  if(!bytes || (i && !fnative(f->manager,roots[i]-32,bytes)))return 0;sizes[i]=bytes;
  for(unsigned j=0;j<11;++j)if(ro(roots[i]-32,bytes,a[j],n[j]))return 0;
  for(unsigned j=0;j<i;++j)if(ro(roots[i]-32,bytes,roots[j]-32,sizes[j]))return 0;
 }
 return 1;
}
static unsigned gp_slice(const GuidePainter *p,const GuideDrawOp *o,UiTextSlice *s) {
 sr_copy(s,&o->text,sizeof(*s));
 if(o->kind==GUIDE_DRAW_UIR_TEXT){if(s->owner)return 0;s->owner=p->uir1_owner;}
 else if(!s->owner){s->owner=p->pool_owner;if(s->offset>p->desired->pool_used || s->units*2>p->desired->pool_used-s->offset)return 0;}
 else if(s->owner!=&p->guide->owner)return 0;
 return s->policy==UI_TEXT_SINGLE && fowner(p->font,s->owner,s->offset,s->units,UI_TEXT_SINGLE);
}
static unsigned gp_admit(const GuidePainter *p,const GuideDrawOp *o) {
 if(o->screen || o->flags&~7u || !o->color || o->color>13 || o->kind==GUIDE_DRAW_BUTTON)return 0;
 if(o->kind==GUIDE_DRAW_BAND)return o->x==4 && o->w==232 && o->h==20 && !o->text.units;
 if(o->h!=16)return 0;
 UiTextSlice s;unsigned w;
 return gp_slice(p,o,&s) && gr_width(&s,(const unsigned char *)p->font->widths,o->w,&w);

}
GuidePaintStatus guide_paint_begin(GuidePainter *p,const GuidePaintRequest *origin) {
 if(!gp_record(p) || (p->phase!=GP_IDLE && p->phase!=GP_PREPARED) || !rr((unsigned)origin,sizeof(*origin)) ||
 ro((unsigned)p,sizeof(*p),(unsigned)origin,sizeof(*origin)))return GUIDE_PAINT_REFUSED;
 GuidePaintRequest r;fcopy(&r,origin,sizeof(r));
 if(r.generation!=p->generation || !gp_binding(p,&r,origin))return GUIDE_PAINT_REFUSED;
 p->heap=r.heap;p->bg=r.bg;p->font=r.font;p->guide=r.guide;p->desired=r.desired;
 p->uir1_owner=r.uir1_owner;p->pool_owner=r.pool_owner;p->index=r.index;p->version=r.version;
 p->upper_rows=p->lower_rows=p->touched_upper=p->touched_lower=p->op_cursor=p->row_cursor=p->full=p->error=0;
 p->phase=GP_ADMIT;return GUIDE_PAINT_MORE;
}
static GuidePaintStatus gp_bad(GuidePainter *p,unsigned acquired,unsigned error) {
 p->error=error;
 if(acquired){p->history[p->index].valid=0;p->history[p->index].upper_invalid=p->history[p->index].lower_invalid=GUIDE_PLAN_FULL;p->phase=GP_FAILED;return GUIDE_PAINT_FAILED;}
 p->phase=GP_IDLE;gp_unbind(p);return GUIDE_PAINT_REFUSED;
}
static UiNativeWindow16 *gp_window(GuidePainter *p,unsigned screen,unsigned index) {
 return screen?&p->bg->lowerWindows[index]:&p->bg->windows[index];
}
/* Tiny tile primitives local to Guide; the Settings painter is unchanged. */
static void gp_pixel(UiNativeWindow16 *w,unsigned x,unsigned y,unsigned color) {
 unsigned off=((y>>3)*30+(x>>3))*32+(y&7)*4+((x&7)>>1),shift=(x&1)*4;
 unsigned char *at=(unsigned char *)w->pixels+off;*at=(unsigned char)((*at&~(15u<<shift))|(color<<shift));
}
static void gp_rect(UiNativeWindow16 *w,unsigned x,unsigned y,unsigned width,unsigned height,unsigned fill,unsigned edge,unsigned mask) {
 /* Two adjacent 4bpp pixels share a byte. Keep odd edge nibbles intact,
  * including one-pixel rectangles and tile crossings. Same raster as before. */
 unsigned char *pixels=w->pixels;
 for(unsigned yy=0;yy<height;++yy)if(mask&(1u<<((y+yy)>>3))) {
  unsigned py=y+yy,xx=0,solid=edge && (!yy || yy+1==height)?edge:fill;
  if(x&1){gp_pixel(w,x,py,edge?edge:solid);xx=1;}
  for(;xx+1<width;xx+=2){unsigned px=x+xx,lo=edge && !xx?edge:solid,hi=edge && xx+2==width?edge:solid;
   pixels[((py>>3)*30+(px>>3))*32+(py&7)*4+((px&7)>>1)]=(unsigned char)(lo|(hi<<4));}
  if(xx<width)gp_pixel(w,x+xx,py,edge?edge:solid);
 }
}
static void gp_chrome(GuidePainter *p,unsigned screen,unsigned row) {
 UiNativeWindow16 *w=gp_window(p,screen,p->index);unsigned mask=1u<<row;
 gp_rect(w,0,row*8,240,8,3,0,mask);
 gp_rect(w,0,row*8,1,8,2,0,mask);gp_rect(w,239,row*8,1,8,2,0,mask);
 gp_rect(w,4,32,232,112,1,0,mask);
 gp_rect(w,4,144,232,32,2,0,mask);
 if(p->desired->view<2) {
  gp_rect(w,4,36,232,100,3,0,mask);
  for(unsigned i=0;i<5;++i)gp_rect(w,6,55+20*i,228,1,11,0,mask);
 }
 for(unsigned i=0;i<p->desired->count;++i){const GuideDrawOp *o=&p->desired->ops[i];
  if(o->screen!=screen || !(gr_rows(o)&mask))continue;
  if(o->kind==GUIDE_DRAW_BAND)gp_rect(w,o->x,o->y,o->w,o->h,1,8,mask);

 }
}
static unsigned gp_read(const UiNativeWindow16 *w,unsigned x,unsigned y) {
 unsigned off=((y>>3)*30+(x>>3))*32+(y&7)*4+((x&7)>>1);
 return ((const unsigned char *)w->pixels)[off]>>((x&1)*4)&15;
}
/* The native printer clears its whole 16-pixel cell to the background, so the
 * list cells (y+4..y+19) erase the separator/band bottom edge at y+19. After
 * all text, replay only those contour pixels that still hold a fill colour
 * (1 band, 3 list): glyph ink (2/5/10) is never overwritten. Upper only. */
static void gp_contour(GuidePainter *p) {
 if(p->desired->view>=2)return;
 UiNativeWindow16 *w=gp_window(p,0,p->index);unsigned mask=p->upper_rows;
 for(unsigned i=0;i<5;++i){unsigned y=55+20*i;if(!(mask&(1u<<(y>>3))))continue;
  for(unsigned x=6;x<234;++x){unsigned c=gp_read(w,x,y);if(c==1 || c==3)gp_pixel(w,x,y,11);}
 }
 for(unsigned i=0;i<p->desired->count;++i){const GuideDrawOp *o=&p->desired->ops[i];unsigned y=o->y+o->h-1;
  if(o->screen || o->kind!=GUIDE_DRAW_BAND || !(mask&(1u<<(y>>3))))continue;
  for(unsigned x=o->x;x<o->x+o->w;++x){unsigned c=gp_read(w,x,y);if(c==1 || c==3 || c==11)gp_pixel(w,x,y,8);}
 }
}
static void gp_geometry(GuidePainter *p,const GuideDrawOp *o) {
 UiNativeWindow16 *w=gp_window(p,o->screen,p->index);unsigned mask=o->screen?p->lower_rows:p->upper_rows;
 if(o->kind==GUIDE_DRAW_BAND) {
  for(unsigned y=0;y<7;++y)for(unsigned x=0;x<4;++x)if((y>3?y-3:3-y)<=3-x && (mask&(1u<<((o->y+8+y)>>3))))gp_pixel(w,o->x+5+x,o->y+8+y,2);
  return;
 }

}
GuidePaintStatus guide_paint_step(GuidePainter *p,unsigned budget) {
 if(!gp_record(p) || !budget || budget>8)return GUIDE_PAINT_REFUSED;
 if(p->phase==GP_PREPARED)return GUIDE_PAINT_PREPARED;
 if(p->phase==GP_FAILED)return GUIDE_PAINT_FAILED;
 if(p->phase==GP_HOLD)return GUIDE_PAINT_HOLD;
 if(p->phase==GP_IDLE)return GUIDE_PAINT_UNCHANGED;
 if(!rio())return GUIDE_PAINT_MORE;
 unsigned acquired=p->phase>=GP_CLEAR;UiFontStatus fs=ui_font_check(p->font);
 if(fs==UI_FONT_DEFER)return GUIDE_PAINT_MORE;
 if(fs==UI_FONT_HOLD){p->phase=GP_HOLD;return GUIDE_PAINT_HOLD;}
 if(fs!=UI_FONT_READY || !ggr_lease(p->guide) || p->desired->pool_epoch!=p->pool_owner->epoch ||
 p->desired->epoch!=p->generation || !p->pool_owner->live || !p->uir1_owner->live)return gp_bad(p,acquired,1);
 if(acquired && (!bg_mutable(p->heap,p->bg,p->generation) || p->bg->preparing!=p->index))return gp_bad(p,1,2);
 const GuidePlan *d=p->desired;const GuideDrawOp *o;
 switch(p->phase) {
 case GP_ADMIT:
  /* Finite immutable-plan scan: no scheduler/native boundary between ops. */
  while(p->op_cursor<d->count)if(!gp_admit(p,&d->ops[p->op_cursor++]))return gp_bad(p,0,3);
  {GuideHistory *h=&p->history[p->index];GuideDirty dirty;
   if(!guide_ui_dirty(h->valid && h->version==p->bg->version[p->index]?&h->plan:0,d,h->upper_invalid,h->lower_invalid,&dirty))return gp_bad(p,0,4);
   p->full=dirty.full;
   if(p->bg->front<2 && !p->bg->role) {
    GuideHistory *front=&p->history[p->bg->front];GuideDirty presented;
    if(front->valid && front->version==p->bg->version[p->bg->front] &&
       guide_ui_dirty(&front->plan,d,front->upper_invalid,front->lower_invalid,&presented) &&
       !presented.full && presented.upper && !presented.lower) {
     dirty=presented;p->full=2;
    }
   }
   p->upper_rows=dirty.upper;p->lower_rows=dirty.lower;
   if(!p->upper_rows && !p->lower_rows){p->full=1;p->upper_rows=GUIDE_PLAN_FULL;p->lower_rows=0;}
   p->row_cursor=0;p->phase=GP_CLOSE;
  }return GUIDE_PAINT_MORE;
 case GP_CLOSE:
  {unsigned upper=p->upper_rows,lower=p->lower_rows;
   for(unsigned i=0;i<d->count;++i){o=&d->ops[i];unsigned rows=gr_rows(o);
    if(o->screen){if(rows&p->lower_rows)p->lower_rows|=rows;}
    else if(rows&p->upper_rows)p->upper_rows|=rows;
   }
   if(upper==p->upper_rows && lower==p->lower_rows)p->phase=GP_ACQUIRE;
   else if(++p->row_cursor>=22)return gp_bad(p,0,5);
  }return GUIDE_PAINT_MORE;
 case GP_ACQUIRE:
  {unsigned window;
   if(p->full==2)window=ui_bg_begin_copy(p->heap,p->bg,p->generation,p->index,p->upper_rows);
   else if(p->full)window=ui_bg_begin(p->heap,p->bg,p->generation,p->index);
   else window=ui_bg_begin_retained(p->heap,p->bg,p->generation,p->index,p->history[p->index].version,p->upper_rows);
   if(!window)return gp_bad(p,window!=0,6);
   GuideHistory *h=&p->history[p->index];h->valid=0;h->upper_invalid|=p->upper_rows;h->lower_invalid|=p->lower_rows;
   p->row_cursor=0;p->phase=GP_CLEAR;
  }return GUIDE_PAINT_MORE;
 case GP_CLEAR:
  if(!p->row_cursor) {
   if(p->upper_rows && !ui_bg_invalidate_rows(p->heap,p->bg,p->generation,p->upper_rows))return gp_bad(p,1,7);
   if(p->lower_rows && !ui_bg_lower_invalidate_rows(p->heap,p->bg,p->generation,p->lower_rows))return gp_bad(p,1,7);
   p->touched_upper|=p->upper_rows;p->touched_lower|=p->lower_rows;
  }
  for(unsigned count=0;p->row_cursor<44 && count<4;++p->row_cursor) {
   unsigned screen=p->row_cursor>=22,row=screen?p->row_cursor-22:p->row_cursor;
   if((screen?p->lower_rows:p->upper_rows)&(1u<<row)){gp_chrome(p,screen,row);++count;}
  }
  if(p->row_cursor==44){p->op_cursor=0;p->phase=GP_REPLAY;}
  return GUIDE_PAINT_MORE;
 case GP_REPLAY:
  while(p->op_cursor<d->count && !(gr_rows(&d->ops[p->op_cursor])&
        (d->ops[p->op_cursor].screen?p->lower_rows:p->upper_rows)))++p->op_cursor;
  if(p->op_cursor==d->count){p->phase=GP_DECORATE;return GUIDE_PAINT_MORE;}
  o=&d->ops[p->op_cursor];
  if(o->kind==GUIDE_DRAW_BAND)gp_geometry(p,o);
  if(!o->text.units){++p->op_cursor;return GUIDE_PAINT_MORE;}
  {UiFontRequest r;fzero(&r,sizeof(r));if(!gp_slice(p,o,&r.text))return gp_bad(p,1,8);
   r.window=gp_window(p,o->screen,p->index);r.front=gp_window(p,o->screen,1-p->index)->pixels;r.pixel_bytes=21120;
   r.scratch=&p->scratch;r.x=o->x;r.y=o->y;r.max_lines=1;
   r.bg=o->color;r.fg=o->flags&4?5:(r.bg==2 || r.bg==3)?10:2;
   r.shadow=r.bg;fs=fbegin_checked(p->font,&p->job,&r);
   if(fs==UI_FONT_DEFER)return GUIDE_PAINT_MORE;
   if(fs==UI_FONT_HOLD){p->phase=GP_HOLD;return GUIDE_PAINT_HOLD;}
   if(fs!=UI_FONT_ACTIVE)return gp_bad(p,1,9);
   p->phase=GP_FONT;
  }return GUIDE_PAINT_MORE;
 case GP_FONT:
  fs=fstep_checked(p->font,&p->job,budget);
  if(fs==UI_FONT_ACTIVE || fs==UI_FONT_DEFER)return GUIDE_PAINT_MORE;
  if(fs==UI_FONT_HOLD){p->phase=GP_HOLD;return GUIDE_PAINT_HOLD;}
  if(fs!=UI_FONT_DONE)return gp_bad(p,1,10);
  ++p->op_cursor;p->phase=GP_REPLAY;return GUIDE_PAINT_MORE;
 case GP_DECORATE:
  if(p->font->job || (p->full==1 && !ui_bg_unframed(p->heap,p->bg,p->generation)))return gp_bad(p,1,11);
  gp_contour(p);
  p->row_cursor=0;p->phase=GP_UPLOAD;return GUIDE_PAINT_MORE;
 case GP_UPLOAD:
  while(p->row_cursor<44){unsigned screen=p->row_cursor>=22,row=screen?p->row_cursor-22:p->row_cursor;
   if((screen?p->lower_rows:p->upper_rows)&(1u<<row))break;++p->row_cursor;
  }
  if(p->row_cursor<44) {
   unsigned screen=p->row_cursor>=22,mask=screen?p->lower_rows:p->upper_rows;
   UiBgRows rows;rows.first=screen?p->row_cursor-22:p->row_cursor;rows.count=1;
   while(rows.first+rows.count<22 && (mask&(1u<<(rows.first+rows.count))))++rows.count;
   unsigned ok=screen?ui_bg_lower_rows(p->heap,p->bg,p->generation,&rows):ui_bg_rows(p->heap,p->bg,p->generation,&rows);
   if(!ok)return gp_bad(p,1,12);p->row_cursor+=rows.count;
  } else p->phase=GP_READY;
  return GUIDE_PAINT_MORE;
 case GP_READY:
  if(p->font->job || p->job.phase==UI_FONT_ACTIVE || !ui_bg_ready(p->heap,p->bg,p->generation,p->version))return gp_bad(p,1,13);
  {GuideHistory *h=&p->history[p->index];fcopy(&h->plan,d,sizeof(*d));h->version=p->version;h->valid=1;h->upper_invalid=h->lower_invalid=0;}
  p->phase=GP_PREPARED;gp_unbind(p);return GUIDE_PAINT_PREPARED;
 default:return GUIDE_PAINT_REFUSED;
 }
}
GuidePaintStatus guide_paint_retire(GuidePainter *p) {
 if(!gp_record(p))return GUIDE_PAINT_REFUSED;
 if(p->phase==GP_IDLE || p->phase==GP_PREPARED){p->phase=GP_IDLE;gp_unbind(p);return GUIDE_PAINT_UNCHANGED;}
 if(!rio())return GUIDE_PAINT_MORE;
 if(p->font && p->font->job==&p->job) {
  UiFontStatus s=ui_font_cancel(p->font,&p->job);
  if(s==UI_FONT_DEFER)return GUIDE_PAINT_MORE;
  if(s!=UI_FONT_CANCELLED){p->phase=GP_HOLD;return GUIDE_PAINT_HOLD;}
 }
 if(p->font && p->font->state==UI_FONT_HOLD){p->phase=GP_HOLD;return GUIDE_PAINT_HOLD;}
 p->history[0].valid=p->history[1].valid=0;
 p->history[0].upper_invalid=p->history[0].lower_invalid=p->history[1].upper_invalid=p->history[1].lower_invalid=GUIDE_PLAN_FULL;
 if(p->bg && p->bg->phase!=UI_BG_STORAGE && (p->touched_upper || p->touched_lower || p->bg->preparing==p->index || p->phase==GP_HOLD)) {
  p->phase=GP_FAILED;return GUIDE_PAINT_FAILED;
 }
 p->phase=GP_IDLE;gp_unbind(p);return GUIDE_PAINT_UNCHANGED;
}
