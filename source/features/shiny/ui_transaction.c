/* Successor-only owner extension. No production code address is assigned here. */
#if !defined(SGP_SETTINGS_UI_SUCCESSOR) || SGP_SETTINGS_UI_SUCCESSOR != 1
#error "Shiny UI extension requires SGP_SETTINGS_UI_SUCCESSOR=1"
#endif
#if !defined(SGP_SETTINGS_UI_FINAL_CHECK) || !(SGP_SETTINGS_UI_FINAL_CHECK & 1) || SGP_SETTINGS_UI_FINAL_CHECK < 0x02000001 || SGP_SETTINGS_UI_FINAL_CHECK > 0x023FFFFF
#error "Shiny UI extension requires the exact compiled coordinator Thumb gate"
#endif
#include "internal.h"
#include "ui_api.h"
#undef RT
#define RT ((volatile ShinyRuntime *)0x023CB200u)
#define D ((const SgpSettingsUiDescriptor *)SGP_SETTINGS_UI_DESCRIPTOR)
#define IME (*(volatile u32 *)0x04000208u)
/* Pinned pure ARM OS_GetCpsrIrq: MRS/AND80/BX LR. Keep its even entry;
 * FN would incorrectly force Thumb. Query only, never enable/disable IRQs. */
#define CPU_IRQ_MASK ((u32 (*)(void))0x020D3A90u)
#define VWORD(p,o) (*(volatile u32 *)((u8 *)(p)+(o)))
#define ENTRY __attribute__((used,noinline))
#define SAVE_BYTES 0x2330Cu
#define FS_BYTES 0x24u
#define TOKEN_MAGIC 0x31545353u /* SST1, owner-private transient encoding */
typedef struct {
    u32 magic;u16 abi,bytes;
    u32 app,app_generation,fs,options;
    SgpShinySnapshot opened;
    SgpShinyDraft draft;
    SgpTrainingUiProof training;
    SgpShinySaved next;
    u32 captured,map;
} Token;
typedef struct {u32 app_generation,fs,save,options,captured,map,queued,pending,token;} Identity;
_Static_assert(sizeof(Token)==152,"private token bytes");
_Static_assert(__builtin_offsetof(Token,opened)==24,"token snapshot");
_Static_assert(__builtin_offsetof(Token,draft)==56,"token draft");
_Static_assert(__builtin_offsetof(Token,training)==76,"token proof");
_Static_assert(__builtin_offsetof(Token,next)==128,"token next");
_Static_assert(__builtin_offsetof(Token,captured)==144,"token cache");

static int range(u32 p,u32 n)
{return !(p&3)&&p>=0x02000000u&&p<=0x02400000u-n;}
static int overlap(u32 a,u32 n,u32 b,u32 m)
{return a<b+m&&b<a+n;}
static int identity_range(u32 p,u32 n)
{return range(p,n)&&!overlap(p,n,0x023C0000u,0x20000u);}
static int code(u32 p)
{return (p&1)&&range(p&~3u,4);}
static void copy(void *to,const volatile void *from,u32 n)
{u8 *a=to;const volatile u8 *b=from;while(n--)*a++=*b++;}
static int equal(const void *a,const volatile void *b,u32 n)
{const u8 *x=a;const volatile u8 *y=b;while(n--)if(*x++!=*y++)return 0;return 1;}
static int descriptor(void)
{
    u32 i;
    if(D->magic!=SGP_SETTINGS_UI_MAGIC||D->abi!=1||D->bytes!=80||
       D->token_bytes!=152||D->training_proof_bytes!=52||D->flags!=3||
       D->original_training_load!=0x023D1321u||D->original_training_bind!=0x023D1A45u||
       D->original_storage_ready!=0x023D1B1Du||D->generation_state!=SGP_SETTINGS_UI_GENERATION||
       !code(D->training_peek)||!code(D->training_validate)||!code(D->training_store)||
       CFG->magic!=SGP_SHINY_MAGIC||CFG->abi!=2||CFG->bytes!=152||
       !code(CFG->core_valid)||!code(CFG->core_denominator)||!code(CFG->core_select))return 0;
    for(i=0;i<4;i++)if(D->reserved[i])return 0;
    return 1;
}
/* The native Options getter is a pinned pure SaveData accessor. Its input full
 * extent is validated before calling; its result must be inside that SaveData. */
static int identity(void *app,Identity *id)
{
    u32 a=(u32)app,f=(u32)RT->fs,s=(u32)RT->save,o=(u32)RT->options;
    if(!descriptor()||RT->magic!=SGP_SHINY_MAGIC||!RT->epoch||
       !identity_range(a,0x30)||!identity_range(f,FS_BYTES)||!identity_range(s,SAVE_BYTES)||
       overlap(a,0x30,f,FS_BYTES)||overlap(a,0x30,s,SAVE_BYTES)||overlap(f,FS_BYTES,s,SAVE_BYTES)||
       VWORD((void *)0x021D4158u,0)!=f||VWORD((void *)f,12)!=s||
       !range(o,4)||o<s||o>s+SAVE_BYTES-4||
       (u32)FN(void *(*)(void *),0x02028EA8)((void *)s)!=o||
       VWORD(app,0x24)!=o||VWORD(app,0x2C)!=SGP_SETTINGS_UI_APP_MAGIC||!VWORD(app,0x28))return 0;
    id->app_generation=VWORD(app,0x28);id->fs=f;id->save=s;id->options=o;
    id->captured=RT->captured;id->map=RT->map;
    id->queued=RT->queued;id->pending=RT->pending;id->token=RT->token;return 1;
}
static int buffer(const void *p,u32 n,void *app,const Identity *id)
{
    u32 a=(u32)p;
    if(a&3)return 0;
    if(a>=SGP_SETTINGS_UI_STACK_LOW&&a<=SGP_SETTINGS_UI_STACK_HIGH-n)return 1;
    return a>=SGP_SETTINGS_UI_HEAP_LOW&&a<=SGP_SETTINGS_UI_HEAP_HIGH-n&&
        !overlap(a,n,id->fs,FS_BYTES)&&!overlap(a,n,id->save,SAVE_BYTES)&&!overlap(a,n,(u32)app,0x30);
}
/* Capture only UI-visible logical state, never the whole runtime/journal.
 * The captured flag means the existing cache must still match current map. */
static int snapshot(void *app,const SgpShinySaved *saved,SgpShinySnapshot *out,Identity *id)
{
    u32 i,j,map;
    if(!identity(app,id)||id->captured>1||RT->charge>40||RT->status>SGP_SHINY_GENERATION_FAILED||RT->method>=5)return 0;
    zero(out,sizeof(*out));
    out->epoch=RT->epoch;out->context=RT->context;out->revision=RT->revision;
    out->charge=RT->charge;out->status=RT->status;out->method=RT->method;
    for(i=0;i<5;i++)if(RT->counts[i]>12)return 0;
    if(id->captured){
        map=VWORD((void *)id->fs,0x20);
        if(!identity_range(map,4)||VWORD((void *)map,0)!=id->map)return 0;
        for(i=0;i<5;i++){
            out->counts[i]=RT->counts[i];
            for(j=0;j<out->counts[i];j++)if(!RT->candidates[i][j]||RT->candidates[i][j]>493)return 0;
            if(out->counts[i])out->method_mask|=(u8)(1u<<i);
        }
    }
    if(saved){
        if(!((int (*)(const SgpShinySaved *))CFG->core_valid)(saved))return 0;
        out->available=1;out->mode=saved->mode;out->target=saved->target;out->chain=saved->chain;
        out->denominator=(u16)((u32 (*)(const SgpShinySaved *,u32,u32))CFG->core_denominator)(saved,saved->target?saved->target:1,!saved->target);
    }
    return 1;
}
static u32 readonly(void *app,SgpShinySnapshot *out,SgpTrainingUiProof *proof,SgpShinySaved *saved,Identity *id)
{
    SgpShinySnapshot before,after;Identity first;u32 status;
    if(!snapshot(app,0,&before,&first))return SGP_SHINY_UNAVAILABLE;
    status=((u32 (*)(void *,SgpShinySaved *,SgpTrainingUiProof *))D->training_peek)((void *)first.fs,saved,proof);
    if(status)return status;
    if(!snapshot(app,0,&after,id)||!equal(&before,&after,32)||!equal(&first,id,sizeof(first)))return SGP_SHINY_STALE;
    if(!snapshot(app,saved,out,id))return SGP_SHINY_UNAVAILABLE;
    return SGP_SHINY_OK;
}
static int target_eligible(const Token *t)
{
    u32 i,m=t->draft.method,s=t->draft.target;
    if(!t->captured||!s)return 0;
    for(i=0;i<t->opened.counts[m];i++)if(RT->candidates[m][i]==s)return 1;
    return 0;
}
static u32 derive(const Token *t,const SgpShinySaved *saved,SgpShinySaved *next)
{
    const SgpShinyDraft *d=&t->draft;u32 changed;
    if(d->epoch!=t->opened.epoch||d->context!=t->opened.context||d->revision!=t->opened.revision||
       d->target>493||d->mode>1||d->method>=5||d->search>1||d->reserved[0]||d->reserved[1]||d->reserved[2]||
       t->opened.revision==0xFFFFFFFFu)return SGP_SHINY_STALE;
    if(RT->queued||RT->pending||RT->token)return SGP_SHINY_BUSY;
    changed=d->mode!=saved->mode||d->target!=saved->target;
    if(d->target!=saved->target&&d->target&&!target_eligible(t))return SGP_SHINY_NO_TARGET;
    if(d->search){
        if(!d->mode)return SGP_SHINY_PRO_ONLY;
        if(!target_eligible(t))return SGP_SHINY_NO_TARGET;
        if(changed||t->opened.charge!=40)return SGP_SHINY_NEED_CHARGE;
    }
    copy(next,saved,16);
    if(changed&&((int (*)(SgpShinySaved *,u32,u32))CFG->core_select)(next,d->mode,d->target)<0)return SGP_SHINY_UNAVAILABLE;
    return SGP_SHINY_OK;
}
static u32 prepare(void *app,const SgpShinySnapshot *opened,const SgpShinyDraft *draft,Token *t)
{
    Identity id;SgpShinySaved saved;u32 result;
    zero(t,sizeof(*t));
    result=readonly(app,&t->opened,&t->training,&saved,&id);
    if(result)return result;
    if(!equal(opened,&t->opened,32))return SGP_SHINY_STALE;
    t->magic=TOKEN_MAGIC;t->abi=1;t->bytes=152;t->app=(u32)app;
    t->app_generation=id.app_generation;t->fs=id.fs;t->options=id.options;
    t->captured=id.captured;t->map=id.map;copy(&t->draft,draft,20);
    return derive(t,&saved,&t->next);
}
static u32 validate(const Token *t,u32 inspect)
{
    return ((u32 (*)(void *,const SgpTrainingUiProof *,const SgpShinySaved *,u32))D->training_validate)((void *)t->fs,&t->training,&t->next,inspect);
}
/* Pure revalidation after the LAST hardware READ and again under the IRQ lock.
 * Training validate0 separately compares all 52 proof bytes. */
static int current(void *app,const Token *t)
{
    SgpShinySnapshot now;Identity id;SgpShinySaved derived;
    const SgpShinySaved *saved=(const SgpShinySaved *)((const u8 *)&t->training+36);
    if(!snapshot(app,saved,&now,&id)||!equal(&t->opened,&now,32)||
       t->app!=(u32)app||t->app_generation!=id.app_generation||t->fs!=id.fs||
       t->options!=id.options||t->captured!=id.captured||t->map!=id.map)return 0;
    return !derive(t,saved,&derived)&&equal(&derived,&t->next,16);
}
ENTRY u32 sgp_shiny_ui_peek(void *app,SgpShinySnapshot *out)
{
    Identity id;SgpShinySnapshot s;SgpTrainingUiProof proof;SgpShinySaved saved;u32 result;
    if(!IME||CPU_IRQ_MASK())return SGP_SHINY_BUSY;
    if(!identity(app,&id)||!buffer(out,32,app,&id))return SGP_SHINY_UNAVAILABLE;
    result=readonly(app,&s,&proof,&saved,&id);
    if(!result)copy(out,&s,32);
    return result;
}
ENTRY u32 sgp_shiny_ui_prepare(void *app,const SgpShinySnapshot *opened,const SgpShinyDraft *draft,SgpSettingsShinyToken *out)
{
    Identity id;Token t;u32 result;
    if(!IME||CPU_IRQ_MASK())return SGP_SHINY_BUSY;
    if(!identity(app,&id)||!buffer(opened,32,app,&id)||!buffer(draft,20,app,&id)||!buffer(out,152,app,&id)||
       overlap((u32)opened,32,(u32)draft,20)||overlap((u32)opened,32,(u32)out,152)||overlap((u32)draft,20,(u32)out,152))return SGP_SHINY_UNAVAILABLE;
    result=prepare(app,opened,draft,&t);
    if(!result)copy(out,&t,152);
    return result;
}
static int gate_valid(const SgpSettingsCommitGate *g,void *app,const Identity *id,u32 token,u32 gate)
{
    return g->abi==1&&g->bytes==12&&g->check==SGP_SETTINGS_UI_FINAL_CHECK&&
        buffer((void *)g->context,4,app,id)&&!overlap(g->context,4,token,152)&&!overlap(g->context,4,gate,12);
}
ENTRY u32 sgp_shiny_ui_commit(void *app,SgpSettingsShinyToken *wire,const SgpSettingsCommitGate *gate)
{
    Identity id;Token t,recomputed;SgpSettingsCommitGate g;u32 result,ime,changed;
    if(!IME||CPU_IRQ_MASK())return SGP_SHINY_BUSY;
    if(!identity(app,&id)||!buffer(wire,152,app,&id)||!buffer(gate,12,app,&id)||
       overlap((u32)wire,152,(u32)gate,12))return SGP_SHINY_UNAVAILABLE;
    copy(&t,wire,152);copy(&g,gate,12);
    if(t.magic!=TOKEN_MAGIC||t.abi!=1||t.bytes!=152||t.app!=(u32)app||
       !gate_valid(&g,app,&id,(u32)wire,(u32)gate))return SGP_SHINY_STALE;
    result=prepare(app,&t.opened,&t.draft,&recomputed);
    if(result)return result;
    if(!equal(&t,&recomputed,152))return SGP_SHINY_STALE;
    result=validate(&t,1);
    if(result)return result;
    ime=IME;IME=0;
    if(!identity(app,&id)||!buffer(wire,152,app,&id)||!buffer(gate,12,app,&id)||
       !gate_valid(&g,app,&id,(u32)wire,(u32)gate)||!equal(&g,gate,12)||!equal(&t,wire,152)||
       !current(app,&t)||validate(&t,0)||!((SgpSettingsFinalCheck)SGP_SETTINGS_UI_FINAL_CHECK)((void *)g.context)){
        IME=ime;return SGP_SHINY_STALE;
    }
    /* No fallible operations, callbacks, storage or yields beyond this point.
     * The Training store capability is the audited infallible bounded primitive. */
    ((void (*)(const SgpTrainingUiProof *,const SgpShinySaved *))D->training_store)(&t.training,&t.next);
    changed=t.opened.mode!=t.draft.mode||t.opened.target!=t.draft.target;
    if(changed){RT->charge=0;RT->pending=0;}
    RT->revision=t.opened.revision+1;RT->method=t.draft.method;RT->status=SGP_SHINY_OK;
    if(t.draft.search){RT->queued=1;RT->queued_context=t.opened.context;RT->queued_revision=t.opened.revision+1;}
    wire->words[0]=0;IME=ime;return SGP_SHINY_OK;
}
