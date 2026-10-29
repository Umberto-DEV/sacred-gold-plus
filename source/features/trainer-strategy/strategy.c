#include "strategy.h"
st_u32 strategy_hash(const st_u8 *buffer, st_u32 size) {
    st_u32 hash = 2166136261u;
    while (size--) hash = (hash ^ *buffer++) * 16777619u;
    return hash;
}
int strategy_apply(st_u8 *buffer, st_u32 trainer, st_u32 type_count,
                   st_u32 plus, const StrategyHeader *config) {
    const StrategyTeam *teams;
    const StrategyMove *moves;
    volatile st_u8 copy[108];
    st_u32 i, j;
    if (!buffer || !config || plus != 1 || config->magic != 0x31544753u ||
        config->teams > 16 || config->moves > 32 ||
        8u + config->teams * 16u + config->moves * 8u > 512u) return 0;
    teams = (const StrategyTeam *)(config + 1);
    moves = (const StrategyMove *)(teams + config->teams);
    for (i = 0; i < config->teams; i++) {
        const StrategyTeam *team = teams + i;
        if (team->trainer != trainer) continue;
        /* This reviewed pilot covers six-member custom-move/item teams only.
         * Other formats keep their original data, rather than being guessed. */
        if (team->type != 3 || team->count != 6 || team->size != 108 ||
            type_count != 0x603 || !team->changes ||
            team->first_delta + team->changes > config->moves) return 0;
        if (strategy_hash(buffer, 108) != team->before_hash) return 0;
        for (j = 0; j < 108; j++) copy[j] = buffer[j];
        for (j = 0; j < team->changes; j++) {
            const StrategyMove *move = moves + team->first_delta + j;
            st_u32 offset = move->offset, local = offset;
            while (local >= 18) local -= 18;
            if (move->reserved || offset >= 107 || (offset & 1) ||
                local < 8 || local > 14 || move->after > 467 ||
                (copy[offset] | (copy[offset + 1] << 8)) != move->before) return 0;
            copy[offset] = (st_u8)move->after;
            copy[offset + 1] = (st_u8)(move->after >> 8);
        }
        if (strategy_hash((const st_u8 *)copy, 108) != team->after_hash) return 0;
        for (j = 0; j < 108; j++) buffer[j] = copy[j];
        return team->changes;
    }
    return 0;
}
