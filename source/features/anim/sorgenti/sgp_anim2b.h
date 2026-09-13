/* SGP-1.2-ANIM-B-02 — FASE 2b: contratto del blob "anim_idle2b".
 *
 * Copiato da `sgp_anim2.h` (fase 2/2a, invariato da ANIM-B-01 fase 1b):
 * STESSO layout, STESSI offset, STESSA struttura di stato e di slot. Il
 * blocco `sgp.anim` resta 1024 B a 0x023D8B00 (PRENOTAZIONI-RISERVA.md),
 * canarino a +0x2F0.
 *
 * UNICA differenza voluta (mandato 02b): l'abilitazione del task non e' piu'
 * un byte scritto dall'iniettore in QUESTO blocco (`SgpAnim2State.flags`
 * come INGRESSO), ma il campo `anim` del chunk di salvataggio di PLUS-03
 * (`SGP-1.2-PLUS-03/CONTRATTO-CHUNK.md` §2): un byte a 0x023D8710+0x6 =
 * 0x023D8716, nella copia in RAM del chunk che il gancio L0 di D1 scrive
 * all'avvio (`SaveData_Init`, 0x020271F8) e che resta corretta per tutta la
 * lotta (il task idle gira SOLO in lotta, ben dopo il boot).
 *
 * Percio' `SgpAnim2State.flags` (+0x00) cambia RUOLO, non FORMATO: resta
 * l'ultimo byte all'offset 0 dello stato di 64 B, ma adesso e' una
 * DIAGNOSTICA che rispecchia l'ultimo valore applicato (0 o SGP_F_TUTTI),
 * non un ingresso che l'iniettore o uno script di prova possano scrivere una
 * volta e lasciare li': la task lo ricalcola dal chunk a OGNI esecuzione.
 * `tools/rileggi_anim.py` (L4) continua a funzionare senza modifiche: legge
 * lo stesso offset e riporta lo stesso significato ("flags applicati ora").
 *
 * CONTRATTO-CHUNK.md §4: "chunk assente ⇒ tutti i byte del chunk (compreso
 * `anim`) a 0 ⇒ byte-identico alla 1.1". Questo header non distingue quindi
 * "assente" da "presente con anim=0": sono la STESSA lettura (0x023D8716==0),
 * esattamente come vuole il contratto — nessun controllo aggiuntivo su
 * `load_status` e' necessario ne' voluto qui (lo fa gia' D1 scrivendo quel
 * byte a 0 nei due casi).
 *
 * Resta identico alla fase 2/2a: il gancio (letterale ov012 0x0226200C),
 * l'ABI, la chiamata al task vanilla come prima istruzione utile,
 * l'astensione totale quando animActive != 0, il divieto di scrivere
 * xOffset, la finestra sulla scala.
 *
 * Un'unica unita' di traduzione (anim_blob2b.c include questo e
 * anim_idle2b.c): `tools/carica_text.py` vieta simboli esterni, rilocazioni
 * diverse dalla BL Thumb interna e qualunque sezione allocata oltre `.text`.
 */
#ifndef SGP_ANIM2B_H
#define SGP_ANIM2B_H

typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef signed int s32;

/* ------------------------------------------------------------------ */
/* Indirizzi del gioco (invariati dalla fase 1/2, letti dal binario).   */
/* ------------------------------------------------------------------ */
#define SGP_POKEPIC_SETATTR 0x020087A5u /* void f(Pokepic*, int attr, int val) */
#define SGP_VANILLA_TASK 0x0226203Du    /* ov12_0226203C, idle bounce vanilla  */

/* Attributi di Pokepic_SetAttr, riletti nella tavola di salto 0x020087B6. */
#define POKEPIC_XOFFSET 3     /* +0x2C — MAI scritto (conteso con l'interprete) */
#define POKEPIC_YOFFSET 4     /* +0x2E */
#define POKEPIC_AFFINEW 12    /* +0x34 */
#define POKEPIC_AFFINEH 13    /* +0x36 */
#define POKEPIC_SHADOW_YOFF 22 /* +0x76 — handler 0x02008896: strh r2,[r0+0x76] */
#define POKEPIC_ANIM_STEP 38  /* +0x5B */

/* OpponentData (ov012): il `data` del task. */
#define OD_POKEPIC 0x20
#define OD_TASK 0x198
#define OD_DEGREES 0x19C

/* Pokepic (ARM9, 0xAC B). */
#define PP_XOFFSET 0x2C
#define PP_YOFFSET 0x2E
#define PP_AFFINEW 0x34
#define PP_AFFINEH 0x36
#define PP_ANIMACTIVE 0x58
#define PP_ANIMSTEP 0x5B
#define PP_SHADOW_FLAGS 0x6C /* u16, letto da DrawAll:
                              *  bit0-1 (attr 42) = lato del lottatore, sceglie
                              *      la cella dello SPRITE (0x020083FC);
                              *  bit2  (attr 43) = ricalcola la X dell'ombra;
                              *  bit3  (attr 44) = ricalcola la Y dell'ombra;
                              *  bit4  (attr 45) = l'ombra segue affineW/H;
                              *  bit5-6 (attr 46) = TAGLIA dell'ombra, sceglie la
                              *      cella dell'OMBRA (0x02008484); viene dai dati
                              *      di lotta della specie (ov012 0x02261358)   */
#define PP_TAGLIA_SHIFT 5    /* bit5-6 di +0x6C: la classe di taglia 0..3 */
#define PP_SHADOW_H 0x6E     /* s8, sottratto SOLO alla Y del corpo         */
#define PP_SHADOW_X 0x70
#define PP_SHADOW_Y 0x72
#define PP_SHADOW_XOFF 0x74
#define PP_SHADOW_YOFF 0x76 /* s16, sommato alla Y dell'ombra              */

#define SGP_FASI 18
#define SGP_SCALA_UNO 0x100
#define SGP_SCALA_FINESTRA 8
#define SGP_SLOT 4

/* ------------------------------------------------------------------ */
/* Bit di `flags`. Zero = comportamento 1.1 esatto.                    */
/* ------------------------------------------------------------------ */
#define SGP_F_RESPIRO 0x01 /* oscillazione verticale (yOffset)                */
#define SGP_F_POSA 0x02    /* battito di ciglia con la posa B                 */
#define SGP_F_SCALA 0x04   /* squash & stretch in controfase (affineW/H)      */
#define SGP_F_OMBRA 0x08   /* ombra ancorata a terra (compensa shadow.yOffset)*/
#define SGP_F_FASE 0x10    /* sfasamento fra i lottatori                      */
#define SGP_F_TAGLIA 0x20  /* ampiezza e scala per taglia (altrimenti classe 1)*/
#define SGP_F_TUTTI 0x3F

/* ------------------------------------------------------------------ */
/* Campo `anim` del chunk di salvataggio di PLUS-03 (fonte di verita' */
/* dell'abilitazione, mandato 02b). CONTRATTO-CHUNK.md §2:            */
/*   base copia in RAM del chunk = 0x023D8710, +0x6 = 0x023D8716.     */
/* Assoluto: non dipende dalla base del blocco sgp.anim. Dominio      */
/* {0,1}; chunk assente => 0 per costruzione di D1 (§4).              */
/* ------------------------------------------------------------------ */
#define SGP_CHUNK_ANIM_ADDR 0x023D8716u

/* ------------------------------------------------------------------ */
/* Tabelle in riserva, a SGP_ANIM2_TAB_ADDR.                           */
/*   +0x00  tab_u[18]  s8   seno x 16 (unita' = 16), 32 B               */
/*   +0x20  par[32]    u8   parametri, 32 B                             */
/* ------------------------------------------------------------------ */
/* Tabelle e stato stanno nella riserva: F0 ha misurato che il gioco non
 * scrive mai in [0x023D8000, 0x023DEB40). Nessun `volatile`: l'unico
 * scrittore siamo noi (e l'iniettore, prima che il task esista). */
#define SGP_TAB_U ((const s8 *)(SGP_ANIM2_TAB_ADDR))
#define SGP_PAR ((const u8 *)(SGP_ANIM2_TAB_ADDR + 0x20))

#define PAR_AMP 0x00      /* 4 B: ampiezza in px per classe di taglia 0..3   */
#define PAR_SCA 0x04      /* 4 B: delta di scala su 0x100 per classe 0..3    */
#define PAR_FASE 0x08     /* 4 B: sfasamento in fasi per slot 0..3           */
#define PAR_BLINK_MIN 0x0C   /* attesa minima fra due battiti, in esecuzioni  */
#define PAR_BLINK_MASK 0x0D  /* maschera dell'attesa casuale aggiunta        */
#define PAR_BLINK_DUR 0x0E   /* durata base del battito (esecuzioni)         */
#define PAR_RARO_OGNI 0x0F   /* dopo quanti battiti comuni ne arriva uno raro */
#define PAR_RARO_PIU 0x10    /* esecuzioni in piu' del battito raro          */

/* ------------------------------------------------------------------ */
/* Stato globale, 64 B a SGP_ANIM2_STATE_ADDR. LAYOUT IDENTICO alla     */
/* fase 2/2a: cambia solo il significato di `flags` (diagnostica, non   */
/* piu' ingresso — vedi commento in cima al file).                      */
/* ------------------------------------------------------------------ */
typedef struct SgpAnim2State {
    u8 flags;      /* +0x00 diagnostica: ultimo valore applicato (0/SGP_F_TUTTI) */
    u8 guard;      /* +0x01 0x5A quando l'iniettore l'ha inizializzato */
    u8 ampiezza;   /* +0x02 diagnostica: ampiezza dichiarata dai parametri */
    u8 rr;         /* +0x03 cursore di sfratto delle voci per lottatore */
    u32 hits;      /* +0x04 esecuzioni del task */
    u32 hits_on;   /* +0x08 esecuzioni che hanno scritto */
    u32 hits_busy; /* +0x0C esecuzioni astenute perche' animActive != 0 */
    s16 last_y;    /* +0x10 ultimo yOffset scritto */
    u8 last_step;  /* +0x12 ultima posa scritta */
    u8 last_idx;   /* +0x13 ultima fase 0..17 (gia' sfasata) */
    u32 blinks;    /* +0x14 battiti di ciglia iniziati */
    u32 rari;      /* +0x18 battiti "rari" iniziati */
    s16 last_s76;  /* +0x1C ultimo shadow.yOffset scritto */
    u8 last_cls;   /* +0x1E ultima classe di taglia letta */
    u8 last_slot;  /* +0x1F ultimo slot usato */
    u32 coda[8];   /* +0x20 riservato */
} SgpAnim2State;

/* Una voce per lottatore, 32 B. Quattro voci a SGP_ANIM2_SLOT_ADDR. */
typedef struct SgpAnim2Slot {
    u32 od;       /* +0x00 OpponentData* (0 = voce libera) */
    u32 pic;      /* +0x04 Pokepic* visto l'ultima volta */
    u32 rng;      /* +0x08 stato dell'LCG */
    s16 base76;   /* +0x0C shadow.yOffset a riposo, catturato */
    s16 last76;   /* +0x0E shadow.yOffset che abbiamo scritto noi */
    u8 blink_left;/* +0x10 esecuzioni restanti con la posa B */
    u8 blink_wait;/* +0x11 esecuzioni all'occhio chiuso successivo */
    u8 blink_cnt; /* +0x12 battiti comuni dall'ultimo raro */
    u8 usato;     /* +0x13 1 se la voce e' occupata */
    u32 coda[3];  /* +0x14 riservato */
} SgpAnim2Slot;

#ifndef SGP_ANIM2_STATE_ADDR
#error "SGP_ANIM2_STATE_ADDR non definito"
#endif
#ifndef SGP_ANIM2_TAB_ADDR
#error "SGP_ANIM2_TAB_ADDR non definito"
#endif
#ifndef SGP_ANIM2_SLOT_ADDR
#error "SGP_ANIM2_SLOT_ADDR non definito"
#endif

#define SGP_STATO2 ((SgpAnim2State *)SGP_ANIM2_STATE_ADDR)
#define SGP_SLOTS ((SgpAnim2Slot *)SGP_ANIM2_SLOT_ADDR)

void sgp_idle_task2(void *task, void *data);

#endif /* SGP_ANIM2B_H */
