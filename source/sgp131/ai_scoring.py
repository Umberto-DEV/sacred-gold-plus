"""Stop the post-KO replacement type score from wrapping at 256.

ov12_02258800 (pret name; called by the trainer AI and by the opponent battle
controller) adds two CalculateTypeEffectiveness results (40 neutral, 160 for
4x) into r0, then truncates the sum to eight bits before comparing it with the
best score so far. Two 4x matchups give 320, which becomes 64.

Original (0x02258934):                  Patched:
    ldr  r1,[sp,#0x4c]                      (unchanged)
    adds r0,r1,r0        ; r0 = sum         (unchanged)
    lsls r0,r0,#24                          lsls r1,r0,#24
    lsrs r0,r0,#24       ; r0 = sum & 255   lsrs r1,r1,#24   ; r1 = sum & 255
    str  r0,[sp,#0x4c]                      str  r1,[sp,#0x4c] ; same word as before
    ldr  r1,[sp,#0x48]   ; best             (unchanged; r1 is dead after it)
    cmp  r1,r0 / bhs     ; unsigned         cmp r1,r0 with the full sum in r0
    ldr  r0,[sp,#0x4c]   ; reload           nop (r0 already holds the sum)
    str  r0,[sp,#0x48]   ; best = score      best = the full sum

The compared value and the new best are the full 32-bit sum; [sp,#0x4c] still
receives the 8-bit value the game stored, so stage two, which reuses that word
when a move has no damage evaluation, reads exactly what it read natively.
Same RNG call, masks, tie-breaking (first wins), super-effective-move check
and fallback stage. Four scoring instructions, eight declared bytes, five of
them change value.

The same stage also fixes HG-B13 in ov12_02252054.  A later weakness row could
set SUPER_EFFECTIVE after an earlier type row had set NO_EFFECT.  The
SUPER_EFFECTIVE arm now tests the mask NOT_VERY_EFFECTIVE|NO_EFFECT (`movs
r0,#4` -> `movs r0,#12`), preserving the normal resistance cancellation while
letting immunity win.  One additional halfword is declared; one byte changes.

The guard is the function 0x02258800..0x02258BA0 (SHA-256 pin) plus twenty
context bytes, not the whole overlay, so changes made to other parts of
overlay 12 by other stages are neither copied nor rejected.

The ``ai-immunities`` stage also fixes HG-B14 in overlay 10.  The trainer AI
had a second, partial implementation of the switch-trapping rules, so it
treated Flying, Levitate and Magnet Rise targets as trapped by Arena Trap and
ignored Shed Shell.  One guarded 16-byte prefix now stores the caller
arguments, passes the battler in r2 and calls the engine's existing
``BattlerCanSwitch`` routine, then branches to the original blocked/allowed
continuations.  The obsolete duplicate checks are bypassed, not rewritten.

The same authenticated archive owner corrects AI-WEB-01 through AI-WEB-04 in
member 0 of ``a/0/9/9``.  Water Spout/Eruption and Facade passed
battler token 0 (the target) to checks that describe the move user; only those
three token words become 1.  The Expert dispatch also listed SolarBeam effect
151 twice, leaving the intact Thunder effect-152 routine unreachable.  Metal
Burst used four partial turn-order shortcuts before its complete speed-order
command.  Only the second duplicate becomes 152 and the four shortcut jumps
become zero.
"""
import hashlib
import struct

OVERLAY_ID = 12
OVERLAY_BASE = 0x022378C0
OVERLAY_SIZE = 0x37380
FUNCTION_START, FUNCTION_END = 0x02258800, 0x02258BA0
FUNCTION_SHA256 = '45b8c7da8e9c25d38616d0524c824098182e48d807fde80da59a4e082569da84'
EFFECTIVENESS_FUNCTION_START, EFFECTIVENESS_FUNCTION_END = 0x02252054, 0x02252218
EFFECTIVENESS_FUNCTION_SHA256 = 'eb5c3828aa198508aa0644dcf61bad54cf2022dab25923d62e8622a840e952a5'
# ldr r1,[sp,#0x4c]; adds r0,r1,r0; lsls r0,#24; lsrs r0,#24; str r0,[sp,#0x4c];
# ldr r1,[sp,#0x48]; cmp r1,r0; bhs; ldr r0,[sp,#0x4c]; str r0,[sp,#0x48]
CONTEXT_ADDRESS = 0x02258934
CONTEXT = bytes.fromhex('1399 0818 0006 000e 1390 1299 8142 0dd2 1398 1290'.replace(' ', ''))
PATCHES = (  # (address, preimage, replacement)
    (0x02258938, bytes.fromhex('0006000e1390'), bytes.fromhex('0106090e1391')),  # lsls/lsrs/str through r1
    (0x02258944, bytes.fromhex('1398'), bytes.fromhex('c046')),                  # reload of [sp,#0x4c] -> nop
)
EFFECTIVENESS_CONTEXT_ADDRESS = 0x022521F8
EFFECTIVENESS_CONTEXT = bytes.fromhex(
    '04201043086070470a680420104203d0042082430a6070470220104308607047')
# In the SUPER_EFFECTIVE arm, test NOT_VERY_EFFECTIVE|NO_EFFECT.  NO_EFFECT
# already cleared SUPER_EFFECTIVE when it was set, so the later weakness row
# must not add it again.  Existing NOT_VERY_EFFECTIVE cancellation is retained.
EFFECTIVENESS_PATCHES = (
    (0x02252202, bytes.fromhex('0420'), bytes.fromhex('0c20')),
)
for _address, _pre, _post in PATCHES:
    if CONTEXT[_address - CONTEXT_ADDRESS:_address - CONTEXT_ADDRESS + len(_pre)] != _pre or len(_pre) != len(_post):
        raise RuntimeError('PATCHES are inconsistent with CONTEXT')
for _address, _pre, _post in EFFECTIVENESS_PATCHES:
    if (EFFECTIVENESS_CONTEXT[
            _address - EFFECTIVENESS_CONTEXT_ADDRESS:
            _address - EFFECTIVENESS_CONTEXT_ADDRESS + len(_pre)] != _pre
            or len(_pre) != len(_post)):
        raise RuntimeError('EFFECTIVENESS_PATCHES are inconsistent with their context')
LANGUAGES = ('EN', 'IT')

# Trainer AI Basic_CheckForImmunity, overlay 10. The second ability word is a
# retail duplicate of Levitate (26); the branch it targets checks Water and
# therefore belongs to Dry Skin (87). The preceding Levitate branch exits to
# the shared continuation, so the duplicate can never cover Dry Skin.
DRY_SKIN_OVERLAY_BASE = 0x0221BE20
DRY_SKIN_OVERLAY_SIZE = 0xF460
DRY_SKIN_OVERLAY_SHA256 = '8676349e6c80b87bea78f68cf5bce4c022255d787c3970a79a4cddf74ac9e7dd'
DRY_SKIN_CONTEXT_ADDRESS = 0x02220BC4
DRY_SKIN_SITE = 0x02220BD4
DRY_SKIN_CONTEXT = struct.pack('<13I', 19, 26, 34, 19, 26, 38,
                               76, 43, 30, 4, 34, 13, 2442)
DRY_SKIN_PREIMAGE = struct.pack('<I', 26)
DRY_SKIN_REPLACEMENT = struct.pack('<I', 87)
DRY_SKIN_ARCHIVE = 'a/0/9/9'
DRY_SKIN_ARCHIVE_FILE_ID = 228
DRY_SKIN_ARCHIVE_SHA256 = '59e4065ab291cad68678145bf20b66985ba7fc827527b93b3523c648edd9e65a'
DRY_SKIN_MEMBER = 0
DRY_SKIN_MEMBER_SIZE = 42428
DRY_SKIN_MEMBER_SHA256 = '29d224e059fc7a59f11a69046fe7cef602e18d5cb5afee5bfab41d2207f147f8'
DRY_SKIN_MEMBER_CONTEXT_OFFSET = 0x118
DRY_SKIN_MEMBER_SITE = 0x128

# AI-WEB-01, Expert_CheckPower: Water Spout and Eruption scale with the
# user's HP, but both HP-percentage commands pass battler token 0 (target).
# The native token resolver maps token 1 to ctx+0x3CF (the move user).
WATER_SPOUT_CONTEXT_OFFSET = 0x6450
WATER_SPOUT_CONTEXT = struct.pack(
    '<25i', 43, 0, 19, 43, 10, 16, 43, 20, 13, 36, 1, 6,
    6, 0, 50, 8, 76, 4, 6, 0, 70, 2, 4, -1, 77)
WATER_SPOUT_SITES = (0x6484, 0x649C)
WATER_SPOUT_PREIMAGE = struct.pack('<I', 0)
WATER_SPOUT_REPLACEMENT = struct.pack('<I', 1)

# AI-WEB-03, Expert_Facade: the move's damage script reads the user's status,
# but the trainer AI checks battler token 0 (target) before adding one point.
# Keep the exact poison/bad-poison/burn/paralysis mask and score delta; only
# resolve the same move user as the damage path (token 1).
FACADE_CONTEXT_OFFSET = 0x5B64
FACADE_CONTEXT = struct.pack('<7i', 10, 0, 0xD8, 2, 4, 1, 77)
FACADE_SITE = 0x5B68
FACADE_PREIMAGE = struct.pack('<I', 0)
FACADE_REPLACEMENT = struct.pack('<I', 1)

# AI-WEB-04, Expert dispatch: the table routes effect 151 (SolarBeam) twice,
# so effect 152 (Thunder) can never reach its intact routine.  Authenticate
# both the dispatch neighbourhood and the destination before changing the
# second duplicate only.
THUNDER_DISPATCH_CONTEXT_OFFSET = 0x2BD8
THUNDER_DISPATCH_CONTEXT = struct.pack(
    '<15i', 47, 144, 2721, 47, 145, 2814, 47, 151, 2811,
    47, 151, 2855, 47, 155, 2878)
THUNDER_DISPATCH_SITE = 0x2C00
THUNDER_DISPATCH_PREIMAGE = struct.pack('<I', 151)
THUNDER_DISPATCH_REPLACEMENT = struct.pack('<I', 152)
THUNDER_ROUTINE_OFFSET = 0x58A4
THUNDER_ROUTINE = struct.pack(
    '<25i', 43, 0, 17, 43, 20, 14, 43, 10, 11, 46, 19, 1, 7,
    20, 2, 9, 4, 1, 76, 5, 0, 50, 2, 4, -3)

# AI-WEB-02, Basic_CheckMetalBurst: the Stall and item-ID shortcuts are only a
# partial model of turn order and contradict each other in mixed Stall/lagging
# cases.  Item ID 107 is also Shiny Stone, not the intended held-item effect
# 107.  The final CheckSortSpeed command is the engine's complete ordering
# authority and already handles Lagging Tail, Full Incense, Stall and their
# combinations.  Make the four shortcut branches fall through by replacing
# their relative jumps with zero; all commands still consume the same words
# and the script geometry is stable.
METAL_BURST_CONTEXT_OFFSET = 0x1DE0
METAL_BURST_CONTEXT = struct.pack(
    '<25i', 43, 0, 607, 41, 0, 19, 100, 602, 85, 0, 107, 598,
    41, 1, 19, 100, 7, 85, 1, 107, 3, 36, 0, 586, 77)
METAL_BURST_ITEM_ID = 107
METAL_BURST_ABILITY = 100
METAL_BURST_JUMP_SITES = (0x1DFC, 0x1E0C, 0x1E20, 0x1E30)
METAL_BURST_JUMPS = (602, 598, 7, 3)
METAL_BURST_REPLACEMENT = struct.pack('<I', 0)

# Trainer AI switch gate, ov10_022203A4.  The replacement delegates all
# trapping/exemption semantics to BattlerCanSwitch (0x02255920) and then uses
# the routine's existing return continuations.  The embedded BL is Thumb and
# was independently decoded by the native reproducer.
ARENA_SWITCH_FUNCTION_START, ARENA_SWITCH_FUNCTION_END = 0x022203A4, 0x022205BC
ARENA_SWITCH_FUNCTION_SHA256 = '2cc6ca06a1e50caf5cf5b70ca296ec6f40d4c44bfa3d0289cdd6ec8551b5d1c0'
ARENA_SWITCH_SITE = 0x022203B4
ARENA_SWITCH_PREIMAGE = bytes.fromhex('7c4a7d4bac58019002911c4230d11032')
ARENA_SWITCH_REPLACEMENT = bytes.fromhex('01900291321c35f0b1fa002830d132e0')
ARENA_SWITCH_TARGET = 0x02255920

# HG-B15, ov10_0221FE8C.  Redirect both the active and party-candidate ability
# comparisons to the 20-byte zero-filled span after the overlay's four-byte
# static-initializer table.  The helper preserves exact equality and admits
# only the Gen-IV pairs 10/78 (Volt Absorb/Motor Drive) and 11/87 (Water
# Absorb/Dry Skin).  Expected ability 18 (Flash Fire) is rejected from the
# normalization path before arithmetic.  The caller's existing conditional
# branches, RNG calls, scan order and tie behaviour remain in place.
ABSORB_SWITCH_FUNCTION_START, ABSORB_SWITCH_FUNCTION_END = 0x0221FE8C, 0x02220010
ABSORB_SWITCH_FUNCTION_SHA256 = 'dc1d8eb617ec8cd15d32876d0a31c8dbce43da2c06a4c27d6af6c9efe63afead'
ABSORB_SWITCH_ACTIVE_SITE = 0x0221FF10
ABSORB_SWITCH_ACTIVE_PREIMAGE = bytes.fromhex('0499814202d1')
ABSORB_SWITCH_ACTIVE_REPLACEMENT = bytes.fromhex('0bf0acf902d1')
ABSORB_SWITCH_PARTY_SITE = 0x0221FFC6
ABSORB_SWITCH_PARTY_PREIMAGE = bytes.fromhex('0006010e049888420dd1')
ABSORB_SWITCH_PARTY_REPLACEMENT = bytes.fromhex('0bf051f90fd1c046c046')
ABSORB_SWITCH_STATIC_INIT_START = 0x0222B268
ABSORB_SWITCH_STATIC_INIT_END = 0x0222B26C
ABSORB_SWITCH_HELPER_ADDRESS = 0x0222B26C
ABSORB_SWITCH_HELPER_PREIMAGE = bytes(20)
ABSORB_SWITCH_HELPER = bytes.fromhex(
    '0499884205d00c2903d8401ac9000c3988427047')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def patch_dry_skin_overlay(image, *, overlay_sha256=DRY_SKIN_OVERLAY_SHA256):
    """Return overlay 10 with the duplicate Levitate ability changed to Dry Skin."""
    if not isinstance(image, (bytes, bytearray, memoryview)):
        raise TypeError('overlay 10 image must be bytes')
    image = bytes(image)
    if len(image) != DRY_SKIN_OVERLAY_SIZE:
        raise ValueError('overlay 10 image size %#x differs from %#x'
                         % (len(image), DRY_SKIN_OVERLAY_SIZE))
    context = DRY_SKIN_CONTEXT_ADDRESS - DRY_SKIN_OVERLAY_BASE
    if image[context:context + len(DRY_SKIN_CONTEXT)] != DRY_SKIN_CONTEXT:
        raise ValueError('Dry Skin AI context preimage does not match overlay 10')
    if _sha(image) != overlay_sha256:
        raise ValueError('overlay 10 differs from the pinned AI build')
    site = DRY_SKIN_SITE - DRY_SKIN_OVERLAY_BASE
    if image[site:site + 4] != DRY_SKIN_PREIMAGE:
        raise ValueError('duplicate Levitate preimage is absent or already patched')
    result = bytearray(image)
    result[site:site + 4] = DRY_SKIN_REPLACEMENT
    changed = [i for i, (old, new) in enumerate(zip(image, result)) if old != new]
    return bytes(result), {
        'site': DRY_SKIN_SITE,
        'ability_before': 26,
        'ability_after': 87,
        'changed_offsets': changed,
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
    }


def _arena_switch_function(image):
    return bytes(image[
        ARENA_SWITCH_FUNCTION_START - DRY_SKIN_OVERLAY_BASE:
        ARENA_SWITCH_FUNCTION_END - DRY_SKIN_OVERLAY_BASE])


def patch_arena_switch_overlay(
        image, *, function_sha256=ARENA_SWITCH_FUNCTION_SHA256):
    """Replace the partial AI trap checks with the normal engine switch gate."""
    if not isinstance(image, (bytes, bytearray, memoryview)):
        raise TypeError('overlay 10 image must be bytes')
    image = bytes(image)
    if len(image) != DRY_SKIN_OVERLAY_SIZE:
        raise ValueError('overlay 10 image size %#x differs from %#x'
                         % (len(image), DRY_SKIN_OVERLAY_SIZE))
    site = ARENA_SWITCH_SITE - DRY_SKIN_OVERLAY_BASE
    if image[site:site + len(ARENA_SWITCH_PREIMAGE)] != ARENA_SWITCH_PREIMAGE:
        raise ValueError('Arena Trap switch-gate context preimage does not match overlay 10')
    if _sha(_arena_switch_function(image)) != function_sha256:
        raise ValueError('Arena Trap switch function differs from the pinned build')
    result = bytearray(image)
    result[site:site + len(ARENA_SWITCH_REPLACEMENT)] = ARENA_SWITCH_REPLACEMENT
    result = bytes(result)
    return result, {
        'site': ARENA_SWITCH_SITE,
        'target': ARENA_SWITCH_TARGET,
        'preimage': ARENA_SWITCH_PREIMAGE.hex(),
        'replacement': ARENA_SWITCH_REPLACEMENT.hex(),
        'changed_offsets': _changed(image, result),
        'function_sha256_before': _sha(_arena_switch_function(image)),
        'function_sha256_after': _sha(_arena_switch_function(result)),
    }


def _absorb_switch_function(image):
    return bytes(image[
        ABSORB_SWITCH_FUNCTION_START - DRY_SKIN_OVERLAY_BASE:
        ABSORB_SWITCH_FUNCTION_END - DRY_SKIN_OVERLAY_BASE])


def patch_absorb_switch_overlay(
        image, *, function_sha256=ABSORB_SWITCH_FUNCTION_SHA256):
    """Admit Dry Skin and Motor Drive without changing the native RNG path."""
    if not isinstance(image, (bytes, bytearray, memoryview)):
        raise TypeError('overlay 10 image must be bytes')
    image = bytes(image)
    if len(image) != DRY_SKIN_OVERLAY_SIZE:
        raise ValueError('overlay 10 image size %#x differs from %#x'
                         % (len(image), DRY_SKIN_OVERLAY_SIZE))
    active = ABSORB_SWITCH_ACTIVE_SITE - DRY_SKIN_OVERLAY_BASE
    party = ABSORB_SWITCH_PARTY_SITE - DRY_SKIN_OVERLAY_BASE
    helper = ABSORB_SWITCH_HELPER_ADDRESS - DRY_SKIN_OVERLAY_BASE
    if image[active:active + len(ABSORB_SWITCH_ACTIVE_PREIMAGE)] != \
            ABSORB_SWITCH_ACTIVE_PREIMAGE:
        raise ValueError('absorb-switch active caller preimage does not match overlay 10')
    if image[party:party + len(ABSORB_SWITCH_PARTY_PREIMAGE)] != \
            ABSORB_SWITCH_PARTY_PREIMAGE:
        raise ValueError('absorb-switch party caller preimage does not match overlay 10')
    if image[helper:helper + len(ABSORB_SWITCH_HELPER_PREIMAGE)] != \
            ABSORB_SWITCH_HELPER_PREIMAGE:
        raise ValueError('overlay 10 tail is not the pinned empty helper span')
    if _sha(_absorb_switch_function(image)) != function_sha256:
        raise ValueError('absorb-switch function differs from the pinned build')
    result = bytearray(image)
    result[active:active + len(ABSORB_SWITCH_ACTIVE_REPLACEMENT)] = \
        ABSORB_SWITCH_ACTIVE_REPLACEMENT
    result[party:party + len(ABSORB_SWITCH_PARTY_REPLACEMENT)] = \
        ABSORB_SWITCH_PARTY_REPLACEMENT
    result[helper:helper + len(ABSORB_SWITCH_HELPER)] = ABSORB_SWITCH_HELPER
    result = bytes(result)
    return result, {
        'active_site': ABSORB_SWITCH_ACTIVE_SITE,
        'party_site': ABSORB_SWITCH_PARTY_SITE,
        'helper': ABSORB_SWITCH_HELPER_ADDRESS,
        'helper_bytes': len(ABSORB_SWITCH_HELPER),
        'changed_offsets': _changed(image, result),
        'function_sha256_before': _sha(_absorb_switch_function(image)),
        'function_sha256_after': _sha(_absorb_switch_function(result)),
    }


def _patch_ai_immunities_overlay(image):
    dry_skin, dry_details = patch_dry_skin_overlay(image)
    arena, arena_details = patch_arena_switch_overlay(dry_skin)
    result, absorb_details = patch_absorb_switch_overlay(arena)
    return result, {'dry_skin': dry_details, 'arena_switch': arena_details,
                    'absorb_switch': absorb_details,
                    'changed_offsets': _changed(image, result),
                    'overlay_sha256_before': _sha(image),
                    'overlay_sha256_after': _sha(result)}


def patch_dry_skin_member(member, *, member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Return trainer-AI archive member 0 with the same Levitate -> Dry Skin fix."""
    if not isinstance(member, (bytes, bytearray, memoryview)):
        raise TypeError('trainer AI member must be bytes')
    member = bytes(member)
    if len(member) != DRY_SKIN_MEMBER_SIZE:
        raise ValueError('trainer AI member size %d differs from %d'
                         % (len(member), DRY_SKIN_MEMBER_SIZE))
    start = DRY_SKIN_MEMBER_CONTEXT_OFFSET
    if member[start:start + len(DRY_SKIN_CONTEXT)] != DRY_SKIN_CONTEXT:
        raise ValueError('Dry Skin AI context preimage does not match archive member 0')
    if _sha(member) != member_sha256:
        raise ValueError('trainer AI member 0 differs from the pinned build')
    if member[DRY_SKIN_MEMBER_SITE:DRY_SKIN_MEMBER_SITE + 4] != DRY_SKIN_PREIMAGE:
        raise ValueError('duplicate Levitate preimage is absent or already patched')
    result = bytearray(member)
    result[DRY_SKIN_MEMBER_SITE:DRY_SKIN_MEMBER_SITE + 4] = DRY_SKIN_REPLACEMENT
    changed = _changed(member, result)
    return bytes(result), {
        'member': DRY_SKIN_MEMBER,
        'member_offset': DRY_SKIN_MEMBER_SITE,
        'ability_before': 26,
        'ability_after': 87,
        'changed_offsets': changed,
        'member_sha256_before': _sha(member),
        'member_sha256_after': _sha(result),
    }


def patch_water_spout_member(member, *, member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Make both Expert-AI HP checks resolve the move user (token 1)."""
    if not isinstance(member, (bytes, bytearray, memoryview)):
        raise TypeError('trainer AI member must be bytes')
    member = bytes(member)
    if len(member) != DRY_SKIN_MEMBER_SIZE:
        raise ValueError('trainer AI member size %d differs from %d'
                         % (len(member), DRY_SKIN_MEMBER_SIZE))
    start = WATER_SPOUT_CONTEXT_OFFSET
    if member[start:start + len(WATER_SPOUT_CONTEXT)] != WATER_SPOUT_CONTEXT:
        raise ValueError('Water Spout/Eruption AI context preimage does not match member 0')
    if _sha(member) != member_sha256:
        raise ValueError('trainer AI member 0 differs from the pinned build')
    for site in WATER_SPOUT_SITES:
        if member[site:site + 4] != WATER_SPOUT_PREIMAGE:
            raise ValueError('Water Spout/Eruption target-battler token is absent or already patched')
    result = bytearray(member)
    for site in WATER_SPOUT_SITES:
        result[site:site + 4] = WATER_SPOUT_REPLACEMENT
    changed = _changed(member, result)
    return bytes(result), {
        'member': DRY_SKIN_MEMBER,
        'member_offsets': list(WATER_SPOUT_SITES),
        'battler_before': 0,
        'battler_after': 1,
        'changed_offsets': changed,
        'member_sha256_before': _sha(member),
        'member_sha256_after': _sha(result),
    }


def patch_facade_member(member, *, member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Make Expert Facade inspect the move user while preserving its mask."""
    if not isinstance(member, (bytes, bytearray, memoryview)):
        raise TypeError('trainer AI member must be bytes')
    member = bytes(member)
    if len(member) != DRY_SKIN_MEMBER_SIZE:
        raise ValueError('trainer AI member size %d differs from %d'
                         % (len(member), DRY_SKIN_MEMBER_SIZE))
    start = FACADE_CONTEXT_OFFSET
    if member[start:start + len(FACADE_CONTEXT)] != FACADE_CONTEXT:
        raise ValueError('Facade AI context preimage does not match member 0')
    if _sha(member) != member_sha256:
        raise ValueError('trainer AI member 0 differs from the pinned build')
    if member[FACADE_SITE:FACADE_SITE + 4] != FACADE_PREIMAGE:
        raise ValueError('Facade target-battler token is absent or already patched')
    result = bytearray(member)
    result[FACADE_SITE:FACADE_SITE + 4] = FACADE_REPLACEMENT
    result = bytes(result)
    return result, {
        'member': DRY_SKIN_MEMBER,
        'member_offset': FACADE_SITE,
        'battler_before': 0,
        'battler_after': 1,
        'status_mask': 0xD8,
        'score_delta': 1,
        'changed_offsets': _changed(member, result),
        'member_sha256_before': _sha(member),
        'member_sha256_after': _sha(result),
    }


def patch_thunder_member(member, *, member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Route effect 152 to the authenticated Expert_Thunder sequence."""
    if not isinstance(member, (bytes, bytearray, memoryview)):
        raise TypeError('trainer AI member must be bytes')
    member = bytes(member)
    if len(member) != DRY_SKIN_MEMBER_SIZE:
        raise ValueError('trainer AI member size %d differs from %d'
                         % (len(member), DRY_SKIN_MEMBER_SIZE))
    start = THUNDER_DISPATCH_CONTEXT_OFFSET
    if member[start:start + len(THUNDER_DISPATCH_CONTEXT)] != \
            THUNDER_DISPATCH_CONTEXT:
        raise ValueError('Thunder AI dispatch context preimage does not match member 0')
    if member[THUNDER_ROUTINE_OFFSET:
              THUNDER_ROUTINE_OFFSET + len(THUNDER_ROUTINE)] != THUNDER_ROUTINE:
        raise ValueError('Thunder AI routine preimage does not match member 0')
    if _sha(member) != member_sha256:
        raise ValueError('trainer AI member 0 differs from the pinned build')
    if member[THUNDER_DISPATCH_SITE:THUNDER_DISPATCH_SITE + 4] != \
            THUNDER_DISPATCH_PREIMAGE:
        raise ValueError('duplicate SolarBeam effect is absent or already patched')
    result = bytearray(member)
    result[THUNDER_DISPATCH_SITE:THUNDER_DISPATCH_SITE + 4] = \
        THUNDER_DISPATCH_REPLACEMENT
    result = bytes(result)
    return result, {
        'member': DRY_SKIN_MEMBER,
        'member_offset': THUNDER_DISPATCH_SITE,
        'effect_before': 151,
        'effect_after': 152,
        'changed_offsets': _changed(member, result),
        'member_sha256_before': _sha(member),
        'member_sha256_after': _sha(result),
    }


def patch_metal_burst_member(member, *, member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Let Metal Burst's complete speed-order check decide every ordering case."""
    if not isinstance(member, (bytes, bytearray, memoryview)):
        raise TypeError('trainer AI member must be bytes')
    member = bytes(member)
    if len(member) != DRY_SKIN_MEMBER_SIZE:
        raise ValueError('trainer AI member size %d differs from %d'
                         % (len(member), DRY_SKIN_MEMBER_SIZE))
    start = METAL_BURST_CONTEXT_OFFSET
    if member[start:start + len(METAL_BURST_CONTEXT)] != METAL_BURST_CONTEXT:
        raise ValueError('Metal Burst AI context preimage does not match member 0')
    if _sha(member) != member_sha256:
        raise ValueError('trainer AI member 0 differs from the pinned build')
    for site, jump in zip(METAL_BURST_JUMP_SITES, METAL_BURST_JUMPS):
        if member[site:site + 4] != struct.pack('<I', jump):
            raise ValueError('Metal Burst Shiny Stone branch is absent or already patched')
    result = bytearray(member)
    for site in METAL_BURST_JUMP_SITES:
        result[site:site + 4] = METAL_BURST_REPLACEMENT
    result = bytes(result)
    return result, {
        'member': DRY_SKIN_MEMBER,
        'member_offsets': list(METAL_BURST_JUMP_SITES),
        'ability': METAL_BURST_ABILITY,
        'item_id': METAL_BURST_ITEM_ID,
        'jump_before': list(METAL_BURST_JUMPS),
        'jump_after': [0] * len(METAL_BURST_JUMP_SITES),
        'changed_offsets': _changed(member, result),
        'member_sha256_before': _sha(member),
        'member_sha256_after': _sha(result),
    }


def patch_ai_member(member, *, member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Compose the authenticated archive-copy fixes without replaying a delta."""
    member = bytes(member)
    dry, dry_details = patch_dry_skin_member(member, member_sha256=member_sha256)
    water, water_details = patch_water_spout_member(member, member_sha256=member_sha256)
    facade, facade_details = patch_facade_member(member, member_sha256=member_sha256)
    thunder, thunder_details = patch_thunder_member(member, member_sha256=member_sha256)
    metal_burst, metal_burst_details = patch_metal_burst_member(
        member, member_sha256=member_sha256)
    result = bytearray(member)
    result[DRY_SKIN_MEMBER_SITE:DRY_SKIN_MEMBER_SITE + 4] = \
        dry[DRY_SKIN_MEMBER_SITE:DRY_SKIN_MEMBER_SITE + 4]
    for site in WATER_SPOUT_SITES:
        result[site:site + 4] = water[site:site + 4]
    result[FACADE_SITE:FACADE_SITE + 4] = facade[FACADE_SITE:FACADE_SITE + 4]
    result[THUNDER_DISPATCH_SITE:THUNDER_DISPATCH_SITE + 4] = \
        thunder[THUNDER_DISPATCH_SITE:THUNDER_DISPATCH_SITE + 4]
    for site in METAL_BURST_JUMP_SITES:
        result[site:site + 4] = metal_burst[site:site + 4]
    result = bytes(result)
    return result, {
        'member': DRY_SKIN_MEMBER,
        'dry_skin': dry_details,
        'water_spout': water_details,
        'facade': facade_details,
        'thunder': thunder_details,
        'metal_burst': metal_burst_details,
        'changed_offsets': _changed(member, result),
        'member_sha256_before': _sha(member),
        'member_sha256_after': _sha(result),
    }


def _dry_skin_archive_layout(raw):
    """Return member 0's data offset in the exact one-member trainer-AI NARC."""
    raw = bytes(raw)
    if len(raw) < 0x3C or raw[:4] != b'NARC' or raw[4:6] not in (b'\xfe\xff', b'\xff\xfe'):
        raise ValueError('trainer AI file is not a NARC archive')
    size, header, blocks = struct.unpack_from('<IHH', raw, 8)
    if size != len(raw) or header != 0x10 or blocks != 3:
        raise ValueError('trainer AI NARC header differs')
    magic, btaf_size, count = struct.unpack_from('<4sII', raw, 0x10)
    if magic != b'BTAF' or count != 1 or btaf_size != 20:
        raise ValueError('trainer AI NARC allocation table differs')
    member_start, member_end = struct.unpack_from('<II', raw, 0x1C)
    btnf = 0x10 + btaf_size
    if raw[btnf:btnf + 4] != b'BTNF':
        raise ValueError('trainer AI NARC name block is absent')
    gmif = btnf + struct.unpack_from('<I', raw, btnf + 4)[0]
    if raw[gmif:gmif + 4] != b'GMIF':
        raise ValueError('trainer AI NARC data block is absent')
    data = gmif + 8
    if member_start != 0 or member_end != DRY_SKIN_MEMBER_SIZE or data + member_end != len(raw):
        raise ValueError('trainer AI NARC member geometry differs')
    return data


def patch_dry_skin_archive(raw, *, archive_sha256=DRY_SKIN_ARCHIVE_SHA256,
                           member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Patch member 0 in place without normalizing the retail NARC container."""
    raw = bytes(raw)
    data = _dry_skin_archive_layout(raw)
    if _sha(raw) != archive_sha256:
        raise ValueError('trainer AI archive differs from the pinned build')
    member = raw[data:data + DRY_SKIN_MEMBER_SIZE]
    patched_member, details = patch_dry_skin_member(member, member_sha256=member_sha256)
    result = bytearray(raw)
    result[data:data + DRY_SKIN_MEMBER_SIZE] = patched_member
    archive_offset = data + DRY_SKIN_MEMBER_SITE
    return bytes(result), {
        **details,
        'archive_offset': archive_offset,
        'archive_sha256_before': _sha(raw),
        'archive_sha256_after': _sha(result),
    }


def patch_ai_archive(raw, *, archive_sha256=DRY_SKIN_ARCHIVE_SHA256,
                     member_sha256=DRY_SKIN_MEMBER_SHA256):
    """Patch all authenticated member-0 AI fixes in the original container."""
    raw = bytes(raw)
    data = _dry_skin_archive_layout(raw)
    if _sha(raw) != archive_sha256:
        raise ValueError('trainer AI archive differs from the pinned build')
    member = raw[data:data + DRY_SKIN_MEMBER_SIZE]
    patched_member, details = patch_ai_member(member, member_sha256=member_sha256)
    result = bytearray(raw)
    result[data:data + DRY_SKIN_MEMBER_SIZE] = patched_member
    archive_offsets = [data + offset for offset in details['changed_offsets']]
    return bytes(result), {
        **details,
        'archive_offsets': archive_offsets,
        'archive_sha256_before': _sha(raw),
        'archive_sha256_after': _sha(result),
    }


def _function(image):
    return bytes(image[FUNCTION_START - OVERLAY_BASE:FUNCTION_END - OVERLAY_BASE])


def _effectiveness_function(image):
    return bytes(image[EFFECTIVENESS_FUNCTION_START - OVERLAY_BASE:
                       EFFECTIVENESS_FUNCTION_END - OVERLAY_BASE])


def _apply_patches(image):
    result = bytearray(image)
    for address, _, post in (*PATCHES, *EFFECTIVENESS_PATCHES):
        result[address - OVERLAY_BASE:address - OVERLAY_BASE + len(post)] = post
    return bytes(result)


def _changed(before, after):
    return [i for i, (old, new) in enumerate(zip(before, after)) if old != new]


def patch_effectiveness_overlay(image, *,
                                function_sha256=EFFECTIVENESS_FUNCTION_SHA256):
    """Apply only HG-B13's one-halfword effectiveness correction."""
    if not isinstance(image, (bytes, bytearray, memoryview)):
        raise TypeError('overlay 12 image must be bytes')
    image = bytes(image)
    if len(image) != OVERLAY_SIZE:
        raise ValueError('overlay 12 image size %#x differs from %#x'
                         % (len(image), OVERLAY_SIZE))
    window = EFFECTIVENESS_CONTEXT_ADDRESS - OVERLAY_BASE
    if image[window:window + len(EFFECTIVENESS_CONTEXT)] != EFFECTIVENESS_CONTEXT:
        raise ValueError('effectiveness preimage does not match overlay 12')
    if _sha(_effectiveness_function(image)) != function_sha256:
        raise ValueError('effectiveness function differs from the pinned build')
    result = bytearray(image)
    for address, _, post in EFFECTIVENESS_PATCHES:
        result[address - OVERLAY_BASE:address - OVERLAY_BASE + len(post)] = post
    result = bytes(result)
    return result, {
        'sites': [{'address': a, 'preimage': pre.hex(), 'replacement': post.hex()}
                  for a, pre, post in EFFECTIVENESS_PATCHES],
        'changed_offsets': _changed(image, result),
        'function_sha256_before': _sha(_effectiveness_function(image)),
        'function_sha256_after': _sha(_effectiveness_function(result)),
    }


def patch_overlay(image, *, function_sha256=FUNCTION_SHA256,
                  effectiveness_function_sha256=EFFECTIVENESS_FUNCTION_SHA256):
    """Return (patched decoded overlay 12, details); refuse anything but the exact preimage.

    ``function_sha256`` exists so synthetic images can be pinned in class A tests."""
    if not isinstance(image, (bytes, bytearray, memoryview)):
        raise TypeError('overlay 12 image must be bytes')
    image = bytes(image)
    if len(image) != OVERLAY_SIZE:
        raise ValueError('overlay 12 image size %#x differs from %#x' % (len(image), OVERLAY_SIZE))
    window = CONTEXT_ADDRESS - OVERLAY_BASE
    if image[window:window + len(CONTEXT)] != CONTEXT:
        raise ValueError('score-conversion preimage does not match overlay 12 (changed or already patched)')
    if _sha(_function(image)) != function_sha256:
        raise ValueError('function 0x%08X..0x%08X differs from the pinned build' % (FUNCTION_START, FUNCTION_END))
    effectiveness_window = EFFECTIVENESS_CONTEXT_ADDRESS - OVERLAY_BASE
    if image[effectiveness_window:effectiveness_window + len(EFFECTIVENESS_CONTEXT)] != EFFECTIVENESS_CONTEXT:
        raise ValueError('effectiveness preimage does not match overlay 12 (changed or already patched)')
    if _sha(_effectiveness_function(image)) != effectiveness_function_sha256:
        raise ValueError('function 0x%08X..0x%08X differs from the pinned build'
                         % (EFFECTIVENESS_FUNCTION_START, EFFECTIVENESS_FUNCTION_END))
    result = _apply_patches(image)
    return result, {
        'sites': [{'address': a, 'preimage': pre.hex(), 'replacement': post.hex()}
                  for a, pre, post in (*PATCHES, *EFFECTIVENESS_PATCHES)],
        'changed_offsets': _changed(image, result),
        'function_sha256_before': _sha(_function(image)), 'function_sha256_after': _sha(_function(result)),
        'effectiveness_function_sha256_before': _sha(_effectiveness_function(image)),
        'effectiveness_function_sha256_after': _sha(_effectiveness_function(result)),
        'overlay_sha256_before': _sha(image), 'overlay_sha256_after': _sha(result),
    }


def verify_images(before, after):
    """Logical check: exactly four scoring instructions and the HG-B13 halfword differ."""
    if len(before) != OVERLAY_SIZE or len(after) != OVERLAY_SIZE:
        raise ValueError('overlay 12 image size differs: %#x and %#x' % (len(before), len(after)))
    window = CONTEXT_ADDRESS - OVERLAY_BASE
    if bytes(before[window:window + len(CONTEXT)]) != CONTEXT:
        raise ValueError('score-conversion preimage is not present in the original overlay')
    effectiveness_window = EFFECTIVENESS_CONTEXT_ADDRESS - OVERLAY_BASE
    if bytes(before[effectiveness_window:effectiveness_window + len(EFFECTIVENESS_CONTEXT)]) != EFFECTIVENESS_CONTEXT:
        raise ValueError('effectiveness preimage is not present in the original overlay')
    declared = {OVERLAY_BASE + i for address, pre, _ in (*PATCHES, *EFFECTIVENESS_PATCHES)
                for i in range(address - OVERLAY_BASE, address - OVERLAY_BASE + len(pre))}
    changed = _changed(before, after)
    if any(OVERLAY_BASE + i not in declared for i in changed):
        raise ValueError('logical bytes differ outside the declared delta: %s' % [hex(OVERLAY_BASE + i) for i in changed[:8]])
    if bytes(after) != _apply_patches(before):
        raise ValueError('the declared scoring and effectiveness replacements are not exactly present')
    return {'changed_offsets': changed, 'changed_bytes': len(changed), 'declared_window_bytes': len(declared),
            'overlay_sha256_before': _sha(before), 'overlay_sha256_after': _sha(after)}


def verify_dry_skin_images(before, after):
    """Prove the decoded overlay-10 delta is exactly the two AI corrections."""
    expected, _ = _patch_ai_immunities_overlay(before)
    if bytes(after) != expected:
        raise ValueError('overlay 10 differs from the declared AI immunity replacements')
    changed = _changed(before, after)
    expected_changed = _changed(before, expected)
    if changed != expected_changed:
        raise ValueError('overlay 10 changed bytes differ from the declared AI corrections')
    return {
        'changed_offsets': changed,
        'changed_bytes': len(changed),
        'overlay_sha256_before': _sha(before),
        'overlay_sha256_after': _sha(after),
    }


def _fat_slot(data, file_id):
    fat_offset, fat_length = struct.unpack_from('<II', data, 0x48)
    if 8 * file_id + 8 > fat_length:
        raise ValueError('file %d is outside the ROM FAT' % file_id)
    start, end = struct.unpack_from('<II', data, fat_offset + 8 * file_id)
    if not 0 <= start <= end <= len(data):
        raise ValueError('file %d has an invalid FAT slot' % file_id)
    return start, end


def apply_dry_skin(data, language):
    """Correct overlay AI defects and their authenticated archive script."""
    import ndspy.rom
    from sgp12.overlay import applica
    from sgp12.rom import Rom
    if language not in LANGUAGES:
        raise ValueError('unknown language %r; expected one of %s' % (language, ', '.join(LANGUAGES)))
    data = bytes(data)
    entry, _, original_image = Rom(data).immagine_overlay(10)
    if entry['ram'] != DRY_SKIN_OVERLAY_BASE or entry['ram_size'] != DRY_SKIN_OVERLAY_SIZE:
        raise ValueError('overlay 10 placement differs from the supported build')
    if (entry['static_init_start'], entry['static_init_end']) != \
            (ABSORB_SWITCH_STATIC_INIT_START, ABSORB_SWITCH_STATIC_INIT_END) \
            or entry['static_init_end'] != ABSORB_SWITCH_HELPER_ADDRESS:
        raise ValueError('overlay 10 static-initializer boundary differs from the safe helper span')
    expected_image, overlay_details = _patch_ai_immunities_overlay(original_image)

    parsed = ndspy.rom.NintendoDSRom(data)
    file_id = parsed.filenames.idOf(DRY_SKIN_ARCHIVE)
    if file_id != DRY_SKIN_ARCHIVE_FILE_ID:
        raise ValueError('%s is not file %d' % (DRY_SKIN_ARCHIVE, DRY_SKIN_ARCHIVE_FILE_ID))
    archive_start, archive_end = _fat_slot(data, file_id)
    archive = data[archive_start:archive_end]
    patched_archive, archive_details = patch_ai_archive(archive)

    intermediate, writer = applica(
        data, 10,
        [(DRY_SKIN_CONTEXT_ADDRESS, DRY_SKIN_CONTEXT),
         (ARENA_SWITCH_SITE, ARENA_SWITCH_PREIMAGE),
         (ABSORB_SWITCH_ACTIVE_SITE, ABSORB_SWITCH_ACTIVE_PREIMAGE),
         (ABSORB_SWITCH_PARTY_SITE, ABSORB_SWITCH_PARTY_PREIMAGE),
         (ABSORB_SWITCH_HELPER_ADDRESS, ABSORB_SWITCH_HELPER_PREIMAGE)],
        [{'addr': DRY_SKIN_SITE, 'pre': DRY_SKIN_PREIMAGE,
          'post': DRY_SKIN_REPLACEMENT},
         {'addr': ARENA_SWITCH_SITE, 'pre': ARENA_SWITCH_PREIMAGE,
          'post': ARENA_SWITCH_REPLACEMENT},
         {'addr': ABSORB_SWITCH_ACTIVE_SITE, 'pre': ABSORB_SWITCH_ACTIVE_PREIMAGE,
          'post': ABSORB_SWITCH_ACTIVE_REPLACEMENT},
         {'addr': ABSORB_SWITCH_PARTY_SITE, 'pre': ABSORB_SWITCH_PARTY_PREIMAGE,
          'post': ABSORB_SWITCH_PARTY_REPLACEMENT},
         {'addr': ABSORB_SWITCH_HELPER_ADDRESS, 'pre': ABSORB_SWITCH_HELPER_PREIMAGE,
          'post': ABSORB_SWITCH_HELPER}])
    if Rom(intermediate).immagine_overlay(10)[2] != expected_image:
        raise ValueError('overlay 10 readback differs from the verified AI immunity patches')
    if _fat_slot(intermediate, file_id) != (archive_start, archive_end) \
            or intermediate[archive_start:archive_end] != archive:
        raise ValueError('overlay writer changed the trainer AI archive or its FAT slot')
    result = bytearray(intermediate)
    result[archive_start:archive_end] = patched_archive
    result = bytes(result)
    receipt = {
        'stage': 'ai-immunities',
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(result),
        'overlay': overlay_details,
        'archive': {**archive_details, 'name': DRY_SKIN_ARCHIVE, 'file_id': file_id,
                    'rom_slot': [archive_start, archive_end],
                    'rom_offsets': [archive_start + offset
                                    for offset in archive_details['archive_offsets']]},
        'writer': writer,
    }
    receipt['verification'] = verify_dry_skin(data, result, receipt)
    return result, receipt


def apply(data, language):
    """Patch a whole ROM in memory through the cartridge-safe overlay writer."""
    from sgp12.overlay import applica
    from sgp12.rom import Rom
    if language not in LANGUAGES:
        raise ValueError('unknown language %r; expected one of %s' % (language, ', '.join(LANGUAGES)))
    entry, _, original = Rom(data).immagine_overlay(OVERLAY_ID)
    if entry['ram'] != OVERLAY_BASE or entry['ram_size'] != OVERLAY_SIZE:
        raise ValueError('overlay 12 placement differs from the supported build')
    expected, details = patch_overlay(original)
    result, receipt = applica(
        data, OVERLAY_ID,
        [(CONTEXT_ADDRESS, CONTEXT),
         (EFFECTIVENESS_CONTEXT_ADDRESS, EFFECTIVENESS_CONTEXT)],
        [{'addr': address, 'pre': pre, 'post': post}
         for address, pre, post in (*PATCHES, *EFFECTIVENESS_PATCHES)])
    if Rom(result).immagine_overlay(OVERLAY_ID)[2] != expected:
        raise ValueError('overlay readback differs from the verified patch')
    receipt = {'stage': 'ai-scoring', 'language': language, 'patch': details, 'writer': receipt}
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt


# ------------------------------------------------------------ independent reader

def _crc16(data):
    """Cartridge-header CRC-16 (poly 0xA001, init 0xFFFF), written here, not taken from the writer."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def _ranges(a, b):
    """Maximal differing byte ranges between equal-length buffers."""
    found, step = [], 1 << 16
    for start in range(0, len(a), step):
        if a[start:start + step] == b[start:start + step]:
            continue
        end = min(start + step, len(a))
        for i in range(start, end):
            if a[i] != b[i]:
                if found and found[-1][1] == i:
                    found[-1][1] = i + 1
                else:
                    found.append([i, i + 1])
    return [tuple(r) for r in found]


def _container(rom):
    """Header, FAT and y9 view parsed from bytes, independent of the writer."""
    fat_offset, fat_length, y9_offset, y9_length = struct.unpack_from('<IIII', rom, 0x48)
    fat = [struct.unpack_from('<II', rom, fat_offset + 8 * i) for i in range(fat_length // 8)]
    y9 = [struct.unpack_from('<8I', rom, y9_offset + 32 * i) for i in range(y9_length // 32)]
    return {'fat_offset': fat_offset, 'fat': fat, 'y9_offset': y9_offset, 'y9': y9}


def _decode_overlay_independently(rom, container, overlay_id):
    """One overlay decoded by the project reader and by ndspy; the two must agree."""
    import ndspy.codeCompression as codec
    from sgp12.rom import Rom
    row = container['y9'][overlay_id]
    start, end = container['fat'][row[6]]
    stream = bytes(rom[start:start + (row[7] & 0xFFFFFF)])
    if not row[7] >> 24 & 1:
        raise ValueError('overlay %d is expected to be a compressed stream' % overlay_id)
    project, second = Rom(rom).immagine_overlay(overlay_id)[2], bytes(codec.decompress(stream))
    if project != second:
        raise ValueError('the two BLZ decoders disagree on overlay %d' % overlay_id)
    return project


def _decode_independently(rom, container):
    """Overlay 12 decoded by the project reader and by ndspy; the two must agree."""
    return _decode_overlay_independently(rom, container, OVERLAY_ID)


def verify_dry_skin(before, after, receipt):
    """Independently verify both AI copies and confine every physical ROM change."""
    import ndspy.narc
    import ndspy.rom
    if len(before) != len(after):
        raise ValueError('ROM size changed: %d -> %d' % (len(before), len(after)))
    old, new = _container(before), _container(after)
    row_old, row_new = old['y9'][10], new['y9'][10]
    if row_old[:7] != row_new[:7] or row_old[0] != 10:
        raise ValueError('y9 entry of overlay 10 changed beyond its size/flag word')
    if len(old['fat']) != len(new['fat']) or old['y9'][:10] != new['y9'][:10] \
            or old['y9'][11:] != new['y9'][11:]:
        raise ValueError('FAT/y9 tables of other files changed')
    overlay_file = row_old[6]
    if overlay_file != 10:
        raise ValueError('overlay 10 is not NitroFS file 10')
    if [entry for index, entry in enumerate(old['fat']) if index != overlay_file] \
            != [entry for index, entry in enumerate(new['fat']) if index != overlay_file]:
        raise ValueError('FAT entries of other files changed')
    (overlay_start, overlay_end_old), (overlay_start_new, overlay_end_new) = \
        old['fat'][overlay_file], new['fat'][overlay_file]
    compressed_after = row_new[7] & 0xFFFFFF
    following = min([start for start, _ in old['fat'] if start > overlay_start] + [len(before)])
    if overlay_start_new != overlay_start or overlay_end_new - overlay_start != compressed_after \
            or overlay_end_new > following:
        raise ValueError('overlay 10 is not an in-place compressed stream inside its slot')
    if not row_new[7] >> 24 & 1 or (row_new[7] >> 24) & ~1 != (row_old[7] >> 24) & ~1:
        raise ValueError('overlay 10 compression flags changed')

    before_image = _decode_overlay_independently(before, old, 10)
    after_image = _decode_overlay_independently(after, new, 10)
    logical = verify_dry_skin_images(before_image, after_image)
    from sgp12.blz import blz_comprimi_ottimo
    canonical = blz_comprimi_ottimo(after_image, bersaglio=overlay_end_old - overlay_start)
    if canonical != bytes(after[overlay_start:overlay_end_new]):
        raise ValueError('overlay 10 BLZ stream is not the canonical writer output')

    rom_before = ndspy.rom.NintendoDSRom(before)
    rom_after = ndspy.rom.NintendoDSRom(after)
    archive_file = rom_before.filenames.idOf(DRY_SKIN_ARCHIVE)
    if archive_file != DRY_SKIN_ARCHIVE_FILE_ID \
            or rom_after.filenames.idOf(DRY_SKIN_ARCHIVE) != archive_file:
        raise ValueError('trainer AI archive file id differs')
    archive_start, archive_end = _fat_slot(before, archive_file)
    if _fat_slot(after, archive_file) != (archive_start, archive_end):
        raise ValueError('trainer AI archive FAT slot changed')
    old_archive = bytes(before[archive_start:archive_end])
    new_archive = bytes(after[archive_start:archive_end])
    expected_archive, archive_details = patch_ai_archive(old_archive)
    if new_archive != expected_archive:
        raise ValueError('trainer AI archive differs from the declared AI patches')
    old_member = bytes(ndspy.narc.NARC(old_archive).files[0])
    new_member = bytes(ndspy.narc.NARC(new_archive).files[0])
    expected_member, _ = patch_ai_member(old_member)
    if new_member != expected_member:
        raise ValueError('independent NARC reader does not see all member-0 AI patches')
    archive_changed = _changed(old_archive, new_archive)
    if archive_changed != archive_details['archive_offsets']:
        raise ValueError('trainer AI archive changed outside the declared bytes')

    y9_word = old['y9_offset'] + 32 * 10 + 28
    zones = ((overlay_start, max(overlay_end_old, overlay_end_new)),
             (old['fat_offset'] + 8 * overlay_file, old['fat_offset'] + 8 * overlay_file + 8),
             (y9_word, y9_word + 4), (0x15E, 0x160), (archive_start, archive_end))
    differing = _ranges(before, after)
    outside = [span for span in differing
               if not any(start <= span[0] and span[1] <= end for start, end in zones)]
    if outside:
        raise ValueError('ROM bytes differ outside overlay 10 and the trainer AI archive')
    if struct.unpack_from('<H', after, 0x15E)[0] != _crc16(bytes(after[:0x15E])):
        raise ValueError('header CRC16 does not match the header')
    if len(rom_before.files) != len(rom_after.files):
        raise ValueError('NitroFS file count changed')
    for index, (old_file, new_file) in enumerate(zip(rom_before.files, rom_after.files)):
        if index not in (overlay_file, archive_file) and old_file != new_file:
            raise ValueError('NitroFS file %d changed' % index)

    if not isinstance(receipt, dict) or receipt.get('input_sha256') != _sha(before) \
            or receipt.get('output_sha256') != _sha(after):
        raise ValueError('receipt must contain matching input and output ROM hashes')
    archive_receipt = receipt.get('archive', {})
    if archive_receipt.get('file_id') != archive_file \
            or archive_receipt.get('rom_slot') != [archive_start, archive_end] \
            or archive_receipt.get('rom_offsets') != [archive_start + offset
                                                      for offset in archive_details['archive_offsets']]:
        raise ValueError('archive receipt differs from the cartridge')
    writer = receipt.get('writer', {})
    overlay_only = bytearray(after)
    overlay_only[archive_start:archive_end] = old_archive
    if writer.get('ingresso_sha256') != _sha(before) \
            or writer.get('uscita_sha256') != _sha(overlay_only):
        raise ValueError('overlay writer receipt hashes differ from the reconstructed intermediate image')
    return {
        'ok': True,
        'overlay_logical_changed_bytes': logical['changed_bytes'],
        'archive_changed_bytes': len(archive_changed),
        'archive_rom_offsets': [archive_start + offset for offset in archive_changed],
        'decoders_agree': True,
        'rom_sha256_before': _sha(before),
        'rom_sha256_after': _sha(after),
    }


def verify(before, after, receipt):
    """Re-read ROM ``before`` and ``after`` and prove the declared ten-byte delta and nothing else.

    Require matching receipt hashes and the writer's deterministic BLZ encoding;
    decoded-image equality alone does not establish compressed-byte integrity."""
    if len(before) != len(after):
        raise ValueError('ROM size changed: %d -> %d (in-place replacement expected)' % (len(before), len(after)))
    old, new = _container(before), _container(after)
    row_old, row_new = old['y9'][OVERLAY_ID], new['y9'][OVERLAY_ID]
    if row_old[:7] != row_new[:7] or row_old[0] != OVERLAY_ID:
        raise ValueError('y9 entry of overlay 12 changed beyond its size/flag word')
    if len(old['fat']) != len(new['fat']) or old['y9'][:OVERLAY_ID] != new['y9'][:OVERLAY_ID] \
            or old['y9'][OVERLAY_ID + 1:] != new['y9'][OVERLAY_ID + 1:]:
        raise ValueError('FAT/y9 tables of other files changed')
    file_id = row_old[6]
    if [e for i, e in enumerate(old['fat']) if i != file_id] != [e for i, e in enumerate(new['fat']) if i != file_id]:
        raise ValueError('FAT entries of other files changed')
    (start, end_old), (start_new, end_new) = old['fat'][file_id], new['fat'][file_id]
    size_new = row_new[7] & 0xFFFFFF
    following = min([first for first, _ in old['fat'] if first > start] + [len(before)])
    if start_new != start or end_new - start != size_new or end_new > following:
        raise ValueError('overlay 12 file range/size is not an in-place compressed stream inside its slot')
    if (row_new[7] >> 24) & ~1 != (row_old[7] >> 24) & ~1 or not row_new[7] >> 24 & 1:
        raise ValueError('flag byte of the overlay 12 y9 entry changed beyond staying compressed')
    if end_new < end_old and before[end_new:end_old] != after[end_new:end_old] and set(after[end_new:end_old]) != {0xFF}:
        raise ValueError('slot tail after the new stream is neither original nor 0xFF padding')
    if end_new > end_old and set(before[end_old:end_new]) != {0xFF}:
        raise ValueError('the longer stream grows over bytes that were not 0xFF padding')
    before_image = _decode_independently(before, old)
    after_image = _decode_independently(after, new)
    logical = verify_images(before_image, after_image)
    # The writer uses the optimal project encoder with the original FAT length
    # as its target. ndspy's greedy encoder produces different, valid bytes and
    # would reject honest outputs. Derive the target from the ROM, never receipt.
    from sgp12.blz import blz_comprimi_ottimo
    canonical = blz_comprimi_ottimo(after_image, bersaglio=end_old - start)
    if canonical != bytes(after[start:end_new]):
        raise ValueError('overlay 12 BLZ stream is not the canonical writer output')

    y9_word = old['y9_offset'] + 32 * OVERLAY_ID + 28
    zones = {'overlay_12_slot': (start, max(end_old, end_new)),
             'fat_entry': (old['fat_offset'] + 8 * file_id, old['fat_offset'] + 8 * file_id + 8),
             'y9_size_flag_word': (y9_word, y9_word + 4), 'header_crc16': (0x15E, 0x160)}
    differing = _ranges(before, after)
    outside = [r for r in differing if not any(a <= r[0] and r[1] <= b for a, b in zones.values())]
    if outside:
        raise ValueError('ROM bytes differ outside the declared regions: %s' % [(hex(a), hex(b)) for a, b in outside[:8]])
    if struct.unpack_from('<H', after, 0x15E)[0] != _crc16(bytes(after[:0x15E])):
        raise ValueError('header CRC16 does not match the header')
    writer = receipt.get('writer', receipt) if isinstance(receipt, dict) else None
    if not isinstance(writer, dict) or writer.get('ingresso_sha256') != _sha(before) \
            or writer.get('uscita_sha256') != _sha(after):
        raise ValueError('receipt must contain matching input and output ROM hashes')
    return {
        'ok': True, 'logical_changed_bytes': logical['changed_bytes'], 'logical_changed_offsets': logical['changed_offsets'],
        'declared_window_bytes': logical['declared_window_bytes'],
        'overlay_sha256_before': logical['overlay_sha256_before'], 'overlay_sha256_after': logical['overlay_sha256_after'],
        'compressed_bytes_before': row_old[7] & 0xFFFFFF, 'compressed_bytes_after': size_new, 'slot_bytes': following - start,
        'changed_zones': {name: {'range': (hex(a), hex(b)),
                                 'differing_bytes': sum(min(y, b) - max(x, a) for x, y in differing if x < b and y > a)}
                          for name, (a, b) in zones.items()},
        'header_crc16': hex(struct.unpack_from('<H', after, 0x15E)[0]),
        'rom_sha256_before': _sha(before), 'rom_sha256_after': _sha(after), 'decoders_agree': True,
    }
