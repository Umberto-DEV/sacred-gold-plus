/* Compose after heap.c: these private checked helpers share its validated ABI. */
#include "resource.h"
typedef unsigned RWord;
typedef unsigned short RHalf;
typedef unsigned char RByte;
#define RMAGIC 0x55525231u
#define RARC ((volatile RWord *)0x021E3654)
#define RINIT ((void (*)(void *))0x020D7F98)
#define ROPEN ((int (*)(void *,const char *))0x020D8278)
#define RREAD ((int (*)(void *,void *,int))0x020D83CC)
#define RCLOSE ((int (*)(void *))0x020D82C0)
#define RSEEK ((int (*)(void *,int,int))0x020D83DC)
#define RIRQ ((RWord (*)(void))0x020D3A90)
_Static_assert(sizeof(UiResourceReader)==744,"reader private ABI");
_Static_assert(sizeof(UiResourceConfig)==64,"config disk ABI");
static unsigned rr(RWord p,RWord n) {return !(p&3) && (hext(p,n,0x02000000,0x02400000)||hext(p,n,0x027E0080,0x027E3780));}
static unsigned ro(RWord p,RWord n,RWord q,RWord m) {return p<q+m && q<p+n;}
/* Only used inside a synchronous group preceded by hmeta: no native calls,
 * allocation, publication or retained validity token between these checks. */
static unsigned rwrite_range(RWord p,RWord n) {
    if(!(hram(p,n) || (!(p&3) && hext(p,n,0x027E0080,0x027E3780))) ||
       ro(p,n,(RWord)HINFO->handles,824))return 0;
    for(RWord i=0;i<28;++i)if(HINFO->handles[i] && ro(p,n,HINFO->handles[i],0x38))return 0;
    return 1;
}
static unsigned rwritable(RWord p,RWord n) {
    return (hram(p,n) || (!(p&3) && hext(p,n,0x027E0080,0x027E3780))) && hmeta() && rwrite_range(p,n);
}
static unsigned rloc(const UiResourceReader *r) {return hram((RWord)r,sizeof(*r));}
static unsigned rvalid(const UiResourceReader *r) {return rloc(r)&&r->magic==RMAGIC;}
static unsigned rio(void) {return *(volatile RWord *)0x04000208==1 && !RIRQ();}
static unsigned rquiet(const UiResourceReader *r) {return !r->fs[0]&&!r->fs[1]&&!r->fs[6]&&!r->fs[7]&&!(r->fs[3]&0x4F);}
static unsigned rtuple(UiResourceReader *r,unsigned capture) {
    if(*(volatile RWord *)0x021E3638!=1 || RARC[0]!=0x006D6F72 || (RARC[7]&7)!=7 ||
       RARC[10] || RARC[12]!=4104 || RARC[14]!=2902 ||
       !hext(RARC[17],7040,HNATIVE_LO,0x02400000) ||
       RARC[11]!=((RARC[17]+31u)&~31u) || RARC[13]!=RARC[11]+4104 ||
       RARC[18]!=0x020D84C4 || RARC[19]!=0x020D850C ||
       RARC[20]!=0x020D7484 || RARC[21]!=0x020D8514 || RARC[22]!=0x602)return 0;
    for(RWord i=0;i<13;++i) {
        if(capture)r->archive[i]=RARC[10+i];
        else if(r->archive[i]!=RARC[10+i])return 0;
    }
    return 1;
}
/* A 64-byte literal table in the existing executable .text section. A C
 * const with section(".text") produces a second non-executable .text on this
 * compiler; explicit assembler ownership keeps one relocatable text payload.
 * This local symbol is defined here, never an external runtime dependency. */
__asm__(".pushsection .text,\"ax\",%progbits\n.balign 4\n.local r_crc_table\n"
        ".type r_crc_table,%object\nr_crc_table:\n.word 0x00000000,0x1DB71064,0x3B6E20C8,0x26D930AC,0x76DC4190,0x6B6B51F4,0x4DB26158,0x5005713C,0xEDB88320,0xF00F9344,0xD6D6A3E8,0xCB61B38C,0x9B64C2B0,0x86D3D2D4,0xA00AE278,0xBDBDF21C\n"
        ".size r_crc_table,64\n.popsection\n");
extern const RWord r_crc_table[16];
static RWord rcrc(RWord c,const RByte *p,RWord n) {
    while(n--) {
        c^=*p++;c=(c>>4)^r_crc_table[c&15];c=(c>>4)^r_crc_table[c&15];
    }
    return c;
}
static unsigned rconfig(const RWord *c) {
    return c[0]==0x32435255 && c[1]==2 && c[2]<=4 && c[4]==468 && c[5]==51 && c[6]==35380 &&
      c[7]>=53380 && c[7]<=69632 && !(c[7]&3) && c[3]==35380+c[7] && c[8]==48320 &&
      c[11]==0x885AB7FC && c[12]==509 && c[13]==64 && c[14]==7 && !c[15];
}
static unsigned rprefix(UiResourceReader *r) {
    const RWord *p=r->prefix,*c=r->config.word;
    if(p[0]!=0x4352414E || p[1]!=0x0100FFFE || p[2]!=c[3] || p[3]!=0x00030010 ||
       p[4]!=0x46415442 || p[5]!=428 || p[6]!=52 || p[111]!=0x464E5442 || p[112]!=16 ||
       p[113]!=4 || p[114]!=0x00010000 || p[115]!=0x46494D47 || p[116]!=34920+c[7])return 0;
    RWord end=0;
    for(RWord i=0;i<52;++i) {
        RWord a=p[7+2*i],b=p[8+2*i];
        if(a<end || b<a || b>34912+c[7] || (i<51 && b>34912))return 0;
        end=b;
    }
    return p[109]==34912 && p[110]==34912+c[7] &&
      (rcrc(~0u,(const RByte *)p,468)^~0u)==c[9];
}
static unsigned rheader(UiResourceReader *r) {
    const RWord *p=(const RWord *)r->root,*c=r->config.word;
    if(p[0]!=0x32524955 || p[1]!=0x00800002 || p[2]!=c[7] || p[3]!=c[2] || p[4]!=48320 ||
       p[5]!=20 || p[6]!=128 || p[7]!=608 || p[8]!=576 || p[9]!=32 || p[10]!=12288 ||
       p[11]!=32576 || p[12]!=44864 || p[13]!=32 || p[14]!=0x885AB7FC || p[15]!=7 ||
       p[16]!=0xF40F4996 || p[17]!=0xC2A996D5 || p[18]!=0x8A8D4A1F || p[19]!=0x4C2AA4C7 ||
       p[20]!=0x4B83577C || p[21]!=0xA7D8BCBF || p[22]!=0x0A2A0BEF || p[23]!=0x02E114ED ||
       p[24]!=48448 || p[25]<493 || p[25]>1024 || p[26]!=p[25]*8 || p[27]!=48448+p[26] ||
       p[27]>c[7] || !p[28] || (p[28]&1) || p[28]>c[7]-p[27] ||
       p[29]!=1 || p[30]!=8 || p[31])return 0;
    RWord end=p[27]+p[28];
    if(((end+3u) & ~3u)!=c[7])return 0;
    for(RWord i=end;i<c[7];++i)if(((const RByte *)p)[i])return 0;
    r->text_cursor=p[27];return 1;
}
static unsigned rroot(const UiResourceReader *r) {
    if(!r->root)return 1;
    if(!hlive(r->heap) || ro(r->root,r->config.word[7],(RWord)r,sizeof(*r)) ||
       ro(r->root,r->config.word[7],(RWord)r->heap,sizeof(*r->heap)))return 0;
    for(RWord i=0;i<16;++i)if(r->heap->acquired[i]==r->root)
        return hblock(r->heap->handle,r->root-16,r->config.word[7]+16);
    return 0;
}
static UiResPoll rresult(const volatile UiResourceReader *r) {
    if(r->phase==UI_RES_READY)return UI_RES_OK;
    if(r->phase==UI_RES_OWNERSHIP_HOLD)return UI_RES_HELD;
    if(r->phase==UI_RES_FAILED || r->phase==UI_RES_RELEASED)return UI_RES_ERROR;
    return UI_RES_MORE;
}
static UiResPoll rhold(UiResourceReader *r) {r->phase=UI_RES_OWNERSHIP_HOLD;return UI_RES_HELD;}
unsigned ui_res_init(UiResourceReader *r) {
    if(!rloc(r) || !rwritable((RWord)r,sizeof(*r)))return 0;
    RWord *p=(RWord *)r;for(RWord i=0;i<sizeof(*r)/4;++i)p[i]=0;
    r->magic=RMAGIC;return 1;
}
UiResPoll ui_res_begin(UiResourceReader *r,const UiResourceConfig *config,UiHeap *heap) {
    if(!rvalid(r) || (r->phase!=UI_RES_ZERO && r->phase!=UI_RES_RELEASED) || r->generation==~0u ||
       !rr((RWord)config,64) || !hlive(heap) ||
       ro((RWord)r,sizeof(*r),(RWord)heap,sizeof(*heap)) ||
       ro((RWord)r,sizeof(*r),(RWord)HINFO->handles,824) ||
       ro((RWord)r,sizeof(*r),(RWord)config,64) ||
       ro((RWord)heap,sizeof(*heap),(RWord)config,64) || !rconfig(config->word) || !rio())return UI_RES_ERROR;
    for(RWord i=0;i<28;++i)if(HINFO->handles[i] && ro((RWord)r,sizeof(*r),HINFO->handles[i],0x38))return UI_RES_ERROR;
    if(!rtuple(r,1))return UI_RES_ERROR;
    for(RWord i=0;i<16;++i)r->config.word[i]=config->word[i];
    ++r->generation;r->heap=heap;r->owned=r->failed=r->cancelled=r->root=0;
    r->crc=~0u;r->cursor=r->verify=r->entry=r->unit=r->text_cursor=r->previous=r->species=0;
    r->refs=r->font_refs=r->published=r->close_attempts=0;
    for(RWord i=0;i<20;++i)r->fs[i]=0;
    RINIT(r->fs);r->phase=UI_RES_OPEN;return UI_RES_MORE;
}
UiResPoll ui_res_step(UiResourceReader *r) {
    if(!rvalid(r))return UI_RES_ERROR;
    if(r->phase==UI_RES_ZERO)return UI_RES_ERROR;
    if(r->phase==UI_RES_READY || r->phase>=UI_RES_FAILED)return rresult(r);
    if(!rquiet(r) || !rtuple(r,0) || !rroot(r))return rhold(r);
    if(r->owned && (r->fs[2]!=(RWord)RARC || !(r->fs[3]&0x10)))return rhold(r);
    if(r->cancelled){r->failed=1;r->phase=r->owned?UI_RES_CLOSE:UI_RES_FAILED;}
    if(r->phase==UI_RES_FAILED)return UI_RES_ERROR;
    if(r->phase<=UI_RES_CLOSE && !rio())return UI_RES_MORE;
    int ok;
    if(r->phase==UI_RES_OPEN) {
        volatile char full[13];full[0]='r';full[1]='o';full[2]='m';full[3]=':';full[4]='/';full[5]='a';
        full[6]='/';full[7]='0';full[8]='/';full[9]='3';full[10]='/';full[11]='8';full[12]=0;
        ok=ROPEN(r->fs,(const char *)full);
        if(ok)r->owned=1;
        if(!rquiet(r) || !rtuple(r,0))return rhold(r);
        if(!ok) {
            if(r->fs[3]&0x30)return rhold(r);
            r->failed=1;r->phase=UI_RES_FAILED;return UI_RES_ERROR;
        }
        if(r->fs[2]!=(RWord)RARC || !(r->fs[3]&0x10))return rhold(r);
        r->phase=UI_RES_PREFIX;
        if(r->fs[9]>r->fs[10] || r->fs[10]-r->fs[9]!=r->config.word[3] || r->fs[11]!=r->fs[9] || r->fs[8]!=167) {
            r->failed=1;r->phase=UI_RES_CLOSE;
        }
    } else if(r->phase==UI_RES_PREFIX) {
        ok=RREAD(r->fs,r->prefix,468);
        if(!rquiet(r) || !rtuple(r,0))return rhold(r);
        if(ok!=468 || !rprefix(r))r->failed=1;
        if(!r->failed) {
            r->root=(RWord)ui_alloc38(r->heap,r->config.word[7],0);
            if(!r->root)r->failed=1;
        }
        r->phase=r->failed?UI_RES_CLOSE:UI_RES_MEMBER;
    } else if(r->phase==UI_RES_MEMBER) {
        RWord off=r->config.word[6],n=r->config.word[7];
        if(r->fs[9]>r->fs[10] || off>r->fs[10]-r->fs[9] || n>r->fs[10]-r->fs[9]-off)r->failed=1;
        if(!r->failed) {
            ok=RSEEK(r->fs,(int)off,0);
            if(!rquiet(r) || !rtuple(r,0))return rhold(r);
            if(!ok || r->fs[11]<r->fs[9] || r->fs[11]-r->fs[9]!=off)r->failed=1;
        }
        if(!r->failed) {
            ok=RREAD(r->fs,(void *)r->root,(int)n);
            if(!rquiet(r) || !rtuple(r,0))return rhold(r);
            if(ok!=(int)n)r->failed=1;
        }
        r->phase=UI_RES_CLOSE;
    } else if(r->phase==UI_RES_CLOSE) {
        if(!r->owned)return rhold(r);
        if(r->close_attempts!=~0u)++r->close_attempts;
        ok=RCLOSE(r->fs);
        if(!rquiet(r) || !rtuple(r,0))return rhold(r);
        if(!ok) {
            if(r->fs[2]!=(RWord)RARC || !(r->fs[3]&0x10))return rhold(r);
            return UI_RES_MORE;
        }
        if(r->fs[2] || (r->fs[3]&0x30))return rhold(r);
        r->owned=0;r->phase=r->failed?UI_RES_FAILED:UI_RES_VERIFY;
    } else if(r->phase==UI_RES_VERIFY) {
        if(!r->verify) {
            if(!rheader(r)){r->phase=UI_RES_FAILED;return UI_RES_ERROR;}
            r->verify=1;
        }
        if(r->verify==1) {
            RWord n=r->config.word[7]-r->cursor;if(n>8192)n=8192;
            r->crc=rcrc(r->crc,(const RByte *)(r->root+r->cursor),n);r->cursor+=n;
            if(r->cursor<r->config.word[7])return UI_RES_MORE;
            if((r->crc^~0u)!=r->config.word[10]){r->phase=UI_RES_FAILED;return UI_RES_ERROR;}
            r->verify=2;return UI_RES_MORE;
        }
        const RWord *p=(const RWord *)r->root;
        RWord budget=1024;
        while(r->entry<p[25] && budget) {
            const RHalf *e=(const RHalf *)(r->root+48448+8*r->entry);
            RWord id=e[0],units=e[1],off=((const RWord *)e)[1];
            if(!r->unit) {
                if(id<=r->previous || !id || (id>0xFFF && (id<0x1001 || id>0x11ED)) ||
                   !units || units>2048 || off!=r->text_cursor || off>p[27]+p[28] || units*2>p[27]+p[28]-off)goto badtext;
                if(id>=0x1001){if(id!=0x1001+r->species)goto badtext;++r->species;}
            }
            while(r->unit<units && budget) {
                RWord w=*(const RHalf *)(r->root+off+2*r->unit);
                if(r->unit+1==units){if(w!=0xFFFF)goto badtext;}
                else if(!(w>=1 && w<=509) && !(w==0xE000 && id<0x1000))goto badtext;
                ++r->unit;--budget;
            }
            if(r->unit==units){r->text_cursor+=units*2;r->previous=id;++r->entry;r->unit=0;}
        }
        if(r->entry==p[25]) {
            if(r->species!=493 || r->text_cursor!=p[27]+p[28])goto badtext;
            r->phase=UI_RES_READY;
        }
    }
    return rresult(r);
badtext:r->phase=UI_RES_FAILED;return UI_RES_ERROR;
}
UiResPoll ui_res_pump(UiResourceReader *r,unsigned cap) {
    if(!cap||cap>16||!rvalid(r))return UI_RES_ERROR;
    for(unsigned n=0;n<cap;++n) {
        unsigned phase=r->phase,cursor=r->cursor,entry=r->entry,unit=r->unit,verify=r->verify;
        UiResPoll result=ui_res_step(r);
        if(result!=UI_RES_MORE)return result;
        if(r->phase!=UI_RES_VERIFY || r->cancelled ||
           (phase==r->phase && cursor==r->cursor && entry==r->entry && unit==r->unit && verify==r->verify))return result;
    }
    return UI_RES_MORE;
}
void ui_res_cancel(UiResourceReader *r) {
    if(!rvalid(r) || r->phase==UI_RES_RELEASED)return;
    r->cancelled=1;r->failed=1;
    if(r->phase!=UI_RES_OWNERSHIP_HOLD)r->phase=r->owned?UI_RES_CLOSE:UI_RES_FAILED;
}
static unsigned rfontclear(const UiResourceReader *r) {
    if(!r->root || !r->published)return 1;
    RWord w=*(volatile RWord *)0x0211188C;
    if(!w)return 1;
    if(w!=0x02111890)return 0;
    RWord m=*(volatile RWord *)(w+0x9C);
    if(!m)return 1;
    if(!hram(m,0x14))return 0;
    RWord cached=*(volatile RWord *)(m+0x10);
    return !hext(cached,1,r->root,r->root+r->config.word[7]);
}
unsigned ui_res_can_release(const UiResourceReader *r) {
    return rvalid(r) && r->phase!=UI_RES_RELEASED && r->phase!=UI_RES_OWNERSHIP_HOLD &&
      !r->owned && !(r->fs[3]&0x30) && rquiet(r) && !r->refs && !r->font_refs && rroot(r) && rfontclear(r);
}
unsigned ui_res_release(UiResourceReader *r) {
    if(!ui_res_can_release(r))return 0;
    if(r->root && !ui_free38(r->heap,(void *)r->root))return 0;
    r->root=0;r->heap=0;r->phase=UI_RES_RELEASED;return 1;
}
static unsigned rseparate(const UiResourceReader *r,RWord p,RWord n) {
    return !ro(p,n,(RWord)r,sizeof(*r)) &&
      !ro(p,n,(RWord)r->heap,sizeof(UiHeap)) &&
      /* The known root also owns its GF wrapper and native used-block header. */
      (!r->root || !ro(p,n,r->root-32,r->config.word[7]+32));
}
static unsigned rout(const UiResourceReader *r,RWord p,RWord n) {
    return rwritable(p,n) && rseparate(r,p,n);
}
unsigned ui_res_acquire(UiResourceReader *r,UiResourceLease *l,unsigned font) {
    if(!rvalid(r) || r->phase!=UI_RES_READY || font>1 || r->refs==65535 ||
       !rout(r,(RWord)l,sizeof(*l)) || l->reader || l->generation || l->font)return 0;
    l->reader=r;l->generation=r->generation;l->font=font;++r->refs;if(font)++r->font_refs;
    r->published=1;return 1;
}
static unsigned rlease(const UiResourceLease *l) {
    return rr((RWord)l,sizeof(*l)) && rvalid(l->reader) && l->generation==l->reader->generation &&
      l->reader->refs && l->font<=1 && (!l->font || l->reader->font_refs);
}
unsigned ui_res_drop(UiResourceLease *l) {
    if(!rlease(l) || !rout(l->reader,(RWord)l,sizeof(*l)))return 0;
    --l->reader->refs;if(l->font)--l->reader->font_refs;
    l->reader=0;l->generation=l->font=0;return 1;
}
static unsigned rslice(const UiResourceLease *l,RWord off,RWord n,UiResourceSlice *s) {
    if(!rlease(l) || l->reader->phase!=UI_RES_READY || !rout(l->reader,(RWord)s,sizeof(*s)) ||
       ro((RWord)s,sizeof(*s),(RWord)l,sizeof(*l)) || off>l->reader->config.word[7] || n>l->reader->config.word[7]-off)return 0;
    s->data=(const void *)(l->reader->root+off);s->bytes=n;return 1;
}
unsigned ui_res_frame(const UiResourceLease *l,unsigned frame,unsigned palette,UiResourceSlice *s) {
    return frame<20 && palette<2 && rslice(l,128+frame*608+palette*576,palette?32:576,s);
}
unsigned ui_res_glyphs(const UiResourceLease *l,UiResourceSlice *s) {return rlease(l)&&l->font&&rslice(l,12288,32576,s);}
unsigned ui_res_font_palette(const UiResourceLease *l,UiResourceSlice *s) {return rslice(l,44864,32,s);}
unsigned ui_res_text(const UiResourceLease *l,unsigned id,UiResourceSlice *s) {
    if(!rlease(l) || l->reader->phase!=UI_RES_READY)return 0;
    const RWord *p=(const RWord *)l->reader->root;RWord a=0,b=p[25];
    while(a<b) {
        RWord mid=a+(b-a)/2;const RHalf *e=(const RHalf *)(l->reader->root+48448+mid*8);
        if(id==e[0])return rslice(l,((const RWord *)e)[1],e[1]*2,s);
        if(id<e[0])b=mid;else a=mid+1;
    }
    return 0;
}

unsigned ui_res_ball(const UiResourceLease *l,UiResourceSlice *s) {return rslice(l,44896,3552,s);}
