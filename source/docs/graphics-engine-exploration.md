# Esplorazione grafica: più vita nelle mappe HGSS

Ricerca e idee del **29 ottobre 2026**, separate dalla
[proposta meccaniche 1.3.1](mechanics-1.3.1-proposal.md). Nessuna modifica grafica,
mappa o importazione di motore è implementata da questo documento.

## Che cosa significa cambiare motore

«Motore» può indicare componenti molto diversi: regole della lotta, costruzione
degli avversari, gestione delle risorse, disegno delle mappe o scena di lotta.
Un annuncio di nuovo motore non prova che siano stati riscritti tutti questi
componenti. Redux V2 rimane un progetto basato su Nero 2/Bianco 2, anche quando
ne riprogetta profondamente le meccaniche e i contenuti.

In HGSS il mondo usa già mappe e oggetti tridimensionali insieme agli sprite
dei personaggi; lo sfondo nativo delle lotte appartiene invece a un percorso
diverso, bidimensionale. Arricchire un percorso o animare un oggetto nel mondo
non richiede automaticamente di sostituire il disegno delle lotte.

Gli autori degli [Expressive Backgrounds per Redux V2 e Cascade White 2](https://www.reddit.com/r/PokemonROMhacks/comments/1rodagv/unova_has_never_looked_so_good_introducing/)
usano scene di lotta 3D con elementi animati e illuminazione ambientale.
Spiegano che la quinta generazione possiede già il supporto necessario agli
sfondi 3D, mentre portarlo alla quarta richiederebbe un intervento considerevole
non realizzato nel loro progetto. È una distinzione tecnica esplicita degli
autori, non soltanto una stima per Sacred Gold Plus.

## Le idee proposte e il percorso più diretto

| Idea | Percorso da esplorare in HGSS | Difficoltà relativa |
| --- | --- | --- |
| Pannelli fotovoltaici, rovine, oggetti ambientali | Modelli o texture coerenti con i materiali e la scala della mappa; posizionamento, collisioni e prospettiva. | Bassa–media per una piccola scena. |
| Pale eoliche in rotazione | Oggetto tridimensionale e animazione ciclica, con registrazione e scaricamento corretti delle risorse. | Media. |
| Fumo dai camini | Effetto animato localizzato: scegliere tra sprite, texture animata o geometria semplice dopo una prova. Trasparenze e sovrapposizioni richiedono attenzione. | Media, da misurare. |
| Pokémon ambientali che camminano o girano | Oggetti/personaggi nativi con sprite, movimento, limiti del percorso e interazione. | Bassa–media per pochi casi; cresce con inseguimenti, folla e percorsi complessi. |
| Nuovi sentieri, radure, relitti e piccoli interni | Geometria, texture, collisioni, eventi, collegamenti e matrice delle mappe. Sono contenuti nuovi e lavoro di integrazione. | Media–alta secondo dimensione e collegamenti. |
| Animazioni dei Pokémon in lotta più ricche | Revisione separata di pose, asset, tempi e transizioni della lotta. L'animazione continua Plus esistente offre una base limitata. | Media per rifiniture; alta per un sistema articolato sul modello Gen V. |
| Sfondi di lotta 3D come quelli annunciati per Redux V2 | Estendere il renderer della lotta, risorse, telecamera, memoria e compatibilità con effetti e formati di scontro. | Molto alta; progetto autonomo. |
| Caricamenti più rapidi | Misurare letture, decompressione, cambi di overlay, allocazioni e fermate dello scheduler; correggere il collo di bottiglia rilevato. | Indeterminata prima delle misure; non è un beneficio automatico di una riscrittura grafica. |

La difficoltà indicata riguarda una prima scena controllata, non l'aggiunta
dello stesso dettaglio a ogni mappa del gioco. Più oggetti non significano
dettagli gratuiti: aumentano risorse, lavoro per fotogramma e possibili problemi
di sovrapposizione, collisione o caricamento. Le animazioni devono anche
fermarsi e ripartire correttamente entrando nei menu e cambiando mappa.

## Basi già presenti e strumenti

Il riferimento è il codice HGSS alla revisione
`0985e8718df4f25e64d6507d89c0c97c0d288981` di `pret/pokeheartgold`:

- [Gestore delle animazioni degli oggetti mappa](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/field/map_prop_animation.c)
  e [relative strutture](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/include/field/map_prop_animation.h)
  espongono caricamento, pausa e cicli. Le strutture hanno capacità finite:
  non dimostrano che un numero arbitrario di animazioni sia sostenibile.
- [Evento Sinjoh](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/field/event_cutscene_sinjoh.c)
  utilizza diversi tipi di animazioni di modelli, materiali e texture. Dimostra
  capacità del gioco; una sequenza dedicata non è però un effetto ambientale
  già pronto da lasciare attivo in qualsiasi mappa.
- [Gestione degli oggetti/personaggi](https://github.com/pret/pokeheartgold/blob/0985e8718df4f25e64d6507d89c0c97c0d288981/src/map_object.c)
  offre il punto di partenza per Pokémon ambientali con movimenti nativi.
- [DSPRE](https://github.com/DS-Pokemon-Rom-Editor/DSPRE/blob/main/README.md)
  documenta strumenti per modelli, collisioni, posizionamenti, eventi e script
  della quarta generazione, incluso HGSS. La sua disponibilità non certifica
  l'applicazione diretta a una ROM Plus già modificata.
- [Pokémon DS Map Studio](https://github.com/Trifindo/Pokemon-DS-Map-Studio)
  permette di creare nuove mappe anche per HGSS con un'interfaccia a tasselli
  convertita in un modello 3D. Il progetto specifica che non importa né modifica
  direttamente le mappe originali: va distinto dal lavoro di integrazione.

Per Plus gli esperimenti devono diventare trasformazioni riproducibili del
builder, con controllo degli input e rilettura indipendente. Non basta esportare
una ROM da un editor e presumere che abbia conservato tutti i componenti Plus.

L'[animazione continua Plus](../features/anim2/README.md) già documentata muove
gli sprite e gestisce pose e sospensioni. Non equivale al sistema di animazione
articolata di quinta generazione. La documentazione segnala inoltre pause
globali dei menu: conservare un task non fa avanzare uno scheduler fermo.
Questa è una ragione concreta per separare fluidità, caricamenti e renderer.

## Riutilizzare e fare reverse engineering

Possiamo studiare gli strumenti pubblici, il codice HGSS e le scelte degli altri
progetti senza progettare ogni formato da zero. Possiamo anche confrontare il
funzionamento di Nero 2/Bianco 2, ma codice, overlay, risorse e interfacce di
quinta generazione non sono compatibili automaticamente con HGSS.

Gli autori degli Expressive Backgrounds annunciano la pubblicazione di strumenti
e materiali dopo l'uscita di entrambi i loro progetti. È una disponibilità
futura dichiarata, non la prova che oggi esista già un pacchetto importabile.
Quando disponibile, andranno verificati codice effettivo, condizioni di riuso,
crediti e compatibilità. Un eventuale port richiederebbe comunque lavoro sul
renderer HGSS, sulle animazioni delle mosse e sui limiti della console.

Per gli asset di gioco seguire il modello del repository: lavorare dagli input
privati e distribuire trasformazioni e codice propri; non aggiungere al Git
pubblico risorse estratte, ROM o pacchetti di dati dei giochi.

## Esperimento consigliato dopo le meccaniche

Una sola piccola scena pilota: un Pokémon ambientale con percorso corto, un
oggetto statico nuovo e un solo oggetto animato. Verificare immagine, tempi per
fotogramma, memoria, entrata/uscita e salvataggi rispetto alla stessa candidata
senza modifiche. Iniziare con risorse e capacità native; ampliare il motore solo
se una limitazione misurata impedisce il risultato desiderato.

La scelta estetica proposta è una mappa HGSS più viva e leggibile, conservando
palette, scala, sagome e percorribilità. Il primo prototipo deve chiarire quanto
questo risultato costi sul banco di riferimento prima di estenderlo alla storia
Kanto–Sinjoh. Nessun incremento di prestazioni è attualmente dimostrato.
