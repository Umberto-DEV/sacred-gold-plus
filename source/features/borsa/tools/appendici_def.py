#!/usr/bin/env python3
"""Definizione delle 6 appendici di bytecode del messaggio «Borsa piena» (199#10).

Questo modulo NON tocca la ROM: contiene solo (a) un micro-assemblatore che
ricava le larghezze degli argomenti da `scrcmd.json` del pret (la stessa fonte
che usa il disassemblatore validato-P1 di SGP-1.2-BORSA-GEN-01), e (b) la
descrizione simbolica delle appendici e dei siti d'innesto.

ABI (da `tools/py_scripts/scrcmd.json`, commit 0985e871 del pret — 853 comandi):
    17  CompareVarToValue  ['var', 2]        -> 2+2+2 =  6 B
    22  GoTo               ['script']        -> 2+4   =  6 B   (RELATIVO alla fine dell'arg)
    28  GoToIf             ['condition','script'] -> 2+1+4 = 7 B
    29  CallIf             ['condition','script'] -> 2+1+4 = 7 B
    41  SetVar             ['var', 2]        -> 2+2+2 =  6 B
    45  NPCMsg             ['message']       -> 2+1   =  3 B
    50  WaitButton         []                -> 2     =  2 B
    53  CloseMsg           []                -> 2     =  2 B
    97  ReleaseAll         []                -> 2     =  2 B
     2  End                []                -> 2     =  2 B
    27  Return             []                -> 2     =  2 B
   194  BufferItemName     [1, 'item']       -> 2+1+2 =  5 B
   440  MsgBoxExtern       ['var', 'var']    -> 2+2+2 =  6 B

Condizioni di `GoToIf`/`CallIf` (`src/scrcmd_c.c:141-149`, `sConditionTable`):
    0 lt | 1 eq | 2 gt | 3 le | 4 ge | 5 ne

PERCHE' `MsgBoxExtern 199, 10` CON DUE LETTERALI E NON DUE `SetVar`
-------------------------------------------------------------------
`ScrCmd_MsgBoxExtern` legge i due argomenti con `ScriptGetVar`
(`src/field/scrcmd_message.c:71-79`), che passa da `FieldSystem_VarGet`
(`src/script_manager.c:365-371`): se `GetVarPointer` torna NULL — e torna NULL
per ogni indice < `VAR_BASE` 0x4000 (`script_manager.c:353-356`) — il valore
letto E' il valore. Quindi un letterale vale quanto una variabile, e la ROM lo
fa gia': membro 246 @474 `MsgBoxExtern x800C, 52`, @485 `MsgBoxExtern x800C, 54`
(il secondo argomento e' un letterale). Risparmia 12 B per appendice rispetto
ai due `SetVar x800B,199` / `SetVar x800C,10` ipotizzati in
`U-borsa-progetto-esecutivo.md` §3.4, e soprattutto NON sporca x800B/x800C, che
in questi flussi portano la tasca dell'oggetto (membro 240 @902/908 usa x800B,
membro 938 @1734/1740 usa x800C).

L'OGGETTO
---------
In tutti e sei i flussi l'oggetto sta in `VAR_SPECIAL_x8004`: e' l'argomento del
`GiveItem x8004, x8005, x800C` del flusso stesso, e ogni flusso ne stampa gia' il
nome con `BufferItemName 1, x8004` poco prima del nostro punto d'innesto
(membro 3 @2197, 141 @6247, 145 @1139, 240 @897, 938 @1729/@1880). L'appendice
lo ricarica da se' (5 B) invece di fidarsi del buffer lasciato dal flusso,
perche' il ramo MT/MN di 141/145 riempie il buffer 1 con la forma indeterminativa
(`BufferItemNameIndef`, EN «a Potion») che nel nostro testo non va bene.

L'ATTESA
--------
`MsgBoxExtern` (440) torna TRUE e arma `SetupNativeScript(ctx, ov01_021EF348)`:
lo script resta fermo finche' la finestra non ha finito. Il `WaitButton` (50)
che segue e' la stessa coppia usata dalla ROM in membro 246 @440-446
(`MsgBoxExtern` ; `WaitButton` ; `CloseMsg` ; `ReleaseAll`). `CloseMsg` e
`ReleaseAll` NON sono nell'appendice quando restano al chiamante (membro 3:
`Return`; 141/145/240: si torna alle istruzioni originali che li fanno).
"""
from __future__ import annotations

import json
import struct
from pathlib import Path

# --- ABI: le larghezze vengono da scrcmd.json, non da queste costanti ------
ARG_SIZES = {
    "object1": 1, "object2": 2, "message": 1, "message_var": 2, "condition": 1,
    "var": 2, "flag": 2, "species": 2, "item": 2, "move": 2, "sound": 2,
    "ribbon": 2, "stdscr": 2, "trainer": 2, "phone_contact": 2, "spawn": 2,
    "maps": 2, "badge": 2, "direction": 2, "rgb": 2, "player_transition": 2,
    "addr": 4, "script": 4, "movement": 4,
}
RELATIVE = {"addr", "script", "movement"}

# Condizioni (sConditionTable, src/scrcmd_c.c:141-149)
COND_EQ = 1
COND_NE = 5

# Variabili speciali (include/constants/vars.h:386-389)
VAR_ITEM = 0x8004        # l'oggetto donato/raccolto, in tutti e 6 i flussi
VAR_SCARTATO = 0x800D    # VAR_SPECIAL_x800D: 1 = il gancio 125 ha scartato

BANCO_MSG = 199          # msg_0199, messaggio nuovo aggiunto da BORSA-GEN-08
MSG_BORSA_PIENA = 10     # 199#10


class Etichetta(str):
    """Riferimento a un'etichetta dell'appendice (destinazione assoluta da
    risolvere in fase di assemblaggio)."""


class Assoluto(int):
    """Destinazione assoluta gia' nota (offset dentro il membro)."""


class Assemblatore:
    """Micro-assemblatore a due passate. Le larghezze degli argomenti sono
    lette da `scrcmd.json`: nessuna lunghezza e' cablata qui dentro."""

    def __init__(self, scrcmd_json: Path):
        dati = json.loads(Path(scrcmd_json).read_text(encoding="utf-8"))
        self.cmds = dati["commands"]
        if len(self.cmds) != 853:
            raise ValueError("scrcmd.json: %d comandi, gScriptCmdTable ne ha 853"
                             % len(self.cmds))

    def larghezze(self, op: int):
        c = self.cmds[op]
        if c.get("switch_arg") is not None:
            raise ValueError("comando %d a caso variabile: non usato dalle appendici" % op)
        return [t if isinstance(t, int) else ARG_SIZES[t] for t in c["args"]], list(c["args"])

    def lunghezza(self, op: int) -> int:
        larg, _ = self.larghezze(op)
        return 2 + sum(larg)

    def nome(self, op: int) -> str:
        return self.cmds[op]["name"]

    def assembla(self, programma, base: int) -> bytes:
        """`programma` e' una lista di ('label', nome) e (opcode, [args]).
        `base` e' l'offset del membro a cui l'appendice verra' accodata.
        Torna i byte dell'appendice."""
        # passata 1: posizioni delle etichette
        pos, off = {}, base
        for voce in programma:
            if voce[0] == "label":
                if voce[1] in pos:
                    raise ValueError("etichetta doppia: %s" % voce[1])
                pos[voce[1]] = off
            else:
                off += self.lunghezza(voce[0])
        # passata 2: emissione
        out = bytearray()
        off = base
        for voce in programma:
            if voce[0] == "label":
                continue
            op, args = voce
            larg, tipi = self.larghezze(op)
            if len(args) != len(larg):
                raise ValueError("%s: %d argomenti, attesi %d"
                                 % (self.nome(op), len(args), len(larg)))
            out += struct.pack("<H", op)
            cur = off + 2
            for v, n, t in zip(args, larg, tipi):
                cur += n
                if t in RELATIVE:
                    dest = pos[v] if isinstance(v, Etichetta) else int(v)
                    v = (dest - cur) & 0xFFFFFFFF
                elif isinstance(v, (Etichetta, Assoluto)):
                    raise ValueError("destinazione su argomento non relativo")
                if not 0 <= int(v) < (1 << (8 * n)):
                    raise ValueError("%s: argomento %r non entra in %d B"
                                     % (self.nome(op), v, n))
                out += int(v).to_bytes(n, "little")
            off += 2 + sum(larg)
        return bytes(out)

    def goto(self, dest, base: int) -> bytes:
        """Un `GoTo` isolato da scrivere IN LUOGO all'offset `base`."""
        return self.assembla([(22, [dest])], base)


# ---------------------------------------------------------------------------
# Il blocco comune: mostra il messaggio se x800D == 1, poi azzera x800D.
#
# Chi azzera x800D: L'APPENDICE, subito dopo aver mostrato il messaggio (scelta
# di questo pacchetto, richiesta dal mandato). Il gancio ARM9 del comando 125 la
# alza soltanto (`sgp_borsa.h:151`, SGP_VAR_SCARTATO, valore 1 = scartato) e non
# la abbassa mai. Senza l'azzeramento, un secondo dono nello stesso script — o
# un flusso che passa due volte per lo stesso punto — ripresenterebbe il
# riquadro senza motivo. x800D vive nella ScriptEnvironment (muore con lo
# script, non entra nel salvataggio: `script_manager.c:353-360`), quindi
# l'azzeramento serve DENTRO lo script, non fra uno script e l'altro.
def blocco_messaggio(suffisso: str):
    fine = Etichetta("fine_msg_%s" % suffisso)
    return [
        (17, [VAR_SCARTATO, 1]),                  # CompareVarToValue x800D, 1
        (28, [COND_NE, fine]),                    # GoToIf ne, fine
        (194, [1, VAR_ITEM]),                     # BufferItemName 1, x8004
        (440, [BANCO_MSG, MSG_BORSA_PIENA]),      # MsgBoxExtern 199, 10
        (50, []),                                 # WaitButton
        (41, [VAR_SCARTATO, 0]),                  # SetVar x800D, 0
        ("label", fine),
    ]


# ---------------------------------------------------------------------------
# I SEI FLUSSI.
#
# `innesti`  : (offset, preimmagine_hex, 'goto' -> etichetta) sovrascrive gli
#              esatti byte della preimmagine con un GoTo verso l'etichetta,
#              riempiendo l'avanzo con 0x00.
# `ritocchi` : (offset_istruzione, indice_argomento, preimmagine_hex, etichetta)
#              cambia SOLO il campo relativo a 4 byte di un ramo esistente, che
#              resta della stessa lunghezza: nessun byte si sposta.
FLUSSI = {
    3: {
        "nota": "membro 3 = scr_seq_0003, gli script comuni std_*. Due flussi: "
                "std_obtain_item_verbose (2008, raccolta verbosa) e "
                "std_give_item_verbose (2033, dono da PNG).",
        "appendici": [
            # --- 2008: ...NPCMsg 30|31 ; WaitButton ; Return
            # I due rami (singolare @2117->2129, plurale @2126) convergono su
            # WaitButton@2129, e la coda utile e' di soli 4 B: non ci sta un
            # GoTo. Ma entrambi gli ingressi sono BERSAGLI DI RAMO (2126 da
            # GoToIf@2110, 2129 da GoTo@2120) e nessun altro ramo entra nella
            # finestra [2126,2133): basta RITOCCARE i due campi relativi, senza
            # sovrascrivere una sola istruzione. Le tre istruzioni originali
            # (NPCMsg 31 ; WaitButton ; Return) restano nel membro ma diventano
            # irraggiungibili; l'appendice le riesegue in testa.
            ("A2008", [
                ("label", Etichetta("a_msg31")),
                (45, [31]),                       # NPCMsg 31   (ramo plurale)
                ("label", Etichetta("a_wait")),
                (50, []),                         # WaitButton  (ramo singolare)
                *blocco_messaggio("a"),
                (27, []),                         # Return  -> al chiamante di CallStd 2008
            ]),
            # --- 2033: ...CallIf ne,2211 ; NPCMsg 89 ; Return
            # Qui si arriva per caduta lineare da CompareVarToValue@2176: serve
            # per forza un GoTo scritto in luogo. La finestra [2182,2194) e' di
            # 12 B e NON contiene bersagli di ramo (misurato): GoTo 6 B + 6 B
            # morti. L'appendice riesegue CallIf (bersaglio 2211, ricalcolato) e
            # NPCMsg 89.
            ("B2033", [
                ("label", Etichetta("b_start")),
                (29, [COND_NE, Assoluto(2211)]),  # CallIf ne, 2211
                (45, [89]),                       # NPCMsg 89
                *blocco_messaggio("b"),
                (27, []),                         # Return
            ]),
        ],
        "innesti": [
            (2182, "1d0005160000002d00591b00", "b_start"),
        ],
        "ritocchi": [
            # GoToIf@2110, arg 1 (i 4 B a 2113): 2126 -> a_msg31
            (2110, 1, "09000000", "a_msg31"),
            # GoTo@2120,  arg 0 (i 4 B a 2122): 2129 -> a_wait
            (2120, 0, "03000000", "a_wait"),
        ],
    },
    141: {
        "nota": "membro 141 = scr_seq_0141, TUTTE le Poke Ball a terra del gioco "
                "(id script 7000+, sScriptBankMapping in script_manager.c:56).",
        "appendici": [
            ("C141", [
                ("label", Etichetta("c_start")),
                (41, [0x800C, 1]),                # SetVar x800C, 1  (originale)
                *blocco_messaggio("c"),
                (22, [Assoluto(6533)]),           # GoTo 6533 = il GoTo originale -> 6186
            ]),
        ],
        "innesti": [(6527, "29000c800100", "c_start")],
        "ritocchi": [],
    },
    145: {
        "nota": "membro 145 = scr_seq_0145, TUTTI gli oggetti nascosti dei banchi "
                "dedicati (id script 8000+). Banco messaggi proprio 210: il "
                "messaggio arriva comunque, perche' MsgBoxExtern carica il banco "
                "che gli si passa (199) e non quello dello script.",
        "appendici": [
            ("D145", [
                ("label", Etichetta("d_start")),
                (41, [0x800C, 1]),
                *blocco_messaggio("d"),
                (22, [Assoluto(1429)]),           # GoTo 1429 = il GoTo originale -> 1084
            ]),
        ],
        "innesti": [(1423, "29000c800100", "d_start")],
        "ritocchi": [],
    },
    240: {
        "nota": "membro 240: un oggetto nascosto scritto A MANO da Sacred Gold, "
                "fuori dal banco dedicato (GiveItem @873).",
        "appendici": [
            ("E240", [
                ("label", Etichetta("e_start")),
                (41, [0x800C, 1]),
                *blocco_messaggio("e"),
                (22, [Assoluto(924)]),            # GoTo 924 = CloseMsg ; ReleaseAll ; End
            ]),
        ],
        "innesti": [(918, "29000c800100", "e_start")],
        "ritocchi": [],
    },
    938: {
        "nota": "membro 938: due oggetti nascosti scritti A MANO (GiveItem @1705 e "
                "@1856). Le due code sono identiche (NPCMsg 34 ; WaitButton ; "
                "SetVar x800C,1 ; CloseMsg ; ReleaseAll ; End), quindi UNA sola "
                "appendice con DUE GoTo; l'appendice chiude da se' con "
                "CloseMsg/ReleaseAll/End invece di tornare a due punti diversi.",
        "appendici": [
            ("F938", [
                ("label", Etichetta("f_start")),
                (41, [0x800C, 1]),
                *blocco_messaggio("f"),
                (53, []),                         # CloseMsg
                (97, []),                         # ReleaseAll
                (2, []),                          # End
            ]),
        ],
        "innesti": [
            (1750, "29000c800100", "f_start"),
            (1901, "29000c800100", "f_start"),
        ],
        "ritocchi": [],
    },
}

# Preimmagini dei membri toccati: lunghezza e sha256 ATTESI PRIMA delle
# appendici (stato 1.2.1 = stato dopo premi_disfa e dopo applica_199, che non
# toccano nessuno di questi cinque membri). Riempite da `misura_preimmagini()`
# e cablate qui: se non combaciano, l'applicatore rifiuta senza scrivere.
PREIMMAGINI = {
    3:   (6080, "db0c3bc3410176b3170c016fd977a8d416f77e834991d534aead7c2681bc2663"),
    141: (6608, "eb0a77aede1937d8c49cf1987948f97735f1117a94ded092996e205b09362b1f"),
    145: (1504, "43e211d1e0a66ddefbc92677f242b04a9809cb73616fb9407cbb554614394ccb"),
    240: (1038, "d2a10c08d23029c03b54366891c8d60b4e63ab57eac8c51bcf633b7bc9cab57b"),
    938: (2106, "5d15c2ad5c9e412e6b5ff278bf64fbd88a6a289157b73081e744470903d81345"),
}

ARCHIVIO = "a/0/1/2"
N_MEMBRI = 965
ARCHIVIO_DOPO_PREMI = 442264     # dopo SGP-1.2-BORSA-GEN-05 (premi_disfa)
ARCHIVIO_1_2_1 = 442616          # estensione FAT della 1.2.1 rilasciata
