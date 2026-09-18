#include "journal.h"
static u32 record_crc(const void *data,u32 n) {
    const u8 *p=(const u8 *)data;u32 crc=~0u,i,j;
    for(i=0;i<n;i++){
        crc^=p[i];for(j=0;j<8;j++)crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
void cap_record_create(CapRecord *r,const CapBag *b,u32 gen,u16 main_crc) {
    u32 p,i,k=0,end,limit;
    r->magic=CAP_RECORD_MAGIC;r->version=1;r->size=sizeof(*r);
    r->generation=gen;r->main_crc=main_crc;r->reserved=0;
    for(p=0;p<8;p++) {
        const CapSlot *v=cap_pocket((CapBag *)b,p);
        end=k+cap_count(p)-cap_old_count(p);limit=(p==3?99u:999u);
        /* The native PocketCompaction pushes spent slots to the end of the
         * pocket KEEPING their id, so {id,0} lands inside the extension. Such a
         * slot is not inventory: writing it would produce a record our own
         * validator rejects, and the save would fail for ever. Only INCOHERENT
         * cells are dropped and the tail is erased; empty cells already there
         * stay where they are, so nothing the player owns changes position. */
        for(i=cap_old_count(p);i<cap_count(p);i++){
            if((v[i].id||v[i].quantity)&&
               (!v[i].id||v[i].id>536||!v[i].quantity||v[i].quantity>limit))continue;
            r->extra[k++]=v[i];
        }
        while(k<end){r->extra[k].id=0;r->extra[k].quantity=0;k++;}
    }
    r->crc=record_crc(r,sizeof(*r)-4);
}
int cap_record_restore(const CapRecord *r,CapBag *b,u32 gen,u16 main_crc) {
    u32 p,i,k=0;
    /* Sectors that are not ours -- erased, zeroed by a converter, or written by
     * somebody else -- mean the extension is ABSENT, not that the save is
     * broken. Only bytes we recognise as ours can be reported as damaged. */
    if(!cap_record_owned_prefix(r))return 0;
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

int cap_record_erased(const CapRecord *r){
    const u8 *b=(const u8 *)r;u32 i;
    for(i=0;i<sizeof(*r);i++)if(b[i]!=255)return 0;
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
