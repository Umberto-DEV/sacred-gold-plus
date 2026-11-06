#ifndef SGP_LEVEL_POLICY_H
#define SGP_LEVEL_POLICY_H

typedef unsigned char sgp_level_u8;

typedef struct {
    sgp_level_u8 over100;
    sgp_level_u8 peak;
} sgp_level_state;

enum sgp_level_result {
    SGP_LEVEL_INVALID = 0,
    SGP_LEVEL_UNCHANGED = 1,
    SGP_LEVEL_CHANGED = 2
};

#define SGP_LEVEL_OBS_PERMANENT 1u
#define SGP_LEVEL_OBS_EGG 2u
#define SGP_LEVEL_OBS_MASK 3u

#define SGP_LEVEL_UNLOCK 100u
#define SGP_LEVEL_CLASSIC_CAP 100u
#define SGP_LEVEL_EXTENDED_CAP 150u

int sgp_level_normalize(sgp_level_state in, sgp_level_state *out);
int sgp_level_observe(sgp_level_state in, unsigned level,
                      unsigned flags, sgp_level_state *out);
unsigned sgp_level_cap(sgp_level_state state);

#endif
