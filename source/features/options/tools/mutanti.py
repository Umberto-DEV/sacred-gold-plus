#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutanti dell'INIEZIONE — SGP-1.2-OPZIONI-04 (CRITERI.md §mutanti).

Colpiscono l'applicatore/rilettore (`applica_opzioni_v2.py` / `rileggi_opzioni_v2.py`),
non il payload C (quello e' gia' coperto dai 27 mutanti di sorgente di
SGP-1.2-OPZIONI-03/tools/mutanti.py, non toccati qui). Otto dei dieci sono
un porto letterale (stessi bersagli, stesso metodo) degli otto mutanti
dell'iniezione di SGP-1.2-OPZIONI-02/tools/mutanti_iniezione.py, adattati ai
nomi v2 (`BLOCK_BASE`/`PRE_A` ecc. sono identici) e al layout a DUE blocchi.
I2 nuovi (I9, I10) sono specifici della v2: il rifiuto "per costruzione" di
una ROM dove la v1 e' gia' applicata, e un canarino spostato.

Ogni mutante DEVE essere ucciso da `applica_opzioni_v2.py` (rifiuto in
scrittura) o da `rileggi_opzioni_v2.py` (esito ROSSO/eccezione). Lavora su
COPIE nella scratchpad di sistema (`tempfile`), mai sulla ROM di lavoro.

Uso: mutanti.py --rom <copia-EN.nds> [--build <dir>] [--uscita prove/mutanti.json]
"""
import argparse
import importlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
OVERLAY01 = QUI.parent.parent / "SGP-1.2-OVERLAY-01" / "tools"
sys.path.insert(0, str(OVERLAY01))
import overlay_patch as ovp   # noqa: E402


def ucciso_applicatore(rom_path, build_dir, lingua, patch_mod, manifest_path=None):
    """Applica con le costanti di modulo eventualmente alterate da `patch_mod`
    (dict nome->valore, ripristinato subito dopo). Ritorna (ucciso, dettaglio)."""
    import applica_opzioni_v2 as ao
    importlib.reload(ao)
    originali = {}
    for k, v in patch_mod.items():
        originali[k] = getattr(ao, k)
        setattr(ao, k, v)
    try:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.nds"
            try:
                ao.applica(rom_path, out, build_dir, lingua, manifest_path, None)
                return False, "applicato senza obiezioni: NON ucciso"
            except ao.Rifiuto as e:
                return True, "RIFIUTATO dall'applicatore: %s" % e
    finally:
        for k, v in originali.items():
            setattr(ao, k, v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True, help="copia (mai la ROM di lavoro) gia' verificata come ingresso valido")
    ap.add_argument("--build", default=str(QUI.parent / "work" / "build"))
    ap.add_argument("--lingua", default="EN", choices=("EN", "IT"))
    ap.add_argument("--uscita", type=Path, default=QUI.parent / "prove" / "mutanti.json")
    a = ap.parse_args()

    rom = str(Path(a.rom).resolve())
    build = str(Path(a.build).resolve())
    esiti = {}

    import applica_opzioni_v2 as ao_ref
    man = json.loads((Path(build) / "manifesto.json").read_text())
    gancio = int(man["simboli"]["sgp_opz_hook"], 16)

    # I1 — preimmagine A presa dalla POSTIMMAGINE (l'errore documentato della 1.1)
    post_a = ao_ref.bl_thumb(ao_ref.SITO_A, gancio)
    ok, det = ucciso_applicatore(rom, build, a.lingua, {"PRE_A": post_a})
    esiti["I1_preimmagine_A_dalla_postimmagine"] = {"ucciso": ok, "dettaglio": det}

    # I2 — preimmagine B1 sbagliata (un byte alterato)
    pre_b1_sbagliata = struct.pack("<I", 0x020FA16D)   # ultimo byte +1
    ok, det = ucciso_applicatore(rom, build, a.lingua, {"PRE_B1": pre_b1_sbagliata})
    esiti["I2_preimmagine_B1_sbagliata"] = {"ucciso": ok, "dettaglio": det}

    # I3 — preimmagine B2 sbagliata
    pre_b2_sbagliata = struct.pack("<I", 0x020FA15D)
    ok, det = ucciso_applicatore(rom, build, a.lingua, {"PRE_B2": pre_b2_sbagliata})
    esiti["I3_preimmagine_B2_sbagliata"] = {"ucciso": ok, "dettaglio": det}

    # I4 — blob compilato per un indirizzo diverso da quello assegnato
    # (riusa il build di OPZIONI-01, compilato per 0x023D8900): M1 deve rifiutare.
    build_i4 = str((QUI.parent.parent / "SGP-1.2-OPZIONI-01" / "work" / "build").resolve())
    if Path(build_i4).is_dir() and (Path(build_i4) / "manifesto.json").is_file():
        import applica_opzioni_v2 as ao4
        importlib.reload(ao4)
        try:
            with tempfile.TemporaryDirectory() as td:
                out = Path(td) / "out.nds"
                ao4.applica(rom, out, build_i4, a.lingua, None, None)
            esiti["I4_blob_spostato"] = {"ucciso": False, "dettaglio": "applicato senza obiezioni: NON ucciso"}
        except ao4.Rifiuto as e:
            esiti["I4_blob_spostato"] = {"ucciso": True, "dettaglio": "RIFIUTATO: %s" % e}
    else:
        esiti["I4_blob_spostato"] = {"ucciso": None, "dettaglio": "build di OPZIONI-01 non trovato, mutante non eseguito"}

    # I5 — testo troncato: si scrive un build con testi-{lingua}.bin TRONCATO,
    # l'applicatore (che non valida il contenuto del testo) lo applica senza
    # obiezioni; il rilettore, confrontato col build CORRETTO, deve vedere lo
    # sha256 diverso (L3) e dichiarare ROSSO.
    with tempfile.TemporaryDirectory() as td:
        build_i5 = Path(td) / "build"
        shutil.copytree(build, build_i5)
        testi_path = build_i5 / f"testi-{a.lingua}.bin"
        dati = testi_path.read_bytes()
        testi_path.write_bytes(dati[: len(dati) // 2])
        out_i5 = Path(td) / "out.nds"
        import applica_opzioni_v2 as ao5
        importlib.reload(ao5)
        try:
            ao5.applica(rom, out_i5, str(build_i5), a.lingua, None, None)
            r = subprocess.run([sys.executable, str(QUI / "rileggi_opzioni_v2.py"), rom, str(out_i5),
                               "--build", build, "--lingua", a.lingua],
                               capture_output=True, text=True)
            esiti["I5_testo_troncato"] = {"ucciso": r.returncode != 0,
                                          "dettaglio": "rilettore rc=%d (atteso != 0)" % r.returncode,
                                          "stdout_ultima_riga": r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""}
        except ao5.Rifiuto as e:
            esiti["I5_testo_troncato"] = {"ucciso": True, "dettaglio": "RIFIUTATO gia' in scrittura: %s" % e}

    # I6 — voce di mappa in conflitto: un blocco finto sovrapposto a sgp.opzioni
    with tempfile.TemporaryDirectory() as td:
        mappa = {"blocchi": [{"nome": "finto.conflitto", "base": "0x023D9080", "bytes": 64}]}
        mpath = Path(td) / "mappa-finta.json"
        mpath.write_text(json.dumps(mappa))
        out_i6 = Path(td) / "out.nds"
        import applica_opzioni_v2 as ao6
        importlib.reload(ao6)
        try:
            ao6.applica(rom, out_i6, build, a.lingua, str(mpath), None)
            esiti["I6_voce_mappa_in_conflitto"] = {"ucciso": False, "dettaglio": "applicato senza obiezioni: NON ucciso"}
        except ao6.Rifiuto as e:
            esiti["I6_voce_mappa_in_conflitto"] = {"ucciso": True, "dettaglio": "RIFIUTATO: %s" % e}

    # I7 — 1 bit alterato nel flusso BLZ di ov054 DOPO l'applicazione
    # (corruzione del file compresso finale): il rilettore deve leggerlo ROSSO
    # o sollevare un'eccezione (decompressione impossibile/immagine diversa).
    with tempfile.TemporaryDirectory() as td:
        out_buono = Path(td) / "buono.nds"
        import applica_opzioni_v2 as ao7
        importlib.reload(ao7)
        ao7.applica(rom, out_buono, build, a.lingua, None, None)
        dati = bytearray(out_buono.read_bytes())
        rom_ro = ovp.Rom(bytes(dati))
        v54 = rom_ro.voce_overlay(ao7.OV_A)
        fat = rom_ro.voce_fat(v54["file_id"])
        meta = fat["inizio"] + (fat["fine"] - fat["inizio"]) // 2
        dati[meta] ^= 0x01
        out_corrotto = Path(td) / "corrotto.nds"
        out_corrotto.write_bytes(bytes(dati))
        r = subprocess.run([sys.executable, str(QUI / "rileggi_opzioni_v2.py"), rom, str(out_corrotto),
                           "--build", build, "--lingua", a.lingua],
                           capture_output=True, text=True)
        esiti["I7_bit_alterato_flusso_ov054"] = {
            "ucciso": r.returncode != 0,
            "dettaglio": "rilettore rc=%d (atteso != 0: ROSSO o eccezione BLZ)" % r.returncode,
            "stderr_ultima_riga": r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "",
        }

    # I8 — flag "compresso" incoerente col corpo scritto (il guasto reale di
    # OPZIONI-01, fotogramma 2091): si spegne il bit compresso nella voce y9
    # di ov054 SENZA decomprimere il corpo.
    with tempfile.TemporaryDirectory() as td:
        out_buono = Path(td) / "buono.nds"
        import applica_opzioni_v2 as ao8
        importlib.reload(ao8)
        ao8.applica(rom, out_buono, build, a.lingua, None, None)
        dati = bytearray(out_buono.read_bytes())
        rom_ro = ovp.Rom(bytes(dati))
        v54 = rom_ro.voce_overlay(ao8.OV_A)
        parola_off = v54["offset_voce"] + 28
        parola = struct.unpack_from("<I", dati, parola_off)[0]
        parola_incoerente = parola & 0x00FFFFFF
        struct.pack_into("<I", dati, parola_off, parola_incoerente)
        out_incoerente = Path(td) / "incoerente.nds"
        out_incoerente.write_bytes(bytes(dati))
        r = subprocess.run([sys.executable, str(QUI / "rileggi_opzioni_v2.py"), rom, str(out_incoerente),
                           "--build", build, "--lingua", a.lingua],
                           capture_output=True, text=True)
        esiti["I8_flag_compresso_incoerente"] = {
            "ucciso": r.returncode != 0,
            "dettaglio": "rilettore rc=%d (atteso != 0)" % r.returncode,
            "stdout_ultima_riga": r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "",
        }

    # I9 — SPECIFICO v2: applicare sopra una ROM dove la v1 e' GIA' applicata
    # (SGP-1.2-OPZIONI-01/02). Deve rifiutare "per costruzione": i siti dei
    # ganci non hanno piu' la preimmagine vanilla (A7/A3), prima ancora di
    # controllare se i blocchi sono a zero.
    build_v1 = QUI.parent.parent / "SGP-1.2-OPZIONI-02" / "work" / "build"
    applica_v1 = QUI.parent.parent / "SGP-1.2-OPZIONI-02" / "tools" / "applica_opzioni.py"
    if build_v1.is_dir() and applica_v1.is_file():
        with tempfile.TemporaryDirectory() as td:
            rom_v1 = Path(td) / "v1.nds"
            r1 = subprocess.run([sys.executable, str(applica_v1), "--base", rom, "--out", str(rom_v1),
                                "--lingua", a.lingua, "--build", str(build_v1), "--niente-registro"],
                               capture_output=True, text=True)
            if r1.returncode != 0:
                esiti["I9_sopra_v1_gia_applicata"] = {"ucciso": None,
                    "dettaglio": "applicatore v1 non ha prodotto una ROM di prova (rc=%d): mutante non eseguito" % r1.returncode}
            else:
                import applica_opzioni_v2 as ao9
                importlib.reload(ao9)
                out_i9 = Path(td) / "v2-sopra-v1.nds"
                try:
                    ao9.applica(str(rom_v1), out_i9, build, a.lingua, None, None)
                    esiti["I9_sopra_v1_gia_applicata"] = {"ucciso": False, "dettaglio": "applicato senza obiezioni: NON ucciso"}
                except ao9.Rifiuto as e:
                    esiti["I9_sopra_v1_gia_applicata"] = {"ucciso": True, "dettaglio": "RIFIUTATO per costruzione: %s" % e}
    else:
        esiti["I9_sopra_v1_gia_applicata"] = {"ucciso": None,
            "dettaglio": "build/applicatore di OPZIONI-02 non trovati: mutante non eseguito"}

    # I10 — SPECIFICO v2: canarino del blocco testi spostato di 16 B (un
    # off-by-16 nell'applicatore, come l'errore reale trovato in OPZIONI-03
    # §4.2, dove il canarino finiva sopra il blocco del vicino). Il rilettore
    # (che ricalcola l'offset atteso da SE', non lo eredita dall'applicatore)
    # deve vedere ROSSO su L5b.
    ok, det = ucciso_applicatore(rom, build, a.lingua, {"TESTI_CANARY_OFF": 0x3E0})
    esiti["I10_canarino_testi_spostato"] = {"ucciso": True if ok else False, "dettaglio": det}
    if not ok:
        # l'applicatore non se ne accorge (e' un dettaglio interno, non un
        # cancello di scrittura): controlla che lo veda il RILETTORE.
        with tempfile.TemporaryDirectory() as td:
            import applica_opzioni_v2 as ao10
            importlib.reload(ao10)
            originale = ao10.TESTI_CANARY_OFF
            ao10.TESTI_CANARY_OFF = 0x3E0
            out_i10 = Path(td) / "out.nds"
            try:
                ao10.applica(rom, out_i10, build, a.lingua, None, None)
                r = subprocess.run([sys.executable, str(QUI / "rileggi_opzioni_v2.py"), rom, str(out_i10),
                                   "--build", build, "--lingua", a.lingua],
                                   capture_output=True, text=True)
                esiti["I10_canarino_testi_spostato"] = {
                    "ucciso": r.returncode != 0,
                    "dettaglio": "applicatore non l'ha visto (nessun cancello dedicato); rilettore rc=%d (atteso != 0)" % r.returncode,
                }
            finally:
                ao10.TESTI_CANARY_OFF = originale

    vivi = [k for k, v in esiti.items() if v["ucciso"] is False]
    non_eseguiti = [k for k, v in esiti.items() if v["ucciso"] is None]
    out = {"schema": 1, "pacchetto": "SGP-1.2-OPZIONI-04", "proposti": len(esiti),
           "uccisi": sum(1 for v in esiti.values() if v["ucciso"]),
           "sopravvissuti": vivi, "non_eseguiti": non_eseguiti, "esiti": esiti}
    a.uscita.parent.mkdir(parents=True, exist_ok=True)
    a.uscita.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"proposti": out["proposti"], "uccisi": out["uccisi"],
                      "sopravvissuti": vivi, "non_eseguiti": non_eseguiti}, indent=1))
    return 1 if vivi else 0


if __name__ == "__main__":
    raise SystemExit(main())
