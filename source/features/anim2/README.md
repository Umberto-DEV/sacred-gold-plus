# ANIM2 — moto continuo in lotta

`sgp.anim2` v5c anima gli sprite dei lottatori a **0,375×** della velocità
precedente, con interpolazione e ripresa graduale. Nome, livello, PS ed EXP
restano fermi. La politica dei nove siti conserva il task nei sette passaggi
dei menu e rispetta le fermate di distruzione e Safari. Il moto si sospende
durante mosse, ingresso, animazione nativa, ridimensionamento e scomparsa/KO.
Prima della cattura i task vengono fermati: Pokédex e soprannome possono
riutilizzare gli sprite senza ereditare il moto della lotta.

L'[audit del 14 settembre 2026](AUDIT-2026-09-14.md) documenta cause,
misure, regressioni e proposte qualitative. **Rimangono le pause globali di
caricamento dei menu**: conservare un task non fa avanzare uno scheduler fermo.

Il blocco occupa 2048 byte a `0x023DB500`. Codice, canarino, tabelle, parametri,
nove valori `lr`, stato e quattro slot hanno regioni separate. L'opzione usa il
campo `anim` del chunk condiviso e resta spenta per difetto.

Ricostruzione autonoma:

```sh
python3 source/features/anim2/tools/compila_anim2.py \
  --uscita /tmp/anim2-build --livello 5c --passo 3
```

Suite A, senza ROM: `test_metadata.py`. Suite B, con ARM9/ov012 estratti:
`test_blob5.py` con `SGP_MODULI`; applicatore, rilettore e mutanti usano
`SGP_ROM_BASE` e `SGP_ROM_ANIM2`. I test Unicorn/headless JIT possono richiedere
esecuzione fuori sandbox su macOS.

`--passo 2`, `3`, `4` corrispondono a 0,25×, 0,375× e 0,5× per il ciclo
di oscillazione/deformazione. La posa B occasionale conserva il suo tempo
separato. I vecchi preset 5a/5b non vengono più generati: la loro estensione
della fermata può attraversare lottatori già distrutti.

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

Per ripetere l'osservazione di tasca e pannello oggetto, senza usarlo:

```sh
python3 source/features/anim2/tools/copioni.py borsa /tmp/borsa.script \
  --fotogrammi 300
```

## Copertura storica della versione 1.2.1

Le prove seguenti riguardano il pacchetto precedente. Non sostituiscono la
matrice di regressione della v5c nell'audit collegato sopra.

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
