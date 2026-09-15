# Verifica codici natura e sesso dei selvatici — 15 settembre 2026

## Esito e causa

I gruppi 44, 45 e 46 vengono rigenerati da `source/cheats/gender.py` per
Sacred Gold Plus 1.2.1 EN/IT. Le 25 nature mantengono nomi e ordine del catalogo.

Il vecchio gruppo 45 non modifica il PID dell'incontro riprodotto. Con lo stesso
salvataggio e gli stessi input, senza codice e con «maschio + Decisa» premendo L,
il gioco crea Kakuna livello 19 con PID `94332253`: natura 16 e femmina.
Il payload agganciato a `020D3F60` scrive invece la word `0227E98C`, passando
`28B9` a `2056`. Il suo indirizzo deriva da `*0211186C + F710`, estraneo al
percorso di creazione osservato. Inoltre l'algebra del payload, `8200*k + c`,
non garantisce il sesso: il byte basso attraversa entrambe le fasce di genere.

Il vecchio gruppo 44 sostituisce anche lo shift che costruisce il PID con una
scrittura della natura. La nuova versione conserva quel generatore nativo.

## Correzione

La patch interviene prima della cifratura, sulle routine native
`CreateMonWithNature` (`0206E108`) e `CreateMonWithGenderNatureLetter`
(`0206E14C`), quest'ultima usata da Incantevole. Due confronti Action Replay
verificano i prologhi originali prima di qualsiasi scrittura.

- **44, natura:** sempre attivo, sostituisce gli argomenti natura; conserva il
  generatore PID e il genere nativi.
- **45/46, sesso + natura:** attivo tenendo L prima dell'incontro. Nel percorso
  standard conserva la metà alta casuale del PID e fissa quella bassa a `00FF`
  per maschio, `0000` per femmina. Il ciclo nativo accetta il PID solo quando
  `PID % 25` coincide con la natura richiesta. Per Incantevole sostituisce gli
  argomenti sesso e natura del generatore nativo dedicato.
- Rilasciare L con 45/46 ancora abilitato ripristina le quattro istruzioni
  originali. Ogni nuovo codice ripristina prima i siti condivisi, consentendo il
  passaggio a un'altra voce della famiglia. Usare una sola voce dei gruppi 44–46.

Non vengono scritti PID di Pokémon esistenti, checksum o dati cifrati. Non sono
necessari payload in RAM, hook DMA o modifiche alla ROM. Le specie monosesso o
asessuate mantengono il loro genere biologico. Per 45/46 cambia la distribuzione
dei PID, quindi anche degli esiti cromatici; non combinarli con codici shiny/PID.
Riavviare se si sono usati i vecchi codici, oppure dopo aver disabilitato 44.
Per disabilitare 45/46 rilasciare prima L; se questo non è avvenuto, riavviare.

## Evidenze

`source/cheats/test_gender.py`: **6 test host verdi**.
`source/cheats/test_gender_arm.py`: **1 test ARM verde per lingua**, che esegue
le istruzioni ARM9 originali con Unicorn per **1.200 casi per ROM**:
25 nature × 3 modalità × 8 rapporti di genere × 2 routine. Sono controllati PID,
natura, genere, parametri della creazione finale, stack e registri preservati.
Il banco sostituisce soltanto RNG, lettura del rapporto di genere e creazione
finale; la selezione del PID è codice ARM originale. Un test separato enumera
le 65.536 metà alte per entrambi i sessi e dimostra che tutte le nature sono
raggiungibili. La migrazione XML rifiuta layout sconosciuti ed è idempotente.

Prove reali con avvio da SRAM e motore Action Replay del runtime melonDS:

| Prova | PID creato | Natura | Sesso | Esito |
|---|---|---|---|---|
| EN, vecchio 45 Decisa | `94332253` | 16 | femmina | identico al controllo senza codice |
| EN, nuovo 45 Decisa | `B5B600FF` | 3 | maschio | cattura, Pokédex, deposito, ritorno al campo e salvataggio |
| IT, nuovo 46 Decisa | `0C4C0000` | 3 | femmina | cattura, Pokédex, deposito, ritorno al campo e salvataggio |
| EN/IT, nuovo 44 Decisa | `0C4C445C` | 3 | femmina | incontro e creazione nativa |

Le catture usano una Master Ball già presente nella fixture; nessuna forzatura
manuale di Pokémon o della routine di cattura. Nelle SRAM salvate il record
catturato è a offset `10B40`, con checksum valido `4ABB` (EN maschio) e `EF7F`
(IT femmina). Il PID è identico a quello passato alla creazione nativa. Dopo riavvio da queste
SRAM senza cheat, entrambi i record sono nuovamente presenti con PID e checksum
corretti. I dump al ritorno al campo confermano inoltre il ripristino delle
quattro istruzioni originali dopo il rilascio di L.

Build utilizzate per queste prove (precedenti all'ampliamento capacità Borsa):

- EN SHA-256 `30bbf4cf0105688218132c5aa4e8b9b3ec8de124961103f36cfbcb4c8e48a708`.
- IT SHA-256 `8f991bdd7f8abb80aaf25855a1708203e2194c222fbcdf4f1f33d2bab93b2610`.

ROM, SRAM, dump, script di fixture e tracce GDB restano locali in
`/tmp/sgp-final-20260915/gender/`, esclusi dai pacchetti pubblici.

## Limiti

Le prove live coprono Kakuna e natura Decisa; le altre nature, i rapporti fissi
e il percorso Incantevole sono verificati dal banco ARM. Non costituiscono una
campagna completa di tutte le specie, dei doni o dei leggendari, né un collaudo
sulla console fisica. L'esclusione reciproca nell'interfaccia dell'emulatore è
un'integrazione distinta; il generatore fornisce codici e istruzioni d'uso.

## Conferma sulla build finale a 17 stadi

Dopo l'ampliamento capacità Borsa, la discovery dei due file `test_gender*.py`
è stata ripetuta su entrambe le ROM finali: 6 test host + 1 test ARM verdi per
lingua, ancora 1.200 casi nativi per ROM. I siti e i contratti del generatore
restano validi. Questa ripetizione finale è ARM; gli incontri sesso/natura live
restano quelli della build precedente descritti sopra.

- EN SHA-256 `09528bd920609b14484bdf6d12fc9fe1c3239934dfdb92a3816a38fac6579d0b`.
- IT SHA-256 `8a28781bcd8debab4a0bfe8c7f8c6b50361733f5a6cce2ffdf8835ab7d8ebe9a`.

Log privati: `/tmp/sgp-final-20260915/regression-17/gender-{EN,IT}.log`.
