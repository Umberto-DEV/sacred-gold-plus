"""Finite stack-destination PP profile; authenticated immutable parent composition."""
from pathlib import Path
import types,copy
H=None
PARENT_SHA256='729a6969a9a28b25f18b4f4720cdcf96d55a424178569eb74af216f03a07d0de'
ADAPTER_SHA256='1d724ba85b7512575566a9e935c31e09adb64635245b7180c1753015e9f7b8c4'
def bind(parent):
 global H
 parent.need(parent.sha(Path(parent.__file__).read_bytes())==PARENT_SHA256 and parent.sha(Path(parent.A.__file__).read_bytes())==ADAPTER_SHA256,'PP parent source drift');H=parent

def rewrite(module,function,edits,namespace,kind):
 H.need(H is not None,'bind PP parent');scope=dict(vars(H.X.A));scope['PINS']={**H.X.A.PINS,**H.Y.A.PINS,'header_caller':H.Z.A.PARENT_SHA256,'prefix_caller':H.J.A.PARENT_SHA256,'personal_caller':H.G.A.PARENT_SHA256,'growth_caller':H.A.PARENT_SHA256,'friendship_caller':PARENT_SHA256};fn=types.FunctionType(H.X.A.rewrite.__code__,scope);return fn(module,function,edits,{**namespace,'__source_kind__':kind})
def inherited(index,extra=()):return [(e['before'],e['after'],e['count']) for e in H.RECIPES[index]['edits']]+list(extra)
def adapt(bench,driver):
 run,proof=H.A.adapt(bench,driver);return run,dict(schema='native-pp-caller-adapter-v1',inherited=proof,effective_sdk=proof['effective_sdk'],native_owner='first CUSTOM move310 PP read after CreateMon return; stack destination; default learnset reads remain modeled')
RESULT_SOURCE_SHA256='0199a89927cbbcb08ed8f13d2a124380cd16da6c8b4dd7dacf6a4b43117d9090'
def counter_result_oracle():
 source=H.V.A.constructor_result;H.need(H.sha(Path(H.V.A.__file__).read_bytes())==RESULT_SOURCE_SHA256,'PP complete constructor result source drift');original=source.__globals__['T'];H.need(original is H.T,'PP semantic counter requires original bound constructor oracle')
 def expected(data,plus):
  records=copy.deepcopy(original.expected(data,plus));H.need(records[0]['fields']['moves'][0]==310 and records[0]['fields']['pp'][0]==15,'PP semantic counter original first slot source profile');records[0]['fields']['pp'][0]=1;return records
 proxy=types.SimpleNamespace(**vars(original));proxy.expected=expected;H.need(proxy.M is original.M and all(getattr(proxy,k)is v for k,v in vars(original).items() if k!='expected'),'PP semantic proxy changes only host expected')
 namespace={**source.__globals__,'T':proxy};result=types.FunctionType(source.__code__,namespace,source.__name__,source.__defaults__,source.__closure__);result.__kwdefaults__=source.__kwdefaults__;H.need(result.__code__ is source.__code__ and set(namespace)==set(source.__globals__) and [k for k,v in source.__globals__.items() if namespace[k]is not v]==['T'],'PP semantic counter complete bytecode unchanged; only T namespace differs');return result

def constructor_result(r,data,qualified):
 if 'pp_expected_slot0' not in data:return H.A.constructor_result(r,data,qualified)
 H.need(type(data['pp_expected_slot0'])is int and data['pp_expected_slot0']==1,'finite PP semantic expectation flag');return counter_result_oracle()(r,data,qualified)
def constructor_evidence(*args):return H.A.constructor_evidence(*args)
