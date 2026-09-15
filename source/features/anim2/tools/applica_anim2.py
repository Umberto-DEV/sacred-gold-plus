#!/usr/bin/env python3
"""Applica ``sgp.anim2`` v5 a una ROM 1.2.1, senza toccare l'ingresso.

API pubblica: ``applica(rom_bytes, build_dir, manifest_path=None)``.
Il blocco ARM9 resta spento di default; ov012 viene ricompresso BLZ in luogo.
"""
import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO = QUI.parents[3]
sys.path.insert(0, str(REPO / "source" / "features" / "anim" / "tools"))
from arm9 import Arm9  # noqa: E402
import overlay_patch as ovp  # noqa: E402

BASE, N_BLOCCO = 0x023DB500, 0x800
OFF_CAN, OFF_TAB, OFF_PAR, OFF_SITI = 0x600, 0x620, 0x640, 0x660
OFF_STATO, OFF_SLOT = 0x6A0, 0x6E0
MAX_CODICE = 0x600
CAN_MOTIVO = 0xCA5A1800

G3_AVVIA = 0x0225DC8A
G1_TASK = 0x0226200C
G2_TESTA = 0x02262016
G2_CODA_V4 = 0x02262032
G4_CATTURA = 0x0223EBD8
V4_TASK = 0x023D8BE5
V4_STOP = 0x023D8BD3
VANILLA_AVVIA = 0x02261FD5
PRE_G2_TESTA = bytes.fromhex("041c6620")
POST_G2_CODA = bytes.fromhex("206a0421")

ENTRATE = ("sgp_idle_task5", "sgp_stop_testa", "sgp_avvia_tutti",
           "sgp_stop_politica", "sgp_avvia_cattura")
INDIRIZZI_BUILD = {
    "base": BASE, "codice": BASE, "canarino": BASE + OFF_CAN,
    "tab_u": BASE + OFF_TAB, "par": BASE + OFF_PAR,
    "siti": BASE + OFF_SITI, "stato": BASE + OFF_STATO,
    "slot": BASE + OFF_SLOT,
}
OFFSET_BUILD = {
    "codice": 0, "canarino": OFF_CAN, "tab_u": OFF_TAB,
    "par": OFF_PAR, "siti": OFF_SITI, "stato": OFF_STATO,
    "slot": OFF_SLOT,
}
ANCORE_BUILD = {
    "Pokepic_SetAttr": "0x020087a5",
    "ov12_task_vanilla": "0x0226203d",
    "ov12_avvia": "0x02261fd5",
    "ov12_ferma": "0x02262015",
    "G3_sito_avvio": "ov012 0x0225dc8a (BL -> sgp_avvia_tutti)",
    "G1_letterale_task": "ov012 0x0226200c",
    "G2_testa_fermata": "ov012 0x02262016 (BL -> sgp_stop_testa)",
    "G2_coda_v4_ritirata": "ov012 0x02262032 torna vanilla (20 6a 04 21)",
    "G4_avvio_cattura": "ov012 0x0223ebd8 (BL -> sgp_avvia_cattura)",
}


class Rifiuto(Exception):
    pass


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def bl_thumb(sito, bersaglio_thumb):
    delta = (bersaglio_thumb & ~1) - (sito + 4)
    if delta & 1 or not (-0x400000 <= delta < 0x400000):
        raise Rifiuto("BL Thumb fuori portata a 0x%08X" % sito)
    return struct.pack("<HH", 0xF000 | ((delta >> 12) & 0x7FF),
                       0xF800 | ((delta >> 1) & 0x7FF))


def canarino_atteso():
    return b"".join((CAN_MOTIVO | i).to_bytes(4, "little") for i in range(4))


def _intero(v, campo):
    try:
        return int(v, 0) if isinstance(v, str) else int(v)
    except (TypeError, ValueError) as e:
        raise Rifiuto("BUILD: %s non e' un intero" % campo) from e


def _verifica_descrizione(nome, dati, descrizione, dimensione=None):
    if not isinstance(descrizione, dict):
        raise Rifiuto("BUILD: manca la descrizione di " + nome)
    if descrizione.get("byte") != len(dati) or descrizione.get("sha256") != sha(dati):
        raise Rifiuto("BUILD: %s non corrisponde a byte/sha256 del manifesto" % nome)
    if dimensione is not None and len(dati) != dimensione:
        raise Rifiuto("BUILD: %s misura %d B invece di %d" %
                      (nome, len(dati), dimensione))


def carica_build(build_dir):
    p = Path(build_dir)
    try:
        m = json.loads((p / "manifesto.json").read_text())
        parti = {n: (p / n).read_bytes() for n in
                 ("blob.bin", "canarino.bin", "tab_u.bin", "par.bin", "siti.bin")}
    except (OSError, json.JSONDecodeError) as e:
        raise Rifiuto("BUILD: bundle incompleto o manifesto illeggibile: %s" % e) from e
    if not isinstance(m, dict):
        raise Rifiuto("BUILD: il manifesto non e' un oggetto JSON")

    indirizzi = m.get("indirizzi")
    relativi = m.get("offset_relativi")
    if not isinstance(indirizzi, dict) or not isinstance(relativi, dict):
        raise Rifiuto("BUILD: pianta indirizzi/offset_relativi mancante")
    for nome, atteso in INDIRIZZI_BUILD.items():
        if _intero(indirizzi.get(nome), "indirizzi." + nome) != atteso:
            raise Rifiuto("BUILD: indirizzo %s diverso da 0x%08X" % (nome, atteso))
    for nome, atteso in OFFSET_BUILD.items():
        if _intero(relativi.get(nome), "offset_relativi." + nome) != atteso:
            raise Rifiuto("BUILD: offset %s diverso da 0x%X" % (nome, atteso))
    if indirizzi.get("blocco_byte") != N_BLOCCO or m.get("blocco_richiesto_byte") != N_BLOCCO:
        raise Rifiuto("BUILD: dimensione blocco diversa da 2048")

    _verifica_descrizione("blob.bin", parti["blob.bin"], m.get("blob"))
    _verifica_descrizione("canarino.bin", parti["canarino.bin"], m.get("canarino"), 16)
    tabelle = m.get("tabelle_bin")
    if not isinstance(tabelle, dict):
        raise Rifiuto("BUILD: descrizioni tabelle_bin mancanti")
    _verifica_descrizione("tab_u.bin", parti["tab_u.bin"], tabelle.get("tab_u"), 32)
    _verifica_descrizione("par.bin", parti["par.bin"], tabelle.get("par"), 32)
    _verifica_descrizione("siti.bin", parti["siti.bin"], tabelle.get("siti"), 64)

    if len(parti["blob.bin"]) > MAX_CODICE:
        raise Rifiuto("BUILD: blob oltre i 1536 B di codice")
    if parti["canarino.bin"] != canarino_atteso():
        raise Rifiuto("BUILD: canarino errato")
    simboli = m.get("simboli")
    if not isinstance(simboli, dict):
        raise Rifiuto("BUILD: tabella simboli mancante")
    fine_blob = BASE + len(parti["blob.bin"])
    for nome in ENTRATE:
        valore = _intero(simboli.get(nome), "simboli." + nome)
        if valore & 1 == 0:
            raise Rifiuto("BUILD: simbolo senza bit Thumb: " + nome)
        if not (BASE <= (valore & ~1) < fine_blob):
            raise Rifiuto("BUILD: simbolo fuori dal blob: " + nome)

    # Questi valori descrivono i ganci che l'applicatore sta per scrivere. Un
    # manifesto di un'altra build non deve poter pilotare gli stessi file.
    if m.get("ancore_del_gioco") != ANCORE_BUILD:
        raise Rifiuto("BUILD: ancore dei ganci incompatibili con questo applicatore")
    return m, parti


def immagine_blocco(parti):
    b = bytearray(N_BLOCCO)
    b[:len(parti["blob.bin"])] = parti["blob.bin"]
    b[OFF_CAN:OFF_CAN + 16] = parti["canarino.bin"]
    b[OFF_TAB:OFF_TAB + 32] = parti["tab_u.bin"]
    b[OFF_PAR:OFF_PAR + 32] = parti["par.bin"]
    b[OFF_SITI:OFF_SITI + 64] = parti["siti.bin"]
    b[OFF_STATO + 1] = 0x5A
    return bytes(b)


def _scrivi_arm9(rom, blocco):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "rom.nds"
        p.write_bytes(rom)
        a = Arm9(p)
        prima = bytes(a.raw)
        zona = bytes(a.leggi(BASE, N_BLOCCO))
        if zona != bytes(N_BLOCCO):
            raise Rifiuto("A0: sgp.anim2 non e' vergine (2048 B non nulli)")
        a.scrivi(BASE, blocco)
        diversi = [i for i, (x, y) in enumerate(zip(prima, a.raw)) if x != y]
        leciti = set(range(a.off(BASE), a.off(BASE) + N_BLOCCO))
        if any(i not in leciti for i in diversi) or len(prima) != len(a.raw):
            raise Rifiuto("A2: scrittura ARM9 fuori dal blocco")
        a.salva(p)
        return p.read_bytes(), len(diversi)


def _controlla_mappa(path):
    if path is None:
        return []
    m = json.loads(Path(path).read_text())
    urti = []
    for b in m["blocchi"]:
        lo, n = int(b["base"], 16), b.get("bytes", 0)
        if b["nome"] in ("sgp.anim2", "libero.1.2", "libero.1.2.finale"):
            continue
        if lo < BASE + N_BLOCCO and lo + n > BASE:
            urti.append(b["nome"])
    if urti:
        raise Rifiuto("A4: sovrapposizione con " + ", ".join(urti))
    return urti


def applica(rom, build_dir, manifest_path=None):
    """Rende ``(rom_derivata, rapporto)`` o solleva ``Rifiuto``."""
    rom = bytes(rom)
    man, parti = carica_build(build_dir)
    _controlla_mappa(manifest_path)
    blocco = immagine_blocco(parti)
    dopo_arm9, n_arm9 = _scrivi_arm9(rom, blocco)

    pre = {
        G3_AVVIA: bl_thumb(G3_AVVIA, VANILLA_AVVIA),
        G1_TASK: struct.pack("<I", V4_TASK),
        G2_TESTA: PRE_G2_TESTA,
        G2_CODA_V4: bl_thumb(G2_CODA_V4, V4_STOP),
        G4_CATTURA: bl_thumb(G4_CATTURA, 0x0200E321),
    }
    post = {
        G3_AVVIA: bl_thumb(G3_AVVIA, int(man["simboli"]["sgp_avvia_tutti"], 16)),
        G1_TASK: struct.pack("<I", int(man["simboli"]["sgp_idle_task5"], 16)),
        G2_TESTA: bl_thumb(G2_TESTA, int(man["simboli"]["sgp_stop_testa"], 16)),
        G2_CODA_V4: POST_G2_CODA,
        G4_CATTURA: bl_thumb(G4_CATTURA, int(man["simboli"]["sgp_avvia_cattura"], 16)),
    }
    guardie = list(pre.items())
    patch = [{"addr": a, "pre": pre[a], "post": post[a]} for a in pre]
    try:
        derivata, ric = ovp.applica(dopo_arm9, None, guardie, patch, strategia="auto")
    except ovp.Rifiuto as e:
        raise Rifiuto("A1/BLZ: " + str(e)) from e
    if ric["overlay"]["id"] != 12:
        raise Rifiuto("A1: le guardie hanno scelto overlay %d" % ric["overlay"]["id"])

    rapporto = {
        "strumento": "applica_anim2.py", "esito": "applicato",
        "sha256_ingresso": sha(rom), "sha256_uscita": sha(derivata),
        "bytes_rom": len(rom), "byte_arm9_diversi": n_arm9,
        "blocco": {"base": hex(BASE), "bytes": N_BLOCCO,
                    "sha256": sha(blocco), "spento_default": True,
                    "blob_bytes": len(parti["blob.bin"]),
                    "blob_sha256": sha(parti["blob.bin"])},
        "preimmagini_ov012": {hex(a): pre[a].hex() for a in pre},
        "postimmagini_ov012": {hex(a): post[a].hex() for a in post},
        "nuovi_ganci_16B": [hex(G3_AVVIA), hex(G1_TASK), hex(G2_TESTA), hex(G4_CATTURA)],
        "ritiro_gancio_coda_v4": hex(G2_CODA_V4),
        "overlay_patch": ric,
    }
    return derivata, rapporto


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--build", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--json")
    a = ap.parse_args()
    try:
        out, r = applica(Path(a.base).read_bytes(), a.build, a.manifest)
        Path(a.out).write_bytes(out)
        if a.json:
            Path(a.json).write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({k: r[k] for k in ("esito", "sha256_uscita", "blocco")}, indent=2))
        return 0
    except Rifiuto as e:
        print("RIFIUTATO: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
