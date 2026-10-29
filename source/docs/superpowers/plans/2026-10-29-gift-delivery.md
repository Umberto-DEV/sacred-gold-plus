# Consegna sicura di Pokémon e uova Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consegnare regali e uova ai box quando la squadra è piena, preservando interamente ricompense, lettere, costi, personalizzazioni ed eventi in caso di fallimento.

**Architecture:** Un servizio comune prepara uno o due Pokémon temporanei, personalizza e nomina prima dell'inserimento, poi esegue una consegna atomica con destinazioni esplicite. Adattatori per evento e costruttori speciali condividono il servizio; nessuna modifica globale a PartyCount o Party_AddMon. Script e nativi sono applicati da `sgp131` con preimage e rilettura indipendente.

**Tech Stack:** Python/ndspy, decoder script pubblico già presente, C Thumb, Unicorn, task e naming nativi HGSS.

**Spec:** [Master](2026-10-29-mechanics-1.3.1.md), [proposta](../../mechanics-1.3.1-proposal.md). Prerequisiti: banco, riserva e box/comandi accettati. Pattern esistenti: `source/sgp13/mew.py`, `test_mew.py`, `test_mew_rom.py`, `source/features/borsa/tools/scr_disasm.py`.

## Global Constraints

Tutti i vincoli del master. Destinazioni: squadra prima, poi primo box libero partendo dal box attivo con scansione ciclica. Massimo due destinatari per singola operazione. Kenya in overflow: Pokémon senza lettera allegata al box e lettera integra nella Casella Posta; se una delle due destinazioni manca, rifiutare tutto. Nessun journal persistente nuovo. Ritiro Pensione, scambi, starter iniziale e altre catture speciali mantengono la loro semantica, con prove negative esplicite.

## Review Focus

Una coppia con un solo posto libero deve restare interamente pendente; lettere e payload Dono Segreto devono sopravvivere al rifiuto; Aprijuice e metadati modificati dall'inserimento nativo devono essere ripristinati dopo un fallimento; variabili script ancora vive non possono essere usate come scratch; flag impostati prima della consegna non possono consumare il regalo. Ogni rischio ha test nei task 1–5.

## Task 1: censimento rigoroso, dispatch e riparazioni circoscritte

**Files:** Create `source/sgp131/gifts_audit.py`, `gifts_scripts.py`, `test_gifts_audit.py`, `test_gifts_scripts.py`, `test_gifts_audit_rom.py`, `data/gifts-claims.json`, `data/gifts-native-guards.json`; Modify snapshot/runner/manifest.

**Interfaces:** `audit_rom(data: bytes, language: str, commands: object) -> dict`, `require_complete_audit(receipt: dict) -> None`; `patch_member(raw: bytes, language: str, member_id: int, commands: object, recipe: dict) -> bytes`, `verify_member(before: bytes, after: bytes, commands: object, recipe: dict) -> dict`.

- [ ] Eseguire audit originale EN/IT: tabella corrente `0x020FAD00`, conteggio853, opcode78 consuma un solo halfword; il dispatch rifiuta2009. Le sei code malformate sono nei membri225/232/243/246/938/962. Registrare CFG, ogni ingresso/uscita, comandi regalo e associazioni a personaggi/eventi; non soltanto il numero di comandi riconosciuti.
- [ ] Scrivere `test_opcode2009_rejected_without_fake_metadata`, `test_native_fanfare_width_and_dispatch_count`, `test_each_ribbon_tail_maps_all_incoming_edges`, `test_branch_into_replaced_interior_refuses`, `test_all_entries_movements_and_cross_calls_survive`, `test_every_delivery_has_claim_or_unchanged_reason`. Eseguire `PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_gifts_audit sgp131.test_gifts_scripts -v` e osservare RED specifico.
- [ ] Per ciascuna coda fiocco confrontare ribbon, flag giornaliero, messaggi e continuazioni con il corrispondente riferimento nativo. Preparare una sostituzione minima del tratto errato con mappa degli ingressi, senza importare l'intero script retail, cancellare l'interazione o cambiare il decoder. Se un'associazione non è dimostrata, audit nonzero con sito preciso e nessun output parziale.
- [ ] Implementare una sola trasformazione delle coordinate originarie per entrypoint e ogni operando relativo script/movement. Rifiutare target interni non mappati, regioni sovrapposte e istruzioni raggiungibili sconosciute. Conservare dati opachi, movimenti e byte fuori dai tratti sostituiti/relocati. Pin alla candidata del corretto stadio, incluso membro858 già modificato da Training.
- [ ] Sul prima richiedere sei errori noti e ammissione rifiutata; sul dopo zero errori, tracce fiocco/flag/messaggio/uscita corrette, stesso inventario regali prima della loro conversione. Provare scene fiocco tramite input normali su copie dei save, oltre alla traccia controllata. Eseguire `PYTHONPATH=source SGP_GIFT_REQUIRE_INPUTS=1 .venv/bin/python -m unittest sgp131.test_gifts_audit_rom -v`, con EN/IT richiesti e nessuno skip obbligatorio.
- [ ] Revisionare e accettare separatamente questa riparazione preliminare con il protocollo comune; commit `Audit gift control flow and repair guarded ribbon tails`, push `main`.

## Task 2: capacità e consegna atomica

**Files:** Create `source/features/gift-delivery/gifts.h`, `capacity.c`, `transaction.c`, `test/test_capacity.py`, `test/test_transaction.py`, `test/test_transaction_arm.py`, `test/test_native_storage.py`; Extend `source/sgp131/gifts.py` come installatore di prova, builder, snapshot, runner e manifest.

**Interfaces:**

```c
enum SgpGiftStatus { OK=0, NO_SPACE=1, NO_MAIL_SPACE=2, NO_PAYMENT=3,
 NO_MEMORY=4, STALE=5, INVALID=6, STORAGE_BLOCKED=7, INSERT_FAILED=8 };
enum SgpGiftDestinationKind { NONE=0, PARTY=1, PC=2 };
typedef struct { u8 kind, party_index, box, slot; } SgpGiftDestination;
typedef struct { u16 status; u8 count, reserved;
 SgpGiftDestination destinations[2]; } SgpGiftResult;
typedef struct { u8 party_count, active_box; u8 occupied[18][30]; } SgpGiftCapacity;
typedef struct { u8 count, reserved[3]; SgpGiftDestination destinations[2]; } SgpGiftPlan;
int sgp_gift_plan(const SgpGiftCapacity *, u8 count, SgpGiftPlan *);
int sgp_gift_commit(const SgpGiftNativeApi *, void *context,
                   SgpGiftPrepared *, SgpGiftResult *);
```

`SgpGiftPrepared` in `gifts.h` possiede due record nativi allineati da236byte, identità/argomenti risolti, piano effetti e ripristino, risultato e fase. Cap dell'owner **8192byte**, verificato da static assert ARM e host; nessuna copia dell'intero PC/save. `SgpGiftNativeApi` ha `recheck(context, prepared)->status`, `snapshot(context, prepared)->status`, `insert(context, destination, pokemon)->int`, `restore(context, prepared)->void`, `effects(context, prepared)->void`. Status OK è0; solo `insert` usa BOOL nativo, successo1 e fallimento0. Ultime due operazioni non allocano, non sospendono e non possono fallire: un effetto fallibile deve essere completato in preparazione su dati temporanei, lasciando al commit solo scritture dimostrate infallibili; altrimenti quel claim non è ammissibile con questa ABI.

- [ ] Scrivere test per squadra4/5/6, uno/due destinatari, box attivo pieno, altri box liberi, wrap17→0, ultimo slot e PC pieno. Per coppie: squadra4+PC0 sì; squadra5+PC0 no; squadra5+PC1 sì; squadra6+PC1 no; squadra6+PC2 sì. Rifiutare capacità corrotte e il sentinel `NUM_BOXES=18` come falso posto libero.
- [ ] Scrivere fault injection per allocazione/snapshot/primo e secondo inserimento, capacità cambiata e payload corrotto. Ogni rifiuto lascia count risultato0, destinazioni NONE, Pokémon e owner byte-identici e nessun effetto. Eseguire `PYTHONPATH=source .venv/bin/python -m unittest discover -s source/features/gift-delivery/test -p 'test_transaction*.py' -v` e `test_capacity.py`: RED specifico.
- [ ] Implementare pianificazione pura e commit: recheck → snapshot completo → inserimenti senza yield → effetti dopo l'ultimo successo; su fallimento ripristinare tutti gli owner. Includere PartyExtra/Aprijuice: Party_AddMon azzera cinque byte del modificatore nello slot inserito. Conservare preimage anche degli slot PC vuoti con dati residui e maschera box modificati. Corruzione è occupazione/rifiuto, mai autorizzazione a sovrascrivere.
- [ ] Eseguire host e ARM, poi `SGP_GIFT_REQUIRE_INPUTS=1` con `test_native_storage.py` su entrambe le ROM e ricevute di prova. Usare veri accessori e inserimenti nativi; stub solo di OS/allocatore non trasformano il core sintetico in prova nativa. Verificare ripristino byte per byte e metadata dopo il secondo inserimento fallito.
- [ ] Provare mutanti: niente recheck, sentinel18 accettato, secondo destinatario saltato, effetti anticipati, metadati/Aprijuice non ripristinati. Ogni mutante deve fallire dopo una baseline verde con test eseguiti. Misurare owner e overlay naming separatamente; sottoporre testo/rodata/stato a riserva. Protocollo comune; commit `Add atomic native gift delivery core`, push `main` senza attivazione parziale degli eventi.

## Task 3: bridge, regali singoli, mosse, soprannomi e pagamenti

**Files:** Create `constructors.c`, `runtime.c`, `naming.c`, `test/test_constructors.py`, `test/test_naming.py`, `test/test_bridge.py`, `test/test_native_gifts.py` nella feature; Create `source/sgp131/test_gifts_install.py`; Extend `gifts.py`, script/claim/native manifests e composizione.

**Interfaces:** `gifts.install(data: bytes, language: str, commands: object, charmap: Path, training_symbols: dict, work_dir: Path) -> tuple[bytes, dict]`, `verify_installed(before: bytes, after: bytes, receipt: dict, commands: object) -> dict`; `int sgp_gift_build(void *field, const SgpGiftClaimSpec *, const SgpGiftResolvedInputs *, SgpGiftPrepared *)`, `int sgp_gift_script(void *ctx)`, `int sgp_gift_task(void *task)`, `int sgp_gift_name_begin(void *task, SgpGiftPrepared *, u8 index)`. ClaimSpec generato dal manifest, ResolvedInputs è copia dei valori vivi, non puntatori a stack script.

Bridge: comando490 mantiene la larghezza originale e usa magic **0xF13B**. Per altri operandi delega all'handler Training installato, ricavato dalla ricevuta e rilettura, senza consumare il PC script. F13A e fallback retail restano invariati. Input8006=CLAIM(0),8007=claim ID; output800B=status,800C=count,8000..8002=kind/index-or-box/slot del primo,8003..8005 del secondo. Il manifest deve dimostrare liveness delle variabili per ogni sito; se ancora vive, salvarle/ripristinarle o usare il risultato posseduto senza proiettarlo su quelle variabili.

- [ ] Scrivere test seed-identici di costruzione, consegna party/PC, mosse successive, nickname default/annulla/conferma/OOM, wrapper F13A/retail/no-consumption e scratch vivo. Includere Dragonair e Pikachu con mosse personalizzate, tutti i cinque siti premi Casinò e regali variabili. `test_constructors.py`, `test_naming.py`, `test_bridge.py`, `sgp131.test_gifts_install`: RED specifico prima dell'implementazione.
- [ ] Preparare il Pokémon completo prima dell'inserimento; costruttori e metadati native, PP nativi per destinazione PC. Non lasciare SetMonMove, BufferPartyMonNick o nickname count−1 diretti a un Pokémon appena mandato al box.
- [ ] Per naming possedere `NamingScreen_CreateArgs` e il Pokémon temporaneo seguendo il pattern pointer-owned di `hatch_egg_task.c`; non usare `CallTask_NamingScreen`, che scrive per indice squadra. Attendere il child, applicare nome al record temporaneo e liberare una volta. Conservare soltanto le offerte di naming già presenti negli eventi.
- [ ] Prima di spendere gettoni o impostare flag, completare tutti gli inserimenti. Dex/statistiche solo per non-uova e dopo successo; nessuna nuova alterazione delle politiche shiny/PID. Risultati e messaggi devono indicare la destinazione reale.
- [ ] Eseguire suite mirate, native installate e mutanti di handler/magic/recipe/target/preimage/snapshot. Recheck finale dell'intera composizione con tutti i componenti V4 conservati. Ogni adapter attivato deve avere scena EN/IT prima/dopo e Continua/SAVE/cold oltre ai test del costruttore. Protocollo comune; commit `Route audited single gifts through native storage`, push `main`; nominare le famiglie ancora non attive.

## Task 4: coppie, uova ordinarie e Togepi

**Files:** Extend manifest/costruttori/task/scripts; Create `test/test_pairs.py`, `test/test_eggs.py`; Extend installed-native e audit ROM. Stesse interfacce, nessun servizio parallelo.

- [ ] Prima del costruttore Togepi fissare residenza e proprietario dell'overlay reale, indirizzi e side effect nativi. Un indirizzo che ricade nell'intervallo di più overlay non costituisce questa prova. Registrare guardie e linkage nel manifest del corretto stadio.
- [ ] Scrivere test per tutte le alternative dei membri coppia25/200/757/837/890, Phione750, nove siti GiveEgg e due Togepi858. Includere flag Primo345/346/347 già anticipati nello script, Togepi112, rifiuto con un posto per due e secondo inserimento fallito dall'adapter installato. Eseguire `test_pairs.py` e `test_eggs.py`: RED specifico.
- [ ] Trasformare l'intero claim, non due GiveMon indipendenti. Preflight e commit coppia atomici; ogni personalizzazione/naming prima dell'inserimento. Flag, hide e linkage PID/gender Togepi soltanto dopo successo; fallimento lascia l'evento esattamente pendente.
- [ ] Provare associazione NPC/entry di Phione: mantenere due uova per invocazione e ripetibilità originaria. Due invocazioni accettate producono due+due uova; una capacità insufficiente produce zero, senza nuovo flag di esclusione.
- [ ] Verificare memo, met, forma, mosse/PP, schiusa e linkage nativi. Rieseguire censimento trasformato, tracce di ogni ramo e scene EN/IT con vecchi raw-save. Protocollo comune; commit `Deliver paired gifts and eggs without partial claims`, push `main`.

## Task 5: famiglie speciali, lettere e Dono Segreto

**Files:** Extend costruzione/runtime/claim/guards; Create `test/test_special.py`, `test/test_mail.py`, `test/test_mystery_gift.py`; Extend installed-native e scene. Stesse interfacce transazionali.

- [ ] Prima dei test pin dei costruttori e residenza overlay effettiva per Pichu/Togepi: indirizzi sovrapposti fra overlay non provano quale proprietario sia caricato. Pin Day Care, prestiti e dispatch Dono Segreto e tutti i loro effetti prima/dopo l'inserimento.
- [ ] Scrivere test Pichu nei tre rami, uovo ereditato Pensione con corsi attivi, Shuckle, Kenya e Mailbox piena/−1, Pokémon/egg/Arceus/Ranger del Dono Segreto, payload con OT/IV/PID/fiocchi e identità coda cambiata. Eseguire le tre suite: RED specifico. Non descrivere fixture Wonder Card sintetiche come distribuzioni storiche provate.
- [ ] Pichu: preservare forma e attributi speciali; var16683/rimozione donatore solo dopo successo. Pensione: costruire su record temporaneo con routine native di ereditarietà; reset pending solo al commit, parenti e corsi invariati. Non chiamare una vecchia funzione che inserisce e resetta incondizionatamente.
- [ ] Kenya: prenotare slot Mailbox0..19 con controllo esplicito−1, conservare lettera integra, svuotare held-mail soltanto nel Pokémon destinato al box. Rifiuto se PC o Mailbox senza spazio. Provare il successivo riconoscimento nativo della lettera e del prestito; consegna in squadra conserva la lettera allegata.
- [ ] Dono Segreto: lavorare su copia del payload, controllare nuovamente l'identità della coda al commit, preservare ribbon/OT/PID/IV/met e side effect Arceus; non chiamare il vecchio receive che consuma la coda dopo un inserimento fallito. Per ogni candidato con Mail, incluso Dono Segreto, applicare la stessa prenotazione Mailbox+svuotamento held-mail del percorso Kenya; payload non rappresentabile rifiutato INVALID senza consumare la coda. Test successo e rifiuto con Mailbox piena. Tag non-Pokémon delegati invariati. Rifiuto lascia la coda byte-identica.
- [ ] Provare ogni ramo/adapter in EN/IT, fault injection e vecchi save, con parenti, corsi, lettere e coda confrontati. Negative controls: ritiro Pensione con squadra6, scambi, starter iniziale, rescue Tentacool, catture e squadre temporanee. Protocollo comune; commit `Preserve special gift and mail semantics on PC delivery`, push `main`.

## Ammissione della funzione completa

- [ ] Il manifest finale associa ogni sito a un adapter accettato o a un'operazione esplicitamente invariata; niente famiglie silenziosamente escluse. Zero errori CFG e side effect prima del successo. Eseguire tutte le suite `gift-delivery/test` e `sgp131.test_gifts_*`, con `SGP_GIFT_REQUIRE_INPUTS=1` nella campagna ROM.
- [ ] Coprire scene di tutti gli adapter, non solo un costruttore per famiglia, riusando fixture e prove già raccolte nelle unità. Matrice capacità, fault, pagamenti, PP, nomi, coppie e repeatability; stessa fixture per il prima e il dopo. Confrontare anche byte di owner estranei e progressi.
- [ ] Continua/SAVE/cold EN/IT su vecchi save e composizione finale con box, Training, Borsa e Plus. Applicare `evidence.validate_acceptance`, aggiornare rapporto e protocollo comune. Soltanto dopo questo gate descrivere la copertura regali come completa.

## Comandi di test

Per ogni file test feature sopra: `PYTHONPATH=source .venv/bin/python -m unittest discover -s source/features/gift-delivery/test -p NOME_FILE.py -v`. Per le suite package: `PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_gifts_audit sgp131.test_gifts_scripts sgp131.test_gifts_install -v`. La campagna Class B richiede `SGP_GIFT_REQUIRE_INPUTS=1`, percorsi EN/IT di baseline/candidata e ricevute nel config del banco; missing input o caso richiesto saltato equivale a fallimento di accettazione. Ogni nuova suite va registrata nel runner sotto la categoria corretta, senza pubblicare input o dati estratti.
