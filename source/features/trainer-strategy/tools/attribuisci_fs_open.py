#!/usr/bin/env python3
"""Native Open wrapper in the qualified PP caller, with two lower FS models.

Path conversion and OpenFast are opaque boundaries. No native archive, card or
FSFile state is fabricated by the wrapper observer.
"""
from pathlib import Path
import importlib.util, types, struct, copy


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


O = load('fs_open_init_parent', Path(__file__).with_name('attribuisci_fs_init.py'))
A = load('fs_open_profile', Path(__file__).parents[1] / 'test/fs_open_bench.py'); A.bind(O)
H, R, P, B, T = O.H, O.R, O.P, O.B, O.T
need, sha = O.need, O.sha
TOP, DEST, STOP, FILE = O.TOP, O.DEST, O.STOP, O.FILE
ENTRY, END, RETURN = 0x20D8278, 0x20D82C0, 0x2007352
CONVERT, FAST, ID, ARC = 0x20D8180, 0x20D8208, TOP - 152, 0x21E3654
OPEN_SHA = '844c19c244efe83b1be9dd83f73da60917d201793d237d72cf0a429ca9158a2d'
SDK = {a: name for a, name in R.SDK.items() if a not in (O.ENTRY, ENTRY)}
SDK.update({CONVERT: 'FS_ConvertPathToFileID', FAST: 'FS_OpenFileFast'})
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_CPSR


def qualify(model, raw, *args):
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    q, proof = O.qualify(model, raw, *args)
    view = P.G.S.SHARED.gifts_audit.Arm9View(raw); blob = view.read(ENTRY, 72)
    need(sha(blob) == OPEN_SHA and blob == P.G.piece(model['segments'], ENTRY, 72), 'Open raw/section identity')
    instructions = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(blob, ENTRY))
    need(len(instructions) == 18 and all(i.size == 4 for i in instructions) and
         [i.address for i in instructions] == list(range(ENTRY, END, 4)), 'Open exact ARM instruction extent')
    calls = {i.address: i.op_str for i in instructions if i.mnemonic == 'bl'}
    need(calls == {0x20D8288: '#0x20d8180', 0x20D82A0: '#0x20d8208'}, 'Open two lower ARM call targets')
    q['fs_open_code'] = {i.address: (4, False) for i in instructions}
    proof['native_fs_open'] = dict(ram=hex(ENTRY), bytes=72, sha256=sha(blob),
        rom_offset=hex(view.offset(ENTRY, 72)), admitted_starts=18, positive_starts=15,
        lower_models={hex(CONVERT): 'FS_ConvertPathToFileID', hex(FAST): 'FS_OpenFileFast'},
        open_frame_bytes=16, reader_peak=152, reader_guard=[TOP - 208, TOP - 152],
        limits='Wrapper only; lower SDK bodies and opaque archive token are not native filesystem state')
    return q, proof


class OpenObserver:
    def __init__(self, driver, reader):
        self.driver, self.reader = driver, reader
        self.active = False
        self.result = dict(entry=None, returned=None, before16=None, after16=None,
            frame_before=None, frame_after=None, flow=[], stores=[], id_reads=[], shadows=[],
            ledger_before=None, ledger_after=None)
        reader.code = {**reader.code, **driver.qualified['fs_open_code']}
        init = driver.fs_observer
        init.base_step = types.MethodType(A.clone(init.base_step.__func__, dict(SDK=SDK)), reader)
        self.base_step = reader.step
        self.base_service = reader.service
        self.base_write = reader.write
        self.base_read = reader.read
        init.base_write = types.MethodType(open_write, reader)
        reader.step, reader.service, reader.write, reader.read = self.step, self.service, self.write, self.read

    def ledger(self):
        r = self.reader
        return dict(initialized=r.initialized, file=r.file, open=r.open, cursor=r.cursor, path=r.path,
                    archive_sha256=None if r.archive is None else sha(r.archive))

    def step(self, u, pc, n, user):
        r, out = self.reader, self.result
        if pc == ENTRY:
            need(out['entry'] is None and r.initialized and r.file == FILE and not r.open,
                 'single actual Open after native Init')
            self.active = True
            out.update(entry=r.regs(), before16=r.read_bytes(ID, 16).hex(),
                       frame_before=r.read_bytes(ID, 152).hex(), ledger_before=self.ledger())
        if pc == RETURN:
            need(self.active and out['returned'] is None, 'single native Open return to Thumb caller')
            out.update(returned=r.regs(), after16=r.read_bytes(ID, 16).hex(),
                       frame_after=r.read_bytes(ID, 152).hex(), ledger_after=self.ledger())
            self.active = False
        if self.active and ENTRY <= pc < END:
            out['flow'].append(dict(pc=hex(pc), regs=r.regs()))
        self.base_step(u, pc, n, user)
        if self.active and pc == 0x20D82A4 and self.driver.open_variant == 'fs_open_false':
            before = r.regs(); need(before[0] == 1 and r.open, 'Open false shadow follows successful lower model')
            u.reg_write(B.R[0], 0)
            out['shadows'].append(dict(pc=hex(pc), before=before, after=r.regs(),
                reason='R0 only after valid modeled OpenFast; native wrapper false path, archive remains open'))

    def write(self, u, access, address, n, value, user):
        if address < TOP - 136:
            need(self.active and ID <= address and address + n <= TOP - 136,
                 'new sixteen stack bytes belong only to native Open')
        if self.active and self.reader.observe:
            self.result['stores'].append(dict(pc=hex(u.reg_read(UC_ARM_REG_PC)), address=address,
                bytes=n, before=self.reader.read_bytes(address, n).hex(), value=value))
        self.base_write(u, access, address, n, value, user)

    def read(self, u, access, address, n, value, user):
        if self.active and u.reg_read(UC_ARM_REG_PC) == 0x20D829C:
            self.result['id_reads'].append(dict(pc='0x20d829c', address=address, bytes=n,
                                               hex=self.reader.read_bytes(address, n).hex()))
        self.base_read(u, access, address, n, value, user)

    def service(self, pc):
        if pc not in (CONVERT, FAST): return self.base_service(pc)
        r, u = self.reader, self.reader.u
        before = r.regs(); args = before[:4]; sp, lr = before[13:15]
        need(self.active and sp == ID and not before[15] & 32 and r.initialized and r.file == FILE,
             'Open lower model actual ARM frame/Init lifetime')
        event = dict(name=SDK[pc], pc=hex(pc), args=args, sp=sp, lr=hex(lr), saved=before[4:12],
                     cursor_before=r.cursor, open_before=r.open, entry=before)
        if pc == CONVERT:
            need(args[0] == ID and args[1] == 0x210F198 and not r.open and r.archive is None and
                 not any(e['name'] == SDK[CONVERT] for e in r.models), 'single path conversion output buffer')
            name = bytearray()
            for offset in range(16):
                byte = r.read_bytes(args[1] + offset, 1)[0]
                if not byte: break
                name.append(byte)
            else: raise ValueError('Open bounded actual path terminator')
            matches = [v for v in r.data.values() if v['path'].encode() == bytes(name)]
            need(len(matches) == 1 and matches[0]['oracle']['file_id'] == 140,
                 'Open path maps to independently read raw FNT file140')
            r.path = name.decode('ascii'); blob = struct.pack('<II', ARC, 140)
            previous = r.read_bytes(ID, 8); u.mem_write(ID, blob)
            event.update(path=r.path, file_id=140, opaque_archive_token=ARC, destination=ID,
                         before_hex=previous.hex(), delivered_hex=blob.hex(), delivered_sha256=sha(blob))
            result = 1
        else:
            need(args[:3] == [FILE, ARC, 140] and r.path == 'a/0/1/1' and not r.open and
                 r.archive is None and r.read_bytes(ID, 8) == struct.pack('<II', ARC, 140),
                 'OpenFast receives actual native by-value FSFileID')
            matches = [v for v in r.data.values() if v['path'] == r.path]
            need(len(matches) == 1, 'OpenFast whole archive identity')
            r.archive = matches[0]['raw']; r.open = True; r.cursor = 0
            event.update(path=r.path, archive_bytes=len(r.archive), archive_sha256=sha(r.archive),
                         native_FSFile_layout_modeled=False, opaque_archive_token=ARC, file_id=140)
            result = self.driver.open_fast_value
        if r.clobber:
            for i in (1, 2, 3, 12): u.reg_write(B.R[i], 0xA5000000 + i)
            u.reg_write(UC_ARM_REG_CPSR, (u.reg_read(UC_ARM_REG_CPSR) & 0x0FFFFFFF) | 0xA0000000)
        u.reg_write(B.R[0], result); u.reg_write(UC_ARM_REG_PC, lr)
        after = r.regs()
        need(after[13] == sp and after[4:12] == before[4:12] and not after[15] & 32,
             'Open lower model actual ARM-to-ARM return and callee-saved state')
        event.update(result_r0=result, return_sp=after[13], return_saved=after[4:12],
                     return_volatile=[after[i] for i in (1, 2, 3, 12)], cursor_after=r.cursor,
                     open_after=r.open, returned=after)
        r.models.append(event)


class Driver(O.Driver):
    def __init__(self, *args, variant='current', open_fast_value=1, **kwargs):
        need(variant in ('current', 'fs_open_false') and type(open_fast_value) is int and
             open_fast_value in (1, 2) and (variant == 'current' or open_fast_value == 1), 'finite Open controls')
        super().__init__(*args, variant='current', **kwargs)
        self.open_variant, self.open_fast_value, self.fs_open_result = variant, open_fast_value, None

    def start_pp(self):
        super().start_pp()
        regs, before = self.regs(), self.read_bytes(0x2000000, 0x400000)
        self.open_observer = OpenObserver(self, self.pp_reader); self.fs_open_result = self.open_observer.result
        need(regs == self.regs() and before == self.read_bytes(0x2000000, 0x400000),
             'Open attachment changes neither CPU nor RAM')


def bindings():
    write, p1 = A.rewrite(O, R, 'Reader.write', [('TOP-136<=address', 'TOP-152<=address', 1)],
                         dict(TOP=TOP), 'narc_reader')
    snapshot_edits = A.edits(H, 1) + [
        ('((TOP-192,192),(DEST,size))', '((TOP-208,208),(DEST,size))', 1),
        ('self.read_bytes(TOP-192,56)==self.before[TOP-192-0x2000000:TOP-136-0x2000000]',
         'self.read_bytes(TOP-208,56)==self.before[TOP-208-0x2000000:TOP-152-0x2000000]', 1)]
    snapshot, p2 = A.rewrite(O, R, 'Reader.run', snapshot_edits,
        dict(TOP=TOP, DEST=DEST, STOP=STOP, COOKIES=H.COOKIES, neighbors_before=H.neighbors_before), 'narc_reader')
    finish, p3 = A.rewrite(O, H, 'Driver.finish_pp', [
        ('stack_guard_before=r.before[TOP-192-0x2000000:TOP-136-0x2000000].hex()',
         'stack_guard_before=r.before[TOP-208-0x2000000:TOP-152-0x2000000].hex()', 1),
        ('stack_guard_after=self.read_bytes(TOP-192,56).hex()', 'stack_guard_after=self.read_bytes(TOP-208,56).hex()', 1),
        ('self.pp_result.update(same_cpu=', 'self.pp_result.update(stack152_before=r.before[TOP-152-0x2000000:TOP-0x2000000].hex(),stack152_after=self.read_bytes(TOP-152,152).hex(),stack_guard_range=[TOP-208,TOP-152],same_cpu=', 1)],
        dict(TOP=TOP, pp_snapshot=snapshot), 'pp_caller')
    run, p4 = A.rewrite(O, H.V, 'run_case', A.edits(O, 1) + [
        ('pp_clobber=False):', 'pp_clobber=False,open_fast_value=1):', 1),
        ('pp_clobber=pp_clobber)', 'pp_clobber=pp_clobber,open_fast_value=open_fast_value)', 1),
        ('return dict(fs_init=', 'return dict(fs_open=driver.fs_open_result,open_fast_value=driver.open_fast_value,fs_init=', 1)],
        dict(Driver=Driver, A=H.A, NAME_ARENA=H.X.NAME_ARENA, NAME_END=H.X.NAME_END), 'message_caller')
    return write, snapshot, finish, run, [p1, p2, p3, p4]


open_write, pp_snapshot, Driver.finish_pp, run_case, RECIPES = bindings()


def native_binding():
    edits = A.edits(O, 0) + [
        ("r['instructions']==127", "r['instructions']==EXPECTED_HOOKS", 1),
        ("r['max_stack']==136", "r['max_stack']==152", 1),
        ("len(code)==113", "len(code)==EXPECTED_PC_COUNT", 1),
        (" ('FS_OpenFile',0x2007353,[path,0],[path,310,c6,c7],None),",
         " ('FS_ConvertPathToFileID',0x20D828C,[path,0],[file,310,c6,c7],None),\n ('FS_OpenFileFast',0x20D82A4,[ARC,140],[file,310,c6,c7],None),", 1),
        ("len(r['models'])==14", "len(r['models'])==15", 1),
        ("event['sp']==event['return_sp']==local",
         "event['sp']==event['return_sp']==(ID if name in ('FS_ConvertPathToFileID','FS_OpenFileFast') else local)", 1),
        ("args=[file]+args12", "args=[ID if name=='FS_ConvertPathToFileID' else file]+args12", 1),
        ("result=read[2] if read else 1", "result=FAST_VALUE if name=='FS_OpenFileFast' else read[2] if read else 1", 1),
        ("if name=='FS_OpenFile':",
         "if name=='FS_ConvertPathToFileID':\n   need(event['path']==o['path'] and event['file_id']==140 and event['opaque_archive_token']==ARC and event['destination']==ID and event['delivered_hex']==struct.pack('<II',ARC,140).hex() and event['delivered_sha256']==sha(struct.pack('<II',ARC,140)),'Open modeled file ID raw-FNT provenance');model_writes.append((ID,struct.pack('<II',ARC,140)))\n  elif name=='FS_OpenFileFast':", 1),
        ("store(0x20073EE,local+20,4,size)", "push(0x20D8278,TOP-144,[path,0x2007353])\n store(0x20073EE,local+20,4,size)", 1),
        ("len(expected)==17+len(STORES)", "len(expected)==19+len(STORES)", 1),
        ("stack=bytearray.fromhex(r['stack_frame_before']);need(len(stack)==136,'actual reader stack preimage size')",
         "stack=bytearray.fromhex(r['stack152_before']);need(len(stack)==152,'actual extended reader stack preimage size')", 1),
        ("stack[e['address']-local:e['address']-local+e['bytes']]",
         "stack[e['address']-(local-16):e['address']-(local-16)+e['bytes']]", 1),
        ("stack[dest-local:dest-local+len(blob)]", "stack[dest-(local-16):dest-(local-16)+len(blob)]", 1),
        ("struct.pack_into('<I',stack,20,size)", "struct.pack_into('<I',stack,36,size)", 1),
        ("r['stack_frame_hex']==stack.hex()", "r['stack152_after']==stack.hex()", 1),
    ]
    return A.rewrite(O, R, 'require_case', edits,
        dict(TOP=TOP, DEST=DEST, STOP=STOP, COOKIES=H.COOKIES, IP=H.IP, STORES=O.STORES,
             SDK=SDK, ID=ID, ARC=ARC, FAST_VALUE=1, EXPECTED_HOOKS=143, EXPECTED_PC_COUNT=128), 'narc_reader')


require_native, NATIVE_RECIPE = native_binding()
require_init_native, INIT_RECIPE = A.rewrite(O, O, 'require_init', [
    ("len(p['models']) == 14", "len(p['models']) == 15", 1),
    ("p['models'][0]['name'] == 'FS_OpenFile'", "p['models'][0]['name'] == 'FS_ConvertPathToFileID'", 1),
    ('native Init has no modeled event; real R2 zero reaches Open',
     'native Init has no modeled event; real R2 zero reaches native Open and lower Convert', 1)], {}, 'fs_init_caller')

# Qualified on Unicorn2.1.4 CPU17: all three false-NE locations deliver hooks,
# while their architectural effects remain suppressed. No counter is accepted
# if this instrumentation policy has not been qualified (None).
FALSE_CONDITIONAL_HOOKS = True


def expected_open(r, variant='current'):
    need(variant in ('current', 'fs_open_false') and type(r['open_fast_value']) is int and
         r['open_fast_value'] in (1, 2), 'finite Open source prediction')
    if variant != 'current':
        need(FALSE_CONDITIONAL_HOOKS is not None, 'qualify conditional-false hooks first')
        import unicorn
        need(unicorn.__version__ == '2.1.4' and r['pp_reader']['cpu_model'] == 17,
             'qualified conditional-false runtime identity')
    clobber = r['pp_clobber']; need(type(clobber) is bool, 'finite lower-model volatile policy')
    regs = [FILE, 0x210F198, 0, 0, 0x210F198, 310, H.MON, 0] + list(H.N.COOKIES[4:]) + [0, TOP - 136, 0x2007353, 0x1F]
    entry, flow, calls = list(regs), [], []

    def lower(pc, result):
        before = list(regs)
        if clobber:
            for i in (1, 2, 3, 12): regs[i] = 0xA5000000 + i
            regs[15] = 0xA000001F
        regs[0] = result
        calls.append(dict(pc=hex(pc), entry=before, returned=list(regs)))

    for pc in range(ENTRY, END, 4):
        if variant == 'current' and pc >= 0x20D82B4: break
        if variant == 'fs_open_false' and pc in (0x20D82A8, 0x20D82AC, 0x20D82B0) and not FALSE_CONDITIONAL_HOOKS: continue
        flow.append(dict(pc=hex(pc), regs=list(regs)))
        if pc == ENTRY: regs[13] -= 8
        elif pc == 0x20D827C: regs[13] -= 8
        elif pc == 0x20D8280: regs[4] = FILE
        elif pc == 0x20D8284: regs[0] = ID
        elif pc == 0x20D8288:
            regs[14] = 0x20D828C; lower(CONVERT, 1)
        elif pc == 0x20D828C: regs[15] = 0x2000001F
        elif pc == 0x20D8294: regs[1] = ID
        elif pc == 0x20D8298: regs[0] = FILE
        elif pc == 0x20D829C: regs[1:3] = [ARC, 140]
        elif pc == 0x20D82A0:
            regs[14] = 0x20D82A4; lower(FAST, r['open_fast_value'])
        elif pc == 0x20D82A4:
            if variant == 'fs_open_false': regs[0] = 0
            regs[15] = 0x6000001F if variant == 'fs_open_false' else 0x2000001F
        elif pc == 0x20D82A8 and variant == 'current': regs[13] += 8
        elif pc == 0x20D82AC and variant == 'current': regs[0] = 1
        elif pc == 0x20D82B0 and variant == 'current':
            regs[4] = 0x210F198; regs[13] += 8; regs[15] |= 32
        elif pc == 0x20D82B4: regs[0] = 0
        elif pc == 0x20D82B8: regs[13] += 8
        elif pc == 0x20D82BC:
            regs[4] = 0x210F198; regs[13] += 8; regs[15] |= 32
    return dict(entry=entry, flow=flow, calls=calls, returned=regs)


def require_open(r, data, variant='current'):
    out, p = r['fs_open'], r['pp_reader']; expected = expected_open(r, variant)
    require_init_native(r)
    need(out['entry'] == expected['entry'] and out['returned'] == expected['returned'] and
         out['flow'] == expected['flow'], 'Open complete source-derived native ABI/condition/return flow')
    before152 = bytes.fromhex(p['stack152_before'])
    need(len(before152) == 152 and before152[16:].hex() == p['stack_frame_before'] and
         p['stack_guard_range'] == [TOP - 208, ID] and len(bytes.fromhex(p['stack_guard_before'])) == 56 and
         p['stack_guard_before'] == p['stack_guard_after'], 'Open extended frame/guard exact preimage binding')
    after152 = bytes.fromhex(p['stack152_after'])
    need(len(after152) == 152 and after152[16:].hex() == p['stack_frame_hex'],
         'Open extended and inherited frame postimages agree')
    before = before152[:16] + bytes.fromhex(r['fs_init']['frame_after'])
    after = struct.pack('<II', ARC, 140) + struct.pack('<II', 0x210F198, 0x2007353) + before[16:]
    need(out['before16'] == before[:16].hex() and out['after16'] == after[:16].hex() and
         out['frame_before'] == before.hex() and out['frame_after'] == after.hex(),
         'Open exact by-value ID8 and saved pair8; original frame136 unchanged')
    stores = [dict(pc=hex(ENTRY), address=TOP - 144 + 4*i, bytes=4,
                   before=before[8+4*i:12+4*i].hex(), value=value)
              for i, value in enumerate((0x210F198, 0x2007353))]
    need(out['stores'] == (stores if r['observe'] else []), 'Open two actual native PUSH word stores')
    blob = struct.pack('<II', ARC, 140)
    need(out['id_reads'] == [dict(pc='0x20d829c', address=ID+offset, bytes=4, hex=blob[offset:offset+4].hex())
                              for offset in (0, 4)], 'Open two actual native LDM reads of delivered FileID')
    models = p['models'][:2]
    need(len(models) == 2 and [e['name'] for e in models] == ['FS_ConvertPathToFileID', 'FS_OpenFileFast'] and
         all(e['entry'] == want['entry'] and e['returned'] == want['returned'] and e['pc'] == want['pc']
             for e, want in zip(models, expected['calls'])), 'Open lower ARM model full16 entry/return and by-value call ABI')
    need(models[0]['before_hex'] == before[:8].hex() and models[0]['delivered_hex'] == blob.hex() and
         models[0]['destination'] == ID and models[0]['delivered_sha256'] == sha(blob),
         'Open modeled path result exact eight-byte write provenance')
    empty = dict(initialized=True, file=FILE, open=False, cursor=None, path=None, archive_sha256=None)
    opened = dict(initialized=True, file=FILE, open=True, cursor=0, path='a/0/1/1',
                  archive_sha256=data['pp_reader']['11']['oracle']['archive_sha256'])
    need(out['ledger_before'] == empty and out['ledger_after'] == opened and
         all(e['name'] not in ('FS_InitFile', 'FS_OpenFile') for e in p['models']),
         'Open real wrapper with two lower models, no fake high-level events')
    shadows = []
    if variant == 'fs_open_false':
        pre = next(e['regs'] for e in expected['flow'] if e['pc'] == '0x20d82a4'); post = list(pre); post[0] = 0
        shadows = [dict(pc='0x20d82a4', before=pre, after=post,
            reason='R0 only after valid modeled OpenFast; native wrapper false path, archive remains open')]
    need(out['shadows'] == shadows, 'Open exact finite R0 shadow after lower success')
    return True


def require_case(r, data, q):
    need(r['variant'] == 'current' and r['pp_shadows'] == [] and 'pp_expected_slot0' not in data,
         'positive Open context has no result shadow')
    require_open(r, data)
    H.require_pp_context(r, data)
    code = {**q['header_code'], **q['fs_init_code'],
            **{pc: value for pc, value in q['fs_open_code'].items() if pc < 0x20D82B4}}
    native = A.clone(require_native, dict(FAST_VALUE=r['open_fast_value']))
    native(r['pp_reader'], data['pp_reader'], code, T.expected(data['constructor'], r['plus'])[0]['ot_draws'][-1])
    H.require_earlier(r, data, q)
    return True


def require_off_pair(on, off, data):
    parent = H.require_off_pair(on, off, data)
    require_open(on, data); require_open(off, data)
    need(on['variant'] == off['variant'] == 'current' and on['open_fast_value'] == off['open_fast_value'] == 1 and
         on['observe'] is True and off['observe'] is False and off['fs_open']['stores'] == [] and
         {k:v for k,v in on['fs_open'].items() if k!='stores'} ==
         {k:v for k,v in off['fs_open'].items() if k!='stores'} and
         {k:v for k,v in on['fs_init'].items() if k!='stores'} ==
         {k:v for k,v in off['fs_init'].items() if k!='stores'},
         'Open OFF retains Init/PUSH/FileID/ARM calls/entire152 and guard56; only native store logs differ')
    return dict(neutral=True, parent=parent, scope='Native Init28B/PUSH8B and modeled FileID8B equal OFF/ON; '
        'complete152-byte frame and56-byte actual guard protected; inherited heap1124B only, no added mask')


def counter_code(q):
    need(type(FALSE_CONDITIONAL_HOOKS) is bool, 'qualify conditional-false hooks first')
    excluded = () if FALSE_CONDITIONAL_HOOKS else (0x20D82A8,0x20D82AC,0x20D82B0)
    return {**q['header_code'], **q['fs_init_code'],
            **{pc:value for pc,value in q['fs_open_code'].items() if pc not in excluded}}


def require_counter(counter, normal, data, q):
    require_case(normal, data, q); r = counter['result']
    need(counter['variant'] == r['variant'] == 'fs_open_false' and r['plus'] == normal['plus'] == 1 and
         r['seed'] == normal['seed'] == 0x12345678 and r['poison'] == normal['poison'] == 0xC7 and
         r['observe'] is True and r['pp_clobber'] is False and r['open_fast_value'] == normal['open_fast_value'] == 1,
         'Open counter finite original fixture domain')
    require_open(r, data, 'fs_open_false')
    need(r['pp_binding'] == normal['pp_binding'] and
         all(r['fs_open'][k] == normal['fs_open'][k] for k in ('entry','before16','frame_before','ledger_before')) and
         all(r['pp_reader'][k] == normal['pp_reader'][k] for k in
             ('stack152_before','stack_guard_before','destination_before','upper_after','models','native_writes',
              'stack152_after','stack_frame_hex','ram_sha256','destination_hex')),
         'Open counter complete shared prestate and same transport/stack/memory after status-only shadow')
    code = counter_code(q); delta = 3 if FALSE_CONDITIONAL_HOOKS else 0
    native = A.clone(require_native, dict(EXPECTED_HOOKS=143+delta, EXPECTED_PC_COUNT=128+delta))
    native(r['pp_reader'], data['pp_reader'], code, T.expected(data['constructor'],1)[0]['ot_draws'][-1])
    H.require_pp_context(r,data)
    replay = copy.deepcopy(r); replay['variant'] = 'current'; H.require_earlier(replay,data,q)
    need(r['instructions'] == normal['instructions']+delta and
         all(r[k] == normal[k] for k in ('mon_hex','prefix','seed_after','pp_flow','pp_stores','pp_checkpoint',
                                        'names','raw_ram_sha256','functional_ram_sha256')),
         'Open false status ignored by actual caller; same complete output and RAM with qualified hook delta')
    disguised = copy.deepcopy(r); disguised['variant'] = 'current'; disguised['fs_open']['shadows'] = []
    try: require_case(disguised,data,q)
    except ValueError as error:
        need(counter['tag_disguised'] is True and str(error) == counter['rejection'] ==
             'Open complete source-derived native ABI/condition/return flow', 'Open counter specific positive rejection')
    else: raise ValueError('Open false-status counter accepted')
    return True


def counter_record(r,data,q):
    disguised = copy.deepcopy(r); disguised['variant'] = 'current'; disguised['fs_open']['shadows'] = []
    try: require_case(disguised,data,q)
    except ValueError as error:
        return dict(variant=r['variant'],result=r,rejection=str(error),tag_disguised=True)
    raise ValueError('Open counter accepted')


def source_identities():
    result = O.source_identities()
    for path in (__file__, A.__file__): result[str(Path(path).resolve().relative_to(P.SOURCE))] = sha(Path(path).read_bytes())
    return result


def analyze(rom, language, objects, strategy_object, readback_only=False):
    import mmap, unicorn
    R.W.require_host_budget(); sources = source_identities()
    model = P.G.S.SHARED.read_current(rom, language)
    with rom.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
        q, proof = qualify(model,raw,language,objects,strategy_object)
        result = dict(schema='trainer31-native-fs-open-v1',language=language,input=model['record'],
            source_sha256=sources,proof=proof,recipes=RECIPES+[NATIVE_RECIPE,INIT_RECIPE],cpu_executed=False,
            conditional_policy=dict(unicorn_version=unicorn.__version__,cpu_model=17,
                false_NE_hooks=FALSE_CONDITIONAL_HOOKS,scope='code-hook delivery; false ARM effects remain suppressed'))
        if not readback_only:
            data = O.resources(model,raw,language)
            positives, guards, controls, off, counters = [], [], [], [], []
            for plus in (0,1):
                for seed in (0x12345678,0x12345679):
                    r = run_case(model,raw,language,q,data,plus,seed)
                    require_case(r,data,q); positives.append(r)
                    print(language,'native Open caller',plus,hex(seed),'verified',flush=True)
                r = run_case(model,raw,language,q,data,plus,0x12345678,observe=False)
                off.append(dict(result=r,proof=require_off_pair(positives[-2],r,data)))
            normal = next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
            r = run_case(model,raw,language,q,data,1,0x12345678,poison=0x39)
            require_case(r,data,q); need(r['mon_hex']==normal['mon_hex'],'Open alternate preimage fill changes party'); guards.append(r)
            for kwargs in (dict(pp_clobber=True),dict(open_fast_value=2)):
                r = run_case(model,raw,language,q,data,1,0x12345678,**kwargs)
                require_case(r,data,q)
                need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and
                     r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and
                     r['pp_reader']['ram_sha256']==normal['pp_reader']['ram_sha256'],
                     'Open lower volatile/noncanonical truthy policy preserves output and phase RAM')
                controls.append(r)
            r = run_case(model,raw,language,q,data,1,0x12345678,variant='fs_open_false')
            counter = counter_record(r,data,q); require_counter(counter,normal,data,q); counters.append(counter)
            result.update(cpu_executed=True,positives=positives,guards=guards,volatile_controls=controls,
                observer_off=off,counters=counters,resources=dict(pp=data['pp_reader']['11']['oracle']),
                limits=['Initialized trainer31 caller and selected custom PP310 Open only',
                        'Native Init and Open wrapper; ConvertPath/OpenFast plus Seek/Read/Close are explicit models',
                        'Opaque ARC token is not native FSArchive state; no invented FSFile fields',
                        'Counter is R0 shadow after valid modeled open, not native SDK/card failure',
                        'Exact152-byte frame/56-byte preimage guard; inherited heap1124B OFF projection only',
                        'Recovered assembly bytes do not reconstruct original SDK compiler provenance',
                        'No natural encounter/full battle/UI/SAVE/cold/hardware or performance claim'])
        need(source_identities()==sources,'Open sources changed during campaign'); R.W.require_host_budget()
    return result


def main():
    import argparse,json,gzip
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('rom','objects','strategy-object','json'): parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    parser.add_argument('--readback-only',action='store_true')
    args = parser.parse_args()
    try:
        need(not args.json.exists() and not args.json.is_symlink() and P.SOURCE not in args.json.resolve().parents,
             'fresh private output outside source required')
        result = analyze(args.rom,args.language,args.objects,args.strategy_object,args.readback_only)
        payload = json.dumps(result,separators=(',',':')).encode(); need(len(payload)<=32*1024**2,'Open expanded report budget')
        blob = gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload
        need(len(blob)<=8*1024**2,'Open stored report budget')
        args.json.parent.mkdir(parents=True,exist_ok=True)
        with args.json.open('xb')as f:f.write(blob)
    except ValueError as error: parser.exit(2,str(error)+'\n')
    print(args.language,'Open readback verified' if args.readback_only else 'native Open caller and explicit lower models verified')


if __name__=='__main__':main()
