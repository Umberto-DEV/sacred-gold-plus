/* Expanded Bag routing with an unchanged native disk structure and cheat mirror. */
#include "core.c"
#include "journal.c"
#define CAP_BASE 0x023DBF00u
#define CAP_STATE 0x023DD700u
#define CAP_MAGIC 0x43415042u
#define RD32(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define RD16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define CALL_ALLOC ((void *(*)(u32,u32))0x0201AA8Du)
#define CALL_ARRAY ((void *(*)(void *,u32))0x020272C9u)
#define CALL_ATTR ((u32 (*)(u16,u32,u32))0x02077D89u)
#define CALL_READ ((int (*)(u32,void *,u32))0x0202877Du)
#define CALL_WRITE ((int (*)(u32,const void *,u32))0x02028759u)
#define CALL_CRC ((u16 (*)(const void *,u32))0x0201FF99u)
#define ENTRY __attribute__((used,noinline))
/* CapState.stato_caricamento: what the two flash copies turned out to be. */
#define CAP_L_ASSENTE   0u /* both copies erased, or no disk read at all */
#define CAP_L_PRIMARIA  1u /* the primary copy matched this save */
#define CAP_L_SPECCHIO  2u /* the mirror matched this save */
#define CAP_L_STALE     3u /* intact record from another save generation */
#define CAP_L_INVALIDA  4u /* our magic but damaged, or foreign bytes */
#define CAP_L_NO_FLASH  5u /* the flash read itself failed */
/* CapState.stato_scrittura: what the last save did with the extension. */
#define CAP_W_NON_TENTATA 0u
#define CAP_W_SCRITTA     1u /* both copies written and read back identical */
#define CAP_W_ESTRANEI    2u /* foreign data in a destination: nothing written */
#define CAP_W_FALLITA     3u /* no usable copy on flash after the attempt */
#define CAP_W_NO_FLASH    4u /* flash unreadable: the extension was skipped */
#define CAP_W_PARZIALE    5u /* only one of the two copies survived readback */
int sgp_cap_original_load(void *save);
int sgp_cap_original_save(void *save,void *manager);
typedef struct {
    u32 magic;
    void *save;
    CapSlot *native;
    u32 rejected;
    u32 owned;
    CapBag bag;
    CapSlot snapshot[487];
    CapRecord record;
    u32 stato_caricamento;
    u32 stato_scrittura;
} CapState;
#define S ((CapState *)CAP_STATE)
_Static_assert(sizeof(CapState)<=0x1400,"state crosses the frozen 1.1 reserve");
static void mirror_copy(CapSlot *to,const CapSlot *from) {
    u32 i;for(i=0;i<487;i++)to[i]=from[i];
}
static void sync(void) {
    if(S->magic==CAP_MAGIC)cap_reconcile(&S->bag,S->native,S->snapshot);
}
static CapBag *route(CapBag *bag) {
    if(S->magic==CAP_MAGIC&&(bag==&S->bag||(void *)bag==(void *)S->native)){
        sync();return &S->bag;
    }
    return bag;
}
/* Classify the copy already read into S->record. No outcome is fatal: the
 * extension may be missing, stale or unreadable, and the native save still
 * loads with its 486 slots. */
static u32 classify(CapBag *bag,u32 generation,u16 main_crc) {
    int status;
    if(cap_record_erased(&S->record))return CAP_L_ASSENTE;
    if(!cap_record_owned_prefix(&S->record))return CAP_L_INVALIDA;
    status=cap_record_restore(&S->record,bag,generation,main_crc);
    if(status==1)return CAP_L_PRIMARIA;
    if(status==2)return CAP_L_STALE;
    return CAP_L_INVALIDA;
}
static void load_inventory(void *save,int disk) {
    u32 sector,generation,first=CAP_L_ASSENTE,second=CAP_L_ASSENTE;u16 main_crc;u8 *footer;
    S->magic=0;S->save=save;S->native=CALL_ARRAY(save,3);S->rejected=0;S->owned=0;
    S->stato_caricamento=CAP_L_ASSENTE;S->stato_scrittura=CAP_W_NON_TENTATA;
    cap_import(&S->bag,S->native);mirror_copy(S->snapshot,S->native);
    if(disk){
        sector=0x30000u+(RD16(save,0x2330A)?0x40000u:0u);
        footer=(u8 *)save+0x10+RD32(save,0x232B8)+RD32(save,0x232BC)-16;
        generation=RD32(save,0x23010);main_crc=RD16(footer,14);
        first=CALL_READ(sector,&S->record,sizeof(S->record))?
              classify(&S->bag,generation,main_crc):CAP_L_NO_FLASH;
        if(first==CAP_L_PRIMARIA)S->stato_caricamento=CAP_L_PRIMARIA;
        else{
            second=CALL_READ(sector+0x200,&S->record,sizeof(S->record))?
                   classify(&S->bag,generation,main_crc):CAP_L_NO_FLASH;
            if(second==CAP_L_PRIMARIA)S->stato_caricamento=CAP_L_SPECCHIO;
            else if(first==CAP_L_NO_FLASH||second==CAP_L_NO_FLASH)S->stato_caricamento=CAP_L_NO_FLASH;
            else if(first==CAP_L_STALE||second==CAP_L_STALE)S->stato_caricamento=CAP_L_STALE;
            else if(first==CAP_L_INVALIDA||second==CAP_L_INVALIDA)S->stato_caricamento=CAP_L_INVALIDA;
        }
        /* Only a flash failure keeps the next save from touching the sectors. */
        S->rejected=first==CAP_L_NO_FLASH||second==CAP_L_NO_FLASH;
        S->owned=S->stato_caricamento&&S->stato_caricamento<=CAP_L_STALE;
    }
    S->magic=CAP_MAGIC;
}
ENTRY CapBag *sgp_cap_get(void *save) {
    if(S->magic!=CAP_MAGIC||S->save!=save)
        load_inventory(save,RD32(save,4)&&!RD32(save,8));
    sync();return &S->bag;
}
ENTRY void sgp_cap_init(void *native) {
    u32 i;u16 *v=native;
    for(i=0;i<974;i++)v[i]=0;
    S->magic=0;
}
ENTRY CapBag *sgp_cap_new(u32 heap) {
    CapBag *b=CALL_ALLOC(heap,sizeof(CapBag));cap_clear(b);return b;
}
ENTRY void sgp_cap_copy(CapBag *from,CapBag *to) {
    from=route(from);to=route(to);cap_copy(from,to);sync();
}
ENTRY u16 sgp_cap_registered1(CapBag *b){return route(b)->registered[0];}
ENTRY u16 sgp_cap_registered2(CapBag *b){return route(b)->registered[1];}
ENTRY int sgp_cap_register(CapBag *b,u16 item){
    u32 i;b=route(b);
    for(i=0;i<2;i++)if(!b->registered[i]){b->registered[i]=item;sync();return i+1;}
    return 0;
}
ENTRY void sgp_cap_unregister(CapBag *b,u16 item){
    b=route(b);
    if(b->registered[1]==item)b->registered[1]=0;
    else if(b->registered[0]==item){b->registered[0]=b->registered[1];b->registered[1]=0;}
    sync();
}
ENTRY u32 sgp_cap_pocket(CapBag *b,u16 item,CapSlot **slots,u32 *count,u32 heap){
    u32 p=CALL_ATTR(item,5,heap);b=route(b);
    *slots=cap_pocket(b,p);*count=cap_count(p);return p;
}
ENTRY int sgp_cap_not_empty(CapBag *b,u32 p){
    u32 i;CapSlot *slots=cap_pocket(route(b),p);
    for(i=0;i<cap_count(p);i++)if(slots[i].id)return 1;
    return 0;
}
ENTRY void *sgp_cap_view(CapBag *b,const u8 *pockets,u32 heap){
    u32 i;void *v=((void *(*)(u32))0x02077879u)(heap);b=route(b);
    for(i=0;pockets[i]!=255;i++)if(pockets[i]<8)
        ((void (*)(void *,CapSlot *,u8,u8))0x020778BDu)(v,cap_pocket(b,pockets[i]),pockets[i],i);
    return v;
}
ENTRY CapSlot *sgp_cap_slot(CapBag *b,u8 pocket,u32 n){
    b=route(b);if(n>=cap_count(pocket))return 0;
    return cap_pocket(b,pocket)+n;
}
ENTRY void sgp_cap_move(CapSlot *slots,u32 from,u32 to,u32 pocket,u32 heap){
    (void)heap;sync();cap_move(slots,cap_count(pocket),from,to);sync();
}
ENTRY int sgp_cap_load(void *save){
    int result;S->magic=0;
    result=sgp_cap_original_load(save);
    if(result)load_inventory(save,1);
    return result;
}
/* Read back what was just written and compare the bytes. Re-validating the
 * domain instead would reject records the game itself can produce, and the
 * save would fail for ever. The 452 bytes are compared in chunks so the
 * comparison needs no second copy of the record in the frozen reserve. */
static int verify_copy(u32 address,const CapRecord *r){
    const u8 *want=(const u8 *)r;u8 got[64];u32 off,i,n;
    for(off=0;off<sizeof(*r);off+=n){
        n=sizeof(*r)-off;if(n>sizeof(got))n=sizeof(got);
        if(!CALL_READ(address+off,got,n))return 0;
        for(i=0;i<n;i++)if(got[i]!=want[off+i])return 0;
    }
    return 1;
}
ENTRY int sgp_cap_save(void *save,void *manager){
    if(RD32(manager,0x14)==0&&RD32(manager,8)==0){
        u32 sector,generation,copy,esito=CAP_W_SCRITTA,good=0;u16 crc;
        sgp_cap_get(save);
        if(S->rejected)esito=CAP_W_NO_FLASH;
        else{
            sector=0x30000u+(RD16(save,0x2330A)?0u:0x40000u);
            generation=RD32(save,0x23010);
            crc=CALL_CRC((u8 *)save+0x10+RD32(save,0x232B8),RD32(save,0x232BC)-16);
            /* Each destination must independently belong to us before any write.
             * Ownership of the active bank never authorizes foreign inactive data. */
            for(copy=0;copy<2&&esito==CAP_W_SCRITTA;copy++){
                if(!CALL_READ(sector+copy*0x200,&S->record,sizeof(S->record)))esito=CAP_W_NO_FLASH;
                else if(!cap_record_erased(&S->record)&&!cap_record_owned_prefix(&S->record))esito=CAP_W_ESTRANEI;
            }
            if(esito==CAP_W_SCRITTA){
                cap_record_create(&S->record,&S->bag,generation,crc);
                for(copy=0;copy<2;copy++)
                    if(CALL_WRITE(sector+copy*0x200,&S->record,sizeof(S->record))&&
                       verify_copy(sector+copy*0x200,&S->record))good++;
                esito=good==2?CAP_W_SCRITTA:(good?CAP_W_PARZIALE:CAP_W_FALLITA);
                if(good)S->owned=1;
            }
        }
        S->stato_scrittura=esito;
    }
    /* The extension never stops the native save: its own result is the answer
     * the caller gets, and the failure is reported in stato_scrittura. */
    return sgp_cap_original_save(save,manager);
}

/* The original prologues are replayed before continuing beyond the entry hook.
 * Both original functions save r3, so the branch scratch register is preserved. */
__attribute__((naked,used)) int sgp_cap_original_load(void *save __attribute__((unused))){
    __asm__ volatile("push {r3,r4,r5,r6,r7,lr}\n"
      "adds r5,r0,#0\n" "ldr r0,=0x232B4\n" "adds r7,r5,#0\n"
      "ldr r3,=0x02027ADD\n" "bx r3\n");
}
__attribute__((naked,used)) int sgp_cap_original_save(void *save __attribute__((unused)),void *manager __attribute__((unused))){
    __asm__ volatile("push {r3,r4,r5,lr}\n" "adds r4,r1,#0\n"
      "adds r5,r0,#0\n" "ldr r0,[r4,#0x14]\n"
      "ldr r3,=0x02027C21\n" "bx r3\n");
}
