# Presentazione compatta della guida

7 settembre 2026. Specifica locale da implementare, ancora senza review del rendering. Il gate [lease](README-lease.md) è passato sulle quattro fixture ed è stato revisionato: non garantisce una grande allocazione in tutti i chiamanti futuri. Restano vincolanti il cleanup e la gestione di NULL del [contratto](CONTRACT.md).

La guida mantiene le tre schede e il font HG originale. I [testi misurati](presentation-text.json) usano font0, interlinea16 e righe di massimo216 pixel dentro una finestra larga224. Tutti gli otto corpi, comprese le due varianti L=A, entrano in tre righe. Il testo IT della seconda scheda è stato accorciato senza cambiare significato. In inglese la pagina è **Stats**, come il titolo r5 effettivo, non il vecchio nome Skills del sorgente.

I comandi visibili sono START Guide/Guida per aprire; indietro, A avanti/fine e B esci nel modal. Il richiamo Reopen/Riapri: START resta distinto dai pulsanti touch. In modalità L=A la terza scheda spiega il limite del lettore r5 e il percorso per scegliere Normal/NORM. nelle opzioni; non modifica le opzioni. Le voci sono state confrontate con il bank45 delle due ROM identificate; `gSystem.buttonMode` è a+0x34, valore3 per L=A nel sorgente fissato. Il test deve dimostrare anche la selezione runtime della variante, senza confondere una preparazione sintetica con l'uso del menu Opzioni.

## Geometria candidata, coordinate in tile da 8 pixel

| Elemento | x, y | Larghezza × altezza | Tile |
|---|---|---|---:|
| Titolo | 2, 3 | 20 × 2 | 40 |
| Indicatore 1/3…3/3 | 27, 3 | 3 × 2 | 6 |
| Corpo, tre righe | 2, 7 | 28 × 6 | 168 |
| Riapertura con START | 2, 16 | 12 × 2 | 24 |
| Indietro | 2, 20 | 9 × 2 | 18 |
| Avanti/Fine | 12, 20 | 8 × 2 | 16 |
| Esci | 22, 20 | 8 × 2 | 16 |
| Sfondo opaco ripetuto | intera mappa | un tile riutilizzato | 1 |

Sono **289 tile / 9.248 byte**. Snapshot caratteri9.248 + bitmap9.248 + tilemap2.048 = **20.544 byte**: rimangono1.984 byte nel lease da22.528 per Window, contesto, stringa temporanea e allineamenti. Il builder deve calcolare gli offset e respingere sforamenti. Non eseguire AddWindow o altri helper che aggiungano allocazioni impreviste durante la prenotazione: verificare prima il percorso di stampa istantaneo e usare solo strutture/buffer con ownership corretta.

Questa geometria è candidata: la review a1× può richiedere margini o target più alti. Si possono ottenere fondi/bordi ripetendo pochi tile uniformi, contabilizzati esplicitamente; non ridurre il font o aumentare il cap per far entrare il layout. Colori e opacità vanno verificati sulla palette reale. Il rettangolo touch deve coincidere con quello disegnato, senza target invisibili. Indietro sulla prima scheda è visibilmente disabilitato.

Il badge chiuso usa una piccola prenotazione distinta, conserva i20 tile prestati e le20 celle della mappa, e li restituisce prima di una transizione Summary o della prenotazione modal. Non trattenerlo insieme al lease grande. Tutti i byte posseduti, compreso il puntatore al contesto persistente tra frame, devono avere una riserva dichiarata; nessun padding del gioco o del save.

Il componente di presentazione non riceve SaveData e non chiama Oak. L'host Summary conserva pagina, membro, EV/IV, callback e risorse originali. L'host Nuova partita è una successiva integrazione, dopo rendering e ritorno Summary verificati.
