# Correzioni degli script dei regali — 1.3.1 (sorgente)

La consegna dei regali e delle uova ai box è stata **abbandonata**: il giocatore usa il box portatile per fare posto in squadra. Restano due correzioni di bug degli script, entrambe solo sull'archivio `a/0/1/2`. Nessun codice ARM, nessuna memoria di riserva, nessun messaggio nuovo, nessun byte dell'ARM9.

## 1. Code dei fiocchi (invariata)

I membri 225, 232, 243, 246, 938 e 962 assegnano un fiocco ma, subito dopo `GiveRibbon`, contengono i 12 byte `4E00 1400 D907 3500 6100 0200`: l'editor aveva incollato il `CallStd 2009` del ramo «zaino pieno» sopra la vera coda di premiazione. Il dispatcher nativo rifiuta l'opcode 2009 (la tabella ha 853 voci) e la scena si ferma prima di `CloseMsg`/`ReleaseAll`. La riparazione sostituisce solo i 6 byte `4E00 1400 D907` con i 12 byte `PlayFanfare; WaitFanfare; SetFlag <flag giornaliero>; WaitButton` della coda retail (+6 byte per membro), con ricollocazione di ingressi e salti. Il produttore e il lettore indipendente sono quelli già consegnati (`gifts_scripts.patch_member`, `verify_member`).

## 2. Eevee del membro 227: guardia «squadra piena» (nuova)

Difetto: l'ingresso 11 del membro 227 (l'Eevee di livello 5) fa `GetPartyCount` e `GiveMon` senza alcuna guardia. Con la squadra piena il `GiveMon` fallisce in silenzio, l'Eevee si perde e `SetFlag 16220` / `HidePerson 15` scattano comunque: l'NPC sparisce e il regalo non è più recuperabile.

Correzione, sul modello dello script retail dell'Eevee di Bill (pret `scr_seq_0892_T25R0401.s`: `GetPartyCount; Compare 6; GoToIfEq <pieno>`; il ramo pieno è `messaggio; WaitButton; CloseMsg; ReleaseAll; End`):

```
PlaySE; LockAll; FacePlayer                       (invariati, ingresso 11 @442)
GetPartyCount 0x8005                              ┐
CompareVarToValue 0x8005, 6                       │ 17 byte inseriti @450, prima del monologo
GoToIf EQ -> PIENO                                ┘
BufferPlayersName ... NPCMsg 14..19 ...           (invariati: stessa sequenza, stessi byte relativi)
PIENO (in coda al membro, 14 byte):
  MsgBoxExtern 25, 39; WaitButton; CloseMsg; ReleaseAll; End
```

- La guardia sta **prima** del monologo (voci 14-18) e del messaggio 19 «ha ricevuto un Eevee!».
- Il messaggio è una **stringa nativa** già presente nella cartuccia, con il significato esatto: banco 25, voce 39 (EN «Your party is full!», IT «La tua squadra è completa!»). È letta con `MsgBoxExtern` dal suo banco: nessun banco messaggi viene modificato, nessuna voce aggiunta. Il banco 25 è fissato per hash (EN/IT) nel produttore.
- Con squadra 6: messaggio, nessun `GiveMon`, nessun `SetFlag 16220`, nessun `HidePerson 15`, nessuna offerta di soprannome; lo script termina e restituisce il controllo. L'evento è ripetibile (niente di persistente è scritto).
- Con squadra < 6: i comandi eseguiti sono quelli del V4 con in più il solo `GetPartyCount` della guardia (prova con il dispatcher reale, variabili finali identiche).
- La variabile `0x8005` è presa in prestito dalla guardia: è scritta di nuovo dal `GetPartyCount` originale (@471) prima di ogni lettura; il sito verifica che fra la guardia e quel punto ci siano solo `BufferPlayersName`/`NPCMsg`, senza salti e senza letture della variabile.
- Costo: +31 byte nel membro 227 (+17 guardia, +14 blocco); nessun salto o ingresso del membro viene perso (lettura indipendente `verify_party_guard`).

## Come entra nella ROM

Un solo produttore di archivio `gifts-scripts` (`sgp131/gifts_archives.py`) dichiara i sette membri 225, 227, 232, 243, 246, 938, 962 di `a/0/1/2` come `ArchiveDelta` legati al V4 per hash. Lo applica lo stadio UI nella sua unica scrittura (`archives.py`); nessuna aggiunta di archivio dopo la UI. I membri Guida (131, 132, 152, 196, 890) sono rifiutati.

## Limiti

- Provato: byte reali V4 EN/IT, dispatcher reale della cartuccia in Unicorn (`0x0203FD6C`, con gestori di `End`, `GoTo`, `GoToIf`, `SetVar`, `CopyVar`, `CompareVarToValue` eseguiti dalla cartuccia) e gestori degli altri comandi sostituiti da registratori. **Non** eseguiti: finestra di testo, dissolvenze, il `GiveMon` vero, la schermata del soprannome.
- Non provato su dispositivo: come appare il messaggio del banco 25 nel campo (finestra, velocità del testo, pagina vuota finale).

## Prove Android da fare (per Codex)

Fixture: salvataggio con l'Eevee del membro 227 non ancora ritirato (flag 16220 spenta).

1. Squadra 5: parlare con l'NPC; monologo, «ha ricevuto un Eevee!», fanfara, offerta di soprannome, scomparsa dell'NPC: identico al V4.
2. Squadra 6: parlare con l'NPC; compare subito «Your party is full!» / «La tua squadra è completa!», nessun monologo, la finestra si chiude con un tasto, il giocatore è libero; l'NPC resta; nessun Eevee in squadra e nei box; ripetere due volte.
3. Con il box portatile liberare un posto, parlare di nuovo: consegna normale, flag 16220 accesa, NPC scomparso.
4. Continua → SAVE → riavvio a freddo dopo (2) e dopo (3); il comportamento deve restare.
5. Un membro fiocco (per esempio 225): la scena del fiocco arriva a `CloseMsg`/`ReleaseAll` e il giocatore non resta bloccato.
