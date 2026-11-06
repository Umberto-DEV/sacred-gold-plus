#include "heap.h"
#include "heap_internal.h"
_Static_assert(sizeof(UiHeap)==92,"heap token ABI");
static unsigned htoken(const UiHeap *t) {
    HWord p=(HWord)t;
    return !(p&3) && (hext(p,sizeof(*t),HNATIVE_LO,HNATIVE_HI) || hext(p,sizeof(*t),0x027E0080,0x027E3780));
}
static unsigned hsize(HWord n) {return n==0x30000 || n==0x40000;}
static unsigned hseparate(const UiHeap *t) {
    HWord p=(HWord)t, base=(HWord)HINFO->handles;
    if(p<base+824 && base<p+sizeof(*t))return 0;
    for(HWord j=0;j<28;++j) {
        HWord h=HINFO->handles[j];
        if(h && p<h+0x38 && h<p+sizeof(*t))return 0;
    }
    return 1;
}
static unsigned hlive(const UiHeap *t) {
    if(!htoken(t) || t->magic!=HMAGIC || !t->generation || !hsize(t->backing) || !hmeta() || !hseparate(t))return 0;
    volatile HInfo *i=HINFO;
    HWord s=t->index;
    if(s<4 || s>=28 || i->indexes[38]!=s || t->parent!=i->handles[i->indexes[3]] ||
       i->handles[s]!=t->handle || i->parents[s]!=t->parent || i->raws[s]!=t->raw ||
       t->handle!=t->raw || !hheader(t->handle) || !hblock(t->parent,t->raw,t->backing) ||
       ((HWord *)t->handle)[7]!=t->raw+t->backing)return 0;
    return 1;
}
unsigned ui_heap38_create(UiHeap *t,HWord backing,HWord generation) {
    if(!htoken(t) || !hsize(backing) || !generation)return 0;
    HWord irq=HDISABLE(), ok=0;
    volatile HInfo *i=HINFO;
    /* Our own new ledger requires a clean count: unlike unrelated native
     * history, an unexplained heap38 balance is not an admitted lifecycle. */
    if(!hmeta() || !hseparate(t) || i->indexes[38]!=28 || i->counts[38])goto done;
    HWord slot=4;
    while(slot<28 && i->handles[slot])++slot;
    if(slot==28)goto done;
    HWord parent=i->handles[i->indexes[3]];
    HWord raw=(HWord)HALLOC((void *)parent,backing,4);
    if(!raw)goto done;
    /* NNS is pinned, but never publish an output outside its parent envelope. */
    if(!hblock(parent,raw,backing))goto done;
    if((HWord)t<raw+backing && raw<(HWord)t+sizeof(*t)) {
        HFREE((void *)parent,(void *)raw);goto done;
    }
    HWord child=(HWord)HCREATE((void *)raw,backing,0);
    if(!child){HFREE((void *)parent,(void *)raw);goto done;}
    /* Exact native ABI is guaranteed by the pinned constructor. */
    if(child!=raw || !hheader(child) || ((HWord *)child)[7]!=raw+backing) {
        HDESTROY((void *)child);HFREE((void *)parent,(void *)raw);goto done;
    }
    t->magic=HMAGIC;t->generation=generation;t->parent=parent;t->raw=raw;
    t->handle=child;t->backing=backing;t->index=slot;
    for(HWord j=0;j<16;++j)t->acquired[j]=0;
    i->handles[slot]=child;i->parents[slot]=parent;i->raws[slot]=raw;
    i->counts[38]=0;i->indexes[38]=(HByte)slot;ok=1;
done:
    HRESTORE(irq);return ok;
}
void *ui_alloc38(UiHeap *t,HWord bytes,HWord tail) {
    if(!bytes || bytes>0xFFFFFFECu || tail>1 || !htoken(t))return 0;
    HWord irq=HDISABLE(),result=0;
    if(!hlive(t) || HINFO->counts[38]==65535)goto done;
    HWord slot=0;while(slot<16 && t->acquired[slot])++slot;
    if(slot==16)goto done;
    HWord raw=(HWord)HALLOC((void *)t->handle,bytes+16,tail?-4:4);
    if(!raw || !hblock(t->handle,raw,bytes+16))goto done;
    HWord *wrapper=(HWord *)raw;
    wrapper[0]=0;wrapper[1]=0;wrapper[2]=0;wrapper[3]=38;
    result=raw+16;t->acquired[slot]=result;++HINFO->counts[38];
done:
    HRESTORE(irq);
    /* Publication precedes zeroing; contract excludes concurrent consumers. */
    if(result) {
        HWord j=0;
        for(;j+4<=bytes;j+=4)*(HWord *)(result+j)=0;
        for(;j<bytes;++j)((HByte *)result)[j]=0;
    }
    return (void *)result;
}
unsigned ui_free38(UiHeap *t,void *ptr) {
    if(!htoken(t) || !ptr)return 0;
    HWord irq=HDISABLE(),ok=0,p=(HWord)ptr;
    if(!hlive(t) || !HINFO->counts[38])goto done;
    HWord slot=0;while(slot<16 && t->acquired[slot]!=p)++slot;
    if(slot==16 || !hblock(t->handle,p-16,16) || *(const HByte *)(p-4)!=38)goto done;
    HWord end=p-16+*(const HWord *)(p-28);
    if((HWord)t<end && p-16<(HWord)t+sizeof(*t))goto done;
    --HINFO->counts[38];t->acquired[slot]=0;HFREE((void *)t->handle,(void *)(p-16));ok=1;
done:
    HRESTORE(irq);return ok;
}
unsigned ui_heap38_destroy(UiHeap *t) {
    if(!htoken(t))return 0;
    HWord irq=HDISABLE(),ok=0;
    if(!hlive(t) || HINFO->counts[38] || hext((HWord)t,1,t->raw,t->raw+t->backing))goto done;
    for(HWord j=0;j<16;++j)if(t->acquired[j])goto done;
    HWord s=t->index;
    HDESTROY((void *)t->handle);HFREE((void *)t->parent,(void *)t->raw);
    HINFO->handles[s]=0;HINFO->parents[s]=0;HINFO->raws[s]=0;HINFO->indexes[38]=28;
    HWord *words=(HWord *)t;for(HWord j=0;j<sizeof(*t)/4;++j)words[j]=0;ok=1;
done:
    HRESTORE(irq);return ok;
}
