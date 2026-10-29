/* GPL-3.0-or-later. Native, save-independent field Guide. */
#include "controller.h"
typedef unsigned char u8; typedef unsigned short u16; typedef unsigned int u32;
#define FN(t,a) ((t)((a)|1u))
#define U32(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define U16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define U8(p,o) (*((u8 *)(p)+(o)))
#define API __attribute__((used,noinline,section(".text")))
#define SYS ((volatile u8 *)0x021D110C)
#define KEY (*(volatile u32 *)(SYS+0x48))
#define TX (*(volatile u16 *)(SYS+0x60))
#define TY (*(volatile u16 *)(SYS+0x62))
#define TOUCH (*(volatile u16 *)(SYS+0x64))
#define CFG ((const u32 *)0x023D7B00)
#define RES ((const u8 *)0x023D7B40)
#define TEXT ((const u8 *)0x023D7C40)
#define HEAP 38u
#define EOS 65535u
typedef struct {void *bg;u8 id,x,y,w,h,pal;u16 tile;u8 *pixels;} Window;
typedef struct {u16 max,size;u32 magic;u16 data[128];} String;
typedef struct {u32 magic;u8 *field;u32 selected,pending,drawn;void *bg;String *str;u8 *content;u32 heap,ready,failed,opens,closes;GuideCursor cursor,saved[8];u32 has_saved;Window header,body,footer,top;u32 field_task;u8 *font;u32 press;} State;
#define S ((State *)0x023D7E00)
_Static_assert(sizeof(State)<=240,"owned state bound");
_Static_assert(__builtin_offsetof(State,field_task)==212,"owned task offset");
_Static_assert(__builtin_offsetof(State,press)==220,"confirmation offset");
#define Alloc FN(void *(*)(u32,u32),0x0201AA8C)
#define Free FN(void (*)(void *),0x0201AB0C)
#define HeapCreate FN(u32 (*)(u32,u32,u32),0x0201A910)
#define HeapDestroy FN(void (*)(u32),0x0201A9C4)
#define ReadNarc FN(void (*)(void *,u32,u32),0x02007508)
#define BgAlloc FN(void *(*)(u32),0x0201AC88)
#define InitBg FN(void (*)(void *,u32,const void *,u32),0x0201B1E4)
#define FreeBg FN(void (*)(void *,u32),0x0201BB4C)
#define BgClear FN(void (*)(void *,u32),0x0201CAE0)
#define BgToggle FN(void (*)(u32,u32),0x0201BC28)
#define CharClear FN(void (*)(u32,u32,u32,u32),0x0201C1C4)
#define Banks FN(void (*)(const void *),0x02022BE8)
#define Modes FN(void (*)(const void *),0x0201ACB0)
#define Pal FN(void (*)(u32,u32,u32,u32,u32,u32),0x02007938)
#define Chars FN(void (*)(u32,u32,void *,u32,u32,u32,u32,u32),0x020078F0)
#define Screen FN(void (*)(u32,u32,void *,u32,u32,u32,u32,u32),0x02007914)
#define FontPal FN(void (*)(u32,u32,u32),0x02003030)
#define AddWin FN(void (*)(void *,Window *,u32,u32,u32,u32,u32,u32,u32),0x0201D40C)
#define DelWin FN(void (*)(Window *),0x0201D520)
#define CopyWin FN(void (*)(Window *),0x0201D578)
#define FillWin FN(void (*)(Window *,u32),0x0201D978)
#define Print FN(u32 (*)(Window *,u32,String *,u32,u32,u32,u32,void *),0x020200FC)
#define Width FN(u32 (*)(u32,String *,u32),0x02002F30)
#define StrNew FN(String *(*)(u32,u32),0x02026354)
#define StrDelete FN(void (*)(String *),0x02026380)
#define Fade FN(void (*)(u32,u32,u32,u32,u32,u32,u32),0x0200FA24)
#define FadeDone FN(u32 (*)(void),0x0200FB5C)
#define VBlank FN(void (*)(void *,void *),0x0201A0FC)
#define Sound FN(void (*)(u32),0x0200604C)
#define Field FN(u8 *(*)(void *),0x0205064C)
#define Env FN(u8 *(*)(void *),0x02050650)

/* Font 0 normally reads each glyph from the cartridge. A long page can then
   block input for several frames. Borrow the native renderer with a checked,
   Guide-owned cache; do not take ownership of a cache another app installed. */
API void guide_font_acquire(void){
 u8 *work=*(u8 **)0x0211188C;if(!work||S->font)return;
 u8 *f=*(u8 **)(work+0x9c);if(!f)return;
 u32 size=U32(f,0xc),count=U32(f,0x64);
 if(U32(f,0)!=1||U32(f,4)!=0x02026111||U32(f,0x10)||!size||size>64||!count||count>512)return;
 void *cache=Alloc(HEAP,size*count);if(!cache)return;
 FN(void (*)(void *,u32,u32,u32,void *),0x0200782C)((void *)U32(f,0x54),U32(f,0x58),U32(f,0x5c),size*count,cache);
 U32(f,0x10)=(u32)cache;U32(f,4)=0x02026069;U32(f,0)=0;S->font=f;
}
API void guide_font_release(void){
 u8 *f=S->font;if(!f)return;void *cache=(void *)U32(f,0x10);
 U32(f,0)=1;U32(f,4)=0x02026111;U32(f,0x10)=0;S->font=0;Free(cache);
}

static void copy_cursor(GuideCursor *a,const GuideCursor *b){a->depth=b->depth;a->category=b->category;a->row=b->row;a->scroll=b->scroll;a->page=b->page;}
static void zero(void *p,u32 n){u8 *q=p;while(n--)*q++=0;}
static int normal(u8 *f){return ((U32(f,0x51c)>>1)&15)==0;}
static void clear_selection(void){S->selected=0;S->pending=0;S->drawn=0;S->press=0;}
static void cancel_selection(u8 *fs){if(U16(fs,0xd0)==32)U16(fs,0xd0)=0;clear_selection();}
static void forget_menu(void){clear_selection();S->field=0;S->field_task=0;}
/* f is provided by the currently executing native menu callback, never by an
   old saved pointer. Every constructor also resets ownership, including reuse. */
static int bind_menu(u8 *f){
 if(!normal(f)){cancel_selection((u8 *)U32(f,0x10));forget_menu();return 0;}
 if(S->field!=f || S->field_task!=U32(f,8)){
  cancel_selection((u8 *)U32(f,0x10));S->field=f;S->field_task=U32(f,8);
 }
 return 1;
}
/* Resolve the current menu through the current FieldSystem's live SysTasks.
   Compare an old pointer only as a value; do not dereference it for validation. */
static u8 *current_menu(u8 *fs){
 void *task=(void *)U32(fs,0xd8);if(!task)return 0;
 u8 *controller=FN(u8 *(*)(void *),0x0201F988)(task);
 if(!controller || U8(controller,0)!=0 || U8(controller,1)!=1)return 0;
 void *child=(void *)U32(controller,4);if(!child)return 0;
 u8 *menu=FN(u8 *(*)(void *),0x0201F988)(child);
 if(!menu || U32(menu,8)!=(u32)child || U32(menu,0x10)!=(u32)fs)return 0;
 return menu;
}
static const u16 *label(u32 n){return (const u16 *)(TEXT+((const u16 *)TEXT)[n]);}
static void text(Window *w,String *s,const u16 *t,u32 x,u32 y,u32 col){
 u32 n=0;while(n<127 && t[n]!=EOS){s->data[n]=t[n];n++;}s->data[n]=EOS;s->size=n;
 if(x==~0u){u32 width=Width(0,s,0);x=width<w->w*8?(w->w*8-width)/2:0;}
 Print(w,0,s,x,y,255,col,0);
}
static void pixel(Window *w,u32 x,u32 y,u32 c){
 u32 off=((y>>3)*w->w+(x>>3))*32+(y&7)*4+((x&7)>>1);u8 v=w->pixels[off];
 w->pixels[off]=(x&1)?((v&15)|(c<<4)):((v&240)|c);
}
static void rect(Window *w,u32 x,u32 y,u32 width,u32 height,u32 c){
 for(u32 j=y;j<y+height;j++)for(u32 i=x;i<x+width;i++)pixel(w,i,j,c);
}
static const u8 *category(void){return S->content+12+S->cursor.category*12;}
static const u8 *entry(void){return S->content+12+U16(S->content,8)*12+(U32(category(),4)+S->cursor.row)*16;}
static const u16 *ctext(u32 off){return (const u16 *)(S->content+off);}
static const u8 *page(void){return S->content+U32(S->content,U32(entry(),12)+S->cursor.page*4);}
static u32 digits(u16 *out,u32 value){
 u32 pos=0,started=0,div=1000;
 for(u32 place=0;place<4;place++){
  u32 d=0;while(value>=div){value-=div;d++;}
  if(d||started||place==3){out[pos++]=0x121+d;started=1;}
  div=place==0?100:place==1?10:1;
 }return pos;
}
static void number(Window *w,u32 a,u32 b,u32 x,u32 y){
 u16 tmp[12];u32 n=digits(tmp,a);tmp[n++]=0x1b1;n+=digits(tmp+n,b);tmp[n]=EOS;text(w,S->str,tmp,x,y,0x01020f);
}
static void border(Window *w,u32 x,u32 y,u32 width,u32 height,u32 edge,u32 fill){
 rect(w,x,y,width,height,edge);rect(w,x+1,y+1,width-2,height-2,fill);
}
static void control(u32 x,u32 width,u32 active){border(&S->footer,x,1,width,21,2,active?1:2);}
static void arrow(Window *w,u32 x,u32 y,u32 right,u32 color){
 for(u32 i=0;i<5;i++)rect(w,x+(right?i:4-i),y+i,1,9-i*2,color);
}
static void draw(void){
 State *s=S;GuideCursor *c=&s->cursor;String *st=s->str;
 u32 count=c->depth?U16(category(),2):U16(s->content,8);
 u32 pos=c->depth?c->row:c->category;
 const u16 *subject=c->depth?ctext(U32(entry(),8)):ctext(U32(category(),8));
 FillWin(&s->header,0);FillWin(&s->body,255);FillWin(&s->footer,0);FillWin(&s->top,255);
 rect(&s->header,0,1,224,22,1);
 if(c->depth==1 && count>5){
  u32 left=pos>0,right=pos+1<count;
  border(&s->header,0,1,32,21,2,left?1:2);
  border(&s->header,192,1,32,21,2,right?1:2);
  arrow(&s->header,4,6,0,left?15:1);arrow(&s->header,214,6,1,right?15:1);
  text(&s->header,st,label(9),18,4,left?0x0f0201:0x010202);
  text(&s->header,st,label(10),196,4,right?0x0f0201:0x010202);
  text(&s->header,st,ctext(U32(category(),8)),~0u,4,0x0f0201);
 }else text(&s->header,st,c->depth==2?subject:c->depth?ctext(U32(category(),8)):label(0),8,4,0x0f0201);
 rect(&s->top,0,0,224,22,1);text(&s->top,st,label(0),8,3,0x0f0201);
 border(&s->top,0,30,224,34,7,8);text(&s->top,st,subject,8,40,0x010208);
 text(&s->top,st,c->depth?ctext(U32(category(),8)):label(4),8,76,0x01020f);
 rect(&s->top,8,99,208,1,2);
 text(&s->top,st,label(c->depth==2?7:8),8,106,0x01020f);
 number(&s->top,c->depth==2?c->page+1:pos+1,c->depth==2?U16(entry(),4):count,152,106);
 control(0,60,1);text(&s->footer,st,label(1),3,4,0x0f0201);
 if(c->depth==2){
  const u8 *p=page();
  for(u32 i=0;i<U16(p,0);i++)text(&s->body,st,ctext(U32(p,4+i*4)),8,i*16+4,0x01020f);
  control(64,36,c->page>0);control(104,36,c->page+1<U16(entry(),4));
  text(&s->footer,st,label(9),68,4,c->page?0x0f0201:0x010202);
  arrow(&s->footer,88,6,0,c->page?15:1);
  arrow(&s->footer,108,6,1,c->page+1<U16(entry(),4)?15:1);
  text(&s->footer,st,label(10),124,4,c->page+1<U16(entry(),4)?0x0f0201:0x010202);
  if(U16(p,2)&&s->has_saved<8){
   control(144,80,1);text(&s->top,st,label(5),8,126,0x01020f);text(&s->footer,st,label(6),152,4,0x0f0201);
  }else text(&s->top,st,label(3),8,126,0x01020f);
 }else{
  u32 scroll=c->depth?c->scroll:0;
  for(u32 i=0;i<5 && i+scroll<count;i++){
   u32 sel=(i+scroll==pos);border(&s->body,0,i*24,224,22,sel?7:2,sel?8:15);
   const u8 *r=c->depth?s->content+12+U16(s->content,8)*12+(U32(category(),4)+i+scroll)*16:s->content+12+(i+scroll)*12;
   text(&s->body,st,ctext(U32(r,8)),8,i*24+3,sel?0x010208:0x01020f);
  }
  text(&s->top,st,label(c->depth==1 && count>5?11:2),8,126,0x01020f);
  control(64,32,pos>0);control(100,32,pos+1<count);control(136,88,1);
  text(&s->footer,st,label(2),152,4,0x0f0201);
  for(u32 j=0;j<5;j++){
   rect(&s->footer,79-j,6+j,j*2+1,1,pos?15:1);
   rect(&s->footer,112+j,6+j,9-j*2,1,pos+1<count?15:1);
  }
 }
 CopyWin(&s->header);CopyWin(&s->body);CopyWin(&s->footer);CopyWin(&s->top);
}
API int guide_init(void *manager,int *phase){
 (void)manager;State *s=S;
 if(*phase)return FadeDone()!=0;
 s->bg=0;s->str=0;s->content=0;s->ready=0;s->failed=0;s->heap=0;s->has_saved=0;s->font=0;
 zero(&s->header,4*sizeof(Window));zero(&s->cursor,sizeof(GuideCursor));
 if(!HeapCreate(3,HEAP,0x40000)){s->failed=1;return 1;}s->heap=1;
 s->content=Alloc(HEAP,CFG[1]);if(!s->content){s->failed=1;return 1;}
 ReadNarc(s->content,27,CFG[0]);
 if(U32(s->content,0)!=0x31474753 || U32(s->content,4)!=CFG[1]){s->failed=1;return 1;}
 s->str=StrNew(128,HEAP);s->bg=BgAlloc(HEAP);
 if(!s->str||!s->bg){s->failed=1;return 1;}
 VBlank(0,0);FN(void (*)(void),0x0201A108)();
 FN(void (*)(void),0x02022C54)();FN(void (*)(void),0x02022CBC)();
 *(volatile u32 *)0x04000000 &= ~0x1f00;*(volatile u32 *)0x04001000 &= ~0x1f00;
 Banks(RES);Modes(RES+40);
 *(volatile u16 *)0x04000304 &= 0x7fff;
 FN(void (*)(u32),0x0200FBDC)(0);FN(void (*)(u32),0x0200FBDC)(1);
 for(u32 i=0;i<5;i++){u32 layer=i<3?i:i+1;InitBg(s->bg,layer,RES+56+i*28,0);BgClear(s->bg,layer);CharClear(layer,32,0,HEAP);}
 s->ready=1;
 Pal(72,2,0,0,64,HEAP);Pal(72,3,4,0,64,HEAP);
 Chars(72,7,s->bg,0,0,0,0,HEAP);Chars(72,8,s->bg,4,0,0,0,HEAP);
 Screen(72,17,s->bg,2,0,0,0,HEAP);Screen(72,19,s->bg,4,0,0,0,HEAP);
 /* Keep native title/footer; expand its plain left background across the
    former Options value controls, which have no meaning in this app. */
 u16 *map=*(u16 **)((u8 *)s->bg+8+2*0x2c);
 for(u32 y=3;y<21;y++)for(u32 x=1;x<32;x++)map[y*32+x]=map[y*32+10];
 FN(void (*)(void *,u32),0x0201BF7C)(s->bg,2);
 FontPal(0,0x1a0,HEAP);FontPal(4,0x1a0,HEAP);
 AddWin(s->bg,&s->header,1,2,0,28,3,13,1);
 AddWin(s->bg,&s->body,1,2,5,28,15,13,85);
 AddWin(s->bg,&s->footer,1,2,21,28,3,13,505);
 AddWin(s->bg,&s->top,5,2,3,28,18,13,1);
 if(!s->header.pixels||!s->body.pixels||!s->footer.pixels||!s->top.pixels){s->failed=1;return 1;}
 FN(void (*)(void *,u32,u32,u32,u32,u32),0x0200E644)(s->bg,1,0x258,15,0,HEAP);
 FN(void (*)(void *,u32,u32,u32,u32,u32),0x0200E644)(s->bg,5,0x258,15,0,HEAP);
 FN(void (*)(Window *,u32,u32,u32),0x0200E998)(&s->body,1,0x258,15);
 FN(void (*)(Window *,u32,u32,u32),0x0200E998)(&s->top,1,0x258,15);
 guide_font_acquire();draw();BgToggle(0,0);BgToggle(1,1);BgToggle(2,1);BgToggle(4,1);BgToggle(5,1);
 Fade(0,1,1,0,6,1,HEAP);s->opens++;*phase=1;return 0;
}
static int follow_link(void){
 u16 target=U16(page(),2);if(!target)return 0;
 for(u32 ci=0;ci<U16(S->content,8);ci++){
  const u8 *cat=S->content+12+ci*12;
  for(u32 j=0;j<U16(cat,2);j++){
   const u8 *e=S->content+12+U16(S->content,8)*12+(U32(cat,4)+j)*16;
   if(U16(e,0)==target){copy_cursor(&S->saved[S->has_saved],&S->cursor);S->has_saved++;S->cursor.category=ci;S->cursor.row=j;S->cursor.page=0;return 1;}
  }
 }return 0;
}
API int guide_main(void *manager,int *phase){
 (void)manager;if(S->failed)return 1;if(*phase)return FadeDone()!=0;
 u32 k=KEY;GuideCursor *c=&S->cursor;
 if(!(k&2) && TOUCH){
  if(TY<24)k=c->depth==2?1024:guide_header(TX,c->depth,U16(category(),2));
  else if(TY>=168 && TY<192){k=guide_footer(TX,c->depth,c->depth==2?U16(page(),2):0);}
  else if(c->depth!=2){int row=guide_touch(TX,TY);u32 n=c->depth?U16(category(),2):U16(S->content,8);
   if(row>=0 && (u32)row+(c->depth?c->scroll:0)<n){if(c->depth)c->row=row+c->scroll;else c->category=row;k=1;}}
 }
 if(!(k&2) && c->depth==2 && (k&1024) && S->has_saved<8 && follow_link()){Sound(1562);draw();return 0;}
 if((k&2)&&S->has_saved){S->has_saved--;copy_cursor(&S->cursor,&S->saved[S->has_saved]);Sound(2368);draw();return 0;}
 int result=guide_step(c,k,U16(S->content,8),U16(category(),2),c->depth==2?U16(entry(),4):1);
 if(result==2){Fade(0,0,0,0,6,1,HEAP);*phase=1;Sound(2368);}
 else if(result){Sound((k&2)?2368:(k&1)?1562:1500);draw();}
 return 0;
}
API int guide_exit(void *manager,int *phase){
 (void)manager;(void)phase;State *s=S;
 VBlank(0,0);
 guide_font_release();
 Window *w=&s->header;for(u32 i=0;i<4;i++){if(w[i].pixels){DelWin(w+i);w[i].pixels=0;}}
 if(s->ready)for(u32 i=0;i<5;i++)FreeBg(s->bg,i<3?i:i+1);
 if(s->bg)Free(s->bg);if(s->str)StrDelete(s->str);if(s->content)Free(s->content);
 s->bg=0;s->str=0;s->content=0;if(s->heap)HeapDestroy(HEAP);s->heap=0;s->closes++;forget_menu();
 return 1;
}
API int guide_return(void *tm){u8 *e=Env(tm);FN(void (*)(void *),0x020505C0)(Field(tm));U16(e,0x26)=15;return 0;}
API int guide_launch(void *tm){
 u8 *e=Env(tm);FN(void (*)(void *,const void *,void *),0x0203DFB4)(Field(tm),(const void *)(CFG+4),0);
 U32(e,0x354)=(u32)guide_return;return 0;
}
API int guide_task_input(void *tm){
 u8 *f=Field(tm);u8 *e=Env(tm);
 if(KEY&(2|1024))cancel_selection(f);
 if(S->selected&&(KEY&1)&&!S->pending){S->pending=1;S->press=9;S->drawn=0;}
 if(S->pending){
  u8 *menu=current_menu(f);
  if(!menu || menu!=S->field || U32(menu,8)!=S->field_task || !normal(menu)
     || (U8(f,0xd2)&63)==0){
   cancel_selection(f);forget_menu();
  }else if(S->press){return 0;
  }else if((U8(f,0xd2)&63)==2 && !FN(u32 (*)(void *),0x021F6B00)(f)
            && FN(u32 (*)(void *),0x021F6B10)(f)==1){
   S->pending=0;U16(f,0xd0)=0;
   FN(void (*)(void *),0x0203C460)(f);FN(void (*)(void *,u32),0x0203DF64)(f,1);FN(void (*)(void *),0x021F6B50)(f);
   FN(void (*)(u32),0x021E636C)(0);U32(e,0x354)=(u32)guide_launch;U16(e,0x26)=4;Sound(1562);return 1;
  }
 }
 return FN(int (*)(void *),0x0203C47C)(tm);
}
API void guide_field_create(u8 *f){
 /* Called after the original label initialization during every construction. */
 forget_menu();bind_menu(f);FN(void (*)(void *),0x0225BC84)(f);
}
static void field_draw(u8 *f,u32 title){
 Window *labelwin=(Window *)(f+0x460);Window book;
 if(title){String *str=StrNew(32,8);if(!str)return;
  FillWin(labelwin,0);text(labelwin,str,label(0),~0u,0,0x0e0200);CopyWin(labelwin);StrDelete(str);}
 /* Shared SUB_BG bank5 is unused in the guarded normal field menu. Match
    the native OBJ palette, including its two selected-color changes. */
 const u16 *pal=(const u16 *)(f+(S->selected?0x4ec:0x4cc));
 for(u32 i=0;i<16;i++)((volatile u16 *)0x050004a0)[i]=pal[i];
 /* BG4 is below the native BG5 labels. Its replaced tiles are solid color3;
    keep that background in unused color1, including the cut frame corners. */
 *(volatile u16 *)0x050004a2=*(volatile u16 *)0x05000406;
 zero(&book,sizeof(book));AddWin(labelwin->bg,&book,4,12,17,8,4,5,0x186);
 if(!book.pixels)return;FillWin(&book,1);
 rect(&book,8,6,40,26,9);rect(&book,10,8,36,11,15);
 rect(&book,10,19,36,2,3);rect(&book,10,21,36,9,4);
 pixel(&book,8,6,1);pixel(&book,47,6,1);pixel(&book,8,31,1);pixel(&book,47,31,1);
 pixel(&book,10,8,2);pixel(&book,45,8,2);pixel(&book,10,29,2);pixel(&book,45,29,2);
 /* Original 22x18 book glyph, centered on the native 40px icon frame. */
 rect(&book,17,10,22,18,8);rect(&book,18,11,9,15,15);rect(&book,29,11,9,15,15);
 rect(&book,27,12,2,16,5);
 for(u32 y=14;y<23;y+=4){rect(&book,20,y,5,1,5);rect(&book,31,y,5,1,5);}
 if(S->press){u32 phase=(9-S->press)>>1;if(phase>2)phase=4-phase;
  u32 edge=37-phase*4;rect(&book,edge,11,1,15,8);rect(&book,28,11,edge-27,1,8);rect(&book,28,25,edge-27,1,8);}
 CopyWin(&book);DelWin(&book);
}
API void guide_field_frame(void *task,u8 *f){
 bind_menu(f);
 if((S->selected||S->pending) && ((KEY&(2|1024)) || (!S->pending && (U8((void *)U32(f,0x10),0xd2)&63)==0)))cancel_selection((u8 *)U32(f,0x10));
 FN(void (*)(void *,void *),0x0225A320)(task,f);
 if(!bind_menu(f))return;
 if(!S->drawn || (S->press&1)){field_draw(f,!S->drawn);S->drawn=1;}
 if(S->press){S->press--;if(!S->press)S->drawn=0;}
}
API int guide_touch_input(u8 *f){
 if(bind_menu(f)&&TOUCH && TX>=96&&TX<156&&TY>=142&&TY<174 && FadeDone() && !(U32(f,0x51c)&32)){
  void *fs=(void *)U32(f,0x10);void *avatar=(void *)U32(fs,0x40);
  if(!FN(u32 (*)(void *),0x0205C6D4)(avatar) && !(KEY&240)){
   S->pending=1;S->selected=1;S->drawn=0;S->press=9;**(u16 **)(f+12)=32;return 0;
  }
 }
 int r=FN(int (*)(void *),0x0225B4D8)(f);
 if(!r && !S->pending){S->selected=0;S->drawn=0;}return r;
}
API void guide_dpad(u8 *f){
 if(!bind_menu(f)){FN(void (*)(void *),0x0225B404)(f);return;}
 if(KEY&(2|1024))cancel_selection((u8 *)U32(f,0x10));
 if(S->pending)return;
 u32 key=KEY,old=U32(f,0x14);
 if(S->selected){
  if(key&240){u32 next=(key&(64|128))?6:3;
   if(!U8(f,0x470+next*8))next=6;
   if(U8(f,0x470+next*8)){U32(f,0x14)=next;FN(void (*)(void *,u32),0x0225B398)(f,next);U8((void *)U32(f,0x10),0xd3)=FN(u32 (*)(void *,u32),0x0225C170)(f,next);S->selected=0;S->drawn=0;Sound(1500);}
  }return;
 }
 if((old==6&&(key&128)) || (old==3&&(key&16))){S->selected=1;S->drawn=0;FN(void (*)(void *,u32),0x0225B398)(f,~0u);Sound(1500);return;}
 FN(void (*)(void *),0x0225B404)(f);
}
