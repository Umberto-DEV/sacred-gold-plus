import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from . import mechanics_stages as ms, controls, portable

class Registration(unittest.TestCase):
    def test_both_are_registered_and_inert_only(self):
        for name in ('controls', 'portable'):
            stage = ms.require_stage(name)
            self.assertTrue(stage.contextual)
            self.assertTrue(stage.slot_payload > 0)
            self.assertNotIn(name, ms.PENDING)
        self.assertEqual(ms.writers(ms.chain_for('portable')), ('moves','ai','ai-immunities','abilities','legacy','legendary-scene-version','trainer-fixes','pokeathlon','traded-egg','bag-foreign','bag-view-position','lottery-id','battle-tower-wrap','battle-animation-facade','battle-animation-dynamicpunch','battle-animation-helping-hand','battle-animation-strength','battle-animation-spit-up','giratina-pc-form','invisible-grass','waterfall-facing','follower-menu-jump','controls','portable'))

    def test_exact_ram_declarations(self):
        class Image:
            def offset(self, address, size): return address - 0x02000000
        with patch.object(ms, '_image', return_value=Image()):
            for name, slot, hooks in (
                ('controls', controls.SLOT_NAME, [(controls.hex_int(s),4) for s,_,_ in controls.SITES]),
                ('portable', portable.SLOT_NAME, [(s,4) for _,s,_,_ in portable.BL_HOOKS]+[(portable.CALLBACK,8)])):
                got = ms.require_stage(name).regions(b'')
                part = ms.reserve_slot(slot)[1]
                expected = [(part['start']-0x02000000,part['start']-0x02000000+part['bytes'])]
                expected += [(s-0x02000000,s-0x02000000+n) for s,n in hooks]
                self.assertEqual([(r.start,r.end) for r in got], expected)
                ms.require_disjoint([got])

    def test_rows_without_full_receipt_are_rejected(self):
        for name in ('controls','portable'):
            stage = ms.require_stage(name)
            parent, part = ms.reserve_slot(stage.slot)
            row = dict(name=stage.slot,parent=parent,start=part['start'],bytes=part['bytes'],capacity=part['bytes'])
            with self.assertRaisesRegex(ValueError, 'full reserve allocation receipt'):
                ms.run_stage(name,b'0'*4096,'EN',allocation=[row])

    def test_controls_adapter_forwards_charmap_and_independent_zero_preimage(self):
        row = dict(name=controls.SLOT_NAME,start=0x023D4C10,bytes=512,capacity=512,parent='field-guide.code')
        allocation = dict(assignments=[row])
        with patch.object(controls,'check_allocation',return_value=row), patch.object(controls,'prepare',return_value=(b'out',{})) as prepare:
            self.assertEqual(ms._controls_apply(b'in','EN',allocation=allocation,charmap=Path('/charmap'),work_dir=Path('/work')),(b'out',{}))
        self.assertEqual(prepare.call_args.kwargs['preimage_sha256'],hashlib.sha256(bytes(512)).hexdigest())
        self.assertIs(prepare.call_args.kwargs['allocation'],allocation)
        self.assertEqual(prepare.call_args.args[2],Path('/charmap'))
        self.assertFalse(prepare.call_args.kwargs.get('active',False))

    def test_portable_adapter_forwards_full_grant_and_stays_inert(self):
        row = dict(name=portable.SLOT_NAME,start=0x023D4E10,bytes=3024,capacity=3024,parent='field-guide.code')
        allocation = dict(assignments=[row])
        with patch.object(portable,'check_allocation',return_value=row), patch.object(portable,'prepare',return_value=(b'out',{})) as prepare:
            ms._portable_apply(b'in','IT',allocation=allocation,charmap=None,work_dir=Path('/work'))
        self.assertEqual(prepare.call_args.kwargs['preimage_sha256'],hashlib.sha256(bytes(3024)).hexdigest())
        self.assertIs(prepare.call_args.kwargs['allocation'],allocation)
        self.assertNotIn('activation',prepare.call_args.kwargs)
        self.assertNotIn('context_proof',prepare.call_args.kwargs)

    def test_controls_replay_refuses_active_receipt(self):
        with self.assertRaisesRegex(ValueError,'activation state differs'):
            ms._controls_verify(b'in',b'out',{'language':'EN','function_state':'active','enabled':1},charmap=Path('/charmap'))

    def test_portable_replay_refuses_active_receipt(self):
        with self.assertRaisesRegex(ValueError,'activation state differs'):
            ms._portable_verify(b'in',b'out',{'language':'EN','function_state':'active'},charmap=None)

    def test_controls_reader_uses_charmap(self):
        receipt = {'language':'EN','function_state':'inert','enabled':0, 'candidate_sha256':None,
                   'evidence':None,'geometry':dict(controls.PROPOSAL),'variant':'compact'}
        with patch.object(controls,'verify',return_value={'ok':True}) as verify:
            self.assertEqual(ms._controls_verify(b'in',b'out',receipt,charmap=Path('/charmap')),{'ok':True})
        self.assertEqual(verify.call_args.kwargs,{'charmap':Path('/charmap')})

class BoundAllocation(unittest.TestCase):
    def test_schema2_owner_delegates_structural_checks_to_shared_reserve_validator(self):
        from sgp131 import reserve
        for owner in (controls,portable):
            parent,part=ms.reserve_slot(owner.SLOT_NAME)
            row=dict(name=owner.SLOT_NAME,parent=parent,start=part['start'],bytes=part['bytes'],capacity=part['bytes'])
            supplied={'schema':2,'installer_verification':{'not_an_authenticator':True}}
            with patch.object(reserve,'validate_allocation',create=True,return_value=[row]) as validate:
                self.assertEqual(owner.check_allocation(supplied,'EN'),row)
                validate.assert_called_once_with(supplied,'EN')
    def test_schema2_cannot_bypass_shared_refusal_or_omit_its_slot(self):
        from sgp131 import reserve
        for owner in (controls,portable):
            with patch.object(reserve,'validate_allocation',create=True,side_effect=ValueError('bound proof refused')):
                with self.assertRaisesRegex(ValueError,'bound proof refused'):
                    owner.check_allocation({'schema':2},'EN')
            with patch.object(reserve,'validate_allocation',create=True,return_value=[]):
                with self.assertRaisesRegex(ValueError,'does not request'):
                    owner.check_allocation({'schema':2},'EN')

if __name__ == '__main__': unittest.main()
