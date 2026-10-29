#ifndef SGP_STRATEGY_H
#define SGP_STRATEGY_H
typedef unsigned char st_u8;
typedef unsigned short st_u16;
typedef unsigned int st_u32;
typedef struct {
    st_u16 trainer, first_delta;
    st_u32 before_hash, after_hash;
    st_u8 type, count, size, changes;
} StrategyTeam;
typedef struct { st_u16 offset, before, after, reserved; } StrategyMove;
typedef struct { st_u32 magic; st_u16 teams, moves; } StrategyHeader;
st_u32 strategy_hash(const st_u8 *buffer, st_u32 size);
int strategy_apply(st_u8 *buffer, st_u32 trainer, st_u32 type_count,
                   st_u32 plus, const StrategyHeader *config);
#endif
