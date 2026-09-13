#!/usr/bin/env python3
"""T1-T5 dell'audit 1.1/1.2, applicati al registro
docs/arm9-reserve-map.json (registro della riserva ARM9; STATO-1.2.md §b (ex 04-RISERVA-ARM9-F0.md §4.3), §6).

  T1  copertura senza buchi ne' sovrapposizioni: i blocchi di ciascuna zona coprono
      [base, fine) in ordine, senza intersezioni, e la somma fa esattamente fine-base.
      Non richiede una ROM: e' sempre attivo.
  T2  ogni blocco con un'impronta dichiarata (sha256, sha256_atteso_a_zero o
      impronte_parziali) combacia con quanto letto dalla ROM di release indicata da
      --rom (o dalla variabile d'ambiente SGP_RISERVA_ROM). Un blocco senza NESSUNA
      impronta dichiarata fa fallire il test (REVISIONE 02, C12: prima veniva saltato
      in silenzio - D5 della revisione privata). Un blocco con "puo_essere_ancora_zero"
      passa anche se e' ancora tutto zero (prenotato ma non ancora scritto).
  T3  ogni ancora e ogni consumatore pubblico cade nel blocco che lo dichiara: si legge
      il letterale che punta al codice camera, si verifica che l'ultima sezione di
      autoload abbia la base e la dimensione dichiarate dalla mappa (REVISIONE 02, C7:
      e' il cancello che fa fallire T3 per una ragione VERA sulla base 1.1, non con un
      LookupError - D2 della revisione privata), e si leggono gli indirizzi dai file di
      cheat pubblici spediti in cheats/ (codici 2xxxxxxx e 5xxxxxxx).
  T4  la riserva non tocca l'heap: ArenaLo + Sigma(heap) + FNT + FAT + margine(8 KiB)
      deve restare sotto la base della riserva (STATO-1.2.md §b (ex 04-RISERVA-ARM9-F0.md §4.3) e §6 passo 1
      cancello 9; REVISIONE 02, C22: il test non esisteva ancora - D1.3 di
      revisione privata).
  T5  l'intestazione SGP2 scritta in ROM (0x023D8020) e' coerente con la mappa: i suoi
      ultimi 16 B sono i primi 16 B di sha256({schema,riserva,zone}) in JSON canonico
      (REVISIONE 02: corregge D1 della revisione privata, dove l'intestazione portava lo
      sha dell'INTERO manifest - che cambia a ogni blocco registrato - e nessun cancello
      lo controllava affatto: un mutante che azzerava quei 16 B usciva VERDE).

Senza una ROM, T2/T3/T4/T5 SALTANO con motivo esplicito (02-COME-LAVORARE.md §7:
"non trovato" si dichiara, non si finge). Se SGP_RISERVA_COMPLETA=1 e' impostata (uso
raccomandato in CI) e SGP_RISERVA_ROM manca, la suite FALLISCE invece di saltare in
silenzio (REVISIONE 02, C18: D10 della revisione privata).

Uso:
    python3 -m unittest verifiche.test_riserva -v          # da source/
    SGP_RISERVA_ROM=<rom.nds> python3 -m unittest ... -v   # per T2/T3/T4/T5 completi
Interprete: richiede ndspy per T2/T3/T4/T5 (rom-review-venv); T1 e' puro Python.
"""
import hashlib
import json
import os
import re
import struct
import sys
import unittest
from pathlib import Path

QUI = Path(__file__).resolve().parent
REPO = QUI.parents[1]
MAPPA = Path(os.environ.get("SGP_MAPPA", REPO / "source/docs/arm9-reserve-map.json"))
# I file di cheat spediti stanno nel pacchetto ZIP della release (non nel repo):
# indicare la cartella scompattata con SGP_CHEATS, altrimenti T3 viene saltato.
CHEATS_DIR = Path(os.environ.get("SGP_CHEATS", REPO / "release/1.2"))


def carica_mappa():
    return json.loads(MAPPA.read_text())


def blocchi_per_zona(mappa, zona):
    return sorted((b for b in mappa["blocchi"] if b["zona"] == zona),
                  key=lambda b: int(b["base"], 16))


class TestT1Copertura(unittest.TestCase):
    """T1 — nessuna sovrapposizione, nessun buco, la somma torna."""

    def setUp(self):
        self.mappa = carica_mappa()

    def test_zone_coprono_la_riserva_senza_buchi(self):
        riserva = self.mappa["riserva"]
        base_tot = int(riserva["base"], 16)
        fine_tot = int(riserva["fine"], 16)
        zone = sorted(self.mappa["zone"], key=lambda z: int(z["base"], 16))
        cursore = base_tot
        for z in zone:
            zb, zf = int(z["base"], 16), int(z["fine"], 16)
            self.assertEqual(zb, cursore, "buco o sovrapposizione fra zone prima di %s" % z["nome"])
            self.assertEqual(zf - zb, z["bytes"], "zona %s: bytes dichiarati non coincidono" % z["nome"])
            cursore = zf
        self.assertEqual(cursore, fine_tot, "le zone non arrivano fino a fine riserva")

    def test_blocchi_di_ogni_zona_non_si_sovrappongono_e_coprono_la_zona(self):
        for z in self.mappa["zone"]:
            zb, zf = int(z["base"], 16), int(z["fine"], 16)
            blocchi = blocchi_per_zona(self.mappa, z["nome"])
            self.assertTrue(blocchi, "zona %s senza blocchi" % z["nome"])
            cursore = zb
            for b in blocchi:
                bb = int(b["base"], 16)
                self.assertEqual(bb, cursore,
                                 "blocco %s inizia a 0x%08X, atteso 0x%08X (buco o sovrapposizione)"
                                 % (b["nome"], bb, cursore))
                cursore = bb + b["bytes"]
            self.assertEqual(cursore, zf,
                             "i blocchi della zona %s finiscono a 0x%08X, attesa 0x%08X"
                             % (z["nome"], cursore, zf))

    def test_nessuna_coppia_di_blocchi_si_sovrappone_globalmente(self):
        tutti = sorted(self.mappa["blocchi"], key=lambda b: int(b["base"], 16))
        for a, b in zip(tutti, tutti[1:]):
            fine_a = int(a["base"], 16) + a["bytes"]
            base_b = int(b["base"], 16)
            self.assertLessEqual(fine_a, base_b,
                                 "%s (fine 0x%08X) si sovrappone a %s (base 0x%08X)"
                                 % (a["nome"], fine_a, b["nome"], base_b))


def _rom_da_ambiente():
    return os.environ.get("SGP_RISERVA_ROM")


def _leggi_sezioni(rom_path):
    import ndspy.code
    with open(rom_path, "rb") as fh:
        head = fh.read(0x200)
        off, _e, ram, size = struct.unpack_from("<IIII", head, 0x20)
        fh.seek(off)
        blob = fh.read(size)
        y9_off, y9_size = struct.unpack_from("<II", head, 0x50)
        fh.seek(y9_off)
        y9 = fh.read(y9_size)
    return ndspy.code.MainCodeFile(blob, ram).sections, y9


def _byte_a(sezioni, addr, n):
    for s in sezioni:
        if s.ramAddress <= addr < s.ramAddress + len(s.data):
            o = addr - s.ramAddress
            if o + n <= len(s.data):
                return bytes(s.data[o:o + n])
    raise LookupError("0x%08X..+%d fuori da ogni sezione" % (addr, n))


def _parte_stabile_sha16(mappa):
    """Stessa formula documentata in MAPPA-RISERVA-ARM9.json (blocco 'intestazione',
    formato 0x10): sha256 di {schema, riserva, zone} come JSON canonico, primi 16 B.
    Scritta qui una TERZA volta, indipendente da applica_riserva12.py e da
    rileggi_riserva12.py (02-COME-LAVORARE.md §2.3)."""
    parte = {"schema": mappa["schema"], "riserva": mappa["riserva"], "zone": mappa["zone"]}
    blob = json.dumps(parte, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).digest()[:16]


class _ImpiantoConROM(unittest.TestCase):
    """Base comune a T2/T3/T4/T5: carica mappa + sezioni di una ROM."""

    @classmethod
    def setUpClass(cls):
        cls.mappa = carica_mappa()
        cls.rom = _rom_da_ambiente()
        try:
            cls.sezioni, cls.y9 = _leggi_sezioni(cls.rom)
        except ImportError as e:
            raise unittest.SkipTest("ndspy non disponibile: usare rom-review-venv (%s)" % e)


@unittest.skipUnless(_rom_da_ambiente(), "T2 richiede una ROM: SGP_RISERVA_ROM=<rom.nds>")
class TestT2Impronta(_ImpiantoConROM):
    """T2 — l'impronta di ogni blocco combacia con quanto letto dalla ROM di release.
    Avrebbe bloccato la ROM 1.1 spedita col gancio camera nel vuoto (04-*.md §4.3)."""

    def _verifica_blocco(self, b):
        letto = _byte_a(self.sezioni, int(b["base"], 16), b["bytes"])

        parziali = b.get("impronte_parziali")
        if parziali:
            for p in parziali:
                frammento = letto[p["offset"]:p["offset"] + p["bytes"]]
                atteso = p["sha256"]
                self.assertEqual(hashlib.sha256(frammento).hexdigest(), atteso,
                                 "blocco %s, offset +%d/+%d: impronta diversa da quella dichiarata"
                                 % (b["nome"], p["offset"], p["bytes"]))
            return

        sha_atteso = b.get("sha256") or b.get("sha256_atteso_a_zero")
        if sha_atteso and "..." not in sha_atteso:
            if b.get("puo_essere_ancora_zero") and set(letto) <= {0}:
                return  # prenotato da un pacchetto successivo, non ancora scritto: stato valido
            candidati = [sha_atteso] + list(b.get("sha256_precedenti", []))
            letto_hash = hashlib.sha256(letto).hexdigest()
            self.assertIn(letto_hash, candidati,
                         "blocco %s: impronta %s non e' fra quelle dichiarate in %s (%s)"
                         % (b["nome"], letto_hash, MAPPA.name, candidati))
            return

        if b.get("tutto_zero"):
            return  # coperto anche da test_ogni_blocco_tutto_zero_lo_e_davvero

        self.fail("blocco %s SENZA alcuna impronta dichiarata (ne' sha256, ne' "
                  "sha256_atteso_a_zero, ne' impronte_parziali): T2 non lo puo' "
                  "controllare (REVISIONE 02, C12: prima era un 'continue' silenzioso, D5 "
                  "della revisione privata)" % b["nome"])

    def test_ogni_blocco_con_sha256_combacia(self):
        for b in self.mappa["blocchi"]:
            with self.subTest(blocco=b["nome"]):
                self._verifica_blocco(b)

    def test_ogni_blocco_tutto_zero_lo_e_davvero(self):
        for b in self.mappa["blocchi"]:
            if not b.get("tutto_zero"):
                continue
            with self.subTest(blocco=b["nome"]):
                letto = _byte_a(self.sezioni, int(b["base"], 16), b["bytes"])
                self.assertTrue(set(letto) <= {0},
                                "blocco %s dichiarato tutto_zero ma non lo e'" % b["nome"])


@unittest.skipUnless(_rom_da_ambiente(), "T3 richiede una ROM: SGP_RISERVA_ROM=<rom.nds>")
class TestT3Ancore(_ImpiantoConROM):
    """T3 — ogni ancora e ogni consumatore pubblico cade nel blocco che lo dichiara.
    Da solo, avrebbe trovato B1 (audit 1.1)."""

    def _blocco_di(self, addr):
        for b in self.mappa["blocchi"]:
            base = int(b["base"], 16)
            if base <= addr < base + b["bytes"]:
                return b
        return None

    def test_riserva_ha_la_base_e_la_dimensione_dichiarate(self):
        """REVISIONE 02 (C7, corregge D2 della revisione privata): senza questo test T3
        passava identico su base e candidata (nessuna controprova reale). Sulla base 1.1
        (riserva ancora a 0x023DEB40) questo test FALLISCE per una ragione vera: la base
        e la dimensione dell'ultima sezione di autoload non coincidono con quelle
        dichiarate dalla mappa — non un LookupError su un indirizzo che non esiste."""
        ultima = self.sezioni[-1]
        base_attesa = int(self.mappa["riserva"]["base"], 16)
        bytes_attesi = self.mappa["riserva"]["bytes"]
        self.assertEqual(ultima.ramAddress, base_attesa,
                         "l'ultima sezione di autoload e' a 0x%08X, la mappa dichiara la "
                         "riserva a 0x%08X: questa ROM non ha (ancora) la riserva estesa"
                         % (ultima.ramAddress, base_attesa))
        self.assertEqual(len(ultima.data), bytes_attesi,
                         "l'ultima sezione e' lunga %d B, la mappa ne dichiara %d"
                         % (len(ultima.data), bytes_attesi))

    def test_letterali_ancora_puntano_dentro_il_blocco_dichiarato(self):
        for b in self.mappa["blocchi"]:
            for ancora in b.get("ancore", []):
                if ancora.get("dove") == "cheat":
                    continue
                dove = int(ancora["dove"], 16)
                with self.subTest(blocco=b["nome"], ancora=ancora["dove"]):
                    letto = struct.unpack_from("<I", _byte_a(self.sezioni, dove, 4))[0]
                    vale = int(ancora["vale"], 16)
                    if b.get("puo_essere_ancora_zero") and letto != vale:
                        # il letterale puo' ancora puntare allo stato PRECEDENTE (blocco
                        # non ancora scritto in questa ROM): non e' un fallimento di per
                        # se', lo e' solo se il letterale non punta a NESSUN blocco noto.
                        target_prec = letto & ~1 if ancora.get("thumb") else letto
                        self.assertIsNotNone(self._blocco_di(target_prec),
                                             "0x%08X (da 0x%08X) non cade in nessun blocco noto, "
                                             "ne' vecchio ne' nuovo" % (target_prec, dove))
                        continue
                    self.assertEqual(letto, vale,
                                     "letterale a 0x%08X vale 0x%08X, atteso 0x%08X (%s)"
                                     % (dove, letto, vale, b["nome"]))
                    target = vale & ~1 if ancora.get("thumb") else vale
                    blocco_target = self._blocco_di(target)
                    self.assertIsNotNone(blocco_target,
                                         "0x%08X (da 0x%08X) non cade in NESSUN blocco della mappa"
                                         % (target, dove))
                    # per un sentinella "fine esclusiva" (es. CAM_EXC_END) il bersaglio e'
                    # per costruzione l'inizio del blocco SUCCESSIVO, non del proprietario
                    # dell'ancora: "punta_a_blocco" lo dichiara esplicitamente.
                    atteso_nome = ancora.get("punta_a_blocco", b["nome"])
                    self.assertEqual(blocco_target["nome"], atteso_nome,
                                     "0x%08X (da 0x%08X) cade in %s, non in %s come dichiarato"
                                     % (target, dove, blocco_target["nome"], atteso_nome))

    def test_cheat_pubblici_spediti_cadono_in_un_blocco_pubblico(self):
        """REVISIONE 02 (C6, corregge D2/D3 della revisione privata):
        - la regex NON e' piu' ancorata a riga intera (^...$ MULTILINE): i due
          cheat.xml spediti hanno tutti i codici su UNA riga sola dentro <codes>, e con
          l'ancoraggio precedente davano 0 indirizzi;
        - copre anche i codici 5xxxxxxx (04 §4.3), non solo 2xxxxxxx: e' cosi' che si
          vede il codice 523DEBE0 002EB570 (guardia camera Classic), presente in tutti
          e quattro i file spediti."""
        if not CHEATS_DIR.is_dir():
            self.skipTest("cartella dei cheat non trovata: %s" % CHEATS_DIR)
        pubblici = [b for b in self.mappa["blocchi"] if b.get("pubblico")]
        self.assertTrue(pubblici, "nessun blocco pubblico dichiarato nella mappa")
        indirizzi_letti = set()
        pat = re.compile(r"\b([25])([0-9A-Fa-f]{7})\s+[0-9A-Fa-f]{8}\b")
        for f in sorted(CHEATS_DIR.rglob("*")):
            if f.suffix.lower() not in (".mch",) and "cheat.xml" not in f.name.lower():
                continue
            testo = f.read_text(errors="ignore")
            for m in pat.finditer(testo):
                _tipo, resto = m.groups()
                indirizzi_letti.add(0x02000000 | int(resto, 16))
        self.assertTrue(indirizzi_letti, "nessun indirizzo 2xxxxxxx/5xxxxxxx trovato nei file di cheat spediti")
        for addr in sorted(indirizzi_letti):
            if not (0x023D8000 <= addr < 0x023E0000):
                continue  # fuori dalla riserva: non e' compito di questo test
            with self.subTest(indirizzo=hex(addr)):
                blocco = self._blocco_di(addr)
                self.assertIsNotNone(blocco, "0x%08X (da un cheat spedito) non cade in alcun blocco" % addr)
                self.assertTrue(blocco.get("pubblico"),
                                "0x%08X e' citato da un cheat spedito ma il blocco %s non e' 'pubblico': true"
                                % (addr, blocco["nome"]))


ARENA_LO_LIT = 0x020D2C5C
HEAP_TOTALE_MISURATO = 0x14D810
"""Somma di sDefaultHeapSpec (0x020F62A4, STATO-1.2.md §b (ex 04-RISERVA-ARM9-F0.md §4.3)), MISURATA e non
riparsata qui dalla ROM: la struttura esatta della tabella non e' documentata in questo
registro. E' la stessa costante con cui la revisione privata §3.2 ha calcolato il franco di
106 578 B (0x0226EC40+0x14D810+0xB56+0x1008 = 0x023BDFAE, verificato con aritmetica
indipendente durante questa revisione). Un pacchetto futuro che cambi l'heap deve
aggiornare QUESTA costante insieme al cambiamento, non il contrario."""
MARGINE_MINIMO_T4 = 8192


@unittest.skipUnless(_rom_da_ambiente(), "T4 richiede una ROM: SGP_RISERVA_ROM=<rom.nds>")
class TestT4MargineHeap(_ImpiantoConROM):
    """T4 (REVISIONE 02, C22: STATO-1.2.md §b (ex 04-RISERVA-ARM9-F0.md §6) passo 1 lo prescriveva - cancello 9 -
    ma non era mai stato scritto; RESULT.json lo dava per 'assorbito qui', D1.3 di
    revisione privata). Protegge dal rischio residuo di 04 §3: se un lavoro futuro
    ingrandisce l'heap o aggiunge file alla FAT/FNT, QUESTO test deve diventare rosso
    prima che il gioco si corrompa."""

    def test_margine_fino_alla_riserva(self):
        with open(self.rom, "rb") as fh:
            head = fh.read(0x200)
        fnt_size = struct.unpack_from("<I", head, 0x44)[0]
        fat_size = struct.unpack_from("<I", head, 0x4C)[0]
        arena_lo = struct.unpack_from("<I", _byte_a(self.sezioni, ARENA_LO_LIT, 4))[0]
        base_riserva = int(self.mappa["riserva"]["base"], 16)
        totale = arena_lo + HEAP_TOTALE_MISURATO + fnt_size + fat_size + MARGINE_MINIMO_T4
        self.assertLess(totale, base_riserva,
                        "ArenaLo(0x%X) + heap(0x%X) + FNT(0x%X) + FAT(0x%X) + margine(0x%X) "
                        "= 0x%X, >= base riserva 0x%X: la riserva rischia di toccare l'heap"
                        % (arena_lo, HEAP_TOTALE_MISURATO, fnt_size, fat_size,
                           MARGINE_MINIMO_T4, totale, base_riserva))


@unittest.skipUnless(_rom_da_ambiente(), "T5 richiede una ROM: SGP_RISERVA_ROM=<rom.nds>")
class TestT5Intestazione(_ImpiantoConROM):
    """T5 (nuovo, mandato di revisione 02): l'intestazione SGP2 scritta in ROM e'
    coerente con la mappa corrente. Scritto una TERZA volta, indipendente da
    applica_riserva12.py e da rileggi_riserva12.py (_parte_stabile_sha16 sopra)."""

    def test_intestazione_coerente_con_la_mappa(self):
        blocco = next(b for b in self.mappa["blocchi"] if b["nome"] == "intestazione")
        base = int(blocco["base"], 16)
        letta = _byte_a(self.sezioni, base, blocco["bytes"])
        self.assertEqual(letta[:4], b"SGP2", "magic dell'intestazione = %r" % letta[:4])
        atteso = _parte_stabile_sha16(self.mappa)
        letto16 = bytes(letta[16:32])
        self.assertEqual(letto16, atteso,
                         "0x%08X+16..+32 = %s, atteso (da schema+riserva+zone della mappa "
                         "corrente) = %s: l'intestazione non e' allineata alla mappa"
                         % (base, letto16.hex(), atteso.hex()))


class TestGuardiaModalitaCompleta(unittest.TestCase):
    """REVISIONE 02 (C18, corregge D10 della revisione privata): senza una ROM, T2-T5
    saltano con motivo esplicito, ed e' corretto per lo sviluppo locale. Ma una suite
    'OK (skipped=8)' e' indistinguibile da una suite verde vera se nessuno la guarda: chi
    vuole una corsa CI che NON possa dimenticare la variabile imposta
    SGP_RISERVA_COMPLETA=1, e allora l'assenza di SGP_RISERVA_ROM diventa un fallimento
    esplicito invece di uno skip silenzioso."""

    def test_rom_presente_se_modalita_completa_richiesta(self):
        if not os.environ.get("SGP_RISERVA_COMPLETA"):
            self.skipTest("SGP_RISERVA_COMPLETA non impostata: modalita' locale, gli skip di T2-T5 sono ammessi")
        self.assertTrue(_rom_da_ambiente(),
                        "SGP_RISERVA_COMPLETA=1 ma SGP_RISERVA_ROM non e' impostata: "
                        "T2/T3/T4/T5 sarebbero saltati in silenzio")


if __name__ == "__main__":
    unittest.main()
