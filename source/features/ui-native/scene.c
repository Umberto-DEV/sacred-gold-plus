/* Compose after foundations, real admission, Settings and Guide implementations.
 * No resident ABI state, second heap authority or old native54 fallback. */
#include "scene.h"
#if !defined(UI_SCENE_WORK_CALLS) || !defined(UI_SCENE_GLYPH_BUDGET) || !defined(UI_SCENE_LAST_START_LINE) || !defined(SGP_UI_SCENE_PHYSICAL_CONSUME) || !defined(SGP_UI_SCENE_PHYSICAL_ACK)
#error "Scene needs explicit calibrated pump/publication and resident input bindings"
#endif
_Static_assert(UI_SCENE_WORK_CALLS>0 && UI_SCENE_WORK_CALLS<=4096,"finite call guard, not time acceptance");
_Static_assert(UI_SCENE_GLYPH_BUDGET>0 && UI_SCENE_GLYPH_BUDGET<=8,"font batch bound");
_Static_assert(UI_SCENE_LAST_START_LINE>=192 && UI_SCENE_LAST_START_LINE<=261,"BG deadline domain");
_Static_assert((SGP_UI_SCENE_PHYSICAL_CONSUME&1) && (SGP_UI_SCENE_PHYSICAL_ACK&1),"resident Thumb exports");
#define SC_CONSUME ((unsigned (*)(const void *,PhysicalToken,PhysicalSample *))SGP_UI_SCENE_PHYSICAL_CONSUME)
#define SC_ACK ((unsigned (*)(const void *,PhysicalToken,unsigned))SGP_UI_SCENE_PHYSICAL_ACK)
#define SC_SYS 0x021D110Cu
enum { SC_CAPTURE,SC_UIR_START,SC_UIR_WAIT,SC_GUIDE_START,SC_GUIDE_WAIT,
 SC_LEASES,SC_POOL,SC_BG,SC_ENTER,SC_BUILD,SC_PAINT_FIRST,SC_WAIT_FIRST,
 SC_RESERVED12,SC_RESERVED13,SC_IDLE,SC_PAINT,SC_WAIT,SC_CLOSING,SC_HELD };
enum { SC_OWNER=1,SC_UIR=2,SC_GUIDE=4,SC_CHROME=8,SC_FONT=16,
 SC_GUIDE_LEASE=32,SC_PAINTER=64,SC_BG_ROOTS=128 };
static unsigned sc_zero(const void *v,unsigned bytes) {
 const unsigned *p=v;for(unsigned i=0;i<bytes/4;++i)if(p[i])return 0;return 1;
}
static unsigned sc_context(const UiSceneContext *c,const unsigned *step) {
 return hmeta() && scontext(c) && sargs(c) &&
 step==(unsigned *)((unsigned)c-__builtin_offsetof(UiBridge,context)+__builtin_offsetof(UiBridge,scene_step));
}
static unsigned sc_app(const UiSceneContext *x) {
 unsigned p=x->app,n=x->role==1?sizeof(SettingsApp):sizeof(GuideApp);
 UiHeap *h=(UiHeap *)x->heap_token;
 if(!hlive(h)||h->generation!=x->generation||h->backing!=(x->role==1?0x30000u:0x40000u)||
 !hram(p,n)||!hblock(h->handle,p-16,n+16)||SB(p-4)!=38)return 0;
 unsigned found=0;for(unsigned i=0;i<16;++i)if(h->acquired[i]==p)found=1;
 if(!found)return 0;
 const SceneCommon *c=(const SceneCommon *)p;
 return c->context==x && c->heap==h && c->prefix.options==x->options &&
 c->prefix.generation==x->generation && c->prefix.magic==SGP_SETTINGS_UI_APP_MAGIC;
}
static UiSceneResult sc_close(SceneCommon *c,unsigned reason) {
 c->error=reason;c->context->error=reason;c->phase=SC_CLOSING;
 if(!c->close_kind)c->close_kind=1;return UI_SCENE_CLOSE;
}
static UiSceneResult sc_hold(SceneCommon *c,unsigned reason) {
 c->error=reason;c->context->error=reason;c->context->flags=1;c->phase=SC_HELD;return UI_SCENE_HOLD;
}
static unsigned sc_build(SceneCommon *c) {
 if(c->pool_owner.epoch==~0u || c->font.job)return 0;
 unsigned epoch=c->pool_owner.epoch+1,ok;
 if(c->context->role==1)ok=settings_scene_build((SettingsApp *)c,epoch);
 else {GuideApp *a=(GuideApp *)c;ok=guide_ui_build(&a->model,&a->lease,&c->chrome,
  (const unsigned char *)c->font.widths,&a->desired,c->pool,epoch);}
 if(!ok)return 0;
 c->pool_owner.kind=UI_TEXT_BUFFER;c->pool_owner.root=c->pool;
 c->pool_owner.bytes=c->context->role==1?256:1024;c->pool_owner.epoch=epoch;c->pool_owner.live=1;
 c->preview_due=0;c->submitted_epoch=c->model_epoch;return 1;
}
static unsigned sc_begin(SceneCommon *c,unsigned index) {
 if(c->next_version==~0u)return 0;unsigned version=++c->next_version;
 if(c->context->role==1) {
  SettingsApp *a=(SettingsApp *)c;
  SettingsPaintRequest r={c->heap,&c->bg,&c->font,&a->catalog,&a->desired,
   &c->uir1_owner,&c->pool_owner,c->prefix.generation,index,version};
  return settings_paint_begin(&a->painter,&r)==SETTINGS_PAINT_MORE;
 }
 GuideApp *a=(GuideApp *)c;
 GuidePaintRequest r={c->heap,&c->bg,&c->font,&a->lease,&a->desired,
  &c->uir1_owner,&c->pool_owner,c->prefix.generation,index,version};
 return guide_paint_begin(&a->painter,&r)==GUIDE_PAINT_MORE;
}
/* Both painters deliberately expose the same finite status numbering. */
_Static_assert((unsigned)SETTINGS_PAINT_MORE==(unsigned)GUIDE_PAINT_MORE &&
 (unsigned)SETTINGS_PAINT_HOLD==(unsigned)GUIDE_PAINT_HOLD,"shared pump status");
static unsigned sc_pump(SceneCommon *c) {
 unsigned result=SETTINGS_PAINT_MORE;
 unsigned calls=UI_SCENE_WORK_CALLS;
 /* Initial full composition is heavier than interactive row updates. Keep
  * its cap separate even when the interactive calibration permits more work. */
 if(c->phase==SC_PAINT_FIRST && calls>32)calls=32;
 for(unsigned i=0;i<calls && result==SETTINGS_PAINT_MORE;++i) {
  if(!rio())break;
  result=c->context->role==1?(unsigned)settings_paint_step(&((SettingsApp *)c)->painter,UI_SCENE_GLYPH_BUDGET):
   (unsigned)guide_paint_step(&((GuideApp *)c)->painter,UI_SCENE_GLYPH_BUDGET);
  /* Each component restores the caller's IME/I after its bounded native call. */
  if(!rio())return SETTINGS_PAINT_HOLD;
 }
 return result;
}
static unsigned sc_visible(SceneCommon *c) {
 return c->bg.front<2 && c->bg.pending==UI_BG_NONE && c->bg.preparing==UI_BG_NONE &&
 c->bg.version[c->bg.front]==c->next_version;
}
static UiSceneResult sc_draw(SceneCommon *c) {
 unsigned result=sc_pump(c);
 if(result==SETTINGS_PAINT_MORE)return UI_SCENE_MORE;
 if(result==SETTINGS_PAINT_HOLD)return sc_hold(c,31);
 if(result==SETTINGS_PAINT_UNCHANGED){c->visible_epoch=c->submitted_epoch;c->phase=SC_IDLE;return UI_SCENE_MORE;}
 if(result!=SETTINGS_PAINT_PREPARED)return sc_close(c,32);
 c->phase=SC_WAIT;return UI_SCENE_MORE;
}
UiSceneResult ui_scene_init(UiSceneContext *x,unsigned *step) {
 if(!rio())return UI_SCENE_MORE;
 if(!sc_context(x,step)||x->flags)return UI_SCENE_HOLD;
 UiHeap *h=(UiHeap *)x->heap_token;SceneCommon *c;
 if(!x->app) {
  /* This guard also rejects duplicate creation after an app allocation fault. */
  if(*step || !sc_zero(h,sizeof(*h)))return UI_SCENE_HOLD;
  unsigned reason=0;SceneAdmission admission=ui_scene_admit(x,&reason);
  if(admission==SCENE_ADMIT_WAIT)return UI_SCENE_MORE;
  if(admission!=SCENE_ADMIT_READY){x->error=reason;return UI_SCENE_CLOSE;}
  if(!ui_heap38_create(h,x->role==1?0x30000:0x40000,x->generation))return UI_SCENE_CLOSE;
  *step=1;
  c=ui_alloc38(h,x->role==1?sizeof(SettingsApp):sizeof(GuideApp),0);
  if(!c){x->error=1;return UI_SCENE_CLOSE;}
  c->prefix.options=x->options;c->prefix.generation=x->generation;c->prefix.magic=SGP_SETTINGS_UI_APP_MAGIC;
  c->context=x;c->heap=h;c->model_epoch=1;x->app=(unsigned)c;
 } else if(!sc_app(x))return UI_SCENE_HOLD;
 c=(SceneCommon *)x->app;
 unsigned result;
 switch(c->phase) {
 case SC_CAPTURE:
  if(x->role==1) {
   result=settings_scene_capture((SettingsApp *)c);
   if(result==SGP_SHINY_BUSY)return UI_SCENE_MORE;
   if(result!=SGP_SHINY_OK)return sc_close(c,2);
   c->acquired|=SC_OWNER;
  } else guide_ui_init(&((GuideApp *)c)->model);
  c->phase=SC_UIR_START;return UI_SCENE_MORE;
 case SC_UIR_START:
  if(!ui_res_init(&c->resource))return sc_close(c,3);
  c->acquired|=SC_UIR;
  result=ui_res_begin(&c->resource,(const UiResourceConfig *)x->ui_config,h);
  if(result!=UI_RES_MORE)return sc_close(c,4);
  c->phase=SC_UIR_WAIT;return UI_SCENE_MORE;
 case SC_UIR_WAIT:
  result=ui_res_pump(&c->resource,16);
  if(result==UI_RES_MORE)return UI_SCENE_MORE;
  if(result==UI_RES_HELD)return sc_hold(c,5);
  if(result!=UI_RES_OK)return sc_close(c,6);
  c->phase=x->role==2?SC_GUIDE_START:SC_LEASES;return UI_SCENE_MORE;
 case SC_GUIDE_START: {
  GuideApp *a=(GuideApp *)c;
  if(!ui_guide_init(&a->reader))return sc_close(c,7);
  c->acquired|=SC_GUIDE;
  result=ui_guide_begin(&a->reader,(const UiGuideConfig *)x->guide_config,h);
  if(result==UI_GUIDE_HOLD)return sc_hold(c,8);
  if(result!=UI_GUIDE_MORE)return sc_close(c,9);
  c->phase=SC_GUIDE_WAIT;return UI_SCENE_MORE;
 }
 case SC_GUIDE_WAIT:
  result=ui_guide_pump(&((GuideApp *)c)->reader,4096,16);
  if(result==UI_GUIDE_MORE)return UI_SCENE_MORE;
  if(result==UI_GUIDE_HOLD)return sc_hold(c,10);
  if(result!=UI_GUIDE_READY)return sc_close(c,11);
  c->phase=SC_LEASES;return UI_SCENE_MORE;
 case SC_LEASES:
  if(!ui_res_acquire(&c->resource,&c->chrome,0))return sc_close(c,12);
  c->acquired|=SC_CHROME;
  result=ui_font_acquire(&c->font,&c->resource,0);
  if(result==UI_FONT_HOLD)return sc_hold(c,13);
  if(result!=UI_FONT_READY)return sc_close(c,14);
  c->acquired|=SC_FONT;
  c->uir1_owner.kind=UI_TEXT_UIR1;c->uir1_owner.root=(void *)c->font.root;
  c->uir1_owner.bytes=c->font.bytes;c->uir1_owner.epoch=c->resource.generation;c->uir1_owner.live=1;
  if(x->role==2) {
   if(!ui_guide_acquire(&((GuideApp *)c)->reader,&((GuideApp *)c)->lease))return sc_close(c,15);
   c->acquired|=SC_GUIDE_LEASE;
  } else {
   SettingsApp *a=(SettingsApp *)c;const unsigned *p=(const unsigned *)c->resource.root;
   a->catalog.root=p;a->catalog.bytes=c->font.bytes;a->catalog.directory=p[24];a->catalog.count=p[25];
   a->catalog.widths=(const unsigned char *)c->font.widths;a->catalog.width_count=509;a->catalog.identity=x->generation;
  }
  c->phase=SC_POOL;return UI_SCENE_MORE;
 case SC_POOL:
  c->pool=ui_alloc38(h,x->role==1?256:1024,0);
  if(!c->pool)return sc_close(c,16);
  /* Owned synchronous setup has no async wait between these stages. Keep
   * each component's admission/rollback and yield before first painting. */
  c->phase=SC_BG;__attribute__((fallthrough));
 case SC_BG:
  result=ui_bg_create(h,&c->bg,x->generation);
  if(c->bg.owned)c->acquired|=SC_BG_ROOTS;
  if(!result)return sc_close(c,17);
  result=x->role==1?settings_paint_init(&((SettingsApp *)c)->painter,sizeof(SettingsPainter),x->generation):
   guide_paint_init(&((GuideApp *)c)->painter,sizeof(GuidePainter),x->generation);
  if(!result)return sc_close(c,18);
  c->acquired|=SC_PAINTER;c->phase=SC_ENTER;__attribute__((fallthrough));
 case SC_ENTER: {
  const void *palette=x->role==1?(void *)((SettingsApp *)c)->painter.palette:(void *)((GuideApp *)c)->painter.palette;
  UiResourceSlice ball;
  if(!ui_res_ball(&c->font.resource,&ball) || !ui_bg_enter_backdrop(h,&c->bg,x->generation,palette,0x564c) ||
     !ui_bg_install_ball(h,&c->bg,x->generation,ball.data,ball.bytes))return sc_close(c,19);
  c->phase=SC_BUILD;
 }
 __attribute__((fallthrough));
 case SC_BUILD:
  if(!sc_build(c)||!sc_begin(c,0))return sc_close(c,20);
  c->phase=SC_PAINT_FIRST;return UI_SCENE_MORE;
 case SC_PAINT_FIRST:
  result=sc_pump(c);
  if(result==SETTINGS_PAINT_MORE)return UI_SCENE_MORE;
  if(result==SETTINGS_PAINT_HOLD)return sc_hold(c,21);
  if(result!=SETTINGS_PAINT_PREPARED)return sc_close(c,22);
  if(c->phase==SC_PAINT_FIRST && !ui_bg_register(&c->bg,x->generation,UI_SCENE_LAST_START_LINE))return sc_close(c,23);
  ++c->phase;return UI_SCENE_MORE;
 case SC_WAIT_FIRST:
  if(!sc_visible(c))return UI_SCENE_MORE;
  /* Root-approved first-front readiness: untouched hidden history remains
   * invalid and its first changed use takes the painter FULL path. */
  c->visible_epoch=c->submitted_epoch;c->phase=SC_IDLE;return UI_SCENE_READY;
 case SC_IDLE:return UI_SCENE_READY;
 case SC_HELD:return UI_SCENE_HOLD;
 default:return sc_close(c,25);
 }
}
static unsigned sc_guide_input(GuideApp *a,unsigned fresh,unsigned busy,
 unsigned mapped,unsigned repeated,unsigned mode) {
 SceneCommon *c=&a->common;
 a->gesture.visible_epoch=0;
 GuideInput in={&c->sample,fresh,mapped,repeated,mode,0,0,0,busy};
 return guide_ui_input(&a->model,&a->lease,&in);
}
UiSceneResult ui_scene_main(UiSceneContext *x,unsigned *step) {
 if(!rio())return UI_SCENE_MORE;
 if(!sc_context(x,step)||x->flags||!sc_app(x)||!x->physical_token)return UI_SCENE_HOLD;
 SceneCommon *c=(SceneCommon *)x->app;
 if(c->phase==SC_HELD)return UI_SCENE_HOLD;
 if(c->phase==SC_CLOSING)return UI_SCENE_CLOSE;
 if(c->phase<SC_IDLE||c->phase>SC_WAIT)return sc_hold(c,26);
 /* Publication already made this frame visible. Retire the wait before
  * consuming the next key, otherwise that fresh edge is discarded as busy. */
 if(c->phase==SC_WAIT && sc_visible(c)) {
  c->visible_epoch=c->submitted_epoch;c->phase=SC_IDLE;
 }
 unsigned fresh=SC_CONSUME(x,x->physical_token,&c->sample);
 if(fresh==PHYS_INVALID){if(x->role==2)((GuideApp *)c)->gesture.visible_epoch=0;return sc_hold(c,27);}
 unsigned busy=c->phase!=SC_IDLE || c->visible_epoch!=c->model_epoch || c->bg.pending!=UI_BG_NONE || c->bg.preparing!=UI_BG_NONE;
 unsigned mapped=0,repeated=0,mode=0;
 if(fresh==PHYS_FRESH){mapped=SW(SC_SYS+0x44);repeated=SW(SC_SYS+0x48);mode=SW(SC_SYS+0x34);c->suspended=0;}
 unsigned changed=0,result=0;
 if(x->role==1) {
  SettingsApp *a=(SettingsApp *)c;
  result=settings_scene_input(a,fresh,busy||a->model.awaiting_apply,mapped,repeated,mode);
  if(result==SETTINGS_CLOSE_DISCARD)return sc_close(c,0);
  changed=result==SETTINGS_CHANGED;
  unsigned preview=settings_owner_preview(&a->owners,&a->model);
  if(preview!=SGP_SHINY_OK && preview!=SGP_SHINY_BUSY)return sc_hold(c,28);
  if(a->model.awaiting_apply && preview==SGP_SHINY_OK) {
   result=settings_apply(&a->model,&a->owners);
   if(result==SETTINGS_CLOSE_APPLIED){c->close_kind=2;return sc_close(c,0);}
   changed=1;
  }
  if(fresh==PHYS_SUSPEND)c->suspended=1;
  settings_scene_tick(a,fresh==PHYS_FRESH);
 } else {
  result=sc_guide_input((GuideApp *)c,fresh,busy,mapped,repeated,mode);
  if(result==GUIDE_UI_CLOSE)return sc_close(c,0);
  changed=result==GUIDE_UI_CHANGED;
  if(fresh==PHYS_SUSPEND)c->suspended=1;
 }
 /* Consumers above have rearmed physical and touch release gates first. */
 /* ACK0 also means folded/reclosed or superseded. Keep suspended/rearmed;
  * reconsume next normal frame. PHYS_INVALID above still fails closed. */
 if(fresh==PHYS_SUSPEND)(void)SC_ACK(x,x->physical_token,c->sample.suspend);
 if(changed) {if(c->model_epoch==~0u)return sc_close(c,30);++c->model_epoch;}
 if(c->phase==SC_WAIT) {
  if(!sc_visible(c))return UI_SCENE_MORE;
  c->visible_epoch=c->submitted_epoch;c->phase=SC_IDLE;return UI_SCENE_MORE;
 }
 if(c->phase==SC_PAINT)return sc_draw(c);
 if(!c->suspended && (changed||c->preview_due||c->model_epoch!=c->visible_epoch)) {
  if(!changed && c->model_epoch==c->visible_epoch){if(c->model_epoch==~0u)return sc_close(c,33);++c->model_epoch;}
  if(!sc_build(c)||!sc_begin(c,c->bg.front^1u))return sc_close(c,34);
  c->phase=SC_PAINT;return sc_draw(c);
 }
 return UI_SCENE_MORE;
}
UiSceneResult ui_scene_exit(UiSceneContext *x,unsigned *step) {
 if(!rio())return UI_SCENE_MORE;
 if(!sc_context(x,step)||x->flags||x->physical_token)return UI_SCENE_HOLD;
 UiHeap *h=(UiHeap *)x->heap_token;
 if(x->app) {
  if(!sc_app(x))return UI_SCENE_HOLD;
  SceneCommon *c=(SceneCommon *)x->app;unsigned result;
  if(c->phase==SC_HELD)return UI_SCENE_HOLD;
  c->phase=SC_CLOSING;
  if(c->acquired&SC_BG_ROOTS) {
   if(!ui_bg_retire(h,&c->bg,x->generation))return sc_hold(c,35);
  }
  if(c->acquired&SC_PAINTER) {
   result=x->role==1?(unsigned)settings_paint_retire(&((SettingsApp *)c)->painter):
    (unsigned)guide_paint_retire(&((GuideApp *)c)->painter);
   if(result==SETTINGS_PAINT_MORE)return UI_SCENE_MORE;
   if(result!=SETTINGS_PAINT_UNCHANGED)return sc_hold(c,36);
   c->acquired&=~SC_PAINTER;
  }
  if(c->acquired&SC_OWNER) {
   result=c->close_kind==2?SGP_SHINY_OK:settings_owner_rollback(&((SettingsApp *)c)->owners);
   if(result==SGP_SHINY_BUSY)return UI_SCENE_MORE;
   if(result!=SGP_SHINY_OK)return sc_hold(c,37);
   c->acquired&=~SC_OWNER;
  }
  if(c->acquired&SC_FONT) {
   result=ui_font_release(&c->font);
   if(result==UI_FONT_DEFER)return UI_SCENE_MORE;
   if(result!=UI_FONT_DONE)return sc_hold(c,38);
   c->acquired&=~SC_FONT;
  }
  c->uir1_owner.live=0;c->pool_owner.live=0;
  if(c->acquired&SC_GUIDE_LEASE) {
   if(!ui_guide_drop(&((GuideApp *)c)->lease))return sc_hold(c,39);
   c->acquired&=~SC_GUIDE_LEASE;
  }
  if(c->acquired&SC_CHROME) {
   if(!ui_res_drop(&c->chrome))return sc_hold(c,40);
   c->acquired&=~SC_CHROME;
  }
  if(c->acquired&SC_GUIDE) {
   UiGuideReader *r=&((GuideApp *)c)->reader;
   if(r->phase!=UI_GGR_ZERO && r->phase!=UI_GGR_READY && r->phase!=UI_GGR_FAILED) {
    result=r->cancelled?ui_guide_step(r,4096):ui_guide_cancel(r);
    if(result==UI_GUIDE_MORE)return UI_SCENE_MORE;
    if(result!=UI_GUIDE_FAILED)return sc_hold(c,41);
   }
   result=ui_guide_release(r);
   if(result==UI_GUIDE_MORE)return UI_SCENE_MORE;
   if(result!=UI_GUIDE_RELEASED)return sc_hold(c,42);
   c->acquired&=~SC_GUIDE;
  }
  if(c->acquired&SC_UIR) {
   UiResourceReader *r=&c->resource;
   if(!r->cancelled)ui_res_cancel(r);
   if(r->owned) {
    result=ui_res_step(r);
    if(result==UI_RES_MORE)return UI_SCENE_MORE;
    if(result==UI_RES_HELD)return sc_hold(c,43);
   }
   if(!ui_res_release(r))return sc_hold(c,44);
   c->acquired&=~SC_UIR;
  }
  if(c->acquired&SC_BG_ROOTS) {
   if(!ui_bg_destroy(h,&c->bg,x->generation))return sc_hold(c,45);
   c->acquired&=~SC_BG_ROOTS;
  }
  if(c->pool){if(!ui_free38(h,c->pool))return sc_hold(c,46);c->pool=0;}
  if(c->acquired)return sc_hold(c,47);
  if(!ui_free38(h,c))return sc_hold(c,48);
  x->app=0; /* Same invocation; no dereference of c is legal after free. */
 }
 if(sc_zero(h,sizeof(*h))) {
  if(HINFO->indexes[38]==28 && !HINFO->counts[38])return UI_SCENE_EXITED;
  x->flags=1;x->error=49;return UI_SCENE_HOLD;
 }
 /* Normal execution was checked above. A refusal now has no known retry
  * boundary: preserve the resident token/code/manager as terminal HOLD. */
 if(!ui_heap38_destroy(h)){x->flags=1;x->error=49;return UI_SCENE_HOLD;}
 return UI_SCENE_EXITED;
}
