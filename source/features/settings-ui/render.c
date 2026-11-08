#include "render.h"
/* All arithmetic is bounded integer arithmetic; division is deliberately absent. */
static unsigned sr_ram(const void *p,unsigned n,unsigned align) {
 unsigned a=(unsigned)p;
 return n && !(a&(align-1)) &&
 ((a>=0x02000000u && a<=0x02400000u && n<=0x02400000u-a) ||
 (a>=0x027e0000u && a<=0x027e4000u && n<=0x027e4000u-a));
}
static unsigned sr_overlap(const void *a,unsigned an,const void *b,unsigned bn) {
 unsigned x=(unsigned)a,y=(unsigned)b;
 return x<y+bn && y<x+an;
}
static unsigned sr16(const unsigned char *p) { return p[0]|((unsigned)p[1]<<8); }
static unsigned sr32(const unsigned char *p) { return sr16(p)|(sr16(p+2)<<16); }
static void sr_zero(void *p,unsigned n) { unsigned char *q=p;while(n--)*q++=0; }
static void sr_copy(void *p,const void *q,unsigned n) {
 unsigned char *a=p;const unsigned char *b=q;while(n--)*a++=*b++;
}
static unsigned sr_catalog(const SettingsRenderCatalog *c) {
 return sr_ram(c,sizeof(*c),4) && c->identity && c->bytes<=131072 &&
 sr_ram(c->root,c->bytes,4) && c->count && c->count<=SGP_UI_GUIDE_PAGING+493 &&
 c->directory<=c->bytes && c->count*8<=c->bytes-c->directory &&
 c->width_count==509 && sr_ram(c->widths,509,1);
}
static const unsigned char *sr_lookup(const SettingsRenderCatalog *c,unsigned id,unsigned *units) {
 unsigned lo=0,hi=c->count,m,key,off,n;
 const unsigned char *root=c->root,*d;
 if (!((id>=1 && id<=SGP_UI_CONTEXT_SEARCH)||(id>=4097 && id<=4589)))return 0;
 while(lo<hi) { m=(lo+hi)>>1;d=root+c->directory+m*8;key=sr16(d);
  if(key<id)lo=m+1;else hi=m;
 }
 if(lo>=c->count)return 0;
 d=root+c->directory+lo*8;if(sr16(d)!=id)return 0;
 n=sr16(d+2);off=sr32(d+4);
 if(n<2 || n>904 || (off&1) || off>c->bytes || n*2>c->bytes-off)return 0;
 *units=n;return root+off;
}
static unsigned sr_measure(const SettingsRenderCatalog *c,unsigned id,unsigned maxlines,
 unsigned *units,unsigned *wide,unsigned *lines) {
 unsigned i,g,w=0,best=0,line=1,len=0,n;const unsigned char *p=sr_lookup(c,id,&n);
 if(!p)return 0;
 for(i=0;i<n;i++) { g=sr16(p+2*i);
  if(g==65535) {if(i!=n-1 || !len)return 0;break;}
  if(g==0xe000) {if(!len || ++line>maxlines)return 0;if(w>best)best=w;w=0;len=0;continue;}
  if(!g || g>509 || !c->widths[g-1] || c->widths[g-1]>16 || ++len>128)return 0;
  w+=c->widths[g-1];
 }
 if(i==n || line>maxlines)return 0;
 if(w>best)best=w;*units=n;*wide=best;*lines=line;return 1;
}
static unsigned sr_alphabet(const SettingsRenderCatalog *c,unsigned short *a) {
 unsigned n,i,j;const unsigned char *p=sr_lookup(c,SGP_UI_FORMAT_POOL,&n);
 if(!p || n<15 || n>129 || sr16(p+2*(n-1))!=65535)return 0;
 for(i=14;i<n-1;i++){unsigned g=sr16(p+2*i);if(!g || g>509 || !c->widths[g-1] || c->widths[g-1]>16)return 0;}
 for(i=0;i<14;i++) {a[i]=(unsigned short)sr16(p+2*i);
  if(!a[i] || a[i]>509 || !c->widths[a[i]-1] || c->widths[a[i]-1]>16)return 0;
  for(j=0;j<i;j++)if(a[i]==a[j])return 0;
 }return 1;
}
static unsigned sr_decimal(unsigned value,unsigned short *out,const unsigned short *a) {
 unsigned power=1000000000u,n=0,digit,started=0;
 for(;;) {digit=0;while(value>=power){value-=power;digit++;}
  if(digit || started || power==1){out[n++]=a[digit];started=1;}
  if(power==1)break;
  /* exact /10 for these ten powers, bounded 32-step bit quotient */
  {unsigned q=0,r=0,i;for(i=32;i;i--){r=(r<<1)|((power>>(i-1))&1);q<<=1;if(r>=10){r-=10;q++;}}power=q;}
 }return n;
}
static unsigned sr_digits(unsigned a,unsigned b,unsigned fraction,const unsigned short *alphabet,unsigned short *out) {
 unsigned n=sr_decimal(a,out,alphabet);if(fraction){out[n++]=alphabet[10];n+=sr_decimal(b,out+n,alphabet);}out[n++]=65535;return n;
}
static SettingsDrawOp *sr_op(SettingsRenderPlan *p,unsigned kind,unsigned id,unsigned x,unsigned y,
 unsigned w,unsigned h,unsigned flags,unsigned row) {
 SettingsDrawOp *o;
 if(p->count>=SETTINGS_RENDER_OPS || !w || !h || x+w>240 || y+h>176)return 0;
 o=&p->ops[p->count++];o->kind=kind;o->id=id;o->x=x;o->y=y;o->w=w;o->h=h;o->flags=flags;o->row=row;return o;
}
static unsigned sr_text(SettingsRenderPlan *p,const SettingsRenderCatalog *c,unsigned id,unsigned x,unsigned y,
 unsigned width,unsigned maxlines,unsigned flags,unsigned row) {
 unsigned units,w,lines;SettingsDrawOp *o;
 if(!sr_measure(c,id,maxlines,&units,&w,&lines) || w>width)return 0;
 o=sr_op(p,SETTINGS_DRAW_TEXT,id,x,y,w,lines*16,flags,row);if(!o)return 0;
 o->units=units;return 1;
}
static unsigned sr_num(SettingsRenderPlan *p,const SettingsRenderCatalog *c,const unsigned short *alphabet,
 unsigned a,unsigned b,unsigned fraction,unsigned x,unsigned y,unsigned width,unsigned flags,unsigned row) {
 unsigned short text[22];unsigned n=sr_digits(a,b,fraction,alphabet,text),i,w=0;SettingsDrawOp *o;
 for(i=0;i<n-1;i++)w+=c->widths[text[i]-1];if(w>width)return 0;
 o=sr_op(p,SETTINGS_DRAW_NUMBER,0,x,y,w,16,flags,row);if(!o)return 0;
 o->a=a;o->b=b;o->choice=fraction;o->offset=p->pool_used;o->units=n;p->pool_used+=n*2;return 1;
}
/* Fixed authored descriptors are compiled into the same bounded payload.
 * They identify layout by ID/content bounds, never by caller identity/language. */
static unsigned sr_footer_descriptor(unsigned variant,unsigned *p) {
 switch(variant){SGP_UI_FOOTER_LAYOUT_CASES default:return 0;}
}
static unsigned sr_footer_match(const SettingsRenderCatalog *c,unsigned id,unsigned *variant,unsigned *used,unsigned *wide) {
 unsigned n,an,found=0,chosen=0,total=0,width=0;
 const unsigned char *text=sr_lookup(c,id,&n),*alpha=sr_lookup(c,SGP_UI_FORMAT_POOL,&an);
 if(!text || !alpha || an<19 || sr16(alpha+2*(an-1))!=65535)return 0;
 unsigned space=sr16(alpha+26);
 for(unsigned v=0;v<SGP_UI_FOOTER_LAYOUT_COUNT;++v) {
  unsigned storage[7];sr_footer_descriptor(v,storage);const unsigned char *d=(const unsigned char *)storage;unsigned last=0,units=0,w=0,ok=1;
  if(d[0]!=id || d[1]!=n || !d[2] || d[2]>8)continue;
  for(unsigned j=0;j<d[2];++j) {
   unsigned start=d[3+3*j],len=d[4+3*j],key=d[5+3*j];
   if(!len || start<last || start>=n-1 || len>n-1-start || key>4 || (key && len!=1)){ok=0;break;}
   while(last<start)if(sr16(text+2*last++)!=space)ok=0;
   if(key && sr16(text+2*start)!=sr16(alpha+2*(an-6+key)))ok=0;
   for(unsigned k=0;k<len;++k){unsigned g=sr16(text+2*(start+k));if(!g || g>509 || !c->widths[g-1] || c->widths[g-1]>16){ok=0;break;}w+=c->widths[g-1];}
   w+=key?13:j+1<d[2]?9:0;units+=len+1;last=start+len;
  }
  if(!ok || last!=n-1 || sr16(text+2*last)!=65535 || w>232)continue;
  if(found){unsigned prior[7];sr_footer_descriptor(chosen,prior);for(unsigned k=1;k<27;++k)if(((const unsigned char *)prior)[k]!=d[k])return 0;}
  else {chosen=v;total=units;width=w;found=1;}
 }
 if(!found)return 0;*variant=chosen;*used=total;*wide=width;return 1;
}
static unsigned sr_footer(SettingsRenderPlan *p,const SettingsRenderCatalog *c,unsigned id) {
 unsigned variant,units,width;
 if(!sr_footer_match(c,id,&variant,&units,&width))return 0;
 SettingsDrawOp *o=sr_op(p,SETTINGS_DRAW_FOOTER,id,4,156,232,16,0,255);if(!o)return 0;
 unsigned storage[7];sr_footer_descriptor(variant,storage);o->a=variant;o->b=((const unsigned char *)storage)[2];o->offset=p->pool_used;o->units=units;p->pool_used+=units*2;return 1;
}
static unsigned sr_value_id(unsigned row,unsigned v) {
 switch(row) {
 case SETTINGS_TEXT:return SGP_UI_VALUE_SLOW+v;
 case SETTINGS_SCENE:return SGP_UI_VALUE_ON+v;
 case SETTINGS_STYLE:return SGP_UI_VALUE_SHIFT+v;
 case SETTINGS_AUDIO:return SGP_UI_VALUE_STEREO+v;
 case SETTINGS_BUTTON:return SGP_UI_VALUE_BUTTON_NORMAL+v;
 case SETTINGS_FRAME:return SGP_UI_FRAME_01+v;
 case SETTINGS_DIFFICULTY:return v?SGP_UI_VALUE_PLUS:SGP_UI_VALUE_NORMAL;
 case SETTINGS_WILD:return v?SGP_UI_VALUE_PLUS:SGP_UI_VALUE_WILD_NORMAL;
 case SETTINGS_ANIMATION:return v?SGP_UI_VALUE_ON:SGP_UI_VALUE_OFF;
 case SETTINGS_NPC:return v?SGP_UI_VALUE_SMOOTH:SGP_UI_VALUE_BUTTON_NORMAL;
 case SETTINGS_WIFI:return SGP_UI_VALUE_ORIGINAL+v;
 case SETTINGS_SHINY_MODE:return SGP_UI_VALUE_CLASSIC+v;
 case SETTINGS_TARGET:return v?SGP_UI_SPECIES_ID(v):SGP_UI_VALUE_NONE;
 case SETTINGS_SELECTOR_METHOD:return SGP_UI_METHOD_LAND+v;
 default:return SGP_UI_VALUE_OPEN;
 }
}
static unsigned sr_current(const SettingsState *s,unsigned row) {
 if(row==SETTINGS_SHINY_MODE)return s->draft.shiny.mode;
 if(row==SETTINGS_TARGET)return s->draft.shiny.target;
 if(row==SETTINGS_SELECTOR_METHOD)return s->draft.shiny.method;
 if(row<6)return ((const unsigned char *)&s->draft.native)[row];
 if(row<11)return ((const unsigned char *)&s->draft.plus)[row-6];
 return 0;
}
static unsigned sr_max(unsigned row) {return row==0||row==10?2:row==5?19:1;}
static unsigned sr_state(const SettingsState *s) {
 unsigned i,n;
 if(!sr_ram(s,sizeof(*s),4) || s->view>6 || s->notice>7 || s->row>=settings_visible_rows(s) ||
 s->search_row>2 || s->draft.shiny.mode>1 || s->draft.shiny.target>493 || s->draft.shiny.method>4 ||
 s->draft.shiny.search>1 || s->snapshot.shiny.available>1 || s->snapshot.shiny.mode>1 ||
 s->snapshot.shiny.method_mask>31 || s->snapshot.shiny.charge>40 || s->snapshot.shiny.chain>40 ||
 s->snapshot.shiny.target>493 || s->snapshot.shiny.status>7 || s->owner_status>7 || s->dirty_groups>7)return 0;
 for(i=0;i<11;i++)if(sr_current(s,i)>sr_max(i))return 0;
 for(i=0;i<5;i++)if(s->snapshot.shiny.counts[i]>12)return 0;
 if(s->view==SETTINGS_SELECTOR) {
  if(s->selector_row>SETTINGS_SELECTOR_METHOD || s->selector_row==SETTINGS_SEARCH_PRO ||
   (s->return_view!=SETTINGS_ROOT && s->return_view!=SETTINGS_SEARCH))return 0;
  if(s->selector_origin>(s->selector_row==SETTINGS_TARGET?493:s->selector_row==SETTINGS_SELECTOR_METHOD?4:sr_max(s->selector_row)))return 0;
  n=settings_selector_count(s);
  if(n ? s->selector_cursor>=n || s->selector_pending!=settings_selector_value(s,s->selector_cursor) :
   s->selector_cursor || s->selector_pending)return 0;
 }
 if(s->view==SETTINGS_INFO && s->info_origin!=SETTINGS_ROOT && s->info_origin!=SETTINGS_SEARCH)return 0;
 if(s->view==SETTINGS_EXIT_CONFIRM && s->choice>2)return 0;
 if(s->view==SETTINGS_APPLY_CONFIRM && s->choice>1)return 0;
 return 1;
}
static unsigned sr_window(unsigned first,unsigned selected,unsigned count,unsigned slots) {
 if(first+slots>count)first=count>slots?count-slots:0;
 if(selected<first)first=selected;
 if(selected>=first+slots)first=selected+1-slots;
 return first;
}
/* Search has no active selector. Ask the controller using a private logical
 * copy rather than duplicating its sparse method enumeration policy. */
static unsigned sr_methods(const SettingsState *s) {
 SettingsState query;unsigned i,n,bits=0;
 sr_copy(&query,s,sizeof(query));query.view=SETTINGS_SELECTOR;query.selector_row=SETTINGS_SELECTOR_METHOD;
 n=settings_selector_count(&query);
 for(i=0;i<n;i++)bits|=1u<<settings_selector_value(&query,i);
 return bits;
}
static unsigned sr_row(SettingsRenderPlan *p,const SettingsRenderCatalog *c,const SettingsState *s,
 unsigned row,unsigned y,unsigned selected,unsigned label,unsigned flags) {
 unsigned n,w,l,i,id,value=sr_current(s,row),max=sr_max(row),total=0,x,enabled;
 unsigned all=row<12 && row!=5 && row!=10,methods=row==SETTINGS_SELECTOR_METHOD?sr_methods(s):0;
 enabled=settings_row_enabled(s,row==SETTINGS_SELECTOR_METHOD?SETTINGS_SEARCH_PRO:row);
 if(row==SETTINGS_SELECTOR_METHOD && !methods)enabled=0;
 if(!enabled)flags|=SETTINGS_DRAW_DISABLED;if(selected)flags|=SETTINGS_DRAW_SELECTED;
 if(selected && !sr_op(p,SETTINGS_DRAW_BAND,0,4,y,232,20,flags,row))return 0;
 if(!sr_measure(c,label,1,&n,&w,&l) || !sr_text(p,c,label,17,y+2,w,1,flags,row))return 0;
 if(row==SETTINGS_SEARCH_PRO) {id=s->draft.shiny.search?SGP_UI_VALUE_PENDING:SGP_UI_VALUE_OPEN;all=0;}
 else id=row==SETTINGS_SELECTOR_METHOD && !(methods&(1u<<value))?SGP_UI_VALUE_UNAVAILABLE:sr_value_id(row,value);
 if(all) {for(i=0;i<=max;i++){unsigned vw;if(!sr_measure(c,sr_value_id(row,i),1,&n,&vw,&l))return 0;total+=vw+7+(i?3:0);}if(17+w+13+total>224)all=0;}
 if(!all){unsigned vw;if(!sr_measure(c,id,1,&n,&vw,&l))return 0;total=vw+7;flags|=SETTINGS_DRAW_SELECTOR;}
 x=224-total;if(x<17+w+8)return 0;
 if(row==SETTINGS_SEARCH_PRO || row==SETTINGS_TARGET) {
  flags|=SETTINGS_DRAW_SELECTOR;
  if(!sr_op(p,SETTINGS_DRAW_ACTION,0,228,y+6,6,8,flags,row))return 0;
 } else {
  unsigned left=value>0,right=value<max;
  if(row==SETTINGS_SELECTOR_METHOD){left=right=0;for(i=0;i<5;i++)if(methods&(1u<<i)){if(i<value)left=1;if(i>value)right=1;}}
  if(!sr_op(p,SETTINGS_DRAW_LEFT,0,x-7,y+6,5,7,flags|(!left||!enabled?SETTINGS_DRAW_DISABLED:0),row) ||
   !sr_op(p,SETTINGS_DRAW_RIGHT,0,228,y+6,5,7,flags|(!right||!enabled?SETTINGS_DRAW_DISABLED:0),row))return 0;
 }
 if(!enabled && !sr_op(p,SETTINGS_DRAW_LOCK,0,228,y+5,6,8,flags,row))return 0;
 for(i=0;i<(all?max+1:1);++i) {
  unsigned vw,vid=all?sr_value_id(row,i):id,chosen=!all || i==value;
  if(!sr_measure(c,vid,1,&n,&vw,&l))return 0;
  if(all && chosen && !sr_op(p,SETTINGS_DRAW_CHOICE,0,x,y+1,vw+7,18,flags|SETTINGS_DRAW_CHOSEN,row))return 0;
  if(!sr_text(p,c,vid,x+3,y+2,vw,1,flags|(chosen?SETTINGS_DRAW_CHOSEN:0),row))return 0;
  x+=vw+10;
 }
 return 1;
}
static unsigned sr_root(SettingsRenderPlan *p,const SettingsRenderRequest *r) {
 const SettingsState *s=r->state;unsigned total=settings_visible_rows(s)+3,sel=s->row+1+(s->row>=6)+(s->row>=11),i,j,row;
 p->first=sr_window(r->first,sel,total,6);
 for(i=0;i<6 && p->first+i<total;i++) {j=p->first+i;
  if(j==0 || j==7 || j==13) {if(!sr_text(p,r->catalog,j==0?3:j==7?4:5,12,38+i*20,220,1,SETTINGS_DRAW_HEADING,255))return 0;}
  else {row=j-1-(j>7)-(j>13);if(!sr_row(p,r->catalog,s,row,36+i*20,row==s->row,SGP_UI_ROW_TEXT+row,0))return 0;}
 }return 1;
}
static unsigned sr_selector(SettingsRenderPlan *p,const SettingsRenderRequest *r) {
 const SettingsState *s=r->state;unsigned count=settings_selector_count(s),i,index,value,flags;
 p->first=sr_window(r->selector_first,s->selector_cursor,count,6);
 for(i=0;i<6 && p->first+i<count;i++) {index=p->first+i;value=settings_selector_value(s,index);flags=0;
  if(value==s->selector_origin)flags|=SETTINGS_DRAW_CHOSEN;
  if(index==s->selector_cursor){flags|=SETTINGS_DRAW_SELECTED;if(!sr_op(p,SETTINGS_DRAW_BAND,0,4,36+20*i,232,20,flags,s->selector_row))return 0;}
  if(flags&SETTINGS_DRAW_CHOSEN)if(!sr_op(p,SETTINGS_DRAW_CHOICE,0,14,37+20*i,220,18,flags,s->selector_row))return 0;
  if(!sr_text(p,r->catalog,sr_value_id(s->selector_row,value),17,38+20*i,214,1,flags,s->selector_row))return 0;
 }return 1;
}
static unsigned sr_info(SettingsRenderPlan *p,const SettingsRenderRequest *r) {
 const SettingsState *s=r->state;unsigned row=s->row,id=SGP_UI_INFO_TEXT+row,n,w,l,prefix,i,preview_width;
 SettingsDrawOp *o;const unsigned char *text;
 if(s->info_origin==SETTINGS_SEARCH)id=s->search_row==0?SGP_UI_INFO_TARGET:SGP_UI_INFO_SEARCH;
 if(!sr_text(p,r->catalog,id,4,38,232,(row==0||row==5)&&s->info_origin==0?4:7,0,255))return 0;
 if(s->info_origin==0 && (row==0 || row==5)) {
  /* Native ring inner: local16,112,200,32; text-speed preview is unframed. */
  preview_width=row==5?200:216;
  if(row==5){p->frame=s->draft.native.frame+1;o=sr_op(p,SETTINGS_DRAW_FRAME,0,0,104,240,48,0,255);if(!o)return 0;o->choice=s->draft.native.frame;}
  if(!sr_measure(r->catalog,SGP_UI_PREVIEW_TEXT,2,&n,&w,&l) || w>preview_width || n>128)return 0;
  text=sr_lookup(r->catalog,SGP_UI_PREVIEW_TEXT,&n);if(!text)return 0;
  prefix=r->preview_units;if(prefix>n-1)prefix=n-1;
  w=0;l=1;for(i=0;i<prefix;i++){unsigned g=sr16(text+2*i);if(g==0xe000){l++;w=0;}else {if(!g||g>509)return 0;w+=r->catalog->widths[g-1];}if(w>preview_width||l>2)return 0;}
  o=sr_op(p,SETTINGS_DRAW_PREVIEW,SGP_UI_PREVIEW_TEXT,row==5?16:12,112,preview_width,32,SETTINGS_DRAW_PREFIX,255);if(!o)return 0;
  o->a=prefix;o->b=s->draft.native.text;o->units=prefix+1;o->offset=p->pool_used;p->pool_used+=(prefix+1)*2;
 }return 1;
}
static unsigned sr_search(SettingsRenderPlan *p,const SettingsRenderRequest *r,const unsigned short *a) {
 const SettingsState *s=r->state;unsigned i,n,w,l,flags,id,value,j,start;
 for(i=0;i<2;i++) {
  start=p->count;
  if(!sr_row(p,r->catalog,s,i?SETTINGS_SELECTOR_METHOD:SETTINGS_TARGET,36+i*20,s->search_row==i,
   i?SGP_UI_STATUS_METHOD:SGP_UI_STATUS_POKEMON,0))return 0;
  for(j=start;j<p->count;j++)p->ops[j].row=i;
 }
 flags=settings_can_prepare(s)?0:SETTINGS_DRAW_DISABLED;
 if(s->search_row==2)flags|=SETTINGS_DRAW_SELECTED;
 if(s->search_row==2 && !sr_op(p,SETTINGS_DRAW_BAND,0,4,76,232,20,flags|SETTINGS_DRAW_SELECTED,2))return 0;
 if(!sr_op(p,SETTINGS_DRAW_ACTION,0,12,82,6,8,flags,2) || !sr_text(p,r->catalog,SGP_UI_ACTION_PREPARE,23,78,209,1,flags,2))return 0;
 for(i=0;i<3;i++){id=SGP_UI_STATUS_SUCCESSES+i;
  if(!sr_measure(r->catalog,id,1,&n,&w,&l) || !sr_text(p,r->catalog,id,12,98+i*20,w,1,SETTINGS_DRAW_READONLY,i+3))return 0;
  value=i==0?s->snapshot.shiny.chain:i==1?1:settings_effective_charge(s);
  if(!sr_num(p,r->catalog,a,value,i==1?s->snapshot.shiny.denominator:i==2?40:0,i!=0,w+20,98+i*20,212-w,SETTINGS_DRAW_READONLY,i+3))return 0;
 }return 1;
}
static unsigned sr_confirm(SettingsRenderPlan *p,const SettingsRenderRequest *r) {
 const SettingsState *s=r->state;unsigned y=38,n,w,l,i,x=4,count=s->view==SETTINGS_EXIT_CONFIRM?3:2,id;
 id=s->view==SETTINGS_EXIT_CONFIRM?SGP_UI_EXIT_PROMPT:SGP_UI_APPLY_PROMPT;
 if(!sr_measure(r->catalog,id,3,&n,&w,&l) || !sr_text(p,r->catalog,id,4,y,232,3,0,255))return 0;y+=l*16+4;
 if(!s->dirty_groups && !sr_text(p,r->catalog,SGP_UI_NO_CHANGES,4,y,232,1,0,255))return 0;
 for(i=0;i<3;i++)if(s->dirty_groups&(1u<<i)){
  if(!sr_measure(r->catalog,SGP_UI_SECTION_GAME+i,1,&n,&w,&l) || x+w>236 || !sr_text(p,r->catalog,SGP_UI_SECTION_GAME+i,x,y,w,1,SETTINGS_DRAW_HEADING,255))return 0;x+=w+8;
 }
 y+=20;
 if(s->draft.shiny.search){if(!sr_text(p,r->catalog,SGP_UI_SEARCH_PENDING,4,y,232,2,SETTINGS_DRAW_PENDING,255))return 0;
  if(!sr_measure(r->catalog,SGP_UI_SEARCH_PENDING,2,&n,&w,&l))return 0;y+=l*16+4;}
 if(y>136)return 0;x=4;
 for(i=0;i<count;i++) {id=i==0?SGP_UI_ACTION_APPLY:count==3?SGP_UI_ACTION_DISCARD+i-1:SGP_UI_ACTION_CANCEL;
  if(!sr_measure(r->catalog,id,1,&n,&w,&l) || x+w+8>240)return 0;
  if(i==s->choice && !sr_op(p,SETTINGS_DRAW_BAND,0,x,136,w+8,20,SETTINGS_DRAW_SELECTED,i))return 0;
  if(!sr_text(p,r->catalog,id,x+4,138,w,1,i==s->choice?SETTINGS_DRAW_SELECTED:0,i))return 0;x+=w+16;
 }return 1;
}
static unsigned sr_error(SettingsRenderPlan *p,const SettingsRenderRequest *r) {
 unsigned n,w,l,id=0;
 if(!sr_measure(r->catalog,SGP_UI_ERROR_OWNER,7,&n,&w,&l) ||
 !sr_text(p,r->catalog,SGP_UI_ERROR_OWNER,4,38,232,7,0,255))return 0;
 switch(r->state->owner_status) {
 case SGP_SHINY_STALE:id=SGP_UI_NOTICE_STALE;break;
 case SGP_SHINY_BUSY:id=SGP_UI_NOTICE_BUSY;break;
 case SGP_SHINY_GENERATION_FAILED:id=SGP_UI_NOTICE_FAILED;break;
 default:break;
 }
 return !id || sr_text(p,r->catalog,id,4,42+l*16,232,7-l,0,255);
}
static unsigned sr_build(SettingsRenderPlan *p,const SettingsRenderRequest *r,const unsigned short *a) {
 const SettingsState *s=r->state;unsigned context=SGP_UI_CONTEXT_ROOT,footer=SGP_UI_FOOTER_ROOT,n,total;
 p->magic=SETTINGS_RENDER_MAGIC;p->identity=r->catalog->identity;p->pool_epoch=r->pool_epoch;p->view=s->view;
 if(s->view==SETTINGS_SELECTOR){context=s->selector_row==12?SGP_UI_HEADING_TARGET:s->selector_row==14?SGP_UI_HEADING_METHOD:SGP_UI_HEADING_VALUE;footer=SGP_UI_FOOTER_SELECTOR;}
 else if(s->view==SETTINGS_INFO){context=SGP_UI_HEADING_INFO;footer=SGP_UI_FOOTER_INFO;}
 else if(s->view==SETTINGS_SEARCH){context=SGP_UI_CONTEXT_SEARCH;footer=SGP_UI_FOOTER_SEARCH;}
 else if(s->view>=SETTINGS_EXIT_CONFIRM){context=SGP_UI_HEADING_EXIT+s->view-SETTINGS_EXIT_CONFIRM;footer=s->view==SETTINGS_ERROR?SGP_UI_FOOTER_ERROR:SGP_UI_FOOTER_CONFIRM;}
 if(s->notice && s->notice<=6 && (s->view==SETTINGS_ROOT || s->view==SETTINGS_SEARCH || s->view==SETTINGS_SELECTOR)) {
  switch(s->notice) {
  case SETTINGS_NOTICE_UNAVAILABLE:context=SGP_UI_NOTICE_UNAVAILABLE;break;
  case SETTINGS_NOTICE_EMPTY_CANDIDATES:context=SGP_UI_NOTICE_EMPTY;break;
  case SETTINGS_NOTICE_PRO_ONLY:context=SGP_UI_NOTICE_PRO;break;
  case SETTINGS_NOTICE_NO_TARGET:context=SGP_UI_NOTICE_NO_TARGET;break;
  case SETTINGS_NOTICE_METHOD:context=SGP_UI_NOTICE_METHOD;break;
  default:context=SGP_UI_NOTICE_CHARGE;break;
  }
 }
 unsigned tw,vw,lines;
 if(!sr_measure(r->catalog,SGP_UI_VERSION,1,&n,&vw,&lines) ||
 !sr_text(p,r->catalog,SGP_UI_TITLE,9,4,176,1,0,255) || !sr_text(p,r->catalog,SGP_UI_VERSION,231-vw,4,vw,1,0,255) ||
 !sr_text(p,r->catalog,context,8,20,200,1,0,255) || !sr_footer(p,r->catalog,footer))return 0;
 if(s->view==SETTINGS_ROOT || s->view==SETTINGS_SELECTOR){total=s->view==0?settings_visible_rows(s):settings_selector_count(s);n=s->view==0?s->row+1:total?s->selector_cursor+1:0;
  if(!sr_num(p,r->catalog,a,n,total,1,199,20,32,0,255))return 0;
  tw=p->ops[p->count-1].w;p->ops[p->count-1].x=231-tw;}
 switch(s->view){
 case SETTINGS_ROOT:return sr_root(p,r);
 case SETTINGS_SELECTOR:return sr_selector(p,r);
 case SETTINGS_INFO:return sr_info(p,r);
 case SETTINGS_SEARCH:return sr_search(p,r,a);
 case SETTINGS_EXIT_CONFIRM:case SETTINGS_APPLY_CONFIRM:return sr_confirm(p,r);
 default:return sr_error(p,r);
 }
}
unsigned settings_render_build(const SettingsRenderRequest *r) {
 SettingsRenderPlan plan;unsigned short alphabet[14],digits[22];unsigned i,j,n;const unsigned char *text;
 if(!sr_ram(r,sizeof(*r),4) || !sr_catalog(r->catalog) || !sr_state(r->state) ||
 r->out_bytes!=sizeof(plan) || !sr_ram(r->out,sizeof(plan),4) || r->pool_bytes<4 || r->pool_bytes>4096 ||
 !sr_ram(r->pool,r->pool_bytes,4) || !r->pool_epoch || r->first>17 || r->selector_first>20)return 0;
 #define SR_ALIAS(p,n) (sr_overlap(r->out,sizeof(plan),(p),(n)) || sr_overlap(r->pool,r->pool_bytes,(p),(n)))
 if(sr_overlap(r->out,sizeof(plan),r->pool,r->pool_bytes) || SR_ALIAS(r,sizeof(*r)) || SR_ALIAS(r->state,sizeof(*r->state)) ||
 SR_ALIAS(r->catalog,sizeof(*r->catalog)) || SR_ALIAS(r->catalog->root,r->catalog->bytes) || SR_ALIAS(r->catalog->widths,509))return 0;
 #undef SR_ALIAS
 if(!sr_alphabet(r->catalog,alphabet))return 0;
 sr_zero(&plan,sizeof(plan));if(!sr_build(&plan,r,alphabet) || plan.pool_used>r->pool_bytes)return 0;
 /* No failures after this point: all slices, geometry and capacity admitted. */
 for(i=0;i<plan.count;i++){SettingsDrawOp *o=&plan.ops[i];unsigned short *out=(unsigned short *)((unsigned char *)r->pool+o->offset);
  if(o->kind==SETTINGS_DRAW_NUMBER){n=sr_digits(o->a,o->b,o->choice,alphabet,digits);for(j=0;j<n;j++)out[j]=digits[j];}
  else if(o->kind==SETTINGS_DRAW_FOOTER){unsigned storage[7];sr_footer_descriptor(o->a,storage);const unsigned char *d=(const unsigned char *)storage;unsigned at=0;
   text=sr_lookup(r->catalog,o->id,&n);
   for(j=0;j<d[2];++j){unsigned k;for(k=0;k<d[4+3*j];++k)out[at++]=(unsigned short)sr16(text+2*(d[3+3*j]+k));out[at++]=65535;}
  }
  else if(o->kind==SETTINGS_DRAW_PREVIEW){text=sr_lookup(r->catalog,o->id,&n);for(j=0;j<o->a;j++)out[j]=(unsigned short)sr16(text+2*j);out[j]=65535;}
 }
 sr_copy(r->out,&plan,sizeof(plan));return 1;
}
static unsigned sr_rows(const SettingsDrawOp *o) {
 unsigned y=o->y,bottom=y+o->h;
 if(o->row!=255 && y>=36 && y<156){y=y<56?36:y<76?56:y<96?76:y<116?96:y<136?116:136;if(bottom<y+20)bottom=y+20;}
 unsigned first=y>>3,last=(bottom-1)>>3,mask=0;
 while(first<=last)mask|=1u<<first++;
 return mask;
}
static unsigned sr_equal(const SettingsDrawOp *a,const SettingsDrawOp *b) {
 return a->a==b->a && a->b==b->b && a->id==b->id && a->units==b->units && a->flags==b->flags &&
 a->x==b->x && a->y==b->y && a->w==b->w && a->h==b->h && a->kind==b->kind && a->row==b->row && a->choice==b->choice;
}
static unsigned sr_plan(const SettingsRenderPlan *p) {
 unsigned i;
 if(p->magic!=SETTINGS_RENDER_MAGIC || p->count>SETTINGS_RENDER_OPS || p->view>6 || p->frame>20)return 0;
 for(i=0;i<p->count;i++){const SettingsDrawOp *o=&p->ops[i];
  if(!o->w || !o->h || o->x+o->w>240 || o->y+o->h>176 || o->kind<1 || o->kind>SETTINGS_DRAW_FOOTER)return 0;
  if(o->kind==SETTINGS_DRAW_FOOTER && (o->a>=SGP_UI_FOOTER_LAYOUT_COUNT || !o->b || o->b>8 || !o->units || o->units>128 || o->x!=4 || o->y!=156 || o->w!=232 || o->h!=16 || o->flags || o->row!=255))return 0;
 }return 1;
}
unsigned settings_render_dirty(const SettingsRenderPlan *old,const SettingsRenderPlan *now,unsigned bad,unsigned *full) {
 unsigned i,j,found,mask=bad&SETTINGS_RENDER_FULL;
 if(!sr_ram(full,4,4) || !sr_ram(now,sizeof(*now),4) ||
 sr_overlap(full,4,now,sizeof(*now)))return SETTINGS_RENDER_FULL;
 if(old && (!sr_ram(old,sizeof(*old),4) || sr_overlap(full,4,old,sizeof(*old))))return SETTINGS_RENDER_FULL;
 *full=1;
 if(!sr_plan(now))return SETTINGS_RENDER_FULL;
 /* Empty regions carry view-dependent chrome outside semantic op bounds. */
 if(!old || !sr_plan(old) || old->identity!=now->identity || old->view!=now->view ||
 old->frame!=now->frame || (bad&SETTINGS_RENDER_FULL)==SETTINGS_RENDER_FULL)return SETTINGS_RENDER_FULL;
 *full=0;
 for(i=0;i<old->count;i++){found=0;for(j=0;j<now->count;j++)if(sr_equal(&old->ops[i],&now->ops[j])){found=1;break;}if(!found)mask|=sr_rows(&old->ops[i]);}
 for(i=0;i<now->count;i++){found=0;for(j=0;j<old->count;j++)if(sr_equal(&now->ops[i],&old->ops[j])){found=1;break;}if(!found)mask|=sr_rows(&now->ops[i]);}
 return mask&SETTINGS_RENDER_FULL;
}

unsigned settings_render_format(const SettingsFormatRequest *r) {
 unsigned short alphabet[14],digits[22];unsigned n,i;
 if(!sr_ram(r,sizeof(*r),4) || !sr_catalog(r->catalog) || r->fraction>1 || !r->pool_epoch ||
 r->pool_bytes<4 || r->pool_bytes>4096 || !sr_ram(r->pool,r->pool_bytes,4))return 0;
 if(sr_overlap(r->pool,r->pool_bytes,r,sizeof(*r)) || sr_overlap(r->pool,r->pool_bytes,r->catalog,sizeof(*r->catalog)) ||
 sr_overlap(r->pool,r->pool_bytes,r->catalog->root,r->catalog->bytes) || sr_overlap(r->pool,r->pool_bytes,r->catalog->widths,509) ||
 !sr_alphabet(r->catalog,alphabet))return 0;
 n=sr_digits(r->a,r->b,r->fraction,alphabet,digits);if(n*2>r->pool_bytes)return 0;
 for(i=0;i<n;i++)((unsigned short *)r->pool)[i]=digits[i];return n;
}
