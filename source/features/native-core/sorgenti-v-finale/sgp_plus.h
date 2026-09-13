/* Sacred Gold Plus 1.2a — difficoltà PLUS. Interfaccia comune.
 * GPL-3.0-or-later.
 *
 * Lo stato a runtime e il chunk stanno in `sgp_chunk.h` (fonte unica).
 * Qui restano le sole due tabelle precalcolate e le firme del blob.
 *
 * Pianta del blocco `sgp.plus` (2048 B a 0x023D8100, MAPPA-RISERVA-ARM9.json):
 *   +0x000 blob Thumb · +0x400 tab_trainer 256 B · +0x500 tab_wild 256 B
 *   +0x600 stato 32 B · +0x620 canarino 16 B · +0x630 blob del salvataggio
 */
#ifndef SGP_PLUS_H
#define SGP_PLUS_H

#include "sgp_chunk.h"

/* Le due tabelle precalcolate, 256 voci indicizzate da un byte (indirizzi
 * derivati da SGP_PLUS_BASE in sgp_chunk.h):
 *   TRN  A(M) = min(cap, R(M, p_plus(M)))
 *   WLD  max(B, min(cap, R(B, p_wild(B)))) */
#define SGP_TAB_TRN ((const u8 *)SGP_TAB_TRAINER_ADDR)
#define SGP_TAB_WLD ((const u8 *)SGP_TAB_WILD_ADDR)

#endif /* SGP_PLUS_H */
