#include "journal.h"
static u32 record_crc(const void *data,u32 n) {
    const u8 *p=(const u8 *)data;u32 crc=~0u,i,j;
    for(i=0;i<n;i++){
        crc^=p[i];for(j=0;j<8;j++)crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
void cap_record_create(CapRecord *r,const CapBag *b,u32 gen,u16 main_crc) {
    u32 p,i,k=0;
    r->magic=CAP_RECORD_MAGIC;r->version=1;r->size=sizeof(*r);
    r->generation=gen;r->main_crc=main_crc;r->reserved=0;
    for(p=0;p<8;p++) {
        const CapSlot *v=cap_pocket((CapBag *)b,p);
        for(i=cap_old_count(p);i<cap_count(p);i++)r->extra[k++]=v[i];
    }
    r->crc=record_crc(r,sizeof(*r)-4);
}
int cap_record_restore(const CapRecord *r,CapBag *b,u32 gen,u16 main_crc) {
    u32 p,i,k=0;int erased=1;const u8 *raw=(const u8 *)r;
    for(i=0;i<sizeof(*r);i++)if(raw[i]!=255){erased=0;break;}
    if(erased)return 0;
    if(r->magic!=CAP_RECORD_MAGIC||r->version!=1||r->size!=sizeof(*r)||r->reserved||
       r->crc!=record_crc(r,sizeof(*r)-4))return -1;
    for(p=0;p<8;p++)for(i=cap_old_count(p);i<cap_count(p);i++){
        const CapSlot *v=&r->extra[k++];
        if(v->id>536||v->quantity>(p==3?99:999)||(!v->id!=!v->quantity))return -1;
    }
    if(r->generation!=gen||r->main_crc!=main_crc)return 2;
    if(!b)return 1;
    k=0;
    for(p=0;p<8;p++){
        CapSlot *v=cap_pocket(b,p);
        for(i=cap_old_count(p);i<cap_count(p);i++)v[i]=r->extra[k++];
    }
    return 1;
}

/* A write interrupted during the magic itself has a correct nonempty prefix
 * followed solely by erased bytes. Complete magic establishes our ownership. */
int cap_record_owned_prefix(const CapRecord *r){
    const u8 *b=(const u8 *)r;u32 magic=CAP_RECORD_MAGIC,i,n=0;
    if(r->magic==CAP_RECORD_MAGIC)return 1;
    for(i=0;i<4;i++){if(b[i]!=(u8)(magic>>(8*i)))break;n++;}
    if(!n)return 0;
    for(i=n;i<sizeof(*r);i++)if(b[i]!=255)return 0;
    return 1;
}
