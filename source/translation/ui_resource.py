"""Preserve the caller's compressed/uncompressed Nitro graphics contract."""
import hashlib

from ndspy import lz10


def normalize_donor(original, donor, transform=None):
    if len(original) < 4 or len(donor) < 4:
        raise ValueError('Truncated UI resource')
    source_compressed = original[0] == 0x10
    donor_compressed = donor[0] == 0x10
    output = donor
    if transform:
        if transform['kind'] != 'lz10-decompress' or source_compressed or not donor_compressed:
            raise ValueError('UI transform violates the original loader storage contract')
        output = lz10.decompress(donor)
        if hashlib.sha256(output).hexdigest() != transform['after_sha256']:
            raise ValueError('UI transform output checksum mismatch')
    elif source_compressed != donor_compressed:
        raise ValueError('UI storage mismatch requires an explicit reviewed transform')
    source_raw = lz10.decompress(original) if source_compressed else original
    output_raw = lz10.decompress(output) if source_compressed else output
    if source_raw[:4] != output_raw[:4]:
        raise ValueError('Nitro resource type changed')
    return output
