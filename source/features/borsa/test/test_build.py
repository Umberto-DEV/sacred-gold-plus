#!/usr/bin/env python3
"""Classe A: manifesto portabile e coerente con gli artefatti spediti."""
import hashlib
import json
import unittest
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
REPO = FEATURE.parents[2]
BUILD = REPO / "source" / "sgp12" / "build" / "borsa"


class ProveBuildPubblico(unittest.TestCase):
    def test_manifesto_portabile_e_artefatti_coerenti(self):
        sha = lambda b: hashlib.sha256(b).hexdigest()
        man = json.loads((BUILD / "manifesto.json").read_text())
        comando = " ".join(man["comando"])
        self.assertNotIn(str(REPO), comando)
        self.assertNotIn("local/", comando)
        self.assertEqual(man["indirizzi"]["originali"], "0x23db2e0")
        self.assertEqual(man["indirizzi"]["staffetta"], "0x23db2f0")
        self.assertEqual(man["blob"]["byte"], len((BUILD / "blob.bin").read_bytes()))
        self.assertEqual(man["blob"]["sha256"], sha((BUILD / "blob.bin").read_bytes()))
        self.assertEqual(man["canarino"]["sha256"],
                         sha((BUILD / "canarino.bin").read_bytes()))
        self.assertEqual(man["sorgente"]["sha256"],
                         sha((FEATURE / "sorgenti" / "borsa.c").read_bytes()))
        self.assertEqual(man["intestazione"]["sha256"],
                         sha((FEATURE / "sorgenti" / "sgp_borsa.h").read_bytes()))


if __name__ == "__main__":
    unittest.main()
