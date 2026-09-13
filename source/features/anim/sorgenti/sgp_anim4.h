/* Sacred Gold Plus 1.2 — `sgp.anim` **v4**: contratto del blob del moto di
 * attesa in lotta. GPL-3.0-or-later.
 *
 * Discende da `SGP-1.2-ANIM-B-03/sorgenti/sgp_anim2b.h` (fase 2b, quella
 * applicata in ROM, più la tavola v3 di `SGP-1.2-RIFINITURA-01`): **stessa
 * pianta, stessi offset, stesse tabelle, stesso gancio del task**. Il blocco
 * resta 1024 B a 0x023D8B00 e il canarino resta a +0x2F0.
 *
 * ---------------------------------------------------------------------------
 * CHE COSA CAMBIA NELLA v4, e perché — tre difetti misurati, non ipotizzati
 * ---------------------------------------------------------------------------
 *
 * D1 — **stato sporco alla sospensione**. Il ciclo di vita del moto è tutto
 *      del gioco: `ov12_02261FD4` avvia il task (UN solo sito di chiamata,
 *      0x0225DC8A, dentro la selezione del comando del giocatore) e
 *      `ov12_02262014` lo ferma (NOVE siti). Quando lo ferma, il gioco
 *      ripulisce **solo** lo `yOffset`:
 *
 *          0x02262022  bl SysTask_Destroy
 *          0x0226202C  [od+0x198] = 0        (task)
 *          0x02262030  [od+0x19C] = 0        (degrees)
 *          0x02262032  ldr r0,[r4,#0x20]     <-- pokepic
 *          0x02262034  movs r1,#4            <-- POKEPIC_YOFFSET
 *          0x02262036  bl Pokepic_SetAttr    (r2 è già 0)
 *          0x0226203A  pop {r4,pc}
 *
 *      La scala affine e lo scostamento dell'ombra che scriviamo NOI restano
 *      addosso allo sprite. **Misurato** su una lotta selvatica giocata
 *      (Typhlosion Lv49 contro Kakuna, ROM 1.2 IT, interruttore acceso):
 *      alla fermata `affineW/H` valevano 257/255 e `shadow.yOffset` −1, e
 *      restavano tali per **1235 fotogrammi** (20,6 s) — tutta l'animazione
 *      della mossa, il KO, la schermata dell'esperienza e la fine della lotta
 *      — fino alla distruzione del lottatore. Con la posa è peggio: se la
 *      fermata cade dentro un battito di ciglia, il Pokémon resta **con gli
 *      occhi chiusi** finché qualcuno non fa ripartire un'animazione.
 *
 *      **Cura**: un secondo gancio, di 4 byte, sulla CODA di `ov12_02262014`
 *      (0x02262032). Diventa `bl sgp_idle_stop`; il nostro codice rimette a
 *      posto quello che ha scritto, libera la voce del lottatore, e **rimette
 *      r0/r1/r2 esattamente come le due istruzioni sostituite**, così le due
 *      istruzioni che seguono (la `Pokepic_SetAttr(pic, YOFFSET, 0)` del gioco
 *      e il `pop`) girano identiche. A interruttore spento non esiste nessuna
 *      voce di lottatore, quindi la pulizia **non tocca un solo byte** della
 *      memoria del gioco: la spegnibilità resta byte-identica.
 *
 * D2 — **le voci per lottatore non venivano mai liberate**. `slot_per()` le
 *      creava e basta: `od` restava impresso per sempre, `usato` non tornava
 *      mai a 0. Conseguenze: (a) in una seconda lotta la voce veniva riusata
 *      con `base76`, `rng` e lo stato del battito della lotta precedente — e
 *      `base76` è il valore a riposo dell'ombra, che dipende dalla SPECIE;
 *      (b) con quattro voci già occupate da lottatori morti, quattro lottatori
 *      vivi (lotta doppia) finivano nello sfratto a giro, rubandosi la voce a
 *      vicenda a ogni esecuzione. La pulizia di D1 libera la voce nel punto
 *      esatto in cui il gioco dichiara finito quel lottatore: deterministico,
 *      non euristico.
 *
 * D3 — **l'interruttore si leggeva senza guardia**. È la segnalazione **S9**
 *      di `SGP-1.2-QUALITA-NATIVO-01`: `anim_idle2b.c` leggeva 0x023D8716 alla
 *      cieca, senza controllare né la guardia `0x5A` del blocco di D1 né
 *      `load_status`. Oggi è innocuo perché `anim` è spento di default, ma
 *      diventa sbagliato il giorno in cui i default 1.2 includessero `anim`
 *      (un chunk RIFIUTATO farebbe animare lo stesso). La v4 usa
 *      `sgp_chunk_opzione()` di `sgp_chunk.h`, l'accessore unico che tutti i
 *      consumatori devono usare. Costa una manciata di byte.
 *
 * ---------------------------------------------------------------------------
 * CHE COSA NON CAMBIA
 * ---------------------------------------------------------------------------
 * Il task vanilla resta la PRIMA cosa che si esegue; l'astensione totale
 * quando `animActive != 0`; il divieto di scrivere `xOffset`; la finestra
 * stretta sulla scala; la tavola v3 (seno lisciato, monotona a passi di 1 px);
 * i parametri per classe di taglia; il battito pseudo-casuale; lo sfasamento
 * per slot. Nessuna rotazione (10c §3.1 idea 5: nearest sampling + rotazione =
 * contorni sdoppiati).
 *
 * Un'unica unità di traduzione (`anim_blob4.c` include questo, `sgp_chunk.h` e
 * `anim_idle4.c`): `tools/carica_text.py` vieta simboli esterni, rilocazioni
 * diverse dalla `BL` Thumb interna e qualunque sezione allocata oltre `.text`.
 */
#ifndef SGP_ANIM4_H
#define SGP_ANIM4_H

/* `sgp_chunk.h` porta i typedef u8/u16/u32/s16/s32, la pianta del chunk di D1
 * e l'accessore unico `sgp_chunk_opzione()`. È la fonte unica: non si
 * riscrivono qui né gli indirizzi né le regole di lettura. */
#include "sgp_chunk.h"

typedef signed char s8;

/* ------------------------------------------------------------------ */
/* Indirizzi del gioco (invariati dalla fase 1/2, letti dal binario).   */
/* ------------------------------------------------------------------ */
#define SGP_POKEPIC_SETATTR 0x020087A5u /* void f(Pokepic*, int attr, int val) */
#define SGP_VANILLA_TASK 0x0226203Du    /* ov12_0226203C, idle bounce vanilla  */

/* Attributi di Pokepic_SetAttr (enum `PokepicAttr`, pret `include/pokepic.h`;
 * riletti anche nella tavola di salto 0x020087B6 del nostro binario). */
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
#define PP_SHADOW_FLAGS 0x6C /* u16 `PokepicShadow`, letto da DrawAll:
                              *  bit0-1 = palSlot (0 => ombra NON disegnata)
                              *  bit2   = shouldAdjustX
                              *  bit3   = shouldAdjustY (l'ombra segue yOffset)
                              *  bit4   = isAffine
                              *  bit5-6 = size, 0..3 (0 => ombra NON disegnata);
                              *           viene dai dati di lotta della specie
                              *           (ov012 0x02261358, attributo 46) ed è
                              *           la nostra misura di TAGLIA            */
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

/* Campo `anim` del chunk di D1: la fonte di verità dell'abilitazione.
 * L'indirizzo NON è cablato: discende dalla pianta di `sgp_chunk.h`
 * (0x023D8710 + 0x6 = 0x023D8716) — se qualcuno sposta il chunk, si sposta
 * anche questo invece di leggere memoria altrui. */
#define SGP_CHUNK_ANIM_ADDR (SGP_CHUNK_ADDR + SGP_C_ANIM)

/* ------------------------------------------------------------------ */
/* Tabelle in riserva, a SGP_ANIM2_TAB_ADDR.                           */
/*   +0x00  tab_u[18]  s8   seno lisciato x 16 (unita' = 16), 32 B      */
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
/* Stato globale, 64 B a SGP_ANIM2_STATE_ADDR. Layout IDENTICO alla     */
/* fase 2b: la v4 usa due parole della coda riservata come contatori    */
/* diagnostici (QUALITA-NATIVO-01 §6: senza contatori una prova verde   */
/* non prova nulla).                                                    */
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
    u32 stop_visti;/* +0x20 v4: quante volte il gancio di coda e' scattato */
    u32 puliti;    /* +0x24 v4: quante voci ha ripulito e liberato */
    u32 coda[6];   /* +0x28 riservato */
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
void sgp_idle_stop(void);
void sgp_pulisci(void *data);

#endif /* SGP_ANIM4_H */
