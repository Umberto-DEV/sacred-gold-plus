# Sacred Gold Plus 1.1 IT.nds
# ROM SHA-256: 7b61646c627eb67cd991dbc33d68519edd69395468ea8b326e867fe98e62d077
# Identificativo melonDS: IPKE 0CA7EBAE
# Sette codici facoltativi, tutti SPENTI. Provane uno alla volta su una copia TEST.
# Compatibilita' verificata staticamente sulla 1.1: le prove funzionali della 1.04 non si trasferiscono.
# Spegnere un codice non annulla le scritture gia' fatte: riavvia senza savestate modificati.

CAT Cheat facoltativi

CODE 0 Testo rapido
DESC Accelera il testo nei dialoghi. Compatibile per indirizzi con la 1.1 (preimmagini identiche alla 1.04); la prova in gioco è stata fatta sulla 1.04, non sulla 1.1. Riavvia senza cheat per ripristinare il codice originale.
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
DESC Riduce le dissolvenze nei cambi mappa; non e' uno sblocco FPS. Compatibile per indirizzi con la 1.1; prova in gioco fatta sulla 1.04, non sulla 1.1.
9200FA78 00009A0C
1200FA78 00002200
1200FA9C 00002200
D2000000 00000000

CODE 0 Cure rapide
DESC Abbrevia le animazioni al Centro Pokemon; cura PS, stato e PP come la cura normale. Compatibile per indirizzi con la 1.1; prova in gioco fatta sulla 1.04, non sulla 1.1. Agisce solo mentre l'overlay del Centro e' caricato.
9206325E 0000F7FC
1206325E 0000E000
1206327A 0000E000
D2000000 00000000
9224BDCC 00002000
1224BDCC 00002001
D2000000 00000000

CODE 0 Nascondi contorni 3D
DESC Disattiva i contorni 3D e mantiene l'antialiasing DS gia' presente; non aumenta la risoluzione. Compatibile per indirizzi con la 1.1; prova in gioco fatta sulla 1.04, non sulla 1.1. Entra ed esci da un edificio dopo l'attivazione.
521FBC38 20204001
221FBC3A 00000010
D2000000 00000000

CODE 0 Rinomina scambiati
DESC Permette al Giudice Onomastico di rinominare Pokemon di altri Allenatori; il nome resta se salvi. Compatibile per indirizzi con la 1.1; prova in gioco fatta sulla 1.04, non sulla 1.1.
9204D240 00002001
1204D240 00002000
D2000000 00000000

CODE 0 Denaro 999999
DESC Premi Select durante la partita per impostare 999999. Il valore resta nel salvataggio; spegnere il cheat non lo annulla. Scrive in RAM di gioco, non modifica codice. L'indirizzo del blocco salvataggio non e' verificabile staticamente: prova in gioco fatta sulla 1.04, non sulla 1.1.
94000130 FFFB0000
6211186C 00000000
B211186C 00000000
0000D068 000F423F
D2000000 00000000

CODE 0 Camera Classic
DESC Riporta la telecamera agli angoli originali di HeartGold. Sostituisce la vecchia build 'Normal Angle'. Si applica al prossimo cambio di mappa. La guardia controlla la firma del modulo 1.1 prima di scrivere: su una ROM diversa il codice non scrive nulla. Compatibile per indirizzi (bit OSSERVATO a 0x023DFFFC, valore 1 nella ROM 1.1); l'effetto a video non e' ancora stato provato in gioco.
523DEBE0 002EB570
223DFFFC 00000000
D2000000 00000000
