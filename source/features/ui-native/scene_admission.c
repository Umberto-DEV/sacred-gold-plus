/* One Scene TU, after accepted heap.c/resource.c/font.c/bg.c. Reuse their
 * read-only predicates; no independent font/GX/heap implementation or owner. */
#include "scene_admission.h"
#include "heap_internal.h"
_Static_assert(sizeof(UiSceneContext)==64 && sizeof(UiBridge)==5036,"USC2/Bridge ABI");
_Static_assert(__builtin_offsetof(UiBridge,context)==4848 &&
 __builtin_offsetof(UiBridge,scene_heap)==4944,"resident authority layout");
#define SW(p) (*(volatile unsigned *)(p))
#define SB(p) (*(volatile unsigned char *)(p))
#define SMODE ((unsigned (*)(void))0x020D3A9Cu)
#define SOPTIONS ((unsigned (*)(void *))0x02028EA9u)
#define SFADE ((unsigned (*)(void))0x0200FB5Du)
#define SBRIGHT ((unsigned (*)(unsigned))0x0200B5C1u)
static unsigned sallocation(unsigned id,unsigned p,unsigned n) {
 unsigned slot=HINFO->indexes[id];
 return slot<28 && hheader(HINFO->handles[slot]) && hram(p,n) &&
 hblock(HINFO->handles[slot],p-16,n+16) && SB(p-4)==id;
}
static unsigned sfont(void) {
 unsigned m=SW(0x0211192Cu);
 if(!fmeta(m)||SB(0x02111944u)!=1)return 0;
 const unsigned *v=(const unsigned *)m;
 /* Lazy decoding leaves the unused cache word uninitialized. */
 return v[0]==1 && v[1]==0x02026111u &&
 sallocation(3,m,124) && sallocation(3,v[21],84) &&
 sallocation(3,v[29],509) && fwidths(v[29]);
}
static unsigned scontext(const UiSceneContext *c) {
 if(!hram((unsigned)c,sizeof(*c)) || c->abi!=UI_SCENE_CONTEXT_ABI ||
 c->role<1 || c->role>2 || !c->generation || c->reserved[0] || c->reserved[1])return 0;
 unsigned f=SW(0x021D4158u),p,m,root;
 if(c->field!=f || !hram(f,0x110) || !hram((p=SW(f)),16) ||
 !hram((m=SW(p+4)),40) || !hram((root=SW(m+28)),5036) ||
 (unsigned)c!=root+4848 || c->heap_token!=root+4944 ||
 c->ui_config!=root+__builtin_offsetof(UiBridge,resource_config) ||
 c->guide_config!=root+__builtin_offsetof(UiBridge,guide_config) ||
 !sallocation(11,root,5036) || ro(root-32,5068,f,0x110) ||
 ro(root-32,5068,p,16) || ro(root-32,5068,m,40))return 0;
 const UiBridge *b=(const UiBridge *)root;
 return b->module_config.role==c->role && b->module_config.generation==c->generation &&
 b->guide_config.generation==c->generation;
}
static unsigned sfield(const UiSceneContext *c) {
 unsigned f=c->field,p=SW(f),m=SW(p+4),t=c->role==1?0x020FA354u:0x023D7B10u;
 if(SW(p) || SW(f+4) || SW(f+0x6C) || (SW(f+0x18)!=1 && SW(f+0x18)!=3) ||
 SW(m+16)!=1 || SW(m+12)!=~0u)return 0;
 for(unsigned i=0;i<4;++i) {
  unsigned fn=SW(m+4*i);
  if(fn!=SW(t+4*i) || (i<3 && (!(fn&1) || !hext(fn&~1u,2,0x02000000u,0x02400000u))))return 0;
 }
 return !ro(f,0x110,p,16) && !ro(f,0x110,m,40) && !ro(p,16,m,40);
}
static unsigned sargs(const UiSceneContext *c) {
 unsigned f=c->field,p=SW(f),m=SW(p+4),s=SW(f+12),o=c->options;
 if(!hram(s,0x2330C) || SW(s+0x2302C)>0x232F8u ||
 o!=s+16+SW(s+0x2302C) || !hram(o,4) || c->input!=f+0x10C ||
 SW(f+0x10C)>1 || c->args!=SW(m+24) || ro(s,0x2330C,f,0x110) ||
 ro(s,0x2330C,p,16) || ro(s,0x2330C,m,40) ||
 ro(s,0x2330C,(unsigned)c-4848-32,5068))return 0;
 if(c->role==1) {
  if(!hram(c->args,12) || SW(c->args+4)!=o || SW(c->args+8)!=c->input ||
   ro(c->args,12,s,0x2330C) || ro(c->args,12,f,0x110) ||
   ro(c->args,12,p,16) || ro(c->args,12,m,40) ||
   ro(c->args,12,(unsigned)c-4848-32,5068))return 0;
 } else if(c->args)return 0;
 return SOPTIONS((void *)s)==o;
}
/* Public entry passes the exact incoming SP. A numerical DTCM range alone
 * would admit a stale lower frame or this function's own output aliases. */
static __attribute__((used,noinline)) SceneAdmission sadmit(const UiSceneContext *c,unsigned *reason,unsigned caller_sp) {
 unsigned q=(unsigned)reason;
 if(SMODE()!=0x1Fu || (q&3) || caller_sp<0x027E0080u || caller_sp>0x027E377Cu ||
 q<caller_sp || !hext(q,4,0x027E0080u,0x027E3780u))return SCENE_ADMIT_REFUSE;
 unsigned e=SCENE_ADMIT_E_NONE;
 SceneAdmission result=SCENE_ADMIT_REFUSE;
 if(SW(0x04000208u)!=1 || RIRQ()) {e=SCENE_ADMIT_E_EXECUTION;result=SCENE_ADMIT_WAIT;}
 else if(!hmeta() || !scontext(c))e=SCENE_ADMIT_E_CONTEXT;
 else if(!sfield(c))e=SCENE_ADMIT_E_FIELD;
 else if(!sargs(c))e=SCENE_ADMIT_E_ARGS;
 else if(!sfont())e=SCENE_ADMIT_E_FONT;
 else {
  for(unsigned i=0;i<4;++i)if(SW(0x021D110Cu+4*i)){e=SCENE_ADMIT_E_CALLBACK;goto done;}
  for(unsigned i=0;i<8;++i)if(SW(0x021D1F74u+4*i)){e=SCENE_ADMIT_E_PRINTER;goto done;}
  for(unsigned i=0;i<4;++i)if(SW(0x040000B8u+12*i)&0x80000000u){e=SCENE_ADMIT_E_DMA;goto done;}
  if((SW(0x04000064u)&0x80000000u) || (B_REG16(0x04000304u)&0x203u)!=0x203u ||
   SW(0x02110C7Cu)!=1 || (SW(0x02110C80u)!=3 && SW(0x02110C80u)!=~0u) ||
   !bg_banks_coherent())e=SCENE_ADMIT_E_DISPLAY;
  else if(SFADE()!=1)e=SCENE_ADMIT_E_FADE;
  else if(SBRIGHT(3)!=1)e=SCENE_ADMIT_E_BRIGHTNESS;
  else result=SCENE_ADMIT_READY;
 }
done:
 *reason=e;return result;
}
__attribute__((naked)) SceneAdmission ui_scene_admit(const UiSceneContext *c __attribute__((unused)),unsigned *reason __attribute__((unused))) {
 __asm__ volatile("mov r2,sp\nb sadmit");
}
