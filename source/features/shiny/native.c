#include "internal.h"

static void bind_owner(void *fs,u32 fresh)
{
    invalidate();
    if(!ptr_ok(fs)||!ptr_ok(PTR(fs,12)))return;
    RT->fs=fs;RT->save=PTR(fs,12);
    RT->options=FN(void *(*)(void *),0x02028EA8)(RT->save);
    FN(void(*)(void *,u32),CFG->training_bind)(RT->save,fresh);
}
static int refresh_config_valid(void)
{
    u32 i,b,count=0;
    if(!CFG->species_count||CFG->species_count>493||CFG->species_reserved||
       (CFG->species_bitmap[0]&1)||(CFG->species_bitmap[61]&0xC0)||
       CFG->species_bitmap[62]||CFG->species_bitmap[63])return 0;
    for(i=0;i<64;++i){
        b=CFG->species_bitmap[i];
        while(b){b&=b-1;++count;}
    }
    return count==CFG->species_count;
}
static void refresh_party(void)
{
    void *party;u32 count,i,species;
    if(!refresh_config_valid())return;
    party=FN(void *(*)(void *),0x02074904)(RT->save);
    count=FN(u32(*)(void *),0x02074640)(party);
    if(count>6)return;
    for(i=0;i<count;++i){
        void *mon=FN(void *(*)(void *,u32),0x02074644)(party,i);
        if(FN(u32(*)(void *,u32,void *),CFG->training_read)(mon,3,0)||
           FN(u32(*)(void *,u32,void *),CFG->training_read)(mon,76,0))continue;
        species=FN(u32(*)(void *,u32,void *),CFG->training_read)(mon,5,0);
        if(species&&species<=493&&(CFG->species_bitmap[species>>3]&(1u<<(species&7))))
            FN(void(*)(void *),0x0206E250)(mon);
    }
}
void sgp_shiny_boot(void){invalidate();FN(void(*)(void),0x02000E6C)();}
void *sgp_shiny_continue(void *manager){void *fs=FN(void *(*)(void *),0x0203DFE0)(manager);bind_owner(fs,0);if(RT->fs)refresh_party();return fs;}
void *sgp_shiny_newgame(void *manager){void *fs=FN(void *(*)(void *),0x0203DFE0)(manager);bind_owner(fs,1);return fs;}
void sgp_shiny_delete(void *manager){invalidate();FN(void(*)(void *),0x0203E058)(manager);}
void sgp_shiny_leave(void *fs){RT->captured=0;if(live()&&fs==RT->fs)FN(void(*)(void *),CFG->search_capture)(fs);FN(void(*)(void *),0x0203DF34)(fs);}
/* Options launches its child directly, bypassing CallTask_LeaveField. Capture
 * here before the original launch clears runningFieldMap and unloads field. */
void sgp_shiny_options(void *fs,void *args){
    RT->captured=0;
    if(live()&&fs==RT->fs)FN(void(*)(void *),CFG->search_capture)(fs);
    FN(void(*)(void *,void *),0x0203EE14)(fs,args);
}
void sgp_shiny_control(void *fs){
    if(RT->queued){if(!live()||fs!=RT->fs){RT->queued=0;RT->captured=0;RT->pending=0;}
        else FN(void(*)(void *),CFG->search_dispatch)(fs);}
    FN(void(*)(void *),0x0203E15C)(fs);
}
u32 sgp_shiny_snapshot(void *app,SgpShinySnapshot *out)
{
    SgpShinySaved s;u32 i;
    if(!out)return 0;
    zero(out,sizeof(*out));out->status=SGP_SHINY_UNAVAILABLE;
    if(!app_live(app))return 0;
    out->epoch=RT->epoch;out->revision=RT->revision;out->context=RT->context;
    if(!read_saved(&s))return 1;
    out->available=1;out->mode=s.mode;out->target=s.target;out->chain=s.chain;
    out->charge=RT->charge;out->status=RT->status;out->method=RT->method;
    out->denominator=(u16)FN(u32(*)(const SgpShinySaved *,u32,u32),CFG->core_denominator)(&s,s.target?s.target:1,!s.target);
    if(cache_current())for(i=0;i<5;++i){out->counts[i]=RT->counts[i];if(out->counts[i])out->method_mask|=(u8)(1u<<i);}
    return 1;
}
u32 sgp_shiny_candidate(void *app,const SgpShinySnapshot *s,u32 method,u32 index)
{
    if(!s||!app_live(app)||!s->available||s->epoch!=RT->epoch||s->context!=RT->context||
       s->revision!=RT->revision||!cache_current()||method>=5||index>=RT->counts[method]||index>=12)return 0;
    return RT->candidates[method][index];
}
u32 sgp_shiny_apply(void *app,const SgpShinyDraft *d)
{
    SgpShinySaved s;u32 changed;
    if(!app_live(app)||!read_saved(&s))return SGP_SHINY_UNAVAILABLE;
    if(!d||d->epoch!=RT->epoch||d->context!=RT->context||d->revision!=RT->revision||
       d->mode>1||d->target>493||d->method>=5||d->search>1||d->reserved[0]||d->reserved[1]||d->reserved[2])return SGP_SHINY_STALE;
    if(RT->queued||RT->pending||RT->token)return SGP_SHINY_BUSY;
    changed=s.mode!=d->mode||s.target!=d->target;
    if(d->target!=s.target&&d->target&&!eligible(d->method,d->target))return SGP_SHINY_NO_TARGET;
    if(d->search){
        if(!d->mode)return SGP_SHINY_PRO_ONLY;
        if(!eligible(d->method,d->target))return SGP_SHINY_NO_TARGET;
        if(changed||RT->charge!=40)return SGP_SHINY_NEED_CHARGE;
    }
    if(changed){
        if(FN(int(*)(SgpShinySaved *,u32,u32),CFG->core_select)(&s,d->mode,d->target)<0||!access(&s,1))return SGP_SHINY_UNAVAILABLE;
        RT->charge=0;RT->revision++;RT->pending=0;
    }
    RT->method=d->method;RT->status=SGP_SHINY_OK;
    if(d->search){RT->queued=1;RT->queued_context=RT->context;RT->queued_revision=RT->revision;}
    return SGP_SHINY_OK;
}
/* The hook's third argument is copied from the audited caller's r5. */
u32 sgp_shiny_step_impl(void *stats,u32 which,void *fs)
{
    u32 result=FN(u32(*)(void *,u32),0x0202D0FC)(stats,which);SgpShinySaved s;
    if(which==0&&fs==RT->fs&&RT->charge<40&&read_saved(&s)&&s.mode&&s.target)RT->charge++;
    return result;
}
__attribute__((naked)) void sgp_shiny_step(void){__asm__ volatile("push {r4,lr}\n movs r2,r5\n bl sgp_shiny_step_impl\n pop {r4,pc}");}

static int begin_token(u32 kind,u32 species,u32 level,u32 ot,void *setup)
{
    SgpShinySaved s;
    RT->pending=0;RT->sequence++;
    if(!species||species>493||!level||level>100||!ptr_ok(setup)||
       WORD(setup,0)||PTR(setup,0x1C0)!=RT->save||!read_saved(&s)||ot!=trainer_ot())return 0;
    RT->token=kind;RT->token_failed=0;RT->token_done=0;
    RT->token_species=species;RT->token_level=level;RT->token_ot=ot;RT->token_setup=setup;
    return 1;
}
/* Original otType0 has no random-OT draws (only otType2 does). Preset OT
 * therefore preserves native IV/item RNG position while encrypting final PID. */
void sgp_shiny_create(void *mon,u32 species,u32 level,u32 iv,u32 fixed,u32 pid,u32 ot_type,u32 ot)
{
    if(RT->token){
        SgpShinySaved s;u32 shiny,offset,out;
        if(RT->token_done||RT->token_failed||species!=RT->token_species||level!=RT->token_level||
           iv!=32||fixed!=1||ot_type!=0||ot!=0||!ptr_ok(RT->token_setup)||
           WORD(RT->token_setup,0)||PTR(RT->token_setup,0x1C0)!=RT->save||!read_saved(&s)||RT->token_ot!=trainer_ot())RT->token_failed=1;
        else{
            RT->token_done=1;
            if(!FN(int(*)(SgpShinySaved *,u32,u32,u32,u32,u32 *,u32 *),CFG->core_draw)(
                &s,FN(u32(*)(void),0x0201FD2C)(),RT->token_ot,species,RT->token==2,&shiny,&offset)||
               !FN(int(*)(u32,u32,u32,u32,u32 *),CFG->core_transform)(pid,RT->token_ot,shiny,offset,&out)||!access(&s,1))RT->token_failed=1;
            else{pid=out;ot_type=1;ot=RT->token_ot;}
        }
    }
    /* On an impossible core failure this builds disposable setup content so
     * the native producer can free its temporary mon. Every scoped caller
     * aborts before launching or exposing the setup. This is not a fallback
     * lottery outcome. */
    FN(void(*)(void *,u32,u32,u32,u32,u32,u32,u32),0x0206DE38)(mon,species,level,iv,fixed,pid,ot_type,ot);
}
/* Native encounter generators are caller stack locals, including ARM9 DTCM.
 * This exception is limited to the complete temporary object; persistent
 * owners and battle setups still require main-RAM ptr_ok validation. */
static int gen_ok(const ShinyGen *gen)
{
    u32 a=(u32)gen;
    return !(a&3)&&((a>=0x02000000u&&a<=0x02400000u-sizeof(*gen))||
                    (a>=0x027E0000u&&a<=0x027E4000u-sizeof(*gen)));
}
u32 sgp_shiny_regular_impl(u32 species,u32 level,u32 battler,u32 perfect,ShinyGen *gen,void *lead,void *setup,u32 method)
{
    u32 admitted=0,success;
    if(RT->token){RT->token_failed=1;RT->pending=0;return 0;}
    RT->pending=0;
    if(method<=4&&battler==1&&!perfect&&gen_ok(gen))admitted=begin_token(1,species,level,gen->ot,setup);
    FN(void(*)(u32,u32,u32,u32,ShinyGen *,void *,void *),0x02247A18)(species,level,battler,perfect,gen,lead,setup);
    success=!admitted||(!RT->token_failed&&RT->token_done);
    RT->token=0;
    if(admitted&&success){RT->pending=1;RT->pend_setup=setup;RT->pend_species=species;
        RT->pend_epoch=RT->epoch;RT->pend_revision=RT->revision;RT->pend_sequence=RT->sequence;}
    if(!success){RT->pending=0;RT->status=SGP_SHINY_GENERATION_FAILED;}
    return success;
}
/* Copy three outgoing stack arguments and the caller's original method at
 * SP+0x28. 24-byte frame keeps the native eight-byte alignment. */
__attribute__((naked)) void sgp_shiny_regular(void)
{
    __asm__ volatile("push {r4,lr}\n sub sp,#16\n ldr r4,[sp,#24]\n str r4,[sp,#0]\n ldr r4,[sp,#28]\n str r4,[sp,#4]\n ldr r4,[sp,#32]\n str r4,[sp,#8]\n ldr r4,[sp,#64]\n str r4,[sp,#12]\n bl sgp_shiny_regular_impl\n add sp,#16\n pop {r4,pc}");
}
u32 sgp_shiny_static_impl(void *fs,u32 species,u32 level,u32 forced,void *setup)
{
    u32 admitted=0,success;
    if(RT->token){RT->token_failed=1;RT->pending=0;return 0;}
    RT->pending=0;
    if(!forced&&live()&&fs==RT->fs)admitted=begin_token(2,species,level,trainer_ot(),setup);
    FN(void(*)(void *,u32,u32,u32,void *),0x02247F30)(fs,species,level,forced,setup);
    success=!admitted||(!RT->token_failed&&RT->token_done);RT->token=0;
    if(!success)RT->status=SGP_SHINY_GENERATION_FAILED;
    return success;
}
u32 sgp_shiny_outcome(void *setup,void *fs)
{
    SgpShinySaved s;u32 admitted=RT->pending&&RT->pend_setup==setup&&RT->pend_epoch==RT->epoch&&
        RT->pend_revision==RT->revision&&RT->pend_sequence==RT->sequence&&fs==RT->fs;
    u32 species=RT->pend_species,result=0;
    RT->pending=0;
    if(admitted&&live()&&ptr_ok(setup)&&PTR(setup,0x1C0)==RT->save)result=WORD(setup,0x14);
    if(result>=1&&result<=6&&read_saved(&s)&&FN(int(*)(SgpShinySaved *,u32,u32),CFG->core_complete)(&s,species,result)>0)access(&s,1);
    return FN(u32(*)(void *,void *),0x02050724)(setup,fs);
}

void sgp_shiny_abort_setup(void *setup)
{
    RT->pending=0;RT->token=0;RT->status=SGP_SHINY_GENERATION_FAILED;
    FN(void(*)(void *),0x02051BF8)(setup);
}
void sgp_shiny_abort_static(void *setup){sgp_shiny_abort_setup(setup);RT->static_abort=1;}
/* Failure exits the guarded native setup frame before any battle statistics
 * or launch. It must not return to the instruction following the hooked BL. */
__attribute__((naked)) void sgp_shiny_static(void)
{
    __asm__ volatile("push {r4,lr}\n sub sp,#8\n ldr r4,[sp,#16]\n str r4,[sp]\n bl sgp_shiny_static_impl\n cmp r0,#0\n beq 1f\n add sp,#8\n pop {r4,pc}\n1:\n add sp,#8\n pop {r4}\n pop {r3}\n movs r0,r4\n push {r4,lr}\n bl sgp_shiny_abort_static\n pop {r4}\n pop {r3}\n ldr r3,=0x0205108B\n bx r3");
}
__attribute__((naked)) void sgp_shiny_scent_abort(void)
{
    __asm__ volatile("push {r4,lr}\n ldr r0,[sp,#36]\n bl sgp_shiny_abort_setup\n pop {r4}\n pop {r3}\n movs r0,#0\n ldr r3,=0x0224736F\n bx r3");
}
u32 sgp_shiny_scent_cleanup_impl(void *fs)
{
    RT->pending=0;RT->token=0;RT->status=SGP_SHINY_GENERATION_FAILED;
    FN(void(*)(u32,u32),0x02022C60)(4,0);
    *(volatile u16 *)0x04000050u=0;
    FN(void(*)(u32,u32),0x0201BB68)(2,3);
    FN(void(*)(void *,u32,u32),0x0201CB04)(PTR(fs,8),2,0);
    FN(void(*)(u32,u32),0x02022C60)(4,1);
    return 1;
}
__attribute__((naked)) void sgp_shiny_scent_cleanup(void)
{
    __asm__ volatile("push {r4,lr}\n movs r0,r5\n bl sgp_shiny_scent_cleanup_impl\n pop {r4,pc}");
}
void sgp_shiny_script_impl(void *task,u32 species,u32 level,void *winflag,u32 catchable,u32 forced,void *ctx)
{
    RT->static_abort=0;
    FN(void(*)(void *,u32,u32,void *,u32,u32),0x02051020)(task,species,level,winflag,catchable,forced);
    if(RT->static_abort){
        RT->static_abort=0;
        FN(void(*)(void *),0x0203FD60)(ctx);
        FN(void(*)(void *),0x0205F5A4)(PTR(PTR(ctx,0x80),0x3C));
    }
}
__attribute__((naked)) void sgp_shiny_script(void)
{
    __asm__ volatile("push {r4,lr}\n sub sp,#16\n ldr r4,[sp,#24]\n str r4,[sp]\n ldr r4,[sp,#28]\n str r4,[sp,#4]\n str r5,[sp,#8]\n bl sgp_shiny_script_impl\n add sp,#16\n pop {r4,pc}");
}
