/* Compose in the documented order; reuse checked heap/resource/font/BG helpers. */
#include "painter.h"
#define SP_MAGIC 0x31545053u
enum { SP_IDLE,SP_ADMIT,SP_CLOSE,SP_ACQUIRE,SP_CLEAR,SP_REPLAY,SP_FONT,
 SP_DECORATE,SP_UPLOAD,SP_READY,SP_PREPARED,SP_FAILED,SP_HOLD };
static unsigned sp_place(const SettingsPainter *p) {
 return fspan((unsigned)p,sizeof(*p)) && rwritable((unsigned)p,sizeof(*p));
}
static unsigned sp_record(const SettingsPainter *p) {
 return sp_place(p) && p->magic==SP_MAGIC && p->self==(unsigned)p && p->generation && p->phase<=SP_HOLD;
}
static void sp_unbind(SettingsPainter *p) {
 p->heap=0;p->bg=0;p->font=0;p->catalog=0;p->desired=0;p->uir1_owner=0;p->pool_owner=0;
}
unsigned settings_paint_init(SettingsPainter *p,unsigned bytes,unsigned generation) {
 if(bytes!=sizeof(*p) || !generation || !sp_place(p))return 0;
 const unsigned *q=(const unsigned *)p;for(unsigned i=0;i<sizeof(*p)/4;++i)if(q[i])return 0;
 p->magic=SP_MAGIC;p->self=(unsigned)p;p->generation=generation;
 p->palette[0]=0;p->palette[1]=0x7bdf;p->palette[2]=0x2508;p->palette[3]=0x51a4;
 p->palette[4]=0x6f19;p->palette[5]=0x45ac;p->palette[6]=0x56b5;p->palette[7]=0x35ad;
 p->palette[8]=0x1cbb;p->palette[9]=0x63b8;p->palette[10]=0x7fff;p->palette[11]=0x564c;
 p->palette[12]=0x3adf;p->palette[13]=0x6b7a;p->palette[14]=0x28f6;p->palette[15]=0x5ef5;
 return 1;
}
/* Actual full native used extent, including GF/NNS prefixes and absorbed slack.
 * Reuse hblock/ledger; this is no second allocator or free policy. */
static unsigned sp_root(const UiHeap *h,unsigned p,unsigned need) {
 if(!hram(p,need) || !hblock(h->handle,p-16,need+16))return 0;
 unsigned found=0;for(unsigned i=0;i<16;++i)if(h->acquired[i]==p)++found;
 const unsigned *gf=(const unsigned *)(p-16);
 if(found!=1 || gf[0] || gf[1] || gf[2] || gf[3]!=38)return 0;
 return *(const unsigned *)(p-28)+16;
}
static unsigned sp_binding(SettingsPainter *p,const SettingsPaintRequest *r,const SettingsPaintRequest *origin) {
 UiFontLease *l=r->font;UiBg *b=r->bg;UiHeap *h=r->heap;
 if(!fspan((unsigned)l,sizeof(*l)) || ui_font_check(l)!=UI_FONT_READY || l->job ||
 !hlive(h) || h->generation!=r->generation || l->resource.reader->heap!=h ||
 !bg_owned(h,b,r->generation) || b->role || b->phase!=UI_BG_DISPLAY ||
 !bg_begin_allowed(h,b,r->generation,r->index) || !fspan((unsigned)b,sizeof(*b)) ||
 !r->version || r->version<=b->version[0] || r->version<=b->version[1])return 0;
 const SettingsRenderCatalog *c=r->catalog;const SettingsRenderPlan *d=r->desired;
 if(!foutput(l,(unsigned)p,sizeof(*p)) || !foutput(l,(unsigned)b,sizeof(*b)) ||
 !foutput(l,(unsigned)c,sizeof(*c)) || !foutput(l,(unsigned)d,sizeof(*d)) ||
 !foutput(l,(unsigned)r->uir1_owner,20) || !foutput(l,(unsigned)r->pool_owner,20) ||
 !sr_catalog(c) || !sr_plan(d) || !d->identity || c->identity!=d->identity ||
 c->root!=(const void *)l->root || c->bytes!=l->bytes || c->directory!=48448 ||
 c->count!=((const unsigned *)l->root)[25] || c->widths!=(const unsigned char *)l->widths)return 0;
 const UiTextOwner *u=r->uir1_owner,*v=r->pool_owner;unsigned pool_extent;
 if(u->kind!=UI_TEXT_UIR1 || !fowner(l,u,0,1,UI_TEXT_SINGLE) ||
 v->kind!=UI_TEXT_BUFFER || !fowner(l,v,0,1,UI_TEXT_SINGLE) || !fbuffer(l,v,&pool_extent) ||
 v->epoch!=d->pool_epoch || d->pool_used>v->bytes)return 0;
 unsigned a[10],n[10],roots[7],sizes[7];
 a[0]=(unsigned)p;n[0]=sizeof(*p);a[1]=(unsigned)b;n[1]=sizeof(*b);
 a[2]=(unsigned)l;n[2]=sizeof(*l);a[3]=(unsigned)c;n[3]=sizeof(*c);
 a[4]=(unsigned)d;n[4]=sizeof(*d);a[5]=(unsigned)u;n[5]=20;
 a[6]=(unsigned)v;n[6]=20;a[7]=(unsigned)l->resource.reader;n[7]=sizeof(UiResourceReader);
 a[8]=(unsigned)h;n[8]=sizeof(*h);a[9]=(unsigned)origin;n[9]=sizeof(*origin);
 for(unsigned i=0;i<10;++i)for(unsigned j=0;j<i;++j)if(ro(a[i],n[i],a[j],n[j]))return 0;
 roots[0]=l->root;sizes[0]=l->bytes;
 for(unsigned i=0;i<5;++i){roots[i+1]=(unsigned)b->roots[i];sizes[i+1]=bg_size(i);}
 roots[6]=(unsigned)v->root;sizes[6]=v->bytes;
 for(unsigned i=0;i<7;++i) {
  unsigned bytes=sp_root(h,roots[i],sizes[i]);
  /* UIR1 intentionally contains this lease's installed glyph cache. Its
   * full native separation was checked before publication by acquire; current
   * fidentity pins that exact root/cache. Other roots must exclude the cache. */
  if(!bytes || (i && !fnative(l->manager,roots[i]-32,bytes)))return 0;
  sizes[i]=bytes;
  for(unsigned j=0;j<10;++j)if(ro(roots[i]-32,bytes,a[j],n[j]))return 0;
  for(unsigned j=0;j<i;++j)if(ro(roots[i]-32,bytes,roots[j]-32,sizes[j]))return 0;
 }
 return 1;
}
static unsigned sp_text(const SettingsPainter *p,const SettingsDrawOp *o,UiTextSlice *s) {
 if(o->kind==SETTINGS_DRAW_TEXT) {
  UiResourceSlice slice;
  if(!ui_res_text(&p->font->resource,o->id,&slice) || slice.bytes!=o->units*2)return 0;
  s->owner=p->uir1_owner;s->offset=(unsigned)slice.data-p->font->root;
 } else {s->owner=p->pool_owner;s->offset=o->offset;}
 s->units=o->units;s->policy=UI_TEXT_LINES;
 if(!s->units || s->offset>s->owner->bytes || s->units*2>s->owner->bytes-s->offset || (s->offset&1))return 0;
 if(o->kind!=SETTINGS_DRAW_TEXT && (s->units>128 || s->offset>p->desired->pool_used || s->units*2>p->desired->pool_used-s->offset))return 0;
 return 1;
}
static unsigned sp_text_kind(const SettingsDrawOp *o) {
 return o->kind==SETTINGS_DRAW_TEXT || o->kind==SETTINGS_DRAW_NUMBER || o->kind==SETTINGS_DRAW_PREVIEW;
}
/* Every native job owns one homogeneous16px cell. Geometry surrounds that
 * cell; no clipping/fake Window and no printer crossing a contour. */
static unsigned sp_background(const SettingsRenderPlan *d,const SettingsDrawOp *o) {
 if(o->y==4)return 3;if(o->y==20)return 13;
 if(o->flags&SETTINGS_DRAW_HEADING)return 2;
 if(o->flags&SETTINGS_DRAW_CHOSEN)return o->flags&SETTINGS_DRAW_DISABLED?13:3;
 if(o->flags&SETTINGS_DRAW_READONLY)return 13;
 if(o->flags&SETTINGS_DRAW_SELECTED)return 1;
 if(o->flags&SETTINGS_DRAW_DISABLED)return 13;
 if(o->row!=255 && (d->view==SETTINGS_ROOT || d->view==SETTINGS_SELECTOR || d->view==SETTINGS_SEARCH))return 3;
 return 1;
}
static unsigned sp_foreground(const SettingsRenderPlan *d,const SettingsDrawOp *o) {
 unsigned bg=sp_background(d,o);
 return o->flags&SETTINGS_DRAW_DISABLED?5:bg==2 || bg==3?10:2;
}
/* All runs share one semantic envelope, but each source is a bounded EOS slice.
 * Called for admission and for one run at replay; never mutates a live job. */
static unsigned sp_footer_run(const SettingsPainter *p,const SettingsDrawOp *o,unsigned run,
 UiTextSlice *slice,unsigned *x,unsigned *fg,unsigned *bg) {
 unsigned storage[7],variant,units,total,offset=o->offset,pos=0,at=0,advance=0;
 if(o->a>=12 || !sr_footer_descriptor(o->a,storage) ||
 !sr_footer_match(p->catalog,o->id,&variant,&units,&total))return 0;
 const unsigned char *d=(const unsigned char *)storage;
 if(o->b!=d[2] || o->id!=d[0] || o->units!=units || run>=o->b ||
 o->x!=4 || o->y!=156 || o->w!=232 || o->h!=16 || o->flags || o->row!=255 ||
 offset>p->desired->pool_used || units*2>p->desired->pool_used-offset ||
 offset>p->pool_owner->bytes || units*2>p->pool_owner->bytes-offset || (offset&1))return 0;
 /* Ambiguous equivalent layout variants are legal only if every boundary is
  * identical. sr_footer_match already rejected all distinct matches. */
 unsigned canonical[7];sr_footer_descriptor(variant,canonical);
 for(unsigned i=1;i<27;++i)if(((const unsigned char *)canonical)[i]!=d[i])return 0;
 const unsigned short *words=(const unsigned short *)((unsigned)p->pool_owner->root+offset);
 unsigned source_units;const unsigned char *source=sr_lookup(p->catalog,o->id,&source_units);
 if(!source)return 0;
 for(unsigned j=0;j<o->b;++j) {
  unsigned len=d[4+3*j],key=d[5+3*j],width=0;
  if(j==run){slice->owner=p->pool_owner;slice->offset=offset+at*2;slice->units=len+1;slice->policy=UI_TEXT_SINGLE;pos=total<=232?4+((232-total)>>1):240;
   *x=pos+advance+(key?5:0);*fg=key?2:10;*bg=key?1:2;}
  for(unsigned k=0;k<len;++k){unsigned g=words[at+k];if(g!=sr16(source+2*(d[3+3*j]+k)) || !g || g>509)return 0;width+=p->catalog->widths[g-1];}
  if(words[at+len]!=65535)return 0;
  advance+=width+(key?13:j+1<o->b?9:0);
  at+=len+1;
 }
 return at==units && *x<236;
}
static unsigned sp_admit(const SettingsPainter *p,const SettingsDrawOp *o) {
 if(o->reserved || (o->flags&~255u))return 0;
 if(o->kind==SETTINGS_DRAW_FRAME)return p->desired->view==SETTINGS_INFO && p->desired->frame==o->choice+1u &&
  o->choice<20 && o->x==0 && o->y==104 && o->w==240 && o->h==48;
 if(o->kind==SETTINGS_DRAW_FOOTER){UiTextSlice slice;unsigned x,fg,bg;
  if(!o->b || o->b>8)return 0;
  for(unsigned i=0;i<o->b;++i)if(!sp_footer_run(p,o,i,&slice,&x,&fg,&bg))return 0;
  return o->b>0 && o->b<=8;
 }
 if(sp_text_kind(o)) {
  if((o->flags&SETTINGS_DRAW_CHOSEN) && (o->x<3 || o->y<1 || o->x+o->w+4>240 || o->y+17>176))return 0;
  if((o->flags&SETTINGS_DRAW_HEADING) && o->y<2)return 0;
  UiTextSlice s;if(!sp_text(p,o,&s) || !sp_background(p->desired,o))return 0;
  if(o->h<16 || (o->h&15))return 0;
  const unsigned short *text=(const unsigned short *)((unsigned)s.owner->root+s.offset);
  unsigned x=0,lines=1;
  for(unsigned i=0;i<s.units;++i) {
   unsigned g=text[i];
   if(g==65535)return i+1==s.units && lines*16<=o->h;
   if(g==0xe000){if(++lines*16>o->h)return 0;x=0;}
   else {if(!g || g>509 || !p->catalog->widths[g-1] || p->catalog->widths[g-1]>o->w-x)return 0;x+=p->catalog->widths[g-1];}
  }return 0;
 }
 if(o->kind==SETTINGS_DRAW_BAND)return o->h==20 && o->w>=3;
 if(o->kind==SETTINGS_DRAW_LEFT || o->kind==SETTINGS_DRAW_RIGHT)return o->w==5 && o->h==7;
 if(o->kind==SETTINGS_DRAW_CHOICE)return o->w>=8 && o->h==18;
 if(o->kind==SETTINGS_DRAW_ACTION)return o->w==6 && o->h==8;
 if(o->kind==SETTINGS_DRAW_LOCK)return o->w==6 && o->h==8;
 return 0;
}
SettingsPaintStatus settings_paint_begin(SettingsPainter *p,const SettingsPaintRequest *input) {
 if(!sp_record(p) || (p->phase!=SP_IDLE && p->phase!=SP_PREPARED) ||
 !rr((unsigned)input,sizeof(*input)) || ro((unsigned)p,sizeof(*p),(unsigned)input,sizeof(*input)))return SETTINGS_PAINT_REFUSED;
 SettingsPaintRequest r;fcopy(&r,input,sizeof(r));
 if(r.generation!=p->generation || !sp_binding(p,&r,input))return SETTINGS_PAINT_REFUSED;
 p->heap=r.heap;p->bg=r.bg;p->font=r.font;p->catalog=r.catalog;p->desired=r.desired;
 p->uir1_owner=r.uir1_owner;p->pool_owner=r.pool_owner;p->index=r.index;p->version=r.version;
 p->initial_rows=p->paint_rows=p->touched_rows=p->row_cursor=p->op_cursor=p->upload_cursor=0;
 p->full=p->replay_stage=p->error=p->reserved=0;p->phase=SP_ADMIT;
 return SETTINGS_PAINT_MORE;
}
static SettingsPaintStatus sp_bad(SettingsPainter *p,unsigned acquired,unsigned error) {
 p->error=error;
 if(acquired){p->phase=SP_FAILED;return SETTINGS_PAINT_FAILED;}
 p->phase=SP_IDLE;sp_unbind(p);return SETTINGS_PAINT_REFUSED;
}
static unsigned sp_current(const SettingsPainter *p) {
 return p->bg && p->heap && p->font && p->desired && p->uir1_owner && p->pool_owner &&
 p->index<2 && p->desired->identity==p->catalog->identity && p->desired->pool_epoch==p->pool_owner->epoch &&
 p->uir1_owner->live==1 && p->uir1_owner->kind==UI_TEXT_UIR1 && p->uir1_owner->root==(void *)p->font->root &&
 p->uir1_owner->bytes==p->font->bytes && p->pool_owner->live==1 && p->pool_owner->kind==UI_TEXT_BUFFER;
}
static void sp_pixel(UiNativeWindow16 *w,unsigned x,unsigned y,unsigned color) {
 unsigned off=((y>>3)*30+(x>>3))*32+(y&7)*4+((x&7)>>1),shift=(x&1)*4;
 unsigned char *p=(unsigned char *)w->pixels+off;
 *p=(unsigned char)((*p&~(15u<<shift))|(color<<shift));
}
static unsigned sp_abs(unsigned a,unsigned b){return a>b?a-b:b-a;}
static void sp_rect(SettingsPainter *p,unsigned x,unsigned y,unsigned width,unsigned height,unsigned fill,unsigned edge,unsigned mask) {
 UiNativeWindow16 *w=&p->bg->windows[p->index];unsigned char *pixels=w->pixels;
 for(unsigned yy=0;yy<height;++yy)if(mask&(1u<<((y+yy)>>3))) {
  unsigned py=y+yy,xx=0,solid=edge && (!yy || yy+1==height)?edge:fill;
  if(x&1){sp_pixel(w,x,py,edge?edge:solid);xx=1;}
  for(;xx+1<width;xx+=2){unsigned px=x+xx,lo=edge && !xx?edge:solid,hi=edge && xx+2==width?edge:solid;
   pixels[((py>>3)*30+(px>>3))*32+(py&7)*4+((px&7)>>1)]=(unsigned char)(lo|(hi<<4));}
  if(xx<width)sp_pixel(w,x+xx,py,edge?edge:solid);
 }
}
/* Native letter stays unscaled at x+5. The16px envelope includes its
 * clipped gray contour and one bottom shadow row. Reapply only the contour
 * after native printing: its16px cell may replace background at top/bottom. */
static void sp_cap(SettingsPainter *p,unsigned x,unsigned y,unsigned width,unsigned mask,unsigned surface) {
 UiNativeWindow16 *w=&p->bg->windows[p->index];
 for(unsigned yy=0;yy<16;++yy)if(mask&(1u<<((y+yy)>>3)))for(unsigned xx=0;xx<width;++xx) {
  unsigned color=1;
  if(yy==15)color=xx>=3 && xx+1<width?7:2;
  else if(!yy || yy==14)color=xx>=2 && xx+2<width?6:2;
  else if(yy==1 || yy==13)color=!xx || xx+1==width?2:xx==1 || xx+2==width?6:1;
  else if(!xx || xx+1==width)color=6;
  if(surface || color!=1)sp_pixel(w,x+xx,y+yy,color);
 }
}
static void sp_chrome(SettingsPainter *p,unsigned row) {
 const SettingsRenderPlan *d=p->desired;unsigned mask=1u<<row,seen=0;
 /* One clipped8px strip. No full-panel semantic operation/dirty closure. */
 for(unsigned y=row*8;y<row*8+8;++y) {
  unsigned outer=(!y || y==175)?2:3,inner=outer,left,right;
  if(y>=4 && y<172) {
   inner=y<20?3:y<36?13:y>=156?2:1;
   if(y>=36 && y<156 && (d->view==SETTINGS_ROOT || d->view==SETTINGS_SELECTOR || d->view==SETTINGS_SEARCH))inner=d->view==SETTINGS_SEARCH && y>=96?13:3;
  }
  left=2|outer*0x1110u|inner*0x11110000u;
  right=0x20000000u|outer*0x01110000u|inner*0x1111u;
  if(y==2){inner=4;left=0x44444432;right=0x23444444;}
  /* One aligned word is one eight-pixel tile scanline. The two edge
   * tiles retain their exact border nibbles; inner tiles are homogeneous. */
  if(d->frame && y>=104 && y<152){inner=1;left=right=0x11111111;}
  unsigned *line=(unsigned *)((unsigned char *)p->bg->windows[p->index].pixels+(y>>3)*960+(y&7)*4);
  line[0]=left;
  for(unsigned tile=1;tile<29;++tile)line[tile*8]=inner*0x11111111u;
  line[29*8]=right;
 }
 for(unsigned i=0;i<d->count;++i) {
  const SettingsDrawOp *o=&d->ops[i];if(!(sr_rows(o)&mask))continue;
  if(o->row!=255 && o->y>=36 && o->y<156 && (d->view<=1 || d->view==3)) {
   unsigned sy=o->y<56?36:o->y<76?56:o->y<96?76:o->y<116?96:o->y<136?116:136;
   unsigned slot=sy==36?0:sy==56?1:sy==76?2:sy==96?3:sy==116?4:5;
   if(seen&(1u<<slot))continue;seen|=1u<<slot;
   unsigned fill=o->flags&SETTINGS_DRAW_READONLY?13:o->flags&SETTINGS_DRAW_SELECTED?1:o->flags&SETTINGS_DRAW_DISABLED?13:3;
   sp_rect(p,4,sy,232,20,fill,0,mask);
   sp_rect(p,6,sy+19,228,1,11,0,mask);
  }
 }
 /* Surface ordering is independent of glyph order: selected/group/chosen
  * interiors are fully prepared before the first native printer borrows it. */
 for(unsigned i=0;i<d->count;++i) {
  const SettingsDrawOp *o=&d->ops[i];
  if((o->flags&SETTINGS_DRAW_HEADING) && o->kind==SETTINGS_DRAW_TEXT){
   if(d->view<=1)sp_rect(p,4,o->y-2,232,20,2,0,mask);
   else sp_rect(p,o->x,o->y,o->w,o->h,2,0,mask);
  }
  if(o->kind==SETTINGS_DRAW_BAND)sp_rect(p,o->x,o->y,o->w,o->h,1,8,mask);
  if(o->kind==SETTINGS_DRAW_TEXT && (o->flags&SETTINGS_DRAW_CHOSEN))sp_rect(p,o->x-3,o->y-1,o->w+7,18,o->flags&4?13:3,o->flags&4?5:4,mask);
 }
}
static void sp_geometry(SettingsPainter *p,const SettingsDrawOp *o) {
 UiNativeWindow16 *w=&p->bg->windows[p->index];
 if(o->kind==SETTINGS_DRAW_CHOICE)return; /* Tile surrounds its native text. */
 if(o->kind==SETTINGS_DRAW_BAND) {
  /* Only the five-by-seven pointer has ink. Do not scan all 232x20 band
   * pixels to discover that the rest has already been drawn by chrome. */
  if(o->w==232)for(unsigned y=6;y<=12;++y)if(p->paint_rows&(1u<<((o->y+y)>>3)))
   for(unsigned x=4;x<=8;++x)if(sp_abs(y,9)<=8-x)sp_pixel(w,o->x+x,o->y+y,2);
  return;
 }
 for(unsigned y=0;y<o->h;++y)for(unsigned x=0;x<o->w;++x) {
  unsigned color=0,d;
  if(!(p->paint_rows&(1u<<((o->y+y)>>3))))continue;
  switch(o->kind) {
  case SETTINGS_DRAW_LEFT:case SETTINGS_DRAW_RIGHT:
   if(!(o->flags&SETTINGS_DRAW_SELECTED))break;
   d=o->kind==SETTINGS_DRAW_RIGHT?o->w-1-x:x;
   if(d<=4 && sp_abs(y,3)<=d && (!(o->flags&4) || d==4 || sp_abs(y,3)==d))color=o->flags&4?5:2;
   break;
  case SETTINGS_DRAW_ACTION:
   if(o->flags&4){if(y>=3 || (y==0 && x>=1 && x<=4) || (y<4 && (x==1 || x==4)))color=5;}
   else if(x<5 && y<7 && sp_abs(y,3)<=4-x)color=o->flags&1?2:10;
   break;
  case SETTINGS_DRAW_LOCK:
   if(y>=3 || (y==0 && x>=1 && x<=4) || (y<4 && (x==1 || x==4)))color=5;
   break;
  default:break;
  }
  if(color)sp_pixel(w,o->x+x,o->y+y,color);
 }
}
SettingsPaintStatus settings_paint_step(SettingsPainter *p,unsigned budget) {
 if(!sp_record(p) || !budget || budget>8)return SETTINGS_PAINT_REFUSED;
 if(p->phase==SP_PREPARED)return SETTINGS_PAINT_PREPARED;
 if(p->phase==SP_FAILED)return SETTINGS_PAINT_FAILED;
 if(p->phase==SP_HOLD)return SETTINGS_PAINT_HOLD;
 if(p->phase==SP_IDLE)return SETTINGS_PAINT_UNCHANGED;
 if(!rio())return SETTINGS_PAINT_MORE;
 unsigned acquired=p->phase>=SP_CLEAR;
 UiFontStatus fs=ui_font_check(p->font);
 if(fs==UI_FONT_DEFER)return SETTINGS_PAINT_MORE;
 if(fs==UI_FONT_HOLD){p->phase=SP_HOLD;return SETTINGS_PAINT_HOLD;}
 if(fs!=UI_FONT_READY || !sp_current(p))return sp_bad(p,acquired,1);
 if(acquired && (!bg_mutable(p->heap,p->bg,p->generation) || p->bg->preparing!=p->index))return sp_bad(p,1,2);
 const SettingsRenderPlan *d=p->desired;const SettingsDrawOp *o;
 switch(p->phase) {
 case SP_ADMIT:
  /* Admit the finite immutable plan before acquiring the hidden buffer. */
  while(p->op_cursor<d->count) {
   const SettingsDrawOp *admit=&d->ops[p->op_cursor++];
   if(!sp_admit(p,admit))return sp_bad(p,0,3);
   if(admit->kind==SETTINGS_DRAW_FRAME)++p->reserved;
  }
  if(p->reserved!=(d->frame?1u:0u))return sp_bad(p,0,16);
  /* Compare against the presented plan. A new hidden buffer can inherit its
   * unframed pixels, avoiding a full redraw just to move the selection. */
  if(p->bg->front<2) {
   SettingsPaintHistory *front=&p->history[p->bg->front];unsigned full;
   if(front->valid && front->version==p->bg->version[p->bg->front]) {
    unsigned rows=settings_render_dirty(&front->plan,d,front->invalid_rows,&full);
    if(!rows && !full){p->phase=SP_IDLE;sp_unbind(p);return SETTINGS_PAINT_UNCHANGED;}
    if(!full && !d->frame && !front->plan.frame) {
     p->initial_rows=p->paint_rows=rows;p->full=0;p->reserved|=2;
     p->op_cursor=0;p->phase=SP_CLOSE;return SETTINGS_PAINT_MORE;
    }
   }
  }
  {SettingsPaintHistory *h=&p->history[p->index];
   p->initial_rows=settings_render_dirty(h->valid && h->version==p->bg->version[p->index]?&h->plan:0,d,h->invalid_rows,&p->full);
   if(!p->initial_rows){p->initial_rows=SETTINGS_RENDER_FULL;p->full=1;}
   p->paint_rows=p->initial_rows;p->op_cursor=0;p->phase=SP_CLOSE;}
  return SETTINGS_PAINT_MORE;
 case SP_CLOSE:
  {unsigned mask=p->paint_rows;
   for(unsigned i=0;i<d->count;++i)if(sr_rows(&d->ops[i])&p->paint_rows)p->paint_rows|=sr_rows(&d->ops[i]);
   if(mask==p->paint_rows){p->phase=SP_ACQUIRE;return SETTINGS_PAINT_MORE;}
   if(++p->replay_stage>=22)return sp_bad(p,0,4);
  }return SETTINGS_PAINT_MORE;
 case SP_ACQUIRE:
  {SettingsPaintHistory *h=&p->history[p->index];unsigned window;
   if(p->reserved&2)window=ui_bg_begin_copy(p->heap,p->bg,p->generation,p->index,p->paint_rows);
   else if(p->full)window=ui_bg_begin(p->heap,p->bg,p->generation,p->index);
   else window=ui_bg_begin_retained(p->heap,p->bg,p->generation,p->index,h->version,p->paint_rows);
   if(!window)return sp_bad(p,0,5);
   h->valid=0;h->invalid_rows|=p->paint_rows;
   p->phase=SP_CLEAR;p->row_cursor=0;
  }return SETTINGS_PAINT_MORE;
 case SP_CLEAR:
  if(!p->row_cursor) {
   if(!ui_bg_invalidate_rows(p->heap,p->bg,p->generation,p->paint_rows))return sp_bad(p,1,6);
   p->touched_rows|=p->paint_rows;
  }
  for(unsigned count=0;p->row_cursor<22 && count<4;++p->row_cursor)
   if(p->paint_rows&(1u<<p->row_cursor)){sp_chrome(p,p->row_cursor);++count;}
  if(p->row_cursor==22){p->phase=SP_REPLAY;p->op_cursor=0;p->replay_stage=0;}
  return SETTINGS_PAINT_MORE;
 case SP_REPLAY:
  while(p->op_cursor<d->count && (!(sr_rows(&d->ops[p->op_cursor])&p->paint_rows) ||
        d->ops[p->op_cursor].kind==SETTINGS_DRAW_FRAME))++p->op_cursor;
  if(p->op_cursor==d->count){p->phase=SP_DECORATE;return SETTINGS_PAINT_MORE;}
  o=&d->ops[p->op_cursor];
  if(sp_text_kind(o) || o->kind==SETTINGS_DRAW_FOOTER) {
   UiFontRequest r;fzero(&r,sizeof(r));
   r.x=o->x;r.y=o->y;r.max_lines=o->h>>4;
   if(o->kind==SETTINGS_DRAW_FOOTER){unsigned x,fg,bg;
    if(!sp_footer_run(p,o,p->replay_stage,&r.text,&x,&fg,&bg))return sp_bad(p,1,7);
    r.x=x;r.fg=fg;r.bg=bg;
    if(bg!=2){unsigned width=0;const unsigned short *q=(const unsigned short *)((unsigned)r.text.owner->root+r.text.offset);
     for(unsigned i=0;i+1<r.text.units;++i)width+=p->catalog->widths[q[i]-1];
     sp_cap(p,x-5,o->y,width+10,p->paint_rows,1);}
   } else {if(!sp_text(p,o,&r.text))return sp_bad(p,1,7);r.fg=sp_foreground(d,o);r.bg=sp_background(d,o);}
   r.shadow=r.bg;
   r.window=&p->bg->windows[p->index];r.front=p->bg->windows[1-p->index].pixels;r.pixel_bytes=21120;
   r.scratch=&p->scratch;
   fs=fbegin_checked(p->font,&p->job,&r);
   if(fs==UI_FONT_DEFER)return SETTINGS_PAINT_MORE;
   if(fs==UI_FONT_HOLD){p->phase=SP_HOLD;return SETTINGS_PAINT_HOLD;}
   if(fs!=UI_FONT_ACTIVE)return sp_bad(p,1,8);
   p->phase=SP_FONT;
  } else {sp_geometry(p,o);++p->op_cursor;}
  return SETTINGS_PAINT_MORE;
 case SP_FONT:
  fs=fstep_checked(p->font,&p->job,budget);
  if(fs==UI_FONT_ACTIVE || fs==UI_FONT_DEFER)return SETTINGS_PAINT_MORE;
  if(fs==UI_FONT_HOLD){p->phase=SP_HOLD;return SETTINGS_PAINT_HOLD;}
  if(fs!=UI_FONT_DONE)return sp_bad(p,1,9);
  o=&d->ops[p->op_cursor];
  if(o->kind==SETTINGS_DRAW_FOOTER){UiTextSlice slice;unsigned x,fg,bg;
   if(!sp_footer_run(p,o,p->replay_stage,&slice,&x,&fg,&bg))return sp_bad(p,1,7);
   if(bg==1){unsigned width=0;const unsigned short *q=(const unsigned short *)((unsigned)slice.owner->root+slice.offset);
    for(unsigned i=0;i+1<slice.units;++i)width+=p->catalog->widths[q[i]-1];
    sp_cap(p,x-5,o->y,width+10,p->paint_rows,0);}
  }
  if(d->ops[p->op_cursor].kind!=SETTINGS_DRAW_FOOTER || ++p->replay_stage==d->ops[p->op_cursor].b){++p->op_cursor;p->replay_stage=0;}
  p->phase=SP_REPLAY;return SETTINGS_PAINT_MORE;
 case SP_DECORATE:
  if(p->font->job)return sp_bad(p,1,10);
  if(p->full) {
   unsigned ok;
   if(d->frame) {
    UiResourceSlice tiles,palette;UiBgFrame frame;
    if(!ui_res_frame(&p->font->resource,d->frame-1,0,&tiles) || !ui_res_frame(&p->font->resource,d->frame-1,1,&palette))return sp_bad(p,1,11);
    frame.x=3;frame.y=15;frame.width=25;frame.height=4;
    frame.tiles=tiles.data;frame.tileBytes=tiles.bytes;frame.palette=palette.data;frame.paletteBytes=palette.bytes;
    ok=ui_bg_frame(p->heap,p->bg,p->generation,&frame);
   } else ok=ui_bg_unframed(p->heap,p->bg,p->generation);
   if(!ok)return sp_bad(p,1,12);
  }
  p->phase=SP_UPLOAD;p->upload_cursor=0;return SETTINGS_PAINT_MORE;
 case SP_UPLOAD:
  while(p->upload_cursor<22 && !(p->paint_rows&(1u<<p->upload_cursor)))++p->upload_cursor;
  if(p->upload_cursor<22) {
   UiBgRows rows;rows.first=p->upload_cursor;rows.count=1;
   while(rows.first+rows.count<22 && (p->paint_rows&(1u<<(rows.first+rows.count))))++rows.count;
   if(!ui_bg_rows(p->heap,p->bg,p->generation,&rows))return sp_bad(p,1,13);
   p->upload_cursor+=rows.count;
  } else p->phase=SP_READY;
  return SETTINGS_PAINT_MORE;
 case SP_READY:
  if(p->font->job || p->job.phase==UI_FONT_ACTIVE)return sp_bad(p,1,14);
  if(!ui_bg_ready(p->heap,p->bg,p->generation,p->version))return sp_bad(p,1,15);
  {SettingsPaintHistory *h=&p->history[p->index];
   fcopy(&h->plan,d,sizeof(*d));h->version=p->version;h->invalid_rows=0;h->valid=1;}
  p->phase=SP_PREPARED;sp_unbind(p);return SETTINGS_PAINT_PREPARED;
 default:return SETTINGS_PAINT_REFUSED;
 }
}
SettingsPaintStatus settings_paint_retire(SettingsPainter *p) {
 if(!sp_record(p))return SETTINGS_PAINT_REFUSED;
 if(p->phase==SP_IDLE || p->phase==SP_PREPARED){p->phase=SP_IDLE;sp_unbind(p);return SETTINGS_PAINT_UNCHANGED;}
 if(!rio())return SETTINGS_PAINT_MORE;
 if(p->font && p->font->job==&p->job) {
  UiFontStatus s=ui_font_cancel(p->font,&p->job);
  if(s==UI_FONT_DEFER)return SETTINGS_PAINT_MORE;
  if(s!=UI_FONT_CANCELLED){p->phase=SP_HOLD;return SETTINGS_PAINT_HOLD;}
 }
 if(p->font && p->font->state==UI_FONT_HOLD){p->phase=SP_HOLD;return SETTINGS_PAINT_HOLD;}
 /* Acquired preparations cannot be abandoned or reused. Parent must retire
  * the entire BG lifecycle/callback first; no implicit BG cancellation. */
 if(p->bg && p->bg->phase!=UI_BG_STORAGE &&
    (p->touched_rows || p->bg->preparing==p->index || p->phase==SP_HOLD)) {
  p->phase=SP_FAILED;return SETTINGS_PAINT_FAILED;
 }
 p->history[0].valid=p->history[1].valid=0;
 p->history[0].invalid_rows=p->history[1].invalid_rows=SETTINGS_RENDER_FULL;
 p->phase=SP_IDLE;sp_unbind(p);return SETTINGS_PAINT_UNCHANGED;
}
