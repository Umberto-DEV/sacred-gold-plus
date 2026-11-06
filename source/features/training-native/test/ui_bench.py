"""ROM-free real Training owner. Seams are hardware flash and OS identity only."""
from pathlib import Path
import struct
import subprocess
import sys
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC, UC_ARM_REG_LR, UC_ARM_REG_SP

SOURCE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SOURCE))
from sgp13 import training, shiny, shiny_core
FLAGS = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
         '-ffreestanding', '-fno-builtin', '-fno-stack-protector', '-fno-jump-tables',
         '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra', '-Werror']
EXT = 0x02200000  # caller scratch only; no production allocation
STATE, GENERATION, DESCRIPTOR = 0x023D3000, 0x023CB1F0, 0x023CB1A0
FS, SAVE, APP = 0x02290000, 0x022A0000, 0x022D0000
OPTIONS = SAVE + 0x110  # SaveData+dynamic_region10+SAVE_PLAYERDATA offset100
OUT, PROOF, NEXT = 0x027E0100, 0x027E0200, 0x027E0300
STACK, STOP = 0x027E3778, 0x023FF800
REGS = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)
SHINY, ADMITTED, FLAGS_OFFSET = STATE + 240, STATE + 1052, STATE + 38


def compile_object(source, obj, flags=()):
    subprocess.run(['clang', *FLAGS, *flags, '-c', str(source), '-o', str(obj)],
                   check=True, capture_output=True)
    loader = training.module(SOURCE / 'features/options/tools/carica_text.py', 'ui_loader')
    return loader.load_text(Path(obj).read_bytes(), EXT)


class Bench:
    def __init__(self, blobs):
        old, self.ts, extension, self.us, core, cs, native, self.ns = blobs
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x02000000, 0x400000)
        self.u.mem_map(0x027E0000, 0x4000)
        for address, blob in ((training.BASE, old), (EXT, extension),
                              (0x023C8100, core), (0x023C9100, native)):
            self.u.mem_write(address, blob)
        config = [0x594E4853, (152 << 16) | 2]
        config += [self.ns['sgp_shiny_' + n] for n in ('snapshot', 'candidate', 'apply')]
        config += [cs['sgp_shiny_' + n] for n in ('valid', 'denominator', 'select', 'complete', 'draw', 'transform')]
        config += [self.ts['training_shiny_access'], self.ts['training_shiny_bind'], self.ts['training_read']]
        config += [0] * 7
        self.u.mem_write(0x023CB100, struct.pack('<21IHH', *config, 0, 0) + bytes(64))
        d = [0x31544955, (80 << 16) | 1, (52 << 16) | 152, 3, 0, 0, 0]
        d += [self.us['training_ui_' + n] for n in ('peek', 'validate', 'store', 'load', 'bind')]
        d += [self.ts['training_load'], self.ts['training_shiny_bind'], self.ts['storage_ready'], GENERATION]
        d += [0] * 4
        self.u.mem_write(DESCRIPTOR, struct.pack('<20I', *d))
        self.put(FS + 12, SAVE)
        self.put(0x021D4158, FS)
        self.put(APP + 0x24, OPTIONS)
        self.put(SAVE + 0x23010, 17)
        self.put(SAVE + 0x2301C + 16, 0x100)  # array1.offset, native Options identity
        self.put(SAVE + 0x232B8, 0)
        self.put(SAVE + 0x232BC, 0x10000)
        self.put(0x023D2F00, 0x023DCA99)
        self.flash = bytearray(b'\xff' * 0x80000)
        self.reads, self.flash_writes, self.owner_writes, self.delegates = [], [], [], []
        self.fail_address = self.on_read = self.on_delegate = None
        self.native_load_result = 1
        self.stack = self.low_sp = STACK
        self.u.hook_add(UC_HOOK_CODE, self.hook)
        self.u.hook_add(UC_HOOK_MEM_WRITE, self.write_hook)
        self.call(self.ts['training_shiny_bind'], SAVE, 1)
        self.u.mem_write(GENERATION, struct.pack('<4I', 0x31475554, 1, SAVE, 0))
        self.u.mem_write(OUT, b'\xa5' * 16)
        self.u.mem_write(PROOF, b'\xa5' * 52)
        self.u.mem_write(NEXT, bytes(16))
        self.owner_writes.clear()
        self.delegates.clear()

    def put(self, p, v):
        self.u.mem_write(p, struct.pack('<I', v))

    def get(self, p):
        return struct.unpack('<I', self.u.mem_read(p, 4))[0]

    def ret(self, value=0):
        self.u.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
        self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def write_hook(self, u, access, address, size, value, data):
        # Resident Training/Shiny/Plus, native save/Options, and ALL native
        # static RAM (includes gSystem and operational audio bookkeeping).
        ranges = ((0x023C0000, 0x023E0000), (SAVE, SAVE+0x2330C),
                  (OPTIONS, OPTIONS+4), (0x02000000, 0x0226EC40))
        if any(address < end and address + size > start for start, end in ranges):
            self.owner_writes.append((address, size, value))

    def hook(self, u, address, size, data):
        self.low_sp = min(self.low_sp, u.reg_read(UC_ARM_REG_SP))
        a, b, c, d = [u.reg_read(r) for r in REGS]
        if address == 0x0202877C:
            self.reads.append((a, c))
            if self.on_read:
                self.on_read(self, len(self.reads))
            if a == self.fail_address:
                self.ret(0)
            else:
                u.mem_write(b, bytes(self.flash[a:a+c]))
                self.ret(1)
        elif address == 0x02028758:
            self.flash_writes.append((a, bytes(u.mem_read(b, c))))
            self.ret(0)
        elif address == 0x02028EA8:
            self.ret(OPTIONS)
        elif address == (self.ts['training_shiny_bind'] & ~1):
            self.delegates.append((a, b, self.get(GENERATION + 4), self.get(GENERATION + 8)))
        elif address == 0x023DCA98:
            self.delegates.append((a, b, self.get(GENERATION + 4), self.get(GENERATION + 8)))
            if self.on_delegate:
                self.on_delegate(self)
            self.ret(self.native_load_result)

    def call(self, address, *args):
        for index, reg in enumerate(REGS):
            self.u.reg_write(reg, args[index] if index < len(args) else 0)
        self.u.reg_write(UC_ARM_REG_SP, self.stack)
        self.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.u.emu_start(address | 1, STOP, count=1000000)
        assert self.u.reg_read(UC_ARM_REG_PC) == STOP, 'instruction bound'
        assert self.u.reg_read(UC_ARM_REG_SP) == self.stack, 'stack balance'
        return self.u.reg_read(UC_ARM_REG_R0)

    def ui(self, name, *args):
        return self.call(self.us['training_ui_' + name], *args)

    def peek(self):
        return self.ui('peek', FS, OUT, PROOF)

    def owner(self):
        return (bytes(self.u.mem_read(0x023C0000, 0x20000)) +
                bytes(self.u.mem_read(SAVE, 0x2330C)) +
                bytes(self.u.mem_read(OPTIONS, 4)) +
                bytes(self.u.mem_read(0x021D110C, 0x100)))

    def lease(self, sector):
        self.call(self.ts['training_owner_encode'], NEXT + 0x100)
        marker = bytes(self.u.mem_read(NEXT + 0x100, 32))
        self.flash[sector + 0x400:sector + 0x420] = marker
        return marker
