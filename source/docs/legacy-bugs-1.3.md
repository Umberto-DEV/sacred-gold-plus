# Bug storici della hack: ricerca e riscontri sulla 1.3.1

Stato del **31 ottobre 2026**. Questo registro riconcilia i venti casi storici
di Sacred Gold/Storm Silver con le dichiarazioni dell'autore Plus e con letture
dei nostri input identificati. Per HGSS originale vedere il
[catalogo retail](known-bugs-hgss.md). L'ordine attuale è: catalogo documentale,
verifica sulla candidata esatta, poi correzioni circoscritte e collaudo.

Lo [stato sintetico delle nuove ROM manuali](../../BUG-FIXES-1.3.1.md)
include anche SG-11, integrato dopo la prima ricognizione. Le schede storiche
qui sotto mantengono i vecchi hash e non vengono reinterpretate come prove
sulle nuove immagini.

**La prima ricognizione era di sola lettura. Il seguito implementa SG-08,
SG-09, SG-15 e il nuovo sottocaso SG-15b nei sorgenti della 1.3.1**, con prove
prima/dopo sul bytecode in modello e rilettura indipendente. Identità,
[verifiche e limiti del seguito](bug-audit-1.3.1.md) sono separati dai vecchi
pending, rimasti immutati. Nessun salvataggio è stato modificato; nessuna nuova
compatibilità o accettazione runtime è implicita.

## Origine e differenze fra versioni

La fonte originaria è la sezione bug nel
[thread di Drayano](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/),
che identifica **1.05, 1 giugno 2012**. Il commento di GengarFan95 nel
[post Plus del 22 luglio 2025](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/)
riprende l'elenco. Il post dichiara sette correzioni dalla **Plus 1.02**;
una riguarda la documentazione. Il testo del Latte MooMoo viene difeso come
slang intenzionale. Una dichiarazione dell'autore non sostituisce la verifica
dei byte della versione effettivamente usata.

Non confondere:

- HGSS retail, con regione e revisione proprie;
- Sacred Gold/Storm Silver **1.05** di Drayano;
- modifica Fairy **1.1/1.1.0** di mikelan98/MeroMero;
- manutenzione **1.1.1/1.1.2** di DeadSkullzJr;
- Plus **1.03** di NefariousnessNo3436;
- nostra release **1.2.5**, candidata **1.3 V4** e pending **1.3.1**.

Un numero maggiore appartenente a un'altra linea non dimostra che contenga i
nostri fix. Non sono stati scaricati ROM, BIOS, save o build alternative.

## Identità delle letture

Hash verificati prima e dopo l'ispezione, senza copiare le ROM. Gli input
retail e 1.2.5 sono identificati anche nel [catalogo retail](known-bugs-hgss.md#primi-riscontri-statici-sulla-candidata-131).

| Input | SHA-256 |
| --- | --- |
| Plus 1.2.5 EN | `a821961fc1a90e4adaa118c4a09fce5445d25d567130d0c9edb20dfb0520050e` |
| Plus 1.2.5 IT | `bdf50a4f327f8ea0d8a2ef312e1491d78460d34e978d9b15d160eaf140b313d4` |
| Plus 1.3 V4 EN | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` |
| Plus 1.3 V4 IT | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` |
| Plus 1.3.1 pending EN | `15f379ebc7e99ce0ec0daa39a5627ccc3dbf4360601d82f59d7b7201078b76a6` |
| Plus 1.3.1 pending IT | `bc566c14050fae3ac7f204e65a63371954b3d7d7fcfb49689bc726cc903b57f1` |

I pending hanno tre moduli inerti: **non sono le candidate finali accettate**.
Un loro successore va identificato e ricontrollato. Le letture di dati non
certificano l'intera composizione, il comportamento del gioco o i save.

Riferimento script: `pret/pokeheartgold` commit
`0985e8718df4f25e64d6507d89c0c97c0d288981`; metadata comandi SHA-256
`fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a`.
Il [decoder pubblico](../features/borsa/tools/scr_disasm.py) permette roundtrip
dei membri pertinenti. Questo non certifica tutti gli script della ROM.

## I venti casi, senza promesse generali

**D** = dati/binding letti; **P** = percorso simbolico con semantica del
riferimento; **R storico** = precedente esecuzione documentata, non ripetuta qui.
«Aperto» non significa che il bug sia stato riprodotto sulla nostra ROM.

| ID | Segnalazione storica | Stato al presente audit |
| --- | --- | --- |
| SG-01 | Schermate nere/bianche nell'area Safari. | **Due difetti source-bound distinti sono corretti (SG-01a/SG-01b); il blackout generico di menu/audio resta non isolato.** Un [resoconto Storm Silver V1.1 su Delta/3DS](https://www.reddit.com/r/Delta_Emulator/comments/1d4yw1m/storm_silver_freezing_in_safari_zone_takeover/) restringe parte dei casi al ponte e riferisce anche Borsa/Squadra/Pokégear neri con audio bloccato. SG-01a copre la durata delle finestre; SG-01b copre soltanto la sconfitta contro l'amministratrice finale. Il censimento read-only non offre ancora una fixture utile per attribuire gli altri sintomi. Restano raw save contro savestate, turbo OFF/ON, menu, audio, SAVE/cold e hardware. |
| SG-01a | Durata della finestra nei dialoghi di cura partner sul Percorso 47. | **Difetto di componente source-bound dimostrato e corretto; accettazione runtime aperta.** Nelle candidate correnti EN/IT, mappa151→script260/evento146: i record coordinate 7/9/14/17 raggiungono rispettivamente le entry Mira/Buck/Cheryl/Marley. Mira chiude il dialogo prima di lasciare il campo, mentre gli altri tre eseguivano `LeaveOverworld`→`RestoreOverworld` e soltanto dopo `CloseMsg`. Il fix sposta ogni chiusura subito dopo `NPCMsg`; le tre rotazioni conservano lunghezza, offset e byte complementari. Il riproduttore pubblico [safari_lifetime.py](../sgp131/safari_lifetime.py) autentica dispatcher, handler/task nativi e sorgente pret pin-nato; l'unico producer [safari_archives.py](../sgp131/safari_archives.py) cambia soltanto il membro260 e verifica in sequenza SG-01a/SG-02 e SG-01b. Nessuna ROM è conservata. L'oracolo non attribuisce automaticamente a questa causa menu neri, audio bloccato o ogni SG-01 storico: raw save, gameplay, SAVE/cold e hardware restano aperti. È separato dal gate Safari `6130`, già famiglia V-CHATOT/HF02. |
| SG-01b | Sconfitta contro l'amministratrice finale sul Percorso 47. | **Difetto source-bound dimostrato e corretto; accettazione runtime aperta.** Nel membro260 il ramo di sconfitta del trainer107 da `0x61C` saltava a `0x6C4`, un percorso di inizializzazione che non raggiunge né `WhiteOut` né `ReleaseAll`. I quattro rami di perdita partner sani puntano invece tutti all'unico `WhiteOut` a `0x7A4`; il changelog autoriale 1.05 descrive la stessa correzione. Il fix same-size ritargetta soltanto i due byte variati del displacement e conserva byte-per-byte i `CloseMsg` SG-01a, il percorso vittoria e gli altri quattro rami perdita. [safari_defeat_whiteout.py](../sgp131/safari_defeat_whiteout.py) e il checker indipendente provano RED/GREEN, mutanti, replay/geometry EN/IT e owner unico del membro260. Mancano sconfitta giocata, SAVE/cold e dispositivo; non è una prova per menu/audio/turbo generici. |
| SG-02 | Battaglia sul Percorso 47 attivabile da posizione anomala. | **Difetto source-bound dimostrato e corretto; runtime naturale aperto.** Il [resoconto originale, post #1460](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-73) conserva lo [screenshot](https://imgur.com/JNtrO): il giocatore è sotto il ponte mentre parte il primo duo in alto. Il dispatcher nativo `sub_0203DE04` confronta X/Z, rettangolo e variabile ma ignora Y; il trigger custom Mira `script7 @ (141,397)` può quindi attivarsi dalla stessa colonna sul livello inferiore. Il record 0×0 è invece irraggiungibile e non è la causa. Non viene alterato il dispatcher globale: tutti i 217 `CoordEvent` correnti hanno Y=0. L'export 7 punta ora a un wrapper aggiunto di 23 byte che esegue `GetPlayerXYZ`, termina senza effetti se Y≠0 e raggiunge l'entry originale `0x1BF` soltanto alla quota del ponte. Quattro ipotesi/dodici sequenze, mutanti, roundtrip, producer e composizione/replay EN/IT passano; output deterministico privato SHA-256 `65e05d94…ab11`. Restano raw save pre-evento, battaglia naturale, SAVE/cold e hardware; gli altri tre trigger non sono dichiarati difettosi senza prova di un percorso inferiore sovrapposto. |
| SG-03 | Dialogo Latte MooMoo alterato. | Slang e difetto strutturale sono separati. Il [precedente intervento 1.04](../../CHANGELOG.md#104--9-september-2026) ripara controlli testo. Nelle 1.2.5 e pending EN/IT, banco 397/voci 12–14 ha controlli di centratura validi; nessuna nuova scena osservata. |
| SG-04 | Lastra Ghiaccio/Steven ad Aranciopoli non funzionano su R4. | **Segnalazione hardware aperta, non una singola causa dimostrata.** L'[elenco originale](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/) accorpa due eventi; un [rapporto contemporaneo](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-25) attribuisce a R4 lo Steven immobile, mentre Drayano documenta separatamente [problemi d'ordine nello script Steven](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-59), oggi SG-15 corretto. Attese e percorsi correnti non mostrano una divergenza comune. Senza modello, kernel, save e prima callback errata di un R4 autenticato, nessuna patch ROM aggiuntiva è giustificata. |
| SG-05 | Freeze dell'evento Mew. | **Correzione 1.3 documentata, R storico.** Tre attese dei movimenti; [causa, hash e prove](deep-debug-2026-10-28.md#crash-mew-riprodotto-e-causa-dimostrata), [campagna EN/IT](android-1.3-dev-validation.md). Nessun nuovo playtest 1.3.1/flashcard qui. |
| SG-06 | Rough Skin mancante a Garchomp. | **D coerente con fix ereditato.** Slot abilità 8/24, quindi Rough Skin presente nella 1.2.5 e nei pending EN/IT. Effetto non rieseguito in lotta. |
| SG-07 | Claydol non impara Volo. | **D coerente con fix ereditato.** Bit compatibilità HM02 presente nella 1.2.5 e nei pending EN/IT; apprendimento UI non giocato. |
| SG-08 | Doppioni Lyra/Ethan dopo sconfitta a Fiordoropoli. | **Corretto nei sorgenti successivi:** SetFlag712 prima di WhiteOut e retry preservato; tre percorsi perdita in modello. Nei sei vecchi input il difetto resta. Doppioni e compatibilità save non ancora osservati sulla nuova composizione. |
| SG-09 | Ball con circa 450 Cura Totale. | **Corretto nei sorgenti successivi: richiesta436→1.** Nei sei vecchi input resta436, non450. Quantità aggiunta e policy di saturazione dipendono dagli hook Borsa preservati. Prove bytecode in modello, nessuna misurazione inventario in partita. |
| SG-10 | Refuso descrizione Pietrastrana. | Autore Plus dichiara fix 1.02. Testo attuale EN/IT leggibile; il refuso storico esatto non è identificato per confronto. Non contare una nuova correzione nostra. |
| SG-11 | Pesca notturna: slot vuoti/Missingno. | **D/P presente nei sei input hack**, assente come troncamento nei due retail controllati. Coinvolge anche sciami e telefono; dettagli sotto. Nessuna cattura/crash provocato. |
| SG-12 | Manuale: Vento Argento sul Percorso 39 invece del 38. | Correzione documentale dichiarata dalla 1.02; il [censimento acquisizioni](../sgp13/data/guide-content-sources.md) colloca la Ball TM62 sul 38. Non è una nuova patch al motore; nessuna nuova verifica integrale dei PDF storici. |
| SG-13 | Nomi Gentiluomo/Madame del Percorso 34. | **Bug dati confermato; `SOURCE_EXHAUSTED`, nessuna patch sicura.** Mappa38/evento35 lega object0 Gentleman al trainer62 e object13 Lady/Socialite al 409. Classi e sprite sono coerenti, ma i nomi restano quelli retail Youngster Samuel/Emanuele e Pokéfan M Brandon/Mariano; dieci Gentleman controllano il decoder. Drayano scrisse soltanto che i nomi «haven't stuck». Il riesame di thread/Wayback, ZIP ufficiale 2012 byte-identico al mirror, tutti i sei PDF, FAQ, video, guide e ricerche multilingue non trova i nomi voluti. Brenda/Mariana o altre rinomine sarebbero invenzioni: riaprire solo con una nuova fonte autoriale. |
| SG-14 | Nome della coppia del Percorso 13. | **D coerente con fix ereditato.** Trainer 559: Tim＆Sue EN, Udo&Mia IT, flag doppio 2. Intro della battaglia non osservata. |
| SG-15 | Steven non riconosce Lati dopo Regigigas. | **Corretto nei sorgenti successivi:** priorità al Lati corretto ancora dovuto, preservando gli altri stati775. Prove modello prima/dopo; nei sei vecchi input resta la precedenza errata. Nuovo sottocaso SG-15b: premio perso logicamente con Borsa piena, ora guardato. Nessuna scena nuova giocata. |
| SG-16 | Freeze Celebi/Giovanni alle Cascate Tohjo. | **Non confermato, D/P/modello; runtime bloccato dalla fixture.** Il membro 114 e il binding mappa 298 sono byte-identici in nove immagini storiche EN/IT. Dodici controlli confutano binding errato, attesa movimento mancante, campo non ripristinato dopo la sconfitta e task deterministicamente non terminante. Nessuno dei 184 raw save unici validi contiene uno stato pre-evento utilizzabile. Le tre dereferenziazioni native del follower restano un rischio latente, ma non è stato dimostrato un `NULL` raggiungibile dal percorso ordinario. Nessun cambio ROM senza prima divergenza giocata. |
| SG-17 | Cynthia non consegna starter Sinnoh dopo Medaglia Terra. | **Confutato come requisito errato, D/P/modello; nessuna patch.** Dodici sequenze sul membro 890 reale, byte-identico in nove immagini EN/IT, confermano che il premio non controlla la Medaglia Terra: richiede titolo di Campione, flag 3F9B libero, starter Sinnoh/evoluzione come primo Pokémon vivo e due slot liberi. Testi EN/IT e Guida descrivono lo stesso contratto; matrice 387..395, squadra 1..6, mutanti e ciclo del flag passano. Nessuna delle 184 fixture raw uniche consente il playtest completo; riaprire solo con un save conforme che venga comunque rifiutato. |
| SG-18 | Scizor impara Night Shade al posto di Night Slash. | **D coerente con fix ereditato.** Night Slash, ID 400, ai livelli 45/65 nelle 1.2.5 e pending EN/IT; non attribuire Neropulsar al resoconto originale. |
| SG-19 | Flag che si azzerano apparentemente senza motivo. | La 1.3 corregge una concreta [sovrapposizione dei flag alti con la Rubrica](../features/event-flags/README.md), con [prove storiche](android-1.3-dev-validation.md). Un [save community 1.0.5](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-113) perde insieme i trigger Jirachi e Manaphy ed è una nuova fixture utile, non una causa distinta già dimostrata. Non inferire una causa unica per tutti i reset riferiti. |
| SG-20 | Statistiche Attacco/Attacco Speciale di Ledyba non scambiate. | **D: dichiarazione 1.02 non confermata nella nostra 1.2.5**, ancora 20/40. V4 e pending hanno 40/40 come [ribilanciamento intenzionale](shiny-species-1.3.md), non lo scambio 40/20. Non sottrarre SpA per inseguire la vecchia dichiarazione. |

## Nuovi candidati community del 3 novembre 2026

Queste tre schede non fanno parte dei venti casi originari. Restano separate
per evitare di attribuire alla ROM dati letti soltanto in una guida o in una
vecchia testimonianza; SG-TR01 è stato successivamente confutato sulla linea
disponibile, SG-TR02 è stato confermato e corretto nei sorgenti, mentre SG-TR03
resta confermato staticamente ma senza una squadra sostitutiva inventata.

| ID | Segnalazione e fonte | Verifica richiesta |
| --- | --- | --- |
| SG-TR01 | Nel rematch massimo del Gentiluomo Alfred al Faro, Noctowl, Arcanine e Nidoking sarebbero privi di moveset e userebbero soltanto Scontro. [Testimonianza diretta GBAtemp, 18 settembre 2012, pagina 67](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-67). | **Confutato sulla linea disponibile, D/P; nessun fix.** Dieci immagini autenticate EN/IT dalla Plus 1.04 alla candidata corrente hanno lo stesso trainer 674 tipo 1/custom-moves: tre record con dodici ID mossa non zero. L'overlay 26 contiene una sola progressione `401/401/672/673/674/0`, quindi il selettore raggiunge quel record. Risultato ripetuto byte-identico; bench nativo locale limitato da `SIGILL`, battaglia non giocata e nessun input autenticato 1.05/Plus 1.03. La testimonianza può descrivere un artefatto storico più vecchio, non un difetto dimostrato della candidata. |
| SG-TR02 | I primi due rematch di Pigliamosche Wade risulterebbero invertiti: prima livelli circa 52, poi 46. [Guida trainer v1.05 ri-pubblicata dalla community](https://www.scribd.com/document/866552982/SS-SG-Trainer-Pokemon-by-JD48096761). | **Confermato e corretto nei sorgenti, D/P.** L'unica tabella del selettore è `4/4/461/460/512/0`; perciò la ROM corrente esegue davvero livelli 52→46→68. Il nuovo stadio `trainer-fixes` scambia soltanto i due membri squadra 460/461, di uguale misura, ottenendo 46→52→68 senza cambiare selettore, header, specie, mosse, geometria NARC o altri allenatori. Sei test mirati e l'applicazione reale in memoria sulle candidate EN/IT passano; otto byte livello sono i soli intervalli diversi. Restano i rematch giocati sullo stesso save e una candidata conservata. |
| SG-TR03 | Il primo rematch di Avicoltore Jose usa il roster retail, un solo Farfetch'd livello 44, fra squadre Plus. [Guida trainer giocata](https://www.scribd.com/document/866552982/SS-SG-Trainer-Pokemon-by-JD48096761). | **Anomalia riprodotta; `SOURCE_EXHAUSTED`, fix bloccato dall'oracolo.** Il selettore `414/414/303/446/602/0` produce duo Farfetch'd+Chatot 48, solo Farfetch'd 44, duo 55 e trio 68, identico da Plus 1.04 alle V4 EN/IT. La guida JD lo chiama «probably a bug» ma dichiara di essere un log giocato, non documentazione autoriale. Thread/Wayback, ZIP ufficiale 2012, sei PDF, FAQ/video, mirror e guide multilingue non prescrivono la tuple. Reena/Gaven/Jamie suggeriscono un duo 50, ma non determinano record, difficulty o politica mosse. Una sostituzione sarebbe una decisione di bilanciamento, non il recupero di un fix storico dimostrato. |
| SG-EV01 | Mantyke non evolve con Remoraid in squadra; [testimonianza contemporanea](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-36) e [conferma dell'autore che il dato richiede Voltorb](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-59). | **Confermato e corretto nei sorgenti/al componente.** Il membro 458 di `a/0/3/4` usava Voltorb 100 invece di Remoraid 223. Il producer cambia soltanto quel parametro, con pre/post-hash e rilettura semantica; la Guida è generata dagli stessi record corretti. Mancano evoluzione giocata, SAVE/cold e dispositivo. |
| SG-EV02 | Feebas tenta di evolvere a ogni livello anche con Bellezza zero; [nota dell'autore](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/) e [prova indipendente](https://www.reddit.com/r/PokemonROMhacks/comments/ff16ju/sacred_goldstorm_silver_feebas_randomly_evolved/). | **Confermato e corretto nei sorgenti/al componente.** Il membro 349 aveva soglia Bellezza 0 invece di 170. Il fix modifica soltanto il parametro; controlli runtime richiesti 169/170 e annullamento+riprova. |
| SG-EV03 | Combee femmina può evolvere già dal livello 6; [resoconto community](https://www.reddit.com/r/PokemonROMhacks/comments/cgxkao). | **Confermato nei dati e corretto nei sorgenti/al componente.** Il membro 415 aveva livello 0 invece di 21; genere maschile e confine 20→21 sono i negativi. Il resoconto era randomizzato, ma coincide con la preimmagine identica in dieci Plus EN/IT. |
| SG-EV04 | Burmy femmina tenta l'evoluzione prima del livello previsto. | **Confermato nei dati e corretto nei sorgenti/al componente.** Il ramo femmina del membro 412 aveva livello 0 invece di 20, mentre il ramo maschio conservava già 20 e funge da controllo differenziale. |
| SG-AI01 | L'IA della Plus non riconosce il tipo Fairy nelle scelte e nei cambi, pur applicando il danno corretto. | **Confermato e corretto nei sorgenti/al componente; runtime battaglia pendente.** Il vecchio banco su otto ROM resta la preimmagine (120 divergenze Fairy, zero retail). Il fix usa un helper Thumb residente da 148 byte, SHA `d965f5ff…b2a6f`, e due seam in overlay 12: gestisce soltanto righe/colonne Fairy e delega ogni altra coppia al consumer nativo, preservando HG-B13, Scrappy, Gravità e Ferropalla. Il solo fix SG-AI01 aggiungeva 8 byte compressi; la composizione corrente con SG-AI02/SG-DM01 aggiunge 20 byte. FAT 12, parola dimensione y9 e il solo CRC y9 derivato di Module96 sono riletti e riconciliati, mentre il peel ricostruisce la UI fredda. Helper, oltre 76.000 casi dinamici, mutanti e composizione completa passano EN/IT; restano battaglie naturali/communication, SAVE/cold e dispositivo. |
| SG-AI02 | Conversione2 non considera il tipo Fairy quando sceglie il nuovo tipo. | **Confermato e corretto nei sorgenti/al componente; runtime battaglia pendente.** Il vero comando `0x02240C98` chiamava `GetTypeEffectivnessData` a `0x0225260C`, fermo a 112 righe retail: con ultimo tipo Fairy scandiva l'intera tabella senza cambiare il tipo corrente. Il riproduttore ARM EN/IT osserva il fallimento e il controllo Fire corretto. Il writer sostituisce esattamente i 64 byte del helper con una versione autenticata (SHA `1ab0ab8d…5875`) che usa le 325 righe selezionabili della chart moderna e preserva RNG/modulo nativi; dopo il fix Fairy sceglie una resistenza valida e non legge la tabella retail. Replay, mutanti e catena completa passano EN/IT; restano battaglia naturale, SAVE/cold e dispositivo. |
| SG-DM01 | Il danno con Ferropalla o Gravità può consultare colonne retail usando l'indice della matrice moderna. | **Confermato e corretto nei sorgenti/al componente; runtime battaglia pendente.** Il calcolo reale `0x02251D28` indicizzava la chart moderna ma il helper `0x02251C74` dereferenziava ancora le colonne retail. Il riproduttore ARM EN/IT mostra Ground→Flying correttamente immune senza grounding ma ancora immune, erroneamente, con Ferropalla o Gravità. Il fix cambia soltanto i due literal a `0x02251D20/24` verso `modern+1/+2`: entrambi i casi diventano danno 100/nessun `NO_EFFECT`; Ground→Veleno e Fairy→Drago restano controlli negativi verdi. Replay e catena completa passano EN/IT; restano battaglia naturale, SAVE/cold e dispositivo. |
| SG-DM02 | La chart danno Plus scambiava i moltiplicatori Spettro→Drago e Spettro→Buio, [segnalato anche dalla community sulla 1.1.2](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-114). | **Confermato e corretto nei sorgenti/al componente.** Sei versioni dalla Plus 1.04 alle manual-test 1.3.1 EN/IT hanno `5` per Drago e `10` per Buio; le altre 322 coppie coincidono con l'oracolo moderno. Il producer confinato scambia soltanto quei due byte in overlay 18 ed è composto nello stadio `ai`; doppia rilettura EN/IT, replay e mutanti passano. Mancano lotta naturale, SAVE/cold e dispositivo. |

Caso interno scoperto dopo questo catalogo, **V-CHATOT**: 24 variabili storia
`612E..6139`/`619E..61A9` erano fuori dominio e aliasavano i campioni Chatot.
È riprodotto e corretto a livello componente con HF02; vedere il
[rapporto codice](bug-audit-1.3.1.md) e il
[contratto nativo](../features/event-flags/README.md). Non è una delle venti
segnalazioni storiche e non viene rinumerato artificialmente come SG-21.

Caso riferito direttamente dal maintainer, **SG-LATIOS**: al totem centrale di
Aranciopoli, dopo dialogo e movimento, l'ingresso nella lotta Latios può
mostrare schermo bianco e audio fermo su una nota. È **aperto e non isolato**.
La mappa 54 usa script 776/entry 16, evento 51 e `WildBattle(381,40,0)`; script
`f70f4320…cbf2`, evento `e407ae57…b9a26`, movimento e finestre native di lancio
lotta risultano invariati in tutte le 26 ROM conservate. La stessa esatta 1.2.5
ha sia un freeze riferito sia
una prova riuscita. L'assenza storica di `WaitMovement` non è causa dimostrata:
nel run riuscito il movimento era già terminato prima di `WildBattle`. Le
candidate correnti passano 18 scenari statici EN e 18 IT. La 1.3.1 cambia solo
la BL verso l'hook shiny per questa statica: va collaudata, ma non può spiegare
il rapporto storico 1.2.5. Non trasferire per
analogia il fix Mew e non dichiarare il freeze corretto senza una prima
divergenza macchina; protocollo e identità sono nel rapporto privato della
campagna Latios.

Il banco runtime del 3 novembre aggiunge 10 cold boot 1.2.5 IT e 10 sulla
candidata IT `420ec8b8…f059a`, con intervalli input 112..130 frame: **20/20**
raggiungono offset 1704 e proprietà della lotta, movimento zero, nessun assert,
ROM e fixture intatte. Digest `51a28336…657f`. È un non-riprodotto più forte,
non un fix né una confutazione universale: una sola fixture e un solo runtime,
senza ARM7/FIFO, audio o dispositivo. Il criterio di arresto sul banco identico
è raggiunto; riaprire la ripetizione soltanto con save/configurazione del freeze
o ambiente indipendente.

Il ricontrollo del 4 novembre sulle postimage correnti Via Vittoria conserva
gli stessi hash di script/evento e passa 36 scenari statici complessivi e 7/7
prove del banco. Questo rafforza il non-riprodotto, ma non identifica una causa:
nessun `WaitMovement` o altro fix Mew viene trasferito senza divergenza macchina.

La ricerca esterna mirata non ha trovato una seconda segnalazione indipendente
del freeze. Ha però trovato un controllo sano distinto: un
[diario di gioco polacco](https://pokemon.fandom.com/pl/wiki/Blog_u%C5%BCytkownika:Jetian/Pok%C3%A9mon_Sacred_Gold_i_Storm_Silver)
descrive reazione della Cuorugiada, comparsa, lotta e cattura di Latios. È
coerente con il run locale riuscito, ma non confuta un difetto intermittente o
dipendente dallo stato del save. Il suono fermo sull'ultima nota è un sintomo
di mancato avanzamento, non prova autonoma di una causa audio.

La risoluzione trainer aggiunge `FIRST_TRAINER_INDEX = 1` dopo la sottrazione
3000/5000: ometterlo attribuirebbe erroneamente i nomi del trainer precedente.
[Codice del riferimento](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/script_manager.c#L425).

## Radici della prima ricognizione e seguito

Le sezioni seguenti conservano le letture dei vecchi input e le proposte
originarie. L’implementazione e le verifiche successive sono nel
[rapporto codice](bug-audit-1.3.1.md); non modificano retroattivamente questi hash.

### SG-09: quantità del pickup

`a/0/1/2`, membro 141, entry zero-based 56, script globale 7056:
`0x0862` imposta item 27; `0x0868` imposta quantità **436** (operando a
`0x086C`). Il ramo comune copia questi parametri nel controllo spazio e in
GiveItem. Binding: mappa 201, Goldenrod Tunnel B2F, evento 194/oggetto 35,
coordinate (7,4), flag nascondimento 1095. Non è una routine morta scollegata
da un oggetto. Non è stato percorso a piedi l'accesso alla Ball.

La Borsa Plus modifica HasSpaceForItem/GiveItem: non dedurre dalla sola
sequenza script che ogni inventario riceva esattamente 436, che un tetto
raggiunto lasci la Ball sul posto o che il dono non possa essere parziale.
Il [contratto Borsa](../features/borsa/README.md) va incluso nell'oracolo.

Correzione proposta, non applicata: dopo conferma dell'intento del pickup,
portare a 1 il solo operando quantità. Preservare flag/ID e tutti gli oggetti
già ottenuti: nessuna sottrazione retroattiva. Prove: inventario vuoto/popolato,
tetto/spazio insufficiente, raccolta una sola volta, SAVE/cold EN/IT.

### SG-08: perdita contro l'amico

Il membro 93 è identico nei sei input:
`99681fdf303533d7eae6bf06ef672a5b947ee1a2b4a3261a7929bfe363d051e0`.
Mappa 118, Goldenrod Tunnel 1F, evento 115: oggetti 2 e 3, amico e Marill,
condividono hideflag 712/`0x2C8`. La scena ancora abilitata con `40F8=0`
crea i due oggetti dopo aver reso il flag visibile.

I rami perdita delle battaglie 11/19 raggiungono `0x0553`:
WhiteOut, ReleaseAll, End, senza il ripristino di 712. Il caricamento successivo
può quindi predisporre gli oggetti che la scena crea nuovamente. Il riferimento
oggetti corrobora la mancata deduplicazione ordinaria; non sono state eseguite
né confrontate integralmente in ARM tutte quelle funzioni.

Proposta: ripristinare **lo stesso** hideflag sul ramo perdita prima di WhiteOut,
conservando `40F8=0` e la possibilità di ritentare. Nessuna nuova variabile o
conversione save. Servono entrambi i generi, ingressi nord/sud, perdita/ritorno,
successiva vittoria, conteggio NPC e SAVE/cold; includere un vecchio save dopo
una perdita. Eventuali doppioni già serializzati richiedono osservazione propria.

### SG-15: ordine dei controlli di Steven

Il membro 757 è identico nei sei input:
`c223b9665a411c9d99a1e73a5857d87931ec41a24a126ad288f55c3bfd1b4b69`.
Binding: mappa 477, casa di Steven a Pewter, evento 430/oggetto 0,
entry 1 one-based (indice 0).
Dopo introduzione e dono Hoenn, `0x0037` controlla 775/`0x0307`;
se impostato, `0x003B` salta a `0x0458`, **prima** dei controlli Lati
`3FCA`/ricompensa `3FB8`. Il ramo mostra messaggio 23 e può aprire la sfida
con Steven, senza arrivare alla consegna Enigma Stone ancora dovuta.

775 è `FLAG_HIDE_MT_SILVER_CAVE_MOLTRES` retail, riusato per Regigigas in
script 106 e anche da script 815. Il flag cattura 365 è anch'esso riusato;
Hall of Fame 825 cancella 775 solo se 365 non è impostato: dopo la cattura,
con 365 impostato, non lo cancella. Non indicare di cancellare flag o rifare
la Lega per «risolvere».

Proposta: correggere precedenza/guardia del dialogo preservando gli ID, i
leggendari già catturati e la consegna unica. Servono i due ordini Lati/Regigigas,
ricompensa già ottenuta/non ottenuta, Lati valido/errato, Medaglia Terra
presente/assente, Borsa piena e SAVE/cold EN/IT. I due percorsi simbolici
con/senza 775 non sostituiscono queste scene.

### SG-11: pesca e consumer secondari

Nei due retail controllati, tutti i 142 record di `a/0/3/7` sono di 196 byte.
Nelle sei immagini hack, l'archivio è identico:
`a66f72f48341a1ec3131b521641ab6e671ad890d07676131b00fed2704ec3d4d`.
Contiene 130 record di 192 byte e 12 completi; **70 record troncati hanno
pesca attiva**. I quattro byte assenti contengono `nightFish` a 192 e
`fishSwarm` a 194. Il loader azzera il buffer prima della lettura: restano zero.

Letture dei consumer, non esecuzioni:

- Overlay 2, `0x02246AD4`: di notte sostituisce senza guardia specie zero in
  Good Rod slot 3 e Super Rod slot 1; pesi ordinari 10%/30% degli incontri
  generati, non di tutti i lanci.
- Overlay 2, `0x02246BD8`: gli sciami di pesca possono sostituire con zero
  ulteriori slot, anche di giorno.
- Overlay 101, `0x021F2E24`: anche le telefonate dei pescatori leggono il
  campo notturno; correggere solo la battaglia lascerebbe questo consumer.
- La radio Pokémon Talk controlla già il valore non nullo.

**Copiare le code retail cambierebbe incontri validi della hack.** Il manuale
originale conservato nei pacchetti, *Pokemon Locations.pdf*, pagina 2, specifica
per New Bark Good Rod Shellder 60%/Chinchou 40%, Super Rod Shellder 60%/
Lanturn 30%/Gyarados 10%, senza distinzione oraria. Gli slot attuali coincidono;
la sostituzione retail eliminerebbe il 30% Lanturn. Non è una riparazione neutra.

Proposta: zero deve significare «nessuna sostituzione notturna» nei due
consumer interessati; completare i record mantenendo i primi 192 byte e
ripristinare i soli sciami effettivamente mappati: Violet/Whiscash,
Route 12/Relicanth, Route 44/Remoraid, Route 32/Qwilfish. Per Route 32 il manuale
non ha la riga Swarm: il riscontro viene dalla tabella nativa e dalla stessa
mappa retail; questa differenza documentale resta esplicita.

Un modello Python enumera 1.125 combinazioni record/amo/orario/sciame; 340
contengono specie zero con i consumer trascritti, nessuna con la policy
ipotetica. **È un modello, non ARM eseguito o pesca giocata.** Il tentativo
Unicorn in sandbox termina SIGILL prima del risultato e non è un PASS.
Servono poi codice realmente installato, controlli negativi, tre ami, cinque
orari, quattro sciami, telefono, radio, Safari separato, EN/IT e SAVE/cold.

## Versione alternativa citata dal commentatore

**Il commento è stato individuato; il nome della patch resta non attribuibile.**
È di speedguru, [30 ottobre 2026, 23:54 UTC](https://www.reddit.com/r/RomHacks/comments/1xebcg1/comment/19rwjjgmhq8ar/).
Nel post vivo il testo non dà nome o link e non ha risposte visibili. La cache
mostrava solo due commenti; il browser ne mostrava 17 e ha permesso il riscontro.
Il profilo pubblico dichiara i commenti nascosti: nessun accesso privato o
messaggio è stato tentato. I crosspost pubblici del maintainer non danno un nome.

DeadSkullzJr, SunGold/MoonSilver e Reforged rimangono candidati da confrontare,
non l'identità stabilita del commentatore. La manutenzione DeadSkullzJr distingue
[packaging/AP e gameplay](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110);
[1.1.1/1.1.2](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-111)
non dichiarano risolti tutti i venti casi. Un
[resoconto Mew del marzo 2026](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-114)
manca di hash e non dimostra una causa universale, ma impedisce quella promessa.

Per [Reforged Alpha 5a](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/KNOWN_ISSUES.md)
sono stati verificati tre piccoli file sorgente/documentali per SHA-256 e Git
blob: circa 27KB, nessun gioco o donor acquisito. Il cleanup partner Safari
dichiarato in Alpha 4ab non è stato dimostrato equivalente a SG-01. Il
[sorgente installer](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/sacred_gold_patcher.py)
applica un xdelta con due donor; non espone il codice della correzione Safari.
REA non può ricavare quel fix dal solo packaging. Nessun delta gioco è stato
importato e nessuna compatibilità fra le linee viene presunta.

| Linea | Dichiarazioni primarie effettivamente trovate | Limite |
| --- | --- | --- |
| Plus 1.02/1.03 originale | Sette correzioni nominate nel post Reddit; mosse/abilità, testi e un documento. | Ledyba dimostra perché va controllato l'input concreto. |
| DeadSkullzJr 1.1.1 | [Autore, pagina 110](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110): gioca come 1.1.0; interventi su immagine, Classic e AP. [Reupload 19 agosto 2025](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-111) per effetti degli strumenti tenuti. | Il numero versione non distingue il reupload; non è un elenco di fix per tutte le quest storiche. |
| DeadSkullzJr 1.1.2 | [13 settembre 2025](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/post-10726814): ripristino inglese degli asset Pokédex. | [Resoconto Mew su 1.1.2](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-114) mostra che non si può inferire soluzione universale. |
| SunGold/MoonSilver | [Topic dell'autore](https://projectpokemon.org/%68ome/forums/topic/37260-pok%C3%A9mon-sungold-amp-pok%C3%A9mon-moonsilver/), marzo 2016: ribilanciamento, con avvertenza sui crash Safari. | Accesso diretto 403, testo primario indicizzato leggibile; non baseline di riparazione provata. |
| Sacred Gold Reforged | [Repository autore](https://github.com/oliverdesa/Sacred-Gold-Reforged), creato 26 ottobre 2026. [Alpha 5a](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/KNOWN_ISSUES.md) dichiara anche un cleanup del partner Safari in Alpha 4ab. | Integrazione Gen V/Anvil; [README](https://github.com/oliverdesa/Sacred-Gold-Reforged/blob/main/patcher/README.md) segnala prototipo e compatibilità save non universale. Nessuna nostra build/prova e nessuna identificazione con la versione del commentatore. |
| Sacred Gold Revamped | [Autore, 2015/2020](https://www.pokecommunity.com/threads/sacred-gold-revamped.359688/): modifica squadre fino a Chuck; incompleto e abbandonato. | Non una correzione generale dimostrata. |

Le affermazioni dei redistributori «complete», «fixed» o «no bugs» non sono state
usate come prove. Problemi di loader/AP/emulatore rimangono separati da errori
ROM: un issue chiuso non dimostra di per sé una correzione del gioco.

## Altre segnalazioni da conservare separatamente

- **Cloyster a Fucsiapoli:** il [resoconto del 13 settembre 2024](https://www.reddit.com/r/PokemonROMhacks/comments/1ffyvun/)
  descrive sovrapposizione e workaround di coordinate. Nella nostra mappa 56,
  script 807/evento 53, la disposizione degli oggetti non basta a dimostrare
  impossibilità di interagire. Un [resoconto 1.05 contemporaneo](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-33)
  aggiunge un difetto distinto: la fuga riuscita farebbe sparire il Cloyster e
  avanzare l'evento come una vittoria. Provare separatamente i tre Cloyster con
  vittoria, sconfitta, fuga riuscita/fallita e flag prima/dopo. Aperto, nessun
  fix dedotto da un singolo frame.
- **GB Sounds durante il takeover della Torre Radio:** due utenti 1.05
  riferiscono musica GB e moderna sovrapposte, poi silenzio aprendo X/menu dopo
  la chiave; Drayano collega il caso all'ottenimento anticipato del GB Sounds
  ([pagina 33](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-33),
  [pagina 47](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-47)).
  È distinto da HG-F06 Surf. Provare takeover con GB Sounds OFF/ON, attivazione
  prima/dopo, stesso percorso retail e cold boot senza cheat/turbo.
- **Lyra/Ethan con premio zero:** Drayano conferma che la classe speciale usa
  moltiplicatore denaro zero ([pagina 59](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-59)).
  La candidata conserva classe 1 e la tabella nativa classe1→0: presenza
  statica, non ancora saldo osservato. Confrontare Silver e un allenatore
  ordinario, Monetamuleto OFF/ON e denaro prima/dopo.
- **Percorso 43, Gastrodon chiamato Nidoking:** l'autore riconosce il testo
  errato ([pagina 23](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-23)).
  Il trainer 132 conserva un solo Gastrodon L40 e il banco EN conserva «My
  Nidoking was outstanding!». Osservare il binding EN/IT e l'eventuale rematch;
  nessuna squadra corrente del caso contiene Nidoking.
- **Rovine d'Alfa, dono Unown:** un singolo utente 1.05 con 18 Unown riferisce
  «communication error» parlando al secondo uomo da sinistra, non ripetuto
  dopo reset ([pagina 35](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-35)).
  Bassa priorità finché non si ripete con 17/18/19 Unown, cold boot contro
  savestate, altri NPC/doni, cheat/turbo OFF e EN/IT.
- **Union Room/scambi e ricomparsa di eventi custom:** tre gruppi storici
  separati riferiscono doni o eventi già conclusi che ritornano dopo scambio,
  Union Room o mixing records: [pagina 46, 2012](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-46),
  [pagina 99, 2018](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-99)
  e [pagina 100, 2018](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-100).
  Rocket davanti alla Palestra di Jasmine, dono Pikachu e Kimono Girl Jirachi
  rendono il sintomo più corroborato della sola pagina 115; il forum non prova
  però la causa. Confrontare separatamente semplice ingresso, scambio e mixing
  records sui medesimi flag prima/dopo SAVE e cold restart. È la migliore
  regressione esterna per il fix locale flag alti/Pal Pad, non un nuovo bug da
  ricontare prima di dimostrare un delta residuo.
- **Moltres catturato, SAVE e Continue nero:** un
  [resoconto Reddit](https://www.reddit.com/r/PokemonHGSS/comments/1mkvka5/game_crash_in_sacred_gold/)
  contiene un secondo caso su DraStic oltre all'autore su melonDS; un precedente
  del 2018 è nella [pagina 100 GBAtemp](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-100).
  Versioni e hash mancano, ma la sequenza è più forte di una singola ipotesi.
  La [pagina 115](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-115)
  aggiunge un recupero attribuito al byte save `0x18BA` e sette flag Safari,
  con analisi tecnica dichiaratamente generata da AI. Non adottare quel byte
  come causa o riparazione senza watchpoint, confronto dei due slot e fixture
  pre-cattura; nessun azzeramento generico dei save.
- **Codadrago sul Percorso 47 durante l'arco Rocket/Safari:** segnalazioni del
  [2012](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-25)
  e [2022](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-108)
  collegano la raccolta prima della liberazione Safari a schermo nero o menu
  bloccati; un [caso 2025](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110)
  amplia i sintomi ma non isola l'oggetto. Provare prima/dopo doppia lotta e
  fine arco, quindi Borsa/Squadra/Pokégear/SAVE e cambio mappa. Non fondere
  l'intero takeover con lo script premio finché il controllo dopo l'arco non
  discrimina la causa.
- **Nastri dei fratelli dei giorni:** due testimonianze del 18–19 settembre
  2012 riferiscono musica interrotta e freeze dopo il dono, prima con Tuscany
  e poi con tutti i fratelli. Corrobora la famiglia già corretta in
  [rapporto gift-script](gift-script-fixes-1.3.1.md); è una fonte storica
  aggiuntiva, non un nuovo
  bug aperto né una seconda patch.
- **QA-05:** Mr. Mime e Lopunny mantengono learnset di 46 byte con terminatore
  a 42 e due zeri finali nei sei input hack, compresi i pending. È una violazione
  del contratto dei consumer, senza crash/perdita dati dimostrati da questo audit.
- **Lastra Ghiaccio:** il ramo letto non imposta direttamente hideflag `3FAB`;
  eventuale ripetibilità richiede una scheda propria e tracing dei consumer.
  Non è già una spiegazione del freeze R4.
- **Stone shop Storm Silver Fairy 1.1:** [FAQ di Drayano, Q85](https://pastebin.com/UEzNBDHC)
  lo attribuisce a quella variante e distingue Sacred Gold, non interessato.
  Non è un bug nuovo della nostra base dimostrato.
- **Guardia della Frontiera Lotta:** un [resoconto storico con risposta di
  Drayano](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-23)
  riferisce freeze parlando alla guardia prima di Fiorlisopoli/Jasmine; l'autore
  credeva di averlo già corretto. Fare un regression screen prima/dopo Medaglia
  Minerale, dialogo e collisione, su melonDS e controllo DeSmuME. È un singolo
  report, non un bug riaperto della candidata.
- **Ghicocca Box:** un [solo caso Delta](https://www.reddit.com/r/Delta_Emulator/comments/1e8i7ey)
  riferisce schermo nero aprendola dopo Kurt; un commentatore sospetta una ROM
  errata. Prima fissare hash/patch e ripetere lo stesso raw save su candidata e
  retail. Bassa priorità, possibile problema di packaging/emulatore.
- **Olivinopoli/rivale e Spearow con lettera:** sono casi storici dichiarati
  corretti rispettivamente in 1.0.1 e 1.0.4. I report Delta moderni senza hash
  giustificano un rapido regression screen, non la riapertura automatica né una
  nuova patch. Conservare identità ROM, cheat/turbo e lo stesso raw save.

## Nuove piste hack-specific — giro globale 3 novembre

- **Deoxys evento/battaglia:** due rapporti descrivono crash nel 2012 e mancata
  comparsa all'orario previsto nel 2020, senza build dichiarata. Provare 1.05
  autenticata e candidata EN/IT con Medaglia Terra e confini RTC
  23:59/00:00/03:59/04:00. [2012](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-45),
  [2020](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-104).
- **Percorsi Pokédex non aggiornati:** rapporti coerenti 2016–2025; serve
  cross-join incontri reali↔risorse area per orario e variante, distinto dal
  filtro regionale retail. [2016](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-94),
  [2025](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-110).
- **Freeze presso Grotta di Mezzo:** un rapporto identifica pescatore sul ponte
  ed escursionista esterno verso Azalina; versione/emulatore ignoti. Mappare ID
  trainer/script e ripetere talk→battle su save pulito.
  [Fonte](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/page-104).
- **Map Card al secondo playthrough:** due post 2025 dello stesso autore valgono
  come una sola testimonianza. Ispezionare Guide Gent e flag Map Card prima di
  promuoverla a bug.

## Continuità dei salvataggi e prossima integrazione

Le proposte sopra preservano gli identificatori degli eventi e non richiedono
un nuovo formato save. Questo è un vincolo progettuale, **non una compatibilità
già testata delle correzioni**; per lo stato implementato vedere il seguito. Nessun oggetto,
Pokémon, progresso o impostazione Plus già posseduto deve essere sottratto o
azzerato; niente nuova partita per accedere ai fix.

Prima dell'integrazione servono test che falliscono sull'originale e passano
sul corretto, preimmagini fissate, readback indipendente e controlli delle
risorse estranee. La 1.3.1 usa un unico writer per gli archivi e semi UI legati
al FAT/header: appendere una seconda copia dopo la UI invaliderebbe quel
contratto. Le modifiche vanno dichiarate al produttore corretto e verificate
sulla composizione finale, non sovrapposte a una ROM già accettata.

Per l'accettazione usare copie di save vecchi senza Plus, configurati, con
Borsa espansa e con attività Training: Continue, SAVE nel gioco, riavvio a
freddo, lettura indipendente dei contenuti. Le fixture già individuate sono
limitate, non copertura universale. La prima ricognizione non comprendeva prove SAVE/cold, build o sessioni Android;
il seguito codice/composizione è documentato separatamente, gli originali sono preservati.

La ricerca ha prodotto piccole relazioni e riproduttori privati, esclusi dal
pubblico, con hash dei dati letti. Non sono distribuiti script estratti, ROM o
salvataggi. Ogni futuro stato «risolto» deve indicare la candidata esatta,
prove eseguite e limiti, senza riscrivere i vecchi rapporti come se riguardassero
nuovi byte.

## HG-B16: forme alternative degli Allenatori

Il primo ciclo dedicato ha autenticato dieci immagini Plus EN/IT fra 1.04,
1.1, 1.2.5, V4 e 1.3.1. Horton #396 contiene davvero cinque Rotom forma 1–5
al livello 57. Il costruttore HGSS crea prima Rotom base e calcola le statistiche,
poi scrive soltanto `MON_DATA_FORM`; l'oracolo indipendente applica la formula
di `CalcMonStats` alla tabella personal della forma risolta.

Tutti i 50 slot raggiungibili divergono, mentre dieci controlli forma 0 restano
identici. Heat/Wash/Frost/Mow risultano `124/62/101/108/124/92` invece di
`124/79/138/92/124/126`; Fan dovrebbe risultare
`124/79/119/123/124/109`. Due corse complete hanno prodotto lo stesso file,
SHA-256 `bc1e98e1bcf5084e42fda53f21b80cd9c7bf60448b7e273f71cc53bba1a8058e`;
digest canonico del risultato `480e44ecbe03f04035ebc34da23e7edc4d4e84654e2bee777a6fe1c8ab6cf6e7`.

Il costruttore ARM9 reale è stato poi eseguito due volte dentro melonDS, con
heap, lettori NARC, cifratura Pokémon e codice Party reali. Entrambe le corse
restituiscono forme 1–5, checksum validi e le statistiche vulnerabili identiche;
digest del componente `6c103588bb48e3e82e40e7a0ab789668c964ff642e5ea1917047676d59c39248`.
Le due allocazioni vengono liberate, il runtime esce zero e originali/copie
restano invariati.

La correzione TDD è ora nello stadio `trainer-fixes`: l'helper condiviso ARM9
mantiene la stessa estensione di 50 byte, chiama `UpdateMonAbility`,
`CalcMonStats` e poi esegue il controllo Frustrazione/amicizia preesistente. I
quattro formati trainer
convergono sullo stesso helper; NARC, overlay, layout save e identificatori non
cambiano. Dopo il fix, melonDS passa T0 naturale due volte, T1/T2 sintetici,
T3 naturale e forma 0 negativa con statistiche attese, checksum validi e heap
liberato. Restano battaglia naturale/ordine turni, runtime EN, SAVE/cold e
dispositivo. Il componente è debugger-assistito su una candidata IT.

Il ciclo separato **SG-TR04** ha poi confermato che `CalcMonStats` da solo non
aggiornava l'abilità: Horton Rotom Fan conservava Levitate 26 invece di Motor
Drive 78; Wormadam Sandy/Trash con slot abilità 1 conservavano 102 invece di
8/5. Il banco ARM ha osservato sei failure EN/IT prima del fix. Lo stesso helper
da 50 byte richiama ora `UpdateMonAbility` prima delle statistiche: Horton,
entrambi gli slot e le tre forme Wormadam, forma 0, PID, checksum,
Frustrazione/amicizia e statistiche passano. La suite trainer è 11/11, le 94
prove mechanics/build e le catene complete EN/IT sono verdi. Restano battaglia
naturale, SAVE/cold e dispositivo; non è una modifica deliberata dei roster o
del bilanciamento.
