#!/usr/bin/env python3
"""APPLICATORE — SGP-1.2-GUIDA-EVIV-02: spegne l'etichetta automatica "START
Guida"/"START Guide" nella pagina ABILITA'/Dati del Riepilogo, mantenendo
START (e il tocco, che non dipende dal disegno: vedi RAPPORTO.md) capace di
aprire i tre pannelli EV/IV. Nessun automatismo di Nuova Partita toccato.

STORIA (importante, vedi RAPPORTO.md §2): il primo tentativo di questo
cantiere ricompilava `combined_guide.c` con `build_combined_guide.py` e
sostituiva l'intera regione codice (4752 B). La prova su `hg_runtime` ha
trovato una REGRESSIONE GRAVE: premendo START, il gioco si bloccava
(eccezione ARM9, `arm9_pc=0xFFFF0108`). Isolata la causa: NON era il taglio
di `badge_create`, era la ricompilazione in se' — persino ricompilando il
sorgente SENZA alcun taglio, con il clang disponibile in questo ambiente
(quasi certamente diverso da quello usato l'11/09/2026 per la ROM spedita),
si ottiene codice che crasha allo stesso modo (stesso `arm9_pc`, stesso
fotogramma). Il compilatore locale non e' quindi utilizzabile per
ricompilare questo file: qualunque ricompilazione, con o senza taglio, e'
oggi PERICOLOSA per questa funzione.

QUESTO APPLICATORE NON RICOMPILA NULLA. Patch chirurgica di 96 byte,
direttamente sui byte macchina della ROM spedita (nessun blob ricompilato,
nessun trampolino spostato, nessun bersaglio Oak cambiato: guide_main resta
esattamente dov'era). `badge_create` e' fusa (inline) dentro `guide_main`
dal compilatore originale; disassemblata (capstone) sulla ROM reale
(`base-1.1-EN.nds`/`base-1.1-IT.nds`, byte identici in questa zona), la
sequenza "Context *c=acquire(s,1); if(!c){P->failures++;return;} P->badge=1;
visibility(...); font_save(c);draw_window(...);border(...);font_restore(c);
...;copy16(...);schedule(s);" occupa ESATTAMENTE 96 byte contigui
(0x01FF8A1A-0x01FF8A7A), racchiusi fra due istruzioni facilmente
riconoscibili (`P->visibility=DISPLAY&VISIBILITY;` appena prima,
`ldr r5,[sp,#0x18]` — la prosecuzione del calcolo di `eligible` — appena
dopo). Nessun'altra istruzione della funzione salta dentro questa regione
(verificato: unico ingresso e' la caduta naturale dall'istruzione
precedente). La regione viene sostituita con:

    movs r0, #1
    str  r0, [r7, #0x2c]   ; P->badge = 1   (r7 = P per tutta guide_main)
    str  r0, [r7, #0x30]   ; P->pending = 1
    b    0x01FF8B18         ; salta al ritorno condiviso di guide_main
    <44x "mov r8,r8" (0x46C0), riempimento NOP fino a 96 B>

Il salto (`b`) evita per intero acquire()/font_save()/draw_window()/
border()/font_restore()/copy16()/schedule(): il codice morto che resta
sotto (0x01FF8ADE-0x01FF8B18, mai piu' raggiunto: nessun altro salto vi
entra, verificato) non viene nemmeno toccato — resta byte per byte quello
spedito, e' semplicemente irraggiungibile. `P->summary=s;
P->visibility=DISPLAY&VISIBILITY;` (appena prima della regione) e le
guardie di eleggibilita' (resources/settled/DISPLAY, il ciclo sui 20 tile)
restano ESATTAMENTE quelle spedite, mai toccate.

Verificato su `hg_runtime-gdb`: l'etichetta non compare piu', START apre i
tre pannelli EV/IV regolarmente (nessun crash, nessun glitch), la pagina
torna pulita uscendo — su entrambe le lingue (il testo dei tre pannelli
resta quello spedito, mai riscritto).

Uso:
  applica_guida.py --rom X.nds --uscita Y.nds [--json F]
  applica_guida.py --rom X.nds --in-luogo [--tmp D] [--json F]
  applica_guida.py --rilegge X.nds     (stampa solo lo stato: originale|spenta|ignoto)

rc: 0 applicato (o gia'-applicato, 0 byte) - 2 RIFIUTATO.
GPL-3.0-or-later.
"""
import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
from arm9 import Arm9  # noqa: E402

# --- l'unica regione toccata: 96 B dentro guide_main, ITCM statica r5.
PATCH_ADDR = 0x01FF8A1A
PATCH_N = 96
TEXT = 0x01FF9B10  # solo per la firma di lingua nel log, mai scritta
TEXT_SIGNATURE_N = 1098

ORIGINALE_SHA = "9ffbcb8c920f67d2343e16cde7426b57f5a639ebddee956cfe2b240dc6bf9aa9"
SPENTA_SHA = "e9c85f702347a58698951876d43662f5f6690f5dbff0290465a435892e46bf08"


def _spenta_bytes():
    patch = struct.pack("<HHHH", 0x2001, 0x62F8, 0x6338, 0xE07A)
    patch += b"\xC0\x46" * ((PATCH_N - len(patch)) // 2)
    assert len(patch) == PATCH_N
    assert hashlib.sha256(patch).hexdigest() == SPENTA_SHA
    return patch


SPENTA_BYTES = _spenta_bytes()

LINGUA_FIRMA = {
    "EN": "5b2061b68b6b471c6043def4e222c893c4b977de4a5389518f8f9f2f77b18188",
    "IT": "c7b977a19f50135526e35fc89ea968f855c652395a923b77d708c2c1187f21cd",
}


class Rifiuto(Exception):
    pass


def no(cancello, msg):
    raise Rifiuto("%s: %s" % (cancello, msg))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def riconosci_lingua(a):
    try:
        campione = bytes(a.leggi(TEXT, TEXT_SIGNATURE_N))
    except KeyError:
        return None
    firma = sha(campione)
    for lingua, attesa in LINGUA_FIRMA.items():
        if firma == attesa:
            return lingua
    return None


def stato_da_bytes(regione):
    s = sha(regione)
    if s == ORIGINALE_SHA:
        return "originale"
    if s == SPENTA_SHA:
        return "spenta"
    return "ignoto"


def leggi_stato(rom_path):
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "arm9-lettura.nds"
        shutil.copyfile(rom_path, tmp)
        a = Arm9(tmp)
        lingua = riconosci_lingua(a)
        regione = bytes(a.leggi(PATCH_ADDR, PATCH_N))
    return {"lingua": lingua, "stato": stato_da_bytes(regione), "regione_sha256": sha(regione)}


def applica(ingresso, uscita, json_path):
    log = {"strumento": "SGP-1.2-GUIDA-EVIV-02/tools/applica_guida.py",
           "ingresso": str(ingresso), "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})
        print("  %-4s passato  %s" % (c, msg))

    dati_in = Path(ingresso).read_bytes()
    log["sha256_ingresso"] = sha(dati_in)
    log["ingresso_bytes"] = len(dati_in)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "arm9-lettura.nds"
        shutil.copyfile(ingresso, tmp)
        a0 = Arm9(tmp)
        lingua = riconosci_lingua(a0)
        regione_ora = bytes(a0.leggi(PATCH_ADDR, PATCH_N))

    log["lingua"] = lingua
    stato = stato_da_bytes(regione_ora)
    log["stato_ingresso"] = stato
    ok("A0", "lingua per il log: %s (la regione patchata non dipende dalla lingua)" % (lingua or "non riconosciuta"))

    if stato == "spenta":
        log["esito"] = "gia-applicato"
        log["byte_diversi"] = 0
        Path(uscita).parent.mkdir(parents=True, exist_ok=True)
        Path(uscita).write_bytes(dati_in)
        log["uscita"], log["uscita_sha256"], log["uscita_bytes"] = str(uscita), sha(dati_in), len(dati_in)
        print("GIA' APPLICATO (idempotenza): 0 byte scritti")
        if json_path:
            Path(json_path).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
        return log
    if stato != "originale":
        no("A1", "la regione (0x%08X, %d B) non e' ne' l'originale spedito ne' la versione "
                 "spenta attesa: non tocco niente (sha=%s)" % (PATCH_ADDR, PATCH_N, sha(regione_ora)))
    ok("A1", "preimmagine originale riconosciuta byte per byte (96 B a 0x%08X)" % PATCH_ADDR)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "arm9-scrittura.nds"
        shutil.copyfile(ingresso, tmp)
        r = Arm9(tmp)
        prima = bytes(r.raw)
        r.scrivi(PATCH_ADDR, SPENTA_BYTES)
        o = r.off(PATCH_ADDR, PATCH_N)
        leciti = set(range(o, o + PATCH_N))
        diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
        fuori = [i for i in diversi if i not in leciti]
        if fuori:
            no("A2", "%d byte scritti fuori dalla regione dichiarata, il primo a 0x%X"
               % (len(fuori), fuori[0]))
        ok("A2", "scrittura confinata alla sola regione dichiarata (96 B)")
        if not (0 < len(diversi) <= PATCH_N):
            no("A2b", "%d byte diversi, atteso un numero fra 1 e %d" % (len(diversi), PATCH_N))
        ok("A2b", "%d byte cambiati dentro la regione di %d B (qualche byte puo' coincidere per caso "
                 "fra preimmagine e postimmagine, non e' un errore)" % (len(diversi), PATCH_N))
        if len(r.raw) != len(prima):
            no("A3", "dimensione della ROM cambiata")
        ok("A3", "dimensione della ROM invariata")
        r.salva(tmp)
        dati_out = Path(tmp).read_bytes()

    with tempfile.TemporaryDirectory() as td:
        tmp2 = Path(td) / "arm9-verifica.nds"
        Path(tmp2).write_bytes(dati_out)
        a_out = Arm9(tmp2)
        regione_dopo = bytes(a_out.leggi(PATCH_ADDR, PATCH_N))
    stato_dopo = stato_da_bytes(regione_dopo)
    if stato_dopo != "spenta":
        no("A4", "dopo la scrittura la regione non e' riconosciuta come 'spenta' (stato=%s)" % stato_dopo)
    ok("A4", "dopo la scrittura la regione e' riconosciuta come 'spenta'")

    log["byte_diversi"] = len(diversi)
    log["regione"] = {"base": hex(PATCH_ADDR), "bytes": PATCH_N,
                      "pre_sha256": ORIGINALE_SHA, "post_sha256": SPENTA_SHA}
    log["esito"] = "applicato"
    Path(uscita).parent.mkdir(parents=True, exist_ok=True)
    Path(uscita).write_bytes(dati_out)
    log["uscita"], log["uscita_sha256"], log["uscita_bytes"] = str(uscita), sha(dati_out), len(dati_out)
    print(json.dumps({k: log[k] for k in ("esito", "lingua", "byte_diversi", "uscita", "uscita_sha256")},
                     indent=2))
    if json_path:
        Path(json_path).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    return log


def aggiorna_sha256sums(rom_path, sha256):
    rom_path = Path(rom_path).resolve()
    sums_path = rom_path.parent / "SHA256SUMS"
    righe = sums_path.read_text().splitlines() if sums_path.exists() else []
    nome = rom_path.name
    nuove = [r for r in righe if not r.endswith("  " + nome)]
    nuove.append("%s  %s" % (sha256, nome))
    nuove.sort(key=lambda r: r.split("  ")[-1])
    sums_path.write_text("\n".join(nuove) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom")
    ap.add_argument("--uscita")
    ap.add_argument("--in-luogo", action="store_true")
    ap.add_argument("--rilegge", metavar="ROM")
    ap.add_argument("--tmp")
    ap.add_argument("--json")
    a = ap.parse_args()

    try:
        if a.rilegge:
            print(json.dumps({"rom": a.rilegge, **leggi_stato(a.rilegge)}, indent=2))
            return 0
        if not a.rom:
            print("uso: --rom e' obbligatorio (tranne con --rilegge)", file=sys.stderr)
            return 2
        if a.in_luogo:
            rom = Path(a.rom)
            if a.tmp:
                Path(a.tmp).mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=a.tmp) as td:
                tmp_in = Path(td) / ("in-" + rom.name)
                tmp_out = Path(td) / ("out-" + rom.name)
                shutil.copyfile(rom, tmp_in)
                log = applica(tmp_in, tmp_out, None)
                if log["esito"] == "gia-applicato":
                    log["rilettura_in_luogo"] = {"saltata": "gia-applicato, 0 byte"}
                    if a.json:
                        Path(a.json).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
                    print("GIA' APPLICATO IN LUOGO (idempotenza): 0 byte, %s non toccata" % rom)
                    return 0
                rilettore = QUI / "rileggi_guida.py"
                r = subprocess.run([sys.executable, str(rilettore), str(tmp_in), str(tmp_out)],
                                   capture_output=True, text=True)
                log["rilettura_in_luogo"] = {"returncode": r.returncode,
                                             "stdout": r.stdout[-6000:], "stderr": r.stderr[-3000:]}
                if r.returncode != 0:
                    print(r.stdout)
                    print(r.stderr, file=sys.stderr)
                    print("RIFIUTATO - rilettura non verde: NON sostituisco %s" % rom)
                    if a.json:
                        Path(a.json).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
                    return 2
                shutil.copyfile(tmp_out, rom)
                log["uscita"] = str(rom)
            if a.json:
                Path(a.json).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
            aggiorna_sha256sums(rom, log["uscita_sha256"])
            print("APPLICATO IN LUOGO %s (verificato prima di sostituire)" % rom)
            return 0
        if not a.uscita:
            print("uso: --uscita e' obbligatorio (oppure --in-luogo)", file=sys.stderr)
            return 2
        applica(a.rom, a.uscita, a.json)
        return 0
    except Rifiuto as e:
        print("RIFIUTATO - %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
