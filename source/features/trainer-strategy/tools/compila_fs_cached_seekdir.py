#!/usr/bin/env python3
"""Reassemble four cached SeekDir components; original SDK headers check ABI.

Does not produce or patch a ROM. The original Metrowerks C code generator is
unavailable; exact bytes here establish recovered-assembly matching only.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import shlex
import shutil
import subprocess


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
R=load(HERE.with_name('rileggi_fs_cached_resources.py'),'cached_recipe_resources')
C=load(HERE.with_name('compila_fs_init.py'),'cached_recipe_layout')
need,sha=R.need,R.sha
SOURCE=HERE.parents[3]
RECIPE=HERE.parents[1]/'sorgenti/fs-cached-seekdir.S'
CC_SHA='fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
SOURCES={'lib/NitroSDK/src/fs/fs_private.h':'b3abfe01ae14a8b64fd68372a4e0646f975373dd296626d4396ffc113c3a122c',
         'lib/NitroSDK/src/fs/FS_command_default.c':'040f053d87d157231bcd051731eee8bf27768a9103940b6c4016f9cf703ca513',
         'lib/NitroSDK/src/fs/FS_archive_prefix.c':'d359268374ed97b359e4344a820c892382fd23f8923d2895a828175662ae3f2d',
         'lib/NitroSDK/src/mi/mi_memory.c':'7bfc34240ca43ec5c45773a7dad14547b0bb38fe7638c055a0f735e0aa0eb592'}
LAYOUT=C.LAYOUT+'''
typedef struct { FSArchive *arc; u32 pos; } FSiSyncReadParam;
CHECK(sizeof(FSArchive)==92); CHECK(sizeof(FSArchiveFNT)==8);
CHECK(sizeof(FSiSyncReadParam)==8); CHECK(sizeof(FSSeekDirInfo)==12);
CHECK(__builtin_offsetof(FSArchive,flag)==28);
CHECK(__builtin_offsetof(FSArchive,fnt)==52);
CHECK(__builtin_offsetof(FSArchive,table_func)==80);
CHECK(__builtin_offsetof(FSArchiveFNT,index)==4);
CHECK(__builtin_offsetof(FSArchiveFNT,parent)==6);
CHECK(OFF(prop.dir.pos)==32); CHECK(OFF(prop.dir.parent)==44);
CHECK(OFF(arg.seekdir.pos)==48);
CHECK(__builtin_offsetof(FSDirPos,own_id)==4);
CHECK(__builtin_offsetof(FSDirPos,index)==6);
CHECK(__builtin_offsetof(FSDirPos,pos)==8);
CHECK(FS_COMMAND_SEEKDIR==2); CHECK(FS_RESULT_SUCCESS==0);
'''


def objects(out):
    loader=load(C.LOADER,'cached_recipe_text_loader');result={}
    for role,(address,size,digest)in R.COMPONENTS.items():
        path=Path(out)/(role+'.o');symbol='native_fs_cached_'+role
        blob,symbols=loader.load_text(path.read_bytes(),address,(symbol,))
        need(len(blob)==size and sha(blob)==digest and symbols[symbol]==address,'exact recovered '+role)
        result[role]=blob
    return result


def build(out,reference,cc='/Library/Developer/CommandLineTools/usr/bin/clang'):
    out=Path(out).resolve();reference=Path(reference).resolve()
    need(out!=SOURCE and SOURCE not in out.parents and not out.exists() and not out.is_symlink(),'fresh output outside source required')
    compiler=Path(shutil.which(cc)or cc).resolve()
    need(compiler.is_file() and sha(compiler.read_bytes())==CC_SHA,'authenticated production compiler required')
    need(subprocess.check_output(['git','-C',str(reference),'rev-parse','HEAD'],text=True).strip()==C.PIN and
         not subprocess.check_output(['git','-C',str(reference),'status','--porcelain']), 'clean pinned SDK reference')
    for relative,digest in SOURCES.items():need(sha((reference/relative).read_bytes())==digest,'SDK source identity '+relative)
    need('typedef struct { FSArchive *arc; u32 pos; } FSiSyncReadParam;' in
         (reference/'lib/NitroSDK/src/fs/fs_private.h').read_text(),'original private parameter typedef')
    out.mkdir(parents=True);commands=[]
    def run(label,argv):
        result=subprocess.run(argv,capture_output=True,timeout=30)
        blob=result.stdout+result.stderr;(out/(label+'.log')).write_bytes(blob)
        commands.append(dict(label=label,argv=argv,exit_code=result.returncode,log_sha256=sha(blob)))
        result.check_returncode()
    flags=[str(compiler),'--target=armv5te-none-eabi','-mcpu=arm946e-s','-marm']
    for role in R.COMPONENTS:
        run(role,flags+['-DBUILD_'+role.upper(),'-c',str(RECIPE),'-o',str(out/(role+'.o'))])
    blobs=objects(out)
    (out/'layout.c').write_text(LAYOUT)
    run('layout',flags+['-DSDK_ARM9','-I',str(reference/'lib/include'),'-I',str(reference/'lib/NitroSDK/src/fs'),
        '-MMD','-MT','cached_seekdir_layout','-MF',str(out/'layout.d'),'-fsyntax-only',str(out/'layout.c')])
    dep=(out/'layout.d').read_text().replace('\\\n',' ')
    headers={}
    for value in shlex.split(dep.split(':',1)[1].replace('$$','$')):
        path=Path(value).resolve()
        if path.is_relative_to(reference):headers[str(path.relative_to(reference))]=sha(path.read_bytes())
    need(all('lib/include/nitro/'+name in headers for name in ('fs/file.h','fs/archive.h','types.h','os/common/thread_shared.h')),'original ABI dependency provenance')
    receipt=dict(schema='native-fs-cached-seekdir-recipe-v1',builder_sha256=sha(HERE.read_bytes()),
        resource_reader_sha256=sha(Path(R.__file__).read_bytes()),layout_helper_sha256=sha(Path(C.__file__).read_bytes()),
        loader_sha256=sha(C.LOADER.read_bytes()),recipe_sha256=sha(RECIPE.read_bytes()),
        compiler_sha256=CC_SHA,compiler_version=subprocess.check_output([str(compiler),'--version'],text=True).splitlines()[0],
        source_pin=C.PIN,source_sha256=SOURCES,header_sha256=headers,layout_passed=True,
        objects={name:dict(ram=R.COMPONENTS[name][0],bytes=len(blob),sha256=sha(blob),object_sha256=sha((out/(name+'.o')).read_bytes()))for name,blob in blobs.items()},
        commands=commands,recipe_is_recovered=True,original_C_codegen_reconstructed=False,ROM_produced=False)
    (out/'manifesto.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--cc',default='/Library/Developer/CommandLineTools/usr/bin/clang');a=p.parse_args()
    try:build(a.uscita,a.reference,a.cc)
    except(ValueError,OSError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('Four recovered components752 bytes matched; original ABI checked, no ROM produced')


if __name__=='__main__':main()
