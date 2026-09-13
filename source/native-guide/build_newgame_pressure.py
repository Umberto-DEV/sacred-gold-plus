#!/usr/bin/env python3
"""Build a separate Oak-only native allocation-pressure instrument, never a candidate."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import build_combined_guide as combined
from build_lease_rom import BASES, HERE, digest, require, replace_arm9, append_files, NintendoDSRom, load_text

PRESSURE_FUNCTION = r'''
static int oak_pressure_acquire(Lease *ui)
{
    u32 irq=IRQ_OFF();
    volatile u32 *block=NNS_ALLOC(ui->heap,174000,4);
    IRQ_RESTORE(irq);
    if(!block) { P->errors|=0x100;return 0; }
    P->badge=1;
    block[0]=0x51A7F00D;block[174000/4-1]=0xE09C1234;
    int actual=lease_acquire(ui);
    if(!actual) P->badge+=0x100;
    else { P->errors|=0x200;lease_release(ui); }
    if(block[0]==0x51A7F00D && block[174000/4-1]==0xE09C1234) P->badge+=0x10000;
    else P->errors|=0x400;
    Lease pressure={ui->heap,block};
    if(lease_release(&pressure)) P->badge+=0x1000000;
    return actual;
}
'''


def instrument_source():
    source = (HERE / 'combined_guide.c').read_text()
    source = '#pragma clang diagnostic ignored "-Wunused-function"\n' + source
    start = source.index('__attribute__((used,noinline,section(".text")))\nint guide_main(')
    end = source.index('__attribute__((used,noinline,section(".text")))\nvoid guide_cleanup(', start)
    source = source[:start] + source[end:]
    start = source.index('__attribute__((naked,used,section(".text"))) void eviv_hook(')
    end = source.index('#include "newgame_host.c"', start)
    source = source[:start] + '''
/* Required ELF entry symbols remain unhooked. Summary keeps original r5. */
__attribute__((naked,used,section(".text"))) void eviv_hook(void) { __asm__ volatile("bx lr"); }
__attribute__((naked,used,section(".text"))) void guide_exit_hook(void) { __asm__ volatile("bx lr"); }
''' + source[end:]
    position = source.index('#ifdef GUIDE_PRESSURE_TEST')
    source = source[:position] + PRESSURE_FUNCTION + source[position:]
    source = source.replace('#define MODAL_ACQUIRE lease_acquire', '#define MODAL_ACQUIRE oak_pressure_acquire')
    return source


def build(source, charmap, out):
    require(not out.exists() and out.resolve().is_relative_to(Path('/private/tmp')), 'New private output required')
    base = source.read_bytes()
    require(digest(base) in BASES, 'Unknown complete Plus base')
    lang, r5_sha = BASES[digest(base)]
    resources = json.loads((HERE / 'new-game-resources.json').read_text())
    r5_path = Path(resources['roms'][lang]['r5_path'])
    require(digest(r5_path.read_bytes()) == r5_sha, 'Historical r5 differs')
    prior = NintendoDSRom(r5_path.read_bytes())
    combined.oak_abi(prior)
    text, lines = combined.texts(lang, charmap, NintendoDSRom(base))
    out.mkdir(parents=True)
    prepared = out / 'pressure.c'
    prepared.write_text(instrument_source())
    obj = out / 'guide.o'
    command = ['clang','--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Os',
        '-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables',
        '-fno-asynchronous-unwind-tables','-fno-jump-tables','-Wall','-Wextra','-Werror',
        '-I'+str(HERE),'-c',str(prepared),'-o',str(obj)]
    result = subprocess.run(command,text=True,capture_output=True)
    (out/'compile.log').write_text(result.stdout+result.stderr)
    require(result.returncode == 0, 'Pressure compilation failed')
    payload, symbols = load_text(obj.read_bytes(), combined.CODE)
    main = prior.loadArm9()
    before = [bytes(section.data) for section in main.sections]
    evidence = combined.extend(main, payload, symbols, text)
    # This instrument tests Oak only: preserve original Summary dispatch.
    for offset in [0x88424,0x8856c]:
        main.sections[0].data[offset:offset+8] = before[0][offset:offset+8]
    arm9 = main.save(compress=True)
    image = replace_arm9(base,arm9)
    image,_ = append_files(image,{'a/0/2/7':prior.getFileByName('a/0/2/7')},reuse_existing=True)
    checked = NintendoDSRom(image)
    actual = checked.loadArm9()
    expected = bytearray(main.sections[0].data)
    table = 0x02000000 + sum(len(section.data) for section in main.sections)
    struct.pack_into('<II',expected,0xba0,table,table+24)
    struct.pack_into('<I',expected,0xbb4,0x02000000+len(arm9))
    require(actual.sections[0].data == expected and
            [bytes(s.data) for s in actual.sections[1:]] == [bytes(s.data) for s in main.sections[1:]],'Pressure roundtrip differs')
    require(bytes(actual.sections[1].data[:0x880]) == before[1] and bytes(actual.sections[2].data) == before[2], 'Historical TCM changed')
    allowed = set(range(0x106068,0x106074)) | set(range(0xd2c68,0xd2c6c)) | set(range(0xba0,0xba8)) | set(range(0xbb4,0xbb8))
    require({i for i,(a,b) in enumerate(zip(before[0],actual.sections[0].data)) if a != b} <= allowed, 'Unselected static mutation')
    require(checked.files == prior.files and checked.arm7 == prior.arm7
            and checked.arm9OverlayTable == prior.arm9OverlayTable
            and checked.arm7OverlayTable == prior.arm7OverlayTable, 'Unselected ROM data changed')
    target = out / f'Native New Game Pressure TEST {lang.upper()}.nds'
    target.write_bytes(image)
    require(digest(source.read_bytes()) == digest(base), 'Base changed')
    meta = {'kind':'private-native-combined-guide','language':lang,'rom_file':target.name,
        'rom_sha256':digest(image),'base_sha256':digest(base),'r5_sha256':r5_sha,
        'source_sha256':{name:digest((HERE/name).read_bytes()) for name in combined.SOURCES+['build_newgame_pressure.py']},
        'prepared_source_sha256':digest(prepared.read_bytes()),'compile_command':command,
        'object_sha256':digest(obj.read_bytes()),'payload_sha256':digest(payload),'payload_bytes':len(payload),'symbols':symbols,
        'text_sha256':digest(text),'text_bytes':len(text),'text_lines':lines,'abi':evidence,
        'memory':{'code_start':combined.CODE,'text_start':combined.TEXT,'state_start':combined.STATE,'arena_low':combined.END,
                  'modal_bytes':22528,'pressure_bytes':174000},
        'pressure_test_instrumentation':True,'normal_summary_dispatch_preserved':True,
        'scope':'Oak allocation failure only; no Summary-guide or normal UI acceptance claim'}
    (out/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
    return meta


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['rom','charmap','out']:
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    result=build(args.rom,args.charmap,args.out)
    print(json.dumps({key:result[key] for key in ['language','rom_sha256','payload_bytes']}))
