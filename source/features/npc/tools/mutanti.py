#!/usr/bin/env python3
"""8 mutanti per SGP-1.2-PRESTAZIONI-NPC-02 (CRITERI.md §4). Ognuno agisce
SULL'INGRESSO (prima di applicare, aspettandosi un RIFIUTO dell'applicatore)
o SULL'USCITA di un'applicazione buona (aspettandosi un ROSSO dal rilettore
indipendente `rileggi_npc.py`). Invoca i due strumenti come PROCESSI separati,
mai per import diretto: se condividessero un errore, non sarebbe perche' lo
condividono.

Uso:
    mutanti.py --base <sgp-1.2-EN.nds> --build <dir> --manifest <MAPPA.json> \\
               --applicato <out-EN.nds gia' applicato buono> --tmp <scratchpad> [--json out.json]
"""
import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
APPLICA = QUI / "applica_npc.py"
RILEGGI = QUI / "rileggi_npc.py"

BLOCK_BASE, BLOCK_N = 0x023D8900, 0x100
OFF_STATO, N_STATO = 0x0E0, 16
CANARY_BASE, N_CANARY = BLOCK_BASE + BLOCK_N, 16
A_GANCIO = 0x021FA570
OV_CAMPO = 1


def run(args):
    r = subprocess.run([sys.executable] + [str(x) for x in args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def esegui_applica(base, out, build, manifest, extra=()):
    return run([APPLICA, "--base", base, "--out", out, "--build", build,
                "--manifest", manifest, "--niente-registro"] + list(extra))


def esegui_rileggi(ingresso, derivata, build, manifest):
    return run([RILEGGI, ingresso, derivata, "--build", build, "--manifest", manifest])


def patch_arm9(path_in, path_out, ram_addr, dati):
    sys.path.insert(0, str(QUI))
    from arm9 import Arm9
    a = Arm9(path_in)
    a.scrivi(ram_addr, dati)
    a.salva(path_out)


def patch_overlay_addr(path_in, path_out, addr, nuovi_byte):
    """Mutante costruito con `overlay_patch.py` (e' costruzione, non verifica:
    la verifica la fa sempre e solo `rileggi_npc.py`, che non lo importa)."""
    sys.path.insert(0, str(QUI))
    import overlay_patch as ovp
    dati = Path(path_in).read_bytes()
    rom = ovp.Rom(dati)
    v, _, img = rom.immagine_overlay(OV_CAMPO)
    off = addr - v["ram"]
    pre = bytes(img[off:off + len(nuovi_byte)])
    out, _ = ovp.applica(dati, OV_CAMPO, [(addr, pre)],
                         [{"addr": addr, "pre": pre, "post": bytes(nuovi_byte)}],
                         strategia="auto")
    Path(path_out).write_bytes(out)


def patch_overlay_raw(path_in, path_out, addr, offset_nel_flusso_compresso=None, xor_byte=None):
    """Mutante grezzo sull'overlay 1: XOR di un byte dentro il CORPO COMPRESSO
    in ROM (non nell'immagine decompressa): serve a colpire il flusso BLZ
    stesso, non solo un'istruzione gia' nota."""
    dati = bytearray(Path(path_in).read_bytes())
    fat_off, fat_len = struct.unpack_from("<II", dati, 0x48)
    y9_off, y9_len = struct.unpack_from("<II", dati, 0x50)
    voce = y9_off + OV_CAMPO * 32
    campi = struct.unpack_from("<8I", dati, voce)
    fid = campi[6]
    fo = fat_off + fid * 8
    s, e = struct.unpack_from("<II", dati, fo)
    idx = s + offset_nel_flusso_compresso
    if not (s <= idx < e):
        raise SystemExit("offset fuori dal corpo dell'overlay")
    dati[idx] ^= xor_byte
    Path(path_out).write_bytes(bytes(dati))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--build", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--applicato", required=True, help="una ROM gia' applicata (buona)")
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()

    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    esiti = []
    tutti_uccisi = True

    def registra(nome, rc, extra=""):
        nonlocal tutti_uccisi
        ucciso = (rc != 0)
        tutti_uccisi &= ucciso
        esiti.append({"mutante": nome, "returncode": rc, "ucciso": ucciso, "nota": extra})
        print("  %-52s %-7s rc=%d  %s" % (nome, "UCCISO" if ucciso else "VIVO!!", rc, extra))
        return ucciso

    # ---- M1: preimmagine del gancio alterata (INGRESSO, in overlay 1) --------
    m1_in = tmp / "m1-base.nds"
    patch_overlay_addr(a.base, m1_in, A_GANCIO, bytes([0x00, 0x00, 0x00, 0x00]))  # non e' piu' e0300068
    rc, out, err = esegui_applica(str(m1_in), str(tmp / "m1-out.nds"), a.build, a.manifest)
    registra("M1 preimmagine del gancio alterata", rc, "atteso A3/overlay rosso (guardia non combacia)")

    # ---- M2: blocco sgp.npc gia' occupato (INGRESSO) --------------------------
    m2_in = tmp / "m2-base.nds"
    patch_arm9(a.base, m2_in, BLOCK_BASE, bytes([0xAA]))
    rc, out, err = esegui_applica(str(m2_in), str(tmp / "m2-out.nds"), a.build, a.manifest)
    registra("M2 blocco sgp.npc non a zero", rc, "atteso A0 rosso")

    # ---- M3: canarino gia' occupato (INGRESSO) ---------------------------------
    m3_in = tmp / "m3-base.nds"
    patch_arm9(a.base, m3_in, CANARY_BASE, bytes([0x01]))
    rc, out, err = esegui_applica(str(m3_in), str(tmp / "m3-out.nds"), a.build, a.manifest)
    registra("M3 canarino gia' occupato", rc, "atteso A1 rosso")

    # ---- M4: blob spostato di 4 B nel blocco (USCITA) --------------------------
    sys.path.insert(0, str(QUI))
    from arm9 import Arm9
    build = Path(a.build)
    blob = (build / "blob.bin").read_bytes()
    r = Arm9(a.applicato)
    blocco = bytearray(r.leggi(BLOCK_BASE, BLOCK_N))
    nuovo = bytearray(BLOCK_N)
    nuovo[4:4 + len(blob)] = blob                       # spostato di 4 B
    nuovo[OFF_STATO:] = blocco[OFF_STATO:]               # stato/margine invariati
    r.scrivi(BLOCK_BASE, bytes(nuovo))
    m4_out = tmp / "m4-out.nds"
    r.salva(m4_out)
    rc, out, err = esegui_rileggi(a.base, str(m4_out), a.build, a.manifest)
    registra("M4 blob spostato di 4 B nel blocco", rc, "atteso L2 rosso (sha diverso)")

    # ---- M5: guardia dello stato azzerata (USCITA) -----------------------------
    r = Arm9(a.applicato)
    r.scrivi(BLOCK_BASE + OFF_STATO + 2, bytes([0x00]))  # guardia a offset +2
    m5_out = tmp / "m5-out.nds"
    r.salva(m5_out)
    rc, out, err = esegui_rileggi(a.base, str(m5_out), a.build, a.manifest)
    registra("M5 guardia dello stato azzerata", rc, "atteso L4 rosso")

    # ---- M6: canarino azzerato (USCITA) ----------------------------------------
    r = Arm9(a.applicato)
    r.scrivi(CANARY_BASE, bytes(N_CANARY))
    m6_out = tmp / "m6-out.nds"
    r.salva(m6_out)
    rc, out, err = esegui_rileggi(a.base, str(m6_out), a.build, a.manifest)
    registra("M6 canarino azzerato", rc, "atteso L5 rosso")

    # ---- M7: blocco registrato sovrapposto in mappa (INGRESSO+mappa) -----------
    mappa = json.loads(Path(a.manifest).read_text())
    mappa["blocchi"].append({"nome": "intruso.test", "base": hex(BLOCK_BASE + 0x10),
                             "bytes": 16, "proprietario": "mutante-M7"})
    m7_manifest = tmp / "m7-mappa.json"
    m7_manifest.write_text(json.dumps(mappa))
    rc, out, err = esegui_applica(a.base, str(tmp / "m7-out.nds"), a.build, str(m7_manifest))
    registra("M7 mappa con un blocco intruso dentro sgp.npc", rc, "atteso A4/mappa rosso")

    # ---- M8: 1 bit alterato nel flusso BLZ compresso dell'overlay (USCITA) -----
    # colpisce l'overlay GIA' patchato (a.applicato): un bit sbagliato nella
    # parte codificata produce un'immagine decompressa diversa altrove (o un
    # decodificatore che si rifiuta), mai un cambiamento invisibile.
    m8_out = tmp / "m8-out.nds"
    patch_overlay_raw(a.applicato, m8_out, A_GANCIO, offset_nel_flusso_compresso=200, xor_byte=0x01)
    rc, out, err = esegui_rileggi(a.base, str(m8_out), a.build, a.manifest)
    ucciso8 = rc != 0
    # se per caso il bit alterato cade in un byte che il decoder tollera senza
    # cambiare l'immagine (raro ma non impossibile in coda al flusso), si
    # riprova piu' vicino alla testa: registriamo comunque l'esito reale.
    registra("M8 1 bit alterato nel flusso BLZ compresso", rc,
             "atteso L6/decompressione rosso; stderr=%s" % (err.strip()[-200:] if not ucciso8 else ""))

    print()
    print("TUTTI UCCISI" if tutti_uccisi else "ALMENO UN MUTANTE VIVO — cancello non affidabile")
    if a.json:
        Path(a.json).write_text(json.dumps({"tutti_uccisi": tutti_uccisi, "mutanti": esiti}, indent=2) + "\n")
    return 0 if tutti_uccisi else 1


if __name__ == "__main__":
    sys.exit(main())
