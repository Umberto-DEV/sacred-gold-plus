"""Bounded adapter of the qualified constructor bench for an outer caller.

The retained constructor bench stays byte-identical. Its nested SDK models are
reused verbatim; only driver setup, SDK dispatch and the outer API argument are
adapted. Any parent or transformation drift is refused before CPU execution.
"""
import ast,copy,hashlib,inspect,textwrap

PARENT_SHA256='2255805889cda2ef008ba221bdbb49f4dcbf7bc81805cf9dbc246f8d66e68639'
FUNCTION_SHA256='de6b5a87600bdd7e1c1339b37ba72ff355017e9088097de26807b7f6e964d36b'

def digest(data):return hashlib.sha256(data).hexdigest()
def demand(ok,reason):
 if not ok:raise ValueError(reason)

def nested_functions(function):
 return {node.name:digest(ast.dump(node,include_attributes=False).encode()) for node in ast.walk(function) if isinstance(node,ast.FunctionDef) and node is not function}

def adapt(bench_module,driver,*,source=None):
 """Return the adapted run function and its reproducible static receipt.

driver.configure(cpu, implementations, events, state, handles) returns the SDK
dispatch table. driver.prepare(cpu) initializes caller fixtures before any API.
driver.factory is the sole CPU creator; save_pointer supplies caller argument1.
"""
 from pathlib import Path
 demand(digest(Path(bench_module.__file__).read_bytes())==PARENT_SHA256,'caller adapter parent source drift')
 canonical=textwrap.dedent(inspect.getsource(bench_module.Bench.run));source=canonical if source is None else source
 demand(type(source)is str and digest(source.encode())==FUNCTION_SHA256,'caller adapter run source drift')
 tree=ast.parse(source);demand(len(tree.body)==1 and isinstance(tree.body[0],ast.FunctionDef),'caller adapter single method');function=tree.body[0];original=copy.deepcopy(function);before=nested_functions(original);demand(len(before)==19,'caller adapter qualified nested helper count')
 demand(function.name=='run' and not function.decorator_list and all(a.arg!='driver' for a in function.args.kwonlyargs),'caller adapter method signature')
 function.args.kwonlyargs.append(ast.arg(arg='driver'));function.args.kw_defaults.append(None)
 counts=dict(configure=0,prepare=0,argument=0);body=[]
 for statement in function.body:
  body.append(statement)
  # These are direct method-body statements, never nested SDK function bodies.
  if isinstance(statement,ast.Assign) and len(statement.targets)==1 and isinstance(statement.targets[0],ast.Name) and statement.targets[0].id=='implementations':
   demand(isinstance(statement.value,ast.Dict),'caller adapter original SDK dispatch table')
   body.extend(ast.parse('implementations = driver.configure(cpu, implementations, events, state, handles)').body);counts['configure']+=1
  if isinstance(statement,ast.Expr) and ast.dump(statement.value,include_attributes=False)==ast.dump(ast.parse('cpu.mem_write(STACK_TOP, STACK_CANARY)').body[0].value,include_attributes=False):
   body.extend(ast.parse('driver.prepare(cpu)').body);counts['prepare']+=1
  if isinstance(statement,ast.For) and isinstance(statement.iter,ast.Call) and isinstance(statement.iter.func,ast.Name) and statement.iter.func.id=='enumerate' and len(statement.iter.args)==1:
   value=statement.iter.args[0]
   if isinstance(value,ast.Tuple) and ast.dump(value,include_attributes=False)==ast.dump(ast.parse('(SETUP, index, 11)',mode='eval').body,include_attributes=False):
    value.elts[1]=ast.Attribute(value=ast.Name(id='driver',ctx=ast.Load()),attr='save_pointer',ctx=ast.Load());counts['argument']+=1
 function.body=body;demand(counts==dict(configure=1,prepare=1,argument=1),'caller adapter exact transformation sites');demand(nested_functions(function)==before,'caller adapter nested SDK model AST changed')
 # Reverse every permitted edit and demand full original AST equality. This
 # covers non-function statements and guards against an unintended fourth edit.
 reverse=copy.deepcopy(function);reverse.args.kwonlyargs.pop();reverse.args.kw_defaults.pop();clean=[]
 for statement in reverse.body:
  if isinstance(statement,ast.Assign) and isinstance(statement.value,ast.Call) and isinstance(statement.value.func,ast.Attribute) and isinstance(statement.value.func.value,ast.Name) and statement.value.func.value.id=='driver' and statement.value.func.attr=='configure':continue
  if isinstance(statement,ast.Expr) and isinstance(statement.value,ast.Call) and isinstance(statement.value.func,ast.Attribute) and isinstance(statement.value.func.value,ast.Name) and statement.value.func.value.id=='driver' and statement.value.func.attr=='prepare':continue
  for node in ast.walk(statement):
   if isinstance(node,ast.Tuple) and len(node.elts)==3 and isinstance(node.elts[1],ast.Attribute) and isinstance(node.elts[1].value,ast.Name) and node.elts[1].value.id=='driver' and node.elts[1].attr=='save_pointer':node.elts[1]=ast.Name(id='index',ctx=ast.Load())
  clean.append(statement)
 reverse.body=clean;demand(ast.dump(reverse,include_attributes=False)==ast.dump(original,include_attributes=False),'caller adapter changes outside declared edits')
 namespace=dict(vars(bench_module));demand(bench_module.ENTRY==0x2073604 and bench_module.STACK_TOP==0x23BF000,'caller adapter original constructor constants')
 extra={0x200BAF8:'CallerNewMsgData',0x200BBA0:'CallerNewString',0x200BB44:'CallerDestroyMsgData'};demand(not(set(extra)&set(bench_module.STUBS)),'caller adapter SDK address collision');namespace.update(Uc=driver.factory,ENTRY=0x20733C0,STACK_TOP=0x23BF000,GF_ASSERT=0x23BE100,WFC_HOOK=0x23BE104,STUBS={**bench_module.STUBS,**extra})
 ast.fix_missing_locations(tree);exec(compile(tree,'<qualified-caller-bench>','exec'),namespace);run=namespace['run']
 proof=dict(schema='qualified-caller-bench-adapter-v1',parent_sha256=PARENT_SHA256,function_source_sha256=FUNCTION_SHA256,original_ast_sha256=digest(ast.dump(original,include_attributes=False).encode()),adapted_ast_sha256=digest(ast.dump(function,include_attributes=False).encode()),nested_function_ast_sha256=before,transformations=counts,all_other_ast_unchanged=True,constructor_entry=hex(bench_module.ENTRY),outer_entry=hex(namespace['ENTRY']),outer_stack_top=hex(namespace['STACK_TOP']),sdk_extra={hex(a):name for a,name in extra.items()},assert_model_address=hex(namespace['GF_ASSERT']),wfc_model_address=hex(namespace['WFC_HOOK']))
 return run,proof
