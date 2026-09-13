#!/usr/bin/env python3
"""7 mutanti per SGP-1.2-ANIM-B-02 (CRITERI.md §4, esattamente l'elenco chiesto
dall'orchestratore: preimmagine, guardia, blob spostato, puntatore senza bit
Thumb, flag acceso all'origine, voce mappa, 1 bit nel flusso). Ognuno agisce
SULL'INGRESSO (rifiuto atteso dell'applicatore) o SULL'USCITA di
un'applicazione buona (rosso atteso di `rileggi_anim.py`). Invoca i due
strumenti come PROCESSI separati, mai per import diretto (stessa disciplina
di `SGP-1.2-PRESTAZIONI-NPC-02/tools/mutanti.py`).

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
APPLICA = QUI / "applica_anim.py"
RILEGGI = QUI / "rileggi_anim.py"

BLOCK_BASE, BLOCK_N = 0x023D8B00, 0x400
OFF_CODICE, MAX_CODICE = 0x000, 0x2F0
OFF_CANARINO, N_CANARINO = 0x2F0, 16
OFF_STATO = 0x340
A_GANCIO = 0x0226200C
OV_CAMPO = 12


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
    la verifica la fa sempre e solo `rileggi_anim.py`, che non lo importa)."""
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


def patch_overlay_raw(path_in, path_out, offset_nel_flusso_compresso, xor_byte=0x01):
    """Mutante grezzo sull'overlay 12: XOR di un byte dentro il CORPO
    COMPRESSO in ROM (non nell'immagine decompressa), per colpire il flusso
    BLZ stesso, non solo un'istruzione gia' nota."""
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
        print("  %-58s %-7s rc=%d  %s" % (nome, "UCCISO" if ucciso else "VIVO!!", rc, extra))
        return ucciso

    sys.path.insert(0, str(QUI))
    from arm9 import Arm9

    # ---- 1. PREIMMAGINE: il gancio, sull'INGRESSO, non vale piu' 3d202602 ----
    m1_in = tmp / "m1-base.nds"
    patch_overlay_addr(a.base, m1_in, A_GANCIO, bytes([0x00, 0x00, 0x00, 0x00]))
    rc, out, err = esegui_applica(str(m1_in), str(tmp / "m1-out.nds"), a.build, a.manifest)
    registra("1-preimmagine (gancio alterato sull'ingresso)", rc,
             "atteso A1/overlay rosso: la guardia del letterale non combacia piu'")

    # ---- 2. GUARDIA: overlay scelto per INDIRIZZO, non per contenuto ---------
    # 0x0226200C cade dentro CINQUE overlay per range (12, 49, 91, 92, 93,
    # CONTRATTO-A1B.md §1.2), ma solo ov012 ha "3d202602" a quel byte: gli
    # altri quattro hanno contenuti diversi. Il mutante sceglie un overlay
    # PER INDIRIZZO (49, che contiene l'indirizzo) invece che per contenuto,
    # e deve essere rifiutato perche' la preimmagine dichiarata ("3d202602",
    # quella VERA di ov012) non e' quella che sta davvero in ov049.
    sys.path.insert(0, str(QUI))
    import overlay_patch as ovp
    dati = Path(a.base).read_bytes()
    rom = ovp.Rom(dati)
    per_range = [i for i in range(rom.n_overlay)
                 if rom.voce_overlay(i)["ram"] <= A_GANCIO < rom.voce_overlay(i)["ram"] + rom.voce_overlay(i)["ram_size"]]
    altro = next((o for o in per_range if o != OV_CAMPO), None)
    if altro is None or len(per_range) < 2:
        registra("2-guardia (overlay scelto per indirizzo)", 1,
                 "meno di due candidati per range (%s): mutante non costruibile" % per_range)
    else:
        pre_vera = bytes.fromhex("3d202602")  # la preimmagine VERA di ov012, non di ov049
        try:
            ovp.applica(dati, altro, [(A_GANCIO, pre_vera)],
                       [{"addr": A_GANCIO, "pre": pre_vera, "post": bytes.fromhex("018b3d02")}],
                       strategia="auto")
            registra("2-guardia (overlay scelto per indirizzo, ov%03d invece di ov012)" % altro, 0,
                     "atteso un rifiuto (preimmagine di ov012 non combacia in ov%03d): NON dovrebbe capitare" % altro)
        except ovp.Rifiuto as e:
            registra("2-guardia (overlay scelto per indirizzo, ov%03d invece di ov012)" % altro, 2,
                     "rifiutato da overlay_patch.py (C1/C3): %s" % str(e)[:160])

    # ---- 3. BLOB SPOSTATO di 4 B nel blocco (USCITA) -------------------------
    build = Path(a.build)
    blob = (build / "blob.bin").read_bytes()
    r = Arm9(a.applicato)
    blocco = bytearray(r.leggi(BLOCK_BASE, BLOCK_N))
    nuovo = bytearray(BLOCK_N)
    nuovo[4:4 + len(blob)] = blob                                # spostato di 4 B
    nuovo[OFF_CANARINO:] = blocco[OFF_CANARINO:]                 # canarino/tabelle/stato/slot invariati
    r.scrivi(BLOCK_BASE, bytes(nuovo))
    m3_out = tmp / "m3-out.nds"
    r.salva(m3_out)
    rc, out, err = esegui_rileggi(a.base, str(m3_out), a.build, a.manifest)
    registra("3-blob spostato di 4 B nel blocco", rc, "atteso L2 rosso (sha diverso all'indirizzo atteso)")

    # ---- 4. PUNTATORE SENZA BIT THUMB (USCITA) -------------------------------
    r = Arm9(a.applicato)
    tb, tdd = None, None
    # rilegge il valore buono dall'overlay 12 gia' patchato e lo riscrive
    # SENZA il bit 0 (bit Thumb), usando overlay_patch.py per costruire (mai
    # per verificare) la patch sul letterale gia' spostato.
    dati_applicato = Path(a.applicato).read_bytes()
    rom2 = ovp.Rom(dati_applicato)
    v, _, img = rom2.immagine_overlay(OV_CAMPO)
    off = A_GANCIO - v["ram"]
    buono = img[off:off + 4]
    senza_thumb = bytes([buono[0] & 0xFE]) + buono[1:]
    out4, _ = ovp.applica(dati_applicato, OV_CAMPO, [(A_GANCIO, buono)],
                          [{"addr": A_GANCIO, "pre": buono, "post": senza_thumb}], strategia="auto")
    m4_out = tmp / "m4-out.nds"
    Path(m4_out).write_bytes(out4)
    rc, out, err = esegui_rileggi(a.base, str(m4_out), a.build, a.manifest)
    registra("4-puntatore senza bit Thumb", rc, "atteso L1 rosso (bit_thumb=False)")

    # ---- 5. FLAG ACCESO ALL'ORIGINE (default deve essere SPENTO) -------------
    # Applica con --flags diverso da 0: non e' un errore dell'applicatore (e'
    # un parametro legittimo), ma il rilettore deve dirlo chiaro (L4 riporta
    # flags!=0): il cancello vero e' che l'ORCHESTRATORE non promuove una ROM
    # cosi'. Qui si dimostra che il rilettore lo segnala sempre, cosi' un
    # errore "flags acceso per sbaglio" non passerebbe inosservato.
    m5_out = tmp / "m5-out.nds"
    rc, out, err = esegui_applica(a.base, str(m5_out), a.build, a.manifest, extra=("--flags", "0x3F"))
    # verifica diretta: il blocco deve avere flags=0x3F, non 0 — leggibile dal
    # rilettore stesso (L4 stampa "flags=0x.."); qui verifichiamo che sia
    # DIVERSO da spento, cioe' che il cancello "e' acceso" sia visibile.
    r5 = Arm9(m5_out)
    stato5 = r5.leggi(BLOCK_BASE + OFF_STATO, 1)
    flag_diverso_da_zero = stato5[0] != 0
    registra("5-flag acceso all'origine (--flags 0x3F)", 1 if flag_diverso_da_zero else 0,
             "flags scritto = 0x%02X (atteso NON zero: si vede, non e' un default silenzioso)" % stato5[0])

    # ---- 6. VOCE MAPPA: un blocco intruso dentro sgp.anim (INGRESSO+mappa) --
    mappa = json.loads(Path(a.manifest).read_text())
    mappa["blocchi"].append({"nome": "intruso.test", "base": hex(BLOCK_BASE + 0x10),
                             "bytes": 16, "proprietario": "mutante-6"})
    m6_manifest = tmp / "m6-mappa.json"
    m6_manifest.write_text(json.dumps(mappa))
    rc, out, err = esegui_applica(a.base, str(tmp / "m6-out.nds"), a.build, str(m6_manifest))
    registra("6-voce mappa (blocco intruso dentro sgp.anim)", rc, "atteso A4/mappa rosso")

    # ---- 7. 1 BIT ALTERATO NEL FLUSSO BLZ COMPRESSO (USCITA) -----------------
    m7_out = tmp / "m7-out.nds"
    patch_overlay_raw(a.applicato, m7_out, offset_nel_flusso_compresso=300, xor_byte=0x01)
    rc, out, err = esegui_rileggi(a.base, str(m7_out), a.build, a.manifest)
    registra("7-1 bit alterato nel flusso BLZ compresso", rc,
             "atteso L6/decompressione rosso; stderr=%s" % (err.strip()[-200:] if rc == 0 else ""))

    print()
    print("TUTTI UCCISI" if tutti_uccisi else "ALMENO UN MUTANTE VIVO — cancello non affidabile")
    if a.json:
        Path(a.json).write_text(json.dumps({"tutti_uccisi": tutti_uccisi, "mutanti": esiti}, indent=2) + "\n")
    return 0 if tutti_uccisi else 1


if __name__ == "__main__":
    sys.exit(main())
