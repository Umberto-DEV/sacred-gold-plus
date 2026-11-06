# Comandi visibili nel riepilogo 1.3.1

Unità 1 del piano interno: la legenda
`L:EV SELECT:Stat. R:IV` nelle viste Statistiche, EV e IV del riepilogo. Stato:
**sorgenti e prove host/ARM complete, hook inattivo finché non arrivano le misure
runtime di finestre e tile, nessun collaudo Android**. Nessun campo di salvataggio,
nessun nuovo ID, nessuna rimappatura dei tasti.

## Scelte e motivi

- **Il lettore installato non si tocca.** La V4 contiene un lettore EV/IV in ITCM
  (payload `0x01FF8620`, 592 byte; lettore `0x01FF8658`, 448 byte) che legge i
  **tasti fisici** (`gSystem.newKeysRaw` `0x021D1148`, repeat `0x021D114C`, letterale
  `0x01FF87F8`): per questo L, R e SELECT funzionano anche con L=A. Il vecchio C
  `native-eviv/eviv.c` legge i tasti elaborati (`0x021D1154`) e non va ricompilato: con
  L=A perderebbe L (una prova su Unicorn lo dimostra riportando il letterale al valore
  elaborato). Lettore, i due hook `0x02088B40`/`0x0208D178`, il wrapper dell'etichetta
  `0x01FF9348` e le stringhe EV/IV restano **byte-identici**, fissati per intervalli e
  per istruzioni complete in `data/controls-native-abi.json`.
- **Una finestra sola, di proprietà del riepilogo.** `sgp_summary_controls_update(summary)`
  crea (una volta), ridisegna e rimuove; `sgp_summary_controls_destroy(summary)` libera.
  Il `Window` (16 byte) e il buffer pixel (1024 byte) stanno nello heap 19 del riepilogo;
  un record residente di 32 byte (owner, generazione, finestra, ridisegni, flag) è il
  solo stato. L'array nativo da 34 finestre non è esteso né toccato.
- **Tre BL completi, nessuna istruzione spostata.** `0x0208CC5A` (stampa della pagina
  Abilità) → `sgp_sc_redraw`: update, poi la funzione nativa, quindi l'hook ereditato del
  lettore; `0x02089D78` (cambio pagina) e `0x0208C564` (uscita) → `sgp_sc_teardown`: destroy
  prima di `sub_0208C4E0`. Sono gli **unici** chiamanti (scansione di tutti i BL e dei
  puntatori dell'ARM9). Portata BL ±4 MiB: ogni base fino a `0x023E0000` è raggiungibile,
  l'encoder rifiuta il resto.
- **Quando disegna.** Pagina Abilità, non in uscita, `args` presente, modalità `args+0x12`
  diversa da 3 e 4, nessuna mossa da imparare (`args+0x18 == 0`), Pokémon presente e non
  uovo (`GetBoxMonData(mon, 76)`). Altrimenti non alloca e, se la finestra esisteva, la
  rimuove. Mai su uovo, apprendimento mossa o altre pagine. Cambio pagina e uscita
  chiamano `destroy` **prima** del teardown nativo: la finestra è liberata prima della
  pagina e prima dello heap.
- **Proprietà.** `generation` è solo diagnostica: non valida il riuso. L'unico percorso che
  distrugge un riepilogo passa dai BL riscritti (scansione completa degli archi), perciò un
  record con lo stesso `owner` ma finestra non liberata non può nascere; rileggere la finestra
  per «controllarla» sarebbe lui stesso un accesso a memoria potenzialmente liberata, quindi non
  è fatto. Solo il riepilogo che l'ha creata la libera; un record di un riepilogo
  precedente (heap già distrutto) viene dimenticato senza accedere alla memoria. Allocazione
  fallita: stato invariato e nessun accesso nullo (non usa `AllocWindows`, che non
  controlla `Heap_Alloc`); si riprova al ridisegno successivo. Nota: `Heap_Alloc` restituisce
  NULL, tranne che `AllocFail()` di pret resetta la console quando la comunicazione è attiva;
  la richiesta è di 16 + 1024 byte sullo heap 19.
- **Mai i tasti.** Il payload non contiene letterali di `gSystem` (controllato dal
  rilettore): la legenda non dipende dalla modalità tasti.
- **Modi tasti nativi realmente presenti** (`gSystem.buttonMode`, pret `system.h`): Normale,
  Start=X, Scambio X/Y e L=A. Solo L=A nasconde L e R dai tasti elaborati; il lettore legge i
  grezzi, quindi in tutti e quattro i modi L→EV, R→IV, SELECT→Statistiche (provato sul lettore
  reale con i tasti elaborati calcolati come `ApplyButtonModeToInput`; Android: Normale e L=A).
- **Dove il lettore c'è e la legenda no.** Apprendimento mossa (modi 3 e 4, e il modo 2 da MT
  che apre già la pagina Abilità con `moveToLearn != 0`): L/R/SELECT continuano a funzionare
  senza legenda, perché la finestra 17 e la quinta mossa occupano la zona in quelle modalità.
  È una scelta conservativa del piano («mai su apprendimento mossa»), non una limitazione del
  lettore.

## Testo e misura

Font nativo 0, colori `0x000E0F00` (bianco con ombra, come «MOSSE LOTTA» e i titoli
EV/IV), una riga. Testo identico in EN e IT (nomi dei tasti e sigle); codifica con la
charmap pret, un carattere non mappato è errore.

| Variante | Testo | Avanzamento | Finestra minima |
|---|---|---:|---|
| compatta (piano, predefinita) | `L:EV SELECT:Stat. R:IV` | 124 px | 16 tile = 128 px |
| spaziata (leggibilità) | `L:EV  SELECT:Stat.  R:IV` | 132 px | 17 tile = 136 px |

La base 955 e la posizione `(1,18)` sono la **proposta non provata** del piano: la ricevuta di
un'installazione inerte le marca `geometry_source: proposal` (e `placement.proven: false`); non vanno lette come scelta.
`prepare` rifiuta una finestra più stretta del testo («truncated») e registra avanzamento
e larghezza nella ricevuta. Render offline EN/IT (font reale estratto dalla ROM in
memoria, sfondo = schermo inferiore dello scatto IT del 29 ottobre, striscia a `(8,144)`)
nel materiale privato `local/notes/cc-modern-mechanics/c8/C/legend-*.png`: la spaziata
separa meglio i tre comandi; entrambe stanno nel rosso sotto il riquadro mosse, sopra le
schede, senza troncamenti. Non sono catture di gioco: la verità resta lo scatto melonDS.

## Posizione e tile: ancora da misurare

Il riquadro proposto `(8,144,128×16)` dello schermo inferiore (layer `bgId 4`) si
sovrappone, nelle tabelle statiche, a `page_skills.12` (quinta mossa), `page_skills.17`
(messaggio `0xC2` mostrato da `sub_0208AFA0` con flag 1), `shared.14` e `shared.29`
(ripulita a fine delle modalità speciali, `unk_02088288.s` righe 4913 e 5038). Possono
essere vuote nella vista ordinaria, ma non è provato: `prepare(..., active=True)`
rifiuta senza una `evidence` che le nomini nascoste (`hidden_windows`) e dichiari liberi
i tile (`free_tiles`). L'evidence è legata a ciò che si è misurato: `capture_rom_sha256`
(la ROM candidata INERTE su cui Codex ha fatto la cattura), che deve essere uguale all'argomento
esplicito `candidate_sha256` di `prepare`, `build_id`, `language` uguale a quella dichiarata,
`geometry` identica, `views` ⊇ {stats, ev, iv}, `button_modes` ⊇ {normal, L=A},
`contexts` ⊇ {field, pc} e `captures` = riferimenti `{name, sha256}` alle catture; un record di
un'altra ROM candidata, lingua o geometria, o senza questa copertura, è rifiutato e finisce intero nella
ricevuta, che registra anche `candidate_sha256`, `capture_rom_sha256` e `candidate_relation`
(`stage-inert-output` se la candidata è esattamente l'uscita inerte di questo stadio, ricalcolata dai byte;
`composed-candidate` se è la ROM composta di tutti gli stadi, che questo modulo non può ricalcolare).
L'evidence non è più legata all'hash dell'immagine in ingresso allo stadio (la V4): una cattura
fatta sulla candidata non poteva mai attivare la legenda. Tile: le finestre native del layer 4 finiscono al 954, il
tilemap ha 10 bit (limite 1023); la base proposta 955 (32 o 34 tile) ha spazio, ma le
sole tabelle non provano l'assenza di altra grafica oltre 954. `sub_0208CBD4` svuota il
tilemap del layer 4 (colonne 0..17, righe 1..23) a ogni disegno di pagina: la legenda
si ridisegna a ogni ridisegno nativo. Nessun `baseTile` è scelto perché «sembra vuoto».

## Composizione: intervalli di byte, non hash della ROM

`audit`/`prepare`/`verify` non confrontano più l'intera immagine con la V4: verificano solo gli
**intervalli** che leggono o riscrivono (`controls.intervals()`: lettore e payload del visualizzatore,
le due parole di aggancio, i corpi interi (estensione di funzione) delle dieci funzioni native chiamate e della funzione che contiene il sito `0x02089D78`, le quattro tabelle di
finestre, i due descrittori BG, i letterali, e i tre siti BL, gli unici byte ARM9 riscritti oltre
allo slot) più il completamento dei chiamanti BL dei quattro bersagli agganciati (predicato, non hash).
Un altro stadio che lascia intatti quei byte (la UI, le altre meccaniche c8) può quindi precedere la
legenda; uno che li tocca è rifiutato con il nome dell'intervallo. L'ordine UI → legenda è provato in
`test_controls_rom.RealUiComposition` con l'uscita reale di `sgp131.ui.install`; l'ordine inverso
(legenda → UI) è rifiutato dalla UI stessa (richiede la V4 esatta), non da questo modulo.
Sovrapposizione con le scritture ARM9 di `sgp131/ui.py` (siti `0x0201A556`, `0x02000DB0`,
`0x0203BFE4`, template `0x020FA354`, payload `0x023CB800`/`0x023D4000`/`0x023D6800`/`0x023D6E10`,
semi e azzeramenti): **nessuna** (`test_controls.Intervals`). Lo slot `summary-controls.runtime`
(`0x023D4C10`, 512 B) confina con la fine del payload Fieldbook (`0x023D4C00`) a 16 byte.

## Base e ricevute

La base non è più un indirizzo né un dizionario libero: `prepare(..., allocation=<ricevuta di
sgp131.reserve.allocate per summary-controls.runtime>, preimage_sha256=...)`. La ricevuta è
ricontrollata contro la politica di riserva in vigore (stessa politica, input V4 della stessa lingua,
nomi non condizionali, assegnazioni identiche a quelle di `reserve.allocate`). Oggi la mappa ufficiale
non può concederla (il proprietario `field-guide.code` è condizionale), quindi in produzione
l'installatore rifiuta: i test usano una politica di prova dichiarata (`bench.declared_reserve`).
La ricevuta riporta `function_state` (`inert`/`active`, ricalcolato da `verify` dalla parola di
attivazione installata) e nessuno stato di processo (revisione, Android).

## Prove

| Livello | Cosa prova | Stato |
|---|---|---|
| Host (nessuna ROM) | pin, confronto, encoder BL/hook, geometria, testo, contratto di `prepare` | eseguito |
| ARM Unicorn su byte V4 EN/IT | `AddWindow`, `FillWindowPixelBuffer`, `ScheduleWindowCopyToVram`, `ClearWindowTilemapAndCopyToVram`, `WindowArray_Delete` reali; lettore EV/IV reale con tasti grezzi (Normale e L=A); flusso reale dal dispatcher e dall'uscita con ROM patchata | eseguito |
| Android (melonDS) | resa, tile, finestre visibili, stati reali | **assente** |

Il banco avvelena la memoria: i blocchi nuovi sono riempiti con `0xCD` (il buffer pixel deve
risultare azzerato dalla legenda stessa) e i blocchi liberati con `0xDD`, con un hook che
registra ogni lettura o scrittura su un intervallo liberato (uso dopo liberazione).

Stub dichiarati e registrati: `Heap_Alloc`/`Heap_Free`, il printer
(`AddTextPrinterParameterizedWithColor`, la sua pila non è misurata), `GetMon`,
`GetBoxMonData`, i trasferimenti VRAM, e nel flusso dall'uscita il teardown nativo.
Riepilogo, BgConfig e Pokémon sono sintetici e sparsi. Il sito di cambio pagina
`0x02089D78` è provato solo per decodifica statica (stesso wrapper dell'uscita).

## Scenari Android per Codex

Fixture: copie dei salvataggi avanzati EN e IT con una squadra che contenga un uovo, un
Pokémon con EV/IV non nulli e una mossa da imparare (livello o MT). Per ogni caso, schermo
inferiore EN e IT e il record da 32 byte alla base assegnata (owner, generazione, finestra,
ridisegni, flag).

1. Continua → squadra → riepilogo → Abilità: legenda visibile, nessuna sovrapposizione con
   riquadro mosse, schede ed ESCI; numeri e titolo invariati.
2. Da Abilità: L (EV), R (IV), SELECT (Statistiche), ripetuti, con **Normale** e **L=A**:
   i tasti rispondono come prima; la legenda resta identica e leggibile nelle tre viste.
3. Cambio Pokémon (D-pad e tocco), cambio pagina e ritorno: nessun frammento fuori da
   Abilità; ogni ritorno la ridisegna; `generazione` +1 per ingresso.
4. Uscita (B/ESCI) e rientro, poi uscita dalla squadra: `owner` 0, nessuna finestra
   residua, nessun blocco.
5. Uovo: nessuna legenda; passare da Pokémon a uovo e viceversa.
6. Apprendimento mossa (livello e MT): nessuna legenda, comportamento nativo invariato.
7. Accesso dal campo e dal PC nativo (riepilogo annidato): stessi esiti, nessun residuo al
   ritorno nel PC.
8. Modalità selezione mossa (tocco sull'area mosse) attiva e non: nessuna sovrapposizione
   con il messaggio della finestra 17.
9. SAVE nativo e riavvio a freddo su copie dei salvataggi: nessuna differenza di dati.
10. Misure da riportare: finestre e tile realmente usati in `(8,144)`–`(136,160)`, ultimo
    tile in VRAM del layer 4, allocazioni dello heap 19 prima e dopo.

## Comandi

```sh
PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_controls -v
PYTHONPATH=source SGP_CONTROLS_REQUIRE_INPUTS=1 .venv/bin/python -m unittest sgp131.test_controls_rom -v
PYTHONPATH=source SGP_CONTROLS_REQUIRE_INPUTS=1 .venv/bin/python -m unittest discover -s source/features/summary-controls/test -p 'test_*.py' -v
```

## Correzioni post-review K (stato congelato)

- **Cancello finale obbligatorio del builder** (`controls.candidate_gate(final_rom, receipt)`): lo sha256 della ROM finale con le parole/flag di attivazione di questo stadio
  azzerate (`controls.inert_view`, funzione pura che cambia solo quelle parole) deve essere uguale a `candidate_sha256`, la candidata inerte su cui e' stata fatta la cattura.
  Senza questo controllo `candidate_relation: composed-candidate` e' un'etichetta, non un'attestazione (il test mostra che una candidata inventata passa `prepare` e non il cancello).
- **Preimmagine dello slot indipendente** (`controls.slot_preimage_from_v4(v4, language, allocation)`): l'hash atteso si calcola sulla V4 esatta, mai su `sha(rom[slot])` dell'immagine in
  ingresso allo stadio (tautologico). Ricetta del builder: `pre = controls.slot_preimage_from_v4(v4, lang, alloc)`; se uno stadio intermedio lascia legittimamente residui nello slot, il suo hash
  va fissato nel manifesto dello stadio e passato come `preimage_sha256`.
- `clang` e (per controls) `charmap.txt` sono fissati per hash; `controls.verify(..., charmap=...)` ricompila il payload con geometria, variante e flag della ricevuta.
- **Limiti noti**: il predicato dei chiamanti BL vede solo BL Thumb nel segmento statico (non BLX da ARM, chiamate da literal pool, overlay); `audit` e' valido solo PRIMA di `prepare`
  (dopo l'installazione i tre siti e le loro funzioni non hanno piu' l'hash del pin); le callee transitive delle funzioni native non sono fissate (garanzia: lista chiusa di scritture degli altri stadi, provata contro la UI).
