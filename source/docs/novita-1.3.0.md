# Novità della 1.3.0 rispetto alla 1.2.5

Aggiornato al **29 ottobre 2026**. Questo documento registra le modifiche realmente integrate nella **candidata 1.3.0**, che nel gioco è ancora identificata come **1.3 DEV**. La 1.2.5 resta la versione pubblicata: questo registro non annuncia una nuova release.

Il confronto parte dalla **1.2.5 di Sacred Gold Plus**, che comprende già modifiche rispetto a HeartGold e ai Pokémon originali. Il dettaglio delle prove è nel [rapporto funzionale Android](android-1.3-dev-validation.md); qui sono raccolti il prima/dopo e il beneficio delle modifiche.

## Confronto a colpo d’occhio

| Area | Nella 1.2.5 | Nella candidata 1.3.0 |
|---|---|---|
| Guida nel menu di campo | Il lettore e la guida EV/IV della Summary erano già presenti; lo spazio ora usato dalla Guida di campo era vuoto. | Nuova Guida/Guide con quattro categorie, 429 voci, pagine e collegamenti, nello stile HGSS. |
| Modifica IV | Nessuno dei nuovi consulenti IV e servizi con tappi della 1.3. | Consulenti, scelta precisa 0–31, tappo per una statistica o per tutte e sei, acquisti e ricompense. |
| Gestione EV | Regole ereditate e strumenti nativi. | Allenamento rapido, riduzioni/reset, modalità Classic e Unlimited, corsi e gestione dei valori precedenti. |
| Pensione | Crescita e riproduzione native legate ai passi. | Corsi opzionali basati su tempo reale o tempo giocato, stato al telefono e risultati applicati al ritiro; riproduzione ancora legata ai passi. |
| Shiny | Nessuna delle nuove modalità native Classic/Pro o ricerca mirata della 1.3. | Seconda pagina Plus, probabilità configurate per modalità, bersaglio, catena e Search. |
| Specie | Bilanciamento ereditato da Sacred Gold Plus. | Analisi di 493 specie e interventi su 67: statistiche base, accesso alle mosse e due nuovi slot abilità. |
| Allenatori Plus | Aumento dei livelli già disponibile. | Nove sostituzioni mirate di mosse in sette allenatori, in aggiunta al sistema di livelli esistente. |
| Indicatore di cattura | Il controllo escludeva le lotte contro allenatori. | La Ball appare anche per i Pokémon degli allenatori quando il Pokédex registra la specie come catturata. |
| Eventi e salvataggio | Percorsi con durata del movimento Mew, flag alti o esito SAVE problematici. | Correzioni mirate, protezione della Rubrica Amici e messaggio corretto quando SAVE viene rifiutato. |
| Identificazione | Etichetta 1.2.5 introdotta nella versione pubblicata. | Etichetta di sviluppo 1.3 DEV; nuova infrastruttura di build e verifica dedicata alla candidata. |

## 1. Guida di campo e interfacce

La nuova Guida usa lo spazio libero del menu di campo e mantiene font, cornici, palette e comandi coerenti con HGSS. È distinta dalla guida EV/IV già presente nella Summary.

| Categoria | Voci |
|---|---:|
| Evoluzioni | 229 |
| Strumenti e MT | 156 |
| Eventi speciali | 38 gruppi |
| Allenamento | 6 argomenti |
| Totale | **429** |

Le liste mostrano cinque righe, supportano touch e pulsanti e consentono salti di cinque voci con L/R. I dettagli sono divisi in pagine; i collegamenti aprono la voce pertinente e il ritorno ripristina pagina e posizione di partenza. I paragrafi brevi restano uniti. La cache temporanea del font riduce le letture ripetute durante la navigazione; viene rilasciata all’uscita.

Il menu Options offre un accesso Plus visibile oltre a SELECT. Plus mantiene le cinque impostazioni precedenti e aggiunge descrizioni contestuali, colori di selezione nativi e la seconda pagina Shiny. Annulla e Applica gestiscono il cambiamento delle due pagine; le Options native conservano la propria conferma. Il rientro ripristina l’anteprima nativa della velocità del testo, con gestione del testo ancora in stampa.

Riferimenti: [Guida](../features/field-guide/README.md), [interfaccia Plus](../features/plus-ui/README.md).

## 2. Consulenti IV e tappi

I nuovi consulenti si trovano nei Market di **Violapoli e Ebanopoli**.

- Un **tappo argento / Silver Cap** porta un IV a 31 oppure al valore preciso scelto fra 0 e 31.
- Un **tappo oro / Gold Cap** porta tutti e sei gli IV a 31.
- Sono IV realmente memorizzati: possono influire su riproduzione e Introforza. Non è una semplice simulazione delle statistiche.
- La selezione mostra i valori attuali e quelli richiesti. Annullamenti, operazioni senza effetto e pagamenti rifiutati non consumano risorse.
- Il tappo argento costa **10.000**, dopo la prima medaglia; quello oro **50.000**, dopo la Lega.

| Traguardo | Nuova ricompensa |
|---|---|
| Ogni palestra di Johto | 2 tappi argento |
| Ogni palestra di Kanto | 3 tappi argento |
| Ottava e sedicesima medaglia | 1 tappo oro aggiuntivo ciascuna |
| Prima vittoria alla Lega | 4 argento + 2 oro |
| Vittorie successive alla Lega | 4 argento + 1 oro |
| Prima vittoria su Red | 3 oro |

I vecchi salvataggi ricevono una sola volta le ricompense storiche ammesse. Le precedenti rivincite della Lega non vengono pagate retroattivamente. Se non c’è spazio per consegnare un tappo, la ricompensa resta in attesa e può essere ritirata successivamente.

## 3. EV e corsi alla Pensione

Il consulente nel **Percorso 34** aggiunge l’allenamento rapido: impostare un valore superiore costa **100 per ogni EV aggiunto**; riduzioni e reset sono gratuiti. La schermata distingue il costo dalla conferma.

| Regola EV | Limite per statistica | Limite complessivo | Comportamento |
|---|---:|---:|---|
| Compatibilità / Legacy | Regole ereditate: fino a 255; vitamine fino a 100 | 510 | Mantiene il comportamento precedente finché non si sceglie una nuova policy. |
| Classic | 252 | 510 | Distribuzione con limite totale. |
| Unlimited | 252 | 1512 | Consente 252 in tutte e sei le statistiche, dopo avviso e conferma. |

Il cambio verso regole più restrittive controlla anche i Pokémon conservati e gli obiettivi dei corsi. Non taglia automaticamente gli EV dei vecchi Pokémon: eventuali valori incompatibili richiedono una riduzione esplicita. Guadagni da battaglia, vitamine e bacche seguono la policy selezionata; i moltiplicatori nativi degli strumenti e del Pokérus restano in uso.

I corsi per i Pokémon depositati sono **gratuiti**, mentre restano le normali tariffe di ritiro della Pensione:

- crescita di un livello ogni **due ore**;
- allenamento opzionale di **32 EV all’ora**, verso l’obiettivo scelto per una statistica;
- tempo reale come impostazione iniziale, oppure tempo di gioco attivo;
- stato e previsione consultabili dal contatto Pensione del Pokégear;
- applicazione del risultato al ritiro, conservando le mosse possedute;
- gestione separata dei due Pokémon depositati e dei rispettivi progressi.

Le uova continuano a dipendere dai passi. Il corso non trasforma il tempo trascorso in progressi di riproduzione e non sostituisce automaticamente le mosse del Pokémon.

Riferimenti: [integrazione dei servizi](../features/training-native/README.md), [regole e persistenza](../features/training/README.md).

## 4. Shiny Classic, Pro e ricerca della specie

La pagina Shiny si apre da **Options → Plus**, usando R o la freccia nell’intestazione. Queste modalità sono indipendenti dalla difficoltà Normal/Plus e dalle omonime regole EV.

| Modalità | Successi completati della specie bersaglio | Probabilità per la generazione ammessa |
|---|---:|---:|
| Classic | Non richiede una catena | **1/512** |
| Pro | 0–9 | **1/4096** |
| Pro | 10–19 | **1/2048** |
| Pro | 20–39 | **1/1024** |
| Pro | Da 40 | **1/512** |

In Pro, le probabilità migliorate valgono per il bersaglio; la nuova soglia parte dalla generazione successiva. Catturarlo o mandarlo KO incrementa la catena. Un’altra specie ordinaria, la fuga, la sconfitta o il pareggio la interrompono; gli incontri esclusi la sospendono. Nessuna soglia garantisce uno shiny.

**Hunt / Search** permette di scegliere una specie già vista e presente nel gruppo di incontri nativi dell’area. Supporta erba/caverne, Surf e le canne possedute, nelle posizioni valide. Rispetta disponibilità, orario, forme e progressione. Servono **40 passi validi**; la ricerca viene preparata nel menu, confermata con Applica e avviata quando il campo torna libero. Può funzionare sotto Repellente e non sostituisce un Pokémon errante.

Il cambio effettivo di modalità o bersaglio azzera catena e carica; annullare la modifica le preserva. Search riuscita consuma la carica. SAVE conserva modalità, bersaglio, catena e stato casuale; il riavvio completo riporta la carica a zero. Non viene scritto un salvataggio a ogni incontro.

L’integrazione copre gli incontri ordinari ammessi e le nuove apparizioni statiche ordinarie non forzate, queste ultime con probabilità base senza bonus di catena. Uova, regali, starter, scambi, Dono Segreto, erranti, Pokémon degli allenatori, Safari, gare, doppi incontri ed eventi forzati mantengono i propri percorsi nativi. I Pokémon già generati non vengono ricalcolati per renderli shiny.

Riferimento completo: [regole, esclusioni e integrazione shiny](shiny-species-1.3.md#controls-and-hunt-rules).

## 5. Ribilanciamento delle specie e accesso alle mosse

Il lavoro prende spunto dai ruoli di Blaze Black 2 / Volt White 2 Redux e li adatta al motore HGSS e ai dati già modificati di Sacred Gold Plus. Non importa il motore di quinta generazione né cerca di assegnare lo stesso totale di statistiche a tutti.

| Intervento rispetto alla 1.2.5 | Quantità |
|---|---:|
| Specie analizzate individualmente | **493** |
| Specie interessate da almeno una modifica | **67** |
| Specie con statistiche base cambiate | **50** |
| Specie con un nuovo secondo slot abilità | **2** |
| Specie con aggiunte al learnset per livello | **29** |
| Aggiunte di livello/mossa | **32** |

Le categorie si sovrappongono. I record delle specie modificati sono 51: Meganium cambia abilità ma non statistiche. Le 32 aggiunte non sono 32 mosse distinte.

Questi interventi riguardano **statistiche base**, non EV regalati o IV aumentati. Valgono per giocatore, selvatici e allenatori, anche in difficoltà Normal. Il ricalcolo selettivo all’avvio aggiorna le statistiche interessate dei membri della squadra conservando danni e KO; il ritiro dal PC usa la conversione nativa. Identità, EV/IV, mosse e abilità già possedute sono conservati.

Esempi delle scelte:

| Pokémon | Miglioramento rispetto alla 1.2.5 | Ruolo conservato o favorito |
|---|---|---|
| Rattata | PS 30→35, Attacco 56→60, Difesa 35→40, Difesa Speciale 35→40 | Più utilizzabile nelle prime fasi, restando fragile. |
| Raticate | PS 65→75, Attacco 91→96, Difesa 60→65, Difesa Speciale 70→75 | Attaccante veloce; resta il compromesso di precisione di Tuttafretta. |
| Tentacruel | Difesa 65→75, Attacco Speciale 80→85; Fangobomba al livello 32 | Resistenza speciale e velocità, con difesa fisica meno debole. |
| Ditto | PS 48→75, Difesa e Difesa Speciale 48→65 | Più resistenza prima di Trasformazione; i PS restano utili anche dopo. Non viene aggiunta Sosia. |
| Kricketune | Attacco 96→106, Velocità 74→80 e maggiore resistenza; nuovo accesso a mosse utili | Attaccante fisico con Tecnico disponibile come secondo slot nei nuovi esemplari. |
| Meganium | Alternacura nel secondo slot, mantenendo Erbaiuto | Supporto; nessun aumento delle statistiche in questo passaggio. |

Le nuove abilità riguardano la generazione dei nuovi esemplari; non esiste una conversione automatica delle abilità possedute né un nuovo servizio per cambiarle. Le mosse aggiunte si ottengono tramite livello o Ricordamosse, senza sostituire quelle già conosciute.

Il registro in fondo elenca tutte le 67 specie interessate. Le tabelle complete delle statistiche prima/dopo sono nella [prima serie](shiny-species-1.3.md#first-species-batch-retained-in-the-expansion) e nell’[estensione alle 493 specie](shiny-species-1.3.md#expanded-audit-of-all-493-species). Le motivazioni individuali sono nel [registro di analisi](../sgp13/data/balance-audit.json).

Questa versione non modifica globalmente potenza, precisione o effetti delle mosse, tipi, evoluzioni, compatibilità MT o EV assegnati dalle specie sconfitte. Le misure di danno e precisione aiutano le scelte, ma non dimostrano l’equilibrio di tutti gli scontri dell’avventura.

## 6. Squadre strategiche e indicatore di cattura

La difficoltà Plus esisteva già. La 1.3 aggiunge queste **nove sostituzioni di mosse in sette allenatori**, mantenendo il precedente sistema dei livelli:

| Allenatore | Pokémon | Prima → dopo |
|---|---|---|
| Raffaello / Bugsy | Scyther | Falsofinale → Coleomorso |
| Angelo / Morty | Gengar | Pugnodombra → Palla Ombra |
| Furio / Chuck | Primeape | Ira → Breccia |
| Jasmine | Magneton | Scintilla → Scarica |
| Jasmine | Steelix | Schianto → Terremoto |
| Jasmine | Steelix | Lucidatura → Vortexpalla |
| Alfredo / Pryce | Dewgong | Purogelo → Riposo |
| Pino / Will | Xatu | Barattoforza → Psichico |
| Lance | Gyarados | Iper Raggio → Cascata |

Le nove sostituzioni vengono attivate solo in Plus. In Normal non si applicano; rimangono comunque attivi il ribilanciamento delle specie e i learnset generali descritti sopra. Non sono state sostituite tutte le squadre degli allenatori. Dettagli e motivazioni: [strategie degli allenatori](trainer-strategy-1.3.md).

La Ball che segnala una specie già catturata viene mostrata anche nelle lotte contro gli allenatori, usando il Pokédex. Questo ampliamento non equivale alla soluzione di ogni vecchia segnalazione di icona intermittente nei selvatici.

## 7. Bug corretti e rifiniture della candidata

| Problema | Modifica integrata | Provenienza e limite |
|---|---|---|
| Il movimento di Mew poteva continuare dopo la distruzione dello script che lo aveva avviato. | Le tre relocation attendono la conclusione del movimento prima di terminare lo script. | Correzione del percorso evento; non prova la soluzione del separato caso Latios. |
| Il chiamante touch di SAVE poteva mostrare successo dopo un rifiuto nativo. | Messaggio EN/IT di fallimento, attesa di conferma A/B/touch, ritorno al campo e possibilità di riaprire SAVE. | Corregge il feedback; un rifiuto persistente resta un salvataggio non riuscito. |
| Flag evento alti potevano sovrapporsi alla Rubrica Amici, come nella cattura Mew verificata. | Area dedicata, importazione conservativa dei bit precedenti, controlli all’avvio e identificatori degli eventi mantenuti. | Corregge la sovrapposizione futura; non ricostruisce dati eventualmente corrotti in passato. |
| La nota inglese della migrazione superava la larghezza della finestra. | Testo ridotto da 218 a 193 pixel nei 204 disponibili; italiano già valido e invariato. | Correzione del testo, senza azzerare le impostazioni per farlo apparire. |
| Un servizio Training già attivo poteva applicare EV e addebitare denaro prima di un successivo SAVE rifiutato. | Nuovo controllo della destinazione prima dei servizi mutanti; conferma rifiutata invalidata e messaggio corretto. | Difetto emerso durante lo sviluppo del nuovo Training della 1.3, assente come servizio nella 1.2.5. |

La Guida e le nuove pagine Plus hanno inoltre ricevuto controlli su apertura/chiusura, annullamento, risorse temporanee, paginazione e convivenza con la preview delle Options. Sono rifiniture delle funzioni nuove, non nuove opzioni di gioco.

## 8. Continuità dei salvataggi e strumenti di sviluppo

L’aggiornamento conserva identificatori e layout nativi dei Pokémon, impostazioni Plus e dati della Borsa ampliata. I nuovi servizi usano un archivio separato, versionato e controllato, con verifiche prima della scrittura: dati estranei o futuri non vengono sovrascritti come se fossero vuoti.

Non è richiesta una nuova partita. Le prove includono copie EN/IT senza Plus, con impostazioni Plus, con Borsa ampliata e con corsi attivi nei salvataggi intermedi di sviluppo. Questi ultimi sono casi di migrazione interna della 1.3, non corsi già presenti nella 1.2.5. La compatibilità verificata è in avanti: il ritorno a una ROM precedente non è una migrazione inversa garantita.

Sul lato sviluppo sono stati aggiunti:

- un builder separato che parte da immagini 1.2.5 identificate dall’impronta, con controlli sui dati prima e dopo ogni modifica;
- un registro delle aree di memoria riservate e verifiche delle integrazioni;
- ricevute di build con impronte, versione degli strumenti e sorgenti usati, senza sovrascrivere gli output esistenti;
- modelli probabilistici condizionati e test delle regole, affiancati da esecuzioni del codice ARM installato;
- una matrice funzionale con prove Android e confronti dei salvataggi grezzi dopo SAVE e riavvio completo;
- pulizia degli intermedi di build e conservazione limitata delle build operative, mantenendo ingressi ed evidenze.

Il builder e i file della release pubblicata 1.2.5 restano separati da questo percorso di sviluppo.

## 9. Verificato, ereditato e ancora fuori dalla copertura

La campagna funzionale documenta **49 checkpoint accettati**: 45 con SAVE e riavvio completo e quattro con rifiuto e file intero conservato. Sono distribuiti fra candidate successive; il [rapporto](android-1.3-dev-validation.md) identifica gli hash e spiega quali prove si trasferiscono sui componenti rimasti identici.

L’ultima esecuzione completa comprende **37 suite Class A, 806 esecuzioni riuscite e 52 skip**. Sono separati gli 86 controlli del codice installato, le 76 migrazioni in RAM e i controlli Class B, con i rispettivi limiti. I numeri non si sommano come se fossero tutti test diversi o tutti playtest Android.

Su Android sono stati osservati, fra gli altri, modifica e persistenza di statistiche/IV/EV, uso di vitamine e bacche, servizi e corsi, catture Classic/Pro, catena e Search, Guida, Plus, Mew e scene di boss. Tecnico è stato acquisito normalmente e verificato dopo PC→squadra→SAVE→riavvio; il suo effetto numerico e il comportamento di Alternacura hanno prove ARM. Non sono state giocate 493 battaglie, tutte le combinazioni dei servizi o un’intera nuova avventura; le due scene boss finali sono prove UI senza SAVE della vittoria. La verifica del dispositivo fisico e delle sue prestazioni resta distinta dal banco Android Software 1x.

**Già presenti nella 1.2.5 e mantenuti**, quindi non da presentare come novità della 1.3: Borsa ampliata, gestione ripetuta delle Caramelle Rare, animazioni opzionali in lotta, fluidità NPC, scelta del server Wi-Fi, scaling dei livelli Plus, camera e correzioni delle grotte, lettore/guida EV/IV della Summary, tipi e mosse Folletto ereditati. Non viene dichiarato un nuovo sblocco FPS o una correzione universale dei freeze e dei problemi grafici dell’emulatore.

## Registro completo delle specie interessate

Elenco ricavato dalle specifiche pubbliche [statistiche/abilità](../sgp13/data/species-changes.json) e [learnset](../sgp13/data/learnset-changes.json), confrontato con le 493 decisioni. “Statistiche” indica un cambiamento effettivo dei valori base; il trattino indica nessun nuovo intervento in quella colonna. I nomi delle mosse sono in inglese per il confronto diretto con le specifiche. Non sono elencate le 426 specie senza nuove modifiche in questo passaggio.

| N. | Pokémon | Statistiche | Nuovo secondo slot abilità | Aggiunte per livello |
|---:|---|---|---|---|
| 19 | Rattata | Sì | — | — |
| 20 | Raticate | Sì | — | — |
| 22 | Fearow | Sì | — | Focus Energy L40 |
| 24 | Arbok | Sì | — | — |
| 28 | Sandslash | Sì | — | — |
| 55 | Golduck | Sì | — | — |
| 57 | Primeape | Sì | — | — |
| 73 | Tentacruel | Sì | — | Sludge Bomb L32 |
| 85 | Dodrio | Sì | — | — |
| 87 | Dewgong | Sì | — | — |
| 97 | Hypno | Sì | — | — |
| 99 | Kingler | Sì | — | — |
| 132 | Ditto | Sì | — | — |
| 144 | Articuno | — | — | Air Slash L50 |
| 154 | Meganium | — | Alternacura / Natural Cure | — |
| 164 | Noctowl | Sì | — | — |
| 165 | Ledyba | Sì | — | — |
| 166 | Ledian | Sì | — | Drain Punch L26 |
| 168 | Ariados | Sì | — | Poison Fang L23 |
| 178 | Xatu | Sì | — | — |
| 182 | Bellossom | — | — | Synthesis L43 |
| 191 | Sunkern | Sì | — | — |
| 199 | Slowking | — | — | Slack Off L43 |
| 206 | Dunsparce | Sì | — | Headbutt L25 |
| 210 | Granbull | Sì | — | — |
| 219 | Magcargo | Sì | — | — |
| 222 | Corsola | Sì | — | — |
| 224 | Octillery | Sì | — | — |
| 225 | Delibird | Sì | — | Ice Shard L22; Roost L32 |
| 226 | Mantine | — | — | Roost L44 |
| 234 | Stantler | Sì | — | — |
| 237 | Hitmontop | — | — | Mach Punch L35 |
| 261 | Poochyena | Sì | — | — |
| 262 | Mightyena | Sì | — | — |
| 267 | Beautifly | Sì | — | — |
| 269 | Dustox | Sì | — | Sludge L23 |
| 283 | Surskit | — | — | BubbleBeam L16 |
| 284 | Masquerain | — | — | BubbleBeam L22 |
| 294 | Loudred | — | — | Hyper Voice L36 |
| 295 | Exploud | Sì | — | Hyper Voice L40 |
| 301 | Delcatty | Sì | — | Hyper Voice L28 |
| 306 | Aggron | Sì | — | — |
| 309 | Electrike | — | — | ThunderShock L9 |
| 310 | Manectric | — | — | Discharge L36 |
| 317 | Swalot | Sì | — | — |
| 321 | Wailord | Sì | — | — |
| 323 | Camerupt | Sì | — | — |
| 326 | Grumpig | Sì | — | — |
| 329 | Vibrava | Sì | — | — |
| 336 | Seviper | Sì | — | Sludge Bomb L34 |
| 337 | Lunatone | Sì | — | — |
| 338 | Solrock | Sì | — | — |
| 340 | Whiscash | Sì | — | — |
| 345 | Lileep | — | — | Mega Drain L18 |
| 346 | Cradily | — | — | Recover L46 |
| 354 | Banette | Sì | — | — |
| 358 | Chimecho | — | — | Psybeam L22 |
| 369 | Relicanth | — | — | Head Smash L50 |
| 389 | Torterra | Sì | — | — |
| 402 | Kricketune | Sì | Tecnico / Technician | Bug Bite L10; Bug Bite L14; Brick Break L26 |
| 411 | Bastiodon | Sì | — | Iron Head L30 |
| 416 | Vespiquen | Sì | — | — |
| 432 | Purugly | Sì | — | — |
| 435 | Skuntank | — | — | Poison Jab L38 |
| 457 | Lumineon | Sì | — | U-turn L31 |
| 470 | Leafeon | — | — | Leaf Blade L33 |
| 477 | Dusknoir | Sì | — | — |
