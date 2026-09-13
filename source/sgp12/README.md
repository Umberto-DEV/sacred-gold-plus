# sgp12 — libreria consolidata per la ROM Sacred Gold Plus 1.2

Obiettivo: `costruisci.py` riproduce la ROM 1.2 da una base 1.1 con UN comando,
`verifica.py` la ricontrolla con UN comando. **Verificato (SGP-1.2-QUALITA-
STRUMENTI-02, 13/09/2026; esteso da SGP-1.2-INTEGRAZIONE-FINALE-02, 13/09/2026
sera)**: da `base-1.1-{EN,IT}.nds` produce ROM IDENTICHE, sha256 per sha256,
alla ROM DEFINITIVA `$SGP_ROM_DIR/sgp-1.2-{EN,IT}.nds`
(§4) — **con animazioni v4, credito ed etichetta guida spenta** (`b631e2a1…` EN, `f4430300…`
IT; dopo INTEGRAZIONE-FINALE-02 era `0811e8c3…`/`f69154cc…`; prima `f024dbb5…`/`d099d717…`,
con anim v3 e senza credito). Questo pacchetto sostituisce, per la parte INFRASTRUTTURALE
(non per la logica di ogni blocco), le copie duplicate di `arm9.py`,
`overlay_patch.py` e simili che vivevano in ciascun cantiere
`SGP-1.2-*`.

Interprete richiesto: `python3 (vedi source/requirements.txt)`
(ndspy 4.2.0). Nessun file `.nds`/`.sav`/BIOS di questo repo va aperto con
uno strumento di lettura testo: solo script che leggono/scrivono i byte.

## I comandi

```
python3 -m sgp12.costruisci --base base-1.1-EN.nds --uscita sgp-1.2-EN.nds --lingua EN
python3 -m sgp12.costruisci --base base-1.1-IT.nds --uscita sgp-1.2-IT.nds --lingua IT

python3 -m sgp12.verifica sgp-1.2-EN.nds --base base-1.1-EN.nds --lingua EN

python3 -m sgp12.estrai_build --rom sgp-1.2-EN.nds --lingua EN   # rigenera i build canonici (§4b)
```

(da dentro `source/`, con quell'interprete — vedi sopra). `verifica.py`
con `--base`/`--lingua` ricostruisce internamente la ROM e la confronta con
quella data (`costruzione_identica`): è così che verifica una ROM di release
vera senza bisogno di ROM intermedie salvate a parte.

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
→ opzioni → wifi → titolo → credito → guida**.

| blocco | stato | pianta | build in `sgp12/build/` |
|---|---|---|---|
| `riserva.py` | **migrato**, `applica`+`rileggi`, byte-identico | deterministico (nessun blob) | `riserva/MAPPA-RISERVA-ARM9.json` |
| `camera.py` | **migrato**, `applica`+`rileggi`, byte-identico | deterministico (tabella nel codice) | nessuno |
| `plus_chunk.py` | **porta diretta** (non più un adattatore): `applica`+`rileggi` propri, scrivono la pianta v-finale di `sgp.plus`/`sgp.salvataggio` (QUALITA-NATIVO-01, 12/09/2026) | `sgp.plus` 2048 B: blob PLUS 256 B (+0x000), blob SALVATAGGIO 500 B (+0x120, **non più** a +0x630 né in codice a 0x023D8730), tab_trainer/tab_wild/stato/canarino INVARIATI (+0x400/+0x500/+0x600/+0x620); `sgp.salvataggio` 256 B: solo buffer (32 B, zero) + canarino (+0xF0) | `plus/{manifesto.json,blob.bin,salva_blob.bin,tab_trainer.bin,tab_wild.bin,stato.bin,canarino.bin}` + `salvataggio/{manifesto.json,canarino.bin}` — **estratti dalla ROM definitiva** |
| `npc.py` | **migrato**, `applica`+`rileggi`, byte-identico (contenuto v-finale: default npc=1 scritto da D1, contratti registro corretti — B2/B4) | invariata (256 B a 0x023D8900 + canarino a 0x023D8A00) | `npc/{manifesto.json,blob.bin}` — **estratto** |
| `anim.py` | **migrato**, `applica`+`rileggi`; **v4** (SGP-1.2-ANIM-SOLIDO-01, 13/09/2026 sera, da INTEGRAZIONE-FINALE-02): DUE ganci in ov012 (G1 letterale + G2 `BL sgp_idle_stop` a coda di `ov12_02262014`, chiude D1), blob 752 B (era 600, scomparto ora PIENO) | invariata (1024 B a 0x023D8B00), blocco pieno 1024/1024 | `anim/{manifesto.json,blob.bin,tab_u.bin,par.bin,canarino.bin}` — **ri-estratto v4** |
| `opzioni.py` | **migrato** (`applica` porta diretta, pianta v3); `rileggi` **adattatore** verso `rileggi_opzioni_v3.py` | `sgp.opzioni` 4096 B: codice 3628 B (+0x000, era 3348), ris (+0xEC0), tab (+0xF20), tpl (+0xF40), stato (+0xF60), canarino INVARIATO (+0xFF0); `sgp.opzioni.testi` 1024 B invariata | `opzioni/{manifesto.json,ui_blob.bin,testi-{EN,IT}.bin,voci-{EN,IT}.bin}` — **ri-estratti sulla pianta v3** (i vecchi erano TRONCATI: la vecchia estrazione tagliava a 3584 B un codice di 3628, vedi §4c) |
| `wifi.py` | **porta diretta** (v-finale, B5/B6/B8): `applica`+`rileggi` propri | `sgp.wifi` 2048 B: veneer G2/G3 INVARIATI di offset (+0x000/+0x020, 24/28 B, contenuto con manutenzione cache), blob 572 B (+0x250, era 660), gancio G1 ripuntato (+0x47C, era +0x2B5) | `wifi/vfinale/{manifesto.json,blob.bin,veneer-g2.bin,veneer-g3.bin}` — **estratto** (la cartella `wifi/wifi04/` resta per archivio, superata: NON usata da `costruisci.py`) |
| `titolo.py` | **nuovo** (SGP-1.2-TITOLO-01): `applica`+`rileggi`, adattatori verso `applica_titolo.py`/le sue funzioni `cancelli_lettura()`. **+ credito** (SGP-1.2-TITOLO-02, 13/09/2026 sera, da INTEGRAZIONE-FINALE-02): `applica_credito`/`rileggi_credito`, stesso NARC, membro 15 (tile del credito) — `rileggi_credito` usa ndspy, indipendente da `applica_credito.py` | titolo: NARC `a/0/4/6`, membro 0 (tilemap SUB_2): 56 B, `0x011A..0x0135` → `0x0000`. credito: membro 15, 119 B, nibble 12/13 → 14 nei tile usati dalla tilemap 17 | nessuno per entrambi (deterministici, nessun blob) |
| `testi.py` | **adattatore** (la funzione originale è già pura bytes→bytes) | trasformazione di `CORREZIONI.tsv`, non un blocco a indirizzo fisso | `testi/{CORREZIONI.tsv,pret-source/charmap.txt}` — dipendenza esterna, vedi §5 |
| `guida.py` | **nuovo** (SGP-1.2-GUIDA-EVIV-02, 13/09/2026): `applica`+`rileggi` propri, porta diretta di `SGP-1.2-GUIDA-EVIV-02/tools/applica_guida.py`+`rileggi_guida.py`. Spegne l'etichetta automatica "START Guida"/"START Guide" nella pagina ABILITÀ/Dati del Riepilogo (START e il tocco restano funzionanti); non tocca la riserva 1.2, il salvataggio, l'automatismo di Nuova Partita né i numeri EV/IV. **Patch chirurgica, NON ricompilazione**: un primo tentativo ricompilava `combined_guide.c` e sostituiva l'intera regione codice (4752 B) — `hg_runtime` ha trovato che il clang disponibile in questo ambiente produce, per quel file, codice che blocca il gioco premendo START (riprodotto anche ricompilando SENZA alcun taglio: non era il taglio, era la ricompilazione in sé). Scartato: la versione consegnata patcha 96 byte macchina direttamente sul binario spedito | sostituisce 96 B a `0x01FF8A1A` (dentro `guide_main`, IDENTICI EN/IT); nessun trampolino, nessun template Oak, nessuna zona testi toccati — vedi `SGP-1.2-GUIDA-EVIV-02/RAPPORTO.md` §2 per la regressione trovata e scartata | nessuno: blocco deterministico (96 byte fissi nel codice), come `riserva`/`camera` |

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

## 4. Stato della verifica end-to-end (13 settembre 2026) — CHIUSO salvo `guida`

**Nota (13/09/2026, sera, SGP-1.2-GUIDA-EVIV-02)**: `costruisci.py` ora applica anche il blocco
`guida` (ultimo passo, dopo `credito`). Le ROM di lavoro reali
(`$SGP_ROM_DIR/sgp-1.2-{EN,IT}.nds`) **non lo portano ancora** — sono bloccate
da un altro cantiere in corso (INTEGRAZIONE-FINALE-02) e non si potevano toccare qui — quindi
`TestCostruisciIdentico` (sotto) ora fallisce, PER DISEGNO: `costruisci()` da `base-1.1-*` produce
una ROM diversa da quella registrata in `SHA256SUMS` (una riga di codice guida in più). Non è un
difetto da correggere qui: chiude l'orchestratore, dopo aver integrato anche l'altro cantiere,
rieseguendo `costruisci.py` e aggiornando `SHA256SUMS`. Il resto (29/31 test di
`sgp12.test_lib`, incluso il nuovo `TestBloccoGuida`) resta verde.

`costruisci.py` da `base-1.1-EN.nds`/`base-1.1-IT.nds` produce ROM **IDENTICHE,
sha256 per sha256**, alla ROM DEFINITIVA (titolo incluso):

```
EN  base 281c2d68e442479e… → costruita b631e2a10593ad9c…  (== bersaglio, SHA256SUMS)
IT  base 7b61646c627eb67c… → costruita f443030042d17540…  (== bersaglio, SHA256SUMS)

(dopo SGP-1.2-INTEGRAZIONE-FINALE-02 e prima di GUIDA-EVIV-02: EN `0811e8c3…`, IT `f69154cc…`)

(prima di SGP-1.2-INTEGRAZIONE-FINALE-02, 13/09/2026 sera: EN `f024dbb5…`, IT
`d099d717…`, con `sgp.anim` v3 e senza il blocco credito.)
```

Verificato con `python3 -m unittest sgp12.test_lib -v` (`TestCostruisciIdentico`
+ `TestBlocchiVFinale`, un test per blocco EN/IT) e con `python3 -m sgp12.verifica
sgp-1.2-{EN,IT}.nds --base base-1.1-{EN,IT}.nds --lingua {EN,IT}` **sulle due
ROM di lavoro reali** (`costruzione_identica.identico: true`, ogni rilettore
`verde`, `T1_T5` 11/11 verdi con `SGP_RISERVA_COMPLETA=1`).

### 4a. `wifi_slot4` sostituisce `wifi_slot3`, non lo segue

Fatto emerso costruendo la catena WIFI (storia, non più nel percorso di
`costruisci.py`): WIFI-04 non andava applicato DOPO WIFI-02, lo sostituiva.
Con la pianta definitiva questo è superato: `blocchi/wifi.py` scrive
direttamente il blob v-finale (572 B) su un blocco a zero, nessuna catena.

### 4b. `estrai_build.py`: i blob canonici si leggono dalla ROM, non si ricompilano

```
python3 -m sgp12.estrai_build --rom sgp-1.2-EN.nds --lingua EN
python3 -m sgp12.estrai_build --rom sgp-1.2-IT.nds --lingua IT
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
`0985e871…`, non in questo repo). `sgp12/build/testi/pret-source/charmap.txt`
è una copia già estratta, trovata identica (stesso sha256) in due handoff
d'archivio (`the private archive */metadata/pret/`) — non
un file inventato in questa sessione.

## 6. Test

```
cd source
python3 (vedi source/requirements.txt) -m unittest sgp12.test_lib -v
```

Roundtrip BLZ (ottimo e avido, 30 prove casuali + confronto diretto con
l'originale), chunk (roundtrip, CRC corrotto rifiutato, invarianti fuori
dominio), formula del canarino, riserva/camera (applica+rileggi verde,
idempotenza, un mutante per blocco), **`TestBloccoGuida`** (nuovo,
SGP-1.2-GUIDA-EVIV-02: `applica`+`rileggi` verde EN/IT, idempotenza, un
mutante che altera un byte della regione codice, confine delle 4 regioni
scritte), **`TestCostruisciIdentico`** (criterio byte-per-byte contro
`SHA256SUMS`, EN e IT — **ROSSO per disegno** finché l'orchestratore non
integra il blocco `guida`, vedi §4) e **`TestBlocchiVFinale`** (un test per
blocco fra plus_chunk/npc/anim/opzioni/wifi/titolo, `applica`+`rileggi` verde
EN e IT, più l'idempotenza di titolo).

## 7. Cose rimaste (in ordine di valore)

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
