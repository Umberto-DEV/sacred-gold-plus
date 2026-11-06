#include "bg.h"
typedef unsigned int BWord;
typedef unsigned short BHalf;
_Static_assert(sizeof(UiBg)==176, "owned state ARM32 layout");
_Static_assert(__builtin_offsetof(UiBg,windows)==36 && __builtin_offsetof(UiBg,pending)==80 &&
               __builtin_offsetof(UiBg,callbackGeneration)==116 &&
               __builtin_offsetof(UiBg,lowerRoots)==120 && __builtin_offsetof(UiBg,lowerWindows)==136 &&
               __builtin_offsetof(UiBg,lowerRows)==168 && __builtin_offsetof(UiBg,role)==172, "owned state offsets");
#define B_MAGIC 0x55424731u
#define B_CALLBACK_SLOT 0x021D110Cu
#define B_REG32(a) (*(volatile BWord *)(a))
#define B_REG16(a) (*(volatile BHalf *)(a))
static unsigned bg_extent(BWord p,BWord n,BWord lo,BWord hi) {
    return p>=lo && p<hi && n<=hi-p;
}
static unsigned bg_ram(BWord p,BWord n) {
    return !(p&3) && bg_extent(p,n,0x0226EC40,0x023C0000);
}
static unsigned bg_state(const UiBg *b) {
    BWord p=(BWord)b;
    return !(p&3) && (bg_ram(p,sizeof(*b)) || bg_extent(p,sizeof(*b),0x027E0080,0x027E3780));
}
static unsigned bg_overlap(BWord a,BWord n,BWord b,BWord m) {return a<b+m && b<a+n;}
static unsigned bg_heap(const UiHeap *h,unsigned g) {
    BWord p=(BWord)h;
    if((p&3) || !(bg_ram(p,sizeof(*h)) || bg_extent(p,sizeof(*h),0x027E0080,0x027E3780)))return 0;
    if(h->magic!=0x55483831 || h->generation!=g || !g ||
       (h->backing!=0x30000 && h->backing!=0x40000) || h->raw!=h->handle ||
       !bg_ram(h->handle,h->backing) || h->index<4 || h->index>=28)return 0;
    BWord handles=B_REG32(0x021D1584),parents=B_REG32(0x021D1588),raws=B_REG32(0x021D158C),indexes=B_REG32(0x021D1594);
    if(!bg_ram(handles,824) || parents!=handles+116 || raws!=handles+228 || indexes!=handles+662)return 0;
    return *(const unsigned char *)(indexes+38)==h->index &&
        ((BWord *)handles)[h->index]==h->handle && ((BWord *)parents)[h->index]==h->parent &&
        ((BWord *)raws)[h->index]==h->raw && *(BWord *)h->handle==0x45585048 &&
        ((BWord *)h->handle)[6]==h->handle+0x38 && ((BWord *)h->handle)[7]==h->handle+h->backing;
}
static unsigned bg_count(const UiBg *b) {return b->role?9:5;}
static unsigned bg_all(const UiBg *b) {return b->role?511:31;}
static unsigned bg_attached(const UiBg *b) {return b->role?15:3;}
static unsigned bg_size(unsigned i) {return i==0?360:(i<3 || i==5 || i==6)?2048:21120;}
static void **bg_slot(UiBg *b,unsigned i) {return i<5?&b->roots[i]:&b->lowerRoots[i-5];}
static const void *bg_ptr(const UiBg *b,unsigned i) {return i<5?b->roots[i]:b->lowerRoots[i-5];}
static unsigned bg_role(const UiBg *b) {
    if(b->role>1)return 0;
    if(!b->role) {
        const BWord *p=(const BWord *)b->lowerRoots;
        for(unsigned i=0;i<12;++i)if(p[i])return 0;
        if(b->lowerRows && b->lowerRows!=UI_BG_STATIC_BALL)return 0;
    }
    return 1;
}
static unsigned bg_root(const UiHeap *h,BWord p,unsigned n) {
    if(!bg_ram(p,n) || p<h->handle+0x58 || !bg_extent(p-32,n+32,h->handle,h->handle+h->backing))return 0;
    unsigned found=0;
    for(unsigned i=0;i<16;++i)if(h->acquired[i]==p)++found;
    return found==1 && *(BHalf *)(p-32)==0x5544 && *(BWord *)(p-28)>=n+16 &&
        bg_extent(p-16,*(BWord *)(p-28),h->handle+0x38,h->handle+h->backing) && *(BWord *)(p-4)==38;
}
static unsigned bg_owned(const UiHeap *h,const UiBg *b,unsigned g) {
    if(!bg_state(b) || !bg_heap(h,g) || b->magic!=B_MAGIC || b->generation!=g || !bg_role(b) || b->owned>bg_all(b) ||
       bg_overlap((BWord)b,sizeof(*b),(BWord)h,sizeof(*h)))return 0;
    for(unsigned i=0;i<bg_count(b);++i) {
        BWord p=(BWord)bg_ptr(b,i),n=bg_size(i);
        if(!(b->owned&(1u<<i))) {if(p)return 0;continue;}
        if(!bg_root(h,p,n))return 0;
        /* Include the validated native block header and GF wrapper in ownership. */
        if(bg_overlap(p-32,n+32,(BWord)b,sizeof(*b)) || bg_overlap(p-32,n+32,(BWord)h,sizeof(*h)))return 0;
        for(unsigned j=0;j<i;++j)if((b->owned&(1u<<j)) && bg_overlap(p-32,n+32,(BWord)bg_ptr(b,j)-32,bg_size(j)+32))return 0;
    }
    return 1;
}
static unsigned bg_empty(const UiBg *b) {
    const BWord *p=(const BWord *)b;for(unsigned i=0;i<sizeof(*b)/4;++i)if(p[i])return 0;return 1;
}
static unsigned bg_detached(const UiBg *b) {
    return !b->attached && !b->callbackOwned &&
        !(B_REG32(B_CALLBACK_SLOT) && B_REG32(B_CALLBACK_SLOT+4)==(BWord)b);
}
unsigned ui_bg_destroy(UiHeap *h,UiBg *b,unsigned g) {
    if(!bg_state(b))return 0;
    if(!b->magic && !b->owned)return bg_empty(b);
    if(!bg_owned(h,b,g) || b->phase!=UI_BG_STORAGE || !bg_detached(b))return 0;
    for(unsigned i=bg_count(b);i>0;--i)if(b->owned&(1u<<(i-1))) {
        if(!ui_free38(h,*bg_slot(b,i-1)))return 0;
        *bg_slot(b,i-1)=0;b->owned&=~(1u<<(i-1));
    }
    BWord *p=(BWord *)b;for(unsigned i=0;i<sizeof(*b)/4;++i)p[i]=0;
    return 1;
}
static unsigned bg_create(UiHeap *h,UiBg *b,unsigned g,unsigned role) {
    if(!bg_state(b) || !bg_heap(h,g) || bg_overlap((BWord)b,sizeof(*b),(BWord)h,sizeof(*h)))return 0;
    const BWord *old=(const BWord *)b;for(unsigned i=0;i<sizeof(*b)/4;++i)if(old[i])return 0;
    b->magic=B_MAGIC;b->generation=g;b->phase=UI_BG_STORAGE;b->role=role;
    b->front=b->pending=b->preparing=UI_BG_NONE;
    for(unsigned i=0;i<bg_count(b);++i) {
        void *p=ui_alloc38(h,bg_size(i),0);
        if(!p){(void)ui_bg_destroy(h,b,g);return 0;}
        *bg_slot(b,i)=p;b->owned|=1u<<i;
    }
    return bg_owned(h,b,g);
}

unsigned ui_bg_create(UiHeap *h,UiBg *b,unsigned g) {return bg_create(h,b,g,0);}
unsigned ui_bg_create_guide(UiHeap *h,UiBg *b,unsigned g) {return bg_create(h,b,g,1);}

#define B_EX ((void (*)(UiNativeBgConfig360 *,unsigned,const UiNativeBgTemplate28 *,unsigned,unsigned))0x0201AD0D)
#define B_A ((void (*)(unsigned))0x02022C9D)
#define B_B ((void (*)(unsigned))0x02022D05)
#define B_HBLANK ((void (*)(void))0x0201A109)
#define B_CALLBACK ((void (*)(void (*)(void *),void *))0x0201A0FD)
#define B_BANKS ((void (*)(const void *))0x02022BE9)
#define B_MODES ((void (*)(const void *))0x0201ACB1)
#define B_CHAR ((void (*)(UiNativeBgConfig360 *,unsigned,const void *,unsigned,unsigned))0x0201C0C1)
#define B_MAP ((void (*)(UiNativeBgConfig360 *,unsigned))0x0201BF7D)
#define B_FILL ((void (*)(UiNativeWindow16 *,unsigned))0x0201D979)
#define B_RING ((void (*)(UiNativeWindow16 *,unsigned,unsigned))0x0200E949)
#define B_DRAIN ((void (*)(void))0x020D28B8)
#define B_DISABLE ((unsigned (*)(void))0x020D3A38)
#define B_RESTORE ((unsigned (*)(unsigned))0x020D3A4C)
static void bg_barrier(void) {__asm__ volatile("" ::: "memory");B_DRAIN();}
static unsigned bg_source(const UiBg *b,const void *v,unsigned n) {
    BWord p=(BWord)v;
    if((p&3) || !bg_extent(p,n,0x02000000,0x02400000) || bg_overlap(p,n,(BWord)b,sizeof(*b)))return 0;
    for(unsigned i=0;i<bg_count(b);++i)if(bg_overlap(p,n,(BWord)bg_ptr(b,i),bg_size(i)))return 0;
    return 1;
}
static unsigned bg_request(const UiBg *b,const void *v,unsigned n) {
    BWord p=(BWord)v;
    return bg_source(b,v,n) || (!(p&3) && bg_extent(p,n,0x027E0080,0x027E3780) &&
                              !bg_overlap(p,n,(BWord)b,sizeof(*b)));
}
static unsigned bg_descriptor(const UiBg *b,unsigned i) {
    unsigned lower=i>=2, index=i&1, bg=lower?index+4:index+1;
    const UiNativeWindow16 *w=lower?&b->lowerWindows[index]:&b->windows[index];
    const UiNativeBgConfig360 *c=b->roots[0];
    const UiNativeBackground44 *d=&c->bgs[bg];
    return c->heapID==38 && !c->scrollScheduled && !c->transferScheduled &&
        w->bg==c && w->bgId==bg && w->x==1 && w->y==1 && w->width==30 && w->height==22 &&
        w->palette==13 && w->baseTile==1 && w->pixels==bg_ptr(b,(lower?7:3)+index) &&
        d->map==bg_ptr(b,(lower?5:1)+index) && d->size==2048 && !d->baseTile && !d->mode && d->screenSize==1 &&
        !d->colorMode && d->tileSize==32 && !d->hOffset && !d->vOffset && !d->rotation &&
        d->xScale==0x1000 && d->yScale==0x1000 && !d->centerX && !d->centerY;
}
static unsigned bg_banks_coherent(void);
static unsigned bg_layout(const UiBg *b) {
    unsigned planes=b->front<2?2u<<b->front:0;
    unsigned lower=b->front<2?(b->lowerRows==UI_BG_STATIC_BALL?1:b->role?1u<<b->front:0):0;
    return bg_role(b) && b->front<=UI_BG_NONE && (B_REG32(0x04000000)&0x1F00)==(planes<<8) &&
        B_REG32(0x021D2200)==planes && B_REG32(0x021D21FC)==lower &&
        B_REG16(0x021E15C2)==1 && bg_banks_coherent() &&
        (B_REG32(0x04000000)&0x7F03E087)==0x10000 &&
        (B_REG32(0x04001000)&0x3FF87)==(0x10000|(lower<<8)) &&
        (!(b->role || b->lowerRows==UI_BG_STATIC_BALL) || (B_REG16(0x04001008)==0x1E01 && (!b->role || B_REG16(0x0400100A)==0x1F11))) && B_REG16(0x0400000A)==0x1E01 && B_REG16(0x0400000C)==0x1F11 &&
        (B_REG16(0x04000304)&0x8203)==0x8203;
}
static void bg_palette(BWord dest,const void *src) {
    const BHalf *p=src;for(unsigned i=0;i<16;++i)((volatile BHalf *)dest)[i]=p[i];bg_barrier();
}
/* Bounded known predecessor configurations: native Field and this canvas.
 * LCDC may retain unused banks; ARM7/clear-image owners are never reclaimed.
 * Field table is field/fieldmap.c ov01_021E6028 at the pinned pret revision. */
static unsigned bg_bank_mask(unsigned profile,unsigned j) {
    if(j==1)return profile==1?4:profile==2?1:0;
    if(j==2)return profile==1?96:profile==2?64:0;
    if(j==4)return profile==1?3:0;
    if(j==5)return profile==1?16:0;
    if(j==9)return profile==1?128:profile==2?4:0;
    if(j==10)return profile?256:0;
    return 0;
}
static unsigned bg_bank_control(unsigned profile,unsigned bank) {
    if(profile==1) {
        if(bank==0 || bank==4)return 0x83;
        if(bank==1)return 0x8B;
        if(bank==2 || bank==7)return 0x81;
        if(bank==5 || bank==8)return 0x82;
        if(bank==6)return 0x8A;
    } else if(profile==2) {
        if(bank==0)return 0x81;
        if(bank==2)return 0x84;
        if(bank==6 || bank==8)return 0x82;
    }
    return 0;
}
/* WVR's successful termination releases the OS VRAM lock and clears its
 * mask/argument/callback, but leaves D mapped to ARM7 (82). Its allocated
 * lock ID persists. Accept only that retired native tuple, never an active
 * ARM7 owner. Field and canvas do not use D, and neither writes this residue.
 * Native literals: WVR 0209E234; OSi_TryLockVram 020D3DE4/8;
 * OS_GetLockID uses 40..6F and a cleared availability bit at 027FFFB0/B4. */
static unsigned bg_retired_wvr_d(void) {
    unsigned id=B_REG16(0x021D43BC);
    if(id<0x40 || id>=0x70 || B_REG16(0x021D43BE) ||
       B_REG32(0x021D43C0) || B_REG32(0x021D43C4) || B_REG32(0x021D4138) ||
       B_REG32(0x021E1A08))return 0;
    for(unsigned j=0;j<9;++j)if(B_REG16(0x021E1A0C+2*j))return 0;
    unsigned bit=id-0x40;
    return !(B_REG32(0x027FFFB0+4*(bit>>5))&(0x80000000u>>(bit&31)));
}
static unsigned bg_banks_coherent(void) {
    const volatile BHalf *gx=(const volatile BHalf *)0x021E15C0;
    unsigned profile=gx[1]==4?1:gx[1]==1?2:0, used=0;
    for(unsigned j=1;j<13;++j) {
        unsigned mask=bg_bank_mask(profile,j);
        if(gx[j]!=mask)return 0;used|=mask;
    }
    if((gx[0]&~0x1FFu) || (gx[0]&used))return 0;
    for(unsigned i=0;i<9;++i) {
        unsigned expected=bg_bank_control(profile,i);
        if(gx[0]&(1u<<i))expected=0x80;
        unsigned actual=*(volatile unsigned char *)(0x04000240+i+(i>6));
        if(i==3 && !expected && profile && actual==0x82 && bg_retired_wvr_d())continue;
        if(expected?actual!=expected:(actual&0x80)!=0)return 0;
    }
    return 1;
}
unsigned ui_bg_enter_backdrop(UiHeap *h,UiBg *b,unsigned g,const void *fontPalette,unsigned main_rgb555) {
    if(main_rgb555>0x7fffu || !bg_owned(h,b,g) || b->owned!=bg_all(b) || b->phase!=UI_BG_STORAGE || b->fontReady || b->attached || b->front!=UI_BG_NONE || b->pending!=UI_BG_NONE || !bg_source(b,fontPalette,32))return 0;
    unsigned irq=B_DISABLE();B_RESTORE(irq);
    if(irq || B_REG32(0x04000208)!=1 || (B_REG16(0x04000304)&0x203)!=0x203 ||
       B_REG32(0x02110C7C)!=1 || (B_REG32(0x02110C80)!=3 && B_REG32(0x02110C80)!=0xFFFFFFFF) ||
       B_REG32(B_CALLBACK_SLOT) || B_REG32(B_CALLBACK_SLOT+8) || (B_REG32(0x04000064)&0x80000000))return 0;
    for(unsigned ch=0;ch<4;++ch)if(B_REG32(0x040000B8+12*ch)&0x80000000)return 0;
    if(!bg_banks_coherent())return 0;
    b->phase=UI_BG_DISPLAY;
    B_REG16(0x0400006C)=0x8010;B_REG16(0x0400106C)=0x8010;
    B_CALLBACK(0,0);B_HBLANK();B_A(0);B_B(0);
    B_REG32(0x04000000)&=~0xE080u;
    /* GXS_DispOn's MODE_MASK is bit16. Mode0 is display-off, not backdrop.
     * Keep SUB in normal graphics with no planes and a black palette[0]. */
    B_REG32(0x04001000)=(B_REG32(0x04001000)&~0x3E080u)|0x10000u;
    B_REG32(0x04000064)=0;
    for(unsigned i=0;i<3;++i){B_REG16(0x04000050+2*i)=0;B_REG16(0x04001050+2*i)=0;}
    B_REG16(0x05000000)=(unsigned short)main_rgb555;B_REG16(0x05000400)=0;
    volatile BWord banks[10],modes[4];
    for(unsigned j=0;j<10;++j)banks[j]=0;
    banks[0]=1;banks[2]=4;banks[4]=64;banks[6]=256;
    for(unsigned j=0;j<4;++j)modes[j]=0;modes[0]=1;
    B_BANKS((const void *)banks);B_MODES((const void *)modes);
    B_REG16(0x04000304)|=0x8000;
    UiNativeBgConfig360 *c=b->roots[0];c->heapID=38;
    for(unsigned i=0;i<(b->role?4u:2u);++i) {
        unsigned lower=i>=2, index=i&1, bg=lower?index+4:index+1;
        UiNativeBgTemplate28 t;
        BWord *tw=(BWord *)&t;for(unsigned j=0;j<7;++j)tw[j]=0;
        t.size=1;t.screenBase=30+index;t.charBase=4*index;t.priority=1;
        B_EX(c,bg,&t,0,0);
        UiNativeBackground44 *d=&c->bgs[bg];
        if(d->map || d->size || d->baseTile || d->mode || d->screenSize!=1 || d->colorMode || d->tileSize!=32 ||
           d->hOffset || d->vOffset || d->rotation || d->xScale!=0x1000 || d->yScale!=0x1000 || d->centerX || d->centerY)return 0;
        d->map=*bg_slot(b,(lower?5:1)+index);d->size=2048;
        UiNativeWindow16 *w=lower?&b->lowerWindows[index]:&b->windows[index];
        w->bg=c;w->bgId=bg;w->x=w->y=1;w->width=30;w->height=22;w->palette=13;w->baseTile=1;w->pixels=*bg_slot(b,(lower?7:3)+index);
        BWord blank[8];for(unsigned j=0;j<8;++j)blank[j]=0;B_CHAR(c,bg,blank,32,0);b->attached|=1u<<i;
    }
    if(!bg_layout(b) || !bg_descriptor(b,0) || !bg_descriptor(b,1))return 0;
    if(b->role && (!bg_descriptor(b,2) || !bg_descriptor(b,3)))return 0;
    bg_palette(0x050001A0,fontPalette);
    if(b->role)bg_palette(0x050005A0,fontPalette);
    b->fontReady=1;
    if(!b->role)B_REG16(0x0400106C)=0;
    return 1;
}
unsigned ui_bg_enter(UiHeap *h,UiBg *b,unsigned g,const void *fontPalette) {
    return ui_bg_enter_backdrop(h,b,g,fontPalette,0);
}
/* Literal CRC identities are metadata only; native pixels remain private ROM
 * inputs. Validate the entire bounded source before touching owned hardware. */
static unsigned bg_crc(const volatile unsigned char *p,unsigned n) {
 unsigned crc=~0u;
 while(n--){crc^=*p++;for(unsigned bit=0;bit<8;++bit)crc=(crc>>1)^((0u-(crc&1))&0xedb88320u);}
 return crc^~0u;
}
unsigned ui_bg_install_ball(UiHeap *h,UiBg *b,unsigned g,const void *compact,unsigned bytes) {
 if(bytes!=3552 || !bg_owned(h,b,g) || b->owned!=bg_all(b) || b->phase!=UI_BG_DISPLAY ||
 !b->fontReady || b->attached!=bg_attached(b) || b->front!=UI_BG_NONE || b->pending!=UI_BG_NONE ||
 b->preparing!=UI_BG_NONE || b->version[0] || b->version[1] || b->lowerRows ||
 !bg_source(b,compact,bytes) || !bg_layout(b) || B_REG32(0x04000208)!=1 ||
 B_REG16(0x0400006C)!=0x8010 || B_REG32(B_CALLBACK_SLOT))return 0;
 const BHalf *src=compact;
 if(bg_crc(compact,3552)!=0xa7f7b946u)return 0;
 for(unsigned i=736;i<1760;++i)if((src[i]&1023)>=46 || (src[i]&0xf000))return 0;
 for(unsigned i=1760;i<1776;++i)if(src[i]>0x7fff)return 0;
 B_REG16(0x0400106C)=0x8010;
 for(unsigned i=0;i<736;++i)((volatile BHalf *)0x06200000)[i]=src[i];
 for(unsigned i=0;i<1024;++i)((volatile BHalf *)0x0620F000)[i]=src[736+i];
 bg_palette(0x05000400,src+1760);
 B_REG16(0x04001008)=0x1e01;B_REG32(0x04001010)=0;
 bg_barrier();b->lowerRows=UI_BG_STATIC_BALL;return 1;
}
static unsigned bg_static_valid(const UiBg *b) {
 return b->lowerRows!=UI_BG_STATIC_BALL ||
 (B_REG32(0x04001010)==0 && bg_crc((const volatile unsigned char *)0x05000400,32)==0x0b1cbb87u);
}
static unsigned bg_begin_allowed(UiHeap *h,UiBg *b,unsigned g,unsigned index) {
    return bg_owned(h,b,g) && b->owned==bg_all(b) && b->phase==UI_BG_DISPLAY && b->fontReady &&
        index<2 && index!=b->front && b->pending==UI_BG_NONE && b->preparing==UI_BG_NONE &&
        bg_descriptor(b,0) && bg_descriptor(b,1) &&
        (!b->role || (bg_descriptor(b,2) && bg_descriptor(b,3))) && bg_layout(b);
}
unsigned ui_bg_begin_retained(UiHeap *h,UiBg *b,unsigned g,unsigned index,unsigned previous,unsigned mask) {
    if(!bg_begin_allowed(h,b,g,index) || b->role || !previous || previous!=b->version[index] ||
       !b->complete || b->rows!=0x3FFFFF || !mask || (mask&~0x3FFFFFu))return 0;
    b->preparing=index;b->rows=0x3FFFFF&~mask;b->complete=1;
    return (BWord)&b->windows[index];
}
unsigned ui_bg_begin_copy(UiHeap *h,UiBg *b,unsigned g,unsigned index,unsigned mask) {
    if(!bg_begin_allowed(h,b,g,index) || b->role || b->front>=2 || !b->version[b->front] ||
       !b->complete || b->rows!=0x3FFFFF || !mask || (mask&~0x3FFFFFu) ||
       (B_REG32(0x02110C80)!=3 && B_REG32(0x02110C80)!=0xFFFFFFFF) ||
       (B_REG32(0x040000DC)&0x80000000))return 0;
    const BHalf *map=b->roots[1+b->front];
    /* Reject native frame/ring palettes and tile ranges before any mutation. */
    for(unsigned i=0;i<1024;++i)if(map[i] &&
       ((map[i]&0xFC00)!=0xD000 || !(map[i]&1023) || (map[i]&1023)>660))return 0;
    b->preparing=index;b->rows=0x3FFFFF&~mask;
    BWord *to=b->roots[3+index];const BWord *from=b->roots[3+b->front];
    for(unsigned i=0;i<21120/4;++i)to[i]=from[i];
    to=b->roots[1+index];from=b->roots[1+b->front];
    for(unsigned i=0;i<2048/4;++i)to[i]=from[i];
    B_CHAR(b->roots[0],index+1,b->roots[3+index],21120,1);
    return (BWord)&b->windows[index];
}
unsigned ui_bg_begin(UiHeap *h,UiBg *b,unsigned g,unsigned index) {
    if(!bg_begin_allowed(h,b,g,index))return 0;
    b->preparing=index;b->rows=0;b->complete=0;
    if(b->lowerRows!=UI_BG_STATIC_BALL)b->lowerRows=0;
    for(unsigned lower=0;lower<=(b->lowerRows==UI_BG_STATIC_BALL?0:b->role);++lower) {
        BHalf *map=*bg_slot(b,(lower?5:1)+index);for(unsigned j=0;j<1024;++j)map[j]=0;
        ((void (*)(UiNativeWindow16 *))0x0201D651)(lower?&b->lowerWindows[index]:&b->windows[index]);
    }
    return (BWord)&b->windows[index];
}

static unsigned bg_mutable(UiHeap *h,UiBg *b,unsigned g) {
    return bg_owned(h,b,g) && b->owned==bg_all(b) && b->phase==UI_BG_DISPLAY && b->preparing<2 &&
        b->preparing!=b->front && b->pending==UI_BG_NONE && bg_descriptor(b,0) && bg_descriptor(b,1) &&
        (!b->role || (bg_descriptor(b,2) && bg_descriptor(b,3))) && bg_layout(b);
}
unsigned ui_bg_begin_guide_retained(UiHeap *h,UiBg *b,unsigned g,unsigned index,const UiBgRetainedPair *p) {
    if(!bg_begin_allowed(h,b,g,index) || !b->role || !bg_request(b,p,sizeof(*p)) ||
       !p->previous || p->previous!=b->version[index] || !b->complete || b->rows!=0x3FFFFF ||
       (b->lowerRows!=UI_BG_STATIC_BALL && b->lowerRows!=0x3FFFFF) ||
       (b->lowerRows==UI_BG_STATIC_BALL && p->lower_dirty) || !(p->upper_dirty|p->lower_dirty) ||
       ((p->upper_dirty|p->lower_dirty)&~0x3FFFFFu))return 0;
    b->preparing=index;b->rows=0x3FFFFF&~p->upper_dirty;if(b->lowerRows!=UI_BG_STATIC_BALL)b->lowerRows=0x3FFFFF&~p->lower_dirty;
    return (BWord)&b->windows[index];
}
unsigned ui_bg_lower_window(UiHeap *h,UiBg *b,unsigned g) {
    if(!bg_mutable(h,b,g) || b->lowerRows==UI_BG_STATIC_BALL || !b->role)return 0;
    return (BWord)&b->lowerWindows[b->preparing];
}
unsigned ui_bg_lower_invalidate_rows(UiHeap *h,UiBg *b,unsigned g,unsigned mask) {
    if(!mask || (mask&~0x3FFFFFu) || !bg_mutable(h,b,g) || b->lowerRows==UI_BG_STATIC_BALL || !b->role)return 0;
    b->lowerRows&=~mask;return 1;
}
unsigned ui_bg_lower_fill(UiHeap *h,UiBg *b,unsigned g,unsigned color) {
    if(color>15 || !bg_mutable(h,b,g) || b->lowerRows==UI_BG_STATIC_BALL || !b->role)return 0;
    B_FILL(&b->lowerWindows[b->preparing],color);b->lowerRows=0;return 1;
}
unsigned ui_bg_lower_rows(UiHeap *h,UiBg *b,unsigned g,const UiBgRows *r) {
    if(!bg_mutable(h,b,g) || b->lowerRows==UI_BG_STATIC_BALL || !b->role || !bg_request(b,r,sizeof(*r)) || r->first>=22 || !r->count || r->count>22-r->first ||
       (B_REG32(0x02110C80)!=3 && B_REG32(0x02110C80)!=0xFFFFFFFF) || (B_REG32(0x040000DC)&0x80000000))return 0;
    unsigned i=b->preparing;
    B_CHAR(b->roots[0],i+4,(const unsigned char *)b->lowerRoots[i+2]+960*r->first,960*r->count,1+30*r->first);
    b->lowerRows|=((1u<<r->count)-1)<<r->first;return 1;
}
unsigned ui_bg_unframed(UiHeap *h,UiBg *b,unsigned g) {
    if(!bg_mutable(h,b,g) || b->complete)return 0;
    b->complete=1;return 1;
}
unsigned ui_bg_invalidate_rows(UiHeap *h,UiBg *b,unsigned g,unsigned mask) {
    if(!mask || (mask&~0x3FFFFFu) || !bg_mutable(h,b,g))return 0;
    b->rows&=~mask;return 1;
}
unsigned ui_bg_fill(UiHeap *h,UiBg *b,unsigned g,unsigned color) {
    if(color>15 || !bg_mutable(h,b,g))return 0;
    B_FILL(&b->windows[b->preparing],color);b->rows=0;return 1;
}
unsigned ui_bg_rows(UiHeap *h,UiBg *b,unsigned g,const UiBgRows *r) {
    if(!bg_mutable(h,b,g) || !bg_request(b,r,sizeof(*r)) || r->first>=22 || !r->count || r->count>22-r->first ||
       (B_REG32(0x02110C80)!=3 && B_REG32(0x02110C80)!=0xFFFFFFFF) || (B_REG32(0x040000DC)&0x80000000))return 0;
    unsigned i=b->preparing;
    B_CHAR(b->roots[0],i+1,(const unsigned char *)b->roots[i+3]+960*r->first,960*r->count,1+30*r->first);
    b->rows|=((1u<<r->count)-1)<<r->first;return 1;
}
unsigned ui_bg_frame(UiHeap *h,UiBg *b,unsigned g,const UiBgFrame *f) {
    if(!bg_mutable(h,b,g) || b->complete || !bg_request(b,f,sizeof(*f)) || f->x<3 || f->x>27 || f->y<2 || f->y>21 ||
       !f->width || f->width>28-f->x || !f->height || f->height>22-f->y ||
       f->tileBytes!=576 || f->paletteBytes!=32 || !bg_source(b,f->tiles,576) || !bg_source(b,f->palette,32) ||
       (B_REG32(0x02110C80)!=3 && B_REG32(0x02110C80)!=0xFFFFFFFF) || (B_REG32(0x040000DC)&0x80000000))return 0;
    unsigned i=b->preparing;
    UiNativeWindow16 geometry;
    geometry.bg=b->roots[0];geometry.bgId=i+1;geometry.x=f->x;geometry.y=f->y;geometry.width=f->width;geometry.height=f->height;
    geometry.palette=14+i;geometry.baseTile=0;geometry.pixels=0;
    B_CHAR(b->roots[0],i+1,f->tiles,576,0x3DC);
    bg_palette(0x050001C0+32*i,f->palette);
    B_RING(&geometry,0x3DC,14+i);b->complete=1;return 1;
}
unsigned ui_bg_ready(UiHeap *h,UiBg *b,unsigned g,unsigned version) {
    if(!bg_mutable(h,b,g) || !version || version<=b->version[0] || version<=b->version[1] ||
       b->rows!=0x3FFFFF || (b->role && b->lowerRows!=UI_BG_STATIC_BALL && b->lowerRows!=0x3FFFFF) || !b->complete ||
       (B_REG32(0x02110C80)!=3 && B_REG32(0x02110C80)!=0xFFFFFFFF) || (B_REG32(0x040000DC)&0x80000000))return 0;
    unsigned i=b->preparing;
    B_MAP(b->roots[0],i+1);if(b->role && b->lowerRows!=UI_BG_STATIC_BALL)B_MAP(b->roots[0],i+4);bg_barrier();
    b->version[i]=version;b->pendingVersion=version;b->preparing=UI_BG_NONE;
    __asm__ volatile("" ::: "memory");b->pending=i;return 1;
}
unsigned ui_bg_publish(UiBg *b,unsigned g,unsigned deadline) {
    if(!bg_state(b) || b->magic!=B_MAGIC || b->generation!=g || !g || b->phase!=UI_BG_DISPLAY || !bg_role(b) || b->owned!=bg_all(b) ||
       b->pending>=2 || b->pending==b->front || b->attached!=bg_attached(b) || !b->fontReady || b->rows!=0x3FFFFF || (b->role && b->lowerRows!=UI_BG_STATIC_BALL && b->lowerRows!=0x3FFFFF) || !b->complete || b->preparing!=UI_BG_NONE ||
       !b->pendingVersion || b->version[b->pending]!=b->pendingVersion || deadline<192 || deadline>261)return 0;
    unsigned irq=B_DISABLE(),ok=0;
    /* Recheck the same bank/retired-WVR tuple before the timing sample.
     * A changed owner never makes a prepared frame eligible to publish. */
    if(!bg_banks_coherent() || !bg_layout(b) || !bg_static_valid(b)){B_RESTORE(irq);return 0;}
    unsigned line=B_REG16(0x04000006);
    if(line>=192 && line<=deadline) {
        unsigned i=b->pending;
        B_A(2u<<i);if(b->lowerRows==UI_BG_STATIC_BALL)B_B(1);else if(b->role)B_B(1u<<i);
        if(b->front==UI_BG_NONE) {
            B_REG16(0x0400006C)=0;if(b->role || b->lowerRows==UI_BG_STATIC_BALL)B_REG16(0x0400106C)=0;
        }
        bg_barrier();b->front=i;b->pending=UI_BG_NONE;ok=1;
    }
    B_RESTORE(irq);return ok;
}
static void bg_callback(void *context) {
    UiBg *b=context;
    if(bg_state(b) && b->magic==B_MAGIC && b->callbackOwned)
        (void)ui_bg_publish(b,b->callbackGeneration,b->deadline);
}
unsigned ui_bg_register(UiBg *b,unsigned g,unsigned deadline) {
    if(!bg_state(b) || b->magic!=B_MAGIC || b->generation!=g || !g || b->phase!=UI_BG_DISPLAY || !bg_role(b) || b->owned!=bg_all(b) ||
       deadline<192 || deadline>261 || b->callbackOwned || B_REG32(B_CALLBACK_SLOT))return 0;
    b->deadline=deadline;b->callbackGeneration=g;b->callbackOwned=1;B_CALLBACK(bg_callback,b);return 1;
}
unsigned ui_bg_retire(UiHeap *h,UiBg *b,unsigned g) {
    if(!bg_state(b))return 0;
    if(!b->magic && !b->owned)return bg_empty(b);
    if(!bg_owned(h,b,g))return 0;
    if(b->phase==UI_BG_STORAGE)return bg_detached(b);
    if(b->phase!=UI_BG_DISPLAY || b->attached>bg_attached(b) || B_REG32(B_CALLBACK_SLOT+8) || B_REG32(B_CALLBACK_SLOT+12))return 0;
    for(unsigned i=0;i<(b->role?4u:2u);++i)if((b->attached&(1u<<i)) && !bg_descriptor(b,i))return 0;
    if(b->callbackOwned) {
        if(B_REG32(B_CALLBACK_SLOT)!=(BWord)bg_callback || B_REG32(B_CALLBACK_SLOT+4)!=(BWord)b)return 0;
    } else if(B_REG32(B_CALLBACK_SLOT) || B_REG32(B_CALLBACK_SLOT+4))return 0;
    for(unsigned ch=0;ch<4;++ch)if(B_REG32(0x040000B8+12*ch)&0x80000000)return 0;
    b->phase=UI_BG_CLOSING;b->pending=UI_BG_NONE;b->preparing=UI_BG_NONE;
    if(b->callbackOwned){B_CALLBACK(0,0);b->callbackOwned=0;}
    /* FieldMap_FadeScreen fades both engines in after reconstruction. Keep
     * both hidden until that shared fade, including the lower native menu. */
    B_A(0);B_B(0);B_REG16(0x0400006C)=0x8010;B_REG16(0x0400106C)=0x8010;
    B_REG16(0x05000000)=0;B_REG16(0x05000400)=0;bg_barrier();
    UiNativeBgConfig360 *c=b->roots[0];
    for(unsigned i=0;i<(b->role?4u:2u);++i)if(b->attached&(1u<<i)) {
        unsigned index=i&1,bg=i>=2?index+4:index+1;
        UiNativeWindow16 *w=i>=2?&b->lowerWindows[index]:&b->windows[index];
        c->bgs[bg].map=0;c->bgs[bg].size=0;w->pixels=0;w->bg=0;
    }
    b->attached=0;b->phase=UI_BG_STORAGE;return 1;
}
