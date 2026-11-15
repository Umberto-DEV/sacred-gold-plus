#!/usr/bin/env python3
"""Build only the two new cached Open comparison objects; reuse the pinned P80 builder.

The shared builder has no SeekDir runtime assumption: component metadata,
recipe, layout assertions and ELF extraction are explicit globals below.
No original C code generator or installed ROM is modified.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import subprocess
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
C=load(HERE.with_name('compila_fs_cached_seekdir.py'),'cached_open_pinned_builder')
L=load(HERE.with_name('rileggi_fs_cached_open.py'),'cached_open_recipe_components')
PARENT_SHA='4f814be3d68b307736fb25b8488a24132d18e99acc0679d528e6a9045fc94517'
BODIES={name:L.NEW[name]for name in('fast_command','direct_command')}
RECIPE=HERE.parents[1]/'sorgenti/fs-cached-open.S'
LAYOUT=C.LAYOUT+'''
CHECK(sizeof(FSArchiveFAT)==8); CHECK(__builtin_offsetof(FSArchiveFAT,bottom)==4);
CHECK(__builtin_offsetof(FSArchive,fat)==44); CHECK(__builtin_offsetof(FSArchive,fat_size)==48);
CHECK(sizeof(FSOpenFileFastInfo)==8); CHECK(sizeof(FSOpenFileDirectInfo)==12);
CHECK(OFF(arg.openfilefast.id.file_id)==52);
CHECK(OFF(arg.openfiledirect.top)==48); CHECK(OFF(arg.openfiledirect.bottom)==52);
CHECK(OFF(arg.openfiledirect.index)==56); CHECK(OFF(prop.file.own_id)==32);
CHECK(OFF(prop.file.top)==36); CHECK(OFF(prop.file.bottom)==40); CHECK(OFF(prop.file.pos)==44);
CHECK(FS_COMMAND_OPENFILEFAST==6); CHECK(FS_COMMAND_OPENFILEDIRECT==7);
CHECK(FS_COMMAND_INVALID==14); CHECK(FS_RESULT_FAILURE==1);
'''


def objects(out):
    loader=load(C.C.LOADER,'cached_open_text_loader');result={}
    for name,(address,size,digest)in BODIES.items():
        symbol='native_fs_cached_'+name
        blob,symbols=loader.load_text((Path(out)/(name+'.o')).read_bytes(),address,(symbol,))
        C.need(len(blob)==size and C.sha(blob)==digest and symbols[symbol]==address,'exact recovered Open '+name)
        result[name]=blob
    return result


def build(out,reference,cc='/Library/Developer/CommandLineTools/usr/bin/clang'):
    C.need(C.sha(Path(C.__file__).read_bytes())==PARENT_SHA,'qualified cached builder drift')
    resource_namespace=types.SimpleNamespace(COMPONENTS=BODIES,sha=L.sha,__file__=L.__file__)
    globals_map={**vars(C),'HERE':HERE,'R':resource_namespace,'RECIPE':RECIPE,'LAYOUT':LAYOUT,'objects':objects}
    derive=types.FunctionType(C.build.__code__,globals_map)
    receipt=derive(out,reference,cc)
    receipt.update(schema='native-fs-cached-open-recipe-v1',parent_builder_sha256=PARENT_SHA,
        scope='Two new recovered objects168B only; twenty retained components are verified separately; no original C or ROM build')
    (Path(out)/'manifesto.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--cc',default='/Library/Developer/CommandLineTools/usr/bin/clang');a=p.parse_args()
    try:build(a.uscita,a.reference,a.cc)
    except(ValueError,OSError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('FastCommand128/DirectCommand40 exact; pinned shared builder/layout, no ROM produced')


if __name__=='__main__':main()
