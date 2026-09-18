#!/usr/bin/env python3
"""sgp12.estrai_build — estrae dai blob CANONICI di una ROM 1.2 già costruita
(la ROM 1.2 prodotta da `costruisci.py`, in una cartella privata)
i byte esatti che ogni blocco scrive, e li salva in `sgp12/build/<blocco>/` con
`origine.json` (ROM di provenienza, sha256, data) e `SHA256SUMS`.

Perché: i blob compilati che si trovano nelle cartelle `prove/build/` dei
cantieri storici sono candidati di collaudo, non necessariamente lo stesso
byte compilato che è finito nella ROM di release (misurato: il blob `sgp.anim`
di `SGP-1.2-ANIM-B-02/prove/build/` differiva di 152 B dal blob VERO, ricompilato
con un compilatore/opzioni leggermente diversi). Estrarre dalla ROM stessa,
invece di ricompilare o fidarsi di una cartella `prove/`, resta valido anche
quando la ROM cambia per la rifinitura in corso: si ri-estrae e basta.

Non modifica la ROM letta. Non scrive nella cartella ROM di lavoro condivisa.

Uso:
    python3 -m sgp12.estrai_build --rom sgp-1.2.2-EN.nds --lingua EN [--build sgp12/build]
    python3 -m sgp12.estrai_build --rom sgp-1.2.2-IT.nds --lingua IT

Blocchi estratti: npc, anim, opzioni (+ testi/voci per lingua), plus,
salvataggio, wifi. `riserva`, `camera` e `guida` (GUIDA-EVIV-02: patch
chirurgica di 96 byte fissi, nessun blob) non hanno bisogno di estrazione:
sono deterministici (nessun blob esterno, solo costanti — per riserva anche
`MAPPA-RISERVA-ARM9.json`),
e già verificati byte-identici in `test_lib.py`. `testi` (LINGUA-04) non è un
blob a indirizzo fisso ma una trasformazione di `CORREZIONI.tsv`: non è
estraibile allo stesso modo, vedi README.md §5.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import struct
import sys
import traceback
from pathlib import Path

from .rom import Arm9, Rifiuto, bl_decode, sha
from . import overlay as ovp

BUILD_DEFAULT = Path(__file__).resolve().parent / "build"


def _e_manifesto_di_compilazione(esistente: dict, sha_blob: str | None) -> bool:
    """Il manifesto gia' presente e' stato scritto da `compila.py` /
    `compila_tutti.py` E descrive PROPRIO il blob che stiamo scrivendo?

    Due condizioni, tutte e due necessarie:

    1. porta `comando` e `compilatore`, cioe' la riga di compilazione: e' la
       firma dei manifesti di compilazione, che i manifesti estratti non hanno;
    2. il suo `blob.sha256` e' lo sha del blob che stiamo scrivendo ora. Senza
       questo, un manifesto di compilazione VECCHIO regalerebbe i suoi simboli a
       un blob diverso — che e' il difetto M3/M10 con un passaggio in piu'.
    """
    if not (esistente.get("comando") and esistente.get("compilatore")):
        return False
    if sha_blob is None:
        return False
    return (esistente.get("blob") or {}).get("sha256") == sha_blob


def _fondi_manifesto(dest: Path, nuovo: dict, decodificati: tuple = (),
                     sha_blob: str | None = None) -> dict:
    """Fonde il manifesto nuovo con quello gia' presente in `dest`.

    M3/M10 della revisione R1. Prima, questa funzione RESUSCITAVA i simboli:
    `estrai_anim` scrive `sgp_idle_stop` solo se il gancio G2 e' presente nella
    ROM, e la fusione lo riportava indietro dal manifesto vecchio — da li' in
    poi `anim.applica` avrebbe installato una BL verso un indirizzo che la ROM
    non contiene, e `anim.rileggi` avrebbe confrontato la ROM con lo STESSO
    manifesto, restando verde. Applicatore e rilettore condividevano la
    costante sbagliata.

    Regola nuova, in due parti:

    1. `decodificati` elenca i simboli di cui QUESTO estrattore risponde. Se
       uno di essi non e' nel manifesto nuovo, l'estrazione FALLISCE: il
       simbolo non e' piu' decodificabile dalla ROM, e un valore vecchio non
       vale come risposta.
    2. i simboli che l'estrattore non produce mai (quelli emessi dal
       compilatore: `$d`, `$t`, i nomi interni del blob) NON si conservano per
       il solo fatto di essere scritti da qualche parte. Si conservano SOLO se
       il manifesto che li porta e' un manifesto di COMPILAZIONE
       (`compila.py` / `compila_tutti.py`: ha `comando` e `compilatore`) e
       descrive proprio questo blob (stesso `blob.sha256`). Allora quei valori
       hanno una fonte — la tabella dei simboli dell'oggetto da cui e' uscito
       QUESTO blob — e restano, elencati in
       `simboli_non_verificati_dalla_rom` perche' nessuno li ha riletti dalla
       ROM. In tutti gli altri casi si BUTTANO, e finiscono in
       `simboli_scartati`: un valore senza fonte non e' un dato, e il punto 1
       era stato scritto proprio per non tenerne.

    Prima di questa correzione il ramo 2 conservava tutto, sempre: bastava che
    un simbolo fosse comparso una volta in `build/<blocco>/manifesto.json`
    perche' sopravvivesse a qualunque estrazione, anche su una ROM in cui quel
    blob era cambiato."""
    for nome in decodificati:
        if nome not in (nuovo.get("simboli") or {}):
            raise Rifiuto(
                "estrazione: il simbolo '%s' non e' decodificabile da questa ROM. "
                "Non viene ripreso dal manifesto precedente: un simbolo stantio "
                "sopravvissuto e' esattamente il difetto M3 della revisione R1." % nome)
    esistente_path = dest / "manifesto.json"
    if not esistente_path.exists():
        return nuovo
    esistente = json.loads(esistente_path.read_text())
    fuso = dict(esistente)
    vecchi = dict(esistente.get("simboli") or {})
    freschi = dict(nuovo.get("simboli") or {})
    candidati = {k: v for k, v in vecchi.items() if k not in freschi and k not in decodificati}
    da_compilazione = _e_manifesto_di_compilazione(esistente, sha_blob)
    conservati = candidati if da_compilazione else {}
    scartati = {} if da_compilazione else candidati
    fuso["simboli"] = {**conservati, **freschi}
    if conservati:
        fuso["simboli_non_verificati_dalla_rom"] = sorted(conservati)
    else:
        fuso.pop("simboli_non_verificati_dalla_rom", None)
    if scartati:
        fuso["simboli_scartati"] = {
            "nomi": sorted(scartati),
            "perche": "il manifesto precedente non e' un manifesto di compilazione di "
                      "QUESTO blob (serve `comando` + `compilatore` e lo stesso "
                      "`blob.sha256`), quindi i suoi simboli non hanno piu' una fonte: "
                      "non vengono ripresi. Per riaverli, ricompilare il blob con "
                      "`features/**/tools/compila*.py`, che i simboli li legge "
                      "dall'oggetto.",
        }
    else:
        fuso.pop("simboli_scartati", None)
    fuso["indirizzi"] = {**esistente.get("indirizzi", {}), **nuovo.get("indirizzi", {})}
    for k, v in nuovo.items():
        if k not in ("simboli", "indirizzi"):
            fuso[k] = v
    return fuso


def _scrivi(build_dir: Path, blocco: str, files: dict, origine: dict,
            decodificati: tuple = (), blob_file: str = "blob.bin"):
    dest = Path(build_dir) / blocco
    dest.mkdir(parents=True, exist_ok=True)
    if "manifesto.json" in files:
        # `blob_file` e' il file che il campo `blob` del manifesto descrive: e'
        # lui a dire se un manifesto di compilazione gia' presente parla di
        # QUESTO blob o di un altro.
        corpo = files.get(blob_file)
        sha_blob = sha(corpo) if isinstance(corpo, (bytes, bytearray)) else None
        files["manifesto.json"] = _fondi_manifesto(dest, files["manifesto.json"],
                                                   decodificati, sha_blob)
    for nome, dati in files.items():
        (dest / nome).write_bytes(dati) if isinstance(dati, (bytes, bytearray)) \
            else (dest / nome).write_text(json.dumps(dati, indent=2, ensure_ascii=False) + "\n")
    origine_path = dest / "origine.json"
    esistente = json.loads(origine_path.read_text()) if origine_path.exists() else {}
    esistente[origine["lingua"]] = origine
    origine_path.write_text(json.dumps(esistente, indent=2, ensure_ascii=False) + "\n")
    righe = []
    for p in sorted(dest.iterdir()):
        if p.is_file() and p.name not in ("SHA256SUMS",):
            righe.append("%s  %s" % (hashlib.sha256(p.read_bytes()).hexdigest(), p.name))
    (dest / "SHA256SUMS").write_text("\n".join(righe) + "\n")


def _origine(rom_path: Path, rom: bytes, lingua: str) -> dict:
    return {"lingua": lingua, "rom": str(rom_path), "sha256": sha(rom),
           "bytes": len(rom), "estratto_il": datetime.date.today().isoformat()}


def _trim_zeri(dati: bytes) -> bytes:
    """Toglie gli zeri finali: il chiamante scrive `blob` seguito da zeri fino
    al confine dichiarato, quindi la lunghezza VERA del blob compilato è fino
    all'ultimo byte non nullo (mai zero byte interni: sarebbero .bss, non
    dentro un .text Thumb)."""
    n = len(dati)
    while n > 0 and dati[n - 1] == 0:
        n -= 1
    return dati[:n]


def estrai_npc(a: Arm9, rom: bytes, lingua: str, build_dir: Path):
    from .blocchi import npc as B
    blocco = a.leggi(B.BLOCK_BASE, B.BLOCK_N)
    blob = _trim_zeri(blocco[B.OFF_BLOB:B.OFF_BLOB + B.N_BLOB_SLOT])
    rom_ovp = ovp.Rom(rom)
    _, _, img = rom_ovp.immagine_overlay(B.OV_CAMPO)
    off_g = B.A_GANCIO - (rom_ovp.voce_overlay(B.OV_CAMPO)["ram"])
    gancio = bl_decode(B.A_GANCIO, bytes(img[off_g:off_g + 4]))
    if gancio is None:
        raise Rifiuto("estrazione npc: a %#x non c'e' una BL decodificabile, "
                      "quindi 'sgp_npc_hook' non e' leggibile da questa ROM"
                      % B.A_GANCIO)
    # M10 della revisione R1: `sgp_npc_tetto` era COSTRUITO
    # (`BLOCK_BASE + OFF_BLOB + 1`), non decodificato — e quel valore e' il
    # secondo byte del blob, non la funzione. Un simbolo inventato soddisfaceva
    # il controllo di presenza di `ENTRATE_ATTESE` senza controllare nulla:
    # meglio non dichiararlo affatto.
    man = {"indirizzi": {"codice": hex(B.BLOCK_BASE + B.OFF_BLOB), "stato": hex(B.BLOCK_BASE + B.OFF_STATO)},
          "blob": {"byte": len(blob), "sha256": sha(blob)},
          "simboli": {"sgp_npc_hook": hex(gancio | 1)}}
    _scrivi(build_dir, "npc", {"blob.bin": blob, "manifesto.json": man},
           _origine(Path("<rom>"), rom, lingua), decodificati=("sgp_npc_hook",))
    return {"blob_bytes": len(blob), "gancio": hex(gancio)}


def estrai_anim(a: Arm9, rom: bytes, lingua: str, build_dir: Path):
    from .blocchi import anim as B
    from .rom import bl_decode
    blocco = a.leggi(B.BLOCK_BASE, B.BLOCK_N)
    blob = _trim_zeri(blocco[B.OFF_CODICE:B.OFF_CODICE + B.MAX_CODICE])
    canarino = bytes(blocco[B.OFF_CANARINO:B.OFF_CANARINO + B.N_CANARINO])
    tab_u = bytes(blocco[B.OFF_TABELLE:B.OFF_TABELLE + 32])
    par = bytes(blocco[B.OFF_TABELLE + 32:B.OFF_TABELLE + 64])
    rom_ovp = ovp.Rom(rom)
    _, _, img = rom_ovp.immagine_overlay(B.OV_CAMPO)
    off_g = B.A_GANCIO - rom_ovp.voce_overlay(B.OV_CAMPO)["ram"]
    codice_thumb = struct.unpack_from("<I", img, off_g)[0]
    simboli = {"sgp_idle_task2": hex(codice_thumb)}
    # G2 (v4, SGP-1.2-ANIM-SOLIDO-01): BL a sgp_idle_stop in coda a
    # ov12_02262014. Assente su una ROM v3: decodificato solo se presente
    # (bl_decode rende None sui 4 byte vanilla/non-BL).
    off_g2 = B.A_G2 - rom_ovp.voce_overlay(B.OV_CAMPO)["ram"]
    bersaglio_g2 = bl_decode(B.A_G2, bytes(img[off_g2:off_g2 + 4]))
    if bersaglio_g2 is not None:
        simboli["sgp_idle_stop"] = hex(bersaglio_g2 | 1)
    # M6 della revisione R2: il manifesto di `anim` dichiarava tre indirizzi su
    # cinque. `tabelle` e `slot` sono quelli con cui il blob e' compilato
    # (-DSGP_ANIM2_TAB_ADDR / _SLOT_ADDR): senza dichiararli, un blob
    # ricompilato per un altro indirizzo veniva accettato in silenzio e andava
    # a leggere e scrivere 128 B di qualcun altro dentro la riserva.
    man = {"indirizzi": {"codice": hex(B.BLOCK_BASE + B.OFF_CODICE), "stato": hex(B.BLOCK_BASE + B.OFF_STATO),
                        "canarino": hex(B.BLOCK_BASE + B.OFF_CANARINO),
                        "tabelle": hex(B.BLOCK_BASE + B.OFF_TABELLE),
                        "slot": hex(B.BLOCK_BASE + B.OFF_SLOT)},
          "blob": {"byte": len(blob), "sha256": sha(blob)},
          "simboli": simboli}
    _scrivi(build_dir, "anim",
           {"blob.bin": blob, "canarino.bin": canarino, "tab_u.bin": tab_u, "par.bin": par,
            "manifesto.json": man},
           _origine(Path("<rom>"), rom, lingua),
           decodificati=("sgp_idle_task2", "sgp_idle_stop"))
    return {"blob_bytes": len(blob), "codice_thumb": hex(codice_thumb),
           "sgp_idle_stop": simboli.get("sgp_idle_stop")}


def estrai_opzioni(a: Arm9, rom: bytes, lingua: str, build_dir: Path):
    from .blocchi import opzioni as B
    blocco = a.leggi(B.BLOCK_BASE, B.BLOCK_N)
    blocco_t = a.leggi(B.TESTI_BASE, B.TESTI_N)
    o_codice, n_codice = B.PIANTA["codice"]
    o_tab, n_tab = B.PIANTA["tab"]
    o_tpl, n_tpl = B.PIANTA["tpl"]
    blob = _trim_zeri(bytes(blocco[o_codice:o_codice + n_codice]))
    tab = bytes(blocco[o_tab:o_tab + n_tab])
    tpl = struct.unpack_from("<8I", blocco, o_tpl)
    o_testi, n_testi = B.PIANTA_TESTI["testi"]
    testi = bytes(blocco_t[o_testi:o_testi + n_testi])
    rom_ovp = ovp.Rom(rom)
    _, _, img54 = rom_ovp.immagine_overlay(B.OV_A)
    v54 = rom_ovp.voce_overlay(B.OV_A)
    off_a = B.SITO_A - v54["ram"]
    gancio = bl_decode(B.SITO_A, bytes(img54[off_a:off_a + 4]))
    # Un gancio non decodificabile valeva `(None or 0) | 1`, cioe' **0x1**
    # scritto nel manifesto come se fosse l'indirizzo di `sgp_opz_hook`: un
    # numero inventato che l'applicatore avrebbe poi scritto in ov054 e il
    # rilettore riletto dallo STESSO manifesto, restando verde. E' lo stesso
    # difetto M4 gia' corretto per `estrai_plus`, che qui era rimasto.
    if gancio is None:
        raise Rifiuto("estrazione opzioni: a %#x non c'e' una BL decodificabile, "
                      "quindi 'sgp_opz_hook' non e' leggibile da questa ROM"
                      % B.SITO_A)
    # M10 della revisione R1: `sgp_ui_frame` era COSTRUITO (`BLOCK_BASE | 1`),
    # non decodificato. Il valore combacia con quello vero solo perche' quella
    # funzione sta per caso all'inizio del blob: non e' una verifica. Resta nel
    # manifesto come simbolo del compilatore (elencato fra quelli «non
    # verificati dalla ROM»), ma questo estrattore non lo inventa piu'.
    man = {"indirizzi": {"codice": hex(B.BLOCK_BASE), "testi": hex(B.TESTI_BASE),
                        "ris": hex(B.BLOCK_BASE + B.PIANTA["ris"][0]),
                        "tab": hex(B.BLOCK_BASE + B.PIANTA["tab"][0]),
                        "tpl": hex(B.BLOCK_BASE + o_tpl),
                        "stato": hex(B.BLOCK_BASE + B.PIANTA["stato"][0])},
          "simboli": {"sgp_opz_hook": hex(gancio | 1),
                      "sgp_cont_init": hex(tpl[0]), "sgp_cont_main": hex(tpl[1]), "sgp_cont_exit": hex(tpl[2]),
                      "sgp_new_init": hex(tpl[4]), "sgp_new_main": hex(tpl[5]), "sgp_new_exit": hex(tpl[6])},
          "blob": {"byte": len(blob), "sha256": sha(blob)}}
    _scrivi(build_dir, "opzioni",
           {"ui_blob.bin": blob, f"testi-{lingua}.bin": testi, f"voci-{lingua}.bin": tab,
            "manifesto.json": man},
           _origine(Path("<rom>"), rom, lingua),
           decodificati=("sgp_opz_hook", "sgp_cont_init", "sgp_cont_main", "sgp_cont_exit",
                         "sgp_new_init", "sgp_new_main", "sgp_new_exit"),
           blob_file="ui_blob.bin")
    return {"blob_bytes": len(blob), "gancio": hex(gancio)}


def estrai_plus(a: Arm9, rom: bytes, lingua: str, build_dir: Path):
    """Pianta DEFINITIVA (SGP-1.2-QUALITA-NATIVO-01, v-finale, applicata in
    luogo 12/09/2026): due blob di codice DENTRO `sgp.plus` (PLUS a +0x000,
    256 B; SALVATAGGIO a +0x120, 500 B — non piu' a +0x630 di `sgp.plus` ne'
    a 0x023D8730 in codice: si e' spostato QUI). tab_trainer/tab_wild/stato/
    canarino restano agli stessi offset di sempre (INVARIATI). Vedi
    MAPPA-RISERVA-ARM9.json, voce "sgp.plus"."""
    from .blocchi import plus_chunk as B

    blocco = a.leggi(B.PLUS_BASE, B.PLUS_N)
    blob_plus = _trim_zeri(bytes(blocco[B.OFF_BLOB_PLUS:B.OFF_BLOB_SALVA]))
    blob_salva = _trim_zeri(bytes(blocco[B.OFF_BLOB_SALVA:B.FINE_CODICE]))
    tab_trainer = bytes(blocco[B.OFF_TAB_TRN:B.OFF_TAB_TRN + 256])
    tab_wild = bytes(blocco[B.OFF_TAB_WLD:B.OFF_TAB_WLD + 256])
    stato = bytes(blocco[B.OFF_STATO:B.OFF_STATO + B.N_STATO])
    canarino = bytes(blocco[B.OFF_CANARY:B.OFF_CANARY + B.N_CANARY])

    bersagli_trainer = [bl_decode(s, a.leggi(s, 4)) for s in B.SITI_TRAINER]
    bersaglio_l0 = bl_decode(B.SITO_L0, a.leggi(B.SITO_L0, 4))
    bersaglio_s0 = bl_decode(B.SITO_S0, a.leggi(B.SITO_S0, 4))

    # sgp_wild_hook: sta dentro ov002 (guardia 0x02246C94), non nell'ARM9
    # statico. Decodificabile direttamente dalla ROM DEFINITIVA (a differenza
    # della vecchia catena a due passi PLUS-02/PLUS-03: qui non c'e' nessuna
    # rilocazione intermedia da inseguire, si legge il bersaglio VERO).
    rom_ovp = ovp.Rom(rom)
    bersaglio_wild = None
    for i in range(rom_ovp.n_overlay):
        v = rom_ovp.voce_overlay(i)
        if not (v["ram"] <= B.SITO_WILD < v["ram"] + v["ram_size"]):
            continue
        try:
            _, _, img = rom_ovp.immagine_overlay(i)
        except Exception:
            continue
        off_w = B.SITO_WILD - v["ram"]
        t = bl_decode(B.SITO_WILD, bytes(img[off_w:off_w + 4]))
        if t is not None and B.PLUS_BASE <= (t & ~1) < B.PLUS_BASE + B.PLUS_N:
            bersaglio_wild = t
            break

    # Un bersaglio non decodificato valeva `0 | 1` e finiva nel manifesto come
    # 0x1: un indirizzo inventato che `_carica_build` accettava perche'
    # controllava solo la presenza del nome (M4 della revisione R2).
    for nome, valore in (("sgp_trainer_hook", bersagli_trainer[0]), ("sgp_wild_hook", bersaglio_wild),
                        ("sgp_gancio_carica", bersaglio_l0), ("sgp_gancio_salva", bersaglio_s0)):
        if valore is None:
            raise Rifiuto("estrazione plus: '%s' non e' decodificabile da questa ROM" % nome)

    man = {"indirizzi": {"codice": hex(B.PLUS_BASE + B.OFF_BLOB_PLUS),
                        "codice_salva": hex(B.PLUS_BASE + B.OFF_BLOB_SALVA),
                        "tab_trainer": hex(B.PLUS_BASE + B.OFF_TAB_TRN),
                        "tab_wild": hex(B.PLUS_BASE + B.OFF_TAB_WLD),
                        "stato": hex(B.PLUS_BASE + B.OFF_STATO),
                        "canarino": hex(B.PLUS_BASE + B.OFF_CANARY)},
          "simboli": {"sgp_trainer_hook": hex(bersagli_trainer[0] | 1),
                      "sgp_wild_hook": hex(bersaglio_wild | 1),
                      "sgp_gancio_carica": hex(bersaglio_l0 | 1),
                      "sgp_gancio_salva": hex(bersaglio_s0 | 1)},
          "blob": {"byte": len(blob_plus), "sha256": sha(blob_plus)},
          "blob_salva": {"byte": len(blob_salva), "sha256": sha(blob_salva)}}
    _scrivi(build_dir, "plus",
           {"blob.bin": blob_plus, "salva_blob.bin": blob_salva,
            "tab_trainer.bin": tab_trainer, "tab_wild.bin": tab_wild,
            "stato.bin": stato, "canarino.bin": canarino, "manifesto.json": man},
           _origine(Path("<rom>"), rom, lingua),
           decodificati=("sgp_trainer_hook", "sgp_wild_hook", "sgp_gancio_carica", "sgp_gancio_salva"))
    return {"blob_bytes": len(blob_plus), "blob_salva_bytes": len(blob_salva),
           "bersagli_trainer": [hex(b) if b else None for b in bersagli_trainer],
           "sgp_wild_hook": hex(bersaglio_wild) if bersaglio_wild else None}


def estrai_salvataggio(a: Arm9, rom: bytes, lingua: str, build_dir: Path):
    """Blocco DATI `sgp.salvataggio` (0x023D8F00, 256 B): dalla v-finale
    contiene SOLO il buffer del chunk (32 B, resta a zero in ROM) e il
    canarino a +0xF0 — il codice si e' spostato dentro `sgp.plus` (vedi
    `estrai_plus`). Nessun blob qui: non e' piu' un blocco di codice."""
    BASE, N = 0x023D8F00, 256
    OFF_CANARY, N_CANARY = 0xF0, 16
    blocco = a.leggi(BASE, N)
    canarino = bytes(blocco[OFF_CANARY:OFF_CANARY + N_CANARY])
    man = {"indirizzi": {"base": hex(BASE), "canarino": hex(BASE + OFF_CANARY)}, "simboli": {}}
    _scrivi(build_dir, "salvataggio", {"canarino.bin": canarino, "manifesto.json": man},
           _origine(Path("<rom>"), rom, lingua))
    return {"canarino_bytes": len(canarino)}


def estrai_wifi(a: Arm9, rom: bytes, lingua: str, build_dir: Path):
    """v-finale (SGP-1.2-QUALITA-NATIVO-01, B5/B6/B8, applicata in luogo
    12/09/2026): blob 572 B (era 660 in WIFI-04/05), veneer G2/G3 con
    manutenzione cache aggiunta (stessa dimensione, 24/28 B, contenuto
    diverso), gancio G1 ripuntato (+0x47C nel blocco, era +0x2B5). Scrive in
    `wifi/vfinale/` (non `wifi/wifi04/`, superata: vedi README §2)."""
    BLOCK_BASE, BLOCK_N = 0x023DA000, 0x800
    OFF_VENEER2, N_VENEER2 = 0x000, 24
    OFF_VENEER3, N_VENEER3 = 0x020, 28
    OFF_CODICE = 0x250
    SITO_G1 = 0x020070A8

    blocco = a.leggi(BLOCK_BASE, BLOCK_N)
    v2 = bytes(blocco[OFF_VENEER2:OFF_VENEER2 + N_VENEER2])
    v3 = bytes(blocco[OFF_VENEER3:OFF_VENEER3 + N_VENEER3])
    blob = _trim_zeri(bytes(blocco[OFF_CODICE:BLOCK_N - 16]))
    bersaglio_g1 = bl_decode(SITO_G1, a.leggi(SITO_G1, 4))

    man = {"indirizzi": {"codice": hex(BLOCK_BASE + OFF_CODICE), "veneer_g2": hex(BLOCK_BASE + OFF_VENEER2),
                        "veneer_g3": hex(BLOCK_BASE + OFF_VENEER3), "dati": hex(BLOCK_BASE + 0x40),
                        "stato_w1": hex(BLOCK_BASE + 0x240)},
          "simboli": {"sgp_wfc_trampolino": hex(bersaglio_g1 | 1)} if bersaglio_g1 is not None else {},
          "blob": {"byte": len(blob), "sha256": sha(blob)},
          "veneer_g2": {"byte": len(v2), "sha256": sha(v2)},
          "veneer_g3": {"byte": len(v3), "sha256": sha(v3)}}
    _scrivi(build_dir / "wifi", "vfinale",
           {"blob.bin": blob, "veneer-g2.bin": v2, "veneer-g3.bin": v3, "manifesto.json": man},
           _origine(Path("<rom>"), rom, lingua), decodificati=("sgp_wfc_trampolino",))
    return {"blob_bytes": len(blob), "bersaglio_g1": hex(bersaglio_g1) if bersaglio_g1 else None}


BLOCCHI = {"npc": estrai_npc, "anim": estrai_anim, "opzioni": estrai_opzioni,
          "plus": estrai_plus, "salvataggio": estrai_salvataggio, "wifi": estrai_wifi}


def estrai(rom_path: Path, lingua: str, build_dir: Path) -> dict:
    """M8 della revisione R1: un blocco la cui estrazione fallisce lascia in
    `build/<blocco>/` i file PRECEDENTI (e il loro `SHA256SUMS`). Prima
    l'errore finiva in una chiave del rapporto e `main()` ritornava comunque 0:
    e' il canale per cui i metadati stantii di M3 sono sopravvissuti. Gli
    errori restano raccolti — cosi' una corsa dice TUTTI i blocchi che non
    riesce a estrarre, non solo il primo — ma `main()` esce diverso da zero."""
    rom = Path(rom_path).read_bytes()
    a = Arm9(rom_path)
    esiti = {}
    for nome, funzione in BLOCCHI.items():
        try:
            esiti[nome] = funzione(a, rom, lingua, build_dir)
        except Exception as e:
            esiti[nome] = {"errore": "%s: %s" % (type(e).__name__, e),
                           "traccia": traceback.format_exc().splitlines()[-8:]}
    return esiti


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--lingua", required=True, choices=("EN", "IT"))
    ap.add_argument("--build", default=str(BUILD_DEFAULT))
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    esiti = estrai(Path(a.rom), a.lingua, Path(a.build))
    # `_origine` scrive `<rom>` come segnaposto: qui si mette il percorso vero.
    origine_reale = {"rom": str(Path(a.rom).resolve())}
    for nome in BLOCCHI:
        for sotto in ([nome] if nome != "wifi" else ["wifi/vfinale"]):
            p = Path(a.build) / sotto / "origine.json"
            if p.exists():
                doc = json.loads(p.read_text())
                if a.lingua in doc:
                    doc[a.lingua]["rom"] = origine_reale["rom"]
                p.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")

    testo = json.dumps(esiti, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    print(testo)
    falliti = [n for n, v in esiti.items() if isinstance(v, dict) and "errore" in v]
    if falliti:
        print("ESTRAZIONE INCOMPLETA: %s — i file di quei blocchi in %s sono quelli "
              "PRECEDENTI, non quelli di questa ROM." % (", ".join(falliti), a.build),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
