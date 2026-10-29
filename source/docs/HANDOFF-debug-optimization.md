# Handoff per debug e ottimizzazione

Metodo operativo per ridurre freeze, arresti, latenza, scatti e caricamenti mantenendo funzioni, velocità di gioco e integrità dei salvataggi. Usarlo per la ROM e, con il diverso confine indicato sotto, per il core o il frontend di melonDS. La priorità è spiegare un difetto e verificare una correzione, non ampliare indiscriminatamente il numero di file analizzati.

Questo documento è pubblico e riutilizzabile. ROM, save, BIOS, dump, APK personali e trace restano privati. Il [passaggio di consegne 1.3](HANDOFF-1.3.md) indica lo stato corrente e i rapporti da leggere. Il [piano del 28 ottobre](deep-debug-2026-10-28-plan.md) e il [rapporto](deep-debug-2026-10-28.md) conservano lo stato di quella specifica indagine; questa guida descrive il metodo.

## Mandato e confini

Il lavoro procede sul Mac per diagnosi, costruzione e regressioni. Le prove sul dispositivo Android vengono dopo, per confermare proprietà che dipendono dal suo frontend, driver, schermo, controller e stato termico. Una prova sul Mac non certifica quelle proprietà.

Rispettare `AGENTS.md` e [source/README.md](../README.md). In questo repository si lavora direttamente su `main`, preservando indice e modifiche altrui; niente branch, worktree o PR. Un thread dedicato all'emulatore deve prima leggere le istruzioni del proprio repository. Non assumere autorizzazione a modificare l'altro progetto o a pubblicare.

Tenere distinte tre attività:

- correzioni di difetti dimostrati;
- ottimizzazioni a comportamento equivalente;
- nuove funzioni o cambi di bilanciamento, assegnati a un progetto separato.

Ridurre righe o dimensioni del sorgente non dimostra velocità. Misurare il lavoro eliminato e la sua incidenza. Una cache può ridurre il costo e aumentare codice o memoria; una deduplicazione può ridurre il codice e aumentare chiamate o invalidazioni. Valutare l'effetto finale e la manutenzione insieme.

## Ricerca e riferimenti

Per ogni problema cercare prima fonti applicabili alla versione e al componente effettivi: codice e documentazione degli autori, commit con test, issue con riproduzione, articoli scientifici o testi degli autori. Una testimonianza con sintomi simili è un indizio; una issue chiusa non dimostra che la correzione sia nel nostro binario. Annotare URL, revisione/data, ipotesi suggerita e prova locale che potrebbe smentirla.

Riferimenti metodologici consultati il 28 ottobre 2026:

| Riferimento | Applicazione nel lavoro |
| --- | --- |
| Brendan Gregg, *Systems Performance*, e [Performance Analysis Methodology](https://www.brendangregg.com/methodology.html) | Definire il problema e il carico, scomporre la latenza, profilare il componente che consuma il tempo. Il riferimento online dell'autore documenta il metodo utilizzato; non si dichiara consultato integralmente il libro |
| Gregg, [USE Method](https://www.brendangregg.com/usemethod.html) | Per CPU, memoria, I/O e code verificare occupazione, saturazione ed errori; una media bassa può nascondere picchi. Adattare le domande all'emulatore senza applicare automaticamente una checklist server |
| Kalibera e Jones, [Rigorous Benchmarking in Reasonable Time, ISMM 2013](https://kar.kent.ac.uk/33611/) | Separare variabilità fra build, processi e iterazioni; investire le ripetizioni dove nasce l'incertezza e riportare l'effetto con la sua incertezza |
| [SPEC CPU 2017 Run and Reporting Rules](https://www.spec.org/cpu2017/Docs/runrules.html) | Prendere i principi di risultato corretto, configurazione dichiarata e riproducibilità. I nostri test non sono benchmark SPEC né risultati certificati SPEC |
| Android, [profileable](https://developer.android.com/guide/topics/manifest/profileable-element) | Verificare i permessi di profiling e usare build rappresentative; una build debug non è automaticamente un riferimento prestazionale |
| Perfetto, [Android tracing](https://perfetto.dev/docs/learning-more/android) e [FrameTimeline](https://perfetto.dev/docs/data-sources/frametimeline) | Registrare e analizzare trace hardware; controllare superfici e supporto prima di interpretare i dati di presentazione |
| SQLite, [How SQLite Is Tested, sezioni 3.2–3.4](https://www.sqlite.org/testing.html) | Esempio di errori I/O controllati, riapertura e verifica dell'integrità dopo il guasto. Adattare il principio alle strutture reali del save; non introdurre un database né attribuire alla ROM le garanzie di SQLite |

Esempi concreti da usare come piste, non come diagnosi:

- Il [tracker Android, issue 1315](https://github.com/rafaelvcaetano/melonDS-android/issues/1315), riporta problemi di scala OpenGL e un intervento del manutentore. Serve a motivare un confronto del renderer e della scala, non a concludere che ogni scatto urbano abbia quella causa.
- La [wiki ufficiale JIT](https://github.com/rafaelvcaetano/melonDS-android/wiki/System) descrive il confronto con interprete per isolare difetti del ricompilatore. È documentazione storica: verificare codice e versione correnti prima di applicarne le conclusioni.
- Il [caso locale Mew](deep-debug-2026-10-28.md) dimostra un errore di durata del contesto: un worker movimento continua dopo la fine dello script. La correzione sincronizza quel confine; non giustifica timeout generali né la stessa modifica su Latios.

Per riusare una soluzione esterna: confrontare precondizioni, architettura, versione, formato dei dati e test. Riprodurre localmente il difetto e controllare licenza/attribuzione se si riusa codice. Non aggiornare dipendenze o applicare patch in massa soltanto perché più recenti.

## Il ciclo di indagine

### 1 Identificare ciò che viene provato

Registrare commit e delta locale, hash ROM/eseguibile, lingua, fixture originale, toolchain e flag, core, renderer, JIT, opzioni, cheat, RTC e percorso input. Una label di versione non identifica un binario personalizzato.

Conservare gli originali; usare copie per setup e scritture. Hashare le fixture prima e dopo. Se si usa warp, modifica RAM o un altro setup artificiale, elencare ogni intervento e dimostrare che il campo è tornato stabile prima della prova. Uno screenshot ottenuto fuori mappa non prova correttezza del rendering.

### 2 Disegnare soltanto il flusso interessato

Partire da una categoria e seguirne ingressi, consumatori, proprietà e durata dei dati. Per esempio: input → script → movimento → lotta, oppure richiesta SAVE → Borsa → journal → commit → messaggio. Indicare chi crea, usa, invalida e libera ogni stato condiviso. In questa ROM contenuti e persistenza sono archivi e strutture native, non un database remoto.

Separare stato persistente, stato di sessione e cache. Verificare errori di proprietà, attese fra task, limiti, ritorni ignorati e invalidazioni sul confine sospetto prima di una revisione riga per riga dell'intero progetto.

### 3 Formulare una domanda falsificabile

Scrivere prima della prova: sintomo, ultima operazione completata, ipotesi, osservazione attesa se vera, risultato che la smentirebbe. Una sola modifica sperimentale per volta.

Per freeze: osservare progressione ARM9/ARM7, task/callback, interrupt, ultimo evento e possibilità di input. PC in HALT, immagine ferma o audio continuo presi da soli non identificano la causa. Per un crash host, raccogliere processo, segnale/exception e stack; non chiamarlo crash ROM.

### 4 Costruire riproduzione e controllo

Una riproduzione deve raggiungere il difetto; il controllo deve escludere una spiegazione alternativa. Un controllo senza interazione distingue evento guasto da scena già compromessa. Un esito inatteso del debugger o del preparatore invalida il caso, non diventa un bug del gioco.

Distinguere esperimento diagnostico da benchmark di ottimizzazione. Camminare contro stare fermi nella stessa città osserva differenze di lavoro, ma esegue funzioni diverse: non può dimostrare un miglioramento. Nel confronto baseline/candidato devono coincidere azioni, carico e risultato semantico.

### 5 Validare prima lo strumento

Usare casi sintetici con conteggi e durate noti; verificare attivazione/disattivazione, finestra di campionamento, overflow/riavvio dei contatori, ARM/Thumb, ritorni, annidamento e dati mancanti quando applicabili. Un ritorno deve corrispondere al contesto e allo stack giusti.

La strumentazione osserva senza cambiare registri, memoria o contabilizzazione del tempo guest. Le copie del core usate per osservare vanno identificate e tenute separate dal banco di riferimento. Confrontare lo stato semantico con osservazione disabilitata. Una trace vuota, un contesto incompleto o uno skip non sono un successo.

### 6 Misurare il confine corretto

| Metrica | Definizione necessaria | Cosa non dimostra |
| --- | --- | --- |
| Risposta guest | Frame da input iniettato a polling, cambiamento di stato e immagine; riportare separatamente questi endpoint | Latenza fisica controller–schermo |
| Lavoro guest | Visite, operazioni, byte, allocazioni, cicli emulati; specificare inclusioni di callees, IRQ e attese | Cicli reali di un DS o tempo del JIT Android |
| Caricamento | Richiesta → scena pronta e capace di accettare input; prima apertura e aperture successive separate | Cache OS fredda dopo un semplice riavvio dell'app |
| Host | CPU attiva, tempo trascorso, attese, I/O, allocazioni e rendering del processo identificato | Velocità del gioco guest o prestazioni di un altro dispositivo |
| Presentazione | Cadenza e ritardo della superficie corretta con timestamp validi | Responsività del tasto fisico senza quell'endpoint |
| Persistenza | Commit riuscito, messaggio corretto, dati dopo Continue/SAVE/cold restart | Compatibilità generale provata da un savestate |

I contatori del main loop non sono automaticamente contatori VBlank. Campioni PC a fine frame non sono conteggi di visite. Un ciclo temporale include anche possibili attese: confrontarlo con le istruzioni osservate. Non sommare intervalli inclusivi annidati per stimare il totale.

### 7 Gestire la variabilità

Separare esperimenti deterministici guest da timing host. Ripetere uno stesso snapshot prova riproducibilità del caso, non copertura di giocatori o salvataggi indipendenti. Il savestate è ammesso per confronti sulla stessa ROM/core; non caricarlo fra ROM diverse, perché può ripristinare vecchio codice.

Per timing host eseguire un pilot, registrare riscaldamento e avvii nuovi, alternare o randomizzare baseline/candidato e tenere costanti le condizioni. Non fare contemporaneamente compilazioni, archiviazioni, altre campagne o catture video pesanti. Separare la campagna con tracing da quella a basso impatto.

Cinque coppie sono un primo controllo, non un requisito universale né una base sufficiente per dichiarare un p95 affidabile. Scegliere numero di ripetizioni e precisione richiesta dopo il pilot e prima del confronto finale. Analizzare variabilità fra processi, non trattare tutti i frame consecutivi come campioni indipendenti. Se si stimano intervalli, usare unità indipendenti o blocchi che rispettino l'autocorrelazione.

Pubblicare campioni, esclusioni motivate, mediana, distribuzione e picchi pertinenti; i quantili richiedono copertura adeguata. Non selezionare la corsa migliore. Registrare anche esiti invariati o peggiori. Un guadagno inferiore al rumore è inconclusivo.

### 8 Correggere o ottimizzare il costo dimostrato

Per un bug costruire prima una prova che fallisca sul comportamento errato, poi una correzione minima e il controllo che passa. Per le prestazioni dimostrare prima che il carico desiderato sia stato eseguito e individuare il costo dominante.

Preferire, dove la misura lo giustifica: evitare lavoro ripetuto, riusare dati ancora validi, ridurre copie/I/O/allocazioni, aggiornare UI solo al cambiamento, limitare ricerche e controlli ridondanti. Ogni cache richiede proprietario, validità e invalidazione verificati. Ogni limite deve conservare il risultato corretto; non troncare lavoro necessario.

Stimare il limite del beneficio prima di investire. Se una parte è il 20% del tempo totale misurato, eliminarla interamente può dare al massimo un fattore 1,25 sullo stesso carico. Questa applicazione della legge di Amdahl evita di promettere grandi guadagni da una funzione marginale; non sostituisce il confronto finale.

Non accettare come ottimizzazione: frame saltati, funzioni disattivate, animazioni accelerate, frequenza di aggiornamento cambiata, errori ignorati, timeout che nascondono il difetto, save parziali o controlli di integrità rimossi. Un intervento di questo tipo cambia il requisito e richiede un progetto distinto.

### 9 Verificare effetti e interazioni

Usare test proporzionati al rischio: predicato puro, codice compilato, blob ARM, caller reale, runtime e raw save rispondono a domande diverse. Un mock della flash prova la gestione del risultato, non un'interruzione fisica dello storage. Un ritorno corretto non prova il messaggio mostrato dalla UI.

Per persistenza verificare letture/scritture fallite, commit interrotto, recupero, retry e notifica. Su copie raw: Continue → azione → SAVE nativo → nuovo processo → confronto di progressione, squadra, box, inventario esteso, impostazioni e dati della funzione. Coprire EN/IT, save senza Plus e con Plus, e percorsi attivi toccati. Mai reset o perdita di dati per far passare una migrazione.

Il guasto simulato deve rispettare il contratto della primitiva nativa. Se un
errore fisico entra in una schermata fatale senza ritorno, simulare soltanto
`FALSE` non prova recupero hardware. Un rifiuto di proprietà o un readback
discordante dopo I/O riuscito permette invece di esercitare un ritorno
recuperabile, quando il codice lo prevede. Verificare insieme stato dei banchi,
contatore, record, messaggio, risorse e tentativo successivo. Anche le primitive
simulate richiedono un oracolo: il CRC dell'header ROM e quello dei dati nativi
possono usare algoritmi diversi, pur avendo entrambi 16 bit.

Per una risorsa liberata in differita, distinguere richiesta e completamento:
seguire il puntatore realmente posseduto dall'app, la callback nella coda,
la sua rimozione e l'ordine rispetto alla distruzione dell'heap. Un'icona
scomparsa non prova che la memoria sia stata liberata; un indirizzo di task
riutilizzato non prova che il vecchio task sia ancora vivo. Provare anche input
già premuto, rilascio e nuova conferma, ritorno e riapertura nello stesso processo.

Per emulazione verificare anche equivalenza di CPU, memoria, output video/audio e ordine degli eventi nei confini interessati, oltre al tempo. Testare invalidazioni JIT/cache e interazioni fra thread quando sono parte della modifica. Sanitizer o build debug servono alla correttezza, con timing tenuto distinto dalla build ottimizzata.

### 10 Accettare e registrare

Una modifica prestazionale è accettata quando il risultato è equivalente, la misura è valida, il guadagno supera l'incertezza ed è utile nell'interazione interessata, senza peggiorare picchi o stabilità. Una correzione è accettata quando la riproduzione precedente passa, il controllo resta corretto e le regressioni pertinenti passano. Rilevare un costo non obbliga a modificarlo.

Revisione indipendente sulle parti rischiose; per questo progetto Sol 6.1 implementa e Astra approfondisce o rivede. Deleghe con file/ambito precisi, nessun edit concorrente sugli stessi componenti e nessuna campagna timing concorrente. Leggere il registro prima di riprendere per non rifare lavoro concluso.

In questo repository eseguire i controlli appropriati e prima di un commit `git diff --check` e `python3 .github/check_public.py`; registrare pass, fail, skip e motivo. Nuovi file pubblici richiedono manifest e indice espliciti. Una build riuscita non è prova runtime; una prova locale non equivale a release pronta.

## Ricerca di difetti latenti e accorpamenti sicuri

La qualità include integrità dei dati e sicurezza della memoria, oltre alle prestazioni. Distinguere un errore di robustezza da una vulnerabilità: per quest'ultima servono un input controllabile, un confine di fiducia attraversato e un impatto dimostrabile. Non assegnare gravità di sicurezza soltanto perché esiste un crash.

Partire da due o tre confini ad alto rischio, scelti dal flusso reale: buffer/lunghezze provenienti da file; durata di task, finestre e cache; salvataggi con più partecipanti; callback che sopravvivono a cambio scena; concorrenza nel frontend. Per ogni confine scrivere gli invarianti e provare le transizioni, inclusi annullamento, errore, retry, riapertura e ordine insolito delle operazioni. Un test combinatorio deve derivare da dipendenze concrete, non dal prodotto cartesiano di tutte le opzioni.

| Strumento o tecnica | Domanda a cui risponde | Limite da registrare |
| --- | --- | --- |
| Analisi statica e compilatore | Puntatori nulli, errori ignorati, limiti, overflow, risorse non rilasciate, percorso verso un uso invalido | Possibili falsi positivi; controllare raggiungibilità e build reale |
| Breakpoint/watchpoint, GDB/LLDB, trace ARM | Chi ha scritto lo stato errato, quale callback è ancora viva, ultimo confine valido | Può cambiare timing; alcuni watchpoint non sono supportati dal banco |
| [AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html) e [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html) | Memoria fuori limite, use-after-free e comportamento C/C++ indefinito nei percorsi eseguiti | Richiedono build compatibili; non applicare direttamente ASan host a un blob DS freestanding e dichiarare validata la ROM |
| [ThreadSanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html) | Data race nei percorsi host concorrenti osservati | Build/campagna separata, supporto piattaforma da verificare; non dimostra assenza di race e non misura prestazioni release |
| [Fuzzing guidato da copertura](https://llvm.org/docs/LibFuzzer.html) | Input limite e combinazioni inattese in parser o API circoscritte | Corpus sintetico, memoria/tempo limitati, riproduzione e riduzione dell'input; copertura non equivale a correttezza |
| Test a proprietà e a stati | Invarianti dopo sequenze di operazioni; encode/decode, rifiuto senza mutazione, rollback, idempotenza | Un round-trip con lo stesso errore in encoder e decoder può passare: serve anche un oracolo indipendente |
| Fault injection e mutanti | Se la protezione rileva davvero errore, attesa mancante, scrittura incompleta o invalidazione assente | Baseline verde obbligatoria; distinguere errore sintetico dal comportamento fisico dell'I/O |
| Differential testing | Confronto fra implementazione originale/candidata o interprete/JIT | Ammesse solo differenze esplicitamente previste; due implementazioni possono condividere lo stesso errore |
| REA e disassemblaggio | Comportamento del binario realmente distribuito rispetto ai sorgenti | Usare quando il binario è necessario; registrare provider disponibili e distinguere decompilazione statica da esecuzione |

Gli strumenti sono una scelta motivata dal problema, non una lista da eseguire integralmente. Riutilizzare test e corpus esistenti. I sanitizer operano dove esiste una build host pertinente; confermare poi i difetti che toccano il gioco con il codice ARM o il runtime effettivo. Per REA controllare le capacità reali della sessione: una skill installata non prova che il motore nativo sia disponibile.

Valutare accorpamenti di funzioni, stringhe, costanti e import solo dopo averne identificato significato, proprietario e durata. Verificare:

- Le copie rappresentano lo stesso contratto, oppure due regole solo apparentemente simili?
- Stringhe localizzate hanno identici placeholder, codifica, terminatori e controlli? I loro ID sono referenziati da script o tabelle?
- L'accorpamento cambia identità dei puntatori, mutabilità, allineamento, collegamento, ordine d'inizializzazione o disponibilità durante caricamento/scaricamento degli overlay?
- Un import Python è parte del builder host oppure codice eseguito nel gioco? Ottimizzare il primo non dimostra meno lag durante la partita.
- La duplicazione è intenzionale per una rilettura indipendente? Qui applier e verificatore non devono condividere automaticamente la costante sbagliata.
- Diminuiscono davvero byte residenti, lavoro, I/O o manutenzione? Controllare output del compilatore/linker prima di supporre che due stringhe nel sorgente occupino due copie nel binario.

Un candidato emerso dall'analisi riceve uno stato esplicito: ipotesi, riprodotto, causa dimostrata, corretto, verificato, oppure non confermato nel perimetro provato. Allegare il caso minimo e i limiti; non promettere codice privo di ogni bug.

## Pacchetto minimo per ogni risultato

Conservare in una directory privata durevole:

1. `case.json`: identità, configurazione, ipotesi, metrica primaria, soglia di accettazione, script/scenario e risultato atteso.
2. `inputs/`: fixture originali immutabili e copie, con provenienza e hash; eventuali interventi di preparazione separati.
3. `raw/`: trace, log, dati completi e immagini necessarie alla verifica dello stato.
4. `analysis/`: parser/calcoli ripetibili, risultati per corsa e riepilogo con esclusioni.
5. `review.md`: causa dimostrata, diff, test, limiti e decisione.
6. `SHA256SUMS` o manifest equivalente: rilettura delle copie e corrispondenza sorgenti–binario–risultati.

È uno schema da adattare, non l'affermazione che ogni campagna passata lo implementi già. Un clone sullo stesso disco protegge dalla pulizia della cartella temporanea, non dalla perdita del disco. I riferimenti nel rapporto pubblico devono permettere di capire la prova senza esporre dati personali o proprietari.

## Adattamento al thread melonDS

Tenere distinti core, frontend e piattaforma. Prima fissare app/core/submodule e differenze locali, poi scegliere un solo caso. Il confronto interprete/JIT può isolare semantica CPU; software/OpenGL e scala possono isolare rendering; audio/pacing e sospensione/storage sono percorsi separati. Nessuna di queste variazioni va combinata nella prima controprova.

Sul Mac sono possibili test del core e del frontend disponibile, analisi statica e regressioni. Un APK Android e le sue impostazioni non ricreano driver, controller o schermo del dispositivo. Una trace acquisita in precedenza può essere analizzata offline ma non misura una build nuova. Per prestazioni Android usare in seguito build ottimizzate comparabili e simboli corrispondenti; ADB non implica accesso a preferenze private o profiler.

Un bug riprodotto solo con strumentazione richiede un controllo dello strumento. Un bug presente in interprete e JIT non è automaticamente del gioco; uno assente sul Mac non è automaticamente del driver. Conservare spiegazioni alternative finché le prove le distinguono.

### Acquisizione riutilizzabile da Android al Mac

Un solo coordinatore controlla il dispositivo e le finestre temporali. Prima
di avviare il gioco, identificare il package realmente usato, estrarre l'APK
installato e registrarne hash, firma e Build ID delle librerie. Individuare
ROM e raw mediante i percorsi effettivi dell'app; copiare con il writer fermo
e verificare hash sorgente prima, copia locale e sorgente dopo. Conservare
configurazioni esportate, BIOS, mapping input, override per gioco, cheat
selezionati con codice effettivo, RTC, layout e display. Un XML di cheat non
prova quali codici siano attivi nel database dell'app.

Le autorizzazioni SAF non si trasferiscono copiando gli URI. Su un AVD nuovo
riconcedere le cartelle dall'interfaccia, verificare il salvataggio associato
e documentare ogni adattamento del layout o del controller. Pareggiare API,
ABI e page size dove possibile; dichiarare separatamente driver, GPU, display,
storage e alimentazione differenti. Conservare il file iniziale e quello
scritto tramite SAVE, poi provare Continue in un nuovo processo. Nessun
savestate sostituisce questo controllo.

Prima dei tempi, verificare anche il backend effettivamente utilizzabile dopo
l'importazione: una preferenza conservata può diventare incompatibile e il
selettore può essere nascosto dal controllo delle capacità grafiche. Conservare
log del lancio, identità del processo ed `ApplicationExitInfo`; un ritorno alla
libreria ROM da solo non distingue errore gestito e terminazione per segnale.
Un profilo alternativo deve avere nome, differenze ed export propri. La
[documentazione Android sui backend grafici](https://developer.android.com/studio/run/emulator-acceleration)
descrive la dipendenza dal driver host; la
[documentazione di ApplicationExitInfo](https://developer.android.com/reference/android/app/ApplicationExitInfo)
precisa come leggere motivo e segnale di uscita. Il backend alternativo può
abilitare regressioni funzionali, senza rendere equivalenti le prestazioni.

Validare ogni raccoglitore con un controllo negativo: se la superficie continua
a presentare immagini durante la pausa, il suo conteggio non è un proxy dei
frame guest. Verificare nei payload Perfetto processo ed eventi richiesti;
un file valido con zero eventi scheduler significa dato assente, non CPU
inattiva. Se si usa `/proc`, controllare PID e starttime, frequenza dei tick,
stderr, durata e quantizzazione. Il totale processo include già i thread:
non sommarlo di nuovo. Il 100% su scala un core non rappresenta tutta la
capacità del dispositivo. Conteggi aggregati non misurano i picchi o il p95.

Separare screenshot/video diagnostici dalle finestre di prestazione. Input
iniettato con ACK e rilascio neutro può rendere ripetibile una prova funzionale,
ma non misura tasto fisico–display; verificarne anche la risposta del gioco.
Escludere esplicitamente corse sovrapposte o con cambio scena e conservarne i
dati. Ripristinare le preferenze temporanee, ricontrollare gli originali e
rimuovere solo artefatti propri già copiati e verificati.

Il risultato è un laboratorio per riproduzione e regressioni, non una copia
dell'hardware. Un eventuale scarto Mac–dispositivo richiede la stessa metrica
qualificata e lo stesso lavoro, con ripetizioni e limiti per scenario. Non
ricavare un moltiplicatore universale da FPS, percentuali CPU o una singola
scena. Per isolare un contributo sensibile alla scala si può alternare compute
6x/1x mantenendo il resto fisso: è una controprova diagnostica, non
un'ottimizzazione a qualità invariata, e da sola non isola il tempo GPU.

## Prompt di avvio per un altro thread

> Leggi questo handoff, le istruzioni del repository e lo stato delle prove esistenti. Riprendi il mandato di debug profondo e ottimizzazione a parità di funzionalità, prima sul Mac; la validazione hardware seguirà. Non rifare attività già concluse. Separa core, frontend e gioco, fissa versioni e fixture, scegli un solo problema prioritario e una metrica con endpoint precisi. Cerca fonti primarie e casi analoghi pertinenti, poi formula un'ipotesi falsificabile e costruisci riproduzione e controllo. Valida lo strumento prima della misura, correggi solo il costo o il difetto dimostrato, verifica equivalenza e regressioni, registra incertezza e limiti. Sol 6.1 per implementazione, Astra per ragionamento e revisione. Conserva dati privati fuori da Git e mantieni un registro riprendibile. Non pubblicare senza il relativo mandato. Produci un risultato concreto verificabile, non una lista generica di possibili ottimizzazioni.
