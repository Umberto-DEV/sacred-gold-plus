#!/usr/bin/env python3
"""sgp12.rom — lettura/scrittura sicura di una ROM NDS, senza dipendenze esterne.

Consolida in un solo posto quello che prima viveva, IDENTICO byte per byte, in
12 copie di `tools/arm9.py` (SGP-1.2-CAMERA-01, PLUS-02, WIFI-02/03/04/05,
PRESTAZIONI-NPC-02/03, OPZIONI-02/04, ANIM-B-02/03: `shasum` conferma le 12
copie identiche) e nella classe `Rom` di `SGP-1.2-OVERLAY-01/tools/overlay_patch.py`
(copiata identica in altre 5 cartelle: ANIM-B-02/03, PRESTAZIONI-NPC-02/03,
OPZIONI-02).

Due viste sulla stessa ROM:

  * `Arm9`  — indirizzo RAM -> offset file, dentro il solo ARM9 statico
              (cammina i «module params» a 0xBA0, come fa il caricatore).
              Usata dai blocchi che scrivono byte dentro l'ARM9 (riserva,
              camera, npc, anim, opzioni, wifi, plus).
  * `Rom`   — header/FAT/tabella overlay (y9) della ROM intera. Usata da
              `sgp12.overlay` per leggere/riscrivere gli overlay compressi.

Nessuna delle due stampa mai un byte di ROM: sono librerie.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path


class Rifiuto(Exception):
    """Un cancello non e' superato. Niente viene scritto quando questo vola."""


def esigi(condizione, messaggio):
    if not condizione:
        raise Rifiuto(messaggio)


def sha(dati) -> str:
    """sha256 esadecimale di `dati` (era ridefinita, identica, in oltre 15 file
    del laboratorio 1.2: applica_*.py, rileggi_*.py, overlay_patch.py, ...)."""
    return hashlib.sha256(bytes(dati)).hexdigest()


def sha_file(percorso) -> str:
    """sha256 di un file letto a blocchi da 1 MiB.

    `sha(Path(p).read_bytes())` tiene in memoria l'intera immagine solo per
    farne l'impronta: 134 MB per riconoscere una HeartGold originale, che lo
    stadio 0 poi non usa (xdelta3 legge il file da solo). Qui non si tiene in
    memoria piu' di un blocco."""
    h = hashlib.sha256()
    with open(percorso, "rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


_BLOCCO_CONFRONTO = 1 << 20


def posizioni_diverse(a, b) -> list:
    """Tutte le posizioni in cui `a` e `b` differiscono, sull'INTERA immagine.

    Confronto a blocchi da 1 MiB: il confronto di fetta (C) scarta in un colpo
    i blocchi identici e solo dentro un blocco che differisce si scende al
    singolo byte. Il risultato e' lo stesso di un ciclo byte per byte su
    127 MB, ma senza il minuto di attesa che quello costa a ogni chiamata
    (`applica`, `rileggi` e i test lo usano piu' volte per ROM).

    Non porta nessuna conoscenza della ROM — confronta due sequenze di byte —
    quindi non e' una costante condivisa fra applicatore e rilettore: sta qui
    perche' vale la pena averne UNA sola.
    """
    n = min(len(a), len(b))
    fuori = []
    for inizio in range(0, n, _BLOCCO_CONFRONTO):
        fine = min(inizio + _BLOCCO_CONFRONTO, n)
        if a[inizio:fine] == b[inizio:fine]:
            continue
        fuori.extend(i for i in range(inizio, fine) if a[i] != b[i])
    fuori.extend(range(n, max(len(a), len(b))))
    return fuori


def esigi_manifesto_descrive(man: dict, corpo, chiave: str = "blob",
                             file: str = "blob.bin", blocco: str = "") -> None:
    """Il manifesto deve descrivere il file che gli sta ACCANTO: `byte` e
    `sha256`, tutti e due, e tutti e due giusti.

    M5 della revisione R2, e poi la revisione della 1.2.1: `build/npc/` aveva un
    manifesto che dichiarava uno sha256 diverso dal `blob.bin` che gli stava
    accanto — e diverso dal `SHA256SUMS` della stessa cartella — e nessuno li
    confrontava. La correzione era stata scritta in `blocchi/npc.py`, e solo li'.
    Le altre sei `_carica_build` erano rimaste com'erano: `anim` e `wifi` non
    guardavano affatto il manifesto, `plus` e `npc` lo guardavano SE il campo
    c'era (`if "blob" in man`), cioe' un manifesto senza quel campo passava per
    buono. Sei copie di una regola, con sei livelli di severita' diversi.

    Qui la regola e' una sola e non ha rami: il campo e' OBBLIGATORIO. Un
    manifesto che non dice quanti byte e quale sha256 non descrive niente, e un
    blob senza manifesto che lo descriva e' esattamente quello che questa
    funzione esiste per impedire."""
    dove = ("%s: " % blocco) if blocco else ""
    d = man.get(chiave)
    esigi(isinstance(d, dict),
          "%sBUILD: il manifesto non ha il campo '%s' che descrive %s "
          "(byte + sha256 sono obbligatori)" % (dove, chiave, file))
    atteso_byte, atteso_sha = d.get("byte"), d.get("sha256")
    esigi(isinstance(atteso_byte, int) and isinstance(atteso_sha, str),
          "%sBUILD: il campo '%s' del manifesto deve avere 'byte' (intero) e "
          "'sha256' (stringa): ha %r" % (dove, chiave, sorted(d)))
    esigi(atteso_byte == len(corpo) and atteso_sha == sha(corpo),
          "%sBUILD: %s (%d B, %s) non corrisponde al manifesto (%s B, %s)"
          % (dove, file, len(corpo), sha(corpo)[:16], atteso_byte, str(atteso_sha)[:16]))


# ------------------------------------------------------------------ STADIO 0
#
# I diciassette blocchi partono da una base 1.1. La base 1.1, pero', non e' una
# ROM che si possa distribuire ne' una che si possa chiedere a chi ricostruisce:
# era un artefatto intermedio, e chi non ce l'aveva non poteva ricostruire
# niente. Lo stadio 0 toglie quel vincolo — l'unico ingresso e' la HeartGold
# ORIGINALE della propria lingua, piu' un delta xdelta pubblico che contiene
# SOLO le differenze fra quella ROM e la base 1.1.
#
# Il pin `base11.json` dice, per lingua: che sha256 ha la ROM originale
# accettata, come si chiama il delta e che sha256 ha, che sha256 deve avere la
# base 1.1 che ne esce. Tutte e tre le impronte sono controllate: una sola che
# non torna e' un `Rifiuto`, mai una costruzione «quasi giusta».

PIN_BASE11 = Path(__file__).resolve().parent / "base11.json"

# Le chiavi che ogni lingua del pin deve avere, e cosa deve esserci dentro.
_PIN_PARTI = ("originale", "delta", "base_1_1")


def verifica_pin(pin: dict) -> dict:
    """Il pin descrive davvero due tratte? Controllo STRUTTURALE, non di merito:
    chiavi presenti, sha256 esadecimali di 64 caratteri, byte interi positivi.
    Le dimensioni plausibili (una HeartGold e' 134 MB, non 12 B) sono un test,
    non una regola di libreria: i test dello stadio 0 iniettano pin sintetici
    con file di pochi byte, e devono poterlo fare."""
    esigi(isinstance(pin, dict) and isinstance(pin.get("basi"), dict) and pin["basi"],
          "PIN: `base11.json` non ha il dizionario 'basi'")
    for chiave in ("encode_options", "decode_options"):
        esigi(isinstance(pin.get(chiave), list) and all(isinstance(x, str) for x in pin[chiave]),
              "PIN: '%s' deve essere una lista di stringhe" % chiave)
    for lingua, voce in pin["basi"].items():
        esigi(lingua in ("EN", "IT"), "PIN: lingua inattesa %r (solo EN e IT)" % lingua)
        for parte in _PIN_PARTI:
            d = voce.get(parte)
            esigi(isinstance(d, dict), "PIN: %s manca della sezione '%s'" % (lingua, parte))
            esigi(isinstance(d.get("nome"), str) and d["nome"],
                  "PIN: %s/%s non ha un 'nome'" % (lingua, parte))
            s = d.get("sha256")
            esigi(isinstance(s, str) and len(s) == 64 and all(c in "0123456789abcdef" for c in s),
                  "PIN: %s/%s non ha uno sha256 esadecimale di 64 caratteri: %r"
                  % (lingua, parte, s))
            esigi(isinstance(d.get("byte"), int) and d["byte"] > 0,
                  "PIN: %s/%s non ha un conteggio 'byte' intero positivo" % (lingua, parte))
        esigi(isinstance(voce["delta"].get("url"), str) and voce["delta"]["url"].startswith("https://"),
              "PIN: %s/delta non ha un 'url' https" % lingua)
    return pin


def carica_pin(percorso=None) -> dict:
    """Legge (e verifica) `sgp12/base11.json`. Nessuna cache: e' un file di un
    paio di kilobyte, e i test devono poterne iniettare un altro."""
    percorso = Path(percorso or PIN_BASE11)
    esigi(percorso.is_file(), "PIN: manca %s" % percorso)
    try:
        pin = json.loads(percorso.read_text())
    except ValueError as e:
        raise Rifiuto("PIN: %s non e' JSON valido: %s" % (percorso, e)) from None
    return verifica_pin(pin)


def classifica_base(sha_hex: str, pin: dict | None = None) -> dict:
    """Funzione PURA: dato uno sha256, dice che cos'e' quella ROM.

    Ritorna `{"tipo": "originale"|"base-1.1"|"sconosciuta", "lingua": "EN"|"IT"|None,
    "etichetta": str|None}`. Sta qui, separata da ogni lettura di file, perche'
    e' la regola che decide se lo stadio 0 serve, si salta o rifiuta: va potuta
    provare senza una ROM."""
    pin = pin or carica_pin()
    s = (sha_hex or "").strip().lower()
    for lingua, voce in pin["basi"].items():
        if s == voce["originale"]["sha256"]:
            return {"tipo": "originale", "lingua": lingua,
                    "etichetta": voce["originale"].get("etichetta", voce["originale"]["nome"])}
        if s == voce["base_1_1"]["sha256"]:
            return {"tipo": "base-1.1", "lingua": lingua,
                    "etichetta": voce["base_1_1"].get("etichetta", voce["base_1_1"]["nome"])}
    return {"tipo": "sconosciuta", "lingua": None, "etichetta": None}


def _elenco_accettato(pin: dict) -> str:
    righe = []
    for lingua, voce in pin["basi"].items():
        righe.append("  %s originale: %s (sha256 %s…, %d B)"
                     % (lingua, voce["originale"]["nome"],
                        voce["originale"]["sha256"][:16], voce["originale"]["byte"]))
    for lingua, voce in pin["basi"].items():
        righe.append("  %s base 1.1 gia' pronta: sha256 %s… (%d B)"
                     % (lingua, voce["base_1_1"]["sha256"][:16], voce["base_1_1"]["byte"]))
    return "\n".join(righe)


def xdelta3_eseguibile() -> str:
    """Il percorso di `xdelta3`, o un `Rifiuto` che dice come installarlo.

    `SGP_XDELTA3` ha la precedenza: serve a una macchina che lo tiene fuori dal
    PATH, e ai test, che ci mettono un finto decodificatore per provare lo
    stadio 0 senza nessuna ROM."""
    exe = os.environ.get("SGP_XDELTA3") or shutil.which("xdelta3")
    esigi(exe, "STADIO 0: serve `xdelta3` per ricavare la base 1.1 dalla HeartGold "
               "originale, e non e' nel PATH.\n"
               "  macOS:          brew install xdelta\n"
               "  Debian/Ubuntu:  sudo apt install xdelta3\n"
               "  altrove:        https://github.com/jmacd/xdelta\n"
               "Oppure passa a --base una base 1.1 gia' pronta, e lo stadio 0 si salta.")
    return exe


def trova_delta(lingua: str, delta=None, pin: dict | None = None, cartella=None) -> Path:
    """Dove sta il delta dello stadio 0: `--delta` se dato, altrimenti
    `$SGP_ROM_DIR/<nome del pin>`. Due posti soli, detti tutti e due quando
    non lo si trova."""
    pin = pin or carica_pin()
    esigi(lingua in pin["basi"], "STADIO 0: lingua %r non nel pin" % lingua)
    nome = pin["basi"][lingua]["delta"]["nome"]
    if delta:
        p = Path(delta)
        esigi(p.is_file(), "STADIO 0: --delta %s non esiste" % p)
        return p
    if cartella is None:
        cartella = os.environ.get("SGP_ROM_DIR")
    cercati = []
    if cartella:
        p = Path(cartella) / nome
        cercati.append(str(p))
        if p.is_file():
            return p
    else:
        cercati.append("$SGP_ROM_DIR non impostata")
    raise Rifiuto(
        "STADIO 0: manca il delta %s, cercato in:\n  %s\n"
        "Scaricalo una volta sola con:\n"
        "  python3 -m sgp12.scarica_base --destinazione \"$SGP_ROM_DIR\"\n"
        "oppure indicalo con --delta <percorso>. E' un file di differenze, non una ROM: "
        "vedi %s" % (nome, "\n  ".join(cercati), pin["basi"][lingua]["delta"]["url"]))


def prepara_base(percorso, lingua: str | None = None, delta=None,
                 pin: dict | None = None, cartella=None) -> tuple[bytes, dict]:
    """STADIO 0 — da quello che sta in `--base` alla base 1.1 su cui girano i
    diciassette blocchi.

    Tre casi, tre esiti:
      * HeartGold ORIGINALE riconosciuta -> applica il delta del pin con
        `xdelta3` in una cartella temporanea, verifica che ne esca esattamente
        la base 1.1 del pin e la restituisce;
      * base 1.1 gia' riconosciuta -> la restituisce com'e', con un avviso:
        lo stadio 0 non serve (compatibilita' con chi la base 1.1 ce l'ha);
      * qualunque altro sha256 -> `Rifiuto`, con l'elenco di cio' che e'
        accettato. Non si prova a costruire su una base che non si riconosce.

    Ritorna `(byte della base 1.1, rapporto dello stadio 0)`; il rapporto
    finisce nel JSON di `costruisci.py` e di `verifica.py`."""
    pin = pin or carica_pin()
    percorso = Path(percorso)
    esigi(percorso.is_file(), "STADIO 0: --base %s non esiste" % percorso)
    impronta = sha_file(percorso)
    c = classifica_base(impronta, pin)
    esigi(c["tipo"] != "sconosciuta",
          "STADIO 0: la ROM data non e' riconosciuta (sha256 %s, %d B).\nAccettate:\n%s"
          % (impronta, percorso.stat().st_size, _elenco_accettato(pin)))
    esigi(lingua in (None, c["lingua"]),
          "STADIO 0: --lingua %s, ma la ROM data e' %s (%s). La lingua si deduce dalla "
          "ROM: o passi quella giusta, o togli --lingua." % (lingua, c["lingua"], c["etichetta"]))
    lingua = c["lingua"]
    voce = pin["basi"][lingua]

    if c["tipo"] == "base-1.1":
        return percorso.read_bytes(), {
            "saltato": "base 1.1 fornita direttamente",
            "avviso": "AVVISO: --base e' gia' la base 1.1 %s (%s…): lo stadio 0 non serve e "
                      "non e' stato eseguito." % (lingua, impronta[:16]),
            "lingua": lingua, "base_sha256": impronta, "base_bytes": percorso.stat().st_size}

    d = trova_delta(lingua, delta, pin, cartella)
    letto, byte = sha_file(d), d.stat().st_size
    esigi(letto == voce["delta"]["sha256"] and byte == voce["delta"]["byte"],
          "STADIO 0: %s non e' il delta che il pin dichiara: letto sha256 %s (%d B), atteso "
          "%s (%d B). Scaricalo di nuovo con `python3 -m sgp12.scarica_base`; non applicare "
          "un delta che non si riconosce." % (d, letto, byte, voce["delta"]["sha256"],
                                              voce["delta"]["byte"]))

    exe = xdelta3_eseguibile()
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="sgp12-stadio0-") as tmp:
        uscita = Path(tmp) / voce["base_1_1"]["nome"]
        r = subprocess.run([exe, *pin["decode_options"], str(percorso), str(d), str(uscita)],
                           capture_output=True, text=True)
        esigi(r.returncode == 0,
              "STADIO 0: xdelta3 ha rifiutato %s su %s (codice %d):\n%s"
              % (d.name, percorso.name, r.returncode, (r.stderr or "").strip()[-600:]))
        fuori = uscita.read_bytes()
    secondi = round(time.time() - t0, 2)
    ottenuto = sha(fuori)
    esigi(ottenuto == voce["base_1_1"]["sha256"] and len(fuori) == voce["base_1_1"]["byte"],
          "STADIO 0: la base ricostruita non e' quella del pin: sha256 %s (%d B), atteso "
          "%s (%d B). Non si prosegue su una base che non e' quella attesa."
          % (ottenuto, len(fuori), voce["base_1_1"]["sha256"], voce["base_1_1"]["byte"]))
    return fuori, {
        "eseguito": True, "lingua": lingua,
        "base_originale": {"nome": percorso.name, "sha256": impronta,
                           "byte": percorso.stat().st_size, "etichetta": c["etichetta"]},
        "delta": {"percorso": str(d), "nome": d.name, "sha256": letto, "byte": byte},
        "xdelta3": {"eseguibile": exe, "opzioni": list(pin["decode_options"])},
        "base_1_1": {"nome": voce["base_1_1"]["nome"], "sha256": ottenuto, "byte": len(fuori)},
        "secondi": secondi}


# --------------------------------------------------------------------- CRC16

_TBL_CRC16 = (0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
              0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400)


def crc16(dati, crc=0xFFFF) -> int:
    """CRC16 dell'header di cartuccia DS (gbatek, «Header CRC16»)."""
    for b in dati:
        crc = (crc >> 4) ^ _TBL_CRC16[(crc ^ b) & 0xF]
        crc = (crc >> 4) ^ _TBL_CRC16[(crc ^ (b >> 4)) & 0xF]
    return crc & 0xFFFF


# ---------------------------------------------------------------------- ARM9

class Arm9:
    """Lettore/scrittore dell'ARM9 di una ROM NDS per indirizzo RAM.

    Non importa ndspy: cammina i «module params» a 0xBA0 dell'ARM9 statico per
    ricavare le sezioni di autoload, esattamente come fa il caricatore del
    gioco, e mappa ogni indirizzo RAM sull'offset nel FILE .nds.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.raw = bytearray(self.path.read_bytes())
        self.off9 = struct.unpack_from('<I', self.raw, 0x20)[0]
        self.ram9 = struct.unpack_from('<I', self.raw, 0x28)[0]
        self.siz9 = struct.unpack_from('<I', self.raw, 0x2C)[0]
        # parametri di modulo: 9 parole a 0xBA0 dentro l'ARM9 statico
        f = struct.unpack_from('<9I', self.raw, self.off9 + 0xBA0)
        self.tab0, self.tab1, self.dati0 = f[0], f[1], f[2]
        self.sezioni = []
        p = self.off9 + (self.tab0 - self.ram9)
        fine = self.off9 + (self.tab1 - self.ram9)
        while p < fine:
            self.sezioni.append(struct.unpack_from('<3I', self.raw, p))  # ram, size, bss
            p += 12
        # segmenti (ram, offset_file, bytes)
        self.segmenti = [(self.ram9, self.off9, self.dati0 - self.ram9)]
        off = self.off9 + (self.dati0 - self.ram9)
        for ram, size, _bss in self.sezioni:
            self.segmenti.append((ram, off, size))
            off += size

    # --- traduzione indirizzi -------------------------------------------
    def off(self, ram, n=1):
        for base, o, size in self.segmenti:
            if base <= ram and ram + n <= base + size:
                return o + (ram - base)
        raise KeyError('0x%08X+%d non e\' dentro nessun segmento ARM9' % (ram, n))

    def leggi(self, ram, n):
        o = self.off(ram, n)
        return bytes(self.raw[o:o + n])

    def scrivi(self, ram, dati):
        o = self.off(ram, len(dati))
        self.raw[o:o + len(dati)] = dati

    def u32(self, ram):
        return struct.unpack('<I', self.leggi(ram, 4))[0]

    def u16(self, ram):
        return struct.unpack('<H', self.leggi(ram, 2))[0]

    def salva(self, path):
        Path(path).write_bytes(bytes(self.raw))

    # --- ricerca di parole nell'ARM9 statico ------------------------------
    def cerca_parola(self, valore):
        """Ritorna gli indirizzi RAM dell'ARM9 STATICO che contengono `valore`."""
        ago = struct.pack('<I', valore)
        base, o, size = self.segmenti[0]
        blob = self.raw[o:o + size]
        fuori, i = [], 0
        while True:
            i = blob.find(ago, i)
            if i < 0:
                break
            if i % 4 == 0:
                fuori.append(base + i)
            i += 1
        return fuori


# ----------------------------------------------------------------- ROM (y9)

class Rom:
    """Vista sui byte di una ROM DS: header, FAT, tabella overlay ARM9 (y9).
    Legge; scrivere e' compito di chi chiama (vedi `sgp12.overlay.applica`)."""

    def __init__(self, dati):
        self.d = bytearray(dati)
        g = lambda o: struct.unpack_from("<I", self.d, o)[0]
        self.arm9_off, self.arm9_ram, self.arm9_len = g(0x20), g(0x28), g(0x2C)
        self.fat_off, self.fat_len = g(0x48), g(0x4C)
        self.ovt9_off, self.ovt9_len = g(0x50), g(0x54)
        self.n_overlay = self.ovt9_len // 32
        self.n_file = self.fat_len // 8

    def voce_overlay(self, oid):
        esigi(0 <= oid < self.n_overlay,
              "overlay %d fuori dalla tabella y9 (%d voci)" % (oid, self.n_overlay))
        off = self.ovt9_off + oid * 32
        (idv, ram, ramsz, bsssz, sis, sie, fid, comp) = struct.unpack_from("<8I", self.d, off)
        return {
            "offset_voce": off, "id": idv, "ram": ram, "ram_size": ramsz,
            "bss_size": bsssz, "static_init_start": sis, "static_init_end": sie,
            "file_id": fid, "parola_comp": comp,
            "dim_compressa": comp & 0xFFFFFF,
            "flag": (comp >> 24) & 0xFF,
            "compresso": bool((comp >> 24) & 1),
            "firmato": bool((comp >> 24) & 2),
        }

    def voce_fat(self, fid):
        esigi(0 <= fid < self.n_file, "file id %d fuori dalla FAT (%d voci)" % (fid, self.n_file))
        off = self.fat_off + fid * 8
        s, e = struct.unpack_from("<II", self.d, off)
        return {"offset_voce": off, "inizio": s, "fine": e, "bytes": e - s}

    def file_bytes(self, fid):
        f = self.voce_fat(fid)
        return bytes(self.d[f["inizio"]:f["fine"]])

    def capienza_slot(self, fid):
        """Byte disponibili per il file `fid` senza spostare nessun altro file:
        dal suo inizio al primo inizio di file successivo (o alla fine della ROM)."""
        f = self.voce_fat(fid)
        prossimo = len(self.d)
        for i in range(self.n_file):
            s, e = struct.unpack_from("<II", self.d, self.fat_off + i * 8)
            if e == 0 and s == 0:
                continue
            if s > f["inizio"] and s < prossimo:
                prossimo = s
        return prossimo - f["inizio"]

    def immagine_overlay(self, oid):
        """L'overlay decompresso, con il decodificatore A di `sgp12.blz`."""
        from . import blz
        v = self.voce_overlay(oid)
        crudo = self.file_bytes(v["file_id"])
        if v["compresso"]:
            esigi(v["dim_compressa"] <= len(crudo),
                  "ov%03d: la tabella dichiara %d B compressi ma il file ne ha %d"
                  % (oid, v["dim_compressa"], len(crudo)))
            img = blz.blz_decomprimi(crudo[:v["dim_compressa"]])
        else:
            img = crudo
        return v, crudo, img


# ---------------------------------------------------------- esadecimale CLI

def esa(s: str) -> bytes:
    s = s.strip().replace(" ", "").replace("_", "")
    if s.lower().startswith("0x"):
        s = s[2:]
    esigi(len(s) % 2 == 0, "esadecimale di lunghezza dispari: %r" % s)
    return bytes.fromhex(s)


def analizza_guardia(spec: str):
    esigi(":" in spec, "guardia malformata (serve INDIRIZZO:ESADECIMALE): %r" % spec)
    a, h = spec.split(":", 1)
    return int(a, 0), esa(h)


def analizza_patch(spec: str):
    parti = spec.split(":")
    esigi(len(parti) == 3, "patch malformata (serve INDIRIZZO:PRE:POST): %r" % spec)
    addr = int(parti[0], 0)
    pre, post = esa(parti[1]), esa(parti[2])
    esigi(len(pre) == len(post),
          "patch a %#x: preimmagine %d B e postimmagine %d B non combaciano"
          % (addr, len(pre), len(post)))
    esigi(len(pre) > 0, "patch a %#x: preimmagine vuota" % addr)
    return {"addr": addr, "pre": pre, "post": post}


def bl_decode(sito: int, quattro_byte: bytes):
    """Inversa di `bl_thumb`: decodifica una `BL` Thumb-1 a 4 byte nel suo
    bersaglio (bit Thumb azzerato), o None se non e' una BL Thumb-1. Usata da
    `estrai_build.py` per leggere il bersaglio VERO di un gancio già applicato
    in una ROM (mai per applicarlo: quello resta `bl_thumb`)."""
    hi, lo = struct.unpack("<HH", quattro_byte)
    if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
        return None
    addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if addend & 0x400000:
        addend -= 0x800000
    return (sito + 4 + addend) & 0xFFFFFFFE


def bl_thumb(sito: int, bersaglio: int) -> bytes:
    """Codifica una `BL` Thumb-1 da `sito` a `bersaglio` (era ridefinita,
    identica nella sostanza, in applica_npc.py/applica_anim.py/applica_wifi.py)."""
    delta = (bersaglio & ~1) - (sito + 4)
    esigi(delta % 2 == 0 and -0x400000 <= delta < 0x400000,
          "BL fuori portata: %#x -> %#x (delta %d)" % (sito, bersaglio, delta))
    hi = 0xF000 | ((delta >> 12) & 0x7FF)
    lo = 0xF800 | ((delta >> 1) & 0x7FF)
    return struct.pack("<HH", hi, lo)
