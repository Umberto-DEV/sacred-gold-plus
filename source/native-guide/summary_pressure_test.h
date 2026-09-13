/* Private compile-time instrumentation only, never enabled in the guide ROM.
 * The real NNS allocator owns the pressure block. The guide's subsequent
 * identical request must itself return NULL. No fabricated free-list state. */
static int pressure_acquire(Lease *ui)
{
    Lease pressure={ui->heap,0};
    if(!lease_acquire(&pressure)) { P->errors|=0x100;return 0; }
    P->reserved+=1;
    pressure.block[0]=0x51A7F00D;
    pressure.block[LEASE_BYTES/4-1]=0xE09C1234;
    int result=lease_acquire(ui);
    if(!result) P->reserved+=0x100;
    else { P->errors|=0x200;lease_release(ui); }
    if(pressure.block[0]!=0x51A7F00D || pressure.block[LEASE_BYTES/4-1]!=0xE09C1234)
        P->errors|=0x400;
    else P->reserved+=0x10000;
    if(lease_release(&pressure)) P->reserved+=0x1000000;
    return 0;
}
