# Box portatile 1.3.1: R o tocco dalla squadra ordinaria al PC nativo

Stato: **ACTIVE_PRIVATE_CANDIDATE, NON-REGRESSIONE APERTA**. La candidata corrente IT e'
`35d459e3fcf7cf127d6ff0aec94a5f502accfce390b2455b83fe189a5ca088f4`
(159.029.292 byte); la corrispondente EN e'
`02cccfbfc49b6addddba90385634ffdfde22b9ff3fbae3d85ae8f5603c5bf0af`
(152.786.376 byte). Lo smoke fresco dell'esatta IT su melonDS Android sul Mac
completa Continue→campo→Squadra→R→PC nativo→campo, senza SAVE. La copia raw
esportata e la fixture originale conservano SHA-256
`553925da5f1814b3ebba587f383b4197381d5bc040ba7b8d8208c1ca8a7fb3ce`.
La coppia corrente include il successore da 2.952
byte che corregge **SG-BOX-NULL**. Il predecessore IT `420ec8b8…f059a` aveva
gia' dimostrato l'uso fisico del Box ma conteneva ancora il payload da 3.020
byte; la successiva IT `171b53b6…d64a0` resta installata sul dispositivo finche' la
candidata corrente non supera il gate fisico. Non va confusa con la candidata
formale corrente.
Le immagini con i flag a zero restano baseline tecniche della pipeline e non
descrivono lo stato della ROM installata. Questo non equivale ancora a una
release accettata: la campagna estesa di non-regressione resta aperta.

Le nuove candidate includono anche HG-T10: `legendary-scene-version` corregge
tre seam dell'overlay 2 affinche' la scena Lugia in mappa 244 usi la versione
8; Ho-Oh e le altre mappe conservano la 7. Il runtime sintetico EN/IT conferma
i consumer Lugia e il controllo Ho-Oh EN, con originali e copie save invariati.
Non e' una prova del freeze storico, della scena completa o del dispositivo fisico;
geometria ROM, riserva residente e layout save restano invariati.

Checkpoint storico precedente a HG-T10: EN `5c561184…2f15` e IT
`c5a45d16…77f97` completavano lo smoke headless fino a `PC_RUNNING` in 4.332
frame; 59/59 test ARM del feature bench, 26/26 package e 26/26 ROM erano verdi.
La vecchia IT aveva inoltre un ciclo Android SAVE/cold su copia. Queste prove
conservano i propri hash e non promuovono SAVE/cold o accettazione della coppia
corrente. Identita' complete e limiti sono nel
[rapporto UI](ui-1.3.1-validation.md).

## Cosa fa

Nella squadra aperta dal menu di avvio (campo ordinario) compare nel prompt di scelta il comando
`R: Box`. Un nuovo R fisico, anche con la mappatura L=A, oppure un tocco sul comando, chiude la squadra
con il normale Annulla, apre il PC nativo in modalita 2 (Sposta Pokemon: deposito, ritiro, spostamento,
controlli nativi su ultimo utilizzabile, Posta, capsula, box pieni) e, alla chiusura del PC, ricostruisce
una nuova squadra con il cursore sullo stesso slot (limitato al numero di Pokemon rimasti). B porta poi al
campo nella posizione originaria. La guarigione nativa di PS, PP e stato del deposito/ritiro e' accettata
dal maintainer e non viene disabilitata. Nessun campo di salvataggio nuovo, nessuna opzione nuova.

## Livelli di prova (non confonderli)

| Livello | Cosa dimostra | Dove |
|---|---|---|
| Host Python | pin, layout ABI, codifica del trampolino, misure di compilazione, installer | `sgp131/test_portable.py` |
| ARM in Unicorn sui byte V4 reali | codice installato + codice nativo avvolto, in un mondo sintetico (FieldSystem, proprietario del menu, PartyMenu, args) con servizi pesanti modellati | `features/portable-box/test/` |
| ROM reali in memoria | installer, verifier, pin su EN/IT, nessun byte fuori dalle zone possedute | `sgp131/test_portable_rom.py` |
| melonDS Android su Mac | **smoke fresco IT `35d459e3…88f4`** | Continue→campo→Squadra→R→PC nativo→campo; copia raw esportata invariata, nessun SAVE |
| melonDS headless storico | **EN `5c561184…2f15` / IT `c5a45d16…77f97`** | fase `PC_RUNNING`, nessun crash in 4.332 frame e save-copy invariata; prova non trasferita ai nuovi hash |
| Android fisico | **Gate della candidata corrente aperto** | la precedente IT `171b53b6…d64a0` resta installata; la nuova IT `35d459e3…88f4` non e' stata installata |

## Ciclo di vita

Hook installati. Le baseline tecniche restano inerti quando le parole di
attivazione sono zero; la coppia privata attiva sopra abilita il percorso:

| Hook | Sito V4 (EN = IT) | Funzione |
|---|---|---|
| lancio squadra | BL a `FieldSystem_LaunchApplication` dentro `PartyMenu_LaunchApp_Unk1`, `0x0203E572` | `sgp_box_launch_app`: lancia e fa `bind` (generazione++, identita di campo/proprietario/args) per tutti e cinque i chiamanti del menu di avvio, compreso il ritorno dal riepilogo |
| squadre non lanciate da Unk1 | nessun hook: legame pigro | `ensure_bound`: ritorno dalla Borsa senza strumento (`start_menu.c` 1074) e scambio strumenti rifiutato (`party_menu.c` 2625, contesto 10 -> 0) vengono legati per **identita viva** (vedi sotto) |
| stato 1 | BL a `PartyMenu_Subtask_MainNormal`, `0x0207909C` | `sgp_box_party_main`: valida, legge R/tocco, accetta la richiesta con `RETURN_0` e stato 32 |
| ritorno squadra | ingresso del callback `0x0203CA9C` (8 byte + trampolino) | `sgp_box_party_return`: consuma la richiesta o lascia girare il callback nativo |
| ritorno PC | callback del proprietario installato dal modulo | `sgp_box_pc_return` |
| prompt | BL a `PrintMessageOnWindowEx` dentro `PrintMessageOnWindow32`, `0x0207DAD2` | `sgp_box_prompt_print` |

Il trampolino del callback e' consapevole delle istruzioni: il BL a ingresso+6 viene ricodificato nel nuovo
indirizzo e la ripresa avviene a ingresso+12 (mai a +8, che cadrebbe dentro il BL). Con `requested=0` il
gate ritorna prima di qualunque chiamata nativa, quindi registri r4-r11, SP, valore di ritorno e memoria
osservabile sono quelli nativi per tutti i 32 valori di `selectedAction` e i 25 contesti (prova Unicorn).

Legame pigro (squadre che `PartyMenu_LaunchApp_Unk1` non ha lanciato): al primo stampare del messaggio 29 o al primo stato 1
con `input` attivo, se la squadra ha contesto 0 il modulo accetta il legame solo se **tutta** l'identita e' viva: `args->fieldSystem`
e `args->fieldMoveCheckData - 0x370` nominano campo e proprietario, il task in corso del campo (`field+0x10`) ha esattamente quel
proprietario come ambiente, il proprietario conserva questi args in `+0x380`, attende l'applicazione (stato 5) e ritorna dal
callback nativo della squadra (`0x0203CA9D`). Mai mentre una richiesta e' in corso o il PC e' aperto. Risultato deterministico:
la squadra della Borsa mostra sempre `R: Box`; dopo lo scambio strumenti rifiutato la squadra ritorna ordinaria ma il suffisso non
era stato stampato in contesto 0, quindi R resta inattivo fino alla prossima stampa nativa del messaggio 29 (comportamento fisso).
Una richiesta scritta dalla sonda PRIMA del legame viene scartata (contata come fallimento), mai eseguita.

Richiesta valida: il chiamante e' il menu di avvio, il contesto e' 0, `args->fieldSystem` e
`args->fieldMoveCheckData - 0x370` identificano campo e proprietario, `owner+0x380 == args`, il proprietario
e' in attesa dell'applicazione, nessuna animazione di tasto, politica ELIGIBLE. Poi:

1. stato 1: `selectedAction = RETURN_0`, stato 32 (uscita nativa con dissolvenza);
2. ritorno: **PCBoxArgs (12 byte, heap 0x0B) allocati prima di liberare gli args**; se l'allocazione fallisce
   la richiesta cade e gira il callback nativo con gli args ancora vivi; altrimenti liberazione unica degli
   args, `PCBox_LaunchApp`, callback del proprietario = `sgp_box_pc_return`;
3. ritorno PC: notifica nativa di box pieno (`sub_02093070`), liberazione unica degli args del PC, chiamata
   diretta al costruttore `PartyMenu_CreateArgs`, controllo del suo ritorno prima di ogni dereferenziazione,
   inizializzazione dei tre campi che il wrapper nativo scriveva e lancio tramite il wrapper Plus (che ri-lega
   il proprietario); cursore limitato al numero di Pokemon e callback nativo ripristinato;
4. se la squadra non si puo' ricreare: `FieldSystem_LoadFieldOverlay` e stato `RETURN` (le stesse due
   istruzioni del ramo Annulla nativo), senza chiamare il lanciatore con NULL.

`FieldMove_InitCheckData` non viene chiamata: il blocco dati MN (+0x370 del proprietario) e' posizionale
(dipende da avatar, oggetto davanti, metatile) e il percorso nativo squadra -> riepilogo -> squadra lo
conserva senza ricalcolarlo. La parola `refresh_field_data` resta riservata a 0 e nessun codice la legge.

## Politica di accesso (negata per default)

Il consenso richiede un segnale **positivo** di campo ordinario letto dai dati del chiamante verificato; tutto cio' che non e'
dimostrabile staticamente resta `UNPROVEN` finche' una prova non e' attestata nella ricevuta.

| Segnale | Origine | Rifiuto |
|---|---|---|
| `inhibitIconFlags` (+0x34C) e `unk_350` del proprietario | `StartMenu_Init` e varianti: ordinario = SAVE abilitato, voci 7 e RETIRE inibite, nessun bit fuori da {Pokedex, Pokemon, Borsa, 7, RETIRE, Pokegear} | `SPECIAL_ACTIVITY`: Safari, Gara Bug, Pal Park, stanza partner Torre Lotta, Colosseo, Union |
| `FieldSystem.mapLoadType` (+0x70) | `MAP_LOAD_TYPE_OVERWORLD = 0` obbligatorio | `SPECIAL_ACTIVITY`: Safari, Union, Colosseo, Torre Lotta, tipo 5 |
| `FieldSystem.frontierFsys` (+0xA0) | non nullo mentre gira una struttura della Frontiera (`scrcmd_9.c`) | `SPECIAL_ACTIVITY` |
| `FieldSystem.linkBattleRuleset` (+0xA4) | regole di lotta in collegamento | `SPECIAL_ACTIVITY` |
| modalita escort | `Save_VarsFlags_CheckHaveFollower(Save_VarsFlags_Get(saveData))`, la stessa lettura di `ScrCmd_CheckEscortMode` (flag script 0x961) | `SPECIAL_ACTIVITY` |
| stato avatar (+0x18 dell'avatar) | `travel_mask` (predefinito 0b11: piedi e bici) | `UNPROVEN_TRAVEL`: Surf e ogni altro stato |
| prova di contesto | parola `context_proof` = 1, scritta dall'installatore solo con una ricevuta `measured` che identifica la cattura (`sha256`, `origin`, `capture_file`, `capture_rom_sha256` della ROM giocata, `build_id`) | `UNPROVEN_CONTEXT` (5): tutto il resto |

La prova di contesto copre cio' che i segnali statici non mostrano: stanze della sfida dei Superquattro, strutture fuori dalla
Frontiera, mappe speciali che usano i flag ordinari, i casi di viaggio. Senza prova l'installatore **rifiuta** `bridge`, `input` e
`prompt` (una ricevuta `synthetic` e' ammessa solo con l'interruttore di test `allow_synthetic_proof` e viene registrata come
`synthetic-for-test`). Lotta, scambi, selezioni di eventi, Borsa/MT/MN, apprendimento, evoluzione non passano dal menu di avvio
con contesto 0 e vivo: non vengono legate (`WRONG_OWNER`). Il rifiuto non mostra alcun comando e non alloca nulla (nessuno spazio
per un testo del motivo: vedi Limiti).

## Interfaccia (impeccable, piattaforma NDS nativa)

Prompt nativo (`Scegli un Pokemon.` / `Choose a Pokemon.`, finestra 32 da 160x16 a (16,168), font 1)
invariato. Dopo la stampa nativa il modulo aggiunge `R: Box` a x locale 112 con lo stesso font e colori:
prompt 98/97 px, scarto 14/15 px, suffisso 33 px che termina a 145, margine destro 15 px. Stessa forma
`L: EV` della legenda del riepilogo; nessun colore o cornice nuovi (coerenza HGSS, nessuna nuova
palette). Annulla nativo a x >= 200: separazione di 28 px dal rettangolo di tocco [124,172) x [168,184), che
non interseca nessun rettangolo nativo (tabelle `0x02110104/0x02110128` lette dalla ROM). Il suffisso e'
disegnato solo quando il messaggio e' il 29 sulla finestra 32 e la politica e' ELIGIBLE; ogni altro messaggio
nativo riscrive tutta la finestra e lo cancella. Il rendering offline col font reale e' un artefatto
privato della revisione, non pubblicato.

Feedback del tocco e del tasto: all'accettazione suona il segnale nativo di conferma (`SEQ_SE_DP_SELECT`, 1500), poi la
squadra si chiude con la normale dissolvenza dell'Annulla nativo. Il comando e' testo in una finestra, non uno sprite: non ha
animazione di pressione e il rettangolo di tocco non e' disegnato. Il feedback visivo e' quindi la chiusura immediata; una
cornice o un'evidenza del suffisso richiederebbe una finestra o uno sprite nuovi ed e' lasciata alla revisione designer sulle
catture Android.

## Installatore parametrico

`portable.prepare(data, language, work, *, allocation, preimage_sha256, activation=None, context_proof=None,
candidate_sha256=None, allow_synthetic_proof=False) -> (rom, receipt)`, `portable.measure(work)` (dimensione richiesta) e
`portable.verify(before, after, receipt)`. La base non e' un indirizzo: e' l'assegnazione di una **ricevuta di
`sgp131.reserve.allocate`** per `portable-box.runtime`, ricontrollata contro la politica di riserva in vigore (stessa politica,
input V4 della stessa lingua, nomi non condizionali, assegnazioni identiche a quelle di `reserve.allocate`); mai scelta, mai
dedotta da zeri. La mappa ufficiale puo' concedere lo slot condizionale soltanto
dopo che la cold UI ha dimostrato il ritiro completo della vecchia Guida
(`cold-ui-guide-retirement-v1`); senza quella prova l'installatore rifiuta.
`preimage_sha256` e' obbligatorio e deve coincidere con i byte sostituiti nell'immagine in ingresso (che puo' essere gia' passata
dalla UI: il modulo fissa solo intervalli di byte, mai l'intera ROM; prova con l'uscita reale della UI in
`test_portable_rom.RealUiComposition`). Controlli: pin di ogni intervallo e funzione nativa (EN = IT), siti hook,
base allineata e dentro un solo segmento ARM9, compartimento non sovrapposto agli hook e contenuto nell'assegnazione, preimmagine
obbligatoria, nessun byte modificato fuori dalle cinque zone possedute, ricompilazione indipendente in `verify`.
La prova di contesto `measured` e' legata a cio' che si e' misurato: `capture_rom_sha256` deve essere uguale all'argomento esplicito
`candidate_sha256` (la ROM candidata inerte su cui e' stata fatta la cattura) e `language` alla lingua dichiarata; la ricevuta
registra `candidate_sha256`, `capture_rom_sha256` e `candidate_relation` (`stage-inert-output` | `composed-candidate`, ricalcolato dai
byte) e `function_state` (`inert` | `active`, ricalcolato da `verify` dalle parole di attivazione installate). Nessuno stato di
processo (revisione, Android) e' scritto nel codice o nelle ricevute.
Parole di attivazione (`bridge`, `input`, `prompt`, `travel_mask`, `context_proof`) tutte a zero/3 per default: installata, la ROM
si comporta come la nativa. Coerenza imposta dall'installatore **e** dal codice: `input` richiede `bridge`; `prompt` richiede `bridge`
e `input` (un'etichetta per un comando che non fa nulla e' rifiutata); `bridge`, `input` o `prompt` richiedono una prova di contesto.
Un utente non puo' impostare `context_proof` a mano.
`UNPROVEN_CONTEXT = 5` estende in modo additivo l'elenco dei motivi del piano (0-4: ELIGIBLE, WRONG_OWNER, BUSY, SPECIAL_ACTIVITY,
UNPROVEN_TRAVEL): nessun consumatore interpreta il valore, il record lo registra soltanto.
`portable.verify(before, after, receipt, require_measured=True)` rifiuta per default una ricevuta con prova `synthetic-for-test`; solo i
test passano `require_measured=False`. La prova resta un'attestazione: il modulo ne controlla la forma e l'identita della cattura, non puo'
verificarne l'esistenza.

Misure (clang 21, Thumb, `-Oz`): codice+record+etichetta 2908 B, trampolino 44 B, compartimento 2952 B
(allineamento 4), stack massimo 48 B, record transitorio 64 B + configurazione 32 B dentro il compartimento,
nessun segmento allocato aggiuntivo. Heap: PCBoxArgs 12 B e PartyArgs nativi 0x44 B nell'heap 0x0B; il primo
viene liberato prima della ricostruzione e il secondo resta al menu squadra ricreato. Un ritorno `NULL` del
costruttore torna al campo senza lancio né dereferenziazione.

## Sonde per il banco

`run_probe.py` e `verify_probe.py` (in `features/portable-box/tools/`) preparano e verificano la riesecuzione dell'harness. Il verifier ricalcola
ogni verdetto dai `runtime.log` (hash, `READ` rilette, terza passata di riproduzione) e per `input-R`/`input-touch` richiede lo stesso blocco di
osservazione del PC e che lo script contenga `tap R` oppure un tocco dentro [124,172) x [168,184). **L'autenticita non e' provabile offline**: un log
e un'osservazione falsificati insieme e coerenti sono indistinguibili da una corsa vera; solo la riesecuzione dell'harness sugli stessi ROM, salvataggio e
script lo dimostra. Le sonde non sono state eseguite su Android.

## Limiti dichiarati

- La prova Android del 1 novembre e la conferma d'uso chiudono l'affermazione
  «funzione inattiva», ma non sostituiscono la campagna completa: manca una
  rilettura fisica corrente dell'hash installato e restano da eseguire input R
  e touch, deposito/ritiro/spostamento/annullamento,50 cicli per lingua,
  pressione heap, contesti negati, SAVE e riavvio a freddo su copie di save.
- Il banco ARM resta un mondo sintetico e modella i servizi pesanti; i suoi
  risultati non vanno confusi con il collaudo fisico.
- La prova di contesto non e' una misura che questo modulo possa produrre: finche' Codex non ne fornisce una `measured`
  l'installatore rifiuta ogni attivazione. Superquattro, strutture non coperte dai segnali statici e viaggi particolari restano
  `UNPROVEN` per costruzione.
- `prompt_shown` e' dedotto dalle stampe della finestra 32: se un percorso nativo cancella la finestra senza
  ristampare il messaggio 29, il flag resterebbe a 1 (misura richiesta a Codex).
- Accompagnatore: il refresh e' quello nativo della chiusura squadra, non provato.
- Nessun testo per il motivo del rifiuto: 48 px liberi non bastano; richiede una scelta del designer.
- Il controllo copre il ritorno del costruttore PartyArgs; non dimostra le allocazioni interne successive del
  gestore di overlay, che restano da esercitare sotto pressione heap sul dispositivo.

## Correzioni post-review K (stato congelato)

- **Cancello finale obbligatorio del builder** (`portable.candidate_gate(final_rom, receipt)`): lo sha256 della ROM finale con le parole/flag di attivazione di questo stadio
  azzerate (`portable.inert_view`, funzione pura che cambia solo quelle parole) deve essere uguale a `candidate_sha256`, la candidata inerte su cui e' stata fatta la cattura.
  Senza questo controllo `candidate_relation: composed-candidate` e' un'etichetta, non un'attestazione (il test mostra che una candidata inventata passa `prepare` e non il cancello).
- **Preimmagine dello slot indipendente** (`portable.slot_preimage_from_v4(v4, language, allocation)`): l'hash atteso si calcola sulla V4 esatta, mai su `sha(rom[slot])` dell'immagine in
  ingresso allo stadio (tautologico). Ricetta del builder: `pre = portable.slot_preimage_from_v4(v4, lang, alloc)`; se uno stadio intermedio lascia legittimamente residui nello slot, il suo hash
  va fissato nel manifesto dello stadio e passato come `preimage_sha256`.
- `clang` e (per controls) `charmap.txt` sono fissati per hash; `controls.verify(..., charmap=...)` ricompila il payload con geometria, variante e flag della ricevuta.
- **Limiti noti**: il predicato dei chiamanti BL vede solo BL Thumb nel segmento statico (non BLX da ARM, chiamate da literal pool, overlay); `audit` e' valido solo PRIMA di `prepare`
  (dopo l'installazione i tre siti e le loro funzioni non hanno piu' l'hash del pin); le callee transitive delle funzioni native non sono fissate (garanzia: lista chiusa di scritture degli altri stadi, provata contro la UI).
