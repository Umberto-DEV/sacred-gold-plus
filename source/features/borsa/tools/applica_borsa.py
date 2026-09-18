#!/usr/bin/env python3
"""SGP-1.2-BORSA-GEN-06 — applicatore del blocco `sgp.borsa`.

Scrive nella riserva ARM9 il blob del pacchetto 03 (`sgp.borsa`, 2048 B a
0x023DAD00), **genera la tabella dei siti permissivi rileggendo la ROM che sta
per patchare** e riscrive le due sole voci di `gScriptCmdTable` che servono
(0x020FAEF4 = [125] `ScrCmd_GiveItem`, 0x020FAEFC = [127]
`ScrCmd_HasSpaceForItem`).

Lavora SEMPRE su una copia: legge `--rom`, scrive `--uscita`, non tocca mai il
file di partenza. Se un cancello vola, NIENTE viene scritto.

ORDINE OBBLIGATO NELLA CATENA
-----------------------------
    1. `premi_disfa.py`   (BORSA-GEN-05)  REWARD-01 -> vanilla 1.03
    2. `applica_199.py`   (BORSA-GEN-08)  il messaggio 199#10
    3. appendici          (BORSA-GEN-09)  i 6 `MsgBoxExtern` in `a/0/1/2`
    4. **questo**                          blocco ARM9 + tabella dalla ROM

I primi tre cambiano i byte di `a/0/1/2`, e la chiave di un sito e' fatta di
offset e impronta dei suoi byte: la tabella va quindi generata per ULTIMA,
sulla ROM finale. Il pacchetto 09 e' ora una precondizione verificata:
l'applicatore accetta solo il suo NARC finale e le firme dei cinque membri
modificati.

COME SI IDENTIFICA UN SITO — e perche' NON per offset
-----------------------------------------------------
`premi_disfa` sposta quattro siti permissivi: le quattro `HasSpaceForItem` di
REWARD-01 vivono oggi nelle routine accodate ai membri 843/859/877 e tornano al
loro posto vanilla quando REWARD viene disfatto. Le appendici del pacchetto 09
soprascrivono 6 byte in cinque membri (3, 141, 145, 240, 938) e ne accodano
altrettante routine. Il confronto con il censimento firmato non puo' quindi
essere «stesso offset, stessa impronta» e basta.

Identita' di un sito = **(membro, comando, numero d'ordine nel flusso)**, dove
il numero d'ordine e' la posizione del sito fra i siti dello STESSO comando
dello STESSO membro, in ordine di offset. Il cancello e' per membro e per
comando:

  a) i siti che non si sono mossi si riconoscono da soli (offset e impronta
     identici al censimento firmato);
  b) quel che resta, da una parte e dall'altra, deve essere coperto ESATTAMENTE
     da uno spostamento DICHIARATO qui sotto, con la sua motivazione;
  c) se un residuo non e' coperto, o se le voci non sono 110, non si scrive
     niente.

ONESTA' SUL «NUMERO D'ORDINE». Il numero d'ordine da solo NON e' invariante
attraverso `premi_disfa`, e la ROM lo dimostra: nel membro 843 i siti
permissivi 127 stanno a 1155, 4370, 4439, 5525, 5613 prima e a 1155, 2387,
4165, 4370, 4439 dopo — l'ordinale 1 passa da 4370 a 2387, cioe' da un sito a
un altro. Per questo il legame sito-per-sito lo porta la tabella
`SPOSTAMENTI_PREMI` (offset firmato -> offset atteso, con motivo), e il numero
d'ordine viene calcolato e REGISTRATO nel rapporto come nome leggibile del
sito, non usato come chiave di accoppiamento. L'insieme per (membro, comando)
resta il cancello vero: e' l'insieme che finisce in tabella.

LA FINESTRA DELL'IMPRONTA — una differenza misurata, non un dettaglio
---------------------------------------------------------------------
`scr_disasm.chiave_sito` calcola l'impronta sui byte
`[max(header_end, fine-32), fine)`: si ferma alla fine dell'intestazione del
membro. Il blob in ARM9 (`sorgenti/borsa.c`, `sgp_chiave`) calcola invece
`disp = script_ptr - mapScripts + 6` e `n = min(32, disp)`: il suo pavimento e'
il **byte 0 del membro**, non la fine dell'intestazione — `mapScripts` e'
l'inizio del membro (`script_manager.c:213`), e il banco di prova del
pacchetto 03 lo verifica (caso t1m).

Su 110 siti la differenza morde UNA volta sola: **membro 145 @1048**, la cui
istruzione finisce a 1056 mentre l'intestazione del membro finisce a 1026. Il
censimento firmato registra l'impronta su 30 byte (0x6815); il gancio, a
runtime, ne calcolera' 32. Se in tabella finisse il valore del censimento,
quel sito non sarebbe mai riconosciuto e gli oggetti nascosti del banco 145
resterebbero al comportamento vanilla.

In tabella va quindi **l'impronta che il gancio calcolera'** — quella su 32
byte con pavimento a 0. Il cancello B5f lo dice per ogni sito: verifica le due
impronte, esige che coincidano ovunque tranne nei casi dichiarati in
`FINESTRA_DIVERSA`, e il rapporto registra entrambi i valori.

CANCELLI
--------
    B0  build: manifesto, blob, canarino, trampolini agli offset fissi.
    B1  censimento firmato: sha256 del TSV, 110 righe, chiavi ben formate.
    B2  idempotenza: una ROM che ha gia' il gancio viene RIFIUTATA.
    B3  preimmagini: 2048 B a zero nel blocco; le due voci di
        `gScriptCmdTable` valgono ancora 0x0204E9D9 e 0x0204EA89.
    B3b la catena a monte e' passata: `a/0/1/2` misura 442 524 B ed e' l'uscita
        firmata delle appendici; i membri 843/859/877 sono al vanilla 1.03
        (premi_disfa), e il banco 199 ha 11 messaggi (applica_199). Senza
        questo cancello l'applicatore
        accetterebbe la 1.2.1 nuda: su di essa i 110 siti firmati si ritrovano
        tutti, perche' il censimento e' stato fatto proprio li'.
    B4  il blocco cade nella zona 1.2 della riserva (e, con `--manifest`, non
        si sovrappone a nessun blocco prenotato).
    B5  la tabella generata dalla ROM: 110 voci, ogni sito ritrovato, ogni
        spostamento dichiarato, chiavi uniche su TUTTI i siti 125/127.
    B6  scrittura: blob, puntatori agli originali (letti PRIMA di riscrivere
        la tabella dei comandi), staffetta a zero, tabella, canarino.
    B7  controllo positivo: si rilegge tutto dai byte.
    B8  conteggio esatto: cambiano 2048 + 8 byte e nessun altro; la ROM non
        cambia lunghezza.
    B9  le altre 851 voci di `gScriptCmdTable` sono bit per bit le originali.

Uso:
    applica_borsa.py --rom IN.nds --uscita OUT.nds [--build DIR]
                     [--censimento TSV] [--manifest MAPPA.json] [--report F]
GPL-3.0-or-later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
PAC = QUI.parent                                   # source/features/borsa
REPO = PAC.parents[2]                              # radice del checkout

sys.path.insert(0, str(REPO / "source"))
sys.path.insert(0, str(QUI))

from sgp12.rom import Arm9, Rifiuto, esigi, posizioni_diverse, sha  # noqa: E402
import scr_disasm as SD  # noqa: E402

BUILD_DEFAULT = REPO / "source" / "sgp12" / "build" / "borsa"
CENSIMENTO_DEFAULT = PAC / "permissivi-1.2.tsv"
SCRCMD_DEFAULT = (Path(os.environ["SGP_PRET_SOURCE"]) / "tools/py_scripts/scrcmd.json"
                  if os.environ.get("SGP_PRET_SOURCE") else None)

# --------------------------------------------------------------- il blocco
# PRENOTAZIONE.md §1 e §4 del pacchetto 03. Ridichiarati qui: il manifesto e'
# controllato contro queste costanti, non il contrario.
BLOCCO_BASE = 0x023DAD00
BLOCCO_N = 0x800                                   # 2048 B
OFF_CODICE = 0x000
OFF_ORIG127 = 0x5E0
OFF_ORIG125 = 0x5E4
OFF_STAFFETTA = 0x5F0
N_STAFFETTA = 8
OFF_TABELLA = 0x600
N_TABELLA = 120                                    # voci u32
OFF_CANARINO = 0x7F0
N_CANARINO = 16
MAX_CODICE = OFF_ORIG127                           # 1504 B
CANARINO_MOTIVO = 0xCA5A1700
ZONA_1_2 = (0x023D8000, 0x023DEB40)

TRAMPOLINI = {"sgp_borsa_cmd127": 0x000, "sgp_borsa_cmd125": 0x008}

# ------------------------------------------------------- gScriptCmdTable
# RAPPORTO.md §2 del pacchetto 03: la tabella sta a 0x020FAD00 nell'ARM9
# STATICO (scrivibile in ROM, non .bss); le due voci sono 125 e 127.
GSCRIPTCMDTABLE = 0x020FAD00
N_COMANDI = 853
VOCE_125 = GSCRIPTCMDTABLE + 4 * 125               # 0x020FAEF4
VOCE_127 = GSCRIPTCMDTABLE + 4 * 127               # 0x020FAEFC
VAN_125 = 0x0204E9D9                               # ScrCmd_GiveItem, Thumb
VAN_127 = 0x0204EA89                               # ScrCmd_HasSpaceForItem

# --------------------------------------------------------- il censimento
# sha256 di `permissivi-1.2.tsv` firmato da SGP-1.2-BORSA-GEN-02. Se il file
# cambia, questo numero non combacia piu' e l'applicatore si ferma: la firma
# non e' un commento, e' un cancello.
CENSIMENTO_SHA = "894e674dc1e9471ef855554eae5caadb08d1c18dedbdf751a42ddc5f7e7c0ea5"
CENSIMENTO_VOCI = 110

CMD_GIVE_ITEM = 125
CMD_HAS_SPACE = 127
NOMI_CMD = {CMD_GIVE_ITEM: "GiveItem", CMD_HAS_SPACE: "HasSpaceForItem"}
LUNG_ISTR = 8
FINESTRA = 32
CLASSI_PERMISSIVE = {"DONO_GRATUITO", "RACCOLTA_A_TERRA", "OGGETTO_NASCOSTO"}

# La lista nera di `REVISIONE.md` §2: due siti che il classificatore automatico
# chiama permissivi e che la revisione a mano di BORSA-GEN-02 ha tolto, perche'
# il prelievo di valuta e' fuori dalla portata di qualunque analisi del
# bytecode. Devono essere PRESENTI e permissivi per il classificatore (se non
# lo fossero, la ROM non sarebbe quella che crediamo) e devono restare FUORI
# dalla tabella.
NERI = {
    (144, CMD_HAS_SPACE, 505):
        "banco consegne, regalo della mamma: la coda MomGiftQueue e' alimentata "
        "solo da acquisti pagati col salvadanaio (src/mom_gift.c:69-70), "
        "prelievo in codice nativo — REVISIONE.md §2.1",
    (904, CMD_HAS_SPACE, 660):
        "Daily Drawing Corner di Fiordoropoli: SubMoneyImmediate 300 a @363 sta "
        "tre livelli di chiamata sopra il sito — REVISIONE.md §2.2",
}

# Spostamenti DICHIARATI. Chiave: (membro, comando, offset nel censimento
# firmato). Valore: (offset atteso dopo la catena, motivo).
#
# I quattro di `premi_disfa`: gli offset di arrivo sono i «ganci» di
# `reward_fix.CALLERS`, cioe' il posto che la HasSpaceForItem occupava nel
# vanilla 1.03 prima che REWARD-01 le mettesse sopra un GoTo di 6 byte
# (premi_disfa.py, costante CALLERS: 859 -> 306, 877 -> 306, 843 -> 2387 e
# 4165). Qui sono RIDIGITATI, non importati: se `premi_disfa` cambiasse idea,
# questo file deve contraddirlo, non seguirlo.
SPOSTAMENTI_PREMI = {
    (843, CMD_HAS_SPACE, 5525): (
        2387,
        "premi_disfa: REWARD-01 disfatto. La HasSpaceForItem del primo ingresso "
        "al laboratorio di Elm torna dalla routine accodata (@5525, fuori dal "
        "membro vanilla di 5468 B) al suo posto vanilla @2387."),
    (843, CMD_HAS_SPACE, 5613): (
        4165,
        "premi_disfa: come sopra, secondo ingresso al laboratorio di Elm "
        "(@5613 -> @4165)."),
    (859, CMD_HAS_SPACE, 573): (
        306,
        "premi_disfa: dono di Falkner (MT51). @573 stava nella routine accodata "
        "da REWARD-01 (membro vanilla 516 B); torna a @306."),
    (877, CMD_HAS_SPACE, 514): (
        306,
        "premi_disfa: dono di Furio/Chuck (MT01). @514 stava nella routine "
        "accodata da REWARD-01 (membro vanilla 457 B); torna a @306."),
}

# Punto d'innesto per il pacchetto 09 (appendici del messaggio 199#10).
#
# Le 6 appendici soprascrivono 6 byte con un `GoTo` nei membri 3, 141, 145,
# 240 e 938, e accodano la routine in fondo al membro. L'impronta di un sito e'
# calcolata sui byte che TERMINANO con la sua istruzione, e i punti d'innesto
# stanno tutti DOPO il rispettivo `GiveItem` (U §3.4: «dopo l'ultimo messaggio
# del dono, prima del Return»): in linea di principio nessuna chiave cambia, e
# l'accodamento non muove nessun offset. Ma «in linea di principio» non e' un
# cancello: se una chiave cambiasse, il pacchetto 09 aggiunge qui la riga
# (membro, comando, offset firmato) -> (nuovo offset, motivo) e il rapporto la
# registra. Il dizionario resta vuoto perche' la catena finale con il pacchetto
# 09 ha dimostrato che nessuna chiave dei membri 3, 141, 145, 240, 938 cambia.
SPOSTAMENTI_APPENDICI: dict = {}

MEMBRI_APPENDICI = (3, 141, 145, 240, 938)

# ------------------------------------------------------ la catena a monte
# L'ordine dei passi non e' una raccomandazione: e' un cancello. Senza questo
# controllo l'applicatore accetterebbe anche la ROM 1.2.1 nuda — su di essa i
# 110 siti firmati si ritrovano tutti al loro posto (il censimento e' stato
# fatto proprio li'), la tabella sarebbe coerente con QUELLA ROM, e nessuno si
# accorgerebbe che REWARD-01 e il messaggio non sono mai passati. Misurato:
# senza B3b, `applica()` sulla 1.2.1 nuda passa tutti i cancelli.
#
# I numeri sono RIDIGITATI dalle costanti VANILLA e ARCHIVIO_VANILLA di
# `premi_disfa.py`, dai rapporti di `applica_199.py` e dall'uscita verificata
# di `applica_appendici.py`. Non sono importati: se quei file cambiassero idea,
# questo deve contraddirli.
NARC_SCRIPT = "a/0/1/2"
NARC_MESSAGGI = "a/0/2/7"
ARCHIVIO_SCRIPT_VANILLA = 442264
ARCHIVIO_SCRIPT_FINALE = 442524
ARCHIVIO_SCRIPT_FINALE_SHA = "b1144f1572c5efe8a4a5ce50386ec569ee782bb55ef4b85c56ad458094986e29"
ARCHIVIO_SCRIPT_CON_REWARD = 442616
MEMBRI_VANILLA = {
    843: (5468, "cb690bc3b229515e11dda13d691f354e0d39905597b7b2d2abd3bafb200862d1"),
    859: (516, "5abff969bd83c4975cf0815c2f5c7c28d581cb2ecae994ca3049123918d41f9e"),
    877: (457, "742f3f4fe75ecc952fa8fbbdc9ecee56c5f743f5199d864eb2725721cc2f4f00"),
}
FIRME_APPENDICI = {
    3: (6163, "fdde73cfa414a6e773f15b1ba04c9e1615669eda1ea3a73250c17b869f70e98a"),
    141: (6652, "4d95a52d22458f98d14cf09d30fc50b28a0a72cfe91012e3796a7a3de0a0630a"),
    145: (1548, "12795b2518150834fb06d625c5a6e9104077982a607eccc59323b221917b9d67"),
    240: (1082, "3bfcee24c0bf46f73bfa3871f3927b6b477f37a096deea196586b55627430d14"),
    938: (2150, "ce0704e5edeccb895c8214b91d0317e0ea35b81cd9899828a7f7c62a02ab0c80"),
}
BANCO_199 = 199
MSG_199_ATTESI = 11          # 10 in vanilla + il messaggio 199#10 del pacchetto 08

# Siti in cui la finestra dell'impronta del censimento (pavimento a
# `header_end`) e quella del gancio (pavimento a 0) NON coincidono. Ogni voce
# e' (membro, comando, offset firmato) -> motivo. Vedi la docstring in testa.
FINESTRA_DIVERSA = {
    (145, CMD_HAS_SPACE, 1048):
        "l'istruzione finisce a 1056 e l'intestazione del membro 145 finisce a "
        "1026: il censimento usa 30 byte, il gancio ne usa 32 (i due byte in "
        "piu' sono la coda dell'intestazione). In tabella va l'impronta del "
        "gancio, altrimenti gli oggetti nascosti del banco 145 non sarebbero "
        "mai riconosciuti.",
}


# ===========================================================================
# il censimento generato dalla ROM
# ===========================================================================
def fnv16_gancio(raw: bytes, fine: int) -> int:
    """L'impronta ESATTAMENTE come la calcola `sgp_chiave` in `borsa.c`:
    pavimento al byte 0 del membro (`mapScripts`), non alla fine
    dell'intestazione."""
    n = FINESTRA if fine > FINESTRA else fine
    h = 0x811C9DC5
    for x in raw[fine - n:fine]:
        h = ((h ^ x) * 0x01000193) & 0xFFFFFFFF
    return h & 0xFFFF


def leggi_censimento_firmato(percorso: Path):
    grezzo = Path(percorso).read_bytes()
    firma = hashlib.sha256(grezzo).hexdigest()
    esigi(firma == CENSIMENTO_SHA,
          "B1: il censimento firmato ha sha256 %s, atteso %s: non e' il file "
          "firmato da SGP-1.2-BORSA-GEN-02" % (firma, CENSIMENTO_SHA))
    voci = []
    for n, riga in enumerate(grezzo.decode("utf-8").splitlines(), 1):
        if not riga.strip():
            continue
        campi = riga.split("\t")
        esigi(len(campi) == 5, "B1: riga %d del censimento: %d campi, attesi 5" % (n, len(campi)))
        membro, nome, off, imp, classe = campi
        esigi(nome in ("HasSpaceForItem", "GiveItem"),
              "B1: riga %d: comando '%s' non e' ganciato" % (n, nome))
        esigi(classe in CLASSI_PERMISSIVE,
              "B1: riga %d: classe '%s' non e' permissiva" % (n, classe))
        voci.append({"membro": int(membro), "comando": nome, "offset": int(off),
                     "impronta16": int(imp), "classe": classe})
    esigi(len(voci) == CENSIMENTO_VOCI,
          "B1: il censimento ha %d voci, attese %d" % (len(voci), CENSIMENTO_VOCI))
    chiavi = {(v["membro"], v["comando"], v["offset"]) for v in voci}
    esigi(len(chiavi) == len(voci), "B1: il censimento ha righe doppie")
    return voci, firma


def censisci_rom(percorso_rom, scrcmd_json):
    """Rilegge `a/0/1/2` dalla ROM e rifa' il censimento con gli strumenti
    firmati del pacchetto 01. Rende (permissivi, tutti_i_siti_ganciati,
    membri, byte_archivio)."""
    cmds = SD.Comandi(Path(scrcmd_json))
    files, dim = SD.carica_narc(str(percorso_rom))
    membri = SD.disassembla_tutto(files, cmds)
    siti = SD.censisci(membri, raggio=0)

    permissivi, ganciati = [], []
    for s in siti:
        if s["comando"] not in ("HasSpaceForItem", "GiveItem"):
            continue
        m = membri[s["membro"]]
        fine = s["offset"] + LUNG_ISTR
        voce = {
            "membro": s["membro"], "comando": s["comando"], "opcode": s["opcode"],
            "offset": s["offset"], "classe": s["classe"],
            "impronta_censimento": s["chiave"]["impronta16"],
            "finestra_censimento": s["chiave"]["finestra"],
            "impronta_gancio": fnv16_gancio(m.raw, fine),
            "header_end": m.header_end,
        }
        ganciati.append(voce)
        if s["classe"] in CLASSI_PERMISSIVE:
            permissivi.append(voce)

    # numero d'ordine nel flusso: posizione fra i siti dello stesso comando
    # dello stesso membro, in ordine di offset. Calcolato su TUTTI i siti
    # ganciati del membro, non solo sui permissivi.
    per_membro: dict = {}
    for v in sorted(ganciati, key=lambda v: (v["membro"], v["comando"], v["offset"])):
        k = (v["membro"], v["comando"])
        v["ordinale"] = per_membro.get(k, 0)
        per_membro[k] = v["ordinale"] + 1
    ordinali = {(v["membro"], v["comando"], v["offset"]): v["ordinale"] for v in ganciati}
    for v in permissivi:
        v["ordinale"] = ordinali[(v["membro"], v["comando"], v["offset"])]
    return permissivi, ganciati, membri, dim


def _nome(v):
    return "membro %d / %s / n.%d (@%d)" % (v["membro"], v["comando"],
                                            v.get("ordinale", -1), v["offset"])


def genera_tabella(percorso_rom, scrcmd_json, firmato, log):
    """B5. Rende (voci_tabella, diagnostica). Ogni voce e' un dict con la
    chiave u32 che finira' in ROM."""
    permissivi, ganciati, membri, dim_archivio = censisci_rom(percorso_rom, scrcmd_json)
    diag = {"archivio_byte": dim_archivio,
            "siti_ganciati": len(ganciati),
            "permissivi_grezzi": len(permissivi),
            "lista_nera": [], "invariati": 0, "spostati": [],
            "finestra_diversa": [], "ordinali": {}}

    # --- B5a: la lista nera della revisione a mano --------------------------
    per_off = {(v["membro"], v["comando"], v["offset"]): v for v in permissivi}
    tenuti = []
    for v in permissivi:
        k = (v["membro"], v["opcode"], v["offset"])
        if k in NERI:
            diag["lista_nera"].append({"sito": _nome(v), "motivo": NERI[k]})
            continue
        tenuti.append(v)
    mancanti_neri = [k for k in NERI if (k[0], NOMI_CMD[k[1]], k[2]) not in per_off]
    esigi(not mancanti_neri,
          "B5a: i siti della lista nera non sono piu' classificati permissivi dal "
          "programma: %s. La ROM o il classificatore sono cambiati: la revisione "
          "a mano di BORSA-GEN-02 non descrive piu' questa ROM." % mancanti_neri)

    # --- B5b: il numero di voci --------------------------------------------
    esigi(len(tenuti) == CENSIMENTO_VOCI,
          "B5b: la ROM da' %d siti permissivi (lista nera esclusa), il censimento "
          "firmato ne ha %d: non si scrive niente" % (len(tenuti), CENSIMENTO_VOCI))

    # --- B5c: accoppiamento con il censimento firmato -----------------------
    trovati = {(v["membro"], v["comando"], v["offset"]): v for v in tenuti}
    attesi = {(v["membro"], v["comando"], v["offset"]): v for v in firmato}
    coppie = []          # (voce firmata, voce trovata, stato, motivo)
    residui_attesi, usati = [], set()
    for k, a in attesi.items():
        t = trovati.get(k)
        if t is None:
            residui_attesi.append(a)
            continue
        esigi(t["impronta_censimento"] == a["impronta16"],
              "B5c: %s si trova al suo offset ma con impronta %#06x invece di "
              "%#06x: i byte del sito sono cambiati senza che nessuno lo abbia "
              "dichiarato" % (_nome(t), t["impronta_censimento"], a["impronta16"]))
        esigi(t["classe"] == a["classe"],
              "B5c: %s ha cambiato classe: %s invece di %s"
              % (_nome(t), t["classe"], a["classe"]))
        coppie.append((a, t, "invariato", ""))
        usati.add(k)
        diag["invariati"] += 1

    residui_trovati = [v for k, v in trovati.items() if k not in usati]
    spostamenti = dict(SPOSTAMENTI_PREMI)
    for k, v in SPOSTAMENTI_APPENDICI.items():
        esigi(k not in spostamenti, "B5c: spostamento dichiarato due volte: %r" % (k,))
        spostamenti[k] = v

    for a in residui_attesi:
        opk = (a["membro"], CMD_GIVE_ITEM if a["comando"] == "GiveItem" else CMD_HAS_SPACE,
               a["offset"])
        esigi(opk in spostamenti,
              "B5c: il sito firmato membro %d / %s @%d non si ritrova nella ROM e "
              "nessuno spostamento e' dichiarato per lui. Se e' un effetto voluto "
              "di un passo della catena, va DICHIARATO in SPOSTAMENTI_* con la sua "
              "motivazione; se no, la ROM e' sbagliata."
              % (a["membro"], a["comando"], a["offset"]))
        nuovo_off, motivo = spostamenti[opk]
        cand = [v for v in residui_trovati
                if v["membro"] == a["membro"] and v["comando"] == a["comando"]
                and v["offset"] == nuovo_off]
        esigi(len(cand) == 1,
              "B5c: lo spostamento dichiarato per membro %d / %s @%d -> @%d non "
              "trova un sito permissivo all'arrivo (candidati: %d)"
              % (a["membro"], a["comando"], a["offset"], nuovo_off, len(cand)))
        t = cand[0]
        esigi(t["classe"] == a["classe"],
              "B5c: %s e' arrivato con classe %s invece di %s"
              % (_nome(t), t["classe"], a["classe"]))
        residui_trovati.remove(t)
        coppie.append((a, t, "spostato", motivo))
        diag["spostati"].append({
            "da": "membro %d / %s @%d (impronta %#06x)"
                  % (a["membro"], a["comando"], a["offset"], a["impronta16"]),
            "a": "membro %d / %s @%d n.%d (impronta %#06x)"
                 % (t["membro"], t["comando"], t["offset"], t["ordinale"],
                    t["impronta_gancio"]),
            "motivo": motivo})

    esigi(not residui_trovati,
          "B5c: la ROM ha %d siti permissivi che il censimento firmato non prevede: "
          "%s" % (len(residui_trovati), [_nome(v) for v in residui_trovati[:5]]))

    # --- B5d: le appendici non hanno mosso nessuna chiave -------------------
    if not SPOSTAMENTI_APPENDICI:
        mossi = [_nome(t) for a, t, stato, _ in coppie
                 if stato == "spostato" and t["membro"] in MEMBRI_APPENDICI]
        esigi(not mossi,
              "B5d: SPOSTAMENTI_APPENDICI e' vuoto ma i membri delle appendici "
              "hanno siti spostati: %s. Il pacchetto 09 deve dichiararli." % mossi)

    # --- B5e: finestra dell'impronta ---------------------------------------
    for a, t, _stato, _ in coppie:
        if t["impronta_gancio"] == t["impronta_censimento"]:
            continue
        k = (a["membro"], CMD_GIVE_ITEM if a["comando"] == "GiveItem" else CMD_HAS_SPACE,
             a["offset"])
        esigi(k in FINESTRA_DIVERSA,
              "B5e: %s ha impronta %#06x per il censimento (finestra %d) e %#06x "
              "per il gancio (finestra 32) e la differenza non e' dichiarata"
              % (_nome(t), t["impronta_censimento"], t["finestra_censimento"],
                 t["impronta_gancio"]))
        esigi(t["finestra_censimento"] < FINESTRA,
              "B5e: %s: le due impronte differiscono ma la finestra del censimento "
              "e' gia' di %d byte: non e' il caso dichiarato"
              % (_nome(t), t["finestra_censimento"]))
        diag["finestra_diversa"].append({
            "sito": _nome(t), "censimento": "%#06x su %d B"
            % (t["impronta_censimento"], t["finestra_censimento"]),
            "gancio": "%#06x su 32 B" % t["impronta_gancio"],
            "motivo": FINESTRA_DIVERSA[k]})

    # --- B5f: chiavi ben formate e uniche su TUTTI i siti ganciati ----------
    voci = []
    for a, t, stato, motivo in coppie:
        esigi(0 < t["offset"] <= 0xFFFF,
              "B5f: %s ha un offset che non sta in 16 bit" % _nome(t))
        chiave = ((t["offset"] & 0xFFFF) << 16) | (t["impronta_gancio"] & 0xFFFF)
        esigi(chiave != 0, "B5f: %s produce la chiave 0, che chiude la tabella" % _nome(t))
        voci.append({"membro": t["membro"], "comando": t["comando"],
                     "ordinale": t["ordinale"], "offset": t["offset"],
                     "classe": t["classe"], "stato": stato, "motivo": motivo,
                     "impronta_gancio": t["impronta_gancio"],
                     "impronta_censimento": t["impronta_censimento"],
                     "chiave": chiave})

    viste: dict = {}
    for v in ganciati:
        k = ((v["offset"] & 0xFFFF) << 16) | (v["impronta_gancio"] & 0xFFFF)
        viste.setdefault(k, []).append(v)
    collisioni = {("%#010x" % k): [_nome(x) for x in g] for k, g in viste.items() if len(g) > 1}
    esigi(not collisioni,
          "B5f: la chiave (offset, impronta a 32 B) NON e' unica su tutti i siti "
          "125/127 della ROM finale: %s. Il gancio non saprebbe decidere."
          % json.dumps(collisioni)[:600])

    esigi(len(voci) <= N_TABELLA,
          "B5f: %d voci non entrano nei %d posti della tabella" % (len(voci), N_TABELLA))
    voci.sort(key=lambda v: v["chiave"])
    diag["ordinali"] = [
        {"membro": v["membro"], "comando": v["comando"],
         "offset": v["offset"], "ordinale": v["ordinale"]}
        for v in voci
    ]
    log["cancelli"].append({
        "cancello": "B5", "esito": "passato",
        "nota": "%d voci generate dalla ROM: %d invariate, %d spostate "
                "(dichiarate), %d in lista nera, %d con finestra diversa"
                % (len(voci), diag["invariati"], len(diag["spostati"]),
                   len(diag["lista_nera"]), len(diag["finestra_diversa"]))})
    return voci, diag


# ===========================================================================
# la build del pacchetto 03
# ===========================================================================
def carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()

    esigi(sha(blob) == man["blob"]["sha256"], "B0: blob.bin non e' quello del manifesto")
    esigi(sha(canarino) == man["canarino"]["sha256"],
          "B0: canarino.bin non e' quello del manifesto")
    ind = man["indirizzi"]
    esigi(int(ind["base"], 16) == BLOCCO_BASE,
          "B0: il manifesto e' compilato per la base %s, non per %#010x"
          % (ind["base"], BLOCCO_BASE))
    esigi(ind["blocco_byte"] == BLOCCO_N, "B0: il manifesto dichiara un blocco di %d B"
          % ind["blocco_byte"])
    esigi(int(ind["canarino"], 16) == BLOCCO_BASE + OFF_CANARINO,
          "B0: il manifesto mette il canarino altrove")
    esigi(int(ind["tabella"], 16) == BLOCCO_BASE + OFF_TABELLA,
          "B0: il manifesto mette la tabella altrove")
    esigi(ind["tabella_voci"] == N_TABELLA, "B0: la tabella del manifesto ha %d voci"
          % ind["tabella_voci"])
    esigi(int(ind["originali"], 16) == BLOCCO_BASE + OFF_ORIG127,
          "B0: il manifesto mette i puntatori agli originali altrove")
    esigi(int(ind["staffetta"], 16) == BLOCCO_BASE + OFF_STAFFETTA,
          "B0: il manifesto mette la staffetta altrove")
    ganci = ind["ganci"]
    esigi(int(ganci["gScriptCmdTable"], 16) == GSCRIPTCMDTABLE,
          "B0: il manifesto dichiara gScriptCmdTable altrove")
    esigi(int(ganci["voce_125"], 16) == VOCE_125 and int(ganci["voce_127"], 16) == VOCE_127,
          "B0: il manifesto dichiara altre due voci di tabella")
    esigi(int(ganci["originale_125"], 16) == VAN_125
          and int(ganci["originale_127"], 16) == VAN_127,
          "B0: il manifesto dichiara altri due originali")

    esigi(len(blob) <= MAX_CODICE, "B0: il blob (%d B) non entra prima dei puntatori"
          % len(blob))
    esigi(len(canarino) == N_CANARINO, "B0: canarino di %d B" % len(canarino))
    atteso = b"".join((CANARINO_MOTIVO | i).to_bytes(4, "little")
                      for i in range(N_CANARINO // 4))
    esigi(canarino == atteso, "B0: il canarino non segue il motivo %#010x" % CANARINO_MOTIVO)

    bersagli = {}
    for nome, off in TRAMPOLINI.items():
        esigi(nome in man["simboli"], "B0: simbolo mancante: %s" % nome)
        v = int(man["simboli"][nome], 16)
        esigi(v & 1, "B0: %s non ha il bit Thumb" % nome)
        esigi((v & ~1) == BLOCCO_BASE + off,
              "B0: %s sta a %#010x invece che a +%#05x: l'applicatore scrive i due "
              "puntatori conoscendo solo la base" % (nome, v & ~1, off))
        bersagli[nome] = v
    for nome, valore in man["simboli"].items():
        if nome.startswith("$"):
            continue
        v = int(valore, 16) & ~1
        esigi(BLOCCO_BASE <= v < BLOCCO_BASE + len(blob),
              "B0: il simbolo '%s' (%s) cade fuori dal blob" % (nome, valore))
    return man, blob, canarino, bersagli


def verifica_catena_a_monte(rom_path, log):
    """B3b: la ROM in ingresso e' gia' passata da `premi_disfa`,
    `applica_199` e `applica_appendici`. Se non lo fosse, la tabella sarebbe
    generata su byte che stanno ancora per cambiare."""
    import ndspy.narc
    import ndspy.rom

    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))
    script = rom.getFileByName(NARC_SCRIPT)
    esigi(len(script) != ARCHIVIO_SCRIPT_CON_REWARD,
          "B3b: %s misura %d B, cioe' porta ancora REWARD-01: `premi_disfa.py` "
          "(BORSA-GEN-05) non e' stato eseguito. L'ordine della catena e' "
          "premi_disfa -> applica_199 -> appendici -> borsa."
          % (NARC_SCRIPT, len(script)))
    esigi(len(script) == ARCHIVIO_SCRIPT_FINALE and sha(script) == ARCHIVIO_SCRIPT_FINALE_SHA,
          "B3b: %s misura %d B / %s, atteso %d B / %s dopo `premi_disfa` e "
          "`applica_appendici`. L'applicatore Borsa accetta solo i byte finali "
          "verificati del pacchetto 09."
          % (NARC_SCRIPT, len(script), sha(script)[:16], ARCHIVIO_SCRIPT_FINALE,
             ARCHIVIO_SCRIPT_FINALE_SHA[:16]))
    membri = ndspy.narc.NARC(script).files
    for idx, (n, firma) in sorted(MEMBRI_VANILLA.items()):
        letto = bytes(membri[idx])
        esigi(len(letto) == n and sha(letto) == firma,
              "B3b: il membro %d di %s misura %d B / %s, atteso %d B / %s: "
              "REWARD-01 non e' stato disfatto come previsto"
              % (idx, NARC_SCRIPT, len(letto), sha(letto)[:16], n, firma[:16]))
    for idx, (n, firma) in sorted(FIRME_APPENDICI.items()):
        letto = bytes(membri[idx])
        esigi(len(letto) == n and sha(letto) == firma,
              "B3b: il membro %d di %s non e' l'uscita verificata di "
              "`applica_appendici`: %d B / %s, atteso %d B / %s"
              % (idx, NARC_SCRIPT, len(letto), sha(letto)[:16], n, firma[:16]))

    banco = ndspy.narc.NARC(rom.getFileByName(NARC_MESSAGGI)).files[BANCO_199]
    quanti = struct.unpack_from("<H", banco, 0)[0]
    esigi(quanti == MSG_199_ATTESI,
          "B3b: il banco %d di %s ha %d messaggi, attesi %d: `applica_199.py` "
          "(BORSA-GEN-08) non e' stato eseguito, e il gancio accenderebbe "
          "il flag 'scartato' per un messaggio che non esiste"
          % (BANCO_199, NARC_MESSAGGI, quanti, MSG_199_ATTESI))
    log["catena_a_monte"] = {
        "%s_byte" % NARC_SCRIPT: len(script),
        "%s_sha256" % NARC_SCRIPT: sha(script),
        "membri_vanilla": sorted(MEMBRI_VANILLA),
        "membri_appendici": sorted(FIRME_APPENDICI),
        "banco_199_messaggi": quanti,
    }


def verifica_manifest_mappa(manifest_path, log):
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    lo, hi = BLOCCO_BASE, BLOCCO_BASE + BLOCCO_N
    visto = False
    for b in mappa["blocchi"]:
        base = int(b["base"], 16)
        n = b.get("bytes", 0)
        if b["nome"] == "sgp.borsa":
            esigi(base == BLOCCO_BASE and n == BLOCCO_N,
                  "B4/mappa: la voce 'sgp.borsa' non e' quella attesa")
            visto = True
            continue
        esigi(not (base < hi and base + n > lo),
              "B4/mappa: '%s' copre ancora %08X..%08X: la prenotazione di sgp.borsa "
              "non e' stata scalata" % (b["nome"], lo, hi))
    esigi(visto, "B4/mappa: nessuna voce 'sgp.borsa' nel registro della riserva")
    log["manifest_controllato"] = True


# ===========================================================================
# l'applicazione
# ===========================================================================
class GiaApplicato(Rifiuto):
    """Il blocco c'e' gia': si rifiuta invece di riscriverlo."""


def corpo_tabella(voci):
    parole = [v["chiave"] for v in voci] + [0] * (N_TABELLA - len(voci))
    return struct.pack("<%dI" % N_TABELLA, *parole)


def applica(rom_path, build_dir, censimento_path, scrcmd_json, manifest_path=None):
    log = {"strumento": "source/features/borsa/tools/applica_borsa.py", "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    man, blob, canarino, bersagli = carica_build(build_dir)
    ok("B0", "manifesto coerente, blob %d B, trampolini a +0x000 e +0x008" % len(blob))

    firmato, firma = leggi_censimento_firmato(censimento_path)
    log["censimento_firmato"] = {"file": str(censimento_path), "sha256": firma,
                                 "voci": len(firmato)}
    ok("B1", "censimento firmato: %d voci, sha256 %s" % (len(firmato), firma[:16]))

    r = Arm9(rom_path)
    prima = bytes(r.raw)
    log["sha256_ingresso"] = sha(prima)
    log["bytes_ingresso"] = len(prima)

    # --- B2: idempotenza ----------------------------------------------------
    v125 = r.u32(VOCE_125)
    v127 = r.u32(VOCE_127)
    dentro = lambda a: BLOCCO_BASE <= (a & ~1) < BLOCCO_BASE + BLOCCO_N  # noqa: E731
    if dentro(v125) or dentro(v127):
        raise GiaApplicato(
            "B2: gScriptCmdTable[125]=%#010x e [127]=%#010x puntano gia' dentro "
            "sgp.borsa: questa ROM ha gia' il gancio. Riapplicare non e' un no-op, "
            "e' un errore di procedura: si parte da una ROM fresca." % (v125, v127))
    ok("B2", "la ROM non era patchata")

    # --- B3: preimmagini ----------------------------------------------------
    esigi(v125 == VAN_125, "B3: gScriptCmdTable[125] vale %#010x, atteso %#010x"
          % (v125, VAN_125))
    esigi(v127 == VAN_127, "B3: gScriptCmdTable[127] vale %#010x, atteso %#010x"
          % (v127, VAN_127))
    blocco = r.leggi(BLOCCO_BASE, BLOCCO_N)
    if blocco != bytes(BLOCCO_N):
        primo = next(i for i, b in enumerate(blocco) if b)
        raise Rifiuto("B3: i %d byte di %08X non sono tutti a zero (primo diverso "
                      "a +%#05x)" % (BLOCCO_N, BLOCCO_BASE, primo))
    ok("B3", "area 0x%08X..0x%08X a zero; le due voci valgono ancora gli originali"
       % (BLOCCO_BASE, BLOCCO_BASE + BLOCCO_N))

    # --- B3b: la catena a monte e' passata ----------------------------------
    verifica_catena_a_monte(rom_path, log)
    ok("B3b", "%s a %d B con i 3 membri vanilla e i 5 membri appendici, "
       "banco 199 con %d messaggi"
       % (NARC_SCRIPT, log["catena_a_monte"]["%s_byte" % NARC_SCRIPT],
          log["catena_a_monte"]["banco_199_messaggi"]))

    # --- B4: zona della riserva --------------------------------------------
    esigi(ZONA_1_2[0] <= BLOCCO_BASE and BLOCCO_BASE + BLOCCO_N <= ZONA_1_2[1],
          "B4: il blocco esce dalla zona 1.2 della riserva")
    verifica_manifest_mappa(manifest_path, log)
    ok("B4", "il blocco cade nella zona 1.2")

    # --- B5: la tabella, generata dalla ROM ---------------------------------
    voci, diag = genera_tabella(rom_path, scrcmd_json, firmato, log)
    log["tabella"] = diag

    # --- B6: scrittura ------------------------------------------------------
    # I puntatori agli originali si scrivono con quel che c'era PRIMA nella
    # tabella dei comandi (v125/v127, letti sopra): se un giorno un'altra patch
    # ci arrivasse prima, la catena si incatena invece di sparire.
    tabella = corpo_tabella(voci)
    r.scrivi(BLOCCO_BASE + OFF_CODICE, blob)
    r.scrivi(BLOCCO_BASE + OFF_ORIG127, struct.pack("<II", v127, v125))
    r.scrivi(BLOCCO_BASE + OFF_STAFFETTA, bytes(N_STAFFETTA))
    r.scrivi(BLOCCO_BASE + OFF_TABELLA, tabella)
    r.scrivi(BLOCCO_BASE + OFF_CANARINO, canarino)
    r.scrivi(VOCE_127, struct.pack("<I", bersagli["sgp_borsa_cmd127"]))
    r.scrivi(VOCE_125, struct.pack("<I", bersagli["sgp_borsa_cmd125"]))
    ok("B6", "blob, 2 puntatori agli originali, staffetta a zero, %d voci di "
             "tabella, canarino, 2 voci di gScriptCmdTable" % len(voci))

    # --- B7: controllo positivo --------------------------------------------
    esigi(r.leggi(BLOCCO_BASE, len(blob)) == blob, "B7: blob riletto diverso")
    esigi(r.leggi(BLOCCO_BASE + OFF_CANARINO, N_CANARINO) == canarino,
          "B7: canarino riletto diverso")
    esigi(r.leggi(BLOCCO_BASE + OFF_TABELLA, len(tabella)) == tabella,
          "B7: tabella riletta diversa")
    esigi(r.u32(BLOCCO_BASE + OFF_ORIG127) == VAN_127
          and r.u32(BLOCCO_BASE + OFF_ORIG125) == VAN_125,
          "B7: i puntatori agli originali non sono quelli letti dalla tabella")
    esigi(r.u32(VOCE_127) == bersagli["sgp_borsa_cmd127"]
          and r.u32(VOCE_125) == bersagli["sgp_borsa_cmd125"],
          "B7: le due voci di gScriptCmdTable non puntano ai trampolini")
    esigi(r.leggi(BLOCCO_BASE + len(blob), OFF_ORIG127 - len(blob))
          == bytes(OFF_ORIG127 - len(blob)), "B7: la coda del codice non e' a zero")
    esigi(r.leggi(BLOCCO_BASE + OFF_STAFFETTA, 0x10) == bytes(0x10),
          "B7: la staffetta non e' a zero")
    ok("B7", "tutto riletto dai byte della ROM prodotta")

    # --- B8: conteggio esatto ----------------------------------------------
    dopo = bytes(r.raw)
    esigi(len(dopo) == len(prima), "B8: la ROM ha cambiato lunghezza")
    leciti = set(range(r.off(BLOCCO_BASE), r.off(BLOCCO_BASE) + BLOCCO_N))
    leciti |= set(range(r.off(VOCE_125), r.off(VOCE_125) + 4))
    leciti |= set(range(r.off(VOCE_127), r.off(VOCE_127) + 4))
    diversi = posizioni_diverse(prima, dopo)
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "B8: %d byte cambiati FUORI dalle regioni dichiarate (primo: %#x)"
          % (len(fuori), fuori[0] if fuori else 0))
    ok("B8", "%d byte cambiati: il blocco (2048 B) e 8 byte in gScriptCmdTable"
       % len(diversi))

    # --- B9: le altre 851 voci ---------------------------------------------
    a = r.off(GSCRIPTCMDTABLE, 4 * N_COMANDI)
    tab_prima = prima[a:a + 4 * N_COMANDI]
    tab_dopo = dopo[a:a + 4 * N_COMANDI]
    cambiate = [i for i in range(N_COMANDI)
                if tab_prima[4 * i:4 * i + 4] != tab_dopo[4 * i:4 * i + 4]]
    esigi(cambiate == [125, 127],
          "B9: le voci cambiate di gScriptCmdTable sono %s, attese [125, 127]" % cambiate)
    ok("B9", "851 voci su 853 sono bit per bit le originali")

    log.update(esito="applicato", byte_diversi=len(diversi),
               uscita_sha256=sha(dopo), uscita_bytes=len(dopo),
               blob={"byte": len(blob), "sha256": sha(blob),
                     "manifesto": man["blob"]["sha256"]},
               canarino_sha256=sha(canarino),
               tabella_sha256=sha(tabella),
               voci=[{"membro": v["membro"], "comando": v["comando"],
                      "ordinale": v["ordinale"], "offset": v["offset"],
                      "impronta": "%#06x" % v["impronta_gancio"],
                      "chiave": "%#010x" % v["chiave"], "classe": v["classe"],
                      "stato": v["stato"], "motivo": v["motivo"]} for v in voci])
    return dopo, log


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--uscita", type=Path, required=True)
    ap.add_argument("--build", type=Path, default=BUILD_DEFAULT)
    ap.add_argument("--censimento", type=Path, default=CENSIMENTO_DEFAULT)
    ap.add_argument("--scrcmd", type=Path, default=SCRCMD_DEFAULT)
    ap.add_argument("--manifest", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    a = ap.parse_args(argv)

    if a.scrcmd is None:
        ap.error("--scrcmd oppure SGP_PRET_SOURCE e' obbligatorio")

    esigi(not a.uscita.exists() or a.uscita.resolve() != a.rom.resolve(),
          "l'uscita non puo' essere la ROM di partenza")
    try:
        dopo, log = applica(a.rom, a.build, a.censimento, a.scrcmd, a.manifest)
    except GiaApplicato as exc:
        print("RIFIUTO (gia' applicato): %s" % exc, file=sys.stderr)
        return 3
    except Rifiuto as exc:
        print("RIFIUTO: %s" % exc, file=sys.stderr)
        return 2

    a.uscita.parent.mkdir(parents=True, exist_ok=True)
    a.uscita.write_bytes(dopo)
    testo = json.dumps(log, indent=2, ensure_ascii=False)
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(testo + "\n", encoding="utf-8")
    print("\n".join("%-4s %s  %s" % (c["cancello"], c["esito"], c["nota"])
                    for c in log["cancelli"]))
    print("uscita %s  sha256 %s" % (a.uscita, log["uscita_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
