"""Functional oracle for actual game-executed lease markers and heap topology."""
import struct

MARKER_ADDRESS = 0x01FF9F00
MARKER_WORDS = 16
MAGIC = 0x4C534531


def require(value, message):
    if not value:
        raise ValueError(message)


def markers(itcm, cycles):
    require(len(itcm) == 32768, 'Wrong ITCM observation size')
    values = struct.unpack_from('<16I', itcm, MARKER_ADDRESS & 0x7FFF)
    names = ['magic', 'cycles', 'allocations', 'frees', 'null_failures', 'noop_cleanups',
             'errors', 'live_context', 'verified_words', 'first_address', 'heap', 'summary',
             'counter_before', 'counter_after', 'lease_bytes', 'last_address']
    result = dict(zip(names, values))
    require(result['magic'] == MAGIC, 'Missing game-executed lease result')
    expected = {'cycles':cycles, 'allocations':cycles, 'frees':cycles, 'null_failures':cycles,
                'noop_cleanups':cycles*2, 'errors':0, 'live_context':0,
                'verified_words':cycles*2*(22528//4), 'lease_bytes':22528}
    for name, value in expected.items():
        require(result[name] == value, f'Lease {name}: expected {value}, got {result[name]}')
    require(result['counter_before'] == result['counter_after'], 'Wrapper allocation counter changed')
    require(result['first_address'] % 4 == result['last_address'] % 4 == 0, 'Lease misaligned')
    return result


def state(ram):
    require(len(ram) == 0x400000, 'Wrong MainRAM observation size')
    def view(a, n):
        require(0x02000000 <= a <= 0x02400000-n, 'Pointer outside MainRAM')
        return ram[a-0x02000000:a-0x02000000+n]
    def word(a): return struct.unpack('<I', view(a,4))[0]
    def half(a): return struct.unpack('<H',view(a,2))[0]
    handles, counters, indices = word(0x021D1584), word(0x021D1590), word(0x021D1594)
    index = view(indices+19,1)[0]
    heap = word(handles+4*index)
    require(word(heap) == 0x45585048, 'Not an expanded heap')
    start, end = word(heap+0x18), word(heap+0x1c)
    lists = {}
    for name, offset, signature in [('free',0x24,0x4652),('used',0x2c,0x5544)]:
        node, tail, previous, seen, blocks = word(heap+offset), word(heap+offset+4), 0, set(), []
        while node:
            require(node not in seen and start <= node < end-16 and node%4 == 0, 'Bad heap node')
            seen.add(node)
            require(half(node)==signature and word(node+8)==previous, 'Bad heap link/signature')
            size = word(node+4)
            require(node+16+size <= end, 'Heap block exceeds extent')
            blocks.append([node,view(node,16).hex()])
            previous, node = node, word(node+12)
        require(previous == tail, 'Bad heap tail')
        lists[name]=blocks
    summary = word(0x021D1110)
    require(word(0x021D110C) == 0x020885DD, 'Not in real Summary')
    args=word(summary+0x22c)
    return {'heap':heap,'heap_header':view(heap,0x38).hex(), 'lists':lists,
            'counter':half(counters+19*2), 'summary':summary,
            'callback':view(0x021D110C,8).hex(), 'args':view(args,0x20).hex(),
            'page':view(summary+0x7bc,1).hex(), 'windows':view(summary+4,34*16).hex(),
            'page_windows':view(word(summary+0x224),word(summary+0x228)*16).hex(),
            'bg_config':view(word(summary),0x168).hex()}
