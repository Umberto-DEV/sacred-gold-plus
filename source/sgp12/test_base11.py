#!/usr/bin/env python3
"""Test dello STADIO 0: dalla HeartGold originale alla base 1.1.

Tutti di CLASSE A — nessuna ROM, nessuna rete, nessun `xdelta3` vero. Lo
stadio 0 e' l'unico punto della ricostruzione che esegue un programma esterno
e legge un file che non sta in questo repository, cioe' esattamente il genere
di codice che, senza una ROM in mano, di solito non si prova mai: qui si prova
con un pin sintetico, file finti di pochi byte e un `xdelta3` finto, e a essere
verificato e' il COMPORTAMENTO (riconosco, rifiuto, controllo le impronte), non
il decodificatore.

Uso (da dentro `source/`):
    python3 -m unittest sgp12.test_base11 -v
"""
import functools
import hashlib
import http.server
import json
import os
import shutil
import socketserver
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from . import rom as romlib
from . import scarica_base as scarica_mod
from . import costruisci as costruisci_mod
from .rom import Rifiuto

PIN = romlib.carica_pin()


def _sha(d):
    return hashlib.sha256(d).hexdigest()


# ---------------------------------------------------------------- il pin vero

class TestPinBase11(unittest.TestCase):
    """Il pin tracciato descrive due tratte complete e plausibili. Se un giorno
    qualcuno ci mette uno sha troncato o un conteggio di byte a occhio, e' qui
    che si ferma, non alla prima ricostruzione su una macchina altrui."""

    def test_due_lingue_con_tutte_le_sezioni(self):
        self.assertEqual(sorted(PIN["basi"]), ["EN", "IT"])
        for lingua, voce in PIN["basi"].items():
            for parte in ("originale", "delta", "base_1_1"):
                self.assertIn(parte, voce, "%s/%s" % (lingua, parte))
                self.assertIn("nome", voce[parte])

    def test_impronte_esadecimali_di_64_caratteri(self):
        for lingua, voce in PIN["basi"].items():
            for parte in ("originale", "delta", "base_1_1"):
                s = voce[parte]["sha256"]
                self.assertRegex(s, r"^[0-9a-f]{64}$", "%s/%s: %r" % (lingua, parte, s))

    def test_dimensioni_plausibili(self):
        """Una HeartGold e una base 1.1 sono cartucce da decine di MB; un delta
        e' un file di differenze, molto piu' piccolo del suo bersaglio."""
        for lingua, voce in PIN["basi"].items():
            self.assertTrue(64 << 20 <= voce["originale"]["byte"] <= 256 << 20,
                            "%s: originale di %d B" % (lingua, voce["originale"]["byte"]))
            self.assertTrue(64 << 20 <= voce["base_1_1"]["byte"] <= 256 << 20,
                            "%s: base 1.1 di %d B" % (lingua, voce["base_1_1"]["byte"]))
            self.assertTrue(1024 <= voce["delta"]["byte"] < voce["base_1_1"]["byte"],
                            "%s: delta di %d B" % (lingua, voce["delta"]["byte"]))

    def test_impronte_tutte_distinte(self):
        viste = [voce[parte]["sha256"] for voce in PIN["basi"].values()
                 for parte in ("originale", "delta", "base_1_1")]
        self.assertEqual(len(viste), len(set(viste)), "due voci del pin hanno lo stesso sha256")

    def test_url_dei_delta_sotto_la_release_dichiarata(self):
        for lingua, voce in PIN["basi"].items():
            self.assertEqual(voce["delta"]["url"], PIN["url_base"] + voce["delta"]["nome"],
                             "%s: l'URL del delta non e' url_base + nome" % lingua)
            self.assertIn("/releases/download/" + PIN["release"] + "/", voce["delta"]["url"])

    def test_opzioni_di_decodifica_quelle_del_manifest_1_1(self):
        self.assertEqual(PIN["decode_options"], ["-d", "-D", "-R", "-s"])
        self.assertEqual(PIN["encode_options"], ["-e", "-A", "-S", "none", "-D", "-s"])

    def test_il_pin_vero_passa_la_propria_verifica(self):
        self.assertIs(romlib.verifica_pin(PIN), PIN)


class TestPinMalformato(unittest.TestCase):
    """`verifica_pin` e' strutturale: rifiuta un pin che non descrive niente."""

    def _guasto(self, muta):
        pin = json.loads(json.dumps(PIN))
        muta(pin)
        with self.assertRaises(Rifiuto) as c:
            romlib.verifica_pin(pin)
        return str(c.exception)

    def test_sezione_mancante(self):
        self.assertIn("delta", self._guasto(lambda p: p["basi"]["EN"].pop("delta")))

    def test_sha_troncato(self):
        m = self._guasto(lambda p: p["basi"]["IT"]["originale"].update(sha256="0123abcd"))
        self.assertIn("64 caratteri", m)

    def test_sha_non_esadecimale(self):
        self._guasto(lambda p: p["basi"]["EN"]["delta"].update(sha256="z" * 64))

    def test_byte_non_intero_positivo(self):
        self.assertIn("byte", self._guasto(lambda p: p["basi"]["EN"]["base_1_1"].update(byte=0)))

    def test_url_non_https(self):
        self.assertIn("url", self._guasto(
            lambda p: p["basi"]["IT"]["delta"].update(url="file:///tmp/delta.xdelta")))

    def test_senza_basi(self):
        self.assertIn("basi", self._guasto(lambda p: p.pop("basi")))


# ------------------------------------------------------- riconoscere una base

class TestClassificaBase(unittest.TestCase):
    """Funzione pura: dato uno sha256, che ROM e'. Nessun file aperto."""

    def test_le_due_heartgold_originali(self):
        for lingua in ("EN", "IT"):
            c = romlib.classifica_base(PIN["basi"][lingua]["originale"]["sha256"], PIN)
            self.assertEqual((c["tipo"], c["lingua"]), ("originale", lingua))

    def test_le_due_basi_1_1(self):
        for lingua in ("EN", "IT"):
            c = romlib.classifica_base(PIN["basi"][lingua]["base_1_1"]["sha256"], PIN)
            self.assertEqual((c["tipo"], c["lingua"]), ("base-1.1", lingua))

    def test_sconosciuta(self):
        for s in ("", None, "0" * 64, _sha(b"una ROM qualunque")):
            c = romlib.classifica_base(s, PIN)
            self.assertEqual((c["tipo"], c["lingua"]), ("sconosciuta", None), s)

    def test_maiuscole_e_spazi_non_cambiano_il_verdetto(self):
        s = PIN["basi"]["EN"]["originale"]["sha256"]
        c = romlib.classifica_base("  " + s.upper() + "\n", PIN)
        self.assertEqual((c["tipo"], c["lingua"]), ("originale", "EN"))

    def test_la_1_2_2_non_e_una_base(self):
        """Le ROM finite non sono basi: `--base sgp-1.2.2-EN.nds` deve essere
        una ROM sconosciuta, non un punto di partenza accettato."""
        self.assertEqual(romlib.classifica_base(
            "03e32bc9aed7aa53188145ab802c0ab0567abc8e3d97f8607464aacc21146762", PIN)["tipo"],
            "sconosciuta")


# --------------------------------------------------- lo stadio 0, senza ROM

ORIGINALE = {"EN": b"HEARTGOLD-US-FINTA;" * 64, "IT": b"HEARTGOLD-IT-FINTA;" * 64}
DELTA = {"EN": b"DELTA-EN;" * 8, "IT": b"DELTA-IT;" * 8}
BASE11 = {"EN": b"BASE-1.1-EN-FINTA;" * 32, "IT": b"BASE-1.1-IT-FINTA;" * 32}

FINTO_XDELTA = """import os, shutil, sys
codice = int(os.environ.get("SGP_FINTO_CODICE", "0"))
if codice:
    sys.stderr.write("finto xdelta3: fallimento richiesto\\n")
    raise SystemExit(codice)
shutil.copyfile(os.environ["SGP_FINTO_USCITA"], sys.argv[-1])
"""


class BancoStadio0(unittest.TestCase):
    """Un pin sintetico, file di pochi byte e un `xdelta3` finto: lo stadio 0
    gira per intero (sottoprocesso compreso) senza una ROM e senza xdelta3."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="sgp12-prova-stadio0-"))
        self.addCleanup(shutil.rmtree, self.d, True)
        self.roms = self.d / "roms"
        self.roms.mkdir()
        self.pin = {
            "schema": 1, "release": "base-1.1-prova",
            "url_base": "https://esempio.invalido/base-1.1/",
            "encode_options": PIN["encode_options"], "decode_options": PIN["decode_options"],
            "basi": {},
        }
        for lingua in ("EN", "IT"):
            (self.d / ("originale-%s.nds" % lingua)).write_bytes(ORIGINALE[lingua])
            (self.d / ("base-1.1-%s.nds" % lingua)).write_bytes(BASE11[lingua])
            (self.roms / ("base-1.1-%s.xdelta" % lingua)).write_bytes(DELTA[lingua])
            self.pin["basi"][lingua] = {
                "originale": {"nome": "originale-%s.nds" % lingua, "etichetta": "Finta %s" % lingua,
                              "sha256": _sha(ORIGINALE[lingua]), "byte": len(ORIGINALE[lingua])},
                "delta": {"nome": "base-1.1-%s.xdelta" % lingua,
                          "url": "https://esempio.invalido/base-1.1/base-1.1-%s.xdelta" % lingua,
                          "sha256": _sha(DELTA[lingua]), "byte": len(DELTA[lingua])},
                "base_1_1": {"nome": "base-1.1-%s.nds" % lingua, "etichetta": "Base finta %s" % lingua,
                             "sha256": _sha(BASE11[lingua]), "byte": len(BASE11[lingua])},
            }
        romlib.verifica_pin(self.pin)

        finto = self.d / "finto-xdelta3"
        finto.write_text("#!%s\n%s" % (sys.executable, FINTO_XDELTA))
        finto.chmod(finto.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        self.finto = finto
        self.amb = mock.patch.dict(os.environ, {
            "SGP_XDELTA3": str(finto),
            "SGP_FINTO_USCITA": str(self.d / "base-1.1-EN.nds"),
            "SGP_ROM_DIR": str(self.roms)}, clear=False)
        self.amb.start()
        self.addCleanup(self.amb.stop)
        os.environ.pop("SGP_FINTO_CODICE", None)


class TestStadio0(BancoStadio0):

    def test_dalla_originale_alla_base_1_1(self):
        fuori, rap = romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin)
        self.assertEqual(fuori, BASE11["EN"])
        self.assertTrue(rap["eseguito"])
        self.assertEqual(rap["lingua"], "EN")
        self.assertEqual(rap["base_originale"]["sha256"], _sha(ORIGINALE["EN"]))
        self.assertEqual(rap["delta"]["nome"], "base-1.1-EN.xdelta")
        self.assertEqual(rap["base_1_1"]["sha256"], _sha(BASE11["EN"]))
        self.assertEqual(rap["xdelta3"]["opzioni"], ["-d", "-D", "-R", "-s"])

    def test_lingua_dedotta_dallo_sha_non_dal_nome(self):
        """Il nome del file dice EN, i byte dicono IT: vince lo sha256."""
        bugiardo = self.d / "base-1.1-EN-bugiardo.nds"
        bugiardo.write_bytes(ORIGINALE["IT"])
        os.environ["SGP_FINTO_USCITA"] = str(self.d / "base-1.1-IT.nds")
        fuori, rap = romlib.prepara_base(bugiardo, None, pin=self.pin)
        self.assertEqual(rap["lingua"], "IT")
        self.assertEqual(fuori, BASE11["IT"])

    def test_base_1_1_fornita_direttamente_salta_lo_stadio_0(self):
        fuori, rap = romlib.prepara_base(self.d / "base-1.1-IT.nds", None, pin=self.pin)
        self.assertEqual(fuori, BASE11["IT"])
        self.assertEqual(rap["saltato"], "base 1.1 fornita direttamente")
        self.assertIn("AVVISO", rap["avviso"])
        self.assertEqual(rap["lingua"], "IT")
        self.assertNotIn("delta", rap)

    def test_sha_sconosciuto_rifiutato_con_l_elenco_di_cio_che_e_accettato(self):
        ignota = self.d / "ignota.nds"
        ignota.write_bytes(b"non sono una HeartGold")
        with self.assertRaises(Rifiuto) as c:
            romlib.prepara_base(ignota, None, pin=self.pin)
        m = str(c.exception)
        self.assertIn("non e' riconosciuta", m)
        self.assertIn(self.pin["basi"]["EN"]["originale"]["sha256"][:16], m)
        self.assertIn(self.pin["basi"]["IT"]["originale"]["sha256"][:16], m)
        self.assertIn(self.pin["basi"]["EN"]["base_1_1"]["sha256"][:16], m)

    def test_lingua_chiesta_diversa_da_quella_della_rom(self):
        with self.assertRaises(Rifiuto) as c:
            romlib.prepara_base(self.d / "originale-EN.nds", "IT", pin=self.pin)
        self.assertIn("--lingua IT", str(c.exception))

    def test_senza_xdelta3_rifiuto_con_le_istruzioni_di_installazione(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(romlib.shutil, "which", return_value=None):
            with self.assertRaises(Rifiuto) as c:
                romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin,
                                    delta=self.roms / "base-1.1-EN.xdelta")
        m = str(c.exception)
        self.assertIn("brew install xdelta", m)
        self.assertIn("apt install xdelta3", m)

    def test_delta_con_sha_diverso_rifiutato(self):
        (self.roms / "base-1.1-EN.xdelta").write_bytes(DELTA["EN"] + b"guasto")
        with self.assertRaises(Rifiuto) as c:
            romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin)
        self.assertIn("non e' il delta che il pin dichiara", str(c.exception))

    def test_delta_assente_indica_scarica_base(self):
        (self.roms / "base-1.1-EN.xdelta").unlink()
        with self.assertRaises(Rifiuto) as c:
            romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin)
        m = str(c.exception)
        self.assertIn("sgp12.scarica_base", m)
        self.assertIn("base-1.1-EN.xdelta", m)

    def test_delta_esplicito_ha_la_precedenza(self):
        altrove = self.d / "altrove.xdelta"
        altrove.write_bytes(DELTA["EN"])
        (self.roms / "base-1.1-EN.xdelta").unlink()
        _, rap = romlib.prepara_base(self.d / "originale-EN.nds", None, delta=altrove, pin=self.pin)
        self.assertEqual(rap["delta"]["percorso"], str(altrove))

    def test_uscita_con_sha_diverso_rifiutata(self):
        """Il decodificatore ha funzionato ma non ha prodotto la base attesa:
        la catena si ferma qui, non ai blocchi."""
        os.environ["SGP_FINTO_USCITA"] = str(self.d / "base-1.1-IT.nds")
        with self.assertRaises(Rifiuto) as c:
            romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin)
        self.assertIn("non e' quella del pin", str(c.exception))

    def test_xdelta3_che_fallisce_diventa_un_rifiuto_con_il_suo_stderr(self):
        os.environ["SGP_FINTO_CODICE"] = "3"
        with self.assertRaises(Rifiuto) as c:
            romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin)
        m = str(c.exception)
        self.assertIn("xdelta3 ha rifiutato", m)
        self.assertIn("fallimento richiesto", m)

    def test_nessun_file_temporaneo_lasciato_indietro(self):
        prima = set(Path(tempfile.gettempdir()).glob("sgp12-stadio0-*"))
        romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin)
        self.assertEqual(set(Path(tempfile.gettempdir()).glob("sgp12-stadio0-*")), prima)


class TestCostruisciRifiutaUnaBaseSconosciuta(BancoStadio0):
    """Il comando, non la libreria: `costruisci --base <ROM ignota>` deve
    uscire 2 con un RIFIUTO, senza scrivere niente e senza traceback."""

    def test_uscita_2_e_nessun_file_scritto(self):
        ignota = self.d / "ignota.nds"
        ignota.write_bytes(b"non sono una HeartGold")
        uscita = self.d / "mai-scritta.nds"
        codice = costruisci_mod.main(["--base", str(ignota), "--uscita", str(uscita)])
        self.assertEqual(codice, 2)
        self.assertFalse(uscita.exists())


# ------------------------------------------------------------- scarica_base

class _SenzaDNS(http.server.ThreadingHTTPServer):
    """`HTTPServer.server_bind` chiama `socket.getfqdn(host)` per riempire un
    campo che a questo test non serve. Su macOS senza responder mDNS quella
    risoluzione inversa di `127.0.0.1` costa decine di secondi al primo test
    della suite (misurato: 35 s). Qui si salta, e il banco torna sotto il
    secondo — un test lento e' un test che si comincia a non eseguire."""

    def server_bind(self):
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]


class ServitoreFinto:
    """Un `http.server` su localhost che serve una cartella. Nessuna rete
    esterna: e' un socket su 127.0.0.1, chiuso alla fine del test."""

    def __init__(self, cartella):
        gestore = functools.partial(_Silenzioso, directory=str(cartella))
        self.httpd = _SenzaDNS(("127.0.0.1", 0), gestore)
        self.url = "http://127.0.0.1:%d/" % self.httpd.server_address[1]
        self.t = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.01},
                                  daemon=True)
        self.t.start()

    def chiudi(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.t.join(timeout=5)


class _Silenzioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class TestScaricaBase(BancoStadio0):

    def setUp(self):
        super().setUp()
        self.sito = self.d / "sito"
        self.sito.mkdir()
        self.dest = self.d / "scaricati"
        self.dest.mkdir()
        self._pubblica()
        self.server = ServitoreFinto(self.sito)
        self.addCleanup(self.server.chiudi)

    def _pubblica(self, guasta=None, sha256sums=None):
        righe = []
        for lingua in ("EN", "IT"):
            corpo = DELTA[lingua] + (b"-guasto" if guasta == lingua else b"")
            nome = self.pin["basi"][lingua]["delta"]["nome"]
            (self.sito / nome).write_bytes(corpo)
            righe.append("%s  %s" % (self.pin["basi"][lingua]["delta"]["sha256"], nome))
        (self.sito / "SHA256SUMS").write_text(sha256sums if sha256sums is not None
                                              else "\n".join(righe) + "\n")

    def test_scarica_verifica_e_deposita(self):
        rap = scarica_mod.scarica(self.dest, pin=self.pin, url_base=self.server.url)
        self.assertEqual([f["esito"] for f in rap["file"]], ["scaricato", "scaricato"])
        for lingua in ("EN", "IT"):
            p = self.dest / self.pin["basi"][lingua]["delta"]["nome"]
            self.assertEqual(p.read_bytes(), DELTA[lingua])
        self.assertTrue((self.dest / scarica_mod.SHA256SUMS_DEPOSITO).is_file())

    def test_non_scrive_sopra_il_sha256sums_delle_rom(self):
        """`$SGP_ROM_DIR/SHA256SUMS` e' gia' l'elenco delle ROM che
        `sgp12/test_lib.py` legge. L'elenco dei delta va accanto, non sopra."""
        gia_li = self.dest / "SHA256SUMS"
        gia_li.write_text("%s  sgp-1.2.2-EN.nds\n" % ("c" * 64))
        scarica_mod.scarica(self.dest, pin=self.pin, url_base=self.server.url)
        self.assertIn("sgp-1.2.2-EN.nds", gia_li.read_text())
        self.assertIn("base-1.1-EN.xdelta",
                      (self.dest / scarica_mod.SHA256SUMS_DEPOSITO).read_text())

    def test_seconda_corsa_non_riscarica(self):
        scarica_mod.scarica(self.dest, pin=self.pin, url_base=self.server.url)
        rap = scarica_mod.scarica(self.dest, pin=self.pin, url_base=self.server.url)
        self.assertEqual([f["esito"] for f in rap["file"]], ["gia presente", "gia presente"])

    def test_file_guasto_rifiutato_e_cancellato(self):
        self._pubblica(guasta="IT")
        with self.assertRaises(Rifiuto) as c:
            scarica_mod.scarica(self.dest, pin=self.pin, url_base=self.server.url)
        self.assertIn("CANCELLATO", str(c.exception))
        self.assertFalse((self.dest / self.pin["basi"]["IT"]["delta"]["nome"]).exists())
        self.assertEqual(list(self.dest.glob("*.parziale")), [])

    def test_sha256sums_che_contraddice_il_pin_ferma_tutto(self):
        self._pubblica(sha256sums="%s  %s\n" % ("a" * 64, self.pin["basi"]["EN"]["delta"]["nome"]))
        with self.assertRaises(Rifiuto) as c:
            scarica_mod.scarica(self.dest, ["EN"], pin=self.pin, url_base=self.server.url)
        self.assertIn("il pin tracciato dice", str(c.exception))
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()), [],
                         "un SHA256SUMS che contraddice il pin non deve lasciare niente")

    def test_sha256sums_che_non_nomina_il_delta(self):
        self._pubblica(sha256sums="%s  altro-file.bin\n" % ("b" * 64))
        with self.assertRaises(Rifiuto) as c:
            scarica_mod.scarica(self.dest, ["EN"], pin=self.pin, url_base=self.server.url)
        self.assertIn("non nomina", str(c.exception))

    def test_una_lingua_sola(self):
        rap = scarica_mod.scarica(self.dest, ["IT"], pin=self.pin, url_base=self.server.url)
        self.assertEqual([f["lingua"] for f in rap["file"]], ["IT"])
        self.assertFalse((self.dest / self.pin["basi"]["EN"]["delta"]["nome"]).exists())

    def test_destinazione_inesistente(self):
        with self.assertRaises(Rifiuto):
            scarica_mod.scarica(self.d / "non-esiste", pin=self.pin, url_base=self.server.url)

    def test_errore_di_rete_non_lascia_un_parziale(self):
        """`apri` sostituito: la connessione salta a meta' del corpo."""
        vero = scarica_mod._apri

        class Monco:
            def __init__(self, dentro):
                self.dentro = dentro
                self.primo = True

            def read(self, n=-1):
                if self.primo:
                    self.primo = False
                    return self.dentro.read(4)
                raise OSError("connessione interrotta")

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def apri(url):
            risposta = vero(url)
            if url.endswith("SHA256SUMS"):
                return risposta
            return Monco(risposta)

        with self.assertRaises(Rifiuto) as c:
            scarica_mod.scarica(self.dest, ["EN"], pin=self.pin, url_base=self.server.url, apri=apri)
        self.assertIn("scaricamento fallito", str(c.exception))
        self.assertEqual(list(self.dest.glob("*.xdelta*")), [])

    def test_lo_stadio_0_usa_quello_che_scarica_base_ha_deposto(self):
        """Le due meta' combaciano: `scarica_base` mette in `$SGP_ROM_DIR` un
        file con il nome e lo sha che `prepara_base` andra' a cercare."""
        scarica_mod.scarica(self.dest, pin=self.pin, url_base=self.server.url)
        fuori, rap = romlib.prepara_base(self.d / "originale-EN.nds", None, pin=self.pin,
                                         cartella=self.dest)
        self.assertEqual(fuori, BASE11["EN"])
        self.assertEqual(rap["delta"]["percorso"],
                         str(self.dest / "base-1.1-EN.xdelta"))


class TestAnalizzaSha256sums(unittest.TestCase):

    def test_formato_di_shasum(self):
        d = scarica_mod.analizza_sha256sums("%s  a.xdelta\n%s *b.xdelta\n" % ("a" * 64, "b" * 64))
        self.assertEqual(d, {"a.xdelta": "a" * 64, "b.xdelta": "b" * 64})

    def test_riga_senza_nome(self):
        with self.assertRaises(Rifiuto):
            scarica_mod.analizza_sha256sums("a" * 64 + "\n")

    def test_impronta_non_valida(self):
        with self.assertRaises(Rifiuto):
            scarica_mod.analizza_sha256sums("non-uno-sha  a.xdelta\n")

    def test_vuoto(self):
        with self.assertRaises(Rifiuto):
            scarica_mod.analizza_sha256sums("\n\n")


if __name__ == "__main__":
    unittest.main()
