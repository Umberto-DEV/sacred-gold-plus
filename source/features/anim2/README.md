# ANIM2 — moto continuo in lotta

`sgp.anim2` v5d anima gli sprite dei lottatori a **0,375×** della velocità
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
  --uscita /tmp/anim2-build --livello 5c --passo 3 --variante V1
```

Suite A, senza ROM: `test_metadata.py`. Suite B, con ARM9/ov012 estratti:
`test_blob5.py` con `SGP_MODULI`; applicatore, rilettore e mutanti usano
`SGP_ROM_BASE` e `SGP_ROM_ANIM2`. I test Unicorn/headless JIT possono richiedere
esecuzione fuori sandbox su macOS.

`--passo 2`, `3`, `4` corrispondono a 0,25×, 0,375× e 0,5× per il ciclo
di oscillazione/deformazione. La posa B occasionale conserva il suo tempo
separato, scelto con `--variante` (vedi sotto). I vecchi preset 5a/5b non
vengono più generati: la loro estensione della fermata può attraversare
lottatori già distrutti.

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

## v5d — accento di posa B (18 settembre 2026)

### Che cosa cambia

Il «battito di ciglia» della v5c diventa un **accento di posa**: lo sprite
resta nella posa B per un tempo che il gioco stesso usa per lo stesso
fotogramma, e ci entra nell'istante di quiete del respiro.

### Perché

Tre misure indipendenti, tutte nella riga 1 tick = 2 fotogrammi video
(30 Hz: `pret/src/main.c:109-125`, la misura runtime di
`10b-ANIMAZIONI-MISURA-P03.md:95-103` e la taratura dell'audit):

- la posa B della v5c durava **2–3 tick = 4–6 fotogrammi = 0,067–0,100 s**
  (rara 10–12 fotogrammi). Misurato sul banco headless su 9060 fotogrammi
  EN e IT: 42 e 43 intervalli per lottatore, sole quattro durate possibili
  {4, 6, 10, 12}, il caso da 67 ms è il 32 % dei battiti;
- il gioco, negli script `a/1/8/0`, tiene la posa B per una **mediana di 10
  chiamate = 0,333 s**, con il valore più frequente a 15 = 0,50 s
  (quartili 5/10/15). Typhlosion di dorso: 12 chiamate = 0,40 s; Kakuna di
  dorso 15 = 0,50 s; Togetic di dorso 9 = 0,30 s;
- la posa B **non è** un occhio che si chiude: per il 99,3–99,65 % delle
  viste è un cambio di posa intero (arti, ali, testa, sagoma). Su Typhlosion
  il passaggio cambia 1681 pixel, su Kakuna 381.

Un fotogramma pieno mostrato per 67 ms si legge come un difetto di resa, non
come un gesto. La causa non era un errore di logica: `blink_dur` è un tempo
assoluto in tick che non è mai stato riletto dopo il rallentamento a 0,375×.

### I quattro cambi nel codice

| | Cosa | Perché |
|---|---|---|
| **Sincronia col respiro** | l'accento parte solo nel tick in cui la fase è al massimo della tavola (`SGP_PICCO_IDX`, indici 4 e 5). Il conto alla rovescia di `blink_wait` non cambia: arrivato a zero la voce resta **armata** e attende il picco | la posa cambiava a caso rispetto al respiro (distribuzione compatibile con l'uniforme). Al picco la tavola è piatta (16, 16) e il cambio di posa non si somma allo spostamento verticale |
| **Posa interrotta = annullata** | quando un cancello si alza, `riarma()` azzera `blink_left` e sorteggia un'attesa piena | il residuo si congelava e la posa B ricompariva nel tick dopo la caduta del cancello: **un lampo fisso alla fine di ogni mossa**, misurato sul banco (posa troncata a 8 fotogrammi, `blink_left` congelato a 2, ripartenza a 4 fotogrammi) |
| **Prima attesa per lottatore** | `blink_wait` iniziale = `BLINK_MIN + (rng & MASK)` invece di `BLINK_MIN` nudo | quattro lottatori creati nello stesso tick facevano il primo accento all'unisono, al tick 71 esatto per tutti |
| **La voce ricorda il `BattleSystem`** | `slot.bs_visto` (+0x18); la voce si riazzera quando cambia | una seconda lotta che riusa gli stessi indirizzi ereditava indice, fase, inviluppo e seme della prima |

A questi si aggiunge, fuori dall'accento: **`sgp_pulisci` prima di entrambe le
uscite «opzione spenta»**. Spegnere l'opzione a lotta in corso lasciava
`affineW/H` (±6), `shadow.yOffset` e la posa impressi sullo sprite, perché il
task vanilla riscrive solo `yOffset`. A interruttore mai acceso non esiste
nessuna voce, quindi non viene scritto un byte: la byte-identità è preservata
e c'è un test che la misura contando le `Pokepic_SetAttr`.

### Il conto dei byte

Il blob resta a **1532 B su 1536**, gli stessi della v5c. Sono stati liberati
i sei campi di diagnostica che nessun test tracciato e nessuno strumento
della v5 leggeva — `blinks` (+0x14), `rari` (+0x18), `stop_visti` (+0x20),
`dentro` (+0x3C), `maxbatt` (+0x3D), `ultimo_sito` (+0x3E) — che valgono
**48 B**, non 52: misurati col mutante che li rimette tutti e sei (1580 B,
contro i 1532 B spediti). Gli offset **non** si spostano: i campi restano
come buchi riservati, così gli strumenti che leggono i primi 32 B dello
stato continuano a funzionare. I quattro lettori di `blinks`/`rari`
(`anim/tools/sonda_moto.py:108`, `anim/tools/misura_v4.py:117`,
`anim/tools/misura_anim.py:73`, `options/tools/misura_anim.py:73`) guardano
lo stato della **v4** a `0x023D8E40`, che non è toccato: `sonda_moto.py`
legge la RAM dal vivo, gli altri tre leggono le stesse colonne da un CSV
già esportato.

### Parametri e varianti

Tutti i tempi stanno in `par.bin`: cambiarli **non ricompila il codice**.
`--variante` sceglie la taratura dell'accento; tutto il resto è invariato.

| Variante | `blink_dur` | posa B comune | posa B rara (1 su 3) | attesa |
|---|---:|---|---|---|
| **V1** «nativa» (default) | 10 | 0,33–0,37 s | 0,50–0,53 s | 4,0–8,2 s |
| **V2** «leggibile» | 15 | 0,50–0,53 s | 0,67–0,70 s | 4,0–8,2 s |
| **V3** «lunga» | 30 | 1,00–1,03 s | 1,00–1,03 s | 4,0–8,2 s |

`blink_min 120`, `blink_mask 127` in tutte e tre. Il jitter di ±1 tick
(±33 ms) sulla durata è nella logica e non è disattivabile dai parametri.
Le attese fra inizi di accento stanno in **[240, 590] fotogrammi (4,0–8,2 s
nominali + al massimo un ciclo di respiro di 96 fotogrammi per aspettare il
picco)**: `blink_wait` sorteggia 120–247 tick (240–494 fotogrammi), poi la
voce resta armata fino al prossimo picco del respiro, che nel caso peggiore
arriva fino a un ciclo intero (96 fotogrammi) più tardi.

### Cancelli del compilatore (zero byte di ROM)

`compila_anim2.py` va in ROSSO, prima di compilare, su cinque configurazioni
che prima accettava in silenzio e che si rompevano a runtime:

| Cancello | Cosa impediva |
|---|---|
| `--blink-dur >= 1` | `blink_left = (u8)(0-1) = 255` → posa B di 8,5 s, una volta su due |
| `blink_min + blink_mask <= 255` | troncamento in u8: `--blink-min 200 --blink-mask 63` dà 263 → 7, cioè 0,23 s invece di 6,7–8,8 s |
| `blink_mask` = 2ⁿ−1 | è una maschera, non un modulo: `100` dà 36 valori sui 101 attesi, con buchi |
| `blink_dur + 1 + raro_piu <= 255` | troncamento della durata massima in `blink_left` |
| ogni `--fase` < 18 | con `--fase 200` l'indice esce dalla tavola e legge dentro lo stato e la voce 0 |

Un sesto cancello, `PICCO ROSSO`, verifica che il massimo di `tab_u` stia
ancora agli indici che il blob confronta: la sincronia col respiro è due
istruzioni e non può cercare il massimo da sé.

### Che cosa NON cambia

Respiro (periodo 96 fotogrammi, ±3 px, controfase, inviluppo), cancelli di
sospensione, politica dei nove siti, G3/G4, indirizzi del blocco, dimensione
e posizione dei primi 32 B dello stato, comportamento a opzione spenta.

## Copertura storica della versione 1.2.1

Le prove seguenti riguardano il pacchetto precedente. Non sostituiscono la
matrice di regressione della v5c/v5d nell'audit collegato sopra.

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
