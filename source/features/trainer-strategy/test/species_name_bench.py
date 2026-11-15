"""Finite heap0/bank237/species profile of authenticated message SDK models.

Only fixture domain and SDK argument expectations change. Native code, cipher
algorithms, ownership models and every other statement remain unchanged.
"""
from pathlib import Path
import ast,copy,hashlib,inspect,textwrap,types
PARENT_SHA256='2a00534ad4df6ff15d18a357524daa8aae6f46516efc9dc8b9aff3cee08a46b8'
SPECIES=(355,353,93,200,302,94)
def demand(ok,reason):
 if not ok:raise ValueError(reason)
def digest(blob):return hashlib.sha256(blob).hexdigest()
def module_hash(nodes):return digest(ast.dump(ast.Module(body=nodes,type_ignores=[]),include_attributes=False).encode())

def profile(message):
 demand(digest(Path(message.__file__).read_bytes())==PARENT_SHA256,'species profile message source drift')
 originals={name:ast.parse(textwrap.dedent(inspect.getsource(getattr(message.Message,name)))).body[0] for name in ('__init__','service')};changed=copy.deepcopy(originals)
 tuples=[n for n in ast.walk(changed['__init__']) if isinstance(n,ast.Tuple) and all(isinstance(e,ast.Constant) and type(e.value)is int for e in n.elts) and [e.value for e in n.elts]==[21,31]]
 demand(len(tuples)==1,'species profile exact fixture ID domain site');tuples[0].elts=[ast.Constant(value=s) for s in SPECIES]
 heaps=[n for n in ast.walk(changed['service']) if isinstance(n,ast.Constant) and type(n.value)is int and n.value==11];banks=[n for n in ast.walk(changed['service']) if isinstance(n,ast.Constant) and type(n.value)is int and n.value==729]
 demand(len(heaps)==2 and len(banks)==1,'species profile exact heap/bank model sites')
 for n in heaps:n.value=0
 banks[0].value=237
 # Reverse the complete allowlist of edits and authenticate whole function
 # signatures/wrappers/bodies, not just an interior statement slice.
 reverse=copy.deepcopy(changed);domain=[n for n in ast.walk(reverse['__init__']) if isinstance(n,ast.Tuple) and len(n.elts)==len(SPECIES) and all(isinstance(e,ast.Constant) and type(e.value)is int for e in n.elts) and tuple(e.value for e in n.elts)==SPECIES]
 demand(len(domain)==1,'species profile reverse fixture domain');domain[0].elts=[ast.Constant(21),ast.Constant(31)]
 # Record structural locations before mutation, avoiding substitution of other
 # zero constants already present in the model.
 def restore(old,new):
  if isinstance(old,ast.Constant) and type(old.value)is int and old.value in (11,729):
   demand(isinstance(new,ast.Constant) and new.value==(0 if old.value==11 else 237),'species profile model constant substitution');new.value=old.value;return
  demand(type(old)is type(new),'species profile AST node type drift')
  for field,value in ast.iter_fields(old):
   other=getattr(new,field)
   if isinstance(value,ast.AST):restore(value,other)
   elif isinstance(value,list):
    demand(len(value)==len(other),'species profile AST list drift')
    for left,right in zip(value,other):
     if isinstance(left,ast.AST):restore(left,right)
     else:demand(left==right,'species profile AST scalar list drift')
   else:demand(value==other,'species profile AST scalar drift')
 restore(originals['service'],reverse['service'])
 demand(all(module_hash([originals[n]])==module_hash([reverse[n]]) for n in originals),'species profile statements outside declared edits')
 namespace=dict(vars(message));bound=type('SpeciesMessage',(message.Message,),{});namespace['Message']=bound
 tree=ast.Module(body=list(changed.values()),type_ignores=[]);ast.fix_missing_locations(tree);temporary=dict(vars(message));exec(compile(tree,'<qualified-species-message-models>','exec'),temporary)
 for name,method in vars(message.Message).items():
  if isinstance(method,types.FunctionType):
   code=temporary[name].__code__ if name in changed else method.__code__;function=types.FunctionType(code,namespace,method.__name__,method.__defaults__,method.__closure__);function.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,function)
 demand({key for key in namespace if namespace[key]is not vars(message).get(key)}=={'Message'},'species profile undeclared global binding')
 return bound,namespace,dict(schema='finite-species-message-models-v1',parent_sha256=PARENT_SHA256,species=list(SPECIES),heap=0,bank=237,transformed_methods={name:dict(original_ast_sha256=module_hash([originals[name]]),profile_ast_sha256=module_hash([changed[name]])) for name in originals},edits=dict(fixture_domain=1,heap_constants=2,bank_constant=1),all_other_AST_unchanged=True,scope='SDK fixture expectations only; native code never transformed')
