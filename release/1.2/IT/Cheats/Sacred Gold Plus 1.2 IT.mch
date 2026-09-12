# Sacred Gold Plus 1.2 IT.nds
# ROM SHA-256: d099d71785285c8be9da2d6384130f562a90ec0104226a8a7323d3fdae81478c
# Identificativo melonDS: IPKE 1C1F741C
# Sette codici facoltativi, tutti SPENTI. Provane uno alla volta su una copia TEST.
# Questi codici valgono solo per Sacred Gold Plus 1.2. Un catalogo 1.1 non puo' agganciarsi
# a questo gioco: melonDS abbina i cheat per codice di gioco E checksum dell'intestazione, e
# quella della 1.2 e' diversa. Importa QUESTO file, non riusare quello della 1.1.
# Le opzioni della 1.2 -- difficolta' Plus, livelli dei selvatici, animazioni in lotta, tetto
# NPC, server online -- NON hanno cheat: si aprono in gioco dalla pagina Opzioni con SELECT.
# Spegnere un codice non annulla le scritture gia' fatte: riavvia senza savestate modificati.

CAT Cheat facoltativi

CODE 0 Testo rapido
DESC Accelera il testo nei dialoghi. Guardia verificata byte per byte sull'immagine ARM9 della 1.2 il 12 settembre 2026; la prova in gioco è stata fatta sulla 1.04 e non è stata ripetuta sulla 1.2. Riavvia senza cheat per ripristinare il codice originale.
92002346 00000E41
12002346 00002100
D2000000 00000000
920202EE 00004819
120202EE 00001C0C
120202F0 00004818
1202031E 0000BD10
02020320 E7E53C2D
1202032E 0000D0DF
1202033A 0000E7F1
D2000000 00000000

CODE 0 Transizioni rapide
DESC Riduce le dissolvenze nei cambi mappa; non è uno sblocco FPS. Guardia verificata byte per byte sull'immagine ARM9 della 1.2 il 12 settembre 2026; la prova in gioco è stata fatta sulla 1.04 e non è stata ripetuta sulla 1.2.
9200FA78 00009A0C
1200FA78 00002200
1200FA9C 00002200
D2000000 00000000

CODE 0 Cure rapide
DESC Abbrevia le animazioni al Centro Pokemon; cura PS, stato e PP come la cura normale. Agisce solo mentre l'overlay del Centro è caricato. Guardia verificata byte per byte sull'immagine ARM9 della 1.2 il 12 settembre 2026; la prova in gioco è stata fatta sulla 1.04 e non è stata ripetuta sulla 1.2. La seconda guardia sta in quell'overlay e non è verificabile staticamente.
9206325E 0000F7FC
1206325E 0000E000
1206327A 0000E000
D2000000 00000000
9224BDCC 00002000
1224BDCC 00002001
D2000000 00000000

CODE 0 Nascondi contorni 3D
DESC Disattiva i contorni 3D e mantiene l'antialiasing DS già presente; non aumenta la risoluzione. Entra ed esci da un edificio dopo l'attivazione. La sua guardia sta in un overlay di mappa, quindi non è verificabile sull'immagine ARM9 statica: per la 1.2 non esiste né una prova statica né una prova in gioco.
521FBC38 20204001
221FBC3A 00000010
D2000000 00000000

CODE 0 Rinomina scambiati
DESC Permette al Giudice Onomastico di rinominare Pokemon di altri Allenatori; il nome resta se salvi. Guardia verificata byte per byte sull'immagine ARM9 della 1.2 il 12 settembre 2026; la prova in gioco è stata fatta sulla 1.04 e non è stata ripetuta sulla 1.2.
9204D240 00002001
1204D240 00002000
D2000000 00000000

CODE 0 Denaro 999999
DESC Premi Select durante la partita per impostare 999999. Il valore resta nel salvataggio; spegnere il cheat non lo annulla. Scrive in RAM di gioco, non modifica codice. L'indirizzo del blocco salvataggio non è verificabile staticamente: prova in gioco fatta sulla 1.04, non sulla 1.2.
94000130 FFFB0000
6211186C 00000000
B211186C 00000000
0000D068 000F423F
D2000000 00000000

CODE 0 Camera Classic
DESC Riporta la telecamera agli angoli originali di HeartGold ovunque. Nella 1.2 la camera negli interni è già nativa in otto mappe: questo codice serve solo a chi vuole gli angoli originali anche fuori. Si applica al prossimo cambio di mappa; la guardia controlla la firma del modulo prima di scrivere, quindi su una ROM diversa non scrive nulla. Guardia verificata byte per byte sull'immagine ARM9 della 1.2 il 12 settembre 2026; la prova in gioco è stata fatta sulla 1.04 e non è stata ripetuta sulla 1.2. L'effetto a video non è ancora stato provato in gioco.
523DEBE0 002EB570
223DFFFC 00000000
D2000000 00000000
