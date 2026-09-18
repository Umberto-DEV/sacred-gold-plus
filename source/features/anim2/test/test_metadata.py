#!/usr/bin/env python3
"""Regressioni del contratto di build di ``sgp.anim2``."""
import json
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACCHETTO = Path(__file__).resolve().parents[1]
REPO = PACCHETTO.parents[2]
COMPILA = PACCHETTO / "tools" / "compila_anim2.py"
BUILD = REPO / "source/sgp12/build/anim2"


def carica_modulo(nome, path):
    spec = importlib.util.spec_from_file_location(nome, path)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


applicatore = carica_modulo("anim2_applicatore_metadata", PACCHETTO / "tools/applica_anim2.py")


class CompilaAnim5Test(unittest.TestCase):
    def compila(self, livello):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        subprocess.run(
            [sys.executable, str(COMPILA), "--uscita", td.name, "--livello", livello],
            check=True, capture_output=True, text=True,
        )
        return json.loads((Path(td.name) / "manifesto.json").read_text())

    def test_5c_tiene_vivi_i_menu_e_non_estende_il_teardown(self):
        """Cattura l'allargamento accidentale della lista di soppressione."""
        m = self.compila("5c")
        self.assertEqual(
            m["politica"]["soppressi"],
            ["IO-BARRA", "IO-SCHERMO-BASSO", "BORSA", "SQUADRA",
             "CONFERMA-MOSSA", "BERSAGLIO", "SI-NO"],
        )
        self.assertEqual(
            m["politica"]["estesi"],
            [],
        )

    def test_build_rifiuta_la_soppressione_della_distruzione(self):
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(
                [sys.executable, str(COMPILA), "--uscita", td, "--sopprimi", "1"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("R3 ROSSO", r.stderr)

    def test_build_rifiuta_scale_che_farebbero_sospendere_il_proprio_moto(self):
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run(
                [sys.executable, str(COMPILA), "--uscita", td,
                 "--sca", "9,9,9,9"], capture_output=True, text=True,
            )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("SCALA ROSSO", r.stderr)

    def esegui(self, *argv):
        with tempfile.TemporaryDirectory() as td:
            return subprocess.run(
                [sys.executable, str(COMPILA), "--uscita", td, *argv],
                capture_output=True, text=True,
            )

    def test_i_cinque_cancelli_dell_accento_bloccano_i_valori_che_si_rompono(self):
        """A1 §3.2 B1/B2/B4 e A8b M3: cinque parametri che il compilatore
        accettava in silenzio e che a runtime davano troncamenti in u8,
        sottrazioni in underflow, maschere a buchi e letture fuori tabella.
        Sono controlli Python: costano zero byte di ROM."""
        casi = (
            (["--blink-dur", "0"], "BLINK ROSSO"),          # B2: (u8)(0-1) = 255 tick
            (["--blink-min", "200", "--blink-mask", "63"], "BLINK ROSSO"),  # B1: 263 -> 7
            (["--blink-mask", "100"], "BLINK ROSSO"),       # B4: maschera non 2^n-1
            (["--fase", "200,200,200,200"], "FASE ROSSO"),  # M3: idx fuori tab_u
            (["--blink-dur", "250", "--raro-piu", "10"], "BLINK ROSSO"),   # blink_left tronca
        )
        for argv, marchio in casi:
            with self.subTest(argv=" ".join(argv)):
                r = self.esegui(*argv)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn(marchio, r.stderr)

    def test_i_valori_spediti_passano_tutti_i_cancelli(self):
        self.assertEqual(self.esegui().returncode, 0)
        for variante in ("V1", "V2", "V3"):
            with self.subTest(variante=variante):
                self.assertEqual(self.esegui("--variante", variante).returncode, 0)

    def test_le_tre_varianti_cambiano_solo_i_parametri(self):
        """V1/V2/V3 sono tarature, non codice: stesso blob, par.bin diverso."""
        manifesti = {}
        for variante in ("V1", "V2", "V3"):
            td = tempfile.TemporaryDirectory()
            self.addCleanup(td.cleanup)
            subprocess.run([sys.executable, str(COMPILA), "--uscita", td.name,
                            "--variante", variante], check=True, capture_output=True)
            manifesti[variante] = json.loads(
                (Path(td.name) / "manifesto.json").read_text())
        blob = {m["blob"]["sha256"] for m in manifesti.values()}
        self.assertEqual(len(blob), 1, "le varianti non condividono il blob")
        par = {v: m["tabelle_bin"]["par"] for v, m in manifesti.items()}
        self.assertEqual(len({p["sha256"] for p in par.values()}), 3)
        self.assertEqual([par["V1"]["blink_dur"], par["V1"]["raro_piu"]], [10, 5])
        self.assertEqual([par["V2"]["blink_dur"], par["V2"]["raro_piu"]], [15, 5])
        self.assertEqual([par["V3"]["blink_dur"], par["V3"]["raro_piu"]], [30, 0])
        for v, pv in par.items():
            self.assertEqual([pv["blink_min"], pv["blink_mask"]], [120, 127], v)

    def test_i_valori_spediti_sono_la_variante_V1(self):
        """Il default del compilatore e' la taratura spedita in build/anim2."""
        m = json.loads((BUILD / "manifesto.json").read_text())
        par = m["tabelle_bin"]["par"]
        self.assertEqual(
            [par["blink_dur"], par["raro_piu"], par["blink_min"], par["blink_mask"]],
            [10, 5, 120, 127])
        self.assertEqual(par["variante"], "V1")

    def copia_build(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        destinazione = Path(td.name)
        for nome in ("manifesto.json", "blob.bin", "canarino.bin", "tab_u.bin",
                     "par.bin", "siti.bin"):
            shutil.copy2(BUILD / nome, destinazione / nome)
        return destinazione

    def test_applicatore_accetta_il_bundle_spedito(self):
        manifesto, parti = applicatore.carica_build(BUILD)
        self.assertEqual(int(manifesto["indirizzi"]["base"], 16), applicatore.BASE)
        self.assertEqual(set(parti),
                         {"blob.bin", "canarino.bin", "tab_u.bin", "par.bin", "siti.bin"})

    def test_applicatore_rifiuta_ogni_artefatto_diverso_dal_manifesto(self):
        for nome in ("blob.bin", "canarino.bin", "tab_u.bin", "par.bin", "siti.bin"):
            with self.subTest(nome=nome):
                build = self.copia_build()
                dati = bytearray((build / nome).read_bytes())
                dati[0] ^= 1
                (build / nome).write_bytes(dati)
                with self.assertRaisesRegex(applicatore.Rifiuto, nome):
                    applicatore.carica_build(build)

    def test_applicatore_rifiuta_indirizzi_e_simboli_fuori_contratto(self):
        mutanti = (
            ("indirizzo stato", lambda m: m["indirizzi"].__setitem__("stato", "0x23dbba4")),
            ("simbolo fuori blob", lambda m: m["simboli"].__setitem__(
                "sgp_idle_task5", "0x01000001")),
            ("simbolo ARM", lambda m: m["simboli"].__setitem__(
                "sgp_stop_politica", "0x23db644")),
            ("gancio incompatibile", lambda m: m["ancore_del_gioco"].__setitem__(
                "G1_letterale_task", "ov012 0x02262010")),
        )
        for nome, guasta in mutanti:
            with self.subTest(nome=nome):
                build = self.copia_build()
                manifesto = json.loads((build / "manifesto.json").read_text())
                guasta(manifesto)
                (build / "manifesto.json").write_text(json.dumps(manifesto))
                with self.assertRaises(applicatore.Rifiuto):
                    applicatore.carica_build(build)


if __name__ == "__main__":
    unittest.main()
