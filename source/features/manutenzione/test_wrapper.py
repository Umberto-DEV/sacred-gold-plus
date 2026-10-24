"""Contratti dei wrapper ARM su RAM sintetica; nessuna ROM o emulatore DS.

Esegue il codice ANIM2 proprio già distribuito. Il confine con il motore
grafico/heap è simulato: queste prove non dimostrano l'assenza di artefatti
visivi nel gioco, ma rilevano scritture durante copie e regressioni ABI.
"""
import json
from pathlib import Path
import struct
import tempfile
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import *

from compila import compila, SOURCE

REG = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
       UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7]
ST, SLOTS, END = 0x023DBBA0, 0x023DBBE0, 0x02001000
SP, OD, PIC, FS, AVATAR = 0x02370000, 0x02350000, 0x02351000, 0x02352000, 0x02353000


class Banco:
    def __init__(self, build, man):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x400000)
        self.sym = {}
        for n, p in man['parti'].items():
            self.uc.mem_write(p['base'], (build / (n + '.bin')).read_bytes())
            self.sym.update(p['simboli'])
        core = SOURCE / 'sgp12/build/anim2'
        m = json.loads((core / 'manifesto.json').read_text())
        for key, file in [('codice', 'blob.bin'), ('tab_u', 'tab_u.bin'),
                          ('par', 'par.bin'), ('siti', 'siti.bin')]:
            self.uc.mem_write(int(m['indirizzi'][key], 16), (core / file).read_bytes())
        self.uc.mem_write(0x023D8703, b'\x02\x5a')
        self.option(True)
        self.w32(FS + 0x40, AVATAR)
        self.w32(AVATAR + 0x18, 0)
        self.calls = []
        self.lookup_result = 4
        self.uc.hook_add(UC_HOOK_CODE, self.hook)

    def w32(self, a, v): self.uc.mem_write(a, struct.pack('<I', v))
    def u32(self, a): return struct.unpack('<I', self.uc.mem_read(a, 4))[0]
    def s16(self, a): return struct.unpack('<h', self.uc.mem_read(a, 2))[0]
    def option(self, on): self.uc.mem_write(0x023D8716, bytes([bool(on)]))

    def sprite(self, i=0):
        od, pic, s = OD + i*0x200, PIC + i*0x100, SLOTS + i*32
        self.w32(od + 0x20, pic)
        self.w32(pic, 1)
        self.uc.mem_write(pic + 0x2E, struct.pack('<h', 3))
        self.uc.mem_write(pic + 0x34, struct.pack('<hh', 260, 252))
        self.uc.mem_write(pic + 0x5B, b'\x01')
        self.uc.mem_write(pic + 0x76, struct.pack('<h', -3))
        self.w32(s, od); self.w32(s + 4, pic)
        self.uc.mem_write(s + 12, struct.pack('<hh', 0, -3))
        self.uc.mem_write(s + 16, bytes([8, 100, 1, 1, 255, 0, 32, 16]))
        return od, pic

    def hook(self, uc, addr, size, data):
        if addr == END:
            uc.emu_stop(); return
        r = [uc.reg_read(x) for x in REG]
        result = None
        if addr == 0x020087A4:  # attributi nativi, solo canali usati da ANIM2
            fields = {4: (0x2E, 2), 12: (0x34, 2), 13: (0x36, 2),
                      22: (0x76, 2), 38: (0x5B, 1)}
            off, n = fields[r[1]]
            uc.mem_write(r[0]+off, (r[2] & ((1 << (8*n))-1)).to_bytes(n, 'little'))
        elif addr == 0x0201AA8C:
            self.calls.append(('alloc', r[0], r[1], self.s16(PIC + 0x2E)))
            result = 0x02354000 + len(self.calls)*0x100
        elif addr == 0x0201AB0C:
            self.calls.append(('free', r[0]))
        elif addr == 0x020542E8:
            self.calls.append(('lookup', r[0], r[1])); result = self.lookup_result
        elif addr == 0x0205C700:
            result = self.u32(r[0] + 0x18)
        elif addr == 0x0226203C:
            self.calls.append(('vanilla_idle', r[0], r[1]))
            pic = self.u32(r[1] + 0x20)
            uc.mem_write(pic + 0x2E, struct.pack('<h', 2))
        else:
            return
        # I nativi possono distruggere r0-r3: la conservazione non è gratuita.
        for i in range(4): uc.reg_write(REG[i], 0xBAD00000 + i)
        if result is not None: uc.reg_write(UC_ARM_REG_R0, result)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def call(self, name, r0=0, r1=0, direction=0):
        saved = [FS, 0x55555555, 0x66666666, direction]
        for reg, v in zip(REG, [r0, r1, 0x22222222, 0x33333333] + saved):
            self.uc.reg_write(reg, v)
        self.uc.reg_write(UC_ARM_REG_SP, SP)
        self.uc.reg_write(UC_ARM_REG_LR, END | 1)
        self.uc.emu_start(self.sym[name] | 1, END, count=20000)
        assert self.uc.reg_read(UC_ARM_REG_PC) == END, 'mancato ritorno entro il budget'
        assert self.uc.reg_read(UC_ARM_REG_SP) == SP, 'stack non ripristinato'
        assert [self.uc.reg_read(x) for x in REG[4:]] == saved, 'callee-saved alterati'
        return self.uc.reg_read(UC_ARM_REG_R0)


class WrapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='sgp-wrapper-test-')
        cls.build = Path(cls.tmp.name)
        cls.man = compila(cls.build)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def setUp(self): self.b = Banco(self.build, self.man)

    def test_neutralizza_tutti_prima_della_copia(self):
        for i in range(4): self.b.sprite(i)
        self.b.call('sgp_copia_inizio', 5, 0x58)
        self.assertEqual(self.b.calls, [('alloc', 5, 0x58, 0)])
        for i in range(4):
            pic = PIC + i*0x100
            self.assertEqual(self.b.s16(pic+0x2E), 0)
            self.assertEqual(self.b.s16(pic+0x34), 256)
            self.assertEqual(self.b.s16(pic+0x36), 256)
            self.assertEqual(bytes(self.b.uc.mem_read(pic+0x5B, 1)), b'\0')

    def test_copie_annidate_bloccano_fino_all_ultima_liberazione(self):
        od, pic = self.b.sprite()
        a = self.b.call('sgp_copia_inizio', 5, 0x58)
        b = self.b.call('sgp_copia_inizio', 5, 0x58)
        self.b.call('sgp_copia_fine', a)
        before = bytes(self.b.uc.mem_read(pic, 0xAC))
        for _ in range(60): self.b.call('sgp_idle_copie', 0x123, od)
        self.assertEqual(bytes(self.b.uc.mem_read(pic, 0xAC)), before)
        self.b.call('sgp_copia_fine', b)
        values = []
        for _ in range(60):
            self.b.call('sgp_idle_copie', 0x123, od)
            values.append(self.b.s16(pic + 0x2E))
        self.assertTrue(any(values), 'idle non riparte dopo ultima copia')

    def test_opzione_spenta_e_riaccesa_mentre_esiste_una_copia(self):
        self.b.option(False)
        od, pic = self.b.sprite()
        self.b.call('sgp_copia_inizio', 5, 0x58)
        self.b.call('sgp_idle_copie', 0x123, od)
        self.assertIn(('vanilla_idle', 0x123, od), self.b.calls)
        self.assertEqual(self.b.s16(pic + 0x2E), 2)
        self.b.option(True)
        self.b.call('sgp_idle_copie', 0x123, od)
        self.assertEqual(self.b.s16(pic + 0x2E), 0)
        before = bytes(self.b.uc.mem_read(pic, 0xAC))
        for _ in range(60): self.b.call('sgp_idle_copie', 0x123, od)
        self.assertEqual(bytes(self.b.uc.mem_read(pic, 0xAC)), before)

    def test_liberazione_senza_copie_non_blocca_l_idle(self):
        od, pic = self.b.sprite()
        self.b.call('sgp_copia_fine', 0x02354000)
        self.assertEqual(self.b.calls, [('free', 0x02354000)])
        values = []
        for _ in range(60):
            self.b.call('sgp_idle_copie', 0x123, od)
            values.append(self.b.s16(pic+0x2E))
        self.assertTrue(any(values))

    def test_copie_non_prendono_scala_posa_e_ombra_native(self):
        od, pic = self.b.sprite()
        self.b.uc.mem_write(pic + 0x34, struct.pack('<hh', 128, 384))
        self.b.uc.mem_write(pic + 0x58, b'\x01')
        self.b.uc.mem_write(pic + 0x76, struct.pack('<h', 9))
        self.b.call('sgp_copia_inizio', 5, 0x58)
        for _ in range(10): self.b.call('sgp_idle_copie', 0x123, od)
        self.assertEqual(self.b.s16(pic + 0x34), 128)
        self.assertEqual(self.b.s16(pic + 0x36), 384)
        self.assertEqual(self.b.s16(pic + 0x76), 9)
        self.assertEqual(bytes(self.b.uc.mem_read(pic + 0x5B, 1)), b'\x01')

    def test_pokepic_assente_o_inattivo_non_viene_scritto(self):
        od, pic = self.b.sprite()
        self.b.call('sgp_copia_inizio', 5, 0x58)
        self.b.w32(od + 0x20, 0)
        self.b.call('sgp_idle_copie', 0x123, od)
        self.b.w32(od + 0x20, pic)
        self.b.w32(pic, 0)
        self.b.uc.mem_write(pic + 0x2E, struct.pack('<h', 7))
        self.b.call('sgp_idle_copie', 0x123, od)
        self.assertEqual(self.b.s16(pic + 0x2E), 7)

    def test_cascata_solo_surf_verso_sud(self):
        for state in (0, 1, 2, 3):
            for direction in (0, 1, 2, 3, 0xFFFFFFFF):
                with self.subTest(state=state, direction=direction):
                    self.b.w32(AVATAR+0x18, state)
                    self.b.calls.clear()
                    v = self.b.call('sgp_cerca_cascata', 0x02354000, 127, direction)
                    if state == 2 and direction == 1:
                        self.assertEqual(v, 4)
                        self.assertEqual(self.b.calls, [('lookup', 0x02354000, 127)])
                    else:
                        self.assertEqual(v, 255)
                        self.assertEqual(self.b.calls, [])

    def test_cascata_conserva_risultato_nativo_assente(self):
        self.b.w32(AVATAR+0x18, 2)
        self.b.lookup_result = 255
        self.assertEqual(self.b.call('sgp_cerca_cascata', 0x02354000, 127, 1), 255)


if __name__ == '__main__': unittest.main()
