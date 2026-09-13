# ANIM2 — moto continuo in lotta

`sgp.anim2` estende il moto procedurale v4 a tutti i lottatori e lo mantiene
nei menu di lotta. Tre cancelli sospendono ogni scrittura durante animazioni di
mossa, ingresso della specie e animazioni native del Pokepic. La politica dei
nove siti di fermata sopprime soltanto `IO-BARRA`, `BORSA` e `SQUADRA`; gli
altri siti fermano e puliscono tutti i lottatori.

Il blocco occupa 2048 byte a `0x023DB500`. Codice, canarino, tabelle, parametri,
nove valori `lr`, stato e quattro slot hanno regioni separate. L'opzione usa il
campo `anim` del chunk condiviso e resta spenta per difetto.

Ricostruzione autonoma:

```sh
python3 source/features/anim2/tools/compila_anim2.py \
  --uscita /tmp/anim2-build --livello 5b
```

Suite A, senza ROM: `test_metadata.py`. Suite B, con ARM9/ov012 estratti:
`test_blob5.py` con `SGP_MODULI`; applicatore, rilettore e mutanti usano
`SGP_ROM_BASE` e `SGP_ROM_ANIM2`. I test Unicorn/headless JIT possono richiedere
esecuzione fuori sandbox su macOS.

`tools/sonda_fasi.py` osserva avvii e fermate reali, distinguendo i nove siti
tramite `lr`; `tools/copioni.py` genera i copioni per il runtime pubblico in
`source/runtime/`. Entrambi accettano percorsi forniti dall'utente e non
richiedono cartelle private. Il prologo e i puntatori dei copioni corrispondono
alla fixture di collaudo nel Parco Nazionale: vanno adattati a un altro
salvataggio. Nessuna ROM o partita è inclusa.

Per osservare la build finale si usa `--politica nessuna`. Le altre politiche,
`--anima-avversario` e `--siti-finti` sono esperimenti di debug: alterano lo
stato in RAM e non dimostrano che una fase sia stata raggiunta normalmente.
Il codice di uscita del processo da solo non certifica la copertura: occorre
leggere eventi, contatori, siti mancanti e catture.

## Copertura misurata

- Menu comandi, Borsa, squadra e cambio Pokémon sulle build EN e IT; moto
  presente sui due lati. I caricamenti dei menu possono fermare il VBlank
  dell'intero gioco: il moto riprende quando riparte il ciclo di gioco.
- Sei script di animazione nativa, selezionati in RAM nella stessa mossa di
  prova: 3.120 catture ON/OFF identiche. Non sono sei mosse scelte dal menu.
- Venti avvii a freddo indipendenti dalla stessa fixture, su tredici specie
  del giocatore, con ritorno al campo e quattro slot vuoti alla fine di ogni
  lotta. Nickname e statistiche restano quelli della fixture.
- Ombra avversaria di Kakuna: bordi verticali invariati in nove catture per
  ciascuna di venti corse. La copertura estetica non comprende ogni specie.
- Ingresso nativo in lotta allenatore, doppia con quattro slot distinti e
  Safari; cattura riuscita, KO e fuga. Il Safari mantiene il moto disattivato
  secondo la regola nativa del gioco.
- Riepilogo e Pokédex EN/IT senza attività del task. Sala d'Onore EN fino al
  salvataggio e ai titoli: 13.572 righe di tracciato e 38 catture identiche
  al controllo precedente ad ANIM2, con opzione e contatori a zero.

Queste sono prove in emulazione con fixture locali; non equivalgono a una
partita completa o a un collaudo su hardware.
