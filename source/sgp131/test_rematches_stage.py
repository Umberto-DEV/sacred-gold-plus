"""ROM-free regression tests for mandatory overlay production and cold reconstruction."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import build, mechanics_stages as M, rematches, reserve


class MandatoryOverlay(unittest.TestCase):
    def test_compiler_environment_has_a_private_writable_tmpdir(self):
        with tempfile.TemporaryDirectory(prefix='rematch-compiler-env-') as work:
            env = rematches.compiler_environment_for(Path(work))
            self.assertEqual(env['TMPDIR'], str(Path(work).resolve()))
            self.assertTrue(Path(env['TMPDIR']).is_dir())
            self.assertEqual(env['HOME'], '/var/empty')
            self.assertEqual(env['CLANG_NO_DEFAULT_CONFIG'], '1')

    def test_omitted_record_rejected(self):
        with self.assertRaisesRegex(ValueError, 'omitted or extra'):
            build.replay_overlays(b'', 'EN', None, ('rematches',), [])

    def test_extra_record_on_shorter_chain_rejected(self):
        with self.assertRaisesRegex(ValueError, 'omitted or extra'):
            build.replay_overlays(b'', 'EN', None, ('portable',), [{'producer':'rematches-module'}])

    def test_unknown_and_duplicate_records_rejected(self):
        for records in ([{'producer':'unknown'}], [{'producer':'rematches-module'}]*2):
            with self.subTest(records=records), self.assertRaisesRegex(ValueError,'omitted or extra'):
                build.replay_overlays(b'', 'EN', None, ('rematches',), records)

    def test_shorter_chain_cannot_smuggle_declared_overlay(self):
        with self.assertRaisesRegex(ValueError,'extra overlay'):
            build.complete_overlays(b'', 'EN', None, (), [object()])

    def test_required_owner_is_always_rebuilt_and_caller_can_only_confirm(self):
        expected=object()
        with patch.object(build.cartridge_deltas,'derive_rematches',return_value=expected) as derive:
            self.assertEqual(build.complete_overlays(b'V4','EN','scratch',('rematches',),()),(expected,))
            self.assertEqual(build.complete_overlays(b'V4','EN','scratch',('rematches',),(expected,)),(expected,))
            with self.assertRaisesRegex(ValueError,'mandatory owner replay'):
                build.complete_overlays(b'V4','EN','scratch',('rematches',),(object(),))
            self.assertEqual(derive.call_count,3)

    def test_overlay_producer_is_required_through_the_final_identity_stage(self):
        build.require_stage('identity')
        self.assertEqual(M.required_overlay_producers(M.chain_for('identity')), ('rematches-module',))


class ColdPreimages(unittest.TestCase):
    def stage(self, callback=None, peel=None):
        return M.MechanicalStage('fixture',lambda *_:None,lambda *_:None,lambda *_:[],
                                 cold_preimages=callback,peel=peel)

    def test_reclaimed_slot_restores_known_zero_instead_of_v4_old_code(self):
        before=b'OLDcode';final=b'NEWcode';regions=[M.Region(0,3,'fixture')]
        stage=self.stage(lambda *_:{(0,3):b'\0'*3})
        result=M.intermediate_images(before,final,[stage],[regions])
        self.assertEqual(result[0],b'\0\0\0code')
        self.assertNotEqual(result[0],before)

    def test_fixed_appended_activation_has_exact_cold_preimage(self):
        before=b'V4';final=b'V4MODULE\1';region=M.Region(8,9,'fixture activation')
        stage=self.stage(lambda *_:{(8,9):b'\0'})
        self.assertEqual(M.intermediate_images(before,final,[stage],[[region]])[0],b'V4MODULE\0')

    def test_unknown_appended_bytes_stay_rejected(self):
        with self.assertRaisesRegex(ValueError,'beyond the pristine'):
            M.intermediate_images(b'V4',b'V4MODULE\1',[self.stage()],[[M.Region(8,9,'unknown')]])

    def test_callback_cannot_add_or_resize_a_declared_region(self):
        for mapping in ({(1,3):b'XX'}, {(0,1):b'long'}, {(0,1):bytearray(b'x')}):
            with self.subTest(mapping=mapping),self.assertRaisesRegex(ValueError,'invalid fixed cold'):
                M.intermediate_images(b'old',b'new',[self.stage(lambda *_,m=mapping:m)],[[M.Region(0,1,'fixture')]])

    def test_peel_cannot_touch_undeclared_or_leave_known_cold_bytes_behind(self):
        for peeled in (b'xld',b'oXd'):
            stage=self.stage(lambda *_:{(0,1):b'\0'},peel=lambda *_,p=peeled:p)
            with self.subTest(peeled=peeled),self.assertRaisesRegex(ValueError,'does not peel back'):
                M.intermediate_images(b'old',b'nld',[stage],[[M.Region(0,1,'fixture')]])


class DownstreamSchema(unittest.TestCase):
    def test_schema2_delegates_structural_validation_and_selects_fixed_owner(self):
        allocation={'schema':2}
        expected={'name':'c8.module-stubs','start':0x023D59E0,'bytes':64,'capacity':192}
        with patch.object(reserve,'validate_allocation',return_value=[expected]) as validate:
            self.assertEqual(rematches.check_allocation(allocation,'EN'),expected)
            validate.assert_called_once_with(allocation,'EN')

    def test_schema2_cannot_skip_structural_refusal(self):
        with patch.object(reserve,'validate_allocation',side_effect=ValueError('invalid proof')):
            with self.assertRaisesRegex(ValueError,'invalid proof'):
                rematches.check_allocation({'schema':2},'EN')

    def test_wrapper_has_no_activation_bypass(self):
        with self.assertRaisesRegex(ValueError,'activation state differs'):
            M._rematches_verify(b'',b'',{'language':'EN','function_state':'active'},charmap=None)
