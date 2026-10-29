#include "core.h"

int sgp_shiny_valid(const SgpShinySaved *s)
{
    SgpShinyU32 i;
    if (!s || s->target > 493 || s->chain > 40 || s->mode > 1 ||
        s->initialized > 1 || (!s->initialized && s->rng) ||
        ((!s->target || !s->mode) && s->chain))
        return 0;
    for (i = 0; i < 7; ++i)
        if (s->reserved[i])
            return 0;
    return 1;
}

SgpShinyU32 sgp_shiny_denominator(const SgpShinySaved *s,
                                SgpShinyU32 species, SgpShinyU32 base_only)
{
    if (!sgp_shiny_valid(s) || !species || species > 493 || base_only > 1)
        return 0;
    if (!s->mode)
        return 512;
    if (base_only || !s->target || species != s->target || s->chain < 10)
        return 4096;
    if (s->chain < 20)
        return 2048;
    return s->chain < 40 ? 1024 : 512;
}

int sgp_shiny_select(SgpShinySaved *s, SgpShinyU32 mode, SgpShinyU32 target)
{
    if (!sgp_shiny_valid(s) || mode > 1 || target > 493)
        return -1;
    if (s->mode == mode && s->target == target)
        return 0;
    s->mode = (SgpShinyU8)mode;
    s->target = (SgpShinyU16)target;
    s->chain = 0;
    return 1;
}

int sgp_shiny_complete(SgpShinySaved *s, SgpShinyU32 species, SgpShinyU32 result)
{
    SgpShinyU32 chain = 0;
    if (!sgp_shiny_valid(s) || !species || species > 493 || !result || result > 6)
        return -1;
    if (s->mode && s->target == species && (result == 1 || result == 4))
        chain = s->chain < 40 ? s->chain + 1u : 40u;
    if (chain == s->chain)
        return 0;
    s->chain = (SgpShinyU8)chain;
    return 1;
}

int sgp_shiny_draw(SgpShinySaved *s, SgpShinyU32 native_seed,
                   SgpShinyU32 full_ot, SgpShinyU32 species,
                   SgpShinyU32 base_only, SgpShinyU32 *shiny, SgpShinyU32 *offset)
{
    SgpShinyU32 rng, threshold, denominator;
    denominator = sgp_shiny_denominator(s, species, base_only);
    if (!denominator || !shiny || !offset)
        return 0;
    rng = s->initialized ? s->rng : native_seed ^ full_ot ^ 0x53485031u;
    rng = 1664525u * rng + 1013904223u;
    threshold = 16;
    if (denominator == 512)
        threshold = 128;
    else if (denominator == 1024)
        threshold = 64;
    else if (denominator == 2048)
        threshold = 32;
    s->rng = rng;
    s->initialized = 1;
    /* Exact fraction conditional on a uniform word, not PRNG independence.
       Sharing this word with the bounded offset does not make PIDs uniform. */
    *shiny = (rng >> 16) < threshold;
    *offset = rng & 2047;
    return 1;
}

/* 256^k mod 25 = 1,6,11,16. The sum is at most 34*255=8670.
   For every 0<=n<=8670, floor(n/25) == (n*5243)>>17.
   The complete bounded domain is independently exhausted by the tests. */
static SgpShinyU32 nature(SgpShinyU32 value)
{
    SgpShinyU32 folded = (value & 255) + 6 * ((value >> 8) & 255) +
                        11 * ((value >> 16) & 255) + 16 * (value >> 24);
    return folded - 25 * ((folded * 5243) >> 17);
}

int sgp_shiny_transform(SgpShinyU32 pid, SgpShinyU32 full_ot,
                       SgpShinyU32 shiny, SgpShinyU32 offset, SgpShinyU32 *out)
{
    SgpShinyU32 fold = (full_ot >> 16) ^ (full_ot & 65535);
    SgpShinyU32 index, probe, low, high, candidate, desired, x;
    if (shiny > 1 || offset > 2047 || !out)
        return 0;
    if (!shiny) {
        if (((pid >> 16) ^ (pid & 65535) ^ fold) < 255) {
            x = (pid >> 8) & 255;
            x = x <= 230 ? x + 25 : x - 25;
            pid = (pid & 0xffff00ffu) | (x << 8);
        }
        *out = pid;
        return 1;
    }
    desired = nature(pid);
    for (probe = 0; probe < 157; ++probe) {
        index = (offset + probe) & 2047;
        low = (pid & 255) | ((index >> 3) << 8);
        high = ((low ^ fold) & 0xfff8) | (index & 7);
        candidate = (high << 16) | low;
        if (nature(candidate) == desired) {
            *out = candidate;
            return 1;
        }
    }
    /* A failure cannot reverse the requested lottery or write an output.
       The reduced-domain cyclic-gap proof establishes this is unreachable. */
    return 0;
}
