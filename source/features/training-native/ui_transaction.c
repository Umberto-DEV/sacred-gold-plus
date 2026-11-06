/* Independent successor extension; historical runtime is not recompiled into it. */
#if !defined(SGP_SETTINGS_UI_SUCCESSOR) || SGP_SETTINGS_UI_SUCCESSOR != 1
#error "Training UI extension requires SGP_SETTINGS_UI_SUCCESSOR=1"
#endif
#include "state.h"
#include "../shiny/ui_api.h"
#define ENTRY __attribute__((used,noinline))
#define S ((volatile TrainingState *)0x023D3000u)
#define G ((volatile SgpTrainingUiGeneration *)SGP_SETTINGS_UI_GENERATION)
#define D ((const SgpSettingsUiDescriptor *)SGP_SETTINGS_UI_DESCRIPTOR)
#define C ((const SgpShinyConfig *)SGP_SHINY_CONFIG)
#define MAGIC 0x31544E52u
#define SAVE_BYTES 0x2330Cu
#define WORD(p,o) (*(volatile u32 *)((u8 *)(p)+(o)))
#define HALF(p,o) (*(volatile u16 *)((u8 *)(p)+(o)))
/* Private encoding, deliberately no journal/jobs/record copy. */
typedef struct {
    u32 epoch, save, native_generation, native_bank;
    u32 enabled, writable, record_status, admitted;
    u16 journal_flags, reserved;
    SgpShinySaved saved_before;
} TrainingProof;
_Static_assert(sizeof(TrainingProof)==52,"private proof wire size");
_Static_assert(__builtin_offsetof(TrainingProof,journal_flags)==32,"proof flags");
_Static_assert(__builtin_offsetof(TrainingProof,saved_before)==36,"proof saved bytes");
_Static_assert(sizeof(sgp_train_journal)-__builtin_offsetof(sgp_train_journal,shiny_rng)==16,"shiny journal tail");

static int main_range(u32 p,u32 n)
{
    return !(p&3)&&p>=0x02000000u&&p<=0x02400000u-n;
}
static int overlap(u32 a,u32 n,u32 b,u32 m)
{
    return a<b+m&&b<a+n;
}
static int buffer(const void *p,u32 n,u32 fs,u32 save)
{
    u32 a=(u32)p;
    if(a&3)return 0;
    if(a>=SGP_SETTINGS_UI_STACK_LOW&&a<=SGP_SETTINGS_UI_STACK_HIGH-n)return 1;
    if(!main_range(a,n)||a<SGP_SETTINGS_UI_HEAP_LOW||a>SGP_SETTINGS_UI_HEAP_HIGH-n||
       overlap(a,n,0x021D4158u,4)||overlap(a,n,fs,16)||overlap(a,n,save,SAVE_BYTES))return 0;
    return 1;
}
static int descriptor(void)
{
    u32 i;
    if(D->magic!=SGP_SETTINGS_UI_MAGIC||D->abi!=1||D->bytes!=80||
       D->token_bytes!=152||D->training_proof_bytes!=52||D->flags!=3||
       D->original_training_load!=0x023D1321u||D->original_training_bind!=0x023D1A45u||
       D->original_storage_ready!=0x023D1B1Du||D->generation_state!=SGP_SETTINGS_UI_GENERATION)return 0;
    for(i=0;i<4;i++)if(D->reserved[i])return 0;
    return 1;
}
static int live(void *fs,u32 *save)
{
    u32 a=(u32)fs,s;
    if(!descriptor()||!main_range(a,16)||overlap(a,16,0x023C0000u,0x20000u)||
       WORD((void *)0x021D4158u,0)!=a)return 0;
    s=WORD(fs,12);
    if(!main_range(s,SAVE_BYTES)||overlap(s,SAVE_BYTES,0x023C0000u,0x20000u)||
       overlap(a,16,s,SAVE_BYTES))return 0;
    *save=s;return 1;
}
static void copy(void *to,const volatile void *from,u32 n)
{
    u8 *a=to;const volatile u8 *b=from;
    while(n--)*a++=*b++;
}
static int equal(const void *a,const void *b,u32 n)
{
    const u8 *x=a,*y=b;
    while(n--)if(*x++!=*y++)return 0;
    return 1;
}
static int saved_valid(const SgpShinySaved *saved)
{
    /* Immutable historical capability: reuse the core's exact value domains. */
    u32 f=C->core_valid;
    return C->magic==SGP_SHINY_MAGIC&&C->abi==2&&C->bytes==152&&
        (f&1)&&main_range(f&~1u,2)&&
        ((int (*)(const SgpShinySaved *))f)(saved);
}
static int capture(void *fs,TrainingProof *p)
{
    u32 save;
    if(!live(fs,&save)||S->magic!=MAGIC||(u32)S->save!=save||
       G->magic!=SGP_SETTINGS_UI_GENERATION_MAGIC||!G->epoch||
       G->save_identity!=save||G->reserved||!S->writable)return 0;
    p->epoch=G->epoch;p->save=save;
    p->native_generation=WORD((void *)save,0x23010);
    p->native_bank=HALF((void *)save,0x2330A);
    p->enabled=S->enabled;p->writable=S->writable;p->record_status=S->record_status;
    p->admitted=S->shiny_admitted;p->journal_flags=S->journal.flags;p->reserved=0;
    copy(&p->saved_before,&S->journal.shiny_rng,16);
    return p->native_bank<=1&&p->enabled<=1&&p->writable==1&&
        p->record_status<=SGP_TRAIN_MISMATCH&&p->admitted<=1&&
        p->journal_flags<=SGP_TRAIN_SHINY_ONLY&&saved_valid(&p->saved_before);
}
static int current(void *fs,const TrainingProof *p)
{
    TrainingProof now;
    return capture(fs,&now)&&equal(p,&now,sizeof(now));
}
static int storage(void)
{
    return ((int (*)(void))D->original_storage_ready)();
}
ENTRY u32 training_ui_peek(void *fs,SgpShinySaved *saved,SgpTrainingUiProof *proof)
{
    TrainingProof p;u32 save;
    if(!live(fs,&save)||!buffer(saved,16,(u32)fs,save)||!buffer(proof,52,(u32)fs,save)||
       overlap((u32)saved,16,(u32)proof,52)||!capture(fs,&p))return SGP_SHINY_UNAVAILABLE;
    if(!p.admitted&&!storage())return SGP_SHINY_UNAVAILABLE;
    if(!current(fs,&p))return SGP_SHINY_STALE;
    copy(saved,&p.saved_before,16);copy(proof,&p,sizeof(p));return SGP_SHINY_OK;
}
ENTRY u32 training_ui_validate(void *fs,const SgpTrainingUiProof *proof,
                             const SgpShinySaved *next,u32 inspect_storage)
{
    TrainingProof p;SgpShinySaved n;u32 save;
    if(inspect_storage>1||!live(fs,&save)||!buffer(proof,52,(u32)fs,save)||
       !buffer(next,16,(u32)fs,save)||overlap((u32)proof,52,(u32)next,16))return SGP_SHINY_UNAVAILABLE;
    copy(&p,proof,sizeof(p));copy(&n,next,sizeof(n));
    if(!current(fs,&p))return SGP_SHINY_STALE;
    if(!saved_valid(&n))return SGP_SHINY_UNAVAILABLE;
    if(inspect_storage&&!storage())return SGP_SHINY_UNAVAILABLE;
    return current(fs,&p)?SGP_SHINY_OK:SGP_SHINY_STALE;
}
ENTRY void training_ui_store(const SgpTrainingUiProof *proof,const SgpShinySaved *next)
{
    volatile u8 *to=(volatile u8 *)&S->journal.shiny_rng;
    const u8 *from=(const u8 *)next;u32 i;
    /* Trusted checked caller, under the same IRQ lock; no fallible phase here. */
    (void)proof;
    for(i=0;i<16;i++)to[i]=from[i];
    S->shiny_admitted=1;
    if(!S->enabled)S->journal.flags=SGP_TRAIN_SHINY_ONLY;
}
/* Epoch zero with initialized magic is a permanent refusal. Only cold zeroed
 * storage can initialize epoch one. Overflow cannot resurrect an old proof. */
static void begin(void)
{
    u32 epoch=0;
    if(!G->magic&&!G->epoch&&!G->save_identity&&!G->reserved)epoch=1;
    else if(G->magic==SGP_SETTINGS_UI_GENERATION_MAGIC&&!G->reserved&&G->epoch)epoch=G->epoch+1;
    G->save_identity=0;G->magic=SGP_SETTINGS_UI_GENERATION_MAGIC;
    G->epoch=epoch;G->reserved=0;
}
static void bound(void *save)
{
    if(G->epoch&&main_range((u32)save,SAVE_BYTES)&&S->magic==MAGIC&&S->save==save)
        G->save_identity=(u32)save;
}
ENTRY int training_ui_load(void *save)
{
    int result;
    if(!descriptor())return 0;
    begin();result=((int (*)(void *))D->original_training_load)(save);
    if(result)bound(save);
    return result;
}
ENTRY void training_ui_bind(void *save,u32 fresh)
{
    if(!descriptor())return;
    begin();((void (*)(void *,u32))D->original_training_bind)(save,fresh);bound(save);
}
