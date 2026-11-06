"""Run the real battle accuracy check (overlay 12) from its entry under Unicorn.

Executed natively: BattleSystem_CheckMoveHit 0x0224BCC4 to its return, the
ability getter 0x022527CC, the ignore-check 0x02252834, the ARM9 division
routines it calls, the hit-chance table, and any payload placed by a test.

Stubbed native boundaries (every call is logged with its arguments):
  0x0223A7E0 BattleSystem_GetBattleType(bsys)          -> case battle_type
  0x02252324 CheckAbilityActive(bsys, ctx, 8, 0, abil) -> abil in active_abilities
  0x02255830 GetBattlerHeldItemEffect(ctx, battler)    -> case items
  0x02255844 GetHeldItemModifier(ctx, battler, 0)      -> case items
  0x0225561C target-moved-first helper (ctx, battler)  -> case moved_first
  0x0223BD98 BattleSystem_Random(bsys)                  -> the enumerated residue
The battle context is synthetic: only fields read by this function are set,
at offsets pinned below and checked against the literals in the binary. This
is CPU coverage of one function, not gameplay or an emulator capture.
"""
import hashlib
import os
import struct
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE  # noqa: E402
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,  # noqa: E402
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                               UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

from sgp12.rom import Arm9, Rom  # noqa: E402

REPOSITORY = SOURCE.parent
INPUTS = {
    'EN': ('SGP_ACCURACY_ROM_EN', 'local/experiments/balance493-2026-10-28/candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': ('SGP_ACCURACY_ROM_IT', 'local/experiments/balance493-2026-10-28/candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
REQUIRE = 'SGP_ACCURACY_REQUIRE_INPUTS'

OV12_BASE = 0x022378C0
ENTRY = 0x0224BCC4
GETTER = 0x022527CC
COMPARE = 0x0224BFDC  # cmp r0, r4: r4 holds the final hit chance
IGNORE_CHECK = 0x02252834
STUBS = {0x0223A7E0: 'battle_type', 0x02252324: 'ability_active', 0x02255830: 'item_effect',
         0x02255844: 'item_modifier', 0x0225561C: 'moved_first', 0x0223BD98: 'random'}
# Literal pool of CheckMoveHit: (address, value) pairs this bench relies on.
LITERALS = ((0x0224BFF0, 0x2D5E), (0x0224BFF4, 0x2DB0), (0x0224BFF8, 0x3E3),
            (0x0224BFFC, 0x213C), (0x0224C000, 0x3DE), (0x0224C004, 0x0226CA74),
            (0x0224C00C, 0x2DCC), (0x0224C014, 0x216C))

MON = 0xC0
STAT_ACC, STAT_EVA = 0x2D5E, 0x2D5F
ABILITY = 0x2D67
STATUS2 = 0x2DB0
EFFECT_FLAGS = 0x2DC0
MICLE = 0x2DCC
FIELD = 0x180
BATTLE_STATUS = 0x213C
MOVE_STATUS = 0x216C
MOVE_DATA = 0x3DE
MOVE_COUNT = 468  # LoadMoveTbl reads (NUM_MOVES + 1) contiguous 16-byte records

FORESIGHT = 1 << 29
SUPPRESSED = 1 << 21
INGRAIN = 1 << 10
MIRACLE_EYE = 1 << 22

CTX, BSYS, STOP, STACK_TOP = 0x02380000, 0x02378000, 0x023F0000, 0x023FF000
CANARY = 0xA5A5A5A5
SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
         UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)


def input_path(language):
    variable, default, digest = INPUTS[language]
    path = Path(os.environ.get(variable) or REPOSITORY / default)
    if not path.is_file():
        return None, digest
    return path, digest


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def overlay_image(rom_bytes):
    entry, _, image = Rom(rom_bytes).immagine_overlay(12)
    if entry['ram'] != OV12_BASE:
        raise ValueError('overlay 12 base drift')
    return image


def move_table(archive):
    """Battle cache exactly as LoadMoveTbl reads it: contiguous from member 0."""
    import ndspy.narc
    narc = ndspy.narc.NARC(archive)
    raw = b''.join(narc.files)
    if len(raw) < MOVE_COUNT * 16:
        raise ValueError('move archive shorter than the native battle cache')
    # Prove the concatenation equals the GMIF byte range the native read covers.
    fimg = archive.find(b'GMIF')
    if archive[fimg + 8:fimg + 8 + MOVE_COUNT * 16] != raw[:MOVE_COUNT * 16]:
        raise ValueError('move members are not contiguous in the archive image')
    return raw[:MOVE_COUNT * 16]


class Bench:
    def __init__(self, rom_path, image, payloads=()):
        """`rom_path` is a ROM path or the ROM bytes (ARM9 and autoloads are mapped)."""
        if isinstance(rom_path, (bytes, bytearray)):
            from sgp131.modern_abilities import _arm9_map
            raw = bytes(rom_path)
            segments = _arm9_map(raw)
        else:
            arm = Arm9(rom_path)
            raw, segments = arm.raw, arm.segmenti
        for address, value in LITERALS:
            found = struct.unpack_from('<I', image, address - OV12_BASE)[0]
            if found != value:
                raise ValueError('accuracy literal drift at %#x: %#x' % (address, found))
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_map(0x01FF8000, 0x8000)
        uc.mem_map(0x027E0000, 0x20000)
        for start, offset, size in segments:
            uc.mem_write(start, bytes(raw[offset:offset + size]))
        uc.mem_write(OV12_BASE, bytes(image))
        for address, data in payloads:
            uc.mem_write(address, bytes(data))
        self.calls = []
        self.getter_calls = []
        self.case = {}
        self.residue = 0
        for address, name in STUBS.items():
            uc.hook_add(UC_HOOK_CODE, self._stub, name, address, address)
        uc.hook_add(UC_HOOK_CODE, self._count_getter, None, GETTER, GETTER)
        uc.hook_add(UC_HOOK_CODE, self._chance, None, COMPARE, COMPARE)
        self.hit_chance = None

    def _ret(self, value):
        self.uc.reg_write(UC_ARM_REG_R0, value & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def _count_getter(self, uc, address, size, user):
        self.getter_calls.append(uc.reg_read(UC_ARM_REG_R1))

    def _chance(self, uc, address, size, user):
        self.hit_chance = uc.reg_read(UC_ARM_REG_R4)

    def _stub(self, uc, address, size, name):
        r0, r1, r2, r3 = (uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        case = self.case
        if name == 'battle_type':
            self.calls.append((name,))
            return self._ret(case.get('battle_type', 0))
        if name == 'ability_active':
            ability = struct.unpack('<I', uc.mem_read(uc.reg_read(UC_ARM_REG_SP), 4))[0]
            self.calls.append((name, r2, r3, ability))
            return self._ret(int(ability in case.get('active_abilities', ())))
        if name == 'item_effect':
            self.calls.append((name, r1))
            return self._ret(case.get('items', {}).get(r1, (0, 0))[0])
        if name == 'item_modifier':
            self.calls.append((name, r1, r2))
            return self._ret(case.get('items', {}).get(r1, (0, 0))[1])
        if name == 'moved_first':
            self.calls.append((name, r1))
            return self._ret(int(bool(case.get('moved_first'))))
        if name == 'random':
            self.calls.append((name,))
            return self._ret(self.residue)
        raise AssertionError(name)

    def _prepare(self, case):
        uc = self.uc
        uc.mem_write(CTX, bytes(0x4000))
        if 'move_table' in case:
            uc.mem_write(CTX + MOVE_DATA, case['move_table'])
        move = case.get('move', 1)
        if 'accuracy' in case:
            record = CTX + MOVE_DATA + move * 16
            uc.mem_write(record, struct.pack('<H', case.get('effect', 0)))
            uc.mem_write(record + 2, bytes([case.get('category', 0)]))
            uc.mem_write(record + 4, bytes([case.get('type', 0)]))
            uc.mem_write(record + 5, bytes([case['accuracy']]))
        for battler in range(4):
            mon = CTX + battler * MON
            acc = case.get('acc', {}).get(battler, 6)
            eva = case.get('eva', {}).get(battler, 6)
            uc.mem_write(mon + STAT_ACC, bytes([acc & 0xFF, eva & 0xFF]))
            uc.mem_write(mon + ABILITY, bytes([case.get('abilities', {}).get(battler, 0)]))
            status2 = case.get('status2', {}).get(battler, 0)
            flags = case.get('effect_flags', {}).get(battler, 0)
            uc.mem_write(mon + STATUS2, struct.pack('<I', status2))
            uc.mem_write(mon + EFFECT_FLAGS, struct.pack('<I', flags))
            uc.mem_write(mon + MICLE, struct.pack('<I', (1 << 27) if battler in case.get('micle', ()) else 0))
        uc.mem_write(CTX + FIELD, struct.pack('<I', case.get('field', 0)))
        uc.mem_write(CTX + BATTLE_STATUS, struct.pack('<I', case.get('battle_status', 0)))
        uc.mem_write(CTX + MOVE_STATUS, struct.pack('<I', case.get('move_status', 0)))

    def run(self, case, residue):
        """Execute one call; return (missed, observation dict)."""
        uc = self.uc
        self.case, self.residue = case, residue
        self.calls, self.getter_calls, self.hit_chance = [], [], None
        self._prepare(case)
        sp = STACK_TOP - 0x100
        uc.mem_write(sp - 0x400, bytes(0x400))
        uc.mem_write(sp, struct.pack('<I', case.get('move', 1)))  # 5th argument: move
        uc.mem_write(sp + 4, struct.pack('<I', CANARY))
        uc.reg_write(UC_ARM_REG_R0, BSYS)
        uc.reg_write(UC_ARM_REG_R1, CTX)
        uc.reg_write(UC_ARM_REG_R2, case.get('attacker', 0))
        uc.reg_write(UC_ARM_REG_R3, case.get('target', 1))
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        for register in SAVED:
            uc.reg_write(register, CANARY)
        uc.emu_start(ENTRY | 1, STOP, count=20000)
        if uc.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('accuracy check did not return')
        preserved = (uc.reg_read(UC_ARM_REG_SP) == sp and
                     all(uc.reg_read(r) == CANARY for r in SAVED) and
                     struct.unpack('<I', uc.mem_read(sp + 4, 4))[0] == CANARY)
        status = struct.unpack('<I', uc.mem_read(CTX + MOVE_STATUS, 4))[0]
        return bool(status & 1), {'returned': uc.reg_read(UC_ARM_REG_R0), 'preserved': preserved,
                                  'calls': list(self.calls), 'getter_calls': list(self.getter_calls),
                                  'status': status, 'hit_chance': self.hit_chance}

    def enumerate(self, case):
        """All 100 residues of Random() % 100; returns hits and per-run invariants."""
        hits, rng_calls, preserved, traces = 0, set(), True, set()
        for residue in range(100):
            missed, seen = self.run(case, residue)
            hits += not missed
            rng_calls.add(sum(1 for call in seen['calls'] if call[0] == 'random'))
            preserved &= seen['preserved']
            traces.add(tuple(seen['calls'][:-1]) if seen['calls'] and seen['calls'][-1][0] == 'random'
                       else tuple(seen['calls']))
        return {'hits': hits, 'rng_calls': sorted(rng_calls), 'preserved': preserved,
                'traces': len(traces)}

    def call(self, address, *args, prepare=None):
        """Call a Thumb function directly with AAPCS arguments and canaries."""
        uc = self.uc
        self.calls, self.getter_calls = [], []
        if prepare is not None:
            self.case = prepare
            self._prepare(prepare)
        sp = STACK_TOP - 0x100
        uc.mem_write(sp, struct.pack('<II', CANARY, CANARY))
        for register, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            uc.reg_write(register, value)
        for register in SAVED:
            uc.reg_write(register, CANARY)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        uc.emu_start(address | 1, STOP, count=2000)
        if uc.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('call did not return')
        preserved = (uc.reg_read(UC_ARM_REG_SP) == sp and all(uc.reg_read(r) == CANARY for r in SAVED)
                     and bytes(uc.mem_read(sp, 8)) == struct.pack('<II', CANARY, CANARY))
        return uc.reg_read(UC_ARM_REG_R0), preserved
