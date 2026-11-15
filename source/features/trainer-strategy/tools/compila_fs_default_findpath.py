#!/usr/bin/env python3
"""Assemble only the default FindPath prefix and check original ARM32 layouts."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,types


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


D=load('default_findpath_read_builder',Path(__file__).with_name('compila_fs_read.py'))
F=load('default_findpath_definition',Path(__file__).with_name('compila_fs_find.py'))
E=load('default_findpath_source_engine',Path(__file__).parents[1]/'test/caller_species_bench.py')
need,sha=D.need,D.sha
PARENT_SHA='92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788'
need(sha(Path(F.__file__).read_bytes())=='5cef6e45d9706815b4a79ed16d4d0a0e8318702a92c7a3eeeea11ff87f385ff9'and
     sha(Path(E.__file__).read_bytes())=='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31','Default FindPath qualified build helpers drift')
BODIES={'command':(0x20D6DB0,28,'e2b54d82ad94489b669926c98c67c430df38f882e24e68ae646f660686de0233')}
OWNER_SHA='70727f66b05763ecfc2b1819f4580f5e0aa029b4cd6cc269776d722fa560e63e'
LAYOUT=F.LAYOUT+'''CHECK(sizeof(FSDirPos)==12);
CHECK(sizeof(FSFindPathInfo)==24); CHECK(sizeof(FSSeekDirInfo)==12);
CHECK(sizeof(FSDirEntry)==148); CHECK(__builtin_offsetof(FSDirEntry,name)==20);
CHECK(OFF(arg.seekdir.pos)==48); CHECK(OFF(arg.seekdir.pos)==OFF(arg.findpath.pos));
CHECK(FS_COMMAND_SEEKDIR==2); CHECK(FS_COMMAND_READDIR==3);
'''
source=Path(D.__file__).read_text();a=source.index('        layout = C.LAYOUT');b=source.index("        (out / 'layout.c')",a)
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'read_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ("'fs-read-'","'fs-default-findpath-'",1),('native_fs_read_','native_fs_default_findpath_',1),
    ('native-fs-read-recipe-v1','native-fs-default-findpath-prefix-recipe-v1',1),
    ("flags + ['-DBUILD_WRAPPER=' + str(int(role == 'wrapper')), '-c'","flags + ['-c'",1),
    (source[a:b],'        layout = LAYOUT\n',1),('fs_read_layout','fs_default_findpath_layout',2),
    ('lib/NitroSDK/src/fs/FS_file.c','lib/NitroSDK/src/fs/FS_command_default.c',1),
    ("('FSi_ReadFileCore', 'FS_ReadFile')","('FSi_FindPathCommand',)",1),
    ("            a = text.index('int ' + function + '('); b = text.index('\\n}\\n', a) + 3\n",'',1),
    ('sha(text[a:b].encode())',"sha(F.definition_source(text,'FSResult',function).encode())",1)],
    dict(__source_kind__='read_builder',__file__=__file__,F=F,LAYOUT=LAYOUT,BODIES=BODIES,
         RECIPE=Path(__file__).parents[1]/'sorgenti/fs-default-findpath-prefix.S'))


def build(out,cc='clang',reference=None):
    r=derive_build(out,cc,reference)
    r.update(source_recipe=RECIPE,rewrite_engine_sha256=sha(Path(E.__file__).read_bytes()),
        scope=dict(compiled_prefix_bytes=28,readback_owner_bytes=484,readback_owner_sha256=OWNER_SHA,
            nested_call='0x20d68c0',return_LR='0x20d6dcc',default_result_returned=False),
        limits='Recovered prefix assembly and original layouts only; no full default body or original Metrowerks C code generation')
    (Path(out)/'manifesto.json').write_text(json.dumps(r,indent=2)+'\n');return r


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--cc',default='clang');p.add_argument('--reference',type=Path);a=p.parse_args()
    try:build(a.uscita,a.cc,a.reference)
    except(ValueError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('Recovered default FindPath prefix28 verified; nested Translate and remaining default body excluded')


if __name__=='__main__':main()
