/* GPL-3.0-or-later. Original bounded NNS lease for the verified HG ABI.
 * Included in the probe translation unit: the historical loader supports
 * internal .text Thumb BL only. No copied game implementation or global data.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

typedef struct { u8 *heap; volatile u32 *block; } Lease;
#define NNS_ALLOC ((void *(*)(void *,u32,int))0x020B53A0)
#define NNS_FREE ((void (*)(void *,void *))0x020B5530)
#define IRQ_OFF ((u32 (*)(void))0x020D3A38)
#define IRQ_RESTORE ((u32 (*)(u32))0x020D3A4C)
#define LEASE_BYTES 22528u

static int ram_range(u32 address, u32 length)
{
    return address >= 0x02000000 && address <= 0x02400000 - length;
}

/* Resolve the current handle each entry; never cache a dynamic heap index. */
static u8 *summary_heap(void)
{
    u8 *info = (u8 *)0x021D1584;
    if (*(u16 *)(info+20) <= 19) return (u8 *)0;
    u8 *indices = *(u8 **)(info+16);
    u32 *handles = *(u32 **)info;
    if (!ram_range((u32)indices,20)) return (u8 *)0;
    u32 index = indices[19];
    if (index >= *(u16 *)(info+24) || index == *(u16 *)(info+26)
        || !ram_range((u32)handles,4*(index+1))) return (u8 *)0;
    u8 *heap = (u8 *)handles[index];
    if (!ram_range((u32)heap,0x38) || ((u32)heap&3)
        || *(u32 *)heap != 0x45585048) return (u8 *)0;
    u32 start=*(u32 *)(heap+0x18), end=*(u32 *)(heap+0x1c);
    if (start < (u32)heap+0x38 || end < start || end>0x02400000) return (u8 *)0;
    return heap;
}

__attribute__((noinline))
static int lease_acquire(Lease *lease)
{
    if (!lease->heap || lease->block) return 0;
    u32 irq = IRQ_OFF();
    lease->block = (volatile u32 *)NNS_ALLOC(lease->heap,LEASE_BYTES,4);
    IRQ_RESTORE(irq);
    return lease->block != (volatile u32 *)0;
}

/* NULL is a no-op. Only the original raw NNS pointer reaches matching free.
 * Never use Heap_Free, RemoveWindow or sHeapInfo.numMemBlocks here. */
__attribute__((noinline))
static int lease_release(Lease *lease)
{
    if (!lease->block) return 0;
    u32 irq = IRQ_OFF();
    NNS_FREE(lease->heap,(void *)lease->block);
    lease->block = (volatile u32 *)0;
    IRQ_RESTORE(irq);
    return 1;
}
