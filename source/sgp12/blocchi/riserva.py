#!/usr/bin/env python3
"""Blocco RISERVA — abbassa la base della riserva ARM9 da 0x023DEB40 a
0x023D8000 (32768 B), lasciando la zona 1.1 (5312 B in coda) byte per byte
identica. Porta a `sgp12` di `SGP-1.2-RISERVA-01/tools/applica_riserva12.py` +
`rileggi_riserva12.py` (letteralmente: stesse costanti, stessi cancelli).

`applica()` e `rileggi()` restano DUE implementazioni indipendenti
dell'impronta del manifest e del canarino basso, di proposito (vedi
`sgp12/riserva.py` in testa): `rileggi()` NON chiama le funzioni interne di
`applica()`.

`build`: una cartella con `MAPPA-RISERVA-ARM9.json` (il registro dei blocchi
della riserva; il registro pubblico e' `docs/arm9-reserve-map.json`).
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from ..rom import Rifiuto, esigi, sha
from ..riserva import canarino

ARENA_HI_LIT = 0x020D2BB0
MAINEX_LO_LIT = 0x020D2C64
ARENA_FINE = 0x023E0000

BASE_1_1 = 0x023DEB40
RISERVA_1_1_BYTES = 0x14C0
RISERVA_1_1_SHA256 = "43cdd97ebb48ad43590274ae90d06352bbc5f5a85c8cb65c651d7f8b35e3e2d2"

BASE_1_2 = 0x023D8000
RISERVA_TOTALE_BYTES = ARENA_FINE - BASE_1_2
CANARINO_BASSO_BYTES = 32
INTESTAZIONE_BYTES = 32
LIBERO_1_2_BYTES = RISERVA_TOTALE_BYTES - CANARINO_BASSO_BYTES - INTESTAZIONE_BYTES - RISERVA_1_1_BYTES
assert LIBERO_1_2_BYTES == 27392

NOME_MANIFEST = "MAPPA-RISERVA-ARM9.json"


def _manifest_path(build) -> Path:
    p = Path(build) / NOME_MANIFEST
    esigi(p.exists(), "manifest non trovato in %s" % p)
    return p


def _parte_stabile_mappa__scrittore(manifest_path) -> bytes:
    """Copia SCRITTA PER `applica()`: sha256({schema,riserva,zone}) canonico,
    primi 16 B. Non condivisa con `_lettore` sotto (vedi nota di modulo)."""
    m = json.loads(Path(manifest_path).read_text())
    parte = {"schema": m["schema"], "riserva": m["riserva"], "zone": m["zone"]}
    blob = json.dumps(parte, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).digest()[:16]


def _parte_stabile_mappa__lettore(manifest_path) -> bytes:
    """Copia SCRITTA INDIPENDENTEMENTE per `rileggi()`: stessa idea, digitata
    separatamente (stesso principio di `rileggi_riserva12.py`)."""
    import json as _json
    m = _json.loads(Path(manifest_path).read_text())
    parte = {"schema": m["schema"], "riserva": m["riserva"], "zone": m["zone"]}
    blob = _json.dumps(parte, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).digest()[:16]


def applica(rom: bytes, build, etichetta: str = "") -> tuple[bytes, dict]:
    import ndspy.code
    import ndspy.rom
    from ndspy import _common

    manifest_path = _manifest_path(build)
    parsed = ndspy.rom.NintendoDSRom(bytes(rom))
    main = parsed.loadArm9()

    r = {"strumento": "sgp12/blocchi/riserva.py:applica", "rom": etichetta,
         "ingresso_sha256": sha(rom), "ingresso_bytes": len(rom), "cancelli": {}}

    ris = main.sections[-1]

    # G0 idempotenza, prima di ogni scrittura
    segni = []
    lit_hi = struct.unpack_from("<I", main.sections[0].data, ARENA_HI_LIT - main.sections[0].ramAddress)[0]
    if lit_hi == BASE_1_2:
        segni.append("il letterale d'arena a 0x%08X vale gia' 0x%08X" % (ARENA_HI_LIT, BASE_1_2))
    if ris.ramAddress == BASE_1_2 or len(ris.data) == RISERVA_TOTALE_BYTES:
        segni.append("l'ultima sezione e' gia' 0x%08X/%d B" % (ris.ramAddress, len(ris.data)))
    esigi(not segni, "G0 IDEMPOTENZA: la ROM in ingresso e' GIA' (in parte) nello stato "
                     "d'uscita. Segni: " + "; ".join(segni))
    r["cancelli"]["G0_idempotenza"] = True

    # G1 preimmagine attesa (base 1.1)
    esigi(len(main.sections) == 4, "G1: sezioni di autoload %d, attese 4" % len(main.sections))
    esigi(lit_hi == BASE_1_1, "G1: il letterale d'arena vale 0x%08X, atteso 0x%08X" % (lit_hi, BASE_1_1))
    lit_mainex = struct.unpack_from("<I", main.sections[0].data,
                                    MAINEX_LO_LIT - main.sections[0].ramAddress)[0]
    esigi(lit_mainex == ARENA_FINE, "G1: mainex_lo vale 0x%08X, atteso 0x%08X" % (lit_mainex, ARENA_FINE))
    esigi(ris.ramAddress == BASE_1_1 and len(ris.data) == RISERVA_1_1_BYTES and ris.bssSize == 0,
          "G1: l'ultima sezione e' 0x%08X/%d/%d, attesa 0x%08X/%d/0"
          % (ris.ramAddress, len(ris.data), ris.bssSize, BASE_1_1, RISERVA_1_1_BYTES))
    riserva_1_1 = bytes(ris.data)
    esigi(sha(riserva_1_1) == RISERVA_1_1_SHA256,
          "G1: la riserva 1.1 ha sha256 %s, atteso %s" % (sha(riserva_1_1), RISERVA_1_1_SHA256))
    r["cancelli"]["G1_preimmagine"] = {"riserva_1_1_sha256": sha(riserva_1_1)}

    # G2 nessuna overlay nella futura riserva
    t = parsed.arm9OverlayTable
    n = len(t) // 32
    overlay = [struct.unpack_from("<8I", t, i * 32) for i in range(n)]
    coll = [(o[0], o[1], o[1] + o[2] + o[3]) for o in overlay
            if o[1] < ARENA_FINE and o[1] + o[2] + o[3] > BASE_1_2]
    esigi(not coll, "G2: %d overlay intersecano [0x%08X,0x%08X): %s" % (len(coll), BASE_1_2, ARENA_FINE, coll))
    r["cancelli"]["G2_nessuna_overlay"] = {"overlay_totali": n}

    can = canarino(0xCA5A1000, 8)
    hdr = bytearray(32)
    hdr[0:4] = b"SGP2"
    struct.pack_into("<I", hdr, 4, 1)
    struct.pack_into("<I", hdr, 8, BASE_1_2)
    struct.pack_into("<I", hdr, 12, ARENA_FINE)
    hdr[16:32] = _parte_stabile_mappa__scrittore(manifest_path)
    libero = bytes(LIBERO_1_2_BYTES)
    nuova_riserva = can + bytes(hdr) + libero + riserva_1_1
    esigi(len(nuova_riserva) == RISERVA_TOTALE_BYTES,
          "la riserva nuova misura %d B, attesi %d" % (len(nuova_riserva), RISERVA_TOTALE_BYTES))
    esigi(nuova_riserva[-RISERVA_1_1_BYTES:] == riserva_1_1, "la coda 1.1 e' stata alterata in memoria")
    r["nuova_riserva"] = {"bytes": len(nuova_riserva), "sha256": sha(nuova_riserva)}

    struct.pack_into("<I", main.sections[0].data, ARENA_HI_LIT - main.sections[0].ramAddress, BASE_1_2)
    main.sections[-1] = ndspy.code.MainCodeFile.Section(nuova_riserva, BASE_1_2, 0)

    arm9_in = bytes(parsed.arm9)
    nuovo = main.save(compress=False)
    sorgente = bytes(rom)
    inizio9 = struct.unpack_from("<I", sorgente, 0x20)[0]
    esigi(inizio9 == 0x4000, "area sicura in posizione inattesa")
    confini = [struct.unpack_from("<I", sorgente, o)[0] for o in (0x30, 0x40, 0x48, 0x50, 0x58, 0x68)]
    fat_off, fat_size = struct.unpack_from("<II", sorgente, 0x48)
    confini += [struct.unpack_from("<II", sorgente, fat_off + i * 8)[0] for i in range(fat_size // 8)]
    est = min(c for c in confini if c > inizio9) - inizio9
    dati9 = nuovo + bytes(parsed.arm9PostData)
    esigi(len(dati9) <= est,
          "G3: ARM9+footer %d B non entra nei %d B liberi prima del prossimo blocco" % (len(dati9), est))
    va, na = arm9_in[:0x800], nuovo[:0x800]
    esigi(va == na, "G4: il prefisso cifrato dell'area sicura e' cambiato")

    risultato = bytearray(sorgente)
    risultato[inizio9:inizio9 + len(dati9)] = dati9
    struct.pack_into("<I", risultato, 0x2C, len(nuovo))
    crc = parsed.secureAreaChecksum ^ _common.crc16(va) ^ _common.crc16(na)
    struct.pack_into("<H", risultato, 0x6C, crc)
    struct.pack_into("<H", risultato, 0x15E, _common.crc16(bytes(risultato[:0x15E])))

    esigi(len(risultato) == len(sorgente), "G5: la dimensione del file e' cambiata")
    r["cancelli"]["G3_spazio_arm9"] = {"disponibile": est, "usato": len(dati9)}
    r["cancelli"]["G4_area_sicura_invariata"] = True
    r["cancelli"]["G5_dimensione_file_invariata"] = len(risultato)
    r["uscita_sha256"] = sha(risultato)
    r["uscita_bytes"] = len(risultato)
    return bytes(risultato), r


def rileggi(base: bytes, candidata: bytes, build) -> dict:
    """Rilettore INDIPENDENTE: non chiama `applica()`, rilegge da zero con le
    proprie costanti (stesse di `rileggi_riserva12.py`)."""
    import ndspy.code

    manifest_path = _manifest_path(build)

    def sezioni(dati):
        rom_off, _e, ram, size = struct.unpack_from("<IIII", dati, 0x20)
        return ndspy.code.MainCodeFile(dati[rom_off:rom_off + size], ram).sections

    def parola(sez, addr):
        for s in sez:
            if s.ramAddress <= addr < s.ramAddress + len(s.data):
                return struct.unpack_from("<I", s.data, addr - s.ramAddress)[0]
        return None

    esiti, ok = [], True

    def check(nome, cond, dettaglio):
        nonlocal ok
        esiti.append({"nome": nome, "esito": "OK" if cond else "ROSSO", "dettaglio": dettaglio})
        if not cond:
            ok = False

    sec_b, sec_c = sezioni(base), sezioni(candidata)
    ris_b = [s for s in sec_b if s.ramAddress == BASE_1_1]
    check("base_ha_riserva_1_1", len(ris_b) == 1, "sezioni base a 0x%08X: %d" % (BASE_1_1, len(ris_b)))
    riserva_base = bytes(ris_b[0].data) if ris_b else b""
    sha_base = hashlib.sha256(riserva_base).hexdigest()

    lit_hi = parola(sec_c, ARENA_HI_LIT)
    check("letterale_arena_hi", lit_hi == BASE_1_2, "vale %s" % (lit_hi and hex(lit_hi)))
    lit_mainex = parola(sec_c, MAINEX_LO_LIT)
    check("letterale_mainex_lo_invariato", lit_mainex == ARENA_FINE, "vale %s" % (lit_mainex and hex(lit_mainex)))

    ris_c = [s for s in sec_c if s.ramAddress == BASE_1_2]
    check("sezione_riserva_candidata", len(ris_c) == 1, "sezioni a 0x%08X: %d" % (BASE_1_2, len(ris_c)))
    if ris_c:
        s = ris_c[0]
        check("dimensione_riserva", len(s.data) == RISERVA_TOTALE_BYTES and s.bssSize == 0,
              "len=%d bss=%d" % (len(s.data), s.bssSize))
        b = bytes(s.data)
        atteso_can = canarino(0xCA5A1000, 8)
        check("canarino_basso", b[:32] == atteso_can, "primi 32 B")
        hdr = b[32:64]
        check("intestazione_magic", hdr[:4] == b"SGP2", "magic=%r" % hdr[:4])
        schema, base_hdr, fine_hdr = struct.unpack_from("<III", hdr, 4)
        check("intestazione_campi", schema == 1 and base_hdr == BASE_1_2 and fine_hdr == ARENA_FINE,
              "schema=%d base=0x%08X fine=0x%08X" % (schema, base_hdr, fine_hdr))
        atteso_manifest = _parte_stabile_mappa__lettore(manifest_path)
        check("intestazione_manifest", bytes(hdr[16:32]) == atteso_manifest, "impronta manifest")
        libero = b[64:64 + LIBERO_1_2_BYTES]
        check("libero_1_2_a_zero", set(libero) <= {0}, "%d non-zero" % sum(1 for x in libero if x))
        coda = b[64 + LIBERO_1_2_BYTES:]
        check("zona_1_1_lunghezza", len(coda) == RISERVA_1_1_BYTES, "len=%d" % len(coda))
        sha_coda = hashlib.sha256(coda).hexdigest()
        check("zona_1_1_identica_alla_base", sha_coda == sha_base, "sha256 %s vs %s" % (sha_coda, sha_base))
        check("canarino_1_1_intatto", coda[:32] == canarino(0xCA5A0000, 8), "canarino 1.1 in coda")

    check("numero_sezioni_autoload", len(sec_c) == 4, "%d sezioni" % len(sec_c))
    check("dimensione_file_invariata", len(base) == len(candidata),
          "base=%d candidata=%d" % (len(base), len(candidata)))

    return {"verdetto": "VERDE" if ok else "ROSSO", "esiti": esiti,
           "riserva_1_1_sha256_base": sha_base}
