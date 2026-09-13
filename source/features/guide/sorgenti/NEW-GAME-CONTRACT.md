# Contratto New Game per la guida 1.05

7 settembre 2026. **Contratto verificato sui binari e sul primo setup nativo EN/IT; nessuna integrazione New Game.** La presentazione Summary Task3 è ancora in sviluppo/review. Questo documento non ne anticipa l’accettazione. [Metadati](new-game-resources.json), [presentazione condivisa](PRESENTATION.md), [piano](../../docs/superpowers/plans/2026-09-07-guida-introduzione-105.md).

Raccomandazione: un host specifico che avvolga il normale Init/Main/Exit di Oak, lasci completare il **primo** setup grafico, presenti la guida e restituisca Oak al suo primo task. Le risorse effettive rendono questa soluzione più contenuta di un secondo overlay/heap grafico prima di Oak. Il componente di testo/input rimane condiviso e non riceve `SaveData*`. Il wrapper è una futura implementazione, non un risultato già eseguito.

## Identità e prova binaria

Basi Plus Community1 esatte: EN SHA-256 `3ed4ea0291092d46def2f71454821bbde7832014ec020680468af7bfca686248`, IT `217daa45f4945abd3feda6f583f5163db029d1aa361c33c18f12b32ad4eca4a4`. Pilot r5: EN `a1d7ed3ecb8aa98f96f65c17015cb49df5bda84323459cb17fd3d4c4501f556e`, IT `96c41b594349e22c34789a52123327093b78e92a5be926f4e3000dd32a8e8ed3`. Percorsi e hash completi sono nel JSON.

Estratti gli overlay tramite ndspy, disassemblati i byte effettivi con clang/llvm-objdump Thumb v5TE e confrontati con il flusso delle fonti pret fissate a `0985e8718df4f25e64d6507d89c0c97c0d288981`. Non è un matching build del decompilato: i nomi sono attribuiti confrontando prologo, chiamate, costanti, layout e template. Le funzioni/table selezionate hanno intervalli/hash, non solo un nome C.

| Overlay | RAM, fine esclusiva | Byte | SHA-256 decompresso |
|---|---|---:|---|
| 36, NewGame / continuazione | `0x021E5900–0x021E5C60` | 864 | `7d8cb8a0b0d2cb1865ffb09066f20a191eb06f8ae41f250828829c23c5b96acc` |
| 53, Oak | `0x021E5900–0x021E88A0` | 12192 | `19a3c683b5e82e37d71bb3cab902b106c14694676550482c15fcdf6c4a850ac0` |
| 74, MainMenu | `0x02227060–0x0223D080` | 90144 | nel JSON |

Tutti e tre coincidono byte per byte EN/IT e base/r5. BSS zero per gli overlay36/53; overlay74 ha6528byte di BSS. Overlay36 e53 occupano la stessa RAM e **non possono essere eseguiti contemporaneamente**. I file ROM restano compressi: gli offset interni usati qui si riferiscono ai dati caricati, non a un offset ROM da patchare alla cieca.

| Percorso verificato | Indirizzi reali |
|---|---|
| MainMenu_QueueSelectedApp | `ov74:0x02228B8C`; caso NewGame a `0x02228BBE`, BL Register a `0x02228BC2`; literal overlay36 a `0x02228C24`, template NewGame a `0x02228C2C` |
| template NewGame, ov36 | `0x021E5C24`: Init `0x021E5901`, Exec `0x021E5919`, Exit `0x021E592D`, id `0xFFFFFFFF` |
| NewGame Exec | `0x021E5918`: legge gli argomenti, chiama `NewGame_InitSaveData` a `0x021E5BC8`, poi ritorna TRUE |
| NewGame Exit | `0x021E592C`: distrugge heap75 e registra il template Oak `0x02106068` con id esterno NONE |
| template Oak, ARM9 statico | `0x02106068`: `0x021E5901`, `0x021E5995`, `0x021E5B49`, overlay id53 |
| Oak Init / Main / Exit | `0x021E5900`, `0x021E5994`, `0x021E5B48` |
| Oak VBlank / InitBgs / InitMsgPrinter | `0x021E5BCC`, `0x021E5BDC`, `0x021E5E6C` |
| Oak prima presentazione | `Oak_DoMainTask=0x021E6F9C`, chiamata da Main a `0x021E5A5C` |
| continuità dopo Oak | Exit registra ov36/template `0x021E5C14`; Init/Exec/Exit `0x021E5949/0x021E5961/0x021E5981` |

I puntatori Thumb hanno bit0=1; gli indirizzi di disassemblaggio sono pari. `OverlayManager_GetData=0x02007290` (byte raw `c0697047`, halfword `0x69C0 0x4770`), `GetArgs=0x020072A4` (byte raw `80697047`, halfword `0x6980 0x4770`): **non invertirli**. Nel vecchio contratto Summary una descrizione attribuisce impropriamente GetData a `0x020072A4`; il codice effettivo di Main chiama `0x02007290`. Il manager conserva data a+`0x1C`, args a+`0x18`, stato applicazione a+`0x14`.

Preimmagini iniziali Oak: Init `38b582b00122051c`, Main `78b583b00d1c21f6`, Exit `70b5061c21f6a0fb`. Il prologo Main contiene parte di una BL PC-relative e non si può rilocare copiando otto byte. La soluzione preferita non intercetta questi prologhi: valida e sostituisce soltanto i tre puntatori del template ARM9 Oak, lasciando intatti id53 e codice originale. Il manager caricherà comunque ov53 prima di chiamare il wrapper Init. Ciascun wrapper chiamerà la funzione originale solo mentre ov53 è caricato. Preimmagini complete del template verificate nelle quattro ROM.

## Checkpoint nativo prima della presentazione

Due avvii da zero, **senza SRAM in input**, su r5 invariata. Interpreter, renderer software1×, FreeBIOS/firmware generato, RTC2026-09-05 12:00:00, zero cheat/freezes. Observer Task3 esistente e invariato: `<scratch>`, SHA-256 `f918f1afb00a1aeff3833d655f5ad078dc680e4ba663ee9c1d7a381c4bed2af1`. Core906e9ebb, hash dei tre oggetti/librerie e sorgente nel JSON. Nessun nuovo observer o core costruito.

Prove nuove private in `<scratch>`. `setup.script` parte dallo stesso prefisso tasti dello script storico. Dump ogni frame2370–2380: primo checkpoint completo **EN2375, IT2374**, PC frame-end `0x020D3F64`, callback `0x021E5BCD`, stato esterno1 e interno0. Ov53 caricato coincide interamente con il decompresso della ROM. Lo stesso numero di frame non è un’invariante fra lingue: usare il contratto di stato/risorse. Il PC è un’osservazione a fine frame, non un breakpoint d’istruzione all’interno del wrapper.

In questi soli campioni: manager `0x0226F27C`, data `0x022A0244`, BgConfig `0x022A08D4`. **Sono puntatori dinamici, non ABI da hardcodare.** Oak Init crea heap80 da parent3, capacità`0x40000`, data`0x180`; `data+0x0` heapID, +`0xC` inner state, +`0x14` naming submanager, +`0x18` BgConfig. Init possiede font4 e i due naming args. Salvataggio/opzioni a+4/+8 restano proprietà Oak; il componente guida non li legge.

Main state0 termina setup BG, messaggi, sprite, YesNo e VBlank; `0x021E5A50–0x021E5A54` imposta outer1 e salta al tail sprite. Il primo state1 inizierà tutorial/audio tramite DoMainTask. Naming ritorna attraverso outer5→0: un gate basato solo su state0 riproporrebbe la guida dopo il nome. Serve un marker per istanza, azzerato esplicitamente da Init e pulito da Exit, senza flag nel save e senza usare il padding di Oak.

## Video e font del nuovo host

Bank table a `0x021E8628` (40byte), modes a`0x021E8548` (16), template main a`0x021E85CC` e sub a`0x021E85E8` (28 ciascuno). Le literal reali di InitBgs e il runtime confermano main BG128KiB A, sub BG128KiB C, main OBJ128KiB B, sub OBJ16KiB I; texture/ext palette assenti. VRAMCNT A–I letti: `81 82 84 00 80 80 80 00 82`; WRAMCNT a0x247 vale3 e non è un bank VRAM. D/H disabilitati, i bit residui non sono una riserva da usare.

| BG | character base | screen base | controllo osservato | priorità |
|---|---:|---:|---:|---:|
| main0 | `0x18000` | `0x7800` | `0x0F19` | 1 |
| main1 | `0x14000` | `0x7000` | `0x0E15` | 1 |
| main2 | `0x10000` | `0x6800` | `0x0D11` | 1 |
| main3 | `0x0C000` | `0x6000` | `0x0C0D` | 1 |
| sub0 / BG4 | `0x18000` | `0x7800` | `0x0F18` | 0 |
| sub1 / BG5 | `0x14000` | `0x7000` | `0x0E14` | 0 |
| sub2 / BG6 | `0x10000` | `0x6800` | `0x0D10` | 0 |
| sub3 / BG7 | `0x0C000` | `0x6000` | `0x0C0F` | 3 |

Tutti text4bpp, tile32byte, map32×32/`0x800`, scroll0. `BgConfig+8`, stride`0x2C`; BG4 a+`0xB8`. Al checkpoint la sua mappa CPU/GPU coincide ed è zero. Character base assoluta BG4=`0x06218000`, GPU map=`0x06207800`. Il font nativo sub è caricato nella **palette14**, non13. Il runtime la conserva identica EN/IT: colore1=`0x296B`,2=`0x5EF5`,14=`0x0000`,15=`0x7FFF`. Per testo scuro su fondo opaco usare i colori del font coerenti con questo host, ad esempio foreground1/shadow2/background15; la leggibilità e i controlli disabilitati richiedono review a1×. Non riusare senza adattamento lo sfondo14 del modal Summary: qui sarebbe nero. Nessuna scrittura palette richiesta dalla soluzione proposta.

**Il display è ancora nero al primo setup.** Entrambi i MASTER_BRIGHT sono`0x8010`. Sub DISPCNT=`0x00011010` (visibilità OBJ`0x1000`), BLDCNT=`0x3944`, BLDALPHA=`0x001F`, BLDY=0. Solo accendere BG4 lascerebbe la guida invisibile. Salvare e ripristinare precisamente sub brightness/blend/visibilità; durante la guida usare brightness neutra, blend disabilitato e solo BG4. Non toccare brightness/main graphics. Il ritorno ripristina il nero originale, quindi Oak esegue la sua normale dissolvenza. Non chiamare di nuovo InitBgs per recuperare lo schermo.

Font0 esiste già ma è **lazy**, mode1, decompression callback`0x02026111`, narcReadBuf NULL; fontwork=`*0x0211188C`, font0=`*(work+0x9C)`, refcount+`0xB4`. I campioni mostrano refcount1 e font4 già allocato; il font0 non va rilasciato o convertito silenziosamente in direct. `FontID_TryLoadGlyph` è lo stesso helper nativo e il sorgente del percorso lazy legge il glifo con NARC_ReadFromAbsolutePos in un buffer interno di64byte. Non dedurre da questo una misura di latenza o l’assenza di ogni effetto FS: il percorso di rendering lazy deve essere osservato nell’integrazione. Il guard Summary che richiede mode0/callback`0x02026069` non è applicabile a Oak.

Il membro font0 già misurato per Summary è riutilizzabile; r5 non ha modificato l’archivio font. Conservare colori/scratch renderer e glyph buffer condiviso; considerare anche il `glyphReadBuf` lazy in `FontData+0x14` (64byte). La posizione del file NARC cambia con le letture assolute: non ripristinare strutture FS private copiandone memoria alla cieca. Verificare il successivo rendering Oak; font mode/refcount/header/puntatori devono restare invariati. Il prestito può mantenere font0 lazy; una conversione direct sarebbe una modifica di ownership/allocazione ulteriore, non autorizzata dal semplice spazio libero misurato.

## Heap, prestito e ritorno

Heap80 risolto dalla tabella corrente `*0x021D1584` e indice in `*0x021D1594 +80`, non tramite il resolver Summary hardcoded19. Nei due checkpoint indice4, handle`0x022A01EC`, extent`[0x022A0224,0x022E01EC)`. Walk in lettura:150 blocchi usati, due liberi8 e191744byte; totale191752, massimo191744. Verificati firma EXP H, firme FR/UD, bounds, allineamento, link predecessor e tail; non basta la capacità nominale.

`0x5800`/22528byte è compatibile con il blocco massimo nel checkpoint. Nessuna allocazione, free, NULL o lease realmente restituito è stato provato qui. Il risultato non certifica il rilascio pulito: quel gate è dell’integrazione. Riutilizzare l’ABI raw NNS già verificata (ARM pari `0x020B53A0` allocate, `0x020B5530` free; IRQ `0x020D3A38/0x020D3A4C`) con heap80 risolto/validato e ownership propria. Non usare Heap_Alloc per tentare la capacità: la sua failure può resettare. Non passare un puntatore NNS a Heap_Free/RemoveWindow.

Modal compatto condiviso:289tile dal tile1, **`[0x06218020,0x0621A440)`**,9248byte. Snapshot caratteri9248 + mappa CPU2048 + bitmap9248 =20544. Rimangono1984byte del lease per context, Window, scratch font/colore e i64byte aggiuntivi lazy. Il limite deve essere ricalcolato/assertato sulle strutture finali, non presunto dalle dimensioni Summary. Nessun badge prima di Oak. Mai occupare altri bank o tile perché sembrano vuoti.

Per il ritorno conservare caratteri prestati, mappa CPU BG4 e relativi trasferimenti, sub visibility/brightness/blend, font scratch e callback/argomento. Non distruggere BgConfig, sprite, finestre YesNo, font4 o naming args. La callback Oak esegue scheduled BG updates e OAM: deve restare valida. Sospendere il normale Main mentre il modal è attivo; lasciare drenare gli aggiornamenti prima dello snapshot, mantenere i buffer fino al VBlank di ripristino, poi rilasciare solo la propria lease e riprendere outer1/inner0 con guardia di rilascio input. La prova dovrà escludere scritture autonome nei byte prestati e heap drift.

## Scelta del wrapper e budget

Un host indipendente **prima** di Oak richiederebbe template/ciclo propri, heap, bank/BG/callback, font/palette e cleanup completo; il menu/ov36 non offre il contratto grafico Oak e ov36 viene scaricato. Occorrerebbe inoltre preservare NewGame_InitSaveData prima di avviare Oak. Non emerge un vantaggio rispetto al setup già pronto, mentre si aggiungono risorse e codice da provare.

Il wrapper del template Oak consente l’Init originale, registra la propria istanza e lascia il primo Main state0 completare la grafica. Prima del successivo state1 mostra la guida. Dopo completamento/skip torna al Main originale con gli stessi argomenti/stati. Alla successiva ricostruzione grafica dopo naming il marker impedisce la ripetizione; prima di Exit elimina qualunque risorsa ancora propria, poi chiama **una sola volta** l’Exit originale che scrive legittimamente nome/genere/rivale e continua la partita. Nulla di questo appartiene al percorso Summary.

Riservare per l’istanza al massimo32byte ITCM espliciti (tag/manager/phase/seen/puntatore contesto e guardie), azzerati da Init e Exit. I dettagli possono condividere storage con l’host Summary solo con una unione e discriminante provati; la coincidenza temporale non basta. **Non è fissato qui un indirizzo libero per quel blocco.** R5 lascia6016byte totali tra`0x01FF8880` e`0x01FFA000`; Task3 usa la stessa partizione per codice/testi/stato. Dopo la sua review il builder dovrà misurare il residuo reale e allocare wrapper+stato nel budget complessivo, senza padding del gioco o estensione della arena. Se non entra, il gate rimane chiuso; non sommare altri6016byte a Summary.

## Baseline riutilizzabile e prove aperte

Lo script storico `rom-tools/runtime/inputs/newgame-keyboard.script`, SHA-256`f8258ebb9ad39ee52322a9497a455909e59e48a3647e794081e3f11e5491f0c4`, eseguito invariato con `--frames 600` su **entrambi** i r5, raggiunge frame9478 con zero cheat/freezes. Revisione delle immagini native: tastiera e conferma nome con personaggio maschile visibili EN/IT; nella IT si vedono anche gli accenti previsti. Le stesse coordinate della tastiera producono un nome TEST diverso in EN: preparazione deterministica, non un confronto di identità fra lingue. Nessun YES finale selezionato, nessun save inventato/importato.

Queste prove possono riutilizzarsi come baseline di selezione NewGame, primo setup, introduzione originale, genere e tastiera. Non esiste nella r5 un pannello equivalente alla nuova guida: il checkpoint prima di DoMainTask è la baseline per confrontare attesa/skip futuri. La navigazione/attesa/skip della guida non sono testati da questi avvii.

Le prove storiche in `rom-tools/runtime/runtime-results.json` e gli script `boot-save.script`/`cold-reload.script` coprono SAVE/reload di una partita TEST già creata a Borgo Foglianova/New Bark Town, non la prima scrittura ottenuta da questa Nuova partita. Resta da osservare sulla futura candidata e sulla propria baseline: conferma nome→Oak Exit→posizione iniziale→primo SAVE→cold boot da quel save; confronto nome/genere/ID/progressione, uscita B anticipata/completa e nessuna ripetizione dopo naming. Non trasferire savestate fra ROM.

Comandi eseguiti: ndspy/hashlib/struct, clang/llvm-objdump per disassemblaggio privato; observer con `locate.script`, `locate2.script`, `setup.script` e script keyboard storico; parser privato `analyze.py`, `finalize-meta.py`, `write-contract.py`. Due locate EN, due setup EN/IT e due keyboard EN/IT: sei avvii, di cui i locate sono esplorativi. Un comando explorativo col Python di sistema ha fallito per ndspy assente; tutte le analisi ndspy successive hanno usato il venv locale. Originali, quattro hash ROM,39 file storici EVIV/runtime e i tre oggetti/librerie observer riconfermati. Nessun save originale aperto, Git mutation, pubblicazione, GUI, Android o Thor. Solo i tre documenti Task4 nuovi restano non committati; i file sporchi precedenti e Task3 sono di altri lavori.
