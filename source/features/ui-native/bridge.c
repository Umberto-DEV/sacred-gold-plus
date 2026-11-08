#include "bridge.h"
#include "heap_internal.h"
/* Build these two bindings from the separately compiled physical blob's actual
 * relocated symbols. No default offsets or unresolved linker symbols. */
#if !defined(UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS)
#error "Bridge requires the exact durable persistent binding"
#endif
_Static_assert(UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS==0x023D7B20u,"durable bootstrap binding");
#if !defined(UI_BRIDGE_PHYSICAL_ACTIVATE) || !defined(UI_BRIDGE_PHYSICAL_DEACTIVATE)
#error "Bridge requires actual relocated physical symbol bindings"
#endif
_Static_assert((UI_BRIDGE_PHYSICAL_ACTIVATE&1) && UI_BRIDGE_PHYSICAL_ACTIVATE>=0x023D6E11u && UI_BRIDGE_PHYSICAL_ACTIVATE<0x023D7210u,"physical activate binding");
_Static_assert((UI_BRIDGE_PHYSICAL_DEACTIVATE&1) && UI_BRIDGE_PHYSICAL_DEACTIVATE>=0x023D6E11u && UI_BRIDGE_PHYSICAL_DEACTIVATE<0x023D7210u,"physical deactivate binding");
_Static_assert(sizeof(UiSceneContext)==64,"context ABI");
_Static_assert(sizeof(UiBridge)==5036,"checked root ABI");
_Static_assert(__builtin_offsetof(UiSceneContext,heap_token)==52,"heap context ABI");
_Static_assert(__builtin_offsetof(UiBridge,scene_heap)==4944,"heap authority ABI");
_Static_assert(sizeof(UiBridgeManager)==40,"native manager ABI");
_Static_assert(sizeof(UiBridgeControl)==16,"resident control ABI");
#define BT ((UiPersistent *)0x023D7B20u)
#define BC ((UiBridgeControl *)0x023D7B48u)
#define BM ((const UiModuleConfig *)0x023D7B60u)
#define BR ((const UiResourceConfig *)0x023D7BC0u)
#define BG ((const UiGuideConfig *)0x023D7C00u)
#define BW(p) (*(volatile unsigned *)(p))
#define BB(p) (*(volatile unsigned char *)(p))
#define BACT ((unsigned (*)(const void *,unsigned short))UI_BRIDGE_PHYSICAL_ACTIVATE)
#define BDEACT ((unsigned (*)(const void *,unsigned))UI_BRIDGE_PHYSICAL_DEACTIVATE)
#define BOPTIONS ((unsigned (*)(void *))0x02028EA9u)
#define BIRQ ((unsigned (*)(void))0x020D3A90u)
#define BABI UI_SCENE_CONTEXT_ABI
#define BP 0x31504955u
enum { BC_EMPTY,BC_OWNED,BC_CLEAN,BC_HOLD };
enum { B_BEGIN,B_LOAD,B_INIT,B_MAIN,B_CLOSE,B_RELEASE,B_RETIRED,B_HOLD };
/* Exact inactive bootstrap; historical lifetime is never reset or recovered. */
static unsigned binactive(void) {
 const unsigned *t=(const unsigned *)BT;
 /* Failed ordinary allocations consume a lifetime ID without changing token.
  * Its last successful generation can therefore precede the global counter. */
 if(t[0]||t[1]||t[2]) {
  if(t[0]!=BP||t[1]!=(unsigned)BT||!t[2]||t[2]>BC->generation)return 0;
 }
 for(unsigned i=3;i<10;++i)if(t[i])return 0;
 return 1;
}
static unsigned bhold(void) {BC->phase=BC_HOLD;return 0;}
static unsigned benabled(void) {return BW(0x04000208u)==1&&!BIRQ();}
static unsigned bequal(const unsigned *a,const unsigned *b,unsigned n) {
 while(n--)if(*a++!=*b++)return 0;return 1;
}
static void bcopy(unsigned *a,const unsigned *b,unsigned n) {while(n--)*a++=*b++;}
/* Validate native ownership before following manager.data or any saved field
 * pointer. Unknown native manager words20/24 are deliberately untouched. */
static unsigned bcaller(UiBridgeManager *m,unsigned *proc,unsigned role,unsigned exec) {
 unsigned f=BW(0x021D4158u),p,s,o,t=role==1?0x020FA354u:0x023D7B10u;
 if(!benabled()||role<1||role>2||!hram((unsigned)m,40)||proc!=&m->proc||m->exec!=exec||
 !hram(f,0x110)||!hram((p=BW(f)),16)||BW(p)||BW(p+4)!=(unsigned)m||BW(f+4)||BW(f+0x6C)||
 m->callbacks[0]!=(unsigned)(role==1?ui_bridge_settings_init:ui_bridge_guide_init)||
 m->callbacks[1]!=(unsigned)ui_bridge_main||m->callbacks[2]!=(unsigned)ui_bridge_exit||
 m->callbacks[3]!=~0u||!bequal(m->callbacks,(const unsigned *)t,4)||
 !hram((s=BW(f+12)),0x2330C)||BW(s+0x2302C)>0x232F8u||
 (o=s+16+BW(s+0x2302C))!=BOPTIONS((void *)s)||BW(f+0x10C)>1)return 0;
 if(role==1)return hram(m->args,12)&&BW(m->args+4)==o&&BW(m->args+8)==f+0x10C;
 return !m->args;
}
static UiBridge *broot(UiBridgeManager *m) {
 UiBridge *b=(UiBridge *)m->data;UiSceneContext *c;
 if(BC->manager!=(unsigned)m||BC->phase!=BC_OWNED||!BC->generation||
 BT->magic!=BP||BT->self!=(unsigned)BT||BT->generation!=BC->generation||
 BT->root!=(unsigned)b||BT->bytes!=sizeof(*b)||!hram((unsigned)b,sizeof(*b)))return 0;
 c=&b->context;
 if(c->abi!=BABI||c->role!=BC->role||c->generation!=BC->generation||c->field!=BW(0x021D4158u)||
 c->options!=BW(BW(c->field+12)+0x2302C)+BW(c->field+12)+16||c->input!=c->field+0x10C||
 c->args!=m->args||c->ui_config!=(unsigned)&b->resource_config||
 c->guide_config!=(unsigned)&b->guide_config||c->heap_token!=(unsigned)&b->scene_heap||c->reserved[0]||c->reserved[1]||
 b->module_config.role!=c->role||b->module_config.generation!=c->generation||
 b->guide_config.generation!=c->generation||
 !bequal((const unsigned *)&b->module_config,(const unsigned *)BM,2)||
 !bequal((const unsigned *)&b->module_config+4,(const unsigned *)BM+4,20)||
 !bequal((const unsigned *)&b->guide_config,(const unsigned *)BG,3)||
 !bequal((const unsigned *)&b->guide_config+4,(const unsigned *)BG+4,12)||!bequal((const unsigned *)&b->resource_config,(const unsigned *)BR,16))return 0;
 return b;
}
static unsigned bfont(UiBridge *b,unsigned capture) {
 unsigned w=BW(0x0211188Cu),m,r;
 if(w!=0x02111890u||!hram((m=BW(w+0x9C)),124))return 0;
 r=BB(w+0xB4);
 if(capture) {
  /* Do not normalize an uninitialized or foreign direct cache. The actual
   * Scene font owner performs complete font metadata/resource admission. */
  /* Lazy native managers may retain an unused cache word after allocation. */
  if(r!=1||BW(m)!=1||BW(m+4)!=0x02026111u)return 0;
  b->fontwork=w;b->fontmanager=m;b->fontref=r;
  b->fontmode=BW(m);b->fontdecoder=BW(m+4);b->fontcache=BW(m+16);return 1;
 }
 return w==b->fontwork&&m==b->fontmanager&&r==b->fontref&&BW(m)==b->fontmode&&
 BW(m+4)==b->fontdecoder&&BW(m+16)==b->fontcache;
}
/* The existing native topology/block predicates validate this sole token;
 * its acquired ledger is the authority, not a second Bridge allocation list. */
static unsigned bapp(UiBridge *b) {
 UiSceneContext *c=&b->context;UiHeap *h=&b->scene_heap;
 unsigned a=c->app,s=h->index,count=0,owned=0;
 if(!hram(a,48)||(a<(unsigned)b+sizeof(*b)&&(unsigned)b<a+48)||
 h->magic!=HMAGIC||h->generation!=c->generation||h->backing!=(c->role==1?0x30000u:0x40000u)||
 !hmeta()||s<4||s>=28||HINFO->indexes[38]!=s||h->parent!=HINFO->handles[HINFO->indexes[3]]||
 HINFO->handles[s]!=h->handle||HINFO->parents[s]!=h->parent||HINFO->raws[s]!=h->raw||
 h->handle!=h->raw||!hheader(h->handle)||!hblock(h->parent,h->raw,h->backing)||
 BW(h->handle+28)!=h->raw+h->backing||!hblock(h->handle,a-16,64))return 0;
 for(unsigned i=0;i<16;++i)if(h->acquired[i]) {
  ++count;if(h->acquired[i]==a)owned=1;
 }
 return owned&&count==HINFO->counts[38]&&!BW(a-16)&&!BW(a-12)&&!BW(a-8)&&BW(a-4)==38&&
 BW(a+36)==c->options&&BW(a+40)==c->generation&&BW(a+44)==0x31495553u;
}
static unsigned bretired(UiBridge *b) {
 if(b->context.app||b->context.physical_token||!hmeta()||HINFO->indexes[38]!=28||
 HINFO->counts[38]||!bfont(b,0)||BW(0x021D110Cu)||BW(0x021D1110u)||
 BW(0x021D1114u)||BW(0x021D1118u))return 0;
 for(unsigned i=0;i<23;++i)if(((const unsigned *)&b->scene_heap)[i])return 0;
 for(unsigned i=0;i<4;++i)if(BW(0x040000B8u+12*i)&0x80000000u)return 0;
 return 1;
}
static UiSceneResult bscene(UiBridgeManager *m,UiBridge *b,unsigned selector) {
 unsigned entry=ui_module_check(&b->module,BC->role,BC->generation,selector);
 if(!entry||broot(m)!=b)return UI_SCENE_HOLD;
 unsigned token=b->context.physical_token,app=b->context.app;
 UiSceneResult result=((UiSceneResult (*)(UiSceneContext *,unsigned *))entry)(&b->context,&b->scene_step);
 return b->context.physical_token==token&&(selector!=1||b->context.app==app)?result:UI_SCENE_HOLD;
}
static unsigned binit(UiBridgeManager *m,unsigned *proc,unsigned role) {
 if(!bcaller(m,proc,role,1))return 0;
 if(BC->phase==BC_EMPTY) {
  if(BC->manager||BC->role||m->data||BC->generation==~0u)return 0;
  if(!binactive())return bhold();
  UiPersistent before;bcopy((unsigned *)&before,(const unsigned *)BT,10);
  BC->manager=(unsigned)m;BC->role=role;++BC->generation;BC->phase=BC_OWNED;
  UiBridge *b=ui_persistent_alloc(BT,sizeof(*b),BC->generation);
  if(!b) {
   if(!bequal((const unsigned *)&before,(const unsigned *)BT,10))return bhold();
   BC->phase=BC_CLEAN;return 1;
  }
  m->data=(unsigned)b;
  bcopy((unsigned *)&b->module_config,(const unsigned *)BM,24);
  bcopy((unsigned *)&b->resource_config,(const unsigned *)BR,16);
  bcopy((unsigned *)&b->guide_config,(const unsigned *)BG,16);
  b->module_config.role=role;b->module_config.generation=BC->generation;
  b->guide_config.generation=BC->generation;
  UiSceneContext *c=&b->context;c->abi=BABI;c->role=role;c->generation=BC->generation;
  c->field=BW(0x021D4158u);c->options=BOPTIONS((void *)BW(c->field+12));
  c->input=c->field+0x10C;c->args=m->args;c->ui_config=(unsigned)&b->resource_config;
  c->guide_config=(unsigned)&b->guide_config;c->heap_token=(unsigned)&b->scene_heap;
  if(!bfont(b,1)||!ui_module_init(&b->module))return bhold();
 }
 if(BC->manager!=(unsigned)m||BC->role!=role)return 0;
 if(BC->phase==BC_CLEAN)return 1;
 UiBridge *b=broot(m);if(!b)return bhold();
 if(b->stage==B_BEGIN) {
  UiModuleResult r=ui_module_begin(&b->module,&b->module_config,role,BC->generation);
  if(r!=UI_MODULE_MORE&&r!=UI_MODULE_FAILED)return bhold();
  if(b->module.phase!=UI_MODULE_P_ZERO)b->stage=B_LOAD;
  return 0;
 }
 if(b->stage==B_LOAD) {
  UiModuleResult r=ui_module_pump(&b->module,role,BC->generation,4096,16);
  if(r==UI_MODULE_FAILED) {
   if(ui_module_release(&b->module,role,BC->generation)!=UI_MODULE_RELEASED)return bhold();
   b->stage=B_RETIRED;return 1;
  }
  if(r==UI_MODULE_MORE)return 0;
  if(r!=UI_MODULE_READY)return bhold();
  b->stage=B_INIT;
 }
 if(b->stage!=B_INIT)return bhold();
 UiSceneResult r=bscene(m,b,0);
 if(!broot(m))return bhold();
 if(r==UI_SCENE_MORE)return 0;
 if(r==UI_SCENE_CLOSE){b->stage=B_CLOSE;b->scene_step=0;return 1;}
 if(r!=UI_SCENE_READY||!bapp(b))return bhold();
 b->context.physical_token=BACT(&b->context,0x0F03);
 b->stage=b->context.physical_token?B_MAIN:B_CLOSE;b->scene_step=0;return 1;
}
unsigned ui_bridge_settings_init(UiBridgeManager *m,unsigned *p) {return binit(m,p,1);}
unsigned ui_bridge_guide_init(UiBridgeManager *m,unsigned *p) {return binit(m,p,2);}
unsigned ui_bridge_main(UiBridgeManager *m,unsigned *p) {
 if(!bcaller(m,p,BC->role,2)||BC->manager!=(unsigned)m)return 0;
 if(BC->phase==BC_CLEAN)return 1;
 UiBridge *b=broot(m);if(!b)return bhold();
 if(b->stage==B_RETIRED||b->stage==B_CLOSE)return 1;
 if(b->stage!=B_MAIN||!bapp(b))return bhold();
 UiSceneResult r=bscene(m,b,1);if(!broot(m))return bhold();
 if(r==UI_SCENE_MORE)return 0;
 if(r!=UI_SCENE_CLOSE)return bhold();
 b->stage=B_CLOSE;b->scene_step=0;return 1;
}
unsigned ui_bridge_exit(UiBridgeManager *m,unsigned *p) {
 if(!bcaller(m,p,BC->role,3)||BC->manager!=(unsigned)m)return 0;
 if(BC->phase==BC_CLEAN)goto done;
 UiBridge *b=broot(m);if(!b)return bhold();
 if(b->stage==B_CLOSE) {
  UiSceneContext *c=&b->context;
  if(c->physical_token) {
   if(!BDEACT(c,c->physical_token))return bhold();
   c->physical_token=0;
  }
  UiSceneResult r=bscene(m,b,2);if(!broot(m))return bhold();
  if(r==UI_SCENE_MORE)return 0;
  if(r!=UI_SCENE_EXITED||!bretired(b))return bhold();
  /* The dynamic frame has returned to this resident callback. */
  UiModuleResult v=ui_module_release(&b->module,BC->role,BC->generation);
  if(v!=UI_MODULE_MORE)return bhold();
  b->stage=B_RELEASE;return 0;
 }
 if(b->stage==B_RELEASE) {
  UiModuleResult r=ui_module_step(&b->module,BC->role,BC->generation,4096);
  if(r==UI_MODULE_MORE)return 0;
  if(r!=UI_MODULE_RELEASED)return bhold();b->stage=B_RETIRED;
 }
 if(b->stage!=B_RETIRED||ui_persistent_free(BT,BC->generation)!=UI_PERSISTENT_RELEASED)return bhold();
 m->data=0;
done:
 BC->manager=0;BC->role=0;BC->phase=BC_EMPTY;return 1;
}
