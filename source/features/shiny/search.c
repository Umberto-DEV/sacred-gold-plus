#include "internal.h"

static int field_ready(void *fs)
{
    void *flags;
    if(!live()||fs!=RT->fs||!overlay_loaded()||!WORD(fs,0x6C)||WORD(fs,0x70)||
       !ptr_ok(PTR(fs,0x40))||!ptr_ok(PTR(fs,0x20)))return 0;
    flags=FN(void *(*)(void *),0x020503D0)(RT->save);
    return !FN(u32(*)(void *),0x02066860)(flags)&&!FN(u32(*)(void *),0x02066870)(flags)&&
           !FN(u32(*)(void *),0x02066644)(flags);
}
static void disk_slots(const u8 *data,ShinySlot *out)
{
    u32 i;for(i=0;i<5;++i){out[i].species=*(const u16 *)(data+4*i+2);out[i].max=data[4*i+1];out[i].min=data[4*i];}
}
static u32 enumerate(void *fs)
{
    const u8 *data;void *dex,*lead;ShinyGen gen;ShinyPosition position;
    u32 method,i,j,n;u8 type=255;
    if(!field_ready(fs))return 0;
    zero(RT->counts,sizeof(RT->counts));zero(RT->slot_count,sizeof(RT->slot_count));
    data=FN(const u8 *(*)(void *),0x0203B8B8)(fs);if(!data)return 0;
    FN(void(*)(void *,ShinyPosition *),0x020649B8)(fs,&position);
    if(position.flags&3)return 0;
    lead=FN(void *(*)(void *,u32),0x02074644)(FN(void *(*)(void *),0x02074904)(RT->save),0);
    FN(void(*)(void *,void *,const void *,ShinyGen *),0x02248618)(fs,lead,data,&gen);
    dex=FN(void *(*)(void *),0x0202A634)(RT->save);
    for(method=0;method<5;++method){
        ShinySlot *slots=RT->slots[method];
        if(method<2){
            if(!data[method]||!FN(u32(*)(void *,u32,u8 *),0x0224762C)(fs,position.standing,&type)||type!=method)continue;
            if(!method){FN(void(*)(const void *,ShinySlot *),0x02246A84)(data,slots);
                FN(void(*)(void *,const void *,ShinySlot *,ShinySlot *),0x02246B58)(fs,data,slots,slots+1);
                FN(void(*)(void *,const void *,ShinySlot *),0x02246B00)(fs,data,slots);n=12;
            }else{disk_slots(data+0x64,slots);FN(void(*)(void *,const void *,ShinySlot *),0x02246B9C)(fs,data,slots);n=5;}
        }else{
            u32 rod=method-2;
            if(!data[method+1]||FN(u32(*)(ShinyPosition *),0x020650E8)(&position)||
               !FN(u32(*)(void *,u32,u32,u32),0x020784B0)(FN(void *(*)(void *),0x0207879C)(RT->save),445+rod,1,11))continue;
            disk_slots(data+0x80+20*rod,slots);
            FN(void(*)(const void *,u32,ShinySlot *),0x02246AD4)(data,rod,slots);
            FN(void(*)(void *,u32,const void *,ShinySlot *),0x02246BD8)(fs,rod,data,slots);n=5;
        }
        RT->slot_count[method]=(u8)n;
        for(i=0;i<n;++i){u32 species=slots[i].species;
            if(!species||species>493||!slots[i].min||slots[i].max>100||slots[i].min>slots[i].max||
               !FN(u32(*)(void *,u32),0x0202A044)(dex,species)||
               (species==201&&!FN(u32(*)(ShinyGen *),0x022482A4)(&gen)))continue;
            for(j=0;j<RT->counts[method];++j)if(RT->candidates[method][j]==species)break;
            if(j==RT->counts[method])RT->candidates[method][RT->counts[method]++]=(u16)species;
        }
    }
    return 1;
}
void sgp_shiny_capture(void *fs)
{
    RT->captured=0;RT->context++;if(!RT->context)RT->context=1;
    if(!enumerate(fs))return;
    RT->map=WORD(PTR(fs,0x20),0);RT->x=FN(u32(*)(void *),0x0205C67C)(PTR(fs,0x40));RT->z=FN(u32(*)(void *),0x0205C688)(PTR(fs,0x40));
    RT->time=FN(u32(*)(void),0x0201481C)();RT->captured=1;
}
static int idle(void *fs)
{
    void *manager=PTR(fs,0),*avatar=PTR(fs,0x40);u32 state;
    if(!ptr_ok(manager)||!ptr_ok(avatar)||!PTR(manager,0)||PTR(manager,4)||WORD(manager,8)||WORD(manager,12)||
       PTR(fs,0x10)||!FN(u32(*)(void *),0x0203E13C)(fs))return 0;
    state=WORD(avatar,0x14);return (state==0||state==3)&&!WORD(avatar,0x10);
}
void sgp_shiny_dispatch(void *fs)
{
    SgpShinySaved s;ShinySlot chosen,slots[12];ShinyGen gen;void *lead,*setup;u32 method,i,n;
    if(!RT->queued)return;
    if(!live()||fs!=RT->fs){RT->queued=0;RT->pending=0;RT->captured=0;return;}
    if(!cache_current()||RT->queued_context!=RT->context||RT->queued_revision!=RT->revision){
        RT->queued=0;RT->captured=0;RT->status=SGP_SHINY_STALE;return;
    }
    if(!WORD(fs,0x6C)||!overlay_loaded()||!idle(fs))return;
    if(!field_ready(fs)){RT->queued=0;RT->captured=0;RT->status=SGP_SHINY_STALE;return;}
    RT->queued=0;
    if(!RT->captured||RT->queued_context!=RT->context||RT->queued_revision!=RT->revision||
       RT->map!=WORD(PTR(fs,0x20),0)||RT->x!=FN(u32(*)(void *),0x0205C67C)(PTR(fs,0x40))||RT->z!=FN(u32(*)(void *),0x0205C688)(PTR(fs,0x40))||
       RT->time!=FN(u32(*)(void),0x0201481C)()){
        RT->status=SGP_SHINY_STALE;RT->captured=0;return;
    }
    if(RT->pending||RT->token){RT->status=SGP_SHINY_BUSY;return;}
    if(!read_saved(&s)){RT->status=SGP_SHINY_UNAVAILABLE;return;}
    method=RT->method;
    if(!s.mode||!s.target||RT->charge!=40||method>=5){RT->status=SGP_SHINY_STALE;return;}
    RT->captured=enumerate(fs);
    if(!eligible(method,s.target)){RT->status=SGP_SHINY_NO_TARGET;return;}
    n=RT->slot_count[method];
    for(i=0;i<n;++i)if(RT->slots[method][i].species==s.target)break;
    if(i==n){RT->status=SGP_SHINY_NO_TARGET;return;}
    chosen=RT->slots[method][i];for(i=0;i<n;++i)slots[i]=chosen;
    lead=FN(void *(*)(void *,u32),0x02074644)(FN(void *(*)(void *),0x02074904)(RT->save),0);
    FN(void(*)(void *,void *,const void *,ShinyGen *),0x02248618)(fs,lead,FN(const void *(*)(void *),0x0203B8B8)(fs),&gen);
    gen.scent=1;gen.repel=0;
    setup=FN(void *(*)(u32,u32),0x020518D8)(11,0);
    if(!setup){RT->status=SGP_SHINY_GENERATION_FAILED;return;}
    FN(void(*)(void *,void *),0x02051F00)(setup,fs);
    if(method>=2)FN(void(*)(void *),0x02052544)(setup);
    if(!FN(u32(*)(void *,u32,ShinyGen *,ShinySlot *,u32,u32,void *),0x02247B64)(lead,method>=2?method-2:255,&gen,slots,method>=2?2:method,1,setup)){
        RT->pending=0;FN(void(*)(void *),0x02051BF8)(setup);RT->status=SGP_SHINY_GENERATION_FAILED;return;
    }
    RT->charge=0;RT->status=SGP_SHINY_OK;
    HALF(fs,0x7C)=0;HALF(fs,0x7E)=0;
    FN(void(*)(void *,void *),0x02050B08)(fs,setup);
}
