# Manutenzione 1.2.4

Questo aggiornamento è lo stadio finale della 1.2.4. Corregge due percorsi
identificati nel codice, senza cambiare il formato di salvataggio. Il
costruttore riproduce prima l'intermedio 1.2.3, verificato per SHA-256, poi
applica questo stadio e aggiorna il titolo. L'applicatore autonomo accetta
le immagini ufficiali 1.2.3 EN/IT; le patch della distribuzione coprono
invece tutte le sorgenti elencate in `source/distribution/release.json`.

## Animazioni in battaglia

Il motore usa copie OAM ferme dei Pokémon durante diversi effetti nativi.
ANIM2 continuava a muovere l'originale anche quando una copia esisteva:
`moveActive`, `animActive` e l'ingresso specie non coprono tutti questi casi.
Questo spiega la doppia sagoma durante cambi e lanci della Ball.

Il nuovo wrapper intercetta l'allocazione nel costruttore comune
`ov07_0221FB90`, riporta a riposo tutti gli slot ANIM2 prima della lettura
dei dati della copia e conta i proprietari ancora vivi. Il task non anima
finché l'ultimo proprietario non viene distrutto. I due distruttori nativi
decrementano il contatore dopo `Heap_Free`. Non vengono aggiunti task.

Il contatore resta coerente anche con opzione spenta. Riaccendendola durante
una copia viene azzerato l'eventuale `yOffset` residuo del bounce vanilla;
scala, posa e ombra native non sono modificate dal wrapper del task.
Il ripristino prima della copia usa le regole di proprietà già presenti in
`sgp_pulisci`. La ripresa ricrea fase, inviluppo e attesa della posa B.

La copertura comprende copie singole, collettive, Ball e `SpriteToOAM`.
Non è una prova che ogni episodio osservato durante KO, dialoghi, borsa o
fuga abbia lo stesso produttore della seconda immagine.

## Ricerca di Cascata durante il movimento

`FieldInput_Process` cercava ogni aggiornamento un Pokémon con Cascata:
fino a sei Pokémon, ciascuno con controllo Uovo e quattro mosse. I singoli
`GetMonData` possono decifrare e ricifrare i dati del Pokémon.

L'unico consumatore del bit ottenuto, `ov01_021F24F4`, può utilizzarlo solo
in Surf (stato 2) andando a sud (direzione 1). Il wrapper salta la ricerca
negli altri casi. In Surf verso sud richiama la funzione originale, con
stessi argomenti e stesso risultato. Le altre ricerche delle mosse non
cambiano; non si introduce una cache della squadra.

È lavoro CPU eliminato, **non una misura di FPS o di latenza**. I precedenti
interventi sul caricamento NPC riguardano soprattutto il passaggio tra zone
e non dimostrano di risolvere il rallentamento continuo nelle città.

## Memoria e applicazione

| Uso | Indirizzo | Ingombro |
| --- | --- | --- |
| Wrapper copie | `0x023DBC60` | 144 B codice + 16 B canarino, nella coda già assegnata ad ANIM2 |
| Contatore copie | `0x023DBBC0` | 4 B precedentemente riservati nello stato ANIM2 |
| Wrapper Cascata | `0x023D8040` | 24 B codice + 24 B padding + 16 B canarino, nella riserva libera della 1.2.3 |

Non cresce la riserva ARM9. Il build contiene soltanto codice compilato da
questi sorgenti. Sei regioni di file sono modificate: titolo, due zone ARM9 e
tre overlay compressi. Nell'immagine decompressa cambiano solo i cinque
ganci dichiarati. Nel controllo EN/IT la ricompressione conserva esattamente
le dimensioni dei file; FAT, header, altri asset e script restano invariati.

Dalla radice del repository, con l'ambiente già disponibile:

```sh
.venv/bin/python3 source/features/manutenzione/compila.py \
  --uscita source/sgp12/build/manutenzione

PYTHONPATH=source .venv/bin/python3 -m sgp12.manutenzione \
  --base /percorso/privato/sgp-1.2.3-IT.nds --verifica
```

`--verifica` non scrive ROM. Per creare una sola immagine 1.2.4,
sostituire `--verifica` con `--uscita /percorso/privato/sgp-manutenzione-IT.nds`.
L'ingresso non viene sovrascritto. Output esistente, preimmagine diversa,
build incoerente o spazio insufficiente causano un rifiuto. La scrittura
legge blocchi da 1 MiB e rilegge l'intera uscita prima di dichiararla valida.
Non produce ROM intermedie. Le varianti personali con altre patch sono
rifiutate: non applicare saltando il controllo dell'impronta.

## Verifiche e limiti

```sh
.venv/bin/python3 -m unittest discover -s source/features/manutenzione -p 'test_*.py'
```

Le prove dei wrapper eseguono il piccolo codice ARM su memoria sintetica
con Unicorn già installato, insieme al blob ANIM2 proprio. I confini con
heap e renderer sono simulati. Non avviano il gioco, melonDS o un firmware.
Su macOS il sandbox può terminare Unicorn durante `mem_map`: in tal caso
serve un ambiente di esecuzione che consenta la memoria della libreria,
non una reinstallazione. Le prove dell'applicatore usano file minuscoli.

La prima verifica ha rilevato i difetti prima delle correzioni; dopo le
correzioni passano 8 prove dei wrapper (20 combinazioni stato/direzione
incluse), 9 dell'applicatore e 7 del verificatore del totem e dei flag.
La suite leggera preesistente `sgp12.test_lib` ha eseguito 42 prove e
saltato le 31 che richiedono ricostruzioni/fixture ROM; la verifica della
mappa ha eseguito 3 prove strutturali e saltato 8 prove con fixture esterne.
Questi skip sono intenzionali e non valgono come controlli superati.
La preparazione sulle due ROM reali ha
verificato preimmagini, spazi, ricompressione e rilettura indipendente in
circa 1,1 secondi per lingua, con picco RSS complessivo di circa 97 MiB.
Questa fase non ha misurato prestazioni né immagini del gioco. La successiva
prova utente e la breve misura della presentazione sono descritte sotto.

## Totem di Aranciopoli: controlli del codice e prima prova riuscita

```sh
.venv/bin/python3 -B source/features/manutenzione/verifica_totem.py
```

Il verificatore legge i membri necessari a streaming, senza salvare asset.
Usa il decoder già presente e il checkout pret locale; non installa nulla.

1. **Dal tasto A all'avvio della lotta:** sei scenari per lingua, con/senza
   Rugiada Anima e conferma/rinuncia. Le destinazioni dei salti, gli oggetti,
   i movimenti e i messaggi risultano strutturalmente validi.
2. **Parametri e ritorno dalla lotta:** dodici scenari per lingua, due
   rami specie e sei esiti. Latios/Latias livello 40 sono validi; lo script
   raggiunge `ReleaseAll/End` e usa `WhiteOut` per sconfitta/pareggio.

Questi sono controlli del bytecode e simulazioni del flusso: le attese
native vengono assunte completate. **Non eseguono il motore durante la
battaglia e non riproducono il freeze.** Sei prove aggiuntive con mutazioni
in RAM verificano che il controllore rilevi salti, oggetti, specie, livelli
e sblocchi alterati.

`LockAll` può attendere indefinitamente un movimento che non termina;
durante la lotta il task attende la chiusura dell'applicazione di battaglia.
Senza lo stato d'esecuzione del momento del blocco non è determinato quale
attesa, se una di queste, rimanga pendente.

È inoltre emerso un limite ereditato dall'hack: i flag `0x3FCA` e `0x3FAF`
superano la struttura nativa `SaveVarsFlags`. Nei binari EN/IT accedono a
due byte del PalPad, rispettivamente `+0xDD` bit 2 e `+0xD9` bit 7. La
stessa gestione esiste già nelle basi Classic 1.04 e Plus 1.1. Potrebbe
essere un riuso deliberato dell'hack; non prova che causi questo freeze.
Cambiare gli ID senza censimento e gestione dei salvataggi preesistenti
potrebbe alterare la progressione: non è stata applicata una rimappatura.

Una verifica separata esegue la vera `Save_VarsFlags_SetFlagInArray` delle
ROM EN/IT con Unicorn su un salvataggio sintetico. Sei chiamate (tre flag
per lingua, incluso un controllo valido) confermano gli offset fuori
struttura e il ritorno regolare con `_021D4150=0`. Per i due flag alti viene
raggiunta `GF_AssertFail`, che in questa condizione ritorna. Nessun mock
sostituisce questi accessori; non è comunque lo stato catturato durante
il freeze dell'utente, né una prova di tutti gli stati possibili.

Lo script e i flag del totem restano quindi invariati. Questi controlli
da soli non dimostrano la risoluzione del blocco.

## Prova utente sulla dispositivo Android del 24 ottobre 2026

Su successiva richiesta esplicita è stata sostituita la ROM sulla dispositivo Android,
preservando il salvataggio corrente e le personalizzazioni della ROM già
installata. L'utente ha avviato e giocato personalmente: riferisce di aver
catturato Latios e di non osservare più i rallentamenti. Ha inoltre precisato
che il vecchio blocco avveniva dopo l'inizio della lotta. Il caso segnalato
ha quindi avuto esito positivo con il candidato; manca ancora una prova
che attribuisca il vecchio freeze a una specifica modifica, e non sono
stati confermati tutti gli scenari di sovrapposizione delle animazioni.

Dopo il resoconto sono stati raccolti circa 30 secondi di tempi di
presentazione SurfaceFlinger: intervallo mediano 16,763 ms, percentile 95
16,767 ms, nessun intervallo oltre 25 ms. Sono tempi della superficie Android,
non FPS della logica DS né misure di latenza dei comandi. La posizione nel
gioco durante questa misura non è stata rilevata: non è un confronto
controllato tra città né con la ROM precedente.

La prima raccolta log si era interrotta prima dell'avvio della partita;
è stato recuperato il buffer dell'app ed eseguita una nuova raccolta durante
la misura. I log disponibili non contengono una riproduzione del vecchio
freeze. La raccolta breve è conclusa; log e ricevute restano in `local/`,
esclusi dal repository pubblico. Non sono stati installati emulatori o APK.

## Riferimenti della diagnosi

I riferimenti al motore sono nella revisione pret/pokeheartgold
`0985e8718df4f25e64d6507d89c0c97c0d288981`, consultata localmente:
`asm/overlay_07.s` (costruttore/distruttori copie),
`src/pokepic.c` (renderer e attributi),
`src/field/field_control.c` e `asm/overlay_01_021F1AFC.s`
(produttore e consumatore del bit Cascata), `src/script_pokemon_util.c`.

Segnalazioni pubbliche descrivono scatti anche nell'originale, ma non
identificano da sole una causa comune:
[Goldenrod e Vermilion, testimonianze del 2025](https://www.reddit.com/r/PokemonHGSS/comments/1k79vaq).
La rimozione del limitatore FPS è una modifica distinta che può accelerare
il gioco: [strumento dell'autore](https://github.com/ITotalJustice/pokemon-gen4-fps-unlocker).
Non è stata inclusa in questo aggiornamento.
