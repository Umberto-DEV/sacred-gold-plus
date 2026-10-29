# Verifica funzionale Android di Sacred Gold Plus 1.3 — 29 ottobre 2026

Aggiornamento del 29 ottobre: le candidate correnti V1.3 e la successiva prova
sul dispositivo fisico sono nel [rapporto dedicato](device-1.3-validation.md).
Gli hash, i conteggi e i limiti della campagna seguente restano riferiti alle
revisioni qui identificate.

La campagna funzionale Android è conclusa con **49 checkpoint accettati**: **45 con SAVE nativo e riavvio a freddo**, più **quattro rifiuti con l’intero file invariato**. La matrice distingue le scene Android dalle prove ARM e dai controlli dei dati, conservando i limiti di ogni risultato. È la verifica di un candidato privato **1.3 DEV**, senza pubblicazione di release o sostituzione di tag, ZIP o file già distribuiti.

Le tappe precedenti restano documentate nel [playtest v5](playtest-1.3-dev.md), nella [verifica delle interfacce v8](ui-1.3-dev-validation.md), nella [diagnosi di stabilità](deep-debug-2026-10-28.md) e nella [verifica iniziale v4](validation-1.3-dev.md). I loro pin e conteggi identificano campagne distinte.

Il banco è un **AVD Android 13 / API 33 ARM64**, con APK acquisito e profilo **Software 1x**. Non è una prova su un dispositivo fisico con profilo Compute 6x, né un confronto di GPU, driver, FPS o latenza. I problemi shader/GLES del banco restano separati dai difetti della ROM.

## Candidati e trasferimento delle prove

| Lingua | Candidato v3, SHA-256 | Stato alla chiusura |
|---|---|---|
| EN | `1ed3c886f26ac01c64e7c4f102c38659af6cec81d5c317ba3cf31c67447fe9d5` | Build, review e otto checkpoint Android v3 accettati: migrazione, Options/Plus, Protein, Kelpsy, carica Pro, due catture e ritiro Tecnico; tutti con SAVE/cold. |
| IT | `2f1b0857f1b57703c635d9076aec8f650a8e9aec8f3335e3a271098a261a45f8` | Intera ROM identica alla v2 già eseguita. Le prove italiane su questo hash valgono sugli esatti byte finali. |

I 49 checkpoint comprendono 25 prove su v1, 16 successive sui byte v2 — sette EN e nove IT — e otto prove EN v3. Sono 45 checkpoint con SAVE e riavvio a freddo, più quattro di rifiuto del salvataggio con file originale integralmente conservato. Il numero dei checkpoint non coincide con quello delle funzionalità.

Si aggiungono i controlli **solo UI** Bugsy Normal IT e Plus EN: Scyther 21 con Agilità e Attacco d’Ala nel primo; Scyther 23 con Coleomorso effettivamente eseguito nel secondo. I sei livelli Plus sono leggibili e diversi dal controllo Normal. La conclusione delle lotte e i successivi dialoghi nel campo sono documentati; le ultime immagini hanno ancora un dialogo aperto e non provano movimento libero. Nessun SAVE nelle lotte: entrambi i file esportati sono integralmente identici ai rispettivi ingressi. Questo non prova lo stato in RAM o la persistenza delle vittorie. Questi casi non incrementano i 49 checkpoint. Falsofinale non è stato osservato; non viene richiesto di forzarne la scelta.

Il confronto v2→v3 EN trova **77 byte cambiati nel solo banco testi Options**: una frase, i relativi offset e il riempimento. Ogni byte esterno, inclusi codice, configurazioni, risorse e metadati ROM, resta identico. IT non presenta alcuna differenza. È quindi giustificato conservare le prove dei percorsi invariati e ripetere il solo percorso EN interessato dal testo. Il confronto non equivale a ripetere tutte le prove su Android EN v3. Il percorso testuale modificato è stato realmente rieseguito: nota completa, accettazione e campo, SAVE esportato prima dell’arresto, cold Continue al campo e salvataggi identici. La fixture ha squadra e PC vuoti: il caso non prova autonomamente la conservazione di Pokémon occupati.

| Tappa precedente della stessa campagna | EN SHA-256 | IT SHA-256 |
|---|---|---|
| v2 | `fe182440f43cb95442fcb2a965ba68a4bf6b4b2e22ccc616f1df3a9bf2fc1106` | Identico all’intera v3 IT sopra indicata. |
| Balance493 v1 | `a290df71a54ea016f4e19cd9e6f8f94e1f8d1f675b4d2dcd209c058d4f6a5b12` | `f7585f5248f483a4bbe12424954a805a86ff9d744f58b62a135e750a7f00099e` |

La nomenclatura v1/v2/v3 qui usata appartiene a questa campagna e non rinomina i precedenti candidati v3, v4 o v8 di altre verifiche.

Il passaggio precedente v1→v2 aveva invece modificato Training, gestione dei flag alti e composizione di Continue. Il trasferimento da v1 rimane limitato ai componenti invariati; quelle integrazioni hanno nuovi test ARM sul codice installato e scene Android dedicate. Le prove storiche non vengono rietichettate come esecuzioni del candidato finale.

## Metodo di verifica e conservazione

Ogni prova usa una **copia** del salvataggio; gli originali vengono conservati e controllati tramite impronte. Le preparazioni controllate sono dichiarate: posizione davanti a un evento o requisito predisposto non sono presentati come normale progressione della storia. Le due catture Search EN sono invece ordinarie, senza modificare PID o RNG.

La persistenza si verifica con Continue, operazioni attraverso il gioco, **SAVE nativo completato ed esportato prima dell’arresto**, arresto e riavvio dell’app, nuovo Continue fino al campo e confronto del salvataggio acquisito. Nel primo caso storico legacy IT, l’esportazione immediata precedeva il flush dell’emulatore ed è stata esclusa: il confronto accettato usa `cold.sav` e `cold-later.sav`, identici fra loro. I savestate non sostituiscono queste prove. Per i rifiuti si confronta invece l’intero file con l’ingresso, senza trasformare un SAVE fallito in una migrazione riuscita.

Gli audit verificano identità e contenuto dei Pokémon, squadra e PC, inventario nativo ed espanso, impostazioni, Pensione, corsi, ricompense, rubrica, coerenza dei banchi e controlli d’integrità. Gli eventuali cambiamenti ammessi di tempo o stato degli NPC sono circoscritti e motivati. Non si cancellano differenze inattese con una normalizzazione generale.

Le prove ARM eseguono funzioni del gioco o del candidato. Dove servizi esterni sono simulati — allocazioni heap, servizi OS, accesso a risorse, memoria flash, commit o trasporto — il confine è dichiarato. Una prova del calcolo del danno o del proprietario del printer non dimostra da sola l’intera sequenza grafica Android.

## Tre difetti corretti durante la campagna

| Difetto riprodotto | Correzione | Verifica disponibile e limite |
|---|---|---|
| Un servizio Training già attivo poteva applicare EV e addebitare denaro prima che una destinazione di salvataggio estranea causasse il successivo rifiuto di SAVE. | Controllo fresco della destinazione prima delle operazioni mutanti 4–8; l’operazione 4 rifiutata invalida anche la preview e il retry richiede una nuova preview. Letture e annullamenti non sono mutazioni. Il messaggio non promette più falsamente che si possa salvare normalmente. | Android EN/IT: richiesta EV a pagamento rifiutata prima della modifica, EV e denaro riletti intatti, SAVE rifiutato e file intero invariato dopo cold Continue. Test ARM coprono anche gli altri servizi e il retry. |
| La gestione di flag evento alti poteva sovrapporsi a dati della Rubrica Amici: una cattura Mew completata alterava un dato estraneo. | Area dedicata ai flag, importazione conservativa dello stato precedente e controlli prima/dopo Continue, mantenendo gli identificatori degli eventi. | Android EN/IT: prima relocation e cattura finale Mew, SAVE/cold e intera rubrica conservata. ARM: tutti i flag della classe interessata, collisioni, importazione e lettore dell’evento Sinjoh. Non una prova Android di ogni quest. |
| La nota EN della migrazione risultava tagliata: 218 pixel di testo su 204 effettivamente disponibili. | Frase EN più breve, larga 193 pixel, con guardia e controllo sullo spazio reale. IT resta invariato e misura 201 pixel, già entro la finestra. | Font e pixel originali confermano il difetto. Test del trasformatore e confronto indipendente della build v3 verificano la modifica testuale circoscritta. **Replay UI e SAVE/cold EN v3 verificati:** nota completa, campo dopo Continue e confronto rigoroso del salvataggio. Il precedente tentativo con comandi sovrapposti è escluso. |

Queste sono tre correzioni della campagna corrente. Non implicano che ogni vecchia segnalazione di freeze o marker mancante abbia la stessa causa o sia stata riprodotta. Le precedenti correzioni della durata dei movimenti Mew e della comunicazione del SAVE fallito restano funzionalità verificate separatamente nella matrice seguente.

## Portata effettiva del bilanciamento

- **493 specie** hanno una decisione individuale documentata; non significa 493 battaglie Android.
- **67 specie** sono interessate da almeno una modifica; le categorie si sovrappongono.
- **50 specie** hanno statistiche base effettivamente cambiate.
- **51 record personal** sono modificati. Meganium cambia solo il secondo slot abilità: è il motivo per cui i record sono 51 ma le specie con statistiche cambiate sono 50.
- **29 learnset** ricevono **32 aggiunte di livello/mossa**, non 32 mosse distinte, senza sostituire automaticamente le mosse dei Pokémon posseduti.
- Due specie ottengono un secondo slot abilità nativo: Kricketune con Tecnico e Meganium con Alternacura. Il comportamento di tali abilità dispone di prove ARM; l’acquisizione ordinaria di Kricketune con Tecnico, il passaggio PC→squadra e la persistenza SAVE/cold sono verificati anche su Android EN. L’effetto numerico di Tecnico e il comportamento di Alternacura restano prove ARM.

Il censimento dei dati e i test nativi coprono l’insieme finito delle modifiche. Le scene Android verificano campioni rappresentativi di generazione, ricalcolo, apprendimento e conservazione. Non si ricava da esse una stima di equilibrio dell’intera avventura o di percentuali di vittoria.

## Matrice delle 37 funzionalità

“Verificato nel campione” indica il percorso descritto, non ogni variante. I due gruppi finali concordati — strumenti EV EN e Pro EN 402 — sono conclusi; i limiti elencati non sono nuove scene dichiarate come eseguite.

| # | Funzionalità | Prova Android disponibile | Prova ARM / dati / codice | Limite o stato residuo |
|---|---|---|---|---|
| 1 | Titolo e versione | Boot e titoli EN/IT documentati; il finale IT ha gli stessi byte già eseguiti. | Titolo e banco testi controllati nel confronto della build. | Nota migrazione EN v3 completa, scelta e SAVE/cold verificati nel campione. |
| 2 | Vecchi save senza Plus | Continue, domanda iniziale, scelta esplicita Plus/Plus, SAVE e cold EN/IT. | Selezione nativa dei banchi, controlli d’integrità e inizializzazione verificati. | Le fixture iniziali hanno squadra e PC vuoti; la conservazione di Pokémon occupati è coperta da altri casi. |
| 3 | Vecchi save con Plus e Bag espansa | Configured ed expanded EN/IT conservati; casi attivi conservano squadra, PC e Pensione. | Record, slot aggiuntivi, proprietari e binding verificati. | Conservazione dello slot esteso provata; visita UI di ogni slot non dichiarata. Gli otto casi di compatibilità sono completati. |
| 4 | Apertura e uscita dalla Guida | EN/IT: ingresso, ritorno al campo e movimento; roundtrip successivo IT salvato e riavviato. | Controller, proprietà delle finestre e ritorni testati. | Campione rappresentativo; non ogni ingresso o cancellazione. |
| 5 | Categorie e contenuti della Guida | Quattro categorie e dettagli leggibili EN/IT. | Censimento di 429 voci: evoluzioni, strumenti, eventi e allenamento. | Il censimento non è presentato come 429 aperture Android. |
| 6 | Pagine, scorrimento e collegamenti della Guida | Salti di lista, dettaglio su due pagine, collegamento e ritorno alla pagina d’origine; ultimo elemento campionato. | Limiti e stati del controller verificati. | Nomi di acquisizioni errati esclusi; non tutti i tasti e bordi sono stati giocati. |
| 7 | Ingresso Plus e preview nativa | EN/IT: prima riga Text Speed corretta, apertura Plus, didascalia ripristinata e nuova stampa parziale fino al testo completo. | Ramo printer attivo di proprietà eseguito ARM con servizi preview/finestre simulati ai confini dichiarati. | Percorso essenziale EN/IT verificato. Nessuna prova di overlap attivo Android all’ingresso Plus; ramo ARM dichiarato, nessun nuovo obbligo di strumentazione. |
| 8 | Draft, annulla e applica Plus | EN/IT: cinque descrizioni, draft annullato, applicazione conservata dopo Quit nativo e cold. | Controller e separazione delle strutture Options/Plus testati. | Campione essenziale EN/IT completato; non ogni combinazione dei valori. |
| 9 | Cinque impostazioni legacy | EN/IT: descrizioni, valori, cancel/apply e cold; velocità nativa, L=A e cornice preservate. Scena Plus del boss realmente eseguita. | Lettura/scrittura delle cinque opzioni e relativi hook verificati. | Campione EN/IT e scena boss Plus completati. Il selettore non dimostra connessione di rete. |
| 10 | Accesso ai consulenti IV/EV | Silver/exact/acquisti EN; Gold/claim IT; servizi sani IT con costo, readback e cold. | Guardie, precondizioni e transazioni eseguite nei test nativi. | Integrazione positiva italiana completata; non ogni direzione di ingresso ai Market. |
| 11 | Silver, IV esatti e Gold | Silver e valore esatto EN; sei IV a 31 con Gold EN/IT, no-op e cold. | Identità, ricalcolo e record completi ricostruiti; confini delle transazioni testati. | Nessun nuovo giro per ogni valore IV; rami non giocati restano qualificati come nativi. |
| 12 | Acquisto tappi | Silver a 10000 EN, Gold a 50000 IT con requisito predisposto; Gold pre-Lega rifiutato. | Prezzi, spazio, fondi e requisiti testati. | Il requisito Lega controllato non dimostra una vittoria naturale della Lega. |
| 13 | Ricompense e ripetizione | Claim IT e ripetizione senza doppioni; claim vuoto EN; SAVE/cold. | Censimento storico, ledger e consegna eseguiti ARM. | Non una campagna naturale di tutte le medaglie, Lega e Red. |
| 14 | Ricompense con stack pieno | EN: stack 999, no-op, consumo e consegna parziale; coda residua conservata al cold. | Caso pieno/pending e controlli negativi verificati. | Stack pieno non significa che ogni slot della Bag sia occupato. |
| 15 | Policy EV | EN: Classic al limite e oltre il limite, Unlimited annullata/applicata; IT Unlimited conservata con operazione sana. Protein e Kelpsy ordinarie EN con SAVE/cold. | Censimento delle precondizioni e confini finiti eseguito. | Campione di policy e strumenti completato; non ogni combinazione di limiti e strumenti in entrambe le lingue. |
| 16 | Allenamento EV rapido | Reset, riduzione, incremento e no-op EN; IT PS 64→65 a 100, ripetizione gratuita e cold. | Costi, identità e commit nativi verificati. | Integrazione rappresentativa completata, senza ogni quantità o statistica per lingua. |
| 17 | EV da battaglia, vitamine e bacche | Guadagno EV da KO IT; EN Protein: EV Attacco 0→10, Attacco 103→104, quantità 992→991. Kelpsy: EV 10→0, Attacco 104→103, quantità 999→998; ripetizione senza effetto o consumo aggiuntivo. Entrambi SAVE/cold. | Hook e regole EV testati nel codice. | Una vitamina e una bacca ordinarie EN verificate; non ogni strumento o statistica in entrambe le lingue. |
| 18 | Iscrizione ai corsi | Nuove iscrizioni ordinarie EN, due soggetti e seriali durabili; proiezione e ritiro IT. | Iscrizione, identità e precondizioni eseguite nei test finali per entrambe le lingue. | Nuova iscrizione IT non giocata: limite dichiarato, senza aggiungere un gate. |
| 19 | Orologi, status e telefono dei corsi | EN: RTC/tempo di gioco e intervallo offline; IT: cinque pagine telefono, due corsi e status residuo. | Proiettore, crediti, ancore e clock testati. | Non ogni cambio orologio o retrocessione RTC è una scena Android. |
| 20 | Ritiro e compattazione corsi | Entrambi i ritiri EN; IT ritiro a 400 con secondo soggetto/job compattato e conservato, cold. | Ritiro e compattazione eseguiti, record ricostruiti. | Campione positivo IT completato. |
| 21 | Migrazione dei corsi precedenti | Save attivi EN/IT: migrazione del journal, due corsi e ricompense preservati, SAVE/cold. | Integrità, versioni e composizione del salvataggio testate. | Le migrazioni in RAM sono supplemento, non sostituto del cold Android già eseguito. |
| 22 | Destinazione estranea e admission | EN/IT: servizio a pagamento rifiutato prima di EV/denaro; readback e file intero invariati dopo cold. | Controllo fresco per tutte le operazioni mutanti, invalidazione preview e retry testati. | Il precedente RED rimane storico; non ogni servizio negativo è stato ripetuto su Android. |
| 23 | Squadre e mosse strategiche dei boss | Normal IT: Scyther 21, Agilità e Attacco d’Ala; Plus EN: tutti i sei livelli e Scyther 23 che esegue Coleomorso. Prove solo UI. | Sette squadre, costruzione e variazioni di livello/mosse verificate. | Gate rappresentativo completato; nessun SAVE delle lotte, nessun claim sul journal RAM. Falsofinale non osservato. Non tutte le difficoltà, sette vittorie o equilibrio iniziale. |
| 24 | Marker catturato, selvatici e trainer | Selvatico IT prima/dopo cattura; trainer Scyther e Pinsir con Ball, Heracross senza Ball, coerenti con il Dex iniziale. | Dispatcher e renderer nativi, richieste e tipi di barra verificati. | La Ball è desiderata anche nei trainer con specie catturata. Nessun fix universale dei vecchi casi intermittenti viene dedotto. |
| 25 | Dati aggiornati nei Pokémon reali | Nuove catture EN/IT, ritiro Tentacruel e vecchio Rattata; nuovi Mew ricostruiti sui dati finali. | Censimento 493, delta dei dati e formule native verificati. | Scena strategica Plus completata. Non 493 battaglie; cache preesistenti conservate non sono dichiarate tutte corrette. |
| 26 | Continue, danno, KO e ritiro PC | Esempi danneggiati, esausti e a PS pieni; ritiro da PC con nuove statistiche e cold. | Ricalcolo nativo, conservazione del danno/KO e idempotenza testati. | Campioni distinti; non ogni specie e combinazione di PS. |
| 27 | Nuovi learnset e mosse possedute | Tentacruel IT apprende normalmente Fangobomba dal Ricordamosse, paga la Squama e conserva identità; cold. | Tutte le aggiunte e accessi nativi verificati; mosse/PP posseduti preservati negli audit. | Non ogni learnset è stato giocato in entrambe le lingue; nessuna sostituzione silenziosa delle mosse. |
| 28 | Nuove abilità e abilità possedute | Abilità precedenti conservate. Due Kricketune EN da Search ordinaria: primo Aiutinsetto, secondo Tecnico; PC→squadra→Summary→SAVE/cold completato per Tecnico. | Tecnico: effetto numerico nativo controllato. Alternacura: produzione, aggiornamento e consumer della squadra eseguiti ARM. | Assegnazione e persistenza Tecnico Android verificate; il suo effetto numerico e Alternacura restano prove ARM, senza stima del danno da barre PS con IV nascosti. |
| 29 | Shiny Classic | Vibrava cromatico EN da stato controllato, cattura/cold; Mew EN/IT statici ordinari Classic non cromatici. | Trasformazione PID e probabilità esatta testate. | Nessuna stima empirica della frequenza o attesa di shiny spontaneo. Mew non è una rotta esclusa. |
| 30 | Pro, bersaglio e soglie | IT: cattura, KO, fuga e stesso bersaglio; impostazioni e catena durabili. EN: Pro/Kricketune, due catture e catena 0→1→2, SAVE/cold. | Stati e soglie della probabilità esauriti nel core. | Percorso Pro EN completato. Non una serie di catture per ogni soglia. |
| 31 | Carica e Search | IT: rifiuto a 0, carica 40 e Search sotto Repel, KO/fuga. EN: rifiuto a 0, carica 40, Search sotto Repel e due catture; consumo della carica verificato. Nel Centro il selettore Method segnala metodo non disponibile. | Pool, metodo, contesto e generazione eseguiti nei test nativi. | Percorso EN completato. Il rifiuto Search a carica zero è distinto dal messaggio del selettore Method nel Centro. Surf usato come attacco non equivale a un incontro Surf. |
| 32 | Esiti e catena | IT: cattura e KO incrementano una volta, fuga azzera, SAVE/cold. EN: due catture ordinarie portano la catena 0→1→2, conservata al cold. | Esiti finiti, proprietario e settlement testati. | Altri esiti non giocati restano limiti. Trainer escluso dalla catena Hunt non significa marker nascosto. |
| 33 | Persistenza Hunt e modalità senza corsi | RNG/catena e impostazioni persistono senza attivare corsi o ricompense; coesistenza nei casi IT attivi. EN: carica realmente 40 prima del SAVE, cold al campo con carica 0 e Pro/bersaglio conservati. | Owner, coesistenza e salvataggio installato verificati. | Reset 40→SAVE/cold→0 verificato separatamente dal cold dopo consumo Search; non ogni combinazione dei corsi o delle modalità. |
| 34 | Rotte ammesse ed esclusioni shiny | Erba ordinaria EN/IT; Mew statico ordinario non forzato con draw persistito. EN: tutte le 11 righe Rules leggibili su tre pagine, con ritorno alla prima. | Classificatori, costruttori e abort con confini espliciti testati. | Le pagine Rules attestano il contenuto UI, non l’esecuzione di ogni rotta. Esclusi rari non sono scene Android; filtro Hunt e marker trainer restano separati. |
| 35 | Mew, relocation e durata dei movimenti | Prima relocation e cattura finale EN/IT: campo libero, flag e rubrica conservati, SAVE/cold. | Attese dei movimenti, flag alti e lettori nativi verificati. | Copie preparate dichiarate; non un inseguimento continuo completo. Il valore finale del flag non è una traccia di ogni scrittura intermedia. |
| 36 | SAVE fallito e acknowledgement | Tre rifiuti per lingua con A/B/touch, riapertura e movimento; nuove scene v2 con cold fino al campo e raw intatto. | Esito, pulizia e sequenza di acknowledgement testati. | Recovery transitoria e interruzione di alimentazione non dimostrate Android; nessun fault aggiuntivo da inventare. |
| 37 | UI native adiacenti | IT: Guida, tre vere pagine help della Summary Stats, ripristino, Bag, Pokégear, Options/Plus, campo e cold; precedente roundtrip EN. | Proprietà finestre e ritorni nei componenti verificati. | Giro essenziale Plus/printer EN completato con cold. Acquisizioni con nomi errati escluse dalle prove. |

## Test automatici: conteggi e confini

La validazione del codice installato v2 comprende **86 test riusciti**, senza failure/error/skip, e **76 migrazioni in RAM**. Codice e configurazioni eseguibili sono identici nella v3; l’evidenza mantiene il proprio scopo e i servizi simulati dichiarati. Le 76 migrazioni non vengono contate come 76 SAVE/cold Android.

Una successiva invocazione completa del runner finale ha concluso **37 suite Class A con PASS**: il runner riporta 806 esecuzioni al netto di 52 skip. Il suo totale 858 include la contabilità degli skip e non è un conteggio indipendente di discovery. Non viene sommato agli 86 test precedenti per ottenere un nuovo totale senza sovrapposizioni.

Class B resta separata: quattro controlli sintetici reader-mutant eseguiti e 176 skip per prerequisiti mancanti. Non è una nuova verifica di tutte le ROM installate. I 52 skip Class A e i 176 Class B restano visibili in questa relazione.

## Chiusura dei due gruppi finali

Protein e Kelpsy sono state usate normalmente dalla Borsa EN. Gli audit ricostruiscono il record completo del soggetto e i delta dell’inventario; il secondo uso Kelpsy è rifiutato senza ulteriore consumo. I cambiamenti giornalieri avvenuti durante Protein sono spiegati separatamente, incluso l’invecchiamento del Pokérus di un altro membro: non vengono attribuiti alla vitamina o nascosti da una normalizzazione generale.

Il giro Pro EN ha letto tutte le tre pagine Rules, salvato con carica effettiva 40 e verificato il cold a 0 mantenendo Pro e bersaglio 402. Due Search sotto Repel hanno prodotto catture ordinarie: prima Aiutinsetto (68), poi Tecnico (101), con catena 0→1→2. Il livello effettivo 19 comprende la trasformazione WildPlus del livello base 18. Entrambe le catture nel PC sono state salvate e riavviate prima della fase successiva.

Il deposito ordinario di Burmy e il ritiro di Kricketune/Tecnico conservano i rispettivi 136 byte di identità boxed; gli altri cinque membri della squadra e tutti gli altri record PC restano esatti. La nuova cache della squadra segue il calcolo nativo. Summary e cold Summary mostrano Kricketune femmina livello 19, **PS 62/62, Attacco 46, Difesa 38, Attacco Speciale 24, Difesa Speciale 37, Velocità 38**, Tecnico e quattro mosse a PP pieni: Fury Cutter 20/20, Bug Bite 20/20, Leech Life 15/15 e Sing 15/15. Il file completo dopo SAVE coincide con quello dopo cold. L’audit finale ricostruisce tutte le 45 regioni confrontate con differenze finite esplicite, senza normalizzatori opzionali; distingue osservazioni puntuali di mappa, RTC e tre parole inutilizzate della Mail da valori ricavati dalle formule. Questo prova acquisizione, conversione PC/squadra e persistenza, mentre l’effetto numerico di Tecnico resta coperto ARM.

## Integrità finale e limiti del banco

Il controllo finale indipendente conferma invariati **23 riferimenti agli ingressi originali** di tipi diversi, **38 fixture uniche**, entrambe le ROM finali, entrambe le basi 1.2.5, 14 artefatti Options di riferimento e 208 file congelati di codice/dati/test. I 23 riferimenti non sono 23 fixture di vecchi save. Le modifiche alla sola documentazione sono esterne a quel manifest congelato e non richiedono di rieseguire ROM o test nativi.

Le due ROM installate corrispondono ai pin finali. L’APK acquisito mantiene SHA-256 `198505e4f50d9eafa2dbc3f941fcec83f0b747e23c95cb00efdb57859ce8afaa`. Alla raccolta finale il buffer crash è vuoto e tutti i 16 record di uscita conservati indicano arresti forzati richiesti dall’utente, coerenti con i cold controllati. È una finestra osservata limitata, non l’assenza di ogni crash storico. I warning grafici dell’host sono conservati; il dispositivo fisico personale non è stato toccato.

La campagna funzionale finita è conclusa entro questi confini. Le prove private e i candidati superati restano conservati in attesa della pulizia coordinata. Nessun risultato implica assenza assoluta di bug, soluzione di Latios, correzione universale del marker o miglioramenti misurati di FPS/input lag.
