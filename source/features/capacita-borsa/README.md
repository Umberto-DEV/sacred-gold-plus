# Capacità Borsa — 1.2.1

| Tasca | Prima | Adesso | Pagine da 6 |
|---|---:|---:|---:|
| Principale |165|252|42|
| Medicine |40|42|7|
| Poké Ball |24|30|5|
| MT/MN |101|102|17|
| Bacche |64|66|11|
| Messaggi |12|12|2|
| Strumenti lotta |30|30|5|
| Strumenti base |50|60|10|

Sono slot di oggetti distinti; i limiti quantità restano 999 (99 MT/MN).
La schermata campo alloca nomi e ID per 252 elementi. Il sesto elemento della
pagina 42 è selezionabile, utilizzabile, cestinabile e riempibile con le normali
funzioni di aggiunta. La vista lotta enumera tramite il getter esteso.

## Architettura

- `sorgenti/core.c`: rappresentazione 594 slot, import/export del layout nativo,
  sincronizzazione per-slot tra scritture dirette del menu e indirizzi cheat.
- `sorgenti/runtime.c`: instrada tutte le API Bag, inclusi oggetti privati di
  battaglia/scambio, registrazione e ordinamento. Non cambia `Save_Bag_sizeof`.
- `sorgenti/journal.c`: estensione 432 byte più 20 byte di metadati/checksum,
  due copie per ciascuna banca flash, associate alla generazione del save e
  alla CRC16 del blocco principale. Si prepara prima del commit nativo.
- ARM9 riservato `0x023DBF00–0x023DEB00`; stato a `0x023DD700` (4808 byte).

## L'estensione non impedisce mai il salvataggio nativo

**In lettura** ogni copia è classificata per conto suo; una copia inutilizzabile
viene ignorata e, se nessuna è utilizzabile, l'estensione è ASSENTE e il gioco
apre con i suoi 486 slot nativi. Settori con byte estranei — azzerati da un
convertitore, da un backup di flashcart o da un editor di salvataggi — sono un
caso normale e silenzioso. **Nessun percorso di caricamento apre la schermata
nativa di errore di lettura.** L'esito finisce in `stato_caricamento`
(`0x023DE9C0`, cioè `CapState + 0x12C0`); vince la prima riga che si applica:

| condizione | inventario | `stato_caricamento` | `owned` |
|---|---|---:|---:|
| la copia primaria corrisponde a questo salvataggio | 594 slot dalla primaria (lo specchio non viene letto) | 1 | 1 |
| lo specchio corrisponde a questo salvataggio | 594 slot dallo specchio | 2 | 1 |
| una copia non è leggibile dalla flash | 486 slot nativi | 5 | 0 |
| una copia è integra ma di un'altra generazione | 486 slot nativi | 3 | 1 |
| una copia ha il nostro magic ma è danneggiata | 486 slot nativi | 4 | 0 |
| una copia contiene byte che non sono nostri | 486 slot nativi | 6 | 0 |
| entrambe le copie cancellate (0xFF) | 486 slot nativi | 0 | 0 |

`rejected` (`CapState + 0x0C`) è **solo diagnostico**: «la flash non ha saputo
leggere la banca da cui abbiamo caricato». Non blocca nulla. In particolare non
vieta il salvataggio successivo: il caricamento legge la banca *attiva*, la
scrittura tocca quella *inattiva*, e se anche quella è illeggibile lo dicono le
due riletture di destinazione (`stato_scrittura` 4). Prima era un veto per tutta
la sessione, e un solo settore illeggibile faceva sparire in silenzio i 108 slot.

**In scrittura** ogni destinazione deve essere indipendentemente *rivendicabile*:
cancellata (0xFF), **uniforme** — 452 byte tutti uguali, come li lascia un
convertitore che azzera i settori inutilizzati o una card pulita con un motivo
fisso — oppure già nostra. Byte estranei *non uniformi* non vengono mai
sostituiti: nessuna delle due copie viene scritta e `stato_scrittura` resta 2.
`cap_record_create` bonifica prima di scrivere — uno slot dell'estensione con
quantità 0, con id 0 o id oltre 536, o con quantità oltre il limite della tasca
viene **svuotato dov'è** (`{0, 0}`), senza far scalare nulla: ogni altro slot
resta esattamente all'indice che aveva nella Borsa. Le stesse celle bonificate
vengono riscritte anche nella Borsa in RAM (solo le celle dell'estensione: le
486 native non si toccano mai), perché `{id, 0}` fa ancora dire «tasca non
vuota» e un id oltre 536 può ancora arrivare alla tabella oggetti dal menu.
Il compattamento nativo spinge in fondo alla tasca gli slot esauriti
*conservandone l'id*, quindi `{id, 0}` finisce dentro l'estensione col gioco
normale; scriverlo produceva un record che il nostro stesso validatore
rifiutava, e da lì in poi il salvataggio falliva per sempre. Per la stessa
ragione la rilettura dopo la scrittura è un **confronto byte per byte dei 452
byte scritti**, non una seconda validazione di dominio. `stato_scrittura`
(`CapState + 0x12C4`): 0 non tentata, 1 due copie scritte e verificate,
2 dati estranei in una destinazione (niente scritto), 3 niente di usabile
scritto, 4 flash illeggibile (saltata), 5 una sola copia verificata.

### Se `stato_scrittura` resta 2 (dati estranei)

È l'unico caso in cui l'estensione non viene più scritta finché la situazione
non cambia: i 108 slot extra spariscono a ogni ricaricamento e il gioco riparte
dai 486 nativi, senza alcun messaggio. La spia è `stato_scrittura` = 2
(`0x023DE9C4`). Il rimedio è manuale e vale su una **copia** del salvataggio:
riportare a `0xFF` i 452 byte all'inizio dei settori 48 e 112 (offset `0x30000`,
`0x30200`, `0x70000`, `0x70200` del `.sav` da 512 KB) con un editor esadecimale,
oppure azzerarli — un settore uniforme è rivendicabile. Al salvataggio successivo
l'estensione torna a essere scritta. Non toccare nient'altro del file.

**In ogni caso il salvataggio nativo parte e il suo risultato è quello
restituito.** Il gancio non risponde mai `WRITE_STATUS_TOTAL_FAIL` di propria
iniziativa: l'applicazione di salvataggio tattile scarta quel valore e scrive
comunque «ha salvato il gioco», quindi un rifiuto dell'estensione perdeva
l'intera sessione in silenzio. Il prezzo è limitato: se l'estensione non viene
scritta, il salvataggio nativo commissiona comunque una nuova generazione, il
vecchio record diventa «stale» e il caricamento successivo degrada ai 486 slot.
- Overlay15 mantiene lo stesso slot FAT e dimensione compressa, verificata
  con decompressione in luogo. Il reader separato non invoca l’applicatore.

Il [contratto salvataggi](../../docs/contracts.md#expanded-bag-121) specifica
recupero, errori e compatibilità. **Salvare su una ROM precedente rende gli
slot extra non recuperabili automaticamente al successivo caricamento 1.2.1.**
Conservare il save 1.2.1 prima di tornare indietro.

## Build e prove

```
python source/features/capacita-borsa/tools/compila.py --uscita source/sgp12/build/capacita_borsa
python -m unittest discover -s source/features/capacita-borsa/test -p test_core.py
python -m unittest discover -s source/features/capacita-borsa/test -p test_journal.py
python -m unittest discover -s source/features/capacita-borsa/test -p test_build.py
```

La classe B usa `SGP_CAPACITY_ROM` (ROM finale privata), `SGP_CAPACITY_BEFORE`
(stadio immediatamente precedente) e `SGP_CAPACITY_BUILD` (bundle compilato).
`test_arm.py` esegue su Unicorn le funzioni ARM native modificate: 252° slot,
copie private, read failure, 452 interruzioni di scrittura con riavvio e retry,
mirror corrotto/erased, rifiuto dati estranei in entrambe le destinazioni,
SRAM interamente a 0x00 e a 0xAA (caricata come assente, poi **rivendicata** dal
salvataggio successivo), la matrice completa primaria×specchio (36 combinazioni,
inclusa la lettura che fallisce), una lettura fallita al caricamento che **non**
impedisce la scrittura nella banca inattiva, una rilettura che restituisce un
record valido ma diverso da quello scritto, e il salvataggio con uno slot
`{id, 0}` o `id > 536` nell'estensione. Il banco verifica che la ROM in prova
contenga esattamente il `blob.bin` del bundle indicato.
`test_reader.py` muta ABI, codice, stato, dimensione Bag nativa e conteggi UI.

Collaudo locale melonDS: fixture sintetica con 251 elementi nella tasca
principale e un elemento finale; pagina 42 piena, rimozione via Cestina,
aggiunta nativa riprendendo un oggetto tenuto da un Pokémon, salvataggio vero
e riavvio freddo da SRAM con l’oggetto ancora nella sesta cella. La SRAM
riesportata dopo il caricamento coincide byte per byte con quella salvata.
ROM, SRAM, dump, savestate e catture restano privati.
