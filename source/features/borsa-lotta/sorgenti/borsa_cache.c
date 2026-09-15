/* Sacred Gold Plus: apertura Borsa con ItemData gia' residente in battaglia.
 * GPL-3.0-or-later. Non alloca memoria e non mantiene stato proprio.
 */
typedef unsigned int u32;
typedef unsigned char u8;
typedef u32 (*Fn2)(u32, u32);
typedef u32 (*Fn3)(u32, u32, u32);

static u32 abilitato(void) {
    u8 load = *(volatile const u8 *)0x023D8703u;
    return *(volatile const u8 *)0x023D8704u == 0x5au
        && (load == 1u || load == 2u)
        && *(volatile const u8 *)0x023D8716u;
}

/* L'app proviene da r4 di ov08_02223BF4; i primi tre argomenti conservano
 * il contratto GetItemAttr. La cache appartiene a BattleContext_New/Delete.
 */
u32 sgp_borsa_attr_cache(u32 item, u32 attr, u32 heap, u32 app) {
    u32 args, bs, ctx, cache, index, count;
    if (!abilitato() || attr != 13u || item > 536u || !app) goto native;
    args = *(const u32 *)app;
    if (!args) goto native;
    bs = *(const u32 *)args;
    if (!bs) goto native;
    ctx = *(const u32 *)(bs + 0x30u);
    if (!ctx) goto native;
    cache = *(const u32 *)(ctx + 0x2120u);
    if (!cache) goto native;
    index = ((Fn2)0x02077C19u)(item, 0u);
    /* LoadAllItemData legge mapping(ITEM_MAX)*sizeof(ItemData), senza +1.
     * L'ultimo membro NON e' in cache: conserva la lettura originale.
     * GetItemIndexMapping non verifica item>ITEM_MAX; il gate precede il BL.
     */
    count = ((Fn2)0x02077C19u)(536u, 0u);
    if (!count || index >= count) goto native;
    return ((Fn3)0x02257E75u)(ctx, item, attr);
native:
    return ((Fn3)0x02077D89u)(item, attr, heap);
}

/* Unico gancio: BL a ov08:02223C30. Frame di 8 byte; r4 resta intatto.
 * Il caricamento originale di r1=13 in ov08 non viene modificato.
 */
__attribute__((naked, used)) void sgp_borsa_attr_hook(void) {
    __asm__ volatile(
        "push {r3,lr}\n"
        "movs r3,r4\n"
        "bl sgp_borsa_attr_cache\n"
        "pop {r3,pc}\n"
    );
}
