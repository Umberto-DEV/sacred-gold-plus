# Pilota 1.05 — EV/IV nel riepilogo

**Ricerca locale del 7 settembre 2026, separata dalla 1.04.** Il codice aggiunge un lettore nativo nella pagina Dati del riepilogo: L mostra gli EV, R gli IV, Select ripristina i valori ordinari. Non richiede cheat e non scrive nuovi campi nel save. Il cambio pagina o Pokémon ripristina titolo e parametri coerenti.

Le prime prove EN/IT Plus hanno verificato valori, navigazione con pulsanti e touch, tasti prolungati, uscita/rientro, SAVE normale e cold boot. I risultati della revisione 4 (private lab record, not distributed) conservano questa prima prova. È un solo starter TEST con EV distinti: non equivale alla compatibilità con ogni Pokémon o partita. La revisione 5 ottimizza Select; le prove ampliate EN/IT (private lab record, not distributed) includono uno e tre slot, due Chikorita con dati distinti, un uovo sintetico e PS non pieni. Tutti i 708 byte della squadra a tre membri restano identici anche dopo SAVE/cold boot.

## Cosa è stato corretto nel pilota

La prima esecuzione ha mostrato titoli EV/IV tagliati. I testi sono stati abbreviati e verificati a video in entrambe le lingue. Il ritorno da un'altra pagina ripristinava i numeri ordinari ma conservava il titolo EV: un aggancio al ridisegno normale ora ripristina anche il titolo, compresi i cambi via touch. Le build precedenti restano nelle prove private.

La misura del codice reale (private lab record, not distributed) ha poi trovato un costo evitabile in Select: il primo disegno richiamava tutta la pagina, riformattando anche abilità e descrizioni. La revisione 5 ripristina soltanto sei valori e titolo, usando gli stessi dati e formattazione del gioco.

| Percorso EN Plus | Revisione 4 | Revisione 5 |
|---|---:|---:|
| Select, cicli ARM9 medi su 8 pressioni | 1295291,75 | 286318,375 |
| Allocazioni/liberazioni osservate per Select | 45 / 45 | 25 / 25 |
| Input senza nuovi tasti, cicli per chiamata | 270 | 269 |

La riduzione di Select è **77,9% nel percorso misurato**, senza cambiamenti alle regioni dei numeri e del titolo. Il controllo originale senza pilota richiede 224 cicli per chiamata inattiva: la revisione 5 aggiunge 45 cicli a quel percorso. EV e IV richiedono rispettivamente circa 237 mila e 273 mila cicli per pressione nei campioni. I contatori includono i sottoprogrammi e l'eventuale tempo d'interruzione, ma non il trasferimento VRAM pianificato successivo. Non sono FPS, tempi GUI o una misura Android.

## Struttura e confini

Il builder ammette solo i quattro hash Community 1 identificati. Controlla due prologhi ARM9, le sezioni autoload e la costante dell'arena ITCM prima delle modifiche. La revisione 5 ha un payload Thumb di 592 byte e riserva **608 byte**, alzando il limite inferiore ITCM; conserva DTCM, BSS e stack. Il tetto esplicito è 0x01FFA000. ARM9 viene ricompresso nel suo spazio originale e il contenitore conserva ARM7, overlay e file non selezionati. Nel NARC messaggi cambia soltanto il banco 302, con il titolo 109 e due nuove stringhe.

Il CRC della secure area viene aggiornato relativamente al valore originale, mantenendo identico il prefisso cifrato di 0x800 byte. La proprietà XOR è coperta da un caso sintetico con prefisso cifrato indipendente. Non si includono chiavi, BIOS o codice di cifratura proprietario; la riuscita del direct boot non certifica un avvio hardware completo.

Le fonti ABI sono [pret/pokeheartgold](https://github.com/pret/pokeheartgold/tree/0985e8718df4f25e64d6507d89c0c97c0d288981) e [hg-engine](https://github.com/BluRosie/hg-engine/tree/1febb90b856745f8648c8a4fa059e7499a3cca3f). Crediti ai loro autori per decompilazione, simboli e ricerca. I commenti di alcuni helper hg-engine riportano ancora indirizzi Platinum: sono stati confrontati con rom.ld, assembly HG e preimmagini effettive. Il payload è un'implementazione propria basata su queste interfacce, senza incorporare l'intero motore o asset esterni. Licenza del codice: GPL-3.0-or-later, come la [licenza del progetto](../../LICENSE); i diritti delle opere di riferimento rimangono ai rispettivi autori.

## Riprodurre

Usare una nuova cartella privata fuori da Git e dalla sincronizzazione. Le ROM complete, gli screenshot, i dump e i save generati rimangono locali. Requisiti: Python con ndspy/Pillow, Clang con target ARM e charmap pret alla revisione indicata; nessuna dipendenza viene installata dal builder.

**Interprete**: il `python3` di sistema non basta (mancano `ndspy`/`Pillow`/`capstone`). Usare il venv
del progetto: `python3 (vedi source/requirements.txt)` (Python 3.9.6, `ndspy 4.2.0`,
`Pillow`, `capstone`). Con il `python3` di sistema **tutte** le suite native falliscono all'import
con `ModuleNotFoundError: No module named 'ndspy'`. Le stesse suite richiedono anche un `clang` con
target ARM funzionante (verificato: Apple clang, `--target=armv5te-none-eabi`).

```sh
python3 -m unittest discover -s source/native-eviv -p 'test_*.py'
python3 source/native-eviv/build_test_rom.py \
  --rom /percorso/Community1-EN.nds \
  --charmap /percorso/pret/charmap.txt \
  --out /percorso/privato/nuova-build
python3 source/native-eviv/run_probe.py \
  --build /percorso/privato/nuova-build/build.json \
  --fixture /percorso/EV-distinct-TEST.sav \
  --harness /percorso/hg_runtime \
  --out /percorso/privato/nuova-prova
```

Il riproduttore controlla hash, checksum/dati del Pokémon, ritorno delle regioni grafiche, save e cold boot. Lascia la revisione visiva grezza `pending`; la verifica umana delle immagini viene aggiunta in un rapporto curato distinto. Nessuno stato attraversa revisioni ROM. Il [lettore TEST](inspect_test_mon.py) conserva la modalità originale a un membro; i test con più slot richiedono conteggio e indice espliciti.

Per i tre slot usare `run_party_probe.py` con gli stessi argomenti e la fixture SHA-256 `966338cfff49cd214479adce11f113df4085c357634b1febce1d89638e1ac583`. Il controllo iniziale confronta anche l'hash dei 708 byte preparati indipendentemente. In una prima lettura IT il core si era fermato durante la decifratura temporanea dell'uovo dentro GetBoxMonData: il checksum risultava corretto sul blocco già in chiaro, ma il flag non viene impostato da quella funzione. I successivi dump erano integri. Il riproduttore ora campiona nella schermata stabile prima di L/R e durante il cold reload; conserva il decoder rigoroso e il tentativo precedente, senza classificare il campionamento intermedio come corruzione del save.

## Riprodurre la misura

`prepare_profile.py --core /checkout/core-osservazione --out /privato/nuovo-profilo` richiede la revisione e i due ganci esatti del runner esistente, controllati tramite hash. Copia soltanto i file tracciati in una cartella nuova e non modifica il checkout originale. Configurare CMake dalla sottocartella `frontend/`, indicando `MELONDS_SOURCE` nella copia `core/` e `HG_BUILD_WAIT_LOOP_TEST=OFF`; costruire il target `hg_runtime`. È un frontend di osservazione distinto dai contributi melonDS.

`run_profile.py` accetta `--rom`, `--fixture`, `--harness`, `--harness-sha256` e `--out`. Richiede l'identità esplicita del binario di osservazione appena revisionato. Misura 600 frame DS senza input e otto pressioni per L/R/Select; controlla chiamate complete, identità degli input e integrità del Pokémon/SRAM. Il riproduttore pubblico è stato rieseguito: gli aggregati della revisione 5 coincidono esattamente con la prima misura.

Per ricostruire il confronto precedente, `build_test_rom.py --baseline-r4` usa il [sorgente storico](history/eviv-r4.c) e rifiuta un payload diverso dai 480 byte misurati. Il payload ricompilato e la ROM EN completa coincidono byte per byte con quelli della revisione 4. Il valore predefinito costruisce il pilota corrente. `profile_trace.h` e il suo test C++ vivono sul Mac; non vengono inseriti nella ROM.

## Seguito necessario

Il caso box EN/IT è passato con EV/IV, ripristino, uscita, SAVE e cold boot; i dati di tutti i box e della squadra rimasta sono invariati. Il [riproduttore](run_box_probe.py) usa la fixture da deposito normale SHA-256 `5208191f489232908c41d160c0782d945bbf0084897c0465d809b9a41d7527d7`. Il primo tentativo aveva omesso una chiusura del menu PC e non completava SAVE: conservato, poi corretto e rieseguito. Le prove EN/IT con due Chikorita distinti e un uovo sintetico hanno conservato tutti i 708 byte della squadra e superato il cold boot; non sono prove di ottenimento, scambio o schiusa. Poi guida riapribile e introduzione di qualità, coerenti soltanto con funzioni reali. Le varianti native Classic non sono ancora provate. Forme, altre specie, lingue aggiuntive, interazioni con altri codici e hardware restano da coprire. Il piano tecnico (private lab record, not distributed) mantiene aperte queste condizioni; non esiste una release 1.05 stabile.
