"""Public discovery contract: stdlib, no imports/producers, path and CLI drift guards."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('public_attribution_catalog',Path(__file__).parents[1]/'attribution_cases.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def tree_hash(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in root.rglob('*')if p.is_file()}


def fixture(root):
    files={'source/docs/validation/README.md':'# Reports\n', '.github/public-files.json':''}
    for slug,spec in M.DESCRIBED.items():
        doc=spec['guide'];files['source/docs/validation/README.md']+='- ['+slug+']('+Path(doc).name+')\n'
        files[doc]='# '+slug+'\nNo acceptance inferred.\n'
        flags=sorted(set(spec['parameters']+['--help','--prepare-only','--probe','--raw-dir']))
        files[spec['tool']]="raise RuntimeError('must never import a producer')\nfor name in "+repr(tuple(f[2:]for f in flags))+":\n    p.add_argument('--'+name)\n"
        files[spec['source_test']]='raise RuntimeError("must never import tests")\n'
        optional=['SGP_FS_SEND_PARENT_SOURCE']if slug=='native-fs-send'else[]
        replay=spec['source_test'].replace('_bench.py','_attribution.py');recipe=spec['source_test'].replace('_bench.py','_recipe.py')
        files[replay]='raise RuntimeError("must never import replay")\nENV='+repr(tuple(spec['replay_env']+optional))+'\n'
        files[recipe]='# independent recipe test declarations\n'
    allow=sorted(files);files['.github/public-files.json']=json.dumps(allow)
    for name,text in files.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    return files


class Discovery(unittest.TestCase):
    def test_describes_three_cases_without_executing_project_code(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);fixture(root);before=tree_hash(root);c=M.Catalog(root)
            docs=c.documents();self.assertEqual(len(docs),3)
            release=c.show('native-fs-release')
            self.assertEqual(release['scope'],'repository-navigation-only')
            commands=release['commands'];prepare=commands['prepare']
            self.assertIn('--prepare-only',prepare['argv']);self.assertNotIn('--probe',prepare['argv'])
            self.assertIs(prepare['requires_private_inputs'],True);self.assertEqual(prepare['effect'],'describe-only')
            self.assertIn('test_fs_release*.py',commands['private_replay']['argv'])
            self.assertEqual(commands['private_replay']['env'],['SGP_FS_RELEASE_REPLAY_CONFIG','SGP_FS_RELEASE_RECIPE_DIR'])
            self.assertEqual(c.check()['issues'],[]);self.assertEqual(tree_hash(root),before)
            self.assertNotIn('accepted',json.dumps(release));self.assertNotIn(str(root),json.dumps(release))

    def test_all_commands_state_cwd_and_replay_env_drift_is_detected(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);fixture(root);c=M.Catalog(root)
            for slug in M.DESCRIBED:
                for command in c.show(slug)['commands'].values():self.assertEqual(command.get('cwd'),'.')
            send=c.show('native-fs-send')['commands']['private_replay']
            self.assertEqual(len(send['env']),10);self.assertIn('SGP_REMATCH_OBJECT_DIR',send['env'])
            self.assertEqual(send['optional_env'],['SGP_FS_SEND_PARENT_SOURCE'])
            self.assertEqual(c.show('native-fs-exec-sync')['commands']['private_replay']['env'],['SGP_FS_EXEC_SYNC_REPLAY_CONFIG','SGP_FS_EXEC_SYNC_RECIPE_DIR'])
            spec=M.DESCRIBED['native-fs-send'];replay=root/spec['source_test'].replace('_bench.py','_attribution.py')
            replay.write_text(replay.read_text().replace('SGP_FS_SEND_REPORT_DIR','SGP_CHANGED_REPORT_DIR'))
            self.assertTrue(any('env' in issue for issue in M.Catalog(root).check()['issues']))

    def test_single_backslash_and_private_error_path_are_rejected(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);fixture(root);c=M.Catalog(root)
            weird='source/weird'+chr(92)+'name.py';p=root/weird;p.parent.mkdir(exist_ok=True);p.write_text('# own synthetic file');c.allowed.add(weird)
            with self.assertRaises(ValueError):c.public_path(weird)
            with patch.object(Path,'read_text',side_effect=PermissionError(str(root))):
                with self.assertRaises(ValueError)as error:c.read(M.INDEX)
            self.assertNotIn(str(root),str(error.exception))

    def test_source_flag_drift_and_unsupported_syntax_are_not_silent_success(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);fixture(root);spec=M.DESCRIBED['native-fs-release'];p=root/spec['tool'];text=p.read_text()
            p.write_text(text.replace("'prepare-only',",''));self.assertTrue(M.Catalog(root).check()['issues'])
            p.write_text(text+"p.add_argument(dynamic_flag())\n");result=M.Catalog(root).check()
            self.assertTrue(any('unresolved' in issue for issue in result['issues']))

    def test_missing_not_public_traversal_and_unknown_case_rejected(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);fixture(root);c=M.Catalog(root)
            with self.assertRaises(ValueError):c.show('not-a-case')
            index=root/'source/docs/validation/README.md'
            for target in('/private/secret.md','../../../../outside-source-rom.md','../../../local/private-source-rom.md'):
                index.write_text('# Reports\n- [bad]('+target+')\n')
                with self.subTest(target=target),self.assertRaises(ValueError):M.Catalog(root).documents()
            fixture(root);(root/M.DESCRIBED['native-fs-send']['guide']).unlink()
            with self.assertRaises(ValueError):M.Catalog(root).documents()

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory()as name,tempfile.TemporaryDirectory()as external:
            root=Path(name);fixture(root);p=root/M.DESCRIBED['native-fs-release']['guide'];p.unlink()
            other=Path(external)/'outside.md';other.write_text('# Outside\n');p.symlink_to(other)
            with self.assertRaises(ValueError):M.Catalog(root).documents()

    def test_cli_works_without_site_packages_from_another_working_directory(self):
        with tempfile.TemporaryDirectory()as name,tempfile.TemporaryDirectory()as cwd:
            root=Path(name);fixture(root);before=tree_hash(root)
            argv=[sys.executable,'-I','-S','-B',str(Path(M.__file__).resolve()),'--root',str(root),'show','native-fs-release','--json']
            r=subprocess.run(argv,cwd=cwd,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr);result=json.loads(r.stdout)
            self.assertEqual(result['id'],'native-fs-release-source-rom-1.3.2')
            self.assertNotIn(str(root),r.stdout);self.assertEqual(tree_hash(root),before)


if __name__=='__main__':unittest.main()
