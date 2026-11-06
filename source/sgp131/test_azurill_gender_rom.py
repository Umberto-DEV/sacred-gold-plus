"""Class B characterization of HG-D02 on immutable V4 EN/IT ARM9 bytes.

This reproduces the defect; it does not install a fix. Synthetic Pokemon run
through CreateMon, GetMonEvolution and the actual 24-byte evolution commit.
The animation, level-up gameplay, SAVE and cold restart are outside this test.
No ROM or save is written. SGP_AZURILL_ROM_EN/IT override paths, never hashes;
missing inputs skip unless SGP_AZURILL_REQUIRE_INPUTS=1.
"""
import hashlib
import itertools
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_R4, UC_ARM_REG_SP)

from sgp12.rom import Arm9


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}
# Literal boundary cases: gender 1 is female; 0 is male.
CASES = ((0x40, 1, 1), (0x7E, 1, 1), (0x7F, 1, 0),
         (0x80, 1, 0), (0xBE, 1, 0), (0xBF, 0, 0), (0xC0, 0, 0))
PERSONAL_SHA = '91cd5b2bbd5d161f66aeec5b1b2122ee18946557fea1415c3ed433755960e3db'
EVOLUTION_SHA = 'fad0200a3e7e56c0bf3a4ce4487937de16598cc4ba71b3741d8741bc3b890322'
RECEIPT_SHA = 'cb9de95e3d957bde0ce5569c63acbf1141c56d569134e94dbaa52239128842cd'
EVOLUTION_COMMIT = bytes.fromhex('221ca06a05216232f8f70dfca06afbf754ffa06af7f70fff')
CREATE_MON, GET_MON, SET_MON = 0x0206DE38, 0x0206E540, 0x0206EC40
GET_GENDER, GET_EVOLUTION = 0x0206FF88, 0x02070E34
COMMIT_START, COMMIT_END = 0x0207641A, 0x02076432
MON, ARGS, CONTEXT = 0x022C0000, 0x022C2000, 0x022D0000
STACK, STOP = 0x023FF000, 0x023EF000
REGISTERS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
NARCS = {2: 'a/0/0/2', 3: 'a/0/0/3', 11: 'a/0/1/1',
         33: 'a/0/3/3', 34: 'a/0/3/4'}
PERMUTATIONS = tuple(itertools.permutations(range(4)))


def unicorn_works():
    """Probe in a child: the Codex sandbox blocks Unicorn before guest code."""
    probe = subprocess.run(
        [sys.executable, '-c',
         'from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB; '
         'u=Uc(UC_ARCH_ARM,UC_MODE_THUMB); u.mem_map(0x2000000,0x1000)'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    return probe.returncode == 0


def input_image(case, language):
    path = Path(os.environ.get('SGP_AZURILL_ROM_' + language)
                or V4_ROOT / f'candidate-v4-{language}.nds')
    if not path.is_file():
        message = f'private {language} V4 input missing: {path}'
        if os.environ.get('SGP_AZURILL_REQUIRE_INPUTS') == '1':
            case.fail(message)
        case.skipTest(message)
    raw = path.read_bytes()
    case.assertEqual((hashlib.sha256(raw).hexdigest(), len(raw)), V4[language])
    arm = Arm9.from_bytes(raw)
    case.assertEqual(arm.leggi(COMMIT_START, 24), EVOLUTION_COMMIT)
    case.assertEqual(hashlib.sha256(arm.leggi(GET_EVOLUTION, 0x408)).hexdigest(),
                     'd2eff7552f78bb7c3bb6fcca288da72a369d239648f5d576dafe456705e36a91')
    case.assertEqual(hashlib.sha256(arm.leggi(GET_GENDER, 160)).hexdigest(),
                     'b23885245b467e9801a87ffff535629af6775c0727a54cb4305fd0785e2646b2')
    rom = ndspy.rom.NintendoDSRom(raw)
    archives = {}
    for narc, name in NARCS.items():
        blob = rom.getFileByName(name)
        if narc in (2, 34):
            case.assertEqual(hashlib.sha256(blob).hexdigest(),
                             PERSONAL_SHA if narc == 2 else EVOLUTION_SHA)
        archives[narc] = ndspy.narc.NARC(blob).files
    case.assertEqual(tuple(archives[2][s][0x10] for s in (298, 183, 184)),
                     (0xBF, 0x7F, 0x7F))
    case.assertEqual(struct.unpack_from('<3H', archives[34][298]), (1, 0, 183))
    return arm, archives


class NativeEvolutionBench:
    """Actual ARM9; only OS heap, NARC I/O and localized name are serviced.

    ITEM_NONE's hold effect is the sole item service seam. Get/SetMonData,
    gender, evolution, encryption, checksum, ability and stats stay native.
    Scratch RAM is test-only and outside the authenticated ARM9 segments.
    """
    def __init__(self, arm, archives):
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.cpu.mem_map(0x01FF0000, 0x410000)
        for address, offset, size in arm.segmenti:
            if 0x01FF0000 <= address and address + size <= 0x02400000:
                self.cpu.mem_write(address, bytes(arm.raw[offset:offset + size]))
        self.archives = archives
        self.heap = 0x02300000
        self.assertions = 0
        self.cpu.hook_add(UC_HOOK_CODE, self.hook)

    def allocate(self, size):
        pointer = self.heap
        self.heap = (pointer + size + 7) & ~7
        if not 0 <= size <= 0x10000 or self.heap >= 0x023B0000:
            raise AssertionError('bounded test heap exhausted')
        self.cpu.mem_write(pointer, bytes(size))
        return pointer

    def ret(self, value=0):
        self.cpu.reg_write(UC_ARM_REG_R0, value)
        self.cpu.reg_write(UC_ARM_REG_PC, self.cpu.reg_read(UC_ARM_REG_LR))

    def hook(self, cpu, address, _size, _user):
        a, b, c, _ = (cpu.reg_read(r) for r in REGISTERS)
        if address in (0x0201AA8C, 0x0201AACC):
            self.ret(self.allocate(b))
        elif address == 0x0201AB0C:
            self.ret()
        elif address == 0x02007508:
            cpu.mem_write(a, bytes(self.archives[b][c]))
            self.ret()
        elif address in (0x02007524, 0x02007544):
            blob = bytes(self.archives[a][b])
            pointer = self.allocate(len(blob))
            cpu.mem_write(pointer, blob)
            self.ret(pointer)
        elif address == 0x0200BCDC:
            # One valid synthetic String; localized glyphs cannot affect gender.
            pointer = self.allocate(12)
            cpu.mem_write(pointer, struct.pack('<HHIHH', 2, 1, 0xB6F8D2EC, 0x012B, 0xFFFF))
            self.ret(pointer)
        elif address == 0x02077D88:
            if (a, b, c) != (0, 1, 0):
                raise AssertionError('unexpected item service: only ITEM_NONE hold effect allowed')
            self.ret(0)
        elif address == 0x0202551C:
            self.assertions += 1
            raise AssertionError('native GF_AssertFail')

    def put(self, address, value):
        self.cpu.mem_write(address, struct.pack('<I', value))

    def call(self, address, *args):
        for i, register in enumerate(REGISTERS):
            self.cpu.reg_write(register, args[i] if i < len(args) else 0)
        for i, value in enumerate(args[4:]):
            self.put(STACK + 4 * i, value)
        self.cpu.reg_write(UC_ARM_REG_SP, STACK)
        self.cpu.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.cpu.emu_start(address | 1, STOP, count=2_000_000)
        if self.cpu.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('native call exceeded instruction budget')
        if self.cpu.reg_read(UC_ARM_REG_SP) != STACK:
            raise AssertionError('native call unbalanced stack')
        return self.cpu.reg_read(UC_ARM_REG_R0)

    def get(self, field):
        return self.call(GET_MON, MON, field, 0)

    def set(self, field, value):
        self.put(ARGS, value)
        self.call(SET_MON, MON, field, ARGS)

    def evolution_commit(self, target):
        self.put(CONTEXT + 0x28, MON)
        self.cpu.mem_write(CONTEXT + 0x62, struct.pack('<H', target))
        self.cpu.reg_write(UC_ARM_REG_R4, CONTEXT)
        self.cpu.reg_write(UC_ARM_REG_SP, STACK)
        self.cpu.emu_start(COMMIT_START | 1, COMMIT_END, count=2_000_000)
        if (self.cpu.reg_read(UC_ARM_REG_PC), self.cpu.reg_read(UC_ARM_REG_SP)) != (COMMIT_END, STACK):
            raise AssertionError('native evolution slice budget/stack failure')

    def box_snapshot(self):
        """Independent decode of the native encrypted record and its checksum."""
        data = bytes(self.cpu.mem_read(MON, 136))
        pid, _, checksum = struct.unpack_from('<IHH', data)
        seed = checksum
        words = []
        for encrypted in struct.unpack('<64H', data[8:]):
            seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
            words.append(encrypted ^ (seed >> 16))
        blocks = struct.pack('<64H', *words)
        position = PERMUTATIONS[((pid >> 13) & 31) % 24].index(1)
        gender = (blocks[position * 32 + 24] >> 1) & 3
        return gender, checksum, checksum == (sum(words) & 0xFFFF)


def reproduce_case(image, pid):
    bench = NativeEvolutionBench(*image)
    bench.call(CREATE_MON, MON, 298, 20, 31, 1, pid, 1, 0xABCD1234)
    before = bench.get(111)
    native_before = bench.call(GET_GENDER, MON)
    identity_before = tuple(bench.get(f) for f in (0, 7, 8))
    species_before = bench.get(5)
    bench.set(9, 219)
    rejected = bench.call(GET_EVOLUTION, 0, MON, 0, 0, ARGS + 0x100)
    bench.set(9, 220)
    target = bench.call(GET_EVOLUTION, 0, MON, 0, 0, ARGS + 0x100)
    method = struct.unpack('<I', bench.cpu.mem_read(ARGS + 0x100, 4))[0]
    bench.evolution_commit(target)
    native_gender = bench.call(GET_GENDER, MON)
    cached_before, checksum_before, valid_before = bench.box_snapshot()
    field_gender = bench.get(111)
    cached_after, checksum_after, valid_after = bench.box_snapshot()
    return {'genders': (before, native_before, native_gender, field_gender),
            'decisions': (rejected, target, method),
            'identity_before': identity_before,
            'identity_after': tuple(bench.get(f) for f in (0, 7, 8)),
            'species': (species_before, bench.get(5)),
            'checksum_failed': bench.get(3),
            'checksum_valid': valid_before and valid_after,
            'assertions': bench.assertions,
            'cache_before_read': cached_before, 'cache_after_read': cached_after,
            'checksum_delta': checksum_after - checksum_before}


class AzurillGenderNativeRomTests(unittest.TestCase):
    def test_same_species_and_pid_cannot_preserve_affected_gender_in_vanilla(self):
        """The interoperability constraint has no exact-PID solution.

        A vanilla peer receives species and PID in the BoxPokemon and derives
        gender from those two values.  Therefore a local cache or sidecar
        cannot keep an affected Marill female without changing species, PID,
        or the peer's personal table/code.
        """
        azurill_female = {low for low in range(256) if 0xBF > low}
        marill_female = {low for low in range(256) if 0x7F > low}
        affected = azurill_female - marill_female
        self.assertEqual(affected, set(range(0x7F, 0xBF)))
        self.assertEqual((len(azurill_female), len(marill_female), len(affected)),
                         (191, 127, 64))
        for low in affected:
            pid = 0x12345600 | low
            self.assertEqual(1 if 0xBF > (pid & 0xFF) else 0, 1)
            self.assertEqual(1 if 0x7F > (pid & 0xFF) else 0, 0)

    def test_native_evolution_exposes_gender_ratio_transition(self):
        images = {language: input_image(self, language) for language in ('EN', 'IT')}
        if not unicorn_works():
            self.skipTest('local Unicorn engine is unavailable before guest execution')
        observed = []
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                image = images[language]
                for low, before, after in CASES:
                    with self.subTest(language=language, low=hex(low)):
                        result = reproduce_case(image, 0x12345600 | low)
                        self.assertEqual(result['genders'], (before, before, after, after))
                        self.assertEqual(result['decisions'], (0, 183, 1))
                        self.assertEqual(result['species'], (298, 183))
                        self.assertEqual(result['identity_before'],
                                         (0x12345600 | low, 0xABCD1234, 6400))
                        self.assertEqual(result['identity_before'],
                                         result['identity_after'])
                        self.assertEqual(result['checksum_failed'], 0)
                        self.assertTrue(result['checksum_valid'])
                        self.assertEqual(result['assertions'], 0)
                        self.assertEqual(result['cache_before_read'], before)
                        self.assertEqual(result['cache_after_read'], after)
                        self.assertEqual(result['checksum_delta'], 2 * (after - before))
                        observed.append({'language': language, 'pid_low': low, **result})
        receipt = hashlib.sha256(json.dumps(
            observed, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(receipt, RECEIPT_SHA)


if __name__ == '__main__':
    unittest.main()
