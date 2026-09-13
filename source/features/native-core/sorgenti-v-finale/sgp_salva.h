/* Sacred Gold Plus 1.2a — chunk di salvataggio della 1.2 (cantiere D1).
 * GPL-3.0-or-later.
 *
 * Il formato pubblico del chunk e lo stato a runtime stanno in `sgp_chunk.h`
 * (fonte unica). Qui restano solo le cose che riguardano il SALVATAGGIO: dove
 * stanno i byte sulla cartuccia, il footer e le funzioni del gioco.
 *
 * Pianta (v-finale, misurata sulla ROM spedita — M3 della revisione R2: il
 * commento diceva ancora +0x630/460 B, cioè la posizione v2, e con quei numeri
 * i due blob di sgp.plus si sovrapponevano sulla carta):
 *   sgp.plus +0x000 = 0x023D8100, 256 B   blob PLUS
 *   sgp.plus +0x120 = 0x023D8220, 500 B   QUESTO codice (era +0x630 nella v2)
 *   sgp.plus +0x630 = 0x023D8730, 464 B   a zero: qui viveva la v2 di questo blob
 *   sgp.salvataggio 0x023D8F00, 256 B     +0x00 buffer 32 B · +0xF0 canarino 16 B
 * Il registro unico degli indirizzi resta `source/docs/arm9-reserve-map.json`.
 */
#ifndef SGP_SALVA_H
#define SGP_SALVA_H

#include "sgp_chunk.h"

#ifndef SGP_BUF_ADDR               /* buffer del chunk, 32 B: 16 payload + 16 footer */
#define SGP_BUF_ADDR 0x023D8F00u
#endif

/* --- funzioni del gioco, lette dal binario (identiche EN/IT) -------------- */
/* Il bit 0 è il bit Thumb, non un indirizzo dispari. */
#ifndef SGP_WRITE_BACKUP
#define SGP_WRITE_BACKUP 0x02028759u        /* scrittura bloccante: (offset, buf, len) */
#endif
#ifndef SGP_READ_BACKUP
#define SGP_READ_BACKUP 0x0202877Du         /* lettura bloccante:   (offset, buf, len) */
#endif
#ifndef SGP_CRC16
#define SGP_CRC16 0x0201FF99u               /* GF_CalcCRC16 = MATH_CalcCRC16CCITT */
#endif
#ifndef SGP_ORIG_LOAD
#define SGP_ORIG_LOAD 0x020277D5u           /* `SaveData_LoadAll`, la chiamata originale di L0 */
#endif
#ifndef SGP_ORIG_SAVE
#define SGP_ORIG_SAVE 0x02027DB5u           /* la chiamata originale di S0 */
#endif

#define CHIAMA_WB  ((int (*)(u32, const void *, u32))SGP_WRITE_BACKUP)
#define CHIAMA_RB  ((int (*)(u32, void *, u32))SGP_READ_BACKUP)
#define CHIAMA_CRC ((u16 (*)(const void *, u32))SGP_CRC16)
#define CHIAMA_ORIG_LOAD ((u32 (*)(void *))SGP_ORIG_LOAD)
#define CHIAMA_ORIG_SAVE ((u32 (*)(void *))SGP_ORIG_SAVE)

/* SAVE_PAGE_MAX = 35, le sei voci di gExtraSaveChunkHeaders si fermano al 46, le
 * due copie del salvataggio distano 64 settori: 47..63 e 111..127 sono liberi.
 * MISURATO su sei salvataggi reali, tutti 0xFF (prove/settori-liberi.json). */
#define SGP_SETTORE_A 0x0002F000u          /* settore 47  */
#define SGP_SETTORE_B 0x0006F000u          /* settore 111 */

/* Il footer ha la forma del gioco (`SaveArrayFooter`) e il suo stesso CRC, ma un
 * magic DIVERSO da 0x20060623: un nostro settore non può mai essere scambiato
 * per un chunk del gioco, né viceversa. Il CRC copre `size + offsetof(crc)`. */
typedef struct SgpFooter {
    u32 magic;          /* 'SGP2' = 0x32504753 */
    u32 saveno;
    u32 size;           /* = 16 */
    u16 idx;            /* = 6: l'id che avrebbe avuto la settima voce */
    u16 crc;
} SgpFooter;            /* sizeof == 16 */

#define SGP_MAGIC_FOOTER 0x32504753u
#define SGP_IDX 6u
#define SGP_PAYLOAD 16u
#define SGP_CRC_LEN (SGP_PAYLOAD + 14u)                    /* = offsetof(SgpFooter, crc) */
#define SGP_RECORD  (SGP_PAYLOAD + (u32)sizeof(SgpFooter))

#define SGP_BUF ((u8 *)SGP_BUF_ADDR)

#endif /* SGP_SALVA_H */
