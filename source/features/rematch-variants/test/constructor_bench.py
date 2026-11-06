"""Unicorn bench that runs the REAL trainer-party constructor (CreateNPCTrainerParty at
0x02073604) from the ARM9 bytes of a ROM image.

Real ARM code runs from the constructor entry down, including the four level hooks
(trainer-strategy and the Plus level function), the LCRNG, CreateMon with its
Pokemon encryption/stat code, SetMonData, the move/PP code and the party code. Only
the environment that cannot exist without the console is replaced; each stub logs its
arguments, so two runs are compared call by call:

  Heap_Alloc / Heap_AllocAtEnd / Heap_Free   bump arena (no heap descriptors exist here)
  ReadWholeNarcMemberByIdPair               copies the member of the ROM archive (id -> a/x/y/z)
  NARC_New / NARC_ReadFromMember / NARC_Delete   the same for the capsule table
  GetSpeciesName (0x0200BCDC)               builds a String from message bank 237 of the ROM

With the module installed as overlay 126 (`overlay=True`) the REAL HandleLoadOverlay / CanOverlayBeLoaded /
GetOverlayLoadDestination / UnloadOverlayByID bytes of the ROM run too, as in the memory proposal's loader_sim: only
the file-system layer is replaced and logged (FS_LoadOverlayInfo reads the ROM's y9 row, FS_LoadOverlayImage copies the
overlay file named by the ROM's FAT into its window or fails on request, FS_StartOverlay does nothing, FS_UnloadOverlay
poisons the window so a use after unload cannot go unnoticed), plus GF_AssertFail and the WFC overlay hook (counted).

The scratch addresses below are TEST-ONLY addresses in main RAM outside every ARM9
segment of the supported images; none of them is a build assignment.
"""
import hashlib
import itertools
import struct

import ndspy.narc
import ndspy.rom
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ_UNMAPPED, \
    UC_HOOK_MEM_WRITE_UNMAPPED, UC_HOOK_MEM_FETCH_UNMAPPED
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
                               UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                               UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR,
                               UC_ARM_REG_CPSR, UC_ARM_REG_PC)

R = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
     UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_R12]
SETUP, ARENA, ARENA_END = 0x02380000, 0x02200000, 0x02300000
PARTIES = 0x02310000          # one 0x1000 slot per enemy index
STACK_TOP, SENTINEL = 0x023BF000, 0x023BE000
ENTRY, SEAM_RESUME, PLUS_STATE = 0x02073604, 0x0207363E, 0x023D8700
LOADER_RESULT = 0x5EED0001     # returned by the stubbed archive reader, handed back by the wrapper
SENTINEL_REGS = {8: 0x88888801, 9: 0x99999902, 10: 0xAAAAAA03, 11: 0xBBBBBB04}
STACK_CANARY = bytes(range(1, 65)) * 2
STUBS = {0x0201AA8C: 'Heap_Alloc', 0x0201AACC: 'Heap_AllocAtEnd', 0x0201AB0C: 'Heap_Free',
         0x02007508: 'ReadWholeNarcMemberByIdPair', 0x0200BCDC: 'GetSpeciesName',
         0x02007688: 'NARC_New', 0x0200782C: 'NARC_ReadFromMember', 0x0200770C: 'NARC_Delete'}
PERMUTATIONS = list(itertools.permutations(range(4)))
REGISTRY, REGISTRY_BYTES = 0x021D0DF0, 64           # overlay registry of the MAIN region: 8 entries {id, active}
FS_INFO, FS_IMAGE, FS_START, FS_UNLOAD, GF_ASSERT, WFC_HOOK = 0x020D88C0, 0x020D8A48, 0x020D8B6C, 0x020D8DB4, 0x0202551C, 0x023DA3CC
POISON = 0xDD


class Archives:
    """Lazy access to ROM archives by path (shared between a ROM and its patched copies)."""

    def __init__(self, data):
        self.rom = ndspy.rom.NintendoDSRom(bytes(data))
        self.cache = {}

    def files(self, path):
        if path not in self.cache:
            self.cache[path] = ndspy.narc.NARC(self.rom.getFileByName(path)).files
        return self.cache[path]


def narc_path(narc_id):
    return 'a/%d/%d/%d' % (narc_id // 100, (narc_id // 10) % 10, narc_id % 10)


def _lcg(seed, count):
    out = []
    for _ in range(count):
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        out.append(seed >> 16)
    return out


def _decrypt(data, seed):
    words = struct.unpack('<%dH' % (len(data) // 2), data)
    return struct.pack('<%dH' % len(words), *[w ^ k for w, k in zip(words, _lcg(seed, len(words)))])


def decode_mon(mon):
    """Independent Gen IV decoder of a 236-byte Pokemon: identity, personality, stats, moves."""
    pid, _flags, checksum = struct.unpack_from('<IHH', mon, 0)
    blocks = _decrypt(mon[8:136], checksum)
    order = PERMUTATIONS[((pid >> 13) & 31) % 24]
    sub = {block: blocks[pos * 32:(pos + 1) * 32] for pos, block in enumerate(order)}
    recomputed = sum(struct.unpack('<64H', blocks)) & 0xFFFF
    a, b = sub[0], sub[1]
    ivs = struct.unpack_from('<I', b, 16)[0]
    party = _decrypt(mon[136:236], pid)
    status, level, capsule, hp, max_hp = struct.unpack_from('<IBBHH', party, 0)
    return {'pid': pid, 'checksum': checksum, 'checksum_ok': checksum == recomputed,
            'species': struct.unpack_from('<H', a, 0)[0], 'item': struct.unpack_from('<H', a, 2)[0],
            'friendship': a[0xC], 'ability': a[0xD], 'evs': list(a[0x10:0x16]),
            'moves': list(struct.unpack_from('<4H', b, 0)), 'pp': list(b[8:12]), 'pp_ups': list(b[12:16]),
            'ivs': [(ivs >> (5 * k)) & 31 for k in range(6)], 'gender': (b[24] >> 1) & 3, 'form': b[24] >> 3,
            'nature': pid % 25, 'level': level, 'hp': hp, 'max_hp': max_hp, 'status': status,
            'ball_capsule': capsule, 'nickname': list(struct.unpack_from('<11H', sub[2], 0))}


class Bench:
    def __init__(self, data, archives, language, watch=None, overlay=False):
        from sgp131 import rematches
        image = rematches._Image(data)
        self.segments = [(address, bytes(image.raw[offset:offset + size])) for address, offset, size in image.segmenti]
        self.archives, self.language, self.watch = archives, language, watch
        self.overlay = overlay
        self.rom = bytes(data) if overlay else None
        self.names = None
        del image

    def module_image(self, oid=126):
        """(window, file bytes) of the module's overlay in the installed ROM (the bench loads it where the real loader would)."""
        fat, _fs, y9, _ys = struct.unpack_from('<4I', self.rom, 0x48)
        row = struct.unpack_from('<8I', self.rom, y9 + 32 * oid)
        start, end = struct.unpack_from('<II', self.rom, fat + 8 * row[6])
        return row[1], bytes(self.rom[start:end])

    def call_function(self, address, args, writes=(), stack_top=STACK_TOP - 0x800, max_instructions=200_000):
        """Run one function of the image (e.g. rematch_native) on a fresh machine and return the Unicorn
        instance, so the caller can read memory. `writes` are (address, bytes) applied before the call. With the
        module installed as an overlay its image is placed at its window first."""
        cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        cpu.mem_map(0x01FF8000, 0x8000)
        cpu.mem_map(0x02000000, 0x400000)
        cpu.mem_map(0x027E0000, 0x1000)
        for start, blob in self.segments:
            cpu.mem_write(start, blob)
        if self.overlay:
            window, image = self.module_image()
            cpu.mem_write(window, image)
        cpu.mem_write(SENTINEL, b'\x70\x47')
        for start, blob in writes:
            cpu.mem_write(start, bytes(blob))
        for number, value in enumerate(args):
            cpu.reg_write(R[number], value)
        cpu.reg_write(UC_ARM_REG_SP, stack_top)
        cpu.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
        cpu.emu_start(address | 1, SENTINEL, count=max_instructions)
        return cpu

    def segment_bytes(self, address, size):
        """Bytes of the loaded ARM9 image (initial RAM contents) at an address."""
        for start, blob in self.segments:
            if start <= address and address + size <= start + len(blob):
                return blob[address - start:address - start + size]
        raise KeyError(hex(address))

    def species_name(self, species):
        if self.names is None:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'quality-audit'))
            import hgss_text
            self.names = (hgss_text, hgss_text.read_bank_raw(self.archives.files('a/0/2/7')[237]))
        text, bank = self.names
        return text.unpack_name(bank[species])[0]

    # ------------------------------------------------------------------ run
    def run(self, trainer, *, plus=1, battle_type=1, index=1, seed=0x12345678, buffer=None,
            trainer_data=None, other_trainers=(0, 0, 0, 0), max_instructions=3_000_000, load_ok=True, busy=()):
        """Construct the enemy party of `trainer` at enemy `index` and return everything observable."""
        cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        cpu.mem_map(0x01FF8000, 0x8000)
        cpu.mem_map(0x02000000, 0x400000)
        cpu.mem_map(0x027E0000, 0x1000)
        for address, blob in self.segments:
            cpu.mem_write(address, blob)
        events, handles, state = [], {}, {'arena': ARENA, 'wrapper_sp': [], 'resume': None, 'misalign': []}
        archives = self.archives
        reg = lambda uc, n: uc.reg_read(R[n])
        sp_of = lambda uc: uc.reg_read(UC_ARM_REG_SP)

        def log(uc, name, *args):
            if sp_of(uc) & 7:
                state['misalign'].append((name, sp_of(uc)))
            events.append((name,) + args)

        def alloc(uc):
            size, heap = reg(uc, 1), reg(uc, 0)
            pointer = state['arena']
            state['arena'] += (size + 0x17) & ~7
            assert state['arena'] <= ARENA_END, 'arena exhausted'
            cpu.mem_write(pointer, bytes(size))
            uc.reg_write(UC_ARM_REG_R0, pointer)
            log(uc, 'alloc', heap, size, pointer)

        def free(uc):
            log(uc, 'free', reg(uc, 0))

        def read_member(uc):
            destination, narc, member = reg(uc, 0), reg(uc, 1), reg(uc, 2)
            member_data = archives.files(narc_path(narc))[member]
            if narc == 56 and buffer is not None:
                member_data = buffer
            uc.mem_write(destination, bytes(member_data))
            uc.reg_write(UC_ARM_REG_R0, LOADER_RESULT)
            log(uc, 'read', narc, member, destination, len(member_data))

        def species_name(uc):
            species, heap = reg(uc, 0), reg(uc, 1)
            words = self.species_name(species)
            pointer = state['arena']
            state['arena'] += (8 + 2 * len(words) + 0x17) & ~7
            uc.mem_write(pointer, struct.pack('<HHI', len(words), len(words), 0xB6F8D2EC) +
                         struct.pack('<%dH' % len(words), *words))
            uc.reg_write(UC_ARM_REG_R0, pointer)
            log(uc, 'name', species, heap, pointer)

        def narc_new(uc):
            narc, heap = reg(uc, 0), reg(uc, 1)
            pointer = state['arena']
            state['arena'] += 0x20
            handles[pointer] = narc
            uc.reg_write(UC_ARM_REG_R0, pointer)
            log(uc, 'narc_new', narc, heap, pointer)

        def narc_read(uc):
            handle, member, offset, size = (reg(uc, n) for n in range(4))
            destination = struct.unpack('<I', bytes(uc.mem_read(sp_of(uc), 4)))[0]
            data = archives.files(narc_path(handles[handle]))[member][offset:offset + size]
            uc.mem_write(destination, bytes(data))
            log(uc, 'narc_read', handles[handle], member, offset, size, destination)

        def narc_delete(uc):
            log(uc, 'narc_delete', reg(uc, 0))

        implementations = {'Heap_Alloc': alloc, 'Heap_AllocAtEnd': alloc, 'Heap_Free': free,
                           'ReadWholeNarcMemberByIdPair': read_member, 'GetSpeciesName': species_name,
                           'NARC_New': narc_new, 'NARC_ReadFromMember': narc_read, 'NARC_Delete': narc_delete}
        for address, name in STUBS.items():
            cpu.mem_write(address, b'\x70\x47')                      # bx lr
            cpu.hook_add(UC_HOOK_CODE, lambda uc, a, s, user, fn=implementations[name]: fn(uc),
                         begin=address, end=address + 1)

        ovl = {'info': [], 'image': [], 'unload': [], 'assert': 0, 'wfc': 0, 'last': None, 'window': None}
        if self.overlay:
            fat, _fs, y9, _ys = struct.unpack_from('<4I', self.rom, 0x48)

            def give_back(uc):
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

            def fs_info(uc):
                oid = reg(uc, 2)
                row = struct.unpack_from('<8I', self.rom, y9 + 32 * oid)
                ovl['info'].append(oid)
                ovl['last'] = oid
                uc.mem_write(reg(uc, 0) + 4, struct.pack('<III', row[1], row[2], row[3]))
                uc.reg_write(UC_ARM_REG_R0, 1)
                give_back(uc)

            def fs_image(uc):
                oid = ovl['last']
                row = struct.unpack_from('<8I', self.rom, y9 + 32 * oid)
                start, end = struct.unpack_from('<II', self.rom, fat + 8 * row[6])
                ovl['image'].append((oid, bool(load_ok)))
                if load_ok:
                    uc.mem_write(row[1], bytes(self.rom[start:end]) + bytes(row[3]))
                    ovl['window'] = (row[1], row[2] + row[3])
                uc.reg_write(UC_ARM_REG_R0, 1 if load_ok else 0)
                give_back(uc)

            def fs_unload(uc):
                oid = reg(uc, 1)
                ovl['unload'].append(oid)
                row = struct.unpack_from('<8I', self.rom, y9 + 32 * oid)
                uc.mem_write(row[1], bytes([POISON]) * (row[2] + row[3]))
                uc.reg_write(UC_ARM_REG_R0, 1)
                give_back(uc)

            def counter(key):
                def hook(uc):
                    ovl[key] += 1
                    give_back(uc)
                return hook
            for address, fn in ((FS_INFO, fs_info), (FS_IMAGE, fs_image), (FS_START, give_back), (FS_UNLOAD, fs_unload),
                                (GF_ASSERT, counter('assert')), (WFC_HOOK, counter('wfc'))):
                cpu.hook_add(UC_HOOK_CODE, lambda uc, a, s_, user, fn=fn: fn(uc), begin=address, end=address)
            for oid in busy:                                    # overlays already live: the loader must refuse the window
                cpu.mem_write(REGISTRY + 8 * list(busy).index(oid), struct.pack('<II', oid, 1))

        def stack_write(uc, access, address, size, value, user):
            if state.get('in_seam') and address < state.get('seam_low', 1 << 32):
                state['seam_low'] = address              # lowest stack word written between the seam BL and its return
        cpu.hook_add(UC_HOOK_MEM_WRITE, stack_write, begin=STACK_TOP - 0x2000, end=STACK_TOP)
        cpu.hook_add(UC_HOOK_CODE, lambda uc, a, s_, user: state.update(in_seam=True), begin=0x0207363A, end=0x0207363A)
        cpu.hook_add(UC_HOOK_CODE, lambda uc, a, s_, user: state.update(in_seam=False), begin=SEAM_RESUME, end=SEAM_RESUME)

        def resume(uc, address, size, user):
            if state['resume'] is None:
                state['resume'] = {'r': [uc.reg_read(r) for r in R], 'sp': sp_of(uc),
                                   'flags': uc.reg_read(UC_ARM_REG_CPSR) >> 28}
        cpu.hook_add(UC_HOOK_CODE, resume, begin=SEAM_RESUME, end=SEAM_RESUME + 1)
        if self.watch:
            def watched(uc, address, size, user):
                state['wrapper_sp'].append(sp_of(uc))
            cpu.hook_add(UC_HOOK_CODE, watched, begin=self.watch[0], end=self.watch[1] - 1)

        def unmapped(uc, access, address, size, value, user):
            raise RuntimeError('unmapped access %#x (type %d) at pc stack' % (address, access))
        cpu.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED | UC_HOOK_MEM_FETCH_UNMAPPED, unmapped)

        cpu.mem_write(SENTINEL, b'\x70\x47')
        # Plus option state: [0] active_plus, [2] level cap (as in the existing trainer-hook bench)
        state_bytes = bytearray(32)
        state_bytes[0], state_bytes[2] = plus, 100
        cpu.mem_write(PLUS_STATE, bytes(state_bytes))
        # BattleSetup: battleType, party pointers, trainer ids, 52-byte trainer data records
        cpu.mem_write(SETUP, bytes(0x400))
        cpu.mem_write(SETUP, struct.pack('<I', battle_type))
        for slot in range(4):
            cpu.mem_write(SETUP + 4 + slot * 4, struct.pack('<I', PARTIES + slot * 0x1000))
        header = trainer_data if trainer_data is not None else archives.files('a/0/5/5')[trainer]
        cpu.mem_write(SETUP + 0x18 + index * 4, struct.pack('<I', trainer))
        cpu.mem_write(SETUP + 0x28 + index * 52, bytes(header))
        for slot, other in enumerate(other_trainers):
            if slot != index and other:
                cpu.mem_write(SETUP + 0x18 + slot * 4, struct.pack('<I', other))
                cpu.mem_write(SETUP + 0x28 + slot * 52, bytes(archives.files('a/0/5/5')[other]))
        cpu.mem_write(STACK_TOP, STACK_CANARY)

        def call(address, *args, count=max_instructions):
            for n, value in enumerate(args):
                cpu.reg_write(R[n], value)
            cpu.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
            cpu.emu_start(address | 1, SENTINEL, count=count)
            return cpu.reg_read(UC_ARM_REG_R0)

        cpu.reg_write(UC_ARM_REG_SP, STACK_TOP)
        call(0x0201FD38, seed)                                        # SetLCRNGSeed
        for number, value in SENTINEL_REGS.items():
            cpu.reg_write(R[number], value)
        cpu.reg_write(UC_ARM_REG_SP, STACK_TOP)
        for n, value in enumerate((SETUP, index, 11)):
            cpu.reg_write(R[n], value)
        cpu.reg_write(UC_ARM_REG_LR, SENTINEL | 1)
        cpu.emu_start(ENTRY | 1, SENTINEL, count=max_instructions)
        end = {'r': [cpu.reg_read(r) for r in R], 'sp': sp_of(cpu)}
        seed_after = call(0x0201FD2C)                                 # GetLCRNGSeed
        party_address = PARTIES + index * 0x1000
        count, size = struct.unpack('<II', bytes(cpu.mem_read(party_address, 8)))
        mons = [bytes(cpu.mem_read(party_address + 8 + n * 0xEC, 0xEC)) for n in range(min(size, 6))]
        ram = bytes(cpu.mem_read(0x02000000, 0x400000))
        resume_state = state['resume']
        return {'events': events, 'mons': mons, 'decoded': [decode_mon(m) for m in mons], 'seed_after': seed_after,
                'seed_before': seed, 'resume': resume_state, 'end': end, 'misalign': state['misalign'],
                'wrapper_sp': state['wrapper_sp'], 'stack_canary': bytes(cpu.mem_read(STACK_TOP, 128)) == STACK_CANARY,
                'party_header': (count, size), 'ram': ram, 'seam_low': state.get('seam_low'),
                'overlay': dict(ovl, registry=[struct.unpack_from('<II', ram, REGISTRY - 0x02000000 + 8 * k) for k in range(8)])}


PAGE = 0x10000


def ram_pages(run, skip=()):
    """sha256 of every 64 KiB page of main RAM, with the given [start, end) ranges zeroed first."""
    ram = bytearray(run['ram'])
    for start, end in skip:
        ram[start - 0x02000000:end - 0x02000000] = bytes(end - start)
    return [hashlib.sha256(ram[o:o + PAGE]).hexdigest() for o in range(0, len(ram), PAGE)]


def compare_runs(patched, oracle, skip):
    """Return a list of human-readable differences between two runs (empty = equivalent)."""
    problems = []
    for key in ('events', 'mons', 'seed_after', 'party_header', 'stack_canary'):
        if patched[key] != oracle[key]:
            problems.append(f'{key} differs')
    a, b = patched['resume'], oracle['resume']
    if a is None or b is None:
        problems.append('resume point 0x0207363E not reached')
    else:
        if a['r'][0] != b['r'][0] or a['r'][4:12] != b['r'][4:12] or a['sp'] != b['sp']:
            problems.append(f'registers at resume differ: {a} vs {b}')
        if a['r'][8:12] != [SENTINEL_REGS[n] for n in range(8, 12)]:
            problems.append('r8-r11 sentinels lost')
    abi = lambda run: (run['end']['r'][0], run['end']['r'][4:12], run['end']['sp'])
    if abi(patched) != abi(oracle):
        problems.append('final r0, r4-r11 or SP differ')
    if patched['misalign'] or oracle['misalign']:
        problems.append(f'SP misaligned at a call: {patched["misalign"][:2]}')
    sp = (oracle['resume'] or patched['resume'] or {'sp': STACK_TOP})['sp']
    window = [(sp - 0x2000, sp)]
    pages_a, pages_b = ram_pages(patched, list(skip) + window), ram_pages(oracle, list(skip) + window)
    differing = [hex(0x02000000 + i * PAGE) for i, (x, y) in enumerate(zip(pages_a, pages_b)) if x != y]
    if differing:
        problems.append(f'RAM pages differ: {differing}')
    return problems
