#!/usr/bin/env python3
"""APPLICATORE P2 fase 2 — tetto NPC per fotogramma (SGP-1.2-PRESTAZIONI-NPC-02).

Scrive il blocco `sgp.npc` (256 B a 0x023D8900, primo spazio libero allineato
a 0x100 dopo i blocchi registrati in MAPPA-RISERVA-ARM9.json alla data del
12/09: `sgp.plus` finisce esattamente a 0x023D8900) + il canarino di coda
(16 B a 0x023D8A00), e patcha il gancio a 0x021FA570 in overlay 1 (4 B:
`e0 30 00 68` -> `BL sgp_npc_hook`), USANDO `overlay_patch.py` (ricompressione
BLZ ottima IN LUOGO, mai riloco: SGP-1.2-OVERLAY-01/RAPPORTO.md §7-8).

Logica e ganci: CONTRATTO-P2.md e PIANO-INIEZIONE.md di
SGP-1.2-PRESTAZIONI-NPC-01, gia' provati su una zona di prova. Qui cambia SOLO
la collocazione (blocco vero, non zona di prova) e lo strumento di patch
dell'overlay (`overlay_patch.py` anziche' `ndspy` diretto: niente riloco).

Non modifica MAI l'ingresso. Rifiuta (RIFIUTATO, rc=2) tutto quello che non
riconosce: A0-A7 sotto, CRITERI.md §2.

FASE 02b — il flag di abilitazione NON vive piu' solo nello stato in RAM di
`sgp.npc`: da questa fase il gancio lo rilegge, a ogni esecuzione, dal chunk
di salvataggio PUBBLICO di PLUS-03 (`SGP-1.2-PLUS-03/CONTRATTO-CHUNK.md`,
campo `npc` a 0x023D8717, guardato da `load_status` a 0x023D8703): chunk
ASSENTE -> acceso di default (mandato P2), chunk VALIDO -> il byte che
contiene, qualunque altro stato -> spento per prudenza. `--attivo` **non e'
piu' un interruttore**: resta come SEME scritto nello stato all'iniezione
(offset 0 del blocco), sovrascritto dal gancio al primo giro con la
decisione presa dal chunk — vedi `sorgenti/npc_tetto.c` per la logica. La
riserva azzerata (blocco non ancora scritto, guardia != 0x5A) resta spenta
per costruzione (il gancio non trova la guardia e non fa nulla): questo non
e' cambiato.

Uso normale (scrive un file NUOVO, l'ingresso resta intatto):
    applica_npc.py --base <sgp-1.2-XX.nds> --out <uscita.nds> --build <dir> \\
                    [--manifest MAPPA-RISERVA-ARM9.json] [--attivo 0|1] [--tetto N] \\
                    [--json log.json]

Uso «in luogo» (stessa disciplina di SGP-1.2-PLUS-02/tools/applica_plus.py):
copia in una cartella temporanea, applica li', rilegge li' con
`rileggi_npc.py`, e SOLO se tutto e' verde sostituisce il file originale e
aggiorna SHA256SUMS/LEGGIMI.md della cartella ROM condivisa:
    applica_npc.py --in-luogo <rom.nds> --build <dir> [--manifest ...] [--tmp <scratchpad>]

NON deve essere invocato con --in-luogo da questo pacchetto in questa fase:
il lucchetto di scrittura sulla ROM di lavoro condivisa e' di un altro
cantiere. Qui si valida solo su COPIE (`--base/--out`).
"""
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

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
from arm9 import Arm9                    # noqa: E402
import overlay_patch as ovp              # noqa: E402

REPO = Path(__file__).resolve().parents[4]
ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))

OV_CAMPO = 1
# contesto (12 B, invariato EN/IT, CONTRATTO-P2.md §1.1) + preimmagine del
# gancio (4 B): sono CONTIGUI (0x021FA564..0x021FA574), quindi un'unica
# guardia di 16 B individua l'overlay E verifica che il gancio non sia gia'
# stato spostato da un refactor futuro.
A_CONTESTO = 0x021FA564
PRE_CONTESTO_PIU_GANCIO = bytes.fromhex("f8b500910121009809024458" + "e0300068")
A_GANCIO = 0x021FA570
PRE_GANCIO = bytes.fromhex("e0300068")

BLOCK_BASE, BLOCK_N = 0x023D8900, 0x100          # 256 B
OFF_BLOB, N_BLOB_SLOT = 0x000, 0x0E0             # blob reale: 100 B
OFF_STATO, N_STATO = 0x0E0, 16                   # fino a 0x0F0
# 0x0F0..0x100: 16 B di margine, a zero, non assegnato.
CANARY_BASE, N_CANARY = BLOCK_BASE + BLOCK_N, 16  # 0x023D8A00
CANARY_MOTIVO = 0xCA5A1300   # 0x...1000/1100/1200 gia' presi (RISERVA-01/CAMERA-01/PLUS-02)

ENTRATE_ATTESE = ("sgp_npc_hook", "sgp_npc_tetto")


class Rifiuto(Exception):
    pass


def no(cancello, msg):
    raise Rifiuto("%s: %s" % (cancello, msg))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def bl_thumb(sito, bersaglio):
    delta = (bersaglio & ~1) - (sito + 4)
    if delta % 2 != 0 or not (-0x400000 <= delta < 0x400000):
        raise Rifiuto("BL fuori portata: %#x -> %#x (delta %d)" % (sito, bersaglio, delta))
    hi = 0xF000 | ((delta >> 12) & 0x7FF)
    lo = 0xF800 | ((delta >> 1) & 0x7FF)
    return struct.pack("<HH", hi, lo)


def carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    if int(man["indirizzi"]["codice"], 16) != BLOCK_BASE + OFF_BLOB:
        no("BUILD", "blob compilato per %s, atteso 0x%08X: ricompila con --codice"
           % (man["indirizzi"]["codice"], BLOCK_BASE + OFF_BLOB))
    if int(man["indirizzi"]["stato"], 16) != BLOCK_BASE + OFF_STATO:
        no("BUILD", "indirizzo stato incoerente col blocco sgp.npc")
    if len(blob) > N_BLOB_SLOT:
        no("BUILD", "blob %d B non entra nei %d B riservati" % (len(blob), N_BLOB_SLOT))
    for nome in ENTRATE_ATTESE:
        if nome not in man["simboli"]:
            no("BUILD", "simbolo mancante nel manifesto: %s" % nome)
    return man, blob


def verifica_manifest_mappa(manifest_path, log):
    """A4: se una mappa e' data, il blocco sgp.npc non deve sovrapporsi a NESSUN
    blocco gia' registrato, e se una voce sgp.npc esiste gia' deve combaciare."""
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    lo, hi = BLOCK_BASE, CANARY_BASE + N_CANARY
    for b in mappa["blocchi"]:
        base = int(b["base"], 16)
        n = b.get("bytes", 0)
        if b["nome"] == "libero.1.2":
            continue  # e' esattamente lo spazio libero che questo pacchetto occupa
        if b["nome"] in ("sgp.npc", "canarino.npc"):
            if base != (BLOCK_BASE if b["nome"] == "sgp.npc" else CANARY_BASE) or n != (BLOCK_N if b["nome"] == "sgp.npc" else N_CANARY):
                no("A4/mappa", "voce '%s' gia' registrata con base/bytes diversi da quelli attesi" % b["nome"])
            continue
        if base < hi and base + n > lo:
            no("A4/mappa", "il blocco sgp.npc [%#x,%#x) si sovrappone a '%s' [%#x,%#x)"
               % (lo, hi, b["nome"], base, base + n))
    log["manifest_controllato"] = True


def applica(ingresso, uscita, build_dir, manifest_path, attivo, tetto, json_path):
    log = {"strumento": "SGP-1.2-PRESTAZIONI-NPC-02/tools/applica_npc.py",
           "ingresso": str(ingresso), "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})
        print("  %-4s passato  %s" % (c, msg))

    if not (1 <= tetto <= 255):
        no("PARAM", "tetto fuori intervallo 1..255")
    if attivo not in (0, 1):
        no("PARAM", "attivo deve essere 0 o 1")

    man, blob = carica_build(build_dir)
    verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione col resto della mappa (o mappa non fornita)")

    dati_in = Path(ingresso).read_bytes()
    log["sha256_ingresso"] = sha(dati_in)
    log["ingresso_bytes"] = len(dati_in)

    # ---------------- scrittura ARM9 (blocco + canarino) --------------------
    with tempfile.TemporaryDirectory() as td:
        arm9_tmp = Path(td) / "arm9-step.nds"
        shutil.copyfile(ingresso, arm9_tmp)
        r = Arm9(arm9_tmp)
        prima = bytes(r.raw)

        # A0: idempotenza — il blocco deve essere ancora tutto a zero
        zona = r.leggi(BLOCK_BASE, BLOCK_N)
        if zona != bytes(BLOCK_N):
            primo = next(i for i, x in enumerate(zona) if x)
            no("A0", "il blocco sgp.npc a 0x%08X non e' a zero (primo byte non nullo a +0x%X): "
                     "gia' applicato, o occupato da qualcun altro" % (BLOCK_BASE, primo))
        ok("A0", "256 B a 0x%08X tutti a zero" % BLOCK_BASE)

        # A1: il canarino di coda deve essere anch'esso a zero (nessuno l'ha gia' preso)
        can_zona = r.leggi(CANARY_BASE, N_CANARY)
        if can_zona != bytes(N_CANARY):
            no("A1", "i 16 B del canarino a 0x%08X non sono a zero" % CANARY_BASE)
        ok("A1", "16 B del canarino a 0x%08X a zero" % CANARY_BASE)

        blocco = bytearray(BLOCK_N)
        blocco[OFF_BLOB:OFF_BLOB + len(blob)] = blob
        stato = bytearray(N_STATO)
        stato[0x0] = attivo & 1   # seme: il gancio lo sovrascrive dal chunk D1 al primo giro (fase 02b)
        stato[0x1] = tetto & 0xFF
        stato[0x2] = 0x5A                    # guardia
        # +0x3 riservato, +0x4 salvato(s16)=0, +0x6 clamp(u16)=0,
        # +0x8 giri(u32)=0, +0xC riservato2(u32)=0: tutti zero all'iniezione.
        blocco[OFF_STATO:OFF_STATO + N_STATO] = stato
        r.scrivi(BLOCK_BASE, bytes(blocco))
        canarino = b"".join(struct.pack("<I", CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
        r.scrivi(CANARY_BASE, bytes(canarino))

        # A2: portata — nessun byte cambiato fuori dal blocco+canarino dichiarati
        leciti = set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N)) | \
                 set(range(r.off(CANARY_BASE), r.off(CANARY_BASE) + N_CANARY))
        diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
        fuori = [i for i in diversi if i not in leciti]
        if fuori:
            no("A2", "%d byte scritti fuori dalle regioni dichiarate, il primo a offset 0x%X"
               % (len(fuori), fuori[0]))
        if len(r.raw) != len(prima):
            no("A2", "la dimensione dell'immagine arm9/riserva e' cambiata")
        ok("A2", "arm9: %d byte scritti (blocco 256 + canarino 16), dimensione invariata" % len(diversi))

        r.salva(arm9_tmp)
        dati_dopo_arm9 = Path(arm9_tmp).read_bytes()

    log["blocco"] = {"base": hex(BLOCK_BASE), "bytes": BLOCK_N, "blob_sha256": sha(blob),
                     "stato_sha256": sha(stato), "attivo": attivo, "tetto": tetto,
                     "canarino_base": hex(CANARY_BASE), "canarino_motivo": hex(CANARY_MOTIVO)}

    # ---------------- patch dell'overlay 1 (in luogo, ricompressione ottima) -
    gancio = int(man["simboli"]["sgp_npc_hook"], 16)
    bl = bl_thumb(A_GANCIO, gancio)
    patch = [{"addr": A_GANCIO, "pre": PRE_GANCIO, "post": bl}]
    guardie = [(A_CONTESTO, PRE_CONTESTO_PIU_GANCIO)]
    try:
        dati_out, ric = ovp.applica(dati_dopo_arm9, OV_CAMPO, guardie, patch, strategia="auto")
    except ovp.Rifiuto as e:
        no("A3/overlay", str(e))
    if ric["overlay"]["id"] != OV_CAMPO:
        no("A3", "overlay scelto (%d) diverso da quello atteso (%d)" % (ric["overlay"]["id"], OV_CAMPO))
    ok("A3", "overlay 1 patchato in luogo: %s" % ric["strategia"]["usata"])
    log["overlay_patch"] = ric
    log["ganci"] = {"gancio": hex(A_GANCIO), "bersaglio": hex(gancio), "bl": bl.hex()}

    uscita = Path(uscita)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_bytes(dati_out)
    log["uscita"] = str(uscita)
    log["uscita_sha256"] = sha(dati_out)
    log["uscita_bytes"] = len(dati_out)
    log["esito"] = "applicato"
    if json_path:
        Path(json_path).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: log[k] for k in ("esito", "uscita", "uscita_sha256")}, indent=2))
    return log


def aggiorna_registro_condiviso(rom_path, log):
    rom_path = Path(rom_path).resolve()
    if rom_path.parent != ROM_DIR:
        return False
    sums_path = ROM_DIR / "SHA256SUMS"
    righe = sums_path.read_text().splitlines() if sums_path.exists() else []
    nome = rom_path.name
    nuove = [r for r in righe if not r.endswith("  " + nome)]
    nuove.append("%s  %s" % (log["uscita_sha256"], nome))
    sums_path.write_text("\n".join(nuove) + "\n")

    leggimi = ROM_DIR / "LEGGIMI.md"
    if leggimi.exists():
        testo = leggimi.read_text()
        riga_vecchia = "| tetto NPC per fotogramma (blocco `sgp.npc` a 0x023D8900) | P2 | `SGP-1.2-PRESTAZIONI-NPC-02` | in applicazione |"
        riga_nuova = "| tetto NPC per fotogramma (blocco `sgp.npc` a 0x023D8900) | P2 | `SGP-1.2-PRESTAZIONI-NPC-02` | applicato, cancelli A0-A4 verdi |"
        if riga_vecchia in testo:
            testo = testo.replace(riga_vecchia, riga_nuova)
        elif "SGP-1.2-PRESTAZIONI-NPC-02" not in testo:
            testo = testo.rstrip("\n") + "\n" + riga_nuova + "\n"
        leggimi.write_text(testo)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="ROM di ingresso (o la ROM di lavoro con --in-luogo)")
    ap.add_argument("--out", help="ROM di uscita (obbligatorio se non --in-luogo)")
    ap.add_argument("--in-luogo", metavar="ROM",
                    help="applica sulla ROM di lavoro condivisa IN LUOGO: copia in scratchpad, applica, "
                         "rilegge con rileggi_npc.py, sostituisce l'originale SOLO se verde")
    ap.add_argument("--build", required=True, help="cartella con blob.bin/manifesto.json (tools/compila.py)")
    ap.add_argument("--manifest", help="MAPPA-RISERVA-ARM9.json, per il cancello A4")
    ap.add_argument("--attivo", type=int, default=1, choices=(0, 1),
                    help="SEME pre-gancio (fase 02b: il gancio lo sovrascrive dal chunk D1 al "
                         "primo giro, vedi docstring); default 1")
    ap.add_argument("--tetto", type=int, default=1)
    ap.add_argument("--tmp", help="cartella scratchpad per --in-luogo")
    ap.add_argument("--json")
    ap.add_argument("--niente-registro", action="store_true")
    a = ap.parse_args()

    try:
        if a.in_luogo:
            rom = Path(a.in_luogo)
            if a.tmp:
                Path(a.tmp).mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=a.tmp) as td:
                tmp_in = Path(td) / ("in-" + rom.name)
                tmp_out = Path(td) / ("out-" + rom.name)
                shutil.copyfile(rom, tmp_in)
                log = applica(tmp_in, tmp_out, a.build, a.manifest, a.attivo, a.tetto, None)
                rilettore = QUI / "rileggi_npc.py"
                r = subprocess.run([sys.executable, str(rilettore), str(tmp_in), str(tmp_out),
                                    "--build", a.build] + (["--manifest", a.manifest] if a.manifest else []),
                                   capture_output=True, text=True)
                log["rilettura_in_luogo"] = {"returncode": r.returncode, "stdout": r.stdout[-4000:], "stderr": r.stderr[-2000:]}
                if r.returncode != 0:
                    print(r.stdout)
                    print(r.stderr, file=sys.stderr)
                    print("RIFIUTATO — la rilettura indipendente non e' verde: NON sostituisco %s" % rom)
                    if a.json:
                        Path(a.json).write_text(json.dumps(log, indent=2) + "\n")
                    return 2
                shutil.copyfile(tmp_out, rom)
                log["uscita"] = str(rom)
            if a.json:
                Path(a.json).write_text(json.dumps(log, indent=2) + "\n")
            if not a.niente_registro:
                aggiorna_registro_condiviso(rom, log)
            print("APPLICATO IN LUOGO %s (verificato prima di sostituire)" % rom)
            return 0
        else:
            if not (a.base and a.out):
                print("uso: --base e --out (oppure --in-luogo ROM)", file=sys.stderr)
                return 2
            log = applica(a.base, a.out, a.build, a.manifest, a.attivo, a.tetto, a.json)
            if not a.niente_registro:
                aggiorna_registro_condiviso(a.out, log)
            return 0
    except Rifiuto as e:
        print("RIFIUTATO — %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
