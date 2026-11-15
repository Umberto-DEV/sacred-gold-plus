#!/usr/bin/env python3
"""Prepare/execute/CPU-free verify the complete cached Convert composition.

Object JSON maps the eighteen component names to user-owned ELF paths. ELF
origin is not inferred from matching text: keep the builders' compiler/layout
receipts separately. This tool verifies recovered recipe/source identities,
ELF entries and exact text, ROM resources, frozen context and execution.
"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import struct
import subprocess


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
SOURCE=HERE.parents[3]
B=load(HERE.parents[1]/'test/fs_cached_convert_bench.py','cached_convert_native_bench')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PIN='cb614ad23449d5852b40321dc409c4143872b35c'
LOADER=SOURCE/'features/anim/tools/carica_text.py'
LOADER_SHA='fff73b384cacedae6525b72a46665a05f3c9710a4ff789fd296568e82e2ce1a8'
SYMBOLS={'convert': 'native_fs_convert_recipe',
 'copy': 'native_fs_cached_copy',
 'disable': 'native_fs_wait_disable_recipe',
 'execute': 'native_fs_exec_sync_command_recipe',
 'find': 'native_fs_find_path_recipe',
 'findpath': 'native_fs_cached_findpath',
 'init': 'native_fs_init_recipe',
 'next': 'native_fs_next_command_recipe',
 'read_dir': 'native_fs_cached_read_dir',
 'read_memory': 'native_fs_cached_read_memory',
 'read_table': 'native_fs_cached_read_table',
 'release': 'native_fs_release_command_recipe',
 'restore': 'native_fs_wait_restore_recipe',
 'seekdir': 'native_fs_cached_seekdir',
 'send': 'native_fs_send_command_recipe',
 'strnicmp': 'native_fs_cached_strnicmp',
 'translate': 'native_fs_translate_command_recipe',
 'wakeup': 'native_os_wakeup_command_recipe'}
RECIPE_FILES={'features/trainer-strategy/sorgenti/fs-cached-findpath.S': 'e302846ed65fa5175511dc3150714ec905e35b9518e443e1a958412b88d28d6c',
 'features/trainer-strategy/sorgenti/fs-cached-seekdir.S': '9b4299d54c17113f8425c66093603c6ae5cac7329ccb2204b7e5543d584604bb',
 'features/trainer-strategy/sorgenti/fs-convert.S': '616f6ed42e8307e36d9bdf461c2dd2e77177315cb9826e6762ad240c309cc114',
 'features/trainer-strategy/sorgenti/fs-exec-sync.S': '386ef26bc2b98f45fc24d946dbec95ac7f6b1b63e6610f868c33b713668d5e6a',
 'features/trainer-strategy/sorgenti/fs-find.S': 'e33243e1fa9c979bdea0af04433d784d096684a4d7a3946c0a00e5af638d3f81',
 'features/trainer-strategy/sorgenti/fs-init.S': '8c9ee97ecb4e158febe24cbd8f90cbcf322c9a1492f62054c2feb836d350b887',
 'features/trainer-strategy/sorgenti/fs-next.S': 'a078decfad1f305f65ebdc33d3ddc1b993d0bf4ae5cead63004c6e737728d2d1',
 'features/trainer-strategy/sorgenti/fs-release.S': 'c9ee020342bfcedd8710ba6319e59788cd749a41104b75210d77301c2793e50b',
 'features/trainer-strategy/sorgenti/fs-send.S': '16a9bf2c2ea20afcfeeea2abc9251ed0586a10caf4cfa2254e5f59f8982d8098',
 'features/trainer-strategy/sorgenti/fs-translate.S': 'f1cf503e0de402fce06fbe030f113ba7d8868890181c9b137db3af6ad2a09b02',
 'features/trainer-strategy/sorgenti/fs-wait.S': '5c61122523eb40339ccdf137555a7811e439a361f74983974e9329aa3e36b430',
 'features/trainer-strategy/sorgenti/os-wakeup.S': 'ca7800fe4e5ccd470b0fad5fea50c590f059fd73bbda7e0531f2b71b2d2b1d06',
 'features/trainer-strategy/tools/compila_fs_cached_findpath.py': 'b62a52f7e7f1e6218039bb6acdaf3c266dcc505fc2f4731dd0a55c9362ad5f4e',
 'features/trainer-strategy/tools/compila_fs_cached_seekdir.py': '4f814be3d68b307736fb25b8488a24132d18e99acc0679d528e6a9045fc94517',
 'features/trainer-strategy/tools/compila_fs_convert.py': '45d8d14c2deb5ba8a13bd18dba3ca44aa4c36ca40b2869ec8d1829176c3a9cbd',
 'features/trainer-strategy/tools/compila_fs_exec_sync.py': 'd35af21ca34e1bc6d0a2aded13f2d45fecd261b1b202a748cc0a888432b9f321',
 'features/trainer-strategy/tools/compila_fs_find.py': '5cef6e45d9706815b4a79ed16d4d0a0e8318702a92c7a3eeeea11ff87f385ff9',
 'features/trainer-strategy/tools/compila_fs_init.py': 'c412b858e85410ce511354bc3e96e78f860783130d53396e12dc746062473e8a',
 'features/trainer-strategy/tools/compila_fs_next.py': 'dc8cb4eeeeb2a78200c76609fbbcc48719cd47113eb939d88249779b807cc243',
 'features/trainer-strategy/tools/compila_fs_release.py': '3229b12fa446cc746c2d413f2b51f18e07a310f7476408f3d0155247edc42109',
 'features/trainer-strategy/tools/compila_fs_send.py': 'c3ff4ad62fd8c5f43235cff213ec4cb0d54df2620b7488bb170a0cf673067c3f',
 'features/trainer-strategy/tools/compila_fs_translate.py': '41c69893d254f7432ef69c210f29c4880c69caefbd9d321efbfc382c0cbd08b4',
 'features/trainer-strategy/tools/compila_fs_wait.py': '2607383e21b39eb42aee854ffccb1be787ae7247f4d3699ad0e515206124c476',
 'features/trainer-strategy/tools/compila_os_wakeup.py': 'eca9aa71492d303f5846b0617d165db8051856329d23a55dcb2b9199fc8de66b'}
SDK_FILES={'lib/NitroSDK/src/fs/FS_archive_prefix.c': 'd359268374ed97b359e4344a820c892382fd23f8923d2895a828175662ae3f2d',
 'lib/NitroSDK/src/fs/FS_command.c': '07333027376e89d3ecc243b0022d089f9c3153cfe4226ef433e086cbe9777e60',
 'lib/NitroSDK/src/fs/FS_command_default.c': '040f053d87d157231bcd051731eee8bf27768a9103940b6c4016f9cf703ca513',
 'lib/NitroSDK/src/fs/FS_file.c': '7b54df220e89b6786743c2996e1e085bd29a9774a96af3551c84e600086e8e8f',
 'lib/NitroSDK/src/fs/fs_private.h': 'b3abfe01ae14a8b64fd68372a4e0646f975373dd296626d4396ffc113c3a122c',
 'lib/NitroSDK/src/fs/fs_send_command.c': '4cc68728ca70d26fb620e996493b7b7ef259d07d8150aab607957851a502e587',
 'lib/NitroSDK/src/mi/mi_memory.c': '7bfc34240ca43ec5c45773a7dad14547b0bb38fe7638c055a0f735e0aa0eb592',
 'lib/NitroSDK/src/os/os_system.c': '1a7a0943c47895f84168d6718fdf9a75ccdd4e8e612367d2850659b33eeaef28',
 'lib/NitroSDK/src/os/os_thread.c': 'eb91f80067f2aa05ef0e17d31c3c5c77aec256e7ce1e4e3e2211da1572723ed5',
 'lib/include/nitro/cp/context.h': 'bd4105ca80b68b715dd9a4d5316ff247af5a2824d25bc924c4816337df1db6b1',
 'lib/include/nitro/fs/archive.h': '0c7fa797839d7112af12c5a467c6fda878621b4bb5ce8b273c9df4ebadfdbe9e',
 'lib/include/nitro/fs/file.h': '4e874cfbaa77f546b6f69473ef8bd24afdaab082c5a99f0bb16c37d41f24598f',
 'lib/include/nitro/hw/ARM9/io_reg.h': 'f1a03c4be734519f9ea7ca0a877cad143909a626b70d6035f3837988903a4af2',
 'lib/include/nitro/hw/ARM9/mmap.h': '1adbf0d1070def154b2ccfb4f094bcf494266d55196b5860fc02681e290331ae',
 'lib/include/nitro/hw/common/io_reg.h': 'f534b5965ee2443de83a804748058bb695b3cdc48612d77d410f082f5746fbb6',
 'lib/include/nitro/hw/consts_shared.h': 'b45b1cb860a581d29a7621199db28fb85b2bbdb544be04a555aed659ad48c30c',
 'lib/include/nitro/hw/io_reg.h': '93cc63bb47d4b6fe2ba561496dddce890f4055a663eae450fe533f1394212ebf',
 'lib/include/nitro/hw/mmap.h': 'a6e89916d84c6dd24d8056d696f9496814327bbcca23369cf1829847061a35d8',
 'lib/include/nitro/hw/mmap_shared.h': '01ad2c66885f230a4282cd4ae6f58f791d28acd9ad50abb2de7a372a2c326413',
 'lib/include/nitro/os/ARM9/system.h': '0d45743cd7f025eeaf8ea96f6c8ce2009839320cd87e2c38b6411764ab6da901',
 'lib/include/nitro/os/common/armArch.h': 'ae4b80486774fd21a14ac23ecc217091cd99d847321c163cf5b62cce87dbc60b',
 'lib/include/nitro/os/common/system_shared.h': '8c060f7388dbf961b7ed214ac5efb4a7a61f001cce1345e3a9573b0eb22d0b5a',
 'lib/include/nitro/os/common/thread_shared.h': 'c5912e365f7a55ab466f1c4db082a5fa9ca1222d69b1709b16bac256369123e2',
 'lib/include/nitro/os/context.h': '15cb1600a66fecc17c1a0501539e778eb4a58a5fa5e224dd28c072367904a337',
 'lib/include/nitro/os/system.h': '528478572cd8fe217c0d6026e0603c98eedffce5816425784175dac3e05c1359',
 'lib/include/nitro/os/thread.h': '265ad31ce9fb0b736232eee6b20f12596b7fcebd8be6c5ace438c0914aa4fdfe',
 'lib/include/nitro/types.h': 'bc6a942130f6d5643c27a69b6aacf6f9b674fe81b0cc8a5210183df2e2debde4'}


def source_identities():
    paths={HERE,Path(B.__file__),Path(B.A.__file__),Path(F.__file__),Path(L.__file__),Path(L.L.__file__),Path(R.__file__),Path(M.__file__),LOADER}
    paths.update(SOURCE/name for name in RECIPE_FILES)
    return {str(p.relative_to(SOURCE)):R.sha(p.read_bytes())for p in sorted(paths)}


def verify_objects(objects,parts):
    need(type(objects)is dict and set(objects)==set(SYMBOLS)and all(type(p)is str for p in objects.values()),'exact eighteen named ELF paths')
    need(R.sha(LOADER.read_bytes())==LOADER_SHA,'pinned independent ELF loader')
    loader=load(LOADER,'convert_exact_elf_reader');rows={}
    for name in sorted(objects):
        obj=Path(objects[name]);need(obj.is_file()and obj.stat().st_size<=1024**2,'bounded ELF input '+name)
        data=obj.read_bytes();a,n,digest=L.COMPONENTS[name]
        text,symbols=loader.load_text(data,a,(SYMBOLS[name],))
        # Recovered ARM comparison objects are relocation-free. Do not accept a
        # relocation that happens to yield the same bytes via the generic loader.
        h=struct.unpack_from('<HHIIIIIHHHHHH',data,16)
        sections=[struct.unpack_from('<10I',data,h[5]+i*h[10])for i in range(h[11])]
        need(not any(s[1]in(4,9)and s[5]for s in sections),'relocation-free recovered ELF '+name)
        need(symbols[SYMBOLS[name]]==a and len(text)==n and R.sha(text)==digest and text==parts[name],'installed ROM / ELF entry and complete bytes '+name)
        rows[name]=dict(object_sha256=R.sha(data),text_sha256=digest,entry_symbol=SYMBOLS[name],entry_ram=a,bytes=n)
    return rows


def prepare(args):
    receipt,parts=L.prepare(args.rom,args.snapshot)
    frozen=json.loads(args.input_contract.read_bytes());need(B.wire(frozen)==B.wire(F.freeze(receipt,parts)),'exact frozen source/input/resource contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned SDK reference')
    for name,digest in SDK_FILES.items():need(R.sha((ref/name).read_bytes())==digest,'SDK source/header drift '+name)
    for name,digest in RECIPE_FILES.items():need(R.sha((SOURCE/name).read_bytes())==digest,'recovered recipe/builder drift '+name)
    objects=json.loads(args.objects.read_bytes());proof=verify_objects(objects,parts)
    inputs={'normal':F.make_input(parts),'precompleted_result':F.make_input(parts,True)}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        objects_sha256=R.file_sha(args.objects),ELF=proof,SDK_pin=PIN,SDK_files=SDK_FILES)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'normal','normal_OFF','precompleted_result'},'complete three-run control matrix')
    need(all(raw['observed']is(name!='normal_OFF')for name,raw in raws.items()),'OFF observation binding')
    for name,raw in raws.items():B.require_run(inputs['normal'if name=='normal_OFF'else name],raw)
    normal,off,projected=raws['normal'],raws['normal_OFF'],raws['precompleted_result']
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(normal[key])==B.wire(off[key]),'OFF neutrality '+key)
        need(B.wire(normal[key])==B.wire(projected[key]),'convergent initial result projection '+key)
    need(normal['initial']==off['initial'] and normal['initial']!=projected['initial'],'input projection provenance')
    for key in('flow','reads'):need(normal[key]==projected[key],'same source route '+key)
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],projected['stores']))if a!=b]
    need(differences==[588,589],'two native result writer preimages')
    forged=copy.deepcopy(projected);forged['initial']=copy.deepcopy(normal['initial'])
    try:B.require_run(inputs['normal'],forged)
    except ValueError as error:need(str(error)=='source native stores','camouflage specifically native stores')
    else:raise ValueError('camouflaged precompleted result accepted')
    for index in(588,589):
        altered=copy.deepcopy(normal);del altered['stores'][index]
        try:B.require_run(inputs['normal'],altered)
        except ValueError as error:need(str(error)=='source native stores','deleted result writer specifically rejected')
        else:raise ValueError('deleted result writer accepted')
    return dict(OFF_pairs=1,convergent_result_pairs=1,different_store_preimages=differences,
        camouflage_rejected='source native stores',deleted_writer_rejections=[588,589])


def save(path,value):
    with Path(path).open('x')as stream:stream.write(json.dumps(value,indent=2)+'\n')


def verify_existing(directory,receipt,inputs,bindings):
    report=json.loads((directory/'report.json').read_bytes())
    need(report.get('schema')=='native-fs-cached-convert-report-v1','native report schema')
    need(report['mode']in('probe','matrix') and report['CPU_executed']is True,'existing native report domain')
    need(B.wire(report['resources'])==B.wire(receipt)and B.wire(report['bindings'])==B.wire(bindings),'existing native resource/source/recipe binding')
    names=['normal']if report['mode']=='probe'else['normal','normal_OFF','precompleted_result']
    need([x['name']for x in report['raw']]==names,'exact ordered raw manifest')
    raws={}
    for row in report['raw']:
        need(row['file']==row['name']+'.json','local raw filename')
        path=directory/row['file'];need(not path.is_symlink()and R.file_sha(path)==row['sha256'],'raw file identity')
        raw=json.loads(path.read_bytes());B.require_run(inputs['normal'if row['name']=='normal_OFF'else row['name']],raw);raws[row['name']]=raw
    evidence=None if report['mode']=='probe'else controls(raws,inputs)
    need(B.wire(evidence)==B.wire(report['controls']),'existing control verdict')
    return dict(verified_report_sha256=R.file_sha(directory/'report.json'),raw_files=len(raws),controls=evidence,CPU_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','probe','matrix','verify'),required=True)
    for name in('rom','objects','reference','input-contract','out-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--raw-dir',type=Path);args=p.parse_args()
    try:
        need((args.mode=='verify')==(args.raw_dir is not None),'--raw-dir required only in verify mode')
        need(args.out_dir.resolve()!=SOURCE and SOURCE not in args.out_dir.resolve().parents,'private raw output outside source required')
        need(not args.out_dir.exists()and not args.out_dir.is_symlink(),'fresh private output directory required')
        receipt,inputs,predictions,bindings=prepare(args)
        args.out_dir.mkdir(parents=True)
        report=dict(schema='native-fs-cached-convert-report-v1',mode=args.mode,resources=receipt,bindings=bindings,CPU_executed=False,raw=[])
        save(args.out_dir/'prepared.json',report)
        if args.mode=='prepare':print('Prepared and predicted, no CPU/compiler');return
        if args.mode=='verify':
            save(args.out_dir/'verification.json',verify_existing(args.raw_dir,receipt,inputs,bindings));print('Existing raw verified; no CPU/compiler');return
        save(args.out_dir/'SOURCE-BEFORE-CPU.json',source_identities())
        names=('normal',)if args.mode=='probe'else('normal','normal_OFF','precompleted_result');raws={}
        for name in names:
            key='normal'if name=='normal_OFF'else name;f=inputs[key]
            raw=B.run(f,B.observation_policy(predictions[key]),observe=name!='normal_OFF')
            path=args.out_dir/(name+'.json');save(path,raw) # Always before verdict.
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'runtime source changed during native execution')
        report['CPU_executed']=True;report['controls']=None if args.mode=='probe'else controls(raws,inputs)
        report['verdict']='PASS within declared isolated cached Convert scope';save(args.out_dir/'report.json',report)
    except(ValueError,OSError,EOFError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print(args.mode,'PASS; full native Convert returned, zero models/runtime host writes')


if __name__=='__main__':main()
