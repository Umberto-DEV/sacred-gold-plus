"""Pure contract checks for the counterfactual runner; no ROM or guest execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1]/'features/type-consumers/tools/verifica_uturn_133.py'
spec = importlib.util.spec_from_file_location('uturn_133_runner', TOOL)
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)

class CounterfactualContract(unittest.TestCase):
    def test_unknown_profile_and_current_counter_are_rejected(self):
        with self.assertRaises(ValueError): R.A.NativeFlinch({}, {}, code_profile="unknown")
        with self.assertRaises(ValueError): R.A.NativeFlinch({}, {}, variant="no_clear", code_profile="current74")

    def test_historical_builder_allowlist_is_finite(self):
        self.assertEqual(len(R.A.LEGACY_BUILDERS), 2)
        self.assertNotIn('0'*64, R.A.LEGACY_BUILDERS)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'uturn.o').write_bytes(b'object'); (p/'native.bin').write_bytes(bytes(68))
            (p/'compile-retained.json').write_text(json.dumps(dict(source_sha256=R.A.LEGACY_SOURCE_SHA, payload_sha256=R.A.U.HELPER_SHA256, builder_sha256='0'*64)))
            with self.assertRaises(ValueError): R.A.verify_build(p)

    @staticmethod
    def rng_observation(seed, count):
        after=R.A.G.next_seed(seed) if count else seed
        calls=([dict(before=seed,after=after,value=after>>16)] if count else [])
        return dict(seed_before=seed,seed_after=after,rng_calls=calls,calls={'rng':count},flinch=False)

    def test_rng_count_and_seed_mutations_rejected_with_same_boolean(self):
        from copy import deepcopy
        sample=self.rng_observation(0x12345678,1)
        R.verify_rng(sample,1)
        for mutate in (lambda x:x['calls'].__setitem__('rng',0),
                       lambda x:x['rng_calls'][0].__setitem__('before',0),
                       lambda x:x['rng_calls'][0].__setitem__('after',0),
                       lambda x:x['rng_calls'][0].__setitem__('value',0),
                       lambda x:x.__setitem__('seed_after',0),
                       lambda x:x.__setitem__('rng_calls',[])):
            forged=deepcopy(sample);mutate(forged)
            self.assertEqual(forged['flinch'],sample['flinch'])
            with self.assertRaises(ValueError):R.verify_rng(forged,1)

    def test_repeat_rng_and_continuity_are_required(self):
        from copy import deepcopy
        first=self.rng_observation(0x12345678,0)
        again=self.rng_observation(first['seed_after'],1)
        row=dict(name='empty',options={},new=first,repeat=again)
        R.verify_case_rng(row)
        bad=deepcopy(row);bad['repeat']=self.rng_observation(first['seed_after'],0)
        with self.assertRaises(ValueError):R.verify_case_rng(bad)
        bad=deepcopy(row);bad['repeat']=self.rng_observation(1,1)
        with self.assertRaises(ValueError):R.verify_case_rng(bad)

    def test_rejects_wrong_payload_before_reading_model(self):
        with self.assertRaises(ValueError): R.counterfactual({}, bytes(74))

    def test_rejects_changed_candidate_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); (p/'uturn.o').write_bytes(b'object'); (p/'native.bin').write_bytes(bytes(74))
            (p/'receipt.json').write_text(json.dumps(dict(source_sha256='wrong',compiler={})))
            with self.assertRaises(ValueError): R.artifact(p)

    def test_counterfactual_only_changes_tail(self):
        addr=R.N.HELPER_ADDRESS; foreign=b'F'*64; legacy=b'L'*68; payload=b'P'*74
        original=foreign+legacy+bytes(60)+b'Z'*8
        real_sha=R.A.sha
        def fake_sha(data):
            if data==payload:return R.N.HELPER_SHA256
            if data==legacy:return R.A.U.HELPER_SHA256
            if data==foreign:return '77844c84762bcdf84e64503a1e0996c871c8ca1027846b8059e5b5b86a8688ce'
            return real_sha(data)
        model=dict(segments=[(addr-64,original)],overlay=b'unchanged')
        with patch.object(R.A,'sha',side_effect=fake_sha): result=R.counterfactual(model,payload)
        self.assertEqual(result['segments'][0][1],foreign+payload+bytes(54)+b'Z'*8)
        self.assertEqual(model['segments'][0][1],original)
        self.assertEqual(result['overlay'],model['overlay'])

    def test_nonzero_legacy_padding_rejected(self):
        addr=R.N.HELPER_ADDRESS; payload=b'P'*74
        model=dict(segments=[(addr-64,b'F'*64+b'L'*68+b'X'+bytes(59))])
        def fake_sha(data):
            return R.N.HELPER_SHA256 if data==payload else R.A.U.HELPER_SHA256
        with patch.object(R.A,'sha',side_effect=fake_sha):
            with self.assertRaises(ValueError): R.counterfactual(model,payload)

if __name__=='__main__':unittest.main()
