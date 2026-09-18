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
compila_mod = carica_modulo("anim2_compila_metadata", COMPILA)


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

    # ------------------------------------------------------------ A8b A1
    def test_relativo_lascia_intatti_i_flag_e_riduce_i_percorsi(self):
        """A1: la vecchia `relativo()` chiamava `Path(x).resolve()` su ogni
        elemento del comando, flag compresi: da dentro `source/` un flag come
        `-Oz` si risolveva in `source/-Oz`. Deve restare intatto; un percorso
        assoluto dentro il repo diventa relativo; uno fuori si riduce al solo
        nome del file (mai al percorso assoluto intero, che porterebbe la
        cartella personale di chi compila)."""
        self.assertEqual(compila_mod.relativo("-Oz"), "-Oz")
        self.assertEqual(compila_mod.relativo("clang"), "clang")
        dentro = str(compila_mod.SORGENTI / "anim_blob5.c")
        atteso = str((compila_mod.SORGENTI / "anim_blob5.c")
                     .relative_to(compila_mod.REPO))
        self.assertEqual(compila_mod.relativo(dentro), atteso)
        with tempfile.TemporaryDirectory() as td:
            fuori = str(Path(td) / "anim_blob5.o")
            self.assertNotIn(td, compila_mod.relativo(fuori))
            self.assertEqual(compila_mod.relativo(fuori), "anim_blob5.o")

    def test_manifesto_rigenerato_dentro_il_repo_non_porta_percorsi_macchina(self):
        """A1: quando `--uscita` sta dentro il repo, `comando` non deve
        portare ne' la cartella personale di chi compila ne' il nome della
        cartella temporanea di questa prova (solo percorsi relativi al repo,
        o i flag/nomi comando intatti); il blob resta quello spedito.
        Nota: `--uscita` diversa da `source/sgp12/build/anim2` produce
        comunque un `-o` relativo ma non identico a quello spedito (l'ultimo
        pezzo del percorso e' il nome di QUESTA cartella): la verifica di
        identita' con `--uscita source/sgp12/build/anim2` va fatta a mano,
        non da un test che scrive dentro l'albero tracciato da git."""
        out = REPO / "source" / "sgp12" / "build" / "anim2-prova-a1"
        self.addCleanup(shutil.rmtree, out, True)
        subprocess.run([sys.executable, str(COMPILA), "--uscita", str(out)],
                       cwd=str(REPO), check=True, capture_output=True, text=True)
        rigenerato = json.loads((out / "manifesto.json").read_text())
        for arg in rigenerato["comando"]:
            self.assertNotIn(str(REPO), arg, arg)
            self.assertNotIn(str(out), arg, arg)
        spedito = json.loads((BUILD / "manifesto.json").read_text())
        self.assertEqual(rigenerato["blob"]["sha256"], spedito["blob"]["sha256"])

    # ------------------------------------------------------------ A8b B3
    def test_override_esplicito_etichetta_la_variante_come_modificata(self):
        m = self.compila_con("--variante", "V1", "--blink-dur", "20")
        par = m["tabelle_bin"]["par"]
        self.assertEqual(par["variante"], "V1 (modificata)")
        self.assertTrue(par["variante_modificata"])

    def test_variante_senza_override_non_e_etichettata_modificata(self):
        m = self.compila_con("--variante", "V2")
        par = m["tabelle_bin"]["par"]
        self.assertEqual(par["variante"], "V2")
        self.assertFalse(par["variante_modificata"])

    def compila_con(self, *argv):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        subprocess.run([sys.executable, str(COMPILA), "--uscita", td.name, *argv],
                       check=True, capture_output=True, text=True)
        return json.loads((Path(td.name) / "manifesto.json").read_text())

    # ------------------------------------------------------------ A8b B4/B5
    def test_valori_negativi_sono_un_rosso_non_un_traceback(self):
        casi = (
            ["--blink-min", "-1"],
            ["--raro-piu", "-1"],
            # forma `--amp=` perche' argparse (fino a Python 3.13) tratta
            # "-1,3,4,4" come un'opzione, non come un numero negativo
            ["--amp=-1,3,4,4"],
        )
        for argv in casi:
            with self.subTest(argv=" ".join(argv)):
                r = self.esegui(*argv)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("NEGATIVO ROSSO", r.stderr)
                self.assertNotIn("Traceback", r.stderr)

    def test_raro_ogni_sotto_due_e_rosso(self):
        for valore in ("0", "1"):
            with self.subTest(valore=valore):
                r = self.esegui("--raro-ogni", valore)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("RARO ROSSO", r.stderr)

    def test_raro_ogni_due_passa(self):
        self.assertEqual(self.esegui("--raro-ogni", "2").returncode, 0)


class SondaFasiGancioTest(unittest.TestCase):
    """Il default di `--gancio-task` di sonda_fasi.py segue il blob spedito.

    Nasce dall'integrazione 1.2.2: il ramo degli strumenti aveva cablato la
    testa v5c (0x023DB750) proprio mentre il ramo anim2 la spostava a
    0x023DB72C con la v5d. Un default cablato non fa rumore quando invecchia —
    il breakpoint non scatta e la corsa sembra «senza eventi» — quindi il
    valore va letto dal manifesto del blocco, non scritto a mano."""

    def setUp(self):
        self.sonda = carica_modulo("anim2_sonda_fasi",
                                   PACCHETTO / "tools/sonda_fasi.py")
        self.manifesto = json.loads((BUILD / "manifesto.json").read_text())
        # il manifesto scrive i simboli come stringhe ("0x23db72d")
        self.testa = int(self.manifesto["simboli"]["sgp_idle_task5"], 0) & ~1

    def test_default_letto_dal_manifesto_del_blob_spedito(self):
        valore, fonte = self.sonda.gancio_task_default()
        self.assertEqual(fonte, "manifesto")
        self.assertEqual(valore, self.testa)
        # bit Thumb tolto davvero, e non e' piu' la testa v5c
        self.assertEqual(valore & 1, 0)
        self.assertNotEqual(valore, 0x023DB750)

    def test_manifesto_diverso_sposta_il_default(self):
        """Il valore VIENE dal file: cambiato il file, cambia il default."""
        with tempfile.TemporaryDirectory() as td:
            finto = Path(td) / "manifesto.json"
            finto.write_text(json.dumps(
                {"simboli": {"sgp_idle_task5": 0x02345679}}))
            self.assertEqual(self.sonda.gancio_task_default(str(finto)),
                             (0x02345678, "manifesto"))

    def test_senza_manifesto_ripiega_su_un_valore_esplicito(self):
        with tempfile.TemporaryDirectory() as td:
            assente = str(Path(td) / "non-c-e.json")
            valore, fonte = self.sonda.gancio_task_default(assente, avvisa=False)
        self.assertEqual(fonte, "ripiego")
        self.assertEqual(valore, self.sonda.GANCIO_TASK_RIPIEGO)
        self.assertEqual(valore, self.testa)

    def test_la_riga_di_comando_usa_quel_default(self):
        r = subprocess.run(
            [sys.executable, str(PACCHETTO / "tools/sonda_fasi.py"), "--help"],
            capture_output=True, text=True, check=True)
        atteso = "%#010x" % self.testa
        self.assertIn(atteso, r.stdout)
        self.assertNotIn("0x023DB750", r.stdout)


if __name__ == "__main__":
    unittest.main()
