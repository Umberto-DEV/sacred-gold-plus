# Banco e aggiornamenti V1.3.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Applicare e verificare incrementi sulla copia di lavoro V1.3 con percorsi fissi, recupero verificabile e prove confrontabili.

**Architecture:** `sgp131` è un successore separato: legge l'input V4 immutabile e ricompone gli incrementi richiesti in memoria o in uno scratch limitato. `workbench` mantiene un solo proprietario, input immutabile, candidata/fallback verificate e un solo pending transitorio, con pubblicazione atomica recuperabile. L'input esistente è referenziato, non duplicato a ogni prova.

**Tech Stack:** Python standard library, ndspy, compilatori e harness già presenti.

**Spec:** [Piano principale e vincoli](2026-10-29-mechanics-1.3.1.md), [builder attuale](../../../sgp13/build.py), [contratto output esistente](../../../sgp13/test_build.py).

## Global Constraints

Valgono tutti i vincoli del piano principale. Non cambiare `sgp13.build.write_new`: protegge output storici e pubblicati. L'unica sostituzione ammessa riguarda il percorso candidato privato registrato nel banco, con hash atteso e processo utilizzatore fermo. Nessun file originale viene spostato o rimosso.

## Review Focus

Disco insufficiente, crash tra ROM e report, symlink/file estraneo, due produttori e snapshot sorgenti cambiato durante build: tutti devono produrre rifiuto o recupero verificabile, mai una promozione falsa; test del task 1. Misure prive di baseline/campioni e fixture modificate devono restare non valutabili; test del task 2.

## Task 1: builder successore e banco a spazio limitato

**Files:** Create `source/sgp131/__init__.py`, `baseline.py`, `build.py`, `workbench.py`, `evidence.py`, `test_baseline.py`, `test_build.py`, `test_workbench.py`, `test_evidence.py` nella stessa cartella; Modify `source/run_tests.py`, `.github/public-files.json`. L'implementazione non modifica ancora il gioco.

**Interfaces:**

- `baseline.identify(data: bytes) -> str`: accetta soltanto i due SHA V4 del piano principale.
- `build.compose(base: bytes, through: str, charmap: Path, scratch: Path) -> tuple[bytes, dict]`: stadi `baseline`, `controls`, `portable`, `gifts`, `rematches`, `identity`, in questo ordine; stadi non implementati rifiutati, non saltati silenziosamente.
- `build.source_snapshot() -> dict[str, str]`: include tutti i `.py/.c/.h/.json` in `sgp131`, ogni nuova cartella feature e tutti gli input sorgenti transitori usati dagli installatori. Ricontrollo prima della pubblicazione.
- `build.verify_composition(before: bytes, after: bytes, receipts: list[dict]) -> dict`: rilettore separato, controlla hook/riserva e insieme esatto di FAT/overlay/regioni autorizzati dalle ricevute; ARM7, file ID e dati estranei invariati. Non allargare indiscriminatamente l'allowlist V1.3.
- `workbench.initialize(config_path: Path, bases: dict[str, Path], root: Path) -> dict`, `workbench.build_candidate(config_path: Path, language: str, through: str) -> dict`, `workbench.accept(config_path: Path, evidence_path: Path) -> dict`, `workbench.recover(config_path: Path) -> dict`.
- `evidence.validate_acceptance(report: dict, candidate_sha256: str) -> None`: schema minimo da questo task, richieste per stadio dichiarate dal builder e non eliminabili dal rapporto del chiamante; rifiuta hash diverso, prove obbligatorie mancanti, fail/skip. Per lo stadio baseline richiede identità byte V4 e input/sorgenti invariati; il task2 aggiunge misure e campagne di prodotto, senza introdurre una dipendenza inversa del banco.

CLI pianificata, introdotta da questo task (non disponibile prima):

```sh
export PYTHONPATH=source
.venv/bin/python -m sgp131.workbench init --config local/sgp131/config.json --base-en "$SGP131_BASE_EN" --base-it "$SGP131_BASE_IT" --root local/sgp131
.venv/bin/python -m sgp131.workbench inspect --config local/sgp131/config.json
.venv/bin/python -m sgp131.workbench build --config local/sgp131/config.json --language EN --through baseline
.venv/bin/python -m sgp131.workbench accept --config local/sgp131/config.json --evidence local/sgp131/evidence/EN/baseline-acceptance.json
```

`SGP131_BASE_EN/IT` vengono assegnate ai file esistenti verificati, non a copie scaricate o ricostruite. Config e prove private sono esclusi da Git.

- [ ] Scrivere test sintetici `test_rejects_foreign_base_before_output`, `test_rejects_input_output_alias_and_symlink`, `test_one_writer_and_busy_candidate_refuse`, `test_disk_budget_preserves_ten_gib`, `test_source_change_aborts_publication`, `test_failure_preserves_last_good_and_foreign_files`, `test_recovery_matches_rom_and_receipt`, `test_accept_requires_exact_evidence_hash`, `test_failed_candidate_never_becomes_fallback`. Usare byte sintetici e fault injection, senza ROM o filesystem pieno reale.
- [ ] Eseguire `PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_baseline sgp131.test_build sgp131.test_workbench sgp131.test_evidence -v`: RED specifico sul comportamento assente, dopo avere validato collection, firme e banco di test.
- [ ] Implementare file e CLI. Layout fisso per lingua: `candidate.nds/.json` verificata, `fallback.nds/.json` precedente verificata, `pending.nds/.json` transitoria in prova. Al primo avvio la riserva può riferirsi alla V4 originale senza copiarla. `build` restituisce il percorso pending, da usare nel collaudo; `accept` ruota candidata → fallback e pending → candidata solo dopo le prove. Conservare la precedente fallback fino all'accettazione. Usare journal di stato, fsync e hash per recuperare una coppia ROM/report dopo interruzione. Uno stato non coerente è non avviabile/non promuovibile; gli stessi nomi vengono riutilizzati a ogni iterazione.
- [ ] Costruire sempre dagli input V4 più i sorgenti attuali, aggiornando lo stesso slot candidato: niente catena di patch dipendente da esperimenti non registrati. Applicare in RAM dove pratico; scratch cancellato in `finally`. Richiedere `free_bytes - planned_peak >= 10 * 1024**3` prima della produzione. Calcolare picco da input, output, backup e massimo scratch effettivo, senza un numero arbitrario dichiarato sicuro.
- [ ] Arrestare il proprio utilizzatore prima di sostituire candidata; lock applicativo del banco con PID/sessione, lock non rimosso automaticamente se il processo è ancora attivo. Non terminare processi di altre chat. Ogni nuovo avvio dell'emulatore deve verificare l'hash candidato.
- [ ] Eseguire le quattro suite: PASS senza skip. Aggiungerle a `source/run_tests.py`; ripetere i test output/cleanup V1.3 per provare che il vecchio contratto resta invariato. Con entrambi gli input reali, `--through baseline` deve produrre byte identici alla V4, input invariati e nessun residuo temporaneo.
- [ ] Far revisionare stato/recupero e applicare protocollo comune del master; commit `Add bounded V1.3 successor workbench`, push `main`. Nessuna promozione di funzionalità è dichiarata da questo task.

## Task 2: audit riproducibili e misure prima/dopo

**Files:** Create `source/sgp131/audit.py`, `test_audit.py`, `source/docs/validation-1.3.1.md`; Extend `source/sgp131/evidence.py`, `test_evidence.py`; Modify `source/run_tests.py`, `.github/public-files.json`.

**Interfaces:** `audit.inspect(data: bytes, pret: Path) -> dict` produce pin di archivi/hook/finestre e elenco limiti, senza estrarre file di gioco pubblici. `evidence.compare(before: dict, after: dict, requirements: dict) -> dict` restituisce `pass`, `fail` o `not_evaluable`, con motivi per caso. `evidence.validate_acceptance(report: dict, candidate_sha256: str) -> None` rifiuta baseline mancante, hash diverso, obblighi incompleti o casi richiesti saltati.

- [ ] Scrivere `test_missing_before_is_not_evaluable`, `test_different_fixture_or_emulator_settings_refused`, `test_skip_is_not_pass`, `test_zero_samples_refused`, `test_positive_feature_and_negative_regression_both_reported`, `test_original_fixture_hash_changed_fails`. Eseguire `PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_audit sgp131.test_evidence -v` e osservare RED specifico.
- [ ] Implementare schema osservazioni: `case_id`, hash ROM/fixture/sorgenti, lingua, modalità tasti/Plus, strumenti/configurazione, sequenza input, attese, osservazioni, campioni, catture, esito e limiti. Prove di preparazione RAM marcate `prepared`; prove normali `natural`; persistenza soltanto Continua/SAVE/cold. Nessuna somma delle categorie come fossero tutte prove giocate.
- [ ] Rilevare baseline attuale: audit EN/IT, Class A, tasti/schermate e PC nativo, almeno una consegna rifiutata a squadra piena, costruzioni native 712/713, save vecchi EN/IT. Riutilizzare fixture e banco esistenti senza duplicarne alberi. Un nuovo script parte dal suo input dichiarato, non assume le coordinate di un altro save.
- [ ] Per prestazioni confrontabili raccogliere 20 campioni per scena dopo due riscaldamenti, stesso emulatore/configurazione/fixture e clock: fotogrammi guest fino alla schermata pronta e memoria/heap osservabile. Casi non valutabili se il timestamp o lo stato finale non è riconoscibile. Segnalare regressione oltre +5% mediana o +10% p95 nei percorsi esistenti; nessuna promessa di aumento FPS. Per un'azione nuova confrontare il suo tratto equivalente con l'app nativa e verificare separatamente il percorso prima assente.
- [ ] Richiedere zero errori strutturali, zero perdite/duplicazioni non previste e identità originali conservate. Sulla baseline eseguire 50 cicli del PC nativo al Centro Pokémon; il piano box ripete poi50 cicli portatili. Confrontare heap liberi agli stessi punti di riposo: nessuna diminuzione progressiva; un residuo fisso deve avere proprietario e dimensione documentati.
- [ ] Eseguire suite evidenze/audit, baseline reale e rilettura del rapporto. Registrare limiti e buchi; nessun caso obbligatorio mancante può risultare verde. Applicare protocollo comune, commit `Record reproducible mechanics baselines and acceptance gates`, push `main`.

Gli esperimenti runtime del task 2 sono le prove **prima** delle modifiche di prodotto: il loro risultato può correttamente essere «funzione assente». Le stesse fixture e gli stessi criteri alimentano il **dopo** nei piani successivi.

## Task 3: spazio eseguibile con proprietari espliciti

**Files:** Create `source/sgp131/reserve.py`, `source/sgp131/test_reserve.py`, `source/sgp131/data/reserve-map.json`; Modify `source/sgp131/build.py`, `source/sgp131/audit.py`, `source/run_tests.py`, `.github/public-files.json`.

**Interfaces:** `reserve.audit(data: bytes) -> dict` inventaria autoload, overlay con BSS, arena e intervalli già posseduti. `reserve.allocate(data: bytes, payloads: dict[str, int]) -> dict` restituisce regioni disgiunte e capacità oppure rifiuta; `reserve.apply(data: bytes, allocation: dict) -> tuple[bytes, dict]` preserva indirizzi pubblici e restituisce una ricevuta riletta indipendentemente.

- [ ] Scrivere `test_owned_zero_padding_is_not_free`, `test_overlay_bss_collision_refused`, `test_public_addresses_and_files_preserved`, `test_combined_payload_overflow_refused`, `test_arena_preimage_required`. Eseguire `PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_reserve -v` e osservare RED.
- [ ] Inventariare sorgenti, simboli compilati e byte dei comparti esistenti. In particolare `0x023D6800..0x023D7500` è `training.extension`, anche se V4 contiene zeri: una sua eventuale cessione richiede prova del proprietario e aggiornamento esplicito nel nuovo manifest, senza modificare il manifest storico 1.3.
- [ ] Implementare l'ammissione incrementale: ogni task di prodotto compila il proprio payload prima dell'installazione e passa dimensioni reali di codice/dati/stato a questo componente. Preferire una cessione dimostrata di spazio riservato inutilizzato; se insufficiente, espandere sotto l'arena attuale seguendo il repacker conservativo di `sgp13.space`, con audit di tutti gli overlay/autoload e BSS. Il primo manifest riporta soltanto proprietà esistenti e policy; ogni nuova allocazione viene fissata e revisionata nello stesso task che introduce il payload. Nessuna base RAM viene inventata anticipando codice ancora non compilato.
- [ ] Implementare applicazione e rilettura indipendente; eseguire suite sintetiche, audit EN/IT e misure heap baseline senza modifiche di prodotto. A ogni successiva nuova allocazione ripetere budget heap e minimi liberi in campo, squadra, PC e schermate annidate sulla riserva proposta. Un budget non sostenibile blocca l'installazione e richiede riduzione del payload o nuova allocazione misurata.
- [ ] Applicare protocollo comune e registrare la decisione nel rapporto; gli stadi successivi rifiutano payload fuori dal proprio intervallo. Commit `Define verified ownership for successor payloads`, push `main`.
