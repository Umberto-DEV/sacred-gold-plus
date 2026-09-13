#!/usr/bin/env python3
"""Blocco NPC — tetto NPC per fotogramma (blocco `sgp.npc`, 256 B a
0x023D8900 + canarino a 0x023D8A00), gancio in overlay 1. Porta a `sgp12` di
`SGP-1.2-PRESTAZIONI-NPC-02/tools/applica_npc.py` + `rileggi_npc.py` (identici,
byte per byte, a NPC-03: `shasum` conferma la stessa copia).

`applica()` usa l'infrastruttura condivisa (`sgp12.rom.Arm9`, `sgp12.overlay`):
e' la parte SCRITTA per scrivere, mai duplicata per verifica.
`rileggi()` resta un rilettore INDIPENDENTE (propria `Arm9RO`, proprio
decodificatore BLZ «in avanti» — famiglia diversa dal decoder «all'indietro in
luogo» di `sgp12.blz` — e proprio decodificatore di BL): non importa `rom.py`
ne' `overlay.py`, per lo stesso principio di `sgp12/riserva.py`.
"""
from __future__ import annotations

import json
import struct
import tempfile
from pathlib import Path

from ..rom import Arm9, Rifiuto, bl_thumb, esigi, esigi_manifesto_descrive, sha
from .. import overlay as ovp

OV_CAMPO = 1
A_CONTESTO = 0x021FA564
PRE_CONTESTO_PIU_GANCIO = bytes.fromhex("f8b500910121009809024458" + "e0300068")
A_GANCIO = 0x021FA570
PRE_GANCIO = bytes.fromhex("e0300068")

BLOCK_BASE, BLOCK_N = 0x023D8900, 0x100
OFF_BLOB, N_BLOB_SLOT = 0x000, 0x0E0
OFF_STATO, N_STATO = 0x0E0, 16
CANARY_BASE, N_CANARY = BLOCK_BASE + BLOCK_N, 16
CANARY_MOTIVO = 0xCA5A1300

# M10 della revisione R1: `sgp_npc_tetto` non e' PRETESO qui. Non perche' non
# esista — esiste, `nm` lo trova a +0x00 del blob (0x23d8901), e il manifesto
# spedito lo dichiara di nuovo dalla 1.2.1, che il blob lo RICOMPILA —, ma
# perche' `estrai_build.py` non lo sa decodificare da una ROM: niente BL punta a
# quella funzione, ci arriva solo la trampolina interna. Pretendere qui un nome
# che l'estrattore non puo' produrre farebbe fallire l'estrazione, o peggio
# inviterebbe a inventarne il valore, che e' esattamente il difetto M10.
# `sgp_npc_hook` invece e' decodificato dalla BL in ov001: quello si pretende.
# Ogni simbolo in PIU' resta comunque controllato: deve cadere dentro il blob.
ENTRATE_ATTESE = ("sgp_npc_hook",)


def _carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    esigi(int(man["indirizzi"]["codice"], 16) == BLOCK_BASE + OFF_BLOB, "BUILD: indirizzo codice")
    esigi(int(man["indirizzi"]["stato"], 16) == BLOCK_BASE + OFF_STATO, "BUILD: indirizzo stato")
    esigi(len(blob) <= N_BLOB_SLOT, "BUILD: blob non entra nello slot")
    # M5 della revisione R2: il manifesto dichiarava uno sha256 DIVERSO dal
    # `blob.bin` che gli sta accanto (e diverso dal SHA256SUMS della stessa
    # cartella), e nessuno li confrontava: la bugia era invisibile a tutti i
    # cancelli. La regola ora e' UNA per tutti i blocchi, in `sgp12/rom.py`, e
    # non ha piu' il ramo `if "blob" in man`: un manifesto senza quel campo non
    # descrive niente, e passava.
    esigi_manifesto_descrive(man, blob, blocco="sgp.npc")
    for nome in ENTRATE_ATTESE:
        esigi(nome in man["simboli"], "BUILD: simbolo mancante: %s" % nome)
    # ogni simbolo dichiarato deve cadere dentro il blob
    for nome, valore in man["simboli"].items():
        v = int(valore, 16) & ~1
        esigi(BLOCK_BASE + OFF_BLOB <= v < BLOCK_BASE + OFF_BLOB + len(blob),
              "BUILD: il simbolo '%s' (%s) cade fuori dal blob di sgp.npc" % (nome, valore))
    return man, blob


def _verifica_manifest_mappa(manifest_path, log):
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    lo, hi = BLOCK_BASE, CANARY_BASE + N_CANARY
    for b in mappa["blocchi"]:
        base = int(b["base"], 16)
        n = b.get("bytes", 0)
        if b["nome"] == "libero.1.2":
            continue
        if b["nome"] in ("sgp.npc", "canarino.npc"):
            esigi(not (base != (BLOCK_BASE if b["nome"] == "sgp.npc" else CANARY_BASE)
                       or n != (BLOCK_N if b["nome"] == "sgp.npc" else N_CANARY)),
                  "A4/mappa: voce '%s' gia' registrata con base/bytes diversi" % b["nome"])
            continue
        esigi(not (base < hi and base + n > lo), "A4/mappa: sovrapposizione con '%s'" % b["nome"])
    log["manifest_controllato"] = True


def applica(rom: bytes, build, manifest_path=None, attivo: int = 1, tetto: int = 1) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/npc.py:applica", "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    esigi(1 <= tetto <= 255, "PARAM: tetto fuori intervallo 1..255")
    esigi(attivo in (0, 1), "PARAM: attivo deve essere 0 o 1")

    man, blob = _carica_build(build)
    _verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione")

    log["sha256_ingresso"] = sha(rom)

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)
    prima = bytes(r.raw)

    zona = r.leggi(BLOCK_BASE, BLOCK_N)
    esigi(zona == bytes(BLOCK_N), "A0: il blocco sgp.npc non e' a zero")
    ok("A0", "256 B a zero")
    can_zona = r.leggi(CANARY_BASE, N_CANARY)
    esigi(can_zona == bytes(N_CANARY), "A1: canarino non a zero")
    ok("A1", "16 B canarino a zero")

    blocco = bytearray(BLOCK_N)
    blocco[OFF_BLOB:OFF_BLOB + len(blob)] = blob
    stato = bytearray(N_STATO)
    stato[0x0] = attivo & 1
    stato[0x1] = tetto & 0xFF
    stato[0x2] = 0x5A
    blocco[OFF_STATO:OFF_STATO + N_STATO] = stato
    r.scrivi(BLOCK_BASE, bytes(blocco))
    canarino = b"".join(struct.pack("<I", CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
    r.scrivi(CANARY_BASE, bytes(canarino))

    leciti = set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N)) | \
             set(range(r.off(CANARY_BASE), r.off(CANARY_BASE) + N_CANARY))
    diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "A2: byte scritti fuori dalle regioni dichiarate")
    esigi(len(r.raw) == len(prima), "A2: dimensione cambiata")
    ok("A2", "%d byte scritti (256+16), dimensione invariata" % len(diversi))

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf2:
        r.salva(tf2.name)
        dati_dopo_arm9 = Path(tf2.name).read_bytes()

    gancio = int(man["simboli"]["sgp_npc_hook"], 16)
    bl = bl_thumb(A_GANCIO, gancio)
    patch = [{"addr": A_GANCIO, "pre": PRE_GANCIO, "post": bl}]
    guardie = [(A_CONTESTO, PRE_CONTESTO_PIU_GANCIO)]
    dati_out, ric = ovp.applica(dati_dopo_arm9, OV_CAMPO, guardie, patch, strategia="auto")
    esigi(ric["overlay"]["id"] == OV_CAMPO, "A3: overlay scelto diverso da quello atteso")
    ok("A3", "overlay 1 patchato in luogo: %s" % ric["strategia"]["usata"])
    log["overlay_patch"] = ric

    log["uscita_sha256"] = sha(dati_out)
    log["esito"] = "applicato"
    return dati_out, log


# ---------------------------------------------------------------- rilettore
# INDIPENDENTE da `applica()` sopra: propria Arm9RO, proprio decoder BLZ «in
# avanti su buffer separato» (famiglia diversa dal decoder «all'indietro in
# luogo» di `sgp12.blz`), proprio decodificatore di BL. Porta letterale di
# `rileggi_npc.py`.

class _Rosso(Exception):
    pass


def _pretendi(c, m):
    if not c:
        raise _Rosso(m)


class _Arm9RO:
    def __init__(self, raw):
        self.raw = raw
        self.off9 = struct.unpack_from("<I", raw, 0x20)[0]
        self.ram9 = struct.unpack_from("<I", raw, 0x28)[0]
        self.siz9 = struct.unpack_from("<I", raw, 0x2C)[0]
        tab0, tab1, dati0 = struct.unpack_from("<3I", raw, self.off9 + 0xBA0)
        self.segmenti = [(self.ram9, self.off9, dati0 - self.ram9)]
        p = self.off9 + (tab0 - self.ram9)
        fine = self.off9 + (tab1 - self.ram9)
        off = self.off9 + (dati0 - self.ram9)
        while p < fine:
            ram, size, _bss = struct.unpack_from("<3I", raw, p)
            self.segmenti.append((ram, off, size))
            off += size
            p += 12

    def off(self, ram, n=1):
        for base, o, size in self.segmenti:
            if base <= ram and ram + n <= base + size:
                return o + (ram - base)
        raise _Rosso("0x%08X+%d non e' dentro nessun segmento ARM9" % (ram, n))

    def leggi(self, ram, n):
        o = self.off(ram, n)
        return bytes(self.raw[o:o + n])


def _bl_decode(sito, quattro_byte):
    hi, lo = struct.unpack("<HH", quattro_byte)
    if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
        return None
    addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if addend & 0x400000:
        addend -= 0x800000
    return (sito + 4 + addend) & 0xFFFFFFFE


def _blz_forward(flusso):
    n = len(flusso)
    _pretendi(n >= 8 and n % 4 == 0, "BLZ: lunghezza %d non plausibile" % n)
    w0, w1 = struct.unpack("<II", flusso[n - 8:n])
    hdr_len = w0 >> 24
    enc_len = w0 & 0xFFFFFF
    inc_len = w1
    _pretendi(8 <= hdr_len <= 11, "BLZ: hdr_len fuori range")
    _pretendi(hdr_len <= enc_len <= n, "BLZ: enc_len incoerente")
    prefisso = flusso[:n - enc_len]
    zona = flusso[n - enc_len:n - hdr_len]
    finale = n + inc_len
    z = bytes(reversed(zona))
    attesi = finale - len(prefisso)
    fuori = bytearray()
    i = 0
    while len(fuori) < attesi:
        _pretendi(i < len(z), "BLZ: flusso finito prima dell'immagine")
        flag = z[i]
        i += 1
        for bit in range(8):
            if len(fuori) >= attesi:
                break
            if flag & (0x80 >> bit):
                _pretendi(i + 1 < len(z), "BLZ: coppia troncata")
                b1, b2 = z[i], z[i + 1]
                i += 2
                dist = (((b1 & 0x0F) << 8) | b2) + 3
                lung = (b1 >> 4) + 3
                _pretendi(dist <= len(fuori), "BLZ: distanza oltre i byte gia' prodotti")
                p = len(fuori) - dist
                for k in range(lung):
                    fuori.append(fuori[p + k])
            else:
                _pretendi(i < len(z), "BLZ: letterale troncato")
                fuori.append(z[i])
                i += 1
    _pretendi(len(fuori) == attesi, "BLZ: dimensione finale sbagliata")
    return prefisso + bytes(reversed(fuori))


def _tabelle(dati):
    p = lambda o: struct.unpack_from("<I", dati, o)[0]
    return {"fat": p(0x48), "fat_len": p(0x4C), "y9": p(0x50), "y9_len": p(0x54)}


def _leggi_overlay(dati, t, oid):
    off = t["y9"] + oid * 32
    campi = struct.unpack_from("<8I", dati, off)
    e = {"id": campi[0], "ram": campi[1], "ram_size": campi[2], "file_id": campi[6],
         "flag": campi[7] >> 24, "dim": campi[7] & 0xFFFFFF, "voce": off}
    fo = t["fat"] + e["file_id"] * 8
    s, fi = struct.unpack_from("<II", dati, fo)
    e["fat_voce"], e["inizio"], e["fine"] = fo, s, fi
    return e


def _immagine_overlay(dati, e):
    corpo = dati[e["inizio"]:e["fine"]]
    if e["flag"] & 1:
        _pretendi(e["dim"] <= len(corpo), "y9 dichiara piu' byte compressi di quanti ne ha la FAT")
        return _blz_forward(bytes(corpo[:e["dim"]]))
    return bytes(corpo)


def _trova_overlay_per_guardia(dati, t, addr, hx):
    n_ov = t["y9_len"] // 32
    trovati = []
    for oid in range(n_ov):
        e = _leggi_overlay(dati, t, oid)
        if not (e["ram"] <= addr and addr + len(hx) <= e["ram"] + e["ram_size"]):
            continue
        try:
            img = _immagine_overlay(dati, e)
        except _Rosso:
            continue
        off = addr - e["ram"]
        if img[off:off + len(hx)] == hx:
            trovati.append((oid, e, img))
    return trovati


def rileggi(ingresso: bytes, derivata: bytes, build, manifest_path=None) -> dict:
    esiti, tutto_verde = [], True

    def esito(nome, ok_, dettaglio=""):
        nonlocal tutto_verde
        esiti.append({"cancello": nome, "esito": "verde" if ok_ else "ROSSO", "dettaglio": dettaglio})
        tutto_verde = tutto_verde and ok_
        return ok_

    man = json.loads((Path(build) / "manifesto.json").read_text())
    blob = (Path(build) / "blob.bin").read_bytes()
    bersaglio = int(man["simboli"]["sgp_npc_hook"], 16) & ~1

    d = _Arm9RO(derivata)
    b = _Arm9RO(ingresso)

    codice = d.leggi(BLOCK_BASE + OFF_BLOB, len(blob))
    esito("L2", sha(codice) == sha(blob), "sha256 blob")

    stato = d.leggi(BLOCK_BASE + OFF_STATO, N_STATO)
    esito("L4", stato[2] == 0x5A, "seme_attivo=%d tetto=%d guardia=0x%02X" % (stato[0], stato[1], stato[2]))

    padding_ok = (d.leggi(BLOCK_BASE + len(blob), OFF_STATO - len(blob)) == bytes(OFF_STATO - len(blob))
                  and d.leggi(BLOCK_BASE + OFF_STATO + N_STATO, BLOCK_N - OFF_STATO - N_STATO)
                  == bytes(BLOCK_N - OFF_STATO - N_STATO))
    esito("L4b", padding_ok, "padding a zero")

    canarino_atteso = b"".join(struct.pack("<I", CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
    canarino = d.leggi(CANARY_BASE, N_CANARY)
    esito("L5", canarino == canarino_atteso, "canarino")
    if manifest_path:
        mappa = json.loads(Path(manifest_path).read_text())
        lo, hi = BLOCK_BASE, CANARY_BASE + N_CANARY
        sovrapposti = [x["nome"] for x in mappa["blocchi"]
                       if x["nome"] not in ("sgp.npc", "canarino.npc", "libero.1.2")
                       and int(x["base"], 16) < hi and int(x["base"], 16) + x.get("bytes", 0) > lo]
        esito("L5b", not sovrapposti, "sovrapposizioni: %s" % sovrapposti)

    _pretendi(b.off9 == d.off9 and b.siz9 == d.siz9, "L7: l'arm9 ha cambiato offset/dimensione")
    diversi = [i for i in range(b.siz9) if b.raw[b.off9 + i] != d.raw[d.off9 + i]]
    leciti = set(range(b.off(BLOCK_BASE, BLOCK_N), b.off(BLOCK_BASE, BLOCK_N) + BLOCK_N)) | \
             set(range(b.off(CANARY_BASE, N_CANARY), b.off(CANARY_BASE, N_CANARY) + N_CANARY))
    fuori = [i for i in diversi if (b.off9 + i) not in leciti]
    esito("L7", not fuori, "%d byte diversi (arm9)" % len(diversi))

    tb = _tabelle(b.raw)
    tdd = _tabelle(d.raw)
    trovati_b = _trova_overlay_per_guardia(b.raw, tb, A_CONTESTO, PRE_CONTESTO_PIU_GANCIO)
    _pretendi(len(trovati_b) == 1, "l'ingresso non ha un overlay unico con quel contesto")
    oid, eb, img_b = trovati_b[0]
    _pretendi(oid == OV_CAMPO, "overlay individuato diverso da quello atteso")

    ed = _leggi_overlay(d.raw, tdd, oid)
    img_d = _immagine_overlay(d.raw, ed)
    _pretendi(len(img_d) == len(img_b), "l'overlay cambia dimensione")

    off_g = A_GANCIO - ed["ram"]
    quattro = img_d[off_g:off_g + 4]
    t = _bl_decode(A_GANCIO, quattro)
    esito("L1", t == bersaglio, "gancio -> %s" % (hex(t) if t is not None else "non-BL"))
    esito("L3", PRE_GANCIO in codice, "istruzioni sostituite presenti nella trampolina")

    diff_ov = [i for i in range(len(img_b)) if img_b[i] != img_d[i]]
    inattesi_ov = [i for i in diff_ov if i not in range(off_g, off_g + 4)]
    if inattesi_ov:
        esito("L6", False, "byte diversi fuori dal gancio")
    else:
        esito("L6", diff_ov == list(range(off_g, off_g + 4)), "solo i 4 B del gancio cambiano")

    return {"esito_finale": "verde" if tutto_verde else "ROSSO", "cancelli": esiti}
