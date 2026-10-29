"""Display the native caught marker on enemy trainer healthbars too."""

ADDRESS = 0x02264A14
CONTEXT_ADDRESS = 0x02264A06
CONTEXT = bytes.fromhex('e868d5f7eafe0121084201d044480440')
REPLACEMENT = bytes.fromhex('c046')  # Thumb MOV r8,r8 (NOP)


def patch_image(image, base):
    """Remove only the trainer filter; retain native enemy-bar and Dex checks."""
    offset = CONTEXT_ADDRESS - base
    if offset < 0 or image[offset:offset + len(CONTEXT)] != CONTEXT:
        raise ValueError('caught HUD preimage does not match overlay 12')
    result = bytearray(image)
    offset = ADDRESS - base
    result[offset:offset + 2] = REPLACEMENT
    return bytes(result)


def apply(data):
    """Patch the guarded overlay through the existing cartridge-safe writer."""
    from sgp12.overlay import applica
    from sgp12.rom import Rom
    entry, _, original = Rom(data).immagine_overlay(12)
    expected = patch_image(original, entry['ram'])
    result, receipt = applica(
        data, 12, [(CONTEXT_ADDRESS, CONTEXT)],
        [{'addr': ADDRESS, 'pre': CONTEXT[-2:], 'post': REPLACEMENT}],
    )
    if Rom(result).immagine_overlay(12)[2] != expected:
        raise ValueError('caught HUD readback differs from the verified patch')
    return result, receipt
