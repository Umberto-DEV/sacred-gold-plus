#!/usr/bin/env python3
"""Freeze actual P78 stopped inputs and keep a declared flag projection separate.

The parent records an actual whole AFTER hash, not a RAM blob. Reconstruct and
authenticate that image before adding the new gate or deriving deeper bytes.
"""
from pathlib import Path
import argparse,copy,importlib.util,json,struct

path=Path(__file__).with_name('congela_fs_default_findpath_contract.py')
s=importlib.util.spec_from_file_location('nested_seekdir_parent_freezer',path)
P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
need,sha,wire,read_report=P.need,P.sha,P.wire,P.read_report
need(sha(path.read_bytes())=='65602cee711d13da912a12f597fc81fb054540bc61492103c86335ec1ef31e9e','Nested SEEKDIR qualified exporter drift')
TOP,FILE,ARC=P.TOP,P.FILE,P.ARC
ENTRY=0x20D68C0


def u32s(value):
    return type(value)is list and len(value)==16 and all(type(x)is int and 0<=x<2**32 for x in value)


def after_state(row):
    need(row['observe']is True and row['fault']is None and wire(row['policy'])==wire(dict(prepush=False,lower_fill=None))and
         row['services']==row['model_stores']==row['host_stores']==[],'Nested SEEKDIR actual zero-model parent')
    cp=row['checkpoints']['nested_translate_entry']
    need(u32s(row['entry'])and u32s(row['returned'])and wire(cp['regs'])==wire(row['returned'])==wire(row['halt_regs'])and
         cp['pc']==row['halt_pc']==row['stop']==hex(ENTRY),'Nested SEEKDIR actual stopped full16')
    need(len(row['flow'])==7 and row['steps']==8 and len(row['stores'])==9 and len(row['reads'])==2 and
         [e['pc']for e in row['flow']]==[hex(x)for x in range(0x20D6DB0,0x20D6DCC,4)],'Nested SEEKDIR complete prefix7')
    frame=bytearray.fromhex(row['frame_before']);archive=bytes.fromhex(row['archive_before']);guard=bytes.fromhex(row['guard_after'])
    need(len(frame)==520 and len(archive)==92 and len(guard)==56 and row['guard_before']==row['guard_after'],
         'Nested SEEKDIR captured parent windows')
    for j,(w,index)in enumerate(zip(row['stores'],(3,4,5,6,7,8,9,10,14))):
        offset=148+4*j
        need(w['pc']=='0x20d6db0'and w['address']==TOP-372+4*j and w['bytes']==4 and
             w['before']==frame[offset:offset+4].hex()and type(w['value'])is int and w['value']==row['entry'][index],
             'Nested SEEKDIR actual native saved-word journal')
        struct.pack_into('<I',frame,offset,w['value'])
    need(frame.hex()==row['frame_after']==cp['frame']and archive.hex()==row['archive_after']==cp['archive'],
         'Nested SEEKDIR forward native prefix reaches actual stop windows')
    result=list(row['entry']);result[13]-=184;result[9]=FILE;result[1]=2;result[14]=0x20D6DCC
    for field,pc,reg in((60,'0x20d6dbc',5),(64,'0x20d6dc4',6)):
        offset=FILE-(TOP-520)+field;blob=bytes(frame[offset:offset+4]);result[reg]=int.from_bytes(blob,'little')
        need(row['reads'][0 if reg==5 else 1]==dict(pc=pc,address=FILE+field,bytes=4,hex=blob.hex()),
             'Nested SEEKDIR actual two field loads')
    need(wire(result)==wire(row['returned'])and result[:2]==[FILE,2]and result[13:16]==[TOP-520,0x20D6DCC,0x6000001F],
         'Nested SEEKDIR native BL delivery, not FSResult or stored command')
    need(struct.unpack_from('<3I',frame,FILE-(TOP-520)+12)==(0x45,4,2)and struct.unpack_from('<I',archive,28)[0]==0x213,
         'Nested SEEKDIR stored command4 and active outer Translate')
    digest=row['whole_ram_sha256'];need(type(digest)is str and len(digest)==64 and all(c in'0123456789abcdef'for c in digest),
                                      'Nested SEEKDIR actual whole AFTER hash')
    return dict(entry=result,captured_frame520_sha256=sha(frame),captured_archive92_sha256=sha(archive),captured_guard56_sha256=sha(guard),
        promoted_guard24_sha256=sha(guard[-24:]),retained_guard32_sha256=sha(guard[:32]),actual_after_whole_sha256=digest,
        observed_before_whole_sha256=row['before_whole_ram_sha256'],parent_native_stores_sha256=sha(wire(row['stores']).encode()),
        whole_hash_observed_at_stop=True,whole_RAM_blob_available=False)


def freeze(parent_report):
    r=read_report(parent_report)
    need(r['schema']=='native-fs-default-findpath-prefix-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
         r['probe_only']is False and len(r['fixtures'])==16 and len(r['groups'])==2 and len(r['cases'])==7 and
         len(r['field_holdout'])==56 and len(r['observer_off'])==2 and len(r['counters'])==2 and len(r['lower_fill_controls'])==1,
         'Nested SEEKDIR complete parent campaign')
    cells=[];seen=set()
    for f in r['fixtures']:
        identity=tuple(f[k]for k in('language','ordinal','plus','seed'))
        need(f['language']in('EN','IT')and all(type(f[k])is int for k in('ordinal','plus','seed'))and identity not in seen,
             'Nested SEEKDIR unique typed parent origin');seen.add(identity)
        g,row=P.P.group_row(r,f)
        cells.append(dict(language=f['language'],ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],parent_group=g['ordinal'],
                          parent_default_fixture_sha256=sha(wire(f).encode()),input=after_state(row)))
    return dict(schema='native-fs-nested-seekdir-prospective-input-v1',cells=cells,parent_report_sha256=sha(parent_report.read_bytes()),
        chronology='Before new dispatch oracle/guest; source and prior raw known, not blind',
        comparison='Actual full16/frame520/archive92/guard56/whole AFTER anchor; flag projection must fail strict actual-input comparison',
        limits=['New frame544 promotes captured guard24; only24 new guard bytes are whole-derived',
                'Parent whole AFTER hash is observed; its RAM blob must be reconstructed and authenticated',
                'No previous native dispatch output exists; activation/output need separate source/raw checks'])


def compare_input(cell,f,row):
    for key in('language','ordinal','plus','seed'):
        need(type(cell[key])is type(f[key])and cell[key]==f[key],'Nested SEEKDIR frozen origin')
    inp=cell['input']
    need(cell['parent_default_fixture_sha256']==sha(wire(f['parent_default_fixture']).encode())and
         f['observed_parent_after_whole_sha256']==inp['actual_after_whole_sha256']and
         sha(wire(f['parent_native_stores']).encode())==inp['parent_native_stores_sha256'],
         'Nested SEEKDIR original fixture and actual whole AFTER anchor')
    need(wire(row['entry'])==wire(f['entry'])==wire(inp['entry'])and u32s(row['entry']),'Nested SEEKDIR frozen full16 input')
    frame,guard=bytes.fromhex(row['frame_before']),bytes.fromhex(row['guard_before'])
    need(len(frame)==544 and len(guard)==56 and sha(frame[24:])==inp['captured_frame520_sha256']and
         sha(frame[:24])==inp['promoted_guard24_sha256']and sha(guard[24:])==inp['retained_guard32_sha256'],
         'Nested SEEKDIR captured frame and promoted guard, no invented stack fill')
    need(sha(bytes.fromhex(row['archive_before']))==inp['captured_archive92_sha256'],'Nested SEEKDIR actual captured archive')
    return dict(passed=True,actual_parent_input=True,input_registers=16,captured_frame_bytes=520,captured_guard_bytes=56,
                newly_derived_guard_bytes=24,output_or_activation_proved_here=False)


def compare_projection(cell,f,row):
    need(wire(row['policy'])==wire(dict(clear_sync=True)),'Nested SEEKDIR explicit flag projection policy')
    try:compare_input(cell,f,row)
    except ValueError as error:need(str(error)=='Nested SEEKDIR actual captured archive','Nested SEEKDIR projection only breaks actual archive')
    else:raise ValueError('Nested SEEKDIR flag projection accepted as actual parent input')
    expected=bytearray.fromhex(f['archive_before']);need(struct.unpack_from('<I',expected,28)[0]==0x213,'Nested SEEKDIR canonical archive flag')
    struct.pack_into('<I',expected,28,0x13);need(row['archive_before']==expected.hex(),'Nested SEEKDIR single declared projection')
    baseline=copy.deepcopy(row);baseline['archive_before']=f['archive_before'];compare_input(cell,f,baseline)
    return dict(actual_parent_input=False,strict_actual_input_rejected=True,projection_declared=True,
                changed_archive_offset=28,flag_before=0x213,flag_after=0x13,output_or_activation_proved_here=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('parent-report','json'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3];need(source not in a.json.resolve().parents and source!=a.json.resolve(),'Nested SEEKDIR private output')
        r=freeze(a.parent_report)
        with a.json.open('x')as out:out.write(json.dumps(r,indent=2)+'\n')
    except(ValueError,KeyError,TypeError,OSError)as error:p.exit(2,str(error)+'\n')
    print('Actual stopped inputs frozen; projected archive flags remain explicitly non-actual')


if __name__=='__main__':main()
