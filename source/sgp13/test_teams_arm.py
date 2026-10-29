"""Actual old/new trainer hooks: level/RNG-relevant registers and move isolation."""
import os
from pathlib import Path
import struct
import tempfile
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
    UC_ARM_REG_SP, UC_ARM_REG_CPSR)

from sgp12.rom import Arm9
from sgp13 import space, teams

REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)
BATTLE, BUFFER, MON, STACK = 0x02380000, 0x02384000, 0x02386000, 0x023BF000


def machine(path):
    arm = Arm9(path)
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    cpu.mem_map(0x02000000, 0x400000)
    for address, offset, size in arm.segmenti:
        if 0x02000000 <= address < 0x02400000:
            cpu.mem_write(address, bytes(arm.raw[offset:offset + size]))
    return cpu


def invoke(cpu, site, trainer, metadata, record, slot, party_index, plus):
    cpu.mem_write(BATTLE, bytes(0x200))
    cpu.mem_write(BATTLE + 0x18 + party_index * 4, struct.pack('<I', trainer))
    cpu.mem_write(BATTLE + 0x28 + party_index * 52, bytes(metadata[:4]))
    cpu.mem_write(BUFFER, bytes(record))
    state = bytearray(32); state[0] = plus; state[2] = 100
    cpu.mem_write(0x023D8700, bytes(state))
    cpu.mem_write(STACK + 0x74, struct.pack('<I', BUFFER))
    initial = (123, 0xAABBCCDD, BUFFER + slot * 18, 0x1F000000,
               BATTLE, party_index * 52, MON, 0x56789ABC)
    for register, value in zip(REGS, initial):
        cpu.reg_write(register, value)
    cpu.reg_write(UC_ARM_REG_SP, STACK)
    cpu.emu_start(site | 1, site + 4, count=100000)
    result = tuple(cpu.reg_read(register) for register in REGS)
    return result, cpu.reg_read(UC_ARM_REG_SP), cpu.reg_read(UC_ARM_REG_CPSR) & 0xF0000000, bytes(cpu.mem_read(BUFFER, 108))


@unittest.skipUnless(os.environ.get('SGP13_BASE_DIR'), 'needs private inputs and executable Unicorn JIT')
class NativeTeams(unittest.TestCase):
    def test_all_four_call_sites_preserve_original_level_abi_in_both_modes(self):
        import json
        spec = json.loads(Path(teams.__file__).with_name('data').joinpath('strategic-teams.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for language in ('EN', 'IT'):
                source = Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds'
                raw = source.read_bytes()
                self.assertEqual(space.identify(raw), language)
                base = directory / 'expanded.nds'; base.write_bytes(space.expand_rom(raw))
                result = directory / 'teams.nds'
                teams.install(base, result, directory)
                original_rom = ndspy.rom.NintendoDSRom(raw)
                new_rom = ndspy.rom.NintendoDSRom.fromFile(result)
                self.assertEqual(new_rom.files, original_rom.files)
                trainer_data = ndspy.narc.NARC(original_rom.getFileByName('a/0/5/5')).files
                party_data = ndspy.narc.NARC(original_rom.getFileByName('a/0/5/6')).files
                old_cpu, new_cpu = machine(base), machine(result)
                for team in spec['teams']:
                    trainer = team['trainer_id']; before = party_data[trainer]
                    after = bytearray(before)
                    for move in team['moves']:
                        struct.pack_into('<H', after, move['offset'], move['after'])
                    for plus in (0, 1):
                        for site in teams.SITES:
                            for slot in range(6):
                                with self.subTest(language=language, trainer=trainer, plus=plus, site=hex(site), slot=slot):
                                    args = (site, trainer, trainer_data[trainer], before, slot, slot % 4, plus)
                                    old = invoke(old_cpu, *args)
                                    new = invoke(new_cpu, *args)
                                    self.assertEqual(new[:3], old[:3])
                                    self.assertEqual(new[1], STACK)
                                    self.assertEqual(new[3], bytes(after) if plus else before)


if __name__ == '__main__':
    unittest.main()
