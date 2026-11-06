# AI dopo KO: punteggio e immunità del sostituto (1.3.1)

Stato: modulo e prove pronti (`source/sgp131/ai_scoring.py`, revisione 5); **collegato al builder dopo UI e mosse**; prova Android della composizione ancora da completare.

## Freeze nel calcolo dei tipi — 6 novembre 2026

La candidata precedente poteva bloccare la battaglia durante il ritorno al
menu mosse, con audio fermo su una nota. Il difetto è nel raccordo di
`fairy_ai` a `ov12_02252054`, non nel formato del salvataggio. Il BL Thumb
installato a `0x022520C6` occupa anche `0x022520C8`; il ramo di ritorno del
ciclo a `0x02252138` conservava invece la destinazione retail `0x022520C8`.
Dalla seconda iterazione eseguiva quindi il solo suffisso del BL, usando un
LR estraneo. Il trace del primo errore mostra il salto nei dati a
`0x023D7836` e il successivo data abort nel consumer abilità a `0x0223AB22`.

La correzione cambia soltanto il byte `C6` in `C8` del BNE a `0x02252138`
(`D1C6` → `D1C8`), destinazione `0x022520CC`. Il fondo del ciclo ha già
calcolato `r1 = 3*r4`, anche nel percorso sentinella: il rientro riusa questo
indice e salta entrambe le metà della chiamata iniziale. Payload residente,
ABI, tabella tipi, geometria ROM e layout save restano invariati. Il producer
autentica anche il fondo ciclo completo e il readback verifica il ramo.

La regressione pubblica esegue la funzione nativa completa in Unicorn sulle
V4 EN/IT, senza sostituire il ciclo con stub: dieci casi per lingua coprono
resistenza, debolezza, immunità, neutralità, doppio tipo e Folletto. Prima del
fix tutti i venti casi raggiungono il suffisso del BL; dopo ritornano con
flag attesi, stack e registri preservati e una sola chiamata all'helper.
Un mutante che ripristina il vecchio ramo è rifiutato anche con hash ROM
aggiornato. Una seconda prova usa un core melonDS interprete, senza JIT né
cheat, e una copia raw caricata con Continua: il combattimento naturale
riproduce la stessa catena di errore; modificando solo quel byte nello stesso
stato il menu torna a rispondere. La modifica RAM è una controprova causale,
non una certificazione della build formale o del salvataggio.

Il difetto non dipende da Houndoom o dalla mappa della Lega: è nel ciclo
comune dei controlli IA sui tipi. Sulla candidata IT i BL diretti verso
`0x02252054` sono otto: sette nell'overlay 10 (`0x0221F78E`, `0x0221FA3A`,
`0x0221FAC8`, `0x0221FC44`, `0x0221FCD4`, `0x0222017C`, `0x02220210`) e
uno nella scelta del sostituto dopo KO dell'overlay 12 (`0x022589FC`).
I primi sette appartengono alle routine `ov10_0221F62C`, `ov10_0221F7F0`
e `ov10_02220010`; tutte condividono il callee corretto. La scansione dei
BL decodificati concorda con i call site della decompilazione. Quando si
raggiunge il ciclo difettoso, la seconda iterazione esegue il suffisso:
nessun Pokémon Folletto è necessario per attivarlo. Sono distinti i percorsi
che escono prima del ciclo, per esempio Scontro o Terra contro Levitazione.
Le venti prove attestano il callee comune, non otto incontri naturali diversi;
non estendono la diagnosi ai freeze di overworld, a ROM precedenti o a ogni
possibile blocco dell'emulatore.

Questa diagnosi riguarda il freeze della candidata 1.3.1 osservato alla Lega.
Non attribuisce automaticamente la stessa causa al precedente blocco Latios,
segnalato su versioni anteriori al raccordo `fairy_ai`.

La successiva prova fisica usa l'esatta IT `c63cf9e9…afbedb`, con JIT e
renderer compute preesistenti: su copia del raw save completa SAVE/cold,
supera Weavile e Honchkrow, esegue un turno contro Houndoom e riapre le mosse.
La ROM ufficiale è aggiornata in luogo e il save corrente ricarica il campo.
La [verifica corrente](ui-1.3.1-validation.md) distingue questa scena dalle
quattro celle di compatibilità host EN/IT e dai checkpoint storici.

## Problema

Quando un Pokémon avversario va KO, `ov12_02258800` (overlay 12, `0x02258800..0x02258BA0`) sceglie il
sostituto in due stadi. Il primo assegna a ogni candidato la somma di due risultati di
`CalculateTypeEffectiveness` (`0x0225264C`): attacco del tipo 1 e del tipo 2 del candidato contro i due
tipi del bersaglio visibile (40 neutro, 160 per 4x). La somma viene poi troncata a 8 bit con
`lsls r0,#24; lsrs r0,#24` (`0x02258938`, `0x0225893A`) prima del confronto con il miglior punteggio.

Un candidato i cui due tipi colpiscono entrambi 4x il bersaglio (tipico: monotipo, ma anche doppio come
Lotta/Terra contro Roccia/Acciaio) vale 160 + 160 = 320, che diventa 64: il miglior candidato di tipo viene
scartato in favore di uno più debole. Sui tipi 0..17 dell'helper reale i casi sono 142 su 104 976
combinazioni (coppia candidato × coppia bersaglio), tutti esattamente 320; ogni altra somma resta ≤ 255. È il difetto documentato in pokeplatinum
(`bugs_and_glitches.md`, «Post-KO switch-in AI scoring overflow»); qui è provato sui byte e sull'esecuzione,
non per somiglianza. La tabella tipi della base V4 non contiene righe con il tipo 9 (Folletto): per questo
helper il tipo 9 è neutro; le prove leggono comunque la tabella reale.

La stessa routine di cambio chiama `ov12_02252054` per stabilire se una mossa
è superefficace. Se una tipologia rende la mossa immune e una riga successiva
rende debole la seconda tipologia, il retail conserva insieme
`NO_EFFECT|SUPER_EFFECTIVE`. Succede per Gligar/Elettro,
Aerodactyl o Skarmory/Terra e Girafarig/Spettro. Il consumer può quindi
scegliere una riserva con Thunderbolt contro Gligar invece di Geloraggio.

Un difetto separato era nel gate `ov10_022203A4`: prima di valutare se cambiare,
l'IA ripeteva controlli parziali per vincoli, Pedinombra, Arena Trap e
Magnetismo invece di usare il contratto normale. Arena Trap bloccava quindi
anche Volante, Levitazione e Magnet Rise; Shed Shell non prevaleva sui quattro
rami. La revisione 4 sostituisce i 16 byte a `0x022203B4` con salvataggio di
`r0/r1`, battler in `r2`, BL Thumb a `BattlerCanSwitch` (`0x02255920`) e rami
verso le continuazioni originali `blocked/allowed`. La funzione di 536 byte è
pin-nata con SHA-256 `2cc6ca06…5d1c0`; dopo vale `17cdabc8…f0db4`.

Il riproduttore privato esegue davvero overlay 10 e la routine autorevole
dell'overlay 12 su sei immagini EN/IT. Copre 96 casi: i falsi blocchi
divergono, mentre grounded, Iron Ball, Gravity, Pedinombra, Magnetismo, vincolo,
Sand Veil e nessuna trappola restano coerenti. Le 42 divergenze includono anche
Shed Shell contro gli altri rami; digest canonico `0a464755…3cf0a`. Gli stub
sono limitati alle query foglia di abilità, tipi e strumento. Non è una lotta
renderizzata.

Un terzo difetto, HG-B15, era nella routine `ov10_0221FE8C`: i confronti
dell'abilità attiva e delle riserve ammettevano soltanto Fuocardore,
Assorbacqua e Assorbivolt. Due BL Thumb a `0x0221FF10` e `0x0221FFC6`
chiamano ora un helper di 20 byte a `0x0222B26C`, dopo la tabella static-init
`0x0222B268..26C`. Il helper conserva il match esatto e aggiunge unicamente le
coppie Assorbivolt/Elettrorapid e Assorbacqua/Pellearsa; Fuocardore non entra
nel ramo normalizzato. La matrice nativa passa 96 casi su sei input EN/IT, con
24 divergenze prima e zero dopo (`2fd8a4fd…db778`). Il flusso RNG esistente,
l'ordine di scansione e i controlli KO/uovo restano invariati.

Un quarto difetto separato, AI-WEB-03, era nella sequenza Expert di Facade nel
membro 0 di `a/0/9/9`. L'opcode status usava il token 0 (bersaglio), mentre lo
script danno della mossa legge l'attaccante. Il test nativo esegue l'interprete
overlay 10 sulle candidate EN/IT: prima della correzione il bersaglio alterato
dà `+1` e l'utilizzatore alterato zero; il solo token a `+0x5B68` cambia 0→1 e
la matrice segue l'utilizzatore. La maschera `0xD8` e il delta `+1` restano
identici; sonno e congelamento sono controlli negativi. Il rematch Plus di
Valerio/Falkner ha AI flags 7 e, nelle varianti A/B, Swellow con Fiammosfera e
Facade. La prova isola la sequenza: dispatch naturale, scelta mossa, SAVE/cold
e dispositivo restano aperti.

Un quinto difetto, AI-WEB-04, era nel dispatch Expert: la tabella elencava due
volte effetto 151 (SolarBeam) e non inviava effetto 152 alla routine Thunder,
pur presente e integra a `+0x58A4`. Il test nativo del dispatch reale EN/IT
mostra che Thunder non legge la routine prima del fix. Una sola parola a
`+0x2C00` cambia 151→152: dopo il fix pioggia assegna `+1`, sole con RNG 50
assegna `-3`, il confine 49/50 è preservato e sereno resta neutro. SolarBeam e
Thunderbolt sono negativi e non entrano nella routine. Sette trainer reali con
Thunder hanno il bit Expert. Resistenza/immunità precomputata, scelta naturale,
SAVE/cold e dispositivo restano aperti.

Un sesto difetto, AI-WEB-02, era nella sequenza Basic di Metal Burst. Prima
del comando finale `CheckSortSpeed`, lo script tentava di anticipare l'ordine
con due controlli Stall e due confronti dell'ID strumento 107. L'ID 107 è
Pietrabrillo, non l'effetto ritardante 107; inoltre le scorciatoie Stall si
contraddicono con Coda Lenta/Full Incense e con due utilizzatori di Stall. Il
riproduttore esegue il vero interprete overlay 10, il `CheckSortSpeed` reale
dell'overlay 12 e i dati strumenti autenticati EN/IT. I 30 scenari per lingua
includono nessun effetto, Pietrabrillo, combinazioni miste, doppio Stall, due
strumenti ritardanti, parità/RNG, Distortozona, Rapidartigli e Baccacrela. La correzione non sostituisce il
motore d'ordine: rende nulli i quattro salti relativi a `+0x1DFC`, `+0x1E0C`,
`+0x1E20` e `+0x1E30`, lasciando gli opcode intatti e facendo arrivare ogni
caso al comando finale già presente. La matrice prima/dopo passa EN e IT e
verifica anche cursore e terminazione; incontro naturale, scelta mossa e
priorità nel contesto battaglia completo,
SAVE/cold e dispositivo restano aperti.

## Prova prima / dopo (CPU, istruzioni native eseguite)

La funzione vera parte dall'ingresso in Unicorn con overlay 12 e ARM9 delle ROM V4 EN/IT. Scenario sintetico
ispirato al piano (non un incontro naturale): allenatore con Rhyperior (Terra/Roccia, slot 2) e Machamp
(Lotta/Lotta, slot 4), bersaglio Bastiodon (Roccia/Acciaio). I tipi sono letti dal personal NARC `a/0/0/2`
della ROM. Entrambi hanno una mossa superefficace (stub dichiarato).

| | Punteggi osservati nel vero CMP | Scelta |
|---|---|---|
| nativo | Rhyperior 180, Machamp 64 (320 & 0xFF) | slot 2 |
| patchato | Rhyperior 180, Machamp 320 (in `[sp,#0x4c]` resta 64) | slot 4 |

Le prove sono in `source/sgp131/test_ai_scoring_rom.py` (Class B) e `test_ai_scoring.py` (Class A).
I log RED (identità prima del fix, poi la variante a due NOP superata) e GREEN restano nelle note private del manutentore; i comandi per riprodurli sono quelli dei due moduli di test.

## Delta esatto (revisione 3: 10 byte dichiarati, 5 istruzioni)

Overlay 12 decodificato (base `0x022378C0`, `0x37380` byte). Prima: `r0` = somma, troncata e poi ricaricata.

| Indirizzo | Prima | Dopo |
|---|---|---|
| `0x02258938` | `0006` `lsls r0,r0,#24` | `0106` `lsls r1,r0,#24` |
| `0x0225893A` | `000e` `lsrs r0,r0,#24` | `090e` `lsrs r1,r1,#24` |
| `0x0225893C` | `1390` `str r0,[sp,#0x4c]` | `1391` `str r1,[sp,#0x4c]` |
| `0x02258944` | `1398` `ldr r0,[sp,#0x4c]` | `c046` `nop` |
| `0x02252202` | `0420` `movs r0,#4` | `0c20` `movs r0,#12` |

- `r0` resta la somma ampia a 32 bit: la `cmp r1,r0` seguente (unsigned, `bhs`) la confronta con il miglior
  punteggio e la `str r0,[sp,#0x48]` salva la somma ampia come nuovo miglior punteggio.
- `[sp,#0x4c]` riceve lo stesso valore troncato a 8 bit di prima. Lo stadio 2 riusa quella parola
  quando una mossa non ha valutazione del danno (id 0 o `ctx[0x3E1+16*mossa]==1`): vede lo stesso tipo di
  valore nativo, non uno più largo. Una prima versione con due soli NOP (`0006000e`→`c046c046`) lasciava
  la somma ampia anche in quella parola ed è stata scartata (mutante `superseded_two_nop`, rifiutato dal
  rilettore e rilevato dai test).
- `r1` non è vivo: dopo la `str` viene ricaricato con `ldr r1,[sp,#0x48]`, usato solo dalla `cmp`, e
  né il ramo `bhs` (`0x02258960`: `ldr r0,[sp,#0x40]`…) né il ramo non preso lo leggono prima di riscriverlo.
  Otto byte dichiarati, di cui cinque cambiano valore (`0x02258938`, `…3A`, `…3D`, `…44`, `…45`).
- Il quinto halfword amplia il test da `NOT_VERY_EFFECTIVE` a
  `NOT_VERY_EFFECTIVE|NO_EFFECT`: la cancellazione debole/resistente resta
  uguale, ma l'immunità ha precedenza. Dei due byte dichiarati cambia solo
  l'immediato a `0x02252202`; in totale sei byte logici cambiano.
- Guardie: 20 byte a `0x02258934` e 32 byte a `0x022521F8`, più SHA-256 delle
  due funzioni (`45b8c7da…69da84`, `eb5c3828…52a5`). Dopo la patch valgono
  `d2cfa7a4…7369c2` e `11d5bacf…a9a2e0`; l'overlay patchato è
  `daa14016…fdef19`, uguale in EN e IT.
- Scrittura ROM: `sgp12.overlay.applica` ricomprime BLZ in luogo. Sulle V4 il flusso resta di 161 572 B
  (slot 161 792 B): parola y9 `0x01027724`, voce FAT e lunghezza ROM invariate, CRC16 dell'header
  invariato. Cambiano solo i byte del flusso compresso dell'overlay (93 419 byte diversi nel file; nessuna
  modifica a FAT, y9 o header). ROM EN dopo `61f75f65…d59cf`, IT dopo
  `16083d75…e6c37`.
- `verify(before, after, receipt)` rilegge i byte senza usare l'esito dell'applicatore come oracolo:
  due decoder BLZ (progetto e ndspy) concordi, preimage, esattamente i dieci byte dichiarati e zero
  altri byte logici, voce y9 e tabella FAT coerenti, nessun'altra voce NitroFS/ARM9 diversa, padding
  0xFF, CRC header.

## Cosa non cambia

Stessa chiamata RNG (`Battler_GetRandomOpposingBattlerId` una volta), stessi accessori, stessa sequenza di
chiamate e argomenti per ogni decisione senza overflow (confronto su 400 scenari casuali), spareggi
(vince il primo), esclusione di KO/uovo/vuoto, slot corrente e in attesa (`ctx+0x219C`, `+0x21A4`, anche
del partner), controllo della mossa superefficace con ricaduta sul secondo candidato e poi sullo stadio di
danno, caso 0 e 1 sostituti. Nessuna nuova conoscenza dell'AI, nessuna nuova allocazione, nessun gating
Normale/Plus (correzione aritmetica comune).

Il troncamento a 8 bit del danno dello stadio 2 (`CalcMoveDamage`, danno > 255) **non è incluso**
(test `test_stage_two_damage_conversion_is_not_part_of_the_fix`).

Mutanti: ognuna delle cinque istruzioni lasciata originale, e la variante a due NOP, fanno fallire almeno
un controllo comportamentale (`test_each_instruction_of_the_delta_is_load_bearing`). Composizione con la
correzione Sguardofermo: finestre disgiunte, stessa immagine in entrambi gli ordini
(`test_composes_with_keen_eye_seam_in_either_order`, indirizzo proprietario solo di prova).

## Stadio 2 e valore stantio

Con questo delta la parola `[sp,#0x4c]` è sempre il valore a 8 bit dell'ultimo candidato valutato, come
nativo (il test ne verifica l'uguaglianza a ogni confronto). Conseguenza dichiarata e non eliminabile da
un delta così piccolo: quel «ultimo candidato valutato» dipende dall'ordine di eliminazione dello stadio 1,
che con la correzione cambia proprio nei casi di overflow (nativo elimina per punteggio troncato, ora per
punteggio vero). Esempio: Rhyperior 180 e Machamp 320, nessun superefficace, prima mossa di Rhyperior senza
danno: nativo lascia 64 (Machamp), ora 180 (Rhyperior) e lo stadio 2 sceglie 2 invece di 4
(`test_stage_two_inherits_the_new_stage_one_elimination_order`). Con due candidati a 320 (stesso ordine
nativo e nuovo) lo stadio 2 coincide col nativo, mentre la versione a due NOP sceglieva diversamente
(`test_stage_two_stale_word_and_choice_stay_native`). Un confronto differenziale su 1500 decisioni casuali
(mosse id 0, flag `ctx` a 1, danno, immunità, KO/uovo/corrente/pending) coincide con il modello «stadio 1
ampio, `[sp,#0x4c]` stretto».

## Chiamanti (la correzione è globale)

BL/BLX e puntatori letterali a `0x02258800` in ARM9 e in tutti i 129 overlay: gli unici chiamanti
residenti insieme all'overlay 12 sono `ov010` a `0x022205FE` (AI allenatore, riga ~9207 dell'asm pret) e
`ov012` a `0x0225F8E8` (controller avversario, `ov12_0225F8AC`, riga ~14203). Dunque singola, doppia,
partner/multi e strutture usano la stessa funzione. Altre corrispondenze grezze (ov045, 049, 091, 092,
093) sono in overlay che occupano la stessa RAM dell'overlay 12 e non sono mai residenti con esso.

## Confini di esecuzione delle prove

Stub Python agli ingressi nativi: `0x0223A7E4` GetBattleContext, `0x0223A7E0` GetBattleType, `0x0223AB6C`
GetBattlerIdPartner, `0x02253DA0` GetRandomOpposingBattlerId, `0x0223A834` GetPartySize, `0x0223A880`
GetPartyMon, `0x0206E540` GetMonData, `0x0224EDE0` GetBattlerVar, `0x02258BB4` tipo mossa, `0x022527CC`
GetBattlerAbility, `0x02255830` GetBattlerHeldItemEffect, `0x02252054` controllo
superefficace, `0x0223AB1C` GetFieldSide, `0x02256FF8` CalcMoveDamage e
`0x02251D28` modificatori/immunità. Il consumer generale mantiene quello stub
per `0x02252054`; le prove HG-B13 eseguono la funzione separatamente sui byte
originali e corretti e ne inoltrano il risultato al consumer. Eseguiti nativamente:
la funzione di scelta, `CalculateTypeEffectiveness` (`0x0225264C`) con il divisore `0x020F2998`, `MaskOfFlagNo`
(`0x020726C0`). Verificati a ogni esecuzione: r4–r11, SP, area chiamante, contesto di battaglia non
scritto e flag C del confronto uguale a `miglior ≥ punteggio` senza segno.

## Limiti

Prova di CPU su scenari sintetici, non uno schermo emulato né una lotta naturale. Non provati: gameplay
Android, vecchi salvataggi con Continua → SAVE → riavvio a freddo, durata della decisione su dispositivo
e una candidata successore conservata. La composizione logica con Sguardofermo e la pipeline ROM EN/IT
sono provate, ma non sostituiscono una lotta renderizzata. Vittorie o danni
maggiori non sono una misura di intelligenza dell'AI.

## Verificatore BLZ — correzione di integrazione

Prima, un footer alterato che decodificava negli stessi byte logici poteva
passare con hash aggiornati nella ricevuta. Ora il lettore richiede entrambi
gli hash e la codifica BLZ canonica del progetto, derivata dai byte della ROM
e dal limite FAT originale. Le suite mirate dati/receipt, native, chiamanti e
mutanti passano senza skip; il negativo del footer copre EN e IT.
