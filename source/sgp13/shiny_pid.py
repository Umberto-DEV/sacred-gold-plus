"""Finite transforms for a candidate that has not yet become a Pokémon.

These helpers neither draw RNG nor choose lottery odds, admit encounter routes,
construct Pokémon, or rewrite stored specimens. The caller supplies the final
16-bit TID XOR SID, a lottery outcome, and an explicit cyclic search offset.

Nature and the full low byte (gender and ability parity) survive the transform.
Independently selected forms must be retained by the caller. Ordinary Wurmple's
future evolution follows the FINAL PID, as do Spinda's spots and other native
PID-derived outcomes; their counterfactual values for the discarded candidate
are not preserved. Legacy PID-selected Unown-letter routes are unsupported.

First-hit search is not uniform over valid PIDs. This module proves no native
RNG distribution, encounter rate, ARM instruction budget or save compatibility.
"""

MAX_SHINY_PROBES = 157


def _unsigned(value, bits, name):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError(f'{name} must be an unsigned {bits}-bit integer')


def _xor(pid, ot_fold):
    _unsigned(pid, 32, 'PID')
    _unsigned(ot_fold, 16, 'OT fold')
    return (pid >> 16) ^ (pid & 0xffff) ^ ot_fold


def is_shiny(pid, ot_fold):
    """Model the existing Plus XOR<255 classification, including old shinies."""
    return _xor(pid, ot_fold) < 255


def transform_pid(pid, ot_fold, *, shiny, seed):
    """Honor an explicit lottery outcome for a new, still uncreated candidate.

    ``seed`` is a search offset in [0, 2047], not a PRNG state. It is unused on
    the nonshiny branch. Selected shiny output has XOR<8 in at most 157 probes;
    selected nonshiny output has XOR>=255 after at most one byte adjustment.
    No fallback can silently reverse the requested lottery outcome.
    """
    original_xor = _xor(pid, ot_fold)
    _unsigned(seed, 11, 'seed')
    if type(shiny) is not bool:
        raise ValueError('shiny must be an explicit boolean lottery outcome')
    if not shiny:
        if original_xor >= 255:
            return pid
        x = (pid >> 8) & 255
        changed = x + 25 if x <= 230 else x - 25
        # ±6400 preserves nature; no carry can alter high16 or low8.
        # Original XOR high8 was zero; changing x makes it nonzero (XOR>=256).
        return (pid & 0xffff00ff) | (changed << 8)

    low_byte, nature = pid & 255, pid % 25
    for offset in range(MAX_SHINY_PROBES):
        index = (seed + offset) & 2047
        low = low_byte | ((index >> 3) << 8)
        high = ((low ^ ot_fold) & 0xfff8) | (index & 7)
        candidate = (high << 16) | low
        if candidate % 25 == nature:
            return candidate
    # Exhaustive reduced-domain proof: for every t=ot_fold>>8 and residue,
    # R=6*x+16*(x^t)+11*s mod25 has a cyclic match gap no greater than 157.
    # low_byte and ot_fold's low8 only add a fixed shift to the target residue.
    raise RuntimeError('shiny PID existence bound violated')
