/* Sacred Gold Plus 1.2 — W1: scelta dello slot di connessione WFC per servizio.
 * GPL-3.0-or-later. Unità di traduzione UNICA, nessuna `.rodata`.
 *
 * La scelta del server sta nella pagina Opzioni v2, che scrive `wifi_server` nel
 * chunk pubblico (`sgp_chunk.h`): qui non c'è nessuna schermata.
 *
 * Regola di ripiego (mandato Umberto, verificato via melonDS): ogni servizio usa
 * il proprio slot designato SE è configurato nel firmware; altrimenti il PRIMO
 * slot configurato; se nessuno lo è, nessuna forzatura.
 */
#ifndef SGP_WIFI_SLOT4_H
#define SGP_WIFI_SLOT4_H

#include "sgp_chunk.h"

/* ---- indirizzi parametrici (-D) ------------------------------------- */
#ifndef SGP_W1_VENEER_ADDR
#define SGP_W1_VENEER_ADDR 0x023da000u     /* veneer ARM di G2, 24 B */
#endif
#ifndef SGP_W1_VENEER3_ADDR
#define SGP_W1_VENEER3_ADDR 0x023da020u    /* veneer ARM di G3, 28 B */
#endif
#ifndef SGP_W1_DATI_ADDR
#define SGP_W1_DATI_ADDR  0x023da040u      /* dati di runtime, 64 B */
#endif
#ifndef SGP_DWC_LISTA_SITE
#define SGP_DWC_LISTA_SITE 0x021fc150u     /* ov000: DWCi_BuildApSearchList, sito di G2 */
#endif
#ifndef SGP_DWC_CONNECT_SITE
#define SGP_DWC_CONNECT_SITE 0x021ec4a4u   /* ov000: DWC_ConnectInetAsync, sito di G3 */
#endif

/* ---- pianta dello slot WFC (256 B), copiata a offset 0 del work buffer DWC */
#define AP_STRIDE        0x100u
#define AP_STATUS        0xe7u   /* 0 Normal, 1 Aoss, 0xFF NON CONFIGURATO */
#define AP_NON_CONFIG    0xffu

/* ---- work buffer di connessione DWC (0x0D18 B) ---------------------- */
#define DWC_WORK_NIBBLE  0xd0cu  /* bit 0-3: 0 = auto, 1..3 = solo lo slot N */

/* ---- overlay: servono solo a G1, l'unico installatore --------------- */
#define OVL_DWC     0u     /* qui si installano G2 e G3 */
#define OVL_WFC     13u    /* utility impostazioni WFC: azzera ogni forzatura */

/* ---- I SITI DI CHIAMATA, misurati (mappa-connect-*.json, identica EN/IT).
 * Ogni overlay di servizio chiama DWC_ConnectInetAsync da UN SOLO sito, con
 * `blx`: lr = sito + 4 | 1 identifica il servizio. Verificato a runtime per il
 * Dono Segreto: lr = 0x02236B8F. */
#define LR_DONO      0x02236b8fu   /* ov074  Dono Segreto                    */
#define LR_GTS       0x022448b9u   /* ov070  GTS / schermata WFC comune      */
#define LR_CLUB      0x02228cfdu   /* ov039  Club Wi-Fi: lotta e scambio     */
#define LR_WFCSCHERM 0x02239219u   /* ov072  schermata Nintendo WFC          */
#define LR_TORRE     0x021e8d27u   /* ov073  Torre Lotta Wi-Fi               */
#define LR_BACHECA   0x022487f3u   /* ov075  Bacheca Wii                     */
/* ov000 chiama DWC_ConnectInetAsync anche da 0x021E5BB7 e 0x021EC570: NON sono
 * servizi, e G3 li lascia passare senza toccare `pending`. */

/* ---- configurazione W1 (16 B): pianta CONDIVISA con OPZIONI-03, non si tocca.
 * La scelta PERSISTENTE del server vive nel chunk (`wifi_server`, dominio 0..3,
 * proprietario W1); `modo`/`slot_gts` qui sono solo la copia di LAVORO che G3
 * risincronizza a ogni connessione, perché il campo può cambiare dal menu
 * Opzioni durante la partita, senza riavvio. `slot_dono` e `flag` restano nella
 * pianta ma questo blob li ignora: il Dono Segreto usa sempre lo slot 1.
 * Semantica: `wifi_server` 2 o 3 → `modo=1` e quello slot per i servizi online;
 * qualunque altro valore, o chunk non valido → Originale, nessuna forzatura. */
typedef struct SgpW1Stato {
    u8  magic;        /* +0x00  0x57 ('W') */
    u8  versione;     /* +0x01  2 */
    u8  modo;         /* +0x02  0 = Originale (inerte), 1 = per servizio */
    u8  slot_gts;     /* +0x03  0 = automatico, 1..3 = slot scelto in Opzioni */
    u8  slot_dono;    /* +0x04  ignorato da questo blob */
    u8  flag;         /* +0x05  ignorato da questo blob */
    u8  riservato[10];/* +0x06 */
} SgpW1Stato;

/* INVARIATO: è il contratto con OPZIONI-03 (indirizzo in sgp_chunk.h). */
#define SGP_W1S ((volatile SgpW1Stato *)SGP_STATO_WIFI_ADDR)
#define SGP_W1_MAGIC_OK 0x57u   /* stesso nome di sgp_ui.h */
#define SGP_W1_VERSIONE 2u   /* diverso dalla versione 1 di WIFI-01 apposta:
                              * un blob vecchio non deve mai leggere dati nuovi */

/* ---- dati di runtime (64 B, non persistenti) ------------------------ */
typedef struct SgpW1 {
    u8  pending;      /* +0x00  0 = nessuna forzatura, 1..3 = slot da imporre */
    u8  servizio;     /* +0x01  SGP_SERV_* */
    u8  installato;   /* +0x02  b0 = G2 installato, b1 = G3 installato */
    u8  riservato0;   /* +0x03 */
    u32 n_overlay;    /* +0x04  diagnostica */
    u32 n_forzature;  /* +0x08 */
    u32 n_installa;   /* +0x0C */
    u32 ultimo_work;  /* +0x10  ultimo work buffer visto da G2 */
    u32 ultimo_lr;    /* +0x14  ultimo lr visto da G3 */
    u32 n_connect;    /* +0x18  quante volte G3 è passato */
    u32 n_ignoti;     /* +0x1C  lr non in tabella: nessuna forzatura cambiata */
    u32 n_fallback;   /* +0x20  quante volte si è usato il primo slot configurato */
    u8  riservato[32];/* +0x24 */
} SgpW1;

#define SGP_W1 ((volatile SgpW1 *)SGP_W1_DATI_ADDR)

#define SGP_SERV_NESSUNO 0u
#define SGP_SERV_DONO    1u   /* slot fisso 1 */
#define SGP_SERV_ONLINE  2u   /* GTS / lotta / scambio / torre / bacheca */

/* I DNS dei server noti non entrano in nessuna decisione di questo blob: stanno
 * in `SGP-1.2-WIFI-04/RAPPORTO.md` (dati v1b) e li usa la pagina Opzioni. */

void sgp_wfc_on_overlay(u32 overlay_id);   /* G1: installatore */
void sgp_wfc_on_connect(u32 lr);           /* G3: trigger, rilegge il chunk */
void sgp_wfc_nibble(u8 *work);             /* G2: scrive il nibble */
s32  sgp_wfc_slot_configurato(const u8 *work, s32 slot);
s32  sgp_wfc_servizio_da_lr(u32 lr);

#endif /* SGP_WIFI_SLOT4_H */
