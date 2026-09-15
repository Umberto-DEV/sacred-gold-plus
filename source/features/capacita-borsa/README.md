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
- ARM9 riservato `0x023DBF00–0x023DEB00`; stato a `0x023DD700`.
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
mirror corrotto/erased, rifiuto dati estranei in entrambe le destinazioni.
`test_reader.py` muta ABI, codice, stato, dimensione Bag nativa e conteggi UI.

Collaudo locale melonDS: fixture sintetica con 251 elementi nella tasca
principale e un elemento finale; pagina 42 piena, rimozione via Cestina,
aggiunta nativa riprendendo un oggetto tenuto da un Pokémon, salvataggio vero
e riavvio freddo da SRAM con l’oggetto ancora nella sesta cella. La SRAM
riesportata dopo il caricamento coincide byte per byte con quella salvata.
ROM, SRAM, dump, savestate e catture restano privati.
