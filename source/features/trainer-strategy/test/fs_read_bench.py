"""Isolated native Read core with explicit payload/position and BOOL boundaries.

No filesystem completion, queue, error or SYNC-clear equivalence is claimed.
Input frames are copies; code and raw payload must be authenticated by the caller.
"""
import copy, hashlib, struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
    UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR,
    UC_ARM_REG_PC, UC_ARM_REG_CPSR)

REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
    UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
    UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_CPSR)
BASE, SIZE, CORE, WRAPPER, SEND, WAIT = 0x2000000, 0x400000, 0x20D8104, 0x20D83CC, 0x20D7788, 0x20D82FC
TOP, FRAME, FILE, DEST = 0x23BEEC0, 0x23BEDD0, 0x23BEE50, 0x23BEEC0
U32 = 0xFFFFFFFF
sha = lambda b: hashlib.sha256(b).hexdigest()


def need(value, message):
    if not value: raise ValueError(message)


def u32s(values):
    return len(values) == 16 and all(type(v) is int and 0 <= v <= U32 for v in values)


def signed(v): return v if v < 0x80000000 else v - 0x100000000


def cmp(a, b, old):
    result = (a - b) & U32
    n, z, c = result >> 31, int(result == 0), int(a >= b)
    v = int(bool(((a ^ b) & (a ^ result)) & 0x80000000))
    return (old & 0x0FFFFFFF) | (n << 31) | (z << 30) | (c << 29) | (v << 28)


def check_fixture(f):
    r = f['entry']; need(u32s(r), 'Read input registers must be unsigned32')
    need(r[0] == FILE and r[13] == TOP - 136 and r[14] & 1 and r[15] & 0x0FFFFFFF == 0x1F,
         'Read derived ARM entry ABI')
    need(len(bytes.fromhex(f['frame'])) == 240, 'Read input frame extent')
    need(len(bytes.fromhex(f['destination_before'])) == r[2] and 0 < r[2] <= 16,
         'Read finite destination extent')
    need(BASE <= r[1] and r[1] + r[2] <= BASE + SIZE and
         (r[1] + r[2] <= FILE or r[1] >= FILE + 72), 'Read output cannot overlap FSFile')
    need(r[1] + r[2] <= r[13] - 24 or r[1] >= r[13], 'Read output cannot overlap native saved frame')
    blob = bytes.fromhex(f['frame']); top, bottom, pos = struct.unpack_from('<3I', blob, FILE - FRAME + 36)
    need(0 <= top <= pos <= bottom < 0x80000000 and r[2] <= bottom - pos,
         'Read finite successful geometry, signed bounds')
    need(len(bytes.fromhex(f['payload'])) == r[2], 'Read exact raw payload length')
    if FRAME <= r[1] and r[1] + r[2] <= FRAME + 240:
        need(blob[r[1] - FRAME:r[1] - FRAME + r[2]].hex() == f['destination_before'],
             'Read frame/output preimage overlap agrees')
    return top, bottom, pos


def boundary_regs(regs, result, clobber):
    r = list(regs)
    if clobber:
        for i in (1, 2, 3, 12): r[i] = 0xA5000000 | i
        r[15] = (r[15] & 0x0FFFFFFF) | 0xA0000000
    r[0] = result
    return r


def predict(f, wait_value=1, send_value=1, clobber=False):
    """Source/dataflow oracle, independent of guest hooks and instruction decoding."""
    check_fixture(f); need(type(wait_value) is int and wait_value in (0, 1, 2) and type(send_value) is int and send_value in (0, 1) and type(clobber) is bool, 'finite BOOL policies')
    r = list(f['entry']); memory = bytearray(bytes.fromhex(f['frame'])); flow = {}; stores = []; services = []
    required = []; optional = []

    def at(pc, effect=True):
        flow[hex(pc)] = list(r); (required if effect else optional).append(hex(pc))

    def word(address): return struct.unpack_from('<I', memory, address - FRAME)[0]

    def store(pc, address, value):
        before = bytes(memory[address - FRAME:address - FRAME + 4]); struct.pack_into('<I', memory, address - FRAME, value)
        stores.append(dict(pc=hex(pc), address=address, bytes=4, before=before.hex(), value=value))

    def service(pc, result):
        before = list(r); frame_before = memory.hex()
        if pc == SEND:
            length = word(FILE + 56); dest = word(FILE + 48); pos = word(FILE + 44)
            need(length == f['entry'][2] and dest == f['entry'][1], 'Read source args into provider')
            if FRAME <= dest and dest + length <= FRAME + 240:
                memory[dest - FRAME:dest - FRAME + length] = bytes.fromhex(f['payload'])
            struct.pack_into('<I', memory, FILE - FRAME + 44, pos + length)
        after = boundary_regs(r, result, clobber); r[:] = after
        services.append(dict(pc=hex(pc), entry=before, returned=after, frame_before=frame_before,
                             frame_after=memory.hex(), result=result))

    at(WRAPPER); r[12] = CORE
    at(WRAPPER + 4); r[3] = 0
    at(WRAPPER + 8)
    at(CORE); r[13] -= 24
    for i, index in enumerate((3, 4, 5, 6, 7, 14)): store(CORE, r[13] + 4 * i, r[index])
    at(0x20D8108); r[7] = r[0]
    at(0x20D810C); r[4] = word(FILE + 44)
    at(0x20D8110); r[0] = word(FILE + 40)
    at(0x20D8114); r[6] = r[2]
    at(0x20D8118); store(0x20D8118, FILE + 48, r[1])
    at(0x20D811C); r[0] = (r[0] - r[4]) & U32
    at(0x20D8120); r[15] = cmp(r[6], r[0], r[15])
    gt = signed(r[6]) > signed(r[0]); at(0x20D8124, gt)
    if gt: r[6] = r[0]
    at(0x20D8128); r[15] = cmp(r[6], 0, r[15])
    lt = signed(r[6]) < 0; at(0x20D812C, lt)
    if lt: r[6] = 0
    at(0x20D8130); store(0x20D8130, FILE + 52, r[2])
    at(0x20D8134); r[5] = r[3]
    at(0x20D8138); store(0x20D8138, FILE + 56, r[6])
    at(0x20D813C); r[15] = cmp(r[5], 0, r[15])
    at(0x20D8140); r[0] = word(FILE + 12)
    at(0x20D8144); r[1] = 0
    at(0x20D8148); r[0] |= 4
    at(0x20D814C); store(0x20D814C, FILE + 12, r[0])
    at(0x20D8150); r[0] = FILE
    at(0x20D8154); r[14] = 0x20D8158; service(SEND, send_value)
    at(0x20D8158); r[15] = cmp(r[5], 0, r[15])
    at(0x20D815C)
    at(0x20D8160); r[0] = FILE
    at(0x20D8164); r[14] = 0x20D8168; service(WAIT, wait_value)
    at(0x20D8168); r[15] = cmp(r[0], 0, r[15])
    at(0x20D816C, bool(wait_value))
    if wait_value: r[0] = word(FILE + 44)
    at(0x20D8170, bool(wait_value))
    if wait_value: r[6] = (r[0] - r[4]) & U32
    at(0x20D8174, not wait_value)
    if not wait_value: r[6] = U32
    at(0x20D8178); r[0] = r[6]
    at(0x20D817C)
    for i, index in enumerate((3, 4, 5, 6, 7)): r[index] = word(r[13] + 4 * i)
    target = word(r[13] + 20); r[13] += 24; r[15] |= target & 1 and 0x20
    return dict(flow=flow, required=required, optional=optional, stores=stores,
        services=services, returned=r, frame_after=memory.hex(), destination_after=f['payload'],
        stop=hex(target & ~1), native_peak=24)


def run(f, bodies, wait_value=1, send_value=1, clobber=False, observe=True, fill=0xA5):
    check_fixture(f); need(type(fill) is int and 0 <= fill <= 255, 'finite RAM fill')
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM); need(u.ctl_get_cpu_model() == 17, 'qualified CPU17')
    u.mem_map(BASE, SIZE); u.mem_write(BASE, bytes([fill]) * SIZE)
    for address, blob in bodies.items(): u.mem_write(address, blob)
    u.mem_write(FRAME, bytes.fromhex(f['frame'])); u.mem_write(f['entry'][1], bytes.fromhex(f['destination_before']))
    # Mode selection precedes banked SP/LR initialization (default Uc is SVC).
    u.reg_write(UC_ARM_REG_CPSR, f['entry'][15])
    for reg, value in zip(REGS[:-1], f['entry'][:-1]): u.reg_write(reg, value)
    stop = f['entry'][14] & ~1; before = bytes(u.mem_read(BASE, SIZE)); flow = []; stores = []; reads = []; services = []
    allowed = set(range(CORE, CORE + 124, 4)) | {WRAPPER, WRAPPER + 4, WRAPPER + 8}
    steps = 0; returned = None

    def regs(): return [u.reg_read(r) for r in REGS]

    def step(uc, pc, n, _):
        nonlocal steps, returned
        steps += 1; need(steps <= 100, 'isolated Read instruction budget')
        if pc == stop:
            returned = regs(); u.emu_stop(); return
        if pc in (SEND, WAIT):
            entry = regs(); frame_before = bytes(u.mem_read(FRAME, 240)); need(entry[0] == FILE, 'Read SDK file ABI')
            if pc == SEND:
                need(entry[1] == 0 and entry[14] == 0x20D8158, 'Read Send0 command/LR ABI')
                dst, org, length = struct.unpack('<3I', bytes(u.mem_read(FILE + 48, 12)))
                pos = struct.unpack('<I', bytes(u.mem_read(FILE + 44, 4)))[0]
                need((dst, org, length) == (f['entry'][1], f['entry'][2], f['entry'][2]), 'Read actual native arguments')
                need(pos == check_fixture(f)[2], 'Read actual provider position')
                u.mem_write(dst, bytes.fromhex(f['payload'])); u.mem_write(FILE + 44, struct.pack('<I', pos + length))
                value = send_value
            else:
                need(entry[14] == 0x20D8168, 'Read Wait LR ABI'); value = wait_value
            result = boundary_regs(entry, value, clobber)
            for reg, value in zip(REGS, result): u.reg_write(reg, value)
            services.append(dict(pc=hex(pc), entry=entry, returned=regs(), frame_before=frame_before.hex(),
                frame_after=bytes(u.mem_read(FRAME, 240)).hex(), result=result[0]))
            u.reg_write(UC_ARM_REG_PC, entry[14]); return
        need(pc in allowed and n == 4, 'Read instruction/size whitelist; literal cannot execute')
        if observe: flow.append(dict(pc=hex(pc), regs=regs()))

    def write(uc, access, address, n, value, _):
        pc = u.reg_read(UC_ARM_REG_PC)
        allowed_write = (pc == CORE and f['entry'][13] - 24 <= address < f['entry'][13]) or (
            (pc, address) in ((0x20D8118, FILE + 48), (0x20D8130, FILE + 52),
                            (0x20D8138, FILE + 56), (0x20D814C, FILE + 12)))
        need(allowed_write and n == 4, 'Read native write owner/width')
        if observe: stores.append(dict(pc=hex(pc), address=address, bytes=n,
            before=bytes(u.mem_read(address, n)).hex(), value=value))

    def read(uc, access, address, n, value, _):
        pc = u.reg_read(UC_ARM_REG_PC)
        need(n == 4 and ((pc == WRAPPER and address == WRAPPER + 12) or
            (pc in (0x20D810C, 0x20D816C) and address == FILE + 44) or
            (pc == 0x20D8110 and address == FILE + 40) or
            (pc == 0x20D8140 and address == FILE + 12) or
            (pc == 0x20D817C and f['entry'][13] - 24 <= address < f['entry'][13])),
            'Read native data/literal/saved-frame read owner')
        if observe: reads.append(dict(pc=hex(pc), address=address, bytes=n, hex=bytes(u.mem_read(address,n)).hex()))

    u.hook_add(UC_HOOK_CODE, step); u.hook_add(UC_HOOK_MEM_WRITE, write); u.hook_add(UC_HOOK_MEM_READ, read)
    fault = None
    try: u.emu_start(WRAPPER, BASE + SIZE, timeout=1000000, count=100)
    except Exception as error:
        fault = dict(type=type(error).__name__, message=str(error)[:512])
    after = bytes(u.mem_read(BASE, SIZE)); dst, length = f['entry'][1:3]
    result = dict(fixture=copy.deepcopy(f), policy=dict(wait=wait_value, send=send_value, clobber=clobber),
        observe=observe, fill=fill, cpu_model=17, entry=list(f['entry']), returned=returned, stop=hex(stop),
        fault=fault, halt_pc=hex(u.reg_read(UC_ARM_REG_PC)), halt_regs=regs(),
        flow=flow, stores=stores, reads=reads, services=services, steps=steps,
        frame_after=bytes(u.mem_read(FRAME, 240)).hex(), destination_after=bytes(u.mem_read(dst,length)).hex(),
        whole_ram_sha256=sha(after), before_whole_ram_sha256=sha(before), native_peak=24)
    del u
    return result


def require_result(r, bodies):
    f = r['fixture']; p = r['policy']; expected = predict(f, p['wait'], p['send'], p['clobber'])
    need(type(r['observe']) is bool and type(r['fill']) is int and 0 <= r['fill'] <= 255 and
         type(r['steps']) is int and 0 < r['steps'] <= 100, 'Read observer/fill/step finite types')
    need(r['fault'] is None and r['halt_pc'] == expected['stop'] and r['halt_regs'] == r['returned'],
         'Read must return to original caller without CPU fault')
    need(r['entry'] == f['entry'] and r['cpu_model'] == 17 and u32s(r['returned']), 'Read entry/CPU/return width')
    for key in ('returned', 'frame_after', 'destination_after', 'stop', 'native_peak', 'services'):
        need(r[key] == expected[key], 'Read source/dataflow ' + key)
    memory = bytearray([r['fill']]) * SIZE
    for address, blob in bodies.items(): memory[address-BASE:address-BASE+len(blob)] = blob
    memory[FRAME-BASE:FRAME-BASE+240] = bytes.fromhex(f['frame'])
    dst, length = f['entry'][1:3]; memory[dst-BASE:dst-BASE+length] = bytes.fromhex(f['destination_before'])
    need(r['before_whole_ram_sha256'] == sha(memory), 'Read whole memory input identity')
    memory[FRAME-BASE:FRAME-BASE+240] = bytes.fromhex(expected['frame_after'])
    memory[dst-BASE:dst-BASE+length] = bytes.fromhex(f['payload'])
    need(r['whole_ram_sha256'] == sha(memory), 'Read exact whole memory delta')
    if r['observe']:
        pcs = [e['pc'] for e in r['flow']]
        need(pcs == list(expected['flow']), 'Read CPU17 qualified complete34 hook delivery/order')
        need(all(u32s(e['regs']) and e['regs'] == expected['flow'][e['pc']] for e in r['flow']),
             'Read full register instruction dataflow')
        need(r['stores'] == expected['stores'], 'Read exact ten native stores')
        expected_reads = [(WRAPPER,WRAPPER+12),(0x20D810C,FILE+44),(0x20D8110,FILE+40),(0x20D8140,FILE+12)]
        if p['wait']: expected_reads.append((0x20D816C,FILE+44))
        expected_reads += [(0x20D817C,f['entry'][13]-24+4*i) for i in range(6)]
        need([(int(e['pc'],16), e['address']) for e in r['reads']] == expected_reads, 'Read actual owned reads')
        # Read values must match the independent fixture/source flow, including literal and native saved words.
        saved = [0, *f['entry'][4:8], f['entry'][14]]
        values = [CORE, check_fixture(f)[2], check_fixture(f)[1], struct.unpack_from('<I', bytes.fromhex(f['frame']), FILE-FRAME+12)[0]]
        if p['wait']: values.append(check_fixture(f)[2] + f['entry'][2])
        values += saved
        need(all(e['bytes'] == 4 and e['hex'] == struct.pack('<I', v).hex() for e,v in zip(r['reads'],values)), 'Read literal/field/saved values')
        need(r['steps'] == len(r['flow']) + 3, 'Read two SDK boundaries and return count')
    else:
        need(not r['flow'] and not r['stores'] and not r['reads'] and r['steps'] == 37,
             'Read OFF observations absent, finite coverage budget')
    return True
