"""Independent physical/logical readback for the single HG-T09 condition byte."""
import hashlib
from sgp131.ui_verify import Image


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def verify(before, after, receipt):
    before, after = bytes(before), bytes(after)
    old, new = Image(before), Image(after)
    a, b = old.offset(0x0202CE0E,2), new.offset(0x0202CE0E,2)
    _need(a == b and len(before) == len(after), 'IGT cartridge geometry changed')
    _need(hashlib.sha256(old.arm(0x0202CDBC,104)).hexdigest() ==
          '276a47f980a794aee10600dec8d3a2736ae37263a6dc1cea5c8bb992792cff02',
          'IGT native preimage')
    _need(old.arm(0x0202CE0E,2) == b'\x02\xd3' and
          new.arm(0x0202CE0E,2) == b'\x02\xd9', 'IGT branch replacement')
    _need(before[:a+1] == after[:a+1] and before[a+2:] == after[a+2:],
          'IGT byte outside the condition changed')
    _need(isinstance(receipt,dict) and receipt.get('language') in ('EN','IT')
          and receipt.get('input_sha256') == hashlib.sha256(before).hexdigest()
          and receipt.get('output_sha256') == hashlib.sha256(after).hexdigest(),
          'IGT receipt identity')
    return {'ok':True, 'logical_changed_bytes':1, 'condition_address':'0x0202CE0F',
            'container_unchanged':True, 'surrounding_bytes_unchanged':True}
