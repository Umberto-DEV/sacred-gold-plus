#!/usr/bin/env python3
"""Check Party register spans against an exact ROM and a private RAM checkpoint.

Run only after authenticating runtime, route and OFF/ON neutrality. CSV alone
cannot attest its producer. This validates the recorded relationships, never
emits memory contents, and makes no hardware timing or global lifetime claim.
"""
import argparse
from collections import Counter
import csv
import gzip
import json
from pathlib import Path
import struct
import sys

import ndspy.rom

sys.path.insert(0, str(Path(__file__).resolve().parent))
from attribuisci import check_identity, move_table, require, sha

ROOT, ATTR_SHIM, PP_SHIM, RECORD, ATTR, PP = (
    0x0221D184, 0x023DBEB4, 0x023DBEBE, 0x023DBE2C, 0x023DBE00, 0x023DBE7C)
NATIVE = (0x02073314, 0x0207332C)
CALL_ATTR = {0x0221D3DE: None, 0x0221D3E8: 3, 0x0221D3F2: 1,
             0x0221D3FC: 4, 0x0221D406: 2}
NONE = 0xFFFFFFFF


def verify(events, ram, table):
    """Require at least one complete five-getter scan with nonnull cache hits.

    Pure verifier: synthetic tests and real captured records use the same rules.
    Parent/order/frame/SP/ISA constraints precede data-value attribution. Native
    calls outside a Party constructor are counted separately, never cache hits.
    """
    require(len(ram) == 4194304 and len(table) == 7488, 'RAM/table extent')
    require(0 < len(events) <= 16384, 'event count outside Party profile budget')
    rows = [{k: int(v) for k, v in row.items()} for row in events]
    allowed = {ROOT, ATTR_SHIM, PP_SHIM, RECORD, ATTR, PP, *NATIVE}
    orders, children = set(), {i: [] for i in range(len(rows))}
    for i, e in enumerate(rows):
        require(e['event'] == i and e['site'] in allowed, 'event/site identity')
        require(e['complete'] == 1 and e['mode'] == 31 and
                e['entry_cpsr'] & 63 == 63 and e['exit_cpsr'] & 63 == 63,
                'incomplete/non-System-Thumb event')
        require(0 <= e['first_frame'] <= e['last_frame'] and
                0 < e['entry_order'] < e['exit_order'], 'event chronology')
        require(e['sp'] % 8 == 0, 'unaligned entry stack')
        require(not ({e['entry_order'], e['exit_order']} & orders), 'duplicate event order')
        orders.update((e['entry_order'], e['exit_order']))
        parent = e['parent']
        if parent != NONE:
            require(0 <= parent < i, 'parent must precede child')
            p = rows[parent]
            require(p['entry_order'] < e['entry_order'] < e['exit_order'] < p['exit_order']
                    and p['first_frame'] <= e['first_frame'] <= e['last_frame'] <= p['last_frame'],
                    'child outside parent span')
            children[parent].append(i)

    def word(address):
        off = address-0x02000000
        require(0 <= off <= len(ram)-4 and address % 4 == 0, 'context pointer outside RAM')
        return struct.unpack_from('<I', ram, off)[0]

    roots = [i for i,e in enumerate(rows) if e['site'] == ROOT]
    require(roots, 'no observed Party constructor')
    lrs, contexts, getters, records = Counter(), set(), 0, 0
    consumed = set(roots)
    for root_id in roots:
        root = rows[root_id]
        require(root['parent'] == NONE, 'unexpected Party constructor parent')
        app = root['arg0']; args = word(app); bs = word(args+8); ctx = word(bs+0x30)
        contexts.add((app,args,bs,ctx))
        offset = ctx + 0x3DE - 0x02000000
        require(0 <= offset <= len(ram)-len(table) and ram[offset:offset+len(table)] == table,
                'checkpoint MoveTbl does not match physical ROM table')
        counts = Counter()
        for shim_id in children[root_id]:
            shim = rows[shim_id]; site = shim['lr']-5
            require(site in CALL_ATTR and shim['sp'] == root['sp']-40,
                    'wrong caller LR/constructor stack frame')
            pp = CALL_ATTR[site] is None
            require(shim['site'] == (PP_SHIM if pp else ATTR_SHIM), 'wrong shim target')
            move, attr = shim['arg0'], shim['arg1']
            require(0 <= move < 468 and (pp or attr == CALL_ATTR[site]), 'unexpected move/attribute')
            require(len(children[shim_id]) == 1, 'shim must enter one cache getter')
            core_id = children[shim_id][0]; core = rows[core_id]
            require(core['site'] == (PP if pp else ATTR) and core['lr'] == shim['site']+9
                    and core['sp'] == shim['sp']-8 and core['arg2'] == app
                    and (core['arg0'],core['arg1']) == (move,attr), 'cache ABI/ancestry mismatch')
            require(len(children[core_id]) == 1, 'expected one record path and no native fallback')
            record_id = children[core_id][0]; rec = rows[record_id]
            require(rec['site'] == RECORD and rec['lr'] == core['site']+(13 if pp else 21)
                    and rec['sp'] == core['sp']-16
                    and (rec['arg0'],rec['arg1']) == (move,app)
                    and rec['result'] == ctx+0x3DE+16*move and not children[record_id],
                    'wrong cache record pointer/ABI')
            pp_base = table[16*move+6]
            expected = ((pp_base+pp_base*min(attr,3)//5)&255) if pp else table[16*move+attr+1]
            require(core['result'] == shim['result'] == expected, 'getter result differs from ROM data')
            consumed.update((shim_id,core_id,record_id))
            counts[site] += 1;lrs[site] += 1;getters += 1;records += 1
        require(set(counts) == set(CALL_ATTR) and len(set(counts.values())) == 1,
                'not a complete five-getter scan')
    remaining = [e for i,e in enumerate(rows) if i not in consumed]
    require(all(e['site'] in NATIVE for e in remaining), 'unattributed cache event outside Party scan')
    return {'constructors': len(roots), 'cached_getters': getters, 'record_hits': records,
            'calls_per_site': {hex(k):v for k,v in sorted(lrs.items())},
            'native_events_outside_scan': len(remaining), 'native_fallbacks_inside_scan': 0,
            'contexts': [{'app':a,'args':b,'battle_system':c,'battle_context':d} for a,b,c,d in sorted(contexts)],
            'constructor_frames': [[rows[i]['first_frame'],rows[i]['last_frame']] for i in roots],
            'limits': ['Requires external producer identity and OFF/ON neutrality.',
                       'RAM validates one endpoint; return values/record pointers are recorded at execution.',
                       'Runtime captures r4-r7 at entry only; preserved-register ABI is tested separately under Unicorn.',
                       'No global lifetime, timing, hardware or unexercised-mode claim.']}


def read(path):
    data = Path(path).read_bytes()
    return gzip.decompress(data) if str(path).endswith('.gz') else data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', required=True)
    p.add_argument('--language', choices=('EN','IT'), required=True)
    p.add_argument('--events', required=True, help='work-events.csv or lossless .gz')
    p.add_argument('--ram', required=True, help='active Party checkpoint, raw 4 MiB or .gz')
    p.add_argument('--json', type=Path)
    args = p.parse_args()
    try:
        raw = Path(args.rom).read_bytes(); identity = check_identity(raw,args.language)
        nds = ndspy.rom.NintendoDSRom(raw); _,table = move_table(nds.getFileByName('a/0/1/1'))
        events,ram = read(args.events),read(args.ram)
        result = verify(list(csv.DictReader(events.decode().splitlines())),ram,table)
        result.update(rom=identity,events_sha256=sha(events),ram_sha256=sha(ram))
        out = json.dumps(result,indent=2)+'\n'
        if args.json:
            with args.json.open('x') as f:f.write(out)
        print(out,end='')
        return 0
    except (ValueError,OSError,KeyError,struct.error) as exc:
        print('execution attribution rejected: %s' % exc,file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
