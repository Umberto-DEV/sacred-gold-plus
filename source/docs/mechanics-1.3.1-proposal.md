# Proposta meccaniche per 1.3.1

Ricerca del **29 ottobre 2026** sulla candidata V1.3 EN/IT identificata nel
[rapporto corrente](device-1.3-validation.md). Questo documento descrive una
proposta: **nessuna delle aggiunte qui progettate è già integrata o collaudata**.
La storia Kanto–Sinjoh procede separatamente; la
[ricerca grafica](graphics-engine-exploration.md) non entra in questo intervento.
Il successivo [piano eseguibile Superpowers](superpowers/plans/2026-10-29-mechanics-1.3.1.md)
fissa ordine, interfacce, audit e prove. Le scelte più circoscritte di quel piano
precisano questa proposta senza trasformarla in una funzione già implementata.

## Scelta consigliata e difficoltà

Estendere le applicazioni e i dati nativi di HGSS con interventi separati,
conservando salvataggi, lingue e impostazioni Plus. Importare integralmente un
altro motore richiederebbe riconciliare molte più modifiche e non offre una
scorciatoia dimostrata per la candidata corrente.

| Aggiunta | Difficoltà relativa | Decisione proposta |
| --- | --- | --- |
| Indicazioni dei comandi nella squadra e nel riepilogo | Medio-bassa, ma dipende dalle finestre native | Primo incremento, con catture EN/IT e verifica dei tasti effettivi. |
| Box portatile dalla squadra | Medio-alta | Priorità di 1.3.1: riusare il box nativo, costruendo ingresso, uscita e controlli di contesto. |
| Regali e uova con squadra piena | Alta per una copertura completa | Priorità di 1.3.1, con consegna verificata prima di consumare premi o completare eventi. |
| Rivincite con squadre alternative | Medio-alta per un gruppo delimitato; alta per un sistema globale | Iniziare da rivincite già esistenti, con squadre complete progettate a mano. |
| Mosse e abilità moderne | Media per parametri compatibili; alta per nuovi effetti o identificatori | Ricerca e selezione di pochi casi, senza introdurre un intero pacchetto moderno nella prima iterazione. |
| AI migliore e strumenti di preparazione | Alta per nuove decisioni di lotta | Prima migliorare squadre e informazioni disponibili; studiare poi singoli difetti dell'AI con casi riproducibili. |

Queste sono stime di complessità, non durate o una garanzia di inclusione in
release. Un prototipo misurato deve risolvere spazio, ciclo di vita e casi
speciali prima di fissare il contenuto definitivo di 1.3.1.

## Box portatile: comportamento per il giocatore

Nella schermata iniziale della squadra, aperta dal menu durante l'esplorazione,
**R apre il box** e un comando visibile offre anche l'accesso al tocco. Nel box
si possono spostare, depositare e ritirare Pokémon con le funzioni native.
Chiudendolo si torna alla squadra ricostruita; uscendo dalla squadra si torna
nel punto della mappa da cui si era partiti.

Il comportamento curativo del box nativo è accettato: il deposito e il ritiro
possono ripristinare PP, PS e stato. Non occorre inventare dati persistenti per
conservare le condizioni precedenti. Rimangono le protezioni native, compresa
quella contro il deposito dell'ultimo Pokémon utilizzabile dove prevista.

La prima copertura deve comprendere città, percorsi, edifici e grotte ordinarie.
Surf, Cascata, altri spostamenti speciali e Pokémon accompagnatore richiedono
prove proprie, soprattutto se si deposita il Pokémon necessario al movimento.
Lotta, scambi, collegamenti, Safari, gare, strutture speciali e selezioni di
Pokémon avviate da altri eventi non devono ereditare automaticamente il comando.
Una normale schermata di squadra non dimostra da sola che ogni attività sia
compatibile. Le limitazioni effettive devono essere visibili e motivate nel gioco.

### Evidenza e integrazione

Una prova Android locale sulla candidata V4 IT, con ingresso dal normale
Continua e modifiche soltanto in RAM, ha confermato che R non ha un'azione nella
squadra ordinaria con l'impostazione tasti normale. È stato aperto anche il box
nativo del Centro Pokémon. Questa prova identifica il comportamento attuale:
**non dimostra ancora un collegamento portatile**, che non esiste nella build.
Le osservazioni EN di questa ricerca sono statiche, senza una corrispondente
nuova sessione Android in inglese.

Il comando script nativo `0x009E`, modalità `2`, apre la gestione/spostamento
Pokémon; non si tratta di un tasto segreto da simulare. Occorre richiamare
l'applicazione box dal ciclo di vita corretto. Il gestore delle applicazioni
figlie non consente di sovrapporre liberamente il PC a una squadra ancora viva.

Percorso proposto:

1. La squadra riconosce R o il tocco nel contesto consentito e chiede una normale
   chiusura, conservando soltanto le informazioni necessarie al ritorno.
2. Il chiamante riconosce la richiesta e avvia il box nativo in modalità 2.
3. Alla chiusura del box ricostruisce gli argomenti e l'applicazione squadra
   usando il contenuto aggiornato; corregge il cursore se la squadra è più corta.
4. L'uscita definitiva segue il ripristino nativo del campo, della mappa e
   dell'accompagnatore. I dati relativi alle MN vanno ricreati solo quando il
   campo è disponibile: non vanno conservati puntatori della vecchia squadra.

Preservare anche la notifica nativa collegata al riempimento dei box. Apertura
di strumenti, riepilogo, soprannomi e altre sottofinestre dentro il PC devono
continuare a usare il loro normale percorso di ritorno.

La [mappa della riserva ARM9](arm9-reserve-map-1.3.json) assegna già ogni
intervallo della nuova riserva 1.3: il padding di un componente non è spazio
libero di un altro. Prima dell'integrazione servono dimensione del nuovo codice,
allocazioni temporanee e una revisione esplicita della riserva o dei confini
dei componenti interessati. Questo vincolo non rende impossibile la funzione,
ma impedisce di promettere che basti inserire un piccolo hook in spazio libero.

## Comandi sempre comprensibili

Il [contratto visivo HGSS](hgss-ui-contract.md) resta il riferimento: font nativo,
due schermi da 256×192, finestre e controlli coerenti, testi EN/IT.

Nella squadra una possibile riga è `Scegli un Pokémon.  R: Box`, misurata a
139 pixel nel font0 della candidata, contro i 160 pixel della finestra ordinaria.
L'audit successivo conferma che il prompt usa font1 e che i membri font0/font1
V4 sono byte-identici in EN/IT; la prova visiva deve comunque usare il renderer
e la spaziatura effettivi. Il piano propone un suffisso separato nella finestra.
È un'indicazione di fattibilità tipografica, non una schermata approvata: occorre
verificare i contesti, l'area del tocco, il cursore e il pulsante Annulla.

Nel riepilogo la candidata usa già **L per EV, R per IV e SELECT per tornare
alle statistiche normali**. Questa mappatura effettiva va conservata e scritta
a schermo; non invertirla partendo da un esempio verbale. Una riga compatta
`L:EV SELECT:Stat. R:IV` misura 124 pixel, ma il titolo esistente ne offre solo
88: non basta accodarla. Studiare una fascia dedicata nello schermo inferiore,
senza coprire mosse, schede o uscita, con finestre e tile propri. Le schermate
di apprendimento mosse e gli altri modi speciali richiedono verifiche separate.
La legenda deve rimanere visibile nelle viste Statistiche, EV e IV e ricomparire
dopo i cambi di Pokémon o pagina; non va mostrata per uova e modi non supportati.

L'opzione nativa **L=A** rende necessario distinguere input fisico e input già
rimappato. La candidata corrente legge già i tasti fisici per il riepilogo;
la nuova azione R della squadra deve essere verificata anche con L=A e con le
altre modalità dei tasti. Mostrare suggerimenti soltanto dove il comando è
disponibile e verificare pressioni mantenute e ripetute durante le transizioni.

## Regali: una consegna verificata, poi il completamento dell'evento

Regola desiderata: con posto in squadra, consegna normale; con squadra piena,
invio al primo posto disponibile secondo l'ordine nativo dei box, partendo dal
box attivo e proseguendo ciclicamente. Se manca capacità, l'evento resta pendente,
con un messaggio chiaro. Non dichiarare il regalo ricevuto e non perderlo.

Non esiste un unico controllo globale sicuro da disattivare. I percorsi nativi
per Pokémon, uova, Togepi, Pichu speciale, prestiti, Dono Segreto e Pensione
sono diversi. Modificare globalmente il conteggio della squadra o l'inserimento
in squadra coinvolgerebbe anche contesti estranei ai regali.

L'ispezione degli script della candidata ha riconosciuto gli stessi siti EN/IT:
50 `GiveMon`, 9 `GiveEgg`, 2 `GiveTogepiEgg`, 3 `GiveSpikyEarPichu`,
2 `GiveLoanMon`, oltre a percorsi separati per starter e Pensione. Sei membri
non sono stati decodificati completamente: il censimento è una base di lavoro,
**non una prova di copertura totale**.
L'audit successivo del dispatch nativo conferma che le sei code fiocco
contengono un opcode fuori tabella, non un comando mancante nei metadata.
Il piano prevede riparazioni circoscritte con prove di flusso e scene; nessuna
scena fiocco è stata ancora eseguita da questa ricerca.

La soluzione proposta costruisce il regalo completo in memoria temporanea,
decide la destinazione e verifica l'inserimento prima di completare l'evento.
Servono adattatori almeno per questi casi:

| Caso | Requisito |
| --- | --- |
| Mosse speciali e soprannomi | Gli script che modificano il Pokémon appena aggiunto non possono più assumere che sia nell'ultimo posto della squadra. Vale, fra gli altri, per Dragonair e Pikachu regalo. |
| Due regali nello stesso evento | Verificare prima la capacità per entrambi e preservare l'evento intero se insufficiente. Inserimenti e flag devono completarsi senza sospensioni, oppure avere un ripristino completo in caso di fallimento. Esistono coppie di Pokémon e di uova. |
| Premi del Casinò | Addebitare i gettoni soltanto dopo una consegna riuscita; nessun doppio premio o doppio addebito al ritorno. |
| Flag anticipati e uova | Alcuni flag sono impostati prima della consegna: anche questi vanno inclusi nella transazione, insieme a provenienza, schiusa e Pokédex. |
| Togepi, Pichu speciale, Dono Segreto | Preservare PID, forma, mosse, OT, fiocchi e dati specifici; non segnare ricevuto un dono che non è stato inserito. |
| Kenya con lettera | Il testo della lettera non appartiene al formato del Pokémon nel box. Proposta da validare: Kenya al box senza lettera allegata e lettera integra nella Casella Posta, con messaggio per entrambe le destinazioni; nessuna consegna se manca posto anche lì. Il controllo nativo contempla già la Casella Posta; il riconoscimento successivo va provato. |
| Pensione | Uovo e ritiro di un Pokémon sono operazioni distinte. Il ritiro, i costi e i corsi Plus richiedono un progetto separato prima di cambiare il loro comportamento. |

L'inserimento nativo nei box è riutilizzabile, ma i valori di ritorno vanno
controllati funzione per funzione: una ricerca di posto vuoto restituisce
`NUM_BOXES` a esaurimento, non un semplice falso booleano.

Non dichiarare «tutti i regali funzionano» lasciando prestiti o Dono Segreto
senza una decisione esplicita. La funzione può essere sviluppata per famiglie,
ma la documentazione della candidata deve nominare ogni esclusione residua.

Preservare anche gli eventi intenzionalmente ripetibili: una sequenza esaminata
consegna due uova di Phione senza flag di completamento a ogni invocazione.
Il collegamento effettivo al personaggio va ancora verificato; non introdurre
un divieto globale di seconda consegna basandosi sui soli regali una tantum.

## Rivincite e miglioramenti delle lotte

La [strategia allenatori 1.3](trainer-strategy-1.3.md) modifica nove mosse in
sette squadre quando è attiva la difficoltà Plus. Non seleziona squadre
alternative e non migliora l'algoritmo dell'AI.

Per un primo incremento si propongono varianti complete delle rivincite già
esistenti della Lega e dei Capipalestra al Dojo, mantenendo accessi, orari e
progressione nativi. Una squadra intera può essere controllata per ruoli,
coperture e risposte disponibili al giocatore; estrarre separatamente ciascun
Pokémon richiederebbe molte più combinazioni da bilanciare. Le lotte multiple
speciali restano una tappa successiva.
Le alternative sono progettate dal developer, preservano l'identità
dell'allenatore e vengono selezionate senza adattarsi alla squadra del giocatore.

La variante deve essere scelta una volta prima di interpretare i componenti
della squadra e restare fissa fino alla fine della lotta. L'hook corrente delle
mosse arriva troppo tardi per sostituire in sicurezza specie e abilità: occorre
un punto precedente del costruttore, con verifiche proprie sul generatore
casuale. Questo è nuovo lavoro di integrazione, anche se parte da codice noto.

Scelta consigliata da approvare insieme alle squadre: collegare inizialmente
le varianti alla difficoltà Plus esistente e conservare il comportamento Normale.
Un'opzione persistente indipendente richiede un contratto dei salvataggi
esplicito; i byte riservati non sono automaticamente disponibili. Evitare
contatori di rivincita nuovi se non servono al comportamento scelto.

Per mosse e abilità moderne distinguere modifiche di potenza, precisione e
apprendimento da effetti nuovi che attraversano danno, fine turno, priorità,
strumenti, AI, animazioni e interfaccia. Prima censire gli identificatori già
riutilizzati da Sacred Gold Plus, comprese le mosse Folletto: lo stesso numero
non garantisce lo stesso significato in un altro progetto.
Non reinterpretare identificatori già memorizzati nei vecchi Pokémon: aggiunte
o cambiamenti di formato richiedono verifica dei limiti e, se necessaria,
migrazione senza perdita.

Per l'AI, partire da decisioni errate riproducibili e correggere un comportamento
alla volta. Accompagnare difficoltà e varianti con informazioni coerenti nella
Guida, strumenti di preparazione già disponibili e descrizioni aggiornate.
Un eventuale sistema che riveli la squadra avversaria è una proposta distinta,
non un requisito già deciso. Non promettere un'AI nuova attraverso semplici
cambi di mosse o impostazioni dei suoi flag.

## Cosa prendere dai progetti di riferimento

- [Redux V2, annuncio degli autori](https://www.reddit.com/r/PokemonROMhacks/comments/1hha3wp/announcing_pok%C3%A9mon_blaze_black_2_and_volt_white_2/):
  riprogettazione delle lotte e molti effetti moderni. Rimane una modifica di
  Nero 2/Bianco 2; «nuovo motore» non implica che ogni sottosistema grafico sia
  riscritto o che esista già un pacchetto compatibile con HGSS.
- [Pool System, spiegazione degli autori](https://www.reddit.com/r/PokemonROMhacks/comments/1ogzapo/introducing_the_pool_system_pok%C3%A9mon_blaze_black_2/):
  alternative curate per gli slot, selezionate prima della lotta, con vincoli
  sulla composizione e possibilità di squadre statiche. L'idea trasferibile è
  la varietà controllata; per Plus conviene iniziare dalle squadre complete.
- [Cascade White 2, commento del suo autore](https://www.reddit.com/r/PokemonROMhacks/comments/1rodagv/unova_has_never_looked_so_good_introducing/):
  descrive PC portatile, strumenti di preparazione e Battle Scan. È un progetto
  distinto da Redux V2: queste funzioni non vanno attribuite automaticamente a
  Redux né trattate come codice già disponibile per HGSS.
- [hg-engine](https://github.com/BluRosie/hg-engine): sorgente pubblico di un
  progetto dedicato a HeartGold inglese, con espansioni di mosse, abilità e
  meccaniche. È un riferimento tecnico più vicino per studiare singoli effetti,
  non una dipendenza già verificata sulla base Plus EN/IT o sui vecchi save.
  Un riuso concreto richiede revisione delle condizioni, crediti, formati e
  modifiche incompatibili; non serve importare la sua espansione dei box.

Gli annunci spiegano risultati e scelte; non sostituiscono sorgenti, formati,
licenze e test. Non è stata stabilita una disponibilità pubblica completa del
motore Redux V2 da trasferire. Studiare direttamente HGSS rimane necessario.

## Ordine di lavoro e prove per ammettere le aggiunte

1. Definire finestre e controlli visibili e misurare lo spazio del codice nuovo.
2. Costruire e verificare squadra → box → squadra → mappa in un contesto ordinario,
   poi estendere la matrice alle altre attività consentite.
3. Integrare le famiglie di regali, con verifiche di capacità, destinazioni e
   completamento degli eventi; risolvere i membri ancora non decodificati.
4. Aggiungere il primo gruppo di rivincite e provarne identità e bilanciamento.
5. Valutare singoli effetti moderni e correzioni AI dopo che queste basi sono
   soddisfacenti. La ricerca può procedere in parallelo.

Il collaudo deve includere EN/IT; tasti normali e L=A; tocco; aperture ripetute;
squadra vuota dove consentito, uno, cinque e sei membri; cambi di ordine,
ultimo Pokémon utilizzabile, uova e accompagnatore. Per i regali: box attivo
pieno ma posto nei successivi, ritorno ciclico, ultimo posto e PC interamente
pieno, capacità zero/uno/due per le coppie, mosse e oggetti speciali, Casella
Posta piena, annullamento e ripetizione dell'evento senza duplicazioni.
Il divieto di duplicazioni vale per i premi una tantum; le consegne previste come
ripetibili devono restarlo. Provare anche fallimenti di allocazione o del secondo
inserimento in una coppia, verificando che nessun premio o costo resti parziale.

Ogni candidata deve avere identità EN/IT e un rapporto proprio. Per i save usare
copie di partite precedenti con e senza dati Plus e con Borsa espansa: normale
Continua, salvataggio nel gioco e riavvio a freddo. Confrontare progressi,
Pokémon, inventario e impostazioni, conservando gli originali. La verifica dei
dati e gli esperimenti in RAM non sostituiscono questa campagna di persistenza.
