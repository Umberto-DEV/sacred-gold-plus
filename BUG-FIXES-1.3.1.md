# Bug ereditati e correzioni della candidata 1.3.1

## Freeze battaglia: salto nel raccordo Folletto — 6 novembre 2026

Le candidate correnti sono EN
`50ba570f97655cecc7b11bed06eb7f683283b191c1c21f02e49ad55f90fc7665`
e IT `c63cf9e993cbee9c38949baf9444dda3e365bddb15840aaa08905d9b02afbedb`;
le due build formali coincidono byte per byte con le trial misurate.
Il ramo di ritorno del ciclo tipi entrava nel suffisso di un BL introdotto da
`fairy_ai`: il primo trace d'errore mostra il salto nei dati e il data abort
ARM9 che ferma immagine e audio. Cambia un solo byte del ramo, con payload e
layout save invariati. Venti casi del ciclo nativo EN/IT falliscono prima e
passano dopo; un core interprete senza JIT riproduce la catena e la
controprova sul solo byte ripristina la risposta del menu.
[Diagnosi e limiti](source/docs/ai-scoring-1.3.1.md).
Il test fisico sulla candidata IT esatta è in corso. Il freeze storico Latios
su versioni precedenti non è attribuito automaticamente a questo difetto.

## Checkpoint storico HG-T10 — 5 novembre 2026


**Stato: candidata formale aggiornata, release non pubblicata.** Questo elenco è il
riferimento breve per GitHub e per un futuro post alla community. Un fix
indicato come «integrato» è presente nelle candidate formali EN
`02cccfbf…f0af` e IT `35d459e3…8f4` identificate nel
[rapporto della candidata](source/docs/bug-audit-1.3.1.md); non implica che
ogni scena sia stata giocata su hardware o che la release sia approvata.
La ROM fisicamente installata resta la precedente IT `171b53b6…d64a0` finché
il dispositivo non viene ricollegato e supera l'aggiornamento conservativo.
Il gate globale del checkpoint precedente termina con exit 0: 2.980 test
raccolti, Class A
2.042/2.095 (53 skip), Class B 577/885 (308 skip), zero failure. Il Box passa
59/59 test ARM del feature bench, 26/26 del package, 26/26 sulla ROM e 2/2 di
binding della precedente candidata Android IT esatta. Gli skip restano limiti
dichiarati;
il dispositivo fisico non era collegato e nessun salvataggio personale è stato
toccato.

Il successore HG-T10 è EN
`02cccfbfc49b6addddba90385634ffdfde22b9ff3fbae3d85ae8f5603c5bf0af`
e IT `35d459e3fcf7cf127d6ff0aec94a5f502accfce390b2455b83fe189a5ca088f4`.
Il mismatch cinematografico dipendente dal titolo è corretto al componente e
integrato: runtime sintetico EN/IT e controllo Ho-Oh passano. Il freeze
completo, la battaglia e la cattura non sono riprodotti; lo stato storico
resta irraggiungibile nella progressione ordinaria Plus. Questi hash non
ereditano nuove prove sul dispositivo fisico o SAVE/cold dal checkpoint precedente.

Le segnalazioni provengono da tre linee diverse: HeartGold/SoulSilver originali,
[Sacred Gold/Storm Silver 1.05 di Drayano](https://gbatemp.net/threads/pokemon-sacred-gold-storm-silver.327567/)
e [Sacred Gold Plus 1.03](https://www.reddit.com/r/PokemonROMhacks/comments/1m69jrj/sacred_gold_plus_fairy_type_full_implementation/).
Una segnalazione in un forum non prova, da sola, che il difetto esista in ogni
versione o sulla nostra candidata. I [cataloghi completi della hack](source/docs/legacy-bugs-1.3.md)
e [del gioco retail](source/docs/known-bugs-hgss.md) distinguono fonte,
versione, prova e limiti.

## Guardia della Lega dopo la lista GS Cup — correzione nei sorgenti

**HG-F08 è integrato nelle candidate formali correnti.** Il viewer “Check
Special Pokémon” e la guardia di Pino condividevano per errore
`VAR_TEMP_x4005`: il primo lasciava 1 dopo qualunque specie elencata, il secondo
interpretava `>=1` come “guardia già spostata” e chiudeva il dialogo senza
movimento. Il producer same-size cambia nove byte nel solo membro 4: il teardown
comune della lista passa in un blocco prima irraggiungibile che azzera `x4005`
e ritorna al menu originale. Membro 819, altre regole, entry, movimenti,
geometria NARC e layout save restano identici. Il banco pubblico EN/IT usa il
video storico come oracolo indipendente, riproduce la preimmagine e prova nove
positivi, omissione, lista vuota, cambio mappa, mutanti e replay del producer.
La navigazione naturale sulla fixture IT resta `TOOL_LIMIT`; mancano UI
renderizzata, SAVE/cold e dispositivo.

## Erba invisibile Percorsi 43/44 — correzione nei sorgenti

**HG-F09 è integrato nelle candidate formali correnti.** Il test pubblico
autentica quelle candidate come preimmagine e localizza i landmark recuperati
in matrix 0, land 87 (Percorso 43) e land 102 (Percorso 44). Sei caselle con
solo materiale grafico di bordo `egrass_u` avevano permission `0x0002`, quindi
la semantica di erba alta pur senza erba pienamente visibile. Erba visibile,
terreno ordinario e acqua sono controlli separati. Il producer registrato
cambia esclusivamente i sei word in `0x0400`, senza ricostruire il NARC e senza
toccare modelli, collisioni, matrix, geometria ROM o layout save. EN/IT,
confinamento byte, mutanti e composizione/replay mirata passano. Mancano prova
renderizzata, incontri/effetto follower, SAVE/cold e dispositivo. Percorso 28
e Safari non sono stati modificati: le fonti non permettono ancora coordinate
normalizzate univoche.

## Orientamento in discesa da Cascata — correzione nei sorgenti

**HG-F02 è integrato nelle candidate formali correnti.** Gli esatti byte
EN/IT riproducono il difetto retail: Sinistra/Destra bloccata seguita da Giù
avvia il task verso Sud ma conserva il facing laterale anche con 0/1/2 frame
neutri; Giù solo è il controllo sano e resta Sud. Il nuovo stage sostituisce
soltanto il BL del ramo riuscito di `ov01_021F24F4` con un wrapper Thumb da 20
byte che chiama il setter Sud prima del task originale. Stack allineato a 8
byte in entrambi i call, registri callee-saved, fallimenti e salita da
script/menu sono preservati. EN/IT, ordine, ABI, mutanti, confinamento e replay
passano. La navigazione naturale con Surf resta `TOOL_LIMIT`; mancano scena
renderizzata, SAVE/cold e dispositivo.

## Accompagnatore sollevato dai menu durante il salto — correzione nei sorgenti

**HG-F13 è integrato nelle candidate formali correnti.** Il precedente trial
bounded apriva X dopo un solo input Giù e osservava `cmd=9`, quindi non
esercitava il trigger storico. Con il secondo Giù il follower entra nel vero
`cmd=21/step=1`: sulle candidate EN/IT ogni ritorno da Squadra riapplicava
`+0x8000` a `facingVector.y`, producendo la sequenza
`0x6000, 0xE000, 0x16000, 0x1E000` a Y mappa invariata. Il nuovo stage, ordinato
dopo `waterfall-facing`, modifica soltanto l'helper altezza di overlay 1: se il
movimento è in pausa restituisce delta zero e conserva la posa già applicata;
fuori pausa mantiene guardia follower, fase, frame e tabella originali. I 28
byte logici restano nel helper da 92 byte e la ricompressione resta nello slot
esatto. RED EN/IT, GREEN 0/1/2/3 ritorni, reset, controllo da fermo, semantica
Thumb/ABI, mutanti, replay condiviso con HG-F02 e copie save invariate passano.
Restano save naturale, altri sottomenu/ambienti, SAVE/cold e dispositivo.

## Pokégear pan/zoom — correzione nei sorgenti

Il culler ereditato dell'overlay 101 controllava soltanto Y; X molto negative
dei Percorsi 40/41 potevano quindi riapparire dopo il wrap OAM. Il successore
conserva i tre caller e usa un trampoline in-place verso il thunk ARM9
registrato `sgp.pokegear_autocull`. Lo stream canonico misura 53.564 byte ed è
riempito fino allo slot invariato di 53.576: FAT, y9, geometria ROM e save non
cambiano. Candidate EN/IT, confini X signed `-7..263`, Y `0..199`,
`autoCull=0`, ABI, riserva e composizione completa passano. Restano UI
pan→zoom→pan, SAVE/cold e dispositivo.

## Regole custom e Cuorugiada — correzione nei sorgenti

Il getter HGSS della regola 13 restituiva l'intero limite totale: con flag
Cuorugiada e limite 50 il valore `0x8032` non coincideva con il confronto
esatto `0x8000` usato dai sei consumer. Il successore maschera soltanto il bit
15 per rule 13; regole 0–12, ID invalidi, GS Cup e limite senza flag restano
identici. Il banco ARM reale EN/IT, il canarino, la riserva registrata e la
composizione legacy completa passano. Restano menu/link naturale, SAVE/cold e
dispositivo.

## Wonder Card e ID decorazioni — correzione nei sorgenti

**HG-SEC01** è riprodotto e corretto al componente sulle candidate EN/IT. Il
percorso reale tag 6 accettava il sigillo 81 e scriveva il primo byte oltre
l'inventario; `0xFFFF` raggiungeva `SealCase+65822`. Il successore ammette solo
sigilli `1..80`, fashion `0..99` e background `0..17` nel check/give e rende
fail-closed i writer interessati anche se chiamati direttamente. Input invalidi
non mutano più la decorazione. Banco ARM reale EN/IT, owner residente
`sgp.wonder_card`, canarino, confinamento e composizione legacy passano.
L'invocazione artificiale del give conserva per compatibilità la coda retail e
può marcare il dono ricevuto pur rifiutando l'ID: non resta però alcuna mutazione
dell'inventario o scrittura OOB. Le prove non consegnano una card, non usano un
save e non provano ACE; restano delivery naturale, SAVE/cold e dispositivo.

## Persistenza delle impostazioni Plus — correzione nei sorgenti

Il blob di salvataggio Plus ignora l'esito delle due scritture dei mirror. Un
riproduttore sul codice macchina spedito mostra che, se il salvataggio nativo
riesce ma entrambe le scritture aggiuntive falliscono, il runtime dichiara
ugualmente valido il record; al riavvio difficoltà Plus e livelli selvatici
tornano invece ai default. Il controllo sano conserva entrambi i mirror e il
fallimento del salvataggio nativo impedisce correttamente qualsiasi scrittura
Plus. Il successore 1.3.1 conta gli esiti reali: zero copie non diventano più
`VALID`, una copia riuscita è recuperabile a freddo ma viene segnalata come
ridondanza parziale; il caricatore confronta le generazioni e sceglie il mirror
valido più recente, invece di fermarsi a una copia A valida ma vecchia. Due
copie sono successo pieno. Il risultato vanilla resta
invariato perché l'app touch scarta un errore inventato dall'estensione e
lascerebbe inoltre sporco il proprio manager. Il blob storico 1.2.x resta
immutato; il nuovo payload confinato passa 18 test QSalva, controlli EN/IT e
composizione in memoria con gli altri fix legacy. Il banco raw-save successivo usa
copie temporanee EN/IT con impostazioni Plus e Borsa estesa: 0/2, sola A, sola
B e 2/2 (otto casi) passano il cold loader dell'esatto payload installato;
originali e ogni byte fuori dai due record da 32 byte restano identici. Non è
più soltanto un modello: la candidata IT installata completa SAVE dalla UI e
cold restart su una copia, con entrambi i mirror `SGP2` validi. Un fault
injection locale sul vero `WriteBackup`, senza patch ROM/emulatore, forza poi
0/2 e 1/2: il runtime registra rispettivamente fallimento e ridondanza parziale,
exporta la SRAM, termina e ricarica a freddo le stesse impostazioni; due run
sono identici. Resta distinto il guasto reale del supporto fisico, non una
causa ROM ancora aperta.

Un secondo difetto della funzione Borsa ampliata è riprodotto e corretto nei
sorgenti 1.3.1: se l'allocazione della copia privata falliva, `sgp_cap_new`
passava `NULL` alla pulizia e il codice macchina tentava una scrittura
all'indirizzo zero. Il successore sostituisce soltanto il corpo esistente da
28 byte, senza spostare ingressi o consumare altra RAM/ROM: il fallimento torna
`NULL`, mentre il controllo positivo azzera ancora tutti i 2.380 byte. Codice
Thumb reale e composizione EN/IT passano. Non è ancora misurata la frequenza
del ramo sotto pressione heap in partita; candidata conservata, SAVE/cold e
dispositivo restano aperti. È registrato come **SG-BAG-ALLOC-01**.

Il ritorno dal Box portatile aveva una seconda finestra di allocazione non
coperta dalla sonda preventiva: il wrapper retail della squadra scriveva nei
PartyArgs immediatamente dopo `PartyMenu_CreateArgs`, anche se il costruttore
restituiva `NULL`. **SG-BOX-NULL** è riprodotto sul codice ARM EN/IT. Il
successore evita quel wrapper insicuro, chiama il costruttore pin-nato, controlla
il risultato e soltanto dopo inizializza e lancia la squadra tramite il wrapper
Plus. Su fallimento torna al campo senza dereferenziare zero. Il payload resta
nel compartimento (2.952/3.024 byte); runtime 20/20, unità 26/26, ROM EN/IT
25/25 e composizione dopo la UI reale passano. La candidata IT installata
`171b53b6…d64a0` include il successore. La nuova composizione portable-only del
5 novembre produce EN `5c561184…2f15` e IT `c5a45d16…77f97`, con il solo Box
attivo: entrambe aprono il PC nativo nel banco headless e l'esatta IT completa
su melonDS Android nel Mac R→Box→ritorno, poi in un ciclo separato
SAVE→riavvio→Continue su copia. Il dispositivo fisico non era collegato né è
stato aggiornato. Restano la pressione heap fisica che provochi questa seconda
allocazione, la matrice estesa delle operazioni e l'accettazione completa sul
dispositivo.

La vista compatta Berries della Borsa ereditava **HG-BAG-VIEW-01**: il setter
retail ignorava la posizione passata dal costruttore e usava l'ID tasca come
indice. La sequenza naturale `(Berries=4, posizione=0)` scriveva quindi l'entry
4; Items `(0,0)` e la vista completa erano controlli sani che lo nascondevano.
Il fix ARM9 usa la posizione per lo stride e conserva l'ID come identità,
ricodificando la funzione adiacente e il suo unico callsite in 36 byte
dichiarati. EN/IT, 12 sequenze, readback e mutanti passano; picker giocato,
SAVE/cold e dispositivo restano aperti.

Il Numero Loto ereditava **HG-LOTTO-ID-01**: il setter scriveva prima la metà
bassa in 0x403C e poi sovrascriveva la stessa variabile con la metà alta,
lasciando 0x403D al valore precedente. Il percorso giornaliero compone
correttamente due roll RNG ma chiama quel setter. Il fix cambia soltanto
l'immediato del secondo `ldr`, usando il literal 0x403D già presente nel getter
adiacente: un halfword confinato e un solo byte fisicamente diverso, senza
riserva, geometria ROM o modifica del layout save. Sei ID, tre coppie RNG e tre
controlli negativi passano EN/IT; cambio giorno giocato, premio, SAVE/cold e
dispositivo restano aperti.

## IA e tipo Folletto — correzione nei sorgenti

**SG-BAG-FOREIGN** non lascia più avanzare silenziosamente il save nativo quando
la banca inattiva contiene byte estranei e la Borsa ha slot extra vivi. Il
coordinatore restituisce il fallimento recuperabile prima del commit; con
estensione vuota o sole celle native il save continua senza sovrascrivere dati
estranei. Blob/ABI Borsa e layout save restano invariati. BuilderChain EN/IT e
i banchi ARM passano; restano SAVE/cold raw e dispositivo.

La prima integrazione sorgente di questa guardia aveva introdotto
**SG-PIPE-BAG-ABI-01**: ricompilando l'intero comparto Training spostava 12 dei
16 ingressi consumati da hook ARM9/overlay e dai descriptor Shiny/UI. Il test
rosso faceva risultare indisponibile la UI Shiny e il decoder dei consumer
misurava i 12 mismatch. Il successore conserva invece byte e indirizzi del
payload storico, sostituisce solo gli 8 byte iniziali di `training_save` e
aggiunge una guardia Thumb da 180 byte nel margine, lasciandone 176 liberi. I 16
consumer, la transazione Shiny, i banchi del save e la composizione completa
EN/IT passano. È un difetto della pipeline di sviluppo, non di una release
pubblicata.

**HG-T12** corregge la palette della schiusa di un uovo scambiato senza
anticipare la mutazione del memo: il solo bit shiny usa OT finale e PID con la
regola Plus. Suite ROM, replay FAT/y9/CRC e BuilderChain EN/IT passano; restano
link trade reale, animazione renderizzata, SAVE/cold e dispositivo.

**SG-AI01** faceva ancora valutare all'IA allenatori la tabella retail priva del
tipo Folletto, benché il danno usasse già la matrice moderna. Un helper Thumb
residente da 148 byte gestisce ora soltanto le interazioni Folletto e delega
tutte le altre coppie al consumer nativo, conservando Scrappy, Gravità,
Ferropalla e le immunità già corrette. Lo stesso writer compone ora anche quattro
riparazioni condivise. **SG-AI02** sostituisce nell'esatto span di 64 byte il
helper di Conversione2, passando dalle 112 righe retail alle 325 righe
selezionabili moderne: il banco ARM EN/IT osserva prima il fallimento con tipo
Folletto e poi una resistenza valida senza letture retail. **SG-DM01** ritargetta
i due literal usati da Ferropalla/Gravità verso le colonne della stessa riga
moderna; Ground→Flying passa dall'immunità errata al moltiplicatore 100, mentre
Ground→Veleno e Fairy→Drago restano invariati. **HG-B01** sostituisce nel gate
a due turni l'effetto 273 di Fire Fang con il 272 di Shadow Force: Fire Fang
neutra e resistita raggiungono Wonder Guard, mentre Shadow Force salta il
controllo durante la carica e lo esegue all'impatto; superefficacia, Fly/Bide e
le altre Fang restano invariati. **HG-B02** sostituisce il mask positivo di
Rage con il bit-clear canonico: abbandonare Rage rimuove solo Rage e non
cancella Transform o gli altri stati volatili. **HG-B03** resta un ID storico
separato ma è la manifestazione downstream della stessa causa, non un secondo
fix: il consumer PartyMon salta correttamente mosse/PP quando il bit Transform
sopravvive. **HG-B08** sostituisce nell'esatto span di 340 byte la ricarica
del BattleMon: durante Transform conserva soltanto Attacco, Difesa, Velocità,
Attacco Speciale e Difesa Speciale copiati, continuando ad aggiornare livello,
amicizia, HP e HP massimi. Non-Transform mantiene anche la ricarica di
mosse/PP/esperienza e il filtro Mimic. La composizione dei sei fix
aumenta il flusso compresso di 28 byte: FAT, parola dimensione y9 e il solo CRC
y9 derivato sono aggiornati e riletti; il replay inverso ricostruisce la UI
fredda. Oltre 76.000 casi dinamici, i 512 ingressi HG-B01, 464 esecuzioni ARM
HG-B02, 16 esecuzioni del consumer HG-B03 e 256 esecuzioni native rosso/verde
HG-B08 passano. L'applicazione V4 reale EN/IT e 36 test mirati EN/IT di replay,
peel e mutanti sono verdi.
Per HG-B02/B03/B08 restano battaglia naturale, PartyMon cifrato reale,
level-up con/senza apprendimento mossa, SAVE/cold e dispositivo; per la
famiglia AI restano inoltre i casi communication.

**HG-B09 Torre Lotta** restringeva a otto bit il numero di round completati
prima della scelta degli avversari. Il save conservava correttamente il valore
a 16 bit, ma 256 round (1792 vittorie) diventavano bracket zero; 258/262
potevano riproporre Palmer e 512 ripeteva il wrap. Lo stadio
`battle-tower-wrap` rimuove entrambi i narrowing, incluso il ramo condiviso da
Multi/Link, senza cambiare save, tabelle o routine RNG; il pool corretto può
consumare un numero diverso di estrazioni. Dieci Plus EN/IT, 18 scenari
ciascuna e 360 esecuzioni native danno 110 divergenze prima e zero dopo; il
risultato è deterministico `c0ec4f35…bb94f`. Applicazione diretta dopo
`lottery-id`, ricevute, mutanti e confinamento passano sulle V4 reali EN/IT.
Restano serie naturale Plus oltre la soglia, schermata/BP, peer link,
SAVE/cold e dispositivo; non è stata conservata una nuova ROM.

**HG-F17 Facade** avviava sei task scale/restore da 10 frame a soli 8 frame di
distanza. Il dispatcher e la macchina a stati reali dell'overlay 7 confermano
che i campi `5/5` sono andata e ritorno; cinque coppie di task si
sovrapponevano. Lo stadio `battle-animation-facade` conserva i sei task e
sincronizza i cinque `Delay` e l'intervallo del suono da 8 a 10: sei byte nel
solo membro 263 di `a/0/1/0`, senza ricostruire il NARC. Le V4 EN/IT passano
con cinque overlap prima e zero dopo; workaround 4+4, delay senza audio e audio
senza delay sono controlli negativi. Anche composizione e replay integrali
EN/IT passano. Restano animazione renderizzata, 1/2/16 usi, entrambi i lati,
animazioni disattivate, SAVE/cold e dispositivo; nessuna ROM/save è conservata.

**HG-F20-DP DynamicPunch** avviava la seconda scossa sul settimo tick della
prima, quando il bersaglio era temporaneamente a X=-1; la seconda scossa
registrava quella coordinata come nuova base. Il valore qualificato `Delay
3→4` la avvia invece all'ottavo tick su X=0. Lo stadio cambia un solo byte nel
membro 223 di `a/0/1/0`, dopo Facade, e preserva i suoi sei byte. Le routine
Thumb reali confermano shake e semantica N+1 dei Delay; EN/IT, confinamento e
replay passano. Questo fix non chiude da solo le cause distinte `HG-F20-HH`
Helping Hand e `HG-F20-SU` Spit Up, entrambe corrette separatamente qui sotto.
Restano rendering completo,
1/2/16 usi, lati/doppie, animazioni off, SAVE/cold e dispositivo; nessuna
ROM/save è conservata.

**HG-F20-HH Helping Hand** lasciava il `Delay 1` fuori dal loop di due
iterazioni. Il secondo shake partiva al tick 7 e catturava X=-1 come nuova
base; il terzo ereditava lo stesso errore. Il Delay esistente è ora dentro il
loop: gli avvii diventano 0/9/18 e tutte le basi restano zero. Il fix riordina
tre parole senza cambiare lunghezza e modifica soltanto tre byte del membro 270
di `a/0/1/0`, dopo Facade e DynamicPunch. Gli handler loop, Delay e shake reali
dell'overlay 7, le candidate EN/IT, il replay confinato e la composizione
completa passano. Rendering, SAVE/cold e dispositivo restano da provare.

**HG-F18 Strength** eseguiva dieci aggiornamenti di uno shake a fase di quattro
tick e terminava con X+2; la cleanup reale ripristinava scala e Y, ma non X. Lo
stadio `battle-animation-strength`, dopo Helping Hand, cambia soltanto il
contatore `10→8` nel membro 70 di `a/0/1/0`. Le prove native 8/9/10/11
distinguono le fasi con somme 0/+2/+2/0; EN/IT, confinamento e replay passano
in 119 test mirati; anche la composizione/replay completa EN/IT passa. Restano
rendering, ripetizioni, lati/doppie, animazioni off, SAVE/cold e dispositivo.

**HG-F20-SU Spit Up** terminava il task con X+2 e ripristinava soltanto Y e
scala. La cleanup dell'overlay 7 ora sottrae esattamente il residuo; il producer
ricomprime BLZ nello stesso slot e il verifier controlla pre/postimage logica e
fisica. Il task reale EN/IT conserva X iniziale 0/1/100/253; i mutanti che
sottraggono 1 o 3 terminano rispettivamente X+1 e X-1. La composizione/replay
completa EN/IT passa. Restano rendering, ripetizioni, lati/doppie, SAVE/cold e
dispositivo.

**HG-F16 Giratina/PC** aggiornava forma e abilità tramite il sotto-record
`BoxMon` anche quando Giratina era ancora in squadra, lasciando le statistiche
della forma precedente. Un hook confinato nell'overlay 14 richiama all'uscita
dal PC la routine retail non-forzante per tutti i Giratina della squadra. EN/IT,
entrambe le direzioni, squadra mista, chiusura senza modifiche e cleanup passano;
restano UI naturale, raw SAVE/Continue/cold e dispositivo.

**HG-B04 Pursuit/Acid Rain** era ancora presente in tutte le 30 immagini Plus
EN/IT locali esaminate. Nel subscript di Pursuit il comando successivo al loop
EXP sottraeva l'ID del battler svenuto dalla maschera globale delle condizioni
di campo e non ripristinava `battlerIdFainted`. Il producer `pursuit-script`
applica la correzione primaria `SUB_TO_ZERO FIELD_CONDITION` →
`SET BATTLER_FAINTED` nel membro `a/0/0/1:153`: cambiano due soli byte, senza
variazioni di dimensione, name block o altri membri. Il banco nativo ha
eseguito originale e postimage su otto Plus EN/IT, 20 scenari per immagine e
320 esecuzioni; due run sono byte-identici. Writer, checker, mutanti fail-closed
e composizione/replay reale EN/IT passano. La chiusura è al livello
componente/sorgenti: restano battaglia renderizzata, Castform/Cherrim, link
host/client, SAVE/cold e
dispositivo, e non è stata prodotta una nuova candidata ROM.

**HG-B05 U-turn/tentennamento da oggetto** usava l'oggetto del Pokémon
subentrato nello slot prima del controllo tardivo King's Rock/Razor Fang. Ne
derivavano sia la perdita del tentennamento dovuto all'uscente sia un
tentennamento spurio dovuto al subentrante. Il producer
`uturn-item-snapshot` salva nello script pivot `a/0/0/1:175` effetto effettivo
e modificatore dell'uscente; due wrapper Thumb nel margine condiviso
`c8.module-stubs` consumano lo snapshot nei due soli getter di
`TryItemFlinch`, poi lo cancellano. Il percorso senza snapshot continua a
usare i getter retail e tutti gli altri gate rimangono byte-identici. Otto
immagini Plus EN/IT, 160 esecuzioni native, controlli RNG/mossa/danno/KO,
mutanti ostili e composizione/replay completa EN/IT passano. Non è stata
conservata una ROM candidata. Restano battaglia naturale, doppio/link tra build
uguali, SAVE/cold e dispositivo; una sessione link con build miste non è
supportata perché il numero di chiamate RNG può differire.

**HG-B06 icona status invisibile** faceva cancellare alla barra HP l'icona di
uno status persistente quando Mente Locale curava la confusione o Indifferenza
curava l'attrazione. Lo status reale restava attivo: il membro
`a/0/0/1:221` inviava `SetHealthbarStatus(NONE)` prima di distinguere la cura
volatile. Il producer `status-icon-script` anticipa i due dispatch e conserva
messaggio e attesa duplicando `WaitButtonABTime 30` nei due rami; le cure
persistenti 0–4 rimangono identiche. Otto immagini Plus EN/IT, 320 esecuzioni
script, 200 esecuzioni native del consumer, controlli sui sei status e mutanti
passano. Anche la composizione/replay completa EN/IT con Pursuit e U-turn è
verde. Nessuna ROM o save è stata conservata. Restano battaglia renderizzata,
switch-out/in, doppio/link, SAVE/cold e dispositivo.

**HG-B07 Pressure/cambio immediato** lasciava il secondo PP detratto soltanto
nel BattleMon: Counter, Mirror Coat, Magic Coat e Snatch usavano un helper
tardivo privo della copia al PartyMon, dal quale il cambio manuale ricaricava il
valore precedente. Metal Burst è stato verificato separatamente sul vero
chiamante successo/fallimento, senza attribuirlo alla fonte storica. I producer
`pressure-switch-effects` e `pressure-switch-subscripts` inseriscono su cinque
soli percorsi riusciti un aggiornamento status a delta zero; lo status resta
identico e il consumer retail effettua la sincronizzazione mancante. Otto
immagini EN/IT, 160 esecuzioni helper, 320 ricaricamenti, 24 sync e 16 chiamate
Metal Burst passano in due run deterministici; composizione e replay reali
EN/IT sono verdi. Nessuna ROM o save è stata
conservata. Restano battaglia naturale, doppio/link, receiver asincrono
completo, SAVE/cold e dispositivo.

## Replay del modulo rivincite — correzione del builder

La composizione completa si fermava dopo i fix legacy perché lo stadio
rivincite ricostruiva il proprio modulo dall'immagine già modificata e
pretendeva ancora la preimmagine V4 di `a/0/5/6`. Il modulo era invece già stato
derivato e autenticato dalla V4 prima della UI. Writer, reader, peel e
attivazione condividono ora quella delta immutabile; soltanto il byte di
attivazione dichiarato può differire. Catena inerte EN/IT e replay completo
fino a `rematches` passano. **SG-PIPE-REMATCH-01** è un difetto della pipeline
di build, tenuto separato dai bug interni alla ROM.

## Evoluzioni di Mantyke, Feebas, Burmy e Combee — correzione nei sorgenti

Quattro parametri ereditati erano errati: Mantyke cercava Voltorb invece di
Remoraid, Feebas usava Bellezza zero, Burmy femmina livello zero e Combee
femmina livello zero. Il producer condiviso modifica soltanto i quattro
halfword parametro nell'archivio evoluzioni e li verifica con pre/post-hash,
rilettura semantica e replay. La Guida in-game viene compilata dagli stessi
record già corretti, quindi non descrive più le soglie precedenti. Le
composizioni reali EN/IT in memoria passano; restano evoluzioni giocate ai
confini, SAVE/cold restart e dispositivo.

## Lotto di Ball di Franz con Borsa piena — correzione nei sorgenti

Lo script ereditato controllava lo spazio ma ignorava il risultato, tentava la
consegna e cancellava comunque il lotto completato. Il nuovo guard usa il
messaggio Borsa piena già presente e raggiunge `ClearKurtApricorn` soltanto
dopo il percorso di consegna. Nei byte reali EN/IT, 950+50 lascia il lotto
disponibile e 949+50 consegna 50 Ball fino a 999; mutanti, relocation e
allineamento dei movimenti sono verificati. Restano dialogo giocato, SAVE/cold
restart e dispositivo.

## TM07 di Alfredo con tasca TM satura — correzione nei sorgenti

Con 99 copie la Borsa Plus accettava la richiesta, inseriva zero TM e mostrava
lo scarto; lo standard 2033 azzerava poi la propria spia transitoria, mentre lo
script poneva comunque il flag del premio. Poiché la Medaglia Ghiacciaio era
già stata data, ogni dialogo successivo saltava definitivamente la consegna.
La correzione **HG-F23** legge la quantità reale prima del dono: a 99 usa il
percorso Borsa piena e lascia il premio pendente; dopo aver liberato uno slot,
il colloquio successivo consegna 98→99, pone il flag e impedisce duplicati.
Entrambi i blocchi del membro 932 passano EN/IT, relocation, edge, mutanti e
byte complementari. Restano dialogo giocato, SAVE/cold e dispositivo. I vecchi
save col flag già posto non sono distinguibili da una consegna riuscita e non
vengono modificati automaticamente.

## Rematch di Wade — correzione nei sorgenti

Il selettore telefonico usa i record `461`, `460`, `512`, ma i dati ereditati
assegnavano loro livelli 52, 46 e 68. La progressione non era quindi soltanto
una voce errata in una guida: è stata riprodotta nei byte delle candidate EN/IT.
Il nuovo stadio confinato scambia esclusivamente i due record di uguale misura
460/461 e ottiene 46→52→68, senza cambiare specie, mosse, script selettore,
geometria dell'archivio o altri allenatori. Sei test mirati e la rilettura
indipendente delle due ROM in memoria passano. La correzione è nei sorgenti ma
non ancora in una ROM candidata conservata; mancano rematch giocati, SAVE/cold
restart e dispositivo. Il caso separato Jose è confermato staticamente: il
primo rematch regredisce dal duo 48 al solo Farfetch'd 44; il roster resta
retail ma le quattro mosse sono già custom Plus. Reena e Gaven non regrediscono.
Un duo livello 50 è coerente con gli allenatori adiacenti, ma non determina
difficulty o mosse: non viene corretto inventando una squadra senza una fonte
di design autorevole o una decisione esplicita di bilanciamento.

## Statistiche e abilità delle forme degli Allenatori — correzione nei sorgenti

Il costruttore nativo creava il Pokémon con i dati della forma base e scriveva
la forma soltanto dopo il primo calcolo delle statistiche. La correzione HG-B16
mantiene lo stesso helper ARM9 di 50 byte ma chiama `UpdateMonAbility` e
`CalcMonStats` prima del controllo amicizia già esistente; tutti i quattro
formati squadra passano da quel punto. Le prove melonDS dopo il fix coprono T0 e T3 naturali, T1/T2
sintetici e forma 0 negativa, con statistiche attese, checksum validi e heap
liberato. Il ciclo SG-TR04 aggiunge Horton Rotom Fan, entrambi gli slot e tutte
le forme Wormadam: Motor Drive 78 e le abilità Sandy/Trash 8/5 sostituiscono le
abilità della forma base senza cambiare PID. Frustrazione conserva amicizia
zero. NARC, overlay, layout save, PID, mosse e strumenti non cambiano. Undici
test trainer, 94 mechanics/build e le catene complete EN/IT passano. Restano
battaglia naturale/ordine turni, SAVE/cold e dispositivo.

## Danno Spettro contro Drago e Buio — correzione nei sorgenti

La chart moderna della Plus conteneva due valori trasposti: una mossa Spettro
era dimezzata contro Drago e neutra contro Buio. Il consumer danno reale legge
quella tabella di overlay 18; la tabella retail separata usata dall'IA non è la
causa di questo caso. Il fix SG-DM02 cambia soltanto i due byte moltiplicatore
`5→10` e `10→5`. Sei immagini EN/IT condividono la preimmagine e il confronto
indipendente di tutte le 324 coppie trova soltanto queste due divergenze. La
correzione è composta nel producer battle/IA e supera rilettura, confinamento,
replay e mutanti; mancano lotta naturale, SAVE/cold e dispositivo.

## IA di Zampillo ed Eruzione — correzione nei sorgenti

Il ramo Expert valutava la potenza usando la percentuale HP del bersaglio,
anziché quella dell'utilizzatore. Il banco esegue il vero interprete Thumb e
lo script autenticato delle candidate EN/IT: prima del fix il punteggio cambia
ai confini 50/51 e 70/71 del bersaglio e ignora gli HP dell'attaccante. La
correzione **AI-WEB-01** cambia soltanto due token battler da bersaglio a
utilizzatore nel membro 0 di `a/0/9/9`; dopo il fix entrambe le soglie seguono
l'attaccante. Restano il percorso Expert completo con negativi Hydro Pump/Surf,
la scelta mossa osservata, SAVE/cold e dispositivo.

## IA di Facade — correzione nei sorgenti

Il ramo Expert controllava veleno, iperavvelenamento, scottatura e paralisi sul
bersaglio invece che sull'utilizzatore di Facade. Il banco esegue il vero
interprete Thumb e la sequenza autenticata delle candidate EN/IT: prima del fix
il bersaglio alterato riceve `+1` e l'attaccante alterato zero. **AI-WEB-03**
cambia soltanto il token battler a `+0x5B68` del membro 0 di `a/0/9/9` da 0 a
1; la matrice dopo il fix segue l'utilizzatore e conserva la maschera `0xD8`,
quindi sonno e congelamento restano esclusi. Le varianti Plus di Valerio
forniscono Swellow con Fiammosfera e Facade e il trainer usa AI flags 7. Restano
dispatch Expert naturale con una mossa di controllo, scelta osservata,
SAVE/cold e dispositivo.

## Dispatch IA di Thunder — correzione nei sorgenti

Il dispatch Expert conteneva due volte l'effetto 151 di SolarBeam e non
inoltrava mai l'effetto 152 alla routine Thunder già integra. Il vero
interprete sulle candidate EN/IT conferma che Thunder non leggeva `+0x58A4`.
**AI-WEB-04** cambia soltanto la seconda parola effetto a `+0x2C00`, 151→152,
quindi un solo byte fisico: dopo il fix pioggia aggiunge `+1`, sole con RNG 50
sottrae 3 e il confine 49/50 resta quello nativo; SolarBeam e Thunderbolt non
entrano nella routine. Sette trainer reali con Thunder hanno il bit Expert.
Restano efficacia resistente/immune nel percorso completo, scelta naturale,
SAVE/cold e dispositivo.

## Ordine IA di Metal Burst — correzione nei sorgenti

La sequenza Basic provava a decidere in anticipo chi agisse per ultimo con due
controlli Stall e due confronti dell'ID strumento 107. Quel valore identifica
Pietrabrillo, non l'effetto di Coda Lenta/Full Incense, e le scorciatoie si
contraddicevano nei casi misti e con doppio Stall. **AI-WEB-02** azzera soltanto
i quattro campi salto a `+0x1DFC`, `+0x1E0C`, `+0x1E20` e `+0x1E30` del membro
0 di `a/0/9/9`: gli opcode continuano a consumare le stesse parole e tutti i
casi arrivano al `CheckSortSpeed` già presente. Il vero interprete overlay 10
e il comparatore overlay 12 passano 30 casi per lingua sulle candidate EN/IT,
inclusi nessun effetto, Pietrabrillo, Stall, Coda Lenta, Full Incense,
parità/RNG, Distortozona, Rapidartigli, Baccacrela e combinazioni. Restano incontro
naturale, scelta osservata e priorità nel contesto battaglia completo,
SAVE/cold e dispositivo.

## Cambio IA sotto Arena Trap — correzione nei sorgenti

Il gate retail dell'IA ripeteva solo una parte delle regole di cambio e
bloccava anche bersagli Volante, con Levitazione o Magnet Rise; Shed Shell non
prevaleva sui rami di trappola. La correzione non aggiunge una terza tabella:
delega alla routine `BattlerCanSwitch` già usata dal motore normale. Sei input
EN/IT e 96 casi CPU passano, con Iron Ball, Gravity, Pedinombra, Magnetismo,
vincoli e nessuna trappola come controlli. Il fix è nei sorgenti; non esiste
ancora una nuova ROM candidata conservata e manca la battaglia giocata.

## Cambio IA verso Pellearsa ed Elettrorapid — correzione nei sorgenti

Il ramo retail riconosceva solo Fuocardore, Assorbacqua e Assorbivolt, sia per
l'abilità già attiva sia per i Pokémon di riserva. Due confronti guardati
usano ora un helper di 20 byte collocato dopo, non dentro, la tabella degli
inizializzatori statici dell'overlay. La matrice nativa su sei input EN/IT
passa 96 casi e conserva vecchi assorbitori, gate RNG, ordine di squadra,
KO/uovo e tipi errati. Il fix è nei sorgenti; non esiste ancora una nuova ROM
candidata conservata e manca la battaglia giocata.

## Sicurezza del banco di sviluppo — 3 novembre 2026

Il downloader opzionale dello stadio 0 poteva seguire un link simbolico
preparato sul nome parziale o sulla ricevuta e scrivere fuori dalla cartella
scelta. Il difetto è stato riprodotto anche inserendo il link nella finestra
fra controllo e apertura. Ora la destinazione deve essere privata, i temporanei
sono esclusivi e no-follow e delta/ricevuta vengono pubblicati atomicamente
rispetto a un descriptor trattenuto. I bersagli esterni restano invariati.
Un secondo difetto consentiva a manifest e delta remoti di consumare memoria,
disco e tempo fino a EOF prima del controllo: ora il manifest è limitato a
64 KiB, ogni delta alla dimensione esatta del pin e l'intera sessione a 30
minuti, con `read1` e controlli prima/dopo ogni operazione. La suite stadio 0
passa 59/59. Sono fix dello strumento, non del gameplay.

Il follow-up Daybreak ha dimostrato e corretto un difetto distinto dal gioco:
il preparatore del core melonDS verificava soltanto l'ID del commit. Un checkout
con lo stesso `HEAD` ma con CMake o sorgenti modificati, file non tracciati, bit
`skip-worktree` oppure un replace ref poteva quindi essere accettato e poi
eseguito dal banco con i privilegi del manutentore.

Il verificatore ora confronta direttamente l'intero albero sul filesystem con
gli oggetti del commit fissato, con replace ref disabilitati, e ammette soltanto
i due file di osservazione nei loro byte esatti. Rifiuta file extra, mancanti,
modificati, ignorati, symlink, hardlink condivisi o modi eseguibili inattesi.
L'indice staged da solo non è un input della build. CMake ripete il controllo
prima di `add_subdirectory` e a ogni build del core. Nove regressioni, due bypass
Git reali, il checkout melonDS autentico e un modulo CMake-sentinella confermano
il risultato; il sentinella non viene eseguito e il core autentico completa una
build pulita. È una correzione del tool di
sviluppo al livello componente/configurazione: non modifica ROM o save, non è
un playtest e non elimina una corsa con un processo dello stesso account che
scriva dopo l'ultimo controllo. Il [rapporto tecnico](source/docs/bug-audit-1.3.1.md)
mantiene identità, duplicati e limiti della scansione.

Il follow-up completo ha ora classificato tutti i 34 candidati statici: 33
sono corretti a livello componente e uno era già risolto. L'ultimo gate ha
verificato che l'AVD privata contiene già l'esatto APK observer successore
corretto e non il precedente APK vulnerabile; non è stata necessaria alcuna
reinstallazione. L'esecuzione end-to-end dell'endpoint Android rimane un limite
di validazione distinto, non un finding statico ancora aperto. Sono
stati chiusi separatamente output/symlink, limiti di risorse, identità e journal
del workbench, peer RSP, snapshot sorgenti, autenticazione delle evidenze e CSV.
Queste correzioni rendono più sicuri build, prove e distribuzione; non vanno
contate come bug interni della ROM né come nuova patch giocabile.

La seconda causa alta chiusa riguarda i reference ZIP della release. Prima il
packager calcolava l'hash, chiudeva il file e riapriva lo stesso pathname: una
sostituzione in quella finestra poteva cambiare licenza, Game Guide e, nella
1.2.5, cheat ereditati non pin-nati. Ora apre senza seguire symlink, richiede un
file regolare, acquisisce una snapshot massima di 256 MiB, verifica l'hash di
quegli esatti byte e passa la stessa snapshot a `ZipFile`. Lo swap riprodotto
non cambia più i membri e tutte le 14 prove di distribuzione passano; anche i
due reference reali da 10,2 e 24,0 MiB vengono ammessi. Non sono state create
nuove release. Path traversal dei nomi e decompressione dei membri restano
famiglie aperte separate.

La terza causa alta chiusa era il checkout RomPatcher.js. Il packager
controllava una sola volta `HEAD` e ignorava i file non tracciati, poi Node
caricava più volte moduli dal working tree mutabile. Un modulo CommonJS senza
estensione prevaleva sul `.js` tracciato; anche `skip-worktree`, un falso
checkout annidato o una sostituzione successiva al controllo potevano portare
byte diversi all'esecuzione. Ora il packager ricostruisce una directory privata
soltanto dagli oggetti del commit fissato, verifica localmente gli SHA-1 di
commit/tree/blob, rifiuta symlink e voci non regolari e passa sempre quella
snapshot a Node. Un quinto riproduttore su clone parziale ha inoltre dimostrato
che il lazy fetch poteva eseguire un helper locale prima della verifica: ora è
disabilitato e gli oggetti mancanti falliscono chiusi. Cinque regressioni e
l'intera suite di 19 test passano; il checkout reale produce 58 file autenticati
e carica i moduli con Node. Non è stato ricostruito alcun pacchetto reale: le
42/50 route richiedono input ROM privati e restano fuori da questa prova di
componente.

## Correzioni presenti nella nuova candidata

Due ulteriori finding del packager sono stati riprodotti e corretti: nomi
pericolosi/collidenti nei ZIP e decompressione senza limite dei membri
selezionati. I controlli includono alias Windows e sostituzione della versione;
le letture ora hanno un tetto di 8 MiB per membro e 32 MiB complessivi, con
STORED/DEFLATED. Passano 26 test e i reference EN/IT reali sotto entrambi i
contratti. Queste prove riguardano gli strumenti di distribuzione.
Il riesame conferma inoltre che la patch RomPatcher risolve già l'esecuzione
di helper dalla configurazione Git. Il controllo fsmonitor-sentinella è ora
una regressione del repository; la suite di distribuzione corrente passa 27/27.

Il quarto finding alto, sull'avvio del compilatore prima dell'autenticazione,
ha una correzione verificata localmente: il binario effettivo viene controllato
prima del probe, i percorsi devono essere protetti da root e l'ambiente del
compilatore è ristretto. Passano 27 test UI e le compilazioni degli otto moduli
1.3. La compatibilità del nuovo pin con il runner Xcode della CI resta da
verificare: il finding non viene ancora contato fra quelli completamente chiusi.

| Origine e ID | Difetto prima della correzione | Cosa cambia nella 1.3.1 | Prova e limite |
| --- | --- | --- | --- |
| Sacred Gold/Plus, **SG-01b** | Perdendo contro l'amministratrice finale sul Percorso 47, il ramo di sconfitta saltava in un percorso senza `WhiteOut` né `ReleaseAll`. | Il salto converge sull'unico `WhiteOut` già usato dai quattro rami perdita partner; SG-01a, vittoria, archivio e save mantengono la propria geometria. | RED/GREEN esatti EN/IT, CFG, mutanti, checker e replay del producer unico passano. Sconfitta giocata, SAVE/cold e dispositivo restano aperti; non prova i blackout generici di menu/audio/turbo. |
| Sacred Gold/Plus, **SG-08** | Perdendo contro Lyra/Ethan a Fiordoropoli, il ramo di sconfitta lasciava visibili gli oggetti che la scena ricreava: possibile duplicazione dei personaggi. | Ripristina il flag di visibilità prima del WhiteOut e conserva la possibilità di ritentare. | Script originale e corretto percorsi in modello; conteggio visivo dei personaggi e vecchi save già colpiti da verificare. |
| Sacred Gold/Plus, **SG-09** | Una Ball nel Tunnel di Fiordoropoli chiedeva **436** Cura Totale, fonte del resoconto «circa 450». | L'operando ora richiede un solo oggetto. Non sottrae oggetti già acquisiti. | Bytecode e binding riletti; quantità effettiva in partita, inclusa Borsa quasi piena, da verificare. |
| Sacred Gold/Plus, **SG-11** | Uno slot di pesca notturna incompleto poteva propagare una specie con ID zero ai consumer di lotta e telefono. | Completa i record interessati e blocca l'ID zero nei due consumer. | Esecuzioni ARM controllate prima/dopo e archivio riletto; incontri con canne, orari, sciami e Safari non ancora giocati integralmente. |
| Sacred Gold/Plus, **SG-15** | Dopo Regigigas, Steven poteva saltare il premio Lati ancora dovuto. | Controlla prima il premio Lati valido, conservando gli stati e la consegna unica. | Matrice dei percorsi script in modello; scena e persistenza da verificare in gioco. |
| Sacred Gold/Plus, **SG-15b** | Con la Borsa piena, il chiamante poteva segnare come consegnata l'Enigmapietra anche dopo il rifiuto del dono. | Controlla lo spazio prima del dono e imposta il flag solo dopo il successo. | Standard script percorsi in modello; prova in partita con Borsa piena e poi liberata ancora necessaria. |
| Sacred Gold/Plus, **V-CHATOT** | Ventiquattro ID variabile `612E..6139`/`619E..61A9` uscivano da SaveVarsFlags e cadevano nei campioni Chatot: gli script alteravano l'audio e una registrazione poteva riaprire o chiudere eventi. | `HF02` fotografa una volta lo stato zero/nonzero dei vecchi gate e reindirizza soltanto questa famiglia a 24 bit persistenti già riservati; audio, layout save e ID degli eventi restano invariati. | 12/12 sequenze di riproduzione; build UI completa EN/IT e istruzioni ARM installate verdi; 8/8 copie zero/HF01 passano SAVE nativo/cold e audit circoscritto integrale. Scene rappresentative e dispositivo restano da eseguire prima della release. |
| HeartGold/SoulSilver, **HG-F15** | Con Ninnananna Pokémon e frequenza base bassa, la sottrazione poteva andare sotto zero e trasformarsi in un valore alto. | La riduzione si ferma a zero. | Funzione ARM originale e corretta eseguita con ingressi controllati; non è una misura di incontri casuali in una partita. |
| HeartGold/SoulSilver, **HG-F05** | Se il messaggio di sopravvivenza al veleno coincideva col salto del follower, il reset immediato cancellava il movimento ma conservava il vettore Y del salto, lasciandolo sospeso. | La sola entry dello standard di sopravvivenza entra dal `LockAll` già esistente, che attende il cleanup nativo del salto; nessun altro uso di `ScrCmd_609` cambia. | Contratto script/ARM9/overlay esatto EN/IT, delta di una word, mutanti e replay passano. Su candidate temporanee, positivi EN/IT tornano a `-0x2000`; fuori cadenza, non avvelenato e HP4 restano negativi. Save copie invariati; restano save naturale, altre sporgenze, SAVE/cold e dispositivo. |
| HeartGold/SoulSilver, **HG-F19** | Parlare lateralmente a Kate prima della sfida mostrava il dialogo post-lotta e `FacePlayer` lasciava l'orientamento errato per il trigger verticale successivo. | L'entry oggetto distingue lo stato prima delle sorelle, il pre-lotta, il premio pendente e lo stato concluso, ricongiungendoli ai percorsi già esistenti. | Sulle V4 EN/IT, il membro 237 cresce di sei byte pari con relocation verificata; evento, coordinate e save sono invariati. Quattro stati, controllo verticale, confinamento e replay passano. Restano scena renderizzata, follower, SAVE/cold e dispositivo. |
| HeartGold/SoulSilver, **HG-F24** | Con Lettore GB attivo, il Summary aperto durante l'apprendimento dopo un'evoluzione ripristinava l'heap audio e sfrattava la sequenza GB dinamica senza ricaricarla al ritorno. | Un wrapper confinato conserva l'helper nativo e richiede di nuovo la sequenza evoluzione solo con GB Sounds attivo. | Cinque prove EN/IT su candidate esatte, interprete Thumb-1 indipendente, rami GB ON/OFF, ABI, confinamento e composizione passano. PCM/UI naturale, accetta/rifiuta/annulla, SAVE/cold e dispositivo restano aperti. |
| HeartGold/SoulSilver, **HG-T09** | Il tempo di gioco poteva passare da 998:59:59 a 999:59:59, saltando 999:00:00. | Corregge il confronto del contatore. Non ricostruisce ore già perse nel save. | Corpo e chiamante ARM eseguiti ai confini; nessun cambiamento del formato save. |
| HeartGold/SoulSilver, **HG-B01** | Fire Fang ignorava Wonder Guard quando non era superefficace perché il gate a due turni usava il suo effetto 273 invece del 272 di Shadow Force. | Un solo byte seleziona Shadow Force nel gate: Fire Fang segue il percorso ordinario e Shadow Force distingue carica e impatto; il branch resta invariato. | Otto Plus EN/IT autenticate, 16 sequenze ciascuna e 512 esecuzioni native sui due consumer. Fix sorgente di un byte verificato; lotta renderizzata, SAVE/cold e dispositivo restano aperti. |
| HeartGold/SoulSilver, **HG-B12** | L'IA controllava Levitazione due volte e non penalizzava le mosse Acqua contro Pellearsa. | Il secondo controllo ora usa Pellearsa sia nella copia caricata in overlay 10 sia nel membro sorgente `a/0/9/9`. Nessun dato Pokémon o formato save cambia. | Firma confermata in 13 immagini; 104 casi con controlli negativi. Applicazione e rilettura BLZ/NARC sulle EN/IT reali passano e sono deterministiche. La correzione è nei sorgenti: non è stata ancora conservata una nuova candidata né osservata la scelta mossa in battaglia. |
| HeartGold/SoulSilver, **HG-B13** | L'IA di cambio poteva marcare una mossa insieme immune e superefficace contro quattro doppi tipi e scegliere una riserva con una mossa che non può colpire. | Il ramo superefficace ora rispetta un'immunità già rilevata; la tabella tipi, il danno e il formato save non cambiano. | Helper e consumer reali eseguiti prima/dopo su sei Plus EN/IT: Thunderbolt contro Gligar viene scartato a favore di Geloraggio; ordine invertito, tre immunità singole e casi non immuni restano invariati. Fix sorgente verificato; candidata conservata, lotta e save/cold ancora aperti. |
| HeartGold/SoulSilver, **HG-B14** | Il gate IA di Arena Trap bloccava anche cambi legalmente ammessi da Volante, Levitazione, Magnet Rise o Shed Shell. | Delega al `BattlerCanSwitch` autorevole invece di mantenere controlli parziali duplicati. | 96 casi nativi su sei Plus EN/IT, 42 divergenze corrette e controlli grounded/Iron Ball/Gravity/trappole invariati. Candidata, lotta e save/cold restano aperti. |
| HeartGold/SoulSilver, **HG-B15** | Il cambio IA ignorava Pellearsa ed Elettrorapid sia già attive sia nelle riserve. | Due confronti condividono un helper di 20 byte dopo la tabella static-init; vecchi assorbitori, RNG e ordine restano invariati. | 96 casi su sei Plus EN/IT, 24 divergenze corrette; dominio completo 0–255 ammette solo `{10,78}`, `{11,87}`, `{18}`. Fix sorgente verificato; candidata, lotta e save/cold restano aperti. |
| HeartGold/SoulSilver, **Pokéathlon wrap** | Il riepilogo Sala Amicizia troncava a otto bit il conteggio 0–493 delle specie con cinque medaglie. | Il campo transitorio passa nel padding `+0x1A` e usa `strh`/`ldrh`; nessuna modifica al save. | 38 casi vulnerabili e 38 corretti sulle candidate EN/IT, sei→zero divergenze; quattro byte logici nel solo overlay 99. Stanza, SAVE/cold e dispositivo restano aperti. |
| HeartGold/SoulSilver, **HG-BAG-VIEW-01** | La vista Berries singola scriveva la tasca nell'entry 4 invece della posizione compatta 0 perché il setter ignorava `position`. | Il setter usa `position` per lo stride e conserva `pocketId` come identità; funzione adiacente equivalente e unico `BL` sono ritargettati. | Dodici sequenze EN/IT, confinamento 32+4 byte e mutanti passano; nessuna modifica a riserva, archivi o save. Picker giocato, SAVE/cold e dispositivo restano aperti. |

Questi casi e i controlli prima/dopo sono descritti nel
[rapporto tecnico dei fix](source/docs/bug-audit-1.3.1.md). Nella stessa
integrazione è stata corretta anche una regressione **nata durante lo sviluppo
della 1.3.1**, l'allineamento dei movimenti Eevee/Steven (**BUG-131-01**): non
va attribuita alla ROM originale o alla Plus 1.03.

La stessa ricerca ha dimostrato **HG-D02**, il cambio di sesso Azurill→Marill
derivato dai diversi rapporti sessi con PID invariato. Il percorso ARM9 reale
passa 14 casi EN/IT con confini e controlli negativi. Non è una correzione già
inclusa: ratio, cache e riscrittura PID hanno effetti incompatibili con almeno
uno fra Pokémon preesistenti, identità e scambi vanilla. I 64 low-byte PID
`0x7F..0xBE` costituiscono una prova diretta: con specie Marill e lo stesso PID
un ricevente vanilla deve calcolare maschio. Il requisito lossless fissa la
politica: preservare Pokémon, PID, save e interoperabilità. Il caso è quindi
chiuso `WONT_FIX` come limite retail documentato; non esiste un fix exact-PID,
interoperabile e lossless da installare automaticamente.

La ricerca giapponese ha inoltre dimostrato e corretto al componente
l'**indicatore Volo di Via Vittoria**. Da Johto il gioco passava al filtro
regionale l'ID del nome Via Vittoria, che alle coordinate `(28,7)` risultava
Kanto, invece dell'identità di destinazione Percorso 26. Il nuovo gate ammette
soltanto `(28,6..7)` e conserva nome, warp, flag e formato save. Le routine
Thumb reali, le candidate EN/IT, i controlli regionali e due postimage
diagnostiche passano; menu Volo naturale, SAVE/cold e dispositivo restano
aperti.

La segnalazione storica **HG-F22** sul follower che scomparirebbe entrando in
bicicletta nel Pozzo Slowpoke non è stata riprodotta sulle V4 EN/IT e non ha
prodotto una patch. Otto attraversamenti validi del Pozzo, a piedi e in bici, mostrano
lo stesso richiamo transitorio e Lapras realmente visibile dopo il primo passo;
quattro attraversamenti Union Cave controllano il comportamento con bici
ancora attiva (12 esecuzioni totali). Il risultato è
limitato a una fixture e una specie e non copre la revisione giapponese, quindi
classifica il caso come non confermato sulle candidate provate, non come bug
universalmente inesistente.

**Aggiornamento HG-T10, 5 novembre:** il successore `legendary-scene-version`
corregge e integra anche il mismatch dipendente dal titolo. Tre seam confinati
nell'overlay 2 selezionano le risorse della scena Lugia sulla mappa 244 e
conservano il percorso Ho-Oh; layout save e geometria ROM non cambiano.
Runtime sintetico EN/IT e controllo Ho-Oh passano sulle candidate sopra.
Restano non riprodotti freeze completo, battaglia e cattura; nessuna nuova
prova sul dispositivo fisico o SAVE/cold è stata eseguita. La progressione ordinaria Plus
continua a impedire lo stato storico anomalo.

**Checkpoint storico precedente:** **HG-T10** è separato dalla normale
progressione: la Plus impedisce di
completare la prima Lega prima del leggendario. In uno stato incoerente minimo,
però, il consumer nativo `ShowPerson` riproduce in EN/IT la duplicazione di un
Ho-Oh attivo da uno a due oggetti ID5. Il sorgente ora corregge questo solo
meccanismo nel membro 21: il flag nascondi `0x242` decide se eseguire
`ShowPerson 5`, quindi la prima esecuzione crea l'oggetto mancante e le
successive non lo duplicano. Il consumer globale e lo script Lugia restano
invariati. Non è ancora una seconda cattura o una scena completa accettata; il
controllo Lugia confuta il precedente sospetto di un object lookup nullo. Il
mismatch dipendente dal titolo è confermato al componente, ma la sua seconda
patch resta `DEFERRED_NO_PATCH / FIXTURE_LIMIT`: camera, specie, verso e
geometria sono incoerenti, mentre la causa del freeze scheduler non è stata
riprodotta con una fixture pre-scena completa.

## Novità della 1.3.1 oltre ai fix

La candidata compone una Guida e una pagina Opzioni Plus riorganizzate e
l'accesso al box nativo dalla squadra, già osservato sul dispositivo fisico.
Comprende inoltre precisione 85 per Fuocofatuo, una guardia per Sguardofermo e
la correzione del punteggio AI dopo un KO. Il titolo mostra V1.3.1. I componenti
per legenda/comandi nel riepilogo e varianti di squadra delle rivincite restano
installati ma inattivi: non sono funzioni giocabili della candidata e non vanno
annunciati come tali. Per le funzioni attive, comportamento completo,
prestazione e persistenza delle nuove interazioni restano da accettare.
Il [changelog](CHANGELOG.md) e il
[rapporto della candidata](source/docs/ui-1.3.1-validation.md) conservano
identità e limiti di ogni tappa.

## Correzioni già presenti nelle versioni precedenti

- **HG-B10, Grandine dopo Scendineve:** la Plus 1.03 usa già il controllo
  corretto della grandine permanente. La 1.3.1 non aggiunge un secondo fix.
- **HG-B11, Peso Ball:** il retail e le Plus 1.01–1.04 confrontavano per errore
  il tasso di cattura con 1024, penalizzando anche i Pokémon da 102,4 a
  204,7 kg. La Plus 1.1 aveva già corretto i due halfword e la correzione è
  ancora presente nelle 1.2.5 e candidate 1.3.1 EN/IT. Il ciclo corrente ha
  autenticato 13 immagini e 96 casi decodificati; Rapid Ball e Velox Ball sono
  state controllate separatamente e non mostrano lo stesso difetto. Non è un
  nuovo fix 1.3.1 né un playtest di cattura.
- **SG-06, SG-07, SG-14 e SG-18:** i dati riletti nelle nostre versioni
  precedenti mostrano rispettivamente Cartavetro di Garchomp, Volo di Claydol,
  il nome della coppia del Percorso 13 e Nottesferza di Scizor. Sono fix
  ereditati, non novità della 1.3.1; le singole scene non sono state rigiocate
  tutte nella nuova candidata.
- **SG-05, evento Mew:** la linea 1.3 ha già corretto la durata di tre
  movimenti, con prove storiche EN/IT. La stessa linea protegge un caso
  concreto di sovrapposizione dei flag alti con la Rubrica Amici (**SG-19**),
  senza spiegare ogni segnalazione generica di flag che si azzerano.
- La linea 1.3 ha anche corretto il feedback dopo un SAVE rifiutato e la
  modifica degli EV prima del rifiuto nel nuovo servizio Allenamento.
  Questi sono difetti della nostra evoluzione, non tutti bug della Plus 1.03.

Le prove di queste correzioni precedenti sono nel
[registro delle novità 1.3](source/docs/novita-1.3.0.md) e nella
[validazione Android storica](source/docs/android-1.3-dev-validation.md).

## Segnalazioni non dichiarate risolte

Restano senza una correzione dimostrata, fra le altre: i sintomi Safari
generici di menu/audio/turbo oltre SG-01a/SG-01b (**SG-01**), gli eventi hardware-specifici su R4 (**SG-04**) e i nomi
del Percorso 34 (**SG-13**). Per SG-13 classe/sprite e nomi retail confermano
la rinomina mancata, ma Drayano non ha pubblicato i sostituti: non vengono
inventati. La vecchia segnalazione sul
mancato starter da Camilla (**SG-17**) attribuiva erroneamente il premio alla
Medaglia Terra: dodici controlli sul vero script, sui testi EN/IT, sulla Guida,
sulle nove specie e sui conteggi squadra confermano invece titolo di Campione,
starter Sinnoh in testa e due slot liberi. Non è un bug dimostrato e non viene
alterata la ROM. Il vecchio freeze Celebi/Giovanni (**SG-16**) non è stato
riprodotto: dodici controlli sul percorso reale ne confutano quattro cause
statiche plausibili, ma manca un save autentico prima della scena; non viene
spacciato per corretto e non introduce una patch. Il caso Ledyba
(**SG-20**) è un bilanciamento intenzionale diverso dallo scambio di statistiche
descritto nel vecchio post. Le 54 schede retail sono un catalogo di ricerca,
non 48 bug corretti. La lettura extra dello scanner Cercastrumenti (**H2**) è
stata confutata come overflow nella memoria reale delle quattro immagini
esaminate; non è un fix. Il follow-up **H1** ha invece dimostrato un bug
interno: due interazioni Plus ordinarie erano classificate come oggetti
nascosti, facendo derivare allo scanner i flag fuori intervallo `E3F3`/`E3EE`.
Il compositore ora cambia solo i due campi tipo da 2 a 1; i veri oggetti
nascosti restano tipo 2. Byte, ricevuta e composizione/replay reale EN/IT sono
verificati. Due postimage diagnostiche private EN/IT confermano i record e
fanno Continue su copie raw immutate; non sono una candidata finale accettata.
La fixture Bugsy disponibile è debugger-assistita e le tre sequenze ordinarie
calibrate non raggiungono mappa74: prova visiva Cercastrumenti, SAVE/cold e
dispositivo restano aperti.

La campagna successiva **V-CHATOT** ha dimostrato un secondo bug interno della
ROM, distinto dai finding Daybreak sugli strumenti: 24 variabili storia fuori
intervallo condividevano byte con `SAVE_CHATOT`. La correzione è integrata nella
vera catena UI 1.3.1 e passa composizione/readback EN/IT e runtime ARM, ma non è
ancora contenuta nelle due vecchie ROM manuali elencate sotto. La matrice
successiva ha completato 8/8 cicli raw zero/HF01 in EN/IT con
SAVE nativo e cold; restano prove di scena e dispositivo, non la persistenza
headless.

## Stato delle prove e installazione

Le ROM manuali storiche **EN** `90435d3c…fc18` e **IT**
`420ec8b8…f059a` sono predecessori e non contengono tutti i fix sopra. I
precedenti trial attivi del 4 novembre sono EN `618f0501…fb13d`
(152.786.376 byte) e IT `171b53b6…d64a0` (159.029.292 byte); la IT è ancora
installata sul dispositivo in attesa del gate fisico della candidata formale
corrente. Entrambe passano cold boot, Continue,
campo e Squadra→R→PC nativo senza crash in 4.332 frame; la copia save rimane
invariata. **253 test mirati passano** e undici cicli
locali su copie di save precedenti hanno coperto Continue, SAVE e riavvio a
freddo: cinque condizioni per lingua e un ulteriore save IT avanzato con
squadra e box. L'auditor integrale originale segnala **NOT PASS** per i byte
dinamici degli oggetti mappa nell'array10; la rivalutazione limitata agli
esatti campi e valori giustificati passa **11/11**, preservando i rapporti
originali. Non è stato necessario modificare il codice della ROM per
quest'anomalia dell'audit. Le prove campionate non certificano ogni vecchia
versione e sono spiegate nel [rapporto](source/docs/ui-1.3.1-validation.md).
Due ulteriori save iniziali dei percorsi updater retail USA e Plus 1.03 hanno
superato il medesimo ciclo locale e audit circoscritto in EN; la loro origine
anteriore all'updater e le partite avanzate di quelle versioni non sono
certificate da questi due file.
Il trial IT è installato in-place dopo prova SAVE/cold su copia: ROM precedente
`420ec8b8…f059a` sostituita dalla `171b53b6…d64a0`, save personale, `.ml0` e
configurazioni cheat invariati, rollback conservato. La canonica si avvia a
freddo fino al campo senza un nuovo SAVE. Mancano la prova fisica EN, il
collaudo di tutte le funzioni e l'accettazione della release.

Questa candidata **non è ancora una patch pubblica pronta da installare**.
Quando la validazione sarà chiusa, il pacchetto offrirà patch di sole differenze,
guide PDF per lingua e istruzioni per partire dalla propria cartuccia o da una
Plus riconosciuta per SHA-256. Conservare sempre una copia del salvataggio
originale; non usare un vecchio savestate per riprendere dopo l'aggiornamento.
