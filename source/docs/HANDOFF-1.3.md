# Riprendere lo sviluppo di Sacred Gold Plus 1.3

Punto di ripartenza aggiornato al **29 ottobre 2026**. La versione pubblicata è
**1.2.5**; la candidata **1.3**, ora identificata nel gioco come **V1.3**,
ha sorgenti su `main`, una campagna Android e prove su dispositivo fisico. Le
nuove idee devono partire dal codice e dalle prove qui indicati, mantenendo
aggiornato il confronto fra le due versioni.

## Documenti da leggere

| Documento | Uso |
| --- | --- |
| [Istruzioni del repository](../../AGENTS.md) e [build e controlli](../README.md) | Lavorare su `main`, preservare modifiche esistenti, salvataggi e spazio su disco. |
| [Novità dalla 1.2.5 alla 1.3.0](novita-1.3.0.md) | Registro delle modifiche realmente integrate, con confronto prima/dopo e appendice delle specie. |
| [Verifica Android del 29 ottobre](android-1.3-dev-validation.md) | Campagna funzionale precedente, identificata da hash, con matrice e limiti. |
| [Candidata V1.3 e dispositivo fisico](device-1.3-validation.md) | Hash correnti EN/IT, nome e icona, versione, prove sul save e limiti. |
| [Builder e funzioni 1.3](../sgp13/README.md) | Costruzione, componenti e contratti del codice corrente. |
| [Metodo di debug e ottimizzazione](HANDOFF-debug-optimization.md) | Riproduzione, ricerca, misure, correzioni, regressioni e conservazione delle prove. |
| [Proposta meccaniche 1.3.1](mechanics-1.3.1-proposal.md) | Ricerca futura: box portatile, regali, comandi e rivincite; nessuna aggiunta ancora implementata. |
| [Piano eseguibile meccaniche 1.3.1](superpowers/plans/2026-10-29-mechanics-1.3.1.md) | Audit del codice/byte V4 e ordine dei quattro sottoprogetti, prove prima/dopo, banco limitato e gate di accettazione. In attesa di revisione del piano. |
| [Esplorazione grafica](graphics-engine-exploration.md) | Idee per mappe animate e distinzione fra contenuti nativi e nuovo renderer; fuori dall'intervento meccaniche. |

I rapporti v4, v5, v8 e della diagnosi del 28 ottobre conservano prove storiche.
Le loro versioni interne non indicano automaticamente il candidato più recente:
per identificarlo usare il rapporto «Candidata V1.3 e dispositivo fisico» sopra
collegato e gli hash.

## Stato del lavoro e della CI

I sorgenti 1.3 sono stati pubblicati su `main` con il commit
[`6512430`](https://github.com/Umberto-DEV/sacred-gold-plus/commit/6512430513ef639a9322f70a3f545ca03be9cc4c).
La [CI di quel commit](https://github.com/Umberto-DEV/sacred-gold-plus/actions/runs/40926637779)
è verde: **Public files** e **Class A tests (no game file)** hanno concluso con
successo. Non sono stati pubblicati release, tag o nuovi download.

Il successivo aggiornamento visivo prepara nome e versione: **Pokémon Sacred
Gold Plus** nella libreria, icona originale conservata, **V1.3** nel titolo e
nelle impostazioni Plus. Il rapporto del dispositivo identifica le nuove ROM e
il confronto integrale con le precedenti. È pubblicato nel commit
[`94ef03e`](https://github.com/Umberto-DEV/sacred-gold-plus/commit/94ef03e2977e6ef6b802f58e4eaf7b77cf0c1224),
con [CI verde sullo stesso SHA](https://github.com/Umberto-DEV/sacred-gold-plus/actions/runs/40934647598):
**Public files** e **Class A tests (no game file)** conclusi con successo.
La suite locale passa con **809 test Class A eseguiti e 52 skip**. Gli eventuali
commit successivi di sola documentazione non cambiano i byte delle candidate
identificate nel rapporto. Prima di intervenire rileggere
`git status --short --branch` e i diff.

Una nuova sessione aperta nella stessa cartella locale può leggere codice,
documenti ed evidenze private conservate. Un nuovo clone contiene solo ciò che
è stato pubblicato. La cronologia della conversazione non sostituisce questi
file: fornire questo documento come punto di ingresso.

Il [workflow](../../.github/workflows/public-checks.yml) esegue
`python source/run_tests.py --json class-a-results.json`. Il
[runner locale aggiornato](../run_tests.py) comprende già le suite Class A della
1.3: non occorre aggiungere uno stage al workflow per includerle. La pubblicazione
comprende runner, dipendenze dei test e manifest. Verificare sempre che una run
verde appartenga allo SHA pubblicato; un risultato locale non sostituisce la CI.

ROM, salvataggi, BIOS ed evidenze private restano fuori dal repository pubblico.
Le prove che richiedono tali input e la campagna Android si svolgono sul banco
locale; una CI verde non le sostituisce.

## Risultato da conservare

Il bilanciamento ha una decisione per tutte le **493 specie**, con **67 specie**
interessate da almeno una modifica. Il registro delle novità distingue
statistiche base, abilità e mosse; non si tratta di aumentare indistintamente
gli EV. Shiny Classic e Pro, ricerca della specie, Training, Guida e interfacce
Plus hanno implementazioni e prove descritte nei documenti collegati.

La campagna Android comprende **49 checkpoint accettati**, dei quali **45 con
SAVE nativo e riavvio a freddo**, più quattro rifiuti con file intero invariato.
Sono distribuiti fra più revisioni del candidato; il rapporto precisa quali
prove valgono sui byte finali. Le verifiche dei dati, ARM e Android rispondono a
domande diverse e non vanno sommate come se fossero tutte sessioni di gioco.

La prova su dispositivo fisico Android 13, melonDS Nightly 2.1.5 e Compute 6x
ha verificato Continue, SAVE e riavvio a freddo su copie del vecchio save IT,
oltre a titolo, Guida e Plus. Il rapporto collegato distingue v3 e v4 e il
confronto dei dati. Il salvataggio originale resta invariato dopo la sostituzione
della ROM. Questa prova limitata non certifica tutte le prestazioni, i driver o
ogni vecchio save; rimangono i limiti della campagna AVD Software 1x.
La candidata V1.3 non è una release pubblicata.

Nel workspace originale, `local/notes/2026-10-29-device-1.3.md` indica le copie
canoniche private, i backup e le prove grezze. Non fa parte del clone pubblico.
Per giocare ripartire da **Continua**, senza caricare uno stato emulatore creato
con una ROM precedente.

## Come continuare e aggiornare i documenti

1. Leggere istruzioni, questo stato e i rapporti pertinenti prima di cambiare
   codice. Controllare branch, indice, modifiche locali e attività concorrenti;
   preservare il lavoro già presente.
2. Registrare una nuova idea nel piano pertinente, indicando comportamento
   atteso, motivazione e prova necessaria. Per il bilanciamento motivare ruoli,
   statistiche, abilità e mosse con dati e calcoli pertinenti; non uniformare
   tutte le specie alla stessa somma di statistiche.
3. Implementare e verificare il percorso interessato. Per un bug conservare la
   riproduzione precedente e la regressione. Distinguere test sintetici, codice
   ARM, dati della ROM, scena Android e persistenza. Segnalare gli skip.
4. Per modifiche al gioco costruire e provare il candidato pertinente. Per la
   compatibilità usare copie di vecchi save EN/IT, con e senza dati Plus e con
   Borsa espansa: Continue, SAVE nel gioco, esportazione, riavvio a freddo e
   confronto dei dati. Conservare gli originali. Per soli documenti bastano i
   controlli documentali e pubblici previsti da `AGENTS.md`.
5. Aggiornare [novita-1.3.0.md](novita-1.3.0.md) quando una modifica entra nel
   codice: prima/dopo, componenti, prove disponibili e limiti. Tenere coerenti
   [CHANGELOG.md](../../CHANGELOG.md), documentazione della funzione e questo
   punto di ripartenza. Non presentare un'idea come già implementata.
6. Registrare nuove campagne in un rapporto datato con hash e configurazione;
   aggiornare qui il collegamento corrente. Conservare identità e limiti delle
   campagne precedenti, senza attribuirle a build nuove. Mantenere una sola
   copia canonica delle evidenze private e rispettare i limiti di conservazione
   delle build in `AGENTS.md`.
7. Prima della pubblicazione richiesta, riesaminare i diff e l'intero contenuto
   dell'indice, registrare i nuovi file pubblici nel manifest ed eseguire i
   controlli appropriati. Commit e push vanno su `main`; verificare la CI sullo
   SHA pubblicato e aggiornare questa sezione di stato. Non sovrascrivere asset
   o tag di release già pubblicate.

## Messaggio per una nuova chat

> Riprendi Sacred Gold Plus nella stessa cartella del progetto. Leggi AGENTS.md,
> source/README.md e source/docs/HANDOFF-1.3.md, poi verifica lo stato Git.
> Mantieni aggiornato source/docs/novita-1.3.0.md e i rapporti delle prove.
> Parti dalla candidata e dalle verifiche già documentate per sviluppare questa
> nuova idea: [descrizione].
