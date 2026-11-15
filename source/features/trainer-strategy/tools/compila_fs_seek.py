#!/usr/bin/env python3
"""Assemble the recovered Seek wrapper; no ROM output or SDK rebuild.

Reuses the qualified Open builder through exact authenticated source edits.
The original headers optionally verify FSFile72 and FSFileID8 under ARM32.
"""
from pathlib import Path
import argparse,importlib.util,json,types,subprocess


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


D=load('fast_open_builder_parent',Path(__file__).with_name('compila_fs_open.py'))
ENGINE=Path(__file__).resolve().parents[1]/'test/caller_species_bench.py'
E=load('fast_builder_source_engine',ENGINE)
need,sha=D.need,D.sha
PARENT_SHA='e804541b4a4cb44ef0d906424bc2f77fea6cc774b8f9897a27a4315d9dc2fa6b'
ENGINE_SHA='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31'
need(sha(ENGINE.read_bytes())==ENGINE_SHA,'qualified source engine drift')
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'open_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ('fs-open.o','fs-seek.o',3),('native_fs_open_recipe','native_fs_seek_recipe',2),
    ('len(body) == 72','len(body) == 108',1),('text_bytes=72','text_bytes=108',1),
    ('native-fs-open-recipe-v1','native-fs-seek-recipe-v1',1),
    ("['0x20d8180', '0x20d8208']","[]",1),
    ('BOOL FS_OpenFile(','BOOL FS_SeekFile(',1),
    ('layout = C.LAYOUT +','layout = FAST_LAYOUT +',1),
    ('recovered Open extent/ARM entry/PC-relative calls differ',
     'recovered Seek extent/ARM entry/PC-relative calls differ',1)],
    dict(__source_kind__='open_builder',__file__=__file__,FAST_LAYOUT=D.C.LAYOUT+'\nCHECK(OFF(arg.openfilefast.id.arc)==48);\nCHECK(OFF(arg.openfilefast.id.file_id)==52);\nCHECK(FS_COMMAND_OPENFILEFAST==6);\nCHECK(FS_COMMAND_CLOSEFILE==8);\nCHECK(OFF(prop.file.own_id)==32);\nCHECK(OFF(prop.file.top)==36);\nCHECK(OFF(prop.file.bottom)==40);\nCHECK(OFF(prop.file.pos)==44);\nCHECK(sizeof(FSSeekFileMode)==4);\nCHECK(FS_SEEK_SET==0);\nCHECK(FS_SEEK_CUR==1);\nCHECK(FS_SEEK_END==2);\nCHECK(FS_FILE_STATUS_IS_FILE==16);\nCHECK(FS_FILE_STATUS_IS_DIR==32);\n',
         RECIPE=Path(__file__).resolve().parents[1]/'sorgenti/fs-seek.S',ADDRESS=0x20D83DC,
         EXPECTED='99e8a8db572238f5c2aa23d35ddfe505843277a0623dedfe207c2d5872236747'))


def build(out,cc='clang',reference=None):
    report=derive_build(out,cc,reference)
    report.update(build_source_parent_sha256=PARENT_SHA,rewrite_engine_sha256=ENGINE_SHA,source_recipe=RECIPE)
    (Path(out)/'manifesto.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uscita',type=Path,required=True)
    parser.add_argument('--cc',default='clang');parser.add_argument('--reference',type=Path)
    args=parser.parse_args()
    try:report=build(args.uscita,args.cc,args.reference)
    except(ValueError,subprocess.SubprocessError)as error:parser.exit(2,str(error)+'\n')
    print('Recovered Seek ARM recipe verified:',report['text_sha256'])


if __name__=='__main__':main()
