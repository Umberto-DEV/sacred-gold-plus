"""Admit only the two legacy V1.3 V4 inputs; config cannot add trusted pins.

The future UI baseline needs an explicitly reviewed pin update. These hashes
must never be learned from an arbitrary input or a workbench configuration.
"""
import hashlib

INPUT_HASHES = {
    '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90': 'EN',
    '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156': 'IT',
}
INPUT_SIZES = {
    '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90': 147345256,
    '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156': 153228136,
}


def input_contracts():
    return {digest: (language, INPUT_SIZES[digest])
            for digest, language in INPUT_HASHES.items()}


def identify(data: bytes) -> str:
    digest = hashlib.sha256(data).hexdigest()
    if digest not in INPUT_HASHES:
        raise ValueError('input must be an exact supported V1.3 V4 ROM')
    return INPUT_HASHES[digest]
