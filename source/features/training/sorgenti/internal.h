#ifndef SGP_TRAIN_INTERNAL_H
#define SGP_TRAIN_INTERNAL_H
#include "training.h"
/* Volatile byte access prevents freestanding compilers from synthesizing libc
 * calls. These bounded copies also work across host/ARM struct alignment. */
static inline void sgp_train_copy(void *to, const void *from, unsigned length)
{
    volatile sgp_train_u8 *d = (volatile sgp_train_u8 *)to;
    const volatile sgp_train_u8 *s = (const volatile sgp_train_u8 *)from;
    while (length--) *d++ = *s++;
}
static inline void sgp_train_zero(void *to, unsigned length)
{
    volatile sgp_train_u8 *d = (volatile sgp_train_u8 *)to;
    while (length--) *d++ = 0;
}
static inline int sgp_train_is_zero(const void *data, unsigned length)
{
    const sgp_train_u8 *p = (const sgp_train_u8 *)data;
    while (length--) if (*p++) return 0;
    return 1;
}
#endif
