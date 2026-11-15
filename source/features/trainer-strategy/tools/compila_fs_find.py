#!/usr/bin/env python3
"""Assemble recovered FindPath and check original layouts; no ROM output."""
from pathlib import Path
import argparse,importlib.util,json,re,subprocess,types


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


D=load('find_read_builder_parent',Path(__file__).with_name('compila_fs_read.py'))
E=load('find_builder_source_engine',Path(__file__).parents[1]/'test/caller_species_bench.py')
need,sha=D.need,D.sha
PARENT_SHA='92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788'
ENGINE_SHA='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31'
need(sha(Path(E.__file__).read_bytes())==ENGINE_SHA,'Find qualified source engine drift')
def definition_source(text,return_type,function):
    """Select a unique pinned top-level definition, skipping prototypes."""
    pattern=r'^'+re.escape(return_type+' '+function)+r'\([^;{}]*\)\s*\{'
    matches=list(re.finditer(pattern,text,re.M));need(len(matches)==1,'Find unique source definition '+function)
    start=matches[0].start();end=text.index('\n}\n',matches[0].end())+3
    return text[start:end]


BODIES={'path':(0x20D7FC0,324,'baf1c233ca8efcaa3ca58e996fe2f01e437fad5753dca7bbe1e6e782dd9abcf8')}
LAYOUT=D.C.LAYOUT+'''CHECK(sizeof(FSFileID)==8);
CHECK(__builtin_offsetof(FSDirPos,arc)==0);
CHECK(__builtin_offsetof(FSDirPos,own_id)==4);
CHECK(__builtin_offsetof(FSDirPos,index)==6);
CHECK(__builtin_offsetof(FSDirPos,pos)==8);
CHECK(OFF(arg.findpath.pos)==48);
CHECK(OFF(arg.findpath.path)==60);
CHECK(OFF(arg.findpath.find_directory)==64);
CHECK(OFF(arg.findpath.result)==68);
CHECK(FS_COMMAND_FINDPATH==4);
'''
source=Path(D.__file__).read_text();a=source.index('        layout = C.LAYOUT');b=source.index("        (out / 'layout.c')",a)
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'read_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ("'fs-read-'","'fs-find-'",1),('native_fs_read_','native_fs_find_',1),
    ('native-fs-read-recipe-v1','native-fs-find-recipe-v1',1),
    ("flags + ['-DBUILD_WRAPPER=' + str(int(role == 'wrapper')), '-c'","flags + ['-c'",1),
    (source[a:b],'        layout = LAYOUT\n',1),('fs_read_layout','fs_find_layout',2),
    ("('FSi_ReadFileCore', 'FS_ReadFile')","('FSi_FindPath',)",1),
    ("'int ' + function","'BOOL ' + function",1),
    ("            a = text.index('BOOL ' + function + '('); b = text.index('\\n}\\n', a) + 3\n",'',1),
    ("sha(text[a:b].encode())","sha(definition_source(text,'BOOL',function).encode())",1)],
    dict(__source_kind__='read_builder',__file__=__file__,LAYOUT=LAYOUT,BODIES=BODIES,definition_source=definition_source,
         RECIPE=Path(__file__).parents[1]/'sorgenti/fs-find.S'))


def build(out,cc='clang',reference=None):
    result=derive_build(out,cc,reference)
    result.update(source_recipe=RECIPE,rewrite_engine_sha256=ENGINE_SHA)
    if reference:
        ref=Path(reference);sources={}
        for rel,function in(('lib/NitroSDK/src/fs/FS_archive_suffix.c','BOOL FS_RegisterArchiveName('),
                             ('lib/NitroSDK/src/fs/FS_rom.c','void FSi_InitRom(')):
            p=ref/rel;text=p.read_text();return_type,name=function.split(' ',1);name=name.split('(')[0]
            sources[rel]=dict(sha256=sha(p.read_bytes()),function_body_sha256=sha(definition_source(text,return_type,name).encode()))
        result['root_initialization_source']=sources
    (Path(out)/'manifesto.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--cc',default='clang');p.add_argument('--reference',type=Path);a=p.parse_args()
    try:build(a.uscita,a.cc,a.reference)
    except(ValueError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('Recovered FindPath320 ARM+literal4 verified; original compiler provenance remains unknown')


if __name__=='__main__':main()
