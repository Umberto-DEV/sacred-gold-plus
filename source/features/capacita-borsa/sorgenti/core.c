/* Array ownership is explicit: the disk Bag remains 1948 bytes. */
#include "core.h"
u32 cap_count(u32 p) {
    switch(p) {case 0:return 252; case 1:return 42;case 2:return 30;case 3:return 102;
        case 4:return 66;case 5:return 12;case 6:return 30;case 7:return 60;default:return 0;}
}
u32 cap_old_count(u32 p) {
    switch(p) {case 0:return 165;case 1:return 40;case 2:return 24;case 3:return 101;
        case 4:return 64;case 5:return 12;case 6:return 30;case 7:return 50;default:return 0;}
}
u32 cap_old_offset(u32 p) {
    switch(p) {case 0:return 0;case 1:return 328;case 2:return 432;case 3:return 215;
        case 4:return 368;case 5:return 316;case 6:return 456;case 7:return 165;default:return 0;}
}
CapSlot *cap_pocket(CapBag *b, u32 p) {
    u32 off=0,i;
    if(p>=8)return 0;
    for(i=0;i<p;i++)off+=cap_count(i);
    return b->slots+off;
}
void cap_clear(CapBag *b) {
    u16 *v=(u16 *)b;u32 i;
    for(i=0;i<sizeof(*b)/2;i++)v[i]=0;
}
void cap_copy(const CapBag *a,CapBag *b) {
    const u16 *s=(const u16 *)a;u16 *d=(u16 *)b;u32 i;
    for(i=0;i<sizeof(*b)/2;i++)d[i]=s[i];
}
void cap_import(CapBag *b,const CapSlot *v) {
    u32 p,i;cap_clear(b);
    for(p=0;p<8;p++) {
        CapSlot *dst=cap_pocket(b,p);const CapSlot *src=v+cap_old_offset(p);
        for(i=0;i<cap_old_count(p);i++)dst[i]=src[i];
    }
    b->registered[0]=v[486].id;b->registered[1]=v[486].quantity;
}
void cap_export(const CapBag *b,CapSlot *v) {
    u32 p,i;
    for(p=0;p<8;p++) {
        const CapSlot *src=cap_pocket((CapBag *)b,p);CapSlot *dst=v+cap_old_offset(p);
        for(i=0;i<cap_old_count(p);i++)dst[i]=src[i];
    }
    v[486].id=b->registered[0];v[486].quantity=b->registered[1];
}
static void reconcile_slot(CapSlot *shadow,CapSlot *native,CapSlot *snapshot) {
    if(native->id!=snapshot->id||native->quantity!=snapshot->quantity)*shadow=*native;
    else *native=*shadow;
    *snapshot=*native;
}
void cap_reconcile(CapBag *b,CapSlot *v,CapSlot *last) {
    u32 p,i;
    for(p=0;p<8;p++) {
        CapSlot *shadow=cap_pocket(b,p);u32 off=cap_old_offset(p);
        for(i=0;i<cap_old_count(p);i++)reconcile_slot(shadow+i,v+off+i,last+off+i);
    }
    reconcile_slot((CapSlot *)b->registered,v+486,last+486);
}
static CapSlot *find_add(CapSlot *v,u32 n,u16 id,u16 q,u32 limit) {
    CapSlot *empty=0;u32 i;
    if(!id||!q||q>limit)return 0;
    for(i=0;i<n;i++) {
        if(v[i].id==id)return (u32)v[i].quantity+q<=limit?v+i:0;
        if(!empty&&!v[i].id&&!v[i].quantity)empty=v+i;
    }
    return empty;
}
int cap_has_space(CapBag *b,u32 p,u16 id,u16 q) {
    return find_add(cap_pocket(b,p),cap_count(p),id,q,p==3?99:999)!=0;
}
static void compact(CapSlot *v,u32 n,int sorted) {
    u32 read,write=0,i;CapSlot x;
    for(read=0;read<n;read++)if(v[read].quantity)v[write++]=v[read];
    for(i=write;i<n;i++){v[i].id=0;v[i].quantity=0;}
    if(!sorted)return;
    for(read=1;read<write;read++){
        x=v[read];i=read;
        while(i&&v[i-1].id>x.id){v[i]=v[i-1];i--;}
        v[i]=x;
    }
}
int cap_add(CapBag *b,u32 p,u16 id,u16 q) {
    CapSlot *v=cap_pocket(b,p),*slot=find_add(v,cap_count(p),id,q,p==3?99:999);
    if(!slot)return 0;
    slot->id=id;slot->quantity+=q;
    if(p==3||p==4)compact(v,cap_count(p),1);
    return 1;
}
u16 cap_quantity(CapSlot *v,u32 n,u16 id) {
    u32 i;for(i=0;i<n;i++)if(v[i].id==id)return v[i].quantity;
    return 0;
}
int cap_pocket_take(CapSlot *v,u32 n,u16 id,u16 q) {
    u32 i;
    for(i=0;i<n;i++)if(v[i].id==id){
        if(v[i].quantity<q)return 0;
        v[i].quantity-=q;
        if(!v[i].quantity)v[i].id=0;
        compact(v,n,0);return 1;
    }
    return 0;
}
int cap_take(CapBag *b,u32 p,u16 id,u16 q) {
    return cap_pocket_take(cap_pocket(b,p),cap_count(p),id,q);
}
void cap_move(CapSlot *v,u32 n,u32 from,u32 to) {
    CapSlot moving;u32 i;
    if(from>=n||to>=n||from==to)return;
    moving=v[from];
    if(from<to)for(i=from;i<to;i++)v[i]=v[i+1];
    else for(i=from;i>to;i--)v[i]=v[i-1];
    v[to]=moving;
}
