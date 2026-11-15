#!/usr/bin/env python3
"""Compose the installed ARM FS_InitFile into the selected native PP caller.

Only this leaf becomes native. Open/Seek/Read/Close remain explicit host models.
Reports and extracted data must stay outside source.
"""
from pathlib import Path
import copy, gzip, json, mmap, struct, types
import importlib.util


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load('fs_init_pp_parent', Path(__file__).with_name('attribuisci_pp_chiamante.py'))
A = load('fs_init_profile', Path(__file__).parents[1] / 'test/fs_init_bench.py')
A.bind(H)
R, P, B, T, Q, V, X, J, G = H.R, H.P, H.B, H.T, H.Q, H.V, H.X, H.J, H.G
need, sha = H.need, H.sha
TOP, DEST, STOP = H.TOP, H.DEST, H.STOP
ENTRY, RETURN, FILE = 0x20D7F98, 0x200734A, TOP - 112
INIT_SHA = '131f15b7db06da746cb03744ffda8f5453b1c6c2fbdf8f0dacab41326e10421f'
STORES = ((0x20D7F9C, 0, 0), (0x20D7FA0, 4, 0), (0x20D7FA4, 28, 0),
          (0x20D7FA8, 24, 0), (0x20D7FAC, 8, 0), (0x20D7FB4, 16, 14),
          (0x20D7FB8, 12, 0))
from unicorn.arm_const import UC_ARM_REG_PC


def qualify(model, raw, *args):
    q, proof = H.qualify(model, raw, *args)
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    view = P.G.S.SHARED.gifts_audit.Arm9View(raw)
    blob = view.read(ENTRY, 40)
    need(sha(blob) == INIT_SHA and blob == P.G.piece(model['segments'], ENTRY, 40),
         'FS Init independent raw/decoded body identity')
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(blob, ENTRY))
    need(len(decoded) == 10 and [i.address for i in decoded] == list(range(ENTRY, ENTRY + 40, 4))
         and all(i.size == 4 for i in decoded) and decoded[-1].mnemonic == 'bx'
         and decoded[-1].op_str == 'lr', 'FS Init exact ARM boundaries/return')
    q['fs_init_code'] = {i.address: (4, False) for i in decoded}
    proof['native_fs_init'] = dict(ram=hex(ENTRY), bytes=40, sha256=sha(blob),
        rom_offset=hex(view.offset(ENTRY, 40)), starts=10, fs_file_bytes=72,
        assigned_bytes=28, preserved_bytes=44, source_counterpart='NitroSDK FS_file.c::FS_InitFile',
        original_compiler_reconstructed=False)
    return q, proof


def bindings():
    native_edits = A.edits(H, 2) + [
        ("r['instructions']==118", "r['instructions']==127", 1),
        ("len(code)==103", "len(code)==113", 1),
        (" ('FS_InitFile',0x200734B,[0,310],[path,310,c6,c7],None),\n", '', 1),
        ("[path,volatile[1] if clobber else 310]", "[path,0]", 1),
        ("len(r['models'])==15", "len(r['models'])==14", 1),
        ("result=file if index==0 else read[2] if read else 1", "result=read[2] if read else 1", 1),
        (",(0x20073EE,20,4,size)", '', 1),
        ("need(len(expected)==17", "\n for pc,offset,value in STORES:store(pc,file+offset,4,value)\n store(0x20073EE,local+20,4,size)\n need(len(expected)==17+len(STORES)", 1),
    ]
    native, p1 = A.rewrite(H, R, 'require_case', native_edits,
        dict(TOP=TOP, DEST=DEST, STOP=STOP, COOKIES=H.COOKIES, IP=H.IP, STORES=STORES), 'narc_reader')
    run, p2 = A.rewrite(H, V, 'run_case', A.edits(H, 3) + [
        ('return dict(pp_reader=', 'return dict(fs_init=driver.fs_init_result,pp_reader=', 1)],
        dict(Driver=Driver, A=H.A, NAME_ARENA=X.NAME_ARENA, NAME_END=X.NAME_END), 'message_caller')
    return native, run, [p1, p2]


class InitObserver:
    """Borrow the same CPU; record native effects, never initialize guest fields."""
    def __init__(self, driver, reader):
        self.driver, self.reader = driver, reader
        self.result = dict(entry=None, returned=None, before=None, after=None,
                           frame_before=None, frame_after=None, flow=[], stores=[], shadows=[],
                           ledger_before=None, ledger_after=None)
        self.active = False
        reader.code = {**reader.code, **driver.qualified['fs_init_code']}
        sdk = {a: name for a, name in R.SDK.items() if a != ENTRY}
        self.base_step = types.MethodType(A.clone(reader.step.__func__, dict(SDK=sdk)), reader)
        reader.service = types.MethodType(A.clone(reader.service.__func__, dict(SDK=sdk)), reader)
        self.base_write = reader.write
        reader.step, reader.write = self.step, self.write

    def step(self, u, pc, n, user):
        r, out = self.reader, self.result
        if pc == ENTRY:
            need(out['entry'] is None and not r.initialized and r.file is None,
                 'single native FS Init before opaque handle exists')
            out.update(entry=r.regs(), before=r.read_bytes(FILE, 72).hex(),
                       frame_before=r.read_bytes(TOP - 136, 136).hex(),
                       ledger_before=dict(initialized=r.initialized, file=r.file, open=r.open))
            self.active = True
        if pc == RETURN:
            need(self.active and out['returned'] is None and not r.initialized and r.file is None,
                 'native FS Init actual return precedes host handle bookkeeping')
            out.update(returned=r.regs(), after=r.read_bytes(FILE, 72).hex(),
                       frame_after=r.read_bytes(TOP - 136, 136).hex())
            # Remaining opaque FS models need a host handle; no guest write or fake Init event.
            r.initialized, r.file = True, FILE
            out['ledger_after'] = dict(initialized=True, file=FILE, open=False)
            self.active = False
        if self.active:
            out['flow'].append(dict(pc=hex(pc), regs=r.regs()))
        self.base_step(u, pc, n, user)
        if self.active and pc == 0x20D7FB4 and self.driver.fs_variant != 'current':
            before = r.regs()
            if self.driver.fs_variant == 'fs_skip_command':
                u.reg_write(UC_ARM_REG_PC, 0x20D7FB8)
            else:
                u.reg_write(B.R[1], 0)
            out['shadows'].append(dict(pc=hex(pc), before=before, after=r.regs(),
                next_pc=hex(u.reg_read(UC_ARM_REG_PC)), variant=self.driver.fs_variant))

    def write(self, u, access, address, n, value, user):
        if self.active and self.reader.observe:
            self.result['stores'].append(dict(pc=hex(u.reg_read(UC_ARM_REG_PC)), address=address,
                bytes=n, before=self.reader.read_bytes(address, n).hex(), value=value,
                regs=self.reader.regs()))
        self.base_write(u, access, address, n, value, user)


class Driver(H.Driver):
    def __init__(self, *args, variant='current', **kwargs):
        need(variant in ('current', 'fs_skip_command', 'fs_command_zero'), 'finite FS Init controls')
        super().__init__(*args, variant='current', **kwargs)
        self.fs_variant, self.fs_init_result = variant, None

    def start_pp(self):
        super().start_pp()
        regs, before = self.regs(), self.read_bytes(0x2000000, 0x400000)
        self.fs_observer = InitObserver(self, self.pp_reader)
        self.fs_init_result = self.fs_observer.result
        need(regs == self.regs() and before == self.read_bytes(0x2000000, 0x400000),
             'FS Init observer attachment changes neither CPU nor RAM')


require_native, run_case, RECIPES = bindings()


def require_init(r, variant='current'):
    out, p = r['fs_init'], r['pp_reader']
    need(variant in ('current', 'fs_skip_command', 'fs_command_zero'), 'finite FS Init oracle domain')
    entry = [FILE, 0, 310, 0, 0x210F198, 310, H.MON, 0] + list(H.N.COOKIES[4:]) + [0, TOP - 136, 0x200734B, 0x1F]
    returned = list(entry); returned[1:3] = [0 if variant == 'fs_command_zero' else 14, 0]; returned[15] = 0x3F
    need(out['entry'] == entry and out['returned'] == returned and
         out['ledger_before'] == dict(initialized=False, file=None, open=False) and
         out['ledger_after'] == dict(initialized=True, file=FILE, open=False),
         'FS Init actual full entry/return ABI and host ledger ordering')
    before = bytes.fromhex(out['before']); frame = bytearray.fromhex(out['frame_before'])
    entry_frame = bytearray.fromhex(p['stack_frame_before'])
    need(len(entry_frame) == 136, 'FS Init original reader frame length')
    # Sixteen actual prefix stores precede Init: wrapper push/argument, parser
    # push and six metadata stores. Do not trust a self-consistent frame pair.
    struct.pack_into('<III', entry_frame, 124, 0x2007509, 5, STOP | 1)
    struct.pack_into('<I', entry_frame, 120, 0)
    struct.pack_into('<6I', entry_frame, 96, 0, 44, 0, H.MON, 0, 0x200751B)
    for offset, width, value in ((0, 4, DEST), (20, 4, 0), (16, 4, 0),
                                  (12, 4, 0), (8, 2, 0), (4, 4, 0)):
        entry_frame[offset:offset + width] = value.to_bytes(width, 'little')
    need(len(before) == 72 and len(frame) == 136 and before == frame[24:96] and
         before == entry_frame[24:96] and frame == entry_frame, 'FS Init actual borrowed file and16-store prefix preimage')
    expected = bytearray(before); stores = []; flow = []; regs = list(entry)
    bypc = {pc: (offset, value) for pc, offset, value in STORES}
    for pc in range(ENTRY, ENTRY + 40, 4):
        flow.append(dict(pc=hex(pc), regs=list(regs)))
        if pc == ENTRY: regs[2] = 0
        if pc == 0x20D7FB0: regs[1] = 14
        if pc == 0x20D7FB4 and variant == 'fs_command_zero': regs[1] = 0
        if pc in bypc and not (pc == 0x20D7FB4 and variant == 'fs_skip_command'):
            offset, value = bypc[pc]
            if pc == 0x20D7FB4 and variant == 'fs_command_zero': value = 0
            stores.append(dict(pc=hex(pc), address=FILE + offset, bytes=4,
                before=bytes(expected[offset:offset + 4]).hex(), value=value, regs=list(regs)))
            struct.pack_into('<I', expected, offset, value)
    frame[24:96] = expected
    need(out['after'] == expected.hex() and out['frame_after'] == frame.hex(),
         'FS Init exact seven assigned words and all44 preserved bytes; outside file unchanged')
    need(out['flow'] == flow and out['stores'] == (stores if r['observe'] else []),
         'FS Init entire native instruction/register/store transcript')
    shadows = []
    if variant != 'current':
        before_regs = next(e['regs'] for e in flow if e['pc'] == '0x20d7fb4')
        after_regs = list(before_regs)
        if variant == 'fs_command_zero': after_regs[1] = 0
        shadows = [dict(pc='0x20d7fb4', before=before_regs, after=after_regs,
            next_pc='0x20d7fb8' if variant == 'fs_skip_command' else '0x20d7fb4', variant=variant)]
    need(out['shadows'] == shadows and len(p['models']) == 14 and
         all(e['name'] != 'FS_InitFile' for e in p['models']) and
         p['models'][0]['name'] == 'FS_OpenFile' and p['models'][0]['args'][2] == 0,
         'native Init has no modeled event; real R2 zero reaches Open')
    return True


def require_case(r, data, q):
    need(r['variant'] == 'current' and r['pp_shadows'] == [] and 'pp_expected_slot0' not in data,
         'positive FS Init domain without value shadow')
    require_init(r)
    H.require_pp_context(r, data)
    code = {**q['header_code'], **q['fs_init_code']}
    require_native(r['pp_reader'], data['pp_reader'], code,
                   T.expected(data['constructor'], r['plus'])[0]['ot_draws'][-1])
    H.require_earlier(r, data, q)
    return True


def require_off_pair(on, off, data):
    parent = H.require_off_pair(on, off, data)
    require_init(on); require_init(off)
    a, b = on['fs_init'], off['fs_init']
    need(on['variant'] == off['variant'] == 'current' and on['observe'] is True and off['observe'] is False
         and b['stores'] == [] and {k: v for k, v in a.items() if k != 'stores'} ==
         {k: v for k, v in b.items() if k != 'stores'},
         'FS Init OFF keeps all native file/ABI/prefix/guard effects; only store log differs')
    return dict(neutral=True, parent=parent, scope='Native Init28B writes and44B preserved bytes '
        'equal OFF/ON; no file/stack projection added; inherited exact1124B heap projection only')


def require_counter(counter, normal, data, q):
    require_case(normal, data, q)
    r, variant = counter['result'], counter['variant']
    need(variant in ('fs_skip_command', 'fs_command_zero') and r['variant'] == variant and
         r['plus'] == normal['plus'] == 1 and r['seed'] == normal['seed'] == 0x12345678 and
         r['poison'] == normal['poison'] == 0xC7 and r['observe'] is True and r['pp_clobber'] is False,
         'FS Init counter finite actual fixture')
    require_init(r, variant)
    need(r['pp_binding'] == normal['pp_binding'] and all(r['fs_init'][key] == normal['fs_init'][key]
         for key in ('entry', 'before', 'frame_before', 'ledger_before')) and
         all(r['pp_reader'][key] == normal['pp_reader'][key] for key in
             ('stack_frame_before', 'stack_guard_before', 'stack_guard_after', 'destination_before', 'upper_after')),
         'FS Init counter identical full source-bound prestate/guard/borrowed output')
    stores = tuple(e for e in STORES if not (variant == 'fs_skip_command' and e[0] == 0x20D7FB4))
    if variant == 'fs_command_zero': stores = tuple((pc, o, 0 if pc == 0x20D7FB4 else v) for pc, o, v in stores)
    # Same complete native reader oracle; only the seven source field assignments
    # change according to the separately validated PC/register shadow above.
    native = A.clone(require_native, dict(STORES=stores))
    native(r['pp_reader'], data['pp_reader'], {**q['header_code'], **q['fs_init_code']},
           T.expected(data['constructor'], 1)[0]['ot_draws'][-1])
    H.require_pp_context(r, data)
    replay = copy.deepcopy(r); replay['variant'] = 'current'
    H.require_earlier(replay, data, q)
    need(r['instructions'] == normal['instructions'] and r['mon_hex'] == normal['mon_hex'] and
         r['prefix'] == normal['prefix'] and r['seed_after'] == normal['seed_after'] and
         r['pp_flow'] == normal['pp_flow'] and r['pp_stores'] == normal['pp_stores'] and
         r['pp_checkpoint'] == normal['pp_checkpoint'],
         'FS Init counter same PP and full party despite omitted/invalid initialization')
    disguised = copy.deepcopy(r); disguised['variant'] = 'current'; disguised['fs_init']['shadows'] = []
    try:
        require_case(disguised, data, q)
    except ValueError as error:
        expected = 'FS Init exact seven assigned words and all44 preserved bytes; outside file unchanged' if variant == 'fs_skip_command' else 'FS Init actual full entry/return ABI and host ledger ordering'
        need(str(error) == counter['rejection'] == expected and counter['tag_disguised'] is True,
             'FS Init counter positive-oracle rejection identity')
    else:
        raise ValueError('FS Init counter accepted with identical PP payload')
    return True


def counter_record(r, data, q):
    disguised = copy.deepcopy(r); disguised['variant'] = 'current'; disguised['fs_init']['shadows'] = []
    try:
        require_case(disguised, data, q)
    except ValueError as error:
        return dict(variant=r['variant'], result=r, rejection=str(error), tag_disguised=True)
    raise ValueError('FS Init counter accepted')


def resources(model, raw, language):
    return dict(preparation=Q.resources(raw), constructor=T.resources(model, raw, language, trainer=31),
        message=V.M.resources(raw), names=X.W.resources(raw), header=R.resources(raw),
        personal_reader=J.resources(raw), growth_reader=G.resources(raw), growth_counter=G.resources(raw, 2),
        pp_reader=H.resources(raw))


def source_identities():
    result = H.source_identities()
    for path in (__file__, A.__file__):
        result[str(Path(path).resolve().relative_to(P.SOURCE))] = sha(Path(path).read_bytes())
    return result


def analyze(rom, language, objects, strategy_object, readback_only=False):
    R.W.require_host_budget(); sources = source_identities()
    model = P.G.S.SHARED.read_current(rom, language)
    with rom.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as raw:
        q, proof = qualify(model, raw, language, objects, strategy_object)
        result = dict(schema='trainer31-native-fs-init-v1', language=language, input=model['record'],
                      source_sha256=sources, proof=proof, recipes=RECIPES, cpu_executed=False)
        if not readback_only:
            data = resources(model, raw, language)
            positive, guards, controls, off, counters = [], [], [], [], []
            for plus in (0, 1):
                for seed in (0x12345678, 0x12345679):
                    r = run_case(model, raw, language, q, data, plus, seed)
                    require_case(r, data, q); positive.append(r)
                    print(language, 'native Init caller', plus, hex(seed), 'verified', flush=True)
                r = run_case(model, raw, language, q, data, plus, 0x12345678, observe=False)
                off.append(dict(result=r, proof=require_off_pair(positive[-2], r, data)))
            normal = next(r for r in positive if r['plus'] == 1 and r['seed'] == 0x12345678)
            r = run_case(model, raw, language, q, data, 1, 0x12345678, poison=0x39)
            require_case(r, data, q); need(r['mon_hex'] == normal['mon_hex'], 'Init guard fill changes output'); guards.append(r)
            r = run_case(model, raw, language, q, data, 1, 0x12345678, pp_clobber=True)
            require_case(r, data, q)
            need(r['mon_hex'] == normal['mon_hex'] and r['seed_after'] == normal['seed_after'] and
                 r['functional_ram_sha256'] == normal['functional_ram_sha256'] and
                 r['pp_reader']['ram_sha256'] == normal['pp_reader']['ram_sha256'],
                 'Init remaining four FS volatile clobber policy preserves game and phase RAM')
            controls.append(r)
            for variant in ('fs_skip_command', 'fs_command_zero'):
                r = run_case(model, raw, language, q, data, 1, 0x12345678, variant=variant)
                counter = counter_record(r, data, q); require_counter(counter, normal, data, q); counters.append(counter)
            result.update(cpu_executed=True, positives=positive, guards=guards, volatile_controls=controls,
                observer_off=off, counters=counters,
                resources=dict(pp=data['pp_reader']['11']['oracle']),
                limits=['Initialized trainer31 caller; only selected first custom PP Init becomes native',
                        'Four opaque FS services and heap remain models; no native Open/card/thread/error-policy proof',
                        'Seven actual guest stores; void R0 residue and volatile R1/R2 are not API status',
                        'OFF retains all native file writes and uses only inherited exact1124B heap projection',
                        'Recovered recipe can match bytes; original SDK compiler invocation remains unavailable',
                        'No natural encounter/full battle/UI/SAVE/cold/hardware or timing claim'])
        need(source_identities() == sources, 'FS Init source drift during run')
        R.W.require_host_budget()
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('rom', 'objects', 'strategy-object', 'json'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--language', choices=('EN', 'IT'), required=True)
    parser.add_argument('--readback-only', action='store_true')
    args = parser.parse_args()
    try:
        need(not args.json.exists() and not args.json.is_symlink() and P.SOURCE not in args.json.resolve().parents,
             'fresh private output outside source required')
        result = analyze(args.rom, args.language, args.objects, args.strategy_object, args.readback_only)
        payload = json.dumps(result, separators=(',', ':')).encode()
        need(len(payload) <= 32 * 1024**2, 'FS Init report budget')
        blob = gzip.compress(payload, mtime=0) if args.json.suffix == '.gz' else payload
        need(len(blob) <= 8 * 1024**2, 'FS Init stored report budget')
        args.json.parent.mkdir(parents=True, exist_ok=True)
        with args.json.open('xb') as f: f.write(blob)
    except ValueError as error:
        parser.exit(2, str(error) + '\n')
    print(args.language, 'FS Init readback verified' if args.readback_only else 'native FS Init caller verified')


if __name__ == '__main__': main()
