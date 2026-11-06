#ifndef SGP_TRAINING_NATIVE_STATE_H
#define SGP_TRAINING_NATIVE_STATE_H
/* Private runtime layout. Persistent bytes are journal-encoded, never dumped. */
#include "../training/sorgenti/training.h"
#include "transaction.h"
typedef sgp_train_u8 u8; typedef sgp_train_u16 u16; typedef sgp_train_u32 u32;
/* All persistent state is encoded by journal.c, never by dumping this struct. */
typedef struct {
 u32 magic; void *save; u32 enabled,writable,record_status,preview_slot,preview_valid;
 sgp_train_journal journal;
 sgp_training_request request;
 u8 primary[256],mirror[256],record[256];
 u32 shiny_admitted;
} TrainingState;
#endif
