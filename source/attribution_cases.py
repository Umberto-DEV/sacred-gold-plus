#!/usr/bin/env python3
"""Read-only public report discovery; no ROM, optional packages or producer imports.

JSON describes navigation and commands. It is never a game acceptance verdict.
Commands are examples only and are not executed by this program.
"""
from pathlib import Path,PurePosixPath
import argparse,ast,fnmatch,json,posixpath,re
from urllib.parse import unquote

INDEX='source/docs/validation/README.md'
GUIDE='source/docs/test-bench.md#linking-source-to-an-exact-rom'
PREFIX='source/features/trainer-strategy/'
DESCRIBED={}
for name,parameters,parents,models,env in(
 ('send',('rom','language','parent-report','objects','strategy-object','read-recipe','wait-recipe','find-recipe','recipe-dir','json'),
  ['native-fs-find-caller-source-rom-1.3.2'],['ExecuteSync'],
  ['SGP_FS_SEND_REPORT_DIR','SGP_FS_SEND_RAW_DIR','SGP_FS_SEND_ROM_DIR','SGP_FS_SEND_PARENT_DIR','SGP_REMATCH_OBJECT_DIR',
   'SGP_STRATEGY_OBJECT_DIR','SGP_FS_SEND_READ_RECIPE','SGP_FS_SEND_WAIT_RECIPE','SGP_FS_SEND_FIND_RECIPE','SGP_FS_SEND_RECIPE_DIR']),
 ('exec-sync',('rom','language','parent-report','find-parent-report','objects','strategy-object','read-recipe','wait-recipe','find-recipe','send-recipe','recipe-dir','json'),
  ['native-fs-send-source-rom-1.3.2'],['Translate','Release','Next'],['SGP_FS_EXEC_SYNC_REPLAY_CONFIG','SGP_FS_EXEC_SYNC_RECIPE_DIR']),
 ('release',('rom','language','parent-report','parent-config','recipe-dir','json'),
  ['native-fs-exec-sync-source-rom-1.3.2'],['empty Wakeup'],['SGP_FS_RELEASE_REPLAY_CONFIG','SGP_FS_RELEASE_RECIPE_DIR'])):
    slug='native-fs-'+name;module=name.replace('-','_')
    DESCRIBED[slug]=dict(guide='source/docs/validation/'+slug+'-source-rom-1.3.2.md',
        tool=PREFIX+'tools/attribuisci_fs_'+module+'.py',parameters=['--'+p for p in parameters],
        source_test=PREFIX+'test/test_fs_'+module+'_bench.py',
        replay_tests=[PREFIX+'test/test_fs_'+module+'_attribution.py',PREFIX+'test/test_fs_'+module+'_recipe.py'],replay_pattern='test_fs_'+module+'*.py',
        parents=parents,modeled_boundaries=models,replay_env=env)


def need(value,message):
    if not value:raise ValueError(message)


def declared_options(text):
    """Inspect literals/simple string-loop concatenation, never evaluate/import code."""
    flags=set();unresolved=0
    def literal(node,env):
        if isinstance(node,ast.Constant)and type(node.value)is str:return node.value
        if isinstance(node,ast.Name):return env.get(node.id)
        if isinstance(node,ast.BinOp)and isinstance(node.op,ast.Add):
            a,b=literal(node.left,env),literal(node.right,env)
            if a is not None and b is not None:return a+b
        return None
    def walk(node,env):
        nonlocal unresolved
        if isinstance(node,ast.For)and isinstance(node.target,ast.Name)and isinstance(node.iter,(ast.Tuple,ast.List)):
            values=[literal(item,env)for item in node.iter.elts]
            if all(v is not None for v in values):
                for value in values:
                    for child in node.body:walk(child,{**env,node.target.id:value})
                for child in node.orelse:walk(child,env)
                return
        if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=='add_argument':
            options=[literal(arg,env)for arg in node.args]
            if not options or any(value is None for value in options):unresolved+=1
            flags.update(v for v in options if v is not None and v.startswith('-'))
        for child in ast.iter_child_nodes(node):walk(child,env)
    walk(ast.parse(text),{})
    return dict(declared_options=sorted(flags),unresolved_declarations=unresolved,inspection='limited-static-syntax; no imports or execution')


class Catalog:
    def __init__(self,root):
        self.root=Path(root).resolve()
        try:allow=json.loads((self.root/'.github/public-files.json').read_text())
        except(OSError,ValueError)as error:raise ValueError('public allowlist unavailable or invalid')from error
        need(type(allow)is list and all(type(p)is str for p in allow),'public allowlist must be a string list')
        self.allowed=set(allow)

    def public_path(self,relative):
        p=PurePosixPath(relative)
        need(not p.is_absolute()and '..'not in p.parts and '\\'not in relative and relative in self.allowed,
             'reference is outside the public allowlist: '+relative)
        path=self.root.joinpath(*p.parts)
        try:resolved=path.resolve(strict=True)
        except OSError as error:raise ValueError('missing public file: '+relative)from error
        need(resolved==path and path.is_file(),'public file must be regular and contain no symlink: '+relative)
        return path

    def read(self,relative):
        path=self.public_path(relative)
        try:
            need(path.stat().st_size<=2*1024**2,'public text exceeds2MiB: '+relative)
            return path.read_text()
        except(OSError,UnicodeError)as error:raise ValueError('public text unavailable or invalid: '+relative)from error

    def link(self,document,target):
        if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target):return None
        target=unquote(target.split('#',1)[0].strip('<>'))
        if not target:return None
        need(not target.startswith('/')and '\\'not in target,'absolute or invalid public link')
        relative=posixpath.normpath(posixpath.join(posixpath.dirname(document),target))
        self.public_path(relative);return relative

    def documents(self):
        paths=set()
        for target in re.findall(r'\]\(([^)]+)\)',self.read(INDEX)):
            relative=self.link(INDEX,target)
            if relative and PurePosixPath(relative).parent==PurePosixPath(INDEX).parent and relative.endswith('.md')and relative!=INDEX:
                paths.add(relative)
        rows=[]
        for relative in sorted(paths):
            title=next((line[2:].strip()for line in self.read(relative).splitlines()if line.startswith('# ')),PurePosixPath(relative).stem)
            rows.append(dict(id=PurePosixPath(relative).stem,guide=relative,title=title))
        return rows

    def show(self,identifier):
        alias=DESCRIBED.get(identifier);target=alias['guide']if alias else identifier
        rows=[r for r in self.documents()if target in(r['id'],r['guide'])]
        need(len(rows)==1,'unknown or ambiguous report: '+identifier);row=rows[0]
        slug=next((k for k,s in DESCRIBED.items()if s['guide']==row['guide']),None)
        result=dict(schema='sgp-attribution-discovery-v1',scope='repository-navigation-only',**row,
            method=GUIDE,commands=None,command_discovery='not-described',limits=['No ROM/byte/execution/acceptance conclusion is inferred'])
        if slug:
            spec=DESCRIBED[slug];argv=['python3',spec['tool']]
            for flag in spec['parameters']:
                value='EN'if flag=='--language'else'<'+flag[2:].replace('-','_').upper()+'>'
                argv.extend([flag,value])
            argv.append('--prepare-only')
            self.public_path(spec['source_test'])
            result.update(command_discovery='three explicitly described interfaces; consult their guides for private schemas',
                owner='source/features/trainer-strategy/README.md',parents=spec['parents'],modeled_boundaries=spec['modeled_boundaries'],
                declared_execution_scope='isolated caller-derived inputs; later standalone results do not compose parents',
                recipe_kind='recovered assembly comparison artifact; original compiler not reconstructed; no installer',
                cli_inspection=declared_options(self.read(spec['tool'])),commands=dict(
                    help=dict(argv=['python3',spec['tool'],'--help'],effect='describe-only',requires_private_inputs=False,
                              requirements='Project Python environment; producer imports may require optional packages'),
                    prepare=dict(argv=argv,effect='describe-only',requires_private_inputs=True,
                                 requirements='Exact ROM, authenticated parent reports/objects/recipes/configuration as specified by the guide; optional historical parent source'),
                    source_tests=dict(argv=['python3','-m','unittest','discover','-s',PREFIX+'test','-p',PurePosixPath(spec['source_test']).name,'-v'],
                                      effect='describe-only',requires_private_inputs=False,requirements='Project Python environment; no guest CPU, but imports require Unicorn'),
                    private_replay=dict(argv=['python3','-m','unittest','discover','-s',PREFIX+'test','-p',spec['replay_pattern'],'-v'],
                                        env=spec['replay_env'],optional_env=['SGP_FS_SEND_PARENT_SOURCE']if slug=='native-fs-send'else[],
                                        effect='describe-only',requires_private_inputs=True,requirements='Private schemas and prerequisite artifacts in the guide; zero skips required for complete qualification')))
        if slug:
            for command in result['commands'].values():command['cwd']='.'
        return result

    def check(self):
        rows=self.documents();issues=[];guides={r['guide']for r in rows}
        for slug,spec in DESCRIBED.items():
            if spec['guide']not in guides:issues.append(slug+': described guide is absent from validation index');continue
            try:
                self.public_path(spec['source_test']);inspection=declared_options(self.read(spec['tool']))
                missing=set(spec['parameters']+['--prepare-only'])-set(inspection['declared_options'])
                if missing:issues.append(slug+': CLI flags missing: '+','.join(sorted(missing)))
                if inspection['unresolved_declarations']:issues.append(slug+': unresolved CLI declarations; static inspection cannot qualify this interface')
                declared_env=set()
                for test in spec['replay_tests']:
                    tree=ast.parse(self.read(test))
                    declared_env.update(n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)and type(n.value)is str and re.fullmatch('SGP_[A-Z0-9_]+',n.value))
                    if not fnmatch.fnmatchcase(PurePosixPath(test).name,spec['replay_pattern']):issues.append(slug+': replay filename pattern differs')
                expected_env=set(spec['replay_env']+(['SGP_FS_SEND_PARENT_SOURCE']if slug=='native-fs-send'else[]))
                if declared_env!=expected_env:issues.append(slug+': replay env declarations differ from the described interface')
            except(ValueError,SyntaxError)as error:issues.append(slug+': '+str(error))
        return dict(schema='sgp-attribution-discovery-v1',scope='repository-navigation-only',indexed_reports=len(rows),
                    described_interfaces=len(DESCRIBED),checks=['public index targets','three described guide/tool/test paths','limited static CLI flag agreement','three replay env declarations and filename patterns'],
                    issues=issues,commands_executed=0,producer_modules_imported=0)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    sub=p.add_subparsers(dest='command',required=True)
    for name in('list','show','check'):
        q=sub.add_parser(name);q.add_argument('--json',action='store_true')
        if name=='show':q.add_argument('case')
        if name=='list':q.add_argument('--match',default='')
    a=p.parse_args()
    try:
        c=Catalog(a.root)
        if a.command=='list':
            rows=[r for r in c.documents()if a.match.lower()in(r['id']+' '+r['title']).lower()]
            result=dict(schema='sgp-attribution-discovery-v1',scope='repository-navigation-only',reports=rows)
        else:result=c.show(a.case)if a.command=='show'else c.check()
    except(ValueError,OSError,SyntaxError)as error:
        if a.json:print(json.dumps(dict(schema='sgp-attribution-discovery-v1',scope='repository-navigation-only',issues=[str(error)])))
        else:print(str(error))
        return 1
    if a.json:print(json.dumps(result,sort_keys=True,indent=2))
    elif a.command=='list':
        for row in result['reports']:print(row['id']+' — '+row['title']+' — '+row['guide'])
    else:print(json.dumps(result,indent=2,sort_keys=True))
    return 1 if result.get('issues')else 0


if __name__=='__main__':raise SystemExit(main())
