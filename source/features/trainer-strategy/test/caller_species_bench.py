"""Finite, source-authenticated composition of the qualified caller observers."""
import ast,copy,hashlib,types,textwrap
from pathlib import Path
PINS={
 'caller':'43f326704dcc3a85e4c888cbb3c3de9c972b88d8e3fb65e0cc98073402f3fa83',
 'message_caller':'f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632',
}
def need(ok,reason):
 if not ok:raise ValueError(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def rewrite(module,function,edits,namespace):
 """Authenticate the full parent, then apply enumerated exact source edits."""
 kind='caller' if function=='Driver.collect_body' and module.__name__.endswith('caller_parent') else 'message_caller'
 # Callers pass an explicit source kind: module aliases are not an authority.
 kind=namespace.pop('__source_kind__',kind)
 source=Path(module.__file__).read_text();need(sha(source.encode())==PINS[kind],'species caller parent source drift: '+kind)
 tree=ast.parse(source);parts=function.split('.');nodes=tree.body
 for part in parts:
  node=next(n for n in nodes if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==part);nodes=node.body
 original=ast.get_source_segment(source,node);changed=original;receipt=[]
 for old,new,count in edits:
  need(changed.count(old)==count,'species caller finite recipe occurrence: '+old);changed=changed.replace(old,new);receipt.append(dict(before=old,after=new,count=count))
 newtree=ast.parse(changed);need(len(newtree.body)==1 and isinstance(newtree.body[0],ast.FunctionDef),'species caller exact function wrapper')
 scope=dict(vars(module));scope.update(namespace);exec(compile(newtree,str(Path(__file__).name)+':'+function,'exec'),scope);result=scope[node.name]
 return result,dict(parent_sha256=PINS[kind],function=function,edits=receipt,original_ast_sha256=sha(ast.dump(ast.parse(original),include_attributes=False).encode()),derived_ast_sha256=sha(ast.dump(newtree,include_attributes=False).encode()))

def adapt(bench,driver):
 V=driver.composition;run,proof=V.A.adapt(bench,driver);old=dict(run.__globals__['STUBS']);need(old==bench.STUBS and old.get(0x200BCDC)=='GetSpeciesName','species caller effective parent SDK table')
 run.__globals__['STUBS']={k:v for k,v in old.items() if k!=0x200BCDC}
 return run,dict(schema='native-species-caller-adapter-v1',inherited=proof,removed_high_level_sdk={'0x200bcdc':'GetSpeciesName'},effective_sdk={hex(k):v for k,v in run.__globals__['STUBS'].items()},isolated_namespace_only=True)
