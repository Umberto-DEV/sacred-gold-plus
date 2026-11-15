"""Frozen-field and activation checks are separate obligations."""
from pathlib import Path
import copy,importlib.util,json,os,tempfile,unittest
s=importlib.util.spec_from_file_location('wakeup_cli',Path(__file__).parents[1]/'tools/attribuisci_os_wakeup.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
t=importlib.util.spec_from_file_location('wakeup_fixture',Path(__file__).with_name('test_os_wakeup_bench.py'))
T=importlib.util.module_from_spec(t);t.loader.exec_module(T)


def sample():
    f=T.fixture();f.update(language='EN',ordinal=0,plus=0,seed=0x12345678,provenance=dict(parent_report_sha256='a'*64))
    r=M.B.predict(f);r['halt_pc']=hex(M.B.RETURN)
    c={k:f[k]for k in('language','ordinal','plus','seed','translated_result','entry')}
    c.update(parent_report_sha256='a'*64,caller_frame_bytes=328,caller_frame_before_sha256=M.sha(bytes.fromhex(f['frame'])[24:]),
        expected_caller_frame_after_sha256=M.sha(bytes.fromhex(f['frame'])[24:]),archive_bytes=92,
        archive_before_sha256=M.sha(bytes.fromhex(f['archive_before'])),expected_archive_after_sha256=M.sha(bytes.fromhex(f['archive_before'])),
        input_queue_address=M.B.QUEUE,input_queue8='00'*8)
    return f,r,c


class Contract(unittest.TestCase):
    def test_recipe_provenance_rejects_forged_header_compiler_layout_inline(self):
        # Only the compared declarations are synthetic; this is not an ELF qualification.
        p=dict(reference=dict(header_sha256={'h'+str(i):str(i)for i in range(18)}),
            compiler_sha256='fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66',compiler_version='qualified')
        r=copy.deepcopy(p);r.update(layout_abi_compatibility=dict(flag='-mabi=apcs-gnu',u64_queried_alignment=8,CPContext_bytes=28,
            CPContext_alignment=4,OSContext_bytes=100,OSContext_alignment=4,
            installed_thread_offsets=dict(state=100,queue=120,link_prev=124,link_next=128),
            meaning='Pinned-header compatibility with installed offsets; original MW compiler/flags and C binary not reconstructed',
            default_eabi_probe_invoked=False,nonempty_thread_runtime_qualified=False),
            queue_inline_source=dict(path='lib/include/nitro/os/common/thread_shared.h',sha256='c5912e365f7a55ab466f1c4db082a5fa9ca1222d69b1709b16bac256369123e2',
                definition_sha256='86451bbc5ac1556f6b1b6a6e7a1cb70e3dad1048a9b7ff0772f5e64147ba4369',
                activation='Expanded in full body but skipped on the qualified empty-head path'))
        M.check_recipe_provenance(r,p)
        mutants=[]
        for key in('compiler_sha256','compiler_version'):
            b=copy.deepcopy(r);b[key]='forged';mutants.append(b)
        b=copy.deepcopy(r);b['reference']['header_sha256']['h0']='forged';mutants.append(b)
        for key in('CPContext_bytes','OSContext_alignment','u64_queried_alignment'):
            b=copy.deepcopy(r);b['layout_abi_compatibility'][key]=0;mutants.append(b)
        b=copy.deepcopy(r);b['queue_inline_source']['definition_sha256']='forged';mutants.append(b)
        for b in mutants:
            with self.assertRaises(ValueError):M.check_recipe_provenance(b,p)

    def test_earlier_contract_reports_volatile_differences_without_native_claim(self):
        f,r,c=sample();p=M.field_contract(c,f,r)
        self.assertTrue(p['passed']);self.assertFalse(p['native_activation_proved_by_this_comparator'])
        self.assertEqual([x['register']for x in p['volatile_changes']],[0,1,2,14])

    def test_field_contract_does_not_mistake_a_noop_for_native_activation(self):
        f,r,c=sample();noop=dict(frame_after=f['frame'],archive_after=f['archive_before'],returned=f['entry'],halt_pc=hex(M.B.RETURN))
        self.assertTrue(M.field_contract(c,f,noop)['passed'])
        # The full native verifier separately requires the trace, PUSH, reads and whole RAM.
        for k in('flow','stores','reads'):self.assertTrue(r[k])
        self.assertEqual(r['native_peak'],24)

    def test_contract_rejects_independent_memory_abi_and_provenance_mutations(self):
        f,r,c=sample()
        for field in('frame_after','archive_after'):
            bad=copy.deepcopy(r);b=bytearray.fromhex(bad[field]);b[-1]^=1;bad[field]=b.hex()
            with self.assertRaises(ValueError):M.field_contract(c,f,bad)
        for index in(*range(4,12),13,15):
            bad=copy.deepcopy(r);bad['returned'][index]^=128 if index==15 else 1
            with self.assertRaises(ValueError):M.field_contract(c,f,bad)
        for key,value in(('parent_report_sha256','b'*64),('ordinal',True),('plus',True),('seed',0)):
            bad=copy.deepcopy(c);bad[key]=value
            with self.assertRaises(ValueError):M.field_contract(bad,f,r)
        bad=copy.deepcopy(r);bad['halt_pc']='0x20d1f34'
        with self.assertRaises(ValueError):M.field_contract(c,f,bad)

    def test_parent_config_rejects_incomplete_or_wrong_language(self):
        with tempfile.TemporaryDirectory()as directory:
            p=Path(directory)/'config.json'
            for value in({},dict(EN={},IT={})):
                p.write_text(json.dumps(value))
                with self.assertRaises((ValueError,KeyError)):M.read_config(p)


class PrivateReplay(unittest.TestCase):
    def test_native_report_and_falsifiers_without_running_guest(self):
        config=os.environ.get('SGP_OS_WAKEUP_REPLAY_CONFIG')
        if not config:self.skipTest('own authenticated ROMs, recipes and retained report required')
        c=json.loads(Path(config).read_bytes());fixtures,bodies,proof,groups=M.prepare(Path(c['parent_config']),Path(c['recipe_dir']))
        report=M.H.H.H.H.N.read_report(Path(c['report']))
        M.require_report(report,fixtures,bodies,proof,groups,Path(c['field_contract']),Path(c['raw_dir']))
        for key,value in(('cpu_executed',False),('compiler_invoked',True),('field_contract_sha256','0'*64),
                          ('field_holdout',[]),('observer_off',[]),('cases',[])):
            bad=copy.deepcopy(report);bad[key]=value
            with self.assertRaises(ValueError):M.require_report(bad,fixtures,bodies,proof,groups,Path(c['field_contract']),Path(c['raw_dir']))
        self.assertEqual(M.wire(report['fixtures']),M.wire(fixtures));self.assertEqual(M.wire(report['proof']),M.wire(proof))
        self.assertEqual(M.wire(report['groups']),M.wire(groups));self.assertEqual(report['source_sha256'],M.source_identities())
        self.assertEqual(len(report['cases']),len(groups)*3)
        for g in groups:
            rows=report['cases'][g['ordinal']*3:g['ordinal']*3+3]
            for cell,(label,options)in zip(rows,M.POLICIES):
                row=cell['result'];self.assertEqual((cell['group'],cell['label']),(g['ordinal'],label))
                self.assertEqual((row['observe'],row['fill']),(options.get('observe',True),options.get('fill',0xA5)))
                self.assertEqual(row['fixture'],g['representative']);M.B.require_result(row,bodies)
            M.require_off_pair(rows[0]['result'],rows[1]['result'],bodies)
            normal=rows[0]['result']
            for field in('flow','stores','reads','observed_pcs'):
                bad=copy.deepcopy(normal);bad[field]=[]
                with self.assertRaises(ValueError):M.B.require_result(bad,bodies)
            for field in('native_peak','steps','whole_ram_sha256'):
                bad=copy.deepcopy(normal);bad[field]=0
                with self.assertRaises(ValueError):M.B.require_result(bad,bodies)


if __name__=='__main__':unittest.main()
