"""Actual historical owners + accepted Training extension; scratch-only gate.

Hardware READ/WRITE and native Options identity getter inherit the documented
Training bench seams. The gate below is real compiled, pure memory-only code,
checking realistic dirty native/Plus fields. It is NOT the future coordinator.
"""
from functools import lru_cache
import importlib.util
from pathlib import Path
import struct
import subprocess
import tempfile
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_CPSR

SOURCE = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('shiny_training_ui_bench', SOURCE / 'features/training-native/test/ui_bench.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
FLAGS, training, shiny, shiny_core = base.FLAGS, base.training, base.shiny, base.shiny_core
FS, SAVE, APP, OPTIONS = base.FS, base.SAVE, base.APP, base.OPTIONS
STATE, GENERATION, DESCRIPTOR = base.STATE, base.GENERATION, base.DESCRIPTOR
SHINY, ADMITTED, FLAGS_OFFSET = base.SHINY, base.ADMITTED, base.FLAGS_OFFSET
RT, EXT, GATE_CODE = 0x023CB200, 0x02202000, 0x02206000
# Real caller frame allocated from native initial SP; output locals above SP.
STACK, SNAP, DRAFT, TOKEN, GATE, CONTEXT = 0x027E3378, 0x027E3380, 0x027E33A0, 0x027E33C0, 0x027E3460, 0x027E3480
IME, PLUS, NATIVE = 0x04000208, 0x023D8700, OPTIONS
IRQ_QUERY = 0x020D3A90  # Even ARM entry, unlike Thumb owner capabilities.
# Test-authored pure ARM semantic boundary, not bytes extracted from a ROM.
# Native helper preimage pinning belongs to installer/Class B verification.
IRQ_QUERY_ASM = """
.syntax unified
.text
.arm
.global test_irq_query
.type test_irq_query,%function
test_irq_query:
    mrs r0,cpsr
    and r0,r0,#0x80
    bx lr
.size test_irq_query,.-test_irq_query
"""


@lru_cache(maxsize=1)
def irq_query_code():
    with tempfile.TemporaryDirectory(prefix='shiny-irq-query-') as temporary:
        source, obj = Path(temporary)/'query.s', Path(temporary)/'query.o'
        source.write_text(IRQ_QUERY_ASM)
        subprocess.run(['clang','--target=armv5te-none-eabi','-mcpu=arm946e-s',
                        '-c',str(source),'-o',str(obj)],check=True,capture_output=True)
        loader = training.module(SOURCE/'features/options/tools/carica_text.py','shiny_irq_loader')
        code, symbols = loader.load_text(obj.read_bytes(),IRQ_QUERY)
        assert symbols['test_irq_query']==IRQ_QUERY
        return code

GATE_SOURCE = r'''
typedef unsigned int u32;
typedef struct {u32 app,generation,native,plus;} Context;
u32 settings_final_check(const Context *c) {
 u32 a=(u32)c;
 if((a&3)||!((a>=0x0226EC40u&&a<=0x023C0000u-16)||
            (a>=0x027E0080u&&a<=0x027E3780u-16)))return 0;
 if(c->app!=0x022D0000u)return 0;
 return *(volatile u32 *)(c->app+0x28)==c->generation&&
        *(volatile u32 *)(c->app+0x2c)==0x31495553u&&
        *(volatile u32 *)0x022A0110u==c->native&&
        *(volatile u32 *)0x023D8700u==c->plus;
}
'''


def compile_all(directory):
    old, ts = training.compile_native(directory / 'historical')
    te, us = base.compile_object(SOURCE / 'features/training-native/ui_transaction.c', directory / 'training-ui.o',
                                ['-DSGP_SETTINGS_UI_SUCCESSOR=1'])
    core, cs = shiny_core.compile_native(directory / 'core')
    native, ns = shiny.compile_native(directory / 'native', 'native')
    gate_file = directory / 'gate.c'
    gate_file.write_text(GATE_SOURCE)
    loader = training.module(SOURCE / 'features/options/tools/carica_text.py', 'shiny_ui_loader')
    base.compile_object(gate_file, directory / 'gate.o')
    gate, gs = loader.load_text((directory / 'gate.o').read_bytes(), GATE_CODE)
    base.compile_object(SOURCE / 'features/shiny/ui_transaction.c', directory / 'ui.o',
                        ['-DSGP_SETTINGS_UI_SUCCESSOR=1', f'-DSGP_SETTINGS_UI_FINAL_CHECK={gs["settings_final_check"]}', '-fstack-usage'])
    extension, symbols = loader.load_text((directory / 'ui.o').read_bytes(), EXT)
    return (old, ts, te, us, core, cs, native, ns), extension, symbols, gate, gs


class Bench(base.Bench):
    def __init__(self, compiled, leased=True):
        self.active = False
        super().__init__(compiled[0])
        # Explicit native SYSTEM mode with CPU IRQ enabled. Keep other masks
        # (including FIQ) unchanged; this is setup, not a product-side policy.
        self.u.reg_write(UC_ARM_REG_CPSR,(self.u.reg_read(UC_ARM_REG_CPSR)&~0x9F)|0x1F)
        self.u.mem_write(IRQ_QUERY,irq_query_code())
        self.symbols, self.gs = compiled[2], compiled[4]
        self.u.mem_write(EXT, compiled[1])
        self.u.mem_write(GATE_CODE, compiled[3])
        self.u.mem_map(0x04000000, 0x1000)
        self.put(IME, 1)
        self.put(APP+0x28, 9)
        self.put(APP+0x2C, 0x31495553)
        self.u.mem_write(RT, struct.pack('<7I', 0x594E4853, 3, 7, 11, FS, SAVE, OPTIONS))
        self.put(FS+0x20, FS+0x100)
        self.put(FS+0x100, 60)
        self.put(RT+28, 1)
        self.put(RT+32, 60)
        self.u.mem_write(RT+48, bytes([40, 0, 0, 0, 1, 1, 0, 0, 0]))
        self.u.mem_write(RT+60, struct.pack('<H', 25))
        self.u.mem_write(RT+84, struct.pack('<H', 25))
        self.u.mem_write(SHINY, struct.pack('<IHBBB7s', 123, 25, 20, 1, 1, bytes(7)))
        for i, n in enumerate(('peek', 'prepare', 'commit')):
            self.put(DESCRIPTOR+16+4*i, self.symbols['sgp_shiny_ui_'+n])
        self.stack = self.low_sp = STACK
        self.u.mem_write(SNAP, b'\xA5'*32)
        self.u.mem_write(TOKEN, b'\xA5'*152)
        self.u.mem_write(GATE, struct.pack('<HHII', 1, 12, self.gs['settings_final_check'], CONTEXT))
        self.u.mem_write(CONTEXT, struct.pack('<4I', APP, 9, self.get(NATIVE), self.get(PLUS)))
        self.canaries = ((0x027E0000, 0x80), (0x027E3780, 0x880))
        for p,n in self.canaries:
            self.u.mem_write(p, b'\x5A'*n)
        if leased:
            self.lease(0x31000)
            self.lease(0x71000)
        self.reads.clear()
        self.owner_writes.clear()
        self.all_writes, self.ime_writes, self.gate_calls, self.masked_io = [], [], [], []
        self.before_lock = self.on_store = None
        self.lock_injected = False
        self.active = True
        self.u.hook_add(UC_HOOK_MEM_READ, self.read_hook, begin=IME, end=IME+3)

    def read_hook(self, u, access, address, size, value, data):
        if address == IME and self.before_lock and self.reads and not self.lock_injected:
            self.lock_injected = True
            self.before_lock(self)

    def write_hook(self, u, access, address, size, value, data):
        super().write_hook(u, access, address, size, value, data)
        if self.active:
            self.all_writes.append((address, size, value))
            if address == IME:
                self.ime_writes.append(value)
            if self.owner_writes and self.owner_writes[-1] == (address, size, value) and self.on_store:
                self.on_store(self)

    def hook(self, u, address, size, data):
        if self.active:
            if address in (0x0202877C, 0x02028758) and (not self.get(IME) or (u.reg_read(UC_ARM_REG_CPSR)&0x80)):
                self.masked_io.append(address)
            if address == (self.gs['settings_final_check'] & ~1):
                self.gate_calls.append((len(self.reads), self.get(IME)))
        super().hook(u, address, size, data)

    def shiny_ui(self, name, *args):
        return self.call(self.symbols['sgp_shiny_ui_'+name], *args)

    def peek(self, out=SNAP):
        return self.shiny_ui('peek', APP, out)

    def draft(self, mode=1, target=25, method=0, search=0):
        self.u.mem_write(DRAFT, struct.pack('<IIIHBBB3s', 3, 11, 7, target, mode, method, search, bytes(3)))

    def prepare(self):
        return self.shiny_ui('prepare', APP, SNAP, DRAFT, TOKEN)

    def commit(self, token=TOKEN, gate=GATE):
        return self.shiny_ui('commit', APP, token, gate)

    def reset_trace(self):
        self.owner_writes.clear()
        self.all_writes.clear()
        self.reads.clear()
        self.gate_calls.clear()
        self.ime_writes.clear()
        self.low_sp = self.stack
