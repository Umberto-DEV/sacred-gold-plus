#!/usr/bin/env python3
"""Assemble the recovered ConvertPath wrapper; no ROM output or SDK rebuild.

Reuses the qualified Open builder through exact authenticated source edits.
The original headers optionally verify FSFile72 and FSFileID8 under ARM32.
"""
from pathlib import Path
import argparse,importlib.util,json,types,subprocess


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


D=load('convert_open_builder_parent',Path(__file__).with_name('compila_fs_open.py'))
ENGINE=Path(__file__).resolve().parents[1]/'test/caller_species_bench.py'
E=load('convert_builder_source_engine',ENGINE)
need,sha=D.need,D.sha
PARENT_SHA='e804541b4a4cb44ef0d906424bc2f77fea6cc774b8f9897a27a4315d9dc2fa6b'
ENGINE_SHA='b8d8819e366528c2d30dde0d0f45c0270ff9c0e3f00989868828af96643efc31'
need(sha(ENGINE.read_bytes())==ENGINE_SHA,'qualified source engine drift')
rewrite=types.FunctionType(E.rewrite.__code__,{**vars(E),'PINS':{'open_builder':PARENT_SHA}})
derive_build,RECIPE=rewrite(D,'build',[
    ('fs-open.o','fs-convert.o',3),('native_fs_open_recipe','native_fs_convert_recipe',2),
    ('len(body) == 72','len(body) == 64',1),('text_bytes=72','text_bytes=64',1),
    ('native-fs-open-recipe-v1','native-fs-convert-recipe-v1',1),
    ("['0x20d8180', '0x20d8208']","['0x20d7f98', '0x20d7fc0']",1),
    ('BOOL FS_OpenFile(','BOOL FS_ConvertPathToFileID(',1),
    ('recovered Open extent/ARM entry/PC-relative calls differ',
     'recovered Convert extent/ARM entry/PC-relative calls differ',1)],
    dict(__source_kind__='open_builder',__file__=__file__,
         RECIPE=Path(__file__).resolve().parents[1]/'sorgenti/fs-convert.S',ADDRESS=0x20D8180,
         EXPECTED='8455d062eee662f58fefa731950eab06ecedb77279478b2ef41123ab5128d172'))


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
    print('Recovered Convert ARM recipe verified:',report['text_sha256'])


if __name__=='__main__':main()
