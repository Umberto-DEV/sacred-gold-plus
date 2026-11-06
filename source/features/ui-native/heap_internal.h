#ifndef SGP_UI_HEAP_INTERNAL_H
#define SGP_UI_HEAP_INTERNAL_H
/* Shared native topology validation only; no heap38 export bodies or state. */
typedef unsigned int HWord;
typedef unsigned short HHalf;
typedef unsigned char HByte;
typedef struct {
    HWord *handles, *parents, *raws;
    HHalf *counts;
    HByte *indexes;
    HHalf total, templates, max, unallocated;
} HInfo;
#define HINFO ((volatile HInfo *)0x021D1584)
#define HNATIVE_LO 0x0226EC40u
#define HNATIVE_HI 0x023C0000u
#define HMAGIC 0x55483831u
#define HCREATE ((void *(*)(void *,HWord,HWord))0x020B535C)
#define HALLOC ((void *(*)(void *,HWord,int))0x020B53A0)
#define HFREE ((void (*)(void *,void *))0x020B5530)
#define HDESTROY ((void (*)(void *))0x020B5394)
#define HDISABLE ((HWord (*)(void))0x020D3A38)
#define HRESTORE ((HWord (*)(HWord))0x020D3A4C)
_Static_assert(sizeof(HWord)==4 && sizeof(HHalf)==2,"fixed-width native scalars");
_Static_assert(sizeof(HInfo)==28,"native heap info ABI");
static unsigned hext(HWord p,HWord n,HWord lo,HWord hi) {
    return p>=lo && p<hi && n<=hi-p;
}
static unsigned hram(HWord p,HWord n) {return !(p&3) && hext(p,n,HNATIVE_LO,HNATIVE_HI);}
static unsigned hheader(HWord p) {
    if (!hram(p,0x38)) return 0;
    const HWord *h=(const HWord *)p;
    return h[0]==0x45585048 && h[6]==p+0x38 && h[7]>p+0x48 && h[7]<=HNATIVE_HI && !(h[7]&3);
}
/* Native tables are one startup arena allocation: max+1 handles (sentinel),
 * max parents/raws, total halfword counts, total byte indexes. Scalars pinned
 * to the installed native initialization; no arbitrary global owner buffers.
 */
static unsigned hmeta(void) {
    volatile HInfo *i=HINFO;
    HWord p=(HWord)i->handles;
    if(i->total!=161 || i->templates!=4 || i->max!=28 || i->unallocated!=28 ||
       !hram(p,824) || (HWord)i->parents!=p+116 || (HWord)i->raws!=p+228 ||
       (HWord)i->counts!=p+340 || (HWord)i->indexes!=p+662 || i->handles[28]) return 0;
    /* Slots fit in one word. This is a fresh local census on every call,
     * retaining duplicate/orphan checks without rescanning all IDs per slot. */
    HWord seen=0;
    for(HWord id=0;id<161;++id) {
        /* Four inactive non-template IDs have no header/count work. Read only
         * aligned words inside the pinned table, including every byte: a late
         * invalid or duplicate ID breaks the word match and takes the full path.
         * No result survives this call; orphan detection below is unchanged. */
        if(id>=6 && id<=157 && (id&3)==2 &&
           *(const HWord *)(p+662+id)==0x1C1C1C1Cu){id+=3;continue;}
        HWord s=i->indexes[id];
        /* Native Heap_Destroy retires the slot but preserves its historical
         * block count. Unrelated inactive IDs may therefore have stale counts;
         * live-handle validation remains entirely index/topology based. */
        if(s>28 || (id<4 && s!=id))return 0;
        if(s<28) {
            /* Native template2's 0x10 backing is below the 0x4C NNS
             * minimum: InitSystem still publishes index2, handleNULL,count0.
             * Keep duplicate-slot validation below even for this one case. */
            if(!hheader(i->handles[s]) &&
               !(id==2 && s==2 && !i->handles[s] && !i->counts[id]))return 0;
            HWord bit=1u<<s;
            if(seen&bit)return 0;
            seen|=bit;
        }
    }
    for(HWord s=0;s<28;++s)if(i->handles[s]) {
        if(!(seen&(1u<<s)))return 0;
        if(s>=4) {
            HWord parent=i->parents[s], raw=i->raws[s], h=i->handles[s];
            if(!hheader(parent) || !hram(raw,0x38) || h!=raw ||
               raw<((HWord *)parent)[6]+16 || ((HWord *)h)[7]>((HWord *)parent)[7])return 0;
        }
    }
    return i->indexes[3]<28 && hheader(i->handles[i->indexes[3]]);
}
static unsigned hblock(HWord heap,HWord raw,HWord need) {
    const HWord *h=(const HWord *)heap;
    if(raw<h[6]+16 || !hext(raw-16,16,h[6],h[7]) || (raw&3))return 0;
    const HHalf *b=(const HHalf *)(raw-16);
    HWord n=*(const HWord *)(raw-12);
    return b[0]==0x5544 && !(n&3) && n>=need && hext(raw,n,h[6],h[7]);
}
#endif
