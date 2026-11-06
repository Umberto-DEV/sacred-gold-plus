# Precisione moderna 1.3.1: Fuocofatuo e Sguardofermo

Rapporto delle due modifiche circoscritte del
piano interno. Stato: **moduli e prove
host/ARM completi; non ancora integrati nella candidata, nessun collaudo Android**.
Nessun nuovo ID, PP, abilità o formato di salvataggio.

## Fuocofatuo: precisione 75 → 85

- Dato: archivio `a/0/1/1` (file 140 nella V4, 471 membri da 16 byte contigui),
  membro 261, byte 5. Preimage del membro
  `a70002000a4b0f000000001611010000` (effetto 167, stato, tipo Fuoco, PP 15).
- `sgp131.modern_moves` cambia **un solo byte della ROM**, in luogo, senza ricostruire
  il NARC; rifiuta archivio estraneo/troncato, conteggio diverso, membro 261 diverso o
  già a 85. Il rilettore riparsa entrambi gli archivi e confronta tutti i membri, gli
  altri file NitroFS, ARM9/ARM7/overlay/banner e la differenza byte a byte della ROM.
- Consumatori nativi verificati sui byte V4 EN/IT: `LoadMoveTbl` (ARM9 `0x02073300`)
  legge dall'archivio NARC 11 il membro 0 per 468 × 16 byte contigui; l'inizializzazione
  della lotta (overlay 12 `0x0224868E`) lo copia in `ctx + 0x3DE`, la base indicizzata
  dal calcolo di precisione. Riepilogo/`GetMoveAttr` leggono il membro 261 via FAT.
  Entrambe le letture danno 85.
- Calcolo nativo eseguito (Unicorn, `BattleSystem_CheckMoveHit` dall'ingresso con la
  cache costruita dall'archivio): 100 residui di `Random() % 100` → **75 colpi prima,
  85 dopo**, differenze soltanto ai residui 75..84, una chiamata RNG per controllo
  in entrambi i casi; scala degli stadi di elusione −6..+6 pari a 85 × tabella nativa.
- Ustione, immunità del tipo Fuoco, Velo Sacro/Sostituto/Protezione e animazione
  dipendono dall'effetto 167 e dagli script di lotta, non dal byte di precisione: il
  rilettore prova che effetto, tipo, ogni altro campo e ogni altro file restano
  identici. Il loro comportamento in gioco non è stato riprovato (campagna Android).
- PP 15 e PP massimi 15/18/21/24 con PP-Up 0..3 invariati (formula di `GetMoveMaxPP`
  `0x0207332C`); i Pokémon salvati non vengono letti né migrati.

## Sguardofermo: ignora tutte le variazioni d'elusione del bersaglio

- Seam unico in `BattleSystem_CheckMoveHit` (overlay 12, base `0x022378C0`):
  `0x0224BD5C BL GetBattlerAbility(ctx, attaccante)` seguito da `CMP r0, #109`; se
  uguale, `r4` (delta elusione del bersaglio) diventa 0. La modifica sostituisce
  soltanto questi 6 byte: `BL` verso un predicato compilato e `CMP r0, #1`. Il ramo
  successivo e il resto del calcolo sono invariati.
- Predicato `features/modern-accuracy/native.c`: chiama **una volta** il getter nativo
  `0x022527CC` e restituisce 1 per abilità effettiva 51 o 109. Il getter applica
  Gastroacido (tranne Multitipo) e le altre soppressioni, quindi Sguardofermo o
  Imprudenza soppressi tornano al comportamento originale. La protezione dai cali di
  precisione (comando di variazione statistiche) non è toccata.
- Payload: 28 byte (budget 128), SHA-256
  `9370a52456cd303a935e69a033224d00f8a18d03c6d70a4032839efa2ef43cdd`, posizione
  indipendente (l'unico letterale è l'indirizzo del getter), allineamento 4,
  stack 8 byte (`push {r7, lr}`), AAPCS r4–r11 preservati. Clang
  `Apple clang version 21.0.0 (clang-2100.3.34.2)` fissato per versione e hash.
- **Indirizzo:** la mappa della riserva assegna `modern-accuracy.code`, 32 byte a
  `0x023D5AA0`, dentro la vecchia Guida ritirata (sotto condizione del ritiro UI).
  `compile_native(work_dir, owned_address)` compila per l'indirizzo dato; gli stadi
  rifiutano senza uno slot e ne verificano l'hash del contenuto attuale. Scrivono solo
  i 28 byte del payload; i 4 byte di coda restano invariati e verificati.
- **Due percorsi:** `apply_code(data, lingua, work_dir, *, slot)` installa solo payload
  e seam, in luogo (nessun file accodato, `a/0/2/7` intatto), con rilettore
  `verify_code(before, after, receipt)`; serve dopo la UI, dove la descrizione viaggia
  come delta del membro 722 (`text.patch_bank`). `apply(..., slot, charmap)` aggiunge
  la descrizione accodando `a/0/2/7` ed è valido solo sugli input V4.
- **Rilettore del flusso compresso:** l'overlay 12 deve essere la codifica BLZ
  canonica del writer (`blz_comprimi_ottimo` con la lunghezza FAT originale), con FAT
  e riga y9 coerenti, bit di compressione e flag invariati, coda dello slot a 0xFF,
  due decoder concordi e hash di ingresso/uscita della ricevuta obbligatori. Un flusso
  diverso che decodifica alla stessa immagine (footer alterato, padding di 4 byte con
  FAT/y9 coerenti, bit di flag inutilizzato) viene rifiutato anche con una ricevuta
  riscritta.

### Descrizione EN/IT (banco 722, riga 51)

`features/modern-accuracy/text.py` sostituisce solo la riga 51 del banco 722 di
`a/0/2/7` (le altre 123 righe e gli altri 829 membri restano identici) e accoda
l'archivio con `sgp13.resources.append_file`. I testi candidati del piano non
entrano nelle finestre reali e sono stati sostituiti:

| Lingua | Testo | px per riga |
| --- | --- | --- |
| EN | `Prevents accuracy loss.` / `Ignores evasion changes.` | 131, 136 |
| IT | `Evita cali di precisione e` / `ignora i cambi d’elusione.` | 131, 134 |

Misure con il font 0 di `a/0/1/6` (interlinea 16 px) e le finestre lette dai byte V4:
riepilogo (ARM9, finestra 7, 152×32 px, x=3) e riepilogo in lotta (overlay 8,
144×32 px, x=0). Massimo due righe; la riga più larga delle altre 123 descrizioni
retail è 136 px, nessuna nuova riga la supera. Il testo non nomina strumenti o meteo.
Font 0 letto anche dall'ARM9 (`0x020F56D8`: altezza 16, spaziature 0). Render ricostruiti dal font (non catture del gioco) restano nelle note private.

### Prove eseguite (ARM, non gameplay)

Banco `features/modern-accuracy/test/accuracy_bench.py`: esegue la vera funzione,
il getter, il controllo Rompiforma `0x02252834`, le divisioni ARM9 e la tabella
nativa; stub dichiarati per tipo di lotta, abilità attive sul campo, strumenti,
helper "ha già agito" e RNG.

| Caso (attaccante, bersaglio, mossa) | Prima | Dopo |
| --- | --- | --- |
| 51, elusione +6, precisione 100 | 33/100 | 100/100 |
| 109, elusione +6, precisione 100 | 100/100 | 100/100 |
| 51, elusione −6, precisione 75 | 100/100 | 75/100 |
| 109, elusione −6, precisione 75 | 75/100 | 75/100 |
| 51 soppressa, elusione +6, precisione 100 | 33/100 | 33/100 |

- Matrice completa: stadi precisione/elusione 0..12 × 4 attaccanti × {nessuna, 51,
  109} × soppressione: dopo la modifica, con 51 effettiva la probabilità è quella
  nativa con elusione del bersaglio neutra; in tutti gli altri casi identica alla
  funzione originale; stessa chiamata RNG.
- Interazioni: Imprudenza e Disinvoltura del bersaglio, Disinvoltura attaccante,
  Insettocchi, Sabbiavelo/Mantelneve con meteo e Antimeteo, nebbia, Gravità,
  Luminpolvere, Grandelente, Zoomlente, Baccaracolo, Preveggenza, Miracolvista,
  Intricopiedi, Tuttafretta, tasso fisso (percorso Nullodifesa), turno di carica,
  mosse senza controllo, Tuono al sole, tutorial, doppie e cambio bersaglio.
- Predicato isolato: 256 abilità × 4 battler × {nessuna, Gastroacido, Gravità e
  Levitazione, Radicamento e Levitazione}, due indirizzi; una chiamata al getter.
- ROM installata (copia in memoria nello slot della mappa; sulla V4 quei byte sono
  ancora codice della Guida, quindi non è una ROM giocabile): il banco esegue ARM9 e
  overlay 12 della ROM prodotta, senza iniettare payload; stessi conteggi della
  tabella. Rilettore indipendente: overlay cambiato solo nel seam, ARM9 solo nel
  payload, coda dello slot, altri file e descrizione verificati.
- Mutanti uccisi dopo baseline verde: 51 assente, 109 assente, lettura diretta del
  byte d'abilità (51 soppressa attiva), CMP ancora 109, solo variazioni positive,
  azzeramento incondizionato, SP danneggiato.

## Interazione con la correzione AI in overlay 12

Le due modifiche toccano byte disgiunti dello stesso overlay (seam `0x0224BD5C..61`,
AI `0x02258938..0x02258945`, 8 byte logici); ogni stadio decodifica l'overlay corrente e verifica solo la
propria funzione. La composizione nei due ordini produce la stessa immagine e la stessa ROM (test `test_composes_with_ai_scoring_in_either_order`, EN e IT).

## Consumatori AI di precisione/elusione

Verifica sui byte dell'overlay 10 V4 EN (script identico al riferimento pret): l'AI
non chiama `BattleSystem_CheckMoveHit` né ne replica la formula; legge gli stadi
ACC/EVA nei comandi di script e l'abilità 51 una sola volta (penalità per mosse che
abbassano la precisione contro Sguardofermo, ancora corretta). Due scelte possono
diventare meno utili (alzare la propria elusione contro un Sguardofermo; bonus legati
all'elusione del bersaglio per un'AI con Sguardofermo): mancata conoscenza
dell'abilità come già in vanilla, nessun errore dimostrato. Nessun hook aggiunto;
un intervento richiederebbe prima un caso riproducibile sul banco.

## Limiti

Nessuna prova Android, persistenza o prestazioni sul dispositivo; nessuna candidata
composta costruita. Prove ARM con contesto sintetico e confini dichiarati.
