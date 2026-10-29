/* Native HGSS Plus second page. The old controller owns its five settings and
 * windows; this controller stages shiny choices through the explicit owner API. */
#include "extended.h"
#define ENTRY __attribute__((used,noinline,section(".text")))
#define X_FILL 0x88u
#define X_COLOR ((1u<<16)|(15u<<8)|8u)
#define APP_BG(a) (*(void **)((u8 *)(a)+0x14))
#define APP_HEAP(a) (*(u32 *)(a))
static void zero(void *p,u32 n){u8 *b=p;while(n--)*b++=0;}
static void close(int apply);
static u32 panel_y(void){return XSTATE->page||XSTATE->panel?2:SGP_UI->ycont;}
static int ready(void){return XCFG->magic==SGP_SHINY_MAGIC&&XCFG->abi==SGP_SHINY_ABI&&XCFG->bytes>=sizeof(*XCFG);}
static const u16 *words(u32 id){return (const u16 *)((const u8 *)XTEXT+XTEXT[id<X_COUNT?id:X_ERROR_OK]);}
static void copy(String *s,const u16 *t){u32 n=0;while(t[n]!=SGP_EOS&&n+1<s->maxsize){s->data[n]=t[n];n++;}s->data[n]=SGP_EOS;s->size=n;}
static void number(String *s,u32 n,int append){u32 p=1000,d,started=0,i=append?s->size:0;volatile u32 left=n;const u16 *digits=words(X_DIGITS);
 do{d=0;while(left>=p){left-=p;d++;}if(d||started||p==1){s->data[i++]=digits[d];started=1;}p=p==1000?100:(p==100?10:(p==10?1:0));}while(p);
 s->data[i]=SGP_EOS;s->size=i;
}
static void ratio(String *s,u32 a,u32 b){number(s,a,0);s->data[s->size++]=*words(X_SLASH);number(s,b,1);}
static void print(Window *w,String *s,u32 x,u32 color,u32 align){u32 width;if(align){width=FontID_String_GetWidth(0,s,0);if(width>x)width=x;x=align==1?x-width:(x-width)/2;}AddTextPrinterWithColor(w,0,s,x,0,0xff,color,0);}
static void label(Window *w,u32 id,u32 x,u32 color,u32 align){String *s=SGP_UI->stringa;copy(s,words(id));print(w,s,x,color,align);}
static void species(Window *w,u32 id,u32 x,u32 color,u32 align){
 String *s;if(!id){label(w,X_NONE,x,color,align);return;}
 s=FN(String *(*)(u32,u32),0x0200BCDCu)(id,APP_HEAP(XSTATE->app));
 if(s){print(w,s,x,color,align);String_Delete(s);}else{XSTATE->error=SGP_SHINY_UNAVAILABLE;label(w,X_UNAVAILABLE,x,color,align);}
}
static u32 candidate(u32 index){ExtendedState *e=XSTATE;return FN(u32 (*)(void *,const SgpShinySnapshot *,u32,u32),XCFG->candidate)(e->app,&e->snapshot,e->draft.method,index);}
static int dirty(void){ExtendedState *e=XSTATE;return e->draft.mode!=e->snapshot.mode||e->draft.target!=e->snapshot.target;}
static u32 charge(void){return dirty()?0:XSTATE->snapshot.charge;}
static void edited(void){XSTATE->draft.search=0;XSTATE->error=0;}
static u32 odds(void){SgpShinySaved s;zero(&s,sizeof(s));s.mode=XSTATE->draft.mode;s.target=XSTATE->draft.target;s.chain=dirty()?0:XSTATE->snapshot.chain;
 return FN(u32 (*)(const SgpShinySaved *,u32,u32),XCFG->core_denominator)(&s,s.target?s.target:1,0);
}
/* Reuse the owned String after removing every main row window. Only complete
 * the preview printer when its task actually belongs to the native preview. */
static void context(u32 first,u32 second){void *app=XSTATE->app;Window w,*source=(Window *)((u8 *)app+0x54);String *s=SGP_UI->stringa;u32 id;void *task,*printer;
 if(!source->pixels||!source->bgConfig||source->bgId!=5||source->w!=27||source->h!=4)return;
 w.pixels=0;AddWindowParameterized(source->bgConfig,&w,5,source->x,source->y,27,4,source->pal,source->baseTile);
 if(!w.pixels)return;
 id=*((u8 *)app+0x328);if(id<8){task=((void **)0x021D1F74u)[id];if(task){printer=FN(void *(*)(void *),0x0201F988u)(task);if(printer&&((Window **)printer)[1]==source)FN(void (*)(void *,String *,u32),0x021E61A8u)(app,*(String **)((u8 *)app+0x324),1);}}
 FillWindowPixelBuffer(&w,0xff);copy(s,words(first));AddTextPrinterWithColor(&w,0,s,0,0,0xff,G_COLORE,0);copy(s,words(second));AddTextPrinterWithColor(&w,0,s,0,16,0xff,G_COLORE,0);CopyWindowToVram(&w);RemoveWindow(&w);
}
static void help(void){ExtendedState *e=XSTATE;u32 id;
 if(e->error){context(X_ERROR_OK+e->error,X_BACK);return;}
 if(!e->snapshot.available){context(X_LOCK_0,X_LOCK_1);return;}
 if(e->draft.search){context(X_PENDING_0,X_PENDING_1);return;}
 if(e->panel==2&&!e->snapshot.counts[e->draft.method]){context(X_NO_CANDIDATES,X_BACK);return;}
 if(e->panel==1&&!e->snapshot.method_mask){context(X_FIELD_0,X_FIELD_1);return;}
 if(e->panel){id=e->panel==1&&e->row>=2?X_CHARGE_0:X_TARGET_0;}
 else if(e->row==0)id=e->draft.mode?X_PRO_0:X_CLASSIC_0;
 else id=e->row==1?X_TARGET_0:(e->row==2?X_CHAIN_0:(e->row==3?X_ODDS_0:X_HUNT_0));
 context(id,dirty()?X_RESET:id+1);
}
static int draw_row(u32 r){ExtendedState *e=XSTATE;Window w;String *s=SGP_UI->stringa;u32 sel,color,id=0,value=0,showvalue=0,index;
 w.pixels=0;AddWindowParameterized(APP_BG(e->app),&w,1,4,panel_y()+3*r,24,2,13,G_BASETILE+48*r);if(!w.pixels){close(0);return 0;}
 sel=r>0&&r<6&&((e->panel==2?e->list-e->top:e->row)==r-1)&&e->panel!=3;
 color=sel?X_COLOR:G_COLORE;FillWindowPixelBuffer(&w,sel?X_FILL:0xff);
 if(r==0){id=e->panel==1?X_HUNT_TITLE:(e->panel==2?X_TARGET_TITLE:(e->panel==3?X_RULES_TITLE:(e->page?X_SHINY:X_PLUS)));
  label(&w,id,192,G_COLORE,2);label(&w,X_LEFT,4,G_COLORE,0);if(e->panel!=1)label(&w,X_RIGHT,186,G_COLORE,1);
 }else if(r==6){label(&w,e->panel?(e->panel==3?X_NEXT:X_PICK):X_APPLY,4,G_COLORE,0);label(&w,e->panel?X_BACK:X_CANCEL,186,G_COLORE,1);
 }else if(e->panel==3){index=e->rules*5+r-1;if(index<11)label(&w,X_RULE_0+index,8,G_COLORE,0);
 }else if(e->panel==2){index=e->top+r-1;if(index<=e->snapshot.counts[e->draft.method]){if(index)species(&w,candidate(index-1),20,color,0);else label(&w,X_NONE,20,color,0);}
 }else{
  index=r-1;if(sel)label(&w,X_RIGHT,4,color,0);
  if(!e->snapshot.available)color=G_COLORE_OFF;
  if(!e->panel){id=X_MODE+index;if(!e->snapshot.available){value=X_UNAVAILABLE;showvalue=index<4;}else if(index==0){value=e->draft.mode?X_PRO:X_CLASSIC;showvalue=1;}else if(index==1){species(&w,e->draft.target,186,color,1);}else if(index==2){number(s,dirty()?0:e->snapshot.chain,0);print(&w,s,186,color,1);}else if(index==3){ratio(s,1,odds());print(&w,s,186,color,1);}else if(e->draft.search){value=X_QUEUED;showvalue=1;}}
  else{ id=index==0?X_CHOOSE:(index==1?X_METHOD:(index==2?X_CHARGE:(index==3?X_SEARCH:X_RULES)));
   if(index==1){value=e->snapshot.method_mask?X_LAND+e->draft.method:X_UNAVAILABLE;showvalue=1;}else if(index==2){ratio(s,charge(),40);print(&w,s,186,color,1);}}
  label(&w,id,20,color,0);if(showvalue)label(&w,e->snapshot.available?value:X_UNAVAILABLE,186,color,1);
 }
 CopyWindowToVram(&w);RemoveWindow(&w);return 1;
}
static void draw(void){u32 r;Window frame;void *bg;
 if(!SGP_UI->aperta||!XSTATE->app)return;
 bg=APP_BG(XSTATE->app);zero(&frame,sizeof(frame));frame.bgConfig=bg;frame.bgId=1;frame.x=4;frame.y=panel_y();frame.w=24;frame.h=XSTATE->page||XSTATE->panel?20:SGP_UI->altezza;
 FN(void (*)(void *,u32),0x0201CAE0u)(bg,1);
 FillBgTilemapRect(bg,1,G_TILE_BIANCO,4,frame.y,24,frame.h,13);
 DrawFrameAndWindow2(&frame,1,G_CORNICE_TILE,G_CORNICE_PAL);
 if(!XSTATE->page&&!XSTATE->panel){FN(void (*)(void *),XCFG->legacy_draw)(bg);draw_row(0);return;}
 for(r=0;r<7;r++)if(!draw_row(r))return;help();
}
static void initialize(void *app){ExtendedState *e=XSTATE;u32 i;zero(e,sizeof(*e));e->app=app;
 if(ready()&&FN(int (*)(void *,SgpShinySnapshot *),XCFG->snapshot)(app,&e->snapshot)){
  e->draft.epoch=e->snapshot.epoch;e->draft.context=e->snapshot.context;e->draft.revision=e->snapshot.revision;e->draft.mode=e->snapshot.mode;e->draft.target=e->snapshot.target;e->draft.method=e->snapshot.method;
  if(e->draft.method>=5||!(e->snapshot.method_mask&(1u<<e->draft.method))){e->draft.method=0;for(i=0;i<5;i++)if(e->snapshot.method_mask&(1u<<i)){e->draft.method=i;break;}}
  e->error=e->snapshot.status<=7?e->snapshot.status:SGP_SHINY_UNAVAILABLE;
 }draw_row(0);
}
ENTRY u32 extended_open(void *app){u32 result;if(!ready())return 0;result=FN(u32 (*)(void *),XCFG->legacy_open)(app);if(result)initialize(app);return result;}
static void close(int apply){ExtendedState *e=XSTATE;u32 result=0;if(apply&&e->snapshot.available&&(dirty()||e->draft.method!=e->snapshot.method||e->draft.search))result=FN(u32 (*)(void *,const SgpShinyDraft *),XCFG->apply)(e->app,&e->draft);
 if(result){e->error=result<=7?result:SGP_SHINY_UNAVAILABLE;e->page=1;e->panel=0;draw();return;}
 FN(void (*)(u32),XCFG->legacy_close)(apply);zero(e,sizeof(*e));
}
#include "hunt_panel.c"
ENTRY u32 extended_frame(void *app){ExtendedState *e=XSTATE;u32 key=K_NEW,x=K_TOUCH_X,y=K_TOUCH_Y,row,header,footer;int touch=K_TOUCH_NEW;
 if(!ready())return 0;
 if(!SGP_UI->aperta){u32 result=FN(u32 (*)(void *),XCFG->legacy_frame)(app);
  if(!SGP_UI->aperta&&touch&&x>=4&&x<112&&y>=172&&y<192)return extended_open(app);
  if(SGP_UI->aperta)initialize(app);return result;
 }
 if(SGP_UI->app!=app||e->app!=app){zero(e,sizeof(*e));return FN(u32 (*)(void *),XCFG->legacy_frame)(app);}
 if(key&(K_B|K_SELECT)){if(key&K_SELECT||!e->panel)close(0);else back();return 1;}
 header=panel_y()*8;footer=(!e->panel&&!e->page)?(SGP_UI->ycont+3*(SGP_UI->n_righe-1))*8:160;
 if(touch&&x>=32&&x<224&&y>=header&&y<header+24&&(x<56||x>=200)){page(x>=200);return 1;}
 if(!touch&&(key&(K_L|K_R))){page((key&K_R)!=0);return 1;}
 if(touch&&x>=32&&x<224&&y>=footer&&y<footer+24){if(x>=128){if(e->panel)back();else close(0);}else if(e->panel)choose();else close(1);return 1;}
 if(!e->panel&&!e->page){if(!touch&&(key&K_A)){close(1);return 1;}FN(u32 (*)(void *),XCFG->legacy_frame)(app);if(SGP_UI->aperta&&((key&(K_UP|K_DOWN|K_LEFT|K_RIGHT))||touch))draw_row(0);return 1;}
 if(!touch&&(key&K_X)){if(e->snapshot.available){if(e->panel==1){e->panel=3;e->rules=0;}else if(!e->panel){e->root_row=e->row;e->panel=1;e->row=0;}draw();}return 1;}
 if(touch){if(x<32||x>=224||y<40||y>=160)return 1;row=y<64?0:(y<88?1:(y<112?2:(y<136?3:4)));
  if(e->panel==2){if(e->top+row<=e->snapshot.counts[e->draft.method]){e->list=e->top+row;choose();}}
  else if(e->panel==3)page(1);else{e->row=row;if(e->panel)choose();else if(row==0&&x>=128)change(1);else if(row==1){open_list();}else if(row==4&&e->snapshot.available){e->root_row=row;e->panel=1;e->row=0;}draw();}return 1;
 }
 if(key&K_A){if(e->panel)choose();else close(1);return 1;}
 if(key&(K_UP|K_DOWN))move((key&K_DOWN)!=0);
 else if(key&(K_LEFT|K_RIGHT))change((key&K_RIGHT)!=0);
 else return 1;
 draw();return 1;
}
