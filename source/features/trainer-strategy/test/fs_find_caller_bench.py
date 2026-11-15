"""Source-owned Find frame and one-time declared BSS input for a caller bench."""
from pathlib import Path
import hashlib,importlib.util,struct


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


F=load('find_caller_qualified_isolated',Path(__file__).with_name('fs_find_bench.py'))
need,sha=F.need,F.sha
need(sha(Path(F.__file__).read_bytes())=='09f9685bd75c48f0e836a65181a56443abf7e8bd839bd1744f1dcbadc43aa893',
     'Find caller qualified isolated source drift')
CURRENT,BASE,TOP,OUTER=F.CURRENT,F.BASE,F.TOP,0x23BF000
ROOT=struct.pack('<3I',F.ARC,0,0)
FRAME,GUARD=TOP-280,TOP-336


def require_root_input(before,after,before_regs,after_regs):
    need(type(before)is type(after)is bytes and len(before)==len(after)==0x400000,'Root setup exact whole4MiB byte preimages')
    need(F.B.u32s(before_regs)and F.B.u32s(after_regs)and before_regs==after_regs,
         'Root setup preserves all actual unsigned32 CPU registers')
    i=CURRENT-BASE
    need(before[i:i+12]==bytes(12),'Root setup once from verified initialized-bench zero preimage')
    expected=bytearray(before);expected[i:i+12]=ROOT
    need(after==bytes(expected),'Root setup changes only declared twelve BSS bytes before all APIs')
    return dict(address=CURRENT,bytes=12,before=before[i:i+12].hex(),after=after[i:i+12].hex(),
        changed_bytes=sum(a!=b for a,b in zip(before[i:i+12],ROOT)),before_ram_sha256=sha(before),after_ram_sha256=sha(after),
        registers=list(before_regs),source_fixture='Declared first-archive root; not boot-captured FSArchive state',initialized_once=True)


def coverage():
    local_start=TOP-296;global_start=OUTER-608
    need(GUARD<local_start<global_start<FRAME<TOP and TOP-FRAME==280 and FRAME-GUARD==56,
         'Find owned frame contained in old local/global projections with explicit readonly guard')
    return dict(local_projection=[local_start,TOP],frame=[FRAME,TOP],guard=[GUARD,FRAME],
        outside_global_readonly_bytes=global_start-GUARD,guard_outside_local_projection_bytes=local_start-GUARD,
        guard_inside_local_projection_bytes=FRAME-local_start,legacy_global_guard_offset_in_new_guard=[local_start-GUARD,global_start-GUARD],
        global_projection_bytes=608,heap_OFF_projection_bytes=1124,guard_is_actual_preimage=True,poison_extended=False)
