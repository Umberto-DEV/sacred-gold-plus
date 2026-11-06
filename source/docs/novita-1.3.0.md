## Freeze durante la battaglia: correzione del ciclo tipi — 6 novembre 2026

Le nuove candidate formali sono EN
`50ba570f97655cecc7b11bed06eb7f683283b191c1c21f02e49ad55f90fc7665`
e IT `c63cf9e993cbee9c38949baf9444dda3e365bddb15840aaa08905d9b02afbedb`.
Entrambe riproducono le trial misurate byte per byte. Nel raccordo Folletto
un ramo conservava una destinazione interna alla nuova chiamata Thumb:
dalla seconda iterazione il calcolo tipi poteva finire in eccezione ARM9,
lasciando immagine ferma e audio su una nota. Il ramo corretto riusa l'indice
già calcolato e salta l'intera chiamata; cambia un byte nell'overlay, senza
modificare Pokémon, strumenti, difficoltà o formato del salvataggio.
Venti scenari del ciclo nativo EN/IT distinguono prima e dopo; riproduzione
melonDS senza JIT e controprova sul singolo byte confermano la causa.
La convalida fisica IT su copia è in corso. Questa correzione non dimostra
la risoluzione del vecchio freeze Latios. Dettagli e limiti in
[ai-scoring-1.3.1.md](ai-scoring-1.3.1.md).

## GUIDA e OPZIONI: risposta e transizioni — 1 novembre 2026

Aggiornamento HG-T10 del 5 novembre: le candidate correnti sono EN
`02cccfbfc49b6addddba90385634ffdfde22b9ff3fbae3d85ae8f5603c5bf0af`
e IT `35d459e3fcf7cf127d6ff0aec94a5f502accfce390b2455b83fe189a5ca088f4`.
Il nuovo stage `legendary-scene-version`, fra `legendary-scenes` e
`trainer-fixes`, corregge la selezione delle risorse della scena Lugia: mappa
244 usa la versione SoulSilver 8, Ho-Oh e le altre mappe conservano la 7.
Tre seam nell'overlay 2 restano nello stesso slot compresso; geometria ROM,
riserva residente e layout save non cambiano. Nel runtime sintetico EN/IT i
tre consumer Lugia ricevono 8; il controllo Ho-Oh EN conserva 7. Stato di
progressione e ingresso scena sono assistiti dal debugger su copie: questo
chiude il mismatch osservato, non dimostra la risoluzione del freeze storico,
la scena completa, battaglia/cattura/cleanup, SAVE/cold o il comportamento sul dispositivo fisico.

Sull'esatta nuova IT, melonDS Android sul Mac completa
Continue→campo→Squadra→R→Box nativo→campo. La copia raw esportata e la fixture
originale conservano SHA-256
`553925da5f1814b3ebba587f383b4197381d5bc040ba7b8d8208c1ca8a7fb3ce`.
È uno smoke senza SAVE; i vecchi cicli SAVE/cold, le suite e le accettazioni
restano legati ai rispettivi hash storici. Solo il Box è attivo; Summary e
rivincite restano inerti. La candidata corrente non è installata sul dispositivo fisico e
l'accettazione completa resta aperta.

Checkpoint storico del 5 novembre, prima di HG-T10: la composizione abilita soltanto
il Box portatile. Le candidate EN `5c561184…2f15` e IT `c5a45d16…77f97`
raggiungono il PC nativo da Squadra con R nel banco locale; l'esatta IT passa
anche su melonDS Android nel Mac il percorso Continue→campo→Squadra→Box→campo
e, in un ciclo separato su copia, SAVE→riavvio→Continue. Controlli Summary e
rivincite configurabili restano installati ma inattivi e non sono descritti
come funzioni giocabili. Il dispositivo fisico non era collegato: nessun file
di salvataggio, savestate,
cheat o ROM fisica è stato modificato e l'accettazione completa resta aperta.
Il gate globale fresco termina con exit 0: Class A 2.042/2.095 con 53 skip e
Class B 577/885 con 308 skip, per 2.980 test raccolti e zero failure. Sul Box
passano anche 59/59 test ARM del feature bench, 26/26 del package e 26/26 sulla
ROM. Gli skip restano limiti di fixture; il dispositivo fisico non era
collegato e non è stato aggiornato.
Una ricostruzione indipendente successiva riproduce EN/IT byte per byte e un
nuovo smoke Android della IT ricostruita ripete il percorso del Box senza SAVE;
la copia raw esportata resta identica all'ingresso.

Audit del 5 novembre, **HG-F08 lista GS Cup/guardia della Lega**: gli esatti
membri script EN/IT mostrano la collisione su `VAR_TEMP_x4005`. La lista lo
lasciava a 1 dopo una specie speciale vista; la guardia legge `>=1` come latch
“già spostata” e saltava `ApplyMovement`. Il producer same-size usa il teardown
comune della sola lista per azzerare la variabile e tornare al menu originale,
senza cambiare guardia, altre regole, entry, movimenti, NARC o layout save.
Riproduttore pre-fix, nove positivi, omissione, lista vuota, reset mappa,
mutanti e replay EN/IT passano. La prova naturale IT resta `TOOL_LIMIT`; il fix
non è nelle trial attive e mancano UI renderizzata, SAVE/cold e dispositivo.

Audit del 5 novembre, **HG-F09 erba invisibile**: matrix 0 e i lands 87/102
delle candidate attive EN/IT confermano sei caselle di bordo visivamente non
erbose ma codificate `0x0002` sui landmark recuperati dei Percorsi 43/44. Il
nuovo stadio sorgente, non ancora presente nelle trial attive, cambia soltanto
quei sei `u16` in `0x0400`; modelli, collisioni, matrix, geometria NARC/ROM,
tile estranei e save restano invariati. Controlli visivi/permission, mutanti,
replay e composizione mirata bilingue passano. Non è una prova gameplay:
incontri, effetto follower, SAVE/cold e dispositivo restano aperti. Percorso 28
e Safari non sono stati modificati perché manca una normalizzazione univoca.

Audit del 5 novembre, **HG-F02 Cascata**: gli esatti byte EN/IT confermano che
una rotazione laterale bloccata seguita da Giù avvia la discesa Sud lasciando
il facing laterale; 0/1/2 frame neutri non lo cancellano, mentre Giù solo è
Sud. Il nuovo stage sorgente instrada soltanto il ramo riuscito a un wrapper da
20 byte che imposta Sud prima del task originale. Fallimenti, salita da
script/menu, stack/ABI, geometria ROM e save restano invariati; mutanti,
confinamento e replay bilingue passano. La fixture naturale Surf resta
`TOOL_LIMIT`: rendering, SAVE/cold e dispositivo sono ancora aperti.

Audit del 5 novembre, **HG-F13 menu durante il salto del follower**: il vecchio
trial bounded usava un solo Giù e fermava il follower nel normale `cmd=9`; il
trigger storico richiede un secondo Giù e X durante `cmd=21/step=1`. Sulle
candidate attive EN/IT i ritorni 0/1/2/3 da Squadra producevano
`0x6000,0xE000,0x16000,0x1E000` nel vettore Y, con posizione mappa invariata.
Il nuovo stage dopo Cascata restituisce delta altezza zero solo quando il
movimento è in pausa, conservando fuori pausa guardia, fase, frame e tabella.
RED/GREEN EN/IT, reset, fermo, semantica Thumb/ABI, mutanti e composizione HG-F02
passano su copie temporanee; restano save naturale, altri sottomenu, SAVE/cold e
dispositivo.

Audit del 5 novembre, **HG-F05 follower/veleno**: il messaggio di sopravvivenza
interrompeva il salto cancellando il flag di movimento ma non il vettore Y. La
sola entry dello standard ora entra dal `LockAll` nativo, che completa il salto.
Delta script di una word, contratto EN/IT, mutanti e runtime temporaneo
positivo EN/IT passano; tre negativi EN e le copie save restano invariati.
Restano save naturale, altre sporgenze/reset, SAVE/cold e dispositivo.

Audit del 4 novembre, **Pokégear pan/zoom**: il culler dell'overlay 101 ignorava
X signed e poteva far riapparire marker lontani dopo il wrap OAM. Il fix
conserva i tre caller e porta la logica in un thunk ARM9 registrato attraverso
un trampoline in-place; lo stream resta nello slot BLZ esatto di 53.576 byte.
EN/IT, confini X `-7..263`, Y `0..199`, `autoCull=0`, ABI, riserva e
composizione passano. Restano pan→zoom→pan renderizzato, SAVE/cold e dispositivo.

Audit del 4 novembre, **Cuorugiada con regole custom**: il getter HGSS
restituiva tutto `totalLevel`, quindi un limite come 50 combinato al flag
produceva `0x8032` e saltava i confronti esatti con `0x8000`. Il fix confinato
maschera soltanto rule 13 e conserva tutte le altre regole e gli ID invalidi.
Hook, payload residente registrato, canarino, candidate EN/IT e composizione
passano; restano menu/link naturale, SAVE/cold e dispositivo. **HG-SEC01** è
ora riprodotto e corretto al componente: il percorso Wonder Card reale
accettava il sigillo 81 e scriveva il primo byte oltre l'inventario; il
successore valida sigilli `1..80`, fashion `0..99` e background `0..17` sia
nel check/give sia nei writer diretti. Banco ARM reale EN/IT, owner residente,
canarino, confinamento e composizione passano. Un give artificiale invalido può
ancora aggiornare la coda retail, ma non muta la decorazione né scrive OOB.
Nessuna card, save o catena ACE Plus è stata eseguita; restano delivery
naturale, SAVE/cold e dispositivo.

Audit del 4 novembre, **Via Vittoria/Volo**: il marker era raggiungibile ma non
si evidenziava aprendo la mappa da Johto. Il percorso di selezione passava al
filtro regionale l'ID del nome Via Vittoria invece dell'identità warp Percorso
26; a `(28,7)` il classificatore ordinario rispondeva Kanto. Il nuovo gate
confinato ammette soltanto i due punti di confine `(28,6..7)` e conserva nome,
destinazione, flag e save. Routine Thumb reali, candidate EN/IT, controlli
regionali, composizione e postimage passano; mancano ancora hover renderizzato
con flag naturale `0x9D1`, SAVE/cold e dispositivo.

Audit del 4 novembre, **HG-F20-DP DynamicPunch**: il secondo shake nasceva al
tick 7 mentre il primo esponeva X=-1 e registrava quella coordinata come nuova
base. Il solo `Delay 3→4` lo sposta al tick neutro 8. Il nuovo stadio cambia un
byte nel membro 223 dopo Facade e ne preserva i sei byte; task Thumb reali,
EN/IT e replay passano. Helping Hand è ora corretto separatamente spostando il
Delay esistente dentro il loop: tre byte nel membro 270, con handler HGSS reali
e replay EN/IT verdi. Spit Up è una causa distinta, corretta separatamente;
restano inoltre rendering, ripetizioni, lati/doppie, animazioni off, SAVE/cold
e dispositivo.

Audit del 4 novembre, **HG-F18 Strength**: lo shake reale di dieci tick lasciava
X+2 e la cleanup non ripristinava X. Il nuovo stadio, dopo Helping Hand, cambia
un solo byte nel membro 70 (`10→8`); i controlli nativi 8/9/10/11 provano la
fase 0/+2/+2/0 e le candidate EN/IT con replay passano; anche la composizione
completa è verde. Restano rendering, ripetizioni, lati/doppie, animazioni off,
SAVE/cold e dispositivo.

Audit del 4 novembre, **HG-F20-SU Spit Up**: il task terminava X+2 e la cleanup
ripristinava solo Y e scala. Il nuovo stadio BLZ rimuove esattamente il residuo;
EN/IT, quattro X iniziali e due mutanti confermano il comportamento. **HG-F16
Giratina/PC** è corretto separatamente: all'uscita dal PC la routine retail
ricalcola forma, abilità e statistiche dei Giratina in squadra. Anche
composizione e replay completi EN/IT passano; restano prove renderizzate/UI,
raw SAVE/cold e dispositivo.

Audit del 4 novembre, **HG-F17 Facade**: lo script avviava sei trasformazioni
5+5 frame a distanza di 8 frame, creando cinque overlap e lo spostamento
residuo dello sprite. Il nuovo stadio conserva le durate e porta a 10 i cinque
Delay e l'intervallo audio corrispondente: sei byte nel membro 263, zero
ricostruzioni del NARC. V4 EN/IT, controlli negativi e catena completa bilingue
passano. Restano rendering, ripetizioni, lati, animazioni off, SAVE/cold e
dispositivo; nessuna ROM o save è stata conservata.

Audit del 4 novembre, **HG-B09**: la Torre Lotta conservava correttamente i
round in 16 bit ma li restringeva a otto bit prima della scelta avversari.
Dopo 1792 vittorie il round 256 diventava zero; ai round 258/262 potevano
ricomparire i Palmer e il wrap tornava a 3584 vittorie. Quattro halfword
confinati mantengono il valore pieno in entrambi i rami, incluso Multi/Link,
senza modificare save, tabelle o routine RNG; il pool corretto può consumare
un numero diverso di estrazioni. Dieci Plus EN/IT passano 18 scenari
ciascuna e 360 esecuzioni native: 110 divergenze prima, zero dopo, risultato
deterministico `c0ec4f35…bb94f`. Stadio, ricevute, mutanti e applicazione
diretta V4 EN/IT dopo Lottery sono verdi. Restano serie naturale oltre soglia,
schermata/BP, peer link, SAVE/cold e dispositivo; nessuna ROM/save è stata
conservata.

Audit del 4 novembre, **HG-B08**: salendo di livello durante Transform, la
routine retail ricaricava dalla specie originaria le cinque statistiche di
lotta prima di controllare il bit Transform. Forma, tipi, abilità e mosse
copiati restavano quindi associati ad Attacco, Difesa, Velocità, Attacco
Speciale e Difesa Speciale sbagliati. La sostituzione sorgente da 340 byte
protegge soltanto quelle cinque statistiche; livello, amicizia, HP/HP massimi,
percorso ordinario e Mimic continuano ad aggiornarsi. Otto immagini Plus EN/IT
passano 128 esecuzioni originali e 128 corrette; i risultati rosso/verde sono
deterministici. Writer e lettore autenticati, applicazione reale V4 EN/IT e
36 test mirati EN/IT di replay, peel e mutanti sono verdi. Restano level-up
giocato con/senza nuova mossa, switch/fine lotta, doppio/link,
SAVE/cold e dispositivo. Nessuna ROM o save è stata conservata.

Audit del 4 novembre, **HG-B07**: il PP di Pressure ricompariva dopo un cambio
manuale immediato perché il decremento tardivo viveva soltanto nel BattleMon e
il rientro ricaricava il PartyMon non aggiornato. Cinque membri script
autenticati sincronizzano ora Counter, Mirror Coat, Magic Coat, Snatch e Metal
Burst sui soli percorsi riusciti tramite il consumer retail già esistente.
Otto immagini Plus EN/IT passano 160 helper, 320 ricaricamenti, 24 sync e 16
chiamate native Metal Burst, con due risultati byte-identici. Metal Burst è
confermato al componente ma non attribuito al resoconto storico né a una prova
su cartuccia. Nessuna ROM/save è stata conservata; restano battaglia naturale,
doppio/link, SAVE/cold e dispositivo.

Audit del 4 novembre: **SG-01a** sul Percorso 47 è dimostrato e corretto al
livello componente source-bound. Il percorso sano di Mira chiude la finestra
prima di lasciare il campo; Buck, Cheryl e Marley eseguivano leave e restore
prima di chiudere la vecchia finestra. Il fix sposta i tre `CloseMsg` subito
dopo il rispettivo `NPCMsg`, senza cambiare lunghezza, entry point o altri
byte. Il produttore d'archivio autentica il membro 260 e rifiuta riapplicazioni
e preimage estranee. Il banco combinato con SG-02 passa 15/15; la composizione e
il replay reali completi EN/IT passano in memoria (1 test, 310,378 s). Non è
stata conservata una nuova ROM. Un follow-up di 12 sequenze lega le segnalazioni
dopo il secondo/terzo/quarto duo proprio ai tre percorsi SG-01a corretti, con
Mira come controllo sano, ma non trasforma la correlazione in una riproduzione
del blackout. Il censimento di 184 raw save unici non trova una fixture utile.
Audio bloccato e menu neri restano **non riprodotti runtime**: servono raw save
di prova, turbo/menu, gameplay, SAVE/riavvio a freddo e dispositivo prima di
attribuire o riaprire un difetto ROM residuo.

Un sottocaso separato, **SG-01b**, è ora corretto nei sorgenti: la sconfitta
contro l'amministratrice finale usava un salto verso `0x6C4`, un percorso che
non raggiungeva né `WhiteOut` né `ReleaseAll`. I quattro rami perdita partner
sani convergono invece sull'unico `WhiteOut` `0x7A4`, coerente anche con la
nota autoriale 1.05. Il fix retargetta soltanto quel displacement, conserva il
percorso vittoria e lascia byte-identici tutti i `CloseMsg` di SG-01a. RED/GREEN,
mutanti, confinamento, replay EN/IT e producer unico del membro260 passano; la
sconfitta giocata, SAVE/cold e dispositivo restano da eseguire. Questo non
chiude i sintomi generici di menu nero, audio bloccato o turbo.

**SG-02** è ora riprodotto separatamente a livello source-bound. Lo screenshot
storico mostra il giocatore sotto il ponte mentre parte il primo duo sopra; il
dispatcher coordinate autentico confronta X/Z ma non Y. Poiché i 217 record
coordinate della candidata hanno quota zero, il motore globale non viene
alterato. Un wrapper locale di 23 byte legge `GetPlayerXYZ` e lascia raggiungere
la vecchia entry Mira soltanto a Y=0, terminando prima di ogni effetto sul piano
inferiore. Dodici sequenze con bordi, stato e quote negative passano, così come
il replay completo EN/IT. Gameplay da raw save, SAVE/cold e hardware restano
aperti; nessuna nuova ROM è stata conservata.

Lo stesso audit distingue correttezza da prestazioni. Settings, Guide e UI
nativa passano 381/381 prove mirate senza nuovo crash, leak o rollback
incompleto naturalmente raggiungibile. La verifica successiva ha distinto le
configurazioni: `4/8/240` produce il modulo da 64.712 byte e 824 byte liberi;
la produzione `64/8/240` riproduce esattamente il modulo cronometrato da 64.728
byte e 808 byte liberi. Le misure 84/99 restano legate alla sua ROM pin-nata;
servono confronti AB/BA sulla composizione più recente e prove sul dispositivo
di destinazione prima di descriverla come accettata o ottimizzata.

Aggiornamento ROM del 3 novembre: il nuovo stadio `ai-immunities` corregge
HG-B12, un controllo duplicato di Levitazione nell'IA che lasciava senza
penalità le mosse Acqua contro Pellearsa. La parola 26→87 viene aggiornata
nelle due copie reali, overlay 10 e membro 0 di `a/0/9/9`; applicazione e
rilettura EN/IT sono deterministiche e confinate. La correzione è nei sorgenti,
ma non è stata ancora prodotta né installata una nuova candidata e manca il
playtest della scelta mossa. HG-D02 Azurill→Marill è riprodotto in 14 casi
ARM9 EN/IT ed è chiuso `WONT_FIX` per invarianti lossless: le opzioni
ratio/cache/PID cambierebbero Pokémon esistenti, identità o scambi vanilla. La
1.3.1 conserva quindi il comportamento retail e documenta il limite, senza una
migrazione distruttiva.
HG-F22, la segnalazione del follower nel Pozzo Slowpoke, non si riproduce in
otto attraversamenti V4 EN/IT a piedi/in bici: dopo il normale richiamo
iniziale Lapras è visibile al primo passo, con Union Cave come controllo.
Quattro attraversamenti Union portano il totale a 12 esecuzioni.
Nessun fix viene applicato; una sola fixture/specie e l'assenza della revisione
JP impediscono di dichiarare il caso universalmente inesistente.

Lo stadio `ai-scoring` corregge ora anche HG-B13: dopo un'immunità, una
debolezza della seconda tipologia non può lasciare insieme i flag immune e
superefficace. Helper e scelta post-KO reali passano prima/dopo su sei input;
il delta è `0420→0c20` a `0x02252202`. Non è ancora una nuova ROM conservata:
restano lotta, save/cold e dispositivo.

Lo stadio `ai-immunities` corregge ora anche HG-B14. Il vecchio gate IA
duplicava in modo incompleto le regole di cambio e trattava come intrappolati
Volante, Levitazione, Magnet Rise e portatori di Shed Shell. Il prefisso
guardato dell'overlay 10 delega ora alla `BattlerCanSwitch` già usata dal
motore normale. Il banco CPU passa 96 casi su sei input EN/IT, inclusi Iron
Ball, Gravity, Pedinombra, Magnetismo, vincoli e controlli senza trappola.
Nessuna candidata è stata scritta o installata; manca la lotta giocata.

Lo stesso stadio corregge HG-B15: l'IA riconosce ora Pellearsa ed
Elettrorapid sia quando sono già attive sia quando valuta una riserva. Due
call site condividono un helper confinato nei 20 byte liberi successivi alla
tabella static-init; non vengono aggiunte chiamate RNG. Sei immagini EN/IT e
96 casi nativi passano, inclusi i vecchi assorbitori e i controlli negativi.
La correzione è nei sorgenti e verificata in memoria, non ancora in una ROM
candidata conservata o in una lotta giocata.

Lo stadio `ai-immunities` include ora anche AI-WEB-01. Il vero interprete
Thumb dell'overlay 10 mostrava che Zampillo/Eruzione usavano gli HP del
bersaglio ai confini 50/51 e 70/71 e ignoravano quelli dell'utilizzatore. Due
sole parole-token del membro 0 di `a/0/9/9` cambiano 0→1; la matrice EN/IT
dopo il fix segue l'utilizzatore. Restano percorso Expert completo con
Hydro Pump/Surf, scelta mossa, SAVE/cold e dispositivo.

Lo stesso stadio include ora AI-WEB-03. Nella sequenza Expert di Facade il
vero interprete EN/IT aggiungeva un punto quando era alterato il bersaglio e
ignorava lo status dell'utilizzatore. Cambia una sola parola-token, 0→1, a
`+0x5B68` del membro 0 di `a/0/9/9`: dopo il fix veleno,
iperavvelenamento, scottatura e paralisi seguono l'utilizzatore; sonno e
congelamento restano negativi. La configurazione Plus di Valerio contiene in
entrambe le varianti Swellow+Fiammosfera+Facade e il trainer ha AI flags 7.
Restano dispatch naturale, scelta mossa, SAVE/cold e dispositivo.

AI-WEB-04 corregge inoltre il dispatch Expert di Thunder. La tabella reale
EN/IT ripeteva effetto 151 (SolarBeam) e non raggiungeva mai la routine Thunder
effetto 152. Una sola parola a `+0x2C00` diventa 152; il banco ARM osserva poi
bonus in pioggia, penalità al sole sul confine RNG 49/50 e controlli SolarBeam/
Thunderbolt invariati. Sette trainer della candidata hanno Thunder e il bit
Expert. Restano resistenza/immunità nel percorso completo, scelta naturale,
SAVE/cold e dispositivo.

AI-WEB-02 corregge la valutazione Basic di Metal Burst. Le due scorciatoie
Stall e i due confronti con l'ID 107 non descrivevano l'ordine completo e
Pietrabrillo poteva essere scambiato per uno strumento ritardante. I quattro
salti relativi vengono resi nulli, così lo script usa sempre il proprio
`CheckSortSpeed`, già capace di gestire Stall, Coda Lenta e Full Incense. Il
banco EN/IT esegue davvero quel comparatore e passa 30 scenari per lingua,
inclusi controlli senza effetto, doppi strumenti, parità/RNG, Distortozona,
Rapidartigli e Baccacrela. Restano incontro naturale, scelta osservata,
priorità nel contesto battaglia completo, SAVE/cold e dispositivo.

HG-F23 è corretto nel producer degli script legacy. A 99×TM07 la Borsa Plus
accettava la richiesta ma inseriva zero; lo standard di consegna consumava la
spia di scarto e il membro 932 marcava ugualmente il premio. Ora entrambi i
blocchi leggono prima la quantità reale e lasciano il flag 210 unset a 99; il
ramo post-medaglia riprova e 98→99 conclude una sola volta. EN/IT, relocation e
mutanti passano. Restano scena, SAVE/cold e dispositivo; nessun regrant
automatico viene tentato sui vecchi save col flag già posto.

Lo stadio confinato `pokeathlon` conserva ora in 16 bit il conteggio 0–493
usato dal riepilogo Sala Amicizia. Prima, overlay 99 troncava il valore a otto
bit: il banco nativo trova sei errori in 38 casi; dopo `strh`/`ldrh` gli stessi
38 casi sono corretti e i campi adiacenti restano invariati. La modifica è di
quattro byte logici nel solo overlay 99 e non cambia salvataggi o identificatori.
Restano prova renderizzata, Continue/SAVE/cold e dispositivo.

Aggiornamento del banco del 3 novembre: tutti i lettori mantenuti della tabella
autoload ARM9 validano ora extent, ordine, somme, overflow e un massimo di 256
sezioni prima di costruire oggetti ndspy. I riproduttori sintetici
sovradimensionati sono rifiutati; la V4 EN pin-nata conserva hash e mappa
attesi. È hardening degli strumenti di costruzione/verifica, non una modifica
ai byte ROM o save.

Correzione ROM del 3 novembre, **V-CHATOT**: 24 ID variabile storia
(`612E..6139`, `619E..61A9`) superavano il blocco SaveVarsFlags e puntavano a
halfword della registrazione Chatot. Gli script potevano alterare l'audio e una
nuova registrazione poteva cambiare in entrambe le direzioni i gate a
coordinate. La versione `HF02` conserva una volta l'ammissibilità osservabile
dei vecchi save (zero aperto, nonzero chiuso), poi usa 24 bit liberi della
riserva già esistente. Non cambia dimensione/ID dei blocchi save e non scrive
Chatot o Rubrica. Riproduzione 12/12, test ARM EN/IT e composizione UI completa
con readback passano. Passano anche 8/8 cicli su copie raw: prenotazione zero
senza Plus/con Plus/Borsa estesa e HF01 in entrambe le lingue, con Continue,
SAVE nativo, arresto e cold restart; dati protetti, Chatot e originali restano
invariati. Mancano scene rappresentative con registrazione/gate e dispositivo:
non attribuire a questa correzione le precedenti prove fisiche delle candidate
HF01.

Verifica SG-16 del 3 novembre: il vecchio freeze Celebi/Giovanni non è stato
riprodotto. Quattro ipotesi e dodici sequenze sul vero binding mappa 298/script
114 confutano versione divergente, attese movimento mancanti, mancato ripristino
della battaglia speciale e blocco deterministico del task. Le dereferenziazioni
follower non protette restano annotate, ma nessun `NULL` raggiungibile è stato
dimostrato. Il censimento di 184 raw save unici validi non contiene una fixture
autentica pre-evento: nessuna modifica ROM, e il playtest resta bloccato da quel
limite del banco.

Verifica SG-17 del 3 novembre: la segnalazione legava erroneamente il dono dei
due starter Sinnoh alla Medaglia Terra. Il vero ramo di Camilla non controlla
medaglie; testi EN/IT e Guida richiedono titolo di Campione, starter Sinnoh o
evoluzione come primo Pokémon vivo e due slot liberi. Dodici sequenze coprono
nove specie, squadre da uno a sei, mutanti e ciclo del flag 3F9B. Nessuna delle
184 fixture raw uniche soddisfa lo stato completo per un playtest, quindi non si
inventa una prova giocata e non si modifica la ROM.

Intervento 1.3.1 a grafica invariata: censimento heap lineare, controllo font
senza duplicazione, avanzamento dei reader e riuso del front per le sole righe
cambiate. Corretti il tasto perso dopo la pubblicazione, il collegamento reale
del fuoco del libro, GUIDA/GUIDE maiuscolo e l’oscuramento di entrambi i display
fino al fade nativo comune. Nessun formato o identificatore save cambia.
Il [rapporto UI](ui-1.3.1-validation.md) distingue misure guest, prove negative,
identità intermedie e finali, cicli raw-save e limiti fisici; le precedenti
prove Android conservano le loro identità.

Sul successore corrente il confronto ripetuto misura apertura OPZIONI 84 frame,
GUIDA 99, Pokémon nativo 77 e Borsa 87. Il cursore visibile richiede 6–7 frame
nelle due UI, nell’intervallo nativo 4–7; GUIDA apre ancora circa 0,2 secondi
più lentamente della Borsa. Cinque copie raw, inclusa quella del personale
archiviato, preservano i dati protetti nel ciclo SAVE/cold. Preparato l’update
IT della ROM esistente, senza sostituire il save, con backup fresco richiesto
al collegamento. Nessuna installazione o misura fisica di questa correzione;
identità e limiti sono nel rapporto collegato.

Aggiornamento del **1 novembre 2026**, precedente candidata IT `420ec8b8…f059a`:
ha completato su Android fisico Continua, caricamento campo, SAVE e avvio a freddo su una copia
del save corrente. La ROM è stata sostituita mantenendo il save personale
originale byte-identico. Dati protetti confrontati e preservati; nessuna nuova
accettazione universale, EN, prestazioni o di tutte le funzioni. Dettagli e
limiti nel [rapporto UI](ui-1.3.1-validation.md). Nessuna pubblicazione autorizzata.

## Nuova candidata con correzioni integrate — 31 ottobre 2026

**Stato save aggiornato:** per la candidata 1.3.1 identificata nel rapporto,
undici copie di salvataggi precedenti hanno completato Continue → SAVE → avvio
a freddo, inclusa una partita IT con squadra e box popolati. Il NOT PASS
dell'auditor integrale originale riguarda byte dinamici degli oggetti mappa
(`array10`); una rivalutazione che ammette solo gli esatti cambi osservati e
verificati passa 11/11. Le ricevute originali restano intatte. Non è una prova
di ogni versione storica né un'accettazione Android. Il dettaglio e i limiti
sono nel [rapporto della candidata](ui-1.3.1-validation.md).

La nuova composizione EN/IT comprende anche pesca SG-11 e tempo di gioco
HG-T09, oltre a SG-08/09/15/15b, Ninnananna e allineamento Eevee.
**253 test mirati PASS in 31,046 secondi, zero skip**; revisione indipendente
senza problemi importanti. Nessuna suite globale o prova Android viene
attribuita a questo risultato. Le nuove immagini e i limiti sono nel
[rapporto della candidata](ui-1.3.1-validation.md#nuova-candidata-con-correzioni-integrate--31-ottobre-2026).

Il maintainer eseguirà sul dispositivo il collaudo funzionale delle nuove
funzioni. La consegna è privata, con legenda, box e rivincite attivi; i gate di
produzione restano invariati. Le sezioni seguenti conservano le tappe e gli hash
precedenti: i vecchi file manuali non includono queste correzioni.

Aggiornamento audit del **31 ottobre 2026**: nei sorgenti 1.3.1 sono integrate
correzioni SG-08/09/15, guardia15b, Ninnananna e allineamento Eevee227, con prove codice prima/dopo e
rilettura indipendente. Hail risulta già corretto dalla Plus 1.03. Il catalogo
ora distingue 48 schede retail e nove piste aggiuntive; la pesca restava aperta
in quella ricognizione ed è stata integrata nella nuova candidata descritta sopra.
[Rapporto e limiti](bug-audit-1.3.1.md).
Il follow-up Daybreak del 3 novembre ha classificato tutti i 34 candidati degli
strumenti: 32 fix di componente, uno già risolto e un observer Android corretto
localmente ma ancora da revocare/sostituire sul dispositivo. Non sono 34 bug di
gameplay e non producono da soli una nuova ROM; dettagli e prove restano nel
rapporto tecnico.
I file manuali precedenti non sono sovrascritti e non includono questi fix;
compatibilità SAVE/cold, prove visive/dispositivo e accettazione restano separate.

Consegna privata del **31 ottobre 2026**: su richiesta del maintainer, il
collaudo funzionale delle nuove funzioni passa al dispositivo. È disponibile una
candidata manuale attiva, distinta dall’accettazione Android e dalla release.
Solo sei campi di attivazione cambiano rispetto alla composizione inerte
verificata; nessuna evidenza runtime viene simulata. La campagna estesa è
interrotta e i test mirati dopo la correzione della tabella intervalli passano.
Identità, prove già svolte e limiti sono nel [rapporto](ui-1.3.1-validation.md).

Aggiornamento successore del **31 ottobre 2026**: catena completa 1.3.1
integrata, con ritiro verificato della vecchia Guida, overlay delle rivincite
incluso nei seed UI e titolo V1.3.1. Le prime candidate complete EN/IT avviano
Continue e campo sul banco locale. Legenda, box e varianti delle rivincite
restano disattivati in attesa delle prove reali; compatibilità SAVE/riavvio,
Android e prestazioni finali non ancora accettate. Identità e limiti nel
[rapporto della candidata](ui-1.3.1-validation.md). Nessun via libera al trasferimento o alla release.

# Novità della 1.3.0 rispetto alla 1.2.5

## Ricerca sui bug ereditati — 31 ottobre 2026

Estensione del 3 novembre: il difetto retail **HG-B11 Peso Ball** è presente
fino alla Plus 1.04 ma risulta già corretto dalla 1.1 e conservato nelle
candidate correnti. Tredici immagini e 96 casi di confine confermano la
transizione; Rapid Ball e Velox Ball sono rami diversi e i controlli statici
non mostrano il medesimo errore. Non è una nuova modifica 1.3 né una cattura
giocata.

Estensione del 4 novembre: il difetto retail **HG-B01 Fire Fang/Wonder Guard**
era ancora presente nelle otto Plus EN/IT autenticate. Il gate a due turni
usava per off-by-one l'effetto 273 di Fire Fang invece del 272 di Shadow Force.
Lo stadio `type_consumers` corregge un solo byte dell'immediato e conserva il
branch: Fire Fang raggiunge Wonder Guard, mentre Shadow Force salta il controllo
in carica e lo esegue all'impatto. Cinquecentododici esecuzioni ARM sui byte
reali coprono 16 sequenze per immagine e mantengono invariati Fly/Bide, Ice
Fang, Thunder Fang e i percorsi senza Wonder Guard o superefficaci. Restano
battaglia renderizzata, SAVE/cold e dispositivo.

Nello stesso ciclo, **HG-B02 Rage/stati volatili** è stato confermato su otto
Plus EN/IT: abbandonare Rage eseguiva un AND positivo che conservava Rage e
cancellava tutti gli altri bit `status2`, incluso Transform. La correzione di
due byte applica invece il bit-clear canonico. Ventinove sequenze per immagine
e 464 esecuzioni ARM coprono ogni campo, i negativi e più battler; la
composizione EN/IT e il writer successivo conservano il fix. **HG-B03**, la
persistenza delle mosse copiate dopo Transform/Rage, è stata tracciata fino al
consumer PartyMon ed è registrata come manifestazione della stessa causa, non
come secondo fix. Restano Pokémon cifrato reale, uscita naturale dalla lotta,
SAVE/cold e dispositivo.

Sempre il 4 novembre, **HG-B04 Pursuit/Acid Rain** è stato confermato in tutte
le 30 immagini Plus EN/IT locali esaminate. Il subscript di Pursuit sottraeva
l'ID del battler svenuto dalla maschera globale del campo invece di
ripristinare il valore salvato: grandine, sole, sabbia, Uproar, Gravity, Fog e
Trick Room potevano quindi trasformarsi in combinazioni di bit spurie; anche la
sola pioggia veniva alterata, pur senza mostrare la miscela «Acid Rain». Il fix
canonico modifica due byte del solo membro `a/0/0/1:153`. Otto immagini, 20
scenari ciascuna e 320 esecuzioni native confermano originale e postimage; il
producer condiviso conserva dimensione e gli altri 296 membri, e la
composizione/replay reale EN/IT passa. Restano prova renderizzata,
Castform/Cherrim, link host/client, SAVE/cold e dispositivo. Non
è stata prodotta una nuova candidata ROM.

Nello stesso giorno, **HG-B05 U-turn/tentennamento da oggetto** è stato
confermato su otto immagini Plus EN/IT. Dopo il cambio, il controllo tardivo
leggeva King's Rock/Razor Fang dal Pokémon subentrato: poteva ignorare
l'oggetto dell'uscente oppure produrre un tentennamento spurio dall'oggetto del
subentrante. Venti scenari per immagine e 160 esecuzioni native coprono i due
versi, King's Rock/Razor Fang, limiti RNG e gate mossa/danno/KO. Il fix salva
effetto effettivo e modificatore dell'uscente nello script pivot e li consuma
nei due soli getter tardivi; il percorso ordinario e tutti gli altri gate
restano invariati. Test TDD, mutanti e composizione/replay completa EN/IT
passano. Restano battaglia naturale, doppio/link tra build uguali, SAVE/cold e
dispositivo; le build link miste non sono supportate per possibile divergenza
RNG. Nessuna ROM candidata è stata conservata.

Sempre il 4 novembre, **HG-B06 icona status invisibile** è stato confermato
su otto immagini Plus EN/IT. Mente Locale e Indifferenza curavano realmente
solo confusione o attrazione, ma lo script aveva già nascosto l'icona di un
eventuale sonno, veleno/iperavvelenamento, bruciatura, congelamento o paralisi.
Il fix porta i due dispatch prima del clear grafico e conserva la stessa attesa
di 30 frame su ogni ramo; le cure persistenti restano invariate. Venti scenari
per input, 320 esecuzioni script, 200 esecuzioni native, mutanti e
composizione/replay completa EN/IT con Pursuit e U-turn passano. Restano
battaglia renderizzata, switch-out/in, doppio/link, SAVE/cold e dispositivo.
Nessuna ROM candidata è stata conservata.

Follow-up H1 del 3 novembre: due interazioni Plus erano codificate come oggetti
nascosti e facevano derivare a Cercastrumenti flag fuori intervallo. Il fix
`legacy-events` riclassifica soltanto quei due record; il componente e la
composizione/replay completa EN/IT sono verificati, conservando anche il vero
oggetto nascosto 8006/type2. Il 4 novembre due postimage diagnostiche private
fino a `legacy` hanno confermato gli stessi record e il Continue EN/IT su copie
raw immutate; non sono candidate finali accettate. La fixture disponibile parte
da una palestra preparata col debugger e non raggiunge mappa74 nelle tre
sequenze ordinarie calibrate: prova visiva Cercastrumenti, SAVE/cold e
dispositivo restano aperti.

Il [catalogo HGSS retail](known-bugs-hgss.md) e il
[registro dei bug storici della hack](legacy-bugs-1.3.md) documentano fonti,
limiti e primi riscontri statici sui pending inerti 1.3.1 identificati per hash.
La prima ricognizione era di ricerca; il seguito sopra indicato integra
correzioni circoscritte. Le prove integrali nel gioco restano aperte.
Nessun nuovo test runtime o salvataggio è attribuito a questo catalogo;
le successive candidate manuali attive hanno identità e prove separate.

## Consegna sorgenti delle meccaniche — 31 ottobre 2026

In questo **checkpoint storico precedente all'attivazione privata**, la
consegna congelata delle meccaniche è stata verificata per SHA-256 e
revisionata: accodamento unico degli archivi, Sguardofermo nel registro degli
stadi, correzione delle sei code fiocco e guardia squadra piena per Eevee.
Il builder deriva automaticamente i produttori obbligatori dei delta.
Legenda del riepilogo, box portatile e rivincite sono sorgenti completi ma
inattivi **in quelle immagini di checkpoint**; restano da completare il ritiro verificato della vecchia Guida,
l'integrazione dell'overlay 126 nei seed UI e la campagna sulla candidata reale.
Nessuna nuova prova Android o compatibilità dei salvataggi deriva dalla sola
consegna: le evidenze precedenti conservano gli hash e i limiti già registrati.
La 1.3.1 non è ancora pronta per sostituire la 1.3 sul dispositivo.

Nel checkpoint storico HG-T10 precedente al fix di selezione versione descritto
in apertura, il sorgente 1.3.1 includeva il guard locale per la scena Ho-Oh:
il membro 21 crea l'oggetto ID5 soltanto quando il flag nascondi `0x242` è
ancora posto, evitando la duplicazione riprodotta al secondo passaggio. Il
consumer globale `ShowPerson`, il membro Lugia e il layout save non cambiano.
Il mismatch dipendente dal titolo era confermato al componente, ma la seconda
patch restava `DEFERRED_NO_PATCH / FIXTURE_LIMIT`: mancava una fixture pre-scena
che esegua cinematica, battaglia e cleanup e localizzi il freeze scheduler.
Questa correzione non è ancora un'accettazione emulator/device della scena.

## Integrazione meccaniche — 30 ottobre, checkpoint successivo

**Smoke integrato IT passato:** candidata `d8a71af2…c32f115`, UI + mosse + AI.
Continua, Guida/Opzioni e ritorno al campo osservati su melonDS Android;
save identici dopo uscita senza SAVE. Sessione chiusa, nessun push/release.
[Identità e limiti della prova](ui-1.3.1-validation.md).

Il builder ora compone **UI → mosse → AI**, con ricevute concatenate e
rilettura indipendente. Prima gli stadi successivi alla UI erano rifiutati;
ora Fuocofatuo a85 di precisione e la correzione del punteggio AI dopo KO
possono entrare nella stessa candidata. Revisione indipendente positiva e134
test di integrazione sorgenti passano. Due prove complete del builder EN/IT
passano in122,975s: catena UI/mosse/AI, replay indipendente, ricevute e
percorso soloUI invariato. Il verificatore AI rifiuta anche flussi
BLZ alterati e ricevute prive degli hash:40 test mirati passano.

La policy residente riconcilia comandi512B, box3024B, stub192B e
Sguardofermo32B nel suffisso dismesso della Guida, lasciando1344B preservati.
Non attiva ancora questi moduli: gli installer devono dimostrare il ritiro
completo e la corretta durata.61 test policy/UI passano. Abilità, comandi,
box, regali e rivincite restano da collegare alla build finale; non sono
certificati dai test dei singoli moduli CC.

Retest Android IT85ac: L resta sulla pagina2/2 anche dopo10s neutri.
Gli8 test del controller compilato passano, ma non spiegano ancora la
ricezione sul frontend. Sessione chiusa e tutti i save invariati. Prestazioni
UI e campagna SAVE/riavvio finale restano aperte. Priorità: composizione delle
meccaniche e smoke della candidata integrata, senza nuove rifiniture estetiche.


Ultimo controllo successore, **30 ottobre, cornici Guida**: il testo nativo
non interrompe più il bordo rosso e i separatori. Prove native e composizioni
EN/IT passano; la candidata Android IT `85ac4963…bbfc48` conferma la correzione,
Info/selettore/annullamento e salvataggi invariati senza SAVE. Modulo 63.220/65.536
byte. Il pilot video rileva ingressi ancora troppo lenti (circa 6,6 s Guida e 4,7 s
Opzioni dal primo fade al contenuto); L precedente resta da riprovare.
Il [rapporto UI](ui-1.3.1-validation.md) distingue queste prove dall'accettazione
completa e dall'integrazione delle meccaniche CC, ancora aperte.

Aggiornato al **29 ottobre 2026**. Questo documento registra le modifiche realmente integrate nella **candidata 1.3.0**, che nel gioco è ora identificata come **V1.3**. La 1.2.5 resta la versione pubblicata: questo registro non annuncia una nuova release.

Il confronto parte dalla **1.2.5 di Sacred Gold Plus**, che comprende già modifiche rispetto a HeartGold e ai Pokémon originali. Il dettaglio delle prove è nel [rapporto funzionale Android](android-1.3-dev-validation.md); qui sono raccolti il prima/dopo e il beneficio delle modifiche.

Aggiornamento di continuità del **30 ottobre 2026**: il successore 1.3.1 ha
nuove unità sorgenti revisionate per UI, fondali, font, contenuti e proprietà
della riserva residente, inclusi ridisegno delle righe, testo dinamico, catalogo
bilingue, caricatore e allocatore persistenti e fondali accoppiati della Guida,
con correzione verificata dei contatori degli heap ritirati, pianificatore delle
impostazioni, backend dei pixel con confronti nativi indipendenti e lettore
separato SGG1 della Guida, chiamante residente e ingresso del libro nel menu
di campo verificati, descritte nel
[rapporto dedicato](ui-1.3.1-validation.md). Non sono ancora installate nelle
candidate 1.3.0 di questo registro; il gate UI, le prove Android dopo la modifica
e l'accettazione dei vecchi save restano aperti. I numeri delle voci qui sotto
continuano quindi a descrivere la V4, non il compilatore successore.
L'ultima correzione sorgente distingue la perdita del fuoco del libro
dall'annullamento del tocco: conserva l'armamento durante il menu inattivo,
senza cambiare B/X o l'attivazione nativa. Revisione e 27 test mirati passano,
con tre regressioni ripetute dall'integratore. La ricostruzione e la prova
reale restano necessarie: nell'ultima candidata provata le Opzioni si aprono,
mentre la Guida ancora no.
La successiva diagnosi corregge il limite usato per la tabella nativa dei file:
la tabella appartiene all'arena di sistema, non allo heap delle applicazioni.
Il controllo mantiene allineamento e proprietà; 17 test distinti e revisione
passano. La nuova copia IT apre realmente la Guida e torna alla mappa con B
sul banco nativo, con save invariato. La riprova Android resta da eseguire;
questo risultato non chiude navigazione completa, persistenza o prestazioni.
La successiva riprova su melonDS Android passa anche il percorso base IT:
Opzioni con selezione, Guida sopra e comandi sotto, categoria Allenamento e
ritorno alla mappa. Save ospiti e originale restano invariati dopo uscita
normale senza SAVE/Applica. Navigazione completa, EN, persistenza dopo SAVE e
fluidità rimangono da validare; le attese delle catture non misurano latenza.
Il banco Android ha una prima prova funzionale su V4 IT, limitata a Continua
e trasporto degli eventi; non certifica prestazioni o nuova UI. L'aspetto
provvisorio delle impostazioni è stato respinto. La revisione HGSS `71d0ecc`
implementa cornici colorate, gruppi e selezione più evidenti e supera i confronti
nativi mirati; il costo CPU totale cresce e deve ancora essere misurato su
Android nella UI composta. Non è installata nelle candidate V4.
L'ingresso successore del libro passa 23 test mirati EN/IT e revisione:
corregge nei casi preparati il fuoco precedente e la gestione di A/touch/B/X.
Rientra nella partizione residente adeguata nello stesso spazio già riservato;
non è ancora installato né verificato come interfaccia completa nel gioco.
Il successore privato del banco di misura passa 38 test nativi/Python e
revisione, inclusi associazione delle misure e proprietari dei sette heap;
non è ancora una prova Android o una modifica alle ROM di questo registro.
Il chiamante `f2aa567` mantiene inoltre l'autorità dello heap dopo il rilascio
dell'applicazione: revisione e prove native coprono attese e rifiuti di pulizia.
Anche questo componente deve ancora entrare nella UI completa.
Il controllo preliminare `730832e` supera revisione e 17 test mirati, verificando
contesto, font e produttori nativi senza modificare i loro stati. Resta un’unità
sorgente: l’installer e le prove sui percorsi reali sono ancora necessari.
La Guida `58eab41` implementa nei sorgenti lettura sul display superiore,
comandi sul display inferiore e stati visivi distinti, con nove testi aggiunti
senza cambiare gli ID precedenti. La revisione corregge un caso di titolo lungo
con spazio iniziale. La scena `3b489a8` corregge il rilascio touch durante il
ridisegno e il rifiuto temporaneo dell’ACK della sospensione, con revisione e
cinque test mirati dell’integratore. Installer e misure Android restano aperti:
nessuna di queste modifiche è ancora nella candidata V4.
Il seguito privato del banco di misura supera revisione e prove ARM64 sul Mac,
compresa la gestione della distruzione senza tracciamento. Il suo APK successore
è ora compilato e revisionato, ma non installato. Il distinto test sintetico
Android si ferma sul controllo iniziale dello stack, prima del worker: diagnosi
e prove nel gioco restano aperte. Nessuna candidata ROM cambia per questo test.
L’installer `4d71e43` compone e verifica la nuova UI EN/IT in memoria,
preservando gli originali. Revisione, 23 test dei contratti e prove canoniche
separate coprono anche le correzioni del compilatore e dei suoi limiti disco.
Il modulo completo occupa 63.244 su 65.536 byte. Banco persistente, avvio nel
gioco e accettazione Android restano da completare: non è un aggiornamento
installato nelle candidate V4.

Il banco `0489f4f` integra poi lo stage UI, con revisione e 83 test mirati,
inclusa la protezione dei file storici durante l'ammissione. La prima copia
persistente italiana coincide con i byte già verificati in memoria e conserva
gli originali. Rimane una candidata di prova: nessuna promozione o accettazione
Android, prestazionale o dei salvataggi è implicita nella costruzione.
La prima prova reale Android avvia questa copia e carica il vecchio save,
ma OPZIONI torna alla mappa dopo una transizione nera senza mostrare la UI.
Il difetto è conservato per la diagnosi; tutti i save verificati restano
invariati. Guida, persistenza e prestazioni non sono ancora accettate.
Il rifiuto è stato isolato nel controllo display: D mantiene la mappatura
hardware dopo il rilascio WVR. La correzione riconosce quello stato ritirato
senza modificare la banca e ricontrolla la coerenza prima di pubblicare un frame.
Revisione e prove mirate passano; modulo di 63.388 byte entro il limite.
La nuova prova Android e la misura del lavoro aggiunto restano necessarie.
La riprova effettiva di `5a0a6de`, con lo stesso APK, conferma ingresso nelle
Opzioni blu HGSS, spostamento della selezione e annullamento con B. La Guida
torna invece alla mappa senza aprirsi: il test composto resta fallito.
Save invariati; persistenza, prestazioni e accettazione finale ancora aperte.


## Ultimo controllo UI — 30 ottobre, dopo la revisione Pokéball

Implementazione e revisione indipendente della UI completate nei sorgenti.
La candidata IT `97ec6430…175379` mostra la nuova UI su melonDS Android;
Guida, pagina Allenamento e ritorno al campo verificati, save invariati senza
SAVE/Applica. Il confronto dei PNG conferma il fondale inferiore invariato
nelle viste stabili. Restano controlli completi EN/IT, persistenza e prestazioni. Le meccaniche CC non sono ancora
composte in questa ROM. Dettagli e identità nel
[rapporto UI](ui-1.3.1-validation.md). Nessun via libera alla release o al push.

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
| Identificazione | Etichetta 1.2.5 introdotta nella versione pubblicata. | Etichetta V1.3 nel titolo e nelle impostazioni Plus; nome Pokémon Sacred Gold Plus nella libreria e icona originale conservata; build e verifica dedicate alla candidata. |

## 1. Guida di campo e interfacce

La nuova Guida usa lo spazio libero del menu di campo e mantiene font, cornici, palette e comandi coerenti con HGSS. È distinta dalla guida EV/IV già presente nella Summary.

| Categoria | Voci |
|---|---:|
| Evoluzioni | 229 |
| Strumenti e MT | 156 |
| Eventi speciali | 38 gruppi |
| Allenamento | 6 argomenti |
| Totale | **429** |

Le liste mostrano cinque righe, usano i pulsanti e consentono salti di cinque
voci con L/R. Il touch del display inferiore è intenzionalmente inerte nel
contratto corrente. I dettagli sono divisi in pagine; i collegamenti aprono la
voce pertinente e il ritorno ripristina pagina e posizione di partenza. I
paragrafi brevi restano uniti. La cache temporanea del font riduce le letture
ripetute durante la navigazione; viene rilasciata all’uscita.

Il menu Options offre un accesso Plus visibile oltre a SELECT. Plus mantiene le cinque impostazioni precedenti e aggiunge descrizioni contestuali, colori di selezione nativi e la seconda pagina Shiny. Annulla e Applica gestiscono il cambiamento delle due pagine; le Options native conservano la propria conferma. Il rientro ripristina l’anteprima nativa della velocità del testo, con gestione del testo ancora in stampa.

Le osservazioni sulle interfacce V4 e le revisioni successive conservano
identità e limiti nel [rapporto UI](ui-1.3.1-validation.md).

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

Il successore 1.3.1 corregge anche la contabilità delle due copie delle
impostazioni Plus: un errore di entrambe le scritture non viene più dichiarato
come record valido, mentre una sola copia riuscita resta recuperabile ed è
segnalata come ridondanza parziale. Al riavvio viene scelta la copia valida con
la generazione più recente, così una A vecchia non nasconde una B aggiornata.
Il formato del salvataggio non cambia.

La Ball che segnala una specie già catturata viene mostrata anche nelle lotte contro gli allenatori, usando il Pokédex. Questo ampliamento non equivale alla soluzione di ogni vecchia segnalazione di icona intermittente nei selvatici.

## 7. Bug corretti e rifiniture della candidata

| Problema | Modifica integrata | Provenienza e limite |
|---|---|---|
| Il movimento di Mew poteva continuare dopo la distruzione dello script che lo aveva avviato. | Le tre relocation attendono la conclusione del movimento prima di terminare lo script. | Correzione del percorso evento; non prova la soluzione del separato caso Latios. |
| Il chiamante touch di SAVE poteva mostrare successo dopo un rifiuto nativo. | Messaggio EN/IT di fallimento, attesa di conferma A/B/touch, ritorno al campo e possibilità di riaprire SAVE. | Corregge il feedback; un rifiuto persistente resta un salvataggio non riuscito. |
| Flag evento alti potevano sovrapporsi alla Rubrica Amici, come nella cattura Mew verificata. | Area dedicata, importazione conservativa dei bit precedenti, controlli all’avvio e identificatori degli eventi mantenuti. | Corregge la sovrapposizione futura; non ricostruisce dati eventualmente corrotti in passato. |
| La nota inglese della migrazione superava la larghezza della finestra. | Testo ridotto da 218 a 193 pixel nei 204 disponibili; italiano già valido e invariato. | Correzione del testo, senza azzerare le impostazioni per farlo apparire. |
| Un servizio Training già attivo poteva applicare EV e addebitare denaro prima di un successivo SAVE rifiutato. | Nuovo controllo della destinazione prima dei servizi mutanti; conferma rifiutata invalidata e messaggio corretto. | Difetto emerso durante lo sviluppo del nuovo Training della 1.3, assente come servizio nella 1.2.5. |
| I primi due rematch di Wade erano ordinati 52→46 per una discordanza fra selettore e record squadra. | Scambio confinato dei soli record squadra 460/461, così l'ordine effettivo diventa 46→52→68. | Verificato staticamente e sulle candidate EN/IT in memoria; restano il percorso telefonico giocato, SAVE/cold e dispositivo. |
| Le forme alternative dei Pokémon degli Allenatori conservavano statistiche e, in alcuni casi, abilità della forma base. | L'helper condiviso aggiorna abilità e statistiche dopo l'impostazione della forma, coprendo tutti i formati squadra senza cambiare save o archivi. | T0–T3, forma 0, Horton Rotom Fan e i due slot delle forme Wormadam passano nel componente ARM9 EN/IT; restano battaglia naturale, SAVE/cold e dispositivo. |
| Conversione2 ignorava il tipo Folletto e Ferropalla/Gravità potevano conservare erroneamente l'immunità Ground→Flying. | Il helper di Conversione2 usa tutte le 325 righe moderne e i due consumer grounding leggono le colonne della stessa riga moderna indicizzata dal danno. | Esecuzione ARM, replay e catena completa EN/IT passano con controlli Fire, Ground→Veleno e Fairy→Drago; restano battaglie naturali, SAVE/cold e dispositivo. |
| Fire Fang poteva ignorare Wonder Guard quando non era superefficace; lo stesso off-by-one ometteva Shadow Force dal gate a due turni. | L'immediato seleziona l'effetto 272 di Shadow Force invece del 273 di Fire Fang; cambia un solo byte nell'overlay 12. | Otto Plus EN/IT e 512 esecuzioni native sui due consumer passano; restano lotta renderizzata, SAVE/cold e dispositivo. |
| La chart danno Plus trattava Spettro→Drago come poco efficace e Spettro→Buio come neutro. | Scambiati i soli due moltiplicatori errati in overlay 18; le altre 322 coppie restano identiche. | Sei immagini EN/IT autenticate e replay del producer passano; restano lotta naturale, SAVE/cold e dispositivo. |
| Mantyke, Feebas, Burmy femmina e Combee femmina avevano parametri evolutivi errati. | Corrette soltanto specie/soglie nei quattro record; la Guida viene generata dalla stessa delta. | Composizioni UI EN/IT e controlli statici passano; restano evoluzioni naturali, SAVE/cold e dispositivo. |
| Franz cancellava il lotto completato anche quando la Borsa rifiutava le Ball. | Il risultato del controllo spazio porta al messaggio esistente e conserva il lotto; la cancellazione resta solo dopo la consegna. | Modello bytecode EN/IT e mutanti passano; restano dialogo, SAVE/cold e dispositivo. |
| Parlare lateralmente a Kate prima della sua sfida mostrava il dialogo post-lotta e ne alterava l'orientamento per il successivo trigger. | L'entry oggetto distingue ora stato prima delle sorelle, pre-lotta, premio pendente e stato concluso, riusando i percorsi esistenti senza cambiare evento o save. | Membro 237 EN/IT, quattro stati, controllo verticale, confinamento e replay passano; restano scena renderizzata, follower, SAVE/cold e dispositivo. |
| Con Lettore GB attivo, il Summary aperto durante l'apprendimento dopo un'evoluzione sfrattava la sequenza audio GB senza ricaricarla. | Un wrapper conserva l'helper nativo e richiede di nuovo la sequenza evoluzione solo quando GB Sounds è attivo. | Candidate EN/IT, replay Thumb-1 indipendente, ABI, confinamento e composizione passano; restano PCM/UI naturale, accetta/rifiuta/annulla, SAVE/cold e dispositivo. |
| La copia privata della Borsa ampliata scriveva a indirizzo zero se l'allocazione falliva. | Il costruttore ora restituisce `NULL` prima della pulizia; sul successo azzera ancora tutti i 2.380 byte. | Codice Thumb EN/IT e composizione in memoria passano senza cambiare ingressi o save; restano pressione heap giocata, SAVE/cold e dispositivo. |
| Un errore di scrittura dell'estensione Borsa poteva avanzare il banco nativo lasciando gli slot extra solo in RAM. | Con slot extra vivi, destinazione estranea, doppia scrittura fallita o flash illeggibile fermano il commit nativo; estensione vuota e una copia verificata restano salvabili. | Composizione ARM 14/14 e identità/ABI 5/5 passano; restano copia raw, SAVE/cold, catena completa e dispositivo. |
| Una destinazione flash estranea poteva far perdere i 108 slot extra dopo un save nativo apparentemente riuscito. | Il coordinatore blocca il commit se trova slot extra vivi; l'integrazione finale conserva tutti gli ingressi Training e usa una guardia confinata nel margine. | Riproduttore e controlli negativi passano EN/IT; restano SAVE/cold raw, UI del fallimento e dispositivo. La regressione ABI scoperta durante la prima integrazione era della pipeline, non di una ROM pubblicata. |

La Guida e le nuove pagine Plus hanno inoltre ricevuto controlli su apertura/chiusura, annullamento, risorse temporanee, paginazione e convivenza con la preview delle Options. Sono rifiniture delle funzioni nuove, non nuove opzioni di gioco.

Il cap oltre 100 non fa parte della candidata: il valore riservato è 150, non
140, ma loader, EXP, Caramella Rara, Pensione, Training, Box e learnset restano
al limite 100. Non va presentato come funzione già disponibile o come semplice
flag da attivare; richiede un filone separato con migrazione save, curve 101–150,
confine 127→128, statistiche, acquisizione/scambi e scaling avversari.

## 8. Continuità dei salvataggi e strumenti di sviluppo

Il setter delle viste compatte della Borsa ora distingue posizione di
visualizzazione e identità della tasca. Nelle candidate EN/IT il percorso
Berries singolo scriveva l'entry 4 pur avendo una sola entry compatta in
posizione 0; Items e la vista completa mascheravano il difetto. La correzione è
confinata a 32 byte ARM9 più un `BL`, non usa riserva e non cambia Borsa, ROM o
formato save. Le prove sorgente/componente passano; apertura giocata del picker
Berries e SAVE/cold restano da accettare.

Il Numero Loto conservava invece soltanto la metà alta nell'esatta variabile
destinata alla metà bassa, lasciando invariata la variabile alta. La
correzione `lottery-id` ritargetta il secondo caricamento verso il literal
0x403D già presente nel getter adiacente: cambia fisicamente un solo byte del
codice ARM9, senza spostare codice o cambiare il formato del salvataggio. Le
12 sequenze EN/IT coprono sei ID, tre cambi giornalieri RNG e tre controlli di
confinamento/rifiuto; il
cambio giorno e la consultazione del premio in partita, SAVE/cold e dispositivo
restano da accettare.

L’aggiornamento conserva identificatori e layout nativi dei Pokémon, impostazioni Plus e dati della Borsa ampliata. I nuovi servizi usano un archivio separato, versionato e controllato, con verifiche prima della scrittura: dati estranei o futuri non vengono sovrascritti come se fossero vuoti.

Non è richiesta una nuova partita. Le prove includono copie EN/IT senza Plus, con impostazioni Plus, con Borsa ampliata e con corsi attivi nei salvataggi intermedi di sviluppo. Questi ultimi sono casi di migrazione interna della 1.3, non corsi già presenti nella 1.2.5. La compatibilità verificata è in avanti: il ritorno a una ROM precedente non è una migrazione inversa garantita.

Sul lato sviluppo sono stati aggiunti:

- un builder separato che parte da immagini 1.2.5 identificate dall’impronta, con controlli sui dati prima e dopo ogni modifica;
- un registro delle aree di memoria riservate e verifiche delle integrazioni;
- ricevute di build con impronte, versione degli strumenti e sorgenti usati, senza sovrascrivere gli output esistenti;
- modelli probabilistici condizionati e test delle regole, affiancati da esecuzioni del codice ARM installato;
- una matrice funzionale con prove Android e confronti dei salvataggi grezzi dopo SAVE e riavvio completo;
- una guardia del banco melonDS che confronta l'intero checkout con il commit fissato e ripete il controllo al configure e a ogni build del core, senza fidarsi di flag dell'indice, `git status` o replace ref;
- una snapshot autenticata dei reference ZIP: gli stessi byte pin-nati vengono letti dal packager, senza riaprire un pathname sostituibile;
- una delta immutabile del modulo rivincite derivata dalla V4 e condivisa da writer, reader, peel e attivazione, così i producer legacy precedenti non vengono scambiati per preimmagini corrotte;
- un downloader stadio 0 che richiede una cartella privata, limita manifest, delta e durata e pubblica delta/ricevuta da temporanei esclusivi no-follow, senza poter seguire symlink verso file esterni;
- controlli sui nomi portabili dei membri ZIP e limiti della decompressione selezionata (8 MiB per membro, 32 MiB totali, STORED/DEFLATED), verificati sui reference reali EN/IT;
- una snapshot privata di RomPatcher.js ricostruita dagli oggetti del commit pin-nato, così file non tracciati, modifiche nascoste e sostituzioni del working tree non entrano nel decoder Node;
- un controllo del compilatore effettivo prima di avviarlo, con percorsi protetti e ambiente ristretto; prove locali superate, compatibilità del pin con la CI ancora da verificare;
- l'oracolo del test Portable dopo UI aggiornato allo slot vuoto lasciato dal ritiro della vecchia Guide, con composizione EN/IT e rifiuto di un byte corrotto verificati;
- pulizia degli intermedi di build e conservazione limitata delle build operative, mantenendo ingressi ed evidenze.

Il builder e i file della release pubblicata 1.2.5 restano separati da questo percorso di sviluppo.

## 9. Verificato, ereditato e ancora fuori dalla copertura

La campagna funzionale documenta **49 checkpoint accettati**: 45 con SAVE e riavvio completo e quattro con rifiuto e file intero conservato. Sono distribuiti fra candidate successive; il [rapporto](android-1.3-dev-validation.md) identifica gli hash e spiega quali prove si trasferiscono sui componenti rimasti identici.

L’ultima esecuzione completa comprende **37 suite Class A, 809 esecuzioni riuscite e 52 skip**. Sono separati gli 86 controlli del codice installato, le 76 migrazioni in RAM e i controlli Class B, con i rispettivi limiti. I numeri non si sommano come se fossero tutti test diversi o tutti playtest Android.

Su Android sono stati osservati, fra gli altri, modifica e persistenza di statistiche/IV/EV, uso di vitamine e bacche, servizi e corsi, catture Classic/Pro, catena e Search, Guida, Plus, Mew e scene di boss. Tecnico è stato acquisito normalmente e verificato dopo PC→squadra→SAVE→riavvio; il suo effetto numerico e il comportamento di Alternacura hanno prove ARM. Non sono state giocate 493 battaglie, tutte le combinazioni dei servizi o un’intera nuova avventura; le due scene boss finali sono prove UI senza SAVE della vittoria. La verifica del dispositivo fisico e delle sue prestazioni resta distinta dal banco Android Software 1x.

La [verifica su dispositivo fisico e della candidata V1.3](device-1.3-validation.md)
aggiunge prove su copie di un vecchio save IT con squadra, box, Plus e Borsa
espansa. Il confronto completo delle ROM EN/IT conferma che la revisione visiva
v4 cambia solo nome del banner, testi della versione e pixel dell’etichetta;
il codice di gioco e di salvataggio rimane identico alla v3. Il salvataggio
personale originale non viene sostituito dalla copia usata per le prove.

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
