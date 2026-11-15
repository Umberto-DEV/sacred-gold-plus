#!/usr/bin/env python3
"""Compile the exact pinned Reset C definition with an authenticated ABI projection.

This creates a private alternative LLVM object, not a ROM or original MWC
reconstruction. Three guest LDR/BX thunks resolve the real native callees.
Prepare writes the exact TU/recipe without invoking the compiler.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import time


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
DEF=load(HERE.with_name('confronta_box_move_pret.py'),'Reset_exact_C_definition_reader')
need=DEF.need
PINS={'productive':'cb614ad23449d5852b40321dc409c4143872b35c','heartgold':'6bf138d6035aa6b43d6f8f4132a12df70f86dcec'}
FILES={'productive': {'src/pokemon.c': '1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3', 'include/pokemon.h': '54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1', 'include/move.h': '54f8598db8aaef0cb04e3d4152153ff7684cd41af5e0a2be4d04bc34db39804f', 'include/constants/pokemon.h': '64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74', 'include/pokemon_types_def.h': '032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d', 'include/global.h': 'babc9a9f87a67f56c07fd8137beba8289aa6e02f6afb9b7d00f74434803d12cf', 'lib/include/nitro/types.h': 'bc6a942130f6d5643c27a69b6aacf6f9b674fe81b0cc8a5210183df2e2debde4'}, 'heartgold': {'src/pokemon.c': 'f0a4323e9ad7925a4a2c9a4628216054e9d93c55a28472bef70e2eaefedcc928', 'include/pokemon.h': '07f0219f84d22b6eea26eabb78ee623a4fcbf814fec24f0dc08c5ce5ce443967', 'include/move.h': '99da5157055dc96da82f73e2c564a3c9472ae87ced46cc12c768bd4f4757989d', 'include/constants/pokemon.h': '64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74', 'include/pokemon_types_def.h': 'f0b7fd6348057d04c9587cb4782cf990939b848df5fa829f222364384fd8af63', 'include/global.h': 'b9a967dae410659b0289bbeef42cbd997867613c80eecaea5a280389302dd668'}}
BODY_NAME='MonSetMoveInSlot_ResetPpUp'
BODY_SHA='e80f65e6bfd87861d55399c0bade3e8c3beabf840a4bcf563cebaa68f53101cd'
COMPILER_SHA='fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
COMPILER_BYTES=124520368
LOADER=SOURCE/'features/native-core/tools/carica_text.py'
LOADER_SHA='fff73b384cacedae6525b72a46665a05f3c9710a4ff789fd296568e82e2ce1a8'
PROTOTYPES={
 'MonSetMoveInSlot':('include/pokemon.h','void MonSetMoveInSlot(Pokemon *mon, u16 move, u8 slot);'),
 'SetMonData':('include/pokemon.h','void SetMonData(Pokemon *mon, int attr, const void *ptr);'),
 'GetMoveMaxPP':('include/move.h','u8 GetMoveMaxPP(u16 moveId, u8 ppUps);')}
TYPE_DECLS=('typedef unsigned char u8;','typedef unsigned short int u16;')
TARGETS={'MonSetMoveInSlot':0x20714e9,'SetMonData':0x206ec41,'GetMoveMaxPP':0x207332d}
FLAGS=('--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-ffreestanding','-fno-builtin',
 '-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-fno-jump-tables',
 '-fno-optimize-sibling-calls','-fsigned-char','-std=c11')
BASE=0x22f1000


def sha(blob):return hashlib.sha256(blob).hexdigest()


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(1024**2),b''):h.update(block)
    return h.hexdigest()


def exact_global(text,line):
    masked=DEF.lexical_mask(text);found=[]
    for match in re.finditer(r'^'+re.escape(line)+r'$',masked,re.M):
        prefix=masked[:match.start()]
        if prefix.count('{')==prefix.count('}'):found.append(match.start())
    need(len(found)==1,'unique global ABI declaration '+line)
    return text[found[0]:found[0]+len(line)]


def validate_body(body):
    need(type(body)is str and len(body.encode())==290 and sha(body.encode())==BODY_SHA,'exact unchanged Reset C290 definition')
    masked=DEF.lexical_mask(body)
    need('->'not in masked and not re.search(r'\b(?:sizeof|offsetof)\b',masked),'opaque Pokemon projection only for a no-layout function')


def validate_targets(targets):
    need(type(targets)is dict and set(targets)==set(TARGETS)and all(type(v)is int and v&1 for v in targets.values())
         and targets==TARGETS,'three exact odd native guest linkage targets')


def thunk_assembly():
    validate_targets(TARGETS);lines=['.syntax unified','.thumb','.pushsection .text,"ax",%progbits']
    for name,target in TARGETS.items():
        lines.extend(['.p2align 2','.global '+name,'.type '+name+',%function','.thumb_func',name+':',
            'ldr r3, 1f','bx r3','.p2align 2','1: .word 0x%08x'%target,'.size '+name+', .-'+name])
    return '\n'.join(lines+['.popsection',''])


def make_tu(body):
    """Wrap a supplied body literally; the public prepare authenticates it first."""
    need(type(body)is str and len(body.encode())<=64*1024,'bounded C body text')
    declarations='\n'.join(TYPE_DECLS)+ '\ntypedef struct Pokemon Pokemon;\n'
    declarations+='\n'.join(row[1]for row in PROTOTYPES.values())+'\n'
    declarations+='#define MON_DATA_MOVE1_PP 58\n#define MON_DATA_MOVE1_PP_UPS 62\n'
    declarations+='_Static_assert(sizeof(int)==4 && sizeof(void*)==4,"ARM32 ABI");\n'
    declarations+='_Static_assert(sizeof(u16)==2 && sizeof(u8)==1,"native integer ABI");\n'
    return '/* Authenticated minimal ABI projection, not the whole Pokemon TU. */\n'+declarations+'\n'+body+'\n\n__asm__('+json.dumps(thunk_assembly())+');\n'


def read_reference(root,kind):
    root=Path(root).resolve()
    actual=Path(subprocess.check_output(['git','-C',str(root),'rev-parse','--show-toplevel'],text=True).strip()).resolve()
    need(actual==root,'reference root is its own Git checkout '+kind)
    need(subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PINS[kind]
         and not subprocess.check_output(['git','-C',str(root),'status','--porcelain']),'clean pinned C source '+kind)
    texts={}
    for name,digest in FILES[kind].items():
        raw=(root/name).read_bytes();need(sha(raw)==digest,'pinned C source dependency '+kind+'/'+name);texts[name]=raw.decode('utf8')
    return texts


def project_sources(reference,heartgold_ref):
    sources={kind:read_reference(root,kind)for kind,root in(('productive',reference),('heartgold',heartgold_ref))}
    definitions={kind:DEF.definition(texts['src/pokemon.c'],BODY_NAME)for kind,texts in sources.items()}
    for definition in definitions.values():validate_body(definition['text'])
    need(definitions['productive']['text']==definitions['heartgold']['text'],'same literal Reset body across pinned references')
    for texts in sources.values():
        for name,(file,line)in PROTOTYPES.items():exact_global(texts[file],line)
        for name,value in(('MON_DATA_MOVE1_PP',58),('MON_DATA_MOVE1_PP_UPS',62)):
            need(len(re.findall(r'^#define\s+'+name+r'\s+'+str(value)+r'\s*$',texts['include/constants/pokemon.h'],re.M))==1,'exact source attribute ID '+name)
    for line in TYPE_DECLS:exact_global(sources['productive']['lib/include/nitro/types.h'],line)
    body=definitions['productive']['text'];tu=make_tu(body);need(len(tu.encode())<=64*1024,'generated TU64KiB bound')
    return tu,dict(reference_pins=PINS,reference_files=FILES,definition_file='src/pokemon.c',definition_lines={k:v['line']for k,v in definitions.items()},
        body_bytes=290,body_sha256=BODY_SHA,body_with_added_newline_sha256=sha((body+'\n').encode()),
        ABI_projection='Authenticated productive u8/u16 typedefs, opaque Pokemon pointer, exact three prototypes and two IDs; function body unchanged',
        whole_pokemon_C_compiled=False,whole_headers_identical=False,newer_SDK_typedefs_reused=False,
        prototypes={name:dict(file=file,text=line)for name,(file,line)in PROTOTYPES.items()},
        type_declarations=list(TYPE_DECLS),attribute_IDs=dict(MON_DATA_MOVE1_PP=58,MON_DATA_MOVE1_PP_UPS=62),
        native_linkage_targets=TARGETS,original_MWC_codegen_reconstructed=False,ROM_opened=False,CPU_executed=False)


def prepare(reference,heartgold_ref,compiler):
    tu,provenance=project_sources(reference,heartgold_ref);compiler=Path(compiler).resolve()
    need(compiler.is_file()and compiler.stat().st_size==COMPILER_BYTES and file_sha(compiler)==COMPILER_SHA,'exact retained-qualified LLVM compiler binary')
    need(file_sha(LOADER)==LOADER_SHA,'unchanged qualified text loader')
    return tu,dict(schema='native-Reset-C-source-recipe-v1',**provenance,translation_unit_sha256=sha(tu.encode()),
        translation_unit_bytes=len(tu.encode()),compiler_sha256=COMPILER_SHA,compiler_bytes=COMPILER_BYTES,
        compiler_identity='Apple clang21.0.0 clang-2100.4.1.1, identity inherited from authenticated SDK recipe; no version invocation',
        flags=list(FLAGS),load_base=BASE,loader_sha256=LOADER_SHA,
        source_sha256={str(p.relative_to(SOURCE)):file_sha(p)for p in(HERE,Path(DEF.__file__),LOADER)},
        scope='Alternative LLVM C unit and three guest linkage thunks; not original56-byte reconstruction, full pokemon.c, a ROM build or semantic acceptance')


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','compile'),required=True)
    for n in('reference','heartgold-ref','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--compiler',type=Path,default=Path('/Library/Developer/CommandLineTools/usr/bin/clang'));a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not a.out_dir.is_symlink(),'fresh private C compilation directory')
        tu,recipe=prepare(a.reference,a.heartgold_ref,a.compiler);out.mkdir(parents=True)
        source=out/'candidate.c';source.write_text(tu);save(out/'source-recipe.json',recipe)
        if a.mode=='prepare':print('Literal ResetC290/ABI projection/TU/flags/CC hash prepared; no compiler or CPU');return
        obj=out/'candidate.o';argv=[str(a.compiler.resolve()),*FLAGS,'-c',str(source),'-o',str(obj)]
        removed=('CCC_OVERRIDE_OPTIONS','SDKROOT','CPATH','C_INCLUDE_PATH','CPLUS_INCLUDE_PATH','OBJC_INCLUDE_PATH')
        env={k:v for k,v in os.environ.items()if k not in removed};start=time.monotonic()
        try:
            result=subprocess.run(argv,capture_output=True,timeout=30,env=env)
            code=result.returncode;stdout=result.stdout;stderr=result.stderr;timed_out=False
        except subprocess.TimeoutExpired as e:code=124;stdout=e.stdout or b'';stderr=e.stderr or b'';timed_out=True
        log=stdout+b'\n'+stderr;truncated=len(log)>2*1024**2
        (out/'compiler.log').write_bytes(log[:2*1024**2])
        receipt=dict(schema='native-Reset-C-compiler-receipt-v1',argv=argv,exit_code=code,elapsed_s=round(time.monotonic()-start,6),
            timed_out=timed_out,log_truncated=truncated,removed_build_environment_names=[k for k in removed if k in os.environ],
            compiler_sha256=file_sha(a.compiler),source_recipe_sha256=file_sha(out/'source-recipe.json'),translation_unit_sha256=file_sha(source),
            compiler_invocations=1,CPU_executed=False,log_sha256=file_sha(out/'compiler.log'))
        if obj.exists():receipt['ELF_bytes']=obj.stat().st_size;receipt['ELF_sha256']=file_sha(obj)
        save(out/'compiler-receipt.json',receipt)
        need(code==0 and not truncated and obj.is_file()and obj.stat().st_size<=1024**2,'bounded single C compilation succeeded; inspect compiler receipt/log otherwise')
        need(file_sha(source)==recipe['translation_unit_sha256']and file_sha(a.compiler)==COMPILER_SHA,'C source/compiler unchanged after invocation')
    except(ValueError,OSError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('One exact-source LLVM C object produced; ELF/ABI/relocations and guest behavior still require independent validation')


if __name__=='__main__':main()
