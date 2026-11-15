#!/usr/bin/env python3
"""Build only the three memory Read comparison objects and a project test caller; reuse the pinned P80 builder.

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
L=load(HERE.with_name('rileggi_fs_memory_read.py'),'cached_open_recipe_components')
PARENT_SHA='4f814be3d68b307736fb25b8488a24132d18e99acc0679d528e6a9045fc94517'
BODIES={name:L.NEW[name]for name in('read_command','read_callback','close_command')}
RECIPE=HERE.parents[1]/'sorgenti/fs-memory-read.S'
SOURCES={**C.SOURCES,
 'lib/NitroSDK/src/fs/FS_file.c':'7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f',
 'lib/NitroSDK/src/fs/FS_archive_suffix.c':'ffbe5fe8c98c0042bf3f56964d17cef81b3047565c21ba8b69ae0bad8d0d2baf'}
DRIVER_RECIPE=HERE.parents[1]/'sorgenti/memory-narc-driver.S'
LAYOUT=C.LAYOUT+'''
CHECK(sizeof(FSReadFileInfo)==12); CHECK(OFF(arg.readfile.dst)==48);
CHECK(OFF(arg.readfile.len_org)==52); CHECK(OFF(arg.readfile.len)==56);
CHECK(OFF(prop.file.pos)==44); CHECK(__builtin_offsetof(FSArchive,base)==40);
CHECK(__builtin_offsetof(FSArchive,read_func)==72);
CHECK(FS_COMMAND_READFILE==0); CHECK(FS_COMMAND_CLOSEFILE==8);
CHECK(FS_FILE_STATUS_SYNC==4); CHECK(FS_FILE_STATUS_IS_FILE==16);
CHECK(FS_RESULT_PROC_ASYNC==6); CHECK(FS_RESULT_SUCCESS==0);
'''


def objects(out):
    loader=load(C.C.LOADER,'cached_open_text_loader');result={}
    for name,(address,size,digest)in BODIES.items():
        symbol='native_fs_cached_'+name
        blob,symbols=loader.load_text((Path(out)/(name+'.o')).read_bytes(),address,(symbol,))
        C.need(len(blob)==size and C.sha(blob)==digest and symbols[symbol]==address,'exact recovered memory Read '+name)
        result[name]=blob
    return result


def build(out,reference,cc='/Library/Developer/CommandLineTools/usr/bin/clang'):
    C.need(C.sha(Path(C.__file__).read_bytes())==PARENT_SHA,'qualified cached builder drift')
    resource_namespace=types.SimpleNamespace(COMPONENTS=BODIES,sha=L.sha,__file__=L.__file__)
    globals_map={**vars(C),'HERE':HERE,'R':resource_namespace,'RECIPE':RECIPE,'LAYOUT':LAYOUT,'objects':objects,'SOURCES':SOURCES}
    derive=types.FunctionType(C.build.__code__,globals_map)
    receipt=derive(out,reference,cc)
    receipt.update(schema='native-fs-memory-read-recipe-v1',parent_builder_sha256=PARENT_SHA,
        scope='Three recovered native objects80B and one project caller116B; twenty-seven retained SDK objects verified separately; no original C or ROM build')
    out=Path(out)
    compiler=Path(receipt['commands'][0]['argv'][0])
    argv=[str(compiler),'--target=armv5te-none-eabi','-mcpu=arm946e-s','-marm','-c',str(DRIVER_RECIPE),'-o',str(out/'driver.o')]
    result=subprocess.run(argv,capture_output=True,timeout=30)
    log=result.stdout+result.stderr;(out/'driver.log').write_bytes(log)
    receipt['commands'].append(dict(label='project-driver',argv=argv,exit_code=result.returncode,log_sha256=C.sha(log)))
    result.check_returncode()
    loader=load(C.C.LOADER,'memory_read_project_driver_loader')
    blob,symbols=loader.load_text((out/'driver.o').read_bytes(),L.DRIVER,('sgp_test_memory_narc_driver',))
    C.need(len(blob)==116 and symbols['sgp_test_memory_narc_driver']==L.DRIVER,'project driver entry/extent')
    import struct
    C.need(struct.unpack_from('<II',blob,108)==(L.RESULT,0x224c),'project driver owned literal pool')
    for offset,target in((0x14,0x20d8278),(0x28,0x20d83cc),(0x3c,0x20d83dc),(0x50,0x20d83cc),(0x5c,0x20d82c0)):
        word=int.from_bytes(blob[offset:offset+4],'little');C.need(word>>24==0xeb,'project driver ARM BL')
        delta=word&0xffffff
        if delta&0x800000:delta-=1<<24
        C.need((L.DRIVER+offset+8+(delta<<2))&0xffffffff==target,'project driver API BL target')
    receipt.update(driver_recipe_sha256=C.sha(DRIVER_RECIPE.read_bytes()),driver=dict(origin='Project-owned synthetic caller, not ROM code or installer',
        ram=L.DRIVER,bytes=116,code_bytes=108,pool_bytes=8,text_sha256=C.sha(blob),code_sha256=C.sha(blob[:108]),pool_sha256=C.sha(blob[108:]),
        entry_symbol='sgp_test_memory_narc_driver',object_sha256=C.sha((out/'driver.o').read_bytes())))
    (out/'manifesto.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--cc',default='/Library/Developer/CommandLineTools/usr/bin/clang');a=p.parse_args()
    try:build(a.uscita,a.reference,a.cc)
    except(ValueError,OSError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('ReadCommand44/ReadCallback28/Close8 and project caller116 verified; no ROM produced')


if __name__=='__main__':main()
