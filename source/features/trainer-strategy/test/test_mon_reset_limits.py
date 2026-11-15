"""ROM-free local64k boundary and semantic-delta counterexamples."""
from pathlib import Path
import importlib.util
import unittest
from unittest import mock


def load(name):
    p=Path(__file__).with_name(name+'.py');s=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def wrong_loop():return 42


class MonResetLimitsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.A=load('arm_thumb_mon_reset_oracle');cls.C=load('mon_reset_cpu')
    def test_only_two_outer_and_two_producer_nodes_change(self):
        self.assertEqual(self.A.audit_source_delta(),2);self.assertEqual(self.C.audit_source_delta(),2)
        self.A.source_identity_guard();self.C.source_identity_guard()
        self.assertEqual((self.A.CAP,self.C.CAP,self.A.BASE.CAP,self.C.BASE.CAP),(65536,65536,32768,32768))
    def test_finite_cap_rejects_bool_zero_and_overflow_before_input(self):
        for cap in(True,False,0,-1,65537,65536.0):
            with self.assertRaisesRegex(ValueError,'finite mixed instruction cap'):
                self.A.run({},(),0,cap=cap,thumb_code={})
    def test_changed_semantics_cannot_hide_behind_limit_adapter(self):
        with mock.patch.object(self.A,'_run_source',wrong_loop):
            with self.assertRaisesRegex(ValueError,'source delta'):self.A.audit_source_delta()
        with mock.patch.object(self.C,'_run_cpu',wrong_loop):
            with self.assertRaisesRegex(ValueError,'producer delta'):self.C.audit_source_delta()
    def test_new_completion_accepts_last_spare_callback(self):
        raw=dict(stopped=True,executed_count=65535,callback_count=65536)
        self.C.require_completion(raw,65535)
        with self.assertRaises(ValueError):self.C.BASE.require_completion(raw,65535)
    def test_at_cap_and_unobserved_gate_rejected(self):
        for raw,steps in((dict(stopped=True,executed_count=65536,callback_count=65537),65536),
                          (dict(stopped=False,executed_count=65535,callback_count=65535),65535)):
            with self.assertRaises(ValueError):self.C.require_completion(raw,steps)
    def test_typed_completion_counts_and_steps(self):
        for raw,steps in((dict(stopped=True,executed_count=True,callback_count=2),1),
                          (dict(stopped=True,executed_count=1,callback_count=True),1),
                          (dict(stopped=True,executed_count=1,callback_count=2),True)):
            with self.assertRaises(ValueError):self.C.require_completion(raw,steps)


if __name__=='__main__':unittest.main()
