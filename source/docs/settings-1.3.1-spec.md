# Impostazioni unificate 1.3.1: contratto di comportamento

Scelte confermate: elenco continuo Gioco/Plus/Cromatici sul display superiore,
display inferiore con Pokéball nativa statica, solo tasti fisici nelle
impostazioni. La revisione richiesta il 30 ottobre sostituisce lo schermo nero
e uniforma i simboli A/B/X/Y senza cambiare le azioni. Il contratto tecnico
e le prove della composizione sono nel [rapporto UI](ui-1.3.1-validation.md).

## Lista

Sei impostazioni native (testo, effetti lotta, stile lotta, audio, comandi,
cornice), cinque Plus e modalità Cromatici; Pro aggiunge Bersaglio e Ricerca Pro.
Intestazioni non selezionabili, cursore per ID stabile, contatore voce/totale,
titolo/versione/posizione in aree separate con un solo renderer. Classic
nasconde i controlli Pro ma conserva il bersaglio; i reset esistenti di serie e
carica avvengono al commit. Nessun nuovo ID persistente.

## Input

| Tasto | Azione |
|---|---|
| Su/Giù | Voce precedente/successiva; no wrap, ripetizione direzionale nativa. |
| Sinistra/Destra | Valore precedente/successivo; clamp agli estremi, non cambia sezione. |
| L/R | Primo controllo della sezione precedente/successiva; no wrap. Tutto resta raggiungibile con Su/Giù. |
| A | Apre selettore o conferma scelta locale, mai Apply globale da una riga ordinaria. |
| B | Indietro; alla radice gestisce l'uscita con modifiche pendenti. |
| X | Conferma esplicita Applica dalla radice; ignorato in selettori e Info. |
| Y | Info superiori; B ritorna alla stessa voce. |
| Touch | Ignorato in ogni stato delle impostazioni. |

Normalizzatore locale: recupera L/R raw e distingue A fisico da quello sintetico
di L=A. Non cambia il modo globale; il nuovo modo Comandi vale dopo Applica.
Una pressione genera una sola azione: priorità B, A reale, X, Y, L/R, direzione.
L+R e direzioni opposte si annullano; input nuovo prevale sulla ripetizione della
stessa famiglia. L+A conserva A reale. In apertura/ritorno attendere rilascio dei
tasti di conferma; testare coperchio/ripresa senza riusare maschere raw stale.

## Bersaglio e ricerca

Bersaglio: specie locali già viste per il metodo corrente più Nessuno. Lista
vuota spiegata con recupero, non come errore di save. A aggiorna soltanto il
draft e torna alla stessa riga Bersaglio; B scarta soltanto la scelta locale e
torna alla stessa riga. Non rientrare implicitamente in un diverso pannello.

Ricerca Pro: pannello superiore con Pokémon, Metodo, Successi, Probabilità e
Passi x/40. Ultimi tre sono stato, non controlli modificabili. Metodo/Bersaglio
modificabili; comando **Prepara ricerca**, non Avvia. Richiede Pro, specie valida
e 40 passi; modo/bersaglio nuovi ancora da applicare hanno carica effettiva zero.
A prepara solo il draft e torna alla riga Ricerca Pro della lista principale,
stato Da applicare. X Applica
elenca gruppi modificati ed eventuale ricerca preparata; solo dopo conferma,
uscita e campo libero l'owner avvia l'incontro secondo le condizioni esistenti.
Cambio modo/specie/metodo invalida la ricerca preparata. Rimuovere Regole dalle
impostazioni; spiegazioni originali e verificate in Guida/Info.

## Transazione

Snapshot/draft temporanei separati per Nativo, Plus e Cromatici, con dirty mask.
Validare **solo i gruppi modificati**: un owner Plus assente non impedisce di
modificare l'audio nativo. I suoi controlli restano leggibili ma disabilitati.

Controllare app/generazione, snapshot, domini, owner e contesto; preparare senza
side effect; eseguire la parte fallibile Cromatici provandone atomicità al
rifiuto; poi confermare Nativo/Plus con precondizioni valide e scritture
deterministiche non fallibili. Se l'audit non prova questo contratto, introdurre
prepare/commit negli adapter prima dell'integrazione. Non concatenare tre vecchi
pulsanti Apply. Confrontare i byte di tutti i gruppi sul rifiuto.

Un rifiuto conserva menu/draft e spiega il recupero, senza altri gruppi applicati.
B alla radice esce subito se pulito; se dirty offre Applica/Scarta/Continua,
preselezionando Continua. Scarta ripristina snapshot e preview; Continua conserva
il draft. Apply aggiorna RAM/stato operativo; il file segue il normale SAVE.

## Ciclo grafico

Intercettare prima della prima presentazione nativa: il solo hook input
`0x021E6820` è troppo tardi. Fissare lifecycle e ingresso con preimage, simboli e
byte EN/IT; non presumere indirizzi. Un owner per LCD swap, BG/OBJ, palette,
VBlank, Window, font e printer. Sotto resta la Pokéball statica anche in
selettori, Info, conferme ed errori, senza controlli o testo. Verificare ingresso
e transizioni; ripristinare campo/callback e liberare solo risorse proprie.

Preview testo/cornice nelle Info o in un'area superiore; audio/preview reversibili.
Nessun printer scrive tile riassegnati. Allocazione fallita: chiusura senza Apply.
Non cancellare il pannello visibile a ogni movimento: comporre prima di trasferire
e aggiornare solo righe/valori cambiati. Niente frame con titolo vecchio o righe
parziali. Legacy: 3.772/3.776 byte; estensione: limite 8.192. Dimensionare prima
di installare; riallocazioni con mappa, guardie e composizione, mai padding libero
presunto.

## Accettazione

EN/IT, tutte le opzioni e transizioni, estremi/sezioni, normale/L=A, input
simultanei/mantenuti, liste vuote/piene, Classic↔Pro, owner assente/rifiuto,
rollback/preview e touch senza effetti. Anche senza Plus le opzioni native
restano usabili, senza azzerare o inizializzare impostazioni per mostrare la UI.

Collaudo finale su **melonDS Android nel Mac**, prima/dopo, EN/IT e copie dei
vecchi raw-save: Continua → UI → SAVE → avvio a freddo, confronto dati/opzioni/
Borsa espansa. Identificare APK, profilo, ROM e strumento. FPS cap arrotondato e
throughput headless non provano assenza di costo: campioni e scene comparabili,
limiti e non valutabili espliciti. Ripetere UI sulla 1.3.1 composta dopo meccaniche.
