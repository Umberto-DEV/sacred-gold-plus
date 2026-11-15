"""Scoped source-interpreter additions needed by the ordinary input exploration.

These arithmetic rules are source-tested, not an original-game execution gate.
The unchanged B1 frontend handles earlier instructions. The separate DIV
selector admits only100/8 from the declared DamageDivide caller. No service
model, complete-path CPU gate or instruction budget is added here.
"""
from pathlib import Path
import hashlib
import importlib.util


path = Path(__file__).with_name('shellbell_dispatch_bench.py')
spec = importlib.util.spec_from_file_location('ordinary_pinned_dispatch', path)
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
need = B.need
PARENT_SHA = '2859e60fad6d5c83fe6a61331fc2662a9f08f03abaa2706003ce966eeaf1ec8c'
DIV_ENTRY = 0x020f2998
DIV_SHA = 'e8183a62ffe6a54210cd7d025b01431ff792025c1b45a0e8537abd8cec16ccfb'


def source_identity_guard():
    need(hashlib.sha256(path.read_bytes()).hexdigest() == PARENT_SHA,
         'pinned owned-dispatch frontend drift')
    B.source_identity_guard()


def select_division(pc, regs, pages):
    """Only the observed consumer candidate100/8 through DamageDivide is routed.

    This adds a source prediction domain, not a native-execution permission.
    The older MaxPP selector and all its domains remain unchanged.
    """
    need(type(pc) is int and pc == DIV_ENTRY, 'exact ordinary DIV entry')
    need(type(regs) is list and len(regs) == 16 and
         all(type(x) is int and 0 <= x <= 0xffffffff for x in regs), 'typed DIV full16')
    need(regs[:2] == [100, 8] and regs[14] == 0x0225318d and regs[15] & 0x3f == 0x1f,
         'finite ordinary division100/8 and caller')
    need(hashlib.sha256(B.M.read(pages, DIV_ENTRY, 524)).hexdigest() == DIV_SHA,
         'exact ordinary DIV corpus')
    parent_selector = B.A.run.__globals__['select_arm']
    engine = parent_selector.__globals__['D']
    need(hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest() ==
         'a73b6128514f76ca46fc710e3cee51f6881a35bc6b817ba34dbc65e710284559',
         'pinned DIV source interpreter')
    return engine, ((DIV_ENTRY, 524),)


def validate_thumb(blob):
    if type(blob) is bytes and len(blob) == 2:
        op = int.from_bytes(blob, 'little')
        if op & 0xffc0 == 0x4200:
            return 'ordinary_TST'
        if op & 0xffc0 in (0x4300, 0x4380):
            return 'ordinary_ORR_BIC'
        if op & 0xffc0 == 0x43c0:
            return 'ordinary_MVN'
        if op & 0xffc0 == 0x4240:
            return 'ordinary_NEG'
        if op == 0x46c0:
            return 'ordinary_NOP'
        if op & 0xfe00 in (0x5a00, 0x5e00):
            return 'ordinary_LDRH_register'
        if op in (0x4694, 0x46a4, 0x46ac, 0x4660):
            return 'ordinary_MOV_ip'
        if op & 0xfe00 in (0x5000, 0x5400):
            return 'ordinary_STR_register'
        if op in (0x447a, 0x4497, 0x447b, 0x449f, 0x447d, 0x44af):
            return 'ordinary_ADD_pc_r2'
        if op == 0x4790:
            return 'ordinary_BLX_r2'
        if op & 0xff00 in (0xd200, 0xd500, 0xda00, 0xdb00, 0xdd00):
            return 'ordinary_BPL_BGE_BLT'
    return B.validate_thumb(blob)


def thumb_step(pc, blob, regs, pages, reads, stores, read_guard=None, write_guard=None):
    kind = validate_thumb(blob)
    if kind not in ('ordinary_TST', 'ordinary_ORR_BIC', 'ordinary_MVN', 'ordinary_NEG', 'ordinary_NOP', 'ordinary_MOV_ip', 'ordinary_LDRH_register', 'ordinary_STR_register', 'ordinary_ADD_pc_r2', 'ordinary_BLX_r2', 'ordinary_BPL_BGE_BLT'):
        return B.thumb_step(pc, blob, regs, pages, reads, stores, read_guard, write_guard)
    need(type(pc) is int and pc % 2 == 0 and 0 <= pc <= 0xfffffffc,
         'aligned ordinary Thumb PC')
    need(len(regs) == 16 and all(type(x) is int and 0 <= x <= 0xffffffff for x in regs)
         and regs[15] & 0x3f == 0x3f, 'typed ordinary Thumb System registers')
    op = int.from_bytes(blob, 'little')
    if kind == 'ordinary_NOP':
        return (pc + 2) & 0xffffffff
    if kind == 'ordinary_NEG':
        operand = regs[(op >> 3) & 7]
        value = (-operand) & 0xffffffff
        regs[op & 7] = value
        regs[15] = ((regs[15] & 0x0fffffff) | (value & 0x80000000)
                    | (int(value == 0) << 30) | (int(operand == 0) << 29)
                    | (int(operand == 0x80000000) << 28))
        return (pc + 2) & 0xffffffff
    if kind == 'ordinary_MOV_ip':
        if op == 0x4660:
            regs[0] = regs[12]
        else:
            regs[12] = regs[(op >> 3) & 15]
        return (pc + 2) & 0xffffffff
    if kind == 'ordinary_BLX_r2':
        need(regs[2] & 1, 'ordinary BLX r2 requires an odd Thumb target')
        regs[14] = (pc + 2) | 1
        return regs[2] & ~1
    if kind == 'ordinary_STR_register':
        width = 1 if op & 0xfe00 == 0x5400 else 4
        address = (regs[(op >> 3) & 7] + regs[(op >> 6) & 7]) & 0xffffffff
        need(address % width == 0, 'aligned ordinary store')
        if write_guard:
            need(write_guard(pc, address, width), 'ordinary store owner/site')
        before = B.M.read(pages, address, width)
        value = regs[op & 7] & ((1 << (8 * width)) - 1)
        stores.append(dict(pc=pc, address=address, bytes=width, before=before.hex(), value=value))
        B.M.put(pages, address, value.to_bytes(width, 'little'))
        return (pc + 2) & 0xffffffff
    if kind == 'ordinary_ADD_pc_r2':
        reg = 5 if op in (0x447d, 0x44af) else 3 if op in (0x447b, 0x449f) else 2
        if op in (0x4497, 0x449f, 0x44af):
            return ((pc + 4 + regs[reg]) & 0xffffffff) & ~1
        regs[reg] = (regs[reg] + pc + 4) & 0xffffffff
        return (pc + 2) & 0xffffffff
    if kind == 'ordinary_LDRH_register':
        address = (regs[(op >> 3) & 7] + regs[(op >> 6) & 7]) & 0xffffffff
        need(address % 2 == 0, 'aligned ordinary halfword read')
        if read_guard:
            need(read_guard(pc, address, 2), 'ordinary halfword read owner/site')
        data = B.M.read(pages, address, 2)
        reads.append(dict(pc=pc, address=address, bytes=2, hex=data.hex()))
        value = int.from_bytes(data, 'little', signed=op & 0xfe00 == 0x5e00)
        regs[op & 7] = value & 0xffffffff
        return (pc + 2) & 0xffffffff
    if kind in ('ordinary_TST', 'ordinary_ORR_BIC', 'ordinary_MVN'):
        left, right = regs[op & 7], regs[(op >> 3) & 7]
        value = (~right & 0xffffffff if kind == 'ordinary_MVN' else
                 left & right if kind == 'ordinary_TST' else
                 left & (~right & 0xffffffff) if op & 0xffc0 == 0x4380 else left | right)
        if kind != 'ordinary_TST':
            regs[op & 7] = value
        regs[15] = (regs[15] & 0x3fffffff) | (value & 0x80000000) | (int(value == 0) << 30)
        return (pc + 2) & 0xffffffff
    n, v = bool(regs[15] & 0x80000000), bool(regs[15] & 0x10000000)
    condition = op >> 8
    taken = {0xd2: bool(regs[15] & 0x20000000), 0xd5: not n,
             0xda: n == v, 0xdb: n != v,
             0xdd: bool(regs[15] & 0x40000000) or n != v}[condition]
    delta = op & 255
    if delta & 128:
        delta -= 256
    return (pc + 4 + 2 * delta if taken else pc + 2) & 0xffffffff
