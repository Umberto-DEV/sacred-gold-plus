/* Successor Settings owner adapter. No installer/address reservation implied. */
#include "owners.h"
#define U32 SettingsU32
#define U16 SettingsU16
#define U8 SettingsU8
#define OW_MAGIC 0x31574F53u
#define TX_MAGIC 0x31585453u
#define FS_SIZE 0x24u
#define SAVE_SIZE 0x2330Cu
#define WORD(a) (*(volatile U32 *)(a))
#define HALF(a) (*(volatile U16 *)(a))
#define BYTE(a) (*(volatile U8 *)(a))
#define IME WORD(0x04000208u)
#define MONO WORD(0x021D05F0u)
#define BUTTON WORD(0x021D1140u)
#define DESC ((const SgpSettingsUiDescriptor *)SGP_SETTINGS_UI_DESCRIPTOR)
#define CONF ((const SgpShinyConfig *)SGP_SHINY_CONFIG)
#define ARM(type,address) ((type)(address))
#define THUMB(type,address) ((type)((address)|1u))
#define ENTRY __attribute__((used,noinline))
typedef struct {U32 app,generation,fs,save,options;} OwnerIdentity;
typedef struct {
    U32 magic,bytes,owners,state;
    SettingsOwners before;
    SettingsState request;
} OwnerTransaction;
_Static_assert(sizeof(SettingsAudioPreview)==36,"audio ledger wire bytes");
_Static_assert(sizeof(SettingsOwners)==252,"private owner record");
_Static_assert(sizeof(OwnerTransaction)==492,"bounded transaction context");

static void ocopy(void *to,const volatile void *from,U32 n)
{U8 *a=to;const volatile U8 *b=from;while(n--)*a++=*b++;}
static void oclear(void *to,U32 n)
{U8 *a=to;while(n--)*a++=0;}
static int oequal(const void *a,const volatile void *b,U32 n)
{const U8 *x=a;const volatile U8 *y=b;while(n--)if(*x++!=*y++)return 0;return 1;}
static int orange(U32 p,U32 n)
{return !(p&3)&&n<=0x400000u&&p>=0x02000000u&&p<=0x02400000u-n;}
static int ooverlap(U32 a,U32 n,U32 b,U32 m)
{return a<b+m&&b<a+n;}
static int oidrange(U32 p,U32 n)
{return orange(p,n)&&!ooverlap(p,n,0x023C0000u,0x20000u);}
static int ocode(U32 p)
{return (p&1)&&orange(p&~3u,4);}
/* Pure identity check: final gate must never invoke even the native getter. */
static int oidmemory(const OwnerIdentity *id)
{
    U32 a=id->app,f=id->fs,s=id->save,o=id->options;
    return oidrange(a,0x30)&&oidrange(f,FS_SIZE)&&oidrange(s,SAVE_SIZE)&&
        !ooverlap(a,0x30,f,FS_SIZE)&&!ooverlap(a,0x30,s,SAVE_SIZE)&&!ooverlap(f,FS_SIZE,s,SAVE_SIZE)&&
        orange(o,4)&&o>=s+0x10&&o<=s+SAVE_SIZE-4&&
        /* SaveArray_Get(save,1): validated native getter plus its exact RAM
         * identity dependency, checked without a call in the final gate. */
        WORD(s+0x2302cu)==o-s-0x10&&
        WORD(0x021D4158u)==f&&WORD(f+12)==s&&WORD(a+0x24)==o&&
        WORD(a+0x28)==id->generation&&id->generation&&WORD(a+0x2c)==SGP_SETTINGS_UI_APP_MAGIC;
}
static int oidentity(void *app,OwnerIdentity *id)
{
    U32 a=(U32)app,f=WORD(0x021D4158u),s;
    if(!oidrange(a,0x30)||!oidrange(f,FS_SIZE))return 0;
    s=WORD(f+12);id->app=a;id->fs=f;id->save=s;
    id->options=WORD(a+0x24);id->generation=WORD(a+0x28);
    return oidmemory(id)&&(U32)THUMB(void *(*)(void *),0x02028EA8u)((void *)s)==id->options;
}
static int obuffer(const void *p,U32 n,const OwnerIdentity *id)
{
    U32 a=(U32)p;
    if(a&3)return 0;
    if(a>=SGP_SETTINGS_UI_STACK_LOW&&a<=SGP_SETTINGS_UI_STACK_HIGH-n)return 1;
    return a>=SGP_SETTINGS_UI_HEAP_LOW&&a<=SGP_SETTINGS_UI_HEAP_HIGH-n&&
        !ooverlap(a,n,id->app,0x30)&&!ooverlap(a,n,id->fs,FS_SIZE)&&!ooverlap(a,n,id->save,SAVE_SIZE);
}
/* Error publication must exclude BOTH captured and current live identities.
 * A forged/stale capture must never turn a live SaveData/FieldSystem extent
 * into an admitted reducer buffer merely by substituting captured pointers. */
static int olivebuffers(const void *state,U32 bytes,const SettingsOwners *owner,const OwnerIdentity *captured)
{
    OwnerIdentity live;
    oclear(&live,sizeof(live));live.app=captured->app;live.fs=WORD(0x021D4158u);
    if(!oidrange(live.fs,FS_SIZE))return 0;
    live.save=WORD(live.fs+12);
    return oidrange(live.save,SAVE_SIZE)&&obuffer(state,bytes,&live)&&obuffer(owner,sizeof(*owner),&live);
}
static void ofrom(const SettingsOwners *o,OwnerIdentity *id)
{id->app=o->app;id->generation=o->generation;id->fs=o->fs;id->save=o->save;id->options=o->options;}
static int orecordspace(const SettingsOwners *o,OwnerIdentity *id)
{
    U32 p=(U32)o;
    if((p&3)||!((p>=SGP_SETTINGS_UI_HEAP_LOW&&p<=SGP_SETTINGS_UI_HEAP_HIGH-sizeof(*o))||
               (p>=SGP_SETTINGS_UI_STACK_LOW&&p<=SGP_SETTINGS_UI_STACK_HIGH-sizeof(*o))))return 0;
    if(o->magic!=OW_MAGIC||o->bytes!=sizeof(*o))return 0;
    ofrom(o,id);return oidrange(id->app,0x30)&&oidrange(id->fs,FS_SIZE)&&
        oidrange(id->save,SAVE_SIZE)&&obuffer(o,sizeof(*o),id);
}
static int orecord(const SettingsOwners *o,OwnerIdentity *id)
{
    return orecordspace(o,id)&&oidmemory(id);
}
static U32 onmask(U32 r)
{
    switch(r){case SETTINGS_TEXT:return 0x000f;case SETTINGS_SCENE:return 0x0080;
    case SETTINGS_STYLE:return 0x0040;case SETTINGS_AUDIO:return 0x0030;
    case SETTINGS_BUTTON:return 0x0300;default:return 0x7c00;}
}
static U32 onshift(U32 r)
{
    switch(r){case SETTINGS_TEXT:return 0;case SETTINGS_SCENE:return 7;
    case SETTINGS_STYLE:return 6;case SETTINGS_AUDIO:return 4;
    case SETTINGS_BUTTON:return 8;default:return 10;}
}
static U32 opaddress(U32 i)
{
    switch(i){case 0:return 0x023D8713u;case 1:return 0x023D8714u;
    case 2:return 0x023D8716u;case 3:return 0x023D8717u;default:return 0x023D8718u;}
}
static U32 ogaddress(U32 i)
{
    switch(i){case 2:return 0x023D8E41u;case 3:return 0x023D89E2u;
    case 4:return 0x023DA240u;default:return 0x023D8704u;}
}
static U32 omax(U32 row)
{return row==SETTINGS_TEXT||row==SETTINGS_WIFI?2:row==SETTINGS_FRAME?19:1;}
static U32 ovalue(const SettingsDraft *d,U32 r)
{return r<6?((const U8 *)&d->native)[r]:((const U8 *)&d->plus)[r-6];}
static U32 obefore(const SettingsSnapshot *s,U32 r)
{return r<6?((const U8 *)&s->native)[r]:((const U8 *)&s->plus)[r-6];}
static int opavailable(const SettingsOwners *o,U32 i)
{return o->plus_guard[0]==0x5a&&(o->plus_load==1||o->plus_load==2)&&
    o->plus_guard[i]==(i==4?0x57:0x5a)&&o->plus_raw[i]<=(i==4?3:1);}
static void oraw(SettingsOwners *o)
{
    U32 i;
    o->native_raw=HALF(o->options);o->plus_load=BYTE(0x023D8703u);
    for(i=0;i<5;i++){o->plus_raw[i]=BYTE(opaddress(i));o->plus_guard[i]=BYTE(ogaddress(i));}
    o->mirrors[0]=BYTE(0x023D8700u);o->mirrors[1]=BYTE(0x023D8701u);
    o->button_raw=BUTTON;
}
static int ocapability(void)
{
    U32 i;
    if(DESC->magic!=SGP_SETTINGS_UI_MAGIC||DESC->abi!=1||DESC->bytes!=80||
       DESC->token_bytes!=152||DESC->training_proof_bytes!=52||DESC->flags!=3||
       !ocode(DESC->shiny_peek)||!ocode(DESC->shiny_prepare)||!ocode(DESC->shiny_commit)||
       CONF->magic!=SGP_SHINY_MAGIC||CONF->abi!=2||CONF->bytes!=152||!ocode(CONF->candidate))return 0;
    for(i=0;i<4;i++)if(DESC->reserved[i])return 0;
    return 1;
}
static int oentry(void)
{
    U32 irq;
    if(!IME)return 0;
    irq=ARM(U32 (*)(void),0x020D3A38u)();
    ARM(void (*)(U32),0x020D3A4Cu)(irq);return !irq;
}
ENTRY U32 settings_owner_capture(void *app,SettingsOwners *out,SettingsSnapshot *snapshot)
{
    OwnerIdentity id;SettingsOwners o;SettingsSnapshot again;U32 i,j,v,raw;
    if(!oentry())return SGP_SHINY_BUSY;
    if(!oidentity(app,&id)||!obuffer(out,sizeof(*out),&id)||!obuffer(snapshot,sizeof(*snapshot),&id)||
       ooverlap((U32)out,sizeof(*out),(U32)snapshot,sizeof(*snapshot)))return SGP_SHINY_UNAVAILABLE;
    oclear(&o,sizeof(o));o.magic=OW_MAGIC;o.bytes=sizeof(o);
    o.app=id.app;o.generation=id.generation;o.fs=id.fs;o.save=id.save;o.options=id.options;
    oraw(&o);raw=MONO;
    o.audio.original_raw=raw;o.audio.expected_raw=raw;o.audio.accepted_target=raw;
    o.audio.pending_target=raw;o.audio.app_generation=id.generation;
    for(i=0;i<6;i++){
        v=(o.native_raw&onmask(i))>>onshift(i);((U8 *)&o.opened.native)[i]=(U8)v;
        if(v<=omax(i))o.opened.editable_rows|=1u<<i;
    }
    for(i=0;i<5;i++){
        v=o.plus_raw[i];if(i==4&&v)v=v==3?2:1;
        ((U8 *)&o.opened.plus)[i]=(U8)v;
        if(opavailable(&o,i))o.opened.editable_rows|=1u<<(i+6);
    }
    if(ocapability()&&!((U32 (*)(void *,SgpShinySnapshot *))DESC->shiny_peek)(app,&o.opened.shiny)){
        for(i=0;i<5;i++)for(j=0;j<o.opened.shiny.counts[i];j++){
            v=((U32 (*)(void *,const SgpShinySnapshot *,U32,U32))CONF->candidate)(app,&o.opened.shiny,i,j);
            if(!v||v>493)return SGP_SHINY_STALE;
            o.opened.candidates[i][j]=(U16)v;
        }
        if(((U32 (*)(void *,SgpShinySnapshot *))DESC->shiny_peek)(app,&again.shiny)||
           !oequal(&o.opened.shiny,&again.shiny,sizeof(again.shiny)))return SGP_SHINY_STALE;
        o.opened.editable_rows|=(1u<<11)|(1u<<12)|(1u<<13);
    }
    if(!oidmemory(&id)||HALF(o.options)!=o.native_raw||BUTTON!=o.button_raw||MONO!=raw||
       BYTE(0x023D8703u)!=o.plus_load)return SGP_SHINY_STALE;
    for(i=0;i<5;i++)if(BYTE(opaddress(i))!=o.plus_raw[i]||BYTE(ogaddress(i))!=o.plus_guard[i])return SGP_SHINY_STALE;
    if(BYTE(0x023D8700u)!=o.mirrors[0]||BYTE(0x023D8701u)!=o.mirrors[1])return SGP_SHINY_STALE;
    ocopy(out,&o,sizeof(o));ocopy(snapshot,&o.opened,sizeof(*snapshot));return SGP_SHINY_OK;
}
/* Recompute masks independently of the reducer; forged snapshot/capabilities or
 * dirty masks cannot expand writes. Invalid clean rows stay disabled/raw. */
static int omodel(const SettingsOwners *o,const SettingsState *s,U32 *fields)
{
    U32 r,f=0,g=0;
    if(!oequal(&o->opened,&s->snapshot,sizeof(o->opened)))return 0;
    for(r=0;r<11;r++)if(ovalue(&s->draft,r)!=obefore(&s->snapshot,r)){
        if(!(s->snapshot.editable_rows&(1u<<r))||ovalue(&s->draft,r)>omax(r))return 0;
        f|=1u<<r;
    }
    if(s->draft.shiny.mode!=s->snapshot.shiny.mode)f|=1u<<11;
    if(s->draft.shiny.target!=s->snapshot.shiny.target)f|=1u<<12;
    if(s->draft.shiny.method!=s->snapshot.shiny.method)f|=SETTINGS_FIELD_METHOD;
    if(s->draft.shiny.search)f|=SETTINGS_FIELD_SEARCH;
    if(f&0xd800u){
        if(!s->snapshot.shiny.available||s->draft.shiny.mode>1||s->draft.shiny.target>493||
           s->draft.shiny.method>=5||s->draft.shiny.search>1||s->draft.shiny.reserved[0]||
           s->draft.shiny.reserved[1]||s->draft.shiny.reserved[2]||
           s->draft.shiny.epoch!=s->snapshot.shiny.epoch||s->draft.shiny.context!=s->snapshot.shiny.context||
           s->draft.shiny.revision!=s->snapshot.shiny.revision)return 0;
        if((f&(1u<<11))&&!(s->snapshot.editable_rows&(1u<<11)))return 0;
        if((f&(1u<<12))&&!(s->snapshot.editable_rows&(1u<<12)))return 0;
        if((f&(SETTINGS_FIELD_METHOD|SETTINGS_FIELD_SEARCH))&&!(s->snapshot.editable_rows&(1u<<13)))return 0;
        if((f&SETTINGS_FIELD_METHOD)&&!(s->snapshot.shiny.method_mask&(1u<<s->draft.shiny.method)))return 0;
        g|=SETTINGS_SHINY;
    }
    if(f&0x3fu)g|=SETTINGS_NATIVE;
    if(f&0x7c0u)g|=SETTINGS_PLUS;
    if(f!=s->dirty_fields||g!=s->dirty_groups)return 0;
    *fields=f;return 1;
}
static int oaudioready(const SettingsOwners *o,const SettingsState *s)
{
    const SettingsAudioPreview *a=&o->audio;U32 target;
    if(a->app_generation!=o->generation||a->ever_previewed>1||a->pending_changed>1||MONO!=a->expected_raw)return 0;
    target=s->draft.native.audio==o->opened.native.audio?a->original_raw:s->draft.native.audio;
    if(!a->ever_previewed)return !(s->dirty_fields&(1u<<SETTINGS_AUDIO))&&
        !a->accepted_generation&&a->accepted_target==a->original_raw&&
        !a->pending_changed&&a->pending_target==a->original_raw&&a->expected_raw==a->original_raw;
    return a->pending_changed==!!(s->dirty_fields&(1u<<SETTINGS_AUDIO))&&
        a->pending_generation&&a->accepted_generation==a->pending_generation&&
        a->accepted_target==target&&a->pending_target==target&&a->expected_raw==target;
}
static int odirty(const SettingsOwners *o,const SettingsState *s)
{
    U32 f,r;OwnerIdentity id;
    ofrom(o,&id);
    if(!oidmemory(&id)||!omodel(o,s,&f)||!oaudioready(o,s))return 0;
    for(r=0;r<6;r++)if((f&(1u<<r))&&((HALF(o->options)^o->native_raw)&onmask(r)))return 0;
    if((f&(1u<<SETTINGS_BUTTON))&&BUTTON!=o->button_raw)return 0;
    for(r=0;r<5;r++)if(f&(1u<<(r+6))){
        if(!opavailable(o,r)||BYTE(0x023D8704u)!=o->plus_guard[0]||BYTE(0x023D8703u)!=o->plus_load||
           BYTE(ogaddress(r))!=o->plus_guard[r]||BYTE(opaddress(r))!=o->plus_raw[r])return 0;
        if(r<2&&BYTE(0x023D8700u+r)!=o->mirrors[r])return 0;
    }
    return 1;
}
static int orequest(const SettingsState *s)
{
    return s->awaiting_apply==1&&s->release_gate==1&&s->choice==0&&
        (s->view==SETTINGS_APPLY_CONFIRM||s->view==SETTINGS_EXIT_CONFIRM);
}
ENTRY U32 settings_final_check(void *context)
{
    const OwnerTransaction *t=context;OwnerIdentity id;U32 p=(U32)t;
    if((p&3)||!((p>=SGP_SETTINGS_UI_HEAP_LOW&&p<=SGP_SETTINGS_UI_HEAP_HIGH-sizeof(*t))||
               (p>=SGP_SETTINGS_UI_STACK_LOW&&p<=SGP_SETTINGS_UI_STACK_HIGH-sizeof(*t))))return 0;
    if(t->magic!=TX_MAGIC||t->bytes!=sizeof(*t)||!orecord(&t->before,&id)||
       !obuffer(t,sizeof(*t),&id)||!obuffer((void *)t->owners,sizeof(SettingsOwners),&id)||
       !obuffer((void *)t->state,sizeof(SettingsState),&id)||
       ooverlap(p,sizeof(*t),t->owners,sizeof(SettingsOwners))||ooverlap(p,sizeof(*t),t->state,sizeof(SettingsState))||
       ooverlap(t->owners,sizeof(SettingsOwners),t->state,sizeof(SettingsState))||
       !oequal(&t->before,(void *)t->owners,sizeof(SettingsOwners))||
       !oequal(&t->request,(void *)t->state,sizeof(SettingsState))||!orequest(&t->request))return 0;
    return odirty(&t->before,&t->request);
}
/* Main thread owns these specific Options bits/Plus fields/mirrors: native
 * options.c and Plus opz_scrivi are their writers; VBlank only publishes tiles.
 * Remask IME for the bounded stores after Shiny restores it. No callback,
 * getter, setter, sound or other fallible service occurs in this phase. */
static void ostore(const SettingsOwners *o,const SettingsState *s)
{
    U32 f=s->dirty_fields,r,mask=0,bits=0,v;
    for(r=0;r<6;r++)if(f&(1u<<r)){mask|=onmask(r);bits|=ovalue(&s->draft,r)<<onshift(r);}
    if(mask)HALF(o->options)=(U16)((HALF(o->options)&~mask)|bits);
    for(r=0;r<5;r++)if(f&(1u<<(r+6))){
        v=ovalue(&s->draft,r+6);if(r==4&&v)v++;
        BYTE(opaddress(r))=(U8)v;if(r<2)BYTE(0x023D8700u+r)=(U8)v;
    }
    if(f&(1u<<SETTINGS_BUTTON))BUTTON=s->draft.native.button?3:0;
}
/* Every refusal publication re-admits the destination after the last possible
 * storage callback. Stale identities may still report an error when the UI
 * buffers are safe; becoming current FieldSystem/SaveData must publish nothing. */
static SettingsResult oreject(SettingsState *state,const SettingsOwners *owners,const OwnerIdentity *opened,U32 status)
{
    OwnerIdentity current;
    if(!orecordspace(owners,&current)||!obuffer(state,sizeof(*state),&current)||
       !obuffer(state,sizeof(*state),opened)||!obuffer(owners,sizeof(*owners),opened)||
       !olivebuffers(state,sizeof(*state),owners,opened)||
       ooverlap((U32)state,sizeof(*state),(U32)owners,sizeof(*owners)))return SETTINGS_NOOP;
    return settings_apply_result(state,status);
}
ENTRY SettingsResult settings_apply(SettingsState *state,const SettingsOwners *owners)
{
    OwnerIdentity id;OwnerTransaction t;SgpSettingsShinyToken token;SgpSettingsCommitGate gate;
    U32 result=SGP_SHINY_STALE,ime,irq,fields;
    if(!orecordspace(owners,&id)||!obuffer(state,sizeof(*state),&id)||
       !olivebuffers(state,sizeof(*state),owners,&id)||
       ooverlap((U32)state,sizeof(*state),(U32)owners,sizeof(*owners)))return SETTINGS_NOOP;
    if(!state->awaiting_apply)return SETTINGS_NOOP;
    if(!orequest(state)||!oidmemory(&id))return oreject(state,owners,&id,SGP_SHINY_STALE);
    if(!IME)return oreject(state,owners,&id,SGP_SHINY_BUSY);
    irq=ARM(U32 (*)(void),0x020D3A38u)();ARM(void (*)(U32),0x020D3A4Cu)(irq);
    if(irq)return oreject(state,owners,&id,SGP_SHINY_BUSY);
    if(!omodel(owners,state,&fields)||!odirty(owners,state))return oreject(state,owners,&id,result);
    oclear(&t,sizeof(t));t.magic=TX_MAGIC;t.bytes=sizeof(t);t.owners=(U32)owners;t.state=(U32)state;
    ocopy(&t.before,owners,sizeof(*owners));ocopy(&t.request,state,sizeof(*state));
    if(fields&0xd800u){
        if(!ocapability())return oreject(state,owners,&id,SGP_SHINY_UNAVAILABLE);
        result=((U32 (*)(void *,const SgpShinySnapshot *,const SgpShinyDraft *,SgpSettingsShinyToken *))DESC->shiny_prepare)
            ((void *)id.app,&t.request.snapshot.shiny,&t.request.draft.shiny,&token);
        if(result)return oreject(state,owners,&id,result);
        gate.abi=1;gate.bytes=12;gate.check=(U32)settings_final_check;gate.context=(U32)&t;
        result=((U32 (*)(void *,SgpSettingsShinyToken *,const SgpSettingsCommitGate *))DESC->shiny_commit)((void *)id.app,&token,&gate);
        if(result)return oreject(state,owners,&id,result);
        ime=IME;IME=0;ostore(&t.before,&t.request);IME=ime;
    }else{
        ime=IME;IME=0;
        if(!settings_final_check(&t)){IME=ime;return oreject(state,owners,&id,SGP_SHINY_STALE);}
        ostore(&t.before,&t.request);IME=ime;
    }
    return settings_apply_result(state,SGP_SHINY_OK);
}
/* Validate both lists completely before taking a node. Shared visited bits
 * reject cycles and a node simultaneously in pending/free. Missing nodes may
 * legitimately belong to native in-flight batches; never touch those batches. */
static int opool(void)
{
    U32 seen[8],list,p,tail,last,i,index,offset;
    if(WORD(0x021E1A40u)!=1)return 0;
    for(i=0;i<8;i++)seen[i]=0;
    for(list=0;list<2;list++){
        p=WORD(0x021E1A60u+(list?8:0));tail=WORD(0x021E1A60u+(list?12:16));last=0;
        while(p){
            if(p<0x021E1D40u||p>=0x021E3540u)return 0;
            offset=p-0x021E1D40u;
            /* Exact quotient for offset/8 in0..767; no division runtime. */
            index=((offset>>3)*683u)>>11;
            if(index*24!=offset)return 0;
            if(seen[index>>5]&(1u<<(index&31)))return 0;
            seen[index>>5]|=1u<<(index&31);last=p;p=WORD(p);
        }
        if(last!=tail)return 0;
    }
    return 1;
}
static U32 opreview(SettingsOwners *o,U32 target,U32 explicit_change)
{
    OwnerIdentity id;SettingsAudioPreview *a;U32 irq,node,nextgen;
    if(!orecord(o,&id))return SGP_SHINY_UNAVAILABLE;
    a=&o->audio;
    if(a->app_generation!=id.generation||a->ever_previewed>1||a->pending_changed>1||MONO!=a->expected_raw||
       (!a->ever_previewed&&(a->expected_raw!=a->original_raw||a->accepted_generation||a->accepted_target!=a->original_raw)))return SGP_SHINY_STALE;
    nextgen=a->pending_generation;
    if(target!=a->pending_target||explicit_change!=a->pending_changed){
        if(nextgen==0xffffffffu)return SGP_SHINY_STALE;
        nextgen++;
    }
    if(!nextgen&&explicit_change)nextgen=1;
    if(!a->ever_previewed&&!explicit_change&&target==a->original_raw){
        /* Cancel only an intent which never acquired/queued any command.
         * Preserve exact entry raw and accepted history; keep the monotonic
         * generation, and mark only pending intent as the untouched baseline. */
        if(a->pending_target!=target||a->pending_changed){
            a->pending_target=target;a->pending_generation=nextgen;a->pending_changed=0;
        }
        return SGP_SHINY_OK;
    }
    if(a->ever_previewed&&nextgen==a->accepted_generation&&target==a->accepted_target)return SGP_SHINY_OK;
    /* Pending request is transient UI data; BUSY preserves raw owner/queue. */
    a->pending_target=target;a->pending_generation=nextgen;a->pending_changed=explicit_change;
    irq=ARM(U32 (*)(void),0x020D3A38u)();
    if(!oidmemory(&id)||MONO!=a->expected_raw||!opool()){
        ARM(void (*)(U32),0x020D3A4Cu)(irq);return SGP_SHINY_STALE;
    }
    node=(U32)ARM(void *(*)(U32),0x020D5714u)(0);
    if(!node){ARM(void (*)(U32),0x020D3A4Cu)(irq);return SGP_SHINY_BUSY;}
    /* No fallible step after allocation: native Push has no failure path. */
    WORD(node+4)=0x18;WORD(node+8)=target?0x40:0xffffffffu;
    WORD(node+12)=0;WORD(node+16)=0;WORD(node+20)=0;
    ARM(void (*)(void *),0x020D579Cu)((void *)node);MONO=target;
    a->expected_raw=target;a->accepted_target=target;a->accepted_generation=nextgen;a->ever_previewed=1;
    ARM(void (*)(U32),0x020D3A4Cu)(irq);return SGP_SHINY_OK;
}
ENTRY U32 settings_owner_preview(SettingsOwners *o,const SettingsState *s)
{
    OwnerIdentity id;U32 target,fields,changed;
    if(!oentry())return SGP_SHINY_BUSY;
    if(!orecord(o,&id)||!obuffer(s,sizeof(*s),&id)||
       ooverlap((U32)o,sizeof(*o),(U32)s,sizeof(*s))||!omodel(o,s,&fields))return SGP_SHINY_STALE;
    target=s->view==SETTINGS_SELECTOR&&s->selector_row==SETTINGS_AUDIO?s->selector_pending:s->draft.native.audio;
    changed=target!=o->opened.native.audio;
    if(changed&&target>1)return SGP_SHINY_STALE;
    if(!changed)target=o->audio.original_raw;
    return opreview(o,target,changed);
}
ENTRY U32 settings_owner_rollback(SettingsOwners *o)
{
    OwnerIdentity id;
    if(!oentry())return SGP_SHINY_BUSY;
    if(!orecord(o,&id))return SGP_SHINY_UNAVAILABLE;
    return opreview(o,o->audio.original_raw,0);
}
