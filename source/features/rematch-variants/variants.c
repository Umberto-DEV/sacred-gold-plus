#include "variants.h"

static rv_u32 rv_hash(const rv_u8 *bytes, rv_u32 size) {
    rv_u32 hash = 2166136261u;
    while (size--) hash = (hash ^ *bytes++) * 16777619u;
    return hash;
}

static rv_u32 rv_half(const rv_u8 *p) { return (rv_u32)p[0] | ((rv_u32)p[1] << 8); }

/* Offset of party n (0 baseline, 1 A, 2 B) of descriptor d, in descriptor order. */
static rv_u32 rv_offset(const RvTrainer *table, rv_u32 n) {
    const RvTrainer *d = table + n / 3u;
    return n % 3u == 0 ? d->base : n % 3u == 1 ? d->a : d->b;
}

rv_u32 rematch_select(rv_u32 seed, rv_u32 trainer) {
    return (seed ^ (seed >> 16) ^ trainer) & 1u;
}

/* The six spans of one descriptor (baseline, A, B) and every other descriptor
 * must lie inside the data area and be pairwise disjoint. */
static int rv_layout_ok(const RvHeader *config) {
    const RvTrainer *table = (const RvTrainer *)(config + 1);
    rv_u32 first = sizeof(RvHeader) + config->trainers * sizeof(RvTrainer);
    rv_u32 total = config->trainers * 3u, i, j;
    for (i = 0; i < total; i++) {
        rv_u32 a = rv_offset(table, i);
        if (a < first || a > config->bytes - RV_PARTY) return 0;
        for (j = 0; j < i; j++) {
            rv_u32 b = rv_offset(table, j);
            if (a < b + RV_PARTY && b < a + RV_PARTY) return 0;
        }
    }
    for (i = 0; i < config->trainers; i++) {
        if (table[i].reserved) return 0;
        for (j = 0; j < i; j++)
            if (table[j].trainer == table[i].trainer) return 0;
    }
    return 1;
}

/* Variant members must be plausible, keep the baseline levels, IV byte and
 * capsule, and may drop the gender/ability override only when the species changed. */
static int rv_party_ok(const rv_u8 *party, const rv_u8 *base) {
    rv_u32 i, j, k;
    for (i = 0; i < 6; i++) {
        const rv_u8 *m = party + i * RV_SLOT, *b = base + i * RV_SLOT;
        rv_u32 word = rv_half(m + 4), species = word & 0x3FFu;
        if (m[0] != b[0] || rv_half(m + 2) != rv_half(b + 2) || rv_half(m + 16) != rv_half(b + 16)) return 0;
        if (species < 1u || species > RV_SPECIES_MAX || (word >> 10)) return 0;
        if (word == rv_half(b + 4) ? m[1] != b[1] : m[1] != 0) return 0;
        if (rv_half(m + 6) > RV_ITEM_MAX) return 0;
        for (j = 0; j < 4; j++) {
            rv_u32 move = rv_half(m + 8 + j * 2);
            if (move < 1u || move > RV_MOVE_MAX) return 0;
            for (k = 0; k < j; k++)
                if (move == rv_half(m + 8 + k * 2)) return 0;
        }
        for (j = 0; j < i; j++)
            if (word == rv_half(party + j * RV_SLOT + 4)) return 0;
    }
    return 1;
}

int rematch_apply(rv_u8 *buffer, rv_u32 trainer, rv_u32 type_count, rv_u32 plus,
                  rv_u32 seed, const void *config, rv_u32 config_bytes) {
    const RvHeader *head = (const RvHeader *)config;
    const RvTrainer *entry = 0;
    const rv_u8 *image = (const rv_u8 *)config, *base, *chosen;
    rv_u32 i, selected;
    if (!buffer || !config || (((rv_uptr)config) & 3u) || plus != 1u || type_count != RV_TYPE_COUNT ||
        config_bytes < sizeof(RvHeader) || head->magic != RV_MAGIC || head->bytes > config_bytes ||
        head->reserved || head->trainers < 1u || head->trainers > RV_MAX_TRAINERS ||
        head->bytes < sizeof(RvHeader) + head->trainers * sizeof(RvTrainer) + RV_PARTY * 3u * head->trainers)
        return 0;
    if (!rv_layout_ok(head)) return 0;
    for (i = 0; i < head->trainers; i++)
        if (((const RvTrainer *)(head + 1))[i].trainer == trainer) entry = (const RvTrainer *)(head + 1) + i;
    if (!entry || entry->type_count != type_count) return 0;
    if ((rv_uptr)buffer < (rv_uptr)image + head->bytes && (rv_uptr)buffer + RV_PARTY > (rv_uptr)image) return 0;
    base = image + entry->base;
    {
        const rv_u8 *a = image + entry->a, *b = image + entry->b;
        /* The whole descriptor must be sound whichever variant is selected: a
         * damaged unselected variant would otherwise surface only intermittently. */
        if (rv_hash(base, RV_PARTY) != entry->base_hash || rv_hash(a, RV_PARTY) != entry->a_hash ||
            rv_hash(b, RV_PARTY) != entry->b_hash || entry->base_hash == entry->a_hash ||
            entry->base_hash == entry->b_hash || entry->a_hash == entry->b_hash ||
            !rv_party_ok(a, base) || !rv_party_ok(b, base)) return 0;
        selected = rematch_select(seed, trainer);
        chosen = selected ? b : a;
    }
    for (i = 0; i < RV_PARTY; i++)
        if (buffer[i] != base[i]) return 0;
    for (i = 0; i < RV_PARTY; i++) buffer[i] = chosen[i];
    return 1 + (int)selected;
}
