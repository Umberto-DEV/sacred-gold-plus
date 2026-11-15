#!/usr/bin/env python3
"""Assemble recovered Wakeup and verify original ARM32 layouts; no ROM output."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,types


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


D=load('os_wakeup_read_builder_parent',Path(__file__).with_name('compila_fs_read.py'))
F=load('os_wakeup_definition_helper',Path(__file__).with_name('compila_fs_find.py'))
E=load('os_wakeup_builder_source_engine',Path(__file__).parents[1]/'test/caller_species_bench.py')
need,sha=D.need,D.sha
PARENT_SHA='92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788'
need(sha(Path(F.__file__).read_bytes())=='5cef6e45d9706815b4a79ed16d4d0a0e8318702a92c7a3eeeea11ff87f385ff9'and
     sha(Path(E.__file__).read_bytes())=='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31',
     'Wakeup qualified definition/source engine drift')
BODIES={'command':(0x20D1ECC,104,'25c7d621d6b4d855be6828b9ec8d98162df8ecdda5a22db405caf344aa4102db')}
LAYOUT=D.C.LAYOUT+'''CHECK(sizeof(OSThreadQueue)==8); CHECK(_Alignof(OSThreadQueue)==4);
CHECK(__builtin_offsetof(OSThreadQueue,head)==0);
CHECK(__builtin_offsetof(OSThreadQueue,tail)==4);
CHECK(_Alignof(u64)==8); CHECK(sizeof(CPContext)==28); CHECK(_Alignof(CPContext)==4);
CHECK(sizeof(OSContext)==100); CHECK(_Alignof(OSContext)==4);
CHECK(sizeof(OSThread)==192); CHECK(_Alignof(OSThread)==4);
CHECK(__builtin_offsetof(OSContext,cp_context)==72);
CHECK(sizeof(OSThreadState)==4); CHECK(OS_THREAD_STATE_READY==1);
CHECK(__builtin_offsetof(OSThread,state)==0x64);
CHECK(__builtin_offsetof(OSThread,queue)==0x78);
CHECK(__builtin_offsetof(OSThread,link.prev)==0x7C);
CHECK(__builtin_offsetof(OSThread,link.next)==0x80);
'''
source=Path(D.__file__).read_text();a=source.index('        layout = C.LAYOUT');b=source.index("        (out / 'layout.c')",a)
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'read_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ("'fs-read-'","'os-wakeup-'",1),('native_fs_read_','native_os_wakeup_',1),
    ('native-fs-read-recipe-v1','native-os-wakeup-recipe-v1',1),
    ("flags + ['-DBUILD_WRAPPER=' + str(int(role == 'wrapper')), '-c'","flags + ['-c'",1),
    ("'-marm']","'-marm', '-mabi=apcs-gnu']",1),
    (source[a:b],'        layout = LAYOUT\n',1),('fs_read_layout','os_wakeup_layout',2),
    ('lib/NitroSDK/src/fs/FS_file.c','lib/NitroSDK/src/os/os_thread.c',1),
    ("('FSi_ReadFileCore', 'FS_ReadFile')","('OS_WakeupThread',)",1),
    ("            a = text.index('int ' + function + '('); b = text.index('\\n}\\n', a) + 3\n",'',1),
    ('sha(text[a:b].encode())',"sha(F.definition_source(text,'void',function).encode())",1)],
    dict(__source_kind__='read_builder',__file__=__file__,F=F,LAYOUT=LAYOUT,BODIES=BODIES,
         RECIPE=Path(__file__).parents[1]/'sorgenti/os-wakeup.S'))


def build(out,cc='clang',reference=None):
    result=derive_build(out,cc,reference);result.update(source_recipe=RECIPE,
        rewrite_engine_sha256=sha(Path(E.__file__).read_bytes()))
    if reference:
        ref=Path(reference);header=ref/'lib/include/nitro/os/common/thread_shared.h'
        result['queue_inline_source']=dict(path=str(header.relative_to(ref)),sha256=sha(header.read_bytes()),
            definition_sha256=sha(F.definition_source(header.read_text(),'static inline void','OS_InitThreadQueue').encode()),
            activation='Expanded in full body but skipped on the qualified empty-head path')
    result['qualified_runtime_scope']='Empty queue only; nonempty thread stores and reschedule remain unqualified'
    result['layout_abi_compatibility']=dict(flag='-mabi=apcs-gnu',u64_queried_alignment=8,CPContext_bytes=28,CPContext_alignment=4,OSContext_bytes=100,OSContext_alignment=4,
        installed_thread_offsets=dict(state=100,queue=120,link_prev=124,link_next=128),
        meaning='Pinned-header compatibility with installed offsets; original MW compiler/flags and C binary not reconstructed',
        default_eabi_probe_invoked=False,nonempty_thread_runtime_qualified=False)
    if reference:
        result['reference']['limits']='Pinned headers with explicit Clang APCS GNU layout compatibility; default EABI differs for CPContext/OSThread. Recovered assembly only, not original compiler/flags or C binary reconstruction.'
    (Path(out)/'manifesto.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--cc',default='clang');p.add_argument('--reference',type=Path);a=p.parse_args()
    try:build(a.uscita,a.cc,a.reference)
    except(ValueError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('Recovered Wakeup104 ARM bytes verified; original native compiler provenance remains unknown')


if __name__=='__main__':main()
