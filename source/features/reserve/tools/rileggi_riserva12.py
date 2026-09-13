#!/usr/bin/env python3
"""SGP-1.2-RISERVA-01 — RILETTORE INDIPENDENTE.

Non importa applica_riserva12.py, non riceve valori attesi da lui: apre la ROM
prodotta (e la ROM base per confronto) e ne rilegge il layout da zero, byte per byte,
con le proprie costanti. Se applicatore e rilettore condividessero una costante
sbagliata la prova sarebbe nulla — sono due file per questo (02-COME-LAVORARE.md §2.3).

Verifica:
  - il letterale d'arena 0x020D2BB0 vale 0x023D8000 nella candidata;
  - il letterale mainex_lo 0x020D2C64 vale ancora 0x023E0000 (non toccato);
  - l'ultima sezione di autoload e' 0x023D8000, len 32768, bss 0;
  - i primi 32 B sono il canarino basso 0xCA5A1000..0xCA5A1007;
  - i 32 B successivi sono l'intestazione SGP2, e i suoi ultimi 16 B sono DAVVERO i primi
    16 B di sha256({schema,riserva,zone} del manifest indicato, JSON canonico) — non solo
    "un valore qualunque" (REVISIONE 02, corregge D1 di REVISIONE-OPUS.md: prima questo
    script non controllava affatto quei 16 B, e un mutante che li azzerava usciva VERDE);
  - i 27392 B centrali sono tutti zero;
  - gli ultimi 5312 B (zona 1.1) sono IDENTICI, byte per byte, alla riserva letta
    dalla ROM BASE fornita (non da una costante): sha256 confrontata direttamente;
  - nessuna overlay ARM9 interseca [0x023D8000, 0x023E0000);
  - diff dell'intera ROM rispetto alla base: elenca ogni offset diverso e i due valori,
    e verifica che TUTTI cadano dentro l'ARM9 (nessuna scrittura fuori posto).

Uso:
    python3 rileggi_riserva12.py <base.nds> <candidata.nds> --manifest MAPPA-RISERVA-ARM9.json
                                  [--json out.json]

--manifest e' OBBLIGATORIO da REVISIONE 02 (C1 di REVISIONE-OPUS.md): senza di lui non si puo'
verificare "intestazione_manifest", ed e' esattamente il controllo che mancava.

Uscita 0 se tutti i controlli passano, 1 altrimenti (con il primo motivo stampato).
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

BASE_1_1 = 0x023DEB40
FINE = 0x023E0000
RISERVA_1_1_BYTES = 5312
CANARINO_BASSO_ATTESO = b"".join(struct.pack("<I", 0xCA5A1000 | i) for i in range(8))
BASE_1_2 = 0x023D8000
LIBERO_1_2_BYTES = 27392
ARENA_HI_LIT = 0x020D2BB0
MAINEX_LO_LIT = 0x020D2C64


def leggi_arm9(percorso):
    with open(percorso, "rb") as fh:
        head = fh.read(0x200)
        rom_off, _e, ram, size = struct.unpack_from("<IIII", head, 0x20)
        fh.seek(rom_off)
        blob = fh.read(size)
        y9_off, y9_size = struct.unpack_from("<II", head, 0x50)
        fh.seek(y9_off)
        y9 = fh.read(y9_size)
    return blob, ram, y9


def sezioni(blob, ram):
    import ndspy.code
    return ndspy.code.MainCodeFile(blob, ram).sections


def parola(sezioni_list, addr):
    for s in sezioni_list:
        if s.ramAddress <= addr < s.ramAddress + len(s.data):
            o = addr - s.ramAddress
            return struct.unpack_from("<I", s.data, o)[0]
    return None


def parte_stabile_mappa_sha16(manifest_path):
    """Scritta INDIPENDENTEMENTE da applica_riserva12.py (stesso principio del resto di
    questo file: se applicatore e rilettore condividessero un'implementazione sbagliata la
    prova sarebbe nulla). Concorda sul FORMATO documentato in MAPPA-RISERVA-ARM9.json
    (blocco 'intestazione'.formato.0x10): sha256 di {schema, riserva, zone} come JSON
    canonico (sort_keys, separatori compatti), primi 16 byte."""
    import json as _json
    m = _json.loads(Path(manifest_path).read_text())
    parte = {"schema": m["schema"], "riserva": m["riserva"], "zone": m["zone"]}
    blob = _json.dumps(parte, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).digest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("candidata")
    ap.add_argument("--manifest", required=True,
                    help="MAPPA-RISERVA-ARM9.json: obbligatorio da REVISIONE 02 (C1)")
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()

    esiti = []
    ok = True

    def check(nome, cond, dettaglio):
        nonlocal ok
        esiti.append({"nome": nome, "esito": "OK" if cond else "ROSSO", "dettaglio": dettaglio})
        if not cond:
            ok = False

    blob_b, ram_b, _y9_b = leggi_arm9(a.base)
    blob_c, ram_c, y9_c = leggi_arm9(a.candidata)
    sec_b = sezioni(blob_b, ram_b)
    sec_c = sezioni(blob_c, ram_c)

    ris_b = [s for s in sec_b if s.ramAddress == BASE_1_1]
    check("base_ha_riserva_1_1", len(ris_b) == 1,
          "sezioni della base a 0x%08X: %d (attesa 1)" % (BASE_1_1, len(ris_b)))
    riserva_base = bytes(ris_b[0].data) if ris_b else b""
    sha_base = hashlib.sha256(riserva_base).hexdigest()

    lit_hi = parola(sec_c, ARENA_HI_LIT)
    check("letterale_arena_hi", lit_hi == BASE_1_2,
          "0x%08X vale %s, atteso 0x%08X" % (ARENA_HI_LIT, lit_hi and hex(lit_hi), BASE_1_2))

    lit_mainex = parola(sec_c, MAINEX_LO_LIT)
    check("letterale_mainex_lo_invariato", lit_mainex == FINE,
          "0x%08X vale %s, atteso 0x%08X (estremo alto immobile)" % (MAINEX_LO_LIT, lit_mainex and hex(lit_mainex), FINE))

    ris_c = [s for s in sec_c if s.ramAddress == BASE_1_2]
    check("sezione_riserva_candidata", len(ris_c) == 1,
          "sezioni della candidata a 0x%08X: %d (attesa 1)" % (BASE_1_2, len(ris_c)))
    if ris_c:
        s = ris_c[0]
        check("dimensione_riserva", len(s.data) == FINE - BASE_1_2 and s.bssSize == 0,
              "len=%d bss=%d, attesi len=%d bss=0" % (len(s.data), s.bssSize, FINE - BASE_1_2))
        b = bytes(s.data)
        check("canarino_basso", b[:32] == CANARINO_BASSO_ATTESO,
              "primi 32 B = %s, attesi %s" % (b[:32].hex(), CANARINO_BASSO_ATTESO.hex()))
        hdr = b[32:64]
        check("intestazione_magic", hdr[:4] == b"SGP2", "magic = %r" % hdr[:4])
        schema, base_hdr, fine_hdr = struct.unpack_from("<III", hdr, 4)
        check("intestazione_campi", schema == 1 and base_hdr == BASE_1_2 and fine_hdr == FINE,
              "schema=%d base=0x%08X fine=0x%08X" % (schema, base_hdr, fine_hdr))
        atteso_manifest = parte_stabile_mappa_sha16(a.manifest)
        letto_manifest = hdr[16:32]
        check("intestazione_manifest", bytes(letto_manifest) == atteso_manifest,
              "16 B nell'intestazione = %s, attesi (da --manifest %s) = %s"
              % (bytes(letto_manifest).hex(), a.manifest, atteso_manifest.hex()))
        libero = b[64:64 + LIBERO_1_2_BYTES]
        check("libero_1_2_a_zero", set(libero) <= {0},
              "%d byte non nulli su %d nella zona libera 1.2" % (sum(1 for x in libero if x), len(libero)))
        coda = b[64 + LIBERO_1_2_BYTES:]
        check("zona_1_1_lunghezza", len(coda) == RISERVA_1_1_BYTES,
              "coda = %d B, attesi %d" % (len(coda), RISERVA_1_1_BYTES))
        sha_coda = hashlib.sha256(coda).hexdigest()
        check("zona_1_1_identica_alla_base", sha_coda == sha_base,
              "sha256 candidata=%s base=%s" % (sha_coda, sha_base))
        check("canarino_1_1_intatto", coda[:32] == b"".join(struct.pack("<I", 0xCA5A0000 | i) for i in range(8)),
              "canarino 1.1 nella coda non e' CA5A0000..CA5A0007")

    n_y9 = len(y9_c) // 32
    coll = []
    for i in range(n_y9):
        oid, ram, size, bss = struct.unpack_from("<4I", y9_c, i * 32)
        fine_o = ram + size + bss
        if ram < FINE and fine_o > BASE_1_2:
            coll.append((oid, hex(ram), hex(fine_o)))
    check("nessuna_overlay_in_riserva", not coll, "overlay in collisione: %s" % coll)

    check("numero_sezioni_autoload", len(sec_c) == 4, "%d sezioni, attese 4" % len(sec_c))

    # diff completo ROM base vs candidata: ogni offset diverso deve stare nell'ARM9
    with open(a.base, "rb") as f:
        base_bytes = f.read()
    with open(a.candidata, "rb") as f:
        cand_bytes = f.read()
    check("dimensione_file_invariata", len(base_bytes) == len(cand_bytes),
          "base=%d candidata=%d" % (len(base_bytes), len(cand_bytes)))
    a9_off, _e, _ram, a9_size_base = struct.unpack_from("<IIII", base_bytes[:0x200], 0x20)
    diff_offsets = []
    if len(base_bytes) == len(cand_bytes):
        BLOC = 4096
        for start in range(0, len(base_bytes), BLOC):
            end = min(start + BLOC, len(base_bytes))
            if base_bytes[start:end] != cand_bytes[start:end]:
                for i in range(start, end):
                    if base_bytes[i] != cand_bytes[i]:
                        diff_offsets.append(i)
    fuori_arm9 = [o for o in diff_offsets if not (0x2C <= o < 0x2C + 4 or o in (0x6C, 0x6D, 0x15E, 0x15F)
                                                   or a9_off <= o < a9_off + 0x200000)]
    check("diff_solo_dentro_arm9_o_header_atteso", not fuori_arm9,
          "%d byte diversi FUORI dall'ARM9/header atteso, primi: %s"
          % (len(fuori_arm9), [hex(o) for o in fuori_arm9[:10]]))

    r = {"base": str(a.base), "candidata": str(a.candidata),
         "riserva_1_1_sha256_base": sha_base, "byte_diversi_totali": len(diff_offsets),
         "primi_20_offset_diversi": [
             {"offset": hex(o), "base": hex(base_bytes[o]), "candidata": hex(cand_bytes[o])}
             for o in diff_offsets[:20]],
         "esiti": esiti, "verdetto": "VERDE" if ok else "ROSSO"}
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(r, indent=1, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
