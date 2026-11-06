"""Unicorn bench for the portable box on the REAL V4 ARM9 bytes.

Evidence level: ARM instructions of the installed hooks, the compiled payload
and the native code that the hooks wrap (callback body, PartyMenu_LaunchApp_Unk1,
the small TaskManager getters, Party_GetCount) run in Unicorn. Large native
services (heap, overlay launcher, text printer, sound, CreateArgs, MainNormal,
Bill notification, field overlay load) are replaced by logged Python models.
The world (FieldSystem, start-menu owner, PartyMenu, args) is synthetic and its
offsets are the ones pinned in data/portable-native-abi.json. This is CPU and
ABI coverage, not Android gameplay.

TEST_BASE below is an emulator placement. The installer tests run under a DECLARED test reserve policy
(`declared_reserve`): slot name/start/size copied from reserve-map.json, own version and digest, refused by
the real policy. Nothing here is a product assignment.
"""
import hashlib
import json
import os
import struct
import sys
from pathlib import Path
from unittest import mock

SOURCE = Path(__file__).resolve().parents[3]
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE)  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,  # noqa: E402
                               UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                               UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

from sgp131 import portable  # noqa: E402
from sgp131.baseline import INPUT_HASHES  # noqa: E402

REPOSITORY = SOURCE.parent
CANDIDATES = REPOSITORY / 'local' / 'experiments' / 'balance493-2026-10-28'
INPUTS = {
    'EN': (os.environ.get('SGP_PORTABLE_ROM_EN') or CANDIDATES / 'candidate-v4-EN.nds', portable.V4_SHA256['EN']),
    'IT': (os.environ.get('SGP_PORTABLE_ROM_IT') or CANDIDATES / 'candidate-v4-IT.nds', portable.V4_SHA256['IT']),
}
REQUIRE = 'SGP_PORTABLE_REQUIRE_INPUTS'

# --- declared TEST reserve policy ------------------------------------------------------------------------
TEST_POLICY_VERSION = 'TEST-ONLY-reserve-policy'
TEST_POLICY_SHA256 = hashlib.sha256(b'TEST-ONLY reserve policy: a declared test double, never the product map').hexdigest()
REAL_RESERVE_POLICY = portable._reserve_policy        # captured before any patch


def real_slot(name=portable.SLOT_NAME):
    """(start, bytes) of `name` in the real reserve-map.json (read only)."""
    policy = json.loads((SOURCE / 'sgp131/data/reserve-map.json').read_text())
    for entry in policy['subdivisions']:
        for part in entry['parts']:
            if part['name'] == name and part['kind'] == 'payload':
                return part['start'], part['bytes']
    raise AssertionError('reserve-map.json has no slot ' + name)


SLOT_START, SLOT_BYTES = real_slot()


def declared_policy():
    part = {'name': portable.SLOT_NAME, 'kind': 'payload', 'start': SLOT_START, 'bytes': SLOT_BYTES}
    return ({'version': TEST_POLICY_VERSION, 'conditional_parents': [],
             'subdivisions': [{'parent': 'test.declared-parent', 'parts': [part]}]}, TEST_POLICY_SHA256)


def declared_allocation(language, size=None, **override):
    """A reserve.allocate-shaped receipt under the declared test policy (fixture, not an assignment)."""
    size = SLOT_BYTES if size is None else size
    record = {'schema': 1, 'input_sha256': next(h for h, lang in INPUT_HASHES.items() if lang == language),
              'language': language, 'policy_version': TEST_POLICY_VERSION, 'policy_sha256': TEST_POLICY_SHA256,
              'audit_sha256': hashlib.sha256(b'test audit').hexdigest(), 'requested': {portable.SLOT_NAME: size},
              'assignments': [{'name': portable.SLOT_NAME, 'parent': 'test.declared-parent', 'start': SLOT_START,
                               'bytes': size, 'capacity': SLOT_BYTES}],
              'preservation': {}, 'address_reserved': True, 'installed': False, 'installation_authorized': False}
    record.update(override)
    return record


def declared_reserve():
    """Context manager: portable._reserve_policy is the declared test double."""
    return mock.patch.object(portable, '_reserve_policy', declared_policy)


def real_reserve():
    return mock.patch.object(portable, '_reserve_policy', REAL_RESERVE_POLICY)


def preimage_of(v4):
    """sha256 of the whole assigned slot in the V4 image: the independent expected preimage (I5), never taken from the
    stage input."""
    return hashlib.sha256(portable.read_ram(v4, portable.arm9_segments(v4), SLOT_START, SLOT_BYTES)).hexdigest()


def _measured_size():
    import tempfile
    with tempfile.TemporaryDirectory(prefix='portable-size-') as work:
        return portable.measure(work)['bytes']


PORTABLE_SIZE = _measured_size()

TEST_BASE = 0x023F0000          # emulator placement, NOT an assignment
STOP = 0x023F8000
STACK_TOP = 0x023FE000
CANARY = 0xA5A5A5A5
SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)

# synthetic world (main RAM, outside the compartment)
FIELD, AVATAR, TASK, OWNER = 0x02310000, 0x02310400, 0x02310800, 0x02311000
PARTY, SAVEDATA, PARTY_CONT = 0x02312000, 0x02390000, 0x02391000
DUMMY = 0x02392000
VARS_FLAGS = 0x02393000
HEAP_BASE, HEAP_END = 0x02320000, 0x02380000
SYS = 0x021D110C
PARTY_TEMPLATE, PC_TEMPLATE = 0x0210159C, 0x020FA414
NATIVE_CB = 0x0203CA9D

N = dict(get_field=0x0205064C, get_env=0x02050650, heap_alloc=0x0201AA8C, heap_free=0x0201AB0C,
         launch_app=0x0203DFB4, pc_launch=0x0203E868, unk1=0x0203E550, create_args=0x0203E4FC,
         sub_93070=0x02093070, load_field=0x020505C0, vars_get=0x020503D0, check_follower=0x02066644, main_normal=0x02079308, print_ex=0x0207DA64,
         add_printer=0x020200A8, copy_vram=0x0201D5C8, play_se=0x0200604C, memcpy=0x020E5AD8)
CB_LO, CB_HI = 0x0203CA9C, 0x0203CF0C

_ROMS = {}


def rom(test, language):
    """(bytes, segments) of a V4 input; skips (or fails when required) if absent."""
    path, digest = INPUTS[language]
    path = Path(path)
    if not path.is_file():
        reason = '%s V4 input not present: %s' % (language, path)
        if os.environ.get(REQUIRE) == '1':
            test.fail(reason)
        test.skipTest(reason)
    if language not in _ROMS:
        data = path.read_bytes()
        test.assertEqual(hashlib.sha256(data).hexdigest(), digest, language + ' input identity')
        segments = portable.arm9_segments(data)
        # keep only the ARM9 image bytes the bench maps, not the 150 MB cartridge
        mapped = [(ram, bytes(data[off:off + size])) for ram, off, size in segments]
        _ROMS[language] = (data, segments, mapped)
    return _ROMS[language]


_BUILD = {}


def build(test, language, activation=None):
    """Compile the payload at TEST_BASE once per (language, activation)."""
    key = (language, tuple(sorted((activation or {}).items())))
    if key not in _BUILD:
        import tempfile
        with tempfile.TemporaryDirectory(prefix='portable-bench-') as work:
            blob, symbols, receipt = portable.compile_native(work, TEST_BASE)
        config = portable._activation(activation, internal=True)
        payload = bytearray(blob)
        area = symbols['sgp_box_area'] - TEST_BASE
        for name, value in config.items():
            struct.pack_into('<I', payload, area + portable.STATE_BYTES + portable.CONFIG_OFFSETS[name], value)
        trampoline = TEST_BASE + ((len(blob) + 3) & ~3)
        payload += bytes(trampoline - TEST_BASE - len(blob))
        payload += portable.callback_trampoline(trampoline, symbols['sgp_box_party_return'])
        _BUILD[key] = (bytes(payload), symbols, trampoline, receipt)
    return _BUILD[key]


class World:
    def __init__(self, test, language, hooked=True, activation=None, installed=None):
        """`installed` = (patched ROM bytes, receipt): run the bytes portable.prepare wrote, with the
        receipt's own symbols and base, instead of the bench's TEST_BASE placement."""
        self.test, self.language, self.hooked = test, language, hooked
        self.base = TEST_BASE if installed is None else installed[1]['base']
        data, segments, mapped = rom(test, language)
        if installed is not None:
            patched = installed[0]
            mapped = [(ram, bytes(patched[off:off + size])) for ram, off, size in portable.arm9_segments(patched)]
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_map(0x01FF8000, 0x8000)
        uc.mem_map(0x027E0000, 0x20000)
        for ram, blob in mapped:
            if ram < 0x02400000 and ram + len(blob) <= 0x02400000 or ram in (0x01FF8000, 0x027E0000):
                uc.mem_write(ram, blob)
        self.events, self.writes, self.errors = [], [], []
        self.isolated = False
        self.heap_next, self.live, self.heap_log = HEAP_BASE, {}, []
        self.fail_alloc = []             # list of predicates (size, heap) -> bool, consumed in order
        self.main_normal_return = 1
        self.escort = 0
        self.child = None
        self.launches = []
        self.stubs, self.stub_hooks = {}, {}
        self.symbols = self.payload = None
        if installed is not None:
            receipt = installed[1]
            self.symbols, self.trampoline = receipt['symbols'], receipt['compartment']['trampoline']
            payload = bytes(uc.mem_read(self.base, receipt['compartment']['bytes']))
        elif hooked:
            payload, symbols, trampoline, _ = build(test, language, activation)
            uc.mem_write(TEST_BASE, payload)
            for site, patch in portable.hook_patches(symbols, trampoline).items():
                uc.mem_write(site, patch)
            self.symbols, self.trampoline = symbols, trampoline
        self._install_stubs()
        self.install_isolation()
        uc.hook_add(UC_HOOK_MEM_WRITE, self._on_write)
        self.hits = {}
        if hooked:
            area = self.symbols['sgp_box_area'] - self.base
            self._area_init = bytes(payload[area:area + 96])
            for name in portable.ENTRIES:
                if name != 'sgp_box_area':
                    address = self.symbols[name] & ~1
                    uc.hook_add(UC_HOOK_CODE, self._hit, name, address, address)
        self._world()

    def _hit(self, uc, address, size, name):
        self.hits[name] = self.hits.get(name, 0) + 1

    def reset(self):
        """Fresh synthetic session; ROM, hooks and payload stay installed."""
        self.events, self.writes, self.heap_log, self.launches, self.errors = [], [], [], [], []
        self.heap_next, self.live, self.fail_alloc, self.child = HEAP_BASE, {}, [], None
        self.main_normal_return, self.hits, self.isolated, self.escort = 1, {}, False, 0
        if self.hooked:
            self.uc.mem_write(self.area, self._area_init)
        self._world()

    # ---------------------------------------------------------------- memory
    def u32(self, a): return struct.unpack('<I', self.uc.mem_read(a, 4))[0]
    def u16(self, a): return struct.unpack('<H', self.uc.mem_read(a, 2))[0]
    def u8(self, a): return self.uc.mem_read(a, 1)[0]
    def w32(self, a, v): self.uc.mem_write(a, struct.pack('<I', v & 0xFFFFFFFF))
    def w16(self, a, v): self.uc.mem_write(a, struct.pack('<H', v & 0xFFFF))
    def w8(self, a, v): self.uc.mem_write(a, bytes([v & 0xFF]))

    @property
    def area(self): return self.symbols['sgp_box_area']

    def state(self, key): return self.u32(self.area + portable.STATE_OFFSETS[key])
    def set_state(self, key, v): self.w32(self.area + portable.STATE_OFFSETS[key], v)
    def cfg(self, key): return self.u32(self.area + portable.STATE_BYTES + portable.CONFIG_OFFSETS[key])
    def set_cfg(self, key, v): self.w32(self.area + portable.STATE_BYTES + portable.CONFIG_OFFSETS[key], v)

    def _in_compartment(self, a):
        return self.hooked and self.base <= a < self.base + 0x1000

    def _on_write(self, uc, access, address, size, value, user):
        if address >= STACK_TOP - 0x4000 or self._in_compartment(address):
            return
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    # ------------------------------------------------------------ synthetic world
    def _world(self):
        w = self
        w.uc.mem_write(HEAP_BASE, bytes(HEAP_END - HEAP_BASE))
        w.uc.mem_write(DUMMY, bytes(0x1000))
        w.uc.mem_write(FIELD, struct.pack('<I', DUMMY) * 0x100)   # every unmodelled pointer is readable
        w.w32(FIELD + 0xC, SAVEDATA)
        w.w32(FIELD + 0x10, TASK)          # taskman: the live start-menu task
        w.w32(FIELD + 0x70, 0)             # mapLoadType = MAP_LOAD_TYPE_OVERWORLD
        w.w32(FIELD + 0xA0, 0)             # frontierFsys
        w.w32(FIELD + 0xA4, 0)             # linkBattleRuleset
        w.w32(FIELD + 0x40, AVATAR)
        w.w32(AVATAR + 0x18, 0)            # walking
        w.w32(TASK + 0x18, FIELD)
        w.w32(TASK + 0xC, OWNER)
        w.uc.mem_write(OWNER, bytes(0x400))
        w.w32(PARTY_CONT + 4, 5)           # Party_GetCount reads +4
        self.set_inputs()

    def set_inputs(self, held=0, new=0, repeat=0, new_processed=None, touch=None, touch_held=None):
        """gSystem raw/processed keys and touch (x, y) for the next frame."""
        proc = new if new_processed is None else new_processed
        self.w32(SYS + 0x38, held)
        self.w32(SYS + 0x3C, new)
        self.w32(SYS + 0x40, repeat | new)
        self.w32(SYS + 0x48, proc)
        if touch is None:
            self.w16(SYS + 0x64, 0)
            self.w16(SYS + 0x66, 1 if touch_held else 0)
        else:
            self.w16(SYS + 0x60, touch[0])
            self.w16(SYS + 0x62, touch[1])
            self.w16(SYS + 0x64, 1)
            self.w16(SYS + 0x66, 1)

    def open_party(self, flags=0x180, unk350=0, avatar_state=0, count=5, slot=0):
        """Real PartyMenu_LaunchApp_Unk1 (+ our bind hook) as Task_StartMenu_Pokemon would call it."""
        w = self
        w.w32(PARTY_CONT + 4, count)
        w.w32(OWNER + 0x34C, flags)
        w.w32(OWNER + 0x350, unk350)
        w.w32(AVATAR + 0x18, avatar_state)
        args = w.call(N['unk1'], FIELD, OWNER + 0x370, slot)
        w.w32(OWNER + 0x380, args)
        w.w32(OWNER + 0x354, NATIVE_CB)
        w.w16(OWNER + 0x26, 5)
        w.uc.mem_write(PARTY, bytes(0xCB0))
        w.w32(PARTY + 0x654, args)
        w.w8(PARTY + 0xC65, slot)
        self.args = args
        return args

    def open_unbound(self, context=0, slot=0, count=5, flags=0x180):
        """A start-menu party built WITHOUT PartyMenu_LaunchApp_Unk1 (Bag return, swap declined):
        the same fields start_menu.c sub_0203CF74 writes, a direct launcher call, no bind hook."""
        w = self
        w.w32(PARTY_CONT + 4, count)
        w.w32(OWNER + 0x34C, flags)
        w.w32(OWNER + 0x350, 0)
        args = w.call(N['create_args'], 0x0B, FIELD, 0, context)
        w.w32(args + 0x18, OWNER + 0x370)
        w.w8(args + 0x26, slot)
        w.call(N['launch_app'], FIELD, PARTY_TEMPLATE, args)
        w.w32(OWNER + 0x380, args)
        w.w32(OWNER + 0x354, NATIVE_CB)
        w.w16(OWNER + 0x26, 5)
        w.uc.mem_write(PARTY, bytes(0xCB0))
        w.w32(PARTY + 0x654, args)
        w.w8(PARTY + 0xC65, slot)
        self.args = args
        return args

    # ------------------------------------------------------------------ stubs
    def _install_stubs(self):
        table = {
            'heap_alloc': self._heap_alloc, 'heap_free': self._heap_free, 'launch_app': self._launch_app,
            'create_args': self._create_args, 'sub_93070': self._plain(1),
            'load_field': self._plain(1), 'main_normal': self._main_normal,
            'print_ex': self._plain(4), 'add_printer': self._add_printer,
            'copy_vram': self._plain(1), 'play_se': self._plain(1), 'memcpy': self._memcpy,
            'vars_get': self._vars_get, 'check_follower': self._check_follower}
        for name, handler in table.items():
            self.stubs[N[name]] = (name, handler)
            self.stub_hooks[name] = self.uc.hook_add(UC_HOOK_CODE, self._dispatch, None,
                                                     N[name], N[name])

    def _ret(self, value=0):
        self.uc.reg_write(UC_ARM_REG_R0, value & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def _dispatch(self, uc, address, size, user):
        name, handler = self.stubs[address]
        regs = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        handler(name, regs)

    def _plain(self, arity):
        """Logged no-op native with `arity` register arguments (the rest is caller scratch)."""
        def handler(name, regs):
            self.events.append((name, tuple(regs[:arity])))
            self._ret(0)
        return handler

    def _heap_alloc(self, name, regs):
        heap, size = regs[0], regs[1]
        self.events.append((name, (heap, size)))
        for predicate in self.fail_alloc:
            if predicate(size, heap):
                self.fail_alloc.remove(predicate)
                self.heap_log.append(('fail', heap, size))
                return self._ret(0)
        pointer = self.heap_next
        self.heap_next += (size + 0x1F) & ~0x1F
        self.uc.mem_write(pointer, bytes(size))
        self.live[pointer] = (heap, size)
        self.heap_log.append(('alloc', heap, size, pointer))
        self._ret(pointer)

    def _heap_free(self, name, regs):
        pointer = regs[0]
        self.events.append((name, (pointer,)))
        if pointer not in self.live:
            self.errors.append('free of a block that is not live: %#x' % pointer)
            return self._ret(0)
        del self.live[pointer]
        self.heap_log.append(('free', pointer))
        self._ret(0)

    def _launch_app(self, name, regs):
        field, template, args = regs[:3]
        self.events.append((name, (field, template, args)))
        if self.child is not None:
            self.errors.append('FieldSystem_LaunchApplication with a child already running')
        if args == 0:
            self.errors.append('launcher called with NULL args')
        self.child = (template, args)
        self.launches.append((template, args))
        self._ret(0)

    def _create_args(self, name, regs):
        heap, field, a2, context = regs
        self.events.append((name, tuple(regs)))
        pointer = self.heap_next
        for predicate in self.fail_alloc:
            if predicate(0x44, heap):
                self.errors.append('native CreateArgs reached with an allocation that fails (unguarded NULL)')
                return self._ret(0)
        self.heap_next += 0x60
        self.uc.mem_write(pointer, bytes(0x44))
        self.live[pointer] = (heap, 0x44)
        self.heap_log.append(('alloc', heap, 0x44, pointer))
        self.w32(pointer + 0x00, PARTY_CONT)
        self.w32(pointer + 0x1C, field)
        self.w32(pointer + 0x20, field + 0x10C)
        self.w8(pointer + 0x24, context)
        self._ret(pointer)

    def _vars_get(self, name, regs):
        self.events.append((name, (regs[0],)))
        self._ret(VARS_FLAGS)

    def _check_follower(self, name, regs):
        self.events.append((name, (regs[0],)))
        self._ret(self.escort)

    def _main_normal(self, name, regs):
        self.events.append((name, (regs[0],)))
        self._ret(self.main_normal_return)

    def _add_printer(self, name, regs):
        sp = self.uc.reg_read(UC_ARM_REG_SP)
        extra = struct.unpack('<3I', self.uc.mem_read(sp, 12))
        self.events.append((name, tuple(regs) + extra))
        self._ret(0)

    def _memcpy(self, name, regs):
        dest, src, size = regs[:3]
        self.events.append((name, (dest, src, size)))
        self.uc.mem_write(dest, bytes(self.uc.mem_read(src, size)))
        self._ret(dest)

    def install_isolation(self, lo=CB_LO, hi=CB_HI):
        """With self.isolated True, every address outside [lo, hi), the compartment and the
        modelled stubs is a logged external call that returns at once."""
        self.uc.hook_add(UC_HOOK_CODE, self._external, (lo, hi), 0x01FF8000, 0x023FFFFF)

    def _external(self, uc, address, size, bounds):
        lo, hi = bounds
        if not self.isolated:
            return
        if lo <= address < hi or address == STOP or address in self.stubs:
            return
        if self.hooked and self.base <= address < self.base + 0x1000:
            return
        regs = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
        self.events.append(('ext', address, tuple(regs)))
        if address == N['get_field']:
            value = self.u32(regs[0] + 0x18)
        elif address == N['get_env']:
            value = self.u32(regs[0] + 0xC)
        else:
            value = 0x02100000 + (address * 2654435761 >> 8 & 0xFFFC)   # mapped, 4-aligned: usable as pointer or function
        self._ret(value)

    def child_exit(self):
        """The overlay manager deleted the finished field child."""
        self.child = None

    # ------------------------------------------------------------------ running
    def call(self, address, *args, stack=(), limit=200000, check_abi=True):
        uc = self.uc
        sp = STACK_TOP - 0x400
        uc.mem_write(sp - 0x300, bytes(0x300 + 0x40))
        for i, value in enumerate(stack):
            self.w32(sp + 4 * i, value)
        for register, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            uc.reg_write(register, value)
        for register in SAVED:
            uc.reg_write(register, CANARY)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        uc.emu_start(address | 1, STOP, count=limit)
        if uc.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('call to %#x did not return (pc=%#x)' % (address, uc.reg_read(UC_ARM_REG_PC)))
        self.last_preserved = (uc.reg_read(UC_ARM_REG_SP) == sp and
                               all(uc.reg_read(r) == CANARY for r in SAVED))
        self.last_regs = tuple(uc.reg_read(r) for r in SAVED)
        self.last_sp = uc.reg_read(UC_ARM_REG_SP)
        if self.errors:
            raise AssertionError('; '.join(self.errors))
        if check_abi and not self.last_preserved:
            raise AssertionError('call to %#x broke AAPCS (sp/r4-r11)' % address)
        return uc.reg_read(UC_ARM_REG_R0)

    # entries of the installed payload
    def entry(self, name):
        return self.symbols[name] & ~1

    def blob_call(self, name, *args, **kw):
        return self.call(self.entry(name), *args, **kw)

    def callback(self, task=TASK):
        """Enter the real party-return callback (hooked or native) as the start-menu task does."""
        return self.call(CB_LO, task)

    def args_bytes(self, args):
        return bytes(self.uc.mem_read(args, 0x44))

    # observation helpers
    def trace(self, names=None):
        return [e for e in self.events if names is None or e[0] in names]

    def balanced(self):
        return {p: v for p, v in self.live.items()}
