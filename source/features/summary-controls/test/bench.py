"""Unicorn bench: the real V4 ARM9 bytes of the Summary window engine plus the payload.

What executes natively (real bytes read from the candidate ROM):
  AllocWindows, AddWindow, FillWindowPixelBuffer (with MI_CpuFillFast),
  ScheduleWindowCopyToVram (PutWindowTilemap_TextMode), ClearWindowTilemapAndCopyToVram
  (ClearWindowTilemapText), WindowArray_Delete, and the installed EV/IV viewer.
Stubbed boundaries (each call is logged with its arguments):
  Heap_Alloc / Heap_Free (bump allocator, double free and wild free are recorded),
  AddTextPrinterParameterizedWithColor, GetMon sub_0208A520, GetBoxMonData,
  the deferred VRAM transfers, and anything a test adds.
The Summary object, BgConfig, args and mon are synthetic and sparse: only fields
read by the code under test are set, at offsets pinned in controls-native-abi.json.
This is CPU coverage of the call sequences, not a rendering or an Android run.
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

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE,  # noqa: E402
                     UcError)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,  # noqa: E402
                               UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                               UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

from sgp131 import controls  # noqa: E402
from sgp131.baseline import INPUT_HASHES  # noqa: E402

REPOSITORY = SOURCE.parent
INPUTS = {
    'EN': ('SGP_CONTROLS_ROM_EN', 'local/experiments/balance493-2026-10-28/candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': ('SGP_CONTROLS_ROM_IT', 'local/experiments/balance493-2026-10-28/candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
REQUIRE = 'SGP_CONTROLS_REQUIRE_INPUTS'

# Declared TEST placements (not reserve assignments): scratch RAM inside the 4 MB map.
TEST_BASE = 0x023A0000
TEST_BASE_ALT = 0x023B8000
SUMMARY, BGCONFIG, TILEMAP, ARGS, MON = 0x02390000, 0x02388000, 0x02386000, 0x02391000, 0x02392000
TILEMAP_BG1 = 0x02384000
HEAP_ARENA, HEAP_END = 0x02300000, 0x02380000
STOP, STACK_TOP, CANARY = 0x023F0000, 0x023FF000, 0xA5A5A5A5
POISON_ALLOC, POISON_FREE = 0xCD, 0xDD  # fresh and released heap blocks are filled; touching a released one is an error
SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
         UC_ARM_REG_R10, UC_ARM_REG_R11)
ARGUMENT_REGISTERS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)

GSYSTEM = 0x021D110C

# --- declared TEST reserve policy ------------------------------------------------------------------------
# The installer accepts a base only from a reserve.allocate receipt checked against the policy in force. The
# real policy cannot grant `summary-controls.runtime` (its owner `field-guide.code` is conditional), so the
# installer tests replace controls._reserve_policy with a declared double: the slot name/start/size are COPIED
# from the real reserve-map.json (they cannot drift) and the parent is declared non-conditional. The double has
# its own version and digest, so a receipt made under it is refused by the real policy. No ROM bytes are
# written outside the slot, and nothing here is a product assignment.
TEST_POLICY_VERSION = 'TEST-ONLY-reserve-policy'
TEST_POLICY_SHA256 = hashlib.sha256(b'TEST-ONLY reserve policy: a declared test double, never the product map').hexdigest()
REAL_RESERVE_POLICY = controls._reserve_policy        # captured before any patch


def real_slot(name=controls.SLOT_NAME):
    """(start, bytes) of `name` in the real reserve-map.json (read only)."""
    policy = json.loads((SOURCE / 'sgp131/data/reserve-map.json').read_text())
    for entry in policy['subdivisions']:
        for part in entry['parts']:
            if part['name'] == name and part['kind'] == 'payload':
                return part['start'], part['bytes']
    raise AssertionError('reserve-map.json has no slot ' + name)


INSTALL_BASE, SLOT_BYTES = real_slot()


def declared_policy():
    start, size = real_slot()
    part = {'name': controls.SLOT_NAME, 'kind': 'payload', 'start': start, 'bytes': size}
    return ({'version': TEST_POLICY_VERSION, 'conditional_parents': [],
             'subdivisions': [{'parent': 'test.declared-parent', 'parts': [part]}]}, TEST_POLICY_SHA256)


def declared_allocation(language, size=None, **override):
    """A reserve.allocate-shaped receipt under the declared test policy (fixture, not an assignment)."""
    start, capacity = real_slot()
    size = capacity if size is None else size
    record = {'schema': 1, 'input_sha256': next(h for h, lang in INPUT_HASHES.items() if lang == language),
              'language': language, 'policy_version': TEST_POLICY_VERSION, 'policy_sha256': TEST_POLICY_SHA256,
              'audit_sha256': hashlib.sha256(b'test audit').hexdigest(), 'requested': {controls.SLOT_NAME: size},
              'assignments': [{'name': controls.SLOT_NAME, 'parent': 'test.declared-parent', 'start': start,
                               'bytes': size, 'capacity': capacity}],
              'preservation': {}, 'address_reserved': True, 'installed': False, 'installation_authorized': False}
    record.update(override)
    return record


def declared_reserve():
    """Context manager: controls._reserve_policy is the declared test double."""
    return mock.patch.object(controls, '_reserve_policy', declared_policy)


def real_reserve():
    return mock.patch.object(controls, '_reserve_policy', REAL_RESERVE_POLICY)
PAGE_SKILLS = 1


def input_path(language):
    variable, default, digest = INPUTS[language]
    path = Path(os.environ.get(variable) or REPOSITORY / default)
    return (path if path.is_file() else None), digest


def addr(abi, name):
    return controls.hex_int(abi['natives'][name]['address'])


class Bench:
    def __init__(self, rom, payload=None, base=TEST_BASE, patches=(), tilemap_dirty=0):
        """`rom` bytes; `payload` placed at `base`; `patches` = (address, bytes) written into ARM9 RAM."""
        self.abi = controls.load_abi()
        segments = controls._arm9_segments(rom)
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x01FF8000, 0x8000)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_map(0x027E0000, 0x20000)
        for start, offset, size in segments:
            uc.mem_write(start, bytes(rom[offset:offset + size]))
        if payload is not None:
            uc.mem_write(base, bytes(payload))
        for address, value in patches:
            uc.mem_write(address, bytes(value))
        self.base = base
        self.log = []          # (name, args...) of every stubbed boundary
        self.heap = {}         # live allocation -> (heap id, size)
        self.allocs, self.frees, self.errors = [], [], []
        self.fail_alloc_after = None   # allocation index from which Heap_Alloc returns NULL
        self.gsystem_reads = []
        self.cursor = HEAP_ARENA
        self.mon_present, self.egg = True, 0
        self.pre_existing = {}
        self.stubs = {}
        self.stop_at = STOP
        self.stub('heap_alloc', self._heap_alloc)
        self.stub('heap_free', self._heap_free)
        self.stub('print', self._print)
        self.stub('get_mon', self._get_mon)
        self.stub('get_box_data', self._box_data)
        self.stub(0x0201C0C0, self._load_char_tiles)
        self.stub(0x0201BF94, self._copy_tilemap_range)
        uc.hook_add(UC_HOOK_MEM_READ, self._watch_reads, None, GSYSTEM, GSYSTEM + 0x70)

    # --- stubs -------------------------------------------------------------
    def stub(self, name_or_address, handler):
        address = addr(self.abi, name_or_address) if isinstance(name_or_address, str) else name_or_address
        self.stubs[address] = handler
        self.uc.hook_add(UC_HOOK_CODE, self._dispatch, handler, address, address)

    def _dispatch(self, uc, address, size, handler):
        args = [uc.reg_read(r) for r in ARGUMENT_REGISTERS]
        sp = uc.reg_read(UC_ARM_REG_SP)
        value = handler(args, sp)
        uc.reg_write(UC_ARM_REG_R0, (value or 0) & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def _stack_word(self, sp, index):
        return struct.unpack('<I', self.uc.mem_read(sp + 4 * index, 4))[0]

    def _heap_alloc(self, args, sp):
        heap, size = args[0], args[1]
        self.log.append(('heap_alloc', heap, size))
        if self.fail_alloc_after is not None and len(self.allocs) >= self.fail_alloc_after:
            return 0
        self.cursor = (self.cursor + 15) & ~15
        pointer, self.cursor = self.cursor, self.cursor + max(size, 16)
        if self.cursor > HEAP_END:
            raise AssertionError('bench heap exhausted')
        self.uc.mem_write(pointer, bytes([POISON_ALLOC]) * max(size, 16))  # fresh heap memory is NOT zero
        self.heap[pointer] = (heap, size)
        self.allocs.append((pointer, heap, size))
        return pointer

    def _heap_free(self, args, sp):
        pointer = args[0]
        self.log.append(('heap_free', pointer))
        if pointer == 0:
            return
        if pointer in self.heap:
            _heap_id, size = self.heap.pop(pointer)
            self.frees.append(pointer)
            size = max(size, 16)
            self.uc.mem_write(pointer, bytes([POISON_FREE]) * size)
            self.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._freed_access, pointer, pointer, pointer + size - 1)
        else:
            self.errors.append(('wild-or-double-free', pointer))

    def _freed_access(self, uc, access, address, size, value, block):
        self.errors.append(('use-after-free', block, address, 'write' if access else 'read'))

    def _print(self, args, sp):
        window, font, string, x = args
        y, speed, color, callback = (self._stack_word(sp, i) for i in range(4))
        magic = struct.unpack('<I', self.uc.mem_read(string + 4, 4))[0]
        size = struct.unpack('<H', self.uc.mem_read(string + 2, 2))[0]
        codes = struct.unpack('<%dH' % size, self.uc.mem_read(string + 8, 2 * size))
        self.log.append(('print', window, font, x, y, speed, color, callback, magic, codes))
        return 0xFF

    def _load_char_tiles(self, args, sp):
        self.log.append(('load_char_tiles', args[1], args[2], args[3], self._stack_word(sp, 0)))

    def _copy_tilemap_range(self, args, sp):
        self.log.append(('copy_tilemap_range', args[1], args[3]))

    def _get_mon(self, args, sp):
        self.log.append(('get_mon', args[0]))
        return MON if self.mon_present else 0

    def _box_data(self, args, sp):
        self.log.append(('get_box_data', args[0], args[1], args[2]))
        return self.egg if args[1] == 76 else 0

    def _watch_reads(self, uc, access, address, size, value, user):
        self.gsystem_reads.append(address)

    # --- synthetic objects ---------------------------------------------------
    def build_summary(self, page=PAGE_SKILLS, state=0, mode=0, move_to_learn=0, windows_ptr=0x02393000):
        uc = self.uc
        uc.mem_write(SUMMARY, bytes(0x7D8))
        uc.mem_write(ARGS, bytes(0x40))
        uc.mem_write(BGCONFIG, bytes(8 + 8 * 0x2C))
        uc.mem_write(TILEMAP, bytes(0x800))
        uc.mem_write(TILEMAP_BG1, bytes(0x800))
        uc.mem_write(BGCONFIG, struct.pack('<I', 19))
        # Background[n]: tilemapBuffer, bufferSize, baseTile | ... | mode, size, colorMode, tileSize
        for layer, buffer in ((4, TILEMAP), (1, TILEMAP_BG1)):
            bg = BGCONFIG + 8 + layer * 0x2C
            uc.mem_write(bg, struct.pack('<III', buffer, 0x800, 0))
            uc.mem_write(bg + 0x14, bytes([0, 1, 0, 0x20]))
        uc.mem_write(SUMMARY, struct.pack('<I', BGCONFIG))
        uc.mem_write(SUMMARY + 0x224, struct.pack('<II', windows_ptr, 18))
        uc.mem_write(SUMMARY + 0x22C, struct.pack('<I', ARGS))
        uc.mem_write(SUMMARY + 0x7BC, bytes([page & 0xFF]))
        uc.mem_write(SUMMARY + 0x7BF, bytes([state]))
        uc.mem_write(ARGS + 0x12, bytes([mode]))
        uc.mem_write(ARGS + 0x18, struct.pack('<H', move_to_learn))
        return SUMMARY

    def add_shared_window(self, index, template):
        """A real native Window in the Summary's shared array (summary + 4 + 16 * index)."""
        raw = struct.pack('<6BH', *template)
        self.uc.mem_write(0x02395000 + 8 * index, raw)
        self.call(addr(self.abi, 'add_window'), BGCONFIG, SUMMARY + 4 + 16 * index, 0x02395000 + 8 * index)
        self.pre_existing = dict(self.heap)

    def tilemap(self):
        return struct.unpack('<%dH' % 0x400, self.uc.mem_read(TILEMAP, 0x800))

    def poke_tilemap(self, index, value):
        self.uc.mem_write(TILEMAP + 2 * index, struct.pack('<H', value))

    def state(self, base=None):
        base = self.base if base is None else base
        return struct.unpack('<8I', self.uc.mem_read(base, 0x20))

    def set_state(self, base=None, **fields):
        names = ('owner', 'generation', 'window', 'redraws', 'enabled')
        current = list(self.state(base))
        for key, value in fields.items():
            current[names.index(key)] = value
        self.uc.mem_write(self.base if base is None else base, struct.pack('<8I', *current))

    def window_bytes(self, pointer):
        return bytes(self.uc.mem_read(pointer, 16))

    # --- execution -----------------------------------------------------------
    def call(self, address, *args, count=200000, entry_regs=None, until=None):
        """Run a Thumb function to its return; returns (r0, preserved, trace)."""
        uc = self.uc
        sp = STACK_TOP - 0x100
        uc.mem_write(sp - 0x400, bytes([0xCC]) * 0x400)   # poison the stack below the canary line
        uc.mem_write(sp, struct.pack('<II', CANARY, CANARY))
        for register in ARGUMENT_REGISTERS:
            uc.reg_write(register, 0)
        for register, value in zip(ARGUMENT_REGISTERS, args):
            uc.reg_write(register, value)
        for register in SAVED:
            uc.reg_write(register, CANARY)
        for register, value in (entry_regs or {}).items():
            uc.reg_write(register, value)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        low = {'v': sp}

        def track(uc_, address_, size_, user):
            pointer = uc_.reg_read(UC_ARM_REG_SP)
            if pointer < low['v']:
                low['v'] = pointer
        hook = uc.hook_add(UC_HOOK_CODE, track)
        try:
            uc.emu_start(address | 1, STOP if until is None else until, count=count)
        except UcError as error:
            raise AssertionError('native call to 0x%08X faulted at pc=0x%08X: %s' % (
                address, uc.reg_read(UC_ARM_REG_PC), error)) from error
        finally:
            uc.hook_del(hook)
        if until is not None:
            self.last_stack_bytes = sp - low['v']
            return uc.reg_read(UC_ARM_REG_R0), None
        if uc.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('call to 0x%08X did not return' % address)
        preserved = (uc.reg_read(UC_ARM_REG_SP) == sp and all(uc.reg_read(r) == CANARY for r in SAVED)
                     and bytes(uc.mem_read(sp, 8)) == struct.pack('<II', CANARY, CANARY))
        self.last_stack_bytes = sp - low['v']
        return uc.reg_read(UC_ARM_REG_R0), preserved

    def live_allocations(self):
        return dict(self.heap)
