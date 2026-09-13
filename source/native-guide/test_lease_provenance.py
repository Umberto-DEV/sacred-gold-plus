import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_fixtures
import run_lease_probe as runner


def tearDownModule():
    test_fixtures.cleanup()


class LeaseProvenance(unittest.TestCase):
    def test_stale_source_manifest_is_rejected_before_execution(self):
        self.assertTrue(hasattr(runner,'current_build'),'Runtime does not bind build to current source')
        rom, build_json = test_fixtures.lease_build(self)
        meta=json.loads(build_json.read_text())
        meta['source_sha256']['lease.c']='0'*64
        with tempfile.TemporaryDirectory() as d:
            changed=Path(d)/'build.json';changed.write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError,'Stale build source: lease.c'):
                runner.current_build(changed,rom)

if __name__=='__main__': unittest.main()
