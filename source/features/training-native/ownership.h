#ifndef SGP_TRAINING_OWNERSHIP_H
#define SGP_TRAINING_OWNERSHIP_H
/* A durable lease is written and read back before either journal is touched.
 * It owns exactly [0,256) and [512,768) in this sector, plus itself at1024.
 * Future formats are never recovered by this version. */
void training_owner_encode(unsigned char out[32]);
int training_owner_valid(const unsigned char bytes[32]);
int training_record_future(const unsigned char bytes[256]);
/* Match the Bag writer: uniform records or its complete/interrupted magic. */
int training_bag_claimable(const unsigned char bytes[452]);
#endif
