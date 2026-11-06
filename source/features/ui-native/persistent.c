#include "persistent.h"
#include "heap_internal.h"
#define PMAGIC 0x31504955u
#define PHOLD UI_PERSISTENT_HELD_MAGIC
#define PIRQ ((HWord (*)(void))0x020D3A90u)
_Static_assert(sizeof(UiPersistent)==40,"persistent token ABI");
#ifdef UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS
_Static_assert(UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS==0x023D7B20u,"fixed reviewed persistent token slot");
_Static_assert(!(UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS&3u),"resident token alignment");
_Static_assert(UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS+sizeof(UiPersistent)==0x023D7B48u,"resident token extent");
#endif
static unsigned penabled(void) {return *(volatile HWord *)0x04000208u==1 && !PIRQ();}
static unsigned pover(HWord p,HWord n,HWord q,HWord z) {return p<q+z && q<p+n;}
static unsigned pplace(const UiPersistent *t) {
    HWord p=(HWord)t;
    return !(p&3) && (
#ifdef UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS
        p==UI_PERSISTENT_RESIDENT_TOKEN_ADDRESS ||
#endif
        hext(p,sizeof(*t),HNATIVE_LO,HNATIVE_HI) || hext(p,sizeof(*t),0x027E0080,0x027E3780));
}
static unsigned pzero(const UiPersistent *t) {
    const HWord *w=(const HWord *)t;
    for(HWord j=0;j<sizeof(*t)/4;++j)if(w[j])return 0;
    return 1;
}
static unsigned pidentity(const UiPersistent *t,HWord g) {
    return pplace(t) && (t->magic==PMAGIC || t->magic==PHOLD) && t->self==(HWord)t && g && t->generation==g;
}
static unsigned pseparate(const UiPersistent *t) {
    HWord p=(HWord)t;
    if(pover(p,sizeof(*t),(HWord)HINFO->handles,824))return 0;
    for(HWord j=0;j<28;++j) {
        HWord h=HINFO->handles[j];
        if(h && pover(p,sizeof(*t),h-(j>=4?16:0),0x38+(j>=4?16:0)))return 0;
    }
    return 1;
}
static unsigned pheap(void) {
    if(!hmeta())return 0;
    HWord s=HINFO->indexes[11];
    if(s<4 || s>=28)return 0;
    HWord h=HINFO->handles[s],parent=HINFO->handles[HINFO->indexes[3]];
    return HINFO->parents[s]==parent && HINFO->raws[s]==h && hheader(h) &&
           hblock(parent,h,((HWord *)h)[7]-h);
}
static unsigned pblock(HWord heap,HWord raw,HWord bytes) {
    HWord need=((bytes+3)&~3u)+16;
    if(!hblock(heap,raw,need))return 0;
    HWord n=*(const HWord *)(raw-12);
    if(n>need+16)return 0;
    HWord p=raw-16,z=n+16;
    if(pover(p,z,(HWord)HINFO->handles,824))return 0;
    for(HWord j=0;j<28;++j) {
        HWord a=HINFO->handles[j];
        if(a && pover(p,z,a-(j>=4?16:0),0x38+(j>=4?16:0)))return 0;
    }
    return 1;
}
static unsigned plive(const UiPersistent *t) {
    if(t->magic!=PMAGIC || !t->root || !t->bytes || t->bytes>0x4000 || !pheap() || !pseparate(t))return 0;
    HWord s=HINFO->indexes[11],h=HINFO->handles[s];
    if(t->index!=s || t->handle!=h || t->raw!=h || t->parent!=HINFO->parents[s] ||
       t->backing!=((HWord *)h)[7]-h || !pblock(h,t->root-16,t->bytes))return 0;
    const HWord *w=(const HWord *)(t->root-16);
    return !w[0] && !w[1] && !w[2] && w[3]==11 && HINFO->counts[11];
}
void *ui_persistent_alloc(UiPersistent *t,HWord bytes,HWord generation) {
    if(!pplace(t) || !bytes || bytes>0x4000 || !generation || !penabled())return 0;
    HWord irq=HDISABLE(),result=0;
    if(!pheap() || !pseparate(t) || HINFO->counts[11]==65535)goto done;
    if(!pzero(t) && !(t->magic==PMAGIC && t->self==(HWord)t && !t->root &&
        t->generation && generation>t->generation))goto done;
    HWord s=HINFO->indexes[11],h=HINFO->handles[s],backing=((HWord *)h)[7]-h;
    /* Bootstrap owner cannot itself inhabit the heap whose allocation may be
     * uncertain. A live caller allocation elsewhere, live SYS frame or explicitly
     * configured durable token suffices; bounds alone do not prove lifetime. */
    if(pover((HWord)t,sizeof(*t),h-16,backing+16))goto done;
    HWord n=(bytes+3)&~3u,raw=(HWord)HALLOC((void *)h,n+16,4);
    if(!raw)goto done;
    /* A pinned NNS success has this shape. Unknown output is retained in a
     * HOLD record, never passed to Free or dereferenced as a payload. */
    t->magic=PHOLD;t->self=(HWord)t;t->generation=generation;t->root=raw+16;
    t->bytes=bytes;t->handle=h;t->parent=HINFO->parents[s];t->raw=h;t->backing=backing;t->index=s;
    if(!pblock(h,raw,bytes))goto done;
    HWord *w=(HWord *)raw;w[0]=0;w[1]=0;w[2]=0;w[3]=11;
    ++HINFO->counts[11];t->magic=PMAGIC;result=raw+16;
done:
    HRESTORE(irq);
    if(result)for(HWord j=0;j<((bytes+3)&~3u);j+=4)*(HWord *)(result+j)=0;
    return (void *)result;
}
unsigned ui_persistent_move(UiPersistent *dst,UiPersistent *src,HWord generation) {
    if(!pplace(dst) || !pidentity(src,generation) || !penabled() ||
       pover((HWord)dst,sizeof(*dst),(HWord)src,sizeof(*src)))return UI_PERSISTENT_REFUSED;
    if(src->magic==PHOLD)return UI_PERSISTENT_HOLD;
    if(!src->root)return UI_PERSISTENT_REFUSED;
    HWord irq=HDISABLE(),result=UI_PERSISTENT_REFUSED;
    if(!plive(src)) {result=UI_PERSISTENT_HOLD;goto done;}
    if(!pseparate(dst))goto done;
    HWord p=src->root,n=*(const HWord *)(p-28);
    if(pover((HWord)dst,sizeof(*dst),p-32,n+16) && !hext((HWord)dst,sizeof(*dst),p,p+src->bytes))goto done;
    if(!pzero(dst))goto done;
    HWord *d=(HWord *)dst,*s=(HWord *)src;
    for(HWord j=0;j<sizeof(*src)/4;++j)d[j]=s[j];
    dst->self=(HWord)dst;
    for(HWord j=0;j<sizeof(*src)/4;++j)s[j]=0;
    result=UI_PERSISTENT_RELEASED;
done:
    HRESTORE(irq);return result;
}
unsigned ui_persistent_free(UiPersistent *t,HWord generation) {
    if(!pidentity(t,generation) || !penabled())return UI_PERSISTENT_REFUSED;
    if(t->magic==PHOLD)return UI_PERSISTENT_HOLD;
    if(!t->root)return UI_PERSISTENT_REFUSED;
    HWord irq=HDISABLE(),result=UI_PERSISTENT_HOLD;
    if(!plive(t))goto done;
    HWord p=t->root,n=*(const HWord *)(p-28);
    if(pover((HWord)t,sizeof(*t),p-32,n+16))goto done;
    --HINFO->counts[11];HFREE((void *)t->handle,(void *)(p-16));
    HWord *w=(HWord *)t;for(HWord j=3;j<sizeof(*t)/4;++j)w[j]=0;
    result=UI_PERSISTENT_RELEASED;
done:
    HRESTORE(irq);return result;
}
