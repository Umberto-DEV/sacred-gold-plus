#!/usr/bin/env python3
"""Assemble one recovered MSL division comparison object, no ROM output.

The bounded source selector and sole repeated block are checked against the
authenticated inline assembly. Original MWC code generation is not recovered.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import re
import shutil
import struct
import subprocess


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
C=load(HERE.with_name('compila_fs_cached_seekdir.py'),'division_qualified_compiler_loader')
need,sha=C.need,C.sha
PARENT_SHA='4f814be3d68b307736fb25b8488a24132d18e99acc0679d528e6a9045fc94517'
PIN=C.C.PIN
RECIPE=HERE.parents[1]/'sorgenti/s32-div.S'
ENTRY,SIZE,DIGEST=0x20f2998,524,'e8183a62ffe6a54210cd7d025b01431ff792025c1b45a0e8537abd8cec16ccfb'
SYMBOL='native_s32_div_recipe'
SOURCES={
 'lib/MSL_C/src/msl_fp_runtime.c':'4772579d74e6406a595ce01ebbbcc45b1f64bf7b7b79833b16b509f591c1dcaa',
 'lib/MSL_C/src/msl_fp_runtime.alias-map.json':'9d97f95c6184fe3607cf3a7a0a1c0c8342ea2244342bf0340ac9a1bd1e29a2f3',
 'lib/asm/msl_fp_emulation_types.s':'eb05b23346092145aac221d5fa2807c32976da12ff01abe63446f890f7194b06'}


def source_body(text):
    need(text.count('@s32_div_f:\n')==text.count('@u32_div_f:\n')==1,'unique bounded MSL labels')
    body=text.split('@s32_div_f:\n',1)[1].split('@u32_div_f:\n',1)[0]
    lines=[re.sub(r'\s+',' ',line.strip()).replace('@020F2B90','.L020F2B90')for line in body.splitlines()if line.strip()]
    need(len(lines)==132 and lines.count('.L020F2B90:')==1,'131 MSL instructions and one internal label')
    return lines


def recipe_body(text):
    need(text.count(SYMBOL+':\n')==1 and text.count('.rept 32')==text.count('.endr')==1,'one comparison symbol and bounded repeat32')
    body=text.split(SYMBOL+':\n',1)[1].split('.size ',1)[0]
    before,repeated=body.split('.rept 32',1);inside,after=repeated.split('.endr',1)
    lines=[]
    for part,count in((before,1),(inside,32),(after,1)):
        chunk=[re.sub(r'\s+',' ',line.strip())for line in part.splitlines()if line.strip()]
        need(all(not line.startswith('.')or line=='.L020F2B90:'for line in chunk),'no unreviewed assembler body directives')
        lines.extend(chunk*count)
    need(len(lines)==132,'expanded comparison instruction/label count')
    return lines


def read_object(path):
    loader=load(C.C.LOADER,'s32_independent_elf_loader');raw=Path(path).read_bytes()
    need(len(raw)<=1024**2,'bounded division ELF')
    blob,symbols=loader.load_text(raw,ENTRY,(SYMBOL,))
    h=struct.unpack_from('<HHIIIIIHHHHHH',raw,16)
    sections=[struct.unpack_from('<10I',raw,h[5]+i*h[10])for i in range(h[11])]
    need(not any(s[1]in(4,9)and s[5]for s in sections),'relocation-free division ELF')
    need(symbols[SYMBOL]==ENTRY and len(blob)==SIZE and sha(blob)==DIGEST,'complete installed division text/entry/extent')
    return blob,dict(object_sha256=sha(raw),text_sha256=sha(blob),ram=ENTRY,bytes=SIZE,entry_symbol=SYMBOL)


def build(out,reference,cc='/Library/Developer/CommandLineTools/usr/bin/clang'):
    out=Path(out).resolve();reference=Path(reference).resolve()
    need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private recipe output')
    need(sha(Path(C.__file__).read_bytes())==PARENT_SHA,'qualified compiler/ELF helper drift')
    compiler=Path(shutil.which(cc)or cc).resolve()
    need(compiler.is_file()and sha(compiler.read_bytes())==C.CC_SHA,'authenticated production compiler')
    need(subprocess.check_output(['git','-C',str(reference),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(reference),'status','--porcelain']),'clean pinned MSL reference')
    for name,digest in SOURCES.items():need(sha((reference/name).read_bytes())==digest,'MSL dependency drift '+name)
    canonical=source_body((reference/'lib/MSL_C/src/msl_fp_runtime.c').read_text())
    need(recipe_body(RECIPE.read_text())==canonical,'instruction-for-instruction MSL source / recovered recipe')
    out.mkdir(parents=True)
    argv=[str(compiler),'--target=armv5te-none-eabi','-mcpu=arm946e-s','-marm','-c',str(RECIPE),'-o',str(out/'s32_div.o')]
    result=subprocess.run(argv,capture_output=True,timeout=30);log=result.stdout+result.stderr
    (out/'compiler.log').write_bytes(log)
    command=dict(argv=argv,exit_code=result.returncode,log_sha256=sha(log))
    # Keep a failed compiler receipt even when no verified manifest can exist.
    (out/'command.json').write_text(json.dumps(command,indent=2)+'\n');result.check_returncode()
    blob,obj=read_object(out/'s32_div.o')
    receipt=dict(schema='native-s32-div-recipe-v1',builder_sha256=sha(HERE.read_bytes()),recipe_sha256=sha(RECIPE.read_bytes()),
        qualified_helper_sha256=PARENT_SHA,loader_sha256=sha(C.C.LOADER.read_bytes()),compiler_sha256=C.CC_SHA,
        compiler_version=subprocess.check_output([str(compiler),'--version'],text=True).splitlines()[0],
        source_pin=PIN,source_sha256=SOURCES,canonical_source_sha256=sha(('\n'.join(canonical)+'\n').encode()),
        source_instructions=131,object=obj,commands=[command],recipe_is_recovered=True,
        original_C_codegen_reconstructed=False,ROM_produced=False,CPU_executed=False)
    (out/'manifesto.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--uscita',type=Path,required=True)
    p.add_argument('--reference',type=Path,required=True);p.add_argument('--cc',default='/Library/Developer/CommandLineTools/usr/bin/clang');a=p.parse_args()
    try:build(a.uscita,a.reference,a.cc)
    except(ValueError,OSError,subprocess.SubprocessError)as e:p.exit(2,str(e)+'\n')
    print('One MSL division comparison ELF524 verified; no original C compiler or ROM build')


if __name__=='__main__':main()
