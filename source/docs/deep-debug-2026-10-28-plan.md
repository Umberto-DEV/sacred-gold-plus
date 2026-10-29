# Piano di debug profondo e stabilità

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Le caselle distinguono attività eseguite e prove ancora necessarie.

**Goal:** isolare i freeze segnalati in 1.2.5, impedire regressioni di salvataggio nella 1.3 e ridurre lavoro misurabile senza cambiare funzioni, velocità di gioco o compatibilità.

**Architecture:** seguire tre confini: evento di campo → lotta, Borsa → journal → commit nativo, input → lavoro CPU/I/O → risposta visibile. Censimento breve; approfondimento guidato da controprove, non scansione indiscriminata.

**Tech Stack:** C/Thumb ARM946E-S, Python, Capstone/Unicorn, pret/pokeheartgold al commit previsto dal progetto, melonDS headless e configurazione Android acquisita dal dispositivo nel pacchetto privato.

**Spec:** [Requisiti e diagnosi](deep-debug-2026-10-28.md), sezione Requisiti. L'utente autorizza coordinamento autonomo, Sol 6.1 per implementazione e Astra per ragionamento/revisione.

## Global Constraints

- Lavorare direttamente su `main`; nessun branch, worktree o PR.
- Preservare le 86 modifiche già nell'indice all'inizio dell'indagine; nessun commit cumulativo del lavoro preesistente.
- ROM, salvataggi, dump, percorsi personali e note private non entrano nei file pubblici.
- Preservare progressione, Pokémon, inventario esteso e impostazioni Plus. Nessun reset, rimappatura di flag o cambiamento del formato per aggirare un problema.
- Distinguere 1.2.5 pubblicata, personalizzazione del dispositivo e 1.3 privata mediante impronte. I file di una release non vengono sostituiti.
- Nessuna dichiarazione di compatibilità basata su savestate; servono copie raw, Continue, SAVE nativo e riavvio a freddo.
- Prima di accettare una modifica: diff, `git diff --check`, `python3 .github/check_public.py`, test pertinenti. Aggiungere esplicitamente nuovi file pubblici a manifest e indice.
- Nessuna ottimizzazione accettata sulla sola riduzione delle righe di codice o sugli FPS dell'emulatore.

## Review Focus

1. Record Borsa estraneo nel banco non attivo: rifiutare l'attivazione training senza mutare nulla; il salvataggio ordinario deve restare possibile (Task 1).
2. Record uniforme o scrittura Borsa interrotta riconoscibile: non rifiutare salvataggi precedentemente supportati (Task 1).
3. Training già attivo con errore di scrittura: non perdere il journal né permettere un commit incoerente; distinguere questa protezione dalla corretta comunicazione dell'errore (Task 1 e 4).
4. Rendering vivo ma script bloccato: richiedere il raggiungimento di uno stato giocabile e risposta all'input (Task 2).
5. Run più veloce perché il percorso non è stato eseguito: verificare opzioni attive, scena, numero di operazioni e risultato semantico identici (Task 3).

## Task 0: Identità, censimento e baseline

**Files:** leggere `source/README.md`, `sgp12/costruisci.py`, `sgp13/build.py`, contratti e report precedenti. Scrivere il rapporto collegato sopra.

- [x] Registrare branch, stato iniziale e salvare una copia privata del diff staged.
- [x] Distinguere categorie, produttori/consumatori, stato persistente e temporaneo.
- [x] Eseguire una baseline Class A con compilatore obbligatorio, registrando separatamente skip e Class B lanciate dal runner.
- [x] Verificare fonti primarie online: autore dell'hack, tracker degli emulatori e documentazione degli strumenti di misura.
- [x] Identificare ROM, banco, toolchain e fixture disponibili senza modificare gli originali.

## Task 1: Ammissione training coerente con il writer Borsa

**Files:** modificare `source/features/training-native/ownership.c`, `ownership.h`, `runtime.c`; creare `source/features/training-native/test/test_save_composition.py`; integrare `source/run_tests.py` e documentare in `source/features/training-native/README.md`. Il coordinatore cura manifest pubblico e rapporto.

**Interfaces:**
- Consumes: `READ(address, destination, length)` già usata dal runtime; contratto di `cap_record_uniform` e `cap_record_owned_prefix` in `features/capacita-borsa/sorgenti/journal.c`.
- Produces: `int training_bag_claimable(const unsigned char bytes[452])`, predicato puro; `storage_ready()` continua a essere interno e read-only.
- Ammissione: leggere 452 byte a `0x30000`, `0x30200`, `0x70000`, `0x70200`. Ogni lettura deve riuscire; ogni record deve essere uniforme oppure riconoscibile secondo il writer Borsa. Conservare anche tutti i controlli training esistenti.
- Un rifiuto conserva il codice servizio 8, lascia `enabled=0`, denaro/Pokémon/journal invariati e non scrive flash. Non cambiare `training_save` né il layout persistente.

- [x] Trasformare il probe ARM composto dell'indagine in test pubblico ROM-free, con percorsi relativi e input sintetici. Eseguire davvero i blob di produzione training e Borsa; dichiarare le seam OS/flash/native commit.
- [x] Test rosso `test_foreign_bag_destination_rejects_activation_and_keeps_native_save`: ciascun indirizzo estraneo, entrambi banchi attivi; servizio 8, training inattivo, nessuna scrittura durante ammissione, native save ancora raggiunto. Separare le eventuali scritture Borsa del successivo save dall'ammissione.
- [x] Test di controllo: record uniformi `00/FF/altro`, magic completo posseduto e prefisso magic interrotto con coda FF sono ammessi; non uniforme estraneo o prefisso con coda estranea rifiutato; fallimento READ in ciascun indirizzo rifiutato. Confrontare il predicato con le funzioni Borsa reali, senza ricopiare la loro logica nel test.
- [x] Implementare solo il predicato e la verifica dei quattro record prima dell'attivazione. Nessun polling per frame o nuova allocazione heap; buffer di stack allineato e limitato.
- [x] Verificare il test composto, le suite ownership/transazione, compilazione nel compartimento fisso e la Class A con compilatore obbligatorio. Conservare la prova che un journal già attivo continua a bloccare il commit se la persistenza fallisce.
- [x] Ricostruire due candidati privati EN/IT con nuovi nomi, rilettura e impronte dei sorgenti; ripetere test nativi pertinenti.
- [x] Revisione indipendente Astra: parità del criterio Borsa, ordine dei controlli, assenza di mutazioni, test discriminanti e limiti. Nessuna pubblicazione implicita.

## Task 2: Separare attesa evento, blocco lotta e crash host

**Files:** leggere `features/manutenzione/verifica_totem.py`, `features/debug/campo/banco.py`, `verifiche/rileva_crash.py`, script 115/776 dalla ROM privata e implementazioni native da pret. Probe e trace restano privati finché non sono generalizzati e privi di dati estratti.

**Interfaces:** record di osservazione con impronta ROM/save, lingua, provenienza setup, frame, PC ARM9/ARM7, vblank, script PC/callback, maschera movimento, task/app attiva, input e stato atteso.

- [x] Decodificare separatamente Mew e Latios/Latias, verificare salti/specie/livelli e individuare l'ultima operazione completata prima di ciascuna attesa.
- [x] Eseguire il vero `LockAll` e il callback nativo su ARM EN/IT: oggetto con movimento pendente mantiene la maschera; togliere solo quel bit deve sbloccare l'attesa. Questo prova il punto diagnostico, non riproduce il freeze utente.
- [x] Verificare gli strumenti locali e avviare una fixture derivata dal save avanzato IT: l'utente autorizza setup/cheat su copie. Conservare provenienza, modifiche minime e controllo senza interazione; distinguere evento ricreato da identità del freeze segnalato.
- [x] Riprodurre Mew su copia derivata dal raw avanzato: due crash identici dopo «Myuu!» e conferma dell'utente che si tratta del proprio episodio. Controllo senza A vivo; data abort e worker movimento pendente dopo distruzione dello script provati.
- [ ] Riprodurre Latios nel bianco dopo transizione e prima dei Pokémon. L'acquisizione successiva del dispositivo conserva ambiente e raw attuale, ma non una nuova cattura del freeze; non assumere la causa trovata per Mew.
- [x] Eseguire un primo controllo derivato Latios sulla 1.2.5 IT: dialoghi e Sì reali, nessun edit a Borsa/flag; transizione e ingresso in lotta passano. Il freeze segnalato resta non riprodotto.
- [ ] Osservare `ctx.native_ptr`, `ctx.script_ptr` e `0x021D415C` per almeno 120 frame dopo interazione. Distinguere player, oggetto parlato, follower e partner. Verificare fase cry/movement e ingresso/uscita battle task.
- [ ] Prima di attribuire il blocco a LockAll, controllare progresso ARM9/ARM7, vblank e interrupt. Su Latios distinguere uscita dal campo, caricamento overlay e inizializzazione grafica della lotta. Il suono fisso non è evidenza di audio normalmente funzionante.
- [ ] Se si usa warp o setup strumentato, eseguire prima il controllo sulla stessa ROM, attendere campo stabile e dichiarare le modifiche. Un errore del debugger non conta come regressione di gioco.
- [ ] Con una riproduzione deterministica, cambiare una sola variabile: animazioni Plus, poi difficoltà, poi configurazione emulatore. Confrontare originale e candidato sulla stessa fixture e timeline.
- [ ] Correggere esclusivamente il produttore dello stato pendente dimostrato. Vietato trasformare timeout o `ReleaseAll` forzato in una presunta soluzione. Fuga, sconfitta, cattura, ripetizione e SAVE/restart diventano regressioni pertinenti.

### Task 2M: Durata del movimento nei tre trasferimenti Mew

**Files:** nuovi `sgp13/mew.py`, `sgp13/test_mew.py` e prove con fixture privata;
integrare `sgp13/build.py` dopo il titolo e prima di caught, e `run_tests.py`.
Il coordinatore cura manifest, rapporto e README; nessuna modifica al builder
pubblicato 1.2.5 o ai salvataggi.

- [x] Controprova privata minima: una WaitMovement al primo trasferimento elimina l'abort sulla stessa timeline e restituisce il controllo al player.
- [x] Inserire WaitMovement ai tre confini confermati (offset originali 191, 260, 325), con hash completo del membro 115 e trasformazione unica degli offset originali.
- [x] Preservare entry ID, flag, argomenti non relativi, movimenti e altri membri/file; rifiutare preimmagini estranee e doppia applicazione. Verificare la rilettura.
- [x] Test sintetici ROM-free di inserzioni, salti avanti/indietro, chiamate e puntatori movimento; prove EN/IT sul flusso originale, corretto e mutanti con ciascuna attesa rimossa.
- [x] Ricostruire candidati privati EN/IT e verificare le tre fughe, il quarto incontro, fuga dalla lotta e SAVE/cold restart intermedio su copie. Dopo Continue da raw, campo visibile, input normale e dati persistenti coincidono. Stessa fixture avanzata IT in entrambe le lingue; spostamenti diagnostici artificiali, cattura/KO e dispositivo non coperti.
- [x] Revisione indipendente Astra del codice, suite e controlli pubblici; nessuna pubblicazione implicita. I gate runtime sono separati dalla revisione del codice.

## Task 3: Misurare prima di snellire

Completato un primo esperimento sul confine `FieldSystem_Control` e il ritorno
al caller nella stessa scena di Fiordoropoli, cammino contro input neutro:
24 chiamate complete per caso, controlli sintetici, scena, input e SRAM validi.
Questo confronto osserva differenze di lavoro; non è un benchmark di
ottimizzazione, perché le azioni sono diverse. Il costo inclusivo comprende
anche interrupt e attese; i sei picchi durante il cammino non sono ancora
attribuiti a una funzione o a un costo dominante della città.

**Files:** riusare `runtime/main.cpp`, `hg_trace.h`, i tools delle feature Borsa/Squadra/ANIM2 e la configurazione del banco; eventuale strumentazione nuova necessita di un caso controllato prima dell'implementazione.

**Interfaces:** una riga per ripetizione/scena con frame input accettato, frame risposta, frame primo input nuovamente accettato, visite alla funzione sospetta, byte letti/allocazioni se osservabili, tempo CPU host e confini di misura.

- [ ] Scegliere un solo percorso caldo verificato: movimento nella mappa problematica oppure apertura Borsa/Squadra durante la stessa lotta. Separare prima apertura e successive.
- [x] Validare la misura locale su due brevi tratti di movimento, Fiordoropoli e Fiorpescopoli, ROM 1.2.5 IT: sei offset temporali per scena, polling input e posizione continua campionati per frame. Nessun confronto candidato o miglioramento ancora dimostrato.
- [x] Validare osservatore e verificatore e raccogliere una coppia diagnostica cammino/neutro sul confine scelto; nessuna modifica prestazionale.
- [ ] Fissare RTC, save, opzioni, renderer, core e input; usare un pilota per stimare la variabilità e dimensionare le coppie baseline/candidato, con ordine bilanciato. Nessun runtime concorrente durante timing host.
- [ ] Per responsiveness riportare frame guest da input accettato a stato/immagine attesa; per caricamento da richiesta a stato che accetta un nuovo input. Non chiamare questi dati latenza fisica tasto-display.
- [ ] Verificare scene e risultati equivalenti; riportare campioni, mediana, p95 e massimo quando il campionamento li sostiene. Separare I/O, CPU e presentazione.
- [ ] Modificare solo il costo dominante dimostrato. Verificare invalidazione/ownership delle cache durante cambio mappa, ingresso/uscita lotta e apertura ripetuta. Un miglioramento deve superare il rumore delle ripetizioni e non peggiorare risposta o picchi.
- [x] Acquisire package/APK/librerie, ROM/raw/BIOS e configurazione effettiva Android: JIT, renderer compute 6x, threading, rewind, velocità, cinque cheat verificati e doppio display. Originali ricontrollati; preferenze temporanee ripristinate. L'identità binaria è fissata, la corrispondenza esatta con il checkout sorgente resta da attestare.
- [x] Validare i raccoglitori sul dispositivo: SurfaceFlinger continua in pausa e non misura i frame guest; Perfetto non emette i payload CPU richiesti. Accounting `/proc` verificato e revisionato: tre finestre urbane ferme, due Koga e una pausa valide; due corse escluse e conservate.
- [x] Preparare una fixture urbana derivata su copia, provarla sul dispositivo Android, eseguire SAVE e nuovo processo/Continue. Copiare il raw scritto e preservare quello personale. Registrazione del movimento separata dal timing, nessuna misura di latenza fisica.
- [ ] Ottenere una metrica continuativa degli stalli e attribuzione CPU/GPU/termica; Thermal HAL non pronto, frequenze puntuali insufficienti. Nessun costo dominante o guadagno prestazionale dimostrato.
- [x] Qualificare il banco Android sul Mac: dopo il recupero di spazio, AVD API 33 ARM64 avviato e APK acquisito installato con hash identico. Preferenze importate, SAF riconcesso, BIOS e raw verificati. Compute 6x provoca errore del compositore e uscita per segnale 11 su GLES 3.0; il profilo distinto Software 1x esegue Continue, movimento, SAVE e Continue in un nuovo processo. Rapporto e prove private conservati.
- [ ] Confronto prestazionale Mac–dispositivo: nessuna calibrazione valida con renderer, GPU e display differenti. Pareggiare prima il lavoro e qualificare la metrica; mantenere separati AVD Software, banco headless e dispositivo Compute. Non trasformare il successo funzionale in una misura di FPS o latenza.

## Task 4: Chiusura delle interazioni e salvataggi

- [x] Dimostrare sul codice macchina dei candidati EN/IT il falso successo del
  caller touch quando training già attivo rifiuta il salvataggio con stato 3.
  Prova di confine con stato sintetico e primitive controllate; non è un test
  completo di rendering, retry o compatibilità raw.
- [x] Correggere la gestione del ritorno FALSE con messaggio veritiero,
  cleanup delle risorse e riapertura di Salva verificata, preservando rollback
  e rifiuto. Il retry transitorio fino al successo è coperto dal test composto
  del codice macchina; resta separato dal retry nell'emulatore completo.

Copertura aggiornata: nove cicli raw sui candidati Task 4, EN/IT legacy,
Plus configurato e Borsa estesa, avanzato IT e due fixture con corsi attivi;
originali invariati. Pagamenti e premi nuovi non fanno parte di questa campagna.

**Files:** nuovi `sgp13/save_ui.py`, `sgp13/test_save_ui.py`,
`sgp13/test_save_ui_rom.py` e helper locale in `features/save-ui/`;
integrazione del coordinatore in `sgp13/build.py`, `run_tests.py` e manifest.
Scenari runtime, fixture e dump restano privati. Nessuna modifica ai writer
Borsa/training, al formato save o al loader globale.

**Progetto verificato:** estendere localmente overlay30 con due stati di
errore, conservando tutti i byte originali tranne il puntatore allo stato di
salvataggio. Aggiunta grezza massima 512 byte; corpo compresso entro lo slot
originale di 2048 byte. Messaggio 117 aggiunto in coda al bank40, preservando
i precedenti ID e contenuti. Su TRUE restano identici messaggio, suono e
chiusura nativi. Su FALSE: cleanup una volta, testo veritiero, attesa di
rilascio → nuova pressione A/B/touch → rilascio, poi uscita nativa. Il retry
avviene riaprendo Salva dal menu, senza alterare dati estranei.

- [x] Test sul dispatcher e caller reali EN/IT: fallisce sulla falsa notifica
  precedente; controllo TRUE conserva il percorso nativo.
- [x] Verificare spazio overlay, assenza di nuovi conflitti RAM, codifica e
  larghezza dei due testi nella finestra nativa. La dimensione compilata e la
  resa effettiva sono gate successivi.
- [x] Implementare il delta minimo e rileggere indipendentemente codice,
  tabella, risorsa testuale, compressione e byte da preservare.
- [x] Verificare rifiuto ripetuto e retry con writer reali nel banco ARM:
  rollback sul rifiuto, commit effettivo al successo, messaggio coerente e
  cleanup unico; primitive I/O e rendering controllate dichiarate nel rapporto.
- [x] Eseguire revisione indipendente, poi UI EN/IT da cold boot e matrice raw
  aggiornata, includendo due fixture con training realmente attivo.
- [x] Verificare nell'emulatore testo persistente, conferma già premuta,
  rilascio/nuova pressione/rilascio A/B/touch, tre riaperture e due ulteriori
  rifiuti per lingua, ritiro VWait prima della distruzione dell'app.
- [ ] Ripetere nell'emulatore completo il caso di errore transitorio seguito
  da un salvataggio riuscito senza riparare o cancellare i record.

- [ ] Matrice raw: EN/IT; save precedente senza Plus; con impostazioni Plus; Borsa estesa con contenuto; training attivo con corso/premi/pagamento. Continue → azione → SAVE → nuovo processo → confronto progressione, squadra, box, Borsa, impostazioni e Day Care. Hash originali invariati.
- [ ] Inserire guasti alle letture/scritture e alle verifiche dei due banchi; osservare rollback, retry e il messaggio effettivo della UI. Il valore di ritorno corretto da solo non dimostra una notifica corretta.
- [x] Le correzioni alla UI errore hanno un nuovo test sul caller reale; non consentire salvataggio parziale né eliminare dati per nascondere l'errore.
- [x] Aggiornare rapporto con casi eseguiti, non eseguiti, causa dimostrata e residui. Non dichiarare eliminati tutti i freeze o aumentati FPS/reattività senza le rispettive misure.
- [x] Revisione indipendente del delta completato e delle prove Task 4; `git diff --check` e controllo file pubblici. Questo non chiude i casi ancora aperti né costituisce approvazione di una release.
