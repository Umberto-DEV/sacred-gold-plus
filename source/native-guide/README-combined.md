# Guida Summary e Nuova partita — prova locale

La composizione distinta `build_combined_guide.py` mantiene il pilota EV/IV r5 e aggiunge la stessa presentazione ai due ingressi. Le basi ammesse sono le Plus Community1 EN/IT identificate dal loro SHA-256 completo. Tutti gli output ROM, save, immagini e dump restano in una nuova directory `<scratch>*`.

Il percorso Nuova partita sostituisce soltanto i tre puntatori del template Oak ARM9, conservando overlay53 e codice Init/Main/Exit originali. Dopo il primo setup grafico, `newgame_host.c` sospende Main prima del primo task Oak. Il marker dell'istanza resta attivo attraverso la tastiera, impedisce la ripetizione e viene azzerato da Exit. La presentazione non inizializza né interpreta SaveData. Il medesimo owner da64 byte serve Summary e Oak durante le rispettive vite; nessuna risorsa di un host resta allocata quando si cambia proprietario.

`combined_guide.c` deriva dal Summary revisionato, che rimane conservato in `summary_guide.c`. Le uniche modifiche al file condiviso `guide_present.c` rendono configurabili la posizione dei testi e la dichiarazione di `copy16`: con i valori predefiniti il payload Summary resta byte-identico. La combinata usa una copia halfword non inline per rispettare il limite del codice. Il resolver heap conserva le stesse verifiche e riceve esplicitamente19 oppure80; alloc/free/IRQ riusano `lease.c` invariato.

| Risorsa | Composizione normale |
|---|---:|
| Unica partizione aggiunta dopo r5 | `0x01FF8880–0x01FFA000`,6016 byte |
| Codice | 4748 byte, termina a`0x01FF9B0C` |
| Testi a`0x01FF9B10` | EN1098 / IT1176 byte |
| Stato a`0x01FF9FC0` | 64 byte |
| Margine totale | EN106 / IT28 byte |
| Lease modale raw NNS | 22528 byte |
| Contesto + backup/mappe/bitmap + extra Oak | 21304 byte; canaria finale separata4 byte |
| Extra Oak | 64 byte glyphReadBuf lazy + brightness/blend8 byte |

Oak conserva font0 lazy, palette14, background15, BG4 caratteri`0x06218000` e mappa`0x06207800`. Prima del prestito controlla callback, configurazione video, heap80 e font. La guida mostra BG4 con brightness neutra e blend spento; il ritorno ripristina esattamente nero, blend, visibilità, mappe, caratteri e scratch del font prima del rilascio e della ripresa di Oak. I buffer rimangono validi fino al trasferimento schedulato. Il rilascio degli input è richiesto prima della continuazione.

Esempio di build normale, dalla radice del repo, sostituendo i percorsi con input identificati; per il banco headless vedi [source/docs/test-bench.md](../docs/test-bench.md):

```sh
python3 source/native-guide/build_combined_guide.py --rom <base-plus> --charmap <charmap-verificata> --out <nuova-directory-privata>
```

`verify_newgame_guide.py` parte senza SRAM e usa soltanto input ordinari. Il copione include guida/skip, genere, tastiera con nome TEST esplicito, conferma, cameretta, dialogo originale con la madre che abilita il menu, primo SAVE e avvio da zero dal save appena prodotto. Verifica SRAM tuttaFF prima di SAVE e roundtrip esatto, nome/genere/partita e location. Il confronto tra nuove partite distingue ID/avatar e var0x403C variabili già nella r5 originale; il generatore casuale non viene modificato.

`verify_combined_summary.py` riusa input e asserzioni Summary revisionati, adattando solo provenienza e offset dei testi. `verify_newgame_transitions.py` controlla i frame di entrata/uscita e la dissolvenza originale di Oak. L'osservatore è quello Task3 identificato, senza nuove modifiche al core.

Per la pressione usare il distinto `build_newgame_pressure.py` e `verify_newgame_pressure.py`: prenotazione propria174000 byte, successiva vera richiesta UI22528 che restituisceNULL, controllo delle canarie e free nativo. Queste ROM lasciano Summary sulla r5 e non sono candidate normali. La strumentazione non modifica free list o dimensione dell'heap.

Gli esiti selezionati e i percorsi delle prove restano in un registro di laboratorio (private lab record, not distributed). Le prove restano limitate a core Mac interprete/software1× e alle fixture descritte; non attestano GUI, audio, Android o console portatili, tutti i save o una release. La review indipendente precede l'accettazione del task.
