"""SG-BAG-FOREIGN must preserve the already-installed Shiny UI consumer ABI."""
import importlib.util
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

from sgp12.rom import Arm9, Rom, bl_decode
from sgp13 import training
from sgp131 import bag_foreign


SOURCE = Path(__file__).resolve().parents[1]
REPOSITORY = SOURCE.parent
FIXTURE = REPOSITORY / "local/experiments/balance493-2026-10-28/candidate-v4-EN.nds"
REPORT = REPOSITORY / "local/experiments/balance493-2026-10-28/candidate-v4-EN.json"

spec = importlib.util.spec_from_file_location(
    "bag_foreign_shiny_ui_bench",
    SOURCE / "features/shiny/test/ui_transaction_bench.py",
)
bench_module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(SOURCE / "features/shiny/test"))
spec.loader.exec_module(bench_module)


def training_symbols():
    report = json.loads(REPORT.read_text())
    return next(
        stage["details"]["symbols"]
        for stage in report["stages"]
        if stage["stage"] == "training"
    )


def entry_target(site, payload):
    if payload[:2] not in (b"\x08\xb5", b"\x10\xb5") or payload[6:8] != b"\x10\xbd":
        raise AssertionError("consumer is not the installed entry wrapper")
    return bl_decode(site + 2, payload[2:6]) | 1


def overlay_bytes(raw, overlay_id, address, count):
    record, _, image = Rom(raw).immagine_overlay(overlay_id)
    offset = address - record["ram"]
    return image[offset:offset + count]


class BagForeignConsumerRegression(unittest.TestCase):
    def test_successor_keeps_the_live_shiny_ui_descriptor_usable(self):
        if not FIXTURE.is_file() or not REPORT.is_file():
            self.skipTest("immutable V4 Training consumer fixture unavailable")

        old_rom = FIXTURE.read_bytes()
        old_blob = Arm9.from_bytes(old_rom).leggi(
            training.BASE, training.CONFIG - training.BASE
        )
        old_symbols = training_symbols()

        with tempfile.TemporaryDirectory(prefix="bag-foreign-consumer-") as work:
            root = Path(work)
            compiled = bench_module.compile_all(root / "consumer")
            parts, extension, symbols, gate, gate_symbols = compiled

            # Negative control: the exact historical Training compartment and
            # descriptor used by the V4 consumer remain admitted.
            historical = (
                (old_blob, old_symbols, *parts[2:]),
                extension,
                symbols,
                gate,
                gate_symbols,
            )
            self.assertEqual(bench_module.Bench(historical).peek(), 0)

            # Exercise the actual confined successor payload, not a textual
            # comparison of symbol addresses.  The UI transaction performs
            # its real descriptor and owner checks before returning a snapshot.
            successor_work = root / "successor"
            successor_work.mkdir()
            installed, _ = bag_foreign.compile_successor(successor_work)
            successor = (
                (installed, parts[1], *parts[2:]),
                extension,
                symbols,
                gate,
                gate_symbols,
            )
            self.assertEqual(bench_module.Bench(successor).peek(), 0)

    def test_successor_keeps_every_installed_external_entry_target(self):
        if not FIXTURE.is_file() or not REPORT.is_file():
            self.skipTest("immutable V4 Training consumer fixture unavailable")

        before = FIXTURE.read_bytes()
        old_symbols = training_symbols()
        with tempfile.TemporaryDirectory(prefix="bag-foreign-entry-abi-") as work:
            root = Path(work)
            after, _ = bag_foreign.apply(before, "EN", work_dir=root)
            successor_blob, successor_symbols = training.compile_native(root / "symbols")
        self.assertEqual(
            hashlib.sha256(successor_blob).hexdigest(), bag_foreign.BASELINE_SHA256
        )

        arm = Arm9.from_bytes(after)
        consumers = {
            "event flags -> load": arm.u32(0x023CFEF0),
            "Bag save wrapper -> save": entry_target(
                0x023DCC9C, arm.leggi(0x023DCC9C, 8)
            ),
            "item archive loader -> items": entry_target(
                0x02078138, arm.leggi(0x02078138, 8)
            ),
            "EV scalar hook -> ev_scalar": entry_target(
                0x02090A84, arm.leggi(0x02090A84, 8)
            ),
            "item usability hook -> canuse": entry_target(
                0x0208FD9C, arm.leggi(0x0208FD9C, 8)
            ),
            "Day Care withdrawal hook -> retrieve": entry_target(
                0x0206C078, arm.leggi(0x0206C078, 8)
            ),
            "Day Care growth hook -> growth": entry_target(
                0x0206C0E8, arm.leggi(0x0206C0E8, 8)
            ),
            "playtime hook -> play": bl_decode(
                0x020183E0, arm.leggi(0x020183E0, 4)
            ) | 1,
            "script command table -> script": arm.u32(0x020FB4A8),
            "battle overlay -> battle": entry_target(
                0x022463E8, overlay_bytes(after, 12, 0x022463E8, 8)
            ),
            "phone overlay -> phone": bl_decode(
                0x021F3968, overlay_bytes(after, 101, 0x021F3968, 4)
            ) | 1,
            "consultant sprite hook -> sprite": entry_target(
                0x021F92DC, overlay_bytes(after, 1, 0x021F92DC, 8)
            ),
            "consultant category hook -> sprite_category": entry_target(
                0x021FA248, overlay_bytes(after, 1, 0x021FA248, 8)
            ),
        }
        shiny_access, shiny_bind, shiny_read = struct.unpack(
            "<3I", arm.leggi(0x023CB100 + 44, 12)
        )
        consumers.update({
            "Shiny config -> shiny_access": shiny_access,
            "Shiny config -> shiny_bind": shiny_bind,
            "Shiny config -> read": shiny_read,
        })
        symbols = {
            "event flags -> load": "training_load",
            "Bag save wrapper -> save": "training_save",
            "item archive loader -> items": "training_items",
            "EV scalar hook -> ev_scalar": "training_ev_scalar",
            "item usability hook -> canuse": "training_canuse",
            "Day Care withdrawal hook -> retrieve": "training_retrieve",
            "Day Care growth hook -> growth": "training_growth",
            "playtime hook -> play": "training_play",
            "script command table -> script": "training_script",
            "battle overlay -> battle": "training_battle",
            "phone overlay -> phone": "training_phone",
            "consultant sprite hook -> sprite": "training_sprite",
            "consultant category hook -> sprite_category": "training_sprite_category",
            "Shiny config -> shiny_access": "training_shiny_access",
            "Shiny config -> shiny_bind": "training_shiny_bind",
            "Shiny config -> read": "training_read",
        }

        # Decoder control: every real V4 consumer resolves to the authenticated
        # entry recorded by the build which installed it.
        self.assertEqual(
            consumers, {consumer: old_symbols[symbol] for consumer, symbol in symbols.items()}
        )
        # The successor replaces the compartment without rewriting any of
        # these consumers. Each must therefore still resolve to its function.
        for consumer, target in consumers.items():
            with self.subTest(consumer=consumer, symbol=symbols[consumer]):
                self.assertEqual(target, successor_symbols[symbols[consumer]])


if __name__ == "__main__":
    unittest.main()
