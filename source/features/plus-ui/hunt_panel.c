/* Included in extended.c: draft-only navigation; all mutations belong to Apply. */
static void list_top(void){XSTATE->top=XSTATE->list>=10?10:(XSTATE->list>=5?5:0);}
static void back(void){ExtendedState *e=XSTATE;if(e->panel==2){e->panel=1;e->row=0;}else if(e->panel==3){e->panel=1;e->row=4;}else{e->panel=0;e->row=e->root_row;}e->error=0;draw();}
static void page(int next){ExtendedState *e=XSTATE;
 if(e->panel==2){u32 count=e->snapshot.counts[e->draft.method]+1,top=e->top;if(next){top+=5;if(top>=count)top=0;}else if(top>=5)top-=5;else{top=count>10?10:(count>5?5:0);}e->list=e->top=top;
 }else if(e->panel==3){e->rules=next?(e->rules+1==3?0:e->rules+1):(e->rules?e->rules-1:2);}
 else if(e->panel){back();return;}else{if(e->page==(u32)next)return;e->page=(u8)next;}
 draw();PlaySE(SE_SCORRI);
}
static void open_list(void){ExtendedState *e=XSTATE;u32 i;if(!e->snapshot.available)return;e->panel=2;e->list=0;for(i=0;i<e->snapshot.counts[e->draft.method];i++)if(candidate(i)==e->draft.target){e->list=i+1;break;}list_top();draw();}
static void choose(void){ExtendedState *e=XSTATE;u32 target,i,found=0;
 if(!e->snapshot.available)return;
 if(e->panel==2){if(e->error==SGP_SHINY_UNAVAILABLE)return;target=e->list?candidate(e->list-1):0;if(e->list&&!target){e->error=SGP_SHINY_STALE;draw();return;}if(target!=e->draft.target){e->draft.target=target;edited();}e->panel=1;e->row=0;}
 else if(e->panel==3){page(1);return;}
 else if(e->panel==1){if(e->row==0){open_list();return;}if(e->row==1){u32 old=e->draft.method;do{e->draft.method=e->draft.method==4?0:e->draft.method+1;if(e->snapshot.method_mask&(1u<<e->draft.method))break;}while(e->draft.method!=old);edited();}
  else if(e->row==4){e->panel=3;e->rules=0;}
  else if(e->row==3){if(!e->draft.mode)e->error=SGP_SHINY_PRO_ONLY;else if(charge()<40)e->error=SGP_SHINY_NEED_CHARGE;else{for(i=0;i<e->snapshot.counts[e->draft.method];i++)if(candidate(i)==e->draft.target)found=1;if(!found)e->error=SGP_SHINY_NO_TARGET;else{e->draft.search=1;e->panel=0;e->row=e->root_row;e->error=0;}}}
 }draw();
}
static void move(int down){ExtendedState *e=XSTATE;u32 max=e->panel==2?e->snapshot.counts[e->draft.method]:4;
 if(e->panel==3){page(down);return;}
 if(e->panel==2){e->list=down?(e->list==max?0:e->list+1):(e->list?e->list-1:max);list_top();}
 else e->row=down?(e->row==max?0:e->row+1):(e->row?e->row-1:max);
 PlaySE(SE_SCORRI);
}
static void change(int right){ExtendedState *e=XSTATE;u32 old;
 if(!e->snapshot.available)return;
 if(e->panel==2||e->panel==3){page(right);return;}
 if(!e->panel&&e->row==0){e->draft.mode^=1;edited();}
 else if(!e->panel&&e->row==1){open_list();}
 else if(e->panel==1&&e->row==1){old=e->draft.method;do{e->draft.method=right?(e->draft.method==4?0:e->draft.method+1):(e->draft.method?e->draft.method-1:4);if(e->snapshot.method_mask&(1u<<e->draft.method))break;}while(e->draft.method!=old);edited();}
 PlaySE(SE_SCORRI);
}
