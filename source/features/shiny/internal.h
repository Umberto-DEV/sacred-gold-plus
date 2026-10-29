#ifndef SGP_SHINY_INTERNAL_H
#define SGP_SHINY_INTERNAL_H
#include "api.h"
typedef SgpShinyU32 u32; typedef SgpShinyU16 u16; typedef SgpShinyU8 u8;
#define FN(type,address) ((type)((address)|1u))
#define CFG ((const SgpShinyConfig *)SGP_SHINY_CONFIG)
#define WORD(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define HALF(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define PTR(p,o) (*(void **)((u8 *)(p)+(o)))
#define RT ((ShinyRuntime *)0x023CB200u)
typedef struct {u32 species;u16 max,min;} ShinySlot;
typedef struct {u32 ot,repel,scent;u8 level,egg,ability,pad0,pad1,sinjoh,puzzle[4],pad2[2];void *dex;} ShinyGen;
_Static_assert(sizeof(ShinyGen)==28,"native encounter state ABI");
typedef struct {u32 map,state;u16 flags,facing,standing,pad;void *avatar,*fs;} ShinyPosition;
_Static_assert(sizeof(ShinyPosition)==24,"native position ABI");
typedef struct {
    u32 magic,epoch,revision,context; void *fs,*save,*options;
    u32 captured,map,x,z,time; u8 charge,status,method,queued;
    u8 counts[5],padding[3]; u16 candidates[5][12];
    ShinySlot slots[5][12]; u8 slot_count[5],reserved[3];
    u32 queued_context,queued_revision;
    u32 sequence,pending,pend_epoch,pend_revision,pend_sequence,pend_species;
    void *pend_setup;
    u32 token,token_failed,token_done,token_species,token_level,token_ot;
    void *token_setup; u32 static_abort;
} ShinyRuntime;
_Static_assert(sizeof(ShinyRuntime)<=1536,"runtime reserve");
static inline void zero(void *p,u32 n){u8 *q=p;while(n--)*q++=0;}
static inline int ptr_ok(const void *p){u32 a=(u32)p;return !(a&3)&&a>=0x02000000u&&a<0x02400000u;}
static inline void invalidate(void){u32 e=RT->epoch+1;zero(RT,sizeof(*RT));RT->magic=SGP_SHINY_MAGIC;RT->epoch=e?e:1;}
static inline int live(void){
    if(RT->magic!=SGP_SHINY_MAGIC||!RT->epoch||!ptr_ok(RT->fs)||
       *(void **)0x021D4158!=RT->fs)return 0;
    if(PTR(RT->fs,12)!=RT->save||!ptr_ok(RT->save))return 0;
    return FN(void *(*)(void *),0x02028EA8)(RT->save)==RT->options;
}
static inline int app_live(void *app){return live()&&ptr_ok(app)&&PTR(app,0x24)==RT->options;}
static inline int access(SgpShinySaved *s,u32 write){return FN(int(*)(void *,void *,u32),CFG->training_access)(RT->fs,s,write);}
static inline int read_saved(SgpShinySaved *s){return live()&&access(s,0)&&FN(int(*)(const SgpShinySaved *),CFG->core_valid)(s);}
static inline int cache_current(void){return RT->captured&&ptr_ok(PTR(RT->fs,0x20))&&WORD(PTR(RT->fs,0x20),0)==RT->map;}
static inline int eligible(u32 method,u32 species){u32 i;if(!cache_current()||method>=5||!species)return 0;for(i=0;i<RT->counts[method];++i)if(RT->candidates[method][i]==species)return 1;return 0;}
static inline u32 trainer_ot(void){return FN(u32(*)(void *),0x02028F84)(FN(void *(*)(void *),0x02028E9C)(RT->save));}
static inline int overlay_loaded(void){return *(u32 *)0x02246C94u==0x28038800u && *(u16 *)0x02246A84u==0xB538u && *(u16 *)0x02248618u==0xB5F8u;}
#endif
