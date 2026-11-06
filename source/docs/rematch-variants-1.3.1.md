# Rivincite variabili 1.3.1: Valerio e Raffaello

Rapporto del piano interno. Stato: **SOURCE_READY_FOR_REVIEW; moduli e prove
host/ARM complete, non ancora integrati nella candidata, nessun collaudo Android, nessuna prova di bilanciamento**.
Nessun nuovo ID di mossa, abilita', strumento, opzione o formato di salvataggio.

## Cosa cambia

Con la difficolta' Plus attiva, ogni volta che il gioco costruisce la squadra di Valerio (Falkner, ID 712) o di Raffaello
(Bugsy, ID 713) in una lotta singola ordinaria, la squadra letta dall'archivio puo' essere sostituita per intero da una di
due squadre complete, **A** o **B**, scritte a mano. In Normale e in ogni altro caso (altri allenatori, Lega, doppie, link,
multi, tag, facility, indice nemico diverso da 1) il gioco resta nativo, byte per byte. Livelli, byte di difficolta' (IV 31),
capsule, ricompense, orari, contatti e accessi non cambiano. Non si legge la squadra del giocatore, non c'e' contatore ne'
stato persistente, non si usa ne' si avanza l'RNG.

## Scelta della variante

`variante = (seed ^ (seed >> 16) ^ id_allenatore) & 1` (0 = A, 1 = B), con `seed` il seme LCRNG che il costruttore nativo ha
gia' salvato prima di cominciare ([sp+0x68], poi ripristinato dal costruttore a 0x02073A8E). E' un selettore a due vie, non un
generatore. La scelta avviene una volta, sostituendo l'intero buffer transitorio di 108 byte **prima** che il costruttore legga
specie, override, PID o abilita'; da quel punto il buffer e' fisso per tutta la lotta. **Nessuna garanzia di alternanza**:
incontri consecutivi, ritentativi e riavvii a freddo possono dare la stessa squadra o l'altra.

## Le quattro squadre

La squadra B si ottiene applicando le sue trasformazioni alla A. Nomi come nel gioco (EN / IT). I livelli base sono quelli
nativi (con Plus il livello e' poi adattato dal gancio livelli esistente, invariato). Gli assi restano Pidgeot (Valerio, slot 6)
e Scizor (Raffaello, slot 2) a Lv 72.

### Valerio / Falkner (712)

#### baseline
| # | Species EN / IT | Lv | Item EN / IT | Moves EN | Moves IT |
|--:|---|--:|---|---|---|
| 1 | Fearow / FEAROW | 68 | - / - | Roost, Drill Peck, Tailwind, Megahorn | Trespolo, Perforbecco, Ventoincoda, Megacorno |
| 2 | Pelipper / PELIPPER | 64 | - / - | Spit Up, Air Slash, Tailwind, Hydro Pump | Sfoghenergia, Eterelama, Ventoincoda, Idropompa |
| 3 | Swellow / SWELLOW | 68 | Flame Orb / Fiammosfera | Endeavor, Aerial Ace, Agility, Air Slash | Rimonta, Aeroassalto, Agilità, Eterelama |
| 4 | Noctowl / NOCTOWL | 66 | - / - | Psycho Shift, Roost, Dream Eater, Nasty Plot | Psicotrasfer, Trespolo, Mangiasogni, Congiura |
| 5 | Staraptor / STARAPTOR | 70 | - / - | Close Combat, Agility, Brave Bird, Double-Edge | Zuffa, Agilità, Baldeali, Sdoppiatore |
| 6 | Pidgeot / PIDGEOT | 72 | Sitrus Berry / Baccacedro | Tailwind, Mirror Move, Air Slash, Brave Bird | Ventoincoda, Speculmossa, Eterelama, Baldeali |
#### A
| # | Species EN / IT | Lv | Item EN / IT | Moves EN | Moves IT |
|--:|---|--:|---|---|---|
| 1 | Fearow / FEAROW | 68 | - / - | Roost, Drill Peck, Tailwind, Megahorn | Trespolo, Perforbecco, Ventoincoda, Megacorno |
| 2 | Pelipper / PELIPPER | 64 | - / - | Ice Beam, Air Slash, Tailwind, Hydro Pump | Geloraggio, Eterelama, Ventoincoda, Idropompa |
| 3 | Swellow / SWELLOW | 68 | Flame Orb / Fiammosfera | Endeavor, Aerial Ace, Agility, Facade | Rimonta, Aeroassalto, Agilità, Facciata |
| 4 | Noctowl / NOCTOWL | 66 | - / - | Psychic, Roost, Air Slash, Nasty Plot | Psichico, Trespolo, Eterelama, Congiura |
| 5 | Staraptor / STARAPTOR | 70 | - / - | Close Combat, Agility, Brave Bird, Double-Edge | Zuffa, Agilità, Baldeali, Sdoppiatore |
| 6 | Pidgeot / PIDGEOT | 72 | Sitrus Berry / Baccacedro | Tailwind, Roost, Air Slash, Brave Bird | Ventoincoda, Trespolo, Eterelama, Baldeali |
#### B
| # | Species EN / IT | Lv | Item EN / IT | Moves EN | Moves IT |
|--:|---|--:|---|---|---|
| 1 | Crobat / CROBAT | 68 | - / - | Roost, Brave Bird, U-turn, Cross Poison | Trespolo, Baldeali, Retromarcia, Velenocroce |
| 2 | Pelipper / PELIPPER | 64 | - / - | Ice Beam, Air Slash, Tailwind, Hydro Pump | Geloraggio, Eterelama, Ventoincoda, Idropompa |
| 3 | Swellow / SWELLOW | 68 | Flame Orb / Fiammosfera | Endeavor, Aerial Ace, Agility, Facade | Rimonta, Aeroassalto, Agilità, Facciata |
| 4 | Noctowl / NOCTOWL | 66 | - / - | Psychic, Roost, Air Slash, Nasty Plot | Psichico, Trespolo, Eterelama, Congiura |
| 5 | Staraptor / STARAPTOR | 70 | - / - | Close Combat, U-turn, Brave Bird, Double-Edge | Zuffa, Retromarcia, Baldeali, Sdoppiatore |
| 6 | Pidgeot / PIDGEOT | 72 | Sitrus Berry / Baccacedro | Tailwind, Roost, Air Slash, Brave Bird | Ventoincoda, Trespolo, Eterelama, Baldeali |
### Raffaello / Bugsy (713)

#### baseline
| # | Species EN / IT | Lv | Item EN / IT | Moves EN | Moves IT |
|--:|---|--:|---|---|---|
| 1 | Yanmega / YANMEGA | 70 | - / - | Screech, U-turn, Air Slash, Bug Buzz | Stridio, Retromarcia, Eterelama, Ronzio |
| 2 | Scizor / SCIZOR | 72 | Sitrus Berry / Baccacedro | Iron Head, Swords Dance, Feint, Night Slash | Metaltestata, Danzaspada, Fintoattacco, Nottesferza |
| 3 | Heracross / HERACROSS | 68 | Damp Rock / Rocciaumida | Reversal, Feint, Megahorn, Horn Drill | Contropiede, Fintoattacco, Megacorno, Perforcorno |
| 4 | Masquerain / MASQUERAIN | 70 | - / - | Air Slash, Whirlwind, Bug Buzz, Hydro Pump | Eterelama, Turbine, Ronzio, Idropompa |
| 5 | Vespiquen / VESPIQUEN | 68 | - / - | Toxic, Defend Order, Destiny Bond, Air Slash | Tossina, Comandoscudo, Destinobbl., Eterelama |
| 6 | Pinsir / PINSIR | 69 | - / - | Guillotine, Superpower, Megahorn, Close Combat | Ghigliottina, Troppoforte, Megacorno, Zuffa |
#### A
| # | Species EN / IT | Lv | Item EN / IT | Moves EN | Moves IT |
|--:|---|--:|---|---|---|
| 1 | Yanmega / YANMEGA | 70 | - / - | Protect, U-turn, Air Slash, Bug Buzz | Protezione, Retromarcia, Eterelama, Ronzio |
| 2 | Scizor / SCIZOR | 72 | Sitrus Berry / Baccacedro | Iron Head, Swords Dance, Bug Bite, Night Slash | Metaltestata, Danzaspada, Coleomorso, Nottesferza |
| 3 | Heracross / HERACROSS | 68 | - / - | Reversal, Rock Slide, Megahorn, Close Combat | Contropiede, Frana, Megacorno, Zuffa |
| 4 | Masquerain / MASQUERAIN | 70 | - / - | Air Slash, Whirlwind, Bug Buzz, Hydro Pump | Eterelama, Turbine, Ronzio, Idropompa |
| 5 | Vespiquen / VESPIQUEN | 68 | - / - | Toxic, Defend Order, Heal Order, Air Slash | Tossina, Comandoscudo, Comandocura, Eterelama |
| 6 | Pinsir / PINSIR | 69 | - / - | X-Scissor, Superpower, Megahorn, Close Combat | Forbice X, Troppoforte, Megacorno, Zuffa |
#### B
| # | Species EN / IT | Lv | Item EN / IT | Moves EN | Moves IT |
|--:|---|--:|---|---|---|
| 1 | Yanmega / YANMEGA | 70 | - / - | Psychic, U-turn, Air Slash, Bug Buzz | Psichico, Retromarcia, Eterelama, Ronzio |
| 2 | Scizor / SCIZOR | 72 | Sitrus Berry / Baccacedro | Iron Head, Swords Dance, Bug Bite, Night Slash | Metaltestata, Danzaspada, Coleomorso, Nottesferza |
| 3 | Heracross / HERACROSS | 68 | - / - | Reversal, Rock Slide, Megahorn, Close Combat | Contropiede, Frana, Megacorno, Zuffa |
| 4 | Forretress / FORRETRESS | 70 | - / - | Spikes, Rapid Spin, Gyro Ball, Earthquake | Punte, Rapigiro, Vortexpalla, Terremoto |
| 5 | Vespiquen / VESPIQUEN | 68 | - / - | Toxic, Defend Order, Heal Order, Air Slash | Tossina, Comandoscudo, Comandocura, Eterelama |
| 6 | Pinsir / PINSIR | 69 | - / - | X-Scissor, Superpower, Megahorn, Close Combat | Forbice X, Troppoforte, Megacorno, Zuffa |

## Motivazioni

- A rimuove combinazioni senza senso della squadra nativa: Spit Up senza Stockpile, Mirror Move in lotta singola, Psycho Shift e
  Dream Eater senza supporto, due mosse OHKO (Guillotine, Horn Drill) e Feint inutile. Facade e Nasty Plot sono pressione
  volutamente nuova, con strumenti e mosse gia' presenti.
- B scambia: per Valerio il Fearow con un Crobat (pivot Veleno/Volante con U-turn) e Agility con U-turn su Staraptor; per Raffaello
  Protect con Psychic su Yanmega e Masquerain (Coleottero/Acqua in questa hack, non Coleottero/Volante) con un Forretress
  (Coleottero/Acciaio) che porta Spikes, Rapid Spin, Gyro Ball e Earthquake.
- Nessun aumento uniforme di EV/IV, nessun effetto nuovo: tutti gli ID mossa sono 1..467 e i loro effetti sono quelli
  dell'archivio `a/0/1/1` letto (Facade 263 effetto 169, Psychic 94 effetto 72, Protect 182 effetto 111, Bug Bite 450 effetto 224,
  Rock Slide 157 effetto 31, Heal Order 456 effetto 32, X-Scissor 404 effetto 0, Spikes 191 effetto 112, Rapid Spin 229 effetto 129,
  Gyro Ball 360 effetto 219, Earthquake 89 effetto 147, U-turn 369 effetto 228, Cross Poison 440 effetto 209, Ice Beam 58 effetto 5).
  Gli ID con significato riutilizzato in questa hack (6, 27, 134, 140, 160, 169, 176) non compaiono in nessuna delle squadre e un
  test lo asserisce. Feint (364) e Toxic (92) hanno dati diversi dal gioco originale (potenza/precisione) ma restano come sono.
- Legalita': ogni coppia (specie, mossa) nuova e' apprendibile per livello, MT o MN secondo i dati correnti (learnset `a/0/3/3`,
  compatibilita' MT in `a/0/0/2`, tabella MT a `0x021000CC`); le fonti esatte sono nel JSON e un cambio dei dati fa rifiutare la
  configurazione. Tipi letti: Crobat Veleno/Volante, Forretress Coleottero/Acciaio, Masquerain Coleottero/Acqua.

## Rischi dichiarati

- **Facade con Fiammosfera** (Swellow, Guts): in A e B Swellow ha Facade con lo strumento gia' presente; e' la minaccia fisica
  piu' alta aggiunta (da misurare, non provata).
- **Congiura (Nasty Plot) con Psychic e Eterelama** su Noctowl: setup + due attacchi speciali affidabili.
- **Trappola di Punte** (Forretress, B di Raffaello) e Rapid Spin: la pressione dipende da come l'IA nativa usa questi effetti;
  non si promette che non ripeta setup o recupero (Heal Order, Roost, Swords Dance): e' un rischio di ciclo da misurare.
- Frana, Forbice X e Close Combat ampliano la copertura di Raffaello; Forretress aggiunge una nuova resistenza Acciaio nella squadra B.
- Niente di cio' e' provato: non e' stato eseguito nessun confronto di bilanciamento. Vittoria del boss o danni maggiori non
  dimostrerebbero IA migliore.

## Come prepararsi (risorse verificate nei dati correnti)

Fonti: le voci della Guida 1.3.1 generate dall'audit statico delle acquisizioni (script, palle strumento, 30 inventari negozio);
non e' una partita completa in emulatore. Le rivincite richiedono 16 badge (gate nativo); non e' stato verificato una per una che
ogni zona sia gia' visitabile a quel punto, ne' sono state eseguite le acquisizioni.

- **Valerio (volanti: debolezza a Elettro, Ghiaccio, Roccia)** - almeno due vie reali:
  1. MT80 Frana: palla strumento alle Rovine d'Alfa, seconda stanza della sala a sud-est (EN: Ruins of Alph southeast chamber, second room).
  2. MT13 Geloraggio: Via Gelata P1S o Isole Spumarine P4S, oppure 4000 gettoni al Casino' di Fiordoropoli (EN: Ice Path B1F, Seafoam Islands B4F, Goldenrod Game Corner).
  3. MT24 Fulmine: riva accanto al Faro di Olivinopoli o Grotta Celeste 1F, oppure 4000 gettoni (EN: shore beside Olivine Lighthouse, Cerulean Cave 2F).
  4. MT12 Provocazione (blocca Congiura, Trespolo, Ventoincoda, Agilita'): acquistabile al Centro Commerciale di Azzurropoli, 2º piano (EN: Celadon Department Store 3F).
  **Variante peggiore (B, con Crobat e U-turn)**: le vie 1-3 colpiscono tutti i volanti compreso Crobat; la 4 limita il setup di Noctowl e il recupero.
- **Raffaello (coleotteri: debolezza a Fuoco, Volante, Roccia; Scizor e Forretress sono Coleottero/Acciaio, quindi la Roccia per loro e'
  NEUTRA: x2 del Coleottero per x0,5 dell'Acciaio)** - vie reali con vantaggio di tipo, per specie:
  1. **Fuoco, 4x su Scizor e Forretress, 2x su Heracross, Pinsir, Yanmega e Vespiquen** - tre fonti distinte (Guida 1.3.1; per la MT38 la
     tabella negozio 7 della ROM, EN e IT, contiene l'oggetto 365, riletta in questa revisione):
     - MT35 Lanciafiamme: Sentiero Din Don o Percorso 28, oppure 4000 gettoni al Casino' di Fiordoropoli (EN: Bellchime Trail, Route 28, Goldenrod Game Corner).
     - MT38 Fuocobomba: in vendita al Centro Commerciale di Fiordoropoli, 4º piano (EN: Goldenrod Department Store 5F), accanto alla MT17 Protezione.
     - MT50 Vampata: palla strumento nella Torre Bruciata P1S (EN: Burned Tower B1F).
  2. **Roccia, 4x su Yanmega e Vespiquen, 2x su Pinsir (nessun vantaggio su Scizor, Forretress, Heracross)**: MT80 Frana (Rovine d'Alfa, seconda stanza della
     sala a sud-est; EN: Ruins of Alph southeast chamber, second room) e MT39 Rocciotomba (Grotta di mezzo P1S; EN: Union Cave B1F).
  3. **MT12 Provocazione** (come sopra, Centro Commerciale di Azzurropoli): impedisce Punte, Danzaspada, Tossina, Comandocura e Comandoscudo.
  **Variante peggiore (B, con Forretress)**: contro Forretress e Scizor valgono la via 1 (almeno due fonti indipendenti: MT35 e MT38, piu' MT50) e,
  per limitarne Punte e il recupero, la via 3; la Roccia (via 2) serve invece per Yanmega e Vespiquen. Le palle strumento (MT39, MT50, MT80, MT35 sul campo)
  sono fonti statiche della Guida, non verificate in partita.
- Per non dipendere da un solo oggetto nessuna delle due squadre richiede una specie rara o un contatore nascosto; la Guida non deve
  promettere che una singola preparazione basti.

## Meccanismo nativo e prove

- Seam: `BL 0x020735E8` (lettore `TrainerData_ReadTrPoke`) a `0x0207363A` dentro `CreateNPCTrainerParty` (`0x02073604`), ripresa a
  `0x0207363E`. Il wrapper salva r0-r2, r4-r7 e LR (8 parole, SP a 8 byte), chiama il lettore nativo **una volta**, poi (solo se tutte
  le guardie concordano) applica il core e restituisce il risultato del lettore. I quattro ganci livelli (`0x02073718`, `0x02073802`,
  `0x0207390C`, `0x02073A0C`) restano intatti.
- Guardie: byte Plus `0x023D8700` (letto dalla funzione livelli Plus a `0x023D8134`), indice nemico in una whitelist esatta,
  `BattleSetup.battleType` in una whitelist esatta di valori, coerenza di buffer/ID con il frame dell'host, formato 3 con 6
  membri, buffer uguale byte per byte alla squadra nativa letta. **Il contesto reale (battleType, indice) NON e' ancora provato a
  runtime**: il wrapper e' installato **inerte** (byte `active` = 0 nella config, delega pura) finche' Codex non fornisce
  `context_proof` di una cattura reale (campi `capture_file`, `capture_rom_sha256`, `build_id`, con `capture_rom_sha256` uguale all'argomento esplicito `candidate_sha256` = la ROM candidata inerte su cui e' stata fatta la cattura); una prova sintetica del banco e' rifiutata salvo
  argomento riservato ai test e la ricevuta la marca `synthetic`; i valori di riferimento (1, 1) non sono prove.
- Memoria misurata: codice 1216 byte, config 716 byte nel modulo, stack del modulo 184 byte sotto l'SP dell'host (200 con il frame dello stub);
  nessuna allocazione, nessuno stato persistente. **Il modulo non e' residente**: e' l'overlay segnaposto 126 (file da 20 byte mai caricato dal gioco),
  riscritto dall'installatore (riga y9: finestra `0x0226B000`, non compresso; immagine 2048 B accodata alla cartuccia come file 126) e caricato per
  la durata di una chiamata del seam da uno **stub residente di 60 byte** (`stub.S`, slot `c8.module-stubs` della mappa di riserva, base solo da una ricevuta
  di `sgp131.reserve.allocate` ricontrollata contro la politica in vigore). Lo stub chiama `HandleLoadOverlay(126)`, esegue il modulo, e chiama
  `UnloadOverlayByID(126)` su ogni percorso (successo, modulo inerte, finestra occupata, caricamento fallito); se il caricamento e' rifiutato o fallisce
  gira il lettore nativo (nessuna variante). La finestra tocca solo l'overlay 12 (battaglia). Lo stub non scrive mai r4-r7 (r4 = BattleSetup per il modulo).
  Costo: **ogni** costruzione di squadra di allenatore carica e scarica l'overlay (un filtro sull'id nello stub non entra nei 64 B): da misurare su dispositivo.
  Non misurato: lo stack e il tempo reali del livello file system (`FS_LoadOverlayImage`), sostituito nel banco.
- Prove ARM (Unicorn sui byte ARM9 reali EN/IT del candidato V4, nessuna ROM scritta): il costruttore reale
  (CreateMon, cifratura, statistiche, LCRNG, ganci livelli) gira con soli stub dell'ambiente (allocatore, lettore di archivi, nome
  della specie, handle NARC); le sei creature costruite (specie/forma, PID, sesso, abilita', natura, IV/EV, livello, mosse/PP,
  strumento, capsule, checksum, struttura intera) coincidono con quelle del costruttore nativo alimentato dalla squadra scelta, per
  EN/IT x Normale/Plus x A/B; seme globale, sequenze alloc/free, SP, registri e RAM coincidono; contesti non ordinari e
  wrapper inerte coincidono col nativo; i sette allenatori della 1.3 sono invariati. Il test non e' una prova Android.
- Indipendenza dall'ordine: viene letto solo il record di ciascuna mossa usata (mai il membro 261 di `a/0/1/1`, riscritto da
  `modern_moves`), quindi l'installazione non dipende dall'ordine rispetto a Fuocofatuo.

## Comandi di prova

    PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_rematches -v                        # host, 26 test
    (cd source/features/rematch-variants/test && ../../../../.venv/bin/python -m unittest test_variants -v)   # core C, 6 test
    PYTHONPATH=source SGP_REMATCH_REQUIRE_INPUTS=1 .venv/bin/python -m unittest sgp131.test_rematches_rom -v   # ROM + Unicorn, 40 test
    (cd source/features/rematch-variants/test && SGP_REMATCH_REQUIRE_INPUTS=1 ../../../../.venv/bin/python -m unittest test_hooks -v)  # 6 test

Regressione dei sette allenatori 1.3 con le basi 1.2.5 reali (senza la variabile il test salta):
`SGP13_BASE_DIR=$PWD/local/roms/1.2.5 PYTHONPATH=source .venv/bin/python -B -m unittest sgp13.test_teams_arm -v`.

I test ROM leggono i candidati V4 EN/IT (sha256 verificati) solo in memoria; `SGP_REMATCH_REQUIRE_INPUTS=1` fa fallire invece di
saltare. lo slot di riserva `c8.module-stubs` (`0x023D59E0`, 192 B a zero nella V4 e nell'uscita UI) e' concesso nei test da una **politica di riserva di prova
dichiarata** (`rom_fixture.declared_reserve`: versione e digest propri, rifiutata dalla politica vera, slot copiato dalla mappa); la politica vera non
puo' concederlo (genitore condizionale). `test_rematches_rom.RealUiComposition` installa il modulo sull'uscita della UI vera.

## Limiti

Niente alternanza garantita; nessun adattamento alla squadra del giocatore; la prova di bilanciamento (18 lotte per allenatore e
lingua piu' baseline) e gli accessi naturali telefono/Dojo non sono stati eseguiti; vedi `local/notes/cc-modern-mechanics/c8/R/ANDROID-SCENARIOS.md`.

## Testo per la Guida (proposta, da integrare da Codex)

- EN: `With Plus on, Falkner's and Bugsy's rematches use one of two prepared teams, chosen at random each time. Normal is unchanged.`
- IT: `Con Plus attivo, le rivincite con Valerio e Raffaello usano una di due squadre preparate, scelta a caso ogni volta. In Normale non cambia nulla.`

## Correzioni post-review

- **I1** `validate_context_proof` rifiuta le prove con `synthetic_harness_only` salvo `allow_synthetic=True` (solo test); per una prova reale
  richiede `capture_file`, `capture_rom_sha256` (sha256, uguale a `candidate_sha256`) e `build_id`; la ricevuta registra `proof_origin` (`android`/`synthetic`),
  `proof_sha256`, `candidate_sha256`, `capture_rom_sha256`, `function_state` (`inert`/`active`, ricalcolato dal byte `active` installato) e `candidate_relation`;
  non scrive piu' stati di processo (il vecchio `context.status` e' stato rimosso). I test asseriscono `synthetic` e il rifiuto senza argomento.
- **I2** La via Roccia non e' un vantaggio contro Scizor e Forretress (neutra): riscritta sopra. La variante peggiore di Raffaello ha tre fonti Fuoco
  reali (MT35, MT38 acquistabile, MT50), verificate nella Guida e, per la MT38, nella tabella negozio 7. Nessuna modifica al set B.
- **M1** la quota config e' una costante di compilazione (`REMATCH_CONFIG_BYTES`, uguale all'allocazione) e limita il core a runtime.
- **M2** `test_hooks.AllTrainersSweep`: wrapper attivo contro nativo per un allenatore di ogni coppia (formato, membri) dell'archivio, Plus 0/1, due esiti del selettore, EN e IT: 0 differenze.
- **M3** indice nemico limitato a 0..3 (wrapper e configurazione); `DirectGate` prova anche gli indici 4, 7 e 8 nel frame.
- **M4** dell'archivio oggetti si pinnano i soli record 158, 273, 285 piu' il conteggio dei membri (non lo sha dell'intero `a/0/1/7`).
- **M5/M6** comando con `SGP13_BASE_DIR` e percorso esplicito degli scenari Android (sopra).
- **M7** il byte Plus e' 0/1 per contratto; il wrapper abilita solo `== 1` mentre la funzione livelli nativa tratta ogni valore non nullo come Plus. Il byte non
  assume altri valori; se lo facesse le rivincite resterebbero native mentre i livelli Plus si applicherebbero.

## Correzioni post-review K (stato congelato)

- **Dojo (B1).** La sequenza ereditata dello script 832 entra in 712/713 con `a4 = 1`: `SetupAndStartTrainerBattle` (V4 `0x02051370`, eseguita in Unicorn dai test)
  costruisce `battleType` 0x1 per il telefono (`a4 = 0`) e 0x801 (`BATTLE_TYPE_11` aggiunto) per la sequenza. La lista bianca installata e' ora
  {0x1, 0x801}, una voce per famiglia nel file di pin (`gate.context.families`); ogni altro valore (anche 0x800, 0x803, 0x13, 0x4B, 0x3...) resta nativo. La prova di
  contesto porta il campo `family` (non piu' `entry`) per ogni osservazione, con la coppia famiglia/valore esatta, per entrambi gli allenatori e entrambe le famiglie.
  La funzione e' fissata (184 byte, `setup`): se un altro stadio la cambia l'installazione e `verify` rifiutano. Il valore reale a runtime resta da catturare su Android.
- **verify** rifiuta per default le ricevute con prova sintetica (`require_measured=True`), richiede `capture_rom_sha256 == candidate_sha256` nelle ricevute attive
  e un'origine coerente. **Cancello finale obbligatorio del builder**: `rematches.candidate_gate(final_rom, receipt)`, cioe' lo sha256 della ROM finale con il byte di
  attivazione azzerato (`inert_view`, pura: cambia solo il byte `active` dentro il file dell'overlay 126, trovato dalla FAT) deve essere uguale a `candidate_sha256` della prova; senza
  questo cancello `candidate_relation: composed-candidate` e' un'etichetta, non un'attestazione.
- `clang` fissato (versione e hash del binario) come in `controls.py`.
- **Limiti**: il modulo cambia la riga y9 dell'overlay 126, la tabella dei file, la lunghezza della cartuccia e il CRC dell'header: i semi della UI (lunghezza, CRC y9) devono
  includerlo (come per ogni stadio che accoda un file, vedi INTEGRATION.md); `audit`-style controlli dei pin valgono PRIMA di `install`.
