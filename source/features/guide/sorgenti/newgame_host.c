/* GPL-3.0-or-later. Oak template host; included only by combined_guide.c.
 * Original ov53 Init/Main/Exit retain all save, naming and graphics ownership.
 * The instance marker survives Oak's naming -> state0 graphics reconstruction.
 */
#define OAK_INIT ((int (*)(u8 *,int *))0x021E5901)
#define OAK_MAIN ((int (*)(u8 *,int *))0x021E5995)
#define OAK_EXIT ((int (*)(u8 *,int *))0x021E5B49)
#define MANAGER_DATA ((u8 *(*)(u8 *))0x02007291)

static u8 *host_heap(u32 id)
{
    u8 *info=(u8 *)0x021D1584;
    if (*(u16 *)(info+20)<=id) return 0;
    u8 *indices=*(u8 **)(info+16);
    u32 *handles=*(u32 **)info;
    if (!ram_range((u32)indices,id+1)) return 0;
    u32 index=indices[id];
    if (index>=*(u16 *)(info+24) || index==*(u16 *)(info+26)
        || !ram_range((u32)handles,4*(index+1))) return 0;
    u8 *heap=(u8 *)handles[index];
    if (!ram_range((u32)heap,0x38) || ((u32)heap&3)
        || *(u32 *)heap!=0x45585048) return 0;
    u32 start=*(u32 *)(heap+0x18),end=*(u32 *)(heap+0x1c);
    if(start<(u32)heap+0x38 || end<start || end>0x02400000) return 0;
    return heap;
}

static int oak_resources(u8 *s)
{
    if(*(u32 *)SYS!=0x021E5BCD || *(u8 **)(SYS+4)!=s
        || *(volatile u16 *)0x04001008!=0x0F18
        || *(volatile u32 *)0x04000240!=0x00848281
        || *(volatile u16 *)0x04000244!=0x8080
        || *(volatile u8 *)0x04000246!=0x80
        || *(volatile u16 *)0x04000248!=0x8200) return 0;
    u8 *bg=host_bg(s),*f=font_work();
    if(!ram_range((u32)bg,0x168) || !ram_range((u32)f,0xBC)) return 0;
    u8 *b=bg+0xB8,*fd=*(u8 **)(f+0x9C);
    return *(u32 *)bg==80 && ram_range(*(u32 *)b,2048)
        && *(u32 *)(b+4)==2048 && !*(u32 *)(b+8)
        && !*(u32 *)(b+12) && !*(u32 *)(b+16)
        && *(u32 *)(b+20)==0x20000100
        && ram_range((u32)fd,0x80) && *(u32 *)fd==1
        && *(u32 *)(fd+4)==0x02026111 && !*(u32 *)(fd+16);
}

__attribute__((used,noinline,section(".text")))
int oak_guide_init(u8 *manager,int *state)
{
    int result=OAK_INIT(manager,state);
    /* Top-level ownership changes only after the prior host released its
     * lease. A foreign live context fails closed; never free another owner. */
    if(!P->context) {
        fill32((void *)P,0,sizeof(Persistent));
        P->magic=OAK_MAGIC;P->reserved=(u32)manager;
        P->summary=MANAGER_DATA(manager);
    }
    return result;
}

__attribute__((used,noinline,section(".text")))
int oak_guide_main(u8 *manager,int *state)
{
    if(oak_owner() && P->reserved==(u32)manager) {
        if(P->phase) {
            modal_run(P->summary);
            if(P->phase) return 0;
        }
        if(!P->opens && *state==0) {
            int result=OAK_MAIN(manager,state);
            if(*state==1 && !*(u32 *)(P->summary+0xC)) {
                P->opens=1;P->panel=0;P->latch=1;P->phase=1;
                P->visibility=DISPLAY&VISIBILITY;
                visibility(0);
            }
            return result;
        }
    }
    return OAK_MAIN(manager,state);
}

__attribute__((used,noinline,section(".text")))
int oak_guide_exit(u8 *manager,int *state)
{
    if(oak_owner() && P->reserved==(u32)manager) {
        guide_cleanup();
        fill32((void *)P,0,sizeof(Persistent));
    }
    return OAK_EXIT(manager,state);
}
