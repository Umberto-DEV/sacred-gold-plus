# Prime rivincite variabili Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Offrire due squadre coerenti per ciascuna rivincita di Valerio712 e Raffaello713 in Plus, mantenendo accessi, livelli, identità degli allenatori e vecchi save.

**Architecture:** Un wrapper della lettura squadra seleziona una variante completa prima che il costruttore interpreti il primo membro. La scelta usa il seed pre-costruzione senza alterare il generatore nativo; il buffer temporaneo rimane fisso per tutta la lotta. Archivi allenatori e strategie 1.3 restano invariati.

**Tech Stack:** Python/ndspy, C/Thumb, Unicorn, costruttore e incontri nativi.

**Spec:** [Master](2026-10-29-mechanics-1.3.1.md), [proposta](../../mechanics-1.3.1-proposal.md), [strategie correnti](../../trainer-strategy-1.3.md). Prerequisiti: banco, UI/box e regali accettati.

## Global Constraints

Tutti i vincoli del master. Solo difficoltà Plus esistente, due varianti per ID712/713. Coprire anche la sequenza Dojo ereditata che usa gli stessi ID. Normale, primi incontri della storia, Lega, altri leader, multi/link/facility restano nativi. Nessun adattamento alla squadra del giocatore, contatore persistente, modifica di mosse/abilità globali o promessa di nuova AI.

## Review Focus

Cambio della prima specie prima di PID/abilità; seed globale invariato; ID condiviso fra telefono e sequenza; Normale con vecchie impostazioni; variante peggiore e preparazione realmente ottenibile. Test nei task 1–3.

## Task 1: contesti naturali e quattro squadre complete

**Files:** Create `source/sgp131/rematches.py`, `test_rematches.py`, `test_rematches_rom.py`, `data/rematch-variants.json`, `data/rematch-native-abi.json`; Create `source/features/rematch-variants/variants.h`, `variants.c`, `test/test_variants.py`; Modify runner/snapshot/manifest.

**Interfaces:** `unsigned rematch_select(unsigned seed, unsigned trainer)` restituisce `((seed ^ (seed >> 16) ^ trainer) & 1)`; `int rematch_apply(unsigned char *buffer, unsigned trainer, unsigned type_count, unsigned plus, unsigned seed, const void *config, unsigned config_bytes)` restituisce0 invariato oppure1/2 per variante A/B. Buffer108byte, nessuna allocazione o accesso al giocatore/save/RNG. `rematches.configuration(data: bytes) -> bytes` materializza quattro squadre complete da trasformazioni proprie del JSON e input privato, rifiutando preimage diverso.
`type_count` è `(format << 8) | count`, valore ammesso `0x0306`.

- [ ] Prima delle modifiche osservare EN/IT: Continua → contatto/chiamata/accettazione → Dojo → lotta; vittoria, sconfitta e nuova qualificazione. Separatamente percorrere la sequenza Dojo che invoca712/713. Registrare ID, indice party nemica, battleType, seed, orario/contatti e gating nativo. Riferimenti reali membro832: incontri a0x41F/0x4D9 e sequenza a0x706/0x738. Un ID forzato al costruttore non prova questi accessi.
- [ ] Confermare nel target il gate ordinario `battleType==1` e indice nemico1; se una famiglia differisce, seguirne il produttore e fissare una whitelist esatta con prove. Non sostituire questa prova con maschere ipotizzate. Conservare contatti, seeking, ricompense e disponibilità originali.
- [ ] Scrivere `test_normal_unknown_and_invalid_records_noop`, `test_both_selector_outcomes_and_seed_unchanged`, `test_four_complete_outputs_and_canaries`, `test_bad_config_offsets_counts_ids_hash_refuse`, `test_levels_IV_capsules_and_aces_preserved`. Eseguire `PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_rematches -v` e la suite feature: RED specifico.
- [ ] Scrivere due varianti partendo dai record effettivi. Proposta precisa A: Pelipper Ice Beam al posto di Spit Up; Swellow Facade al posto di Air Slash; Noctowl Psychic/Air Slash per supportare Nasty Plot; Pidgeot Roost al posto di Mirror Move. Per Raffaello: Yanmega Protect al posto di Screech; Scizor Bug Bite al posto di Feint; Heracross Rock Slide/Close Combat al posto di Feint/Horn Drill e niente Damp Rock; Vespiquen Heal Order al posto di Destiny Bond; Pinsir X-Scissor al posto di Guillotine. Proposta B applicata su A: Valerio sostituisce Fearow con Crobat `[Roost, Brave Bird, U-turn, Cross Poison]` e Staraptor usa U-turn al posto di Agility; Raffaello usa Psychic al posto di Protect su Yanmega e Forretress `[Spikes, Rapid Spin, Gyro Ball, Earthquake]` al posto di Masquerain.
- [ ] Preservare livelli per slot, difficoltà/IV, capsule e override, salvo nuove specie con form0/override0. Pidgeot e Scizor restano gli assi. Verificare tutti gli ID/effetti nella ROM corrente e apprendibilità/precedenti legali del nuovo set; la Masquerain della base è Coleottero/Acqua, quindi il cambio altera anche la copertura. Nessun effetto nuovo o aumento uniforme di EV/IV. Se un set fallisce legalità o bilanciamento, modificare quel set esplicitamente e rifare le prove, senza cambiare il motore globale.
- [ ] Materializzare e confrontare tutte le tuple dei quattro risultati nel rapporto privato; pubblicare solo trasformazioni e squadre progettate, non dump di archivi retail. Valori esatti delle mosse nel JSON sono risolti e verificati contro il significato effettivo, compresi ID riutilizzati. Suite verdi, revisione e protocollo comune; commit `Define bounded Plus rematch variants`, push `main` senza attivare hook non verificati.

## Task 2: wrapper precedente alla costruzione e prova ARM completa

**Files:** Create `source/features/rematch-variants/native.c`, `test/test_hooks.py`; Extend installer/readback, build, reserve map e composizione.

**Interfaces:** `rematches.install(data: bytes, language: str, work: Path) -> tuple[bytes, dict]`, `rematches.verify(before: bytes, after: bytes, receipt: dict) -> dict`. Wrapper nativo chiama una volta la lettura originale e poi il core, preservando risultato, stack e stato osservabile alla ripresa.

- [ ] Pin V4 EN/IT del costruttore `0x02073604..0x02073A98` e del BL `0x0207363A` verso `0x020735E8`, ripresa `0x0207363E`. È il punto dopo caricamento archivio e prima di leggere specie/override; i quattro hook livelli esistenti sono troppo tardivi e devono restare intatti. Snapshot seed pre-costruzione e argomenti prima della chiamata, con offset stack corretti dopo il prologo del wrapper e allineamento8byte.
- [ ] Scrivere `test_wrong_seam_or_constructor_hash_refused`, `test_occupied_region_and_overflow_refused`, `test_loader_once_SP_registers_and_resume_equivalent`, `test_every_constructed_member_matches_selected_team`, `test_existing_seven_strategies_unchanged`. Eseguire `sgp131.test_rematches_rom` in modalità required-input e test hook: RED specifico del comportamento, non dell'assenza di fixture.
- [ ] Aggiungere `test_non_single_link_multi_facility_contexts_noop` al wrapper nativo: stessi ID712/713 e Plus1, ma flag doubles/link/multi/tag/frontier/bit sconosciuti oppure indice diverso da1. Richiedere loader chiamato una volta e buffer, Pokémon costruiti, seed, SP e canary equivalenti al nativo; il test del solo core non dimostra il filtro contesto.
- [ ] Compilare e richiedere spazio al manifest composto. La regione0x023D6800..7500 contiene zeri in V4 ma è posseduta da Training: nessun uso senza cessione esplicita provata nel piano banco e controllo che gli incrementi precedenti non l'abbiano già assegnata. Non assumere una capacità disponibile dalla sola lettura degli zeri.
- [ ] Implementare guardie Plus==1, contesti verificati, ID/type3/count6/preimage/config. Config non valido lascia tutto invariato. Scegliere una sola variante, copiarla una volta; native RNG prosegue e ripristina il suo seed. Nessuna nuova opzione o stato persistente.
- [ ] Confrontare per EN/IT × Normale/Plus × A/B tutti i sei Pokémon effettivamente costruiti: specie/forma, PID, sesso, abilità, natura, IV/EV, livello, mosse/PP, oggetto, capsule e checksum. Confrontare seed globale, stack/canary e carico/free. Normale e casi rifiutati devono essere equivalenti al nativo; i sette allenatori già modificati da1.3 mantengono i loro risultati.
- [ ] Eseguire suite package/feature e regressioni `sgp13.test_teams_arm` con gli input originali richiesti da quella suite, senza passarle erroneamente V4 come1.2.5. Applicare protocollo comune; commit `Select complete Plus parties before native construction`, push `main`.

## Task 3: incontri, bilanciamento e persistenza

**Files:** Create `source/docs/rematch-variants-1.3.1.md`; Extend prove di accettazione, Guida EN/IT e rapporto corrente; aggiornare novità/changelog/handoff solo con risultati effettivi.

- [ ] Ripetere gli accessi normali del task1, compresi vittoria, sconfitta, retry, orari/gate negati e sequenza ereditata. Verificare ordine, ricompense e uscita. Separare da questi gli incontri a seed controllato del banco usati per enumerare A/B; nessun interruttore debug nei save del giocatore.
- [ ] Per ogni allenatore e lingua confrontare vecchio Plus e A/B con tre squadre giocatore: equilibrata, preparata con vantaggio di tipo, ordinaria poco preparata; tre seed per squadra. Registrare livelli, strumenti, turni, KO, cure, scelte AI e cicli ripetuti. Sono18 lotte con varianti per allenatore/lingua più baseline corrispondenti, non18 prove già svolte.
- [ ] Bloccare l'accettazione per loop di setup/recupero o mancanza di almeno due vie di preparazione ottenibili alla progressione prevista. Controllare acquisizione reale di mosse/strumenti/Pokémon indicati, variante peggiore e pressione Facade/Nasty Plot/hazard. Descrivere differenze osservate; vittoria del boss o danni maggiori non dimostrano AI migliore. Se si cambia un set, ripetere i confronti interessati.
- [ ] Continua → rivincita → SAVE → cold Continue su copie dei vecchi save EN/IT pre-Plus, Plus e Borsa espansa; verificare Normale invariato e nuova variante al successivo incontro senza reset. Nessuna garanzia che incontri consecutivi abbiano squadre diverse.
- [ ] Pubblicare le quattro squadre progettate, effetto dell'opzione Plus e limiti del pilot nella Guida/documentazione; confrontare prima/dopo con `evidence.compare` e aggiornare rapporto. Applicare protocollo comune; commit `Validate and explain Plus rematch variety`, push `main`. Passare all'accettazione composta del master.

## Comandi di test

`PYTHONPATH=source .venv/bin/python -m unittest sgp131.test_rematches -v`; `PYTHONPATH=source .venv/bin/python -m unittest discover -s source/features/rematch-variants/test -p 'test_*.py' -v`; campagna reale `PYTHONPATH=source SGP_REMATCH_REQUIRE_INPUTS=1 .venv/bin/python -m unittest sgp131.test_rematches_rom -v`. Il config del banco fornisce baseline/candidate EN/IT e ricevute. Required-input significa zero skip nelle prove richieste; non cambiare la classificazione dei test per ottenere un rapporto verde.
