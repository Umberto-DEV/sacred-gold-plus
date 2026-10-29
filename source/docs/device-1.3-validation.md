# Candidata V1.3 e verifica su dispositivo Android fisico

Verifica del **29 ottobre 2026**. La candidata corrente mostra **V1.3** nel
titolo e nelle impostazioni Plus. Rimane una versione di sviluppo: la release
pubblicata è ancora la 1.2.5. Questo rapporto aggiunge una prova su hardware e
la correzione del nome nella libreria alla precedente
[campagna funzionale Android](android-1.3-dev-validation.md).

## Identità delle ROM correnti

| Lingua | Revisione locale | Byte | SHA-256 |
| --- | --- | ---: | --- |
| EN | v4 | 147345256 | `179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90` |
| IT | v4 | 153228136 | `2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156` |

Le due build partono dagli ingressi 1.2.5 verificati dal builder. Le ricevute
conservano hash degli input, sorgenti, strumenti di riferimento e singoli stage.
Le verifiche della composizione e del codice installato eseguite dal builder
passano; non sono da sole una prova di gioco.

## Nome e versione

Il banner interno precedente indicava ancora «Pokémon HeartGold» in tutte e
sei le lingue DS, sia nella base 1.2.5 sia nella candidata v3. La v4 lo cambia
in **Pokémon Sacred Gold Plus**, conservando pixel, palette e riga del publisher
originali. Il checksum del banner viene ricalcolato; formato, checksum e nomi
di partenza inattesi vengono rifiutati.

L’etichetta del titolo passa da «1.3 DEV» a **V1.3**. La prima pagina Plus mostra
**Sacred Gold Plus V1.3 1/2**, e le due intestazioni della tabella precedente
usano **Sacred Gold Plus V1.3**. La pagina shiny mantiene i propri comandi.
Il nuovo header misura **137 pixel su 144 disponibili** in EN e IT.

Il confronto integrale v3→v4 trova **2396 byte diversi in EN e 2501 in IT**,
confinati al banner, ai 384 byte grafici dell’etichetta e alle due aree dei testi
Plus. Tutto il codice eseguibile, compreso quello di salvataggio, e tutte le
altre risorse restano identici. Le prove precedenti sui componenti immutati
restano pertinenti, conservando i loro limiti e gli hash originali.

La suite completa dopo la modifica riporta **37 suite Class A, 809 test
eseguiti e 52 skip**. I quattro test Class B sintetici eseguiti e i 176 skip
Class B restano separati. Nove controlli mirati verificano banner, checksum,
icone, limiti dei puntatori, grafica e tabella dei testi. La revisione
indipendente non rileva problemi nel diff di identificazione.

## Prova sul dispositivo

Configurazione osservata: Android 13 ARM64, melonDS Nightly **2.1.5**,
versionCode **46**, renderer **Compute**, risoluzione interna **6x**, due
schermi. APK e configurazione grafica non vengono sostituiti da questa prova.

Su copie di un vecchio save IT sono stati eseguiti **Continue, SAVE nel gioco,
chiusura del processo e riavvio a freddo**, prima con v3 e poi con v4. In
entrambi i casi il file esportato dopo il riavvio è identico a quello del SAVE
completato. Gli stati dell’emulatore precedenti non sono stati caricati.

Il confronto indipendente ricostruisce tutte le **45 regioni**, senza byte
inattesi: conservati i sei Pokémon in squadra, i 248 record occupati dei box,
identità, mosse, EV/IV, abilità, HP e statistiche memorizzate, inventario nativo,
Borsa espansa, impostazioni Plus, denaro, progressi, flag e Rubrica Amici.
La generazione nativa passa da 198 a 199 e i contatori Plus da 107 a 108;
il banco precedente rimane intatto.

Le variazioni di orologio, tempo giocato, eventi giornalieri, umore del follower,
Pokérus e stato temporaneo degli oggetti sono esplicitamente ricostruite. Nella
prova v4 l’apertura di Plus prima del SAVE inizializza il journal SHINY_ONLY con
Classic e valori predefiniti, senza applicare una modifica: è il comportamento
del proprietario dei dati già presente nella v3. Nessun corso o premio viene
creato. La discrepanza preesistente nella cache delle statistiche di Typhlosion
rimane invariata: questa prova non la corregge.

Sul dispositivo sono visibili il titolo **V1.3**, il nuovo header Plus, la
pagina shiny Classic **1/512** e, sulla v3, l’anteprima Pro **1/4096**, annullata
senza applicare. La Guida è stata aperta sulla v3. Il cambio pagina tramite
freccia touch funziona anche con l’opzione nativa **L=A**, che nasconde i due
dorsali agli input di gioco. Nome e icona della voce definitiva sono stati
verificati nella libreria melonDS dopo l’aggiornamento.

## Conservazione e limiti

La ROM IT corrente è installata allo stesso percorso e con lo stesso nome del
file precedente. Il `.sav` personale originale, il vecchio stato emulatore e
il file cheat sono conservati; il salvataggio originale rimane identico byte
per byte. Backup e ROM precedente sono verificati sul computer. Le copie di
prova e le relative voci temporanee della libreria vengono rimosse conservando
gli altri giochi. Per riprendere usare **Continua**, senza caricare un vecchio
stato emulatore.

Questa prova fisica copre un save IT con Plus e Borsa espansa, senza Pokémon
alla Pensione o corsi attivi. EN ha build, misure e confronto binario in questa
sessione; la sua copertura di gioco resta quella della campagna Android
precedente. Non sono ripetute tutte le catture, le probabilità shiny, le 493
specie o un’intera partita. Non è una misura delle prestazioni, un’approvazione
di ogni cheat precedente o una certificazione universale contro freeze e
difetti grafici. Screenshot, salvataggi e audit grezzi restano privati.
