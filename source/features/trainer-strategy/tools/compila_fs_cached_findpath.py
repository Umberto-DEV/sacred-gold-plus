#!/usr/bin/env python3
"""Build only the three new comparison objects; reuse the pinned P80 builder.

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
C=load(HERE.with_name('compila_fs_cached_seekdir.py'),'cached_find_pinned_builder')
L=load(HERE.with_name('rileggi_fs_cached_findpath.py'),'cached_find_recipe_components')
PARENT_SHA='4f814be3d68b307736fb25b8488a24132d18e99acc0679d528e6a9045fc94517'
BODIES={name:L.NEW[name]for name in('findpath','read_dir','strnicmp')}
RECIPE=HERE.parents[1]/'sorgenti/fs-cached-findpath.S'
LAYOUT=C.LAYOUT+'''
CHECK(sizeof(FSDirEntry)==148); CHECK(__builtin_offsetof(FSDirEntry,name)==20);
CHECK(__builtin_offsetof(FSDirEntry,is_directory)==12);
CHECK(__builtin_offsetof(FSDirEntry,name_len)==16);
CHECK(sizeof(FSReadDirInfo)==8); CHECK(__builtin_offsetof(FSReadDirInfo,p_entry)==0);
CHECK(__builtin_offsetof(FSReadDirInfo,skip_string)==4);
CHECK(OFF(arg.findpath.path)==60); CHECK(OFF(arg.findpath.find_directory)==64);
CHECK(OFF(arg.findpath.result)==68); CHECK(FS_COMMAND_READDIR==3);
CHECK(FS_COMMAND_FINDPATH==4);
'''


def objects(out):
    loader=load(C.C.LOADER,'cached_find_text_loader');result={}
    for name,(address,size,digest)in BODIES.items():
        symbol='native_fs_cached_'+name
        blob,symbols=loader.load_text((Path(out)/(name+'.o')).read_bytes(),address,(symbol,))
        C.need(len(blob)==size and C.sha(blob)==digest and symbols[symbol]==address,'exact recovered FindPath '+name)
        result[name]=blob
    return result


def build(out,reference,cc='/Library/Developer/CommandLineTools/usr/bin/clang'):
    C.need(C.sha(Path(C.__file__).read_bytes())==PARENT_SHA,'qualified cached builder drift')
    resource_namespace=types.SimpleNamespace(COMPONENTS=BODIES,sha=L.sha,__file__=L.__file__)
    globals_map={**vars(C),'HERE':HERE,'R':resource_namespace,'RECIPE':RECIPE,'LAYOUT':LAYOUT,'objects':objects}
    derive=types.FunctionType(C.build.__code__,globals_map)
    receipt=derive(out,reference,cc)
    receipt.update(schema='native-fs-cached-findpath-recipe-v1',parent_builder_sha256=PARENT_SHA,
        scope='Three new recovered objects864B only; five retained components are verified separately; no original C or ROM build')
    (Path(out)/'manifesto.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--cc',default='/Library/Developer/CommandLineTools/usr/bin/clang');a=p.parse_args()
    try:build(a.uscita,a.reference,a.cc)
    except(ValueError,OSError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('Find484/ReadDir300/Str80 exact; pinned shared builder/layout, no ROM produced')


if __name__=='__main__':main()
