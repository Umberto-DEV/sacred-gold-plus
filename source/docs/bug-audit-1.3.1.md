# Audit e correzioni dei bug ereditati — 31 ottobre 2026

## Freeze 1.3.1 nel ciclo tipi: diagnosi e successore — 6 novembre 2026

Le candidate formali correnti sono EN
`50ba570f97655cecc7b11bed06eb7f683283b191c1c21f02e49ad55f90fc7665`
e IT `c63cf9e993cbee9c38949baf9444dda3e365bddb15840aaa08905d9b02afbedb`.
Il raccordo `fairy_ai` aveva sostituito due istruzioni con un BL Thumb, ma
un ramo retail continuava a puntare alla seconda metà della chiamata. La
riproduzione della battaglia su core interprete mostra il salto nei dati e
il primo data abort; la controprova sul solo byte del ramo riattiva il menu.
La correzione a `0x02252138` porta il rientro a `0x022520CC`, riusando
l'indice già calcolato. Dieci scenari nativi per lingua distinguono prima e
dopo, senza stub del ciclo. Payload, dati di gioco e layout save invariati;
le build formali coincidono con le trial misurate. Il gate fisico IT su copia
ha completato Continua, SAVE nativo e cold Continue; la battaglia arriva da
Weavile e Honchkrow a Houndoom, esegue un turno e riapre il menu mosse.
L'esatta IT è installata sul percorso ufficiale e carica il save corrente.
La matrice host aggiunge quattro cicli SAVE/cold su due fixture autentiche
in EN/IT, con e senza Plus e con tre slot Borsa extra; limiti e delta nativi
sono riportati nella [verifica corrente](ui-1.3.1-validation.md).
Questo finding di regressione è separato dal conteggio storico
Daybreak e dal freeze Latios preesistente, la cui causa non viene dedotta
per somiglianza del sintomo. [Diagnosi completa](ai-scoring-1.3.1.md).


Stato corrente del follow-up del 3 novembre: **34 finding risolti**
(33 fix di componente e 1 già risolto dalla patch precedente), **0 fix
Daybreak pendenti sul dispositivo** e **0 candidati statici Daybreak ancora da
riprodurre**. L'ultimo gate Android ha verificato che l'AVD di prova contiene
già l'esatto APK successore corretto; il vecchio APK vulnerabile non è
installato. La campagna
ROM storica resta distinta e non è completamente chiusa.
Gate finale mirato: 176 test compiler/Portable, 32 distribuzione e 59 stadio 0
PASS. Il runner pubblico conclusivo su una copia composta soltanto dai file del
contratto pubblico passa integralmente: Class A raccoglie 2.249 test, ne esegue
1.919 e ne salta 330; Class B ne raccoglie 679, ne esegue 12 e ne salta 667.
Totale 2.928, zero failure. I tentativi globali interrotti descritti più avanti
restano evidenza storica e non sostituiscono questo esito finale. Non rimane
una scansione o un test in background.

## HG-T10: mismatch cinematografico corretto e integrato — 5 novembre 2026

La candidata corrente con il successore `legendary-scene-version` è EN
`02cccfbfc49b6addddba90385634ffdfde22b9ff3fbae3d85ae8f5603c5bf0af`
e IT `35d459e3fcf7cf127d6ff0aec94a5f502accfce390b2455b83fe189a5ca088f4`.
Il mismatch HG-T10 passa a `FIXED_COMPONENT / INTEGRATED_CANDIDATE`:
tre seam confinati nell'overlay 2 selezionano le risorse della scena Lugia
sulla mappa 244, conservando il percorso Ho-Oh. Il producer non usa nuova
riserva ARM9 e non cambia geometria ROM, identificatori o layout save.
La prova runtime sintetica EN/IT esercita i consumer cinematografici corretti
e il controllo Ho-Oh; non è un replay naturale della scena completa.

La normale progressione Plus continua a rendere irraggiungibile lo stato
storico anomalo. Freeze completo, battaglia e cattura non sono stati
riprodotti; nessuna nuova prova sul dispositivo fisico o SAVE/cold è attribuita a questi hash.
Il guard precedente della duplicazione Ho-Oh resta distinto dal nuovo fix.
Le sezioni storiche sotto conservano diagnosi, identità e limiti precedenti,
compreso lo stato allora `DEFERRED_NO_PATCH / FIXTURE_LIMIT`; non descrivono
più il mismatch come un difetto ancora senza correzione nella candidata.

Checkpoint precedente del 5 novembre: la composizione formale allora corrente
è EN
`5c5611844678d26bdc5677855da3aacbc1dd1700f97afec249b24532f2362f15`
e IT `c5a45d169e04fd85f17889f201ba7c6fe6f5d4ad43243b6a043a5ab848777f97`.
Le ricevute includono tutti i fix sorgente censiti, compresi HG-F05, HG-F08,
HG-F09, HG-F02 e HG-F13; abilita soltanto il Box portatile, lasciando controlli
Summary e rivincite configurabili inerti. Gli output formali sono byte-identici
alle trial sottoposte ai test runtime. La ROM fisica resta la precedente IT
`171b53b6…d64a0`: nessuna prova della candidata corrente sul dispositivo è
inferita dalla composizione.

Gate globale del checkpoint precedente del 5 novembre: `source/run_tests.py`
termina con exit 0 e
report JSON `full-suite-2026-11-05.json`. Class A raccoglie 2.093 test, ne
esegue 2.040 e ne salta 53; Class B ne raccoglie 885, ne esegue 626 e ne salta
259. Totale 2.978 raccolti, zero failure. I test Box passano 59/59 al feature
bench, 26/26 al package, 26/26 sulla ROM e 2/2 nel binding Android della IT
esatta. Gli skip restano limiti di fixture dichiarati e non diventano prove
funzionali. L'accettazione fisica della candidata corrente resta aperta perché
ADB non rileva il dispositivo; nessun salvataggio personale o file del
dispositivo è stato toccato.

## Candidate attive e prova conservativa — 4 novembre 2026

Il workbench privato ha composto da zero entrambe le lingue sullo stesso
snapshot di 793 sorgenti registrati, con politica riserva
`sgp131-resident-11` (`58834447e7643821e3c41bd78419b1cb6abd97deab9f16f4f42c57b52611bec5`).
Le due ricevute schema 2 arrivano allo stadio `identity` e dichiarano
`static_verified: true`; l'accettazione di release completa resta separata:

| Lingua | Base V4 autenticata | Candidata attiva | Byte | Stato |
| --- | --- | --- | ---: | --- |
| EN | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` | `618f0501d1355f5c7ee6d0301847222fd23a3d67701027190424bf28225fb13d` | 152.786.376 | Smoke locale; non installata fisicamente |
| IT | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` | `171b53b6c47555d54cb82c724569f26e9dfd92f51aa064545dd44b09179d64a0` | 159.029.292 | Smoke locale e installazione privata in-place |

Gli SHA-256 coincidono con le ricevute; le mappe sorgenti EN/IT sono identiche
e i pin correnti passano 94/94. Entrambe le candidate completano in melonDS
headless cold boot, Continue, campo e Squadra→R→PC nativo fino alla fase
`PC_RUNNING`, senza crash in 4.332 frame e con la copia save byte-identica.

La prova fisica IT è stata confinata a copie: Continue→campo→SAVE con due
conferme→cold restart→Continue torna allo stesso campo. La copia raw da 524.288
byte passa da `67285f…ac11` a
`e2c6a6f86ec2ff3082a9dfe0519bdd0616847413c230c798f0ce0522a1ea7be9`;
il save personale non viene mai sostituito. L'installazione canonica aggiorna
in-place soltanto la ROM Sacred Gold Plus da `420ec8b8…f059a` a
`171b53b6…d64a0`. Save personale
`67285f796c76d0042aadf88839bede46b90d610250773131aab35d3967a2ac11`,
file `.ml0` `268023…5801` e due configurazioni cheat `587651…be04` e
`cbe23…2fa4` restano invariati. La ROM canonica completa poi un avvio a freddo
fino al campo senza un nuovo SAVE. Il rollback verificato è conservato e i
file fisici temporanei sono rimossi. Due voci cache inerti, senza file fisico,
restano nella libreria per il comportamento fail-closed della build melonDS e
non sono ROM installate.

La precedente coppia effimera EN `410c3fc8…a4012` / IT
`baa02e54…c228`, costruita prima dell'ultimo snapshot sorgenti, rimane soltanto
una prova statica storica: non è la coppia attiva e non è stata installata.
Questa prova non promuove una release o un pacchetto giocatori: EN non ha prova
fisica e non tutte le funzioni sono state esercitate.

## HG-F02: facing laterale durante la discesa da Cascata — 5 novembre 2026

Stato `CONFIRMED_COMPONENT_EXACT_ACTIVE_EN_IT / FIXED_SOURCE_COMPONENT /
NATURAL_SURF_RUNTIME_TOOL_LIMIT`. Gli overlay 1 delle trial attive EN/IT sono
identici e confermano il percorso retail: una rotazione bloccata laterale
commette `currentFacing`, poi Giù supera il gate Sud e avvia il task senza
richiamare il setter. Il mismatch sopravvive 0/1/2 frame neutri; Giù solo resta
Sud. Una descrizione retail indipendente qualifica proprio il fronte laterale
“instead of down”, mentre lo slide forzato è il controllo sano che imposta il
facing prima del movimento.

Lo stage `waterfall-facing`, dopo `invisible-grass`, sostituisce esclusivamente
il BL riuscito a `0x021F252E` con un wrapper residente di 20 byte nell'owner
`sgp.waterfall_facing` (`0x023D8AEC..0x023D8AFF`). Il wrapper salva quattro
registri, mantiene SP allineato a 8 byte a entrambi i BL, imposta Sud e richiama
il task originale. I rami falliti e la salita separata da script/menu non
attraversano il seam. EN/IT, Down-only, 0/1/2 frame, ordine, ABI, mutanti,
confinamento e replay passano; geometria ROM e layout save non cambiano. La
fixture Surf naturale resta non disponibile, quindi non si dichiara rendering,
SAVE/cold o dispositivo.

## HG-F13: menu durante il salto del follower — 5 novembre 2026

Stato `CONFIRMED_RUNTIME_EXACT_ACTIVE_EN_IT / FIXED_SOURCE_RUNTIME_TEMP /
NATURAL_SAVE_DEVICE_PENDING`. Il precedente trial bounded non era una
confutazione del trigger storico: dopo un solo Giù il follower eseguiva il
normale `cmd=9/step=1`. Una scansione frame-esatta con un secondo Giù raggiunge
il salto follower reale `cmd=21/step=1`; aprendo X nella finestra e tornando da
Squadra zero/una/due/tre volte, EN e IT producono
`facingVector.y=0x6000,0xE000,0x16000,0x1E000`, sempre a
`positionVector.y=458752`. Ogni rientro aggiunge quindi esattamente `0x8000`.
Da fermo il vettore resta stabile e chiudere il menu lo riporta alla base. Una
seconda sporgenza del Percorso 45 ripete la progressione nel dossier privato.

La ricostruzione del lifecycle mostra che il menu mette in pausa i map object,
la pagina Squadra smonta e ricrea il renderer di campo, e
`ov01_022054E0` legge fase/frame ancora congelati e restituisce nuovamente la
stessa altezza dalla tabella. Il caller la somma al `facingVector` già
persistente: è distinto da HG-F05, che cancella il movimento da script e lascia
un singolo offset, ma condivide lo stesso vettore come portatore dello stato.

Lo stage `follower-menu-jump`, immediatamente dopo `waterfall-facing`, aggiunge
all'helper altezza il controllo nativo `MapObject_CheckMovementPaused`: in pausa
restituisce zero, fuori pausa conserva chiamata mode, getter fase/frame, bound a
16 e tabella immutata. La rimozione della copia stack della tabella immutabile
fa stare il controllo negli stessi 92 byte; cambiano 28 byte logici, tutti nel
helper, e soltanto lo stream compresso nello slot FAT invariato di overlay 1.
Un peel esatto ricostruisce l'output HG-F02, così la catena condivisa può
verificare entrambi gli writer dello stesso slot.

Il RED pubblico riproduce la progressione EN/IT sul vero command 21; il GREEN
mantiene `0x6000` per 0/1/2/3 ritorni, resetta alla base e non altera il
controllo da fermo né le copie save. Un interprete Thumb bounded decodifica il
postimage e prova uscita in pausa prima dei getter, ordine unpaused
mode→phase→frame→tabella, argomento map object, SP allineato e ripristinato;
mutanti del branch/call, stream, receipt e confinamento sono rifiutati. Passano
EN/IT diretti e il runtime EN composto dopo HG-F02. Restano save naturale,
altri sottomenu/ambienti, SAVE/cold e dispositivo; non è una garanzia universale
su ogni follower, sporgenza o emulatore.

## HG-F19: Kate dopo Jenn/Irene — 4 novembre 2026

Stato `CONFIRMED_COMPONENT_EXACT_V4_EN_IT / FIXED_COMPONENT /
FIELD_UI_RUNTIME_PENDING`. Sulle candidate V4 autenticate EN/IT, l'oggetto Kate
di Route 34 è la riga 7 dell'evento 35, script 9/entry 8 del membro 237; i due
trigger verticali richiamano invece l'entry 5. Dopo Jenn/Irene e il reload, lo
stato pre-lotta `0x4097=1` poteva quindi entrare lateralmente nell'entry oggetto:
`FacePlayer`, messaggio post-lotta 32 e fine, senza `TrainerBattle`. Il successivo
trigger verticale conservava l'orientamento alterato. Il controllo sano
verticale mostra il messaggio 28 e avvia l'allenatrice 118.

Il successore sostituisce il vecchio span di 38 byte `0x299..0x2BE` con 44 byte:
stato 0 conserva il dialogo precedente alle sorelle, stato 1 si ricongiunge al
percorso pre-lotta esistente dopo il movimento verticale, stato 2 mantiene il
retry del premio e stato 3 mantiene il messaggio 32. La crescita pari di sei
byte conserva l'allineamento dei movimenti; il membro diventa 3.482 byte e la
relocation aggiorna entry e puntatori successivi. Evento, coordinate, flag e
save non cambiano; la postimage bilingue è
`db88418abf2841158aac6e88215449519615288aa964716b939a5024a8636b24`.
Riproduzione, quattro stati, controllo verticale, confinamento, reapply e input
estraneo passano. Restano scena renderizzata, movimento/scheduler completo,
overlap del follower sui percorsi alternativi, SAVE/cold e dispositivo.

## Via Vittoria: highlight Volo da Johto — 4 novembre 2026

Il difetto ereditato è ora `CONFIRMED / REPRODUCED /
FIXED_COMPONENT / UI_RUNTIME_PENDING`. Sulle candidate V4 autenticate EN
`179edfb1…fbf90` e IT `2a2f0b43…3a156`, il banco Thumb esegue i veri
classificatori degli overlay 100 e 101. Il record conserva nome Via Vittoria
`124`, warp Percorso 26 `30`, flypoint `33` e coordinate `(28,7)`: da Johto il
gate riceveva il nome e restituiva `0`, mentre lo stesso punto con l'ID warp
restituiva `1`. Kanto, Indigo, Altopiano, Blackthorn, Viridian e `y=8`
controllano che non sia un flag, hitbox o allargamento regionale.

Il producer `victory_road_fly` sostituisce la sola funzione di 24 byte e
riconosce i due punti condivisi `(28,6..7)`, delegando tutto il resto al
classificatore originale. Cambiano 23 byte logici e 3.596 byte del flusso BLZ
ricompresso nello stesso slot overlay 101 da 53.576 byte; tabella, nome, warp,
FAT, y9, dimensione ROM e layout save restano invariati. Il producer è composto
transazionalmente dopo Pesca nel proprietario `legacy_native`; 79 prove mirate
complessive passano. Due postimage
diagnostiche private rileggono la semantica: EN `8a7e7232…e7219d3b`, IT
`8fa039e0…3e7a7ac`. Nessuna fixture naturale censita possiede il flag
`0x9D1`: menu Volo renderizzato, Continue→SAVE→cold e dispositivo non sono
ancora prove concluse.

## Pokégear pan/zoom: marker fuori viewport — 4 novembre 2026

Stato `CONFIRMED_COMPONENT_EXACT_CANDIDATES / FIXED_COMPONENT /
UI_RUNTIME_PENDING`.
Sulle V4 EN/IT il vero `PokegearManagedObject_AutoCull` dell'overlay 101 ha la
stessa preimmagine di 36 byte e decide il draw flag usando soltanto Y. Unicorn
conferma i confini `-1/0/216/217`, ma lascia disegnati `x=-512` e `x=+512`;
`autoCull=0` è il controllo sano e non modifica il flag. La mappa zoomata può arrivare a
`left=34`: Percorsi 40/41 assumono X logiche `-416/-424`, che l'OAM riduce a
`96/88` e fa riapparire dall'altro lato. D-pad, touch e zoom richiamano davvero
il culler dopo gli spostamenti. Non è corruzione save né duplicato del filtro
Via Vittoria. Le celle NCER centrate 16×16 qualificano X `-7..263` e Y
`0..199`. Una prima variante da 36 byte che sembrava richiedere solo +4/+8 B
usava però `ldrh`: tratta `-7..-1` come unsigned e non è un fix corretto. Il
redesign ABI-privato verificato usa `ldrsh`, conserva stack, `autoCull=0` e i
confini completi: la variante di riferimento misura 53.584 byte. Tredici
costruzioni equivalenti, ABI con X nei caller e oltre cento compensazioni NOP
non entrano. Il [banco pubblico](../sgp131/test_pokegear_autocull_rom.py) fissa
la migliore variante valida: confronto invertito più `MOVS/ADCS` trasforma il
carry in Boolean senza allargare i 36 byte e passa esattamente X `-7..263`, Y
`0..199` e `autoCull=0`; sulle postimage EN/IT produce però 53.580 byte, ancora
quattro oltre lo slot 53.576. Le vecchie varianti `ldrh` e quella che eseguiva
`MOVS` prima di `BHI` sono scartate, non candidate.

Il successore lascia i tre callsite e il loro `LR` invariati e trasforma i 36
byte originari in un trampoline `ldr/bx` seguito da zero; la logica signed vive
nel nuovo owner ARM9 `sgp.pokegear_autocull` a `0x023D8AC8..EB`. La compressione
canonica scende a 53.564 byte e viene riempita fino allo slot esatto di 53.576,
senza modificare FAT, y9, geometria ROM o save. Il thunk da 36 byte conserva ABI,
stack e registri callee-saved; EN/IT passano X `-7..263`, Y `0..199`, estremi,
`autoCull=0`, preimmagini, collisioni della riserva e composizione completa.
Restano UI renderizzata pan→zoom→pan, SAVE/cold e dispositivo.

## HG-F24: Lettore GB dopo evoluzione e Summary — 4 novembre 2026

Stato `CONFIRMED_COMPONENT_EXACT_V4_EN_IT / FIXED_COMPONENT /
PCM_UI_RUNTIME_PENDING`. Il banco autentica sulle candidate EN/IT la catena
macchina che rende deterministica la segnalazione storica: l'evoluzione avvia
la sequenza DS 1011, il dispatcher GB la traduce nella risorsa dinamica 1223,
il Summary per scegliere la mossa entra nella scena audio 57 e ripristina
l'heap allo stato 4, mentre al ritorno il flusso evoluzione non richiama né
`StartSequence` né `PlayBGM`. Il modello della lifetime perde quindi la risorsa
soltanto con Lettore GB attivo e passaggio dal Summary. I controlli GB OFF con
Summary e GB ON senza Summary conservano invece il materiale audio.

Questa è una riproduzione al componente basata su percorsi e digest reali, non
una cattura PCM o un'esecuzione completa della UI. Restano fixture naturale
qualificata, scelte accetta/rifiuta/annulla,
audio nativo end-to-end, SAVE/cold e dispositivo.

Il fix confinato usa un hook al ritorno Summary
`0x020767BC` e un wrapper Thumb di 32 byte: conserva l'helper originale e,
soltanto con GB Sounds attivo, richiede di nuovo la sequenza evoluzione 1011.
Poiché Unicorn locale termina con `SIGILL`/132 prima del guest, un interprete
Thumb-1 indipendente e ristretto ai soli opcode del wrapper esegue la postimage:
GB ON percorre helper→getter→`StartSequence(1011)`, GB OFF percorre soltanto
helper→getter; SP e registri callee-saved restano invariati. Cinque test focali
EN/IT, confinamento, rifiuto lingua/preimage, composizione legacy e reserve gate
passano. Il producer occupa `sgp.gb_sounds_evolution` a
`0x023D8AA8..0x023D8AC7`; il successivo thunk Pokégear lascia 20 byte liberi e
porta la politica storica di quella candidata a `sgp131-resident-11`. Geometria ROM e layout save
non cambiano. Il banco non
sostituisce una cattura PCM/UI: serve ancora un trace/capture melonDS EN/IT.

## LINK-WEB-01: regole custom e Cuorugiada — 4 novembre 2026

Stato `CONFIRMED_COMPONENT_EXACT_CANDIDATES / FIXED_COMPONENT /
UI_LINK_RUNTIME_PENDING`. Il getter ARM9 a `0x020290FC` restituisce
per la clausola Cuorugiada l'intero `totalLevel` invece del solo bit `0x8000`.
Il codice Thumb reale sulle V4 EN/IT restituisce `0x8000`, `0x8032` e `0x8FFF`
senza maschera; sei consumer confrontano poi esattamente con `0x8000`.
Perciò ruleset custom che combinano flag e limite totale saltano Cuorugiada,
limite di due leggendari e controlli associati. GS Cup integrata `0x8000`,
limite `0x0032` senza flag e rule 3 del livello totale sono controlli sani.
Manca una fixture naturale Mystery Gift/menu/link. Il fix unico nel getter usa
un hook di otto byte e un thunk di 24: il banco ARM sulle candidate reali
conserva regole 0–12, invalidi e GS Cup, mentre `0x8032/0x8FFF` diventano
`0x8000` solo per la regola 13. Il payload occupa il nuovo owner registrato
`sgp.soul_dew` a `0x023DEB00..1F`; i successivi 32 byte appartengono ora al
guard Wonder Card e il canarino 1.1 resta intatto. Producer, rilettore,
politica della candidata `sgp131-resident-11` e
composizione bilingue completa passano; layout save e geometria ROM non
cambiano. Restano menu/link naturale, SAVE/cold e dispositivo.

## HG-SEC01: Wonder Card e ID decorazioni — 4 novembre 2026

Stato `CONFIRMED_COMPONENT_EXACT_V4_EN_IT /
CONTROLLED_REPLAY_TAG6_TO_OOB_WRITE / FIXED_COMPONENT /
FULL_CARD_DELIVERY_NOT_RUN / NO_ACE_RUN`. Il tag 6 porta due
interi `kind,id` a check e consegna; per i sigilli né il dispatcher né i leaf
impongono `1<=id<=80` prima di indicizzare `inventory[id-1]`. Un modello
replay ARM RAM-only con canary esegue il dispatcher, check, writer e leaf reali
delle candidate EN/IT: ID 1 scrive l'offset 288, ID 80 l'ultimo byte valido
367, ID 81 il primo byte fuori limite 368 e `0xFFFF` l'offset 65822. Check
accetta anche gli ID invalidi; receive incrementa un solo byte e invoca la
coda. Le routine sono ancorate con digest esatti (`ScrCmd_MysteryGift`
`0x0204BDA4`, check `0x0204C550`, give `0x0204C588`, leaf writer
`0x0202CCAC`, action table `0x020FC0E8`). Nessuna Wonder Card, copia save,
consegna end-to-end o catena ACE è stata eseguita. La catena pubblica ACE resta
dimostrata solo su SoulSilver EN.

Il successore valida sigilli `1..80`, fashion `0..99` e background `0..17`
nel check e nel give; i writer interessati falliscono inoltre in modo chiuso
se chiamati direttamente. Input invalidi restituiscono `false` nel check e non
mutano l'oggetto. Il validator condiviso occupa i 32 byte registrati come
`sgp.wonder_card` a `0x023DEB20..3F`; hook, postimage, canarino seguente,
confinamento, geometria ROM e layout save sono verificati sulle candidate V4
EN/IT. Il producer è composto dopo Cuorugiada nella catena legacy e le prove
ARM reali passano. Il percorso artificiale di give conserva la semantica retail
della coda e può ancora marcare il dono come ricevuto dopo aver rifiutato la
decorazione invalida: è un limite transazionale distinto, senza mutazione
dell'inventario né scrittura OOB. Gift Pokémon/item usano dispatch separati.
Restano card/consegna naturale, persistenza SAVE/cold, catena ACE Plus e
dispositivo.

Il ciclo finale ha chiuso separatamente le quattordici cause rimaste: output
builder/runtime privati e no-replace; identità root/lock/PID/transaction/journal,
consumer e scratch del workbench; pacchetti RSP limitati e peer loopback reale;
snapshot sorgenti descriptor-bound e limitato; hash espliciti delle evidenze di
promozione e della configurazione meccaniche; JSON di accettazione limitato con
chiavi duplicate rifiutate; label CSV neutralizzate. Le revisioni ostili hanno
aggiunto casi parent-swap, inode lock sostituito, PID riusato/EPERM, journal
estraneo, lease senza sessione, FIFO, `..`, symlink/hardlink e formula/control
injection. Il workbench esegue ora compilatori e verificatori con cwd ottenuta
via `fchdir` sull'inode scratch pinnato: lo swap post-yield non devia letture,
scritture o cleanup. Il confine resta cooperativo contro processi concorrenti
dello stesso account, che possono causare rifiuto/DoS ma non sono autorizzati
come writer durante l'operazione.

Il finding del compilatore è chiuso a livello componente: il binario Apple CLT
effettivo viene autenticato prima del primo processo e 27/27 test del contratto
passano. L'identità esatta del runner Xcode resta un limite di validazione della
pubblicazione, non una riapertura della causa locale. Per Android il sorgente
ora genera il token con `getrandom` per processo, rifiuta UID shell e consente
un solo bootstrap a root; il controller conserva il segreto soltanto in una
ricevuta nuova `0600` e non lo stampa. I test host C++/Python passano. Il gate
del 5 novembre sull'AVD privata ha identificato l'APK installato come l'esatto
successore corretto (`6c6a2d32…1532`); il precedente APK vulnerabile
(`fb76c0b8…48cc3`) non è installato e il processo non era in esecuzione. Non è
stata necessaria alcuna reinstallazione. Il finding passa quindi a
`fixed_component`; l'esecuzione end-to-end dell'endpoint Android resta un gate
di validazione separato e non viene inferita dall'identità dell'APK.

Binario ROM separato: H1 è ora un bug interno dimostrato e corretto nei
sorgenti. Due interazioni Plus in `a/0/3/2` (membri 71/440) erano marcate come
oggetti nascosti e portavano lo scanner ARM ai flag `E3F3`/`E3EE`.
`legacy-events` cambia soltanto i due halfword tipo 2→1. Test unitari/confine,
archivi reali EN/IT e composizione/replay completa EN/IT passano; non è ancora
una ROM o una release accettata e mancano prove visive, save e dispositivo.

Il ciclo ROM successivo ha chiuso a livello componente **V-CHATOT**: 24 ID
`612E..6139`/`619E..61A9` producevano puntatori dentro `SAVE_CHATOT`. Le 12
sequenze provano entrambe le direzioni (script→audio e registrazione→gate), i
consumer reali e i controlli adiacenti. `HF02` migra una volta il gate
zero/nonzero dopo LOAD accettato e intercetta soltanto SetVar/VarGet della
famiglia; layout e audio restano invariati. Sei test sintetici, 12 test ARM
EN/IT e composizione UI completa EN/IT passano. Otto cicli raw-save su copie
zero/HF01, senza Plus/con Plus/Borsa estesa, completano SAVE nativo e cold in
entrambe le lingue con audit circoscritto integrale PASS e Chatot invariato.
Mancano scene rappresentative e dispositivo: non è una release accettata.

La ricerca communication qualifica inoltre il vecchio SG-19. Il vero
`SavePalPad_Merge` ricostruisce i 32 byte Pal Pad usati impropriamente dal bank
`3F00..3FFF`: con Pal Pad vuoto li azzera, con entry 0 valida li sostituisce con
dati del peer. Trade selection e link battle raggiungono davvero il merge;
l'ingresso semplice in Union Room non è ancora un trigger dimostrato. Le
candidate HF01 conservate `90435d3c…d5fc18`/`420ec8b8…f059a` hanno una race al
primo upgrade: merge→primo Check perde la sorgente, Check→merge la preserva.
HF02 corrente migra sul Continue prima del campo e chiude il caso a livello
componente/cold-save, ma mancano due peer reali, link battle/mixing records,
SAVE+cold post-wireless e New Game. Non dichiarare le candidate HF01
universalmente protette.

Il ciclo retail **HG-B11 Peso Ball** ha riconciliato una vecchia correzione
Plus che non compariva più nel registro pubblico. La retail US/IT e le Plus
1.01–1.04 contengono `90088542`: il ramo calcola 1024 in `r0` e confronta il
tasso di cattura `r5`, così anche la fascia neutra 102,4–204,7 kg perde 20.
Dalla Plus 1.1 la finestra è `91088842` e confronta invece il peso `r0`; la
stessa correzione è presente nelle 1.2.5 e candidate 1.3.1 EN/IT. Il
riproduttore read-only autentica 13 immagini, 96 casi Peso Ball sui quattro
confini, nove controlli Rapid Ball e nove controlli separati Velox Ball; due
run producono il medesimo `result.json`, SHA-256
`7268feda856fd75d641506b1c5a93bd75ff9969373041455a6931d7c6b09e0cb`.
Il runtime Unicorn locale termina con `Illegal instruction` prima del mapping:
la prova esegue la semantica decodificata degli halfword reali, non è una
cattura giocata o un'esecuzione CPU nativa. Nessuna nuova patch è necessaria.

Il ciclo retail **HG-B01 Fire Fang/Wonder Guard** ha dimostrato un off-by-one
ancora presente dalla Plus 1.04 alle candidate 1.3.1. Le otto immagini
autenticate sono 1.04 Classic, 1.2.5, 1.3.1 bugfix e 1.3.1 UI, EN/IT; gli hash
logici dell'overlay 12 sono rispettivamente `a31cef88…620983`,
`37d98c7a…d98894` e `7ea4080e…263ee4`. In tutte, le mosse 424/467 sono gli
unici membri con effetti 273/272. Il helper `ov12_02258440` usava 273 nel gate
delle mosse a due turni invece di 272: Fire Fang saltava i due consumer di
Wonder Guard, mentre Shadow Force li raggiungeva già nel turno non dannoso.

Il riproduttore privato esegue i byte ARM reali dei due consumer con sei seam
foglia deterministici: 16 sequenze per immagine, originale e corretto, per 512
esecuzioni native. Fire Fang neutra e resistita attraversano Wonder Guard
prima del fix e vengono fermate dopo; Shadow Force neutra viene erroneamente
fermata durante la carica prima del fix, poi salta il controllo e lo raggiunge
nel turno d'impatto. Fire Fang superefficace, assenza dell'abilità, Tackle,
Ember, Fly, Bide, Ice Fang e Thunder Fang sono controlli invariati.
`result.json` ha SHA-256
`8dec6ee7dd63062ae6773c7b6c26f414a461e7f2d1341c8411a14603a0b766fa`.

La prima correzione TDD `05 d1→05 e0` qualificava Fire Fang ma ometteva la
seconda metà dell'off-by-one; la revisione primaria pret l'ha respinta prima di
una candidata. Il postimage canonico nello stadio `type_consumers` cambia
soltanto `0x0225848C` da `11 32` a `10 32`, cioè il byte fisico all'offset
logico `0x20BCC`, e conserva il branch `05 d1`. Il test rettificato è passato
da rosso a verde e sorveglia contesto, preimmagine, branch, delta dichiarato,
mutanti e composizione/peel dello stadio `abilities`. Cinquanta test mirati e
la catena EN/IT passano. Non cambia alcun archivio, formato save o dato
Pokémon. Le ROM originali sono rimaste in sola lettura e non è stata conservata
una nuova candidata; restano lotta renderizzata, Continue/SAVE/cold e
dispositivo.

Il ciclo retail **HG-B02 Rage/stati volatili** ha poi dimostrato la causa
diretta nell'intera famiglia Plus autenticata. Nel controller pre-turno
l'halfword pair `01 40` applicava `status2 &= STATUS2_RAGE`: scegliendo una
mossa diversa da Rage conservava proprio Rage e cancellava ogni altro stato
volatile. Il riproduttore privato esegue la funzione ARM reale originale e la
correzione canonica `81 43` su otto immagini 1.04/1.2.5/1.3.1 EN/IT. Ventinove
sequenze per immagine coprono ogni campo `status2` separatamente, i quattro bit
Attract, il bit 7 riservato, l'aggregato Baton Pass, `0xFFFFFFFF`, Rage
selezionata/assente e quattro battler: 464 esecuzioni native. Due run producono
lo stesso `result.json`, SHA-256
`96afa553d77915d92a81bea6a9155d75546a7bc040e1484eb43fb94b24c5ac05`.

**HG-B03 Transform/Rage** è mantenuto come manifestazione storica collegata,
non contato come secondo fix. La catena reale raggiunge il consumer client del
comando `0x27`: con `STATUS2_TRANSFORM` presente non scrive le quattro mosse e
i PP nel PartyMon; dopo la cancellazione errata del bit esegue invece otto
`SetMonData`, mentre la maschera Mimic esclude soltanto gli slot dichiarati.
Il consumer è stato eseguito sui byte di quattro immagini con quattro controlli
per immagine. La correzione HG-B02 preserva Transform e chiude questo gate al
livello componente. Restano il setter su un Pokémon cifrato reale, l'uscita
naturale dalla lotta, la copia nel party residente, SAVE/cold e dispositivo;
non viene inferita la persistenza grezza nel `.sav` da questa sola prova. Due
run del riproduttore downstream sono byte-identici, SHA-256
`74370ad04150d3ca9440323f6fba7cd3604a2967c9f0a392d11429ee9f0a99e4`.

Il fix TDD è aggregato nello stesso writer overlay 12 di `type_consumers` e
non aggiunge un secondo writer BLZ. La funzione originale di 340 byte è pin-nata
da SHA-256 `6b1cc1e0…a2de0`; il delta cambia soltanto i due byte al sito
`0x022493FC`. La composizione EN/IT conserva 200 byte di margine nello stream,
lo stadio `abilities` e il suo peel mantengono il postimage, e 133 test mirati
passano (61 skip di fixture opzionali). Nessun formato save, archivio o dato
Pokémon viene modificato e non è stata prodotta una nuova ROM candidata.

Il ciclo successivo **HG-B04 Pursuit/Acid Rain** ha isolato un secondo difetto
retail, questa volta nello script battaglia `a/0/0/1:153`. Dopo aver salvato
`battlerIdFainted` in `tempData`, lo script riusava il primo per il loop EXP ma
poi eseguiva `SUB_TO_ZERO FIELD_CONDITION, TEMP_DATA`: il prestito aritmetico
accendeva bit meteo e di campo inferiori e il battler non veniva ripristinato.
La scansione binaria trova la stessa preimmagine in tutte le 30 immagini Plus
EN/IT locali esaminate. Il fix primario è `SET BATTLER_FAINTED, TEMP_DATA` e
cambia soltanto gli offset membro `0x398` e `0x39C`.

Il riproduttore privato autentica otto immagini, esegue il consumer nativo
originale e corretto su 20 scenari ciascuna e totalizza 320 esecuzioni. Copre
campo vuoto, pioggia, sabbia, sole, grandine, Uproar, Gravity, Fog, Trick Room,
combinazioni e battler 0/1/3; due run producono lo stesso JSON, SHA-256
`69d87dfc0f6d161b7e7ab49c6319e02cc364226ff0955d828102aaa1f9842eac`.
Il producer/checker `pursuit-script` pin-na archivio e membro, conserva il name
block storico, modifica un membro su 297 e rifiuta reapply e mutanti. La
composizione/replay reale `legacy` EN/IT passa. La chiusura resta al livello
componente/sorgenti: dispatcher completo, battaglia
renderizzata, loop Castform/Cherrim, link host/client, SAVE/cold e dispositivo
sono limiti dichiarati. Nessuna ROM o save è stata scritta.

Il ciclo retail **HG-B05 U-turn/tentennamento da oggetto** ha poi confermato
che il controllo tardivo King's Rock/Razor Fang leggeva l'oggetto dal battler
attaccante quando lo slot era già occupato dal subentrante. Il difetto produce
sia un falso negativo (oggetto sull'uscente, subentrante senza oggetto) sia un
falso positivo (uscente senza oggetto, oggetto sul subentrante). Il banco
privato autentica otto immagini Plus EN/IT, esegue 20 scenari per immagine e
160 chiamate native; due run byte-identici producono `result.json` SHA-256
`f9f09132446d13f3b0367540cc5ec38ab4401c1ade1d6dd4ac475c1f8777a896`.
King's Rock, Razor Fang, nessun oggetto, roll 0/9/10/99, mossa incompatibile,
fallimento, danno zero, bersaglio KO/assente e percorso senza cambio separano
la causa dai gate successivi.

La correzione registra nello script pivot `a/0/0/1:175` l'effetto effettivo
dell'oggetto dell'uscente, rispettando Klutz/Embargo, e il suo modificatore.
Due wrapper Thumb di 68 byte nel margine già revisionato di
`c8.module-stubs` fanno leggere e cancellare quello snapshot ai due soli getter
di `TryItemFlinch`; senza marcatore delegano ai getter retail. Il resto della
funzione, inclusi ordine dei fallimenti, danno, RNG, idoneità mossa e HP
bersaglio, rimane byte-identico. Test TDD sul codice ARM coprono i due versi,
il percorso ordinario, l'ordine dei gate e mutanti; la composizione e il replay
completi EN/IT fino a `uturn-flinch` passano. Gli output sono rimasti transitori
in memoria: EN `ad2db33…1a3f`, IT `8e418fa7…686f`; nessuna ROM o save è stata
conservata. Restano battaglia naturale, doppio/link tra build uguali,
SAVE/cold e dispositivo. Il link tra build corretta e non corretta può divergere
nel numero di chiamate RNG e non è una configurazione supportata.

Il ciclo retail **HG-B06 icona status invisibile** ha distinto l'errore grafico
dalla guarigione reale. Il subscript condiviso `a/0/0/1:221` eseguiva
`SetHealthbarStatus(NONE)` subito dopo il messaggio e soltanto dopo leggeva
`msgTemp`: i rami 5 (Mente Locale/Own Tempo) e 6
(Indifferenza/Oblivious) cancellavano correttamente confusione o attrazione,
ma avevano già nascosto l'icona dell'eventuale status persistente. Il campo
`BMON_DATA_STATUS` non viene toccato in quei rami.

Il riproduttore privato autentica otto Plus EN/IT, il membro di 236 byte, la
tabella comandi e il vero `BtlCmd_SetHealthbarStatus` Thumb. Venti sequenze per
input coprono sonno, veleno, iperavvelenamento, bruciatura, congelamento,
paralisi, assenza di status, entrambe le abilità e le cinque cure persistenti
come controlli. Due run byte-identici totalizzano 320 esecuzioni script e 200
native; 15 casi per input divergono solo nell'emissione grafica. Il JSON ha
SHA-256 `1c48cb8cd3fb624ce336fbf0731a74b9d982b893ed304def31bf5bd5c9763a2d`.

Il producer `status-icon-script` mette i due confronti volatili prima del
clear e duplica `WaitButtonABTime 30` in ciascun ramo: il membro cresce di 16
byte, ma messaggio, attesa e ordine delle mutazioni rimangono uguali. I rami
0–4 conservano il clear dell'icona; i rami 5/6 non lo emettono e preservano lo
status persistente e gli altri bit volatili. Test TDD, mutanti, rilettura NARC
e composizione/replay reali EN/IT passano insieme a HG-B04/HG-B05. Il NARC
finale dei tre producer è identico nelle due lingue (`3fe79ec9…e85597b`);
gli output ROM transitori EN/IT sono `c4eb3c12…145892` /
`8a5443ed…a9b43c` e non sono stati conservati. Restano renderer e battaglia
naturale, switch-out/in, doppio/link, SAVE/cold e dispositivo.

Il ciclo retail **HG-B07 Pressure/cambio immediato** ha confermato la scissione
fra la copia battaglia e il PartyMon. Il percorso PP ordinario emette il comando
di copia dopo il costo base e Pressure; `CheckIgnorePressure`, usato più tardi
da Counter, Mirror Coat, Magic Coat e Snatch, decrementava invece soltanto
`battleMons`. Il cambio manuale autentico ricarica poi i quattro PP dal
PartyMon e fa ricomparire l'unità non sincronizzata. Il limite a un PP, turno
intermedio, U-turn, KO e bersaglio senza Pressure distinguono la causa dal solo
refresh grafico.

Il riproduttore privato autentica otto immagini Plus EN/IT e per ciascuna
esegue 20 sequenze: 160 chiamate del helper reale, 320 del loop PP reale di
`BattleSystem_GetBattleMon` e 24 del vero `BtlCmd_UpdateMonData`. Prima del fix
nove sequenze per immagine ricaricano un PP più alto; dopo, zero. Il risultato
di due run è byte-identico, SHA-256
`6d1c1745b72c714baac45dc0c5fcf28e5a5f662bb073efae463610b46e6192a9`.
Metal Burst è separato dalla fonte storica: 16 esecuzioni del vero
`BtlCmd_TryMetalBurst` sulle stesse immagini mostrano che il successo raggiunge
il helper e il fallimento no. È quindi confermato al componente, non come prova
di cartuccia o battaglia naturale.

I producer `pressure-switch-effects` e `pressure-switch-subscripts` cambiano
soltanto `a/0/3/0:{89,144,227}` e `a/0/0/1:{139,146}`. Su ogni successo
inseriscono `UpdateMonData ADD BMON_DATA_STATUS, 0`: il valore resta invariato,
ma il consumer esistente esegue la copia BattleMon→PartyMon. Pre/post-hash,
percorsi fallimento, mutanti, reapply, geometria NARC e merge disgiunto con
Pursuit/U-turn/icona status passano; anche composizione e replay reali EN/IT
sono verdi. Nessun formato save, ABI o riserva cambia
e nessuna ROM o save viene scritta. Restano receiver asincrono completo,
battaglia naturale singola/doppia/link, SAVE/cold e dispositivo.

Il ciclo retail **HG-B08 level-up durante Transform** ha quindi confermato una
causa distinta. `BtlCmd_Transform` copia specie, cinque statistiche, mosse,
tipi, forma e abilità, ma non livello, amicizia o HP. Dopo il level-up,
`BattleSystem_ReloadMonData` ricaricava però Attacco, Difesa, Velocità,
Attacco Speciale e Difesa Speciale dal PartyMon prima di controllare
`STATUS2_TRANSFORM`; il risultato era un BattleMon ibrido con forma e mosse
copiate ma statistiche della specie originaria. Lo stesso chiamante centrale è
usato dal level-up e dai due percorsi successivi di apprendimento mossa, quindi
una patch al solo primo call site sarebbe incompleta.

Il riproduttore privato autentica otto immagini Plus EN/IT e per ciascuna
esegue 16 sequenze della vera funzione Thumb, con sole seam controllate per
PartyMon, `GetMonData` e maschera Mimic. Le 128 esecuzioni originali osservano
sei sovrascritture distinguibili per input; il caso con statistiche uguali è
un negativo di osservabilità. Il risultato rosso è deterministico, SHA-256
`f34586647fa3b926a640d2fb08a7f440ba81444748b4e3f2d2b5ac52869361b9`.
Un replacement source-owned di 340 byte, hash
`41ad8522c1920ccf38115b5e971d28ec9ae0126536756d002379e0624eb2f942`,
mette sotto il guard soltanto le cinque statistiche: altre 128 esecuzioni
azzerano le divergenze e lasciano verdi Non-Transform, Mimic, livello,
amicizia, HP/HP massimi, mosse/PP e esperienza. Il risultato verde privato è
`c74153a56502824282ec5efffa1ff742c26c5d25b00d21ce7e1b82d5d8ab82c0`.

Il producer fail-closed è composto nello scrittore condiviso dell'overlay 12:
preimmagine, literal pool, compilatore, target Thumb, span, BLZ canonico,
FAT/y9 e CRC UI sono autenticati. I test unitari e l'applicazione reale V4
EN/IT passano; 36 test mirati EN/IT di replay, peel e mutanti passano dopo aver
aggiornato il banco al nuovo delta compresso di 28 byte. La battaglia naturale
con e senza nuova mossa, switch/fine lotta, doppio/link, SAVE/cold e dispositivo
restano aperti. La suite globale contiene
inoltre errori indipendenti `archive delta type` negli stadi successivi: non
sono attribuiti a HG-B08 né nascosti come PASS. Nessuna ROM o save è scritta.

Il ciclo retail **HG-B09 Torre Lotta/1792 vittorie** ha isolato un troncamento
distinto. Il contatore persistente `currentRound` è un halfword e satura solo a
`0xFFFE`; non si azzera a 255. `FrontierFieldSystem_SetRandomFrontierTrainers`
lo riduce però a otto bit sia nel ramo da sette avversari sia in quello da
quattordici prima di chiamare il selettore. Il selettore tratta già ogni valore
`>=7` come fascia 200–299: al round 256 riceve invece zero, ai round 258/262
può riproporre i Palmer e al round 512 il ciclo ricomincia. Il producer da 174
byte (`1e202231…fbc97`) e il selector da 124 byte (`116f286b…01c6`) sono
identici in dieci Plus EN/IT 1.04, 1.1, 1.2.5, V4 e 1.3.1.

Il banco privato esegue entrambi i corpi Thumb reali con sole seam
deterministiche per PRNG, divisione Nitro e confronto duplicati. Diciotto
sequenze per immagine producono 360 esecuzioni: 110 casi originali divergono e
zero dopo la correzione. Sono coperti Single, Double, Wi-Fi, Multi, Link e
mode 6; round 0/2/6/7/255/256/257/258/262/263/512/65534; Palmer legittimi e
spurii; precedenza del round alleato, unicità ID, contatore e canarini. Due run
generano lo stesso `result.json`, SHA-256
`c0ec4f3582c1c698e6b4d56cef359c486dfb1948d2d9158dd7b9be1d4acbb94f`.

Lo stadio pubblico `battle-tower-wrap` sostituisce quattro halfword in tre
span: nel ramo Multi/Link copia il valore pieno invece di mascherarlo e nel
ramo Single/Double/Wi-Fi neutralizza i due shift. Solo sette byte logici
differiscono; caller, selector, lingua, ricevuta, geometria e reapply/mutanti
sono fail-closed. Quattro test specifici, 67 test del registro/stadio e la
composizione diretta dopo `lottery-id` sulle V4 reali EN/IT passano. Non sono
state scritte ROM o save. Restano una serie naturale Plus oltre 1792,
rendering e BP, un peer link reale, Continue/SAVE/cold e dispositivo; la fonte
HG 2024 usa una streak modificata, mentre la serie naturale 2009 è Platinum.

Il ciclo retail **HG-B12 Pellearsa/IA** ha invece trovato un difetto ancora
presente. `Basic_CheckForImmunity` confrontava l'abilità 26 (Levitazione) due
volte; il secondo ramo controlla il tipo Acqua e deve confrontare 87
(Pellearsa). La firma è identica nelle retail US/IT, Plus 1.01–1.04, 1.1,
1.2.5, V4 e candidate 1.3.1 EN/IT: 13 immagini autenticate. Il riproduttore
privato decodifica 104 scenari e produce due volte lo stesso risultato,
SHA-256 `c02b728db2bb113c6843d288a64a297a851d886ad9786902d4be5c994966cda4`.
Solo Pellearsa+mossa Acqua diverge; Pellearsa+Fuoco, Rompiforma+Pellearsa,
Assorbacqua+Acqua, Levitazione+Terra, Elettrorapid+Elettro e Fuocardore+Fuoco
restano controlli negativi coerenti.

La correzione TDD è ora nello stadio `ai-immunities`. Cambia una parola
26→87 nell'overlay 10 caricato e la copia al membro 0 di `a/0/9/9`, senza
normalizzare il NARC retail. Sulle immagini correnti EN/IT l'applicazione è
deterministica dopo l'integrazione HG-B14/HG-B15: EN `90435d3c…fc18`→`700c62e1…3fca`,
IT `420ec8b8…059a`→`df5daaef…250f`. Il verificatore usa due decoder BLZ,
ricompressione canonica, rilettura NARC indipendente, confronto degli altri
file e confinamento nei due slot; osserva un byte nel membro NARC e 15 byte
logici complessivi nell'overlay 10 per HG-B12+HG-B14+HG-B15. Non è stata scritta o
conservata una nuova ROM candidata. Restano una
lotta controllata che osservi la scelta mossa, i casi Android e il ciclo
Continue/SAVE/cold su copia; il formato save non è toccato.

Il ciclo retail **HG-B13 immunità doppio tipo/IA** ha quindi dimostrato un
secondo difetto del cambio post-KO. In sei Plus EN/IT autenticate,
`ov12_02252054` conserva `NO_EFFECT|SUPER_EFFECTIVE` per Gligar/Elettro,
Aerodactyl o Skarmory/Terra e Girafarig/Spettro. Il consumer reale sceglie così
Porygon/Thunderbolt contro Gligar invece di Porygon2/Geloraggio. Invertire
l'ordine e tre immunità singole separano il difetto dal tie-break.

La correzione è integrata nello stadio `ai-scoring`: il halfword a
`0x02252202` passa da `0420` a `0c20`, facendo prevalere un'immunità già
rilevata senza cambiare tabella tipi o danno. Il riproduttore privato passa
6/6 (`ccefe0ff…f2b467`); la batteria pubblica AI passa 32/32, inclusi 104.976
abbinamenti tipi, mutanti, chiamanti e BLZ, mentre stadio/composizione e builder
passano 81/81 e 29/29. Applicazione ROM EN/IT 9/9 e controlli nativi 2/2 sono
verdi. Nessuna ROM successore è stata conservata: restano lotta renderizzata,
Continue/SAVE/cold e dispositivo.

Il ciclo **HG-B14 gate di cambio/Arena Trap** è ora chiuso al livello
sorgente/componente. Il banco esegue il gate nativo dell'overlay 10 e la vera
`BattlerCanSwitch` dell'overlay 12 su sei input EN/IT: 96 casi, 42 divergenze
attese, digest `0a464755…3cf0a`. Volante, Levitazione, Magnet Rise e Shed Shell
passano da falso blocco ad ammesso; grounded, Iron Ball, Gravity, Pedinombra,
Magnetismo, vincolo, Sand Veil e assenza di trappola sono controlli. Il prefisso
`0x022203B4` di 16 byte è l'unico nuovo intervallo dichiarato; includendo il
byte HG-B12, il delta logico dell'overlay 10 è 15 byte. Output solo in memoria
dello stadio: EN `51ad07e5…1a76f7`, IT `e14b09ef…315e6`. Restano lotta
giocata, candidata conservata, SAVE/cold e dispositivo.

Il ciclo **HG-B15 cambio verso abilità assorbenti** è chiuso al livello
sorgente/componente. La prima proposta correggeva soltanto il candidato e
occupava per errore la parola `0x0222B268..26C`, che la y9 dichiara come
tabella static-init: i test iniziali passavano, ma la revisione indipendente
l'ha scartata prima di produrre una ROM. La variante finale intercetta sia
l'abilità attiva a `0x0221FF10` sia il candidato a `0x0221FFC6` e usa soltanto
i 20 byte liberi `0x0222B26C..280`. Il helper ammette esattamente
Assorbivolt/Elettrorapid e Assorbacqua/Pellearsa, lasciando Fuocardore sul solo
match esatto.

Il riproduttore CPU autentica sei Plus EN/IT: 96 casi, 24 divergenze prima e
zero dopo, SHA-256 risultato `2fd8a4fdd960dab34f996e9269e310ab6e1687f39be44d3050b0e0304dddb778`.
Le abilità nuove già attive ora evitano il cambio inutile; candidati nuovi
raggiungono la stessa moneta RNG dei vecchi. Ordine, numero e siti RNG, KO,
uovo, mossa di stato, tipo errato, Assorbacqua, Assorbivolt e Fuocardore sono
controlli; sui 256 ID possibili il helper ammette solo `{10,78}`, `{11,87}` e
`{18}`. Il delta combinato HG-B12/14/15 è di 48 byte logici, overlay
`6365fa4f…0120`; output solo in memoria EN `700c62e1…3fca`, IT
`df5daaef…250f`. Restano candidata conservata, lotta, SAVE/cold e dispositivo.

Il ciclo **Pokéathlon wrap del riepilogo Amicizia** è chiuso al livello
sorgente/componente. Il contatore nativo in overlay 98 restituisce correttamente
un `u16` 0–493; overlay 99 lo troncava con `strb` a `summary+0x16` e il getter
lo rileggeva con `ldrb`. Il riproduttore autentica 13 immagini e sulle due
candidate correnti esegue contatore, writer, getter e mapper reali: 38 casi
vulnerabili producono sei divergenze, gli stessi 38 dopo la correzione zero.
I confini 254/255/256/257 e 455/456/493, il percorso diretto e i campi adiacenti
sono controlli; digest `8f7bc818827a58229f3b557063142c0128a44916944f1ce8e2fd196b7a2b6316`.

Lo stadio `pokeathlon`, dopo `trainer-fixes` e prima di `controls`, sposta il
campo nel padding allineato `+0x1A` e usa `strh`/`ldrh`: quattro byte logici,
solo file/overlay 99, nessun FAT/y9/header/layout save. La ricompressione ha
inoltre trovato un limite reale nel selettore BLZ: fra stream della stessa
lunghezza il massimo prefisso poteva sovrapporre sorgente e destinazione di un
byte. Il compressore conserva l'output storico quando sicuro e sceglie un altro
cut equivalente quando necessario; stream sicuro 13.708 byte
`e6c157762956be2e9d5f5fae3670f91727b3b7a578430939839b1c57cca337f9`.
Quattro test nativi privati, 88 test fix/codec e 97 test stage/builder passano.
Restano stanza renderizzata, Continue/SAVE/cold EN/IT e dispositivo; nessuna
ROM successore è stata scritta.

**HG-D02 Azurill→Marill è ora riprodotto, non corretto.** Le candidate V4
EN/IT hanno rapporto `0xBF` per Azurill e `0x7F` per Marill/Azumarill. Il banco
autentica ROM, archivi e routine, poi esegue l'ARM9 reale: `CreateMon`,
`GetMonEvolution` a amicizia 219/220, i 24 byte del commit evoluzione e
`GetMonGender`/campo 111. I sette byte bassi PID `40,7E,7F,80,BE,BF,C0` per
lingua producono 14 casi: `7F,80,BE` cambiano femmina→maschio, gli altri sono
controlli femmina→femmina o maschio→maschio. Specie 298→183, metodo 1;
PID, OT, esperienza, checksum e assenza di `checksumFailed` sono verificati.
La ricevuta canonica dei risultati è
`cb9de95e3d957bde0ce5569c63acbf1141c56d569134e94dbaa52239128842cd`.
La cache resta femmina dopo il commit, ma entrambi i getter ricalcolano maschio
e il campo 111 aggiorna cache e checksum: una sola scrittura cache è confutata.

Il censimento successivo trova 68 consumer effettivi di genere/cache. La prova
di interoperabilità chiude anche lo spazio delle soluzioni exact-PID: Azurill
usa ratio `0xBF`, Marill `0x7F`, quindi i 64 low-byte PID `0x7F..0xBE` sono
femmina prima e necessariamente maschio dopo per qualunque ricevente vanilla
che conservi specie e PID. Cache o sidecar possono divergere soltanto nella
Plus; scambio/Pensione e helper specie+PID bypassano quella scelta. Stato:
`CONFIRMED / EXACT_PID_INTEROPERABLE_FIX_IMPOSSIBLE /
CLOSED_WONT_FIX_LOSSLESS_INVARIANTS`.

La diagnosi e la scelta di prodotto sono registrate separatamente. Portare
Azurill al 50% cambia immediatamente alcuni Azurill preesistenti; portare
Marill al 75% cambia Marill/Azumarill preesistenti; riscrivere il PID altera
identità e calcoli Pokéathlon; rendere autorevole la cache richiede constructor,
setter/getter e consumer diretti come la Pensione, e un ricevente HGSS vanilla
ricalcolerebbe comunque dal PID. Il mandato lossless di `AGENTS.md` decide
quindi l'invariante: preservare Pokémon esistenti, PID, dati save e scambi
vanilla. La 1.3.1 conserva il comportamento retail e documenta il limite; non
applica una migrazione distruttiva o una cache incompatibile. Un replay fresco
del 5 novembre esegue di nuovo il banco ARM9 reale EN/IT, 2/2 senza skip. Il
caso è chiuso come `WONT_FIX` vincolato dagli invarianti, non come bug corretto;
animazione/scena, SAVE/cold e scambio reale non cambierebbero l'impossibilità
exact-PID e non sono gate di una patch. Non è dimostrata corruzione del save.

**HG-F22 Pozzo Slowpoke non è riprodotto nelle condizioni V4 provate; nessuna
patch è stata applicata.** La fonte risale a una singola segnalazione anonima
del 7 giugno 2010, poi riassunta dalla stessa wiki: non è una seconda conferma
indipendente e non identifica regione o revisione. Il banco autentica V4 EN
`179edfb1…fbf90` e IT `2a2f0b43…3a156`, usa soltanto copie della fixture TEST
`c6aa841d…c1e7` con Lapras e attraversa l'ingresso mediante input e task bici
nativi. In otto esecuzioni valide del Pozzo, a piedi e in bici, l'arrivo
richiama temporaneamente il follower e il primo passo a sinistra lo rende
visibile sia nei flag sia nelle catture reali. Il controllo Union Cave EN/IT
mostra lo stesso richiamo a piedi; in bici conserva correttamente avatar1 e il
follower nascosto in quattro ulteriori esecuzioni (12 totali). Venti
esecuzioni ARM su Pikachu/Onix e cinque mappe confermano inoltre il permesso
follower. Report privato
`920a5055fb371646dd3eaa668ee847ff2f4b694363ed559ee7068b27370dc917`;
ROM, fixture e copie save invariati. Una sola fixture/specie runtime, nessuna
revisione JP, foto, SAVE/cold o prova fisica impediscono una confutazione
universale. Correggere globalmente la visibilità romperebbe invece stati bici,
Surf e scene speciali senza una divergenza dimostrata.

**Checkpoint storico HG-T10, precedente al successore del 5 novembre sopra.**
La diagnosi e il differimento qui conservati non sono lo stato corrente del fix.

**HG-T10 non è ordinariamente raggiungibile nella Plus; il censimento ha
isolato due difetti latenti in uno stato incoerente e il guard locale chiude
quello di duplicazione nel sorgente.** Il censimento autentica V4 EN/IT e
confronta 28 immagini Sacred Gold/Plus: gli script Ho-Oh21, Lugia104, Sala
d'Onore825 e Kimono928 sono invariati nel perimetro. Lo script dell'uscita est
di Borgo Foglianova mantiene il blocco finché l'evento principale non porta la
scena da 2 a 3; una partita normale non può quindi completare la prima Lega
prima della convocazione. Su 759 percorsi, 184 save unici e 182 validi, nessuno
ha lo stato naturale richiesto; digest censimento
`7be459c047e8ad85bc183344f8d4217fce0685b014a705034e43241b967448fe`.

Il codice resta però vulnerabile a un save importato/glitchato. La Sala d'Onore
rende visibili entrambi i leggendari se non catturati. La successiva scena
Ho-Oh chiama ancora `ShowPerson`; il motore riusa soltanto oggetti con flag25,
mentre quello statico della mappa non lo possiede, e `HidePerson` elimina solo
il primo ID trovato. È quindi strutturalmente possibile lasciare un secondo
Ho-Oh interagibile. Nel ramo Lugia in HeartGold, `BirdFinalApproach` e altri
ingressi dell'overlay scelgono specie/verso/effetti da `gGameVersion` anziché
dalla scena. Il primo runtime ha però confutato il precedente lookup `NULL`:
Ho-Oh e Lugia usano entrambi object ID5, quindi la ricerca trova l'oggetto
Lugia. Le risorse cinematografiche Lugia sono presenti, confutando anche
l'ipotesi «filmato mancante». Restano un ramo semantico sbagliato e altri
assert/version gate da tracciare, non una causa del freeze già localizzata.
L'audit successivo qualifica la divergenza: lo script 104 invoca la sequenza
Lugia, ma su HeartGold `BeginClearBellAnim` deriva camera e danza da
`gGameVersion`, `BeginLugiaArrivesEffect` e il pan ritornano senza
inizializzare la camera Lugia, mentre `BirdFinalApproach` seleziona specie,
verso, tempi e geometria Ho-Oh. Overlay 2/106 e l'archivio cinematografico sono
autenticati e identici EN/IT; le risorse Lugia sono presenti. Gli otto test
pubblici del guard verificano duplicazione e archivio, non eseguono questi
helper e non vanno citati come replay del mismatch. La scena è quindi
incoerente al componente, ma lo scheduler non ha riprodotto il freeze completo;
senza fixture pre-scena non è giustificato scegliere fra parametrizzare,
saltare o migrare lo stato.
Questi sono fatti statici e una catena causale parziale, non ancora doppia
cattura o freeze osservati.
Il runtime controllato userà soltanto copie TEST e uno stato artificiale minimo,
separato dalla raggiungibilità ordinaria. Il primo ciclo è ora ripetibile EN/IT:
sulla mappa340 il gate reale restituisce script7, esiste un Ho-Oh ID5/slot6 e
il consumer nativo `MapObject_CreateFromObjectEventWithId` usato da
`ShowPerson` crea un secondo ID5/slot7; entrambi hanno flag25 falso. È la
duplicazione del componente dimostrata, non ancora script21 completo, cleanup,
seconda interazione o seconda cattura. Sulla mappa244 il gate restituisce
script6 e lo stesso consumer crea un solo ID5 con sprite Lugia426, confutando
il percorso `NULL`. Il coupling statico specie/verso/timing resta, ma il freeze
non è riprodotto. Riproduttore privato
`eaf4450de0f2ccab931fac2cfb474f1f3c0ae89d72c88a96ece37e088492224e`;
ROM, fixture TEST `c6aa841d…c1e7`, runtime e copie restano invariati. Mancano
scena scheduler completa, battaglia/cattura/cleanup e controlli 40FA0/2,
caught e progressione normale.

La duplicazione Ho-Oh ha ora una correzione locale nel sorgente 1.3.1. Il
producer `legendary-scenes-scripts` accetta soltanto il membro 21 V4 autenticato
(`cccdd680…c609`) e produce `8907965e…394c`: prima della coppia ereditata
`ClearFlag 0x242; ShowPerson 5` controlla il flag nascondi. Se il flag è già
libero, la mappa ha già materializzato l'oggetto e lo script salta direttamente
a `MakeObjectVisible 5`; se è ancora posto, crea esattamente un oggetto. Una
seconda esecuzione non crea altri ID5. La patch aggiunge 18 byte, preserva gli
archi e i movimenti decodificati, non modifica il consumer nativo globale né il
membro Lugia 104 e non cambia layout o identificatori del save. Il test sulle
V4 EN/IT conserva anche il consumer ARM9 byte per byte. Rimangono fuori da
questa chiusura la migrazione di un oggetto già duplicato in memoria/savestate,
la scena completa, battaglia/cattura/cleanup, i rami cinematografici dipendenti
dal titolo e il freeze segnalato: non vanno marcati corretti per effetto di
questo guard.

La ricerca storica isola ora la famiglia evoluzioni **SG-EV01..04**: Mantyke
richiedeva Voltorb 100 invece di Remoraid 223; Feebas aveva Bellezza 0 invece
di 170; Burmy femmina livello 0 invece di 20; Combee femmina livello 0 invece
di 21. Le stesse quattro preimmagini compaiono nelle candidate EN/IT e i valori
retail sono confermati dal consumer pret e dalla documentazione originale.
Il producer `evolution-fixes` cambia soltanto i quattro halfword parametro in
`a/0/3/4`; hash, checker ostile, roundtrip, replay e mutanti passano. La stessa
delta alimenta la Guida in-game prima di compilarne il testo, evitando regole
stale. Due composizioni UI reali EN/IT in memoria rileggono rispettivamente
`170/20/21/223`; nessuna ROM è stata conservata. Mancano ancora evoluzioni
giocate ai confini, animazione, Continue/SAVE/cold e dispositivo.

La stessa famiglia di script chiude al livello sorgente/componente **HG-F25
Franz/Kurt**. Il membro 874 chiamava `HasSpaceForItem` ma non confrontava
`VAR_SPECIAL_RESULT`: anche con quantità 950 e lotto 50 entrava nello standard
di consegna e poi cancellava il lotto. Il guard relocato usa il messaggio 9 già
presente e lascia quantità/tipo in attesa; 949+50 conserva invece il percorso
sano fino a 999 e alla cancellazione successiva. EN/IT, preimmagine, tutti gli
edge relativi, byte complementari, mutanti e allineamento dei movimenti
passano. Il membro cresce di 20 byte; nessun layout save cambia. Mancano scena
renderizzata, riparlare dopo SAVE/cold e dispositivo.

HG-F23 è ora confermato al livello ROM/componente e corretto nei sorgenti. Il
membro 932, 634 byte e SHA `b4bbc075…d9a5`, usa due siti permissivi della Borsa
Plus: a 99×TM07 `HasSpaceForItem` restituisce successo, `GiveItem` inserisce
zero e lo standard 2033 mostra lo scarto ma azzera `x800A` prima di ritornare;
il chiamante poneva comunque il flag 210 e il badge saltava per sempre il dono.
Il fix non controlla la spia ormai consumata: legge la quantità reale prima
della consegna, usa il cleanup Borsa piena a 99 e lascia il flag unset. Il ramo
post-medaglia consulta il flag e riprova; a 98 aggiunge una TM, pone il flag e
i colloqui seguenti non duplicano. EN/IT, entrambi i blocchi, relocation,
allineamento movimenti, mutanti e byte complementari passano. Restano scena,
SAVE/cold e dispositivo; i vecchi save con flag 210 sono indistinguibili da
una consegna riuscita e non ricevono una migrazione speculativa.

**SG-AI01 è confermato e corretto nei sorgenti/al componente.** La preimmagine è stata confermata
nativamente: su otto Plus EN/IT autenticate, dalla 1.04 alle candidate 1.3.1,
il vero helper scalare, il vero helper flag e lo scorer post-KO producono 120
divergenze Fairy contro la matrice danno autorevole, zero divergenze nei
controlli retail e otto decisioni discriminanti errate. Il digest canonico è
`9cb98293…e9081`; la ricevuta privata passa due casi component.

Le controprove hanno respinto la scorciatoia iniziale. Cambiare soltanto i due puntatori base mescola indici moderni con le
colonne retail di `CheckFlyingImmunity`: Ground→Flying con Ferropalla o Gravità
diventa erroneamente immune. Quattro puntatori coerenti correggono questi
controlli, preservano Scrappy/Foresight e risolvono la decisione offline, ma
dipendono da overlay 18: la `.sinit` di overlay 12 lo carica nelle lotte normali
e lo salta in alcune modalità communication. La correzione usa invece un helper
Thumb residente da 148 byte (SHA `d965f5ff…b2a6f`) e due seam in overlay 12.
L'helper tratta soltanto le dodici interazioni Fairy e delega le altre coppie al
consumer nativo: oltre 76.000 casi dinamici coprono Fairy, controlli retail,
HG-B13, Scrappy, Gravità, Ferropalla, ABI, registri, stack e canary. La crescita
BLZ di 8 byte viene registrata nella FAT 12 e nella sola parola dimensione y9;
il CRC y9 derivato di Module96 viene riconciliato e il peel inverso ricostruisce
la UI fredda byte per byte. I test isolati e la composizione completa passano
EN/IT; restano battaglie naturali/communication, SAVE/cold e dispositivo.

La stessa analisi ha aperto due candidati separati, non confusi con SG-AI01:
`GetTypeEffectivnessData`/Conversione2 conservava tabella retail e limite 112;
il percorso danno moderno conservava invece due colonne retail nel controllo
Ferropalla/Gravità. I successivi riproduttori e le correzioni SG-AI02/SG-DM01
sono registrati nella sezione di chiusura sotto; questa è la sequenza storica
della scoperta, non il loro stato corrente.

Il finding medio `csf_112884f3ef52818e3e3bd332` sulla tabella autoload ARM9 è
confermato e corretto a livello dei lettori. Una ROM sintetica poteva dichiarare
10.000 righe esterne all'extent ARM9 e farle materializzare prima di qualunque
limite. Il validatore condiviso ora controlla extent, ordine, divisibilità,
massimo 256 sezioni, somme e overflow prima della costruzione degli oggetti.
La prima revisione ha individuato sei chiamate dirette residue a
`MainCodeFile`; anche quelle passano ora dal decoder limitato e dal preflight.
Sei regressioni mirate e i nove test dello stage spazio passano; la V4 EN reale
con tre righe autoload/quattro segmenti viene letta con SHA-256 invariato.

I due finding bassi del frontend runtime sono confermati e corretti a livello
del banco host, non del gameplay. Prima, una ROM sparsa da 513 MiB veniva
allocata interamente prima del rifiuto melonDS e `read ... 0xffffffff` poteva
produrre miliardi di letture; script ripetuti accumulavano inoltre frame, stato
e output senza budget comune. Il frontend ora ammette prima dell'allocazione
ROM ≤512 MiB, SRAM entro capacità/64 MiB e savestate ≤32 MiB, trasferisce i
byte ROM senza seconda copia e applica limiti cumulativi a comandi, frame,
letture, watch/freeze/cheat, tempo e output. La revisione ha chiuso anche race
check/reopen e righe CR/interattive illimitate. Undici test runtime, rebuild e
link reali contro il checkout pin-nato, fixture sparsa 512 MiB+1 e tutti gli
SHA del kit passano. Le allocazioni interne del parser savestate sono una pista
separata, non attribuita a questi due finding.

Tre finding medi sugli ingressi del builder sono chiusi insieme senza fonderne
le identità. ROM 1.2.5 e V4 vengono ora aperte no-follow, ammesse per una delle
sole quattro coppie dimensione/SHA autorizzate e lette dallo stesso descriptor;
dimensioni estranee, symlink, hardlink, crescita e identità errate falliscono
prima della materializzazione utile. La charmap esterna (massimo 1 MiB) viene
autenticata una volta e tutti gli stadi consumano la copia privata; `scrcmd.json`
viene analizzato direttamente dagli stessi byte autenticati. Sei regressioni,
79 test mirati e le quattro ROM canoniche EN/IT passano; anche charmap reale
29.082 byte e tabella reale da 853 comandi conservano gli hash fissati. Lo
snapshot dei sorgenti 1.3 resta una famiglia TOCTOU distinta. Il follow-up del
4 novembre la riproduce ora al componente: uno stadio può consumare byte
temporaneamente sostituiti e il writer può poi ripristinare l'inode ammesso,
così che gli snapshot prima/dopo risultino identici. Il controllo negativo
rileva invece la modifica lasciata visibile. Stato `CONFIRMED /
REPRODUCED_COMPONENT / ARCHITECTURAL_HARDENING_REQUIRED / UNFIXED`: una copia
privata mode 0700 non ferma uno scrittore dello stesso UID; la chiusura richiede
consumer descriptor-bound per Python/JSON/C/header o isolamento kernel
dell'intero build.

Il follow-up architetturale ha escluso due false chiusure con regressioni
eseguibili. Un vero loader Python consuma il modulo intermedio e i due snapshot
restano uguali dopo il ripristino; inoltre un secondo processo con lo stesso UID
rende di nuovo scrivibile e modifica senza errore una copia `0700/0400`. Lock
cooperativi, directory privata, ACL/flag revocabili dal proprietario e un terzo
hash non costituiscono quindi una barriera di autenticità.

Il contratto minimo per una futura chiusura è ora delimitato: un broker con UID
distinto o autorità amministrativa deve leggere l'albero descriptor-relative,
materializzare quei byte in un filesystem kernel read-only e avviare **un nuovo
interprete** dal mount, senza moduli repository già importati. Python, JSON, C,
header e assembly consumati devono tutti risolversi nel mount; toolchain e
dipendenze eseguibili devono provenire da percorsi protetti, mentre output e
scratch restano su un volume separato scrivibile. Il gate richiede che uno
scrittore concorrente dello UID del maintainer possa alterare il checkout ma
non i byte consumati, che ogni scrittura al mount fallisca e che l'artefatto
resti legato al manifest descriptor-bound. Questa autorità non è disponibile
al builder in-process corrente: nessuna patch parziale viene promossa.

## Follow-up Daybreak: checkout melonDS non autenticato — 3 novembre 2026

La scansione sigillata `a64b8d0b-ec86-42ac-addd-fdb5fba81024`, sul commit
`db6a3c54e938352ea575e7f41a6872c203d47ca1` e snapshot
`b064d0f881b4e39a1fc3502ff6feb305eb5c819b6909c3844be0bbb5deb4c68d`,
ha prodotto 34 candidati statici: 4 alti, 20 medi e 10 bassi. La copertura JSON
è marcata `complete`, ma il rapporto dichiara correttamente copertura manuale
parziale: 926 file pubblici/prodotto inventariati, soltanto un sottoinsieme
letto integralmente e oltre 57.000 file locali in gran parte privati, generati
o vendorizzati. “Scansione completata” non significa quindi 100% del codice
revisionato né exploit riprodotti.

Prima unità scelta: finding
`csf_593b8a34746de23fcdc1fb80`, regola
`untrusted-code.dirty-pinned-melonds-checkout`, priorità alta. È stata preferita
perché il percorso documentato raggiunge CMake con autorità del manutentore,
si prova senza ROM, save, rete o dispositivo e non si sovrappone alle modifiche
UI già presenti. È duplicato semantico dei rilievi 18 e 59 del run cancellato
del 2 novembre (`supply-chain.dirty-pinned-checkout` e
`external-source-checkout-not-authenticated`): conta come una sola causa, non
come tre bug.

### Riproduzione, confutazioni e fix

Prima del fix, cinque test fallivano come previsto: un CMake tracciato
modificato, un modulo `cmake/CheckIPOSupported.cmake` non tracciato, un payload
ignorato e uno spoof del marker di idempotenza venivano accettati; mancava
anche una verifica separata al configure. La revisione indipendente ha poi
riprodotto due bypass più forti con repository Git reali:

- `skip-worktree` nascondeva un `CMakeLists.txt` modificato a `git status`;
- `refs/replace` conservava l'OID testuale di `HEAD` ma sostituiva l'albero
  letto da `git show`.

Il controllo sano, un checkout pulito al commit fissato, applicava una sola
volta gli hook esatti ed era idempotente. Il controllo negativo finale ha
clonato localmente il checkout reale `906e9ebb…`, applicato gli hook e aggiunto
un modulo CMake che avrebbe scritto `SHOULD_NOT_EXIST`: `--verify-only`, la
configurazione CMake e una build successiva lo hanno rifiutato; il sentinella
non è comparso e, nella prova finale, nessuna compilazione è iniziata.

La correzione non usa più indice o porcelain come autorità. Con replacement
objects disabilitati, legge il tree del commit fissato, enumera l'intero
filesystem, confronta byte, tipo e modo eseguibile di ogni blob, rifiuta
extra/mancanti/directory inattese e deriva dai blob originali i soli due output
strumentati ammessi. Le letture dei file regolari usano no-follow dove il
sistema lo offre, rifiuta hardlink condivisi e sostituisce atomicamente i due
file. CMake invoca `--verify-only` prima di valutare il checkout e a ogni build
del target core. Modifiche presenti soltanto nell'indice staged non sono
attestate perché CMake non le consuma.

Stato: **confirmed e fixed al livello componente/configurazione**, non bug di
gameplay. Nove test del nuovo riproduttore e il parser RTC passano; il checkout
reale viene ammesso e configurazione più build completa del target `core`
terminano correttamente. Non
è stata compilata una nuova ROM, non è stato aperto un save e non deriva alcuna
accettazione Android/release. Resta un limite del banco cooperativo ora
riprodotto con due regressioni: un processo dello stesso account può esporre
byte intermedi a un consumer e ripristinare l'inode ammesso prima del secondo
snapshot, eludendo il confronto prima/dopo. Una modifica non ripristinata viene
invece rilevata. Non è stato applicato un falso fix parziale: servono consumer
descriptor-bound o isolamento kernel dell'intero build.

### Seconda unità: race sul reference ZIP

Il finding alto `csf_fc9587fb5d70c1bda3c8c8eb`, regola
`integrity.reference-zip-check-use-race`, è distinto dalla prima causa. Il
packager calcolava SHA-256 tramite un primo descriptor, lo chiudeva e apriva di
nuovo il pathname con `ZipFile`. Un test rosso ha sostituito atomicamente il
file proprio al secondo open: manuale pin-nato invariato, ma licenza e Game
Guide false sono entrate nei membri. Un secondo rosso ha mostrato che un
symlink al reference veniva seguito. I pin dei manuali originali limitavano
solo quei membri; `omit-unverified` della 1.3.1 eliminava i cheat ma non la
licenza e la Game Guide.

Il fix legge una sola snapshot da un descriptor no-follow, richiede un file
regolare, limita il contenitore a 256 MiB e verifica l'hash degli stessi byte
poi analizzati con `ZipFile(BytesIO(...))`. Una sostituzione o una mutazione
del pathname non può cambiare i byte consumati. I reference reali EN/IT misurano
10.213.443 e 24.014.179 byte e superano il nuovo controllo. Le due regressioni,
tutte le 14 prove di distribuzione e la revisione indipendente passano.

Stato: **confirmed e fixed al livello componente**, senza creare pacchetti di
release nuovi e senza ROM/save. È rimasto intenzionalmente fuori da questa
unità il contenuto decompresso dei singoli membri e la validazione dei loro
nomi: `zip-decompression` e `release-archive-members` restano famiglie aperte,
non limiti nascosti di questo risultato.

### Terza unità: checkout RomPatcher.js eseguibile e mutabile

Il finding alto `csf_bbc26628ba733900c87b807f`, regola
`toctou.executable-toolchain-checkout`, unisce due rappresentazioni della stessa
causa: il packager eseguiva byte del working tree che non erano legati in modo
atomico al commit dichiarato. Il vecchio controllo confrontava `HEAD` e usava
`git status --untracked-files=no`, poi, dopo reference e xdelta, avviava Node
42 volte per la 1.2.5 o 50 per la 1.3.1 sul pathname originale.

I riproduttori rosso/verde coprono cinque bypass concreti:

- `modules/HashCalculator` non tracciato prevaleva sul
  `HashCalculator.js` del commit per la risoluzione CommonJS senza estensione;
- `skip-worktree` nascondeva una modifica tracciata al controllo porcelain;
- una directory non tracciata annidata nel repository fissato veniva scambiata
  per la radice valida da `git -C`, ma Node caricava moduli sotto la directory
  falsa;
- dopo il controllo, una modifica al checkout restava osservabile dalle
  invocazioni Node successive;
- in un clone parziale un blob mancante avviava il lazy fetch configurato nel
  repository: il test promisor eseguiva un helper-sentinella prima di fallire.

Il fix non copia più il working tree. Richiede la vera radice non-symlink del
checkout, neutralizza le variabili `GIT_*` ereditate e replacement objects,
disabilita ogni lazy fetch, verifica `HEAD`, commit, tree e ogni blob con
l'identità SHA-1 Git, rifiuta link
e modi non supportati e materializza i soli blob fissati in una directory
temporanea privata. Tutte le invocazioni Node ricevono quella stessa snapshot.
Il checkout reale al commit `31838840…` produce 58 file, non contiene lo shadow
locale e carica `BinFile.js` e `RomPatcher.js` con Node. Cinque regressioni e
tutti i 19 test di distribuzione passano; `py_compile` e `node --check` passano.

Il tentativo della suite globale non è stato promosso a PASS: Class A ha
raccolto 1.040 test, ne ha eseguiti 994 e saltati 46, ma il runner marca come
failure numerosi gruppi con zero test raccolti. I dieci errori Stage 0 erano un
limite del sandbox sul bind loopback: lo stesso modulo, ripetuto fuori sandbox,
passa 46/46. Class B ha raccolto 334 test, ne ha eseguiti 41 e saltati 293;
restano due errori preesistenti `portable` per preimage mismatch e altri gruppi
vuoti. Questi limiti del banco non sono nascosti né attribuiti al fix
RomPatcher; il suo package proprietario resta verde 19/19.

Rerun host del 4 novembre sulla snapshot di suite caricata all'avvio: Class A
ha raccolto 2.029 test, ne ha eseguiti 1.976 e saltati 53, con verdetto globale
**FAIL**. Il runner era partito prima della registrazione dei primi test Safari;
il loro set finale, ampliato a 14 prove fra oracolo, candidate e producer, passa
separatamente 14/14 e non viene sommato retroattivamente al conteggio globale.
I quattro rossi erano regressioni del banco, non bug ROM, e sono ora corretti:
il fixture `sgp12.test_versione` costruisce un layout autoload valido; la catena
attesa include `traded-egg` e `bag-foreign`; il censimento UI separa le write
dirette da quelle delegate al producer event-flags e protegge l'intero payload
più i quattro hook; il test gifts verifica il rifiuto specifico della metadata
SHA-256 alterata. I gruppi coinvolti, rieseguiti insieme ai registri e alla
composizione Safari, passano 212/212. Il runner globale completo non è stato
rieseguito e non viene promosso retroattivamente a PASS. Il precedente run
Class B era stato arrestato con exit 130 prima di duplicare Guide/Scene già
eseguite separatamente: niente JSON finale. Prima dell'arresto
passavano, fra gli altri, native settings owners 8/8, painter Opzioni 4/4,
Box portatile 59/59 e riparazioni ereditate 43/43. Il banco UI indipendente ha
poi chiuso Settings 105/105, Guide 53/53, ui-native 185/185 e 38/38 prove native
EN/IT mirate. Runner e figli sono stati verificati terminati.

Stato: **confirmed e fixed al livello componente/toolchain**. Non è stato
eseguito un rebuild reale delle 42/50 route perché richiederebbe ROM e target
privati; non sono stati creati o pubblicati ZIP di release e non deriva alcuna
prova di gameplay/save. `verify-rompatcher.cjs` resta un helper interno, non un
autenticatore standalone. Configurazione Git locale ostile, ambiente Node
preload e sandbox del processo appartengono a candidati separati finché non
vengono verificati sul loro confine specifico.

### Quarta unità: compilatore eseguito prima dell'autenticazione

Il finding `csf_752bacc9b5e70c84e674895d` è ora **confirmed con correzione
locale verificata e integrazione CI aperta**. Il riproduttore inserisce un
`clang` con il banner atteso: prima del fix il probe `--version` scriveva una
sentinella prima del rifiuto. Lo stesso controllo passa dopo il fix per tutti
i cinque ingressi 1.3.1, con sentinella assente.

Il vecchio SHA-256 autenticava il dispatcher `/usr/bin/clang`, non il
compilatore da esso scelto. Il nuovo helper `sgp13/compiler.py` autentica il
binario effettivo Apple CLT (`fc5e3cbb…bd6d66`) prima dell'esecuzione e richiede
file e antenati di proprietà root, senza scrittura gruppo/altri e senza ACL
estesi. La destinazione canonica protetta impedisce la sostituzione da parte
del writer non privilegiato; sostituzioni amministrative rimangono fuori dal
contratto. Un ambiente ristretto elimina override del driver, loader, plugin,
include e configurazioni utente. Sono coperti anche gli otto moduli 1.3 e il
sottoprocesso Options, che riceve il percorso verificato mediante `--cc`.

Le 27 prove UI passano, compresi rifiuto prima del probe nei cinque ingressi,
rifiuto di un file riscrivibile anche con digest atteso, rifiuto ACL reale e
controprova `CCC_OVERRIDE_OPTIONS` con il compilatore autentico. La compilazione
diretta degli otto moduli 1.3, inclusi navigation/extended e Options, passa.
La prima invocazione allargata ha indicato tre nomi di moduli test inesistenti:
è un errore del comando, conservato come tale, e non prova di un difetto del
prodotto. I test esistenti effettivamente eseguiti in quel run non fallivano.

Il runner `xcode-27` offre ora Xcode 27.2 release (27B52), che porta Apple clang
21.0.0 `clang-2100.4.1.1`. Il workflow seleziona esplicitamente quell'Xcode e
rifiuta versione o SHA-256 diversi prima delle suite. La compatibilità completa
resta da osservare sul primo run GitHub: non viene ottenuta ignorando il pin e
un'immagine runner diversa resta un errore. La composizione statica corrente è
registrata sopra; nessuna accettazione runtime deriva dalla sola selezione CI.
Il test globale fuori sandbox è diagnostico; le modifiche
durante il run impediscono di attribuirlo a una snapshot sorgenti unica.

Il runner ora distingue un processo terminato da segnale (per esempio SIGILL
del JIT nel sandbox) da una suite realmente vuota, mostra avanzamento senza
buffering e include anche i contratti di distribuzione 1.3.1. I controlli
sintetici segnale/suite vuota/suite sana passano. La singola suite Settings
render ripetuta fuori sandbox passa 24/24; questo confuta la precedente
interpretazione dei suoi zero test come assenza di copertura.

### Quinta e sesta unità: nomi e decompressione dei pacchetti

`csf_3b744f6a242a05b471a87fef` (medio, nomi dei membri) è **confirmed/fixed al
livello componente**. I test rossi emettevano traversal, backslash, drive,
alias Windows e collisioni dopo il cambio versione. Il fix controlla versioni,
ID sorgente, nomi consumati e nomi trasformati prima dell'inserimento e prima
di creare il ZIP; include collisioni NFC/casefold, file-directory e device
Windows con cifre in apice. La revisione ha trovato gli alias COM¹/LPT²,
successivamente aggiunti ai rifiuti. Il controllo reale ha anche identificato
la sostituzione intenzionale di `Cheats/ABOUT-CHEATS.txt`: resta ammessa soltanto
come overlay esplicito del documento del progetto sullo stesso nome esatto.

`csf_b0ad04816e66ae5ee8147c99` (basso, decompressione) è **confirmed/fixed al
livello componente**. Tutte le letture selezionate condividono limiti di 8 MiB
per membro e 32 MiB aggregati, applicati a metadati e byte effettivi. I test
rossi usavano ZIP reali con limiti piccoli: overflow singolo e aggregato erano
ammessi prima. Il confine esatto ora passa e il byte successivo è rifiutato;
patch inutilizzate e cheat omessi non consumano il budget. La revisione ha
mostrato che BZIP2/LZMA possono espandere un blocco interno senza limite nella
libreria Python: questi metodi sono ora rifiutati prima dell'apertura del membro.
STORED/DEFLATED restano ammessi.

Le 26 prove di distribuzione passano. I reference e i PDF reali EN/IT, sotto
entrambi i contratti, superano lettura e finalizzazione (16 membri per lingua
1.2.5, 14 per lingua 1.3.1, senza le patch ROM). I membri selezionati storici
sono tutti DEFLATED, massimo 1.510.542 byte; aggregati EN 3.603.904 e IT
3.635.792 byte. Nessun nuovo pacchetto ROM è stato creato o pubblicato.

### Correzione dell'oracolo del banco Portable

La coppia di errori Class B Portable è stata riprodotta nuovamente EN/IT.
`RealUiComposition` passava il preimage del codice Guide V4, mentre la UI
attuale ritira quel codice e il suo slot Portable 0x023D4E10/3.024 byte è
documentatamente vuoto; anche il test dello stage di produzione richiede il
digest di 3.024 byte zero. La correzione riguarda soltanto il test: confronta
lo slot con gli zeri indipendenti e passa quel digest. Prima prova due errori;
dopo, composizione e readback EN/IT passano e una mutazione di un byte nello
slot continua a essere rifiutata dal controllo di produzione invariato.
Livello: componente/composizione in memoria sugli input V4 identificati dai
pin del test; nessuna ROM o save è stato scritto. Non è un nuovo bug di gioco
né un finding Daybreak aggiuntivo.

### Riesame configurazione Git: risolto dalla correzione precedente

`csf_2ea75e03a230e8332e9f3159` (medio) è **resolved_by_prior_patch**, esito
`no_change` sul codice di produzione. Un repository Git temporaneo configurato
con un fsmonitor-sentinella dimostra che il vecchio `git status` lo esegue;
`pinned_git_snapshot` materializza invece i blob autentici senza eseguirlo.
Il riesame indipendente ha provato anche configurazione inclusa, pager e alias.
I comandi attuali sono soltanto `rev-parse`/`cat-file`, con fsmonitor/hook/pager
e lazy fetch disabilitati. È aggiunta una regressione stabile: l'intera suite
di distribuzione passa 27/27. Nessun nuovo fix viene ricontato per questa chiusura.

### Settima unità: output del downloader e symlink

`csf_fba8aa09854d71105e28b860` (medio) è **confirmed/fixed al livello
componente**. Prima della correzione, un link simbolico dangling sul nome
prevedibile `<delta>.parziale` faceva creare e scrivere un file esterno alla
destinazione; il delta finale restava a sua volta un symlink. Separatamente,
un link su `SHA256SUMS-base-1.1` faceva troncare il relativo bersaglio esterno.
Un terzo riproduttore ha inserito deterministicamente il link nella finestra
fra `unlink` e `open`. Hash e dimensione successivi non potevano annullare il
danno già avvenuto.

Il downloader trattiene ora un descriptor della cartella privata, rifiuta una
destinazione non posseduta o scrivibile da gruppo/altri, crea temporanei casuali
0600 con `O_EXCL`/`O_NOFOLLOW`, calcola hash e byte sul medesimo stream e
pubblica delta e ricevuta con `os.replace` relativo al descriptor. I link sui
nomi finali vengono sostituiti come entry e non seguiti. Cinque controlli di
sicurezza e l'intera suite stadio 0 passano, **51/51**; `py_compile`,
`git diff --check` e revisione indipendente sono verdi. Nessuna rete esterna,
ROM o save è stata usata. Un vecchio nome `*.parziale` prevedibile può restare
come residuo ignorato; non viene aperto o rimosso dal nuovo percorso.

### Ottava unità: budget delle risposte HTTP

`csf_aaa0e4625ef66d42c16cf5a6` (medio) è **confirmed/fixed al livello
componente**. Il manifest remoto veniva letto integralmente con `read()`; i
delta venivano copiati fino a EOF e confrontati con la dimensione pin-nata
soltanto dopo il consumo di memoria/disco. Il riproduttore pre-fix ha
materializzato 2 MiB di manifest e, con quattro byte attesi, consumato e scritto
quasi 400 KiB prima del cleanup. Il percorso restava raggiungibile anche con
un delta locale già valido.

Il manifest è ora limitato a 64 KiB e il primo byte successivo viene rifiutato.
Ogni delta usa direttamente la dimensione esatta del pin come budget e non
scrive il byte eccedente. Un `Content-Length` superiore viene rifiutato prima
del body; header assente o falso non evita il conteggio sullo stream. Manifest
e due lingue condividono una deadline monotona di 30 minuti. La revisione ha
individuato due bypass del primo fix: EOF/ultimo blocco dopo la scadenza e
`HTTPResponse.read(n)`, che può tentare di riempire l'intera richiesta mentre
un server invia a gocce. Il codice controlla ora il tempo prima e dopo ogni
lettura e preferisce `read1(n)`, una sola operazione del trasporto per giro.

Otto controlli budget e l'intera suite stadio 0 passano, **59/59**; `py_compile`,
`git diff --check` e revisione indipendente sono verdi. Il timeout socket limita
la singola operazione già iniziata; il clock Python può rifiutare soltanto al
suo ritorno. Nessuna rete esterna, ROM o save è stata usata.

### Nona-undicesima unità: guide e gate pubblico

Tre finding distinti sono **confirmed/fixed al livello componente**. I PDF
forniti a `pack.py` potevano essere letti attraverso symlink. La revisione del
primo fix ha riprodotto anche uno swap fra `lstat` e `resolve` capace di
impacchettare due sentinelle esterne e una FIFO capace di bloccare l'apertura.
Il percorso finale risolve soltanto gli alias di sistema root-owned, poi apre
ogni componente no-follow e conserva il descriptor; i PDF sono aperti
non-bloccanti e accettati soltanto se regolari. Le regressioni coprono link
fermi, swap deterministico e FIFO.

Il contratto delle guide accettava immagini assolute, `..`, drive Windows e
UNC. Ora i nomi sono relativi e portabili, ogni componente sotto
`source/images` è aperto no-follow e ReportLab riceve i byte dello stesso
descriptor. Quattordici escape lessicali, link finali/intermedi, nove immagini
predefinite e sei immagini annidate 1.3.1 passano la revisione indipendente.
La resa PDF completa non è stata rigenerata perché questo ambiente non contiene
ReportLab 4.4.9: è un limite release separato, non un'eccezione al confine file.

Infine `.xdelta` aveva un ramo speciale nel gate pubblico che saltava i
controlli di contenuto. I patch file restano correttamente membri generati dei
pacchetti, ma non possono essere file tracciati nel source tree; il magic VCDIFF
è inoltre respinto anche se rinominato `.vcdiff` o `.bin`. Suite distribuzione
**32/32** e contratto pubblico **929 file** PASS. Nessuna ROM, save o ZIP di
release è stata prodotta.

### Dodicesima unità: allocazione BLZ

`csf_750c41b2c9ecbdad9d76e0da` (medio) è **confirmed/fixed al livello
componente**. Il trailer minimo `08000008ffffffff` calcolava un'immagine di
4.294.967.303 byte e chiamava `bytearray` prima dei controlli. Il limite di
4 MiB della RAM principale DS e l'uguaglianza con `ram_size` y9 sono ora
verificati prima di qualunque allocazione nei decoder condivisi, nelle tre
copie storiche e nei cinque rilettori indipendenti.

La revisione ha trovato bypass nei decoder `ndspy` di ARM9 e overlay. Il source
tree non li chiama più direttamente: wrapper comuni riconoscono lo stesso
trailer, includono l'eventuale coda ARM9, verificano y9/file ID e soltanto dopo
delegano a ndspy. Dodici test BLZ/security, 27 UI e 9 space PASS (uno skip per
input esterno). La V4 EN pin-nata, letta senza scriverla, conserva hash
`179edfb1…f90` e ammette 4 sezioni ARM9/129 overlay. Il percorso manutenzione
già preceduto dal pin completo resta coerente ma usa anch'esso il wrapper.
È un DoS locale del tooling su input costruito, non un bug di gameplay.

### Tredicesima unità: extent dei banchi testo

`csf_810b76c9b02604001e7a6aa4` (medio) è **confirmed/fixed al livello
componente**. Tre parser completi accettavano record sovrapposti e duplicavano
le liste decodificate: una fixture di 84 byte produceva 36 word logiche e una
tabella da circa 655 KiB poteva dichiararne oltre 2,1 miliardi. Ora l'intera
allocation table è validata prima della prima word, extent vuoti o sovrapposti
sono rifiutati e il limite è 4096 messaggi.

I test normali e con `python -O` passano **17/17**; l'audit non dipende più da
`assert`. Un banco di 4096 record adiacenti con chiave nonzero fa roundtrip
byte-esatto, 4097 sono rifiutati. Controllo read-only sulle V4 EN/IT pin-nate:
tutti gli 829 bank messaggi passano nei tre parser, massimo reale 1717 nel
bank728, hash delle ROM invariati. Il membro UI aggiunto non è un bank messaggi
e resta fuori da questo conteggio. È DoS locale del tooling, non gameplay.

Questo era il conteggio storico intermedio di 21 candidati ancora da chiudere:
un compilatore alto con correzione locale e 20 **ipotesi statiche da
verificare**, non bug dimostrati. Il follow-up successivo li ha riconciliati
tutti: restano **0 candidati statici Daybreak da riprodurre**. Le 62 occorrenze
del run cancellato includevano duplicati e piste non promosse e non vanno
sommate ai 34 finding canonici. La campagna ROM storica resta separata.

## Chiusura codice e nuova composizione

La nuova candidata comprende due ulteriori correzioni riprodotte prima del fix:

- **SG-11:**2.250 esecuzioni del consumer battaglia mostrano680 risultati
  specie0 prima e0 dopo;3.550 esecuzioni telefono mostrano140 prima e0 dopo.
  Guardie zero conservano gli slot base; restano controlli nonzero, radio,
  abilità, canne, orari, sciami, no-bite e percorso Safari separato.
 130 record incontri troncati passano192→196 byte senza modificare il prefisso;
  nightFish resta0 e solo i quattro fishSwarm documentati vengono ripristinati.
  Il writer conserva il BTNF16 originale dell'archivio identificato per hash;
  l'eccezione non ammette altri input non canonici.
- **HG-T09:** il codice originale produce998:59:59+1→999:59:59. Il solo byte
  ARM9 `0x0202CE0F`, D3→D9, ripristina999:00:00.112 esecuzioni native
  coprono104 invocazioni del corpo e8 del caller con wrapper Training, confini,
  massimo e guardie memoria. Nessun cambio formato save né ricostruzione IGT storico.

Lullaby, pesca e IGT sono un unico owner nativo con letture indipendenti;
archivi legacy/pesca precedono l'unico append UI. Slot overlay2/101, FAT/y9,
header e complemento sono verificati; nessuna crescita degli slot compressi.
**253 test mirati PASS in31,046s, zero skip**, revisione indipendente senza
problemi importanti. Sono prove native/modello controllate, non incontri giocati.
Le identità nuove e la copertura locale dei save sono nel
[rapporto](ui-1.3.1-validation.md#nuova-candidata-con-correzioni-integrate--31-ottobre-2026).
Le sezioni seguenti conservano i risultati precedenti e i loro limiti.

La seconda ricognizione amplia il [catalogo retail](known-bugs-hgss.md) a
54 schede qualificate, più nove piste di raccolta. Il
[registro hack](legacy-bugs-1.3.md) mantiene i venti casi storici e distingue
il nuovo sottocaso SG-15b. Non sono 64 bug confermati nella nostra ROM.
Fonti e codice sono stati confrontati; le implementazioni successive hanno
ricevuto revisioni indipendenti.

## Piano eseguito e criteri

1. Fissare input e provenienza; distinguere retail US/IT, Drayano 1.05,
   Plus originale 1.03, V4 e le diverse candidate 1.3.1.
2. Cercare fonti primarie e percorsi raggiungibili, tentando confutazioni.
   Non trasformare commenti BUG, indici o dichiarazioni degli autori in prove.
3. Riprodurre il difetto al livello dichiarato, prima della modifica; applicare
   un intervento minimo e verificare comportamento, byte complementari e rami.
4. Integrare i delta prima dell'unico writer archivi UI; confinare le scritture
   native e rileggere indipendentemente la composizione.
5. Conservare identificatori e formati save. La successiva accettazione richiede
   copie dei raw save, Continue → SAVE normale → avvio a freddo EN/IT;
   controlli visivi e dispositivo restano l'ultimo passaggio.

## Risultati nel codice

| Caso | Prima e intervento | Prova e limite |
| --- | --- | --- |
| SG-01a durata finestra Safari | Tre dialoghi cura partner (Buck, Cheryl e Marley) lasciavano il campo con la finestra ancora aperta e la chiudevano solo dopo il ripristino; Mira chiude prima ed è il controllo sano. Il fix ruota ciascun `CloseMsg` subito dopo `NPCMsg`, lasciando invariati lunghezza, entry e ogni altro byte. | Riproduttore e riparazione autenticati sulle candidate correnti EN/IT: mappa151, script260, evento146 e trigger coordinate→entry; dispatcher/handler/task nativi e sorgente engine pin-nato legano gli opcode al teardown. Il producer cambia solo il membro260, rifiuta reapplicazione/preimage estranee e la composizione/replay reale EN/IT passa (1 test, 270,342 s); 14/14 prove focali verdi. Nessuna ROM conservata. Blackout, menu, audio, raw save, turbo, gameplay, SAVE/cold e hardware non eseguiti: SG-01 generico resta aperto e V-CHATOT è distinto. |
| SG-01b sconfitta finale Safari | Il `GoToIf` di perdita dopo trainer107 puntava a `0x6C4`, da cui il CFG non raggiungeva `WhiteOut` o `ReleaseAll`; i quattro rami perdita partner sani puntano tutti all'unico `WhiteOut` `0x7A4`. Il fix same-size ritargetta quel solo displacement. | RED/GREEN esatti EN/IT, checker indipendente, mutanti, percorso vittoria e quattro controlli perdita provano il retarget. L'unico producer del membro260 compone SG-01a/SG-02 prima di SG-01b e dimostra che tutti i `CloseMsg` restano byte-identici; nessuna ROM/save viene scritta. Mancano sconfitta giocata, SAVE/cold e dispositivo, quindi menu/audio/turbo generici restano fuori attribuzione. |
| SG-09 pickup | L'operando richiedeva 436 Cura Totale; ora richiede uno. | Percorso del bytecode originale e corretto in modello; solo halfword `141:0x086C` cambiata. Policy di saturazione Borsa preservata, nessuna sottrazione retroattiva. |
| SG-08 sconfitta Lyra/Ethan | Il ramo WhiteOut lasciava visibili gli oggetti ricaricati; ripristinato hideflag 712 prima di WhiteOut, mantenendo il retry. | Tre rami perdita verificati sul bytecode in modello; entry, salti e movimenti rilocati/riletti. Non è un conteggio NPC osservato nel gioco né una pulizia di doppioni già salvati. |
| SG-15 Steven | Il flag Regigigas 775 precludeva il Lati dovuto. Il solo Lati corretto, non ancora premiato, prende il percorso originale del premio. | Matrice modello su entrambi gli ordini delle quest e controlli degli altri stati. Nessuna flag persistente nuova o azzerata. Un premio già segnato come ricevuto non viene riaccreditato deducendolo dalla sola assenza dell’oggetto. |
| SG-15b premio e Borsa | CallStd2033 poteva fallire ma il chiamante impostava comunque 3FB8. Aggiunte guardie spazio prima dei due doni Enigma Stone. | Bytecode reale degli standard 2009/2033 percorso in modello: piena → messaggio nativo, nessun flag; liberato spazio → un premio. Nuove chiavi assenti dalla tabella permissiva Borsa. Nessuna perdita osservata in una partita completa. |
| HG-F15 Ninnananna | Con base20, sottrazione25 →251→cap100. Ora la sottrazione satura a zero. | Frammento originale eseguito con 256 ingressi per lingua; funzione ARM completa prima/dopo con getter radio, secondo roll e divisione reali. Registri, stack, PRNG e controlli verificati. |
| HG-B10 Hail | Il retail controlla solo grandine temporanea; Plus usa già maschera temporanea/permanente. | Undici input letti e 264 condizioni VM: **già corretto dalla Plus 1.03**, nessuna nuova patch. |
| H1 Cercastrumenti/eventi Plus | Due interazioni aggiunte, script 19 ad Azalina e 14 alla Gara Pigliamosche, erano `type=2`: il percorso ARM degli oggetti nascosti derivava i flag invalidi `E3F3`/`E3EE`. `legacy-events` le riclassifica `type=1`. | Sui candidati correnti EN/IT il getter reale cambia col bit alias e raggiunge l'assert seam. Il fix cambia un solo halfword nei membri evento 71/440; hash completi, 489 membri complementari e oggetto nascosto 8006/type2 verificati. Composizione/replay completa PASS; due postimage diagnostiche private `b1358db1...712da`/`e05ef31...5eab4` contengono l'archivio post `8633158e...32e08` e fanno Continue in mappa180 su copie raw immutate. La fixture Bugsy è debugger-assistita e tre percorsi ordinari non raggiungono mappa74: scena/UI Cercastrumenti, SAVE/cold e dispositivo restano aperti, senza usare un warp come prova. |
| V-CHATOT | 24 variabili storia `61xx` cadevano nei campioni Chatot; gli script alteravano l'audio e registrare poteva riaprire/chiudere i gate. HF02 conserva una volta zero/nonzero e usa 24 bit liberi della riserva esistente. | Riproduzione 12/12; sei test sintetici, 12 ARM EN/IT e build UI completa con readback. 8/8 copie zero/HF01 passano SAVE/cold EN/IT e audit integrale circoscritto; nessun byte Chatot cambia. Scene ed hardware restano aperti. |

I test degli script sono modelli limitati degli opcode effettivamente decodificati:
non eseguono scheduling, heap, movimenti o ARM. Gli esiti lotta e le capacità
Borsa sono input dichiarati. Il checker confronta ogni istruzione sopravvissuta,
operando, destinazione relativa, entry e byte complementare.

La revisione indipendente aggiunge 854 scenari modello (704 sui percorsi non eleggibili
e 150 su versione/temporanea8002),
verifica i binding degli eventi e conserva le fingerprint Borsa del pickup.
I 31 test specifici script/delta passano; gli scenari negativi sul bytecode
originale producono 30 subtest falliti coerenti con le quattro cause.

Ninnananna ha quattro test ROM, zero skip, con **18.476 esecuzioni native**
complessive, oltre ai test senza ROM. Le sorgenti di avatar/terreno e PRNG sono
seam dichiarati, non incontri giocati. Il boost dipende dalle **inversioni di
direzione**, non dal numero di passi: a piedi, su terreno ordinario, contatore
0/1 e radio Ninnananna portano il primo roll a zero. Contatori 2/3/4 producono
25/35/55; radio spenta/Marcia, bici/Surf, corsa, erba alta e alias GB sono controlli.

## Difetto aggiuntivo trovato nella composizione: BUG-131-01

Il controllo dei consumer ha scoperto un vincolo non coperto dai soli modelli
dei dialoghi: i dati dei movimenti sono coppie di halfword. ApplyMovement
passa il puntatore direttamente al consumer ARM `0x020622E8`, che usa LDRH.
Il lettore ARM9 dell'emulatore locale maschera il bit basso dell'indirizzo;
un puntatore dispari legge dal byte precedente, non dal comando serializzato.
È una prova di contratto/istruzioni, non un freeze osservato nel gioco.

La prima variante Steven (+149 byte) spostava il movimento0x706 a0x79B:
è stata rifiutata. La versione finale ha gate91 byte, crescita142 e movimento
0x794 allineato; il checker verifica tutti i target, non soltanto quel caso.

La guardia Eevee preesistente spostava invece undici movimenti da offset pari
a dispari: inserimento17 byte prima dei movimenti e14 byte in coda. Questo è
un difetto della composizione1.3.1, distinto dai bug storici Drayano/Plus1.03.
La correzione usa guardia20 byte + coda14 (totale34); il BufferPlayersName0
aggiuntivo è identico al comando originale immediatamente successivo, soltanto
sul successo. Tutti gli undici movimenti restano pari; la refusal non cambia.
Test negativo precedente, modelli e dispatcher ARM corretto passano. Le prove
dei percorsi logici precedenti conservano il proprio limite.
Le due prime campagne cumulative sono state interrotte (codice130), non
promosse a PASS: gli hash prodotti in quelle prove sono esclusi dall'accettazione.

## Composizione e identità

Il nuovo stadio `legacy`, fra `gifts` e `controls`, dichiara `legacy-scripts`
per i soli membri 93/141/757 di `a/0/1/2` e `legacy-events` per i membri
71/440 di `a/0/3/2`. I producer non scrivono una ROM; si fondono con gli altri
delta prima dell'append UI. Il solo writer successivo corregge l'overlay 2 nel
medesimo slot compresso da 42.700 byte.

La prima codifica Ninnananna non entrava nello slot (+4 byte) ed è stata
rifiutata. La variante finale riusa il primo risultato del getter radio puro,
conserva gli shift e il cap comune e non cambia FAT, y9, header o seed UI.
Il getter e la lettura del numero sequenza sono fissati per hash/preimmagine;
nessun consumo PRNG aggiuntivo. Non sono assegnati nuovi slot residenti.

Input delle prove codice EN/IT: V4
`179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` e
`2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156`.
Gli originali e i file manuali già consegnati non sono sovrascritti.
**237 test mirati PASS, zero skip**, inclusi dispatcher ARM Eevee EN/IT,
Ninnananna, script/delta/rilocazioni e integrazione dei registri. Le due prove
cumulative precedenti sono interrotte130, non PASS. La consegna interna
richiede una composizione finale con questi sorgenti, ricevute nuove e
test sul dispositivo.
Una fixture con evidenze sintetiche non è una candidata accettata o consegnabile.

## Elenco delle correzioni nostre, distinto per origine

| Origine | Caso | Attribuzione e stato |
| --- | --- | --- |
| HGSS retail | HG-F15 Ninnananna | Correzione nostra nei sorgenti1.3.1, prova ARM prima/dopo. Nuovo collaudo in partita/save aperto. |
| Hack ereditata | SG-05 Mew | Correzione nostra1.3 delle tre attese movimento, con [riproduzione e prova storica](deep-debug-2026-10-28.md#crash-mew-riprodotto-e-causa-dimostrata); nessuna nuova garanzia flashcard. |
| Hack ereditata | SG-19, sottocaso flag alti/Rubrica | Correzione nostra1.3 di una concreta sovrapposizione, [contratto e prove](../features/event-flags/README.md). Non una spiegazione universale di tutti i reset segnalati. |
| Hack ereditata | V-CHATOT, 24 gate `61xx` | Bug ROM confermato: variabili fuori SaveVarsFlags aliasavano la registrazione Chatot. HF02 separa i proprietari e conserva una volta il gate zero/nonzero. Composizione e ARM EN/IT passano; 8/8 cicli zero/HF01 passano SAVE/cold, mentre scene e dispositivo restano aperti. |
| Hack ereditata | SG-08 Lyra/Ethan | Cleanup dopo perdita preparato oggi; prove modello e readback, runtime nuovo aperto. |
| Hack ereditata | SG-09 Cura Totale | Quantità436→1 preparata oggi; nessuna rimozione retroattiva. |
| Hack ereditata | SG-15 Steven/Lati | Precedenza condizionata preparata oggi; identificatori e altri stati preservati. |
| Hack, ramo di errore | SG-15b Enigma/Borsa | Guardia difensiva preparata oggi sul fallimento modellato della consegna; qualificare la raggiungibilità naturale del pocket pieno. Non una perdita osservata in partita. |
| Nostra integrazione1.3.1 | BUG-131-01 Eevee | Difetto di allineamento introdotto dalla precedente guardia, ora corretto nei sorgenti e verificato nel dispatcher. Non è un bug originale HGSS o Drayano. |

Hail, Rough Skin Garchomp, Volo Claydol e Night Slash Scizor risultano già
coerenti con correzioni ereditate: **non attribuirle a noi**. Per modifiche
precedenti e versioni pubblicate fa fede il changelog; non spostare i fix
preparati oggi nella colonna «rilasciato». La [matrice completa](legacy-bugs-1.3.md)
mantiene anche casi aperti, smentiti o non applicabili.

## Cosa resta aperto

Checkpoint operativo del **4 novembre 2026**. Questa è la coda canonica dei
casi non ancora chiusi; le prove finali su UI, SAVE/cold e dispositivo dei fix
già integrati restano gate di release, ma non vengono ricontate qui come nuovi
bug da correggere.

Follow-up del 5 novembre: due segnali storici sono stati rimossi dalla coda fix
con prove pubbliche ripetibili e senza cambiare la ROM. **HG-F12** non è presente
nei dati delle candidate: 62 componenti roccia della Grotta Scura, 118
intersezioni e 111 celle uniche hanno zero behavior acqua; il mutante positivo
è rilevato. **HG-D01** non si applica alla Plus: fra tutte le specie 1–493,
Glalie maschio è l'unico padre compatibile di Nosepass che apprende Head Smash
(livello 42); Aron e Froslass sono i controlli negativi. Restano prove statiche
sui dati esatti, non gameplay renderizzato.

Lo stesso follow-up aveva inizialmente classificato **HG-F13** come non
riprodotto, ma il trial usava un solo Giù e osservava `cmd=9`, non il salto
follower. La scansione corretta con il secondo Giù ha poi dimostrato e corretto
il difetto; il risultato sostitutivo e i suoi limiti sono registrati nella
sezione HG-F13 del 5 novembre sopra.

**HG-F05**, 5 novembre, è invece confermato sulle candidate attive EN/IT. Nel
positivo la sopravvivenza al veleno scatta mentre il follower salta: lo standard
2003 eseguiva `ScrCmd_609`, che azzera comando/step e `SingleMovement` senza
azzerare `facingVector`, poi `LockAll` saltava il proprio wait. Il vettore
restava `+0x6000`, esattamente `+0x8000` rispetto a fuori cadenza, non
avvelenato e HP4. Il producer `poison-follower-script` cambia soltanto la word
dell'entry 3 del membro `a/0/1/2:3`, target `0x584→0x586`, entrando dal
`LockAll` esistente: 6.163 byte e istruzioni restano invariati. RED 609≠96,
GREEN EN/IT, contratto eseguibile, mutanti e replay passano. Due candidate
temporanee applicate agli attivi chiudono il positivo a `-0x2000`; i tre
negativi EN sono invariati e tutte le copie save restano uguali. Mancano save
naturale, altre sporgenze/reset, SAVE/cold e dispositivo.

| Famiglia | Stato verificato | Prossimo passo ammesso |
| --- | --- | --- |
| Catalogo storico/community HGSS | **54 fenomeni qualificati, non 54 bug confermati.** Le voci senza esito esplicito (fra cui grafica/collisioni/follower, RTC, Pokéwalker, Pal Park e GTS) restano segnali pre-promozione, spesso regionali, deboli o dipendenti da servizi esterni. | Promuovere una voce alla coda fix soltanto dopo identità della revisione, procedura deterministica, atteso motivato, positivo e controllo negativo sulla candidata. |
| Daybreak, candidati statici | **0 da riprodurre.** I finding della scansione sono classificati. La TOCTOU cooperativa dei sorgenti è ora separatamente riprodotta anche tramite un vero import Python; una copia `0700/0400` è modificabile dallo stesso UID. | Broker con UID distinto/autorità amministrativa: snapshot descriptor-bound, mount kernel read-only e nuovo interprete/toolchain protetta. L'in-process corrente non possiede questa barriera. Non rilanciare la scansione sigillata. |
| Pokégear AutoCull | **Corretto nei sorgenti/al componente.** Un trampoline lossless nell'overlay 101 raggiunge il thunk ARM9 registrato; lo stream resta nello slot esatto di 53.576 byte. Confini signed, `autoCull=0`, ABI, EN/IT, riserva e composizione passano. | Pan→zoom→pan renderizzato, SAVE/cold e dispositivo: sono gate di accettazione, non un nuovo fix. |
| HG-F24 Lettore GB | **Corretto nei sorgenti/al componente.** Il wrapper confinato conserva l'helper e ricarica 1011 soltanto con GB ON; cinque prove, interprete Thumb-1, composizione EN/IT e riserva passano. | Cattura PCM/UI naturale EN/IT, accetta/rifiuta/annulla, SAVE/cold e dispositivo: sono gate di accettazione, non un nuovo fix. |
| HG-F06 GB Sounds/Surf | **Fonte corroborata; non riprodotto nel fixture diretto EN/IT.** Il trigger canonico dalla Borsa esegue ON→OFF e torna a Surf 1014, coda/fade 0, stato `0→1→0`, volume 128. Dopo OFF il sink PCM post-mix resta attivo per 600 frame per lingua, senza frame silenti o quasi silenti. La prima differenza deterministica è la scena audio `0x33` impostata da `Bag_Init` e saltata dall'uso registrato, ma non produce una divergenza difettosa. | Incontro e transizione Cannella/Percorso 20 restano `FIXTURE_LIMIT`: serve una fixture open-water naturale che manifesti il mute e un trace della prima divergenza. Nessuna patch speculativa sulla sola scena `0x33`. |
| SG-SV01 salvataggio Plus | **Fix sorgente/componente presente e gate emulatore chiuso.** L'esatto payload passa 0/2, A-only, B-only e 2/2 su copie raw EN/IT. Il SAVE/cold IT fisico sano contiene entrambi i mirror `SGP2` validi. Sul vero `WriteBackup`, fault injection 0/2 e 1/2 produce `FAILED`/`PARTIAL`, export→stop→cold conserva le impostazioni e due run sono identici; ROM/save originali restano invariati. | Resta soltanto il limite distinto del guasto reale del supporto fisico e la copertura EN sul dispositivo; non è una causa ROM ancora aperta. |
| HG-D02 Azurill→Marill | **Chiuso `WONT_FIX` per invarianti lossless.** I 64 PID `0x7F..0xBE` rendono incompatibili specie Marill, stesso PID, sesso femmina e scambio vanilla. Il replay ARM9 EN/IT fresco passa 2/2. | La politica conserva Pokémon esistenti, PID, save e interoperabilità vanilla; nessuna patch ratio/cache/PID. Resta un limite retail documentato, non un fix aperto. |
| SG-TR03 Jose | **Anomalia dati riprodotta; `SOURCE_EXHAUSTED`.** Thread/Wayback, ZIP ufficiale 2012, sei PDF, FAQ/video, mirror e guide non contengono il roster destinazione. | Solo una nuova fonte autoriale o una scelta esplicita di bilanciamento può riaprire il caso. |
| SG-13 nomi Percorso 34 | **Rinomina mancante confermata; `SOURCE_EXHAUSTED`.** La nota autoriale conferma che i nomi non sono rimasti, ma lo stesso corpus non pubblica quelli voluti. | Solo una nuova fonte autoriale; non inventare sostituti. |
| SG-01 blackout Safari generico | **Parzialmente separato.** SG-01a, SG-01b e SG-02 sono dimostrati e corretti al componente; menu/audio/turbo generici restano non isolati. | Raw save immediatamente precedente, prima callback errata, turbo/menu/audio e controllo hardware. |
| SG-04 Lastra Ghiaccio/Steven su R4 | **Segnalazione hardware aperta; nessuna causa comune dimostrata.** | Modello R4, kernel, save e prima callback errata autenticati. |
| SG-16 Celebi/Giovanni | **Non riprodotto; quattro cause statiche confutate.** | Save autentico pre-evento e trace della prima divergenza; nessuna patch per analogia. |
| SG-LATIOS | **Intermittente non riprodotto; causa non isolata e criterio di arresto raggiunto.** Venti cold boot e 36 scenari correnti entrano in lotta. Script 776/evento 51 sono byte-identici fra 1.2.5 IT e trial EN/IT; usano oggetti 20/21/22, non 5. Il singolo passo di Latios termina prima di cry/fade/lotta e i test totem 7/7 più shiny route/abort 53/53 passano. Il difetto Mew è strutturalmente diverso; la nota audio bloccata resta un sintomo, non una causa. | Riaprire soltanto con save/configurazione che manifesta il freeze o con un ambiente indipendente capace di trace ARM9/ARM7/FIFO sincronizzato. |
| HG-T10 scena leggendario | **Duplicazione Ho-Oh e mismatch titolo corretti al componente e integrati nella candidata EN `02cccfbf…f0af` / IT `35d459e3…8f4`.** Runtime sintetico EN/IT e controllo Ho-Oh passano; il freeze completo non è riprodotto e lo stato naturale resta irraggiungibile nella Plus. | Restano scena naturale completa, battaglia/cattura e trace scheduler del freeze; nessuna nuova prova sul dispositivo fisico o SAVE/cold. Gli 8 test storici del solo guard non sostituiscono la nuova prova dei consumer cinematografici. |
| HG-T11 GTS vuota | **Classificato al componente; body vuoto confutato, record vuoto length-valid riprodotto; freeze non riprodotto.** Sulle V4 EN/IT l'overlay 70 accetta ogni unità da `0x124` byte senza validare Pokémon/trainer: 0 byte blocca «Select», 292 byte zero lo rende raggiungibile. Record Pokémon checksum-corretto e trainer popolato ed errore `-13` sono i controlli; banco offline 5/5. | Nessuna patch: il payload storico e l'esito UI mancano, mentre un validatore inventato può rifiutare record leciti. Riaprire soltanto con payload catturato/autenticato o servizio controllato che manifesti il nero; non usare la rete pubblica. |
| Cap oltre 100 | **Funzione non installata; non è un bug corretto.** Il contratto host cap 150 è provato, ma restano bitfield a 7 bit, learnset, Honey Gather, UI, scaling e migrazione. | Decisione di prodotto su statistiche/scaling e implementazione completa lossless prima di qualunque ROM candidata. |

SG-TR01 è confutato sulla linea disponibile, SG-TR02 è corretto, SG-13 e
SG-TR03 non sono autorizzazioni a inventare contenuti. I fix già installati che
richiedono soltanto gameplay/UI, SAVE/cold o dispositivo rimangono nel registro
di accettazione e non rientrano in questa coda di diagnosi.

**SG-SV01 — perdita silenziosa delle impostazioni Plus su errore di scrittura**
è confermato al livello componente/codice macchina e il primo fix è ora nei
sorgenti 1.3.1. Sul blob spedito da 500 byte, due ritorni di
errore consecutivi da `WriteBackup` lasciano invariati i settori 47/111, ma il
runtime passa ugualmente a `load_status=VALID`; un cold load successivo vede il
record assente e riporta difficoltà Plus e selvatici a zero. Il controllo sano
conserva entrambi i mirror e il controllo con salvataggio nativo fallito non
chiama `WriteBackup`. Il riproduttore non usa ROM/save e non misura quanto il
fallimento sia raggiungibile su hardware. Il successore compilato con
`SGP_SAVE_WRITE_STATUS_FIX` conserva il valore di ritorno vanilla e registra a
`SgpStato+5` successo pieno, parziale o fallito: 0/2 copie non convalida un
record assente, 1/2 copie è `VALID` ma parziale e torna valido al cold load,
anche quando la sola B è nuova: il loader ispeziona entrambe e sceglie il
`saveno` valido più recente. 2/2 è successo pieno. Il payload autenticato è
608 byte (`f6d42c2d…c5c4c4d`) nello stesso comparto da 736 byte; il call-site
esistente viene ritargettato alla nuova entrata e verificato byte per byte,
mentre layout save e blob storico restano immutati. QSalva passa 18/18;
installer e reader EN/IT passano 2/2, registrazione legacy 3/3 e le composizioni
reali V4 in memoria verificano i quattro owner. Il follow-up esegue poi l'esatto
payload installato su copie temporanee di due raw save EN/IT da 512 KiB con
impostazioni Plus e Borsa estesa: 0/2, sola A, sola B e 2/2 producono otto cold
load corretti, con originali invariati e differenze confinate ai due record da
32 byte. Questa prova ha scoperto e corretto un difetto del banco: il kernel
HGSS `0x020E38E0` usa CRC-CCITT normale `0x1021`, mentre lo stub e
`sgp12.chunk` riusavano il CRC riflesso `0x8408` dell'header cartuccia. Le
fixture raw valide rifiutavano il vecchio mutante. La candidata IT conservata
ha poi completato SAVE dalla UI e cold restart sul dispositivo; il raw di prova
post-SAVE contiene due mirror `SGP2` validi e identici, generazione `0x72`.
Questo accetta il percorso fisico sano 2/2. Il follow-up locale intercetta poi
il vero `WriteBackup` tramite GDB loopback, senza patch ROM/emulatore: 0/2
ritorna `[0,0]` e `write_status=FAILED`; 1/2 ritorna `[0,1]`, lascia A alla
generazione 108 e avanza B valida a 109 con `write_status=PARTIAL`. Export,
stop, cold Continue e seconda esportazione conservano le impostazioni e la SRAM
attesa; due run producono lo stesso report. Originali invariati. Resta separato
il guasto reale del supporto fisico e la copertura EN sul dispositivo, non un
difetto ROM ancora da correggere.

**Cap oltre 100 — modello verificato, funzione non installata.** Il campo
`over100` del chunk e il valore futuro 150 sono riserve di formato: il loader
imposta ancora cap 100 e nessun percorso osserva un Pokémon del giocatore per
sbloccarlo. Motore EXP, lotta, Caramella Rara, Pensione nativa, Training, Box,
shiny e learnset conservano limiti espliciti a 100; i livelli 128–150 incontrano
anche il formato learnset a sette bit. La difficoltà Plus corrente non è un
aumento fisso del 10%: usa curve precompilate, limitate a 100, circa +6%→+12% per gli
allenatori e +5%→+8% per i selvatici. Non viene quindi “attivato” un flag nella
1.3.1. La decisione storica recuperata dall'archivio di progettazione locale
era cap **150**, non 140. Gli archivi documentano un checkpoint CORE e candidate
diagnostiche cap150 del 9 settembre, ma il percorso originario non esiste più:
il controllo cap100 entrava in lotta, quello cap150 restava nel campo e
`cap150_fix_qualified` era falso. Esistette quindi un tentativo/prototipo
descritto, non una funzione qualificata o oggi recuperabile da promuovere; non
esiste una build accettata su ARM, save/cold o dispositivo. Il nuovo componente
ROM-free `features/extended-levels` fissa e
prova il contratto corrente: cap iniziale 100, latch permanente quando un
Pokémon non-uovo già commesso a Party/Box/Pensione è osservato a livello 100 o
superiore, picco monotono e cap derivato 150. Nella sessione corrente tutte le
14 prove host passano impostando `SGP_CAP150_ROM` alla candidata V4 EN
autenticata. Le prove eseguite includono tutti i 65.536
stati byte del latch, tutte le transizioni canoniche, mutanti e
confini 99/100, 100/101, 127/128, 149/150 e il mutante overflow u32. Le otto
tabelle reali `a/0/0/3`
delle candidate V4 EN e IT coincidono con le preimmagini pin-nate; il generatore
preserva esattamente i 404 byte 0–100 e produce in modo deterministico le soglie
101–150 con intermedio a 64 bit. Non scrive una ROM e non è uno stadio della
pipeline.
Prima dell'installazione va mantenuta la decisione di saturare ogni statistica
a 999 e va fissato lo scaling avversari; poi vanno
provate curve EXP, 127→128, Box/Pensione/scambi, UI e migrazione dei vecchi save
senza perdere progressi o impostazioni.

La mappa statica M1 ha inoltre trovato quattro blocchi non coperti dal vecchio
progetto. `metLevel` nel BoxPokemon è un bitfield a sette bit: catture/scambi a
128–150 registrerebbero 0–22 senza una policy compatibile col save. Honey
Gather produce indici 10–14 oltre il livello 100 per una tabella da dieci righe,
mentre Pickup satura già correttamente. Summary e overlay 8 comprimono anch'essi
il livello in sette bit e leggono `T(level+1)`. Il rientro dal Pokéwalker ha un
proprio gate 100 e accredito di un solo livello. Infine battle e Pensione oggi
clampano a `T(100)` prima che un observer post-commit possa accendere il latch:
un premio 99→101 perderebbe l'eccedenza se l'ordine non viene definito. Sono
blocchi d'integrazione dimostrati nel sorgente retail/Plus, non bug raggiungibili
nella ROM attuale che resta correttamente limitata a 100; non è stata applicata
una correzione speculativa.

**Audit incrociato delle funzioni Plus.** Non è emerso un nuovo difetto nel menu
o nella Guida, ma la verifica d'integrazione ha dimostrato
**SG-PIPE-BAG-ABI-01** nella prima composizione sorgente di SG-BAG-FOREIGN: 12
dei 16 ingressi pubblici Training usati da hook ARM9/overlay e Shiny/UI erano
stati spostati. La versione finale conserva byte e ABI storici, devia soltanto
gli 8 byte iniziali di `training_save` e aggiunge una guardia da 184 byte nel
margine, lasciandone 172 liberi. Il test rosso Shiny e la matrice dei 16 consumer
sono verdi; l'applicazione diretta EN/IT passa, mentre il BuilderChain corrente
resta da ripetere con gli asset UI privati. È una regressione della pipeline di
sviluppo, non di una release pubblicata. Le altre campagne mirate passano:
Caramella Rara 17/17 EN/IT,
Borsa ARM 16/16 per lingua, shiny 126 con due sole integrazioni private saltate,
Training 35/35, controller Opzioni 19/19, persistenza Plus 18/18, modulo/scena/
bridge UI 30/30, Opzioni/ownership/painter/input 81/81 e Guida 53/53. `HOLD` è
un arresto fail-closed: trattiene proprietari e risorse quando non può provarne
la distruzione, e non è stato reso raggiungibile da gameplay normale. Resta
separato **SG-UI-WAIT**, riprodotto soltanto al componente con fault injection:
dopo un repaint reale la sola soppressione del callback VBlank lascia `SC_WAIT`
stabile per 256 chiamate main, senza nuove allocazioni, accessi FS o mutazioni
dei buffer; lo stesso callback eseguito una volta pubblica il pending e riporta
la scena a `SC_IDLE`. Non è dimostrato che il gameplay possa continuare mentre
il VBlank registrato non viene mai eseguito, quindi resta candidato/limite del
banco e non autorizza a indebolire ownership o controlli. Servono misura
sull'esatta candidata e sul dispositivo Android di destinazione. Le 155 prove
qualificate sull'attuale sorgente UI passano. Il successivo controllo di
identità ha corretto una classificazione del banco: gli stessi sorgenti con
configurazione ridotta `4/8/240` producono `b036cb…cb62` (64.712 byte), mentre
la configurazione di produzione `64/8/240` riproduce esattamente il modulo
cronometrato `62ac98…a8239` (64.728 byte); coincidono anche tutte le 68
dipendenze registrate. Le misure 84/99 restano quindi valide per quel modulo e
per la ROM pin-nata del benchmark, non per una composizione successiva o per il
dispositivo senza una nuova prova AB/BA. È una correzione documentale del banco,
non un nuovo bug ROM.

Il rerun del banco UI ha riprodotto anche due falsi rossi del runner, separati
dal gameplay: i bench Painter Opzioni/Guida e il bench persistente importavano
`sgp12` senza aggiungere `source/` quando eseguiti dalla directory ufficiale.
I tre bootstrap ora dichiarano il percorso prima dell'import. Dopo la
correzione passano Settings/Opzioni 105/105 (Painter 21/21), Guida 53/53 e UI
nativa Class A 185/185. Nessuna ROM o save è stata aperta da queste correzioni;
SG-UI-WAIT e le prove candidata/device restano invariati.

Il banco SG-UI-WAIT copre ora otto combinazioni: Opzioni/Guida,
`SC_WAIT_FIRST`/`SC_WAIT` e budget sincrono 4/64. In ogni caso 32 callback senza
VBlank conservano fase, epoche, front/pending, versioni, allocazioni, FS e tutti
i buffer; `VCOUNT=241` oltre la deadline 240 è rifiutato senza mutazioni,
mentre `VCOUNT=192` pubblica, torna a `SC_IDLE` e consente teardown completo.
La matrice passa in 186,508 s e il riproduttore storico separato in 32,947 s.
Questa estensione dimostra integrità e recupero del componente, non la perdita
naturale della callback su ROM/emulatore/dispositivo.

La matrice Caramella/Borsa esegue inoltre le API ARM reali della Borsa ampliata,
senza stub di quantità/rimozione: slot nativo 0 e primo slot extra 165 passano
2→1 (menu ancora aperto) e 1→0 (uscita), in EN/IT. Il predicato nativo accetta
livello 99 e rifiuta 100 senza consumare la Caramella nello slot extra. Non è
emerso un bug d'interazione; questo non implementa il cap 150.

La ricognizione funzione-per-funzione distingue inoltre presenza da
attivazione. Difficoltà Plus e selvatici sono installati e il banco ARM reale
copre 672 confronti, ma le curve correnti sono rispettivamente circa
+6%→+12% e +5%→+8%, non un +10% fisso. Shiny Classic/Pro/Search è installato e
126 test passano, con due sole integrazioni private rinviate alla candidata
successiva. Borsa e Caramella sono attive. Per il Box portatile, le baseline
tecniche della pipeline restano intenzionalmente **inerti**, ma non descrivono
la ROM installata. La candidata IT corrente `171b53b6…d64a0` ha i gate attivi,
include il successore da 2.952 byte con SG-BOX-NULL corretto ed è installata
in-place. Lo smoke locale EN/IT raggiunge `PC_RUNNING` senza crash; l'uso
fisico del Box era già confermato sul predecessore `420ec8b8…f059a`, mentre la
matrice completa sul successore corrente resta distinta. I test del componente
e SG-BOX-NULL restano distinti
dalla campagna estesa ancora aperta (R/tocco, operazioni PC, 50 cicli, pressione
heap, contesti negati, SAVE/cold e rilettura fisica corrente).
Opzioni e Guida sono implementate e non mostrano nuovi crash/leak nelle suite,
ma richiedono ripetizione sulla candidata composta e accettazione dispositivo.
Le sette fixture raw EN/IT provano Continue→SAVE→cold sulla candidata
precedente, incluse impostazioni Plus e Borsa, ma non certificano
automaticamente il successore con gli ultimi fix. I limiti aperti restano
accettazione raw-save/cold di SG-BAG-FOREIGN, non-regressione/pressione heap del
Box, SG-UI-WAIT, misure della UI sorgente corrente e la nuova campagna raw-save;
non vanno riassunti come “tutte le funzioni chiuse”.

**SG-BAG-ALLOC-01 — dereference NULL nella Borsa ampliata, corretto nei
sorgenti.** Il blob
installato della 1.2.5 è stato eseguito forzando a zero soltanto il ritorno di
`Heap_Alloc` usato da `sgp_cap_new`: il codice entra in `cap_clear(0)` e termina
con `UC_ERR_WRITE_UNMAPPED`, PC `0x023DBFF4`, `r0=0`. Il controllo sano con
allocazione riuscita completa copia, modifica e copia inversa della Borsa
privata. È quindi un bug dimostrato al livello componente/codice macchina, non
una misura della raggiungibilità sotto pressione heap in partita. Il
riproduttore privato autentica ROM EN 1.2.5 `a821961f…050e` e blob
`e41d95a3…c1fb`; nessuna ROM o save viene modificata. Il successore 1.3.1
riscrive in luogo i soli 28 byte di `sgp_cap_new`: una chiamata Thumb diretta
libera il literal necessario alla guardia `NULL`, senza spostare le altre
entrate o usare altra riserva. Esecuzione reale EN/IT verifica ritorno zero e
nessuna scrittura sul fallimento; il controllo positivo restituisce la copia e
azzera ancora 2.380 byte. Reader, mutante e composizione legacy passano. Il blob
storico resta immutato. Restano frequenza reale sotto pressione heap, candidata
conservata, SAVE/cold su copie raw e dispositivo.

**SG-BOX-NULL — costruttore squadra dopo il Box portatile, confermato e
corretto nei sorgenti/al componente.** Il wrapper nativo
`PartyMenu_LaunchApp_Unk1` chiama `PartyMenu_CreateArgs` e scrive subito a
`args+0x18` senza controllare `NULL`; la sonda preventiva del modulo Plus non
eliminava la finestra tra le due allocazioni. Il riproduttore ARM EN/IT forza il
vero costruttore a restituire zero dopo il ritorno dal PC. Il successore chiama
direttamente il costruttore pin-nato, controlla il risultato, inizializza gli
stessi campi e passa dal wrapper di lancio Plus; su fallimento torna al campo
senza dereferenziare o lanciare. Il payload misura 2.952/3.024 byte, stack
massimo 48 byte. Suite runtime 20/20, unità installer 26/26, ROM EN/IT 25/25 e
composizione sulla UI reale 1/1 passano. La candidata IT attiva
`171b53b6…d64a0` include questo payload ed è installata; lo smoke locale EN/IT
apre il PC nativo e torna senza crash. L'attivazione e l'uso fisico del Box sul
predecessore sono confermati separatamente; restano da provocare
questa specifica seconda allocazione fallita sotto pressione heap reale e da
ripetere operazioni PC, SAVE/cold e non-regressione estesa sul dispositivo.

**SG-BAG-FOREIGN — perdita dei 108 slot extra con destinazione flash estranea,
dimostrata e corretta nei sorgenti/al componente.** Con lo slot 252 valorizzato, 452 byte non uniformi nella
banca inattiva fanno rifiutare correttamente la scrittura dell'estensione, ma
il save nativo restituisce successo e avanza generazione/banca. Al cold load la
nuova banca non ha un'estensione corrispondente e lo slot extra torna vuoto;
i byte estranei restano intatti. Il successore Training controlla lo status 2
prima del writer nativo: con almeno uno dei 108 slot extra vivo restituisce il
fallimento recuperabile e non avanza il save; con estensione vuota o sole celle
native consente il commit senza sovrascrivere i byte estranei. L'integrazione
finale conserva esattamente il payload Training storico da 11.420 byte e tutti
gli ingressi pubblici, sostituisce gli 8 byte iniziali di `training_save` e
accoda una guardia Thumb da 184 byte; il comparto usa 11.604/11.776 byte. Blob/
ABI Borsa, hook e layout save restano invariati. La composizione save corrente
passa 14/14 e i 5 test dedicati conservano tutti i consumer e applicano lo
stadio direttamente a EN/IT. Il BuilderChain completo corrente è stato saltato
per asset UI privati mancanti. Restano UI del fallimento, SAVE/cold su copie raw
e dispositivo.

**SG-BAG-WRITE-01 — perdita potenziale dei 108 slot extra quando la scrittura
estensione fallisce, dimostrata e corretta nei sorgenti/al componente.** È distinta da
SG-BAG-FOREIGN: con uno slot extra vivo, sia il fallimento delle due scritture
(status Borsa 3) sia il flash illeggibile (status 4) conservano il record solo
in RAM, ma il vecchio percorso senza Training attivo/valido invocava comunque
il writer nativo (`native_saves=1`, ritorno 2). Il modello cold-load esistente
mostra che la banca appena avanzata può non contenere l'estensione e perdere lo
slot. La guardia confinata ora tratta gli status 2–4 come non durevoli quando
uno dei 108 slot extra è vivo: restituisce il fallimento recuperabile 3 e il
writer nativo non viene raggiunto. Estensione vuota e status parziale 5 sono
controlli negativi e continuano a committare. La composizione ARM Bag/Training
passa 14/14 e identità/ABI 5/5, inclusa applicazione diretta EN/IT. Il replay
BuilderChain è stato saltato per asset UI privati mancanti. Non sono ancora
provati candidata completa, fault injection su copia raw, SAVE/cold o frequenza
hardware.

**SG-PIPE-BAG-ABI-01 — spostamento degli ingressi pubblici Training nella prima
integrazione SG-BAG-FOREIGN, dimostrato e corretto.** La ricompilazione completa
spostava 12 dei 16 consumer reali; la transazione Shiny osservava
`unavailable=1` invece di 0. Il controllo negativo autentica la baseline e
decodifica load/save, item, EV, can-use, retrieve, growth, play, script, battle,
phone, sprite/category e i tre ingressi Shiny. Il trampoline confinato sopra
mantiene tutti e 16 gli indirizzi e la transazione torna valida. È un bug della
pipeline corrente, non un bug interno a una ROM già pubblicata.

**SG-PIPE-REMATCH-01 — replay rivincite su preimmagine già trasformata,
corretto.** La prima composizione completa superava i fix legacy ma lo stadio
`rematches` ricostruiva il modulo da quell'immagine e pretendeva ancora il pin
V4 di `a/0/5/6`, già modificato legittimamente dal producer pesca. Il modulo è
ora derivato una volta dai byte V4 autenticati, registrato nella ricevuta UI e
consumato dalla stessa delta immutabile in writer, reader, peel e attivazione.
Il percorso attivo può differire soltanto nel byte dichiarato. I 108 test
mirati passano; catena inerte e replay reali fino a `rematches` passano EN e IT
senza conservare ROM. È un bug della pipeline di build, non un difetto gameplay.

**SG-PIPE-REMATCH-TMP-01 — ambiente temporaneo del compilatore rivincite,
dimostrato e corretto.** La composizione completa EN/IT falliva prima degli
stadi gameplay: l'ambiente autenticato rimuove correttamente lo stato utente e
imposta `HOME=/var/empty`, ma il compilatore rivincite non aggiungeva un
`TMPDIR` scrivibile. Clang terminava con `unable to make temporary file`.
Il wrapper ora usa il work dir privato già creato, come gli altri produttori
ARM. Il test dell'ambiente, lo stub reale da 60 byte e la composizione/replay
integrale bilingue passano. È un difetto della pipeline, non di una ROM
pubblicata.

**HG-F17 Facade è dimostrato e corretto nei sorgenti/al componente.** Il membro
263 EN/IT `1f9cd6b…eebbd` avvia sei task scale/restore 5+5 frame ogni 8 frame.
Dispatcher `0x2D`, funzione `0x2A` e macchina a stati dell'overlay 7 HGSS
pin-nato provano le durate: cinque coppie consecutive si sovrappongono. Il fix
causale conserva i task e sincronizza i cinque Delay e il suono 8→10, sei byte
fisici; il workaround HGSS 4+4, delay-only e audio-only sono controlli negativi
e non vengono combinati. Le V4 EN/IT passano da cinque overlap a zero; writer,
reader, mutanti, confinamento e composizione/replay integrali bilingue sono
verdi. Restano rendering, watchpoint X/Y, 1/2/16 usi, entrambi i lati,
animazioni disattivate, SAVE/cold e dispositivo. Nessuna ROM o save è stata
conservata.

**HG-F20-DP DynamicPunch è dimostrato e corretto nei sorgenti/al componente.**
L'ID storico HG-F20 viene mantenuto come umbrella: Helping Hand (`HG-F20-HH`)
ha una chiusura separata sotto e Spit Up (`HG-F20-SU`) è una causa distinta,
anch'essa corretta al componente. Il membro
223 di `a/0/1/0`, SHA pre `e481d17d…2fab2`, avvia lo shake breve
`(1,0,1,2)` e, dopo `Delay 2` più `Delay 3`, lo shake lungo `(4,0,1,10)`.
Le routine Thumb reali dell'overlay 7 producono
`+1,0,-1,0,+1,0,-1,0`; la callback Delay riprende dopo N+1 chiamate. Il
secondo task nasce quindi al tick 7 e fotografa X=-1. Il producer cambia solo
il valore del secondo Delay 3→4 a ROM `0x0106FC88`: nascita al tick 8, base e
finale X=0. Facade precede questo stadio nello stesso NARC; il writer accetta
soltanto l'archivio Facade `8d9e8540…d35a3` e produce il combinato
`afa4fe46…dc63`, preservando i suoi sei byte. EN/IT, applicazione, confinamento,
ordine e replay passano; il riproduttore privato ARM ha risultato
`a4906b60…2efdd`. Restano scheduler/rendering completi, 1/2/16 usi, lati e
doppie, animazioni disattivate, SAVE/cold e dispositivo. Nessuna ROM/save è
scritta o conservata.

**HG-F20-HH Helping Hand è dimostrato e corretto nei sorgenti/al componente.**
Il membro 270 pre `d37bcb64…c942` conteneva `EndLoop; Delay 1`: in HGSS il
primo shake dura otto tick, mentre i Delay 3 e 2 riprendono dopo 4 e 3 callback.
Gli shake del loop partivano quindi a 0 e 7, e il secondo catturava X=-1; il
terzo shake esterno partiva a 16 dalla stessa base corrotta. Il producer sposta
il Delay esistente prima di `EndLoop`, senza cambiare lunghezza: tick 0/9/18,
basi 0/0/0. Cambiano solo tre byte ROM `0x01074B2C/30/34`; membro post
`f824c040…adc2`, archivio combinato post `476aaa76…f6ab`. Il writer accetta
soltanto il predecessore Facade+DynamicPunch e ne preserva i membri 263/223.
Gli handler reali `BeginLoop`/`EndLoop`, Delay e shake sono eseguiti su overlay
7 EN/IT; 118 test mirati e il replay confinato passano. Riproduttore privato
`9a2f8c9f…5d25a9`. La composizione/replay completa EN/IT passa; restano
rendering, ripetizioni, lati/doppie, animazioni off, SAVE/cold e dispositivo.
Nessuna ROM/save è scritta o conservata.

**HG-F18 Strength è dimostrato e corretto nei sorgenti/al componente.** Il task
reale somma lo shake `+2,0,-2,0` e con dieci aggiornamenti termina X+2; la
cleanup ripristina scala e Y ma omette X. Il producer cambia soltanto il
contatore `10→8` nel membro 70 di `a/0/1/0`, byte ROM `0x0105F3F8`, preservando
i predecessori Facade, DynamicPunch e Helping Hand. I controlli nativi
8/9/10/11 terminano rispettivamente 0/+2/+2/0; candidate EN/IT, confinamento e
replay passano in 119 test mirati; anche la composizione/replay completa EN/IT
passa. Restano rendering, ripetizioni, lati/doppie, animazioni off, SAVE/cold e dispositivo.
Nessuna ROM/save è scritta o conservata.

**HG-F20-SU Spit Up è dimostrato e corretto nei sorgenti/al componente.** Il
task reale termina X+2 e la cleanup originale ripristina scala/Y ma non X. La
postimage in-place sottrae 2; il producer/verifier autentica task, caller,
accessori ARM9, immagine logica e stream BLZ nello stesso slot. EN/IT e basi
0/1/100/253 terminano alla X iniziale; mutanti `-1/-3` terminano X+1/X-1. Cinque
test passano; anche la composizione/replay completa EN/IT passa. Restano
rendering, ripetizioni, lati/doppie, SAVE/cold e dispositivo.

**HG-F16 Giratina/PC è dimostrato e corretto nei sorgenti/al componente.** Il PC
passava `BoxMon_UpdateGiratinaForm` anche il sotto-record di un Giratina ancora
in squadra: forma e abilità cambiavano ma le statistiche restavano quelle della
forma precedente. Un hook all'uscita dal PC nell'overlay 14 chiama la routine
retail non-forzante di aggiornamento Party. Sei test nativi EN/IT coprono le due
direzioni, squadra mista, nessun cambio e cleanup. Restano UI naturale, raw
SAVE/Continue/cold e dispositivo.

La suite host ha inoltre isolato quattro difetti del **banco**, non della ROM:
`SG-TEST-BAGVIEW-MAP-01` leggeva un falso ARM9 contiguo da 2 MiB invece dei
segmenti autenticati; `SG-TEST-UINATIVE-PYTHONPATH-01` ometteva `source/` per
tre test UI; `SG-TEST-BLZ-ALT-01` presumeva un bit inutilizzato nell'ultimo
gruppo BLZ; `SG-TEST-CONTROLS-PREIMAGE-01` riusava la preimage V4 dopo che la UI
aveva correttamente azzerato lo slot Guide. I test mirati ora caricano i
segmenti reali, ricevono l'ambiente dichiarato, usano una seconda codifica BLZ
ottima della stessa lunghezza e pin-nano il postimage zero. Queste correzioni
non modificano bytes gameplay.

SG-11 e HG-T09 non sono più aperti a livello codice nella candidata corrente:
la sezione precedente registra consumer ARM battaglia/telefono, archivio pesca,
corpo IGT e wrapper Training. Restano i playtest e i limiti di accettazione lì
indicati; non retrodatare queste prove alle vecchie immagini manuali.

Il checkpoint storico HG-T10 qui riepilogato aveva il solo guard sorgente per
la duplicazione Ho-Oh. Il follow-up del 5 novembre sopra integra anche il
mismatch dipendente dal titolo e lo prova in runtime sintetico EN/IT con
controllo Ho-Oh; scena completa, battaglia/cattura e freeze restano distinti e
non riprodotti. Strength, Facade, DynamicPunch, Helping Hand e Spit Up hanno
chiusure componente separate sopra e mantengono i limiti di accettazione già
dichiarati; HG-F20 non va comunque usato come singola causa tecnica.
HG-B16 è ora dimostrato su dieci Plus EN/IT e nel costruttore ARM9 reale:
Horton #396 espone 50/50 statistiche divergenti, la forma 0 passa 10/10 controlli
e due chiamate component melonDS concordano su cinque Rotom vulnerabili, digest
`6c103588…c39248`. Il fix TDD è ora nello stadio `trainer-fixes`: riscrive in
luogo il solo helper ARM9 condiviso, aggiungendo `UpdateMonAbility` e
`CalcMonStats` prima del controllo amicizia. La candidata IT corretta passa in melonDS T0 naturale due
volte, T1/T2 sintetici, T3 naturale e forma 0 negativa; statistiche, checksum,
heap e preservazione degli input sono verdi. Il follow-up SG-TR04 riproduce sei
divergenze EN/IT prima del fix: Rotom Fan 26→78 e Wormadam Sandy/Trash slot 1
102→8/5. Dopo il fix, matrice PID/slot/forma, Frustrazione e replay passano;
le suite canoniche correnti passano 11/11 trainer e 94/94 mechanics/build, con
catene complete EN/IT verdi. Restano ordine dei turni in battaglia, SAVE/cold
e dispositivo.

AI-WEB-01 è ora dimostrato e corretto nei sorgenti. Il riproduttore esegue il
vero interprete Thumb dell'overlay 10 e la sequenza autenticata del membro 0 di
`a/0/9/9` a `+0x6450`: prima del fix, a HP attaccante invariati il punteggio
cambia ai confini 50/51 e 70/71 degli HP del difensore, mentre 25/100% HP
dell'attaccante non lo cambiano. Il resolver reale conferma che il token 0 è il
bersaglio e il token 1 l'utilizzatore. La correzione sostituisce soltanto i due
token a `+0x6484` e `+0x649C`; la stessa matrice EN/IT segue poi gli HP
dell'utilizzatore. Il reader indipendente vede undici soli byte cambiati nel
membro includendo le correzioni Pellearsa, Facade, Thunder e Metal Burst, con overlay, FAT e resto
del NARC confinati. Restano percorso Expert completo con controlli naturali
Hydro Pump/Surf, scelta mossa osservata, SAVE/cold e dispositivo.

AI-WEB-03 è ora dimostrato e corretto nei sorgenti, separato dal difetto
grafico HG-F17. Il riproduttore esegue il vero interprete Thumb dell'overlay 10
e la sequenza autenticata a `+0x5B64`: sulle candidate EN/IT il punteggio
seguiva veleno, iperavvelenamento, scottatura o paralisi del bersaglio e
ignorava lo stesso status sull'utilizzatore. Il fix cambia soltanto il token a
`+0x5B68` da 0 a 1. Dopo il fix la matrice si inverte correttamente; sonno e
congelamento restano negativi e maschera `0xD8`/delta `+1` sono invariati. La
configurazione reale delle varianti Plus di Valerio/Falkner contiene
Swellow+Fiammosfera+Facade e l'header trainer ha AI flags 7. Il patcher,
l'applicazione archivio e il replay della catena EN/IT passano. Restano il
dispatch Expert naturale con una mossa diversa, una scelta osservata,
SAVE/cold e dispositivo. La suite larga conserva due aspettative del banco da
triagiare separatamente: flag finale BLZ completamente usato e crescita
compressa overlay 12 20 byte invece degli 8 storici; non coinvolgono il membro
Facade e non sono PASS globali.

AI-WEB-04 è ora dimostrato e corretto nei sorgenti. Il dispatch autenticato del
membro 0 ripete effetto 151 (SolarBeam) a `+0x2C00`, mentre la routine Thunder
effetto 152 è presente e integra a `+0x58A4`. Il vero interprete EN/IT conferma
che Thunder non legge mai quella routine prima del fix. Il solo 151→152 cambia
un byte; dopo legge la routine e produce score 100 sereno, 101 in pioggia,
100 al sole con RNG 49 e 97 con RNG 50. SolarBeam al sole resta 102 e
Thunderbolt in pioggia 100, senza raggiungere la routine Thunder. Sette trainer
reali della candidata contengono Thunder e hanno `aiFlags & 4`, fra cui Lt.
Surge, Red e Cynthia. Patcher, pipeline ROM EN/IT e regressivi archivio passano.
Non è ancora pilotata in modo affidabile l'efficacia precomputata resistente/
immune nel percorso Expert completo; restano anche scelta naturale, SAVE/cold
e dispositivo.

AI-WEB-02 è ora dimostrato e corretto nei sorgenti. La sequenza Basic di Metal
Burst nel membro 0 autenticato conteneva due scorciatoie Stall e due confronti
con l'ID strumento 107 prima del comando finale `CheckSortSpeed`. L'ID è
Pietrabrillo, non l'effetto ritardante 107, e i rami parziali producevano score
errati anche in combinazioni Stall/Coda Lenta/Full Incense. Il riproduttore
esegue il vero interprete overlay 10, il `CheckSortSpeed` overlay 12 e i dati
strumenti autenticati EN/IT; 30 scenari per lingua coprono nessun effetto,
Pietrabrillo, doppio Stall, casi misti, strumenti ritardanti, parità/RNG,
Distortozona, Rapidartigli e Baccacrela. Il fix rende
zero soltanto i campi salto a `+0x1DFC`, `+0x1E0C`, `+0x1E20` e `+0x1E30`,
lasciando intatti opcode e geometria e delegando sempre al confronto completo
già presente. Patcher fail-closed, pipeline NARC/ROM e matrice prima/dopo
passano, incluse geometria dei salti e terminazione. Restano incontro naturale,
scelta mossa e priorità nel contesto battaglia completo, SAVE/cold e dispositivo.

La ricerca multilingue ha inoltre isolato **SG-DM02**, distinto da SG-DM01 e
SG-AI01. La chart moderna di overlay 18 contiene 322 coppie principali, marker
e due immunità speciali; soltanto Spettro→Drago e Spettro→Buio sono trasposte
(`5/10` invece di `10/5`) in sei Plus EN/IT dalla 1.04 alla 1.3.1. Il loop
danno ordinario `0x02251D28` carica davvero la chart moderna e passa il
moltiplicatore al consumer; la chart retail separata non alimenta quel percorso.
Il fix TDD cambia i soli due byte e viene composto nello stadio `ai`: quattro
test coprono l'intero oracolo 324 coppie, EN/IT reali, replay e mutanti. Manca
ancora la lotta naturale (Spettro contro Umbreon/Dragonair), SAVE/cold e device.

**SG-AI02 e SG-DM01 non sono più candidati soltanto statici.** Un banco ARM
esegue il vero comando Conversione2 `0x02240C98`, il helper
`GetTypeEffectivnessData` `0x0225260C`, il calcolo danno `0x02251D28` e il
helper grounding `0x02251C74` sulle candidate EN/IT. Prima della correzione,
Conversione2 con ultimo tipo Fairy percorre tutte le 112 righe retail senza
cambiare tipo; Ferropalla e Gravità lasciano Ground→Flying immune perché
l'indice della chart moderna viene applicato alle colonne retail. La patch
combinata conserva la geometria dell'overlay: sostituisce l'esatto span di
64 byte di Conversione2 con un helper autenticato sulle 325 righe moderne e
ritargetta soltanto i due literal delle colonne grounding. Dopo il fix,
Conversione2 sceglie Poison/Steel/Fire secondo RNG, entrambi i grounding
producono moltiplicatore 100 e i controlli Fire, Ground→Veleno e Fairy→Drago
restano invariati. Le suite mirate passano 10/10, i riproduttori ROM 13/13 e la
catena completa del producer passa EN e IT; il delta compresso combinato di
overlay 12 è 20 byte, entro lo slot fisico esistente. Restano battaglie
naturali, communication, SAVE/cold e dispositivo: il livello di prova è
correzione sorgente/componente, non accettazione gameplay finale.

Il follow-up Safari di 12 sequenze lega il secondo, terzo e quarto duo ai tre
percorsi Buck/Cheryl/Marley di SG-01a già corretti; Mira resta il controllo sano.
La correlazione spiega perché le segnalazioni si concentrano dopo quelle lotte,
ma non riproduce schermo/audio bloccati. Il censimento di 759 percorsi e 184 raw
save unici non trova una fixture su Percorso 47/48, nel complesso Safari o con
stato scena 1–3.

Un sottocaso ulteriore, **SG-01b**, è però source-bound: dopo trainer107 il ramo
di sconfitta `0x61C` aveva target `0x6C4`; il CFG terminava senza raggiungere né
`WhiteOut` né `ReleaseAll`. I quattro rami perdita partner precedenti convergono
invece tutti all'unico `WhiteOut` `0x7A4`, seguito da `ReleaseAll; End`, e il
changelog autoriale 1.05 descrive il fix della sconfitta nello stesso incontro.
Il producer unico del membro260 applica prima SG-01a/SG-02 e poi retargetta il
solo displacement SG-01b (`0x61F..0x622`) senza cambiare lunghezza: variano due
byte, mentre tutti i `CloseMsg` di SG-01a, il ramo vittoria e i quattro controlli
perdita restano identici. RED/GREEN EN/IT, mutanti, geometry/replay e checker
indipendente passano. Mancano sconfitta giocata, SAVE/cold e dispositivo; gli
altri blackout di menu/audio/turbo restano non confermati e non autorizzano
altre patch senza una prima callback errata osservata. R4 e collisioni non hanno ancora
una causa confermata sufficiente a una nuova correzione. SG-17/Cynthia è invece confutato come requisito errato:
il vero ramo non legge la Medaglia Terra e richiede Campione, starter Sinnoh in
testa e due slot liberi, coerentemente con testi EN/IT e Guida. Dodici sequenze
coprono binding, bytecode, nove specie, conteggi 1..6, mutanti e ciclo 3F9B;
nessun byte ROM è cambiato. Per Tohjo/SG-16, una campagna circoscritta
di dodici sequenze ha confutato binding/versione, attese movimento, ritorno dalla
battaglia speciale e non-terminazione deterministica del task. Il runtime resta
bloccato: il censimento di 184 raw save unici validi non ha trovato una fixture
autentica pre-evento. Nessun cambio ROM è giustificato senza la prima transizione
errata osservata.

SG-02 è invece distinto dal blackout. Il post storico #1460 conserva la
schermata del giocatore sotto il ponte mentre si avvia il primo duo sopra. Il
dispatcher `sub_0203DE04`, autenticato nelle candidate EN/IT, non legge la quota
Y del giocatore: stessa X/Z e stato variabile producono lo stesso script a ogni
altezza. Il record 0×0 non può attivarsi ed è stato confutato come causa. Una
patch globale non è ammissibile perché tutti i 217 record coordinate correnti
portano Y=0; il fix resta locale al primo duo. L'export 7 di membro260 raggiunge
ora un wrapper aggiunto di 23 byte: `GetPlayerXYZ`, confronto Y=0, salto
all'entry originale `0x1BF` solo a quota corretta, altrimenti `End` prima di
BGM/lock/movimenti. Quattro ipotesi e dodici sequenze, negativi su bordi/stato,
roundtrip, postimage confinato e composizione/replay completa EN/IT passano.
Mancano ancora raw save pre-evento, battaglia, SAVE/cold e dispositivo.

Nessun nuovo formato save, migrazione, reset, riassegnazione flag o rimozione
inventario/Pokémon è introdotto. Per V-CHATOT la successiva matrice raw copre
zero/HF01, senza Plus/con Plus/Borsa estesa in entrambe le lingue; non estende
automaticamente la compatibilità agli altri fix o a ogni save storico. Restano
le rispettive prove Continue/SAVE/cold e Training dove indicate. Nessuna nuova
accettazione Android, flashcart, visiva o release deriva dai soli test codice.

**HG-BAG-VIEW-01 è dimostrato e corretto nei sorgenti.** Il setter ARM9
`0x020778BC` delle candidate V4 EN/IT conserva il difetto retail: usa
`pocketId*12` e ignora l'indice compatto `position`. Otto sequenze all-pocket e
Items `(0,0)` spiegano perché il bug resta normalmente invisibile; il caller
gardening Berries `(4,0)` scrive invece l'entry 4 lasciando vuota la 0. Due
permutazioni confutano la falsa correzione che userebbe `position` anche come
identità. Il fix Thumb usa `position` per il solo stride; per ottenere i due
byte necessari ricodifica in 12 byte l'adiacente setter del bit e lo sposta a
`0x020778CA`, ritargettando il suo unico `BL` a `0x0203E442`. Il producer
autentica preimmagini, cambia soltanto lo span locale da 32 byte e il callsite
da 4 byte e preserva lunghezza ROM, riserva, archivi, ABI Borsa e layout save.
Riproduttore, reader, confinamento e registrazione nella catena passano EN/IT.
Poiché Unicorn locale termina con SIGILL, un interprete Thumb-1 indipendente e
limitato agli opcode osservati esegue i byte installati con canarini sulle otto
entry e conserva il setter adiacente. Picker Berries giocato, controllo Items,
Continue/SAVE/cold e dispositivo restano aperti e non sono dichiarati accettati.

**HG-LOTTO-ID-01 è dimostrato e corretto nei sorgenti.** Le candidate V4 EN/IT
contengono il setter retail a `0x02066CAC`: la prima chiamata salva i sedici bit
bassi in 0x403C, la seconda carica ancora 0x403C e la sovrascrive con i sedici
bit alti, lasciando 0x403D al canarino precedente. Anche
`Save_VarsFlags_RollLotoId` consuma i due valori RNG nell'ordine previsto e
raggiunge lo stesso setter, quindi il difetto è nella destinazione persistente,
non nella composizione del numero. Il fix `lottery-id` cambia `0x4902` in
`0x490B` nel solo secondo `ldr r1`, riusando il literal 0x403D già presente nel
getter adiacente. Lo span dichiarato è un halfword e un solo byte differisce;
ROM, riserva e layout save restano invariati. Quattro ipotesi e dodici sequenze
per lingua coprono sei ID, tre coppie RNG, confinamento, riapplicazione e lingua
errata; il riproduttore RAM-only conserva gli input. Mancano cambio giorno e
consultazione premio giocati, SAVE nativo/cold restart e dispositivo.

**SG-LATIOS resta aperto, non isolato e non riprodotto nelle condizioni
provate; nessuna patch è giustificata.** L'evento di Aranciopoli è mappa 54,
script 776/entry 16, evento 51 e `WildBattle(381,40,0)`. Su dodici immagini
autenticate dalla Plus 1.04 alle V4 EN/IT, script
`f70f4320…cbf2`, evento `e407ae57…b9a26`, oggetti e movimento sono identici.
Sei percorsi prelotta e dodici combinazioni specie/esito per immagine hanno
parametri validi e raggiungono il cleanup previsto; i mutanti rifiutano salti,
oggetti, specie, livelli o `ReleaseAll` alterati. I flag fuori dominio `3FCA` e
`3FAF` restano un difetto di ownership separato: il secondo viene scritto solo
dopo la cattura e il primo governa la presenza dell'evento, senza entrare nei
parametri del launcher una volta iniziata l'interazione.

La campagna runtime privata `ds-campaign-vermilion-latios-2026-11-03` esegue
dieci cold boot sulla 1.2.5 IT `bdf50a4f…b313d4` e dieci sulla candidata IT
attiva `420ec8b8…f059a`, variando gli intervalli A da 112 a 130 frame. Tutti i
20 tentativi raggiungono offset 1704 e proprietà della lotta con
`field_running=0`, task di transizione presenti, contatore movimento zero,
assert mode zero ed exit zero; ROM, fixture `975bc4d…f6f1a` e copie temporanee
restano invariate. Digest ricalcolato `51a28336…657f`; risultato
`1aa0a62f…1bb81f`. Il controllo precedente 1.2.5 mostra anche verso e menu
Lotta reali. Le finestre native di `Task_StartBattle`, `Task_StartEncounter`,
`Battle_LaunchApp` e `FieldSystem_ApplicationIsRunning` sono invariate fra
1.04, 1.2.5 e V4; la deviazione shiny V4 conserva ABI e percorsi di abort, con
69 esecuzioni ARM host verdi nel gruppo mirato (una suite d'integrazione
cartridge separata non raccolta da quel comando).

Questa è una non-riproduzione circoscritta, non una confutazione universale:
usa una fixture e un runtime deterministico, senza trace ARM7/FIFO/audio né lo
stato/configurazione originale del freeze. L'assenza di `WaitMovement` non è
una causa Mew trasferibile per analogia, perché nei run riusciti il movimento è
già concluso. Il criterio d'arresto vieta di ripetere lo stesso lotto; un nuovo
runtime richiede il raw save/configurazione che blocca o un ambiente
indipendente con prima divergenza ai checkpoint 1625, 1686, 1695 o 1697/1704.

**HG-F09 è dimostrato staticamente e corretto nei sorgenti per i soli Percorsi
43/44.** Le candidate attive EN/IT condividono matrix 0 e l'archivio land; i
land 87/102 legano senza ambiguità i landmark recuperati a due file contigue di
tre caselle. Il readback NSBMD mostra materiale superiore di bordo `egrass_u`
(con gli edge aggiuntivi previsti sulla terza casella del Percorso 43), mentre
la griglia permission usa `0x0002`, lo stesso behavior dell'erba pienamente
visibile adiacente. Terreno `0x0400`, acqua `0x0010` e sette celle
`egrass_u`/`0x0400` nello stesso land sono negativi e oracolo semantico. Lo
stage registrato sostituisce soltanto i sei `u16` con `0x0400`: dodici byte ROM,
lunghezza e geometria NARC/FAT invariate, nessun cambio a modelli, collisioni,
matrix, altri tile o save. EN/IT, mutanti e replay/composizione mirata passano.
Le candidate attive restano preimmagini e non includono il fix; non è stata
eseguita una prova renderizzata di incontri o follower, né SAVE/cold/device.
Percorso 28 e Safari restano esclusi finché le fonti non consentono coordinate
normalizzate univoche.

**HG-F01, HG-F03, HG-F04, HG-F10 e HG-F11 sono chiusi senza una nuova
correzione ROM, con esiti distinti.** F01 e F11 hanno esaurito le sorgenti e non
mostrano divergenze statiche: i lands 9/10 del Percorso 31 e le tredici insegne
Mart restano invariati dalla 1.04 alle candidate attive. F03 non è applicabile
alle dodici immagini EN/IT: il masso del Pozzo Slowpoke incontra la parete a
`(32,3)`, non una casella d'acqua; la revisione giapponese non è stata
inferita. In F04 il seed Y iniziale diverge, ma `MapObject_Create` invoca già
il resolver nativo: senza una fixture naturale map 139 non è lecito
duplicarlo. Per F10 il trigger storico corretto è il rifiuto dell'anziano
tramite entry palestra 4 e rientro città 12; script, init, eventi e slice
overlay sono invariati e ricreano renderer/OAM, confutando il legame ROM al
livello componente. Il censimento finale contiene 191 raw save unici, 189
validi, ma nessuna fixture Percorso 31, mappa 139 o mappe 78/80. Questi esiti
sono rispettivamente `SOURCE_EXHAUSTED`, `NOT_APPLICABLE`,
`RUNTIME_FIXTURE_LIMIT` e `COMPONENT_REFUTED`: non sono bug corretti né PASS
gameplay universali.
