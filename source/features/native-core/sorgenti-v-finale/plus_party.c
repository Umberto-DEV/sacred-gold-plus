/* Sacred Gold Plus 1.2a — difficoltà PLUS sulla squadra dell'allenatore.
 * GPL-3.0-or-later.
 *
 * Regola (doc 13 §2.2):
 *     p_plus(M) = min(12, 6 + M/10)
 *     R(B, p)   = (B*(100+p) + 50) / 100
 *     A         = min(cap, R(M, p_plus(M)))          [tabella SGP_TAB_TRN]
 *     L_i       = max(B_i, A − (M − B_i))
 * M è il massimo dei livelli BASE del gruppo. Nessuna divisione a runtime: A(M)
 * è precalcolato sul Mac e vive in una tabella di 256 byte.
 *
 * Il gancio agisce SOLO sul 3° argomento di CreateMon. Seme/PID e IV sono già
 * calcolati PRIMA del punto di gancio (verificato sul disassemblato: il seme
 * legge `trmon+2` a 0x020736BC, gli IV `trmon+0` a 0x020736F6, entrambi prima
 * di 0x02073718): restano quelli della 1.1.
 */
#include "sgp_plus.h"

/* Stride del record TRPOKE per trainerType (pret `include/trainer_data.h`):
 * bit0 = mosse personalizzate (+8), bit1 = strumento (+2). Un solo chiamante e
 * nessun gancio ci punta: in linea, così non costa una BL e un pool. */
static u32 sgp_trpoke_stride(u32 type)
{
    return 8u + ((type & 1u) << 3) + (type & 2u);
}

__attribute__((used, noinline, section(".text")))
u32 sgp_group_max(const u8 *buf, u32 stride, u32 npoke)
{
    u32 i;
    u32 m = 0u;

    if (!buf || npoke == 0u || npoke > 6u) {
        return 0u;
    }
    for (i = 0u; i < npoke; i++) {
        const u8 *e = buf + i * stride;
        u32 lv = (u32)e[2] | ((u32)e[3] << 8);   /* u16 letto a byte: nessun vincolo di allineamento */
        if (lv > m) {
            m = lv;
        }
    }
    return m;
}

/* base       = livello nativo del membro corrente (u16 letto da trmon+2)
 * buf        = base del buffer TRPOKE del gruppo (BattleSetup: [sp+0x74])
 * type_npoke = (npoke << 8) | trainerType
 */
__attribute__((used, noinline, section(".text")))
u32 sgp_trainer_level(u32 base, const u8 *buf, u32 type_npoke)
{
    SgpStato *s = SGP_STATO;
    u32 m, a, cap;
    s32 l;

    s->hits_trainer++;
    if (!s->active_plus) {
        return base;                          /* PLUS spento: byte-identico alla 1.1 */
    }
    cap = s->cap;
    if (cap == 0u) {
        return base;                          /* stato incoerente: non si tocca niente */
    }
    if (base == 0u || base > 255u) {
        return base;                          /* la tabella ha 256 voci: indice sempre un byte */
    }

    /* nessuna maschera sugli argomenti: `sgp_trpoke_stride` guarda solo i due bit
     * bassi e `sgp_group_max` rifiuta da sé npoke fuori da 1..6. */
    m = sgp_group_max(buf, sgp_trpoke_stride(type_npoke), type_npoke >> 8);
    if (m > 255u || m < base) {
        return base;                          /* M deve stare in un byte e dominare il membro
                                               * (base ≥ 1, quindi m = 0 cade già qui) */
    }

    a = SGP_TAB_TRN[m];
    l = (s32)a - (s32)(m - base);
    if (l > (s32)cap) {
        l = (s32)cap;                         /* rete di sicurezza: la tabella è già
                                               * limitata al cap, ma vive in RAM */
    }
    if (l < (s32)base) {
        l = (s32)base;                        /* pavimento NATIVO: vince sul cap (R-CAP) */
    }
    return (u32)l;
}

/* Trampolina per i quattro siti del livello allenatore.
 * Sostituisce esattamente 4 byte ("ldrh r2,[r2,#2]" ; "adds r0,r6,#0") con un BL.
 *
 * All'ingresso:  r2 = TRPOKE* corrente, r4 = BattleSetup*, r5 = 0x34*partyIndex,
 *                r6 = Pokemon* di lavoro, r1 = species (VIVO), r3 = IV a metà
 *                calcolo (VIVO: `lsls r3,#24` prima, `lsrs r3,#24` dopo il sito),
 *                lr = libero, sp = frame dell'ospite, allineato a 8.
 * All'uscita:    r2 = livello effettivo, r0 = r6, r1/r3/r4..r7 invariati, e i
 *                flag sono quelli di `adds r0,r6,#0` come nell'originale.
 *
 * Si salvano quattro registri (16 B) e non tre, per conservare l'allineamento a
 * 8 della pila alla BL: da qui l'offset 0x74 + 0x10 = 0x84.
 */
__attribute__((naked, used, section(".text")))
void sgp_trainer_hook(void)
{
    __asm__ volatile(
        "ldrh  r2, [r2, #2]\n"        /* B_i, istruzione sostituita */
        "push  {r1, r2, r3, lr}\n"    /* r1 species e r3 IV sono VIVI; sp -= 16 */
        "adds  r0, r2, #0\n"          /* arg0 = B_i */
        "adds  r2, r4, r5\n"          /* &BattleSetup.trainer[partyIndex] */
        "adds  r2, #0x28\n"
        "ldrb  r1, [r2, #3]\n"        /* npoke  (TrainerData +3) */
        "ldrb  r2, [r2, #0]\n"        /* trainerType (TrainerData +0) */
        "lsls  r1, r1, #8\n"
        "orrs  r2, r1\n"              /* arg2 = (npoke << 8) | type */
        "ldr   r1, [sp, #0x84]\n"     /* arg1 = buffer TRPOKE: [sp+0x74] dell'ospite + 16 */
        "bl    sgp_trainer_level\n"
        "pop   {r1, r2, r3}\n"        /* r1 e r3 ripristinati; r2 = B_i, scartato */
        "adds  r2, r0, #0\n"          /* r2 = livello effettivo */
        "adds  r0, r6, #0\n"          /* seconda istruzione sostituita */
        "pop   {pc}\n"
    );
}
