"""Mutazioni solo in RAM: il verificatore deve rifiutare difetti reali."""
from pathlib import Path
import hashlib
import struct
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ROM = ROOT / 'local/roms/1.2.3/sgp-1.2.3-EN.nds'
PRET = ROOT / 'local/tools/pokeheartgold'


class TotemChecks(unittest.TestCase):
    def setUp(self):
        path = HERE / 'verifica_totem.py'
        self.assertTrue(path.exists(), 'verificatore mirato non ancora implementato')
        import sys
        sys.path.insert(0, str(HERE))
        import verifica_totem
        self.v = verifica_totem
        if not ROM.exists() or not PRET.exists():
            self.skipTest('ROM privata/pret locale non disponibili')
        self.f = self.v.load_fixture(ROM, PRET)

    def change_instruction(self, name, transform):
        raw = bytearray(self.f.script)
        instructions = self.v.decode(self.f).istruzioni
        instruction = next(i for i in instructions.values() if i.nome == name
                           and i.off in self.v.reachable(self.v.decode(self.f)))
        transform(raw, instruction)
        self.f.script = bytes(raw)

    def test_release_attuale_supera_entrambi_i_contratti(self):
        self.assertEqual(self.v.verify_start(self.f)['errori'], [])
        report = self.v.verify_battle(self.f)
        self.assertEqual(report['errori'], [])
        self.assertEqual(report['esiti_controllati'], 12)

    def test_rifiuta_salto_fuori_membro(self):
        self.change_instruction('GoToIf', lambda raw, i:
                                struct.pack_into('<I', raw, i.off + 3, 0x100000))
        self.assertTrue(self.v.verify_start(self.f)['errori'])

    def test_rifiuta_oggetto_lotta_assente(self):
        del self.f.objects[22]
        self.assertTrue(self.v.verify_start(self.f)['errori'])

    def test_rifiuta_specie_non_valida(self):
        self.change_instruction('WildBattle', lambda raw, i:
                                struct.pack_into('<H', raw, i.off + 2, 0))
        self.assertTrue(self.v.verify_battle(self.f)['errori'])

    def test_rifiuta_livello_non_valido(self):
        self.change_instruction('WildBattle', lambda raw, i:
                                struct.pack_into('<H', raw, i.off + 4, 256))
        self.assertTrue(self.v.verify_battle(self.f)['errori'])

    def test_rifiuta_sblocco_finale_rimosso(self):
        raw = bytearray(self.f.script)
        member = self.v.decode(self.f)
        for instruction in member.istruzioni.values():
            if instruction.nome == 'ReleaseAll':
                struct.pack_into('<H', raw, instruction.off, 0)  # Nop, stessa misura
        self.f.script = bytes(raw)
        self.assertTrue(self.v.verify_battle(self.f)['errori'])

    def test_flag_nativi_legacy_ritornano_offline_ma_scrivono_fuori_struttura(self):
        """Esegue il vero SetFlagInArray, senza mock, su save sintetico.

        Modalità assert=0 esplicita: il risultato non vale per ogni stato
        del gioco. Nessun salvataggio reale viene caricato o modificato.
        """
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
            UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
        for lang in ('EN', 'IT'):
            rom = ROM.with_name(f'sgp-1.2.3-{lang}.nds')
            if not rom.exists():
                self.skipTest(f'manca ROM privata {lang}')
            with rom.open('rb') as stream:
                header = stream.read(512)
                stream.seek(struct.unpack_from('<I', header, 0x20)[0])
                arm = stream.read(struct.unpack_from('<I', header, 0x2C)[0])
            self.assertEqual(hashlib.sha256(arm[0x5045C:0x504A8]).hexdigest(),
                '850e018f34f69dcd31aee0c7868ee149e128b9ed377f75b818c62cd6554c93c3')
            for flag, offset, assertions in ((0xB5F, 0x44B, 0),
                                             (0x3FAF, 0xAD5, 1), (0x3FCA, 0xAD9, 1)):
                with self.subTest(lingua=lang, flag=hex(flag)):
                    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
                    uc.mem_map(0x02000000, 0x400000)
                    uc.mem_write(0x02000000, arm)
                    uc.mem_write(0x021D4150, bytes(4))
                    visits = []
                    def trace(machine, addr, size, data):
                        if addr == 0x0202551C: visits.append(addr)
                        if addr == 0x02340000: machine.emu_stop()
                    uc.hook_add(UC_HOOK_CODE, trace)
                    for reg, value in ((UC_ARM_REG_R0, 0x02350000), (UC_ARM_REG_R1, flag),
                        (UC_ARM_REG_SP, 0x02370000), (UC_ARM_REG_LR, 0x02340001)):
                        uc.reg_write(reg, value)
                    uc.emu_start(0x02050409, 0x02340000, count=1000)
                    self.assertEqual(uc.reg_read(UC_ARM_REG_PC), 0x02340000)
                    changed = [i for i, b in enumerate(uc.mem_read(0x02350000, 0x1000)) if b]
                    self.assertEqual(changed, [offset])
                    self.assertEqual(len(visits), assertions)



if __name__ == '__main__':
    unittest.main()
