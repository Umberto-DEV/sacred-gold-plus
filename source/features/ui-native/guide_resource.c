/* Compose after heap.c/resource.c. Reuse pure checked helpers and CRC only. */
#include "guide_resource.h"
typedef unsigned GgrU;
#define GGR_MAGIC 0x31524747u
#define GGR_FAST ((unsigned (*)(void *,unsigned,unsigned))0x020D8208)
#define GGR_READ ((unsigned (*)(void *,void *,unsigned))0x020D83BC)
#define GGR_P(x) UI_GGR_##x
_Static_assert(sizeof(UiGuideConfig)==64 && sizeof(UiGuideReader)==292 && sizeof(UiGuideLease)==36,"Guide owner ABI");
_Static_assert(sizeof(UiGuideCategory)==32 && sizeof(UiGuideEntry)==32 && sizeof(UiGuidePage)==16,"Guide views ABI");
static unsigned ggr_zero(const void *v,unsigned bytes) {
 const unsigned *p=v;for(unsigned i=0;i<bytes/4;++i)if(p[i])return 0;return 1;
}
static void ggr_copy(unsigned *to,const volatile unsigned *from,unsigned n) {while(n--)*to++=*from++;}
static unsigned ggr_equal(const unsigned *a,const volatile unsigned *b,unsigned n) {while(n--)if(*a++!=*b++)return 0;return 1;}
static unsigned ggr_valid(const UiGuideReader *r) {return hram((unsigned)r,sizeof(*r))&&r->magic==GGR_MAGIC&&r->self==(unsigned)r;}
/* Actual payload includes a possible unsplittable NNS tail; exclude full prefix. */
static unsigned ggr_alloc(const UiHeap *h,unsigned p,unsigned *bytes) {
 if(!hlive(h)||!p||!hblock(h->handle,p-16,16))return 0;
 unsigned found=0;for(unsigned i=0;i<16;++i)if(h->acquired[i]==p)++found;
 const unsigned *gf=(const unsigned *)(p-16);unsigned size=*(const unsigned *)(p-28);
 if(found!=1||size<16||gf[0]||gf[1]||gf[2]||gf[3]!=38)return 0;
 *bytes=size-16;return 1;
}
static unsigned ggr_container(const UiGuideReader *r,const UiHeap *h,unsigned *root,unsigned *bytes) {
 for(unsigned i=0;i<16;++i) {
  unsigned p=h->acquired[i],n;
  if(p&&ggr_alloc(h,p,&n)&&hext((unsigned)r,sizeof(*r),p,p+n)){*root=p;*bytes=n;return 1;}
 }
 return 0;
}
static unsigned ggr_config(const UiGuideConfig *c) {
 return c->magic==0x31435247&&c->abi==1&&c->language<=4&&c->generation&&c->file_id<513&&
 c->rom_bytes>=512&&c->rom_bytes<=0x20000000&&c->file_top>=512&&c->file_top<=c->rom_bytes&&
 c->file_bottom>=c->file_top&&c->file_bottom<=c->rom_bytes&&c->file_bytes==c->file_bottom-c->file_top&&
 c->member_offset<=c->file_bytes&&c->member_bytes>=40&&c->member_bytes<=131072&&!(c->member_bytes&1)&&
 c->member_bytes<=c->file_bytes-c->member_offset&&c->categories>=1&&c->categories<=4&&
 c->entries>=1&&c->entries<=4096&&!c->reserved[0]&&!c->reserved[1];
}
static unsigned ggr_source(UiGuideReader *r,unsigned capture) {
 const UiGuideConfig *c=&r->config;
 if(*(volatile unsigned *)0x021E3638!=1||RARC[0]!=0x006D6F72||(RARC[7]&7)!=7||RARC[10]||
 RARC[12]!=4104||RARC[14]!=2902||(RARC[17]&3)||!hext(RARC[17],7040,HNATIVE_LO,0x02400000)||RARC[11]!=((RARC[17]+31)&~31u)||
 RARC[13]!=RARC[11]+4104||RARC[18]!=0x020D84C4||RARC[19]!=0x020D850C||
 RARC[20]!=0x020D7484||RARC[21]!=0x020D8514||RARC[22]!=0x602)return 0;
 if(ro(RARC[17],7040,r->source[0]-32,r->source[1]+32)||
 ro(RARC[17],7040,r->config_address,64)||ro(RARC[17],7040,(unsigned)r->heap,sizeof(UiHeap)))return 0;
 const unsigned *fat=(const unsigned *)RARC[11];
 if(fat[2*c->file_id]!=c->file_top||fat[2*c->file_id+1]!=c->file_bottom)return 0;
 unsigned a=*(volatile unsigned *)0x021E3640,b=*(volatile unsigned *)0x021E363C;
 if(capture){ggr_copy(r->archive,RARC+10,13);r->source[2]=a;r->source[3]=b;}
 else if(!ggr_equal(r->archive,RARC+10,13)||a!=r->source[2]||b!=r->source[3])return 0;
 return 1;
}
static unsigned ggr_current(UiGuideReader *r) {
 unsigned n;
 if(!ggr_valid(r)||!r->heap||!ggr_alloc(r->heap,r->source[0],&n)||n!=r->source[1]||
 !hext((unsigned)r,sizeof(*r),r->source[0],r->source[0]+n)||
 !rr(r->config_address,64)||!ggr_equal((const unsigned *)&r->config,(const unsigned *)r->config_address,16)||
 !ggr_config(&r->config)||r->generation!=r->config.generation||!ggr_source(r,0))return 0;
 if(r->root) {
  if(!ggr_alloc(r->heap,r->root,&n)||n<r->config.member_bytes||
  ro(r->root-32,n+32,r->source[0]-32,r->source[1]+32)||
  ro(r->root-32,n+32,(unsigned)r->heap,sizeof(UiHeap))||ro(r->root-32,n+32,r->config_address,64)||
  ro(r->root-32,n+32,r->archive[7],7040))return 0;
 }
 return 1;
}
typedef struct { unsigned f[18],a[10]; } GgrSnapshot;
static void ggr_snapshot(const UiGuideReader *r,GgrSnapshot *s) {
 unsigned mask=HDISABLE();ggr_copy(s->f,r->fs,18);ggr_copy(s->a,RARC,10);HRESTORE(mask);
}
/* quiet0, exactly-owned pending1, suspended2, unknown3. */
static unsigned ggr_shape(const UiGuideReader *r,const GgrSnapshot *s) {
 const unsigned *f=s->f,*a=s->a;
 if(r->fs[18]!=0xA35C691E||r->fs[19]!=0x5CA396E1||a[3]||a[4]||a[5]||a[6]||a[8]||f[6]||f[7]||
 (f[2]&&f[2]!=(unsigned)RARC))return 3;
 if(f[3]&0x4F)return r->file_bound&&r->file_opened&&f[2]==(unsigned)RARC&&
 f[0]==(unsigned)RARC+32&&!f[1]&&f[3]==0x59&&!f[4]&&f[5]==2&&a[7]==0x117&&a[9]==(unsigned)r->fs?1:3;
 if(f[0]||f[1]||a[9]||(f[3]&~16u)||((a[7]&~0x88u)!=7))return 3;
 if(r->file_bound?f[2]!=(unsigned)RARC:f[2])return 3;
 return a[7]==7?0:2;
}
static UiGuideResult ggr_hold(UiGuideReader *r) {r->phase=GGR_P(HOLD);return UI_GUIDE_HOLD;}
/* Even ZERO/RELEASED must not erase an unexpected native association. */
static unsigned ggr_unbound(const UiGuideReader *r) {
 GgrSnapshot s;ggr_snapshot(r,&s);
 return !r->file_bound&&!r->file_opened&&!s.f[2]&&!s.f[3]&&ggr_shape(r,&s)<3;
}
static UiGuideResult ggr_fail(UiGuideReader *r) {
 r->failed=1;r->phase=r->file_bound?GGR_P(ABORT_DRAIN):GGR_P(FAILED);
 return r->file_bound?UI_GUIDE_MORE:UI_GUIDE_FAILED;
}
static unsigned ggr_props(const UiGuideReader *r,const unsigned *f,unsigned pos) {
 return f[8]==r->config.file_id&&f[9]==r->config.file_top&&f[10]==r->config.file_bottom&&f[11]==r->config.file_top+pos;
}
static unsigned ggr_prefix(const UiGuideReader *r) {return 12+12*r->config.categories+16*r->config.entries;}
static unsigned ggr_extent(const UiGuideReader *r,unsigned off,unsigned n,unsigned align) {
 return !(off&(align-1))&&off>=ggr_prefix(r)&&off<=r->config.member_bytes&&n<=r->config.member_bytes-off;
}
static unsigned ggr_string(const UiGuideReader *r,unsigned off,UiTextSlice *s,const UiTextOwner *owner) {
 if(!ggr_extent(r,off,4,2))return 0;
 const unsigned short *t=(const unsigned short *)(r->root+off);
 for(unsigned i=0;i<128&&2*(i+1)<=r->config.member_bytes-off;++i) {
  unsigned c=t[i];if(c==65535){if(!i)return 0;s->owner=owner;s->offset=off;s->units=i+1;s->policy=UI_TEXT_SINGLE;return 1;}
  if(c<1||c>509)return 0;
 }
 return 0;
}
static const unsigned short *ggr_entry(const UiGuideReader *r,unsigned i) {
 return (const unsigned short *)(r->root+12+12*r->config.categories+16*i);
}
static unsigned ggr_entry_ok(const UiGuideReader *r,unsigned i) {
 if(i>=r->config.entries)return 0;const unsigned short *e=ggr_entry(r,i);UiTextSlice title;
 return e[0]&&e[1]&&e[2]&&e[2]<=255&&!e[3]&&ggr_string(r,((const unsigned *)e)[2],&title,0)&&
 ggr_extent(r,((const unsigned *)e)[3],4*e[2],4);
}
static unsigned ggr_header(UiGuideReader *r) {
 const unsigned *p=(const unsigned *)r->root;const unsigned short *s=(const unsigned short *)p;
 if(p[0]!=0x31474753||p[1]!=r->config.member_bytes||s[4]!=r->config.categories||s[5]!=r->config.entries||ggr_prefix(r)>p[1])return 0;
 unsigned count=0;
 for(unsigned i=0;i<s[4];++i) {
  const unsigned *c=p+3+3*i;const unsigned short *h=(const unsigned short *)c;UiTextSlice text;
  if(!h[0]||!h[1]||c[1]!=count||h[1]>s[5]-count||!ggr_string(r,c[2],&text,0))return 0;
  for(unsigned j=0;j<i;++j)if(h[0]==((const unsigned short *)(p+3+3*j))[0])return 0;
  count+=h[1];
 }
 return count==s[5];
}
unsigned ui_guide_init(UiGuideReader *r) {
 if(!hram((unsigned)r,sizeof(*r))||!rwritable((unsigned)r,sizeof(*r))||!ggr_zero(r,sizeof(*r)))return 0;
 r->magic=GGR_MAGIC;r->self=(unsigned)r;r->fs[18]=0xA35C691E;r->fs[19]=0x5CA396E1;return 1;
}
UiGuideResult ui_guide_begin(UiGuideReader *r,const UiGuideConfig *c,UiHeap *h) {
 if(!ggr_valid(r)||(r->phase!=GGR_P(ZERO)&&r->phase!=GGR_P(RELEASED))||!rr((unsigned)c,64)||
 !ggr_config(c)||c->generation<=r->generation||!hlive(h)||
 ro((unsigned)r,sizeof(*r),(unsigned)h,sizeof(*h))||ro((unsigned)r,sizeof(*r),(unsigned)c,64)||
 ro((unsigned)h,sizeof(*h),(unsigned)c,64))return UI_GUIDE_REFUSED;
 if(!rio())return UI_GUIDE_MORE;
 if(!ggr_unbound(r))return ggr_hold(r);
 unsigned app,n;if(!ggr_container(r,h,&app,&n)||ro(app-32,n+32,(unsigned)c,64))return UI_GUIDE_REFUSED;
 r->heap=h;r->source[0]=app;r->source[1]=n;r->config_address=(unsigned)c;
 ggr_copy((unsigned *)&r->config,(const unsigned *)c,16);r->generation=c->generation;
 r->failed=r->cancelled=r->file_bound=r->file_opened=r->read_offset=r->read_count=r->read_return=0;
 r->root=r->cursor=r->close_attempts=r->lease_address=r->verify_entry=0;r->crc=~0u;
 if(!ggr_source(r,1))return ggr_hold(r);
 RINIT(r->fs);r->phase=GGR_P(OPEN);return UI_GUIDE_MORE;
}
UiGuideResult ui_guide_step(UiGuideReader *r,unsigned budget) {
 if(!ggr_valid(r)||!budget||budget>4096)return UI_GUIDE_REFUSED;
 if(r->phase==GGR_P(HOLD))return UI_GUIDE_HOLD;
 if(r->phase==GGR_P(FAILED))return UI_GUIDE_FAILED;
 if(r->phase==GGR_P(RELEASED))return UI_GUIDE_RELEASED;
 if(r->phase==GGR_P(ZERO))return UI_GUIDE_REFUSED;
 if(!rio())return UI_GUIDE_MORE;
 if(!ggr_current(r))return ggr_hold(r);
 GgrSnapshot s;ggr_snapshot(r,&s);unsigned shape=ggr_shape(r,&s);
 if(shape==3)return ggr_hold(r);
 if(r->phase==GGR_P(READY))return !shape&&!r->file_bound?UI_GUIDE_READY:ggr_hold(r);
 if(r->cancelled&&r->phase<GGR_P(ABORT_DRAIN))return ggr_fail(r);
 if(shape==2)return UI_GUIDE_MORE;
 switch(r->phase) {
 case GGR_P(OPEN): {
  if(shape||r->file_bound)return ggr_hold(r);r->file_bound=1;
  unsigned ok=GGR_FAST(r->fs,(unsigned)RARC,r->config.file_id);
  ggr_snapshot(r,&s);if(!s.f[2])r->file_bound=0;
  if(ggr_shape(r,&s)>2)return ggr_hold(r);
  if(!ok)return ggr_fail(r);
  if(!r->file_bound||s.f[3]!=16||s.f[5]||!ggr_props(r,s.f,0))return ggr_hold(r);
  r->file_opened=1;r->phase=GGR_P(SEEK);break;
 }
 case GGR_P(SEEK): {
  if(shape||!r->file_opened)return ggr_hold(r);
  unsigned ok=RSEEK(r->fs,(int)r->config.member_offset,0);ggr_snapshot(r,&s);
  if(ggr_shape(r,&s)>2)return ggr_hold(r);
  if(!ok||!ggr_props(r,s.f,r->config.member_offset))return ggr_fail(r);
  r->phase=GGR_P(ALLOC);break;
 }
 case GGR_P(ALLOC):
  if(shape||!r->file_opened)return ggr_hold(r);
  r->root=(unsigned)ui_alloc38(r->heap,r->config.member_bytes,0);
  if(!r->root)return ggr_fail(r);
  if(!ggr_current(r))return ggr_hold(r);r->phase=GGR_P(READ);break;
 case GGR_P(READ):
  if(shape||!r->file_opened||!ggr_props(r,s.f,r->config.member_offset+r->read_offset))return ggr_hold(r);
  /* The entire bounded member already has a persistent allocation. Submit one
   * asynchronous request and yield; CRC/directory work keeps its own budget. */
  r->read_count=r->config.member_bytes-r->read_offset;
  r->read_return=GGR_READ(r->fs,(void *)(r->root+r->read_offset),r->read_count);r->phase=GGR_P(WAIT);break;
 case GGR_P(WAIT):
  if(shape==1)break;
  if(!r->file_bound||!r->file_opened)return ggr_hold(r);
  if(s.f[4]||s.f[5]||r->read_return!=r->read_count||!ggr_props(r,s.f,r->config.member_offset+r->read_offset+r->read_count)||
  s.f[12]!=r->root+r->read_offset||s.f[13]!=r->read_count||s.f[14]!=r->read_count)return ggr_fail(r);
  r->read_offset+=r->read_count;r->phase=r->read_offset==r->config.member_bytes?GGR_P(CLOSE):GGR_P(READ);break;
 case GGR_P(CLOSE):case GGR_P(ABORT_CLOSE): {
  if(shape||!r->file_bound)return ggr_hold(r);if(r->close_attempts!=~0u)++r->close_attempts;
  unsigned ok=RCLOSE(r->fs);ggr_snapshot(r,&s);
  if(!ok){if(ggr_shape(r,&s)>2)return ggr_hold(r);break;}
  r->file_bound=0;
  if(ggr_shape(r,&s)>2||s.f[2]||s.f[3]||s.f[4]!=14||s.f[5])return ggr_hold(r);
  r->file_opened=0;r->phase=r->failed?GGR_P(FAILED):GGR_P(CRC);break;
 }
 case GGR_P(ABORT_DRAIN):
  if(shape==1)break;r->phase=r->file_bound?GGR_P(ABORT_CLOSE):GGR_P(FAILED);break;
 case GGR_P(CRC): {
  unsigned n=r->config.member_bytes-r->cursor;if(n>budget)n=budget;
  r->crc=rcrc(r->crc,(const unsigned char *)(r->root+r->cursor),n);r->cursor+=n;
  if(r->cursor==r->config.member_bytes) {
   if((r->crc^~0u)!=r->config.member_crc||!ggr_header(r)){r->phase=GGR_P(FAILED);break;}
   r->phase=GGR_P(DIRECTORY);
  }break;
 }
 case GGR_P(DIRECTORY): {
  unsigned end=r->verify_entry+64;if(end>r->config.entries)end=r->config.entries;
  for(;r->verify_entry<end;++r->verify_entry) {
   unsigned i=r->verify_entry;if(!ggr_entry_ok(r,i)){r->phase=GGR_P(FAILED);break;}
   const unsigned short *e=ggr_entry(r,i);unsigned matched=0;
   for(unsigned ci=0;ci<r->config.categories;++ci) {
    const unsigned *c=(const unsigned *)(r->root+12+12*ci);const unsigned short *ch=(const unsigned short *)c;
    if(i>=c[1]&&i-c[1]<ch[1]&&e[1]==ch[0])matched=1;
   }
   if(!matched){r->phase=GGR_P(FAILED);break;}
  }
  if(r->verify_entry==r->config.entries)r->phase=GGR_P(READY);break;
 }
 default:return ggr_hold(r);
 }
 return r->phase==GGR_P(READY)?UI_GUIDE_READY:r->phase==GGR_P(FAILED)?UI_GUIDE_FAILED:UI_GUIDE_MORE;
}
UiGuideResult ui_guide_pump(UiGuideReader *r,unsigned budget,unsigned cap) {
 if(!cap||cap>16||!ggr_valid(r)||!budget||budget>4096)return UI_GUIDE_REFUSED;
 for(unsigned n=0;n<cap;++n) {
  unsigned phase=r->phase,cursor=r->cursor,entry=r->verify_entry,offset=r->read_offset;
  UiGuideResult result=ui_guide_step(r,budget);
  if(result!=UI_GUIDE_MORE)return result;
  if(r->phase==GGR_P(WAIT) || r->cancelled ||
     (phase==r->phase && cursor==r->cursor && entry==r->verify_entry && offset==r->read_offset))return result;
 }
 return UI_GUIDE_MORE;
}
UiGuideResult ui_guide_cancel(UiGuideReader *r) {
 if(!ggr_valid(r)||r->phase==GGR_P(ZERO)||r->phase==GGR_P(RELEASED)||r->phase==GGR_P(READY))return UI_GUIDE_REFUSED;
 if(r->phase==GGR_P(HOLD))return UI_GUIDE_HOLD;r->cancelled=1;return ggr_fail(r);
}
UiGuideResult ui_guide_release(UiGuideReader *r) {
 if(!ggr_valid(r)||r->phase==GGR_P(RELEASED))return UI_GUIDE_REFUSED;
 if(r->phase==GGR_P(HOLD))return UI_GUIDE_HOLD;
 if(r->lease_address||r->file_bound||(r->phase!=GGR_P(READY)&&r->phase!=GGR_P(FAILED)&&r->phase!=GGR_P(ZERO)))return UI_GUIDE_REFUSED;
 if(!rio())return UI_GUIDE_MORE;
 if(r->phase==GGR_P(ZERO)&&!ggr_unbound(r))return ggr_hold(r);
 if(r->phase!=GGR_P(ZERO)) {
  if(!ggr_current(r))return ggr_hold(r);
  GgrSnapshot s;ggr_snapshot(r,&s);if(ggr_shape(r,&s))return ggr_hold(r);
  if(r->root&&!ui_free38(r->heap,(void *)r->root))return UI_GUIDE_REFUSED;
 }
 r->root=0;r->heap=0;r->phase=GGR_P(RELEASED);return UI_GUIDE_RELEASED;
}
static unsigned ggr_lease(const UiGuideLease *l) {
 if(!hram((unsigned)l,sizeof(*l))||l->self!=(unsigned)l||!ggr_valid(l->reader))return 0;
 UiGuideReader *r=l->reader;unsigned p=(unsigned)l;
 return r->phase==GGR_P(READY)&&r->lease_address==p&&r->generation==l->generation&&r->epoch==l->epoch&&l->epoch&&
 hext(p,sizeof(*l),r->source[0],r->source[0]+r->source[1])&&!ro(p,sizeof(*l),(unsigned)r,sizeof(*r))&&
 !ro(p,sizeof(*l),(unsigned)r->heap,sizeof(UiHeap))&&ggr_current(r)&&l->owner.kind==UI_TEXT_SGG1&&
 l->owner.root==(const void *)r->root&&l->owner.bytes==r->config.member_bytes&&l->owner.epoch==l->epoch&&l->owner.live==1;
}
unsigned ui_guide_acquire(UiGuideReader *r,UiGuideLease *l) {
 unsigned p=(unsigned)l;
 if(!ggr_valid(r)||r->phase!=GGR_P(READY)||r->lease_address||r->epoch==~0u||!ggr_current(r)||
 !hext(p,sizeof(*l),r->source[0],r->source[0]+r->source[1])||(p&3)||
 ro(p,sizeof(*l),(unsigned)r,sizeof(*r))||ro(p,sizeof(*l),(unsigned)r->heap,sizeof(UiHeap))||!ggr_zero(l,sizeof(*l)))return 0;
 ++r->epoch;l->reader=r;l->self=p;l->generation=r->generation;l->epoch=r->epoch;
 l->owner.kind=UI_TEXT_SGG1;l->owner.root=(const void *)r->root;l->owner.bytes=r->config.member_bytes;l->owner.epoch=l->epoch;l->owner.live=1;
 r->lease_address=p;return 1;
}
unsigned ui_guide_drop(UiGuideLease *l) {
 if(!ggr_lease(l))return 0;l->owner.live=0;l->reader->lease_address=0;
 unsigned *p=(unsigned *)l;for(unsigned i=0;i<sizeof(*l)/4;++i)p[i]=0;return 1;
}
static unsigned ggr_output(const UiGuideLease *l,void *out,unsigned n) {
 unsigned p=(unsigned)out;
 return ggr_lease(l)&&!(p&3)&&hext(p,n,0x027E0080,0x027E3780)&&
 !ro(p,n,(unsigned)l->reader->heap,sizeof(UiHeap))&&!ro(p,n,l->reader->config_address,64);
}
static unsigned ggr_lookup(const UiGuideReader *r,unsigned id,unsigned *index) {
 if(!id||id>65535)return 0;
 for(unsigned i=0;i<r->config.entries;++i)if(ggr_entry(r,i)[0]==id){if(!ggr_entry_ok(r,i))return 0;*index=i;return 1;}
 return 0;
}
unsigned ui_guide_find(const UiGuideLease *l,unsigned id,unsigned *out) {
 if(!ggr_output(l,out,4))return 0;unsigned i;if(!ggr_lookup(l->reader,id,&i))return 0;*out=i;return 1;
}
unsigned ui_guide_category(const UiGuideLease *l,unsigned index,UiGuideCategory *out) {
 if(!ggr_output(l,out,sizeof(*out))||index>=l->reader->config.categories)return 0;
 const UiGuideReader *r=l->reader;const unsigned *c=(const unsigned *)(r->root+12+12*index);const unsigned short *h=(const unsigned short *)c;
 UiGuideCategory v;v.id=h[0];v.first=c[1];v.count=h[1];v.total=r->config.categories;
 if(!v.id||!v.count||v.first>r->config.entries||v.count>r->config.entries-v.first||!ggr_string(r,c[2],&v.title,&l->owner))return 0;
 ggr_copy((unsigned *)out,(const unsigned *)&v,sizeof(v)/4);return 1;
}
unsigned ui_guide_entry(const UiGuideLease *l,unsigned ci,unsigned index,UiGuideEntry *out) {
 if(!ggr_output(l,out,sizeof(*out))||ci>=l->reader->config.categories)return 0;
 const UiGuideReader *r=l->reader;const unsigned *c=(const unsigned *)(r->root+12+12*ci);const unsigned short *ch=(const unsigned short *)c;
 if(index>=ch[1]||c[1]>=r->config.entries||index>=r->config.entries-c[1]||!ggr_entry_ok(r,c[1]+index))return 0;
 const unsigned short *e=ggr_entry(r,c[1]+index);if(e[1]!=ch[0])return 0;
 UiGuideEntry v;v.id=e[0];v.category=e[1];v.pages=e[2];v.index=c[1]+index;
 if(!ggr_string(r,((const unsigned *)e)[2],&v.title,&l->owner))return 0;
 ggr_copy((unsigned *)out,(const unsigned *)&v,sizeof(v)/4);return 1;
}
static const unsigned short *ggr_page(const UiGuideReader *r,unsigned entry,unsigned page) {
 if(!ggr_entry_ok(r,entry))return 0;const unsigned short *e=ggr_entry(r,entry);if(page>=e[2])return 0;
 unsigned table=((const unsigned *)e)[3],off=*(const unsigned *)(r->root+table+4*page);
 if(!ggr_extent(r,off,4,4))return 0;const unsigned short *p=(const unsigned short *)(r->root+off);
 if(!p[0]||p[0]>7||!ggr_extent(r,off,4+4*p[0],4))return 0;
 unsigned target;if(p[1]&&!ggr_lookup(r,p[1],&target))return 0;
 for(unsigned i=0;i<p[0];++i){UiTextSlice s;if(!ggr_string(r,((const unsigned *)p)[1+i],&s,0))return 0;}
 return p;
}
unsigned ui_guide_page(const UiGuideLease *l,unsigned entry,unsigned page,UiGuidePage *out) {
 if(!ggr_output(l,out,sizeof(*out)))return 0;const unsigned short *p=ggr_page(l->reader,entry,page);if(!p)return 0;
 UiGuidePage v;v.entry=entry;v.page=page;v.lines=p[0];v.reference=p[1];ggr_copy((unsigned *)out,(const unsigned *)&v,4);return 1;
}
unsigned ui_guide_line(const UiGuideLease *l,unsigned entry,unsigned page,unsigned line,UiTextSlice *out) {
 if(!ggr_output(l,out,sizeof(*out)))return 0;const unsigned short *p=ggr_page(l->reader,entry,page);
 if(!p||line>=p[0])return 0;UiTextSlice v;if(!ggr_string(l->reader,((const unsigned *)p)[1+line],&v,&l->owner))return 0;
 ggr_copy((unsigned *)out,(const unsigned *)&v,4);return 1;
}
