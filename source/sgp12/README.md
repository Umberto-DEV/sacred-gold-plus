# sgp12 — libreria consolidata per la ROM Sacred Gold Plus 1.2.2

Obiettivo: `costruisci.py` riproduce la ROM 1.2.2 dalla propria HeartGold
ORIGINALE con UN comando, `verifica.py` la ricontrolla con UN comando. **Verificato il 13/09/2026**: da
`base-1.1-{EN,IT}.nds` produce ROM IDENTICHE, sha256 per sha256, alla ROM
DEFINITIVA `$SGP_ROM_DIR/sgp-1.2.2-{EN,IT}.nds` (§4) — **con animazioni v4,
credito, etichetta guida spenta, versione in gioco 1.2.2, pagina Opzioni v4,
tetto NPC restituito allo spegnimento, Caramella Rara riutilizzabile, doni a pila piena e moto continuo in lotta** (`82db6c33…` EN, `de5485b0…` IT; la 1.2 era `b631e2a1…`/`f4430300…`). Questo pacchetto sostituisce, per la parte INFRASTRUTTURALE
(non per la logica di ogni blocco), le copie duplicate di `arm9.py`,
`overlay_patch.py` e simili che vivevano in ciascun cantiere
`SGP-1.2-*`.

Interprete richiesto: `python3 (vedi source/requirements.txt)`
(ndspy 4.2.0). Nessun file `.nds`/`.sav`/BIOS di questo repo va aperto con
uno strumento di lettura testo: solo script che leggono/scrivono i byte.

## I comandi

```
python3 -m sgp12.scarica_base --destinazione "$SGP_ROM_DIR"   # una volta sola, stadio 0

python3 -m sgp12.costruisci --base "$SGP_ROM_DIR/Pokemon - HeartGold Version.nds" --uscita sgp-1.2.2-EN.nds
python3 -m sgp12.costruisci --base "$SGP_ROM_DIR/Pokemon - Versione Oro HeartGold.nds" --uscita sgp-1.2.2-IT.nds

python3 -m sgp12.verifica sgp-1.2.2-EN.nds --base "$SGP_ROM_DIR/Pokemon - HeartGold Version.nds"

python3 -m sgp12.estrai_build --rom sgp-1.2.2-EN.nds --lingua EN   # rigenera i build canonici (§4b)
```

(da dentro `source/`, con quell'interprete — vedi sopra). `--lingua` non serve
piu': la dice lo sha256 di `--base`, e se la si passa deve coincidere.
`verifica.py` con `--base` rifa' lo stesso percorso del costruttore, stadio 0
compreso, e confronta il risultato con la ROM data (`costruzione_identica`): è
così che verifica una ROM di release vera senza bisogno di ROM intermedie
salvate a parte.

## Lo stadio 0 (`base11.json`, `rom.prepara_base`, `scarica_base.py`)

I diciassette blocchi partono da una base 1.1, che fino alla 1.2.2 era un
artefatto intermedio che chi ricostruiva doveva gia' possedere. Ora e' il
costruttore a ricavarla, come PRIMO stadio, dalla HeartGold originale piu' un
delta xdelta pubblico (asset della release `base-1.1`). Il delta contiene solo
DIFFERENZE: non e' una ROM e senza la HeartGold della sua lingua non serve a
niente. Nessuna ROM e' distribuita da questo repository.

| pezzo | cosa fa |
|---|---|
| `base11.json` | il pin TRACCIATO: per EN e IT, sha256+byte della HeartGold accettata, nome/sha256/byte/URL del delta, sha256+byte della base 1.1 che ne deve uscire, e le opzioni di decodifica (`-d -D -R -s`, quelle del manifest 1.1) |
| `rom.classifica_base(sha)` | funzione PURA: `originale` / `base-1.1` / `sconosciuta`, e la lingua. E' la regola che decide se lo stadio 0 serve, si salta o rifiuta, e si prova senza una ROM |
| `rom.prepara_base(percorso, ...)` | lo stadio 0: riconosce, cerca il delta (`--delta` o `$SGP_ROM_DIR`), ne verifica lo sha256, lo applica con `xdelta3` in una cartella temporanea, verifica lo sha256 dell'uscita. Tre impronte, tre cancelli; una sola che non torna e' un `Rifiuto` |
| `scarica_base.py` | l'UNICO punto di rete del repository, opt-in: scarica i delta e il `SHA256SUMS` della release (deposto come `SHA256SUMS-base-1.1`, per non coprire quello delle ROM), verifica, e cancella cio' che non combacia |
| `test_base11.py` | 45 test di CLASSE A: pin, riconoscimento, ogni rifiuto, e `scarica_base` contro un `http.server` locale. Nessuna ROM, nessuna rete, nessun `xdelta3` vero (pin sintetico e decodificatore finto) |

Senza `xdelta3` nel PATH il rifiuto dice quali pacchetti installare
(`brew install xdelta`, `sudo apt install xdelta3`). Una base 1.1 passata
direttamente a `--base` resta accettata: lo stadio 0 si salta con un avviso.

## 1. La libreria (moduli in cima, non per blocco)

| modulo | cosa consolida | da |
|---|---|---|
| `rom.py` | `Arm9` (indirizzo RAM → offset file dell'ARM9) e `Rom` (header/FAT/tabella overlay), `sha`, `crc16`, `Rifiuto`/`esigi`, `bl_decode`/`bl_thumb` | 12 copie identiche di `tools/arm9.py` + la classe `Rom` di `overlay_patch.py` (altre 5 copie identiche) |
| `blz.py` | codec BLZ: `blz_decomprimi` (decoder A, all'indietro in luogo) e `blz_comprimi_ottimo` (analisi ottima, cammino minimo sui token) | `SGP-1.2-OVERLAY-01/tools/overlay_patch.py` (805 righe, 6 copie identiche) |
| `overlay.py` | `applica()`: patch di byte dentro un overlay compresso, con guardia per contenuto e ricompressione in luogo | idem |
| `chunk.py` | formato del chunk di salvataggio pubblico (0x023D8710, 16 B) e del footer su disco (settore 47/111) | `SGP-1.2-PLUS-03/CONTRATTO-CHUNK.md` (prima: nessun formato eseguibile, solo la tabella nel documento) |
| `riserva.py` | **solo** l'infrastruttura meccanica: lettura delle sezioni di autoload (`ndspy.code`) e la formula del canarino | vedi §3 sotto: NON la fingerprint del manifest |

Verificato in questa sessione, non solo dichiarato: `blz.py` produce output
BYTE PER BYTE identico all'originale su 30 prove casuali + 2 algoritmi
(ottimo e avido); `rom.py`/`overlay.py` producono lo stesso sha256
dell'originale applicando una patch reale sulla ROM base vera.

## 2. I blocchi (`blocchi/`) — pianta DEFINITIVA (13/09/2026)

Ordine di costruzione: **riserva → camera → plus+chunk → testi → npc → anim
→ opzioni → wifi → titolo → credito → guida → caramelle → borsa → anim2 → borsa_lotta → squadra_lotta → capacita_borsa**.
Quindici blocchi. `borsa` compone ripristino dei premi, messaggio, appendici
e ganci ARM9: le chiavi dei siti si calcolano dopo le appendici. `anim2`
aggiorna i ganci di lotta dopo il blocco `anim` originale, che resta in riserva.

| blocco | stato | pianta | build in `sgp12/build/` |
|---|---|---|---|
| `riserva.py` | **migrato**, `applica`+`rileggi`, byte-identico | deterministico (nessun blob) | `riserva/MAPPA-RISERVA-ARM9.json` |
| `camera.py` | **migrato**, `applica`+`rileggi`, byte-identico | deterministico (tabella nel codice) | nessuno |
| `plus_chunk.py` | **porta diretta** (non più un adattatore): `applica`+`rileggi` propri, scrivono la pianta v-finale di `sgp.plus`/`sgp.salvataggio` (QUALITA-NATIVO-01, 12/09/2026) | `sgp.plus` 2048 B: blob PLUS 256 B (+0x000), blob SALVATAGGIO 500 B (+0x120, **non più** a +0x630 né in codice a 0x023D8730), tab_trainer/tab_wild/stato/canarino INVARIATI (+0x400/+0x500/+0x600/+0x620); `sgp.salvataggio` 256 B: solo buffer (32 B, zero) + canarino (+0xF0) | `plus/{manifesto.json,blob.bin,salva_blob.bin,tab_trainer.bin,tab_wild.bin,stato.bin,canarino.bin}` + `salvataggio/{manifesto.json,canarino.bin}` — **estratti dalla ROM definitiva** |
| `npc.py` | **migrato**, `applica`+`rileggi`, byte-identico (contenuto v-finale: default npc=1 scritto da D1, contratti registro corretti — B2/B4). **1.2.1**: blob RICOMPILATO dai sorgenti spediti con la correzione M2 della revisione R2 — spegnere la fluidità restituisce al gioco il tetto che gli era stato tolto (`st->salvato`, che era scritto e mai letto) invece di aspettare il cambio di mappa. Blob 128 → 144 B, `sgp_npc_hook` 0x023D8971 → 0x023D8981, BL in ov001 riscritta | invariata (256 B a 0x023D8900 + canarino a 0x023D8A00) | `npc/{manifesto.json,blob.bin}` — **ricompilato** (1.2.1; fino alla 1.2 era un estratto) |
| `anim.py` | **migrato**, `applica`+`rileggi`; **v4** (SGP-1.2-ANIM-SOLIDO-01, 13/09/2026 sera, da INTEGRAZIONE-FINALE-02): DUE ganci in ov012 (G1 letterale + G2 `BL sgp_idle_stop` a coda di `ov12_02262014`, chiude D1), blob 752 B (era 600, scomparto ora PIENO) | invariata (1024 B a 0x023D8B00), blocco pieno 1024/1024 | `anim/{manifesto.json,blob.bin,tab_u.bin,par.bin,canarino.bin}` — **ri-estratto v4** |
| `opzioni.py` | **migrato** (`applica` porta diretta, pianta v3); `rileggi` **adattatore** verso `rileggi_opzioni_v3.py`. **1.2.1**: blob v4, correzione A1 della revisione R2 — `opz_presente` applica a OGNI voce la precondizione del chunk di D1 (guardia + `load_status` ASSENTE o VALIDO), non solo alle due di D1; con un chunk RIFIUTATO o mai letto le voci anim/NPC/Wi-Fi non si lasciano più confermare. +4 B, i sette simboli che finiscono in ROM si spostano. **1.2.2 aggiornata (19/09/2026)**: blob v5 — la riga «SELECT → PLUS» del menu Opzioni si ridisegna a ogni ingresso perché `opz_suggerimento` legge la cella (0,22) della tilemap di MAIN_1 invece del flag `sugg` (che sopravviveva all'app Opzioni, rinata allo stesso indirizzo di heap); le tre Window sullo stack azzerano `pixels` prima di `AddWindowParameterized`. +32 B | `sgp.opzioni` 4096 B: codice 3664 B (+0x000; v4 3632, v3 3628, v2 3348), ris (+0xEC0), tab (+0xF20), tpl (+0xF40), stato (+0xF60), canarino INVARIATO (+0xFF0); `sgp.opzioni.testi` 1024 B invariata | `opzioni/{manifesto.json,ui_blob.bin,testi-{EN,IT}.bin,voci-{EN,IT}.bin}` — **ri-estratti sulla pianta v3** (i vecchi erano TRONCATI: la vecchia estrazione tagliava a 3584 B un codice di 3628, vedi §4c) |
| `wifi.py` | **porta diretta** (v-finale, B5/B6/B8): `applica`+`rileggi` propri | `sgp.wifi` 2048 B: veneer G2/G3 INVARIATI di offset (+0x000/+0x020, 24/28 B, contenuto con manutenzione cache), blob 572 B (+0x250, era 660), gancio G1 ripuntato (+0x47C, era +0x2B5) | `wifi/vfinale/{manifesto.json,blob.bin,veneer-g2.bin,veneer-g3.bin}` — **estratto** (la cartella `wifi/wifi04/` resta per archivio, superata: NON usata da `costruisci.py`) |
| `titolo.py` | **nuovo** (SGP-1.2-TITOLO-01): `applica`+`rileggi`, adattatori verso `applica_titolo.py`/le sue funzioni `cancelli_lettura()`. **+ credito** (SGP-1.2-TITOLO-02, 13/09/2026 sera, da INTEGRAZIONE-FINALE-02): `applica_credito`/`rileggi_credito`, stesso NARC, membro 15 (tile del credito) — `rileggi_credito` usa ndspy, indipendente da `applica_credito.py` | titolo: NARC `a/0/4/6`, membro 0 (tilemap SUB_2): 56 B, `0x011A..0x0135` → `0x0000`. credito: membro 15, 119 B, nibble 12/13 → 14 nei tile usati dalla tilemap 17 | nessuno per entrambi (deterministici, nessun blob) |
| `testi.py` | **adattatore** (la funzione originale è già pura bytes→bytes) | trasformazione di `CORREZIONI.tsv`, non un blocco a indirizzo fisso | `testi/{CORREZIONI.tsv,pret-source/charmap.txt}` — dipendenza esterna, vedi §5 |
| `guida.py` | **nuovo** (SGP-1.2-GUIDA-EVIV-02, 13/09/2026): `applica`+`rileggi` propri, porta diretta di `SGP-1.2-GUIDA-EVIV-02/tools/applica_guida.py`+`rileggi_guida.py`. Spegne l'etichetta automatica "START Guida"/"START Guide" nella pagina ABILITÀ/Dati del Riepilogo (START e il tocco restano funzionanti); non tocca la riserva 1.2, il salvataggio, l'automatismo di Nuova Partita né i numeri EV/IV. **Patch chirurgica, NON ricompilazione**: un primo tentativo ricompilava `combined_guide.c` e sostituiva l'intera regione codice (4752 B) — `hg_runtime` ha trovato che il clang disponibile in questo ambiente produce, per quel file, codice che blocca il gioco premendo START (riprodotto anche ricompilando SENZA alcun taglio: non era il taglio, era la ricompilazione in sé). Scartato: la versione consegnata patcha 96 byte macchina direttamente sul binario spedito | sostituisce 96 B a `0x01FF8A1A` (dentro `guide_main`, IDENTICI EN/IT); nessun trampolino, nessun template Oak, nessuna zona testi toccati — vedi `SGP-1.2-GUIDA-EVIV-02/RAPPORTO.md` §2 per la regressione trovata e scartata | nessuno: blocco deterministico (96 byte fissi nel codice), come `riserva`/`camera` |
| `caramelle.py` | **nuovo** (1.2.1, da SGP-1.2-CARAMELLE-01): `applica`+`rileggi` propri, e il `rileggi` è di un'ALTRA famiglia (vista sull'ARM9 scritta a mano con `struct`, BL decodificata con capstone, ogni indirizzo ridichiarato). Dopo l'uso di una Caramella Rara dal menu squadra si RESTA nel menu, salvo che ci sia un'evoluzione in coda: in quel caso si esce come il vanilla. Nove cancelli in scrittura (G0 idempotenza, G2 zona, G3 preimmagini, G4 motivo unico nell'ARM9 statico, G5 invarianti della 1.1, G6/G7/G8 controlli positivi e conteggio) | `sgp.caramelle` 256 B a 0x023DAC00: blob Thumb 192 B (+0x000, su 240) + canarino `0xCA5A1600|i` (+0x0F0); **più** 6 B nell'ARM9 statico a 0x02081E96 (BL + `pop {r3,r4,r5,pc}`) | `caramelle/{manifesto.json,blob.bin,canarino.bin,origine.json}` — **compilato**, non estratto: la 1.2.1 è la prima ROM in cui questi byte esistono |
| `borsa.py` | Doni gratuiti e raccolte al tetto, messaggio con nome; acquisti e scambi invariati. Quattro sottorilettori indipendenti. | `sgp.borsa`, 2048 B a `0x023DAD00`, più due voci della tabella comandi e modifiche mirate agli script/testi | `borsa/`: blob e canarino compilati dai sorgenti |
| `anim2.py` | Moto v5 sui lottatori, continuo nei menu e sospeso durante le mosse; spento per default | `sgp.anim2`, 2048 B a `0x023DB500`, più quattro finestre in ov012 | `anim2/`: codice, tavola, parametri, siti e canarino |
| `borsa_lotta.py` | Riusa la cache ItemData della battaglia durante la costruzione della Borsa; OFF segue il getter originale | `sgp.borsa_lotta`, 256 B a `0x023DBD00`, un BL in ov008 | `borsa_lotta/`: codice e canarino, senza dati o immagini di gioco |
| `squadra_lotta.py` | Riusa la MoveTbl della battaglia nella scansione Squadra; OFF conserva i getter originali | `sgp.squadra_lotta`, 256 B a `0x023DBE00`, cinque BL in ov008 | `squadra_lotta/`: codice e canarino; [misure e limiti](../features/squadra-lotta/README.md) |
| `capacita_borsa.py` | Tasca principale 252 slot e pagine complete in tutte le tasche; estensione save associata alla generazione nativa | `sgp.capacita_borsa`, 11264 B a `0x023DBF00`; stato a `0x023DD700`, 15 hook ARM9 e layout ov015 | `capacita_borsa/`: codice compilato e provenienza; [contratto e prove](../features/capacita-borsa/README.md) |

**Cantieri scartati per duplicazione letterale** (stesso `shasum`, non solo
"stessa idea"): NPC-03 ≡ NPC-02, ANIM-B-03 ≡ ANIM-B-02, WIFI-05 ≡ WIFI-04
(intere cartelle `tools/`, `diff -rq` senza output). LINGUA-05 e OPZIONI-05
non hanno un applicatore proprio: sono cantieri di sola riverifica.
**Superati dalla pianta definitiva** (non più applicati da `costruisci.py`):
WIFI-02/03/04/05 (blob v2, sostituito dal v-finale di QUALITA-NATIVO-01),
OPZIONI-01..05 (pagina v2, sostituita dalla v3 di RIFINITURA-01), il blob PLUS
di PLUS-01/02 e il blob SALVATAGGIO di PLUS-03 (sostituiti dal v-finale).

## 3. Perché `riserva.py`/`camera.py`/`npc.py` NON condividono la fingerprint col loro `applica()`

`SGP-1.2-RISERVA-01/tools/rileggi_riserva12.py` lo dice esplicitamente:
*"Non importa `applica_riserva12.py` [...] Se applicatore e rilettore
condividessero una costante sbagliata la prova sarebbe nulla — sono due file
per questo"* (`02-COME-LAVORARE.md §2.3`). `blocchi/riserva.py` ha DUE
funzioni per la fingerprint del manifest, digitate separatamente;
`blocchi/camera.py::rileggi` cammina l'ARM9 con una classe `_Immagine`
propria, non `sgp12.rom.Arm9`; `blocchi/npc.py::rileggi` ha un `_Arm9RO` e un
decoder BLZ "in avanti" propri, di famiglia diversa dal decoder "all'indietro
in luogo" di `sgp12.blz`.

**Limite dichiarato di questo cantiere (QUALITA-STRUMENTI-02)**: i rilettori
NUOVI scritti qui (`plus_chunk.rileggi`, `wifi.rileggi`, `anim.rileggi`)
RIUSANO `sgp12.rom.Arm9`/`bl_decode` invece di una famiglia di decoder
indipendente — non hanno la stessa proprietà diagnostica di
riserva/camera/npc (un bug in `sgp12.rom` non verrebbe scoperto da questi tre
rilettori). Restano comunque **indipendenti dalla LOGICA** di `applica()`
(ridecodificano tutto da zero, non riusano nessuno stato prodotto da
`applica()`), e sono onesti su questo compromesso, non taciuto. `opzioni.rileggi`
non ha questo limite: è un adattatore verso `rileggi_opzioni_v3.py`
(famiglia di decoder propria, mai condivisa con `sgp12`). `titolo.rileggi`
idem: adattatore verso le funzioni di lettura di `applica_titolo.py`, che
sono già indipendenti dalla sua funzione di scrittura.

## 4. Stato della verifica end-to-end (13 settembre 2026) — CHIUSO

`costruisci.py` da `base-1.1-EN.nds`/`base-1.1-IT.nds` produce ROM **IDENTICHE,
sha256 per sha256**, alla ROM DEFINITIVA (quattordici blocchi, Borsa e moto continuo inclusi):

```
EN  base 281c2d68e442479e… → costruita 82db6c33264598c8…  (== bersaglio, SHA256SUMS)
IT  base 7b61646c627eb67c… → costruita de5485b0ed93d487…  (== bersaglio, SHA256SUMS)
```

(la 1.2 era EN `b631e2a1…` / IT `f4430300…`; prima di GUIDA-EVIV-02 EN `0811e8c3…` / IT `f69154cc…`)

`sgp12.test_lib` gira 57 test: **tutti verdi**, `TestCostruisciIdentico` incluso.
(erano 37: la revisione R1 ha aggiunto `TestOverlayFlag`, cinque prove di classe A
sul bit «compresso» della voce y9, e `TestMappaRiserva`, che pretende che le due
copie del registro della riserva — quella di `build/` e quella pubblica di
`docs/` — siano la stessa cosa. Da 50 a 57 con la revisione della 1.2.1:
`TestManifestoDescriveIlBlob`, sei prove di classe A sulla regola unica «il
manifesto descrive il blob che gli sta accanto» — che prima era scritta sei
volte con sei severità diverse — e un settimo test di classe B che pretende che
`features/caramelle/tools/applica_caramelle.py` e
`sgp12.blocchi.caramelle.applica` producano la STESSA ROM, byte per byte.)
`BERSAGLIO` in `test_lib.py` è la costante che nomina la ROM attesa dentro
`$SGP_ROM_DIR`: si aggiorna a ogni release, non si aggira.

Verificato con `python3 -m unittest sgp12.test_lib -v` (`TestCostruisciIdentico`
+ `TestBlocchiVFinale`) e con `python3 -m sgp12.verifica sgp-1.2.2-{EN,IT}.nds
--base base-1.1-{EN,IT}.nds --lingua {EN,IT}` **sulle due
ROM di lavoro reali** (`costruzione_identica.identico: true`, ogni rilettore
`verde`, `T1_T5` 11/11 verdi). T3 legge i file di cheat spediti: senza
`SGP_CHEATS` li cerca in `release/1.2.2/`, cioè dove li lascia l'esportazione.

### 4a. `wifi_slot4` sostituisce `wifi_slot3`, non lo segue

Fatto emerso costruendo la catena WIFI (storia, non più nel percorso di
`costruisci.py`): WIFI-04 non andava applicato DOPO WIFI-02, lo sostituiva.
Con la pianta definitiva questo è superato: `blocchi/wifi.py` scrive
direttamente il blob v-finale (572 B) su un blocco a zero, nessuna catena.

### 4b. `estrai_build.py`: i blob canonici si leggono dalla ROM, non si ricompilano

```
python3 -m sgp12.estrai_build --rom sgp-1.2.2-EN.nds --lingua EN
python3 -m sgp12.estrai_build --rom sgp-1.2.2-IT.nds --lingua IT
```

Per ogni blocco con un blob a indirizzo fisso (npc, anim, opzioni, plus,
salvataggio, wifi — non riserva/camera, deterministici, non titolo,
deterministico anch'esso, non testi, che è una trasformazione di
`CORREZIONI.tsv`), legge dalla ROM canonica DATA i byte esatti del blob e —
dove decodificabile in modo univoco — il bersaglio delle patch overlay/ARM9
(una `BL` Thumb si decodifica con `sgp12.rom.bl_decode`), e li scrive in
`sgp12/build/<blocco>/`. Un manifesto già presente in quella cartella viene
FUSO, non sostituito.

**Aggiornamento QUALITA-STRUMENTI-02**: la pianta definitiva ha spostato
`sgp_wild_hook`/`sgp_gancio_carica`/`sgp_gancio_salva` DENTRO `sgp.plus`
(prima uno era in ov002 non decodificato dal primo applicatore, gli altri due
in un blocco separato): `estrai_plus` ora li decodifica TUTTI direttamente
dalla ROM definitiva — nessun simbolo "preservato" da un manifesto vecchio,
il problema del §4b originale (due applicatori in catena, target intermedio
non decodificabile) non esiste più con la scrittura in un solo passo.

### 4c. `opzioni`: la vecchia estrazione era TRONCATA, non solo superata

`estrai_opzioni` è generica (guidata da `blocchi.opzioni.PIANTA`): prima di
questo cantiere quel dizionario aveva ancora i confini v2 (`codice` tagliato a
3584 B), mentre la ROM conteneva già il codice v3 (3628 B, applicato in luogo
da RIFINITURA-01): `ui_blob.bin` estratto era TAGLIATO agli ultimi 44 byte, e
`tab`/`tpl`/`stato` leggevano dentro il codice vero (bytes di istruzioni
scambiati per un puntatore). Aggiornare `PIANTA` (5 offset, vedi
`blocchi/opzioni.py`) e ri-eseguire `estrai_build.py` risolve per intero: le
letture dipendono TUTTE da quel dizionario.

## 5. Dipendenza esterna del blocco testi

`applica_testi.py::apply_to_rom_bytes` legge `pret_source/charmap.txt`, che
viene da un checkout esterno di `pret/pokeheartgold` (commit
`0985e8718df4f25e64d6507d89c0c97c0d288981`, non in questo repository e non
redistribuito). Si indica con `SGP_PRET_SOURCE=<checkout>`, oppure si mette una
copia in `sgp12/build/testi/pret-source/`, che non è tracciata.

Se il file manca, il blocco RIFIUTA dicendo che cosa manca e come si rimedia, e
i test di classe B che ne dipendono SALTANO con lo stesso messaggio: prima erano
dodici `FileNotFoundError` a metà catena (E5 della revisione R3).

## 6. Test

```sh
cd source
../.venv/bin/python -m unittest sgp12.test_lib -v
```

(l'interprete è quello del venv creato alla radice con `source/requirements.txt`;
la riga qui sopra portava un rimando in prosa lasciato dentro il comando.)

Roundtrip BLZ (ottimo e avido, 30 prove casuali + confronto diretto con
l'originale), chunk (roundtrip, CRC corrotto rifiutato, invarianti fuori
dominio), formula del canarino, riserva/camera (applica+rileggi verde,
idempotenza, un mutante per blocco), **`TestBloccoGuida`** (nuovo,
SGP-1.2-GUIDA-EVIV-02: `applica`+`rileggi` verde EN/IT, idempotenza, un
mutante che altera un byte della regione codice, confine delle 4 regioni
scritte), **`TestCostruisciIdentico`** (criterio byte-per-byte contro
`SHA256SUMS`, EN e IT — verde, vedi §4) e **`TestBlocchiVFinale`** (un test per
blocco fra plus_chunk/npc/anim/opzioni/wifi/titolo, `applica`+`rileggi` verde
EN e IT, più l'idempotenza di titolo).

## 6a. Limite noto dei canarini: due coppie condividono il motivo

Misurato sui blob spediti (revisione R1, M9):

| regione | indirizzo | motivo |
|---|---|---|
| `canarino.npc` | `0x023D8A00` | `0xCA5A1300` |
| `sgp.salvataggio +0xF0` | `0x023D8FF0` | **`0xCA5A1300`** |
| `sgp.anim +0x2F0` | `0x023D8DF0` | `0xCA5A1400` |
| `sgp.opzioni +0xFF0` | `0x023D9FF0` | **`0xCA5A1400`** |

Due guardie con lo stesso motivo non distinguono le due regioni: `npc.rileggi` L5
e `plus_chunk.rileggi` L6 resterebbero entrambi verdi se i due guardiani da 16 B
fossero scambiati o scritti all'indirizzo dell'altro; idem per anim e opzioni.
Le guardie fanno ancora il lavoro principale (uno sfondamento cambia le parole e
il controllo nomina un blocco), ma non dicono *quale* dei due.

Non si corregge qui: cambiare quei sedici byte a quattro indirizzi dentro la
riserva cambia la ROM, e questa è una release che deve ricostruirsi byte per
byte. **Da chiudere nella 1.3**, insieme alla revisione dei motivi. Lo stesso
limite è scritto in `source/docs/arm9-reserve-map.md`, §Canaries.

## 7. Cose rimaste (in ordine di valore)

0. I canarini duplicati di §6a (1.3).
1. Dare a `plus_chunk.rileggi`/`wifi.rileggi`/`anim.rileggi` una famiglia di
   decoder indipendente da `sgp12.rom` (vedi §3: oggi condividono `Arm9`/
   `bl_decode` con l'`applica()` che verificano — limite dichiarato, non
   nascosto).
2. Un mutante per ciascuno dei blocchi ancora senza (`npc`, `anim`,
   `opzioni`, `wifi`, `plus_chunk`, `titolo`, `testi`) — oggi hanno solo
   applica+rileggi verde, non un caso rotto verificato rifiutato.
3. Portare `testi.py` da adattatore a modulo che usa `sgp12.rom`/
   `sgp12.overlay` (nessuna copia di `arm9.py` coinvolta, ma la funzione
   originale resta esterna).
4. `wifi/wifi04/` (build della pianta v2, superata) potrebbe essere tolta da
   `sgp12/build/`: non serve più a nessun blocco, resta solo come storia di
   `estrai_build.py` prima di questo cantiere.
