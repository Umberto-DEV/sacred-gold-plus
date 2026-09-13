# Borsa al tetto

Questo modulo permette ai doni gratuiti e agli oggetti raccolti a terra di
proseguire quando lo slot della Borsa è già al tetto. La quantità che entra
viene aggiunta normalmente; l'eccedenza viene scartata e lo script mostra il
messaggio dedicato. Negozi, premi a pagamento, scambi e altri siti fuori dal
censimento restano sul comportamento originale.

I tetti sono 999 per le tasche impilabili e 99 per MT/MN. Posta e oggetti
chiave sono eccezioni esplicite e mantengono sempre il comportamento originale.
La tabella contiene 110 siti permissivi identificati dai byte finali degli
script; 106 chiavi restano invariate e quattro vengono rigenerate dopo
l'inversione di REWARD-01.

L'API pubblica è il blocco composto `source/sgp12/blocchi/borsa.py`:

```python
finale, rapporto = borsa.applica(rom, build_dir, lingua, manifest_path=None)
verdetto = borsa.rileggi(rom, finale, build_dir, lingua)
```

I quattro stadi sono `premi`, `testo199`, `appendici` e `arm9`. Il rilettore
espone un rapporto distinto per ciascuno e rende `esito_finale: ROSSO` se cade
anche una sola condizione o se il risultato differisce di un byte dalla
ricostruzione attesa. Gli strumenti singoli in `tools/` restano disponibili
per diagnosi; il costruttore usa l'API composta.

Serve un checkout di `pret/pokeheartgold` al commit
`0985e8718df4f25e64d6507d89c0c97c0d288981`, indicato con
`SGP_PRET_SOURCE`. Il modulo legge `charmap.txt` e il file tracciato
`tools/py_scripts/scrcmd.json`; non richiede ROM 1.03 né file sotto `local/`.

La build ARM si riproduce con:

```sh
python3 source/features/borsa/tools/compila_borsa.py --uscita DIR
python3 source/features/native-core/tools/compila_tutti.py --uscita DIR --solo borsa
```

La Classe B usa le basi private `base-1.1-{EN,IT}.nds` in `SGP_ROM_DIR` e
ricostruisce pubblicamente tutti gli stadi fino a Caramelle:

```sh
SGP_ROM_DIR=/percorso/rom SGP_PRET_SOURCE=/percorso/pokeheartgold \
python3 -m unittest discover -s source/features/borsa/test -v
SGP_ROM_DIR=/percorso/rom \
python3 source/features/borsa/tools/mutanti.py --uscita DIR/mutanti.json
```

Il banco Unicorn esegue 27 casi sul codice ARM e uccide 12 mutanti a un bit.
Le verifiche statiche e di contenitore coprono entrambe le lingue, le 110
chiavi, i quattro rilettori, l'idempotenza, la lunghezza invariata e ogni byte
fuori dalle regioni dichiarate. Il runtime su una raccolta di Percorso 29 è verificato in EN e IT con una
fixture controllata: a 999 Pozioni la quantità resta 999, la Ball scompare e
le due pagine dell'avviso nominano l'oggetto e spiegano lo scarto. A 998 la
quantità sale a 999 senza avviso di scarto. Sulle stesse fixture e sul codice
precedente, a 999 la raccolta resta bloccata e il flag non cambia.

Questa prova esercita il flusso condiviso delle Ball a terra; non è una prova
runtime di tutti i 110 siti né di ogni dono NPC, scambio o acquisto. Questi
percorsi sono coperti dalla classificazione, dai rilettori e dal banco ARM.
