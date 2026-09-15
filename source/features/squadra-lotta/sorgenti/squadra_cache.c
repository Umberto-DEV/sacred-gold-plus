/* Sacred Gold Plus: dati mosse gia' residenti per il menu Squadra in lotta.
 * GPL-3.0-or-later. Nessuna cache aggiuntiva o stato persistente.
 */
typedef unsigned int u32;
typedef unsigned char u8;
typedef u32 (*Fn2)(u32, u32);

static const u8 *record(u32 move, u32 app) {
    u32 args, bs, ctx;
    u8 load = *(volatile const u8 *)0x023D8703u;
    if (*(volatile const u8 *)0x023D8704u != 0x5au
        || (load != 1u && load != 2u)
        || !*(volatile const u8 *)0x023D8716u || move > 467u || !app)
        return (const u8 *)0;
    args = *(const u32 *)app;
    if (!args) return (const u8 *)0;
    bs = *(const u32 *)(args + 8u);
    if (!bs) return (const u8 *)0;
    ctx = *(const u32 *)(bs + 0x30u);
    if (!ctx) return (const u8 *)0;
    /* LoadMoveTbl carica 468 record da 16 byte in trainerAIData.moveData. */
    return (const u8 *)(ctx + 0x3deu + move * 16u);
}

u32 sgp_squadra_attr_cache(u32 move, u32 attr, u32 app) {
    const u8 *data;
    if (attr >= 1u && attr <= 4u && (data = record(move, app)))
        return data[attr + 1u];
    return ((Fn2)0x02073315u)(move, attr);
}

u32 sgp_squadra_pp_cache(u32 move, u32 ups, u32 app) {
    const u8 *data = record(move, app);
    u32 pp, numerator, extra;
    if (!data) return ((Fn2)0x0207332du)(move, ups);
    if (ups > 3u) ups = 3u;
    pp = data[6];
    /* Per 0 <= numerator <= 765, (numerator*205)>>10 coincide con
     * floor(numerator/5). Contratto verificato su tutti i valori PP/PP-Up. */
    numerator = pp * ups;
    extra = (numerator * 205u) >> 10;
    return (u8)(pp + extra);
}

/* I cinque BL sono in ov08_0221D184. Il puntatore app e' a [sp] del
 * chiamante, prima del nostro frame di 8 byte; i registri r4-r7 restano
 * quelli della scansione della squadra. */
__attribute__((naked, used)) void sgp_squadra_attr_hook(void) {
    __asm__ volatile("push {r3,lr}\nldr r2,[sp,#8]\nbl sgp_squadra_attr_cache\npop {r3,pc}\n");
}
__attribute__((naked, used)) void sgp_squadra_pp_hook(void) {
    __asm__ volatile("push {r3,lr}\nldr r2,[sp,#8]\nbl sgp_squadra_pp_cache\npop {r3,pc}\n");
}
