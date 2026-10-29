/* Resident training adapter. Native layouts remain opaque except audited ABI fields. */
#include "../training/sorgenti/core.c"
#include "../training/sorgenti/clock.c"
#include "../training/sorgenti/journal.c"
#include "transaction.c"
#include "ownership.c"
typedef sgp_train_u8 u8; typedef sgp_train_u16 u16; typedef sgp_train_u32 u32;
typedef sgp_train_u64 u64;
#define FN(a,t) ((t)((a)|1u))
#define R32(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define R16(p,o) (*(u16 *)((u8 *)(p)+(o)))
#define PTR(p,o) (*(void **)((u8 *)(p)+(o)))
#define ENTRY __attribute__((used,noinline))
#define CFG ((const u32 *)0x023D2F00u)
#define GET training_read
#define BOX training_box_read
#define SET FN(0x0206EC40,void (*)(void *,int,const void *))
#define SETBOX FN(0x0206ED70,void (*)(void *,int,const void *))
#define CALC FN(0x0206E250,void (*)(void *))
#define ARRAY FN(0x020272C8,void *(*)(void *,u32))
#define PARTY FN(0x02074904,void *(*)(void *))
#define MON FN(0x02074644,void *(*)(void *,int))
#define COUNT FN(0x02074640,u32 (*)(void *))
#define PROFILE FN(0x02028E9C,void *(*)(void *))
#define MONEY FN(0x02029024,u32 (*)(void *))
#define SUBMONEY FN(0x02029068,u32 (*)(void *,u32))
#define BAG FN(0x0207879C,void *(*)(void *))
#define ADD FN(0x02078398,int (*)(void *,u16,u16,u32))
#define TAKE FN(0x02078434,int (*)(void *,u16,u16,u32))
#define ROOM FN(0x02078384,int (*)(void *,u16,u16,u32))
#define READ FN(0x0202877C,int (*)(u32,void *,u32))
#define WRITE FN(0x02028758,int (*)(u32,const void *,u32))
#define CRC FN(0x0201FF98,u16 (*)(const void *,u32))
#define VAR FN(0x02040374,u16 *(*)(void *,u16))
#define VALUE FN(0x020403AC,u16 (*)(void *,u16))
#define EXP FN(0x0206FD00,u32 (*)(u32,u32))
#define LEVEL FN(0x0206FD70,u32 (*)(void *))
#define ATTR FN(0x02077D88,u32 (*)(u16,u32,u32))
#define MAGIC 0x31544E52u
/* All persistent state is encoded by journal.c, never by dumping this struct. */
typedef struct {
 u32 magic; void *save; u32 enabled,writable,record_status,preview_slot,preview_valid;
 sgp_train_journal journal;
 sgp_training_request request;
 u8 primary[256],mirror[256],record[256];
 u32 shiny_admitted;
} TrainingState;
#define S ((TrainingState *)0x023D3000u)
_Static_assert(sizeof(TrainingState)<=0x1000,"training state overflow");
static void copy_bytes(void *to,const void *from,u32 n){u8 *a=to;const u8 *b=from;while(n--)*a++=*b++;}
static void clear_bytes(void *to,u32 n){volatile u8 *a=to;while(n--)*a++=0;}
/* Validate the encrypted checksum on a disposable segment before invoking a
 * getter that would otherwise enter the native assertion path for bad data. */
static int checksum_valid(void *mon,u32 decrypted){
 u32 segment[32];
 if(R16(mon,4)&4)return 0;
 if(R16(mon,4)&decrypted)return 1;
 copy_bytes(segment,(u8 *)mon+8,128);
 FN(0x020725E0,void (*)(void *,u32,u32))(segment,128,R16(mon,6));
 return FN(0x020725E8,u32 (*)(void *,u32))(segment,128)==R16(mon,6);
}
ENTRY u32 training_read(void *mon,int field,void *dest){
 if((field==5||field==3)&&!checksum_valid(mon,1))return field==3;
 return FN(0x0206E540,u32 (*)(void *,int,void *))(mon,field,dest);
}
ENTRY u32 training_box_read(void *mon,int field,void *dest){
 if((field==5||field==3)&&!checksum_valid(mon,2))return field==3;
 return FN(0x0206E640,u32 (*)(void *,int,void *))(mon,field,dest);
}

static u8 policy(void){return S->magic==MAGIC&&S->enabled?S->journal.policy:SGP_TRAIN_LEGACY;}
static int clock_now(u8 clock,u64 *now){
 if(clock==SGP_TRAIN_PLAY){*now=S->journal.played;return 1;}
 if(!R32((void *)0x021D1048,0)||R32((void *)0x021D1048,12))return 0;
 *now=FN(0x020147DC,u64 (*)(void))();return 1;
}
static void advance_all(void){u32 i;u64 now;for(i=0;i<2;i++)if(S->journal.jobs[i].active&&clock_now(S->journal.jobs[i].clock,&now))sgp_train_advance(&S->journal.jobs[i],policy(),now);}
static int sector_owner(u32 sector,int claim);
static void load_training(void *save,int disk){
 u8 source,writable=0;u32 sector;u8 *footer;int status=SGP_TRAIN_ERASED;
 clear_bytes(S,sizeof(*S));S->save=save;sgp_train_defaults(&S->journal);
 if(disk){
  sector=0x31000+(R16(save,0x2330A)?0x40000:0);
  footer=(u8 *)save+0x10+R32(save,0x232B8)+R32(save,0x232BC)-16;
  if(!READ(sector,S->primary,256)||!READ(sector+0x200,S->mirror,256))status=SGP_TRAIN_CORRUPT;
  else status=sgp_train_select(S->primary,S->mirror,R32(save,0x23010),R16(footer,14),&S->journal,&source,&writable);
 }else writable=1;
 if(status==SGP_TRAIN_VALID&&!writable&&sector_owner(sector,0)&&
    !training_record_future(S->primary)&&!training_record_future(S->mirror))writable=1;
 if(status!=SGP_TRAIN_VALID)S->journal.flags=SGP_TRAIN_SHINY_ONLY;
 S->enabled=status==SGP_TRAIN_VALID&&!S->journal.flags;S->writable=writable;S->record_status=status;S->magic=MAGIC;
 if(S->enabled)advance_all();
}
static void ensure(void *save){if(S->magic!=MAGIC||S->save!=save)load_training(save,R32(save,4)&&!R32(save,8));}
ENTRY int training_load(void *save){int r;S->magic=0;r=FN(CFG[0],int (*)(void *))(save);if(r)load_training(save,1);return r;}
ENTRY void training_play(void *igt,u32 delta){
 if(S->magic==MAGIC){u64 a=S->journal.played;S->journal.played=a+delta;if(S->journal.played<a)S->journal.played=~(u64)0;}
 FN(0x0202CDBC,void (*)(void *,u32))(igt,delta);
}
/* The durable sector lease authorizes repair of our torn record payloads.
 * A future journal header still blocks the downgrade, even with a v1 lease. */
static int sector_owner(u32 sector,int claim){
 u8 marker[32],expected[32],buf[32];u32 off,i;int tail=0;
 training_owner_encode(expected);
 if(!READ(sector+0x400,marker,32))return 0;
 if(training_owner_valid(marker))return 1;
 if(!claim)return 0;
 /* A torn first lease is resumable only when it is an exact prefix followed
  * by erased bytes and EVERY other byte in this previously unused sector is
  * erased. Foreign marker/sector bytes never authorize a write. */
 for(i=0;i<32;i++){if(marker[i]!=expected[i])tail=1;if(tail&&marker[i]!=255)return 0;}
 for(off=0;off<4096;off+=32){if(off==0x400)continue;if(!READ(sector+off,buf,32))return 0;for(i=0;i<32;i++)if(buf[i]!=255)return 0;}
 if(claim==2)return 1;
 return WRITE(sector+0x400,expected,32)&&READ(sector+0x400,marker,32)&&training_owner_valid(marker);
}
/* Read-only admission check. Neither alternating bank may trap a newly paid
 * transaction behind unknown bytes at its next native save. */
static int storage_ready(void){u32 sector,i,record[113];
 /* Reuse one word-aligned buffer for the 452-byte Bag and 256-byte training
  * records. Admission must agree with both writers in both alternating banks. */
 for(sector=0x30000;sector<=0x70000;sector+=0x40000)
  for(i=0;i<2;i++)if(!READ(sector+i*0x200,record,452)||!training_bag_claimable((const u8 *)record))return 0;
 for(sector=0x31000;sector<=0x71000;sector+=0x40000){
  if(!sector_owner(sector,2))return 0;
  for(i=0;i<2;i++)if(!READ(sector+i*0x200,record,256)||training_record_future((const u8 *)record))return 0;
 }return 1;
}
static int verify_record(u32 address){u8 buf[32];u32 i,j;for(i=0;i<256;i+=32){if(!READ(address+i,buf,32))return 0;for(j=0;j<32;j++)if(buf[j]!=S->record[i+j])return 0;}return 1;}
int training_native_save(void *,void *);
/* Called by the old Bag wrapper in place of its native-prologue trampoline.
 * At phase zero there is no flash operation pending. Failure3 is cleaned up by
 * Save_WriteFileAsync / Save_WriteManFinish, including counter/sleep rollback. */
ENTRY int training_save(void *save,void *manager){
 u32 sector,i,good=0;u16 crc;
 ensure(save);
 if(!R32(manager,0x14)&&!R32(manager,8)&&(S->enabled||S->shiny_admitted||S->record_status==SGP_TRAIN_VALID)){
  /* The Bag wrapper has reconciled its mirror and completed both writes. */
  if(R32((void *)0x023DD700,0)!=0x43415042u||R32((void *)0x023DD700,CFG[1])!=1)return 3;
  if(!S->writable)return 3;
  sector=0x31000+(R16(save,0x2330A)?0:0x40000);
  if(!sector_owner(sector,1))return 3;
  for(i=0;i<2;i++)if(!READ(sector+i*0x200,S->record,256)||training_record_future(S->record))return 3;
  advance_all();S->journal.generation=R32(save,0x23010);
  crc=CRC((u8 *)save+0x10+R32(save,0x232B8),R32(save,0x232BC)-16);S->journal.main_crc=crc;
  if(sgp_train_encode(&S->journal,S->record)!=SGP_TRAIN_OK)return 3;
  for(i=0;i<2;i++)if(WRITE(sector+i*0x200,S->record,256)&&verify_record(sector+i*0x200))good++;
  /* A single matching copy recovers the new bank, but both are required before
   * committing native data: conservative core ownership rejects torn siblings. */
  if(good!=2)return 3;
 }
 return training_native_save(save,manager);
}
__attribute__((naked,used)) int training_native_save(void *a __attribute__((unused)),void *b __attribute__((unused))){
 __asm__ volatile("push {r3,r4,r5,lr}\n adds r4,r1,#0\n adds r5,r0,#0\n ldr r0,[r4,#0x14]\n ldr r3,=0x02027C21\n bx r3\n .ltorg\n");
}
ENTRY void *training_items(u32 heap){return FN(0x0200757C,void *(*)(u32,u32,u32,u32,u32))(17,0,heap,0,516*36);}
ENTRY int training_ev_scalar(int value,int others,int delta){
 int next=value,cap=policy()==SGP_TRAIN_LEGACY?100:252,total=policy()==SGP_TRAIN_UNLIMITED?1512:510,room;
 if(value<0||value>255||others<0)return -1;
 if(delta<0)next=delta<=-value?0:value+delta;
 else if(delta>0&&value<cap&&others<total-value){room=cap-value;if(room>total-value-others)room=total-value-others;next+=delta<room?delta:room;}
 return next==value?-1:next;
}
int training_original_canuse(void *,u16,int,u32);
ENTRY int training_canuse(void *mon,u16 item,int move,u32 heap){
 u32 i,total=0,value=0,stat=255;
 if(item>=45&&item<=49)stat=item-45;else if(item==52)stat=5;
 if(stat<6){for(i=0;i<6;i++){u32 v=GET(mon,13+i,0);total+=v;if(i==stat)value=v;}if(!stat&&GET(mon,5,0)==292)return 0;return training_ev_scalar(value,total-value,10)>=0;}
 return training_original_canuse(mon,item,move,heap);
}
__attribute__((naked,used)) int training_original_canuse(void *a __attribute__((unused)),u16 b __attribute__((unused)),int c __attribute__((unused)),u32 d __attribute__((unused))){
 __asm__ volatile("push {r3,r4,r5,r6,r7,lr}\n sub sp,#24\n str r1,[sp,#4]\n adds r6,r0,#0\n ldr r4,=0x0208FDA5\n bx r4\n .ltorg\n");
}
ENTRY void training_battle(void *party,int slot,u32 species,u32 form){
 void *personal=FN(0x0206FA6C,void *(*)(u32,u32,u32))(species,form,5),*mon=MON(party,slot);
 u16 item=GET(mon,6,0);u32 effect=ATTR(item,1,5),param=ATTR(item,2,5),i;
 u8 evs[6],after[6];int virus=FN(0x020719F8,int (*)(void *,u8))(party,(u8)(1u<<slot));
 for(i=0;i<6;i++)evs[i]=GET(mon,13+i,0);
 for(i=0;i<6;i++){
  int gain=FN(0x0206FAA8,int (*)(void *,u32))(personal,10+i);
  u32 power=i==0?122:(i==3?121:(i<3?116+i:115+i));
  if(effect==power)gain+=param;if(virus)gain*=2;if(effect==50)gain*=2;
  if(sgp_train_ev_delta(evs,policy(),i,gain,0,after)==SGP_TRAIN_OK){evs[i]=after[i];SET(mon,13+i,&evs[i]);}
 }
 FN(0x0206FBB0,void (*)(void *))(personal);
}
static int charge(void *save,u32 currency,u32 amount){
 void *profile;
 if(currency<2)return TAKE(BAG(save),(u16)(113+currency),(u16)amount,4);
 profile=PROFILE(save);if(MONEY(profile)<amount)return 0;SUBMONEY(profile,amount);return 1;
}
static int mon_snapshot(void *mon,sgp_training_request *r,u8 kind){
 u32 clone[59],i,species;copy_bytes(clone,mon,236);species=GET(clone,5,0);
 if(!species||species>493||GET(clone,3,0))return SGP_TRAIN_INVALID;
 if(GET(clone,76,0))return SGP_TRAIN_EGG;
 clear_bytes(r,sizeof(*r));r->personality=GET(clone,0,0);r->ot=GET(clone,7,0);r->species=species;r->kind=kind;r->policy=policy();
 for(i=0;i<6;i++)r->target[i]=r->expected[i]=GET(clone,(kind?13:70)+i,0);return 0;
}
static int storage_mon_fits(void *box,u8 mode){u32 clone[34],i,species;u8 evs[6];if(sgp_train_is_zero(box,136))return 1;copy_bytes(clone,box,136);if(BOX(clone,3,0))return 0;species=BOX(clone,5,0);if(!species)return 1;if(species>493||BOX(clone,3,0))return 0;for(i=0;i<6;i++)evs[i]=BOX(clone,13+i,0);return sgp_train_mode_fits(evs,mode);}
static int storage_fits(void *save,u8 mode){
 void *party=PARTY(save),*pc=ARRAY(save,41),*dc=ARRAY(save,7),*walker=ARRAY(save,39),*migrated=ARRAY(save,28);u32 i,j;
 /* Outstanding external transfers cannot establish a complete owned census. */
 {u32 clone[34];copy_bytes(clone,(u8 *)walker+4,136);if(!sgp_train_is_zero(clone,136)&&(BOX(clone,3,0)||BOX(clone,5,0)))return 0;}
 for(i=0;i<6;i++)if(!storage_mon_fits((u8 *)migrated+i*236,mode))return 0;
 for(i=0;i<COUNT(party);i++)if(!storage_mon_fits(MON(party,i),mode))return 0;
 for(i=0;i<18;i++)for(j=0;j<30;j++)if(!storage_mon_fits(FN(0x02074058,void *(*)(void *,u32,u32))(pc,i,j),mode))return 0;
 for(i=0;i<2;i++){if(!storage_mon_fits((u8 *)dc+i*236,mode))return 0;if(S->journal.jobs[i].active&&(S->journal.jobs[i].kinds&2)&&!sgp_train_mode_fits(S->journal.jobs[i].target_evs,mode))return 0;}
 return 1;
}
static void rewards(void *fs,int historical){
 void *profile=PROFILE(S->save),*stats=ARRAY(S->save,16);u32 i,league=FN(0x0202D18C,u32 (*)(void *,int))(stats,74);
 for(i=0;i<16;i++)if(FN(0x02028F98,int (*)(void *,int))(profile,i))sgp_train_queue_reward(&S->journal,i,i<8?2:3,(i==7||i==15)?1:0,S->journal.league_seen);
 if(league&&!(S->journal.claims&(1u<<16)))if(sgp_train_queue_reward(&S->journal,16,4,2,historical?league:1)!=SGP_TRAIN_OK)return;
 while(league>S->journal.league_seen)if(sgp_train_queue_reward(&S->journal,255,4,1,S->journal.league_seen+1)!=SGP_TRAIN_OK)break;
 if(VALUE(fs,0x4131))sgp_train_queue_reward(&S->journal,17,0,3,S->journal.league_seen);
}
/* Field owner supplies a live FieldSystem after proving its lifecycle. These
 * functions are the only shiny access to training-owned persistence. The first
 * admission reads both banks; it never writes flash or changes EV policy. */
ENTRY void training_shiny_bind(void *save,u32 fresh){
 if(fresh)load_training(save,0);else ensure(save);
}
ENTRY int training_shiny_access(void *fs,u8 data[16],u32 write){
 void *save;
 _Static_assert(sizeof(sgp_train_journal)-__builtin_offsetof(sgp_train_journal,shiny_rng)==16,"shiny logical layout");
 if(!fs||!data||write>1)return 0;
 if(write&&(get16(data+4)>493||data[6]>40||data[7]>1||data[8]>1||
    (!data[8]&&get32(data))||((!get16(data+4)||!data[7])&&data[6])||
    !sgp_train_is_zero(data+9,7)))return 0;
 save=PTR(fs,12);if(!save)return 0;ensure(save);
 if(!S->writable)return 0;
 if(!S->shiny_admitted){if(!storage_ready())return 0;S->shiny_admitted=1;}
 if(!S->enabled)S->journal.flags=SGP_TRAIN_SHINY_ONLY;
 if(write)copy_bytes(&S->journal.shiny_rng,data,16);
 else copy_bytes(data,&S->journal.shiny_rng,16);
 return 1;
}
static int collect(void *fs){u32 delivered=0;void *bag=BAG(S->save);rewards(fs,0);
 while(S->journal.pending_silver&&ADD(bag,113,1,4)){sgp_train_reward_delivered(&S->journal,1,0);delivered++;}
 while(S->journal.pending_gold&&ADD(bag,114,1,4)){sgp_train_reward_delivered(&S->journal,0,1);delivered++;}
 return delivered?SGP_TRAIN_OK:SGP_TRAIN_NO_CHANGE;
}
static int purchase(u32 gold){void *p=PROFILE(S->save),*bag=BAG(S->save);u32 price=gold?50000:10000;
 if(gold>1||(!gold&&!FN(0x02028FF0,u32 (*)(void *))(p))||(gold&&!FN(0x0202D18C,u32 (*)(void *,int))(ARRAY(S->save,16),74)))return SGP_TRAIN_INVALID;
 if(MONEY(p)<price||!ROOM(bag,113+gold,1,4))return SGP_TRAIN_PAYMENT;
 if(!ADD(bag,113+gold,1,4))return SGP_TRAIN_PAYMENT;SUBMONEY(p,price);return 0;
}
static int job_matches(sgp_train_job *job,void *box){u32 clone[34];copy_bytes(clone,box,136);return !BOX(clone,3,0)&&sgp_train_identity(job,job->serial,BOX(clone,0,0),BOX(clone,7,0),BOX(clone,5,0));}
static int enroll(u32 slot,u32 stat,u32 target){
 u32 clone[34],i,experience,maximum;u64 now;sgp_train_job job;void *dc=ARRAY(S->save,7),*box=(u8 *)dc+236*slot;
 if(slot>1||S->journal.jobs[slot].active||S->journal.next_serial==0xffffffffu||!clock_now(S->journal.default_clock,&now))return SGP_TRAIN_BUSY;
 copy_bytes(clone,box,136);clear_bytes(&job,sizeof(job));job.species=BOX(clone,5,0);
 if(!job.species||job.species>493||BOX(clone,3,0)||BOX(clone,76,0))return SGP_TRAIN_INVALID;
 job.serial=S->journal.next_serial;job.personality=BOX(clone,0,0);job.ot=BOX(clone,7,0);job.active=1;job.clock=S->journal.default_clock;
 job.kinds=SGP_TRAIN_LEVEL;job.target_level=100;job.stat=255;job.anchor=now;job.steps_at_enrollment=R32(box,232);
 experience=BOX(clone,8,0);maximum=EXP(job.species,100);
 if(experience>maximum)experience=maximum;
 if(job.steps_at_enrollment>maximum-experience)experience=maximum;else experience+=job.steps_at_enrollment;
 SETBOX(clone,8,&experience);job.baseline_exp=experience;job.start_level=LEVEL(clone);
 for(i=0;i<6;i++)job.baseline_evs[i]=BOX(clone,13+i,0);
 if(stat<6){job.kinds|=SGP_TRAIN_EV;job.stat=stat;job.ev_period=3600;job.ev_points=32;
  for(i=0;i<6;i++)job.target_evs[i]=job.baseline_evs[i];
  if(target>252||target<job.baseline_evs[stat])return SGP_TRAIN_INVALID;job.target_evs[stat]=target;
 }else if(stat!=255)return SGP_TRAIN_INVALID;
 if(sgp_train_job_validate(&job,policy())!=SGP_TRAIN_OK)return SGP_TRAIN_INVALID;
 copy_bytes(&S->journal.jobs[slot],&job,sizeof(job));S->journal.next_serial++;return 0;
}
/* Active jobs are projected without touching the encrypted native box. The
 * existing DayCare phone calls this same growth routine, so remote growth is
 * playable through the ordinary Pokegear DayCare contact. */
ENTRY int training_growth(void *dcmon){
 u32 clone[34],exp,before,i;sgp_train_projection projection;
 if(S->magic==MAGIC&&S->enabled){void *dc=ARRAY(S->save,7);advance_all();for(i=0;i<2;i++)if(dcmon==(u8 *)dc+i*236&&S->journal.jobs[i].active&&job_matches(&S->journal.jobs[i],dcmon)&&sgp_train_project(&S->journal.jobs[i],policy(),&projection)==SGP_TRAIN_OK){copy_bytes(clone,dcmon,136);return projection.level-LEVEL(clone);}}
 copy_bytes(clone,dcmon,136);before=LEVEL(clone);exp=BOX(clone,8,0)+R32(dcmon,232);SETBOX(clone,8,&exp);return LEVEL(clone)-before;
}
u16 training_original_retrieve(void *,void *,void *,u8);
ENTRY u16 training_retrieve(void *party,void *formatter,void *daycare,u8 slot){
 u32 clone[120],exp,base,rem,ceiling,i;u16 species;sgp_train_job expected;sgp_train_projection projection;
 if(slot>1||COUNT(party)>=6)return 0;
 if(S->magic!=MAGIC||!S->enabled)return training_original_retrieve(party,formatter,daycare,slot);
 copy_bytes(&expected,&S->journal.jobs[slot],sizeof(expected));
 if(!expected.active){species=training_original_retrieve(party,formatter,daycare,slot);if(species)sgp_train_withdraw(S->journal.jobs,policy(),slot,&expected);return species;}
 if(!job_matches(&expected,(u8 *)daycare+236*slot))return 0;
 advance_all();copy_bytes(&expected,&S->journal.jobs[slot],sizeof(expected));
 if(sgp_train_project(&expected,policy(),&projection)!=SGP_TRAIN_OK)return 0;
 copy_bytes(clone,daycare,480);void *box=(u8 *)clone+236*slot;
 base=EXP(expected.species,expected.start_level);rem=expected.baseline_exp>=base?expected.baseline_exp-base:0;
 exp=EXP(expected.species,projection.level);
 if(projection.level<100){ceiling=EXP(expected.species,projection.level+1)-exp-1;if(rem>ceiling)rem=ceiling;exp+=rem;}
 SETBOX(box,8,&exp);for(i=0;i<6;i++)SETBOX(box,13+i,&projection.evs[i]);
 if(BOX(box,3,0)||BOX(box,8,0)!=exp)return 0;
 for(i=0;i<6;i++)if(BOX(box,13+i,0)!=projection.evs[i])return 0;
 R32(box,232)=0;
 /* CopyBoxPokemonToPokemon sets its current level from EXP; native retrieval
  * sees no extra level delta, preserving the deposited move set. */
 species=training_original_retrieve(party,formatter,clone,slot);
 if(species){copy_bytes(daycare,clone,480);sgp_train_withdraw(S->journal.jobs,policy(),slot,&expected);}
 return species;
}
__attribute__((naked,used)) u16 training_original_retrieve(void *a __attribute__((unused)),void *b __attribute__((unused)),void *c __attribute__((unused)),u8 d __attribute__((unused))){
 __asm__ volatile("push {r4,r5,r6,lr}\n adds r6,r2,#0\n adds r5,r0,#0\n adds r4,r1,#0\n ldr r2,=0x0206C081\n bx r2\n .ltorg\n");
}
/* Script490/F13A, width4 unchanged. Inputs 8006 op,8007 slot,8008 arg,
 * 8009 value,800A kind. Outputs800B result,800C cost;8000..8005 six stats.
 * Only script constants/native specials, never persisted map variables. */
ENTRY int training_script(void *ctx){
 u8 *pc=PTR(ctx,8);void *fs,*save,*party;u16 op,slot,arg,value,kind;int result=SGP_TRAIN_INVALID;u32 i,cost=0;
 if((pc[0]|(pc[1]<<8))!=0xF13A)return FN(0x0204EE20,int (*)(void *))(ctx);
 PTR(ctx,8)=pc+2;fs=PTR(ctx,0x80);save=PTR(fs,12);ensure(save);
 if(!S->enabled)result=SGP_TRAIN_BUSY;
 op=VALUE(fs,0x8006);slot=VALUE(fs,0x8007);arg=VALUE(fs,0x8008);value=VALUE(fs,0x8009);kind=VALUE(fs,0x800A);
 if(op==0){result=S->enabled?0:SGP_TRAIN_BUSY;*VAR(fs,0x8000)=policy();*VAR(fs,0x8001)=S->journal.default_clock;*VAR(fs,0x8002)=S->journal.pending_silver;*VAR(fs,0x8003)=S->journal.pending_gold;}
 else if(op==1&&S->writable&&arg<=2){if(!storage_ready())result=8;else if((arg==0&&policy()==0)||storage_fits(save,arg)){if(!S->enabled){S->journal.flags=0;rewards(fs,1);}S->journal.policy=arg;S->enabled=1;result=0;}else result=SGP_TRAIN_BUSY;}
 else if(S->enabled&&S->writable){
  /* Active journals still need fresh admission before a persistent service
   * mutation. Refuse before charging, and never replay a rejected preview. */
  if(op>=4&&op<=8&&!storage_ready()){if(op==4)S->preview_valid=0;result=8;}
  else if(op==2||op==3){S->preview_valid=0;party=PARTY(save);if(slot<COUNT(party)){
   result=mon_snapshot(MON(party,slot),&S->request,op==3);
   if(!result){S->request.stat=arg;S->request.value=value;S->request.iv_kind=kind;
    if(op==2){u8 cap;result=sgp_train_iv_preview(S->request.expected,kind,arg,value,0,1,S->request.target,&cap);cost=1;}
    else if(arg<6&&value<=252){S->request.target[arg]=value;result=sgp_train_ev_allocate(S->request.target,policy(),S->request.target);for(i=0;i<6;i++)if(S->request.target[i]>S->request.expected[i])cost+=(S->request.target[i]-S->request.expected[i])*100;}
    else if(arg==255){for(i=0;i<6;i++)S->request.target[i]=0;result=0;}
    else result=SGP_TRAIN_INVALID;
    if(!result){S->preview_valid=1;S->preview_slot=slot;for(i=0;i<6;i++)*VAR(fs,0x8000+i)=S->request.target[i];}
   }
  }}else if(op==4){party=PARTY(save);if(S->preview_valid&&S->preview_slot<COUNT(party)){
    sgp_training_native_api api;api.read=GET;api.write=SET;api.recalculate=CALC;api.charge=charge;
    result=sgp_training_transaction(&api,save,MON(party,S->preview_slot),&S->request,&cost);
   }S->preview_valid=0;
  }else if(op==5)result=purchase(arg);
  else if(op==6)result=collect(fs);
  else if(op==7&&arg<=1){u64 old,newnow;result=0;for(i=0;i<2;i++)if(S->journal.jobs[i].active&&(!clock_now(S->journal.jobs[i].clock,&old)||!clock_now(arg,&newnow)))result=SGP_TRAIN_BUSY;
   if(!result){for(i=0;i<2;i++)if(S->journal.jobs[i].active){clock_now(S->journal.jobs[i].clock,&old);clock_now(arg,&newnow);sgp_train_switch_clock(&S->journal.jobs[i],policy(),old,arg,newnow);}S->journal.default_clock=arg;}
  }else if(op==8)result=enroll(slot,arg,value);
  else if(op==9&&slot<2){sgp_train_projection p;sgp_train_job *j=&S->journal.jobs[slot];advance_all();result=sgp_train_project(j,policy(),&p);if(!result){*VAR(fs,0x8000)=p.level;*VAR(fs,0x8001)=j->stat;*VAR(fs,0x8002)=j->stat<6?p.evs[j->stat]:0;*VAR(fs,0x8003)=j->stat<6?j->target_evs[j->stat]:0;*VAR(fs,0x8004)=j->clock;volatile u32 seconds=p.remaining_seconds;while(seconds>=60){cost++;seconds-=60;}if(seconds)cost++;}}
  else if(op==10){S->preview_valid=0;result=0;}
  else if(op==11){party=PARTY(save);if(slot<COUNT(party)&&kind<=1){sgp_training_request request;result=mon_snapshot(MON(party,slot),&request,kind);if(!result)for(i=0;i<6;i++)*VAR(fs,0x8000+i)=request.expected[i];}}
 }
 *VAR(fs,0x800B)=result;*VAR(fs,0x800C)=cost>65535?65535:cost;return 0;
}
/* Called ONLY from DayCare Lady's existing pre-status phone message. Native
 * phone progression, egg/contact branches and message completion remain native. */
ENTRY void training_phone(void *ctx,void *messages,u8 message){
 u32 i,index=0,multiplier=1;void *format=PTR(ctx,0x50);sgp_train_projection p;
 if(S->magic==MAGIC&&S->enabled){
  advance_all();
  for(i=0;i<2;i++){
   sgp_train_job *job=&S->journal.jobs[i];u32 type=0,values[5],j;
   if(job->active&&sgp_train_project(job,policy(),&p)==SGP_TRAIN_OK){
    type=(job->kinds&SGP_TRAIN_EV)?2:1;
    values[0]=p.level;values[1]=0;values[2]=type==2?p.evs[job->stat]:0;values[3]=type==2?job->target_evs[job->stat]:0;values[4]=p.remaining_seconds;
    for(j=0;j<5;j++)if(j!=1)FN(0x0200BFCC,void (*)(void *,u32,u32,u32,u32,u32))(format,i*5+j,values[j],j==4?6:3,0,1);
    if(type==2)FN(0x0200C1D4,void (*)(void *,u32,u32))(format,i*5+1,job->stat);
   }
   index+=type*multiplier;multiplier*=3;
  }
  if(index)message=CFG[2]+index+9*S->journal.default_clock;
 }
 FN(0x021F2208,void (*)(void *,void *,u8))(ctx,messages,message);
}

/* The Cap consultant has a dedicated graphic. Keep every native sprite entry
 * and deliveryman texture untouched; this runs only during object lookup. */
ENTRY const u16 *training_sprite(u32 sprite){
 if(sprite==194)return (const u16 *)(CFG+4);
 const u16 *p=(const u16 *)0x022074A8;
 for(;*p!=65535;p+=3)if(*p==sprite)return p;
 FN(0x0202551C,void (*)(void))();return 0;
}
ENTRY void *training_sprite_category(u32 sprite){
 const u16 *p=training_sprite(sprite);
 return p?(void *)(0x02207318+((p[2]>>10)*8)):0;
}
