# Contratto delle risorse — guida nativa 1.05

**Aggiornamento dopo la review Task 1:** il successivo controllo heap (private lab record, not distributed) respinge il modal a bitmap intera proposto sotto: 44.928 byte non entrano nei 24.528–25.728 byte totali liberi dei quattro campioni. La descrizione rimane come ipotesi documentata e respinta. Implementare invece finestre di testo separate con prenotazione bounded proposta 22.528 byte; il [probe reale](README-lease.md) è ora passato sulle quattro fixture e revisionato. Proseguire dal [layout compatto](PRESENTATION.md), la cui resa resta da verificare. Badge e prenotazione del modal devono occupare fasi distinte: non trattenere il grande blocco durante il normale Main Summary o L/R/Select. Nessuna memoria aggiunta all’heap 19.


7 settembre 2026. Contratto per la prossima implementazione, **nessuna guida ancora eseguibile**. Segue il piano approvato e la ricerca di integrazione (private lab record, not distributed). Il lettore [EV/IV r5](../native-eviv/README.md), i suoi risultati e i suoi sorgenti restano intatti.

La scelta minima è una presentazione modale sul touch screen del riepilogo: tre pannelli testuali, stesso font HG, ingresso `START Guide` / `START Guida` sulla pagina Skills/Dati. La guida prende temporaneamente in prestito BG4, conserva i caratteri e la tilemap che copre e li restituisce prima di riabilitare il riepilogo. Non distrugge Summary, non ricostruisce il Pokémon e non richiama Oak. La pagina superiore resta nella modalità parametri/EV/IV esistente.

## Livelli di evidenza

- **Verificato su Plus EN/IT r5:** hash completi delle ROM, intervalli ARM9 selezionati, tabelle BG/finestre confrontate byte per byte con le direttive pret, quattro dump stabili già esistenti (squadra e box nelle due lingue), font 0 effettivo. Dati selezionati in un registro di laboratorio (private lab record, not distributed).
- **Sorgente di riferimento:** pret `0985e8718df4f25e64d6507d89c0c97c0d288981`; hg-engine `1febb90b856745f8648c8a4fa059e7499a3cca3f`. L'identità EN/IT di una funzione non equivale alla ricompilazione integrale del sorgente pret. Gli indirizzi sono corroborati da ganci r5, literal e destinazioni BL effettive; i commenti Platinum di alcuni helper hg-engine non sono autorità per HG.
- **Decisione da implementare e collaudare:** badge, snapshot BG4, isolamento input, rilascio risorse, rendering dei tre pannelli. Nessuna prova grafica della nuova guida viene dichiarata.
- **Non verificato:** varianti Classic, altre modalità Summary, capacità contigua dell'heap per le nuove allocazioni, New Game e il suo gancio binario. Questi ultimi due punti sono gate espliciti, non PASS.

Le basi ammesse per questa analisi sono Community 1 Plus EN `3ed4ea02…6248` e IT `217daa45…a4a4`; le ROM r5 ispezionate sono EN `a1d7ed3e…556e` e IT `96c41b59…8ed3`. Gli hash interi sono nel JSON. Non aggiungere Classic alla allowlist della guida solo perché il vecchio builder la riconosce. Costruire la candidata guida in un'area nuova a partire da una base controllata, componendo r5 e guida; non sovrapporre alla cieca nuovi ganci sulla ROM r5 o modificare il builder storico.

## Chiamante Summary: indirizzi e memoria

Indirizzi ARM9 senza bit Thumb; le chiamate indirette Thumb richiedono `address | 1`.

| Funzione / gancio | Indirizzo | Contratto verificato |
|---|---|---|
| `PokemonSummary_Init` | `0x02088298` | Heap parent 3, child 19, size `0x45000`; dati overlay `0x7D8`, inizializzati a zero; `BgConfig` in `summary+0` |
| `PokemonSummary_Main` | `0x02088424` | `r0=OverlayManager*`, `r1=int* state`; stato 2 chiama l'input normale; il tail anima sprite/Poképic |
| `PokemonSummary_Exit` | `0x0208856C` | Disattiva VBlank prima del teardown; rimuove finestre, BG, font e dati; distrugge heap 19 |
| input `sub_02088B40` | `0x02088B40` | `r0=summary`; restituisce il prossimo stato. R5 consuma L/R/Select restituendo 2 |
| renderer Skills `sub_0208D178` | `0x0208D178` | R5 intercetta il ridisegno per ripristinare titolo; guida non deve provocarlo all'uscita |
| finestre fisse `sub_0208C3E4` | `0x0208C3E4` | 34 `Window` da 16 byte a `summary+4`; template `0x02104D94` |
| finestre pagina `sub_0208C42C` | `0x0208C42C` | Skills: 18 finestre da template `0x02104D04`; puntatore `summary+0x224`, count `+0x228` |
| rimozione finestre pagina | `0x0208C4E0` | Libera l'array in base alla pagina attuale; non chiamarla dal modal |
| callback VBlank | `0x020885DC` | Argomento `summary`; BG scheduled updates, Poképic image/palette, VRAM transfer tasks, OAM, IRQ flag |

Nei quattro dump la callback in `gSystem` è `0x020885DD`, heap 19, pagina1, 18 finestre; dataType1 per squadra e 2 per box, mode0. I puntatori sono dinamici: squadra Summary `0x022C034C`, box `0x022D035C` nei soli campioni esaminati. **Non hardcodarli.** Ricavarli dall'OverlayManager (`OverlayManager_GetData`, BL verificato a `0x02007290`). **Correzione documentale del 7 settembre:** `0x020072A4` è invece `OverlayManager_GetArgs` (+0x18); GetData legge +0x1C. Il disassemblaggio della BL reale in Main a0x02088428 e il contratto New Game confermano la distinzione. Il codice Task3 usa GetData corretto; il pacchetto storico Task1 resta immutato. `summary+0x22C` punta agli argomenti: dataType `+0x11`, mode `+0x12`, posizione `+0x14`. Pagina `summary+0x7BC`; `summary+0x7BF` contiene bit di stato, non memoria libera.

I primi otto byte originali dei due ganci r5 sono `70b56d4a051ca95c` e `38b586b000231021`; in r5 sono già trampolini rispettivamente a `0x01FF883D` e `0x01FF881D`. Il wrapper aggiuntivo Main deve verificare `38b50c1c7ef732ff` a `0x02088424`. Quegli otto byte comprendono una BL PC-relative: **non copiarli come blob rilocato**; riemettere il prologo e la chiamata a `OverlayManager_GetData`, poi riprendere a `0x0208842C`. Analogamente il prologo Exit `38b5051c7ef78efe` contiene una BL e richiede rilocazione corretta se intercettato.

R5 occupa payload592/reserva608 byte da `0x01FF8620`; arenaLow dopo r5 `0x01FF8880`, limite autorizzato `0x01FFA000`: residuo `0x1780` =6016 byte. È budget di codice/dati ITCM, non VRAM o heap. Una composizione deve ricalcolare dimensione, allineamento32, destinazioni dei trampolini e arenaLow. Superare il budget è un errore del builder; non consumare DTCM, BSS, stack o nuovi spazi apparentemente vuoti.

Il loader r5 [`thumb_object.py`](../native-eviv/thumb_object.py) carica solamente `.text`, risolve BL Thumb interne e richiede `eviv_hook`; rifiuta dati in `.data/.bss/.rodata` e rilocazioni ABS32. Un nuovo `static GuideState` non viene quindi caricato o azzerato automaticamente. Usare contesto esplicitamente allocato e raggiungibile con ownership verificata; qualsiasi nuova capacità del builder/loader va sviluppata separatamente nella composizione guida, con controlli di sezione/rilocazione e preservazione del contratto r5, senza modificare il loader storico per comodità. Anche stringhe e puntatori costanti richiedono una strategia compatibile con il formato del payload.

## Risorse video esistenti e prestito proposto

`sub_02088610` usa la tabella bank a `0x02103990`; `sub_02088630` inizializza BG1/2/3 e BG4/5/6. Le due tabelle selezionate, 292 e544 byte, coincidono esattamente tra sorgente pret e le due ROM. La tabella finestre completa decodificata è nel JSON.

| BG | buffer tilemap | screenBase | charBase | priorità |
|---|---:|---:|---:|---:|
| 1, main BG1 | `0x800` | 31 | 4 | 0 |
| 2, main BG2 | `0x2000` | 27 | 0 | 1 |
| 3, main BG3 | `0x800` | 26 | 0 | 3 |
| 4, sub BG0 | `0x800` | 31 | 4 | 0 |
| 5, sub BG1 | `0x2000` | 27 | 2 | 2 |
| 6, sub BG2 | `0x800` | 26 | 0 | 3 |

BG4 è text/4bpp, tile32 byte, 32×32 map, scroll0 nei dump. `BgConfig.bgs` comincia a+8, ogni `Background` occupa **0x2C**, quindi BG4 a `bgConfig+0xB8`. Puntatore tilemap a+0 di Background, dimensione a+4. Non usare0x30: una prima decodifica privata con quello stride è stata respinta e corretta confrontando header e dump. Nel mapping Summary charBase4 corrisponde a sub BG VRAM `0x06210000`, screenBase31 a `0x0620F800`; il runtime deve verificare bank e BG control correnti prima delle copie, non ricavarli dalla sola capacità RAM.

Le finestre esistenti usano palette13. `sub_020887C4` carica 512 byte di palette su ciascun motore e gli asset di sfondo da NARC162; questo non lascia implicitamente una palette libera. Usare la palette13 esistente per i glifi della guida, senza cambiare palette globali, bank, font, brightness o renderer 3D. La scelta dei colori di riempimento/bordo deve essere confermata a1×, mantenendo sfondo opaco e contrasto; non assumere che il colore0, trasparente, oscuri le mosse sottostanti.

**Badge proposto, solo Skills/Dati normale:** Window BG4, x21/y18, width10/height2, palette13, baseTile`0x3C0`; copre tile960–979 e pixel `[168,248)×[144,160)`. Nei quattro dump la sua regione tilemap è tutta zero. I template Skills BG4 terminano al massimo al tile esclusivo`0x3BB`; badge sotto1024 e separato dai tile del modal. È spazio riservabile nel contesto Skills controllato, non un'estensione valida su tutte le pagine: la finestra descrizione mosse ha una geometria che può coprire quest'area quando attivata. Il badge va rimosso prima di lasciare stato2/pagina1 e ricreato/ridisegnato quando vi si rientra; mai durante selezione mosse o altre sottomodalità.

**Modal proposto:** una Window BG4 x1/y1, width30/height22, palette13, baseTile1. Borrow di660 tile `[1,661)`: byte `[0x06210020,0x062152A0)`, lunghezza`0x5280`. Prima del prestito conservare quei caratteri GPU e l'intera tilemap CPU BG4 di`0x800` byte, dopo aver drenato i trasferimenti precedenti. Tenere intatti `Window` originali e i loro pixelBuffer: sono ancora di Summary. La guida possiede la sua Window/bitmap e la copia di ripristino. Salvare la maschera di visibilità sub; durante il modal mostrare BG4 e nascondere gli altri BG/OBJ sub per non sovrapporre icone animate. Ripristinare la maschera esatta alla fine. Non cambiare bank o distruggere il BgConfig.

Budget minimo, escluso overhead: snapshot`0x5A80` (caratteri+tilemap), bitmap modal`0x5280`, bitmap badge`0x280`: **44928 byte**, più contesto/stringhe/allineamento e overhead degli allocatori. `Heap_Alloc(19,…)` è l'allocatore proprietario, `Heap_Free`/`RemoveWindow` i rilasci corrispondenti. `AddWindow` alloca un pixelBuffer, `RemoveWindow` lo libera: un buffer interno al contesto non deve essere passato a RemoveWindow come se fosse un'allocazione separata.

**Gate heap ancora aperto:** heap totale`0x45000` non prova44928 byte contigui disponibili nei vari chiamanti. Il sorgente `Heap_Alloc` invoca `AllocFail`, che può fare `PrintErrorMessageAndReset`; provare una grande allocazione e controllare NULL non è un fallback sicuro. Prima di abilitare l'ingresso, il prossimo passo deve verificare capacità/largest allocation e overhead sulle fixture squadra/box, quindi una prenotazione bounded e il rilascio, o rivedere il budget con risorse più piccole. Non usare `HeapExp_FndGetTotalFreeSize` come dimostrazione della contiguità; il suo indirizzo/ABI e un'eventuale query largest-block non sono qui validati. Non aumentare l'heap 19 sottraendo memoria al parent senza una prova dedicata.

## Init / Run / Exit

Interfaccia propria consigliata: `Guide_Init(GuideContext*, GuideHost*)`, `Guide_Run(GuideContext*, GuideInput) -> active/done`, `Guide_Exit(GuideContext*)`. Il componente riceve dal chiamante BG/window ownership, lingua, font, pixel budget e input già normalizzati; non riceve un SaveData*. Il contesto sta in memoria esplicitamente allocata, mai in padding Summary o save.

1. **Init del percorso Summary:** richiedere stato2, pagina1, mode0, `summary[0x7BF] >> 4 != 1`, callback/BG attesi e risorse prenotate. La compatibilità futura con mode1/2/3/4 richiede un contratto proprio. Salvare i dati di ritorno per verificarli (argomenti, pagina, posizione), non modificarli. Sopprimere il normale Main quando il modal è attivo, incluso il tail di animazione; mantenere la callback VBlank Summary e le sue attività necessarie. Una fase iniziale lascia terminare il VBlank precedente prima dello snapshot; nessun AddWindow/free in IRQ. Non cancellare globalmente le code di trasferimento.
2. **Run:** tre pannelli, testo istantaneo; disegnare soltanto dopo cambio pannello, non ogni frame. Tutti gli input mentre la guida è attiva sono consumati dal modal: non passano a L/R/Select EV/IV, mosse, cambio Pokémon, touch Summary o uscita B originale. La callback continua a eseguire scheduled transfers; eventuali aggiornamenti autonomi che scrivano BG4 durante il prestito sono una regressione da rilevare con i probe, non autorizzati dalla sospensione del solo handler input.
3. **Exit:** attendere conclusione dei trasferimenti della guida; ripristinare caratteri e copia CPU tilemap, schedulare il trasferimento della mappa originale, poi ripristinare visibilità. Mantenere contesto e buffer validi fino al VBlank che completa il ritorno. Solo dopo rimuovere/free delle sole risorse possedute e permettere al Main originale di riprendere, con stato2 invariato. Non chiamare renderer Skills, `PokemonSummary_Init`, `PokemonSummary_Exit` o Oak per ripristinare la vista: cancellerebbero la modalità EV/IV o l'ownership. Una guardia di rilascio input impedisce che B chiuda anche Summary e che il touch sul modal attivi una mossa appena sotto.
4. **Uscita Summary:** se esistono risorse della guida, il suo cleanup precede la distruzione di heap 19 e della callback. Nessun puntatore al contesto sopravvive all'overlay. Ripetere Exit o uscire da Init incompleto deve essere innocuo grazie a flag espliciti per ogni allocazione e fase di trasferimento.

`ScheduleWindowCopyToVram` **non rimanda tutto al VBlank**: nel sorgente `bg_window.c` prepara/schedula la tilemap, ma copia subito i caratteri. Per evitare tearing usare una fase delimitata di presentazione (ad esempio BG4 nascosto durante l'aggiornamento e mostrato dopo commit), con copie a16/32 bit e semantica di cache/DMA degli helper originali. Non liberare memoria che una copia schedulata legge ancora.

## Input e visibilità

Originale `sub_02088B40`: uscita speciale da`+0x7BF`, poi direzioni ripetute sinistra/destra/su/giù, B, A, touch mosse/ribbon, cambio membro box, navigazione pagine touch. R5 cede ad A/B o direzioni, usa L/R/Select solamente su pagina1 non uovo e mantiene la politica originale. La guida aggiunge il nuovo comando senza alterare quella precedenza quando è chiusa: nessuna apertura con A/B/direzioni concorrenti o durante un'altra transizione.

START è libero nel ramo normale esaminato. Il badge nominato misura61 pixel nelle due lingue, dentro80 pixel. Consigliare START fisico tramite `newKeysRaw`, conservato anche con la modalità START=X, e lo stesso rettangolo touch visibile. Non affidarsi a un tasto X implicito. La modalità L=A del sistema nasconde L/R agli input rimappati: è un limite del lettore r5 da registrare nei test delle istruzioni, non un motivo per cambiare ora il suo codice storico.

`gSystem=0x021D110C`; raw held/new sono`+0x38/+0x3C`, mapped new/repeated`+0x48/+0x4C`; touchX/Y/New/Held`+0x60/+0x62/+0x64/+0x66`. L/R/Select sono`0x200/0x100/0x4`, START`0x8`, A/B`1/2`, destra/sinistra`0x10/0x20`. Non scrivere nei bit globali per consumarli: sospendere il dispatch del chiamante.

Nel modal usare pressioni nuove, senza repeat: B/Esci precede tutto; poi sinistra/Indietro, infine A/destra/Avanti. Un solo evento per frame. A/destra sull'ultima scheda esce; sinistra sulla prima non fa wrap. Al primo pannello il target Indietro è visibilmente disabilitato; sull'ultimo Avanti diventa Fine/Done. Ogni target è disegnato e testato come parte della Window, con hitbox identica ai bounds visibili. Bloccare il primo evento fino al rilascio del comando di ingresso e analogamente all'uscita; tenere premuto START/A/B/touch non deve attraversare pannelli o riaprire la guida. Se si usano i tasti fisici raw, dichiararlo nel mapper locale senza cambiare le opzioni del giocatore.

Le hitbox originali confrontate: mosse da`0x021038D4`, frecce box da`0x021038B8`, pagina/Annulla e altre icone da`0x02104FFC`. Il badge a y144–159 resta sotto le icone (ultima fascia fino138) e sopra la barra inferiore (inizia165), e a destra delle mosse (x8–127). Il controllo di collisione e screenshot finali deve includere proprio squadra e box.

## Font, testo e helper

Font0 è già accessDirect per Summary; font4 viene allocato e rilasciato da Summary. La guida prende font0 in prestito: non incrementa/rilascia refcount né cambia access mode. Il NARC font è ID16, percorso ROM`a/0/1/6`, membro0. Il membro0 ha SHA-256`9a17de30…9e73` identico EN/IT; header16, widthDataStart32592,509 glifi. L'archivio complessivo differisce EN/IT: non dedurre identità di tutti i font.

Percorso di misura: charmap pret → codici HG → widths[glyph−1], spacing0, stesso font del renderer. `FontID_String_GetWidth=0x02002F30` è verificato dalle BL del renderer; `AddTextPrinterParameterizedWithColor=0x020200FC`, `FillWindowPixelBuffer=0x0201D978`, `AddWindow=0x0201D4F8`, `ScheduleWindowCopyToVram=0x0201D5C8`, `GetWindowWidth=0x0201EE90`. I nuovi helper non già usati da r5 devono avere controlli delle loro preimmagini nel builder prima di essere chiamati; gli indirizzi sopra non certificano qualunque altro ROM.

Area modal240×176px, margine interno8px: body224px, font alto16px. Le sei descrizioni del piano entrano ciascuna in tre righe/48px con misura reale: larghezze massime IT224/222/210, EN216/205/204. Gli a capo misurati sono nel JSON, non ancora revisionati graficamente. Riservare spazio distinto a titolo, indicatore1/3, body, suggerimento `START Guide/Guida` e barra di navigazione. La riga IT larga224 esatta può essere spezzata prima per lasciare margine alla review; non ridurre il font.

La charmap non contiene l'apostrofo ASCII del testo di lavoro: usare l'apostrofo tipografico U+2019, glyph`0x01B3`, senza sostituire é o altri accenti. Rifiutare caratteri non mappati invece di convertirli silenziosamente. Non passare il corpo guida al formatter r5 centrato: tronca la larghezza a8bit ed è destinato ai piccoli valori. Stampare righe tramite il printer nativo, coordinate esplicite, velocità istantanea e callbackNULL; niente buffer scratch Summary`+0x7AC` condiviso con una stampa ancora attiva.

## New Game: lavoro distinto ancora necessario

[Oak pret](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/oaks_speech.c) fornisce un riferimento, non il componente da richiamare: crea heap proprio`0x40000`, naming args, sprite/BG, callback Oak; `OakSpeech_Exit` scrive nome/genere/rivale e registra l'overlay36 di inizializzazione partita. Le sue finestre fullscreen24×24 a baseTile`0x12D`/palette5 appartengono al suo layout. Non riusarle simultaneamente alle risorse Summary.

Il prossimo sottotask deve trovare e confrontare EN/IT il punto reale di selezione Nuova partita, il passaggio a overlay53/Oak e la continuazione dopo guida. Non sono qui fissati offset ROM, overlay preimmagine, callback o heap del nuovo host. Preferire un host separato prima di Oak che richiami lo stesso componente di testo/input, con risorse proprie e ritorno al flusso originale. Non collegare l'Exit di Oak al riepilogo, non saltare inizializzazioni necessarie della vera Nuova partita, non scrivere un flag “vista” nel save.

## Probe di accettazione dell'implementazione

Prima prenotazione memoria e badge isolato; poi modal e infine New Game. Nessun nuovo test EV/IV o trainer audit è stato eseguito per questo documento.

- Prima/dopo funzionale: START nella stessa scena r5 non apre una guida; nella candidata apre il pannello visibile e la navigazione/ripristino soddisfa le invarianti. Non basta la presenza di un simbolo o di stringhe nel payload.
- Hash completi ROM/save/harness, commit/build, interprete software1×, cheat disabilitati; gli originali e r5 restano intatti. Canarie e conteggio alloc/free, massimo blocco richiesto, pressione heap di squadra/box e fallimento prima di alterare display/input.
- Snapshot prima/dopo: pagina, posizione, modalità, Pokémon, SRAM, BG4 tilemap CPU/GPU, caratteri prestati, visibilità, callback e argomento. Il confronto dello schermo superiore deve dimostrare il ritorno esatto da EV e IV senza redraw parametri.
- Tre pannelli EN/IT, back/next/Fine/B, touch visibile, bordo dei target, input simultanei, tasti tenuti, ingresso ripetuto10 volte e uscita durante le fasi transitorie; nessuna perdita o doppio free e nessun trasferimento verso buffer liberati.
- Fuori Skills o mentre A entra nelle mosse il badge non cattura comandi né lascia tile; cambio membro e box, apertura/chiusura Summary, SAVE normale e cold boot conservano dati e corrispondenza nome/ID/progressione.
- New Game separato: uscita anticipata/completa, Oak/nome/genere/rivale e primo SAVE; su save esistente nessuna sequenza di inizializzazione. Nessuna conclusione su Android o su console portatili da questi probe.

Il contratto è pronto per review; l'abilitazione della guida resta condizionata alla prenotazione sicura dell'heap, al rendering e al ripristino verificati. L'ingresso New Game rimane una seconda integrazione con indirizzi da provare.
