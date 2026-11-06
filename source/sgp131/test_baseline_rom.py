"""Class B: verify immutable V4 EN/IT baseline composition entirely in memory.

Set SGP131_BASE_EN / SGP131_BASE_IT to the existing verified originals. Set
SGP131_REQUIRE_INPUTS=1 for an explicit campaign: missing inputs then fail.
Ordinary discovery reports one clear skip per absent language. No generated
ROM, workbench slot, emulator, extracted resource or original file is written.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from . import baseline, build, evidence


V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}


def _hash_original(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


class RealBaselineTests(unittest.TestCase):
    def _check_language(self, language):
        variable = 'SGP131_BASE_' + language
        configured = os.environ.get(variable)
        if not configured:
            message = variable + ' is required for the real V4 baseline check'
            if os.environ.get('SGP131_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message + '; set SGP131_REQUIRE_INPUTS=1 to require both inputs')
        path = Path(configured)
        self.assertTrue(path.is_file(), variable + ' must identify an existing original file')
        expected, size = V4[language]
        before = _hash_original(path)
        self.assertEqual(before, expected, 'only the immutable verified V4 input is admitted')
        self.assertEqual(path.stat().st_size, size)
        sources = build.source_snapshot()
        try:
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), before)
            self.assertEqual(baseline.identify(data), language)
            with tempfile.TemporaryDirectory(prefix='sgp131-baseline-readback-') as directory:
                scratch = Path(directory)
                payload, report = build.compose(data, 'baseline', scratch / 'unused-charmap', scratch / 'unused')
                self.assertEqual(payload, data)
                self.assertEqual(report['input_sha256'], expected)
                self.assertEqual(report['output_sha256'], expected)
                self.assertEqual(report['output_bytes'], size)
                self.assertEqual(report['language'], language)
                self.assertEqual(report['source_sha256'], sources)
                self.assertEqual(build.verify_composition(data, payload, report['receipts']), report['composition'])
                evidence.validate_provenance(report)
                self.assertEqual(list(scratch.iterdir()), [], 'baseline must leave no scratch or output files')
            self.assertEqual(build.source_snapshot(), sources)
        finally:
            self.assertEqual(_hash_original(path), before, 'original input changed during read-only composition')
        print(json.dumps({'language': language, 'input_bytes': size,
                          'input_before_sha256': before, 'input_after_sha256': before,
                          'output_sha256': report['output_sha256'], 'byte_identical': True,
                          'source_snapshot_sha256': hashlib.sha256(
                              json.dumps(sources, sort_keys=True).encode()).hexdigest(),
                          'sources_unchanged': True, 'scratch_empty': True,
                          'rom_output_files_written': 0}, sort_keys=True))

    def test_en_v4_baseline_in_memory(self):
        self._check_language('EN')

    def test_it_v4_baseline_in_memory(self):
        self._check_language('IT')
