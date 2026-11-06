"""Test-only BLZ variants that keep the physical overlay extent unchanged."""
from sgp12 import blz


def alternate_same_size_stream(canonical):
    """Return another in-place-safe optimal stream for the same decoded image.

    Equal-length optimal encodings can use different raw-prefix cuts.  This is
    a stronger canonicality mutant than toggling an allegedly unused flag bit:
    some valid streams consume every bit in their final flag group.
    """
    canonical = bytes(canonical)
    image = blz.blz_decomprimi(canonical)
    raw_len = len(image)
    reversed_image = bytes(reversed(image))
    best, dist_best = blz._riscontri_massimi(reversed_image)
    cost, choice, tokens = blz._analisi_ottima(reversed_image, best)

    def total(k):
        token_count = tokens[k]
        packed = (cost[k] - token_count) // 8 + (token_count + 7) // 8
        body = raw_len - k + packed
        return body + (-body) % 4 + 8

    candidates = sorted(
        (k for k in range(1, raw_len + 1) if total(k) == len(canonical)),
        reverse=True,
    )
    for k in candidates:
        stream = blz._confeziona(
            image,
            reversed_image,
            blz._emetti(reversed_image, choice, dist_best, k),
            k,
        )
        if stream == canonical:
            continue
        try:
            decoded = blz.blz_decomprimi(stream, raw_len)
        except blz.Rifiuto:  # candidate rejection is expected; the final absence is not
            continue
        if decoded == image:
            if len(stream) != len(canonical):
                raise AssertionError('alternate BLZ stream changed physical length')
            return stream
    raise AssertionError('no alternate same-size in-place-safe BLZ stream exists')
