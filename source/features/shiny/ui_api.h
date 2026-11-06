#ifndef SGP_SHINY_UI_API_H
#define SGP_SHINY_UI_API_H
/* Successor discovery wire ABI. ABI2 in api.h remains exactly 152 bytes.
 * Addresses below are proposed config-tail ownership, not an installation. */
#include "api.h"
#define SGP_SETTINGS_UI_DESCRIPTOR 0x023CB1A0u
#define SGP_SETTINGS_UI_GENERATION 0x023CB1F0u
#define SGP_SETTINGS_UI_MAGIC 0x31544955u /* UIT1 */
#define SGP_SETTINGS_UI_ABI 1u
#define SGP_SETTINGS_UI_READONLY_PEEK 1u
#define SGP_SETTINGS_UI_REJECT_ATOMIC 2u
#define SGP_SETTINGS_UI_GENERATION_MAGIC 0x31475554u /* TUG1 */
/* Native Settings allocation prefix; Init/Exit own these private fields. */
#define SGP_SETTINGS_UI_OPTIONS_OFFSET 0x24u
#define SGP_SETTINGS_UI_APP_GENERATION_OFFSET 0x28u
#define SGP_SETTINGS_UI_APP_MAGIC_OFFSET 0x2Cu
#define SGP_SETTINGS_UI_APP_PREFIX_BYTES 0x30u
#define SGP_SETTINGS_UI_APP_MAGIC 0x31495553u /* SUI1 */
/* Audited native SYSTEM stack slice: excludes DTCM static data and IRQ stack.
 * Successor installer must guard crt0 SYSTEM/IRQ bounds in both languages. */
#define SGP_SETTINGS_UI_STACK_LOW 0x027E0080u
#define SGP_SETTINGS_UI_STACK_HIGH 0x027E3780u
/* Audited OS_GetInitArenaLo(ARM9) and conservative resident-owner ceiling.
 * The installer must guard the arena literal; this grants no code allocation. */
#define SGP_SETTINGS_UI_HEAP_LOW 0x0226EC40u
#define SGP_SETTINGS_UI_HEAP_HIGH 0x023C0000u
typedef struct { SgpShinyU32 words[13]; } SgpTrainingUiProof;
typedef struct { SgpShinyU32 words[38]; } SgpSettingsShinyToken;
typedef SgpShinyU32 (*SgpSettingsFinalCheck)(void *context);
/* Wire addresses rather than host-sized function/data pointers. */
typedef struct {
    SgpShinyU16 abi, bytes;
    SgpShinyU32 check, context;
} SgpSettingsCommitGate;
typedef struct {
    SgpShinyU32 magic;
    SgpShinyU16 abi, bytes, token_bytes, training_proof_bytes;
    SgpShinyU32 flags;
    SgpShinyU32 shiny_peek, shiny_prepare, shiny_commit;
    SgpShinyU32 training_peek, training_validate, training_store;
    SgpShinyU32 load_wrapper, bind_wrapper;
    SgpShinyU32 original_training_load, original_training_bind, original_storage_ready;
    SgpShinyU32 generation_state, reserved[4];
} SgpSettingsUiDescriptor;
typedef struct {
    SgpShinyU32 magic, epoch, save_identity, reserved;
} SgpTrainingUiGeneration;
_Static_assert(sizeof(SgpShinyU8)==1&&sizeof(SgpShinyU16)==2,"wire integer widths");
_Static_assert(sizeof(SgpTrainingUiProof)==52,"training proof ABI");
_Static_assert(sizeof(SgpSettingsShinyToken)==152,"settings token ABI");
_Static_assert(sizeof(SgpSettingsCommitGate)==12,"commit gate wire ABI");
_Static_assert(__builtin_offsetof(SgpSettingsCommitGate,check)==4,"commit gate address");
_Static_assert(sizeof(SgpSettingsUiDescriptor)==80,"settings descriptor ABI");
_Static_assert(__builtin_offsetof(SgpSettingsUiDescriptor,training_peek)==28,"training capabilities");
_Static_assert(__builtin_offsetof(SgpSettingsUiDescriptor,original_training_load)==48,"original capabilities");
_Static_assert(__builtin_offsetof(SgpSettingsUiDescriptor,generation_state)==60,"generation capability");
_Static_assert(sizeof(SgpTrainingUiGeneration)==16,"generation sidecar ABI");
/* Status returns use SgpShinyStatus: zero is OK, unlike legacy boolean APIs.
 * All buffers must be four-byte aligned, exact-size, disjoint native-heap or bounded SYSTEM-stack buffers.
 * Peek/validate never initialize, admit, write flash or modify owner state.
 * Store is trusted and infallible: caller MUST validate under the same lock. */
SgpShinyU32 training_ui_peek(void *fs, SgpShinySaved *saved, SgpTrainingUiProof *proof);
SgpShinyU32 training_ui_validate(void *fs, const SgpTrainingUiProof *proof,
                               const SgpShinySaved *next, SgpShinyU32 inspect_storage);
void training_ui_store(const SgpTrainingUiProof *proof, const SgpShinySaved *next);
int training_ui_load(void *save);
void training_ui_bind(void *save, SgpShinyU32 fresh);
SgpShinyU32 sgp_shiny_ui_peek(void *app, SgpShinySnapshot *out);
SgpShinyU32 sgp_shiny_ui_prepare(void *app, const SgpShinySnapshot *opened,
                               const SgpShinyDraft *draft, SgpSettingsShinyToken *out);
SgpShinyU32 sgp_shiny_ui_commit(void *app, SgpSettingsShinyToken *token,
                              const SgpSettingsCommitGate *gate);
#endif
