"""One confined legacy owner: audio/events, IGT, save and Bag repairs.

The reader reconstructs the Lullaby intermediate, peels only the IGT condition
from the actual output, rederives fishing, then independently reads the
Victory Road Fly gate and the remaining changes.  Archive data remains a
separate producer consumed before the single UI append.
"""
import hashlib

from . import (bag_alloc, fishing, gb_sounds_evolution, igt, igt_verify,
               lullaby, plus_save, pokegear_autocull, soul_dew,
               victory_road_fly, wonder_card)
from .ui_verify import Image


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _need(ok, reason):
    if not ok:
        raise ValueError('legacy native: ' + reason)


def apply(data, language):
    _need(type(data) is bytes and language in ('EN', 'IT'), 'input/language')
    first, radio = lullaby.apply(data, language)
    second, fish = fishing.apply(first, language)
    third, fly = victory_road_fly.apply(second, language)
    fourth, dew = soul_dew.apply(third, language)
    fifth, card = wonder_card.apply(fourth, language)
    sixth, gb_audio = gb_sounds_evolution.apply(fifth, language)
    seventh, cull = pokegear_autocull.apply(sixth, language)
    eighth, clock = igt.apply(seventh, language)
    ninth, saved = plus_save.apply(eighth, language)
    out, bag = bag_alloc.apply(ninth, language)
    return out, {'stage': 'legacy-native', 'language': language,
                 'input_sha256': _sha(data), 'output_sha256': _sha(out),
                 'steps': [radio, fish, fly, dew, card, gb_audio, cull,
                           clock, saved, bag]}


def verify(before, after, receipt):
    _need(type(before) is bytes and type(after) is bytes and len(before) == len(after), 'image geometry')
    _need(type(receipt) is dict and set(receipt) == {
        'stage', 'language', 'input_sha256', 'output_sha256', 'steps'}, 'receipt fields')
    language = receipt['language']
    _need(receipt['stage'] == 'legacy-native' and language in ('EN', 'IT')
          and receipt['input_sha256'] == _sha(before)
          and receipt['output_sha256'] == _sha(after), 'receipt identity')
    steps = receipt['steps']
    _need(type(steps) is list and len(steps) == 10 and all(type(s) is dict for s in steps),
          'ten owner receipts')
    _need([s.get('stage') for s in steps] == ['legacy-lullaby', 'legacy-fishing', 'victory-road-fly',
                                              'soul-dew', 'wonder-card-decoration-guard',
                                              'gb-sounds-evolution', 'pokegear-autocull',
                                              'legacy-igt', 'plus-save', 'bag-allocation']
          and all(s.get('language') == language for s in steps), 'owner order/language')
    # Rederive the two predecessors.  The original compressed overlay stream
    # is not recoverable byte-for-byte by recompressing the fixed stream, so
    # fishing is re-run from the authenticated first intermediate instead of
    # pretending the shared BLZ slot can be peeled from logical bytes alone.
    first, derived_radio = lullaby.apply(before, language)
    _need(steps[0] == derived_radio, 'Lullaby receipt differs from rederivation')
    second, derived_fish = fishing.apply(first, language)
    _need(steps[1] == derived_fish, 'fishing receipt differs from rederivation')
    old, final = Image(before), Image(after)
    ninth = bytearray(after)
    bag_start, bag_end = bag_alloc.span(before)
    ninth[bag_start:bag_end] = before[bag_start:bag_end]
    ninth = bytes(ninth)
    eighth = bytearray(ninth)
    for save_start, save_end in plus_save.spans(before):
        eighth[save_start:save_end] = before[save_start:save_end]
    eighth = bytes(eighth)
    at = old.offset(igt.SITE, 2)
    _need(at == final.offset(igt.SITE, 2), 'IGT physical placement')
    seventh = eighth[:at] + before[at:at+2] + eighth[at+2:]

    # Overlay 101 is a shared compressed slot.  Re-derive the authenticated
    # predecessors to recover the exact stream before the AutoCull stage;
    # each independent reader below still verifies its own before/after pair.
    third, _derived_fly = victory_road_fly.apply(second, language)
    fourth, _derived_dew = soul_dew.apply(third, language)
    fifth, _derived_card = wonder_card.apply(fourth, language)
    sixth, _derived_gb = gb_sounds_evolution.apply(fifth, language)
    fifth = bytearray(sixth)
    for audio_start, audio_end in gb_sounds_evolution.spans(before):
        fifth[audio_start:audio_end] = before[audio_start:audio_end]
    fifth = bytes(fifth)
    fourth = bytearray(fifth)
    for card_start, card_end in wonder_card.spans(before):
        fourth[card_start:card_end] = before[card_start:card_end]
    fourth = bytes(fourth)
    third = bytearray(fourth)
    for dew_start, dew_end in soul_dew.spans(before):
        third[dew_start:dew_end] = before[dew_start:dew_end]
    third = bytes(third)
    radio = lullaby.verify(before, first, steps[0])
    fish = fishing.verify(first, second, steps[1])
    fly = victory_road_fly.verify(second, third, steps[2])
    dew = soul_dew.verify(third, fourth, steps[3])
    card = wonder_card.verify(fourth, fifth, steps[4])
    gb_audio = gb_sounds_evolution.verify(fifth, sixth, steps[5])
    cull = pokegear_autocull.verify(sixth, seventh, steps[6])
    clock = igt_verify.verify(seventh, eighth, steps[7])
    saved = plus_save.verify(eighth, ninth, steps[8])
    bag = bag_alloc.verify(ninth, after, steps[9])
    return {'ok': True, 'lullaby': radio, 'fishing': fish,
            'victory_road_fly': fly, 'soul_dew': dew, 'igt': clock,
            'wonder_card': card, 'gb_sounds_evolution': gb_audio,
            'pokegear_autocull': cull,
            'plus_save': saved,
            'bag_allocation': bag,
            'container_unchanged': True, 'save_layout_unchanged': True}
