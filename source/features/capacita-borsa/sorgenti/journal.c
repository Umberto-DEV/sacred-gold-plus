#include "journal.h"
static u32 record_crc(const void *data,u32 n) {
    const u8 *p=(const u8 *)data;u32 crc=~0u,i,j;
    for(i=0;i<n;i++){
        crc^=p[i];for(j=0;j<8;j++)crc=(crc>>1)^(0xEDB88320u&(0u-(crc&1u)));
    }
    return ~crc;
}
void cap_record_create(CapRecord *r,const CapBag *b,u32 gen,u16 main_crc) {
    u32 p,i,k=0,limit;
    r->magic=CAP_RECORD_MAGIC;r->version=1;r->size=sizeof(*r);
    r->generation=gen;r->main_crc=main_crc;r->reserved=0;
    for(p=0;p<8;p++) {
        const CapSlot *v=cap_pocket((CapBag *)b,p);
        limit=(p==3?99u:999u);
        /* The native PocketCompaction pushes spent slots to the end of the
         * pocket KEEPING their id, so {id,0} lands inside the extension. Such a
         * slot is not inventory: writing it would produce a record our own
         * validator rejects, and the save would fail for ever. An INCOHERENT
         * cell is emptied WHERE IT IS: dropping it and closing the gap would
         * pull every following item one cell up, so the position of what the
         * player owns is exactly the position it had in the Bag. */
        for(i=cap_old_count(p);i<cap_count(p);i++,k++){
            if((v[i].id||v[i].quantity)&&
               (!v[i].id||v[i].id>536||!v[i].quantity||v[i].quantity>limit)){
                r->extra[k].id=0;r->extra[k].quantity=0;
            }else r->extra[k]=v[i];
        }
    }
    r->crc=record_crc(r,sizeof(*r)-4);
}
int cap_record_restore(const CapRecord *r,CapBag *b,u32 gen,u16 main_crc) {
    u32 p,i,k=0;
    /* Sectors that are not ours -- erased, zeroed by a converter, or written by
     * somebody else -- mean the extension is ABSENT, not that the save is
     * broken. Only bytes we recognise as ours can be reported as damaged.
     * In the ROM the caller (classify) has already told the two apart, so this
     * guard changes nothing there; it is what makes the function safe to call
     * on its own, as the host tests and the standalone reader do. */
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

/* 452 identical bytes hold no data: erased flash, a sector a converter filled
 * with 0x00, a card wiped with a pattern. Such a destination is claimable --
 * refusing it for ever meant a normalised .sav could never save the extension
 * again. Only NON-uniform bytes we do not recognise belong to somebody else. */
int cap_record_uniform(const CapRecord *r){
    const u8 *b=(const u8 *)r;u32 i;
    for(i=1;i<sizeof(*r);i++)if(b[i]!=b[0])return 0;
    return 1;
}

int cap_record_erased(const CapRecord *r){
    return ((const u8 *)r)[0]==255&&cap_record_uniform(r);
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
