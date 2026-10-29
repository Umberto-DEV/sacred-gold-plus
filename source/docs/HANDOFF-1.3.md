# Riprendere lo sviluppo di Sacred Gold Plus 1.3

Punto di ripartenza aggiornato al **29 ottobre 2026**. La versione pubblicata è
**1.2.5**; la **1.3 DEV** è una candidata locale con una campagna funzionale
Android conclusa. Le nuove idee devono partire dal codice e dalle prove qui
indicati, mantenendo aggiornato il confronto fra le due versioni.

## Documenti da leggere

| Documento | Uso |
| --- | --- |
| [Istruzioni del repository](../../AGENTS.md) e [build e controlli](../README.md) | Lavorare su `main`, preservare modifiche esistenti, salvataggi e spazio su disco. |
| [Novità dalla 1.2.5 alla 1.3.0](novita-1.3.0.md) | Registro delle modifiche realmente integrate, con confronto prima/dopo e appendice delle specie. |
| [Verifica Android del 29 ottobre](android-1.3-dev-validation.md) | Candidati identificati da hash, matrice delle funzioni, prove accettate e limiti. |
| [Builder e funzioni 1.3](../sgp13/README.md) | Costruzione, componenti e contratti del codice corrente. |
| [Metodo di debug e ottimizzazione](HANDOFF-debug-optimization.md) | Riproduzione, ricerca, misure, correzioni, regressioni e conservazione delle prove. |

I rapporti v4, v5, v8 e della diagnosi del 28 ottobre conservano prove storiche.
Le loro versioni interne non indicano automaticamente il candidato più recente:
per identificarlo usare il rapporto Android sopra collegato e gli hash.

## Stato del lavoro e della CI

Il 29 ottobre è iniziata la pubblicazione dei **soli sorgenti 1.3 su `main`**,
partendo da `809b6300622d58017d6ad0b3833ac53f73c13886`. Questo aggiornamento non
crea una release, un tag o nuovi download. La revisione prima del commit ha
confermato che codice, test e dati corrispondono al pacchetto già esaminato nella
campagna Android; le differenze successive riguardano documentazione e manifest.
L'esito della CI sul nuovo commit verrà registrato dopo il push. Prima di
intervenire rileggere `git status --short --branch` e i diff.

Una nuova sessione aperta nella stessa cartella locale può leggere codice,
documenti ed evidenze private conservate. Un nuovo clone contiene solo ciò che
è stato pubblicato. La cronologia della conversazione non sostituisce questi
file: fornire questo documento come punto di ingresso.

La [run Public checks del 27 ottobre](https://github.com/Umberto-DEV/sacred-gold-plus/actions/runs/40582914096)
è conclusa con successo sul commit indicato: entrambi i job, **Public files** e
**Class A tests (no game file)**, sono verdi. Questo risultato precede le
modifiche locali della 1.3.

Il [workflow](../../.github/workflows/public-checks.yml) esegue
`python source/run_tests.py --json class-a-results.json`. Il
[runner locale aggiornato](../run_tests.py) comprende già le suite Class A della
1.3: non occorre aggiungere uno stage al workflow per includerle. La pubblicazione
comprende runner, dipendenze dei test e manifest; verificare la run sul nuovo
SHA. Un risultato locale non certifica la futura esecuzione sul runner GitHub.

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

Rimane da eseguire la prova controllata sul dispositivo fisico. Il banco Android
ha usato un AVD ARM64 con Software 1x: non certifica driver, prestazioni o
profilo Compute 6x del dispositivo. La candidata non è una release pubblicata.

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
