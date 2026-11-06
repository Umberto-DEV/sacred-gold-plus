"""Offline HG-T11 GTS response-path reproducer for immutable V4 EN/IT.

No network or save is used.  The bench authenticates the exact overlay-70
client routines, then feeds controlled response bodies through a literal
model of their observed contract.  It deliberately distinguishes a truly
empty HTTP body from one length-valid, but semantically empty, 0x124-byte
record.  The latter is the smallest input that makes ``Select`` reachable
without a Pokemon or trainer identity.

This is a component reproducer, not an emulator/UI freeze claim.  The exact
historical server payload is unavailable and the official service is closed.
"""
import hashlib
import itertools
from pathlib import Path
import struct
import unittest

from sgp12.rom import Rom


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / "local/experiments/balance493-2026-10-28"
V4 = {
    "EN": ("179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90",
           147345256),
    "IT": ("2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156",
           153228136),
}

OVERLAY_ID = 70
OVERLAY_RAM = 0x022378C0
OVERLAY_SIZE = 61248
OVERLAY_SHA256 = "8232f02cc4f5bd9357f29d1f178ff7ef06ad744e160868f81c51af5b8ef52b4e"

# Search callback, result router and the case-4 (Select) handler respectively.
ROUTINES = {
    (0x02237C72, 0x02237CEA): "ae8372e84bf741dd9d3b6d8b813e8c9ddd83d12172c531185f86951ed99a14d8",
    (0x0223C0C8, 0x0223C19C): "e384bcb971be232cc6dbcab2dae55a26274661a5e845acf496da5a1fe92dbdda",
    (0x0223BD90, 0x0223BE84): "e62008f1d5b66e076956fc81301d1ad4081d675fdef3eb32c08a9423c4fcbaad",
}
SELECT_GUARD = bytes.fromhex(
    "4a2080002058002825d01d20e06210200090012001903d2002900020011c021c"
    "031cd3f5f2fd0c48caf503f903b018bd"
)

RECORD_SIZE = 0x124
POKEMON_SIZE = 236
TRAINER_NAME = 0x10C
TRAINER_ID = 0x11C
COUNTRY = 0x11E
REGION = 0x11F
AVATAR = 0x120
GAME_VERSION = 0x122
LANGUAGE = 0x123
PERMUTATIONS = tuple(itertools.permutations(range(4)))


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def candidate(case, language):
    path = V4_ROOT / ("candidate-v4-%s.nds" % language)
    if not path.is_file():
        case.skipTest("immutable V4 candidate unavailable: " + str(path))
    data = path.read_bytes()
    case.assertEqual((_sha(data), len(data)), V4[language])
    return data


def _crypt(words, seed):
    """Gen-IV Pokemon word cipher (symmetric XOR with the native LCRNG)."""
    output = []
    for word in words:
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        output.append(word ^ (seed >> 16))
    return output


def populated_record():
    """A checksum-valid synthetic Pokemon plus populated GTS trainer fields."""
    pid = 0x12345678
    blocks = [bytearray(32) for _ in range(4)]
    struct.pack_into("<H", blocks[0], 0, 25)       # Pikachu
    struct.pack_into("<I", blocks[0], 4, 0xA1B2C3D4)
    struct.pack_into("<I", blocks[0], 8, 125000)  # deterministic experience
    blocks[0][12:14] = bytes((70, 9))              # friendship, ability
    struct.pack_into("<4H", blocks[1], 0, 85, 98, 86, 0)
    blocks[1][8:12] = bytes((15, 30, 20, 0))
    struct.pack_into("<I", blocks[1], 16, sum(31 << (5 * n) for n in range(6)))
    struct.pack_into("<11H", blocks[2], 0, 0x012B, 0x012C, *([0xFFFF] * 9))
    struct.pack_into("<8H", blocks[3], 0, 0x012B, *([0xFFFF] * 7))

    order = PERMUTATIONS[((pid >> 13) & 31) % 24]
    clear = b"".join(blocks[index] for index in order)
    clear_words = struct.unpack("<64H", clear)
    checksum = sum(clear_words) & 0xFFFF
    encrypted = struct.pack("<64H", *_crypt(clear_words, checksum))

    party = bytearray(100)
    struct.pack_into("<IBB7H", party, 0, 0, 50, 0, 120, 120, 90, 70, 80, 100, 90)
    party_words = struct.unpack("<50H", party)
    pokemon = struct.pack("<IHH", pid, 0, checksum) + encrypted
    pokemon += struct.pack("<50H", *_crypt(party_words, pid))
    assert len(pokemon) == POKEMON_SIZE

    record = bytearray(RECORD_SIZE)
    record[:POKEMON_SIZE] = pokemon
    struct.pack_into("<8H", record, TRAINER_NAME,
                     0x012B, 0x012C, 0xFFFF, 0xFFFF,
                     0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF)
    struct.pack_into("<H", record, TRAINER_ID, 0x4321)
    record[COUNTRY:AVATAR + 1] = bytes((1, 2, 3))
    record[GAME_VERSION:LANGUAGE + 1] = bytes((7, 2))
    return bytes(record)


def decode_species(record):
    pid, _flags, checksum = struct.unpack_from("<IHH", record)
    encrypted = struct.unpack_from("<64H", record, 8)
    clear = struct.pack("<64H", *_crypt(encrypted, checksum))
    order = PERMUTATIONS[((pid >> 13) & 31) % 24]
    species = struct.unpack_from("<H", clear, order.index(0) * 32)[0]
    return species, checksum == (sum(struct.unpack("<64H", clear)) & 0xFFFF)


class GtsClientModel:
    """Literal contract of the three authenticated routines above.

    ``ov70_02237C72`` accepts each complete 0x124-byte unit without inspecting
    its content. ``ov70_0223C0C8`` stores 0..7 as the result count.
    ``ov70_0223BD90`` case 4 guards Select on that count alone.
    """

    @staticmethod
    def search_status(body, communication_error=False):
        if communication_error:
            return -13
        if len(body) >= RECORD_SIZE:
            return len(body) // RECORD_SIZE
        if not body:
            return 0
        return -2 if body[0] == 0x0E else -13

    @staticmethod
    def result_count(status):
        return status if 0 <= status <= 7 else 0

    @classmethod
    def select_reachable(cls, body, communication_error=False):
        status = cls.search_status(body, communication_error)
        return cls.result_count(status) != 0


class GtsEmptyRomTests(unittest.TestCase):
    def test_v4_en_it_share_the_length_only_search_and_select_path(self):
        for language in V4:
            rom = Rom(candidate(self, language))
            entry, _stream, image = rom.immagine_overlay(OVERLAY_ID)
            self.assertEqual((entry["ram"], len(image), _sha(image)),
                             (OVERLAY_RAM, OVERLAY_SIZE, OVERLAY_SHA256))
            for (start, end), digest in ROUTINES.items():
                self.assertEqual(_sha(image[start - OVERLAY_RAM:end - OVERLAY_RAM]),
                                 digest)
            guard = image[0x0223BE1A - OVERLAY_RAM:0x0223BE4A - OVERLAY_RAM]
            self.assertEqual(guard, SELECT_GUARD)

    def test_clean_empty_response_blocks_select(self):
        self.assertEqual(GtsClientModel.search_status(b""), 0)
        self.assertFalse(GtsClientModel.select_reachable(b""))

    def test_populated_valid_record_is_the_healthy_result_control(self):
        record = populated_record()
        self.assertEqual(len(record), RECORD_SIZE)
        self.assertEqual(decode_species(record), (25, True))
        self.assertNotEqual(record[TRAINER_NAME:TRAINER_ID], bytes(TRAINER_ID - TRAINER_NAME))
        self.assertEqual(GtsClientModel.search_status(record), 1)
        self.assertTrue(GtsClientModel.select_reachable(record))

    def test_communication_error_never_exposes_select(self):
        record = populated_record()
        self.assertEqual(GtsClientModel.search_status(record, communication_error=True), -13)
        self.assertFalse(GtsClientModel.select_reachable(record, communication_error=True))

    def test_one_zero_filled_record_reaches_select_without_identity(self):
        padded_empty = bytes(RECORD_SIZE)
        # A zero record decodes to species 0 and fails the Pokemon checksum;
        # the GTS search callback never performs either validation.
        self.assertEqual(decode_species(padded_empty), (0, False))
        self.assertEqual(padded_empty[TRAINER_NAME:TRAINER_ID],
                         bytes(TRAINER_ID - TRAINER_NAME))
        self.assertEqual(padded_empty[TRAINER_ID:AVATAR + 1],
                         bytes(AVATAR + 1 - TRAINER_ID))
        self.assertEqual(GtsClientModel.search_status(padded_empty), 1)
        self.assertTrue(GtsClientModel.select_reachable(padded_empty))


if __name__ == "__main__":
    unittest.main()
