# Borsa in battaglia: riduzione della pausa di apertura

Con le animazioni opzionali attive, la costruzione della Borsa riusa i dati
degli oggetti già residenti nella battaglia. Nella fixture locale EN/IT la
pausa del task idle passa da **55 a 7 frame**, circa **0,9 → 0,12 secondi** a
60 Hz. Resta un breve caricamento: il risultato non è movimento continuo in
ogni fotogramma. Il blocco si applica dopo `anim2` e conserva la taratura v5c
a 0,375×.

## Causa verificata nel gioco

Il costruttore della lista `ov08_02223BF4` scorre gli slot delle otto tasche e
chiama `GetItemAttr(item, ITEMATTR_BATTLE_POCKET, heap)` per ciascuno slot
occupato. Questa funzione apre, legge e libera i dati NARC a ogni chiamata.
Le letture ripetute costituiscono la parte dominante della pausa osservata.

`BattleContext_New` ha già caricato `trainerAIData.itemData` con
`LoadAllItemData`; `BattleContext_Delete` la libera alla fine della battaglia.
Il menu Borsa usa lo stesso contesto ancora vivo. Il getter nativo
`GetItemVar` può leggere l'attributo da questa cache senza I/O.

Riferimento letto e confrontato con entrambe le immagini locali:
`pret/pokeheartgold`, commit `0985e8718df4f25e64d6507d89c0c97c0d288981`:

- [Creazione e distruzione del contesto](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/battle/battle_controller_player.c).
- [Getter degli attributi nella battaglia](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/battle/overlay_12_0224E4FC.c).
- [Lettura, mappatura e cache ItemData](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/item.c).

## Implementazione e contratti

[borsa_cache.c](sorgenti/borsa_cache.c) intercetta un solo BL a
`ov008:0x02223C30`. Lo shim acquisisce da `r4` il contesto del menu e conserva
il frame allineato a 8 byte. La chiamata mantiene oggetto, attributo e heap;
il caricamento originale di `r1=13` resta intatto.

Il percorso cache richiede il blocco opzioni valido, animazioni attive,
attributo 13 e tutti i puntatori del contesto presenti. Prima di chiamare
`GetItemIndexMapping` verifica `item <= ITEM_MAX` (536), perché il mapper
nativo non controlla quel limite. Confronta poi l'indice con la dimensione
effettiva caricata, ricavata dallo stesso mapper.

`LoadAllItemData` legge `mapping(ITEM_MAX) * sizeof(ItemData)` senza `+1`:
nella build verificata sono 513 record, indici 0–512. L'ultimo membro, 513,
non è residente e segue il getter originale. Cache assente, indice fuori
limite, opzione OFF o contesto non valido conservano anch'essi quel percorso.
Non vengono allocate altre cache né introdotti stati persistenti.

Il confronto dei dati locali verifica che l'attributo tasca dei 513 record
residenti coincide con quello letto dai rispettivi membri NARC. Il gancio
legge questo attributo; quantità, selezione e uso degli oggetti restano
gestiti dal codice nativo.

Il blocco ARM9 prenotato è di **256 byte a `0x023DBD00`**: codice 162 byte,
margine zero fino a `+0xF0`, canarino di 16 byte. Le impronte dei getter e
del costruttore della lista devono corrispondere prima dell'applicazione.
Il BL occupa quattro byte, di cui tre effettivamente diversi. La ricompressione
ov008 conserva dimensioni, FAT e contenuto esterno alla modifica.

[compila.py](tools/compila.py) produce solo codice compilato, canarino e
metadati, con impronte delle fonti e `SHA256SUMS`; l'oggetto intermedio resta
temporaneo. L'[applicatore](../../sgp12/blocchi/borsa_lotta.py) rifiuta bundle
obsoleti, preimmagini diverse o prenotazioni sovrapposte. Il
[rilettore](tools/rileggi.py) decodifica separatamente ARM9 e overlay e
verifica l'intero file, senza richiamare l'applicatore.

## Verifica del 14 settembre 2026

Fixture: Typhlosion contro Kakuna nel Parco Nazionale, salvataggio locale
copiato per ogni corsa. Quattro avvii freddi completano Borsa → tasca →
oggetto → ritorno alla lotta, quindi seconda apertura e ritorno, fino al
frame 5962.

| Prova | Risultato |
| --- | --- |
| EN e IT, animazioni ON | Prima e seconda apertura: plateau di 7 frame del task, 6 del contatore VBlank. Nel menu stabile entrambi gli offset Y assumono 7 valori distinti. |
| EN e IT, animazioni OFF | Prima e seconda apertura: 55 frame VBlank, coerenti con il fallback nativo. |
| Blob ARM, 10 test | Cinque contratti eseguiti sia sul blob spedito sia su quello appena compilato: argomenti, ritorno, stack, registri preservati, modalità Thumb e fallback. Con la stessa toolchain è richiesta anche identità binaria; compilatori diversi eseguono entrambi i blob. |
| Bundle, 6 test | Dimensioni, impronte, provenienza delle fonti, simboli e prenotazione; rifiuto delle alterazioni. |
| Rilettore, 6 test per lingua | Immagine valida accettata; mutanti di codice, margine, canarino, bersaglio, header e coda FAT respinti. Coda FAT di 344 byte intatta. |
| Build complete EN/IT | Ricostruzione byte-identica dalle basi 1.1; tutti i 15 rilettori verdi senza salti e controlli T1–T5 della riserva superati. |
| Controllo visivo IT | Catture di Borsa, tasca, Ultra Ball e ritorno alla lotta ispezionate: menu, sprite e riquadri integri. |

Queste sono prove in emulazione su una fixture, non un collaudo di tutte le
tasche e combinazioni d'inventario o su hardware. Le brevi pause residue e
il caricamento della Squadra restano fuori dalla correzione. Non vengono
aggiunte pose o immagini e il codice anim2 già approvato rimane identico.

## Riproduzione

Dalla radice del repository, con le dipendenze di `source/requirements.txt`
e clang con target ARMv5:

```sh
python3 source/features/borsa-lotta/tools/compila.py \
  --uscita source/sgp12/build/borsa_lotta
python3 -m unittest discover -s source/features/borsa-lotta/test -p test_build.py
python3 -m unittest discover -s source/features/borsa-lotta/test -p test_blob.py
SGP_ROM_BORSA_PRIMA=/percorso/finale-anim2-EN.nds \
SGP_ROM_BORSA_DOPO=/percorso/finale-borsa-EN.nds \
  python3 -m unittest discover -s source/features/borsa-lotta/test -p test_rilettore.py
```

Ripetere il rilettore con la coppia IT. Il processo Unicorn deve poter
eseguire codice JIT. Le suite senza ROM sono incluse in `source/run_tests.py`;
i mutanti su ROM sono riportati separatamente fra le prove di classe B.

La pipeline [sgp12](../../sgp12/README.md) applica e rilegge `borsa_lotta`
come quindicesimo stadio. La [guida di ricostruzione](../../docs/rebuilding-1.2.md)
descrive la verifica completa e la riproducibilità dell'immagine finale.
ROM, salvataggi e catture rimangono nel laboratorio locale ignorato da Git.
