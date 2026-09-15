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
