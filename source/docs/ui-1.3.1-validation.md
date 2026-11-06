# Verifiche delle unità sorgenti UI 1.3.1

## Successore input nativo — 6 novembre 2026

| Lingua | SHA-256 successore | Byte |
| --- | --- | ---: |
| EN | `185dc5c53a75652c021ced65157e1c3388cd661ebe90775e5b49314aee753b08` | 152786376 |
| IT | `b68ddd5691538c3895b75f3f20db5a163b2bd8376629f59d2a9d55dc05935bce` | 159029292 |

L'analisi del codice identifica `heldKeys` letto come nuova pressione. Il fix
legge newKeys e newAndRepeatedKeys ai campi nativi corretti, conservando i timer
iniziali/continui del gioco. Il confronto completo EN/IT distingue dieci byte:
due immediati LDR nell'overlay 54 e due parole CRC32 Module96. Gli altri 512 file
NitroFS, le attivazioni e tutto il payload Portable restano byte-identici.
La retroproiezione integrale coincide con gli hash inerti misurati del
checkpoint seguente. Il gate chiuso [input_lineage.py](../sgp131/input_lineage.py)
registra questa sola derivazione statica: `runtime_acceptance: not-run`.

Nessun nuovo test locale o ciclo di gioco, input timing, SAVE o cold Continue è
stato eseguito per questo successore, su richiesta esplicita del maintainer.
Non si trasferisce l'accettazione runtime dei vecchi hash ai nuovi. La CI e i
readback di compilazione/ricostruzione pacchetti restano controlli distinti.
I rapporti storici sottostanti sono conservati con le rispettive identità.


## Candidata freeze battaglia — 6 novembre 2026

| Lingua | SHA-256 candidata formale | Byte | Owner runtime attivi |
| --- | --- | ---: | --- |
| EN | `50ba570f97655cecc7b11bed06eb7f683283b191c1c21f02e49ad55f90fc7665` | 152.786.376 | `portable` |
| IT | `c63cf9e993cbee9c38949baf9444dda3e365bddb15840aaa08905d9b02afbedb` | 159.029.292 | `portable` |

Le build formali da V4 coincidono byte per byte con le trial misurate.
Il gate di attivazione Box usa catture fresche legate alle nuove immagini:
EN e IT completano Continua→campo→Squadra→R→PC nativo in 4.332 frame.
Non è una nuova misura di latenza. Controlli Summary e rivincite restano
inerti. Nel ciclo nativo di efficacia, venti casi EN/IT falliscono sul vecchio
rientro a metà BL e passano dopo la correzione del ramo. Stack, registri,
flag attesi e ingresso singolo nel payload sono verificati. Il readback
rifiuta il ramo precedente anche quando l'hash esterno viene aggiornato.
Sul dispositivo fisico Android 13, melonDS profiling 2.1.9/50 con JIT e renderer compute
6x già configurati, l'esatta IT completa su copia raw Continua→campo→SAVE
nativo→arresto processo→cold Continue. Il confronto conserva Pokémon,
inventario, impostazioni e progressi; i delta nativi osservati sono espliciti.
Una successiva battaglia su quella copia supera Weavile e Honchkrow e il
primo turno contro Houndoom, poi riapre il menu mosse. Non è una vittoria
completa sulla Lega né copertura fisica EN. La ROM ufficiale IT è sostituita
in luogo, a percorso e nome invariati: hash del save corrente identico prima
e dopo la sola installazione, poi Continua→campo osservato senza nuovo SAVE.

La matrice host fresca usa due fixture autentiche, ciascuna su entrambe le
lingue: un save iniziale senza Plus e un backup 1.2.2 con impostazioni Plus,
5 Pokémon in squadra, 113 nei box e tre slot Borsa oltre il limite retail.
Tutti e quattro i cicli Continua→SAVE nativo→nuovo processo→cold Continue
passano il confronto semantico protetto; ogni cold export è byte-identico al
proprio SAVE. Gli audit strict iniziali non passano per migrazione HF02,
movimento NPC/follower e bitmap PC: restano conservati, con eccezioni limitate
ai byte pre/post osservati e spiegati dal codice nativo. Non si dichiara
uguaglianza integrale fra input e output. Originali e ROM restano invariati.
Il runtime host è interprete/software con FreeBIOS e RTC fisso; non Android.
Le quattro celle rappresentano due fixture uniche, senza save avanzato EN
indipendente, no-Plus avanzato, TNR1 attivo o prova del 252° slot Borsa.
La suite globale raccoglie 2.988 test senza fallimenti: classe A 2.099
raccolti, 2.046 eseguiti e 53 saltati; classe B 889 raccolti, 581 eseguiti e
308 saltati. I salti dipendenti dalle fixture restano scoperti. Il codice
del gioco resta stabile durante il run; le modifiche documentali e del
contratto di distribuzione intervenute nel frattempo sono coperte da un nuovo
run separato di tutti i 32 test distribuzione sul contratto finale
`4b2edbf3648050bedd2287a30f11d3ea1a6e078e195515c731a85a3df69ced32`.
I tre controlli CLI e le due ricostruzioni V4 del bootstrap sono ulteriori
prove, non aggiunte retroattivamente a quel totale. Le 100 ricostruzioni patch
e le 42 pagine PDF sono registrate nel [rapporto pacchetti](package-1.3.1-validation.md).
I checkpoint sottostanti conservano le identità e i limiti originali.


## Candidata HG-T10 e smoke Android su Mac — 5 novembre 2026

| Lingua | SHA-256 candidata corrente | Byte | Owner runtime attivi |
| --- | --- | ---: | --- |
| EN | `02cccfbfc49b6addddba90385634ffdfde22b9ff3fbae3d85ae8f5603c5bf0af` | 152.786.376 | `portable` |
| IT | `35d459e3fcf7cf127d6ff0aec94a5f502accfce390b2455b83fe189a5ca088f4` | 159.029.292 | `portable` |

Il nuovo stage `legendary-scene-version` segue `legendary-scenes` e precede
`trainer-fixes`. Corregge tre seam dell'overlay 2: la scena Lugia in mappa 244
seleziona la versione 8; Ho-Oh e le altre mappe mantengono la 7. Il delta resta
nel medesimo slot compresso da 42.700 byte, senza cambiare FAT/y9, geometria
ROM, riserva residente o layout save.

Le prove runtime sintetiche sulle nuove EN/IT osservano tutti e tre i consumer
Lugia con valore 8; il controllo Ho-Oh EN mantiene 7 nei due consumer pertinenti.
Il gate coordinate è quello nativo, poi lo script parte dal seam nativo
`StartMapSceneScript`; progressione e posizione sono predisposte nel debugger
soltanto in RAM. ROM, fixture originali e copie raw restano invariati.
Le evidenze private sono
`local/experiments/ds-campaign-hg-t10-fullchain-2026-11-05/`:
`post-fix-EN-lugia.json`, `post-fix-IT-lugia.json` e
`post-fix-EN-hooh-control.json`. I run usavano immagini temporanee con gli hash
indicati, senza attestare da soli una composizione formale. Il mismatch è
corretto nei percorsi osservati; freeze storico, raggiungibilità naturale,
scena completa, battaglia/cattura/cleanup, persistenza e dispositivo fisico restano fuori
da questa prova.

Un nuovo smoke dell'esatta IT su melonDS Android nell'AVD sul Mac mostra
Continue→campo→Squadra→R→Box nativo→campo. La cattura del Box ha SHA-256
`ef4e647d1ce65f42e4bf2b0f309cde7405a956123ca768fca3b9f31d0f20572a`.
La copia raw esportata coincide con la fixture originale a
`553925da5f1814b3ebba587f383b4197381d5bc040ba7b8d8208c1ca8a7fb3ce`;
nessun SAVE è stato eseguito. Il registro privato
`local/notes/codex-1.3.1-closeout/android-hg-t10-smoke-2026-11-05-01/END.json`
chiude la sessione senza errori, con i file guest protetti preservati e senza
verdetto automatico di accettazione. Lo smoke dimostra il percorso del Box
sul nuovo hash IT; i cicli SAVE/cold, i conteggi delle suite e l'accettazione
delle sezioni storiche sottostanti conservano i propri hash. La candidata
corrente non è installata sul dispositivo fisico e l'accettazione completa resta aperta.

## Checkpoint storico portable-only e prove Android su Mac — 5 novembre 2026

| Lingua | SHA-256 candidata formale | Byte | Owner runtime attivi |
| --- | --- | ---: | --- |
| EN | `5c5611844678d26bdc5677855da3aacbc1dd1700f97afec249b24532f2362f15` | 152.786.376 | `portable` |
| IT | `c5a45d169e04fd85f17889f201ba7c6fe6f5d4ad43243b6a043a5ab848777f97` | 159.029.292 | `portable` |

Le ricevute di composizione indicano `controls` e `rematches` inerti e il solo
Box portatile attivo. I quattro word di attivazione del Box sono l'unica
differenza rispetto alle rispettive immagini tutte inerti; azzerandoli si
riottengono esattamente EN `8ed686d2…92b20` e IT `7a29903a…04df3`. Gli output
formali sono byte-identici alle trial manuali già usate dai test runtime.
Una ricostruzione indipendente del 5 novembre, in un workbench privato nuovo,
parte dalle due V4 e dagli input autenticati correnti e produce di nuovo gli
stessi hash e le stesse dimensioni; `cmp` conferma l'uguaglianza byte per byte
con entrambe le candidate formali.

Nel banco headless EN e IT raggiungono Squadra con il comando «R: Box», quindi
il PC nativo (`PC_RUNNING`) in 4.332 frame. Le copie save di ingresso e la
fixture originale restano a
`553925da5f1814b3ebba587f383b4197381d5bc040ba7b8d8208c1ca8a7fb3ce`.
La candidata IT esatta è stata poi avviata in melonDS Android nell'AVD
Android 13 arm64: cold startup, Continue, campo, Squadra, R, Box nativo e
ritorno al campo risultano visibili nelle catture del run privato; non viene
eseguito SAVE in questo primo ciclo.

Un secondo ciclo separato usa ancora una copia: Continue, campo, SAVE nativo
con conferme, arresto e riavvio del processo senza ricaricare la fixture,
Continue e campo. Le esportazioni dopo SAVE e dopo cold load sono entrambe di
524.288 byte e hanno SHA-256
`93a943120c05f18b336cce9f5049c16fb06405aaa44826738cbfd8dd279193db`;
differiscono dall'ingresso come atteso. La fixture host originale e gli otto
file guest protetti restano invariati. I record del controller sono
deliberatamente `no-test-verdict`: il giudizio deriva dalle catture e dagli
hash osservati, non da un'accettazione automatica dell'adapter.

Dopo la ricostruzione byte-identica, un ulteriore run Android isolato sulla IT
appena ricostruita ripete avvio, Continue, campo, Squadra, «R: Box», PC nativo
e ritorno. Cinque catture mostrano le transizioni; non viene eseguito SAVE. Il
save TEST esportato dopo il ritorno coincide con la fixture a
`553925da5f1814b3ebba587f383b4197381d5bc040ba7b8d8208c1ca8a7fb3ce`.
Il controller termina senza errori, conserva gli otto file guest protetti e
spegne il solo AVD posseduto.

Il controllo mirato fresco passa 59/59 test ARM del Box, 26/26 del package,
26/26 sulla ROM e 2/2 nel binding Android. Il runner globale fresco termina
con exit 0: Class A 2.042/2.095 con 53 skip dichiarati e Class B 577/885 con
308 skip, per 2.980 test raccolti e zero failure. Anche le ricevute formali
conservano `runtime_acceptance: pending`: le prove accettano il Box e un ciclo
SAVE/cold su copia, non tutte le funzioni né il pacchetto release.

Il 5 novembre `adb devices -l` non mostra dispositivi. La console fisica non è stata
aggiornata e nessun `.sav`, savestate o cheat fisico è stato toccato. La
procedura conservativa sul dispositivo resta subordinata a riconnessione,
backup fresco verificato e prova della candidata esatta su una copia separata.

## Trial attivo finale e aggiornamento conservativo — 4 novembre 2026

| Lingua | SHA-256 candidata attiva | Byte | Accettazione eseguita |
| --- | --- | ---: | --- |
| EN | `618f0501d1355f5c7ee6d0301847222fd23a3d67701027190424bf28225fb13d` | 152.786.376 | Smoke locale headless |
| IT | `171b53b6c47555d54cb82c724569f26e9dfd92f51aa064545dd44b09179d64a0` | 159.029.292 | Smoke locale, prova fisica isolata e installazione in-place |

Entrambe completano cold boot, Continue, campo e Squadra→R→PC nativo fino a
`PC_RUNNING` nel runtime locale, senza crash in 4.332 frame. La copia save di
ingresso resta byte-identica. Non è un collaudo esaustivo delle funzioni.

Sulla prova fisica IT, una copia raw da 524.288 byte completa
Continue→campo→SAVE con due conferme→cold restart→Continue nello stesso campo:
hash iniziale `67285f…ac11`, hash finale
`e2c6a6f86ec2ff3082a9dfe0519bdd0616847413c230c798f0ce0522a1ea7be9`.
Il save personale non viene mai sostituito. L'installazione canonica conserva
nome, percorso, lingua, associazione e impostazioni e sostituisce soltanto la
ROM `420ec8b8…f059a` con `171b53b6…d64a0`. Save personale
`67285f796c76d0042aadf88839bede46b90d610250773131aab35d3967a2ac11`,
`.ml0` `268023…5801` e configurazioni cheat `587651…be04` /
`cbe23…2fa4` risultano invariati. La ROM canonica viene avviata a freddo fino
al campo senza eseguire un nuovo SAVE. Il backup rollback resta conservato; i
file fisici temporanei sono rimossi. Due sole voci cache inerti, prive di file
fisico, restano nella libreria per la policy fail-closed della nuova build
melonDS e non rappresentano giochi o ROM installati.

La prova non promuove il pacchetto giocatori o una release: EN non è stata
provata fisicamente, le funzioni non sono state percorse tutte e nessun
pacchetto è stato pubblicato.

## Composizione effimera del 4 novembre: statica, non accettata

Il workbench privato ha composto l'albero corrente completo sulle basi V4 EN
`179edfb1…fbf90` e IT `2a2f0b43…3a156`. Le postimage sono EN
`410c3fc8e0a773c7acaf2d3ca3670a2a1109cd94f608e9f1e33dc28aac7a4012`
(152.786.376 byte) e IT
`baa02e5484af47d71357865b64f32743469fcc9b7aa56af0eeb4f328a08cc228`
(159.029.292 byte). Le ricevute registrano lo stesso snapshot di 793 sorgenti,
politica storica della trial `sgp131-resident-11`, stadio `identity`, readback statico positivo e
`runtime_acceptance: pending`; gli hash dei file sono stati ricalcolati e
coincidono.

Questa coppia è una prova di composizione ripetibile precedente all'ultimo
snapshot sorgenti; non coincide con la coppia attiva finale sopra e non è stata
accettata, installata o pubblicata.
Non aggiorna da sola timing, comportamento del Box, controlli Summary,
rivincite, audio, SAVE/cold o dispositivo. Gli output ROM temporanei vengono
scartati dopo aver conservato identità e risultato del banco.

## Confronto con i menu nativi e preparazione dell’update — 1 novembre 2026

Le misure 84/99 appartengono alla configurazione di produzione `64/8/240`.
Una ricompilazione indipendente dei sorgenti correnti produce ancora esattamente
64.728 byte, SHA-256 `62ac98c1…2a8239`, e tutte le 68 dipendenze registrate
coincidono con le ricevute del benchmark. Il modulo da 64.712 byte,
`b036cbee…bf2cb62`, è invece la configurazione ridotta del banco `4/8/240`:
non è un successore sorgente diverso. Le misure restano valide per quell'esatto
modulo, configurazione e ROM pin-nata; non certificano automaticamente una ROM
composta successiva né il dispositivo fisico senza un nuovo confronto AB/BA.

Il successore corrente mantiene la grafica e completa il confronto richiesto
con le altre pagine del gioco. Il criterio distingue ingresso pronto (versione
pubblicata, luminosità comune ripristinata e stato di input ammesso) da cursore
**realmente visibile** nelle catture per frame. Stessa ROM IT, stesso runtime,
fixture raw e pressioni di due frame; nessun cheat, scrittura RAM o savestate.
Per il cursore si confrontano i pixel cambiati del selettore, escludendo le
icone animate native. Una pressione persa non viene accettata come tempo zero.

| Pagina | Apertura, frame guest | Cursore visibile giù / su | Ritorno al campo |
| --- | ---: | ---: | ---: |
| Pokémon nativo | 77 | 5 / 4 | 100 |
| Borsa nativa | 87 | 6 / 7 | 103 |
| OPZIONI corrente | 84 | 7 / 6 | 75 |
| GUIDA corrente | 99 | 7 / 6 | 75 |

Due ripetizioni complete danno gli stessi numeri. Il cursore delle nuove UI
rientra nell’intervallo nativo osservato, 4–7 frame. OPZIONI apre in circa
1,4 secondi guest; GUIDA in circa 1,65, ancora 12 frame (circa 0,2 secondi)
più della Borsa. Il caricamento non è identico fra tutte le pagine. Questi
risultati documentano una reattività comparabile, **non una misura fisica
Android**. La chiusura conserva i display sincronizzati.

La ripetizione con lo stesso criterio sul precedente IT `420ec8b8…f059a`
misura OPZIONI 277 frame, cursore 91/90; GUIDA 411, cursore 61/37.
La prima ottimizzazione IT `c87bb9af…fd90` misurava ancora 107/129 frame
di apertura e 12 per il cursore in questo copione. Il miglioramento finale
è quindi verificato sul gioco completo e sul risultato visivo, oltre che
sul numero di chiamate del banco. Il precedente 410 per GUIDA sotto proviene
dal copione iniziale: non viene sostituito o spacciato per la stessa misura.

Il profilo ha isolato ulteriori scansioni vuote, controlli font duplicati
all’interno della medesima chiamata e rasterizzazione del fondale per coppia
di pixel. I painter ora ammettono la lista finita insieme, saltano in blocco
gli elementi invariati, puliscono al massimo quattro righe per passo e
caricano intervalli contigui. OPZIONI scrive le linee omogenee dei tile con
parole allineate, conservando i nibble dei bordi; la freccia visita soltanto
i propri pixel. I controlli di destinazione condividono un censimento heap
locale nello stesso gruppo sincrono, senza cache fra chiamate. Le API font
pubbliche continuano a verificare tutto; i soli painter riusano il controllo
appena concluso, senza attraversare chiamate native o confini di scheduling.
Budget glifi ancora 8, nessuna nuova allocazione per frame.

I reader usano il limite già ammesso di 16 passi, cedendo su attese e chiusure
fallite; pool, BG, ingresso e piano attraversano insieme la preparazione
sincrona, conservando ammissioni e rollback e cedendo prima del primo disegno.
Il CRC spedito resta quello con tabella da 64 byte. Nessuna capacità o guard
è stata aumentata: dynamic54 di produzione misura **64.728/65.536 byte**,
con 808 byte liberi e BSS zero. La configurazione ridotta `4/8/240` misura
64.712 byte e non è quella usata per i timing. Nel
confronto nativo con configurazione 64/8/240 il picco osservato è 2.884.197
istruzioni per OPZIONI e 3.016.232 per GUIDA; stack massimo 2.216/3.120 byte,
entro il canary di 4.096. Sono istruzioni del banco, non limiti di durata
garantiti sull’hardware.

### Identità del checkpoint privato del 1 novembre, ora superato

| Lingua | SHA-256 ROM attiva di prova | Byte |
| --- | --- | --- |
| EN | `1ad993585702aa4c2ab7878679158c36eb3c1c20a85f5a32f3bf50f8195ad07d` | 152.544.720 |
| IT | `1f39ede6c638f1ec28cc15886613547776460b1d0f2fbd2c0ebb0e1fb4b7f479` | 158.787.732 |

Composizioni inerti EN
`86fcd2709dac3aeb1f2deaf0680c7d3faaa1cfe01208016b77a43d999793a581`, IT
`cc639dd24e7267ef26553e664796ca87f1461b4769714f371e191e74ecdeef97`.
Composizione completa riletta indipendentemente e sole sei attivazioni
preesistenti, con roundtrip esatto all’inerte. La ricompilazione dopo gli
aggiornamenti ai soli test mantiene gli stessi byte; le ricevute vengono
rigenerate realmente, non aggiornate artificialmente.

**Grafica e sicurezza:** 18 scene native GUIDA EN/IT e 16 configurazioni
OPZIONI fra viste e parità coincidono con i riferimenti indipendenti, inclusi
pixel, tilemap e palette. Il confronto con il codice precedente conserva
anche le sei immagini radice/cursore. Passano 57 test heap/font/resource,
compresi corruzione di ogni byte dei gruppi heap, alias delle cinque
destinazioni font e mutazioni successive. Restano invariati i guard delle
singole chiamate e le prove di sospensione/annullamento. Nessun nuovo PASS
globale viene dedotto da questa campagna mirata.

La campagna Scene completa raccoglie 18 test: 16 passano nel primo run;
due aspettative del test erano superate dalla nuova implementazione (fase
intermedia non più esposta fra callback e primo buffer ora copiato invece
che FULL). Le prove corrette ripetono rispettivamente il fallimento di tutte
le nove allocazioni e ingresso/storia/cleanup EN/IT: entrambe PASS. Il run
originario **NON PASS** resta conservato; non viene dichiarato un nuovo
18/18 completo dopo quelle correzioni ai soli test.

**Save:** sulle ROM correnti, cinque copie completano Continua → SAVE normale
→ cold: EN/IT senza Plus, EN/IT con Plus/Borsa espansa e una copia del save
personale IT archiviato `9c0cde6d…fb95c`. Generazione +1 e banca alternata,
SRAM cold identica al SAVE, dati protetti preservati: profilo/progressi,
Pokémon squadra/box/pensione, inventario nativo/espanso, impostazioni e journal.
Originali invariati. Il confronto strict integrale resta **NOT PASS** per
5–7 byte `array10` nei casi EN, 4–6 nei casi IT iniziali, e 5 byte `array0`
più 2 `array21` nel personale. Le ricevute e i limiti restano separati dal
confronto protetto; non viene dichiarata compatibilità universale.

In quel checkpoint era stata preparata una patch IT dalla copia installata
`420ec8b8…f059a`,
50.301 byte, SHA-256
`62bc071f1086e99426858e40a5b14d2222bf882f54db05e05dbebd000bab8d18`:
decodifica e identità finale verificate. Il pacchetto privato contiene patch,
hash, manifest e procedura, senza save o ROM duplicati. L’installazione dovrà
aggiornare il file esistente, mantenendo lingua, basename, percorso,
associazione e impostazioni. Richiede prima un backup fresco del save
realmente attivo e prova su una copia: il save archiviato non sostituisce
quello attuale. La copia di test non deve mai sovrascrivere il personale.
Il dispositivo era assente a quegli audit ADB; **questo stato storico è ora
superato** dall'installazione conservativa del trial del 4 novembre documentata
all'inizio del rapporto.

Evidenze private canoniche: `local/notes/guide-latency-2026-11-01/`, in
particolare `page-timing/`, `compare-normal-64.json`, `update-save-cycles/`,
`guide-compact-artifacts/`, `settings-compact-native.log` e il pacchetto update.
Le sezioni successive conservano le candidate precedenti con i propri limiti.

## Latenza di GUIDA e OPZIONI — 1 novembre 2026

Il maintainer segnala circa sette secondi per aprire la Guida, input molto lento
in entrambe le nuove interfacce, fuoco residuo su Opzioni/PokéGear e ritorno dei
due display sfalsato. Il vincolo è conservare aspetto e disposizione della UI.

La diagnosi trova scansioni ripetute e quadratiche della topologia heap, una
doppia verifica identica per ogni destinazione del font, preparazione dei file
frammentata in molti turni e ridisegno completo del buffer nascosto anche per
spostare il cursore. Il controllo del fuoco era collegato nel banco nativo ma
**mancava nell’installer**: ora il BL a `0x0225A96E` raggiunge il successore,
con preimmagine, destinazione e inventario degli ingressi riletti indipendentemente.
L’etichetta ereditata è convertita in GUIDA/GUIDE nella sola String temporanea.

I sorgenti conservano ogni verifica di ownership, CRC, font, DMA e versioni:
la topologia usa un censimento locale senza cache fra chiamate; il font elimina
soltanto la verifica duplicata. I reader avanzano entro un limite esplicito,
cedendo su attese, assenza di progresso e confini di durata. La Guida invia una
sola richiesta asincrona per il membro già allocato; la prova nativa del limite
131.072 byte copre completamento, dati troncati, errore e annullamento pendente,
con file e buffer trattenuti fino alla quiete e prefissi/confini invariati.

Per i movimenti senza cornice nativa, il painter copia il front completo nel
buffer nascosto e modifica solo le righe cambiate. Controlla storia/versione,
trasferitore e DMA; rifiuta mappe con palette o tile della cornice. Non alloca,
non modifica il front e richiede ancora l’upload delle righe invalidate prima
della pubblicazione. Le cornici native mantengono il percorso precedente.
Una prova prima/dopo riproduce inoltre il tasto scartato mentre il frame era
già visibile: il ciclo ora ritira l’attesa prima di consumare quel nuovo input.

Il primo successore intermedio IT `e2b9ab41…c5d350a` ha misurato sul runtime
melonDS locale ingresso Opzioni 277→131 frame e Guida 410→193; movimenti
Opzioni 90→23 e Guida 60/37→16/9. Sono frame guest dell’interprete locale,
**non una nuova misura Android fisica**. Questo successore è superato dagli
ulteriori cambi al buffer e al reader: numeri e cinque cicli SAVE/cold su quei
byte restano storici, non sono trasferiti automaticamente alla copia finale.
In uscita, luminosità diversa fra i display per 59 frame prima, zero dopo,
sia per Opzioni sia per Guida. Il ritorno completo resta 75 frame in quel
campione: la correzione sincronizza gli schermi, non elimina il caricamento
nativo del campo.

Il compilatore disponibile è ora Apple clang 21 `clang-2100.4.1.1`. I pin dei
soli produttori 1.3.1 sono aggiornati dopo ricompilazione identica dei 6.402 byte
della vecchia Guida e prova EN/IT dell’installer con 24 alterazioni rifiutate
per lingua. Le verifiche storiche/payload 1.2.5 rimangono invariati. Budget del
font 8 glifi, pubblicazione linea 240; la candidata finale usa 64 passi interattivi,
con massimo 32 per la prima composizione completa. Questi sono limiti di
lavoro, non una certificazione di durata hardware.

Le evidenze private canoniche sono in
`local/notes/guide-latency-2026-11-01/`. La sessione iniziale ADB non trova
dispositivi; nessuna nuova installazione fisica o pubblicazione è implicita.
Il seguito registra separatamente hash e prove della candidata finale.

### Prima candidata ottimizzata e misure ripetute, ora superata

Composizione completa EN/IT, con rilettura indipendente di ogni stadio fino
all’identità finale. La ricompilazione dopo due correzioni ai soli test produce
immagini inerti byte-identiche. Le sei attivazioni già presenti nella prova
manuale precedente sono conservate; azzerandole si recupera esattamente
l’immagine inerte. Non costituisce accettazione dei gate di produzione.

| Lingua | SHA-256 prova manuale attiva | Byte |
| --- | --- | --- |
| EN | `d1cf70b6d1ba6695587a63841a9721a60004b548191dc0b66dd0b53afaaa0795` | 152.544.188 |
| IT | `c87bb9af3492ecc6cf68fff8fe1f14444ca2f7a09bdf2ea39c745cc2fd35fd90` | 158.787.200 |

Hash inerti EN `bb7bf833f62407d3d4a52b44613f2ad33f31b9b1799820bc4df9dbc9d93512b0`,
IT `087ce223426f03f74b31149caee3674618879b7b08e18864fa737027e70237cd`.
Configurazione esplicita del produttore: `schema: 1`, `kind: test-candidate`,
`scene_work_calls: 64`, `scene_glyph_budget: 8`, `scene_last_start_line: 240`.
I precedenti file manuali restano il fallback; nessuna installazione o
pubblicazione di questi nuovi byte è stata eseguita.

La ripetizione usa il gioco reale nel runtime melonDS locale, una copia raw
IT invariata, input fisici simulati e nessun savestate, cheat o scrittura RAM.
Misura da touch/tasto fino alla scena pronta con versione pubblicata e
luminosità comune ripristinata; non è una misura fotografica del display.
Il runtime non scrive il save durante questa prova: l’esportazione resta
byte-identica alla fixture. Sono confrontati il fallback IT `420ec8b8…f059a`
e la candidata IT finale sopra, con lo stesso runtime e gli stessi input.

| Operazione | Prima, frame guest | Finale, frame guest |
| --- | ---: | ---: |
| Apertura OPZIONI | 277 | 110 |
| Apertura GUIDA | 410 | 129 |
| Cursore OPZIONI, giù / su | 90 / 90 | 11 / 11 |
| Cursore GUIDA, giù / su | 60 / 37 | 11 / 11 |
| Ritorno completo al campo, entrambe | 75 | 75 |
| Luminosità diversa fra i display in uscita | 59 | 0 |

Sono rispettivamente circa 1,8 e 2,2 secondi di apertura e 0,18 secondi per
il cursore a circa 60 Hz guest. Non sono tempi wall-clock o Android fisici:
il beneficio sul dispositivo va ancora misurato. Il ritorno nativo al campo
rimane circa 1,25 secondi, ora con gli schermi sincronizzati. Tracce complete
in `runtime-visible/results.json`; schermate dei cursori e del ritorno rilette.

### Verifiche e limiti del successore finale

Il confronto nativo prima/dopo conserva esattamente pixel, tilemap e palette
per radice e movimenti di entrambe le UI. La Guida completa anche il corpus
indipendente di 18 scene EN/IT, incluse pagine lunghe, link e ritorno.
Il corpus esteso OPZIONI è stato interrotto dopo i casi già confrontati;
non viene dichiarato completo. Le nuove prove native coprono copia del front,
rifiuto di DMA/trasferitore/cornice incompatibili, righe ancora da caricare,
lettura asincrona massima con fault e annullamento, input subito dopo la
pubblicazione e ciclo completo delle due scene EN/IT. Margini heap osservati:
75.080 byte OPZIONI e 49.436 GUIDA.

Il modulo completa 19 test, compresi confini di durata e annullamento; i
112 test di registrazione/controls/portable/rematches ripetuti passano. La
campagna globale aveva rilevato l’aspettativa obsoleta sul writer `legacy`
e l’indirizzo del nuovo hook assente dall’inventario del test: entrambi
corretti. La parte nativa globale è stata fermata durante corpus duplicati;
**nessun PASS globale** viene attribuito alla sessione. Nel confronto privato
dei costi, una chiamata GUIDA con budget 64 supera il guard diagnostico di
quattro milioni di istruzioni; la ripetizione usa esplicitamente otto milioni,
senza cambiare guard o gate del prodotto. I limiti di lavoro non dimostrano
una durata massima hardware. Revisione indipendente del diff senza problemi
bloccanti; test, ricevute e limiti restano nel fascicolo privato canonico.

Cinque copie raw completano Continua → SAVE normale → arresto → cold:
EN/IT senza dati Plus, EN/IT con impostazioni Plus e Borsa espansa, più una
copia del save avanzato IT già conservato. Generazione +1, banca alternata,
SRAM cold identica al SAVE; confrontati profilo/progressi, Pokémon di
squadra/box/pensione, inventario nativo/espanso, impostazioni e journal
protetti. Gli originali restano invariati. Le ricevute
`save-cycles-final/results.json` identificano ROM, fixture, SAVE e cold.
L’auditor integrale originale resta **NOT PASS**: 5–7 byte `array10` nei casi
EN, 4–6 nei casi IT iniziali, e 5 byte `array0` più 2 `array21` nel save
avanzato. Questi cambi dinamici non vengono rimossi né trasformati in un
PASS integrale. Il confronto protetto e il riavvio riuscito sono prove
circoscritte, non compatibilità universale o un nuovo collaudo fisico.

## Prova fisica IT e aggiornamento conservativo — 1 novembre 2026

Sulla candidata IT `420ec8b8d5dbf30d209849bf18a439046a666a710656e01966a1f217d70f059a`,
Nightly Android 2.1.6/47: una copia del save attuale con 16 medaglie, 6 Pokémon
in squadra e 248 nei box completa Continua → campo → SAVE normale → arresto
processo → avvio a freddo → Continua → campo. Generazione 201→202, banca 1→0;
SRAM dopo cold identica al SAVE. Profilo/progressi, Pokémon squadra/box/pensione,
inventario nativo/espanso, impostazioni Plus, lavori Training e profilo shiny
sono conservati nel confronto. Il save personale originale rimane byte-identico
al backup fresco; la copia modificata non viene importata sopra l'originale.

Sostituita soltanto la ROM, mantenendo nome/percorso e una sola copia finale
sul dispositivo. Gli altri file protetti restano invariati. Controller/layout
ed impostazioni esportabili coincidono con il backup; le configurazioni dei
giochi restano associate. I cheat storici non sono stati riattivati o convertiti:
la loro associazione era già relativa a una vecchia identità, e la compatibilità
delle scritture non è certificata sulla 1.3.1.

Il confronto strict integrale della copia segnala variabili/seed aggiornati nei
blocchi 4/14/19/21/34 oltre ai tempi ammessi: rimane NON PASS e viene conservato,
separatamente dal confronto dei dati protetti e dal ciclo fisico completato.
Non viene attribuita compatibilità universale, una nuova prova EN o accettazione
di tutte le funzioni, prestazioni e release. Pubblicazione ancora non autorizzata.

## Nuova candidata con correzioni integrate — 31 ottobre 2026

Gli hash correnti includono SG-08/09/15/15b, Ninnananna, Eevee, pesca SG-11
e IGT HG-T09. I file manuali precedenti sotto sono storici e non consigliati
per il nuovo collaudo. Composizione EN/IT completa riletta attraverso gli stadi
UI, moves, AI, abilities, legacy, controls, portable, rematches e identity.

| Lingua | SHA-256 nuova prova manuale attiva | Byte |
| --- | --- | --- |
| EN | `90435d3c3a140774fea773ba16039a7eed8aa262bb5b2377217714b6f8d5fc18` | 152.543.400 |
| IT | `420ec8b8d5dbf30d209849bf18a439046a666a710656e01966a1f217d70f059a` | 158.786.412 |

Composizioni inerti di origine EN
`da235d1ec94550358c6a8aaf21360781b8366b2934d949bb42280021f96585db`, IT
`73044f5eac0cf03d5f623c4f2a867b25c7f09cb28dc724247abf3a0f757e2f12`.
Le sole sei attivazioni booleane distinguono ciascuna prova manuale dalla
propria immagine inerte; azzerandole si ricostruisce esattamente l'hash iniziale.
Nessuna ricevuta Android o accettazione di produzione viene inventata.

**Codice:**253 test mirati PASS in31,046s, zero skip; revisione indipendente
senza problemi importanti. I test includono consumer ARM prima/dopo, caller
Training, archivi, complementi e composizione dei tre fix nativi. Nessun
nuovo PASS globale. Il maintainer ha richiesto controlli brevi e svolgerà
sul dispositivo il collaudo funzionale esteso delle nuove funzioni.

**Controlli locali sulle nuove immagini attive:** squadra e R aprono il PC
nativo EN/IT, registro BOUND1→PC_RUNNING3,1 apertura e0 errori;
9,706s EN e9,732s IT per copione, senza attribuire prestazioni a questi tempi.
Le schermate di squadra/PC sono state rilette.

**Salvataggi:** Continue → SAVE normale → avvio a freddo su copie delle cinque
fixture per lingua: legacy senza Plus, impostazioni Plus, Borsa espansa,
Training attivo e shiny hunt positivo. Aggiunta una undicesima prova IT con
save avanzato, squadra e box popolati. Verificati avanzamento generazione di
uno, alternanza banca, SRAM del riavvio identica al SAVE, profilo/progressi,
Pokémon di squadra/box/pensione, inventario nativo/espanso, impostazioni già
presenti e journal con le migrazioni native dichiarate. IGT e tempo Training
sono confrontati con i contatori realmente letti, non con stime di wall clock.
Nessun originale è stato modificato; nessun savestate, cheat o scrittura RAM.

**Indagine sull'array10:** l'auditor indipendente originale resta **NOT PASS**
in tutte le undici ricevute perché esige identità byte per byte anche per lo
stato degli oggetti mappa salvato dal gioco. Nel codice nativo di HGSS,
`FieldSystem_SyncMapObjectsToSaveEx` copia gli oggetti attivi al SAVE: durante
il normale tempo di gioco cambiano direzione, coordinate correnti e buffer del
movimento. Un follower nel caso hunt cambia il bit `0x20` quando viene chiuso
il movimento; nel save avanzato un NPC cambia insieme il flag
`SINGLE_MOVEMENT` e un byte del buffer nativo. Questi ultimi byte restano
classificati solo per il caso e i valori osservati, senza normalizzazione
generale. I medesimi cambi di NPC comparivano già in un audit Android della
linea 1.3 precedente. Nessun identificatore, script, binding o posizione del
giocatore è cambiato nei casi esaminati.

Una **rivalutazione supplementare circoscritta** applica all'auditor originale
solo gli esatti byte osservati e motivati, dopo aver verificato hash di ROM,
fixture, SAVE e cold e l'unicità dell'errore originale; ottiene **11/11 PASS**.
I test negativi rifiutano cambi a script, altri flag, posizione del giocatore
e transizioni incomplete del buffer. Le ricevute NOT PASS originali rimangono
intatte. Non è stata cambiata la ROM per questo esito: non è stato riprodotto
un difetto di serializzazione. Questa prova campionata non garantisce ogni
vecchia versione o partita; Android, prestazioni e collaudo funzionale completo
restano separati. Le ricevute dettagliate e gli originali restano nell'archivio
di prova privato.

**Due percorsi storici supplementari EN:** copie dei save conservati dalle
prove updater etichettate «retail USA» (`bd4922d5…336042e8`) e «Plus 1.03»
(`6b7995db…7b0a94ca6`) completano anch'esse Continue → SAVE → cold sulla
stessa ROM EN. Generazione +1, banca alternata, dati protetti confrontati e
SRAM cold identica; i rispettivi audit strict riportano solo `array10` (7 e
6 byte) e la rivalutazione limitata ai medesimi campi nativi passa **2/2**.
Sono partite iniziali senza squadra o box: attestano questi specifici file e
percorsi updater, non tutte le partite retail o 1.03, né la loro provenienza
originaria oltre la ricevuta dell'updater. Gli originali sono rimasti invariati.

Gli intermedi inerti riproducibili sono stati eliminati con il workbench dopo
la verifica; ricevute e hash rimangono. Sono conservati i nuovi file manuali,
i precedenti file manuali storici e gli input originali.

Le sezioni seguenti sono evidenza storica, legata esclusivamente ai propri hash.

## Consegna privata per collaudo manuale — 31 ottobre 2026


| Lingua | SHA-256 prova manuale attiva | Byte |
| --- | --- | --- |
| EN | `322bec42d65a613c0f6aed0d48d7b6b90388b7cbc37aea0c5585587aae695b80` | 152.514.228 |
| IT | `82041ecf0535dadcd0d4083fdfafaa29a1ba1da1b78c6e017c34477b3787285b` | 158.757.240 |

Questi hash identificano gli output manuali; gli hash inerti sotto restano le
identità delle prove precedenti. Non trasferire un PASS fra immagini diverse.

Smoke finale locale sugli output attivi EN/IT: avvio a freddo e Continue su
una copia controllata a Fiorpescopoli, squadra ordinaria, pressione R e box
nativo visibile in entrambe le lingue. Il registro passa BOUND1→PC_RUNNING3,
con1 apertura e0 errori. Runtime9,397s EN e9,415s IT per il copione completo;
questi tempi non sono una misura di prestazioni. Il raw di ingresso resta
invariato. Non è una prova Android, di operazioni nel box o di SAVE/cold.

Il maintainer ha richiesto di ridurre le prove e si è assunto il collaudo
funzionale sul dispositivo. L’output attivo è quindi una **manual-device-trial**,
separata dall’accettazione di produzione del workbench. Le sei attivazioni
sono gli unici delta rispetto alla composizione inerte completamente riletta;
il loro azzeramento ricostruisce l’intera ROM inerte byte per byte. Non vengono
create ricevute di prova Android o attive con provenienza simulata.

Sul pending IT inerte sono osservati titolo V1.3.1, Continue, campo, Guida,
Opzioni e riepilogo sul campo stats/EV/IV in Normale e L=A. I quattro overlap
proposti non hanno celle BG4 corrispondenti e i tile955..986 non sono referenziati
in queste sei viste. Il contesto PC e la durata della legenda non sono coperti.
L al punto iniziale del banco non inviava input grezzo; al punto corretto si
misura0x200 e la Guida torna2→1 anche con L=A. Uscita senza SAVE: SRAM identica
all’originale; tutti i salvataggi e BIOS protetti restano invariati.

La suite globale è interrotta rc130 su richiesta, con risultato incompleto.
Tre importazioni della medesima asserzione sugli intervalli UI fallivano per
il nuovo clear della Guida; il controllo ora distingue clear e payload vivi.
Il seguito mirato135+26 passa; le nuove prove ROM catena rivincite4,
attivazione EN/IT2, comandi/box2 e identità1 passano nel runner prima dello stop.
La campagna Android estesa e i dieci cicli save non sono completati e non
vengono sostituiti da test offline. Nessuna accettazione di prestazioni.

Stato al **30 ottobre 2026**, sorgenti accettati fino al commit locale `4d71e43`.
Il mandato e il layout sono approvati. Questo rapporto registra unità
implementate e revisionate; **il gate UI resta aperto**. Non esiste ancora una
ROM 1.3.1 composta e accettata. Le candidate V4 EN/IT identificate nel
[rapporto dispositivo](device-1.3-validation.md) restano gli input immutabili.


## Catena completa del 31 ottobre: candidate inerti, accettazione aperta

Questa sezione aggiorna lo stato corrente; le sezioni precedenti e successive
conservano le identità storiche. Tutti gli stadi sono ora collegati al builder,
con dismissione verificata della vecchia Guida, overlay126 nei seed UI e titolo
V1.3.1. Le funzioni soggette a prove runtime restano disattivate.

| Lingua | SHA-256 candidata completa inerte | Byte |
| --- | --- | --- |
| EN | `15f379ebc7e99ce0ec0daa39a5627ccc3dbf4360601d82f59d7b7201078b76a6` | 152.514.228 |
| IT | `bc566c14050fae3ac7f204e65a63371954b3d7d7fcfb49689bc726cc903b57f1` | 158.757.240 |

Entrambe sono costruite con il workbench canonico fino a `identity`, con
calibrazione UI4/8/240 e configurazione meccanica esplicita inerte. Rilettura,
permessi dei quattro slot e replay della catena sono eseguiti dal builder.
Il banco nativo locale mostra Continue e campo dopo avvio a freddo; entrambi
escono con codice0 e SRAM esportata identica all’originale, senza SAVE.
Il runtime usato ha SHA-256
`0afd2926507f718e739160e7e0f915153ca9ee3653e42875c17a205d6497f942`.

Passano202 test mirati e quattro composizioni complete EN/IT della catena
inerte; la suite globale finale è in corso. Il primo tentativo Android si
ferma prima dell’upload per un requisito del profilo SRAM non soddisfatto.
Non costituisce una prova del gioco né un PASS Android. Restano aperti prove
di attivazione, comportamento funzionale, dieci cicli SAVE/cold EN/IT,
regressioni UI, heap e prestazioni. Nessuna candidata è ancora accettata per
sostituire quella sul dispositivo; nessuna release è pubblicata.

## Revisione visiva del 30 ottobre: sorgenti revisionati, Android parziale

### Prima candidata UI, mosse e AI insieme: smoke Android

La candidata IT `d8a71af2a7a2dbc1cfdff998a1b204ab3f8ccde68fc2cf0bcca0f5eb0c32f115`
(158.302.992 byte) compone UI, Fuocofatuo a 85 di precisione e correzione
AI dopo KO. Due prove builder EN/IT passano in 122,975 s: composizione,
rilettura indipendente, ricevute e percorso solo UI invariato.

Sul medesimo APK `6c6a2d32…1532`, AVD API33 e configurazione UI 4/8/240,
la prova italiana osserva titolo, Continua UMBI (16 medaglie, Pokédex 288),
campo con accompagnatore, apertura Guida, B al campo, apertura Opzioni e
B al campo, uscita normale. Nessun SAVE, Applica o savestate. Tutti tre save
ospiti e originale restano `f61855c8…1df9`; sorgenti congelati invariati.
Sessione 193,896 s prima del cleanup, emulatore e owner terminati, prestito
rilasciato senza errori. La stessa copia di lavoro sostituisce il precedente
pending UI; non è una promozione ad accettazione finale.

Questo smoke non prova l'AI durante una battaglia, la precisione della mossa
nel riepilogo, SAVE/riavvio, EN runtime o prestazioni. Restano aperti L e
l'ingresso lento della UI. Box, regali/uova, comandi, rivincite e abilità
non sono ancora stadi attivi della candidata.

### Successore cornici: prove mirate e nuovo limite temporale

Il painter ripristina bordi/separatori dopo il printer nativo, senza toccare
inchiostro, righe pulite, buffer frontale o schermo inferiore. Prima: 2 regressioni
falliscono su 3 test. Dopo: 5 test pubblici passano; 7 canvas con font originale
(6 IT, 1 EN), inclusi entrambi gli storici parziali e dettaglio invariato, passano.
Due composizioni canoniche EN/IT passano con 20 alterazioni rifiutate per lingua.
Modulo 63.220/65.536 byte (+308), heap e formato UIR2 invariati.

IT `85ac49635ecc1f077fcea20cd9203ac66cb89309b0a75383989e5469c0bbfc48`
(158.302.992byte) su stesso APK 6c6a2d32…1532/AVD API33 e config 4/8/240:
Continua, radice/Allenamento/Giù/Su/dettaglio/R/B, Info Opzioni, selettore e
annullamento osservati. La cornice precedentemente interrotta risulta continua
nei PNG originali; 12 viste conservano lo stesso fondale inferiore. Il tentativo L
non certifica il ritorno: la cattura mostra ancora 2/2, da diagnosticare senza
attribuire subito la causa. Tutti 3 save ospiti e originale byte-identici;
nessun SAVE/Applica. Sessione 373,001 s prima del cleanup, owner/emulatore
terminati, prestito rilasciato, sorgenti congelati invariati.

Il pilot video registra un ingresso ancora troppo lento: primo fade candidato
Guida 1,204789 s, pannello completo 7,804811 s; Opzioni 1,056489 s e 5,806300 s.
Circa6,60s e 4,75 s sono durate visive su un campione, non latenza precisa
dall'input o una regressione attribuibile alla sola cornice. PTS reali da
AVAssetReader, nessun assunto 60 Hz; la clip Guida termina 0,201 s dopo l'arrivo.
Diagnosi caricamento/disegno e calibrazione restano aperte. Il checkpoint
successivo richiede questi tempi risolti, matrice UI completa, EN, SAVE/riavvio
e meccaniche integrate; nessun via libera a push/CI/release.

Le sezioni seguenti conservano i checkpoint precedenti con le rispettive
identità e limitazioni.

La Guida usa il display superiore per contenuti e comandi fisici; sotto
compare lo sfondo statico nativo Pokéball, anche nelle Opzioni. Il touch
inferiore è inerte; il libro nel menu di campo resta apribile con il touch.
Le righe blu HGSS e la selezione chiara con bordo rosso restano; i pulsanti
A/B/X/Y delle Opzioni hanno cornici neutre uniformi e tre pixel prima
delle etichette. Revisione indipendente dei 34 file e prove mirate native
completate; non equivalgono all'accettazione completa nel gioco.

La risorsa UIR2 contiene il fondale nativo ricomposto senza perdita in
3.552 byte. Il limite risorse è 69.632 byte: EN usa 68.040, IT 68.672.
Il modulo dinamico completo usa 62.912 su 65.536 byte; gli heap non crescono.
La Guida elimina quattro allocazioni inferiori, per 46.336 byte di payload.
La prova nativa dell'allocazione massima lascia 8.364 byte liberi nello heap
Guida. Sono budget e prove circoscritte, non misure di prestazioni Android.

Prima: candidata IT `e8d91d38…e24d8`, comandi inferiori della Guida.
Dopo: IT `97ec64302bbb1155ccbb4f6cad1d6cfb23f26047521a8bbf85cd97e2ee175379`,
158.302.708 byte; ricevuta iniziale
`892925df29446ce6687426b71755084ef316671430801e19c3405806956c8a45`.
La prima prova melonDS Android verifica Continua normale, nuova vista delle
Opzioni, Guida aperta dal libro, selezione invariata dopo i tocchi sui vecchi
comandi inferiori, Allenamento con cinque righe visibili, R fino alla sesta
voce, B alla radice e ritorno al campo originale. Tre save ospiti e originale
restano byte-identici dopo uscita normale senza SAVE/Applica. Sessione
terminata entro il limite di 600 secondi, emulatore fermato e prestito rilasciato.

**Il gate resta aperto.** Un controllo diretto dei PNG ha corretto una lettura
errata delle anteprime: il fondale inferiore è identico in otto catture
stabili delle Opzioni e della Guida; i presunti schermi neri durante la
navigazione non sono presenti nei file originali. Restano i fotogrammi neri
all'ingresso, prima della prima presentazione, da misurare. Il tentativo
Y Info non ha prodotto quella vista e non conta come successo. Mancano
navigazione completa, EN, SAVE e riavvio a freddo, sospensione/audio, picchi
runtime e misure di risposta/fluidità. La configurazione 4/8/240 resta
soltanto diagnostica. Nessuna promozione della candidata o nuova CI verde.

Una seconda sessione italiana sugli stessi byte, con ricevuta di provenienza
aggiornata, raccoglie 60 catture sparse senza schermi interamente neri nelle
aree misurate: campo, Guida a riposo e passaggi A/R/B. Verifica anche Pokémon
speciali → Arceus, sette righe sopra la fascia dei comandi, e ritorno al campo.
I save restano invariati. Il campionamento non misura ogni fotogramma né
chiude la fluidità: la risposta osservata richiede ancora calibrazione.
È invece confermata una piccola interruzione della cornice sotto alcune
celle di testo della Guida; una correzione mirata con test è in preparazione.

## Risultati circoscritti

I numeri indicano metodi delle suite, non sessioni di gioco né prove Android.
Class A esegue sorgenti compilati con confini nativi dichiarati o dati sintetici;
Class B usa gli input V4 verificati. Le prove CPU native dichiarano gli stati
preparati e i servizi hardware sostituiti dal banco. Le esecuzioni mirate sotto
riportate non hanno skip.

| Unità | Commit locale | Ultima verifica mirata dell'integratore |
|---|---|---|
| Modello e coordinatore atomico delle impostazioni | `11f6a88`, `c61d3f1` | 33 Class A e 8 Class B sul coordinatore composto; le estensioni Training e Cromatici hanno verifiche separate. |
| Campionamento fisico condiviso | `0f66686` | 13 Class A e 8 Class B. |
| Heap UI con allocazioni controllate | `f4293f0`, `cd75c17` | Ultima verifica: 16 Class A e 14 Class B; il ciclo nativo Create/Alloc/Destroy conserva i contatori storici degli heap ritirati. |
| Allocatore persistente per il futuro chiamante UI | `cd75c17`, `f397d05` | Ultima verifica: 16 Class A e 14 Class B; bootstrap residente opzionale di 40 byte e proprietà trattenuta oltre il ritorno. Collocazione condizionale, nessuna installazione. |
| Compilatore delle risorse e rilettore indipendente | `7f75499` | 21 Class A e 2 Class B, risorse generate in memoria. |
| Catalogo bilingue e vincoli geometrici | `331e75a`, `39769e4` | Ultima verifica: 15 Class A e 2 Class B; 133 ID, font nativo, avvisi compatti e rilettura completa EN/IT. |
| Pianificatore delle impostazioni | `39769e4` | 22 Class A e 2 Class B, 238 scenari; area interna della cornice corretta prima del disegno dei pixel. |
| Backend dei pixel delle impostazioni | `21be9b2` | 17 Class A e 2 Class B: 19 test in 1.467,870 s, zero skip; 56 confronti nativi EN/IT, inclusi aggiornamenti su entrambi i buffer. Aspetto provvisorio respinto, seguito dalla revisione HGSS `71d0ecc`. |
| Revisione visiva HGSS delle impostazioni | `71d0ecc` | Revisione indipendente e correzione del passaggio Info → selettore; 20 metodi mirati eseguiti dall’integratore e due confronti nativi completi EN/IT, con dettagli e limiti sotto. |
| Lettore delle risorse e durata dei file aperti | `23233a7` | 16 Class A e 11 Class B dopo la correzione dell'alias con l'intestazione dell'allocazione. |
| Lettore separato della Guida | `878bafa` | 18 Class A e 7 Class B: 25 test in 478,079 s, nessuno skip; intero contenuto EN/IT e filesystem nativo con trasporto dichiarato. |
| Contenuti successori della Guida | `a68f5cf` | 15 Class A, 2 Class B e 10 test legacy pertinenti dopo il controllo indipendente dei glifi in entrambe le direzioni. |
| Fondali, Window e pubblicazione del pannello | `a6229a4`, `82f3a4f`, `08c82f0` | Ultima verifica: 11 Class A e 38 Class B, con pannelli accoppiati della Guida, righe invalidate e scelta esplicita senza cornice. |
| Prestito del font nativo e disegno limitato | `e5ae968`, `3a47fc0` | Ultima verifica: 19 Class A e 7 Class B, con pool di testo dinamico e misure di disegno separate dalla pulizia. Revisioni indipendenti della correzione e dell'estensione. |
| Mappa delle proprietà residenti del successore | `0132264`, `ce1d115`, `0294796`, `3f8a93f` | Ultima verifica: 38 test Class A/B in 9,511 s; partizione Fieldbook adeguata nello stesso spazio e chiamante contiguo invariato. Nessuna scrittura nella ROM. |
| Caricamento del codice UI con file persistente | `e380ad8` | 16 Class A e 14 Class B dopo la revisione indipendente del nuovo ciclo completo; nessuna collocazione o installazione ancora assegnata. |
| Chiamante residente delle applicazioni UI | `a57af6d`, `f2aa567` | Seguito: 8 Class A e tre casi nativi decisivi ripetuti dall’integratore, 11 test in 123,975 s senza skip; campagna completa del produttore di 31 test revisionata. Autorità durevole dello heap verificata; applicazioni finali ancora da integrare. |
| Ingresso della Guida dal menu di campo | `013b152` | 18 Class A e 5 Class B: 23 test in 57,689 s, zero skip; fuoco nativo, A/touch, annullamento, allocazioni e ritorno residente. Hook e schermata completa ancora da installare. |
| Controllo preliminare della scena | `730832e` | 12 Class A e 5 Class B: 17 test ripetuti dall’integratore in 11,754 s, senza skip. Controlli in sola lettura su contesto, font e produttori nativi; esclusione dei futuri scrittori ancora dipendente da installer e prove reali. |
| Controller, impaginazione e pixel della Guida | `58eab41` | Revisione completa e correzione mirata dei titoli lunghi; 19 metodi dell’integratore sul predecessore e un nuovo test del contratto corretto. Campagne native e identità distinte descritte sotto; integrazione nel gioco ancora da accettare. |
| Scena comune delle impostazioni e della Guida | `3b489a8` | Revisione e correzione di ACK della sospensione e tocco durante il feedback; ripetizione dell’integratore di tre Class A e due casi nativi decisivi, cinque test in 422,486 s senza skip. Nessuna installazione o prova Android implicita. |

Ogni unità ha superato revisione indipendente e controlli dei file pubblici.
La verifica integrale finale non è ancora conclusa. Un tentativo durante
l'unità RTC del banco nativo ha restituito **non-PASS**: impronte del runtime
ancora da riconciliare, bind locale negato al test Stage0 e processi di alcune
suite senza riepilogo completo. La raccolta risultava incompleta; questo
tentativo non sostituisce le verifiche mirate sopra. L'integrazione RTC ha poi
verificato le impronte aggiornate, i test del parser/CLI e 28 test della suite
maintenance senza riprodurre quell'interruzione; gli altri casi richiedono
ancora la verifica finale nel relativo ambiente. Nessun controllo è stato
indebolito per classificare il tentativo come verde.
Il push e la verifica della CI sullo stesso SHA finale restano successivi
all'accettazione locale composta; questi commit locali non attestano una nuova
CI verde.

La mappa `sgp131-resident-5` mantiene invariata la riserva ARM9 e assegna
540 byte alla futura tabella narrativa in `0x023D7240–0x023D745C` (estremo
superiore escluso). Le due estensioni di codice mantengono margine interno,
senza espandere l'arena. La prenotazione è distinta dall'installazione:
`installation_authorized=false`; l'operazione corrente restituisce gli stessi
byte ricevuti. Le nuove proprietà UI restano bloccate: lo spazio contiguo
di 12.272 byte per il chiamante deriva da vecchi percorsi Plus, il cui ritiro
effettivo deve ancora essere provato nell'installazione. I controlli EN/IT
verificano gli input V4, le aree già possedute
e il rifiuto di mappe o assegnazioni alterate. Non provano ancora la capienza
del codice UI composto, il picco degli heap o l'installazione di nuove mappe.
La porzione condizionale Fieldbook è ora di 3.072 byte a `0x023D4000`, con
guardia di 16 byte a `0x023D4C00` e suffisso preservato di 5.104 byte da
`0x023D4C10`. Sommano gli stessi 8.192 byte del vecchio proprietario Guida,
il cui controllo completo resta invariato. L'aumento serve a conservare le
correzioni di input e allocazione in lavorazione; non accetta automaticamente
quel codice né autorizza a sovrascrivere la vecchia Guida. Revisione e test
verificano che tutte le nove proprietà condizionali restino bloccate.

## Cosa dimostrano queste prove

Il nuovo compilatore UIR1 conserva i 51 elementi precedenti dell'archivio e
aggiunge un elemento con cornici, font, testi propri e nomi delle specie.
Il lettore usa un file persistente nell'applicazione, verifica lunghezze,
posizione, struttura e CRC prima di pubblicare le viste e conserva la proprietà
del file quando la chiusura richiede un nuovo tentativo. Le prove native EN/IT
eseguono filesystem e heap reali, con trasporto della scheda e un caso di attesa
dichiarati come sostituzioni del banco. Non sono prove del driver Android o
dell'intero scheduler del DS.

Il catalogo aggiunge 133 testi originali EN/IT con ID stabili, separati dalle
493 specie. Misura titolo, contatore, alternative, Info, avvisi e comandi con
il font nativo, senza ridurlo. Dopo gli avvisi compatti e la correzione
dell'anteprima, la risorsa completa misura 64.272 byte EN e 64.900 byte IT,
rispettivamente 1.264 e 636 byte sotto il limite di 65.536.
Ogni aggiunta successiva deve ripetere il controllo completo nelle due lingue.
Queste misure non provano ancora la disposizione dei pixel della schermata.

Il pianificatore produce tutte e sette le viste con un record di 1.184 byte.
La cornice nativa lascia un'area interna di 200×32 pixel: il testo dell'anteprima
è stato riadattato a questa larghezza senza ridurre il font. Il successivo
backend dei pixel ha superato revisione indipendente e verifica mirata.
Il maintainer ha respinto la
resa visiva provvisoria: richiede cornici colorate, gruppi distinti e selezioni
più evidenti, coerenti con HGSS. L'accettazione estetica resta aperta;
correttezza dei pixel e approvazione del loro aspetto sono verifiche distinte.
Il backend mantiene due cronologie completate, chiude le righe condivise fra
operazioni e ridisegna anche i testi invariati che le intersecano. I confronti
con String e printer nativi coprono canvas, mappe, palette e RGB555. Record
3.320 byte; codice composto delle sue dipendenze 31.784 byte. I 56 confronti
dell'integratore comprendono 44 scene e 12 aggiornamenti numerici; due ulteriori
prove iniziali del produttore restano evidenze separate. Questi conteggi non
sono frame Android o test di persistenza. Il seguito visivo `71d0ecc`, descritto più sotto, attua il
Task 3a (piano interno) nei sorgenti.

I contenuti successori SGG1 mantengono ID e rimandi, eliminano il prefisso
numerico dalle evoluzioni e aggiungono gli accessi alle specie dei gruppi.
Le righe ammettono soltanto glifi 1–509 e il terminatore finale. La condivisione
dei testi e delle pagine immutabili produce **467 voci**, **76 righe speciali**,
**38 alias** e **64 specie speciali** accessibili per nome. Le dimensioni sono
91.592 byte EN e 92.600 byte IT, sotto il limite invariato di 131.072 byte.
Il generatore legacy riproduce ancora esattamente il precedente elemento 829
EN/IT. Questo cambiamento non è ancora installato nelle ROM V4.

Il lettore SGG1 usa un record separato di 292 byte, configurazione di 64 e
prestito di 36. Il filesystem asincrono mantiene il proprietario durante attese
e chiusure fallite; CRC e directory vengono verificati prima delle viste.
Il codice composto heap/lettore comune/Guida misura 11.386 byte. I test non
dimostrano ancora il picco di memoria dell'applicazione completa. Resta un
caso minore da aggiungere: completamento positivo ritardato di un blocco non
finale, seguito dal caricamento fino a READY.

La prosa aggiornata segue i fatti verificati per Cynthia, Regis, Sinjoh,
trio creazione, prerequisiti di Arceus e sequenza Darkrai/Cresselia. Non corregge
il distinto incidente della variabile fuori intervallo `0x6131` e non promette
durata, unicità o ripetibilità di quell'evento attraverso il riavvio.

Il componente grafico prepara pannelli nascosti e pubblica solo quelli
completati. Le prove CPU eseguono i servizi nativi EN/IT con sostituzioni
hardware dichiarate e verificano anche il rifiuto senza modifiche quando stato
o token invadono l'intestazione di un'allocazione. Dopo la correzione delle
intestazioni, l'estensione per mantenere il pannello nascosto misurava 6.648 byte
di codice heap/BG e uno stato di 120 byte. L'estensione successiva della Guida
porta lo stato a 176 byte, conservando i primi 120, e il codice composto attuale
a 8.098 byte con il controllo heap corretto. I nove buffer della Guida richiedono
93.032 byte di payload; le impostazioni mantengono cinque buffer e il display
inferiore vuoto. I due display della Guida condividono versione e pubblicazione,
con righe completate indipendentemente. La scelta senza cornice preserva tutti
i tile del testo; la cornice resta disponibile per l'anteprima nelle Info.
Le prove alternano tre sequenze di navigazione per lingua e confrontano mappe,
palette, pannello visibile e righe invariate; righe mancanti o invalidate dopo
il trasferimento impediscono la pubblicazione. Il renderer dovrà rispettare
questi vincoli quando modifica i pixel. Il componente non assegna ancora il limite
temporale di pubblicazione e non dimostra l'assenza di frame parziali su Android.

Il printer limitato usa il font nativo con una risorsa trattenuta fino alla
restituzione. I confronti EN/IT verificano tutti i 21.120 byte del pannello e
il cursore contro String e printer nativi, inclusi accenti, larghezze zero,
interruzioni di riga e bordi. Le prove distinguono il font preparato dal suo
caricamento durante il gioco. Un rifiuto della restituzione della risorsa lascia
ora uno stato esplicito di proprietà trattenuta, anche quando l'acquisizione del
font non era stata pubblicata. Il nuovo pool formattato usa un'allocazione
dedicata di 4–4.096 byte, con proprietà e intestazioni verificate; anche la
capacità nativa oltre il testo dichiarato è protetta dalle sovrapposizioni.
I 38 confronti nativi dell'estensione includono contatori e frazioni
originali in EN/IT. Il codice composto heap/lettore/font misurava 11.542 byte
in `3a47fc0`; con il controllo heap di `cd75c17` misura 11.538 byte;
le strutture del font restano di 88, 152 e 652 byte. Non sono ancora prove
delle schermate complete o del formatter che produrrà quei testi nel gioco.

Il caricatore del codice conserva un file nativo e i metadati in un record
persistente: attese, annullamenti e chiusure fallite non autorizzano a liberarlo.
Le prove verificano anche il rifiuto di dati compressi corrotti prima della
decompressione e il rilascio della sola riserva posseduta. Il codice residente
misura 4.566 byte, il record 4.624 byte e la configurazione 96 byte; nelle
allocazioni native preparate il record richiede 4.656 byte con le intestazioni.
Sono verifiche del confine del caricatore. Restano da installare il codice
nella riserva, verificare gli effetti degli hook nativi nel contesto reale e
legare la configurazione alla ROM finale.

Il chiamante residente `f2aa567` usa 9.484 byte di codice composto con
allocatore e caricatore, entro i 12.272 condizionali; il record proprietario
misura 5.036 byte e il contesto resta di 64. Il token dello heap 38 vive ora
nel record residente e resta disponibile anche dopo il rilascio dell'app.
Il codice dinamico può essere ritirato soltanto dopo il ritorno al chiamante,
con token interamente azzerato e heap nativo realmente inattivo.

La campagna completa del produttore passa 31 test in 1.861,859 s, senza skip;
la revisione indipendente non ha rilievi. L'integratore ripete otto Class A e
le tre prove native decisive: app liberata e distruzione rifiutata tre volte
prima del successo, arresto HOLD con risorse trattenute, allocazione dell'app
fallita dopo la creazione dello heap. Passano 11 test in 123,975 s, senza skip.
I vecchi frame SYS vengono alterati dalla prova per verificare che non siano
più l'autorità usata per la pulizia. I rifiuti usano il vero helper nativo;
la discrepanza transitoria del contatore che li provoca è dichiarata come
iniezione del banco. Argomenti e manager mantengono i rispettivi proprietari.
Questi test usano applicazioni preparate: non sono le schermate finali,
una prova Android o la misura del picco di memoria della UI completa.

Il controllo preliminare `730832e` verifica il contesto corrente, il rapporto
fra scena padre e figlia, gli argomenti presi in prestito e il font nativo,
oltre a callback, stampanti di testo, DMA, dissolvenza e luminosità. Non azzera
stati globali per ottenere un esito favorevole. Le prove preparate EN/IT
eseguono allocazioni e interrogazioni native; ogni chiamata conserva RAM e
registri hardware, salvo il risultato sullo stack del chiamante.
La revisione indipendente e i 17 test ripetuti dall’integratore passano;
il codice aggiunge 1.402 byte alla composizione dei suoi helper, senza simboli
esterni irrisolti. Il massimo osservato è 19.056 istruzioni e 144 byte di stack,
non una misura temporale Android o del picco dell’applicazione completa.

Il payload verificato ha SHA-256
`2cb280c6b6ae2d133e5a0b77ce469dff56084fe709f6db0462f984955da9013a`.
Le prove precedenti al congelamento non avevano log originali conservati:
questa limitazione resta esplicita; le nuove esecuzioni conservano log,
impronte, differenze e ricevuta di compilazione. Un distinto tentativo della
suite globale è stato interrotto con exit 143 e resta **non completato**.
L’esito positivo del controllo preliminare non prova che nessun altro task
scriverà in futuro nelle risorse: questo vincolo richiede ancora l’installer
e l’osservazione dei percorsi reali di ingresso e uscita.

## Gate ancora aperti

L'ingresso successore della Guida usa 2.596 dei 3.072 byte condizionali,
senza occupare guardia o suffisso. Nei casi nativi preparati, selezionare il
libro disattiva il fuoco dei nove sprite precedenti e omette la loro richiesta
di animazione di conferma. A e touch hanno nove invii di feedback verificati;
B/X rilasciano soltanto il comando posseduto. Il testo GUIDE/GUIDA, la finestra
delle Opzioni e gli altri banchi di palette sono controllati separatamente.
La revisione indipendente e il seguito sulle due osservazioni minori sono
chiusi. Le immagini ricostruiscono BG e font nativi, senza il menu completo
e il rasterizzatore OAM: non sono catture Android. Non è ancora provato il
percorso composto attraverso il nuovo chiamante e il lettore della Guida.

- Integrazione font e BG/Window, ciclo completo delle applicazioni e disegno delle schermate;
  chiamante del caricatore, riserva, picco heap e rilascio dei callback.
- Installer e rilettura della ROM composta, testi completi, controlli della Guida
  sul display inferiore e impostazioni interamente sul display superiore.
- Prove Android EN/IT prima/dopo, sequenze visive, tempi fino alla schermata
  pronta, memoria e ripetizioni; il solo contatore FPS arrotondato non misura
  questi aspetti. Le misure mancanti restano non valutabili.
- Vecchi save EN/IT, con e senza dati Plus e con Borsa ampliata: Continua,
  SAVE nativo e riavvio a freddo su copie, preservando gli originali.
- Nuove meccaniche e regressioni composte, suite finale, push e CI dello stesso
  SHA prima della consegna per il test sul dispositivo.

Un controllo successivo sulla cattura RAM EN V4 ha rilevato un rifiuto
conservativo non coperto dalle fixture iniziali: uno heap già distrutto conserva
il proprio contatore, come permette il codice nativo. Il modello comune lo
richiedeva nullo. La correzione `cd75c17`, revisionata indipendentemente, passa
il ciclo nativo EN/IT e l'allocazione sulla cattura EN originale, conservando il
contatore storico. Il nuovo allocatore persistente usa lo heap 11, trasferisce
esplicitamente il record proprietario e trattiene le risorse quando non può
dimostrarne il rilascio. Record 40 byte, codice heap/allocatore 3.260 byte:
sono confini verificati, non il chiamante completo. Dopo la modifica sono
passati anche tutti i 53 test di lettore e font dipendenti dal controllo comune,
senza skip. La ROM V4 resta invariata.

Il limite iniziale di 8 KiB del chiamante non bastava alla composizione
misurata. La mappa condizionale corrente propone 12.272 byte contigui senza
espandere l'arena; occorre ancora dimostrare il ritiro dei vecchi percorsi e
verificare il chiamante completo. Il bootstrap persistente ha verifiche
separate: il codice predefinito resta invariato, quello configurato lega il
token all'esatta collocazione residente. Non è un'autorizzazione a installarlo.

## Revisione visiva HGSS nei sorgenti

`71d0ecc` aggiunge il pannello blu, separatori di sezione, riga selezionata
chiara con bordo rosso, valori incorniciati e comandi raggruppati. Conserva font,
sei slot, schermo inferiore nero e assenza di nuove allocazioni per frame.
La revisione indipendente ha trovato un difetto nella cronologia del buffer
nascosto: Info → ritorno → selettore corto lasciava parte dello sfondo chiaro.
La regressione nativa lo riproduce in EN/IT con entrambe le parità; la correzione
ridisegna tutto al cambio di vista, conservando gli aggiornamenti parziali
all'interno della stessa vista.

La campagna originaria del produttore contiene 72 successi e due fallimenti
del vecchio oracolo geometrico, poi corretti e rieseguiti separatamente.
I suoi 41 metodi nativi erano verdi ma non coprivano il difetto trovato dalla
revisione. Il seguito passa 26 Class A e due metodi nativi, con 16 confronti
esatti della sequenza fra viste e 12 aggiornamenti numerici rimasti parziali;
nessuno skip. La revisione del seguito non ha rilievi aperti.

L'integratore ha poi eseguito 18 metodi mirati e due confronti completi dei
pixel EN/IT sulla prima schermata. Due test del catalogo erano inizialmente
saltati per configurazione degli input assente: sono stati rieseguiti con input
obbligatori, entrambi verdi. I 20 metodi effettivamente eseguiti non includono
gli skip come successi. La risorsa accettata misura 64.280 byte EN e 64.908 IT.
Il codice del painter misura 35.024 byte; la composizione dei componenti già
scritti misura 44.624 byte, lasciandone 20.912 prima di Scene e painter Guida.

Il confronto nativo prima/dopo sullo stesso caso passa da 23 a 30 job di testo:
14.932.584 → 19.186.180 istruzioni EN (+28,49%) e
15.157.082 → 19.416.509 IT (+28,10%). Le chiamate massime osservate diventano
più piccole, ma il lavoro totale cresce; non è una prova di maggiore velocità.
Sono conteggi CPU, non cicli, FPS o latenza Android. La composizione deve ancora
calibrare quante chiamate eseguire per frame e superare le misure reali di
apertura e risposta. Anche l'accettazione visiva del maintainer resta aperta.

## Banco Android: risultato funzionale circoscritto

L'APK privato dell'osservatore è stato costruito e provato realmente su
melonDS Android nel Mac. Sul V4 IT, il normale Continua raggiunge il campo;
configurazione, acquisizione, esportazione, conferma e chiusura della sessione
funzionano. La cattura verificata contiene 36 coppie di eventi frame e due
input ricevuti/applicati. I save copiati restano invariati: questa prova non
ha eseguito SAVE e non sostituisce la matrice di compatibilità.

Identità APK SHA-256
`fb76c0b83a3fbe04e21dcfab4424a8bba61a996b5d1b196e36e4b77093448cc3`;
cattura SHA-256
`35ab48534f8039978c81843cbca4d56187251f2b0c591ac49ca6dd59b048f1e4`.
La revisione indipendente non ha rilevato problemi nella prova circoscritta.
Un input applicato dall'emulatore non prova che l'azione sia stata consumata
dal gioco. Schermata pronta, heap, scadenze video e tempi prima/dopo restano
non valutabili. Il prossimo osservatore deve includere lo heap 11 del
chiamante persistente insieme a 0, 3, 9, 10, 12 e 38. Nessuna misura di questo
APK viene trasferita implicitamente a una futura ROM o a un APK diverso.

Il successore privato del banco include ora questi sette heap e controlli
sull'associazione fra caso, frame, stato e gruppi di misure. La revisione ha
corretto sia l'identità dello heap dei due oggetti PC, sia il conteggio finale
delle acquisizioni interrotte: gli eventi mancanti dopo un errore non diventano
misure o schermate pronte. La ricevuta sorgenti schema 7 è identificata da
`10f7589e140020d334965b6bd7c0f8acb61184f537aaa8858fc85d4b219a3718`.
Dopo revisione indipendente, l'integratore ha eseguito 4 test nativi e 34 Python
in 11,642 s, senza errori o skip, verificando identità di sorgenti ed eseguibili
prima e dopo. Sono prove sul computer dei componenti del banco; questo
successore non è ancora stato costruito come APK né eseguito su Android.
Le misure reali di memoria, consumo delle azioni e tempi restano da acquisire.

Restano due osservazioni minori sui fondali: esplicitare nel commento pubblico
che il callback nativo gira nel main loop dopo l'attesa VBlank e aggiungere un
caso mirato sulla coda inattiva dello stato delle impostazioni. Il controllo
esistente la rifiuta; la revisione finale dovrà riprendere entrambe.

Resta inoltre da aggiungere l'asserzione esplicita di allineamento dello stack
al confine FS del banco del lettore: la revisione non ha osservato un errore ABI,
ma il controllo ereditato di heap/IRQ non copre direttamente quel confine.
La verifica finale deve riprendere questa osservazione.

Le misure storiche del banco font includono chiusura e pulizia e restano
massimi aggregati. Il banco aggiornato isola ora ogni chiamata di disegno e
misura separatamente la pulizia; la revisione indipendente ha chiuso questa
osservazione per `3a47fc0`. I massimi osservati allora per il testo dinamico
sono 225.899 istruzioni per chiamata, 58.213 durante I=1 e 1.152 byte di stack.
Sono misure CPU dei casi preparati, non cicli, durate IRQ o limiti universali:
non assegnano budget Main/IRQ e non dimostrano prestazioni Android.

Il piano interno UI e il
piano interno delle meccaniche fissano
l'ordine di accettazione. Nessuna misura dei soli sorgenti sostituisce questi gate.


## Guida a due schermi: componente `58eab41`

Il controller conserva navigazione a cinque righe e otto ritorni completi dai
riferimenti. Il lettore usa il display superiore; sotto compaiono comandi con
stati normale, selezionato, premuto e disabilitato. Il planner pubblica solo
piani e pool completi; il painter conserva due cronologie accoppiate senza
scrivere sul front o sul buffer in attesa. I nove testi aggiunti portano il
catalogo a 142 ID propri più 493 specie, preservando i 133 precedenti.
Le risorse EN/IT misurano 64.448/65.096 byte: margini 1.088/440 su 65.536.

La prima composizione dei componenti misura 54.298 byte, SHA-256
`17d4f55237f471cf7dcdb9d93a9e4a9c626e3fcd3cc853c03f1645e73b63002e`.
Su questa identità il produttore verifica 18 scene native accoppiate EN/IT e
l'intero grafo dei contenuti; il distinto compilato del solo planner verifica
2.397 piani, massimo 22 operazioni e 44 byte di pool. L'integratore ripete
16 Class A, un caso nativo di alias/proprietà e due cataloghi completi:
19 metodi in 39,874 s, senza skip. Un primo comando selezionava erroneamente
suite omonime delle impostazioni: è stato fermato e conservato come non-PASS.
La registrazione usa processi distinti per evitare questa ambiguità.

La revisione trova poi un titolo valido di 208 pixel che viene rifiutato:
uno spazio anticipato produce 8+200 pixel invece di 160+48. Il seguito preferisce
uno spazio solo quando entrambe le righe rientrano nei limiti. Il nuovo caso
fallisce prima e passa dopo, conservando tutti i glifi; passano anche gli otto
test del planner e una ripetizione mirata dell'integratore in 11,197 s complessivi.
La revisione del seguito non ha rilievi di codice aperti. La registrazione
anticipata di un log dell'integratore ancora in scrittura è stata riconciliata:
l'impronta originaria corrisponde esattamente ai primi 158 byte dei 259 finali;
le altre prove e tutte le impronte sorgenti coincidono. Il log completato ha
una ricevuta distinta, senza sostituire il documento originario.

Il compilato finale dei componenti misura **54.334 byte**, SHA-256
`af0c7bb89e749bdbe03b7d8632fc907cf01c904f9420044605c436b9295ff764`.
Non include ancora scena, admission o chiamante residente. Non ha simboli
irrisolti; stack statico del builder 2.432 byte, invariato. Le campagne complete
del predecessore mantengono la propria identità: non sono etichettate come
nuove esecuzioni del seguito. I titoli attuali, massimo 145 pixel, non entrano
nel ramo corretto. Il seguito della scena descritto sotto corregge i difetti
riprodotti di tocco durante il feedback e ACK della sospensione. Nessuna prova qui stabilisce tempi
Android, compatibilità dei save o installazione.

## Scena comune: componente `3b489a8`

La scena collega controller, risorse, disegno e rilascio delle due applicazioni.
La revisione riproduce due difetti: un rifiuto temporaneo dell’ACK di sospensione
bloccava definitivamente la scena; il ridisegno dello stato premuto annullava
il rilascio touch dello stesso pulsante. I due test falliscono sul predecessore.
Il seguito ritenta l’ACK mantenendo le proprietà e conserva una testimonianza
di 16 byte del gesto iniziato sulla vista effettivamente mostrata. Consente
solo la continuazione di quel gesto; tocchi nuovi su una transizione non ancora
visibile, trascinamento, input fisico concorrente o identità scadute non aprono
una voce. La perdita reale del proprietario continua a rifiutare il proseguimento.

Revisione completa e revisione della correzione non hanno rilievi aperti.
Il produttore conserva sei test nativi sulla dipendenza Guida precedente e
quattro sulla dipendenza finale, con ricevute distinte. Sulla versione finale
l’integratore ripete tre Class A e i due casi decisivi: **cinque PASS in
422,486 s, zero skip**, verificando prima/dopo sei sorgenti propri e 53
dipendenze. Il compilato misura **60.532 byte**, SHA-256
`4300012b535c6c1f39f45b6cc61a41e409936267bef8f2ec2c55c0a5d1f6a968`;
restano 5.004 byte entro il limite di 65.536. Non include ancora la coda
Cromatici né i collegamenti residenti dell’installer.

Le prove preparate misurano 13 allocazioni della Guida: spazio libero e massimo
blocco contiguo 6.564 byte EN e 4.908 IT, con applicazione di 4.996 byte.
Lo stack aggregato osservato è 3.096 byte; il frame statico di Main è 112.
Sono misure del banco nativo, non margini certificati nel gioco completo.
Il rifiuto ACK è simulato secondo il contratto residente: non è una prova del
coperchio reale. I parametri 4 chiamate, 8 glifi e linea 240 sono espliciti
valori del test, senza default di produzione. Installer, vecchi chiamanti,
misure Android, audio, prestazioni e vecchi save restano gate aperti.

## Seguito privato del banco: intervalli e durata degli oggetti

L'osservatore distingue ingresso, esecuzione e completamento dei blocchi ARM64,
con limiti conservativi: non inventa un timestamp esatto per gli eventi interni
al blocco. Conserva ring e formati precedenti; i descrittori sono immutabili
prima dell'attivazione. La revisione trova un accesso a NDS già distrutto nelle
configurazioni senza tracciamento. Il seguito separa il legame di durata dalla
registrazione del tracciamento, mantenendo quest'ultimo disattivato in quel caso.

Il test usa oggetti reali e rende inaccessibili le pagine dopo la distruzione:
quattro casi falliscono prima; tutti e nove passano dopo, coprendo entrambi gli
ordini di distruzione e la riconfigurazione. Dopo revisione indipendente senza
rilievi aperti, l'integratore ripete tre target nativi in 6,654 s e verifica
1.187 impronte correnti e 1.225 del predecessore ricostruito prima/dopo.
Ricevuta del seguito:
`6664b77ec5cff09b83af371596b592856936fc63520fbe7f0c0dc38102c53434`.
La precedente esecuzione di quattro target e 30 test Python resta distinta.
La crescita dell'osservatore è 4.776 byte; il legame aggiuntivo di durata occupa
8 byte in NDS, senza modificare i dati serializzati. Gli avvisi CMake ereditati
da Teakra sono conservati e dichiarati, non soppressi.

Sono prove sul Mac: fastmem fault/rewrite/reuse non è supportato dal percorso
Apple e rimane esplicitamente non verificato. Compilazione e stack Android,
sequenze ARM64 su più blocchi, callback installati, latenza e prove prima/dopo
restano aperti. Al termine di questa fase l'APK successore era ancora in
preparazione; quello della precedente prova Android non acquisisce
retroattivamente queste proprietà. Il seguito è registrato qui sotto.

### APK successore e prima esecuzione sintetica Android

Il seguito privato `dispatch-fix1-binding1` è stato compilato e revisionato.
La revisione ha richiesto di verificare anche due dipendenze Python prima
della loro esecuzione; la correzione supera la revisione circoscritta e sette
test ripetuti dall’integratore in 2,232 s, senza skip. Ricevuta dei sorgenti:
`b4a069c61b38f79d8951dadeafe5b39597ecaa61e0f8685441cf6f657fbc2df2`.
APK: `6c6a2d3266c4a531906c2eaf588e34a090554d30d0ada06480bf36fa01bd1532`.
Questo APK non è ancora installato e non contiene una nuova prova nel gioco.

Il distinto eseguibile sintetico Android ARM64, SHA-256
`54d26fda4b367d58bafcb84ff3a0fda78a04a662a1d74bda3a330aeb3a20957d`,
è stato eseguito una volta su API 33. Termina con codice 1 prima di creare
il worker: il controllo composto sulla dimensione predefinita dello stack
pthread e sull’allineamento alla pagina rifiuta il valore. Il banco non
stampa gli operandi, quindi non è ancora identificata la sotto-condizione
fallita. Cicli di vita, sequenze su più blocchi, fastmem e margine dello stack
non sono stati raggiunti e non risultano superati. Il precedente tentativo
di solo avvio dell’emulatore non aveva eseguito il test.

L’eseguibile ospite è stato rimosso e i processi dell’emulatore e della guardia
sono terminati. Nessuna ROM, app o copia di salvataggio è stata modificata
da questa prova. Il fallimento resta conservato per una diagnosi numerica;
non è una regressione osservata nella ROM né un’accettazione del banco.

Il successivo piccolo probe indipendente, SHA-256
`380c8bc1f7b96c0a25d1a264cb736c5cce63801322933d03507e02d5c19c5a15`,
termina una volta con codice 0 sullo stesso target: pagina 4.096 byte,
minimo pthread 16.384, attributo predefinito 1.015.808 e stack del thread
predefinito 1.019.136, guardia 4.096. Tutti i ritorni delle API sono zero.
Sono valori del probe, non gli operandi mancanti del primo eseguibile;
non misurano consumo o margine dello stack. Il test sintetico completo resta
da correggere e ripetere. Anche questa sessione termina con ospite rimosso
e processi posseduti arrestati.

## Installer controllato: componente `4d71e43`

L’installer compone le due lingue in memoria a partire dalle identità V4
immutabili. Il verificatore indipendente ricompila i payload attesi e controlla
i byte modificabili, i collegamenti effettivi, i vecchi ingressi ritirati e
il resto della ROM. La ricevuta del chiamante non può autorizzare altre scritture.
La configurazione dei budget della scena è obbligatoria ed esplicita; i valori
di prova non diventano automaticamente una calibrazione di produzione.

La revisione trova due difetti nel compilatore: riserva disco insufficiente e
file temporaneo delle dipendenze prodotto da Clang. La correzione riserva
100 MiB oltre la soglia libera di 10 GiB e riceve le dipendenze tramite output
limitato, lasciando al processo padre la scrittura del file previsto. Conserva
i limiti per file, diagnostica, numero di file e durata dei processi; nessun
nome temporaneo viene aggiunto alle eccezioni. Revisione completa e revisione
della correzione non hanno rilievi aperti.

L’integratore ripete 17 test della correzione in 3,577 s e le due composizioni
EN/IT, con readback indipendente e rifiuto di una coda protetta alterata:
22,650 s complessivi, nessuno skip e nessuna ROM scritta su disco. Il successivo
adattamento dei soli test all’ambiente CI supera una revisione distinta e
23 test ripetuti in 4,243 s, senza skip. Questi test usano, dove dichiarato,
le identità degli strumenti host; i vincoli degli strumenti di produzione
rimangono invariati. Le due ulteriori composizioni dell’autore passano in
13,155 s con gli strumenti di produzione e gli stessi byte finali. La precedente
campagna di 40 mutazioni mantiene la propria identità: non è stata ripetuta.

| Lingua | Byte in memoria | SHA-256 |
|---|---:|---|
| EN | 152.056.444 | `ddb1603029048f0740ebe08726c9ff8defb6ff9844c66c48c1b44766d22657c7` |
| IT | 158.299.460 | `6f64a2b83be4d2b0d81e3fb951edcce76fffe757e3c7766a606a2929679047be` |

Il modulo dinamico completo, inclusa la coda Cromatici, misura 63.244 byte
su 65.536: margine 2.292, BSS zero. Il chiamante residente misura 9.484 byte,
l’input fisico 904, Training 1.360 e l’ingresso Guida 2.596, entro i rispettivi
comparti. Le impronte dei cinque file e di 91 dipendenze sono verificate;
originali e salvataggi non cambiano. La suite pubblica registra ora i contratti
senza ROM e la distinta suite canonica che richiede gli input privati.

Restano da integrare lo stage nel banco con candidata/fallback e da creare
la copia persistente di prova. Non è ancora stata avviata una ROM 1.3.1:
aspetto Android, ingressi/uscite, callback, tempi, audio e compatibilità dei
vecchi save restano aperti. Il commit locale non implica push o nuova CI verde.

## Banco persistente e prima candidata: `0489f4f`

Lo stage UI è ora integrato nel banco. Richiede configurazione esplicita,
identità degli input e verifica indipendente prima di pubblicare o usare una
candidata. La revisione ha individuato una sostituzione concorrente dei file
storici durante la verifica: la correzione registra identità e assenza dei
file prima dell'ammissione e le ricontrolla prima del journal e della prima
modifica. Quattro regressioni passano da rosso a verde; revisione circoscritta
senza rilievi e 83 test ripetuti dall'integratore in 1,769 s, senza skip.
Il recupero delle transazioni mantiene il proprio contratto precedente.

La prima composizione persistente IT impiega 20,122 s e produce **158.299.460
byte**, SHA-256
`6f64a2b83be4d2b0d81e3fb951edcce76fffe757e3c7766a606a2929679047be`.
È la stessa identità verificata in memoria. La ricevuta persistente ha SHA-256
`d6af24019cc4a5b6bfcf5a3b5f002c5a631f70f4fdf9087ed22e2a12419409f0`.
Originali EN/IT e 590 identità sorgenti restano invariati; intermedi rimossi,
54.283.743.232 byte liberi alla fine. Esiste una sola copia persistente IT
in stato di prova; nessuna candidata o fallback verificata viene sostituita.

La calibrazione **4 chiamate / 8 glifi / linea 240** è dichiarata di prova,
non ancora di produzione. I gate dello stage richiedono evidenze runtime
associate alla candidata, agli input e all'APK. Questo risultato prova la
costruzione e la gestione dei file: non certifica avvio, aspetto, prestazioni,
salvataggi o meccaniche. La prima prova funzionale Android è il passo seguente.

## Prima prova Android della candidata IT: fallimento conservato

La candidata IT `6f64a2b8…047be` sopra identificata è stata avviata su
melonDS Android nell'AVD ARM64/API 33 esistente. L'APK installato tramite
aggiornamento normale ha SHA-256
`6c6a2d3266c4a531906c2eaf588e34a090554d30d0ada06480bf36fa01bd1532`;
l'impronta del file effettivamente installato coincide. Una copia raw del
save precedente, SHA-256
`f61855c808c74d5183497f6fa49bb54062b03e8709648147695c0099c08b1df9`,
carica tramite Continua la mappa prevista, con 16 medaglie e Pokédex 288.

**Esito FAIL:** il tocco su OPZIONI produce schermi neri, poi un ritorno
automatico alla stessa mappa senza mostrare le nuove impostazioni. La cattura
successiva precede qualsiasi comando Indietro: non è quindi dimostrato un
blocco permanente. Otto immagini e azioni limitate conservano la sequenza.
La Guida e le ulteriori navigazioni non sono state provate dopo il difetto.

La sessione dura 128,191 s e termina con uscita normale dal frontend,
emulatore arrestato e prestito della candidata rilasciato. Nessun SAVE o
Applica: copia ospite, due vecchi save ospiti e fixture originale mantengono
la propria impronta. Nessun ripristino nasconde modifiche. Il pending resta
non accettato. Questo fallimento richiede diagnosi e nuova prova Android;
prestazioni, persistenza e matrice EN/IT restano aperte.

### Diagnosi e correzione del controllo display

Il replay nativo della stessa candidata individua il primo rifiuto:
modulo caricato, poi `SCENE_ADMIT_E_DISPLAY` prima di allocare la UI.
La banca video D conserva `0x82` dopo la terminazione del servizio WVR;
il servizio ha già rilasciato la proprietà, ma non azzera quel registro.
I test preparati usavano D disabilitata e non rappresentavano questo ingresso.
Una prova a variabile singola riproduce il rifiuto cambiando solo D.

La correzione riconosce esclusivamente lo stato WVR ritirato osservato:
ID allocato e nel suo intervallo nativo, maschera, argomento e callback nulli,
servizio inattivo e nessuna proprietà VRAM OS residua. Conserva D e tutte le
altre verifiche di coerenza. Un ulteriore test ha individuato l'assenza del
ricontrollo alla pubblicazione: ora lo stesso controllo precede il campionamento
della linea video, entro la maschera IRQ già esistente, senza pubblicare né
alterare il frame pendente quando fallisce.

Revisione indipendente senza rilievi bloccanti; 27 test mirati senza skip e
tre regressioni ripetute dall'integratore in 6,207 s, con 590 identità sorgenti
invariate. Le prove native del ciclo coprono EN/IT; la matrice negativa nativa
usa EN. Le due composizioni in memoria e i readback indipendenti passano.
Modulo completo **63.388/65.536 byte**, BSS zero, margine 2.148 byte.
IT: `fbc10e57eb5b64331c62dd9cc5c9eb673be3ec65f67c4ae31d5211efce4a5ca9`;
EN: `566f09f431e2c76a4434f42a3011e98965f1431a1ee39f9ddb0dd0eea7b88bd5`.

Il controllo aggiunge 855 istruzioni con IRQ mascherati (56 → 911); la lettura
della linea precede ancora le scritture video. Sono conteggi, non tempi Android.
L'accettazione richiede ancora ricostruzione della copia persistente, nuova prova
nel gioco e misure prestazionali. Il precedente fallimento resta conservato.

### Riprova Android del successore `5a0a6de`

La stessa copia persistente IT è stata ricostruita in 17,292 s, con identità
`fbc10e57…5ca9` sopra indicata e ricevuta
`e4c4188b5c1029bcc903efd5894cf1517c7db9828b5fb49e2eb1e25eaab1fa96`.
La vecchia copia fallita è stata rimossa dal banco, conservandone ricevuta e
prove; originali e fallback invariati. Anche i due test integrati aggiuntivi
terminano positivamente: Opzioni IT e Guida EN/IT, 332,718 s, nessuno skip.

La prova reale usa lo **stesso APK** `6c6a2d32…1532`, verificato sul dispositivo,
senza reinstallarlo. Ora le Opzioni mostrano sul display superiore le righe
blu HGSS, la selezione chiara con bordo rosso, valori incorniciati e legenda;
il display inferiore resta nero. Giù sposta la selezione da Testo a Effetti
lotta; B annulla e torna alla stessa mappa. È un PASS circoscritto per ingresso,
selezione e annullamento, rispetto al precedente rifiuto riprodotto.

**La Guida fallisce invece l'ingresso:** dopo il tocco sul libro il display
inferiore diventa nero, poi torna il menu di campo senza mostrare il lettore.
Non sono stati inviati altri comandi fra le due catture. Il test composto
rimane FAIL; la causa di questo distinto percorso richiede diagnosi.

Sessione di 156,306 s, 12 immagini, uscita normale, emulatore arrestato e
prestito rilasciato. Tutte le tre copie ospiti e la fixture raw originale
mantengono `f61855c8…b1df9`; nessun SAVE, Applica o ripristino. Sono prove
funzionali, non misure di latenza. EN, Guida completa, persistenza, prestazioni
e accettazione finale restano aperte; nessuna promozione del pending.

### Correzione del primo rifiuto all'ingresso Guida

La riproduzione nativa sulla stessa candidata IT mostra che il lettore non
raggiunge il chiamante: la generazione resta quella della precedente apertura
delle Opzioni. Quando il menu di campo è inattivo, il frame del libro cancella
l'armamento prima del dispatch del nuovo tocco; il comando 32 non viene
accodato. Un test sul compilato identico a quello installato riproduce
`0 != 32`, mentre il vecchio banco preparava soltanto il menu già attivo.
L'attribuzione ad Android deriva da identità dei byte e sintomo concordante;
non è una lettura della RAM Android.

La modifica separa la deselezione passiva dall'annullamento B/X: conserva
l'armamento derivato dal rilascio, senza forzare lo stato del menu o chiamare
direttamente il lettore. Il secondo controllo nel task e il percorso nativo
di attivazione restano invariati. Il nuovo ingresso misura 2.608/3.072 byte
(+12), SHA256
`46db0eef2d0b878940cb574f32158daf5cc32d607f327675f930a200686a8289`.

Revisione indipendente positiva; 27 test mirati, inclusi i casi nativi EN/IT
già preparati, passano in 58,217 s senza skip. L'integratore ripete tre nuove
regressioni decisive in 1,607 s, tutte verdi. Un precedente comando con
Python di sistema falliva l'import di ndspy: non è una prova nativa positiva.
Il nuovo banco dichiara esplicitamente il confine del dispatch simulato e non
dimostra la pianificazione completa. Ricostruzione, generazione successiva
una sola volta, lettore visibile e successiva prova Android restano obbligatori.
L'ultima copia persistente rimane quella del precedente test fallito: il primo
tentativo di rebuild è stato fermato prima di ogni mutazione per coordinare
il nuovo produttore parallelo dei moduli meccaniche.

### Guida: tabella nativa fuori dal limite dello heap

La copia successiva IT `92d61a29c4ceaaef33e01999c7f0d901b0954d6d9d4d54eb9b7e3ee8a3af76ee`
conferma la correzione del tocco: il comando 32 attiva il menu e la seconda
generazione della Guida viene avviata una volta. La prova rivela però HOLD
all'inizio del lettore, prima del disegno e dell'attivazione dei comandi.
La lettura circoscritta dello stato individua il controllo errato: la cache
FAT/FNT occupa `0x023BE564..0x023C00E4`, 228 byte oltre il limite dello heap
applicativo. Il codice nativo la alloca invece nell'arena di sistema. Metadati,
code, allineamento e voce FAT sono coerenti; non è un file lasciato aperto.

Il lettore verifica ora soltanto quella cache nel dominio RAM nativo già usato
dal lettore UIR1, mantenendo l'allineamento a quattro byte, controlli FAT,
esclusioni di sovrapposizione e verifica della sorgente. I limiti globali degli
heap restano invariati. La regressione all'indirizzo reale fallisce prima in
entrambe le lingue e passa dopo, compresi caricamento, lettura, rilascio e
distruzione sul nativo preparato. Due campagne mirate eseguono 17 metodi
distinti: 2 in 18,120 s e 16 in 62,193 s, con una sovrapposizione, nessuno skip.
La revisione indipendente è positiva. Scene misura 60.672 byte e il modulo
completo 63.384/65.536, quattro byte meno del predecessore.

La nuova copia persistente IT misura 158.299.640 byte, SHA256
`e8d91d3824684fd2b05416d4aa44f5a12719148a5c253a03657df0eb415e24d8`.
La ricevuta della prima costruzione è
`36c365c120acf83538a5f40a8f75ffeb82dcde3b66387389a046ea430fc60642`.
Ricostruzione in 15,950 s, sorgenti stabili durante la build, originali
invariati, intermedi rimossi. La riprova nativa effettiva mostra Opzioni,
selezione e ritorno al campo, poi Guida leggibile sullo schermo superiore,
comandi inferiori e ritorno alla stessa mappa con B. Le immagini sono state
ispezionate; il save originale e l'esportazione restano `f61855c8…b1df9`.
Sessione di circa 24,77 s, prestito rilasciato, nessun SAVE o Applica: la
durata della sessione non misura la latenza dell'interfaccia.

La successiva ammissione Android si ferma prima del boot per modifiche
concorrenti ai nuovi moduli delle meccaniche. Una ricostruzione produce gli
stessi byte, con ricevuta
`bac493c5b2481472f9edb4fe2b6dac1fbb002f1e09adda9186d569cb32bc7c89`,
ma il controllo immediato rileva ulteriori cambiamenti e rifiuta l'avvio.
Nessuna prova Android, modifica ospite o nuovo esito funzionale deriva da
questo tentativo. Il prossimo passo è la sessione Android a sorgenti stabili,
seguita da navigazione completa EN/IT, save e misure; il gate UI resta aperto.

### Riprova Android IT: Opzioni e Guida accessibili

Il 30 ottobre 2026, dopo la correzione `c0f5b18`, la stessa candidata IT
`e8d91d3824684fd2b05416d4aa44f5a12719148a5c253a03657df0eb415e24d8`
supera il percorso funzionale base su melonDS Android. La ricostruzione
verificata conserva i byte e produce ricevuta
`07eb30078b206414c39c98a483af18a679e075a516e29d4caa2ccc3189d0d69b`.
Stesso APK `6c6a2d32…1532`, AVD/API33 e configurazione diagnostica4/8/240.

Dopo Continua, le Opzioni mostrano righe blu HGSS, selezione chiara con bordo
rosso e valori incorniciati; Giù sposta il cursore da Testo1/12 a Effetti
lotta2/12 e B torna al campo. La Guida mostra le quattro categorie sopra e
comandi distinti sotto. A apre Allenamento1/6, con cinque voci corrispondenti
alla risorsa letta indipendentemente dalla candidata. B torna alla radice,
un secondo B alla stessa mappa con accompagnatore e menu. Le diciassette
catture includono una transizione iniziale nera e la successiva Guida visibile:
non dimostrano latenza esatta o assenza di ogni flash.

Uscita normale dal frontend, nessun SAVE, Applica o cambio di valore. Tutti
i tre save ospiti e l'originale conservano SHA256 `f61855c8…b1df9`.
I sorgenti UI verificati restano invariati. Sessione di321,701s comprendente
ispezioni e attese degli strumenti, non misura delle prestazioni del gioco.
Emulatore e processo proprietario terminati, rilascio del prestito nello stesso
processo verificato. Rimane soltanto un record inattivo di un precedente
avvio errato del terminale; quel tentativo non aveva usato il gioco.

Esito limitato: **PASS del percorso base IT**. Navigazione completa e input,
lingua inglese, vecchi save con SAVE/riavvio a freddo, heap e confronto delle
prestazioni restano obbligatori. Nessuna promozione, pubblicazione o nuova CI.

### Bridge Options/Guida: oracolo CLOSE aggiornato

Il 3 novembre due test del bridge restavano in attesa di osservare la fase
transitoria `IMAGE_CLOSE` fra due callback. Con `ui_module_pump` quella fase può
essere attraversata correttamente nella stessa callback: entrambi i casi
arrivavano a `RELEASED`, senza owner vivo, e non dimostravano un leak. Gli
oracoli ora ritardano la lettura dell'immagine e contano gli effetti reali dei
close falliti, conservando associazione file, owner e assenza di ingresso nella
scena. I due casi mirati passano 2/2; la regressione completa
`test_bridge_rom.py + test_module.py + test_module_rom.py` passa 56/56 in
705,626s. Restano prove fisiche di coperchio, preview audio/rollback e misure
sul dispositivo: il banco non le sostituisce.

### SG-SV01: esito delle copie delle impostazioni Plus

Il 3 novembre 2026 il blob storico da 500 byte è stato eseguito in Unicorn con
la convenzione reale di `WriteBackup` (1 successo, 0 fallimento): due fallimenti
non scrivono i settori 47/111 ma il vecchio codice dichiarava ugualmente
`load_status=VALID`. Il test TDD copre `[0,0]`, `[1,0]`, `[0,1]` e `[1,1]`, con
cold load delle copie superstiti e controllo del risultato vanilla.

Il successore compilato con toolchain autenticata misura 608 byte, SHA256
`f6d42c2d9001c5f3a92faf223bdbea6eb0a4aa04cdccfe7a0bfd689a9c5c4c4d`,
e resta nello stesso comparto da 736 byte. Zero copie lascia il record non
convalidato; una copia è recuperabile ma segnalata parziale. Il loader sceglie
il `saveno` valido più recente, inclusi copia B nuova con A vecchia, parità e
wrap u32; due copie sono successo pieno. QSalva passa 18/18. Il call-site di
salvataggio è ritargettato dalla vecchia entrata alla nuova e controllato come
seconda regione fisica. Installer/readback EN/IT e registrazione pipeline
passano 5/5; la suite canonica build/Reserve/meccaniche/legacy passa 173/173.
Le composizioni
V4 complete dei quattro owner legacy sono state prodotte e verificate soltanto
in memoria, senza conservare ROM.

Il follow-up del 4 novembre ha legato il payload installato a due fixture raw
EN/IT da 512 KiB con impostazioni Plus e Borsa estesa, sempre su copie
temporanee. Per lingua, 0/2 conserva i vecchi record, A-only e B-only scrivono
la generazione successiva nel solo mirror riuscito e 2/2 aggiorna entrambi;
otto cold loader complessivi recuperano valori e generazione attesi. Gli hash
degli originali restano invariati e nessun byte esterno ai due record da 32
byte cambia. La prova ha inoltre corretto il banco: il kernel HGSS esatto
`0x020E38E0` usa CRC-CCITT normale `0x1021`; lo stub precedente riusava
erroneamente il CRC riflesso `0x8408` dell'header cartuccia. Le fixture reali
uccidono quel mutante. Restano candidata conservata, SAVE avviato dalla UI,
fallimento fisico/rilettura, dispositivo; il gate release resta aperto.

### SG-BAG-ALLOC-01: allocazione privata Borsa a NULL

Il blob Borsa installato della 1.2.5 EN (`e41d95a3…c1fb`) è stato eseguito con
la sola `Heap_Alloc` di `sgp_cap_new` forzata a restituire zero. Il successivo
`cap_clear(0)` produce `UC_ERR_WRITE_UNMAPPED` a PC `0x023DBFF4`, con `r0=0`.
Il percorso di controllo con allocazione riuscita conserva slot e registrati.
Il successore 1.3.1 sostituisce in luogo il solo corpo da 28 byte
(`a7ad1c38…b665f6`): la chiamata diretta all'allocatore lascia spazio a
`cmp/beq`, restituisce zero sul fallimento e chiama ancora lo stesso
`cap_clear` sul successo. Non cambia nessun ingresso, comparto, hook o layout
save e il blob storico resta immutato. Sulle V4 EN/IT, l'esecuzione Thumb reale
passa fallimento e controllo positivo: nessuna scrittura a zero, una sola
allocazione, ritorno `NULL` nel primo caso e azzeramento di tutti i 2.380 byte
nel secondo. Installer/readback e mutante passano 3/3; composizione legacy
EN/IT e la regressione mirata passano. La sandbox blocca `sysctl` e fa terminare
Unicorn prima del guest; la stessa suite fuori sandbox passa 3/3, limite del
banco registrato e non attribuito alla ROM. Restano frequenza del ramo sotto
pressione heap reale, candidata conservata, SAVE/cold e dispositivo.

La prima composizione completa ha inoltre scoperto un rifiuto corretto del
composer: i successori Plus-save e Borsa erano dichiarati dentro la riserva ma
senza una concessione di proprietà. La pipeline ora deriva esclusivamente i
due owner storici `sgp.plus` e `sgp.capacita_borsa` dalla mappa autenticata;
non assegna spazio libero e il confinement continua a limitare le scritture ai
736+4 byte del save e ai 28 byte del costruttore. La composizione reale EN fino
allo stadio `legacy`, con replay indipendente, passa.

La prima corsa fino a `rematches` ha poi isolato un distinto difetto del
composer, **SG-PIPE-REMATCH-01**: il modulo rivincite era già derivato dalla V4
prima della UI, ma lo stadio provava a derivarlo di nuovo dall'immagine dopo i
producer legacy. `a/0/5/6`, legittimamente cambiato dal fix pesca, falliva così
il pin della preimmagine V4. Writer, reader, peel e attivazione ora consumano
la stessa delta immutabile, rifatta dalla V4 e già legata alla ricevuta UI;
l'attivazione può cambiare solo il byte inert→active. Le composizioni complete
inermi fino a `rematches` e il replay passano EN
`b2973c79…15ccaeb` e IT `463a065e…2357bc`, rispettivamente 152.715.176 e
158.958.092 byte, senza ROM conservate. I 108 test mirati della pipeline
passano. È una correzione del builder, non un nuovo bug gameplay della ROM.

La distinta prova completa fino a `identity` passa inoltre con radice inerte e
owner attivi per entrambe le lingue: EN inerte `07f9e785…8ffa221`, attiva
`e07bff3b…4e8a6`; IT inerte `1002b2b5…729ef9`, attiva
`ca37cd1f…71d90e`. La concessione resta quella del verifier Guide di produzione
e il replay ricostruisce la stessa radice. I documenti di prova dell'attivazione
sono però sintetici e dichiarati: questa è copertura byte/ricevute, non una
cattura Android né accettazione runtime dei tre owner.
