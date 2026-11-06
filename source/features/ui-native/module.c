#include "module.h"
typedef unsigned U;
#define MAGIC 0x32444D55u
#define BASE 0x021E5900u
#define REG ((volatile U *)0x021D0DF0u)
#define ARC ((volatile U *)0x021E3654u)
#define WORD(p) (*(volatile U *)(p))
#define IRQ ((U (*)(void))0x020D3A90u)
#define DISABLE ((U (*)(void))0x020D3A38u)
#define RESTORE ((void (*)(U))0x020D3A4Cu)
#define INITFILE ((void (*)(void *))0x020D7F98u)
#define DIRECT ((U (*)(void *,U,U,U,U))0x020D81C0u)
#define FAST ((U (*)(void *,U,U))0x020D8208u)
#define READ ((U (*)(void *,void *,U))0x020D83BCu)
#define CLOSE ((U (*)(void *))0x020D82C0u)
#define INVALIDATE ((void (*)(void *,U))0x020D285Cu)
#define CLEAR ((void (*)(void *))0x020D8764u)
#define START ((void (*)(void *))0x020D8B6Cu)
#define END ((U (*)(void *))0x020D8D50u)
#define WIFI ((void (*)(U))0x023DA3CDu)
#define P(x) UI_MODULE_P_##x
#define E(x) UI_MODULE_E_##x
_Static_assert(sizeof(UiModuleConfig)==96,"config ABI2");
_Static_assert(sizeof(UiModule)==4624,"persistent owner ABI2");
static U extent(U p,U n,U lo,U hi) {return p>=lo&&n<=hi-lo&&p<=hi-n;}
static U overlap(U p,U n,U q,U z) {return p<q+z&&q<p+n;}
static U ram(U p,U n) {return !(p&3)&&extent(p,n,0x02000000u,0x02400000u);}
static U writable(U p,U n) {return !(p&3)&&extent(p,n,0x0226EC40u,0x023C0000u);}
static U readable(U p,U n) {return ram(p,n)||(!(p&3)&&extent(p,n,0x027E0080u,0x027E3780u));}
static void copy(U *to,const volatile U *from,U n) {while(n--)*to++=*from++;}
static U equal(const U *a,const volatile U *b,U n) {while(n--)if(*a++!=*b++)return 0;return 1;}
static U location(const UiModule *m) {return writable((U)m,sizeof(*m));}
static U valid(const UiModule *m) {return location(m)&&m->magic==MAGIC&&m->self==(U)m;}
static U identity(const UiModule *m,U r,U g) {return valid(m)&&r>=1&&r<=2&&g&&m->role==r&&m->generation==g;}
static U enabled(void) {return WORD(0x04000208u)==1&&!IRQ();}
static U boot(void) {return *(volatile unsigned short *)0x027FFC40u!=2;}
static U *table(UiModule *m) {return (U *)(((U)m->table_storage+31u)&~31u);}
static U packed(const UiModule *m) {return m->config.packed&0xFFFFFFu;}
static UiModuleResult held(UiModule *m,U e) {if(!m->error)m->error=e;m->phase=P(HOLD);return UI_MODULE_HOLD;}
static U config(const UiModuleConfig *c,U r,U g) {
 U n=c->size,z=c->packed&0xFFFFFFu;
 if(c->magic!=0x314D4955u||c->abi!=2||r<1||r>2||c->role!=r||!g||c->generation!=g||
 c->overlay_id!=54||c->file_id!=54||c->base!=BASE||n<0x280u||n>0x10000u||(n&3)||c->bss||
 (c->packed>>24)!=1||z<8||z>n||(z&3)||c->sinit_start!=c->sinit_end||
 (c->sinit_start&3)||c->sinit_start<BASE||c->sinit_start>BASE+n||c->y9_bytes!=4128||c->y9_entries!=129||
 c->rom_bytes<0x200||c->rom_bytes>0x20000000u||!extent(c->y9_rom_offset,4128,0x200,c->rom_bytes)||
 (c->y9_rom_offset&3)||!extent(c->file_top,z,0x200,c->rom_bytes)||c->file_bottom!=c->file_top+z||
 overlap(c->file_top,z,c->y9_rom_offset,4128))return 0;
 const U *p=&c->init_offset;
 for(U i=0;i<3;++i)if(!(p[i]&1)||p[i]>n-1)return 0;
 return p[0]!=p[1]&&p[0]!=p[2]&&p[1]!=p[2];
}
static U separated(const UiModule *m,const UiModuleConfig *c) {
 U n=(c->size+31)&~31u;
 return !overlap((U)m,sizeof(*m),(U)c,sizeof(*c))&&!overlap((U)m,sizeof(*m),BASE,n)&&!overlap((U)c,sizeof(*c),BASE,n);
}
/* Source allocations are immutable by caller contract; the changing native
 * command/queue tuple is sampled separately under a short IRQ mask. */
static U source(UiModule *m,U capture) {
 U fat=ARC[11],fnt=ARC[13],t=WORD(0x021E3644u),n=WORD(0x021E3648u);
 if(WORD(0x021E3638u)!=1||ARC[0]!=0x006D6F72u||(ARC[7]&7)!=7||ARC[10]||
 ARC[12]!=4104||ARC[14]!=2902||!ram(ARC[17],7040)||fat!=((ARC[17]+31)&~31u)||fnt!=fat+4104||
 ARC[18]!=0x020D84C4u||ARC[19]!=0x020D850Cu||ARC[20]!=0x020D7484u||ARC[21]!=0x020D8514u||ARC[22]!=0x602)return 0;
 if(t?(!ram(t,4128)||n!=4128):n)return 0;
 U roots[2]={ARC[17],t},lens[2]={7040,t?4128u:0u};
 for(U i=0;i<2;++i)if(lens[i]&&(overlap(roots[i],lens[i],(U)m,sizeof(*m))||
 overlap(roots[i],lens[i],m->config_address,96)||overlap(roots[i],lens[i],BASE,(m->config.size+31)&~31u)))return 0;
 if(t&&overlap(t,4128,roots[0],7040))return 0;
 U v[8]={t,n,WORD(0x027FFE50u),WORD(0x027FFE54u),WORD(fat+54*8),WORD(fat+54*8+4),WORD(0x021E3640u),WORD(0x021E363Cu)};
 if(v[2]!=m->config.y9_rom_offset||v[3]!=4128||v[4]!=m->config.file_top||v[5]!=m->config.file_bottom)return 0;
 if(capture){copy(m->archive,&ARC[10],13);copy(m->source,v,8);}
 else if(!equal(m->archive,&ARC[10],13)||!equal(m->source,v,8))return 0;
 return 1;
}
typedef struct {U f[18],a[10];} Snapshot;
static void snapshot(UiModule *m,Snapshot *s) {
 U mask=DISABLE();copy(s->f,(volatile U *)m->file,18);copy(s->a,ARC,10);RESTORE(mask);
}
/* 0 quiet, 1 the owned pending read, 2 transient archive suspension/unload,
 * 3 unknown ownership. Only state 0 may issue a new synchronous command. */
static U shape(UiModule *m,const Snapshot *s) {
 const U *f=s->f,*a=s->a;
 if(m->canary[0]!=0xA35C691Eu||m->canary[1]!=0x5CA396E1u||a[3]||a[4]||a[5]||a[6]||a[8]||f[6]||f[7])return 3;
 if(f[2]&&f[2]!=(U)ARC)return 3;
 if(f[3]&0x4Fu) {
  return m->file_bound&&m->file_opened&&f[2]==(U)ARC&&f[0]==(U)ARC+32&&!f[1]&&f[3]==0x59&&
   f[4]==0&&f[5]==2&&a[7]==0x117&&a[9]==(U)m->file ? 1:3;
 }
 if(f[0]||f[1]||a[9]||(f[3]&~16u)||((a[7]&~0x88u)!=7))return 3;
 if(m->file_bound?(f[2]!=(U)ARC):f[2])return 3;
 return a[7]==7?0:2;
}
static U current(UiModule *m) {
 const UiModuleConfig *c=(const UiModuleConfig *)m->config_address;
 if(!readable((U)c,96)||!equal((const U *)&m->config,(const U *)c,24)||!config(c,m->role,m->generation)||
 !separated(m,c)||!source(m,0)||!equal(m->registry,REG,16))return 0;
 if(m->y9_verified&&m->source[0]) {
  U *t=table(m);const U *cached=(const U *)m->source[0];
  if(!equal(t+54*8,cached+54*8,8))return 0;
  for(U i=0;i<8;++i)if(m->registry[2*i+1]&&!equal(t+m->registry[2*i]*8,cached+m->registry[2*i]*8,8))return 0;
 }
 return 1;
}
static UiModuleResult abort_load(UiModule *m,U error) {
 if(!m->error)m->error=error;
 m->phase=m->file_bound?P(ABORT_DRAIN):(m->started?P(ABORT_END):(m->registry_owned?P(ABORT_UNRESERVE):P(FAILED)));
 return m->phase==P(FAILED)?UI_MODULE_FAILED:UI_MODULE_MORE;
}
static U metadata(UiModule *m) {
 U *t=table(m),*own=t+54*8;const UiModuleConfig *c=&m->config;
 U expect[8]={54,BASE,c->size,0,c->sinit_start,c->sinit_end,54,c->packed};
 if(!equal(expect,own,8))return 0;
 for(U i=0;i<129;++i)if(t[i*8]!=i||t[i*8+6]>=513)return 0;
 U seen[8],count=0,free=8;
 for(U i=0;i<8;++i) {
  U id=m->registry[2*i],active=m->registry[2*i+1];
  if(active>1)return 0;
  if(!active){if(free==8)free=i;continue;}
  if(id>=129||id==54)return 0;
  for(U j=0;j<count;++j)if(seen[j]==id)return 0;
  seen[count++]=id;U *e=t+id*8;
  if(!e[2]||!ram(e[1],e[2])||e[3]>0x02400000u-e[1]-e[2])return 0;
  U lo=e[1]&~31u,hi=(e[1]+e[2]+e[3]+31)&~31u;
  if(overlap(BASE,(c->size+31)&~31u,lo,hi-lo))return 0;
 }
 m->slot=free;return free<8;
}
static U transaction(UiModule *m,U reserve) {
 U mask=DISABLE(),ok=equal(m->registry,REG,16);
 if(ok){U i=2*m->slot;if(reserve){REG[i]=54;m->registry[i]=54;}REG[i+1]=reserve;m->registry[i+1]=reserve;}
 RESTORE(mask);if(ok)m->registry_owned=reserve;return ok;
}
static void hash_start(UiModule *m) {m->crc_cursor=0;m->crc_acc=~0u;}
/* Same reflected CRC32 as the resource reader, two nibbles per byte.
 * Explicit executable-section literal: no writable cache or external data. */
__asm__(".pushsection .text,\"ax\",%progbits\n.balign 4\n.local m_crc_table\n"
        ".type m_crc_table,%object\nm_crc_table:\n.word 0x00000000,0x1DB71064,0x3B6E20C8,0x26D930AC,0x76DC4190,0x6B6B51F4,0x4DB26158,0x5005713C,0xEDB88320,0xF00F9344,0xD6D6A3E8,0xCB61B38C,0x9B64C2B0,0x86D3D2D4,0xA00AE278,0xBDBDF21C\n"
        ".size m_crc_table,64\n.popsection\n");
extern const U m_crc_table[16];
static U hash_step(UiModule *m,const unsigned char *p,U n,U budget,U compare) {
 U end=m->crc_cursor+budget;if(end>n)end=n;U c=m->crc_acc;
 for(U i=m->crc_cursor;i<end;++i) {
  U b=p[i];if(compare&&b!=((const volatile unsigned char *)m->source[0])[i])return 2;
  c^=b;c=(c>>4)^m_crc_table[c&15];c=(c>>4)^m_crc_table[c&15];
 }
 m->crc_cursor=end;m->crc_acc=c;return end==n;
}
static U footer(UiModule *m) {
 U n=packed(m),a=WORD(BASE+n-8),increase=WORD(BASE+n-4),header=a>>24,encoded=a&0xFFFFFFu;
 return header>=8&&header<=n&&encoded>=header&&encoded<=n&&increase==m->config.size-n;
}
static U props(UiModule *m,const U *f,U done) {
 U id=m->read_kind?54:~0u;
 return f[8]==id&&f[9]==m->read_start&&f[10]==m->read_end&&
 f[11]==m->read_start+(done?m->read_size:0);
}
unsigned ui_module_init(UiModule *m) {
 if(!location(m))return 0;const U *p=(const U *)m;
 for(U i=0;i<sizeof(*m)/4;++i)if(p[i])return 0;
 m->magic=MAGIC;m->self=(U)m;m->canary[0]=0xA35C691Eu;m->canary[1]=0x5CA396E1u;return 1;
}
UiModuleResult ui_module_begin(UiModule *m,const UiModuleConfig *c,U r,U g) {
 if(!valid(m)||(m->phase!=P(ZERO)&&m->phase!=P(RELEASED))||!readable((U)c,96)||!config(c,r,g)||
 !separated(m,c)||(m->phase==P(RELEASED)&&g<=m->generation))return UI_MODULE_REFUSED;
 if(!enabled())return UI_MODULE_MORE;
 if(!boot())return UI_MODULE_REFUSED;
 /* Previous terminal state has no native references. Preserve self/canaries. */
 U *p=&m->phase;for(U i=0;i<22;++i)p[i]=0;
 m->role=r;m->generation=g;m->config_address=(U)c;copy((U *)&m->config,(const U *)c,24);
 copy(m->registry,REG,16);
 if(!source(m,1))return abort_load(m,E(SOURCE));
 m->phase=P(META_OPEN);return UI_MODULE_MORE;
}
UiModuleResult ui_module_step(UiModule *m,U r,U g,U budget) {
 if(!identity(m,r,g)||!budget||budget>4096)return UI_MODULE_REFUSED;
 U phase=m->phase;
 if(phase==P(HOLD))return UI_MODULE_HOLD;
 if(phase==P(FAILED))return UI_MODULE_FAILED;
 if(phase==P(RELEASED))return UI_MODULE_RELEASED;
 if(phase==P(ZERO))return UI_MODULE_REFUSED;
 if(!enabled())return UI_MODULE_MORE;
 if(!current(m))return held(m,E(SOURCE));
 Snapshot s;snapshot(m,&s);U sh=shape(m,&s);
 if(sh==3)return held(m,E(OWNERSHIP));
 if(phase==P(READY))return sh==0&&!m->file_bound?UI_MODULE_READY:held(m,E(OWNERSHIP));
 if(m->cancelled&&phase<P(ABORT_DRAIN))return abort_load(m,E(CANCELLED));
 if(sh==2)return UI_MODULE_MORE;
 switch(phase) {
 case P(META_OPEN):case P(IMAGE_OPEN): {
  if(sh||m->file_bound)return held(m,E(OWNERSHIP));
  m->read_kind=phase==P(IMAGE_OPEN);m->read_size=m->read_kind?packed(m):4128;
  m->read_start=m->read_kind?m->config.file_top:m->config.y9_rom_offset;m->read_end=m->read_start+m->read_size;
  INITFILE(m->file);m->file_bound=1;
  U ok=m->read_kind?FAST(m->file,(U)ARC,54):DIRECT(m->file,(U)ARC,m->read_start,m->read_end,~0u);
  snapshot(m,&s);if(!s.f[2])m->file_bound=0;
  if(shape(m,&s)>2)return held(m,E(OWNERSHIP));
  if(!ok)return abort_load(m,E(OPEN));
  if(!m->file_bound||s.f[3]!=16||s.f[5]||!props(m,s.f,0))return held(m,E(OWNERSHIP));
  m->file_opened=1;m->phase=m->read_kind?P(IMAGE_CLEAR):P(META_INVALIDATE);break;
 }
 case P(META_INVALIDATE):case P(IMAGE_CLEAR):
  if(sh||!m->file_opened)return held(m,E(OWNERSHIP));
  if(phase==P(META_INVALIDATE)){INVALIDATE(table(m),4128);m->phase=P(META_READ);}
  else {copy(m->info,table(m)+54*8,8);m->info[8]=0;m->info[9]=s.f[9];m->info[10]=s.f[10]-s.f[9];CLEAR(m->info);m->phase=P(IMAGE_READ);}break;
 case P(META_READ):case P(IMAGE_READ):
  if(sh||!m->file_opened||!props(m,s.f,0))return held(m,E(OWNERSHIP));
  m->read_return=READ(m->file,m->read_kind?(void *)BASE:table(m),m->read_size);
  m->phase=m->read_kind?P(IMAGE_WAIT):P(META_WAIT);break;
 case P(META_WAIT):case P(IMAGE_WAIT):
  if(!m->file_bound||!m->file_opened)return held(m,E(OWNERSHIP));
  if(sh==1)break;
  if(s.f[4]||s.f[5]||m->read_return!=m->read_size||!props(m,s.f,1)||
   s.f[12]!=(m->read_kind?BASE:(U)table(m))||s.f[13]!=m->read_size||s.f[14]!=m->read_size)return abort_load(m,E(READ));
  m->phase=m->read_kind?P(IMAGE_CLOSE):P(META_CLOSE);break;
 case P(META_CLOSE):case P(IMAGE_CLOSE):case P(ABORT_CLOSE): {
  if(sh||!m->file_bound)return held(m,E(OWNERSHIP));
  if(m->close_attempts!=~0u)++m->close_attempts;
  U ok=CLOSE(m->file);snapshot(m,&s);
  if(!ok){if(shape(m,&s)>2)return held(m,E(OWNERSHIP));break;}
  m->file_bound=0;
  if(shape(m,&s)>2||s.f[2]||s.f[3]||s.f[4]!=14||s.f[5])return held(m,E(OWNERSHIP));
  m->file_opened=0;
  if(phase==P(ABORT_CLOSE))return abort_load(m,m->error);
  hash_start(m);m->phase=m->read_kind?P(PACKED_VERIFY):P(META_VERIFY);break;
 }
 case P(META_VERIFY): {
  U result=hash_step(m,(const unsigned char *)table(m),4128,budget,m->source[0]!=0);
  if(result==2)return abort_load(m,E(METADATA));
  if(result){if((m->crc_acc^~0u)!=m->config.y9_crc||!metadata(m))return abort_load(m,E(METADATA));m->y9_verified=1;m->phase=P(RESERVE);}break;
 }
 case P(RESERVE):
  if(sh||m->file_bound||!transaction(m,1))return held(m,E(REGISTRY));m->phase=P(IMAGE_OPEN);break;
 case P(PACKED_VERIFY):
  if(hash_step(m,(const unsigned char *)BASE,packed(m),budget,0)) {
   if((m->crc_acc^~0u)!=m->config.packed_crc||!footer(m))return abort_load(m,E(PACKED));
   m->phase=P(START);
  }break;
 case P(START):
  if(sh||m->file_bound)return held(m,E(OWNERSHIP));
  if(!boot())return abort_load(m,E(BOOT));
  START(m->info);m->started=1;hash_start(m);m->phase=P(DECODED_VERIFY);break;
 case P(DECODED_VERIFY):
  if(hash_step(m,(const unsigned char *)BASE,m->config.size,budget,0)) {
   if((m->crc_acc^~0u)!=m->config.crc)return abort_load(m,E(DECODED));
   m->image_verified=1;m->phase=P(WIFI);
  }break;
 case P(WIFI):
  if(m->wifi_done||!m->image_verified)return held(m,E(OWNERSHIP));
  WIFI(54);m->wifi_done=1;m->phase=P(READY);return UI_MODULE_READY;
 case P(ABORT_DRAIN):
  if(sh==1)break;
  m->phase=P(ABORT_CLOSE);break;
 case P(ABORT_END):case P(RELEASE_END):
  if(sh||m->file_bound||!m->started)return held(m,E(OWNERSHIP));
  if(!END(m->info))return held(m,E(OWNERSHIP));m->started=0;
  m->phase=phase==P(ABORT_END)?P(ABORT_UNRESERVE):P(RELEASE_UNRESERVE);break;
 case P(ABORT_UNRESERVE):case P(RELEASE_UNRESERVE):
  if(sh||m->file_bound||m->started||!m->registry_owned||!transaction(m,0))return held(m,E(REGISTRY));
  m->phase=phase==P(ABORT_UNRESERVE)?P(FAILED):P(RELEASED);
  return m->phase==P(FAILED)?UI_MODULE_FAILED:UI_MODULE_RELEASED;
 default:return held(m,E(OWNERSHIP));
 }
 return UI_MODULE_MORE;
}
UiModuleResult ui_module_pump(UiModule *m,U r,U g,U budget,U cap) {
 if(!cap||cap>16)return UI_MODULE_REFUSED;
 for(U n=0;n<cap;++n) {
  /* Validate before reading private fields; step repeats all guards. */
  if(!identity(m,r,g)||!budget||budget>4096)return UI_MODULE_REFUSED;
  U phase=m->phase,cursor=m->crc_cursor;
  UiModuleResult result=ui_module_step(m,r,g,budget);
  if(result!=UI_MODULE_MORE)return result;
  if(m->cancelled || (m->phase==phase&&m->crc_cursor==cursor))return result;
  if(phase==P(RESERVE)||phase==P(START)||phase==P(WIFI)||
     m->phase==P(META_WAIT)||m->phase==P(IMAGE_WAIT)||m->phase==P(RESERVE)||
     m->phase==P(START)||m->phase==P(WIFI)||m->phase>=P(ABORT_DRAIN))return result;
 }
 return UI_MODULE_MORE;
}
UiModuleResult ui_module_cancel(UiModule *m,U r,U g) {
 if(!identity(m,r,g)||m->phase==P(ZERO)||m->phase>=P(READY))return UI_MODULE_REFUSED;
 if(!enabled())return UI_MODULE_MORE;
 m->cancelled=1;return UI_MODULE_MORE;
}
unsigned ui_module_check(UiModule *m,U r,U g,U selector) {
 if(!identity(m,r,g)||m->phase!=P(READY)||selector>2||!enabled())return 0;
 if(ui_module_step(m,r,g,1)!=UI_MODULE_READY)return 0;
 return BASE+(&m->config.init_offset)[selector];
}
UiModuleResult ui_module_release(UiModule *m,U r,U g) {
 if(!identity(m,r,g))return UI_MODULE_REFUSED;
 if(m->phase==P(HOLD))return UI_MODULE_HOLD;
 if(m->phase!=P(READY)&&m->phase!=P(FAILED))return UI_MODULE_REFUSED;
 if(!enabled())return UI_MODULE_MORE;
 if(m->phase==P(FAILED)){m->phase=P(RELEASED);return UI_MODULE_RELEASED;}
 if(ui_module_step(m,r,g,1)!=UI_MODULE_READY)return UI_MODULE_HOLD;
 m->phase=P(RELEASE_END);return UI_MODULE_MORE;
}
