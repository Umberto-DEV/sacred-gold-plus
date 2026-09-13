# Gate heap nativo: lease da 22.528 byte

Prova locale del 7 settembre 2026, separata dal lettore EV/IV r5: **quattro fixture EN/IT squadra/box, dieci cicli ciascuna, PASS**. Non implementa la guida, un badge o un layout grafico. Il progetto da 44.928 byte resta respinto; il budget ridotto supera soltanto questo prerequisito. Risultati selezionati in [lease-verification.json](lease-verification.json), preimmagini in [lease-abi.json](lease-abi.json).

Per ciascuna fixture il gioco ha eseguito 10 allocazioni da `0x5800`, 10 seconde richieste dello stesso importo con ritorno NULL mentre il primo blocco era vivo, 10 rilasci corrispondenti e 20 cleanup senza blocco. Due verifiche complete del pattern su ogni blocco hanno controllato 112.640 parole, compresi gli estremi, senza errori. L’indirizzo restituito è allineato a 4 byte e interno ai limiti dell’heap corrente.

Dopo **ciascun** ciclo, liste free/used (indirizzi, firme, dimensioni e collegamenti), header heap, contatore `329`, callback, argomenti, pagina e finestre Summary sono identici. SRAM e dati Pokémon/squadra/box sono preservati. Il primo START mantenuto per 120 frame esegue un solo ciclo; L/R/Select, direzioni, A+START per il dettaglio mosse, B per ritornare e B+START per uscire mantengono i comportamenti originali senza eseguire cicli aggiuntivi.

## Ownership e ABI

[lease.c](lease.c) risolve heap19 da `sHeapInfo` e dall’indice dinamico corrente. Usa direttamente **ARM** `NNS_FndAllocFromExpHeapEx(0x020B53A0)` e `NNS_FndFreeToExpHeap(0x020B5530)`, protetti da `OS_DisableInterrupts`/`OS_RestoreInterrupts` come nel wrapper originale verificato. Il sorgente pret fissato e il disassemblato delle preimmagini EN/IT confermano il ramo NULL dell’allocatore originale, le liste e i limiti dell’heap. Nessuna sostituzione dell’algoritmo di allocazione.

Il lease possiede soltanto il puntatore raw restituito da NNS. Il rilascio lo azzera una volta sola e non agisce quando è NULL. Non passa blocchi raw o puntatori interni a Heap_Free/RemoveWindow e non modifica `numMemBlocks`. Le allocazioni originali del gioco conservano il proprio wrapper e la propria contabilità.

[lease_probe.c](lease_probe.c) è solo codice di prova. Include il helper nello stesso translation unit affinché il loader r5 invariato possa gestire esclusivamente `.text` e BL Thumb interne. Non usa `.bss`, `.data`, `.rodata` o relocation ABS32. Il wrapper mantiene il payload r5 byte-identico e vi passa il controllo quando START non è ammissibile; il gancio di ridisegno r5 resta intatto.

Il probe occupa **792 byte** a `0x01FF8880`; il suo codice termina a `0x01FF8B98`. Il builder estende esplicitamente l’autoload ITCM e alza arenaLow a `0x01FFA000`. L’intervallo `[0x01FF9F00,0x01FFA000)` è riservato e inizializzato a zero: i primi 64 byte contengono i marker. Questa memoria non è save padding, RAM scelta arbitrariamente o un indirizzo dinamico hardcoded. Il lease heap viene liberato alla fine di ogni invocazione; i marker di prova restano nella riserva ITCM fino al riavvio.

## Strumenti e riproduzione locale

- [build_lease_rom.py](build_lease_rom.py): accetta soltanto le basi complete Plus Community1 EN/IT, ricompone r5 con il builder originale e ne verifica l’hash completo, valida le preimmagini dei nuovi helper, compila e aggiunge il probe. Le basi Classic e ROM r5 già patchate non sono input ammessi. L'uscita e' una cartella nuova FUORI da questo checkout.
- [prepare_lease_observer.py](prepare_lease_observer.py): compila un frontend separato dalla sorgente storica fissata aggiungendo soltanto `dumpitcm`, copia in lettura dei 32 KiB fisici ARM9.ITCM. Collega le librerie storiche senza ricostruire/modificare il core. Sorgenti, comandi, input oggetto/libreria e binario sono legati da hash nel manifest privato.
- [run_lease_probe.py](run_lease_probe.py) e [lease_oracle.py](lease_oracle.py): avviano da save normali TEST, registrano input e output reali e confrontano heap, Summary, SRAM e schermate. Prima del runtime rifiutano manifest di sorgente, oggetto o ROM obsoleti; i dump ITCM confermano anche i byte effettivamente caricati di r5 e probe.

Esempio, usando Python con `ndspy` e Pillow già presenti nel laboratorio:

```sh
lab/python3 (vedi source/requirements.txt) rom-tools/native-guide/prepare_lease_observer.py <scratch>
lab/python3 (vedi source/requirements.txt) rom-tools/native-guide/build_lease_rom.py --rom /percorso/base-Plus-EN.nds --charmap /percorso/pret-fissato/charmap.txt --out <scratch>
lab/python3 (vedi source/requirements.txt) rom-tools/native-guide/run_lease_probe.py --rom '<scratch> Lease TEST EN.nds' --fixture /percorso/EV-distinct-TEST.sav --observer <scratch> --out <scratch> --kind party --rom-sha HASH_INTERO_DAL_BUILD
lab/python3 (vedi source/requirements.txt) -m unittest discover -s rom-tools/native-guide -p 'test_lease_*.py'
```

Per il controllo RED, `--red` accetta l’hash esatto della r5 passata e cerca lo stesso risultato runtime: sulle quattro fixture fallisce con `Missing game-executed lease result`. Le fixture locali identificate sono necessarie per `run_lease_probe.py`/`lease_oracle.py` (corse a runtime); niente di tutto questo è incorporato nel gate. Nessuna ROM, save, dump o schermata è incorporata nei file del gate.

**Aggiornamento 12/09/2026** (`private development notes (ex 01-AUDIT-1.1.md)`, §I4/R4): i test statici di `test_lease_builder.py`, `test_summary_builder.py` e `test_lease_provenance.py` non fanno più riferimento a ROM lasciate da corse precedenti in una directory temporanea (percorsi effimeri, persi a ogni riavvio). `test_fixtures.py` in questa cartella costruisce da solo, a ogni corsa, la r5 EV/IV pilota e la ROM lease completa da una ROM 1.04 riconosciuta e dal charmap pret già presenti in questo checkout, sotto una cartella nuova nella directory temporanea di sistema (fuori dal checkout, come richiede `build_lease_rom.build()`), e la cancella a fine modulo. Se quegli input non sono presenti localmente, i test si saltano con un motivo esplicito invece di fallire.

## Verifiche e limiti

Sei test mirati verificano base sconosciuta, directory esistente, preimmagine del gancio errata, dimensione ITCM errata, sovrapposizione codice/marker e manifest di sorgente obsoleto. RED iniziale: cinque assertion sul composer ancora assente, più il RED reale sulle quattro r5; il controllo anti-stale ha un proprio RED/GREEN. I 39 file storici `native-eviv`/runtime controllati hanno mantenuto gli hash iniziali.

Il primo tentativo di composizione sul contenitore r5 già compresso è stato respinto dal limite originale ARM9. La composizione corretta usa il contenitore base esatto e aggiunge il solo bank messaggi r5. Il primo controllo roundtrip statico ha inoltre respinto i tre campi di metadati che `ndspy.save` riscrive: ora sono calcolati e confrontati esattamente (inizio/fine tabella autoload e fine dati compressi), senza ignorare un’area generica. I tentativi falliti restano privati.

La prova usa core melonDS `906e9ebb…`, interprete, renderer software 1×, RTC fisso, FreeBIOS e nessun cheat. Non è GUI, Android, Thor, misura prestazioni o garanzia su tutti i chiamanti Summary. L’uguaglianza grafica include tutto lo schermo inferiore, righe numeriche e titolo superiore; sprite e indicatore animati superiori sono esclusi dal confronto pixel. Nessuna prova SAVE/cold-reload aggiuntiva, font/layout ridotto, VRAM, badge o Nuova partita: questi restano gate successivi della guida.
