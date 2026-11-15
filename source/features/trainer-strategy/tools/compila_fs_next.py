#!/usr/bin/env python3
"""Assemble recovered Next and verify original ARM32 layouts; no ROM output."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,types


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


D=load('next_read_builder_parent',Path(__file__).with_name('compila_fs_read.py'))
F=load('next_definition_helper',Path(__file__).with_name('compila_fs_find.py'))
E=load('next_builder_source_engine',Path(__file__).parents[1]/'test/caller_species_bench.py')
need,sha=D.need,D.sha
PARENT_SHA='92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788'
need(sha(Path(F.__file__).read_bytes())=='5cef6e45d9706815b4a79ed16d4d0a0e8318702a92c7a3eeeea11ff87f385ff9'and
     sha(Path(E.__file__).read_bytes())=='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31',
     'Next qualified definition/source engine drift')
BODIES={'command':(0x20D749C,532,'d3785eb030614f3050cb9ef747e3a173e534c40ef5ffa3d75c95acd6fa778e9c')}
LAYOUT=D.C.LAYOUT+'''#define ARC_OFF(f) __builtin_offsetof(FSArchive,f)
CHECK(sizeof(FSArchive)==92); CHECK(_Alignof(FSArchive)==4);
CHECK(ARC_OFF(flag)==28); CHECK(ARC_OFF(list)==32);
CHECK(ARC_OFF(list.prev)==32); CHECK(ARC_OFF(list.next)==36);
CHECK(ARC_OFF(proc)==84); CHECK(ARC_OFF(proc_flag)==88);
CHECK(FS_COMMAND_FINDPATH==4); CHECK(FS_COMMAND_ACTIVATE==9);
CHECK(FS_RESULT_SUCCESS==0); CHECK(FS_RESULT_FAILURE==1);
CHECK(FS_RESULT_BUSY==2); CHECK(FS_RESULT_CANCELED==3);
CHECK(FS_FILE_STATUS_BUSY==1); CHECK(FS_FILE_STATUS_SYNC==4);
CHECK(FS_FILE_STATUS_OPERATING==0x40);
CHECK(FS_ARCHIVE_FLAG_REGISTER==1); CHECK(FS_ARCHIVE_FLAG_LOADED==2);
CHECK(FS_ARCHIVE_FLAG_SUSPEND==8); CHECK(FS_ARCHIVE_FLAG_RUNNING==16);
CHECK(FS_ARCHIVE_FLAG_UNLOADING==128);
CHECK(FS_ARCHIVE_PROC_ACTIVATE==0x200); CHECK(FS_ARCHIVE_PROC_IDLE==0x400);
CHECK(FS_ARCHIVE_FLAG_CANCELING==0x20); CHECK(FS_ARCHIVE_FLAG_SUSPENDING==0x40);
CHECK(FS_FILE_STATUS_CANCEL==2); CHECK(FS_COMMAND_IDLE==10);
CHECK(ARC_OFF(stat_q)==20); CHECK(_Alignof(FSFile)==4);

'''
source=Path(D.__file__).read_text();a=source.index('        layout = C.LAYOUT');b=source.index("        (out / 'layout.c')",a)
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'read_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ("'fs-read-'","'fs-next-'",1),('native_fs_read_','native_fs_next_',1),
    ('native-fs-read-recipe-v1','native-fs-next-recipe-v1',1),
    ("flags + ['-DBUILD_WRAPPER=' + str(int(role == 'wrapper')), '-c'","flags + ['-c'",1),
    (source[a:b],'        layout = LAYOUT\n',1),('fs_read_layout','fs_next_layout',2),
    ('lib/NitroSDK/src/fs/FS_file.c','lib/NitroSDK/src/fs/FS_archive_prefix.c',1),
    ("('FSi_ReadFileCore', 'FS_ReadFile')","('FSi_NextCommand',)",1),
    ("            a = text.index('int ' + function + '('); b = text.index('\\n}\\n', a) + 3\n",'',1),
    ('sha(text[a:b].encode())',"sha(F.definition_source(text,'FSFile *',function).encode())",1)],
    dict(__source_kind__='read_builder',__file__=__file__,F=F,LAYOUT=LAYOUT,BODIES=BODIES,
         RECIPE=Path(__file__).parents[1]/'sorgenti/fs-next.S'))


def build(out,cc='clang',reference=None):
    result=derive_build(out,cc,reference);result.update(source_recipe=RECIPE,
        rewrite_engine_sha256=sha(Path(E.__file__).read_bytes()))
    if reference:
        ref=Path(reference);header=ref/'lib/include/nitro/fs/archive.h';text=header.read_text()
        names=('FSi_IsArchiveCanceling','FSi_IsArchiveSuspending','FS_IsArchiveSuspended','FSi_IsArchiveRunning')
        result['archive_inline_source']=dict(path=str(header.relative_to(ref)),sha256=sha(header.read_bytes()),
            definition_sha256={name:sha(F.definition_source(text,'static inline BOOL',name).encode())for name in names})
        file=ref/'lib/include/nitro/fs/file.h'
        result['sync_inline_source']=dict(path=str(file.relative_to(ref)),sha256=sha(file.read_bytes()),
            definition_sha256=sha(F.definition_source(file.read_text(),'static inline BOOL','FS_IsFileSyncMode').encode()))
    result['qualified_runtime_scope']='Empty archive, no cancel/suspend/IDLE callback; two native IRQ leaves only'
    result['layout_limits']='FSFile72/FSArchive92 and pointer ABI checked; no OSThread layout/runtime or original MW C compiler provenance claimed'
    (Path(out)/'manifesto.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--cc',default='clang');p.add_argument('--reference',type=Path);a=p.parse_args()
    try:build(a.uscita,a.cc,a.reference)
    except(ValueError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('Recovered Next532 ARM bytes verified; original native compiler provenance remains unknown')


if __name__=='__main__':main()
