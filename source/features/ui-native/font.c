/* Compose with accepted heap.c/resource.c. No mutable static state. */
#include "font.h"
#define FWORK 0x02111890u
#define FWORKPTR (*(volatile unsigned *)0x0211188C)
#define FMAN (*(volatile unsigned *)(FWORK+0x9C))
#define FREF (*(volatile unsigned char *)(FWORK+0xB4))
#define FRENDER ((unsigned (*)(UiFontPrinter52 *))0x02020359)
#define FGENERATE ((void (*)(unsigned,unsigned,unsigned))0x0202036D)
_Static_assert(sizeof(UiFontPrinter52)==52,"native printer");
_Static_assert(__builtin_offsetof(UiFontPrinter52,state)==40,"printer state");
_Static_assert(__builtin_offsetof(UiFontPrinter52,callback)==28,"printer callback");
_Static_assert(__builtin_offsetof(UiFontPrinter52,unk30)==48,"printer pointer");
_Static_assert(sizeof(UiFontScratch)==652,"scratch");
_Static_assert(sizeof(UiTextOwner)==20 && sizeof(UiTextSlice)==16,"text descriptors");
_Static_assert(sizeof(UiFontLease)==88 && sizeof(UiFontPrintJob)==152,"persistent records");
_Static_assert(__builtin_offsetof(UiFontLease,resource)==8 && __builtin_offsetof(UiFontLease,job)==84,"lease token/job offsets");
_Static_assert(__builtin_offsetof(UiFontPrintJob,text)==52 && __builtin_offsetof(UiFontPrintJob,window)==80 &&
 __builtin_offsetof(UiFontPrintJob,owner)==96 && __builtin_offsetof(UiFontPrintJob,scratch)==124 &&
 __builtin_offsetof(UiFontPrintJob,expected_x)==136,"job persistent offsets");
_Static_assert(sizeof(UiFontRequest)==40,"copied request");
static void fcopy(void *d,const void *s,unsigned n) {
 unsigned char *a=d;const unsigned char *b=s;while(n--)*a++=*b++;
}
static void fzero(void *d,unsigned n) {unsigned char *a=d;while(n--)*a++=0;}
static unsigned fequal(const void *a,const void *b,unsigned n) {
 const unsigned char *p=a,*q=b;while(n--)if(*p++!=*q++)return 0;return 1;
}
static unsigned fspan(unsigned p,unsigned n) {return !(p&3)&&hext(p,n,HNATIVE_LO,HNATIVE_HI);}
static unsigned fobj(unsigned p,unsigned n) {return fspan(p,n)&&rwritable(p,n);}
static unsigned fmeta(unsigned m) {
 if(FWORKPTR!=FWORK || FMAN!=m || !fspan(m,124))return 0;
 const unsigned *v=(const unsigned *)m;
 return v[2]==3 && v[3]==64 && fspan(v[21],84) && !v[22] && v[23]==16 &&
 v[24]==0x7F50 && v[25]==509 && v[26]==0x02021010 && !v[27] &&
 v[28]==0x020262B5 && fspan(v[29],509) && v[30] &&
 !ro(m-32,156,v[29]-32,541) && !ro(m-32,156,v[21]-32,116) &&
 !ro(v[21]-32,116,v[29]-32,541);
}
static unsigned fnative(unsigned m,unsigned p,unsigned n) {
 if(!fmeta(m))return 0;
 const unsigned *v=(const unsigned *)m;
 if(ro(p,n,m-32,156)||ro(p,n,v[21]-32,116)||ro(p,n,v[29]-32,541))return 0;
 if(v[4] && (!fspan(v[4],32576)||ro(p,n,v[4]-32,32608)))return 0;
 for(unsigned i=1;i<6;++i) {
  unsigned other=((volatile unsigned *)(FWORK+0x9C))[i];
  if(other) {
   if(!fspan(other,124)||ro(p,n,other-32,156))return 0;
   const unsigned *a=(const unsigned *)other;
   if(!a[25]||a[25]>65535||!a[3]||a[3]>64)return 0;
   if(a[21]&&(!fspan(a[21],84)||ro(p,n,a[21]-32,116)))return 0;
   if(a[29]&&(!fspan(a[29],a[25])||ro(p,n,a[29]-32,a[25]+32)))return 0;
   if(a[4]&&(!fspan(a[4],a[25]*a[3])||ro(p,n,a[4]-32,a[25]*a[3]+32)))return 0;
  }
 }
 return 1;
}
static unsigned froot(const UiFontLease *l) {
 return rlease(&l->resource) && l->resource.font==1 &&
 l->resource.reader->phase==UI_RES_READY && !l->resource.reader->cancelled &&
 l->resource.reader->root==l->root && l->resource.reader->config.word[7]==l->bytes;
}
static unsigned fidentity(const UiFontLease *l) {
 if(!froot(l)||!fmeta(l->manager)||FREF<2||FREF>127)return 0;
 const unsigned *m=(const unsigned *)l->manager;
 if(m[0] || m[1]!=0x02026069 || m[4]!=l->cache || m[21]!=l->narc ||
 m[29]!=l->widths || m[30]!=l->gmif)return 0;
 return !l->cache_owner || (fspan((unsigned)l->cache_owner,sizeof(*l->cache_owner)) &&
 fequal(l->cache_owner,&l->cache_snapshot,sizeof(*l->cache_owner)));
}
static unsigned fwidths(unsigned p) {
 return (rcrc(~0u,(const unsigned char *)p,509)^~0u)==0x885AB7FC;
}
static unsigned foutput(const UiFontLease *l,unsigned p,unsigned n) {
 /* rout already performs rwritable, including a fresh complete heap census.
  * Retain fspan's stricter native-RAM domain without running that census twice. */
 return fspan(p,n)&&rout(l->resource.reader,p,n)&&fnative(l->manager,p,n)&&
 !ro(p,n,(unsigned)l,sizeof(*l)) &&
 (!l->cache_owner||!ro(p,n,(unsigned)l->cache_owner,sizeof(*l->cache_owner)));
}
static UiFontStatus fhold(UiFontLease *l) {l->state=UI_FONT_HOLD;return UI_FONT_HOLD;}
/* Acquisition has not published any native reference or tuple. A refused
 * token drop must retain the authoritative token and a sticky ownership HOLD. */
static UiFontStatus funpublished(UiFontLease *l) {
 if(ui_res_drop(&l->resource))return UI_FONT_REFUSE;
 l->owned=0;l->manager=0;l->job=0;return fhold(l);
}
UiFontStatus ui_font_acquire(UiFontLease *l,UiResourceReader *r,const UiFontCacheOwner *o) {
 /* This must precede even CRC/admission, and never unmasks the caller. */
 if(!rio())return UI_FONT_DEFER;
 unsigned m=FMAN;
 if(!rvalid(r)||r->phase!=UI_RES_READY||r->cancelled||!rroot(r)||
 !fobj((unsigned)l,sizeof(*l))||!rout(r,(unsigned)l,sizeof(*l))||
 !fnative(m,(unsigned)l,sizeof(*l))||l->state||l->resource.reader||l->resource.generation||l->resource.font)return UI_FONT_REFUSE;
 const unsigned *v=(const unsigned *)m;
 unsigned mode=v[0],fn=v[1],cache=v[4],width=v[29],narc=v[21],gmif=v[30];
 unsigned root=r->root,bytes=r->config.word[7];
 UiFontCacheOwner owner_snapshot;fzero(&owner_snapshot,sizeof(owner_snapshot));
 if(FREF<1||FREF>126||!fwidths(width))return UI_FONT_REFUSE;
 if(mode==1 && fn==0x02026111 && !cache) {if(o)return UI_FONT_REFUSE;}
 else if(mode==0 && fn==0x02026069 && cache) {
  if(!o||!fobj((unsigned)o,sizeof(*o))||!rout(r,(unsigned)o,sizeof(*o))||
   !fnative(m,(unsigned)o,sizeof(*o))||ro((unsigned)o,sizeof(*o),(unsigned)l,sizeof(*l))||
   o->cache!=(const void *)cache||o->bytes!=32576||!o->epoch||o->live!=1||!o->owner_id||
   ro(cache-32,32608,root-32,bytes+32))return UI_FONT_REFUSE;
  fcopy(&owner_snapshot,o,sizeof(*o));
  if((rcrc(~0u,(const unsigned char *)cache,32576)^~0u)!=0xA8CD6456)return UI_FONT_REFUSE;
 } else return UI_FONT_REFUSE;
 if(!fnative(m,r->root-32,r->config.word[7]+32))return UI_FONT_REFUSE;
 if(!ui_res_acquire(r,&l->resource,1))return UI_FONT_REFUSE;
 UiResourceSlice glyph;
 if(!ui_res_glyphs(&l->resource,&glyph)||glyph.data!=(void *)(r->root+12288)||glyph.bytes!=32576) {
  return funpublished(l);
 }
 unsigned irq=HDISABLE(),ok=fmeta(m)&&v[0]==mode&&v[1]==fn&&v[4]==cache&&
 v[29]==width&&v[21]==narc&&v[30]==gmif&&FREF>=1&&FREF<=126&&
 rlease(&l->resource)&&r->phase==UI_RES_READY&&!r->cancelled&&r->root==root&&r->config.word[7]==bytes&&
 (!o||fequal(o,&owner_snapshot,sizeof(*o)));
 if(ok) {
  l->owned=mode==1;l->root=r->root;l->bytes=r->config.word[7];l->manager=m;
  l->widths=width;l->narc=narc;l->gmif=gmif;l->prior_mode=mode;l->prior_fn=fn;l->prior_cache=cache;
  l->cache_owner=o;if(o)fcopy(&l->cache_snapshot,o,sizeof(*o));else fzero(&l->cache_snapshot,sizeof(*o));
  l->cache=mode==1?(unsigned)glyph.data:cache;l->job=0;
  ++FREF;
  if(l->owned){((volatile unsigned *)m)[4]=l->cache;((volatile unsigned *)m)[1]=0x02026069;((volatile unsigned *)m)[0]=0;}
  l->state=UI_FONT_READY;
 }
 HRESTORE(irq);
 if(!ok)return funpublished(l);
 return UI_FONT_READY;
}
UiFontStatus ui_font_check(UiFontLease *l) {
 if(!rio())return UI_FONT_DEFER;
 if(!fspan((unsigned)l,sizeof(*l)))return UI_FONT_REFUSE;
 if(l->state==UI_FONT_HOLD)return UI_FONT_HOLD;
 if(l->state!=UI_FONT_READY)return UI_FONT_REFUSE;
 if(!fidentity(l)||!rroot(l->resource.reader)||!fwidths(l->widths))return fhold(l);
 return UI_FONT_READY;
}
static unsigned fwindow(const UiNativeWindow16 *w,unsigned bytes) {
 if(!fspan((unsigned)w,sizeof(*w))||!fspan((unsigned)w->bg,360)||w->bgId>=8||
 !w->width||!w->height||w->palette>15||(w->baseTile&0x8000)||
 bytes!=(unsigned)w->width*w->height*32||!fspan((unsigned)w->pixels,bytes))return 0;
 const UiNativeBackground44 *b=&w->bg->bgs[w->bgId];
 return w->bg->heapID==38&&!b->mode&&!b->colorMode&&b->tileSize==32&&b->screenSize==1;
}
/* A BUFFER root is a dedicated current checked-heap allocation, not an
 * inline app field or an SGG1 claim. Check the whole native allocation so an
 * understated public extent cannot hide live app records in its trailing area.
 * Native NNS may consume a small unsplittable tail; payload need only fit. */
static unsigned fbuffer(const UiFontLease *l,const UiTextOwner *o,unsigned *extent) {
 unsigned p=(unsigned)o->root,n=o->bytes;const UiHeap *h=l->resource.reader->heap;
 if(n<4||n>4096||(n&3)||!hlive(h)||!hblock(h->handle,p-16,n+16))return 0;
 unsigned found=0;for(unsigned i=0;i<16;++i)if(h->acquired[i]==p)++found;
 const unsigned *gf=(const unsigned *)(p-16);
 if(found!=1||gf[0]||gf[1]||gf[2]||gf[3]!=38)return 0;
 unsigned full=*(const unsigned *)(p-28)+16;
 if(!foutput(l,p-32,full))return 0;
 *extent=full;return 1;
}
static unsigned fowner(const UiFontLease *l,const UiTextOwner *o,unsigned off,unsigned units,unsigned policy) {
 if(!foutput(l,(unsigned)o,sizeof(*o))||o->live!=1||!o->epoch||!units||units>2048||policy>1||
 !fspan((unsigned)o->root,o->bytes)||off>o->bytes||units*2>o->bytes-off||(off&1))return 0;
 if(o->kind==UI_TEXT_UIR1) {
  if((unsigned)o->root!=l->root||o->bytes!=l->bytes)return 0;
 } else if(o->kind==UI_TEXT_SGG1) {
  if(o->bytes>0x20000||units>128||ro((unsigned)o->root-32,o->bytes+32,l->root-32,l->bytes+32))return 0;
 } else if(o->kind==UI_TEXT_BUFFER) {
  if(units>128)return 0;
 } else return 0;
 return !ro((unsigned)o,sizeof(*o),(unsigned)o->root-32,o->bytes+32)&&
 !ro((unsigned)o->root+off,units*2,l->root+12288,32576)&&
 fnative(l->manager,(unsigned)o->root+off,units*2);
}
static unsigned ffit(const unsigned short *text,unsigned units,const unsigned char *widths,
 unsigned x,unsigned y,unsigned w,unsigned h,unsigned cap,unsigned policy,unsigned *lines) {
 if(!cap||cap>11||x>w||y>h||16>h-y)return 0;
 unsigned xx=x,count=1;
 for(unsigned i=0;i<units;++i) {
  unsigned c=text[i];
  if(i+1==units){if(c!=0xFFFF)return 0;*lines=count;return 1;}
  if(c==0xE000){if(!policy||++count>cap||16*count>h-y)return 0;xx=x;}
  else {if(c<1||c>509||widths[c-1]>w-xx)return 0;xx+=widths[c-1];}
 }
 return 0;
}
/* Validate every writable/read-only participant pair before job publication.
 * Known roots include their native+GF 32-byte prefix. Window pixels are caller
 * allocations too; their descriptors cannot occupy either allocation header. */
static unsigned fparts(const UiFontLease *l,UiFontPrintJob *j,const UiFontRequest *r) {
 unsigned jp=(unsigned)j,sp=(unsigned)r->scratch,wp=(unsigned)r->window;
 const UiTextOwner *o=r->text.owner;
 if(!fowner(l,o,r->text.offset,r->text.units,r->text.policy)||!fwindow(r->window,r->pixel_bytes)||
 !fspan((unsigned)r->front,r->pixel_bytes))return 0;
 unsigned p=(unsigned)r->window->pixels,q=(unsigned)r->front,n=r->pixel_bytes;
 /* These five destinations form one synchronous admission. Repeat all range,
  * native-font and separation checks, with one fresh topology census. There
  * are no native calls or writes and no cached result across API calls. */
 unsigned dst[5]={jp,sp,wp,p,q};volatile unsigned extent[5];
 extent[0]=sizeof(*j);extent[1]=652;extent[2]=16;extent[3]=n;extent[4]=n;
 if(!hmeta())return 0;
 for(unsigned i=0;i<5;++i)if(!fspan(dst[i],extent[i]) || !rwrite_range(dst[i],extent[i]) ||
    !rseparate(l->resource.reader,dst[i],extent[i]) || !fnative(l->manager,dst[i],extent[i]) ||
    ro(dst[i],extent[i],(unsigned)l,sizeof(*l)) ||
    (l->cache_owner && ro(dst[i],extent[i],(unsigned)l->cache_owner,sizeof(*l->cache_owner))))return 0;
 unsigned root_bytes=o->bytes+32;
 if(o->kind==UI_TEXT_BUFFER&&!fbuffer(l,o,&root_bytes))return 0;
 if(ro(p-32,n+32,q-32,n+32))return 0;
 unsigned starts[6]={jp,sp,wp,(unsigned)o,(unsigned)l,(unsigned)r->window->bg};
 volatile unsigned sizes[6];sizes[0]=sizeof(*j);sizes[1]=652;sizes[2]=16;
 sizes[3]=sizeof(*o);sizes[4]=sizeof(*l);sizes[5]=360;
 for(unsigned a=0;a<6;++a) {
  if(ro(starts[a],sizes[a],p-32,n+32)||ro(starts[a],sizes[a],q-32,n+32)||
   ro(starts[a],sizes[a],(unsigned)o->root-32,root_bytes))return 0;
  for(unsigned b=0;b<a;++b)if(ro(starts[a],sizes[a],starts[b],sizes[b]))return 0;
 }
 return !ro(p-32,n+32,(unsigned)o->root-32,root_bytes)&&
 !ro(q-32,n+32,(unsigned)o->root-32,root_bytes)&&
 (o->kind==UI_TEXT_UIR1 || fnative(l->manager,(unsigned)o->root-32,o->bytes+32));
}
/* Private synchronous continuations: painters have just run ui_font_check
 * and perform only owned pixel writes / pure admission before this point.
 * Public entry points always perform their own fresh complete check. */
static UiFontStatus fbegin_checked(UiFontLease *l,UiFontPrintJob *j,const UiFontRequest *input) {
 if(!rr((unsigned)input,sizeof(*input)))return UI_FONT_REFUSE;
 UiFontRequest request;fcopy(&request,input,sizeof(request));const UiFontRequest *r=&request;
 if(l->job||!rr((unsigned)r,sizeof(*r))||r->letter_spacing||r->line_spacing||
 r->fg>15||r->bg>15||r->shadow>15||!fparts(l,j,r)||j->phase==UI_FONT_ACTIVE)return UI_FONT_REFUSE;
 const UiTextOwner *o=r->text.owner;const unsigned short *text=(const unsigned short *)((unsigned)o->root+r->text.offset);
 unsigned lines;
 if(!ffit(text,r->text.units,(const unsigned char *)l->widths,r->x,r->y,r->window->width*8,r->window->height*8,r->max_lines,r->text.policy,&lines))return UI_FONT_REFUSE;
 fzero(j,sizeof(*j));j->text=text;j->units=r->text.units;j->lease=l;j->lines=1;j->cap=r->max_lines;
 j->owner=o;fcopy(&j->owner_snapshot,o,sizeof(*o));j->policy=r->text.policy;
 j->scratch=r->scratch;j->front=r->front;j->pixel_bytes=r->pixel_bytes;fcopy(&j->window,r->window,16);
 UiFontPrinter52 *p=&j->printer;p->current=text;p->window=r->window;p->x=r->x;p->y=r->y;
 p->current_x=r->x;p->current_y=r->y;j->expected_x=j->start_x=r->x;j->expected_y=j->start_y=r->y;p->fg=r->fg;p->bg=r->bg;p->shadow=r->shadow;
 p->unk1b=255;p->active=1;p->id=8;j->phase=UI_FONT_ACTIVE;l->job=j;
 return UI_FONT_ACTIVE;
}
UiFontStatus ui_font_begin(UiFontLease *l,UiFontPrintJob *j,const UiFontRequest *input) {
 UiFontStatus s=ui_font_check(l);return s==UI_FONT_READY?fbegin_checked(l,j,input):s;
}
static void fretire(UiFontLease *l,UiFontPrintJob *j,unsigned phase) {
 j->printer.current=0;j->printer.window=0;j->text=0;j->lease=0;j->owner=0;
 fzero(&j->owner_snapshot,sizeof(j->owner_snapshot));fzero(&j->window,sizeof(j->window));
 j->scratch=0;j->front=0;j->phase=phase;l->job=0;
}
static unsigned fprinter(const UiFontPrintJob *j) {
 const UiFontPrinter52 *p=&j->printer;
 return !p->pad&&!p->font&&!p->letter&&!p->line&&!p->unk14&&p->fg<=15&&p->bg<=15&&p->shadow<=15&&
 !p->glyph_table&&!p->unk1a&&p->unk1b==255&&!p->callback&&!p->state&&!p->speed&&!p->delay&&
 !p->scroll&&p->id==8&&!p->unk2d&&!p->unk2e&&!p->unk30&&p->active==1&&
 !p->sub[0]&&!(p->sub[1]&127)&&!p->sub[2]&&!p->sub[3]&&!p->sub[4]&&!p->sub[5]&&!p->sub[6]&&
 p->current_x==j->expected_x&&p->current_y==j->expected_y&&p->x==j->start_x&&p->y==j->start_y&&
 j->consumed<j->units&&p->current==j->text+j->consumed;
}
static UiFontStatus fstep_checked(UiFontLease *l,UiFontPrintJob *j,unsigned budget) {
 if(!rio())return UI_FONT_DEFER;
 if(!fspan((unsigned)j,sizeof(*j)))return UI_FONT_REFUSE;
 if(j->phase==UI_FONT_DONE)return UI_FONT_DONE;
 UiFontStatus s;
 if(l->job!=j||j->lease!=l||j->phase!=UI_FONT_ACTIVE||!budget||budget>8)return UI_FONT_REFUSE;
 if(!fprinter(j)||!fspan((unsigned)j->owner,20)||!fequal(j->owner,&j->owner_snapshot,20)||
 !fspan((unsigned)j->printer.window,16)||!fequal(j->printer.window,&j->window,16)||
 !fwindow(j->printer.window,j->pixel_bytes)) {fretire(l,j,UI_FONT_INVALID);return UI_FONT_INVALID;}
 UiFontRequest binding;fzero(&binding,sizeof(binding));binding.window=j->printer.window;
 binding.front=j->front;binding.pixel_bytes=j->pixel_bytes;binding.scratch=j->scratch;
 binding.text.owner=j->owner;binding.text.offset=(unsigned)j->text-(unsigned)j->owner_snapshot.root;
 binding.text.units=j->units;binding.text.policy=j->policy;
 if(!fparts(l,j,&binding))goto invalid;
 /* Bounded predicted prefix, not a repeated whole-text scan. */
 unsigned count=0,pos=j->consumed,x=j->printer.current_x,y=j->printer.current_y,lines=j->lines;
 unsigned end[8],xs[8],ys[8],ls[8],result[8];
 while(count<budget) {
  unsigned done=0;
  for(;;) {
   if(pos>=j->units)goto invalid;
   unsigned c=j->text[pos++];
   if(c==0xFFFF){if(pos!=j->units)goto invalid;done=1;break;}
   if(c==0xE000){if(!j->policy||++lines>j->cap||lines>11)goto invalid;x=j->printer.x;y+=16;if(y+16>j->window.height*8u)goto invalid;continue;}
   if(c<1||c>509||x>j->window.width*8u||((const unsigned char *)l->widths)[c-1]>j->window.width*8u-x)goto invalid;
   x+=((const unsigned char *)l->widths)[c-1];break;
  }
  end[count]=pos;xs[count]=x;ys[count]=y;ls[count]=lines;result[count++]=done;
  if(done)break;
 }
 unsigned irq=HDISABLE();
 if(!fidentity(l)){HRESTORE(irq);return fhold(l);}
 UiFontScratch *scratch=j->scratch;
 fcopy(scratch->flags,(void *)0x02111886,2);fcopy(scratch->colors,(void *)0x021D1F6E,6);
 fcopy(scratch->lookup,(void *)0x021D1F94,512);fcopy(scratch->glyph,(void *)FWORK,130);
 *(volatile unsigned short *)0x02111886&=(unsigned short)~17u;
 FGENERATE(j->printer.fg,j->printer.bg,j->printer.shadow);
 s=UI_FONT_ACTIVE;
 for(unsigned i=0;i<count;++i) {
  unsigned actual=FRENDER(&j->printer);
  if(actual!=result[i]||j->printer.current!=j->text+end[i]||j->printer.current_x!=xs[i]||j->printer.current_y!=ys[i]||
   j->printer.state||j->printer.speed||j->printer.delay||j->printer.callback||j->printer.glyph_table||j->printer.unk30) {s=UI_FONT_INVALID;break;}
  j->consumed=end[i];j->lines=ls[i];j->expected_x=xs[i];j->expected_y=ys[i];if(actual==1){s=UI_FONT_DONE;break;}
 }
 fcopy((void *)FWORK,scratch->glyph,130);fcopy((void *)0x021D1F94,scratch->lookup,512);
 fcopy((void *)0x021D1F6E,scratch->colors,6);fcopy((void *)0x02111886,scratch->flags,2);
 HRESTORE(irq);
 if(s!=UI_FONT_ACTIVE)fretire(l,j,s);
 return s;
invalid:fretire(l,j,UI_FONT_INVALID);return UI_FONT_INVALID;
}
UiFontStatus ui_font_step(UiFontLease *l,UiFontPrintJob *j,unsigned budget) {
 if(!rio())return UI_FONT_DEFER;
 if(!fspan((unsigned)j,sizeof(*j)))return UI_FONT_REFUSE;
 if(j->phase==UI_FONT_DONE)return UI_FONT_DONE;
 UiFontStatus s=ui_font_check(l);return s==UI_FONT_READY?fstep_checked(l,j,budget):s;
}
UiFontStatus ui_font_cancel(UiFontLease *l,UiFontPrintJob *j) {
 if(!rio())return UI_FONT_DEFER;
 if(!fspan((unsigned)l,sizeof(*l))||!fspan((unsigned)j,sizeof(*j))||l->job!=j||j->lease!=l||j->phase!=UI_FONT_ACTIVE)return UI_FONT_REFUSE;
 fretire(l,j,UI_FONT_CANCELLED);return UI_FONT_CANCELLED;
}
UiFontStatus ui_font_release(UiFontLease *l) {
 UiFontStatus s=ui_font_check(l);if(s!=UI_FONT_READY)return s;
 if(l->job)return UI_FONT_REFUSE;
 unsigned irq=HDISABLE();if(!fidentity(l)){HRESTORE(irq);return fhold(l);}
 volatile unsigned *m=(volatile unsigned *)l->manager;
 if(l->owned){m[4]=l->prior_cache;m[1]=l->prior_fn;m[0]=l->prior_mode;}
 --FREF;
 HRESTORE(irq);
 /* Only the exact owned tuple was detached, or disjoint borrowed cache retained.
  * Reader's independent known-font0 barrier still gates final root freeing. */
 if(!ui_res_drop(&l->resource))return fhold(l);
 l->state=UI_FONT_DONE;return UI_FONT_DONE;
}
