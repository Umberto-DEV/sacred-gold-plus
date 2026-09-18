# Squadra in battaglia: riduzione della pausa di apertura

Con le animazioni opzionali attive, il menu Squadra riusa la tabella delle
mosse già caricata dalla battaglia. Nella fixture EN/IT la pausa del task idle
scende da **33 a 20 frame**, circa **0,55 → 0,33 secondi** a 60 Hz, alla prima
e alla seconda apertura. Rimane un caricamento visibile: non è movimento
continuo in ogni fotogramma. La taratura del respiro anim2 a 0,375× resta invariata
(v5c, e la [v5d](../anim2/README.md#v5d--accento-di-posa-b-18-settembre-2026) non la tocca:
cambia solo la posa B).

**La cache è attiva solo con l'opzione «animazioni» accesa.** Quel byte
(`0x023D8716` nel chunk di salvataggio Plus) è **spento per difetto**:
`record()` in [squadra_cache.c:13](sorgenti/squadra_cache.c) lo controlla
insieme al blocco opzioni valido, e con l'opzione OFF la funzione ritorna
sempre il getter nativo. Con l'opzione spenta il percorso resta quello
nativo: la riduzione 33→20 frame **non** si applica, come misurato di
seguito nella riga «OFF».

## Causa e contratto

`ov08_0221D184` prepara i dati dei sei Pokémon. Per ogni mossa occupata chiama
`GetMoveMaxPP` e quattro volte `GetMoveAttr`: tipo, categoria, precisione e
potenza. Ogni chiamata nativa rilegge il membro NARC della mossa; il loader
esegue sette letture FS fra intestazioni, indice e contenuto. Il profilo GDB
conferma le letture durante la pausa; una sonda limitata ai cinque getter
ha misurato la riduzione prima dell'applicazione permanente.

`BattleContext_New` ha già caricato con `LoadMoveTbl` i 468 record da 16 byte
usati dalla battaglia. L'offset corretto è **`ctx + 0x3DE`**, verificato nel
letterale passato al caricatore a `ov012:0x022486A8`. La successiva `itemData`
è allineata separatamente: sottrarre la dimensione della tabella dal suo
indirizzo darebbe un offset errato di due byte.

Il [blob](sorgenti/squadra_cache.c) intercetta cinque BL nella sola scansione
Squadra: `0x0221D3DE`, `0x0221D3E8`, `0x0221D3F2`, `0x0221D3FC` e
`0x0221D406`. Legge il contesto del menu da `[sp]` del chiamante, mantenendo
stack allineato e registri preservati. Le guardie richiedono opzioni valide,
animazioni ON, puntatori presenti e mossa nel range 0–467; il getter degli
attributi accetta soltanto i quattro attributi previsti. Ogni altro caso
conserva il getter originale. Non ci sono nuove allocazioni, cache persistenti
o scritture ai dati delle mosse.

I PP mantengono la formula nativa, il limite di tre PP-Up e il risultato a
8 bit. La divisione per cinque usa un'identità intera valida nel dominio
0–765, verificata su tutti i 256 valori PP e sei valori PP-Up, inclusi quelli
che richiedono il limite.

Il blocco occupa **256 byte a `0x023DBE00`**: codice 200 byte, margine zero di
40 byte, canarino di 16 byte. [Compilatore](tools/compila.py),
[applicatore](../../sgp12/blocchi/squadra_lotta.py) e
[rilettore indipendente](tools/rileggi.py) verificano provenienza, impronte,
riserva, preimmagini, tutti i bersagli e confinamento dell'intera immagine.
L'overlay resta compresso nello stesso slot, con FAT e coda inalterate.

Sorgente nativo esaminato: `pret/pokeheartgold`, commit
`0985e8718df4f25e64d6507d89c0c97c0d288981`, file `asm/overlay_08.s`,
`src/move.c`, `include/move.h` e `src/battle/battle_controller_player.c`.

## Verifica del 15 settembre 2026

Fixture: Typhlosion livello 49 contro Kakuna livello 19 nel Parco Nazionale,
con squadra di sei Pokémon. Ogni replay parte dalla ROM fredda e da una
copia dello stesso salvataggio; l'opzione animazioni è impostata esplicitamente
in RAM, senza alterare mosse o Pokémon.

| Prova | Risultato |
| --- | --- |
| EN/IT, ON, due aperture | Plateau task 33→20 frame per apertura; menu e ritorni completati. |
| EN/IT, OFF, due aperture | Plateau VBlank di 32 frame, percorso nativo conservato. Il plateau task ON della baseline è 33: sono due contatori distinti. |
| ABI ARM, 10 test | Cinque contratti sul blob spedito e su quello ricompilato: valori, PP, limiti, opzioni, puntatori e stack/registri/Thumb. |
| Equivalenza ARM nativa, una prova per lingua | Tutte le 468 mosse, quattro attributi e sei PP-Up confrontati con i getter originali. Intercettato soltanto il trasporto NARC; eseguite anche le istruzioni native di divisione. |
| Dati live EN | 7.488 byte della tabella in RAM identici ai 468 membri NARC. |
| Regressione offset | Il mutante `0x3E0` viene respinto dal confronto nativo: potenza della mossa 1 pari a 100 anziché 40. |
| Cambio e fine lotta EN/IT | Due replay freddi: Typhlosion→Togetic, scelta mossa, KO e ritorno al campo entro il frame 9262; schermate e PP ispezionati. |
| Build complete EN/IT | Ricostruzione byte-identica dalle basi 1.1; 16 rilettori verdi senza salti e T1–T5 della riserva superati. |
| Bundle, 7 test | Provenienza, impronte delle due mappe, simboli, checksum e sovrapposizioni. |
| Rilettore, 6 test per lingua | ROM valida accettata; alterazioni di codice, margine, canarino, metadati, header e coda FAT respinte. |

Le prove sono in emulazione, su una fixture; non dimostrano compatibilità
completa di ogni modalità, Safari, doppie o hardware. Restano letture di
dati specie/esperienza, caricamenti grafici e pause durante i ritorni.
L'ottimizzazione non modifica questi percorsi. L'audit animazioni precedente
resta disponibile [qui](../anim2/AUDIT-2026-09-14.md).

## Riproduzione

```sh
python3 source/features/squadra-lotta/tools/compila.py \
  --uscita source/sgp12/build/squadra_lotta
python3 -m unittest discover -s source/features/squadra-lotta/test -p test_build.py
python3 -m unittest discover -s source/features/squadra-lotta/test -p test_blob.py
SGP_ROM_SQUADRA_PRIMA=/percorso/pre-squadra-EN.nds \
SGP_ROM_SQUADRA_DOPO=/percorso/finale-EN.nds \
  python3 -m unittest discover -s source/features/squadra-lotta/test -p test_rilettore.py
SGP_ROM_SQUADRA_DOPO=/percorso/finale-EN.nds \
  python3 -m unittest discover -s source/features/squadra-lotta/test -p test_native_data.py
python3 source/features/squadra-lotta/tools/copione.py /tmp/squadra.script
```

Ripetere le prove su ROM con la coppia IT. Il copione richiede la fixture
compatibile descritta in `anim2/tools/copioni.py`; `--off` ripete il percorso
con animazioni disattivate. Unicorn richiede il permesso di eseguire codice
JIT. ROM, salvataggi, stati, catture e dump rimangono privati. La verifica
completa e riproducibile usa `sgp12.verifica` come nella
[guida di ricostruzione](../../docs/rebuilding-1.2.md).
