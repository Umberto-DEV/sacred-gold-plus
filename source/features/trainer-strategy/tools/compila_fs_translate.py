#!/usr/bin/env python3
"""Assemble recovered Translate396+pool4 and check original ARM32 layouts."""
from pathlib import Path
import argparse,importlib.util,json,subprocess,types


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


D=load('translate_read_builder_parent',Path(__file__).with_name('compila_fs_read.py'))
F=load('translate_definition_helper',Path(__file__).with_name('compila_fs_find.py'))
E=load('translate_builder_source_engine',Path(__file__).parents[1]/'test/caller_species_bench.py')
need,sha=D.need,D.sha
PARENT_SHA='92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788'
need(sha(Path(F.__file__).read_bytes())=='5cef6e45d9706815b4a79ed16d4d0a0e8318702a92c7a3eeeea11ff87f385ff9'and
     sha(Path(E.__file__).read_bytes())=='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31',
     'Translate qualified definition/source engine drift')
BODIES={'command':(0x20D68C0,400,'f1df0f035e516cdfff9df4668530ca636f88b9a1a70d86804b9671c8bce7341a')}
CODE_SHA='9c42ca76b2fa192199ad1687f07ea9bcf54a90f5b6fe950c6fd9cbb641fb719d'
TABLE_SHA='a2a3fe2a981c9967141752f3228d54c59d73c639339443bbe0ef04f13319d287'
LAYOUT=D.C.LAYOUT+'''#define ARC_OFF(f) __builtin_offsetof(FSArchive,f)
CHECK(sizeof(FSArchive)==92); CHECK(_Alignof(FSArchive)==4);
CHECK(ARC_OFF(flag)==28); CHECK(ARC_OFF(proc)==84); CHECK(ARC_OFF(proc_flag)==88);
CHECK(ARC_OFF(sync_q)==12); CHECK(sizeof(OSThreadQueue)==8);
CHECK(FS_COMMAND_FINDPATH==4); CHECK(FS_COMMAND_CLOSEFILE==8);
CHECK(FS_RESULT_SUCCESS==0); CHECK(FS_RESULT_FAILURE==1); CHECK(FS_RESULT_BUSY==2);
CHECK(FS_RESULT_PROC_ASYNC==6); CHECK(FS_RESULT_PROC_DEFAULT==7); CHECK(FS_RESULT_PROC_UNKNOWN==8);
CHECK(FS_FILE_STATUS_SYNC==4); CHECK(FS_FILE_STATUS_OPERATING==0x40);
CHECK(FS_ARCHIVE_FLAG_IS_SYNC==0x200); CHECK(FS_ARCHIVE_FLAG_IS_ASYNC==0x100);
'''
source=Path(D.__file__).read_text();a=source.index('        layout = C.LAYOUT');b=source.index("        (out / 'layout.c')",a)
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'read_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ("'fs-read-'","'fs-translate-'",1),('native_fs_read_','native_fs_translate_',1),
    ('native-fs-read-recipe-v1','native-fs-translate-recipe-v1',1),
    ("flags + ['-DBUILD_WRAPPER=' + str(int(role == 'wrapper')), '-c'","flags + ['-c'",1),
    (source[a:b],'        layout = LAYOUT\n',1),('fs_read_layout','fs_translate_layout',2),
    ('lib/NitroSDK/src/fs/FS_file.c','lib/NitroSDK/src/fs/FS_command.c',1),
    ("('FSi_ReadFileCore', 'FS_ReadFile')","('FSi_TranslateCommand',)",1),
    ("            a = text.index('int ' + function + '('); b = text.index('\\n}\\n', a) + 3\n",'',1),
    ('sha(text[a:b].encode())',"sha(F.definition_source(text,'FSResult',function).encode())",1)],
    dict(__source_kind__='read_builder',__file__=__file__,F=F,LAYOUT=LAYOUT,BODIES=BODIES,
         RECIPE=Path(__file__).parents[1]/'sorgenti/fs-translate.S'))


def build(out,cc='clang',reference=None):
    result=derive_build(out,cc,reference);result.update(source_recipe=RECIPE,rewrite_engine_sha256=sha(Path(E.__file__).read_bytes()),
        extent=dict(instructions=396,literal_pool=4,pool_runtime='0x20d6a4c',pool_value='0x210e124',code_sha256=CODE_SHA),
        default_table=dict(runtime='0x210e124',bytes=36,sha256=TABLE_SHA,command=4,target='0x20d6db0',installed_from_this_recipe=False))
    if reference:
        ref=Path(reference);private=ref/'lib/NitroSDK/src/fs/fs_private.h';table=ref/'lib/NitroSDK/src/fs/FS_command_default.c'
        text=table.read_text();a=text.index('FSResult (*const fsi_default_command[])(FSFile *) = {');b=text.index('\n};',a)+4
        result['default_table_source']=dict(path=str(table.relative_to(ref)),sha256=sha(table.read_bytes()),
            declaration_sha256=sha(text[a:b].encode()),source_only_not_compiled_C_table=True)
        result['private_header_sha256']=sha(private.read_bytes())
    result['limits']='Recovered assembly and original header layout, not original Metrowerks C code generation or native default handler execution'
    (Path(out)/'manifesto.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--uscita',type=Path,required=True)
    parser.add_argument('--cc',default='clang');parser.add_argument('--reference',type=Path);a=parser.parse_args()
    try:build(a.uscita,a.cc,a.reference)
    except(ValueError,subprocess.SubprocessError)as error:parser.exit(2,str(error)+'\n')
    print('Recovered Translate400 verified; literal pool is not executed code and default handler remains separate')


if __name__=='__main__':main()
