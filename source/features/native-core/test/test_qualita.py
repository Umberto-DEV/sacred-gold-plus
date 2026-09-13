#!/usr/bin/env python3
"""Cancelli Q1-Q7 di CRITERI.md, eseguendo il codice macchina.

Ogni test che confronta «prima» e «dopo» carica DUE blob: quello ESTRATTO dalla
ROM di lavoro (`prove/estratti/blob-*.bin`, i byte che oggi girano) e quello
appena compilato da `sorgenti-v-finale/`. I difetti veri si vedono qui: il test
che riproduce il difetto FALLISCE sul blob estratto e PASSA su quello nuovo.

Serve il `python3` di SISTEMA (unicorn + capstone); il venv `rom-review` no.
"""
import json
import struct
import subprocess
import sys
import atexit
import shutil
import tempfile
import unittest
from pathlib import Path

QUI = Path(__file__).resolve().parent
PACCHETTO = QUI.parent
W = PACCHETTO.parent
sys.path.insert(0, str(QUI))

try:
    from banco import (Banco, crc16_ccitt, DC_FLUSH, IC_INVAL, SP0,
                       WRITE_BACKUP, READ_BACKUP)
    UNICORN = True
except ImportError:                                             # pragma: no cover
    UNICORN = False

import os

# Con SGP_SOLO_NUOVO=1 si provano SOLO i blob di `sorgenti-v-finale/`: la suite
# diventa verde. Senza, si provano anche i byte oggi in ROM e i 15 rossi che
# restano SONO i difetti riprodotti (vedi RAPPORTO.md §1).
BLOB = ("nuovo",) if os.environ.get("SGP_SOLO_NUOVO") else ("vecchio", "nuovo")

ESTRATTI = PACCHETTO / "prove" / "estratti"
# Livelli di allenatori e selvatici della 1.1: sono dati DEL GIOCO, letti
# dalla ROM, e non stanno in questo repository. Chi vuole il cancello Q3 li
# rigenera dalla propria ROM (source/README.md, «Class B»); senza, salta.
DATI_1_1 = Path(os.environ.get("SGP_DATI_1_1", PACCHETTO / "prove" / "dati-1.1.json"))

# --- indirizzi in RAM -------------------------------------------------------
STATO = 0x023D8700
CHUNK = STATO + 0x10
TAB_TRN, TAB_WLD = 0x023D8500, 0x023D8600
NPC_BLOB, NPC_STATO = 0x023D8900, 0x023D89E0
W1_STATO, W1_DATI = 0x023DA240, 0x023DA040
VENEER2, VENEER3 = 0x023DA000, 0x023DA020
SITO_G2, SITO_G3 = 0x021FC150, 0x021EC4A4
PRE_G2, PRE_G3 = 0xE92D4070, 0xE92D4000
SET_A, SET_B = 0x0002F000, 0x0006F000
BUF = 0x023D8F00
WORK = 0x02300000                      # work buffer DWC nell'area dati

# --- simboli dei blob ESTRATTI (manifesti dei pacchetti che li hanno applicati)
VECCHIO = {
    "plus": dict(file="blob-plus-EN.bin", base=0x023D8100, simboli={
        "sgp_trpoke_stride": 0x23D823D, "sgp_group_max": 0x23D824B,
        "sgp_trainer_level": 0x23D827D, "sgp_trainer_hook": 0x23D82E5,
        "sgp_wild_level": 0x23D8305, "sgp_wild_hook": 0x23D8341}),
    "salva": dict(file="blob-salvataggio-EN.bin", base=0x023D8730, simboli={
        "sgp_gancio_carica": 0x23D8731, "sgp_gancio_salva": 0x23D8859}),
    "npc": dict(file="blob-npc-EN.bin", base=0x023D8900, simboli={
        "sgp_npc_tetto": 0x23D8901, "sgp_npc_hook": 0x23D8971}),
    "wifi": dict(file="blob-wifi_slot4-EN.bin", base=0x023DA250, simboli={
        "sgp_wfc_slot_configurato": 0x23DA251, "sgp_wfc_servizio_da_lr": 0x23DA301,
        "sgp_wfc_on_connect": 0x23DA349, "sgp_wfc_nibble": 0x23DA3AD,
        "sgp_wfc_on_overlay": 0x23DA431, "sgp_wfc_trampolino": 0x23DA4B5}),
}

_nuovo = {}


def nuovo(nome):
    """Compila (una volta) i blob di `sorgenti-v-finale/` e restituisce il
    dizionario {byte, base, simboli} del blob richiesto."""
    if not _nuovo:
        d = Path(tempfile.mkdtemp(prefix="sgp-qual-"))
        atexit.register(shutil.rmtree, d, ignore_errors=True)
        r = subprocess.run([sys.executable, str(PACCHETTO / "tools" / "compila_tutti.py"),
                            "--uscita", str(d)], text=True, capture_output=True)
        if not (d / "manifesto.json").exists():
            raise RuntimeError(r.stdout + r.stderr)
        man = json.loads((d / "manifesto.json").read_text())
        for k, v in man["blob"].items():
            _nuovo[k] = dict(byte=(d / (k + ".bin")).read_bytes(),
                             simboli={n: int(x, 16) for n, x in v["simboli"].items()
                                      if not n.startswith("$")},
                             manifesto=v)
    return _nuovo[nome]


def vecchio(nome):
    spec = VECCHIO[nome]
    return dict(byte=(ESTRATTI / spec["file"]).read_bytes(),
                simboli=spec["simboli"])


def chunk_bytes(magic=0x5347, versione=2, plus=0, selvatici=0, oltre100=0,
                anim=0, npc=0, wifi=0, picco=1, r0=0, r1=0, r2=0):
    return struct.pack("<HBBBBBBBBBBI", magic, versione, plus, selvatici,
                       oltre100, anim, npc, wifi, picco, r0, r1, r2)


def settore(payload, saveno=1, magic=0x32504753, size=16, idx=6, crc=None):
    testa = struct.pack("<IIIH", magic, saveno, size, idx)
    if crc is None:
        crc = crc16_ccitt(payload + testa[:14 - 16 + 16][:14])
    return payload + testa + struct.pack("<H", crc)


def settore_valido(payload, saveno=1):
    testa = struct.pack("<IIIH", 0x32504753, saveno, 16, 6)
    return payload + testa + struct.pack("<H", crc16_ccitt(payload + testa))


def stato_bytes(active_plus=0, active_wild=0, cap=100, load=2, guard=0x5A,
                hits_t=0, hits_w=0, chunk=None):
    testa = struct.pack("<BBBBBBHII", active_plus, active_wild, cap, load,
                        guard, 0, 0, hits_t, hits_w)
    return testa + (chunk if chunk is not None else chunk_bytes())


def trpoke(livelli, stride):
    b = bytearray(stride * len(livelli))
    for i, lv in enumerate(livelli):
        b[i * stride + 2] = lv & 0xFF
        b[i * stride + 3] = (lv >> 8) & 0xFF
    return bytes(b)


class BancoPlus(Banco):
    def __init__(self, blob):
        super().__init__()
        base = 0x023D8100
        self.simboli = blob["simboli"]
        self.carica(base, blob["byte"])
        self.carica(TAB_TRN, (ESTRATTI / "tab-trainer-EN.bin").read_bytes())
        self.carica(TAB_WLD, (ESTRATTI / "tab-wild-EN.bin").read_bytes())
        self.carica(STATO, stato_bytes())

    def stato(self, **kw):
        self.carica(STATO, stato_bytes(**kw))

    def sim(self, nome):
        return self.simboli[nome]


CANARINI = [0xA0A0A000, 0xA1A1A101, 0xA2A2A202, 0xA3A3A303,
            0xA4A4A404, 0xA5A5A505, 0xA6A6A606, 0xA7A7A707]


@unittest.skipUnless(UNICORN, "unicorn assente: i cancelli Q non sono superati")
class Q7Byte(unittest.TestCase):
    """Q7.1/Q7.2 — che cosa è cambiato rispetto ai byte applicati."""

    def test_dimensioni_e_identita(self):
        atteso = {"plus": False, "salva": False, "npc": False, "wifi": False}
        for nome, ident in atteso.items():
            m = nuovo(nome)["manifesto"]
            self.assertEqual(m["identico_al_blob_applicato"], ident,
                             "%s: identità col blob applicato cambiata" % nome)

    def test_blob_stanno_nei_loro_blocchi(self):
        """sgp.plus: blob PLUS + blob salvataggio devono stare sotto +0x400."""
        fine_plus = 0x023D8100 + len(nuovo("plus")["byte"])
        base_salva = int(nuovo("salva")["manifesto"]["comando"] and 0x023D8220)
        fine_salva = base_salva + len(nuovo("salva")["byte"])
        self.assertLessEqual(fine_plus, base_salva)
        self.assertLessEqual(fine_salva, 0x023D8100 + 0x400)
        self.assertLessEqual(len(nuovo("npc")["byte"]), 0xE0)
        self.assertLessEqual(0x023DA250 + len(nuovo("wifi")["byte"]), 0x023DA800)


@unittest.skipUnless(UNICORN, "unicorn assente")
class QPlusEquivalenza(unittest.TestCase):
    """Q7.3 — il blob PLUS nuovo (senza `plus_state.c`) calcola ESATTAMENTE
    quello che calcola il blob applicato, su tutto il dominio."""

    @classmethod
    def setUpClass(cls):
        cls.v = BancoPlus(vecchio("plus"))
        cls.n = BancoPlus(nuovo("plus"))
        if not DATI_1_1.exists():
            raise unittest.SkipTest(
                "classe B: manca %s (livelli letti dalla ROM, non pubblicabili)" % DATI_1_1)
        cls.dati = json.loads(DATI_1_1.read_text())

    def _confronta_wild(self, wild):
        for b in (self.v, self.n):
            b.stato(active_wild=wild)
        for base in range(0, 256):
            rv = self.v.chiama(self.v.sim("sgp_wild_level"), (base,))[0]
            rn = self.n.chiama(self.n.sim("sgp_wild_level"), (base,))[0]
            self.assertEqual(rv, rn, "wild base=%d wild=%d" % (base, wild))

    def test_wild_tutto_il_dominio(self):
        self._confronta_wild(0)
        self._confronta_wild(1)

    def test_wild_fuori_dominio(self):
        for b in (self.v, self.n):
            b.stato(active_wild=1)
        for base in (256, 300, 0xFFFF, 0xFFFFFFFF):
            self.assertEqual(self.v.chiama(self.v.sim("sgp_wild_level"), (base,))[0],
                             self.n.chiama(self.n.sim("sgp_wild_level"), (base,))[0])

    def test_trainer_tutti_i_gruppi(self):
        gruppi = self.dati["allenatori"]["gruppi"]
        self.assertGreater(len(gruppi), 100)
        n_membri = 0
        for plus in (0, 1):
            for b in (self.v, self.n):
                b.stato(active_plus=plus)
            for g in gruppi:
                liv = g["livelli"]
                tipo = g.get("tipo", 0)
                stride = 8 + ((tipo & 1) << 3) + (tipo & 2)
                buf = trpoke(liv, stride)
                for b in (self.v, self.n):
                    b.scrivi(WORK, buf)
                tn = (len(liv) << 8) | tipo
                for base in liv:
                    rv = self.v.chiama(self.v.sim("sgp_trainer_level"), (base, WORK, tn))[0]
                    rn = self.n.chiama(self.n.sim("sgp_trainer_level"), (base, WORK, tn))[0]
                    self.assertEqual(rv, rn, "gruppo %s base %d" % (g.get("id"), base))
                    n_membri += 1
        self.assertGreater(n_membri, 2000)

    def test_trampoline_preservano_i_registri(self):
        """Q1.1 — le due trampoline, eseguite con canarini su r0..r7."""
        for b in (self.v, self.n):
            b.stato(active_plus=1, active_wild=1)
            b.scrivi(WORK, trpoke([20, 20, 20], 8))
        # gancio selvatici: r1..r6 invariati, r7 = livello effettivo
        for b in (self.v, self.n):
            can = list(CANARINI)
            can[7] = 40
            b.scrivi(SP0 + 0x10, b"\x05")
            _, fuori = b.chiama(b.sim("sgp_wild_hook"), (), canarini=can)
            self.assertEqual(fuori[0], 5, "r0 = indice di slot")
            for i in (4, 5, 6):
                self.assertEqual(fuori[i], can[i], "r%d sporcato dal gancio selvatici" % i)
            self.assertGreater(fuori[7], 40, "r7 = livello effettivo")


@unittest.skipUnless(UNICORN, "unicorn assente")
class QSalva(unittest.TestCase):
    """Q2.2, Q4.3, Q4.5 — lettura e scrittura del chunk."""

    def banco(self, quale):
        b = Banco()
        spec = nuovo("salva") if quale == "nuovo" else vecchio("salva")
        base = 0x023D8220 if quale == "nuovo" else 0x023D8730
        b.carica(base, spec["byte"])
        b.simboli = spec["simboli"]
        b.carica(STATO, bytes(32))
        b.carica(BUF, bytes(32))
        return b

    def carica(self, b, hits=(0, 0)):
        b.carica(STATO, stato_bytes(load=0, guard=0, hits_t=hits[0], hits_w=hits[1]))
        b.chiama(b.simboli["sgp_gancio_carica"], (0x12345678,))
        return b.leggi(STATO, 32)

    def salva(self, b):
        b.orig_save_ret = 2
        b.chiama(b.simboli["sgp_gancio_salva"], (0x12345678,))

    # --- lettura ---------------------------------------------------------
    def test_chunk_assente(self):
        for q in BLOB:
            b = self.banco(q)
            st = self.carica(b)
            self.assertEqual(st[3], 1, "%s: load_status deve essere ABSENT" % q)
            self.assertEqual(st[4], 0x5A)
            self.assertEqual(st[0], 0)
            self.assertEqual(st[1], 0)
            self.assertEqual(st[16 + 9], 1, "picco = 1")

    def test_chunk_valido(self):
        p = chunk_bytes(plus=1, selvatici=1, anim=1, npc=1, wifi=3, picco=57)
        for q in BLOB:
            b = self.banco(q)
            b.settori[SET_A] = settore_valido(p)
            st = self.carica(b)
            self.assertEqual(st[3], 2)
            self.assertEqual((st[0], st[1]), (1, 1))
            self.assertEqual(bytes(st[16:32]), p)

    def test_copia_A_rotta_si_usa_la_B(self):
        p = chunk_bytes(plus=1, picco=9)
        for q in BLOB:
            b = self.banco(q)
            b.settori[SET_A] = b"\x00" * 32
            b.settori[SET_B] = settore_valido(p)
            st = self.carica(b)
            self.assertEqual(st[3], 2, "%s: la copia B doveva salvare la lettura" % q)

    def test_tredici_malformati_rifiutati(self):
        casi = {
            "magic chunk": chunk_bytes(magic=0x4747),
            "versione 0": chunk_bytes(versione=0),
            "versione 3": chunk_bytes(versione=3),
            "plus 2": chunk_bytes(plus=2),
            "selvatici 2": chunk_bytes(selvatici=2),
            "oltre100 2": chunk_bytes(oltre100=2),
            "anim 2": chunk_bytes(anim=2),
            "npc 2": chunk_bytes(npc=2),
            "wifi 4": chunk_bytes(wifi=4),
            "picco 0": chunk_bytes(picco=0),
            "picco 101": chunk_bytes(picco=101),
            "riservato0": chunk_bytes(r0=1),
            "riservato2": chunk_bytes(r2=1),
        }
        for q in BLOB:
            for nome, p in casi.items():
                b = self.banco(q)
                b.settori[SET_A] = settore_valido(p)
                b.settori[SET_B] = settore_valido(p)
                st = self.carica(b)
                self.assertEqual(st[3], 3, "%s/%s doveva essere RIFIUTATO" % (q, nome))

    def test_S4_versione_1_non_si_legge_con_la_pianta_2(self):
        """Un chunk di versione 1 ha una pianta diversa: accettarlo vorrebbe dire
        leggerlo storto. `CONTRATTO-CHUNK` §6 diceva «1 <= versione <= 2»; nessuna
        ROM ha mai scritto una versione 1, quindi il contratto va stretto, non il
        codice allargato. Va aggiornata §6."""
        p = chunk_bytes(versione=1, picco=9)
        for q in BLOB:
            b = self.banco(q)
            b.settori[SET_A] = settore_valido(p)
            b.settori[SET_B] = settore_valido(p)
            with self.subTest(blob=q):
                self.assertEqual(self.carica(b)[3], 3,
                                 "%s: un chunk di versione 1 e' stato accettato" % q)

    def test_crc_sbagliato_rifiutato(self):
        p = chunk_bytes(plus=1)
        for q in BLOB:
            b = self.banco(q)
            s = bytearray(settore_valido(p))
            s[-1] ^= 0xFF
            b.settori[SET_A] = bytes(s)
            b.settori[SET_B] = bytes(s)
            self.assertEqual(self.carica(b)[3], 3)

    def test_magic_del_gioco_non_e_il_nostro(self):
        """Un chunk del gioco (magic 0x20060623) è «assente», non «rifiutato»."""
        p = chunk_bytes()
        testa = struct.pack("<IIIH", 0x20060623, 1, 16, 6)
        s = p + testa + struct.pack("<H", crc16_ccitt(p + testa))
        for q in BLOB:
            b = self.banco(q)
            b.settori[SET_A] = s
            b.settori[SET_B] = s
            self.assertEqual(self.carica(b)[3], 1)

    def test_hits_non_si_azzerano(self):
        for q in BLOB:
            b = self.banco(q)
            st = self.carica(b, hits=(7, 9))
            self.assertEqual(struct.unpack("<II", st[8:16]), (7, 9))

    # --- scrittura -------------------------------------------------------
    def test_scrive_due_copie_e_saveno_cresce(self):
        for q in BLOB:
            b = self.banco(q)
            self.carica(b)
            self.salva(b)
            self.assertIn(SET_A, b.settori)
            self.assertEqual(b.settori[SET_A], b.settori[SET_B])
            n1 = struct.unpack("<I", b.settori[SET_A][20:24])[0]
            self.salva(b)
            n2 = struct.unpack("<I", b.settori[SET_A][20:24])[0]
            self.assertEqual(n2, (n1 + 1) & 0xFFFFFFFF)

    def test_chunk_rifiutato_non_si_riscrive(self):
        p = chunk_bytes(anim=2)
        for q in BLOB:
            b = self.banco(q)
            b.settori[SET_A] = settore_valido(p)
            b.settori[SET_B] = settore_valido(p)
            self.carica(b)
            prima = dict(b.settori)
            self.salva(b)
            self.assertEqual(b.settori, prima, "%s: un chunk rifiutato è stato riscritto" % q)

    def test_senza_guardia_non_scrive(self):
        for q in BLOB:
            b = self.banco(q)
            b.carica(STATO, bytes(32))
            self.salva(b)
            self.assertEqual(b.settori, {}, "%s: scritto con lo stato non inizializzato" % q)

    def test_esito_non_2_non_scrive(self):
        for q in BLOB:
            b = self.banco(q)
            self.carica(b)
            b.orig_save_ret = 1
            b.chiama(b.simboli["sgp_gancio_salva"], (0,))
            self.assertEqual(b.settori, {})

    def test_valore_di_ritorno_dei_due_ganci_intatto(self):
        for q in BLOB:
            b = self.banco(q)
            for v in (0, 1, 2, 3, 0xFFFFFFFF):
                b.orig_load_ret = v
                self.assertEqual(b.chiama(b.simboli["sgp_gancio_carica"], (0,))[0], v)
                b.orig_save_ret = v
                self.assertEqual(b.chiama(b.simboli["sgp_gancio_salva"], (0,))[0], v)

    # --- Q4.5: DIFETTO B3 -------------------------------------------------
    def test_B3_il_chunk_scritto_e_sempre_rileggibile(self):
        """Un byte fuori dominio scritto da un altro cantiere non deve poter
        produrre un chunk che al prossimo avvio si auto-rifiuta (e che, essendo
        rifiutato, non verrà mai più riscritto: impostazioni perse per sempre)."""
        sporchi = [
            ("anim", 0x16, 2), ("anim", 0x16, 0xFF), ("npc", 0x17, 5),
            ("wifi_server", 0x18, 7), ("wifi_server", 0x18, 0xFF),
            ("oltre100", 0x15, 3), ("picco", 0x19, 0), ("picco", 0x19, 200),
        ]
        for q in BLOB:
            for nome, off, val in sporchi:
                b = self.banco(q)
                self.carica(b)
                st = bytearray(b.leggi(STATO, 32))
                st[off] = val
                b.carica(STATO, bytes(st))
                self.salva(b)
                # secondo avvio: si rilegge quello che si è appena scritto
                b2 = self.banco(q)
                b2.settori = dict(b.settori)
                letto = self.carica(b2)
                with self.subTest(blob=q, campo=nome, valore=val):
                    self.assertEqual(
                        letto[3], 2,
                        "%s: con %s=%d il chunk scritto non si rilegge "
                        "(load_status=%d): impostazioni perse" % (q, nome, val, letto[3]))

    def test_B7_lettura_fallita_non_convalida_il_buffer(self):
        """Se ReadBackup non scrive nel buffer, il contenuto precedente non deve
        poter passare per un chunk valido appena letto."""
        p = chunk_bytes(plus=1, picco=42)
        for q in BLOB:
            b = self.banco(q)
            b.carica(BUF, settore_valido(p))      # residuo in RAM
            b.lettura_ok = False
            with self.subTest(blob=q):
                self.assertEqual(self.carica(b)[3], 1,
                                 "%s: buffer stantio scambiato per chunk letto" % q)


@unittest.skipUnless(UNICORN, "unicorn assente")
class QNpc(unittest.TestCase):
    """Q4.2, Q4.3 e il difetto B2 (default acceso perso al primo salvataggio).

    I test del default sono di INSIEME: fanno girare il gancio di lettura di D1
    e poi il gancio di P2, perché è esattamente lì che il difetto vive."""

    def banco(self, quale, tetto=1, guardia=0x5A):
        b = Banco()
        npc = nuovo("npc") if quale == "nuovo" else vecchio("npc")
        salva = nuovo("salva") if quale == "nuovo" else vecchio("salva")
        b.carica(NPC_BLOB, npc["byte"])
        b.carica(0x023D8220 if quale == "nuovo" else 0x023D8730, salva["byte"])
        b.simboli = dict(npc["simboli"])
        b.simboli.update(salva["simboli"])
        b.carica(NPC_STATO, struct.pack("<BBBBhHII", 0, tetto, guardia, 0, 0, 0, 0, 0))
        b.carica(STATO, bytes(32))
        b.carica(BUF, bytes(32))
        return b

    def d1_carica(self, b):
        """Il gancio L0 di D1: è lui che normalizza la copia in RAM del chunk."""
        b.chiama(b.simboli["sgp_gancio_carica"], (0x12345678,))

    def d1_salva(self, b):
        b.orig_save_ret = 2
        b.chiama(b.simboli["sgp_gancio_salva"], (0x12345678,))

    def lista(self, b, tetto=10):
        b.scrivi(WORK, struct.pack("<hh", 4, tetto))
        return WORK

    def gira(self, b, tetto=10):
        l = self.lista(b, tetto)
        b.chiama(b.simboli["sgp_npc_tetto"], (l,))
        return struct.unpack("<h", b.leggi(l + 2, 2))[0]

    def test_senza_guardia_non_tocca_niente(self):
        for q in BLOB:
            b = self.banco(q, guardia=0)
            self.d1_carica(b)
            prima_stato = b.leggi(NPC_STATO, 16)
            prima_chunk = b.leggi(CHUNK, 16)
            self.assertEqual(self.gira(b), 10)
            self.assertEqual(b.leggi(NPC_STATO, 16), prima_stato,
                             "%s: stato toccato senza la guardia" % q)
            self.assertEqual(b.leggi(CHUNK, 16), prima_chunk,
                             "%s: chunk toccato senza la guardia" % q)

    def test_load_status_0_o_3_spento(self):
        for q in BLOB:
            for load in (0, 3):
                b = self.banco(q)
                b.carica(STATO, stato_bytes(load=load, guard=0x5A,
                                            chunk=chunk_bytes(npc=1)))
                self.assertEqual(self.gira(b), 10,
                                 "%s: load_status=%d doveva essere vanilla" % (q, load))

    def test_chunk_valido_comanda(self):
        for q in BLOB:
            for npc, atteso in ((0, 10), (1, 1)):
                b = self.banco(q)
                b.carica(STATO, stato_bytes(load=2, guard=0x5A,
                                            chunk=chunk_bytes(npc=npc)))
                self.assertEqual(self.gira(b), atteso)

    def test_chunk_assente_acceso(self):
        """Con un salvataggio 1.1 la fluidità è accesa: è il mandato P2."""
        for q in BLOB:
            b = self.banco(q)
            self.d1_carica(b)
            self.assertEqual(b.leggi(STATO, 32)[3], 1, "il chunk doveva essere ASSENTE")
            self.assertEqual(self.gira(b), 1,
                             "%s: chunk assente = acceso (mandato P2)" % q)

    # --- DIFETTO B2 -------------------------------------------------------
    def test_B2_il_default_acceso_sopravvive_al_primo_salvataggio(self):
        """Salvataggio 1.1 → avvio → il giocatore salva → riavvio. Se il default
        non entra nel chunk, il salvataggio scrive npc=0 e la fluidità si spegne
        per sempre; e nel frattempo la pagina Opzioni (che legge quel byte)
        mostra «spento» mentre il clamp è attivo."""
        for q in BLOB:
            b = self.banco(q)
            self.d1_carica(b)
            with self.subTest(blob=q, fase="quel che vede Opzioni"):
                self.assertEqual(b.leggi(CHUNK + 7, 1)[0], 1,
                                 "%s: il byte `npc` del chunk è 0 mentre il gancio "
                                 "clampa: la pagina Opzioni mostra il contrario" % q)
            self.gira(b)
            self.d1_salva(b)
            b2 = self.banco(q)
            b2.settori = dict(b.settori)
            self.d1_carica(b2)
            with self.subTest(blob=q, fase="secondo avvio"):
                self.assertEqual(b2.leggi(STATO, 32)[3], 2, "il chunk doveva essere VALIDO")
                self.assertEqual(self.gira(b2), 1,
                                 "%s: dopo il primo salvataggio la fluidità è spenta "
                                 "per sempre" % q)

    def test_B2_non_riaccende_quello_che_il_giocatore_ha_spento(self):
        for q in BLOB:
            b = self.banco(q)
            b.carica(STATO, stato_bytes(load=2, guard=0x5A, chunk=chunk_bytes(npc=0)))
            self.gira(b)
            self.assertEqual(b.leggi(CHUNK + 7, 1)[0], 0,
                             "%s: con chunk VALIDO non si tocca la scelta" % q)
            self.assertEqual(self.gira(b), 10)

    # --- DIFETTO B4 -------------------------------------------------------
    @unittest.skipIf(os.environ.get("SGP_SOLO_NUOVO"), "confronta vecchio e nuovo")
    def test_B4_contratto_della_trampolina_npc(self):
        """Il contratto dichiarava «r1..r7 invariati»: falso, r3 è clobberato
        dalla chiamata C. È sicuro (r3 è morto al sito: disasm-npc.txt), ma il
        contratto va detto giusto. Qui si verifica quello VERO."""
        for q in BLOB:
            b = self.banco(q)
            b.scrivi(WORK, struct.pack("<hh", 4, 10))
            DATI_R0 = 0x02310000
            b.scrivi(DATI_R0, struct.pack("<I", 0xDEADBEEF))
            can = list(CANARINI)
            can[0] = DATI_R0 - 0xE0
            can[4] = WORK
            _, fuori = b.chiama(b.simboli["sgp_npc_hook"], (), canarini=can)
            self.assertEqual(fuori[0], 0xDEADBEEF, "r0 = [r0+0xE0]")
            for i in (1, 2, 4, 5, 6, 7):
                self.assertEqual(fuori[i], can[i], "%s: r%d sporcato" % (q, i))


@unittest.skipUnless(UNICORN, "unicorn assente")
class QWifi(unittest.TestCase):
    """Q2.3, Q4.2, Q5 e i difetti B5 (pending azzerato), B6 (guardia di D1),
    B8 (manutenzione cache)."""

    def banco(self, quale, magic=0x57, versione=2, modo=0, slot=0):
        b = Banco()
        spec = nuovo("wifi") if quale == "nuovo" else vecchio("wifi")
        b.carica(0x023DA250, spec["byte"])
        b.simboli = spec["simboli"]
        b.carica(W1_STATO, struct.pack("<BBBBBB10s", magic, versione, modo,
                                       slot, 0, 0, b"\0" * 10))
        b.carica(W1_DATI, bytes(64))
        b.carica(SITO_G2, struct.pack("<I", PRE_G2))
        b.carica(SITO_G3, struct.pack("<I", PRE_G3))
        b.carica(STATO, stato_bytes(load=2, guard=0x5A))
        return b

    def workbuf(self, b, configurati=(0, 1, 2), dns=b"\xb2\x3e\x2b\xd4"):
        w = bytearray(0xD18)
        for i in range(3):
            w[i * 0x100 + 0xE7] = 0 if i in configurati else 0xFF
            w[i * 0x100 + 0xC8:i * 0x100 + 0xCC] = dns
        b.scrivi(WORK, bytes(w))
        return WORK

    def _pending(self, b):
        return b.leggi(W1_DATI, 1)[0]

    def test_magic_o_versione_sbagliati_non_scrivono(self):
        for q in BLOB:
            for kw in (dict(magic=0x58), dict(versione=1)):
                b = self.banco(q, **kw)
                b.chiama(b.simboli["sgp_wfc_on_overlay"], (0,))
                self.assertEqual(b.leggi(W1_DATI, 64), bytes(64))
                self.assertEqual(struct.unpack("<I", b.leggi(SITO_G2, 4))[0], PRE_G2)

    # --- Q5: idempotenza ---------------------------------------------------
    def test_Q5_installa_una_volta_sola(self):
        for q in BLOB:
            b = self.banco(q)
            for _ in range(5):
                b.chiama(b.simboli["sgp_wfc_on_overlay"], (0,))
            n = struct.unpack("<I", b.leggi(W1_DATI + 0x0C, 4))[0]
            self.assertEqual(n, 2, "%s: %d installazioni invece di 2" % (q, n))
            g2 = struct.unpack("<I", b.leggi(SITO_G2, 4))[0]
            self.assertEqual(g2 >> 24, 0xEA, "non è un B ARM")

    def test_Q5_overlay_ricaricato_reinstalla_una_volta(self):
        for q in BLOB:
            b = self.banco(q)
            b.chiama(b.simboli["sgp_wfc_on_overlay"], (0,))
            b.carica(SITO_G2, struct.pack("<I", PRE_G2))   # Overlay_Load rilegge ov000
            b.carica(SITO_G3, struct.pack("<I", PRE_G3))
            for _ in range(3):
                b.chiama(b.simboli["sgp_wfc_on_overlay"], (0,))
            self.assertEqual(struct.unpack("<I", b.leggi(W1_DATI + 0x0C, 4))[0], 4)

    def test_ov013_azzera_la_forzatura(self):
        for q in BLOB:
            b = self.banco(q, modo=1, slot=2)
            b.scrivi(W1_DATI, b"\x02\x02")
            b.chiama(b.simboli["sgp_wfc_on_overlay"], (13,))
            self.assertEqual(self._pending(b), 0)

    # --- ripiego (WIFI-04) -------------------------------------------------
    def test_ripiego_slot_designato_non_configurato(self):
        for q in BLOB:
            b = self.banco(q, modo=1, slot=3)
            w = self.workbuf(b, configurati=(1,))          # solo lo slot 2
            b.scrivi(W1_DATI, b"\x03")
            b.chiama(b.simboli["sgp_wfc_nibble"], (w,))
            self.assertEqual(b.leggi(w + 0xD0C, 1)[0] & 0xF, 2)
            self.assertEqual(struct.unpack("<I", b.leggi(W1_DATI + 0x20, 4))[0], 1)

    def test_nessuno_configurato_nessuna_forzatura(self):
        for q in BLOB:
            b = self.banco(q, modo=1, slot=2)
            w = self.workbuf(b, configurati=())
            b.scrivi(W1_DATI, b"\x02")
            b.chiama(b.simboli["sgp_wfc_nibble"], (w,))
            self.assertEqual(b.leggi(w + 0xD0C, 1)[0] & 0xF, 0)

    def test_slot_designato_configurato_nessun_ripiego(self):
        for q in BLOB:
            b = self.banco(q, modo=1, slot=3)
            w = self.workbuf(b, configurati=(0, 1, 2))
            b.scrivi(W1_DATI, b"\x03")
            b.chiama(b.simboli["sgp_wfc_nibble"], (w,))
            self.assertEqual(b.leggi(w + 0xD0C, 1)[0] & 0xF, 3)
            self.assertEqual(struct.unpack("<I", b.leggi(W1_DATI + 0x20, 4))[0], 0)

    def test_pending_fuori_dominio_non_forza(self):
        for q in BLOB:
            for p in (4, 0x7F, 0xFF):
                b = self.banco(q, modo=1, slot=2)
                w = self.workbuf(b)
                b.scrivi(W1_DATI, bytes([p]))
                b.chiama(b.simboli["sgp_wfc_nibble"], (w,))
                self.assertEqual(b.leggi(w + 0xD0C, 1)[0] & 0xF, 0)

    def test_nibble_conserva_il_nibble_alto(self):
        for q in BLOB:
            b = self.banco(q, modo=1, slot=2)
            w = self.workbuf(b)
            b.scrivi(w + 0xD0C, b"\xA0")
            b.scrivi(W1_DATI, b"\x02")
            b.chiama(b.simboli["sgp_wfc_nibble"], (w,))
            self.assertEqual(b.leggi(w + 0xD0C, 1)[0], 0xA2)

    # --- G3 ----------------------------------------------------------------
    def test_servizi_noti(self):
        casi = {0x02236B8F: 1, 0x022448B9: 2, 0x02228CFD: 2, 0x02239219: 2,
                0x021E8D27: 2, 0x022487F3: 2, 0x02222222: 0}
        for q in BLOB:
            b = self.banco(q)
            for lr, atteso in casi.items():
                self.assertEqual(b.chiama(b.simboli["sgp_wfc_servizio_da_lr"], (lr,))[0],
                                 atteso)

    def test_G3_applica_la_scelta_del_chunk(self):
        for q in BLOB:
            for wifi, lr, atteso in ((0, 0x022448B9, 0), (2, 0x022448B9, 2),
                                     (3, 0x022448B9, 3), (2, 0x02236B8F, 1),
                                     (1, 0x022448B9, 0), (5, 0x022448B9, 0)):
                b = self.banco(q)
                b.carica(STATO, stato_bytes(load=2, guard=0x5A,
                                            chunk=chunk_bytes(wifi=wifi)))
                b.chiama(b.simboli["sgp_wfc_on_connect"], (lr,))
                self.assertEqual(self._pending(b), atteso,
                                 "%s: wifi_server=%d lr=%08X" % (q, wifi, lr))

    # --- DIFETTO B5 --------------------------------------------------------
    def test_B5_un_lr_interno_non_cancella_la_scelta(self):
        """ov000 chiama DWC_ConnectInetAsync anche da due siti suoi. Se G3
        azzera `pending` su un lr sconosciuto, la scelta del giocatore sparisce
        prima che G2 scriva il nibble."""
        for q in BLOB:
            b = self.banco(q)
            b.carica(STATO, stato_bytes(load=2, guard=0x5A, chunk=chunk_bytes(wifi=3)))
            b.chiama(b.simboli["sgp_wfc_on_connect"], (0x022448B9,))
            self.assertEqual(self._pending(b), 3)
            b.chiama(b.simboli["sgp_wfc_on_connect"], (0x021EC574,))   # sito interno
            with self.subTest(blob=q):
                self.assertEqual(self._pending(b), 3,
                                 "%s: un lr interno di ov000 ha azzerato pending" % q)

    # --- DIFETTO B6 --------------------------------------------------------
    def test_B6_chunk_non_valido_non_si_legge(self):
        """Stessa guardia di P2: con `load_status` diverso da VALID il campo
        `wifi_server` non è attendibile e non deve forzare niente."""
        for q in BLOB:
            for load, guard in ((0, 0x5A), (3, 0x5A), (2, 0)):
                b = self.banco(q)
                b.carica(STATO, stato_bytes(load=load, guard=guard,
                                            chunk=chunk_bytes(wifi=3)))
                b.chiama(b.simboli["sgp_wfc_on_connect"], (0x022448B9,))
                with self.subTest(blob=q, load=load, guard=guard):
                    self.assertEqual(self._pending(b), 0,
                                     "%s: load_status=%d guard=%#x e forza lo slot "
                                     "lo stesso" % (q, load, guard))

    # --- DIFETTO B8 --------------------------------------------------------
    def test_B8_manutenzione_cache_dopo_aver_scritto_codice(self):
        """Scrivere un'istruzione in RAM senza `DC_FlushRange` +
        `IC_InvalidateRange` lascia la parola sporca in D-cache: su DS reale la
        CPU può prelevare ancora quella vecchia. melonDS non modella le cache,
        quindi nessuna corsa può accorgersene."""
        for q in BLOB:
            b = self.banco(q)
            b.chiama(b.simboli["sgp_wfc_on_overlay"], (0,))
            visti = {a for a, _, _ in b.chiamate}
            with self.subTest(blob=q):
                self.assertIn(DC_FLUSH, visti, "%s: manca DC_FlushRange" % q)
                self.assertIn(IC_INVAL, visti, "%s: manca IC_InvalidateRange" % q)


if __name__ == "__main__":
    unittest.main(verbosity=2)


@unittest.skipUnless(UNICORN, "unicorn assente")
class QVincoli(unittest.TestCase):
    """Q2.1, Q3 e il difetto B1 (due piante incompatibili sullo stesso stato)."""

    # --- DIFETTO B1 -------------------------------------------------------
    @unittest.skipIf(os.environ.get("SGP_SOLO_NUOVO"), "riguarda solo il blob applicato")
    def test_B1_lo_stato_v1_corrompe_il_chunk_v2(self):
        """Il blob PLUS applicato porta ancora `sgp_state_*`, scritte per la
        pianta `SgpExtra` di versione 1 che nessuna ROM ha mai salvato. Quelle
        funzioni scrivono negli STESSI 16 byte del chunk pubblico v2: `peak` cade
        su `selvatici`, `exp_pct_idx` su `npc`, la versione torna 1, e i due
        `hits_*` che il chunk v2 conserva di proposito vengono azzerati. Oggi
        nessuno le chiama; `CONTRATTO-D1` §288 però prevede ancora che la pagina
        Opzioni chiami `sgp_state_set_plus`. Nel blob nuovo non esistono più."""
        b = BancoPlus(vecchio("plus"))
        b.carica(STATO, stato_bytes(load=2, guard=0x5A, hits_t=11, hits_w=13,
                                    chunk=chunk_bytes(plus=1, selvatici=0, npc=1,
                                                      wifi=3, picco=57)))
        b.chiama(0x23D8101, (0,))            # sgp_state_reset del blob applicato
        st = b.leggi(STATO, 32)
        self.assertEqual(st[16 + 2], 1, "versione del chunk riscritta a 1")
        self.assertEqual(st[16 + 4], 1, "`peak`=1 è finito su `selvatici`")
        self.assertEqual(struct.unpack("<II", st[8:16]), (0, 0),
                         "i contatori che il chunk v2 conserva sono stati azzerati")
        self.assertNotIn("sgp_state_reset", nuovo("plus")["simboli"])
        self.assertNotIn("sgp_state_set_plus", nuovo("plus")["simboli"])

    # --- Q2.1 -------------------------------------------------------------
    def test_Q2_indici_di_tabella_sempre_un_byte(self):
        """`sgp_trainer_level` e `sgp_wild_level` con argomenti arbitrari su 32
        bit: nessun accesso fuori dalle due tabelle (le pagine intorno restano a
        zero e non c'è mai un'eccezione), e il risultato resta nel dominio."""
        import random
        rnd = random.Random(20260912)
        for quale in BLOB:
            b = BancoPlus(vecchio("plus") if quale == "vecchio" else nuovo("plus"))
            b.stato(active_plus=1, active_wild=1)
            for _ in range(400):
                base = rnd.getrandbits(32)
                r = b.chiama(b.sim("sgp_wild_level"), (base,))[0]
                self.assertTrue(r == base or 1 <= r <= 100, "wild %d -> %d" % (base, r))
                buf = trpoke([rnd.getrandbits(16) for _ in range(6)], 18)
                b.scrivi(WORK, buf)
                tn = rnd.getrandbits(16)
                r = b.chiama(b.sim("sgp_trainer_level"), (base, WORK, tn))[0]
                self.assertTrue(r == base or 1 <= r <= 100,
                                "trainer base=%d tn=%d -> %d" % (base, tn, r))

    # --- Q3 ---------------------------------------------------------------
    def test_Q3_niente_divisione_float_libc(self):
        """Disassembla i quattro blob nuovi: nessuna divisione hardware, nessuna
        istruzione in virgola mobile, e ogni `BL`/`BLX` immediata resta dentro il
        proprio blob (nessun simbolo esterno: non c'è linker)."""
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        md.detail = False
        basi = {"plus": 0x023D8100, "salva": 0x023D8220,
                "npc": 0x023D8900, "wifi": 0x023DA250}
        vietate = ("sdiv", "udiv", "vadd", "vmul", "vldr", "vstr", "vmov", "fmul")
        for nome, base in basi.items():
            byte = nuovo(nome)["byte"]
            fine = base + len(byte)
            for i in md.disasm(byte, base):
                self.assertFalse(i.mnemonic.startswith(vietate),
                                 "%s: %s a %08X" % (nome, i.mnemonic, i.address))
                if i.mnemonic in ("bl", "blx") and i.op_str.startswith("#"):
                    dst = int(i.op_str[1:], 0)
                    self.assertTrue(base <= dst < fine,
                                    "%s: %s fuori dal blob verso %08X" % (nome, i.mnemonic, dst))

    def test_Q3_nessuna_sezione_oltre_text(self):
        """`carica_text.load_text` rifiuta .rodata, simboli esterni e rilocazioni
        diverse dalla BL Thumb interna: se la compilazione è passata, il vincolo
        è rispettato. Qui si controlla solo che non sia rimasto un avviso."""
        for nome in ("plus", "salva", "npc", "wifi"):
            self.assertEqual(nuovo(nome)["manifesto"]["avvisi"], [],
                             "%s: il compilatore ha avvisi" % nome)
