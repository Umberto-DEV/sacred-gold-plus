"""Source-only Find → Convert → Open contexts, with synthetic stack bytes."""
from pathlib import Path
import builtins,contextlib,dis,importlib.util,io,struct,sys,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('find_caller_context',Path(__file__).parents[1]/'tools/attribuisci_fs_find_chiamante.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)


def fixture():
    parent=dict(find_value=1,send_value=1,pp_clobber=False)
    old=Z.C.H.V.expected_convert(parent)
    entry=list(old['find']['entry']);frame=bytearray(b'\xC7'*280)
    struct.pack_into('<4I',frame,112,0,Z.FILE,310,0x20D828C)
    f=dict(entry=entry,frame=frame.hex(),path='a/0/1/1',current_dir=Z.A.ROOT.hex(),file_id=140,
        destination_before=bytes(frame[Z.ID-Z.FRAME:Z.ID-Z.FRAME+8]).hex())
    return dict(parent,send4_value=1,find=dict(fixture=f))


class Context(unittest.TestCase):
    def test_cli_rejects_combined_readback_and_cpu_modes_before_analyze(self):
        argv=['find-caller']
        for name in('rom','objects','strategy-object','read-recipe','wait-recipe','recipe-dir','json'):
            argv+=['--'+name,'unused']
        argv+=['--language','EN','--readback-only','--probe']
        with patch.object(sys,'argv',argv),patch.object(Z,'analyze',side_effect=AssertionError('must not analyze'))as run:
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit)as error:Z.main()
            self.assertEqual(error.exception.code,2);run.assert_not_called()

    def test_root_fence_must_bind_actual_api_entry(self):
        regs=[0]*15+[0x3F]
        root=dict(address=Z.A.CURRENT,bytes=12,before=bytes(12).hex(),after=Z.A.ROOT.hex(),
                  changed_bytes=4,initialized_once=True,registers=regs)
        r=dict(root_input=root,root_fences=[],api_calls=[])
        for number in range(3):
            entry=list(regs)
            if number==1:entry[4:12]=Z.C.H.PP.N.COOKIES
            r['root_fences'].append(dict(number=number,begin=hex(number),root_before=Z.A.ROOT.hex(),
                root_after=Z.A.ROOT.hex(),regs_before=list(regs),regs_after=list(entry)))
            r['api_calls'].append(dict(begin=hex(number),entry=entry,end=list(entry)))
        self.assertTrue(Z.require_root(r))
        r['root_fences'][0]['regs_before'][0]=1
        with self.assertRaises(ValueError):Z.require_root(r)

    def test_source_auth_bindings_resolve_all_effective_globals(self):
        # Regression: a transplanted Open oracle once missed its property helper.
        for fn in(Z.find_step,Z.find_write,Z.pp_snapshot,Z.finish_native,Z.run_case,
                  Z.expected_convert,Z.expected_open,Z.require_readonly_guard,Z.require_init,
                  Z.require_open,Z.require_convert,Z.require_fast,Z.require_timeline,Z.require_native):
            missing={i.argval for i in dis.get_instructions(fn)if i.opname=='LOAD_GLOBAL'and
                     i.argval not in fn.__globals__ and not hasattr(builtins,i.argval)}
            self.assertEqual(missing,set(),fn.__qualname__)

    def test_noncanonical_true_remains_visible_then_normalizes(self):
        r=fixture();one=Z.expected_convert(r);r['send4_value']=2;two=Z.expected_convert(r)
        self.assertEqual(one['find']['returned'][0],1);self.assertEqual(two['find']['returned'][0],2)
        self.assertEqual(one['returned'],two['returned']);self.assertEqual(one['returned'][0:3],[1,4,0])
        self.assertEqual(one['returned'][14],0x20D80F8)
        self.assertEqual(one['flow'][13:],two['flow'][13:])
        r.update(open_fast_value=1,variant='current')
        opened=Z.expected_open(r)
        self.assertEqual(opened['returned'],Z.C.H.F.predict_open(r)['returned'])
        self.assertEqual([c['pc']for c in opened['calls']],[hex(Z.F.SEND)]*2)

    def test_clobber_restores_saved_r3_and_preserves_source_lr(self):
        r=fixture();r['pp_clobber']=True;out=Z.expected_convert(r)
        self.assertEqual(out['returned'][3],0);self.assertEqual(out['returned'][12],0xA500000C)
        self.assertEqual(out['returned'][1:3],[0xA5000001,0xA5000002])
        self.assertEqual(out['returned'][14],0x20D80F8)

    def test_bool_boundary_value_and_wrong_actual_find_entry_rejected(self):
        r=fixture();r['send4_value']=True
        with self.assertRaises(ValueError):Z.expected_convert(r)
        r=fixture();r['find']['fixture']['entry'][2]^=4
        with self.assertRaises(ValueError):Z.expected_convert(r)


if __name__=='__main__':unittest.main()
