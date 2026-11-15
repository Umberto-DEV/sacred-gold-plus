"""Pure replay of private exact-input observations; never starts a guest CPU."""
from pathlib import Path
import copy, gc, gzip, importlib.util, json, mmap, os, unittest

SOURCE = Path(__file__).resolve().parents[3]
ENV = ('SGP_FS_INIT_ROM_DIR', 'SGP_FS_INIT_REPORT_DIR', 'SGP_REMATCH_OBJECT_DIR', 'SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k) for k in ENV), 'requires private exact ROMs, objects and Init reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = SOURCE / 'features/trainer-strategy/tools/attribuisci_fs_init.py'
        spec = importlib.util.spec_from_file_location('fs_init_replay', path)
        cls.z = z = importlib.util.module_from_spec(spec); spec.loader.exec_module(z)
        cls.reports, cls.data, cls.q = {}, {}, {}
        for language in os.environ.get('SGP_FS_INIT_LANGUAGES', 'EN,IT').split(','):
            rom = Path(os.environ[ENV[0]]) / ('r4-' + language + '.nds')
            model = z.P.G.S.SHARED.read_current(rom, language)
            with rom.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as raw:
                cls.q[language], _ = z.qualify(model, raw, language,
                    Path(os.environ[ENV[2]]) / ('public-build-' + language),
                    Path(os.environ[ENV[3]]) / ('build-' + language) / 'teams.o')
                cls.data[language] = z.resources(model, raw, language)
            path = Path(os.environ[ENV[1]]) / ('fs-init-' + language + '.json.gz')
            cls.reports[language] = json.loads(gzip.decompress(path.read_bytes()))
            del model; gc.collect()

    def base(self):
        language = next(iter(self.reports))
        return language, copy.deepcopy(self.reports[language]['positives'][0])

    def require(self, language, record):
        self.z.require_case(record, self.data[language], self.q[language])

    def test_all_positive_guard_and_clobber_observations(self):
        for language, report in self.reports.items():
            self.assertEqual(report['source_sha256'], self.z.source_identities())
            self.assertEqual(len(report['positives']) + len(report['guards']) + len(report['volatile_controls']) +
                             len(report['observer_off']) + len(report['counters']), 10)
            for record in report['positives'] + report['guards'] + report['volatile_controls']:
                self.require(language, record)

    def test_frame_and_preserved44_cannot_be_resealed_locally(self):
        for key in ('preserved', 'metadata', 'saved', 'short', 'borrowed', 'guard'):
            language, r = self.base(); out = r['fs_init']
            if key in ('metadata', 'saved'):
                offset = 10 if key == 'metadata' else 96
                for field in ('frame_before', 'frame_after'):
                    image = bytearray.fromhex(out[field]); image[offset] ^= 1; out[field] = image.hex()
            elif key == 'preserved':
                image = bytearray.fromhex(out['after']); image[20] ^= 1; out['after'] = image.hex()
                image = bytearray.fromhex(out['frame_after']); image[44] ^= 1; out['frame_after'] = image.hex()
            elif key == 'short': out['before'] = out['before'][:-8]
            elif key == 'borrowed': r['pp_reader']['upper_after'] = '00' * 16
            else: r['pp_reader']['stack_guard_after'] = '00' * 56
            with self.subTest(key=key), self.assertRaises(ValueError): self.require(language, r)

    def test_fetches_do_not_substitute_for_actual_store_proof(self):
        for key in ('missing', 'order', 'width', 'address', 'before', 'value', 'register', 'fetch'):
            language, r = self.base(); out = r['fs_init']
            if key == 'missing': out['stores'].pop(5)
            elif key == 'order': out['stores'][0], out['stores'][1] = out['stores'][1], out['stores'][0]
            elif key == 'width': out['stores'][0]['bytes'] = 2
            elif key == 'address': out['stores'][0]['address'] += 4
            elif key == 'before': out['stores'][0]['before'] = '00000000'
            elif key == 'value': out['stores'][5]['value'] = 0
            elif key == 'register': out['stores'][0]['regs'][12] ^= 1
            else: out['flow'] = out['flow'][:-1]
            with self.subTest(key=key), self.assertRaises(ValueError): self.require(language, r)

    def test_full_abi_ledger_and_no_fake_init_event(self):
        for key in ('r0', 'r1', 'r2', 'r12', 'sp', 'lr', 'isa', 'early', 'modeled', 'open_r2'):
            language, r = self.base(); out = r['fs_init']
            if key in ('r0', 'r1', 'r2', 'r12', 'sp', 'lr', 'isa'):
                out['returned'][{'r0': 0, 'r1': 1, 'r2': 2, 'r12': 12, 'sp': 13, 'lr': 14, 'isa': 15}[key]] ^= 1
            elif key == 'early': out['ledger_before']['initialized'] = True
            elif key == 'modeled': r['pp_reader']['models'][2]['name'] = 'FS_InitFile'
            else: r['pp_reader']['models'][0]['args'][2] = 310
            with self.subTest(key=key), self.assertRaises(ValueError): self.require(language, r)

    def test_executed_off_and_both_counters(self):
        z = self.z
        for language, report in self.reports.items():
            data, q = self.data[language], self.q[language]
            for entry in report['observer_off']:
                off = entry['result']; on = next(r for r in report['positives'] if r['plus'] == off['plus'] and r['seed'] == off['seed'])
                self.assertEqual(z.require_off_pair(on, off, data), entry['proof'])
            normal = next(r for r in report['positives'] if r['plus'] == 1 and r['seed'] == 0x12345678)
            for counter in report['counters']: z.require_counter(counter, normal, data, q)

    def test_counter_prestate_and_shadow_are_not_free_parameters(self):
        for language, report in self.reports.items():
            normal = next(r for r in report['positives'] if r['plus'] == 1 and r['seed'] == 0x12345678)
            for counter in report['counters']:
                for key in ('entry', 'before', 'shadow', 'extra_register', 'next_pc', 'payload', 'binding'):
                    bad = copy.deepcopy(counter); r = bad['result']; out = r['fs_init']
                    if key == 'entry': out['entry'][3] = 1
                    elif key == 'before': out['before'] = '00' * 72
                    elif key == 'shadow': out['shadows'] = []
                    elif key == 'extra_register': out['shadows'][0]['after'][12] ^= 1
                    elif key == 'next_pc': out['shadows'][0]['next_pc'] = '0x20d7fbc'
                    elif key == 'payload': r['pp_reader']['destination_hex'] = '00' * 16
                    else: r['pp_binding']['ram_sha256'] = '0' * 64
                    with self.subTest(variant=counter['variant'], key=key), self.assertRaises(ValueError):
                        self.z.require_counter(bad, normal, self.data[language], self.q[language])


if __name__ == '__main__': unittest.main()
