/* GPL-3.0-or-later. Bounded native Summary host, separate from historical r5.
 * The builder owns and zeroes 64 bytes at 01FF9FC0 for pointers/state/counters.
 * Every dynamic pointer is released before heap19 teardown. */
#include "lease.c"
#include "guide_present.c"
#define DISPLAY (*(volatile u32 *)0x04001000)
#define VRAM ((void *)0x06210000)
#define GPU_MAP ((void *)0x0620F800)
#define VISIBILITY 0x1F00u
#define BADGE_BYTES 2048u
#define MODAL_TILES 289u

typedef struct {
    GuideWindow window;
    u16 *map;
    u32 bytes;
    u16 first,tilecount,mapcount,padding;
    u32 fontScratch[164];
    u32 data[];
} Context;
typedef struct {
    u32 magic;
    Context *context;
    u8 *heap,*summary;
    u32 phase,panel,latch,visibility,opens,frees,failures,badge,pending,allocs,errors,reserved;
} Persistent;
#define P ((volatile Persistent *)0x01FF9FC0)
#ifdef GUIDE_PRESSURE_TEST
#include "summary_pressure_test.h"
#define MODAL_ACQUIRE pressure_acquire
#else
#define MODAL_ACQUIRE lease_acquire
#endif
_Static_assert(sizeof(GuideWindow)==16,"Window ABI");
_Static_assert(sizeof(Persistent)==64,"Persistent reservation");
_Static_assert(sizeof(Context)+2*MODAL_TILES*32+2048<=LEASE_BYTES,"Modal cap");
_Static_assert(sizeof(Context)+2*20*32+40<=BADGE_BYTES,"Badge cap");

static u8 *font_work(void) { return *(u8 **)0x0211188C; }

static int resources(u8 *s)
{
    if (*(u32 *)SYS!=0x020885DD || *(u8 **)(SYS+4)!=s) return 0;
    if (*(volatile u16 *)0x04001008!=0x1F10
        || *(volatile u32 *)0x04000240!=0x82848381
        || *(volatile u16 *)0x04000244!=0x8382
        || *(volatile u8 *)0x04000246!=0x8B
        || *(volatile u16 *)0x04000248!=0x8280) return 0;
    u8 *bg=*(u8 **)s,*f=font_work();
    if (!ram_range((u32)bg,0x168) || !ram_range((u32)f,0xBC)) return 0;
    u8 *b=bg+0xB8,*fd=*(u8 **)(f+0x9C);
    return *(u32 *)bg==19 && ram_range(*(u32 *)b,2048)
        && *(u32 *)(b+4)==2048 && !*(u32 *)(b+8)
        && !*(u32 *)(b+12) && !*(u32 *)(b+16)
        && *(u32 *)(b+20)==0x20000100
        && ram_range((u32)fd,0x80) && !*(u32 *)fd
        && *(u32 *)(fd+4)==0x02026069;
}

static void schedule(u8 *s) { *(u16 *)(*(u8 **)s+6)|=16; }
static int settled(u8 *s) { return !(*(u16 *)(*(u8 **)s+6)&16); }
static void visibility(u32 mask) { DISPLAY=(DISPLAY&~VISIBILITY)|mask; }

static u8 *saved_chars(Context *c) { return (u8 *)c->data; }
static u16 *saved_map(Context *c) { return (u16 *)(saved_chars(c)+c->tilecount*32); }
static u8 *bitmap(Context *c) { return (u8 *)(saved_map(c)+c->mapcount); }

static void font_save(Context *c)
{
    u8 *d=(u8 *)c->fontScratch;
    copy16(d,(void *)0x021D1F6E,6);
    copy16(d+8,(void *)0x021D1F94,512);
    copy16(d+520,font_work(),132);
}
static void font_restore(Context *c)
{
    u8 *d=(u8 *)c->fontScratch;
    copy16((void *)0x021D1F6E,d,6);
    copy16((void *)0x021D1F94,d+8,512);
    copy16(font_work(),d+520,132);
}

static void draw_window(Context *c,u32 x,u32 y,u32 w,u32 h,u32 first,u32 id,u32 disabled)
{
    GuideWindow *v=&c->window;
    v->bg=*(void **)P->summary; v->id=4;v->x=x;v->y=y;v->w=w;v->h=h;v->pal=13;v->tile=first;
    v->pixels=bitmap(c)+(first-c->first)*32;
    fill32(v->pixels,0xEEEEEEEE,w*h*32);
    COLORS(disabled?15:1,14,disabled?14:2);
    guide_line(v,id,(id>=15 && id!=20)?(w*8-TEXT[24+id])/2:0,0);
    for(u32 row=0;row<h;row++) for(u32 col=0;col<w;col++)
        c->map[(y+row)*32+x+col]=0xD000+first+row*w+col;
}

static Context *acquire(u8 *s,u32 badge)
{
    Lease lease={summary_heap(),0};
    if (!lease.heap) return 0;
    if (badge) {
        u32 irq=IRQ_OFF();lease.block=NNS_ALLOC(lease.heap,BADGE_BYTES,4);IRQ_RESTORE(irq);
    } else if (!MODAL_ACQUIRE(&lease)) return 0;
    if (!lease.block) return 0;
    Context *c=(Context *)lease.block;
    fill32(c,0,sizeof(Context));
    c->first=badge?960:1;c->tilecount=badge?20:MODAL_TILES;c->mapcount=badge?20:1024;
    c->map=*(u16 **)(*(u8 **)s+0xB8);c->bytes=badge?BADGE_BYTES:LEASE_BYTES;
    c->padding=0xA6FE;*(u32 *)((u8 *)c+c->bytes-4)=0x6C1EA5ED;
    P->heap=lease.heap;P->context=c;P->allocs++;
    copy16(saved_chars(c),(u8 *)VRAM+c->first*32,c->tilecount*32);
    if (badge) {
        for(u32 i=0;i<20;i++) saved_map(c)[i]=c->map[(18+i/10)*32+21+i%10];
    } else copy16(saved_map(c),c->map,2048);
    return c;
}

static void restore(Context *c)
{
    visibility(c->mapcount==20?(P->visibility&~256u):0);
    copy16((u8 *)VRAM+c->first*32,saved_chars(c),c->tilecount*32);
    if (c->mapcount==20) {
        for(u32 i=0;i<20;i++) c->map[(18+i/10)*32+21+i%10]=saved_map(c)[i];
    } else copy16(c->map,saved_map(c),2048);
    schedule(P->summary);
}

static void release_context(void)
{
    Context *c=P->context;
    if(c && (c->padding!=0xA6FE || *(u32 *)((u8 *)c+c->bytes-4)!=0x6C1EA5ED)) P->errors|=1;
    Lease l={P->heap,(volatile u32 *)c};
    if (lease_release(&l)) P->frees++;
    P->context=0;P->heap=0;P->badge=0;
}

static void badge_remove(void)
{
    if (!P->badge || !P->context) return;
    restore(P->context);release_context();P->pending=1;
}

static void badge_create(u8 *s)
{
    if (!resources(s) || !settled(s) || !(DISPLAY&256)) return;
    u16 *map=*(u16 **)(*(u8 **)s+0xB8);
    for(u32 i=0;i<20;i++) if(map[(18+i/10)*32+21+i%10] || ((volatile u16 *)GPU_MAP)[(18+i/10)*32+21+i%10]) return;
    P->summary=s;P->visibility=DISPLAY&VISIBILITY;
    Context *c=acquire(s,1);
    if(!c) { P->failures++;return; }
    P->badge=1;visibility(P->visibility&~256u);
    font_save(c);draw_window(c,21,18,10,2,960,15,0);border(&c->window,15);font_restore(c);
    copy16((u8 *)VRAM+960*32,bitmap(c),640);schedule(s);P->pending=1;
}

/* Only plain font0 glyphs are borrowed. The three body rows share one native
 * 28x6 Window; each other element owns its distinct tile extent. */
static void modal_draw(Context *c)
{
    u32 panel=P->panel;
    font_save(c);
    fill32(bitmap(c),0xEEEEEEEE,MODAL_TILES*32);
    for(u32 i=0;i<1024;i++) c->map[i]=0xD001;
    draw_window(c,2,3,20,2,2,panel*4,0);
    draw_window(c,27,3,3,2,42,21+panel,0);
    u32 body=(panel==2 && *(volatile u32 *)(SYS+0x34)==3)?12:panel*4+1;
    draw_window(c,2,7,28,6,48,body,0);
    guide_line(&c->window,body+1,0,16);guide_line(&c->window,body+2,0,32);
    draw_window(c,2,16,12,2,216,20,0);
    draw_window(c,2,20,9,2,240,16,panel==0);border(&c->window,panel==0?2:15);
    draw_window(c,12,20,8,2,258,panel==2?18:17,0);border(&c->window,15);
    draw_window(c,22,20,8,2,274,19,0);border(&c->window,15);
    font_restore(c);
    copy16((u8 *)VRAM+32,bitmap(c),MODAL_TILES*32);schedule(P->summary);
}

static int maps_equal(u8 *s)
{
    u16 *cpu=*(u16 **)(*(u8 **)s+0xB8);volatile u16 *gpu=GPU_MAP;
    for(u32 i=0;i<1024;i++) if(cpu[i]!=gpu[i]) return 0;
    return 1;
}

static int modal_run(u8 *s)
{
    Context *c=P->context;
    if(P->phase==1) {
        if(!settled(s)) return 1;
        if(!resources(s) || !maps_equal(s) || !(c=acquire(s,0))) {
            P->failures++;visibility(P->visibility);P->phase=7;return 2;
        }
        P->phase=2;
    }
    if(P->phase==2) { modal_draw(c);P->phase=3;return 1; }
    if(P->phase==3) {
        if(settled(s)) { visibility(256);P->phase=4; }
        return 1;
    }
    if(P->phase==4) {
        if(P->latch) { if(released()) P->latch=0;return 1; }
        int event=guide_event();
        if(!event) return 1;
        P->latch=1;
        if(event==3 || (event==2 && P->panel==2)) P->phase=5;
        else if(event==2) { P->panel++;P->phase=2; }
        else if(P->panel) { P->panel--;P->phase=2; }
        if(P->phase!=4) visibility(0);
        return 1;
    }
    if(P->phase==5) { restore(c);P->phase=6;return 1; }
    if(P->phase==6) {
        if(settled(s)) { release_context();P->pending=1;P->phase=7;return 2; }
        return 1;
    }
    if(P->phase==7) {
        /* The first native tail repopulates OAM while hidden; the original
         * post-wait VBlank callback transfers it before this next Main call. */
        if(P->pending) { visibility(P->visibility);P->pending=0; }
        if(released()) { P->phase=0;P->latch=0; }return 2;
    }
    return 0;
}

__attribute__((used,noinline,section(".text")))
int guide_main(u8 *s,int *state)
{
    P->magic=0x47554931;
    if(P->phase) return modal_run(s);
    if(P->pending && P->summary==s && settled(s)) { visibility(P->visibility);P->pending=0; }
    u8 *a=*(u8 **)(s+0x22C);
    int eligible=*state==2 && s[0x7BC]==1 && a[0x12]==0 && (s[0x7BF]>>4)!=1;
    u32 keys=*(volatile u32 *)(SYS+0x48),repeat=*(volatile u32 *)(SYS+0x4C);
    u32 raw=*(volatile u32 *)(SYS+0x3C),touch=*(volatile u16 *)(SYS+0x64);
    if(eligible && P->badge && !P->pending && !((keys&0x307)|(repeat&0xF0))
        && ((raw&8) || (touch && in_rect(168,144,80,16)))) {
        badge_remove();P->pending=0;P->panel=0;P->latch=1;P->phase=1;P->opens++;
        visibility(0);return 1;
    }
    int input=keys || (repeat&0xF0) || touch;
    if(!eligible || input) badge_remove();
    else if(!P->context && !P->pending) badge_create(s);
    return 0;
}

__attribute__((used,noinline,section(".text")))
void guide_cleanup(void)
{
    if(P->context) {
        restore(P->context);
        /* Exit disables callback immediately: commit its borrowed map now,
         * still hidden, before freeing the raw lease and allowing teardown. */
        copy16(GPU_MAP,P->context->map,2048);
        visibility(P->visibility);
        release_context();
    }
    P->summary=0;P->phase=0;P->pending=0;P->latch=0;
}

__attribute__((naked,used,section(".text"))) void eviv_hook(void)
{
    __asm__ volatile(
        "push {r3-r5,lr}\nmovs r4,r1\nldr r3,1f\nblx r3\nmovs r5,r0\nmovs r1,r4\nbl guide_main\n"
        "cmp r0,#0\nbeq 2f\ncmp r0,#2\nbeq 4f\nmovs r0,#0\npop {r3-r5,pc}\n"
        "2: movs r0,r5\nldr r3,3f\nbx r3\n4: ldr r3,5f\nbx r3\n.balign 4\n"
        "1: .word 0x02007291\n3: .word 0x0208842D\n5: .word 0x0208854B\n");
}
__attribute__((naked,used,section(".text"))) void guide_exit_hook(void)
{
    __asm__ volatile(
        "push {r3-r5,lr}\nmovs r5,r0\nldr r3,1f\nblx r3\nmovs r4,r0\nbl guide_cleanup\n"
        "movs r0,r4\nldr r3,2f\nbx r3\n.balign 4\n"
        "1: .word 0x02007291\n2: .word 0x02088575\n");
}
