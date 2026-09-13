#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-QUALITA-NATIVO-01 — riapplicatore dei quattro blob nativi corretti.

**NON E' STATO ESEGUITO.** Questo pacchetto è una revisione: i byte della ROM di
lavoro non sono stati toccati. Lo strumento è pronto e l'esecuzione è una
decisione dell'utente.

Che cosa riscrive (e nient'altro):

  blocco `sgp.plus` 0x023D8100, 2048 B — NUOVA PIANTA dei due blob di codice
      +0x000  blob PLUS           276 B   (era 592: via `plus_state.c`, morto)
      +0x120  blob SALVATAGGIO    532 B   (era a +0x630, 460 B)
      +0x114..+0x120 e +0x334..+0x400  a zero
      +0x400  tab_trainer · +0x500 tab_wild · +0x600 stato · +0x620 canarino
              INVARIATI, byte per byte
      +0x630..+0x800  azzerati: diventano 464 B liberi veri
  blocco `sgp.npc` 0x023D8900 — blob 128 B (stessa lunghezza, contenuto diverso);
      stato e canarino invariati
  blocco `sgp.wifi` 0x023DA000 — veneer G2/G3 rigenerati (i bersagli `blx` si
      spostano), blob 580 B a 0x023DA250 (era 660); stato W1 invariato

  ganci ri-puntati (stessa istruzione, nuovo bersaglio):
      arm9  0x02073718 / 0x02073802 / 0x0207390C / 0x02073A0C -> sgp_trainer_hook
      arm9  0x020271F8 -> sgp_gancio_carica · 0x02027456 -> sgp_gancio_salva
      arm9  0x020070A8 -> sgp_wfc_trampolino
      ov002 0x02247D3A -> sgp_wild_hook        (BLZ ricompresso in luogo)
      ov001 0x021FA570 -> sgp_npc_hook         (il simbolo NON si sposta: la BL
                                                resta identica e l'overlay non
                                                si tocca affatto)

Cancelli (nessuna uscita se uno solo cade):
  A0 provenienza  — l'ingresso è una delle due ROM di lavoro attese (sha256);
  A1 stato di partenza — i tre blocchi hanno ESATTAMENTE i blob vecchi attesi e
                  i sette ganci puntano ESATTAMENTE ai bersagli vecchi;
  A2 blob nuovi   — ricompilati qui, con gli sha256 del manifesto del pacchetto;
  A3 capienza     — ogni blob sta nel proprio blocco, i due di `sgp.plus` non si
                  sovrappongono e non toccano tab/stato/canarino;
  A4 invarianti   — tab_trainer, tab_wild, stato, i sei canarini e la zona 1.1
                  [0x023DEB40, 0x023E0000) restano identici al byte;
  A5 portata      — fuori dai tre blocchi e dai sette ganci non cambia un byte,
                  e la ROM non cambia lunghezza;
  A6 ri-lettura   — i sette ganci decodificati puntano ai nuovi simboli.

Uso (scrive un file NUOVO; l'ingresso resta intatto):
    python3 applicatori/riapplica_nativo.py --base <rom.nds> --out <uscita.nds> \\
        [--build DIR] [--json log.json] [--asciutto]

`--asciutto` esegue tutti i cancelli e stampa il piano SENZA scrivere niente:
è il modo in cui questo strumento è stato provato.

Serve il python3 di SISTEMA (clang per i blob). `overlay_patch.py` di
SGP-1.2-OVERLAY-01 fa la ricompressione BLZ in luogo; non serve ndspy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import os
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve()
PACCHETTO = QUI.parents[1]
W = PACCHETTO.parent
REPO = W.parents[1]
sys.path.insert(0, str(W / "SGP-1.2-PLUS-02/tools"))
sys.path.insert(0, str(W / "SGP-1.2-PRESTAZIONI-NPC-03/tools"))
sys.path.insert(0, str(W / "SGP-1.2-WIFI-04/tools"))
from arm9 import Arm9                                             # noqa: E402
import overlay_patch as OP                                        # noqa: E402
from compila_wifi4 import veneer_g2, veneer_g3, arm_b             # noqa: E402

ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))

BASI_ATTESE = {
    "EN": "02426b586e27ac51649c407969bc7cbba871cacec97961d506b6db3a51f23308",
    "IT": "9b6751b0515cedb726c8fe7779f7265c431799643bda71ff9fc2ffd358213323",
}

# --- pianta ----------------------------------------------------------------
PLUS_BASE, PLUS_N = 0x023D8100, 2048
OFF_BLOB_PLUS, OFF_BLOB_SALVA, FINE_CODICE = 0x000, 0x120, 0x400
OFF_TAB_TRN, OFF_TAB_WLD, OFF_STATO, OFF_CANARY = 0x400, 0x500, 0x600, 0x620
OFF_VECCHIO_SALVA, N_VECCHIO_SALVA = 0x630, 0x1D0
NPC_BASE, NPC_CODICE_N = 0x023D8900, 0xE0
WIFI_VEN2, WIFI_VEN3, WIFI_CODICE = 0x023DA000, 0x023DA020, 0x023DA250
WIFI_CODICE_N = 0x023DA800 - WIFI_CODICE
SITO_G2, SITO_G3 = 0x021FC150, 0x021EC4A4
ZONA11_BASE, ZONA11_N = 0x023DEB40, 0x023E0000 - 0x023DEB40

# --- stato di partenza atteso (prove/estratti/ESTRATTI.json) ---------------
VECCHI = {
    "blob PLUS": (PLUS_BASE, 592,
                  "0d4079400623bcb3260defd0af7642cb5ff30e5e0050954fb48c483bc5f15057"),
    "blob SALVATAGGIO": (PLUS_BASE + OFF_VECCHIO_SALVA, 460,
                         "35cccda383f33275036c40eee2a4ee8894a136838a48350d2f4db243514171b3"),
    "blob NPC": (NPC_BASE, 128,
                 "bda5f6de73a486c68a77be7e88f6e097c978fc4965b2abde95cf1a13d5f1a6a2"),
    "blob wifi_slot4": (WIFI_CODICE, 660,
                        "13a2d94f6260779667f960bc469b2951c6d7ac688b53d6ee0291bae3ff782ac1"),
}

# sito -> (bersaglio VECCHIO, nome del simbolo NUOVO)
GANCI_ARM9 = {
    0x02073718: (0x023D82E4, "sgp_trainer_hook"),
    0x02073802: (0x023D82E4, "sgp_trainer_hook"),
    0x0207390C: (0x023D82E4, "sgp_trainer_hook"),
    0x02073A0C: (0x023D82E4, "sgp_trainer_hook"),
    0x020271F8: (0x023D8730, "sgp_gancio_carica"),
    0x02027456: (0x023D8858, "sgp_gancio_salva"),
    0x020070A8: (0x023DA4B4, "sgp_wfc_trampolino"),
}
GANCI_OVERLAY = {
    0x02247D3A: (2, 0x023D8340, "sgp_wild_hook",
                 {0x02246C94: "00880328"}),          # guardia: identifica ov002
    0x021FA570: (1, 0x023D8970, "sgp_npc_hook",
                 {0x021FA564: "f0b5"}),              # prologo dell'ospite
}
BLOB_DEL_SIMBOLO = {"sgp_trainer_hook": "plus", "sgp_wild_hook": "plus",
                    "sgp_gancio_carica": "salva", "sgp_gancio_salva": "salva",
                    "sgp_npc_hook": "npc", "sgp_wfc_trampolino": "wifi"}


class Rifiuto(Exception):
    pass


def no(cancello, msg):
    raise Rifiuto("%s: %s" % (cancello, msg))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def bl_codifica(sito, bersaglio):
    delta = (bersaglio & ~1) - (sito + 4)
    if delta % 2 or not (-0x400000 <= delta < 0x400000):
        no("BL", "delta %d fuori portata da %08X a %08X" % (delta, sito, bersaglio))
    return struct.pack("<HH", 0xF000 | ((delta >> 12) & 0x7FF),
                       0xF800 | ((delta >> 1) & 0x7FF))


def bl_bersaglio(sito, b):
    hi, lo = struct.unpack("<HH", b)
    off = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if off & 0x400000:
        off -= 0x800000
    if (hi & 0xF800) != 0xF000 or (lo & 0xF800) != 0xF800:
        no("A1", "a %08X non c'è una BL Thumb-1 (%s)" % (sito, b.hex()))
    return sito + 4 + off


def compila(dest):
    r = subprocess.run([sys.executable, str(PACCHETTO / "tools" / "compila_tutti.py"),
                        "--uscita", str(dest)], text=True, capture_output=True)
    man = dest / "manifesto.json"
    if not man.exists():
        no("A2", "compilazione fallita\n" + r.stdout + r.stderr)
    return json.loads(man.read_text())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--build", type=Path)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--asciutto", action="store_true",
                    help="esegue tutti i cancelli e stampa il piano, senza scrivere")
    a = ap.parse_args(argv)
    if not a.asciutto and not a.out:
        ap.error("serve --out (o --asciutto)")

    registro = {"strumento": str(QUI.relative_to(REPO)), "asciutto": a.asciutto}
    grezzo = a.base.read_bytes()
    s_in = sha(grezzo)
    registro["ingresso_sha256"] = s_in
    lingua = next((k for k, v in BASI_ATTESE.items() if v == s_in), None)
    if lingua is None:
        no("A0", "l'ingresso %s non è una ROM di lavoro attesa (%s)" % (a.base, s_in))
    registro["lingua"] = lingua

    # --- A2: i blob nuovi --------------------------------------------------
    tmp = None
    dest = a.build
    if dest is None:
        tmp = tempfile.TemporaryDirectory(prefix="sgp-riappl-")
        dest = Path(tmp.name)
    man = compila(dest)
    blob = {k: (dest / (k + ".bin")).read_bytes() for k in man["blob"]}
    simboli = {k: {n: int(x, 16) for n, x in v["simboli"].items() if not n.startswith("$")}
               for k, v in man["blob"].items()}
    registro["blob_nuovi"] = {k: {"byte": len(v), "sha256": sha(v)} for k, v in blob.items()}

    # --- A3: capienza ------------------------------------------------------
    fine_plus = OFF_BLOB_PLUS + len(blob["plus"])
    fine_salva = OFF_BLOB_SALVA + len(blob["salva"])
    if fine_plus > OFF_BLOB_SALVA:
        no("A3", "il blob PLUS (%d B) invade il blob salvataggio a +0x%X" % (len(blob["plus"]), OFF_BLOB_SALVA))
    if fine_salva > FINE_CODICE:
        no("A3", "il blob salvataggio (%d B) supera +0x400" % len(blob["salva"]))
    if len(blob["npc"]) > NPC_CODICE_N:
        no("A3", "il blob NPC (%d B) supera i %d B del suo slot" % (len(blob["npc"]), NPC_CODICE_N))
    if len(blob["wifi"]) > WIFI_CODICE_N:
        no("A3", "il blob WiFi (%d B) supera i %d B del suo slot" % (len(blob["wifi"]), WIFI_CODICE_N))

    a9 = Arm9(a.base)

    # --- A1: stato di partenza --------------------------------------------
    for nome, (ram, n, atteso) in VECCHI.items():
        letto = sha(a9.leggi(ram, n))
        if letto != atteso:
            no("A1", "%s a %08X: sha %s invece di %s (la ROM non è quella attesa, "
                     "o qualcuno ha già riapplicato)" % (nome, ram, letto, atteso))
    for sito, (vecchio_dst, simbolo) in GANCI_ARM9.items():
        letto = bl_bersaglio(sito, bytes(a9.leggi(sito, 4)))
        if letto != vecchio_dst:
            no("A1", "gancio %08X punta a %08X invece di %08X" % (sito, letto, vecchio_dst))

    rom = OP.Rom(grezzo)
    patch_overlay = {}
    for sito, (oid, vecchio_dst, simbolo, guardie) in GANCI_OVERLAY.items():
        voce, _, dec = rom.immagine_overlay(oid)
        pre = dec[sito - voce["ram"]: sito - voce["ram"] + 4]
        if bl_bersaglio(sito, pre) != vecchio_dst:
            no("A1", "gancio ov%03d %08X punta a %08X invece di %08X"
               % (oid, sito, bl_bersaglio(sito, pre), vecchio_dst))
        nuovo = bl_codifica(sito, simboli[BLOB_DEL_SIMBOLO[simbolo]][simbolo] & ~1)
        if nuovo == pre:
            # il simbolo non si e' spostato: non si tocca l'overlay (ricomprimere
            # BLZ per riscrivere gli stessi quattro byte e' rischio senza scopo)
            registro.setdefault("overlay_gia_a_posto", []).append(
                {"overlay": oid, "sito": hex(sito), "simbolo": simbolo})
            continue
        patch_overlay.setdefault(oid, []).append((sito, pre, nuovo, guardie, simbolo))

    # --- il piano ----------------------------------------------------------
    invarianti = {
        "tab_trainer": sha(a9.leggi(PLUS_BASE + OFF_TAB_TRN, 256)),
        "tab_wild": sha(a9.leggi(PLUS_BASE + OFF_TAB_WLD, 256)),
        "stato": sha(a9.leggi(PLUS_BASE + OFF_STATO, 32)),
        "canarino_plus": sha(a9.leggi(PLUS_BASE + OFF_CANARY, 16)),
        "blocco_salvataggio": sha(a9.leggi(0x023D8F00, 256)),
        "stato_npc": sha(a9.leggi(0x023D89E0, 16)),
        "canarino_npc": sha(a9.leggi(0x023D8A00, 16)),
        "stato_wifi": sha(a9.leggi(0x023DA240, 32)),
        "zona_1_1": sha(a9.leggi(ZONA11_BASE, ZONA11_N)),
    }
    registro["invarianti_prima"] = invarianti

    scritture = []
    scritture.append(("azzera codice sgp.plus", PLUS_BASE, bytes(FINE_CODICE)))
    scritture.append(("blob PLUS", PLUS_BASE + OFF_BLOB_PLUS, blob["plus"]))
    scritture.append(("blob SALVATAGGIO", PLUS_BASE + OFF_BLOB_SALVA, blob["salva"]))
    scritture.append(("azzera il vecchio posto del blob salvataggio",
                      PLUS_BASE + OFF_VECCHIO_SALVA, bytes(N_VECCHIO_SALVA)))
    scritture.append(("azzera codice sgp.npc", NPC_BASE, bytes(NPC_CODICE_N)))
    scritture.append(("blob NPC", NPC_BASE, blob["npc"]))
    scritture.append(("azzera codice sgp.wifi", WIFI_CODICE, bytes(WIFI_CODICE_N)))
    scritture.append(("blob wifi_slot4", WIFI_CODICE, blob["wifi"]))
    scritture.append(("veneer G2", WIFI_VEN2,
                      veneer_g2(WIFI_VEN2, simboli["wifi"]["sgp_wfc_nibble"], SITO_G2 + 4)))
    scritture.append(("veneer G3", WIFI_VEN3,
                      veneer_g3(WIFI_VEN3, simboli["wifi"]["sgp_wfc_on_connect"], SITO_G3 + 4)))
    for sito, (_, simbolo) in GANCI_ARM9.items():
        dst = simboli[BLOB_DEL_SIMBOLO[simbolo]][simbolo]
        scritture.append(("gancio %08X -> %s" % (sito, simbolo), sito, bl_codifica(sito, dst)))
    registro["scritture"] = [{"cosa": c, "ram": hex(r), "bytes": len(b)} for c, r, b in scritture]
    registro["patch_overlay"] = [
        {"overlay": oid, "sito": hex(s), "pre": p.hex(), "post": n.hex(), "simbolo": sim}
        for oid, voci in patch_overlay.items() for s, p, n, _, sim in voci]

    if a.asciutto:
        print(json.dumps(registro, indent=2))
        if a.json:
            a.json.write_text(json.dumps(registro, indent=2) + "\n")
        return 0

    # --- scrittura ---------------------------------------------------------
    lavoro = Path(tempfile.mkdtemp(prefix="sgp-riappl-rom-"))
    try:
        parziale = lavoro / "parziale.nds"
        shutil.copy2(a.base, parziale)
        a9w = Arm9(parziale)
        for _, ram, byte in scritture:
            a9w.scrivi(ram, byte)
        a9w.salva(parziale)

        dati = parziale.read_bytes()
        for oid, voci in patch_overlay.items():
            guardie, patch = {}, []
            for sito, pre, nuovo, g, _ in voci:
                guardie.update(g)
                patch.append((sito, pre, nuovo))
            dati = OP.applica(dati, oid,
                              [OP.analizza_guardia("%#x:%s" % (k, v)) for k, v in guardie.items()],
                              [OP.analizza_patch("%#x:%s:%s" % (s, p.hex(), n.hex()))
                               for s, p, n in patch])[0]
        Path(a.out).write_bytes(dati)

        # --- A4/A5/A6: ri-lettura ---------------------------------------------
        a9o = Arm9(a.out)
        dopo = {k: v for k, v in invarianti.items()}
        for k, (ram, n) in {"tab_trainer": (PLUS_BASE + OFF_TAB_TRN, 256),
                            "tab_wild": (PLUS_BASE + OFF_TAB_WLD, 256),
                            "stato": (PLUS_BASE + OFF_STATO, 32),
                            "canarino_plus": (PLUS_BASE + OFF_CANARY, 16),
                            "blocco_salvataggio": (0x023D8F00, 256),
                            "stato_npc": (0x023D89E0, 16),
                            "canarino_npc": (0x023D8A00, 16),
                            "stato_wifi": (0x023DA240, 32),
                            "zona_1_1": (ZONA11_BASE, ZONA11_N)}.items():
            letto = sha(a9o.leggi(ram, n))
            if letto != dopo[k]:
                no("A4", "%s è cambiato (%s -> %s)" % (k, dopo[k], letto))
        if len(Path(a.out).read_bytes()) != len(grezzo):
            no("A5", "la ROM ha cambiato lunghezza")
        for sito, (_, simbolo) in GANCI_ARM9.items():
            atteso = simboli[BLOB_DEL_SIMBOLO[simbolo]][simbolo] & ~1
            letto = bl_bersaglio(sito, bytes(a9o.leggi(sito, 4)))
            if letto != atteso:
                no("A6", "gancio %08X punta a %08X invece di %08X" % (sito, letto, atteso))
        romo = OP.Rom(Path(a.out).read_bytes())
        for sito, (oid, _, simbolo, _) in GANCI_OVERLAY.items():   # anche quelli non toccati
            voce, _, dec = romo.immagine_overlay(oid)
            atteso = simboli[BLOB_DEL_SIMBOLO[simbolo]][simbolo] & ~1
            letto = bl_bersaglio(sito, dec[sito - voce["ram"]: sito - voce["ram"] + 4])
            if letto != atteso:
                no("A6", "gancio ov%03d %08X punta a %08X invece di %08X" % (oid, sito, letto, atteso))

        registro["uscita_sha256"] = sha(Path(a.out).read_bytes())
        registro["esito"] = "VERDE"
        if a.json:
            a.json.write_text(json.dumps(registro, indent=2) + "\n")
        print(json.dumps(registro, indent=2))
        if tmp:
            tmp.cleanup()
        return 0
    finally:
        shutil.rmtree(lavoro, ignore_errors=True)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Rifiuto as e:
        print("RIFIUTATO — %s" % e, file=sys.stderr)
        sys.exit(2)
