#!/usr/bin/env python3
"""Assemble recovered ExecuteSync and verify original ARM32 layouts; no ROM output."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,types


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


D=load('exec_sync_read_builder_parent',Path(__file__).with_name('compila_fs_read.py'))
F=load('exec_sync_definition_helper',Path(__file__).with_name('compila_fs_find.py'))
E=load('exec_sync_builder_source_engine',Path(__file__).parents[1]/'test/caller_species_bench.py')
need,sha=D.need,D.sha
PARENT_SHA='92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788'
need(sha(Path(F.__file__).read_bytes())=='5cef6e45d9706815b4a79ed16d4d0a0e8318702a92c7a3eeeea11ff87f385ff9'and
     sha(Path(E.__file__).read_bytes())=='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31',
     'ExecuteSync qualified definition/source engine drift')
BODIES={'command':(0x20D7744,68,'44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55')}
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
CHECK(FS_ARCHIVE_PROC_ACTIVATE==0x200);
'''
source=Path(D.__file__).read_text();a=source.index('        layout = C.LAYOUT');b=source.index("        (out / 'layout.c')",a)
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'read_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ("'fs-read-'","'fs-exec-sync-'",1),('native_fs_read_','native_fs_exec_sync_',1),
    ('native-fs-read-recipe-v1','native-fs-exec-sync-recipe-v1',1),
    ("flags + ['-DBUILD_WRAPPER=' + str(int(role == 'wrapper')), '-c'","flags + ['-c'",1),
    (source[a:b],'        layout = LAYOUT\n',1),('fs_read_layout','fs_exec_sync_layout',2),
    ('lib/NitroSDK/src/fs/FS_file.c','lib/NitroSDK/src/fs/FS_archive_prefix.c',1),
    ("('FSi_ReadFileCore', 'FS_ReadFile')","('FSi_ExecuteSyncCommand',)",1),
    ("            a = text.index('int ' + function + '('); b = text.index('\\n}\\n', a) + 3\n",'',1),
    ('sha(text[a:b].encode())',"sha(F.definition_source(text,'BOOL',function).encode())",1)],
    dict(__source_kind__='read_builder',__file__=__file__,F=F,LAYOUT=LAYOUT,BODIES=BODIES,
         RECIPE=Path(__file__).parents[1]/'sorgenti/fs-exec-sync.S'))


def build(out,cc='clang',reference=None):
    result=derive_build(out,cc,reference);result.update(source_recipe=RECIPE,
        rewrite_engine_sha256=sha(Path(E.__file__).read_bytes()))
    if reference:
        ref=Path(reference);header=ref/'lib/include/nitro/fs/file.h'
        result['success_inline_source']=dict(path=str(header.relative_to(ref)),sha256=sha(header.read_bytes()),
            definition_sha256=sha(F.definition_source(header.read_text(),'static inline BOOL','FS_IsSucceeded').encode()))
        models={}
        for rel,functions in(('lib/NitroSDK/src/fs/FS_command.c',(('void','FSi_ReleaseCommand'),('FSResult','FSi_TranslateCommand'))),
                              ('lib/NitroSDK/src/fs/FS_archive_prefix.c',(('FSFile *','FSi_NextCommand'),))):
            path=ref/rel;text=path.read_text()
            funcs={name:sha(F.definition_source(text,return_type,name).encode())for return_type,name in functions}
            models[rel]=dict(sha256=sha(path.read_bytes()),function_body_sha256=funcs)
        private=ref/'lib/NitroSDK/src/fs/fs_private.h'
        result['boundary_model_sources']=models
        result['list_helper_source_sha256']=sha(private.read_bytes())
    (Path(out)/'manifesto.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--cc',default='clang');p.add_argument('--reference',type=Path);a=p.parse_args()
    try:build(a.uscita,a.cc,a.reference)
    except(ValueError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print('Recovered ExecuteSync68 ARM bytes verified; original native compiler provenance remains unknown')


if __name__=='__main__':main()
