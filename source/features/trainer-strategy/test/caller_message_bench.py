"""Authenticated caller adapter and unchanged constructor-only replay guards.

The parent caller/bench sources stay untouched. The two pure blocks below are
literal AST copies of the qualified caller guards, authenticated before use.
"""
import ast,hashlib,struct,copy
from pathlib import Path
U=None
PARENT_SHA256='43f326704dcc3a85e4c888cbb3c3de9c972b88d8e3fb65e0cc98073402f3fa83'

def demand(ok,reason):
 if not ok:raise ValueError(reason)
def digest(blob):return hashlib.sha256(blob).hexdigest()

def bind(caller):
 global U,B,T,P,Q,INNER,sha,need
 demand(digest(Path(caller.__file__).read_bytes())==PARENT_SHA256,'message caller parent source drift')
 original={n.name:n for n in ast.parse(Path(caller.__file__).read_text()).body if isinstance(n,ast.FunctionDef)}
 source={n.name:n for n in ast.parse(Path(__file__).read_text()).body if isinstance(n,ast.FunctionDef)}
 first=original['require_case'].body
 start=next(i for i,n in enumerate(first) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
 end=next(i for i,n in enumerate(first) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require_evidence')
 second=original['require_evidence'].body
 end2=next(i for i,n in enumerate(second) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='string' for t in n.targets))
 blocks=(first[start:end],second[1:end2]);demand(tuple(map(len,blocks))==(20,28),'message caller finite oracle block sizes')
 templates=('def constructor_result(r,data,qualified):\n returned=r["ctor_return"]\n return True\n','def constructor_evidence(r,all_data,qualified):\n want=T.expected(all_data["constructor"],r["plus"])\n return True\n')
 hashes=[]
 for old,template in zip(blocks,templates):
  expected=ast.parse(template).body[0];expected.body=expected.body[:1]+copy.deepcopy(old)+expected.body[-1:];actual=source[expected.name]
  demand(ast.dump(expected,include_attributes=False)==ast.dump(actual,include_attributes=False),'message caller complete oracle function/signature/wrapper drift');new=actual.body[1:-1]
  before=ast.dump(ast.Module(body=old,type_ignores=[]),include_attributes=False);after=ast.dump(ast.Module(body=new,type_ignores=[]),include_attributes=False)
  demand(before==after,'message caller copied constructor oracle AST drift');hashes.append(digest(before.encode()))
 U=caller;B,T,P,Q,INNER,sha,need=U.B,U.T,U.P,U.Q,U.INNER,U.sha,U.need
 return dict(parent_sha256=PARENT_SHA256,constructor_guard_block_sha256=hashes,all_copied_AST_unchanged=True,complete_wrappers_authenticated=True)

def adapt(bench,driver):
 oracle=bind(driver.parent);run,proof=U.A.adapt(bench,driver);old=dict(run.__globals__['STUBS']);extra={0x200BAF8:'CallerNewMsgData',0x200BBA0:'CallerNewString',0x200BB44:'CallerDestroyMsgData'}
 demand(old=={**bench.STUBS,**extra},'message caller inherited SDK stubs drift');run.__globals__['STUBS']=dict(bench.STUBS)
 demand(set(old)-set(run.__globals__['STUBS'])==set(extra) and all(run.__globals__['STUBS'][k]==v for k,v in bench.STUBS.items()),'message caller exact three high-level stub removals')
 return run,dict(schema='native-message-caller-adapter-v1',inherited=proof,effective_sdk={hex(k):v for k,v in bench.STUBS.items()},removed_high_level_sdk={hex(k):v for k,v in extra.items()},constructor_oracle=oracle,isolated_namespace_only=True)

def constructor_result(r, data, qualified):
    returned = r['ctor_return']
    body = r['body']
    need(body is not None and body['end'] == returned and (body['header'] == r['header'] == [6, 6]) and (body['mon_hex'] == r['mon_hex']) and (len(r['mon_hex']) == len(r['decoded']) == 6), 'one native complete party through caller return')
    want = T.expected(data['constructor'], r['plus'])
    need(body['seed_after'] == r['seed'] and body['plus_hits'] == r['plus_hits'] == 6 and (not body['live']) and (not body['handles']) and body['canaries'] and body['unrelated_ram_unchanged'] and (body['max_stack'] <= 512), 'constructor lifetime/seed/canary/stack bounds')
    need(body['reader_calls'] == body['unloads'] == 1 and body['prefix_transition']['buffer_hex'] == data['constructor']['record']['before'] and (body['prefix_transition']['seed'] == r['seed']) and body['prefix_transition']['observer_neutral'], 'native constructor raw prefix and neutral transition')
    party = bytes.fromhex(data['constructor']['record']['after']) if r['plus'] else data['constructor']['party']
    need(body['buffer_before_free'] == party.hex() and body['buffer_writes'] == ([dict(pc='0x23d619a', offset=i, bytes=1, value=v) for i, v in enumerate(party)] if r['plus'] else []), 'actual one-time strategy buffer commit')
    for packet, reported, record in zip(r['mon_hex'], r['decoded'], want):
        raw = bytes.fromhex(packet)
        need(len(raw) == 236, 'complete native packet width')
        decoded = T.M.decode(raw)
        need(decoded == reported and decoded['checksum_ok'], 'independent native packet decode/checksum')
        decoded['capsule_hex'] = B._decrypt(raw[136:], struct.unpack_from('<I', raw)[0])[76:100].hex()
        need(all((decoded[k] == v for k, v in record['fields'].items())), 'source-derived full native Pokemon fields')
    need(len(body['creation_inputs']) == len(body['pid_overrides']) == len(body['additions']) == 6 and len(body['seed_calls']) == 7 and (len(body['post_form_calls']) == 24), 'six native constructions/copies and helper groups')
    for record, create, pid, addition in zip(want, body['creation_inputs'], body['pid_overrides'], body['additions']):
        fields = record['fields']
        slot = record['slot']
        need(create['args'] == [B.ARENA + 128, fields['species'], fields['level'], record['iv']] and create['stack'] == [1, fields['pid'], 2, 0] and (create['sp'] == INNER - 152) and (create['lr'] == '0x2073a17'), 'actual nested-frame CreateMon arguments')
        need(pid['after_gender'] == record['pid_gender'] and pid['args'][3] == INNER - 152 + 124, 'actual native persistent PID state')
        need(addition == dict(count=slot + 1, sp=INNER - 152, mon_hex=r['mon_hex'][slot], party_slot_sha256=sha(bytes.fromhex(r['mon_hex'][slot]))), 'native six actual PartyAdd copies')
    for event, value in zip(body['seed_calls'], [x['class_seed'] for x in want] + [r['seed']]):
        need(event['args'][0] == event['result'][0] == event['after_seed'] == value, 'source-derived actual reseed and restoration')
    need([e['lr'] for e in body['seed_calls']] == ['0x20739c3'] * 6 + ['0x2073a95'], 'actual constructor reseed callers')
    for event in body['native_calls'] + body['post_form_calls'] + body['capsule_calls'] + body['pid_overrides'] + body['seed_calls'] + body['extra_calls']:
        need(event['sp'] == event['return_sp'] and event['saved'] == event['return_saved'] and (event['return_pc'] == int(event['lr'], 16) & ~1), 'all nested native helper return ABI')
    native = iter(body['native_calls'])
    consumed = 0

    def next_call():
        nonlocal consumed
        try:
            event = next(native)
        except StopIteration:
            raise ValueError('incomplete native constructor call sequence')
        consumed += 1
        return event
    for record in want:
        state = record['class_seed']
        fields = record['fields']
        slot = record['slot']
        for after in record['class_draws']:
            event = next_call()
            need(event['entry'] == '0x201fd44' and event['lr'] == '0x20739d3' and (event['before_seed'] == state) and (event['after_seed'] == after) and (event['result'][0] == after >> 16), 'actual complete class RNG draws')
            state = after
        event = next_call()
        need(event['entry'] == '0x206de38' and event['args'] == [B.ARENA + 128, fields['species'], fields['level'], record['iv']] and (event['lr'] == '0x2073a17'), 'actual native CreateMon caller')
        for i, after in enumerate(record['ot_draws']):
            event = next_call()
            need(event['entry'] == '0x201fd44' and event['lr'] == ('0x206df13' if i % 2 == 0 else '0x206df19') and (event['before_seed'] == state) and (event['after_seed'] == after) and (event['result'][0] == after >> 16), 'actual native anti-shiny OTID draws')
            state = after
        event = next_call()
        need(event['entry'] == '0x206ec40' and event['args'][:3] == [B.ARENA + 128, 6, B.ARENA + 18 * slot + 6] and (event['lr'] == '0x2073a23'), 'native held item source pointer')
        for move_slot, move in enumerate(fields['moves']):
            event = next_call()
            need(event['entry'] == '0x20714e8' and event['args'][:3] == [B.ARENA + 128, move, move_slot] and (event['lr'] == '0x2073a37'), 'all actual native move setters')
        for entry, lr in (('0x2072a44', '0x2073a4f'), ('0x206ec40', '0x2073a59'), ('0x2073ae4', '0x2073a5f'), ('0x2074524', '0x2073a69')):
            event = next_call()
            need(event['entry'] == entry and event['lr'] == lr, 'native capsule/form/postform/PartyAdd sequence')
            if entry == '0x2072a44':
                need(event['args'][:3] == [record['capsule'], B.ARENA + 128, 11] and event['result'][0] == int(record['capsule'] != 0), 'native capsule ID/BOOL')
            if entry == '0x2074524':
                need(event['args'][:2] == [B.PARTIES + 4096, B.ARENA + 128] and event['result'][0] == 1, 'actual native PartyAdd BOOL')
    need(consumed == len(body['native_calls']), 'no extra native constructor calls')
    need(len(body['capsule_calls']) == 2 and [x['lr'] for x in body['capsule_calls']] == ['0x2072a81', '0x2072a8b'] and (body['capsule_calls'][0]['value_hex'] == '01000000') and (body['capsule_calls'][1]['value_hex'] == want[-1]['fields']['capsule_hex']), 'actual capsule14 setters and raw slice')
    need(not body['game_shadows'], 'accepted installed constructor must have no game counter shadows')
    return True

def constructor_evidence(r, all_data, qualified):
    want = T.expected(all_data['constructor'], r['plus'])
    body, data = (r['body'], all_data['constructor'])
    prefix = r['prefix']
    extra = body['extra_calls']
    position = 0
    need(len(extra) == (37 if r['plus'] else 31), 'complete constructor extra observer count')

    def next_extra(entry):
        nonlocal position
        need(position < len(extra), 'missing extra helper')
        event = extra[position]
        position += 1
        need(event['entry'] == entry, 'extra native helper order')
        return event
    event = next_extra('0x20735f8')
    need(event['args'][0] == 72 and event['result'][0] == 0 and (event['return_pc'] == 34027088), 'native class-table consumer')
    for record in want:
        slot = record['slot']
        event = next_extra('0x20f2998')
        need(event['args'][:2] == [data['party'][18 * slot] * 31, 255] and event['result'][:2] == list(divmod(data['party'][18 * slot] * 31, 255)) and (event['return_pc'] == 34028022), 'native source difficulty/IV division')
        event = next_extra('0x23d602c')
        need(event['args'] == [B.ARENA, 31, 1539, r['plus']] and event['stack0'] == 37578240 and (event['result'][0] == int(r['plus'] == 1 and slot == 0)) and (event['return_pc'] == 37577244) and (event['slot'] == slot), 'native strategy/config/once-only core')
        event = next_extra('0x23d61c4')
        need(event['args'][:3] == [B.SETUP, 52, B.ARENA] and event['return_pc'] == 37577268 and (event['slot'] == slot), 'native strategy wrapper caller')
        if r['plus']:
            event = next_extra('0x23d8100')
            need(event['args'][:3] == [B.ARENA, 18, 6] and event['result'][0] == 29 and (event['return_pc'] == 37585258), 'native six-opponent maximum')
        event = next_extra('0x23d8134')
        need(event['args'][:3] == [record['base'], B.ARENA, 1539] and event['result'][0] == record['fields']['level'] and (event['return_pc'] == 37585324), 'inherited native level/table semantics')
        event = next_extra('0x23d6228')
        need(event['result'] == [B.ARENA + 128, record['fields']['species'], record['fields']['level'], record['iv'] << 24] and event['return_pc'] == 34028048 and (event['nzcv'] == 0), 'strategy hook actual live ABI/flags')
    need(position == len(extra), 'no extra unbound native helpers')
    for slot, record in enumerate(want):
        for event, entry, lr in zip(body['post_form_calls'][4 * slot:4 * slot + 4], ('0x20722d4', '0x206e250', '0x2071754', '0x206ec40'), ('0x2073aed', '0x2073af3', '0x2073afb', '0x2073b11')):
            need(event['entry'] == entry and event['lr'] == lr and (event['args'][0] == B.ARENA + 128), 'complete owned post-form native chain')
        has = body['post_form_calls'][4 * slot + 2]
        setter = body['post_form_calls'][4 * slot + 3]
        need(has['args'][1] == 218 and has['result'][0] == int(218 in record['fields']['moves']) and (setter['args'][1] == 9) and (setter['value_byte'] == record['fields']['friendship']), 'native move218/friendship source semantics')
        pid = body['pid_overrides'][slot]
        before_seed = r['seed'] if slot == 0 else want[slot - 1]['ot_draws'][-1]
        need(pid['args'] == [record['fields']['species'], 0, 0, INNER - 152 + 124] and pid['sp'] == INNER - 152 and (pid['lr'] == '0x20739ab') and (pid['before_gender'] == pid['after_gender'] == 136) and (pid['before_seed'] == pid['after_seed'] == before_seed), 'native PID source/previous state binding')
    need([event['args'][1] for event in body['capsule_calls']] == [162, 171] and all((event['args'][0] == B.ARENA + 128 for event in body['capsule_calls'])), 'native capsule setters attribute IDs')
    move_reads = [e for e in body['buffer_reads'] if e['pc'] == '0x2073a2c']
    need(move_reads == [dict(pc='0x2073a2c', offset=18 * i + 8 + 2 * j, bytes=2, value=record['fields']['moves'][j]) for i, record in enumerate(want) for j in range(4)], 'all24 native edited-buffer move loads')
    code = body['code']
    need(type(code) is list and len(code) > 0 and (len({e['ram'] for e in code}) == len(code)) and all((qualified['body_code'].get(int(e['ram'], 16)) == (e['bytes'], e['thumb']) for e in code)), 'constructor observed code must bind qualified instruction starts/width/ISA')
    pcs = {int(e['ram'], 16) for e in code}
    need({34027070, 34028044, 34004536, 34028082, 34030884, 34028176, 34028182, 37576748} <= pcs, 'constructor required body/strategy/return starts')
    prefix_models = body['prefix_models']
    need([e['name'] for e in prefix_models] == ['Heap_Alloc', 'Heap_Alloc'] + ['0x20d88c0'] * 4 + ['0x20d8a48', '0x20d8b6c', 'ReadWholeNarcMemberByIdPair', '0x20d88c0', '0x20d8db4'] and prefix_models[0]['args'][:2] == [11, 108] and (prefix_models[1]['args'][:2] == [11, 236]) and (prefix_models[8]['args'][:3] == [B.ARENA, 56, 31]), 'native prefix allocations/raw-reader/FS service order')
    need(body['critical'] == [dict(pc=hex(pc), address=hex(address), bytes=4, value=value) for pc, address, value in ((33583150, B.REGISTRY + 4, 1), (33583152, B.REGISTRY, 126), (37594082, 37593156, 1), (33582968, B.REGISTRY + 4, 0))] and [list(x) for x in r['overlay']['registry']] == [[126, 0]] + [[0, 0]] * 7, 'native overlay registry load/unload lifetime')
    live = {B.ARENA: 108, B.ARENA + 128: 236}
    handles = {}
    events = [['alloc', 11, 108, B.ARENA], ['alloc', 11, 236, B.ARENA + 128], ['read', 56, 31, B.ARENA, 108]]
    next_pointer = B.ARENA + 384
    for event in body['models']:
        kind, args = (event['name'], event['args'])
        need(event['sp'] == event['return_sp'] and event['saved'] == event['return_saved'] and ('result' in event), 'SDK modeled return ABI')
        if kind in ('Heap_Alloc', 'Heap_AllocAtEnd', 'GetSpeciesName'):
            pointer = event['result']
            need(pointer == event['pointer'] == next_pointer and pointer not in live and (pointer not in handles), 'unique sequential SDK allocation')
            image = B.pack_species_string(data['names'][str(args[0])]) if kind == 'GetSpeciesName' else bytes(args[1])
            need(event['bytes'] == len(image) and event['output_pointer'] == pointer and (event['output_sha256'] == sha(image)), 'modeled allocation image from raw species/name input')
            next_pointer += len(image) + 23 & ~7
            live[pointer] = len(image)
            events.append(['name', args[0], args[1], pointer] if kind == 'GetSpeciesName' else ['alloc', args[0], args[1], pointer])
        elif kind == 'Heap_Free':
            need(args[0] in live and live.pop(args[0]) == event['bytes'], 'single exact live SDK free')
            events.append(['free', args[0]])
        elif kind == 'ReadWholeNarcMemberByIdPair':
            need(args[1] in data['archives'], 'raw SDK archive domain')
            payload = data['archives'][args[1]][args[2]]
            need(event['bytes'] == len(payload) and event['sha256'] == event['output_sha256'] == sha(payload) and (event['output_pointer'] == args[0]), 'independent raw SDK readback')
            need(any((p <= args[0] and args[0] + len(payload) <= p + size for p, size in live.items())) or (args[0] == 35471900 and args[1] == 3 and (len(payload) == 404)) or (args[1] == 11 and len(payload) == 16 and (args[0] == event['sp']) and (event['return_pc'] == 34026272) and (INNER - 512 <= args[0]) and (args[0] + 16 <= INNER)), 'raw SDK read live destination')
            events.append(['read', args[1], args[2], args[0], len(payload)])
        elif kind == 'NARC_New':
            pointer = event['result']
            need(args[:2] == [185, 11] and pointer == event['pointer'] == next_pointer and (pointer not in live) and (not handles), 'capsule SDK opaque handle lifetime')
            next_pointer += 32
            handles[pointer] = 185
            events.append(['narc_new', 185, 11, pointer])
        elif kind == 'NARC_ReadFromMember':
            need(handles.get(args[0]) == 185 and args[1:] == [0, 312, 24] and (event['destination'] == event['output_pointer'] == event['sp'] + 8) and (event['output_sha256'] == sha(data['archives'][185][0][312:336])), 'raw capsule14 slice/handle/destination')
            events.append(['narc_read', 185, 0, 312, 24, event['destination']])
        elif kind == 'NARC_Delete':
            need(args[0] in handles, 'single live NARC delete')
            handles.pop(args[0])
            events.append(['narc_delete', args[0]])
        else:
            raise ValueError('unknown constructor SDK model event')
    need(not live and (not handles), 'reconstructed complete constructor SDK lifetime')
    need([list(e) for e in body['events']] == events and [list(e) for e in r['events']] == [['read', 55, 31, Q.LOCAL, 20]] + events, 'original SDK backend events match reconstructed ledger')
    return True
