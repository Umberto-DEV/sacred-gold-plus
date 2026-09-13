#!/usr/bin/env python3
"""SGP-1.2-RISERVA-01 — mutanti che rileggi_riserva12.py e test_riserva.py DEVONO uccidere.

Parte da una candidata GIA' corretta (prodotta da applica_riserva12.py) e la corrompe
in tre modi deliberati, ricostruendo l'ARM9 con ndspy (non con offset di file scritti a
mano: gli autoload NON sono in ordine di indirizzo RAM dentro il blob, quindi solo
ndspy sa dove va davvero un indirizzo), poi rilancia il rilettore indipendente.

    M1  letterale d'arena sbagliato: 0x020D2BB0 viene riportato a un valore che NON e'
        ne' 0x023DEB40 (1.1) ne' 0x023D8000 (1.2), ma un terzo indirizzo a caso dentro
        la riserva. Deve fallire "letterale_arena_hi" nel rilettore.
    M2  canarino basso spostato: i 32 B a 0x023D8000 vengono traslati di 16 B più in
        alto, lasciando 0x023D8000..0x023D8010 a zero. Deve fallire "canarino_basso".
    M3  zona 1.1 alterata di 1 byte: il padding a 0x023DEB60 (atteso 0x00) diventa
        0x01. Deve fallire "zona_1_1_identica_alla_base" (sha256 diversa) e T2 di
        test_riserva.py sul blocco "padding".
    M4  (REVISIONE 02, corregge D1/C1 di REVISIONE-OPUS.md: e' l'ex mutante "m7" del
        revisore, che usciva VERDE) i 16 B a 0x023D8030 (coda dell'intestazione, lo sha
        della parte stabile del manifest) vengono azzerati. Deve fallire
        "intestazione_manifest" nel rilettore.

Uso:
    python3 mutanti.py <base.nds> <candidata-buona.nds> <cartella-uscita> --manifest MAPPA.json
                        [--json out.json]

Richiede l'interprete rom-review-venv (ndspy). Uscita 0 se TUTTI i mutanti sono stati
uccisi (rilettore ROSSO su ciascuno), 1 altrimenti.
"""
import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[3]
RILEGGI = TOOLS / "rileggi_riserva12.py"
PY = Path(sys.executable)

if str(PY) != sys.executable:
    import os
    os.execv(str(PY), [str(PY), __file__, *sys.argv[1:]])

import ndspy.rom  # noqa: E402
from ndspy import _common  # noqa: E402

ARENA_HI_LIT = 0x020D2BB0
BASE_1_2 = 0x023D8000
BASE_1_1 = 0x023DEB40


def ricostruisci(sorgente_path, main, dst):
    """Riserializza l'ARM9 mutato in una copia della ROM, con lo stesso metodo di
    applica_riserva12.py (nessuna scrittura raw: solo ndspy)."""
    sorgente = Path(sorgente_path).read_bytes()
    parsed = ndspy.rom.NintendoDSRom(sorgente)
    arm9_in = bytes(parsed.arm9)
    nuovo = main.save(compress=False)
    inizio9 = struct.unpack_from("<I", sorgente, 0x20)[0]
    dati9 = nuovo + bytes(parsed.arm9PostData)
    risultato = bytearray(sorgente)
    risultato[inizio9:inizio9 + len(dati9)] = dati9
    struct.pack_into("<I", risultato, 0x2C, len(nuovo))
    va, na = arm9_in[:0x800], nuovo[:0x800]
    crc = parsed.secureAreaChecksum ^ _common.crc16(va) ^ _common.crc16(na)
    struct.pack_into("<H", risultato, 0x6C, crc)
    struct.pack_into("<H", risultato, 0x15E, _common.crc16(bytes(risultato[:0x15E])))
    Path(dst).write_bytes(bytes(risultato))


def carica(percorso):
    parsed = ndspy.rom.NintendoDSRom(Path(percorso).read_bytes())
    return parsed, parsed.loadArm9()


def scrivi_parola(main, addr, val):
    for s in main.sections:
        if s.ramAddress <= addr < s.ramAddress + len(s.data):
            struct.pack_into("<I", s.data, addr - s.ramAddress, val)
            return
    raise SystemExit("indirizzo 0x%08X fuori da ogni sezione" % addr)


def sezione(main, ram):
    for s in main.sections:
        if s.ramAddress == ram:
            return s
    raise SystemExit("nessuna sezione a 0x%08X" % ram)


def mutante_m1(src, dst):
    _parsed, main = carica(src)
    valore_sbagliato = 0x023DA000
    scrivi_parola(main, ARENA_HI_LIT, valore_sbagliato)
    ricostruisci(src, main, dst)
    return {"nome": "M1_letterale_arena_sbagliato",
            "descrizione": "0x020D2BB0 = 0x%08X (ne' 0x023DEB40 ne' 0x023D8000)" % valore_sbagliato,
            "atteso": "rileggi_riserva12.py: letterale_arena_hi ROSSO"}


def mutante_m2(src, dst):
    _parsed, main = carica(src)
    s = sezione(main, BASE_1_2)
    b = bytearray(s.data)
    canarino32 = bytes(b[:32])
    b[:32] = bytes(16) + canarino32[:16]
    s.data = b
    ricostruisci(src, main, dst)
    return {"nome": "M2_canarino_spostato",
            "descrizione": "i 32 B a 0x023D8000 traslati di 16 B (primi 16 B a zero)",
            "atteso": "rileggi_riserva12.py: canarino_basso ROSSO"}


def mutante_m3(src, dst):
    _parsed, main = carica(src)
    s = sezione(main, BASE_1_2)
    b = bytearray(s.data)
    off = (BASE_1_1 + 0x20) - BASE_1_2   # padding, atteso 0x00
    assert b[off] == 0x00, "preimmagine: il padding a 0x023DEB60 non e' 0x00"
    b[off] = 0x01
    s.data = b
    ricostruisci(src, main, dst)
    return {"nome": "M3_zona_1_1_alterata_1_byte",
            "descrizione": "0x023DEB60 (padding, atteso 0x00) -> 0x01",
            "atteso": "rileggi_riserva12.py: zona_1_1_identica_alla_base ROSSO"}


def mutante_m4(src, dst, manifest):
    _parsed, main = carica(src)
    s = sezione(main, BASE_1_2)
    b = bytearray(s.data)
    off = 0x20 + 16   # intestazione (+0x20 nella sezione) + 16 = coda con lo sha del manifest
    assert any(b[off:off + 16]), "preimmagine: i 16 B dello sha del manifest sono gia' a zero"
    b[off:off + 16] = bytes(16)
    s.data = b
    ricostruisci(src, main, dst)
    return {"nome": "M4_intestazione_manifest_azzerata",
            "descrizione": "i 16 B a 0x023D8030 (sha della parte stabile del manifest) azzerati",
            "atteso": "rileggi_riserva12.py: intestazione_manifest ROSSO",
            "nota": "REVISIONE 02: e' il mutante m7 di REVISIONE-OPUS.md, che con lo strumento "
                    "precedente usciva VERDE (D1)."}


def esegui_rilettore(base, mutante, manifest):
    p = subprocess.run([str(PY), str(RILEGGI), str(base), str(mutante), "--manifest", str(manifest)],
                       capture_output=True, text=True)
    try:
        r = json.loads(p.stdout)
    except json.JSONDecodeError:
        r = {"verdetto": "ILLEGGIBILE", "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}
    return p.returncode, r


def main_():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("candidata_buona")
    ap.add_argument("out_dir")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    generatori = [mutante_m1, mutante_m2, mutante_m3]
    esiti = []
    for gen in generatori:
        dst = out / (gen.__name__.split("_", 1)[1] + ".nds")
        meta = gen(a.candidata_buona, dst)
        rc, r = esegui_rilettore(a.base, dst, a.manifest)
        ucciso = (r.get("verdetto") == "ROSSO")
        esiti.append({**meta, "file": str(dst), "rilettore_exit": rc,
                      "rilettore_verdetto": r.get("verdetto"),
                      "esiti_rossi": [e["nome"] for e in r.get("esiti", []) if e["esito"] == "ROSSO"],
                      "esito": "UCCISO" if ucciso else "SOPRAVVISSUTO"})

    dst4 = out / "m4_intestazione_manifest_azzerata.nds"
    meta4 = mutante_m4(a.candidata_buona, dst4, a.manifest)
    rc4, r4 = esegui_rilettore(a.base, dst4, a.manifest)
    ucciso4 = (r4.get("verdetto") == "ROSSO")
    esiti.append({**meta4, "file": str(dst4), "rilettore_exit": rc4,
                  "rilettore_verdetto": r4.get("verdetto"),
                  "esiti_rossi": [e["nome"] for e in r4.get("esiti", []) if e["esito"] == "ROSSO"],
                  "esito": "UCCISO" if ucciso4 else "SOPRAVVISSUTO"})

    riepilogo = {"generati": len(esiti), "uccisi": sum(1 for e in esiti if e["esito"] == "UCCISO"),
                "sopravvissuti": sum(1 for e in esiti if e["esito"] == "SOPRAVVISSUTO"),
                "mutanti": esiti}
    testo = json.dumps(riepilogo, indent=1, ensure_ascii=False)
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(testo + "\n")
    print(testo)
    return 0 if riepilogo["sopravvissuti"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main_())
