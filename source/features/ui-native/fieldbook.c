/* GPL-3.0-or-later. Conditional B6 field-menu successor, not an installer. */
#include "fieldbook.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define U32(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define U16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define U8(p,o) (*((u8 *)(p)+(o)))
#define N(t,a) ((t)((a)|1u))
#define API __attribute__((used,noinline,section(".text")))
#define SYS ((volatile u8 *)0x021D110C)
#define KEYS U32(SYS,0x48)
#define HELD U32(SYS,0x44)
#define LABELS ((const u16 *)0x023D7C40)
#define TEMPLATE ((const void *)0x023D7B10)
#define MAGIC 0x314B4246u
#define SELECTED 1u
#define COMMAND 2u
#define ARMED 4u
#define READY 8u
#define Sound N(void (*)(u32),0x0200604C)
#define Field N(u8 *(*)(void *),0x0205064C)
#define Env N(u8 *(*)(void *),0x02050650)
#define Data N(u8 *(*)(void *),0x0201F988)
#define FadeDone N(u32 (*)(void),0x0200FB5C)
#define Mode N(void (*)(void *,u32),0x02024B78)
#define Palette ((void (*)(const void *,u32,u32))0x020CFD70)
typedef struct {void *bg;u8 id,x,y,w,h,pal;u16 tile;u8 *pixels;} Window;
typedef struct {u16 max,size;u32 magic;u16 data[32];} String;
typedef struct {u32 magic;u8 *menu;void *task;u8 *fs;u32 generation,flags,drawn,press;} State;
#define S ((State *)0x023D7E00)
_Static_assert(sizeof(State)==32,"field state");
_Static_assert(sizeof(Window)==16,"native window");
static int ram(const void *p,u32 size){u32 a=(u32)p;return !(a&3)&&a>=0x02000000u&&a<=0x023C0000u-size;}
static int normal(u8 *m){return !(U32(m,0x51c)&30);}
static u8 *current(u8 *fs){
 if(!ram(fs,0xdc)||fs!=*(u8 **)0x021D4158)return 0;
 void *t=(void *)U32(fs,0xd8);if(!ram(t,28))return 0;
 u8 *c=Data(t);if(!ram(c,16)||U16(c,0)!=0x100||U32(c,8)!=(u32)fs)return 0;
 t=(void *)U32(c,4);if(!ram(t,28)||U32(t,20)!=(u32)fieldbook_frame)return 0;
 u8 *m=Data(t);if(!ram(m,0x540)||U32(m,8)!=(u32)t||U32(m,16)!=(u32)fs||!normal(m))return 0;
 return m;
}
static int own(u8 *m){return S->magic==MAGIC&&m&&m==S->menu&&m==current(S->fs)&&U32(m,8)==(u32)S->task;}
static void cancel(u8 *fs){
 if((S->flags&COMMAND)&&fs==S->fs&&own(current(fs))&&U16(fs,0xd0)==32)U16(fs,0xd0)=0;
 S->flags&=READY;S->press=0;S->drawn=0;
}
static void unfocus(u8 *m){
 for(u32 i=0;i<9;i++){void *s=(void *)U32(m,0x390+4*i);if(s)Mode(s,1);}
}
API void fieldbook_focus(void **sprites,u32 index){
 u8 *m=(u8 *)sprites-0x390;
 if(own(m)&&(S->flags&SELECTED))unfocus(m);
 else N(void (*)(void **,u32),0x0225B4AC)(sprites,index);
}
static void select(u8 *m){
 S->flags|=SELECTED;S->drawn=0;unfocus(m);
 /* Clear every palette bank, including sprites in a retired/disabled slot. */
 for(u32 i=0;i<7;i++)Palette(m+0x4cc,i*32,32);
}
static void press(u8 *m){
 if(!(S->flags&ARMED)||S->press||U16(S->fs,0xd0)||U32(m,0x51c)&32)return;
 select(m);S->flags=(S->flags|COMMAND)&~ARMED;S->press=9;U16(S->fs,0xd0)=32;
}
static void pixel(Window *w,u32 x,u32 y,u32 c){
 u32 p=((y>>3)*8+(x>>3))*32+(y&7)*4+((x&7)>>1);u8 old=w->pixels[p];
 w->pixels[p]=(x&1)?((old&15)|(c<<4)):((old&240)|c);
}
static void rect(Window *w,u32 x,u32 y,u32 width,u32 height,u32 c){
 for(u32 j=y;j<y+height;j++)for(u32 i=x;i<x+width;i++)pixel(w,i,j,c);
}
static int draw(u8 *m,u32 visual){
 Window w={0};
 N(void (*)(void *,Window *,u32,u32,u32,u32,u32,u32,u32),0x0201D40C)((void *)U32(m,0x460),&w,4,12,17,8,4,5,0x186);
 if(!w.pixels)return 0;
 u32 background=*(volatile u16 *)0x05000406;const u16 *pal=(const u16 *)(m+((visual&2)?0x4ec:0x4cc));
 for(u32 i=0;i<16;i++){
  u32 c=pal[i];if(visual==1){u32 result=0;for(u32 shift=0;shift<15;shift+=5)result|=((((c>>shift)&31)*6+((background>>shift)&31)*9)>>4)<<shift;c=result;}
  ((volatile u16 *)0x050004a0)[i]=c;
 }
 *(volatile u16 *)0x050004a2=background;
 N(void (*)(Window *,u32),0x0201D978)(&w,1);
 rect(&w,8,6,40,26,9);rect(&w,10,8,36,11,15);rect(&w,10,19,36,2,3);rect(&w,10,21,36,9,4);
 pixel(&w,8,6,1);pixel(&w,47,6,1);pixel(&w,8,31,1);pixel(&w,47,31,1);
 rect(&w,17,10,22,18,8);rect(&w,18,11,9,15,15);rect(&w,29,11,9,15,15);rect(&w,27,12,2,16,5);
 for(u32 y=14;y<23;y+=4){rect(&w,20,y,5,1,5);rect(&w,31,y,5,1,5);}
 if(S->press){u32 phase=(9-S->press)>>1;if(phase>2)phase=4-phase;u32 edge=37-phase*4;rect(&w,edge,11,1,15,8);rect(&w,28,11,edge-27,1,8);rect(&w,28,25,edge-27,1,8);}
 N(void (*)(Window *),0x0201D578)(&w);N(void (*)(Window *),0x0201D520)(&w);return 1;
}
API void fieldbook_create(void *menu){
 u8 *m=menu;N(void (*)(void *),0x0225BC84)(m);
 if(S->magic&&S->magic!=MAGIC)return;
 S->flags=0;S->press=0;S->drawn=0;S->menu=0;S->task=0;S->fs=0;
 if(S->generation==0xffffffffu)return;
 ++S->generation;S->magic=MAGIC;
 if(!normal(m))return;
 u32 off=LABELS[0];if(off<2||off>382||(off&1))return;
 String *s=N(String *(*)(u32,u32),0x02026354)(32,8);if(!s)return;
 const u16 *label=(const u16 *)((const u8 *)LABELS+off);u32 n=0;
 /* Native Latin a..z follow A..Z by 26 glyphs. Keep the inherited label
  * table immutable; only this button's temporary String is uppercased. */
 while(n<31&&label[n]!=0xffff){u16 c=label[n];s->data[n]=c>=325&&c<=350?c-26:c;n++;}
 s->data[n]=0xffff;s->size=n;Window *w=(Window *)(m+0x460);
 N(void (*)(Window *,u32),0x0201D978)(w,0);
 u32 width=N(u32 (*)(u32,String *,u32),0x02002F30)(0,s,0);
 N(u32 (*)(Window *,u32,String *,u32,u32,u32,u32,void *),0x020200FC)(w,0,s,width<72?(72-width)/2:0,0,255,0x0e0200,0);
 N(void (*)(Window *),0x0201D578)(w);N(void (*)(String *),0x02026380)(s);
 if(!draw(m,!!(U8((void *)U32(m,16),0xd2)&63)))return;
 S->drawn=1+!!(U8((void *)U32(m,16),0xd2)&63);
 S->menu=m;S->task=(void *)U32(m,8);S->fs=(u8 *)U32(m,16);S->flags=READY;
 if(!(HELD&1)&&!U16(SYS,0x64))S->flags|=ARMED;
}
API void fieldbook_frame(void *task,void *menu){
 u8 *m=menu;int ours=own(m)&&task==S->task;
 if(ours){
  if(KEYS&1026)cancel(S->fs);
  /* Passive native-menu closure clears focus, not the fresh-touch arm. */
  else if(!(S->flags&COMMAND)&&!(U8(S->fs,0xd2)&63)&&(S->flags&SELECTED)){
   S->flags&=~SELECTED;S->drawn=0;
  }
  if(!(HELD&1)&&!U16(SYS,0x64))S->flags|=ARMED;
 }
 N(void (*)(void *,void *),0x0225A320)(task,m);
 if(!ours||!normal(m))return;
 u32 visual=(S->flags&SELECTED)?2:!!(U8(S->fs,0xd2)&63);
 if(S->drawn!=visual+1||(S->press&1)){if(!draw(m,visual))return;S->drawn=visual+1;}
 if(S->press){--S->press;if(!S->press)S->drawn=0;}
}
API int fieldbook_touch(void *menu){
 u8 *m=menu;if(own(m)){
  if(S->flags&COMMAND)return 0;
  if(U16(SYS,0x64)&&U16(SYS,0x60)>=96&&U16(SYS,0x60)<156&&U16(SYS,0x62)>=142&&U16(SYS,0x62)<174&&!(KEYS&240)&&FadeDone()&&!(U32(m,0x51c)&32)&&!N(u32 (*)(void *),0x0205C6D4)((void *)U32(S->fs,0x40))){press(m);if(S->flags&COMMAND)return 0;}
 }
 int result=N(int (*)(void *),0x0225B4D8)(m);
 if(own(m)&&!result){S->flags&=~SELECTED;S->drawn=0;}return result;
}
API void fieldbook_dpad(void *menu){
 u8 *m=menu;u32 k=KEYS;
 if(!own(m)||!normal(m)){N(void (*)(void *),0x0225B404)(m);return;}
 if(k&1026){cancel(S->fs);return;}
 if(S->flags&COMMAND)return;
 if(S->flags&SELECTED){
  if(k&240){u32 next=(k&192)?6:3;
   if(!U8(m,0x470+8*next)){for(next=0;next<7&&!U8(m,0x470+8*next);next++);}
   if(next<7){U32(m,20)=next;N(void (*)(void *,u32),0x0225B398)(m,next);U8(S->fs,0xd3)=N(u32 (*)(void *,u32),0x0225C170)(m,next);S->flags&=~SELECTED;S->drawn=0;Sound(1500);}
  }return;
 }
 u32 old=U32(m,20);
 if(!(U32(m,0x51c)&32)&&((old==6&&(k&128))||(old==3&&(k&16)))){select(m);Sound(1500);return;}
 N(void (*)(void *),0x0225B404)(m);
}
API int fieldbook_task_input(void *tm){
 u8 *fs=Field(tm);u8 *m=current(fs);
 if(own(m)){
  if(KEYS&1026)cancel(fs);
  else if((S->flags&SELECTED)&&(KEYS&1)&&!(S->flags&COMMAND)){press(m);if(!(S->flags&COMMAND))return 0;}
  if(S->flags&COMMAND){
   if(U16(fs,0xd0)!=32||!(U8(fs,0xd2)&63)){cancel(fs);}
   else if(S->press)return 0;
   else if((U8(fs,0xd2)&63)==2&&!N(u32 (*)(void *),0x021F6B00)(fs)&&N(u32 (*)(void *),0x021F6B10)(fs)==1){
    u8 *e=Env(tm);U16(fs,0xd0)=0;S->flags=0;S->menu=0;S->task=0;S->fs=0;
    N(void (*)(void *),0x0203C460)(fs);N(void (*)(void *,u32),0x0203DF64)(fs,1);
    N(void (*)(u32),0x021E636C)(0);U32(e,0x354)=(u32)fieldbook_launch;U16(e,0x26)=4;Sound(1562);return 1;
   }else return 0;
  }
 }
 return N(int (*)(void *),0x0203C47C)(tm);
}
API int fieldbook_launch(void *tm){
 u8 *e=Env(tm);N(void (*)(void *,const void *,void *),0x0203DFB4)(Field(tm),TEMPLATE,0);U32(e,0x354)=(u32)fieldbook_return;return 0;
}
API int fieldbook_return(void *tm){u8 *e=Env(tm);N(void (*)(void *),0x020505C0)(Field(tm));U16(e,0x26)=15;return 0;}
