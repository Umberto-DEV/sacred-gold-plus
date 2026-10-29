/* 1.3 native visual refinement. Keep the 1.2.5 input/save controllers intact.
 * GPL-3.0-or-later. */
#include "ui_common.c"
#undef G_RIEMPIMENTO_SEL
#undef G_COLORE_SEL
#define G_RIEMPIMENTO_SEL 0x88u
#define G_COLORE_SEL ((1u << 16) | (15u << 8) | 8u)
/* Footer button aligns with the original Confirm/Quit controls. Its temporary
 * window reuses the Plus page's tiles only while that page is closed. */
#undef G_SUGG_Y
#undef G_SUGG_H
#define G_SUGG_Y 21u
#define G_SUGG_H 3u
#include "../options/sorgenti/opzioni_pagina.c"
#include "../options/sorgenti/continua_domanda.c"
