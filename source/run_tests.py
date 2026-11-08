#!/usr/bin/env python3
"""Run the Class A test suites — the ones that need no game file.

These are the test suites GitHub Actions runs on configured pushes and pull
requests. Local and hosted toolchains can differ, so compare their per-suite
results and skips. From the repository root:

    python3 -m venv .venv
    .venv/bin/pip install -r source/requirements.txt
    .venv/bin/python source/run_tests.py

It prints one line per suite with how many tests ran, how many were skipped
and why, then a total. It exits non-zero if any suite fails.

The compiled-code suites need a C compiler with the ARM target (`clang --target=armv5te-none-eabi`)
because they run our own compiled code under an ARM946E-S emulator. A MISSING
compiler makes the options-page suite SKIPPED, with its test count, and it
stays in the summary and in the JSON — it used to vanish from both. With
`--richiedi-compilatore` (or `SGP_CI=1`, which continuous integration sets) a
missing compiler is a failure instead: on a machine that is supposed to have
one, a silently skipped suite is 95 tests nobody notices. A compiler that is
present but cannot BUILD the shipped sources is never a skip: that is a defect,
and it fails here as it would anywhere else.

A Class A suite that collects no test or skips every collected test is a
FAILURE. `unittest discover` on a
folder with no test file prints "Ran 0 tests ... OK" and exits 0, so deleting
three suites used to leave the run green.

Class B suites — the ones with game-dependent assertions — are listed and run
apart. On public CI those assertions skip without a ROM; any synthetic checks
inside those suites can still execute and are not Class A coverage. They are
still part of the ONE final verdict printed at the end: the
Class A line used to be the last thing on screen and was printed before the
Class B suites had even run, so a red Class B suite left the exit code and the
JSON red while the output ended on the word PASS. See `source/README.md`.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parent

# (name, working directory, unittest arguments)
SUITE = [
    ("multilingual localization contracts", SOURCE, ["-m", "unittest", "discover", "-s", "localization", "-t", ".", "-p", "test*.py"]),
    ("maintenance synthetic wrappers and release stage", SOURCE / "features/manutenzione", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("distribution archive contracts", SOURCE / "distribution", ["-m", "unittest", "discover", "-p", "test*.py"], {"PYTHONPATH": str(SOURCE)}),
    ("Class A runner contracts", SOURCE, ["-m", "unittest", "test_run_tests"]),
    ("cheat selector catalogue", SOURCE / "cheats", ["-m", "unittest", "test_selector", "test_catalogue", "test_gender"]),
    ("sgp12 library",          SOURCE, ["-m", "unittest", "sgp12.test_lib", "sgp12.test_versione", "sgp12.test_titolo_versione", "sgp12.test_publication"]),
    ("stage 0 (original ROM)", SOURCE, ["-m", "unittest", "sgp12.test_base11"]),
    ("ARM9 reserve register",  SOURCE, ["-m", "unittest", "verifiche.test_riserva"]),
    ("runtime crash and freeze gate", SOURCE, ["-m", "unittest", "verifiche.test_runtime_gate"]),
    ("runtime source, RTC and resource guards", SOURCE / "runtime/test", ["-m", "unittest", "test_patch_core", "test_rtc_parser", "test_runtime_limits", "test_frame_observation"]),
    ("runtime debug transport/output guards", SOURCE, ["-m", "unittest", "features.debug.test_secure_output", "features.debug.tools.test_rsp"]),
    ("text codec / translation", SOURCE, ["-m", "unittest", "discover", "-s", "translation", "-p", "test_*.py"]),
    ("text width measurement", SOURCE, ["-m", "unittest", "discover", "-s", "quality-audit", "-p", "test_*.py"]),
    ("EV/IV guide (1.1)",      SOURCE, ["-m", "unittest", "discover", "-s", "native-guide", "-p", "test_*.py"]),
    ("EV/IV reader (1.1)",     SOURCE, ["-m", "unittest", "discover", "-s", "native-eviv", "-p", "test_*.py"]),
    ("guide label patch",      SOURCE / "features/guide/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("save chunk",             SOURCE / "features/plus-chunk/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("full bag build metadata", SOURCE / "features/borsa/test", ["-m", "unittest", "discover", "-p", "test_build.py"]),
    ("battle motion build policy", SOURCE / "features/anim2/test", ["-m", "unittest", "discover", "-p", "test_metadata.py"]),
    ("battle bag build metadata", SOURCE / "features/borsa-lotta/test", ["-m", "unittest", "discover", "-p", "test_build.py"]),
    ("battle party build metadata", SOURCE / "features/squadra-lotta/test", ["-m", "unittest", "discover", "-p", "test_build.py"]),
    ("battle bag cache (Unicorn)", SOURCE / "features/borsa-lotta/test", ["-m", "unittest", "discover", "-p", "test_blob.py"]),
    ("battle party cache (Unicorn)", SOURCE / "features/squadra-lotta/test", ["-m", "unittest", "discover", "-p", "test_blob.py"]),
    ("bag capacity core", SOURCE / "features/capacita-borsa/test", ["-m", "unittest", "discover", "-p", "test_core.py"]),
    ("bag capacity journal", SOURCE / "features/capacita-borsa/test", ["-m", "unittest", "discover", "-p", "test_journal.py"]),
    ("bag capacity build", SOURCE / "features/capacita-borsa/test", ["-m", "unittest", "discover", "-p", "test_build.py"]),
]

# Class B, listed apart on purpose. These need a real game file (SGP_ROM_DIR) and
# therefore skip everywhere Class A runs — including CI. They used to sit in the
# list above, where "0 run, 3 skipped ok" counted as a pass: the whole BLZ codec
# and in-place overlay applicator, 31 tests, could not fail anything. They are
# run and reported, but they are never counted as Class A coverage.
SUITE_CLASSE_B = [
    ("native gender and nature", SOURCE / "cheats", ["-m", "unittest", "test_gender_arm"]),
    ("overlay in place",       SOURCE / "features/overlay/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    # The rare-candy suite runs the shipped ARM9 under Unicorn starting from the
    # hook site itself, so it needs the built ROMs (SGP_ROM_DIR). Without them it
    # skips with a reason, and it is never counted as Class A coverage.
    ("rare candy (Unicorn)",   SOURCE / "features/caramelle/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("full bag pipeline",      SOURCE / "features/borsa/test", ["-m", "unittest", "discover", "-p", "test_composta.py"]),
    ("full bag (Unicorn)",     SOURCE / "features/borsa/test", ["-m", "unittest", "discover", "-p", "test_borsa_nucleo.py"]),
    ("battle motion (Unicorn)", SOURCE / "features/anim2/test", ["-m", "unittest", "discover", "-p", "test_blob5.py"]),
    ("battle motion reader mutants", SOURCE / "features/anim2/test", ["-m", "unittest", "discover", "-p", "test_mutanti_anim2.py"]),
    ("battle bag reader mutants", SOURCE / "features/borsa-lotta/test", ["-m", "unittest", "discover", "-p", "test_rilettore.py"]),
    ("battle party reader mutants", SOURCE / "features/squadra-lotta/test", ["-m", "unittest", "discover", "-p", "test_rilettore.py"]),
    ("battle party native move data", SOURCE / "features/squadra-lotta/test", ["-m", "unittest", "discover", "-p", "test_native_data.py"]),
    ("bag capacity native ARM", SOURCE / "features/capacita-borsa/test", ["-m", "unittest", "discover", "-p", "test_arm.py"]),
    ("bag capacity reader mutants", SOURCE / "features/capacita-borsa/test", ["-m", "unittest", "discover", "-p", "test_reader.py"]),
]

# The successor pipeline is separate from the reproducible 1.2.5 builder, but
# its source-only tests belong to the same mandatory project check. Keep tests
# that require private cartridges out of Class A.
SUITE += [
    ("1.3.1 bounded successor workbench", SOURCE, ["-m", "unittest", "sgp131.test_baseline", "sgp131.test_build", "sgp131.test_workbench", "sgp131.test_evidence", "sgp131.test_mechanics_stages", "sgp131.test_battle_animation_facade", "sgp131.test_battle_animation_dynamicpunch", "sgp131.test_battle_animation_helping_hand", "sgp131.test_battle_animation_strength", "sgp131.test_battle_animation_spit_up", "sgp131.test_giratina_pc_form"]),
    ("1.3.1 resident ownership policy", SOURCE, ["-m", "unittest", "sgp131.test_reserve"]),
    ("1.3.1 settings model and input", SOURCE / "features/settings-ui/test", ["-m", "unittest", "test_state", "test_input"]),
    ("1.3.1 settings render plan", SOURCE / "features/settings-ui/test", ["-m", "unittest", "test_render"]),
    ("1.3.1 settings pixel painter", SOURCE / "features/settings-ui/test", ["-m", "unittest", "test_painter"]),
    ("1.3.1 Guide controller", SOURCE / "features/guide-ui/test", ["-m", "unittest", "discover", "-p", "test_controller.py"]),
    ("1.3.1 Guide render plan", SOURCE / "features/guide-ui/test", ["-m", "unittest", "discover", "-p", "test_render.py"]),
    ("1.3.1 Guide pixel painter", SOURCE / "features/guide-ui/test", ["-m", "unittest", "discover", "-p", "test_painter.py"]),
    ("1.3.1 read-only training UI owner", SOURCE / "features/training-native/test", ["-m", "unittest", "test_ui_transaction"]),
    ("1.3.1 checked shiny UI owner", SOURCE / "features/shiny/test", ["-m", "unittest", "test_ui_transaction"]),
    ("1.3.1 atomic settings owners", SOURCE / "features/settings-ui/test", ["-m", "unittest", "test_owners"]),
    ("1.3.1 shared physical sampler", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_physical"]),
    ("1.3.1 checked UI heap", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_heap"]),
    ("1.3.1 persistent UI allocation", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_persistent"]),
    ("1.3.1 UI resource compiler", SOURCE, ["-m", "unittest", "sgp131.test_ui_resource"]),
    ("1.3.1 authored UI catalogue", SOURCE, ["-m", "unittest", "sgp131.test_ui_copy"]),
    ("1.3.1 checked UI resource reader", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_resource"]),
    ("1.3.1 checked Guide resource reader", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_guide_resource"]),
    ("1.3.1 checked UI backgrounds", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_bg"]),
    ("1.3.1 checked UI font", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_font"]),
    ("1.3.1 persistent UI module lifecycle", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_module"]),
    ("1.3.1 resident native UI caller", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_bridge"]),
    ("1.3.1 native field Guide entry", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_fieldbook"]),
    ("1.3.1 read-only Scene admission", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_scene_admission"]),
    ("1.3.1 composed UI Scene", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_scene"]),
    ("1.3.1 successor Guide content", SOURCE, ["-m", "unittest", "sgp131.test_guide_content"]),
    ("1.3.1 guarded UI compiler contracts", SOURCE, ["-m", "unittest", "sgp131.test_ui"]),
    ("1.3 event flag storage", SOURCE, ["-m", "unittest", "sgp13.test_event_flags"]),
    ("1.3 recoverable save feedback", SOURCE, ["-m", "unittest", "sgp13.test_save_ui"]),
    ("1.3 conditional balance probabilities", SOURCE, ["-m", "unittest", "sgp13.test_balance_math"]),
    ("1.3 guarded learnset additions", SOURCE, ["-m", "unittest", "sgp13.test_learnsets"]),
    ("1.3 species balance", SOURCE, ["-m", "unittest", "sgp13.test_species.SpeciesTests", "sgp13.test_species.BalanceAuditTests"]),
    ("1.3 shiny core and adapters", SOURCE / "features/shiny/test", ["-m", "unittest", "test_core", "test_native_owner", "test_native_routes", "test_native_search", "test_native_abort", "test_native_install.InstallTests"]),
    ("1.3 finite PID reference", SOURCE, ["-m", "unittest", "sgp13.test_shiny_pid"]),
    ("1.3 build, admission and guide facts", SOURCE, ["-m", "unittest", "sgp13.test_admission", "sgp13.test_space.SpaceTests", "sgp13.test_resources", "sgp13.test_caught", "sgp13.test_content", "sgp13.test_build", "sgp13.test_title", "sgp13.test_consultant", "sgp13.test_mew"]),
    ("extended-level model (not installed)", SOURCE / "features/extended-levels/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("1.3 training rules", SOURCE / "features/training/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("1.3 training adapters", SOURCE / "features/training-native/test", ["-m", "unittest", "test_transaction", "test_transaction_arm", "test_ownership", "test_scripts", "test_save_composition", "test_shiny_owner"]),
    ("1.3 native guide", SOURCE / "features/field-guide/test", ["-m", "unittest", "test_content", "test_native", "test_failures", "test_hooks", "test_font_cache"]),
    ("1.3 trainer strategies", SOURCE / "features/trainer-strategy/test", ["-m", "unittest", "discover", "-p", "test_*.py"]),
    ("1.3 Plus presentation", SOURCE / "features/plus-ui/test", ["-m", "unittest", "test_context", "test_navigation", "test_extended.ExtendedMenu"]),
]
# Modern mechanics (4a). The accuracy suites import `sgp131`, so they run with SOURCE on PYTHONPATH; the
# Apple clang 21.0.0 compiler test fails (SGP_CI=1) or skips, never passes silently, on a different compiler.
SOURCE_ENV = {"PYTHONPATH": str(SOURCE)}
SUITE += [
    ("1.3.1 cold UI owner stages", SOURCE, ["-m", "unittest", "sgp131.test_controls_portable_stages", "sgp131.test_identity", "sgp131.test_rematches_stage", "sgp131.test_activation", "sgp131.test_activation_forwarding"], SOURCE_ENV),
]
SUITE_CLASSE_B += [
    ("1.3.1 final title identity ROM", SOURCE, ["-m", "unittest", "sgp131.test_identity_rom"], SOURCE_ENV),
    ("1.3.1 full rematches chain ROM", SOURCE, ["-m", "unittest", "sgp131.test_rematches_stage_rom"], SOURCE_ENV),
    ("1.3.1 evidence-bound activation ROM", SOURCE, ["-m", "unittest", "sgp131.test_activation_rom"], SOURCE_ENV),
    ("1.3.1 controls and portable chain ROM", SOURCE, ["-m", "unittest", "sgp131.test_controls_portable_stages_rom"], SOURCE_ENV),
]
SUITE += [
    ("1.3.1 modern moves", SOURCE, ["-m", "unittest", "sgp131.test_modern_moves"], SOURCE_ENV),
    ("1.3.1 map resource envelopes", SOURCE, ["-m", "unittest", "sgp131.test_map_resources"], SOURCE_ENV),
    ("1.3.1 inherited repair arithmetic and registration", SOURCE, ["-m", "unittest", "sgp131.test_lullaby", "sgp131.test_legacy_stage"], SOURCE_ENV),
    ("1.3.1 legendary scene-version selector", SOURCE, ["-m", "unittest", "sgp131.test_legendary_scene_version_rom.SelectorUnitTests"], SOURCE_ENV),
    ("1.3.1 AI scoring", SOURCE, ["-m", "unittest", "sgp131.test_ai_scoring"], SOURCE_ENV),
    ("1.3.1 Fairy AI helper", SOURCE, ["-m", "unittest", "sgp131.test_fairy_ai"], SOURCE_ENV),
    ("1.3.1 modern abilities", SOURCE, ["-m", "unittest", "sgp131.test_modern_abilities"], SOURCE_ENV),
    ("1.3.1 Keen Eye text", SOURCE / "features/modern-accuracy/test", ["-m", "unittest", "test_text"], SOURCE_ENV),
    ("1.3.1 archive deltas", SOURCE, ["-m", "unittest", "sgp131.test_archives"], SOURCE_ENV),
    ("1.3.1 Safari lifetime oracle", SOURCE, ["-m", "unittest", "sgp131.test_safari_lifetime.LifetimeOracle", "sgp131.test_safari_lifetime.ArchiveRegistration"], SOURCE_ENV),
    ("1.3.1 BLZ input boundaries", SOURCE, ["-m", "unittest", "sgp131.test_blz_security"], SOURCE_ENV),
    ("1.3.1 Pokéathlon counter bounds", SOURCE, ["-m", "unittest", "sgp131.test_pokeathlon"], SOURCE_ENV),
]
# These methods have no ROM, external reference checkout, or production compiler
# requirement. Their neighboring methods in the same modules have separate
# private-input or production-toolchain requirements. Keep the selection exact.
AUDITED_SYNTHETIC_SELECTORS = [
    "sgp131.test_battle_tower_wrap.BattleTowerWrapTests.test_repair_passes_full_width_rounds_and_preserves_low_rounds",
    "sgp131.test_dark_cave_rock_rom.DarkCaveRockRomTests.test_overlap_detector_rejects_a_water_coded_rock",
    "sgp131.test_evolution_fixes.EvolutionDeltas.test_legacy_stage_owns_evolution_archive_once",
    "sgp131.test_gts_empty_rom.GtsEmptyRomTests.test_clean_empty_response_blocks_select",
    "sgp131.test_gts_empty_rom.GtsEmptyRomTests.test_populated_valid_record_is_the_healthy_result_control",
    "sgp131.test_gts_empty_rom.GtsEmptyRomTests.test_communication_error_never_exposes_select",
    "sgp131.test_gts_empty_rom.GtsEmptyRomTests.test_one_zero_filled_record_reaches_select_without_identity",
    "sgp131.test_pursuit_script.PursuitScriptDelta.test_field_mask_control_matrix_distinguishes_bug_from_restore",
    "sgp131.test_pursuit_script.PursuitScriptDelta.test_legacy_stage_owns_the_fix_once",
    "sgp131.test_rtc_daily_contract_rom.RtcSourceContractTests.test_clock_change_reanchors_without_consuming_daily_flags",
    "sgp131.test_rtc_daily_contract_rom.RtcSourceContractTests.test_natural_rollover_clears_daily_flags_and_rotates_buena",
    "sgp131.test_rtc_daily_contract_rom.RtcSourceContractTests.test_bug_contest_weekday_gate_is_not_an_rtc_penalty_gate",
    "sgp131.test_rtc_daily_contract_rom.RtcSourceContractTests.test_backward_day_reanchors_without_daily_rollover",
    "sgp131.test_rtc_daily_contract_rom.RtcSourceContractTests.test_same_day_save_is_a_negative_control_for_buena_rotation",
    "sgp131.test_trainer_fixes.Registration",
    "sgp131.test_uturn_script.UTurnScriptDelta.test_snapshot_commands_encode_effective_item_and_modifier",
    "sgp131.test_traded_egg.TradedEggPatchTests.test_four_ot_pid_cases_replace_only_the_palette_classification",
]
SUITE.append(("1.3.1 audited synthetic regressions", SOURCE,
              ["-m", "unittest", *AUDITED_SYNTHETIC_SELECTORS], SOURCE_ENV))

# These modules are intentionally outside the public runner. New test modules
# must either enter SUITE/SUITE_CLASSE_B or receive a reviewed classification;
# test_run_tests.py checks this inventory. A local-only entry is not CI coverage.
LOCAL_ONLY_SGP131_TESTS = {
    'test_bag_alloc_rom': 'private candidate and native runtime',
    'test_bag_foreign': 'production compiler and private candidate',
    'test_bag_foreign_consumer': 'private V4 fixture and production compiler',
    'test_kate_script_rom': 'private candidate',
    'test_nosepass_head_smash_rom': 'private candidate',
    'test_plus_save_rom': 'private candidate and raw save fixtures',
    'test_pokeathlon_rom': 'private candidate',
    'test_pokegear_autocull_rom': 'uninstalled design and private candidate',
    'test_pressure_switch_scripts': 'private V4 and reference inputs',
    'test_status_icon_script': 'private V4 and reference inputs',
    'test_traded_egg_rom': 'private candidate and production compiler',
    'test_transform_reload': 'production compiler identity and native runtime',
    'test_type_chart': 'private candidate and native runtime',
    'test_type_consumers': 'production compiler identity and native runtime',
}
# c8 features (Summary controls, portable box, rematch variants, gift script fixes). Class A: these suites run tests without any
# game file; their ROM cases skip without the V4 candidates. The *_rom modules are Class B below.
SUMMARY_CONTROLS_ENV = {"PYTHONPATH": os.pathsep.join([str(SOURCE), str(SOURCE / "features/summary-controls/test")])}
PORTABLE_BOX_ENV = {"PYTHONPATH": os.pathsep.join([str(SOURCE), str(SOURCE / "features/portable-box/test")])}
REMATCH_VARIANTS_ENV = {"PYTHONPATH": os.pathsep.join([str(SOURCE), str(SOURCE / "features/rematch-variants/test")])}
SUITE += [
    ("1.3.1 Summary controls feature", SOURCE / "features/summary-controls/test", ["-m", "unittest", "discover", "-p", "test_*.py"], SUMMARY_CONTROLS_ENV),
    ("1.3.1 Summary controls package", SOURCE, ["-m", "unittest", "sgp131.test_controls"], SOURCE_ENV),
    ("1.3.1 portable box feature", SOURCE / "features/portable-box/test", ["-m", "unittest", "discover", "-p", "test_*.py"], PORTABLE_BOX_ENV),
    ("1.3.1 portable box package", SOURCE, ["-m", "unittest", "sgp131.test_portable"], SOURCE_ENV),
    ("1.3.1 rematch variants feature", SOURCE / "features/rematch-variants/test", ["-m", "unittest", "discover", "-p", "test_*.py"], REMATCH_VARIANTS_ENV),
    ("1.3.1 rematch variants package", SOURCE, ["-m", "unittest", "sgp131.test_rematches"], SOURCE_ENV),
    ("1.3.1 gift script archives", SOURCE, ["-m", "unittest", "sgp131.test_gifts_archives"], SOURCE_ENV),
    ("1.3.1 gift script audit", SOURCE, ["-m", "unittest", "sgp131.test_gifts_audit"], SOURCE_ENV),
    ("1.3.1 gift script fixes", SOURCE, ["-m", "unittest", "sgp131.test_gifts_scripts"], SOURCE_ENV),
]
SUITE_CLASSE_B += [
    ("1.3.1 immutable V4 baseline", SOURCE, ["-m", "unittest", "sgp131.test_baseline_rom"]),
    ("1.3.1 Azurill gender ROM reproducer", SOURCE, ["-m", "unittest", "sgp131.test_azurill_gender_rom"], SOURCE_ENV),
    ("1.3.1 GB Sounds evolution component reproducer", SOURCE, ["-m", "unittest", "sgp131.test_gb_sounds_evolution_rom"], SOURCE_ENV),
    ("1.3.1 Wonder Card seal OOB reproducer and repair", SOURCE, ["-m", "unittest", "sgp131.test_wonder_card_seal_rom", "sgp131.test_wonder_card_fix_rom"], SOURCE_ENV),
    ("1.3.1 inherited script and native repairs", SOURCE, ["-m", "unittest", "sgp131.test_legacy_scripts", "sgp131.test_legacy_archives", "sgp131.test_gs_cup_guard", "sgp131.test_lullaby_rom"], SOURCE_ENV),
    ("1.3.1 legendary scene guard", SOURCE, ["-m", "unittest", "sgp131.test_legendary_scenes", "sgp131.test_legendary_scene_rom"], SOURCE_ENV),
    ("1.3.1 legendary scene-version ROM repair", SOURCE, ["-m", "unittest", "sgp131.test_legendary_scene_version_rom.ExactRomTests"], SOURCE_ENV),
    ("1.3.1 battle animation ROM repairs", SOURCE, ["-m", "unittest", "sgp131.test_battle_animation_facade_rom", "sgp131.test_battle_animation_dynamicpunch_rom", "sgp131.test_battle_animation_helping_hand_rom", "sgp131.test_battle_animation_strength_rom", "sgp131.test_battle_animation_spit_up_rom"], SOURCE_ENV),
    ("1.3.1 Giratina PC form ROM repair", SOURCE, ["-m", "unittest", "sgp131.test_giratina_pc_form_rom"], SOURCE_ENV),
    ("1.3.1 Route 43/44 invisible-grass ROM repair", SOURCE, ["-m", "unittest", "sgp131.test_invisible_grass_rom"], SOURCE_ENV),
    ("1.3.1 Waterfall descent-facing ROM repair", SOURCE, ["-m", "unittest", "sgp131.test_waterfall_facing_rom"], SOURCE_ENV),
    ("1.3.1 follower menu-jump ROM repair", SOURCE, ["-m", "unittest", "sgp131.test_follower_menu_jump_rom"], SOURCE_ENV),
    ("1.3.1 Bag compact-position ROM repair", SOURCE, ["-m", "unittest", "sgp131.test_bag_view_position_rom"], SOURCE_ENV),
    ("1.3.1 Lottery Number ROM repair", SOURCE, ["-m", "unittest", "sgp131.test_lottery_id_rom"], SOURCE_ENV),
    ("1.3.1 Safari script ROM repairs", SOURCE, ["-m", "unittest", "sgp131.test_safari_lifetime.CurrentCandidateReproducer", "sgp131.test_safari_defeat_whiteout_rom"], SOURCE_ENV),
    ("1.3.1 fishing, Fly, Soul Dew, Wonder Card and IGT native repairs", SOURCE, ["-m", "unittest", "sgp131.test_fishing", "sgp131.test_victory_road_fly_rom", "sgp131.test_soul_dew_rom", "sgp131.test_igt", "sgp131.test_legacy_native"], SOURCE_ENV),
    ("1.3.1 native resident ownership audit", SOURCE, ["-m", "unittest", "sgp131.test_reserve_rom"]),
    ("1.3.1 native settings owners", SOURCE / "features/settings-ui/test", ["-m", "unittest", "test_owners_rom"]),
    ("1.3.1 canonical settings render plan", SOURCE / "features/settings-ui/test", ["-m", "unittest", "test_render_rom"]),
    ("1.3.1 native settings pixel painter", SOURCE / "features/settings-ui/test", ["-m", "unittest", "test_painter_rom"]),
    ("1.3.1 native Guide rendering", SOURCE / "features/guide-ui/test", ["-m", "unittest", "test_guide_rom"]),
    ("1.3.1 native physical sampler", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_physical_rom"], SOURCE_ENV),
    ("1.3.1 native checked UI heap", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_heap_rom"], SOURCE_ENV),
    ("1.3.1 native persistent UI allocation", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_persistent_rom"]),
    ("1.3.1 canonical UI resources", SOURCE, ["-m", "unittest", "sgp131.test_ui_resource_rom"]),
    ("1.3.1 canonical UI catalogue", SOURCE, ["-m", "unittest", "sgp131.test_ui_copy_rom"]),
    ("1.3.1 native UI resource reader", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_resource_rom"]),
    ("1.3.1 native Guide resource reader", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_guide_resource_rom"]),
    ("1.3.1 native UI backgrounds", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_bg_rom"], SOURCE_ENV),
    ("1.3.1 native UI font", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_font_rom"]),
    ("1.3.1 native UI module lifecycle", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_module_rom"]),
    ("1.3.1 native UI caller lifecycle", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_bridge_rom"]),
    ("1.3.1 native field Guide lifecycle", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_fieldbook_rom"], SOURCE_ENV),
    ("1.3.1 native Scene admission", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_scene_admission_rom"]),
    ("1.3.1 native composed UI Scene", SOURCE / "features/ui-native/test", ["-m", "unittest", "test_scene_rom"]),
    ("1.3.1 canonical Guide content", SOURCE, ["-m", "unittest", "sgp131.test_guide_content_rom"]),
    ("1.3.1 canonical UI installation", SOURCE, ["-m", "unittest", "sgp131.test_ui_rom"]),
    ("1.3 native event flags", SOURCE, ["-m", "unittest", "sgp13.test_event_flags_rom"]),
    ("1.3 real species statistics", SOURCE, ["-m", "unittest", "sgp13.test_species.ActualTableTests"]),
    ("1.3 native shiny constructors", SOURCE / "features/shiny/test", ["-m", "unittest", "test_native_constructor", "test_native_options", "test_native_install.CartridgeInstallTests"]),
    ("1.3 native shiny text widths", SOURCE / "features/plus-ui/test", ["-m", "unittest", "test_extended.ExtendedText"]),
    ("1.3 real save feedback callers", SOURCE, ["-m", "unittest", "sgp13.test_save_ui_rom"]),
    ("1.3 cartridge and hooks", SOURCE, ["-m", "unittest", "sgp13.test_space.RealRomTests", "sgp13.test_caught_arm", "sgp13.test_teams_arm", "sgp13.test_mew_rom"]),
    ("1.3 guide composition", SOURCE / "features/field-guide/test", ["-m", "unittest", "test_install_ranges"]),
    ("1.3 native training", SOURCE / "features/training-native/test", ["-m", "unittest", "test_native"]),
    ("1.3.1 modern moves ROM", SOURCE, ["-m", "unittest", "sgp131.test_modern_moves_rom"], SOURCE_ENV),
    ("1.3.1 AI scoring ROM", SOURCE, ["-m", "unittest", "sgp131.test_ai_scoring_rom",
                                      "sgp131.test_ai_water_spout_rom",
                                      "sgp131.test_ai_metal_burst_rom",
                                      "sgp131.test_ai_facade_rom",
                                      "sgp131.test_ai_thunder_rom"], SOURCE_ENV),
    ("1.3.1 Fairy AI helper ROM", SOURCE, ["-m", "unittest", "sgp131.test_fairy_ai_rom"], SOURCE_ENV),
    ("1.3.1 modern abilities ROM", SOURCE, ["-m", "unittest", "sgp131.test_modern_abilities_rom"], SOURCE_ENV),
    ("1.3.1 Keen Eye native", SOURCE / "features/modern-accuracy/test", ["-m", "unittest", "test_native"], SOURCE_ENV),
    ("1.3.1 Keen Eye hooks", SOURCE / "features/modern-accuracy/test", ["-m", "unittest", "test_hooks"], SOURCE_ENV),
    ("1.3.1 Keen Eye text ROM", SOURCE / "features/modern-accuracy/test", ["-m", "unittest", "test_text_rom"], SOURCE_ENV),
    ("1.3.1 mechanics after UI", SOURCE, ["-m", "unittest", "sgp131.test_mechanics_stages_rom"], SOURCE_ENV),
    ("1.3.1 archive deltas ROM", SOURCE, ["-m", "unittest", "sgp131.test_archives_rom"], SOURCE_ENV),
    ("1.3.1 Summary controls ROM", SOURCE, ["-m", "unittest", "sgp131.test_controls_rom"], SOURCE_ENV),
    ("1.3.1 portable box ROM", SOURCE, ["-m", "unittest", "sgp131.test_portable_rom"], SOURCE_ENV),
    ("1.3.1 rematch variants ROM", SOURCE, ["-m", "unittest", "sgp131.test_rematches_rom"], SOURCE_ENV),
    ("1.3.1 gift script audit ROM", SOURCE, ["-m", "unittest", "sgp131.test_gifts_audit_rom"], SOURCE_ENV),
]

CONTA = re.compile(r"^Ran (\d+) tests?", re.M)
SALTI = re.compile(r"skipped=(\d+)")


# Closed legacy test suites whose owned native producers need the observed
# protected host compiler. Production commands never enter this test-only seam.
NONPRODUCTION_NATIVE_SUITES = {
    '1.3.1 read-only training UI owner': ('sgp13.training', 'sgp13.shiny_core', 'sgp13.shiny'),
    '1.3.1 checked shiny UI owner': ('sgp13.training', 'sgp13.shiny_core', 'sgp13.shiny'),
    '1.3.1 atomic settings owners': ('sgp13.training', 'sgp13.shiny_core', 'sgp13.shiny'),
    '1.3 shiny core and adapters': ('sgp13.shiny_core', 'sgp13.shiny'),
    '1.3 training adapters': ('sgp13.training', 'sgp131.bag_foreign'),
    '1.3 native guide': ('sgp13.guide',),
    '1.3 Plus presentation': ('sgp13.plus_ui', 'sgp13.shiny_core'),
    '1.3 native shiny constructors': ('sgp13.shiny', 'sgp13.shiny_core'),
    '1.3.1 portable box ROM': ('sgp131.portable',),
    '1.3.1 rematch variants ROM': ('sgp131.rematches',),
}
NONPRODUCTION_NATIVE_COMMAND = """import importlib, sys, unittest
source = sys.argv.pop(1)
names = sys.argv.pop(1).split(',')
sys.path.insert(0, source)
from sgp131.test_ui import nonproduction_native_compiler_contract
owners = [importlib.import_module(name) for name in names]
print('Nonproduction protected host compiler contract: ' + ', '.join(names), flush=True)
with nonproduction_native_compiler_contract(*owners):
    unittest.main(module=None, argv=['unittest', *sys.argv[1:]])
"""


def esegui(nome, cwd, argv, env=None, classe_b=False):
    amb = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    amb.update(env or {})
    if argv[:3] == ['-m', 'unittest', 'discover']:
        argv = [*argv[:3], '-v', *argv[3:]]
    elif argv[:2] == ['-m', 'unittest']:
        # Verbose output is captured, then only skip reasons are printed on a
        # successful suite. Default unittest output gives a count but no reason.
        argv = [*argv[:2], '-v', *argv[2:]]
    if nome in NONPRODUCTION_NATIVE_SUITES:
        if argv[:2] != ['-m', 'unittest']:
            raise ValueError('host native contract requires the unchanged unittest entry point')
        owners = NONPRODUCTION_NATIVE_SUITES[nome]
        argv = ['-c', NONPRODUCTION_NATIVE_COMMAND, str(SOURCE), ','.join(owners), *argv[2:]]
    started = time.perf_counter()
    r = subprocess.run([sys.executable, *argv], cwd=str(cwd), env=amb,
                       text=True, capture_output=True)
    elapsed_seconds = round(time.perf_counter() - started, 3)
    uscita = r.stdout + r.stderr
    m = CONTA.search(uscita)
    unittest_ran = int(m.group(1)) if m else 0
    s = SALTI.search(uscita)
    saltati = int(s.group(1)) if s else 0
    # A module-level skip reports "Ran 0 tests" with skipped=N: those N tests
    # were collected, not run.
    n = max(unittest_ran, saltati)
    ok = r.returncode == 0
    if r.returncode < 0:
        print("  %-26s   child terminated by %s; test counts unavailable" %
              (nome, signal.Signals(-r.returncode).name))
    if not classe_b and n == 0 and r.returncode == 0:
        # `unittest discover` on a folder with no test file exits 0. A suite
        # that collects nothing is not a suite that passes.
        ok = False
        print("  %-26s   no test collected — the suite is empty or was not found" % nome)
    skipped_methods = len(re.findall(r"^test_.* \.\.\. skipped [\"']", uscita, re.M))
    if (not classe_b and n > 0 and r.returncode == 0
            and (unittest_ran == 0 or skipped_methods == unittest_ran)):
        # Subtest skips are indented and do not count as skipped test methods.
        # A passing method with one skipped subtest may still show skipped=1.
        ok = False
        print("  %-26s   all collected Class A tests skipped" % nome)
    executed_methods = max(0, unittest_ran - skipped_methods)
    print("  %-26s %3d methods ran, %2d skip events   %s   %.3fs" %
          (nome, executed_methods, saltati, "ok" if ok else "FAILED", elapsed_seconds))
    if saltati:
        reasons = Counter()
        for line in uscita.splitlines():
            _, marker, literal = line.partition(" ... skipped ")
            if marker:
                try:
                    reason = ast.literal_eval(literal)
                except (SyntaxError, ValueError):
                    reason = literal
                if isinstance(reason, str):
                    reasons[reason] += 1
        for reason, count in reasons.most_common(8):
            print("    skip reason (%d): %s" % (count, reason[:240]))
        if len(reasons) > 8:
            print("    %d further distinct skip reasons" % (len(reasons) - 8))
        if not reasons:
            print("    skip reasons unavailable from this suite's unittest output")
    if not ok:
        print(uscita[-4000:])
    return ok, n, saltati, elapsed_seconds, executed_methods


def compila_opzioni(tmp: Path):
    """Build the options page payload and lay the shipped text blobs beside it.

    Returns `(folder or None, reason or None, missing_compiler)`. The reason is
    kept so the summary can say why the suite did not run: it used to be printed
    and then dropped, and the suite disappeared from the totals and from the
    JSON.

    The third value is the one that matters. A missing compiler and a *broken
    build* are not the same event: the first is "this machine cannot run the
    suite" — a skip, unless CI says every machine must have one; the second is
    "the shipped sources no longer compile", which is a failure everywhere, on
    every machine, CI or not. Both used to take the same branch and be reported
    as "no usable ARM compiler", so a real compile error was quietly downgraded
    to a skip on every developer machine."""
    uscita = tmp / "options"
    uscita.mkdir(parents=True, exist_ok=True)
    if shutil.which("clang") is None:
        return None, "no ARM compiler: clang is not on PATH", True
    r = subprocess.run([sys.executable, str(SOURCE / "features/options/tools/compila.py"),
                        "--uscita", str(uscita)], text=True, capture_output=True)
    if r.returncode != 0:
        tutto = r.stdout + r.stderr
        motivo = (r.stderr.strip().splitlines() or ["(no output)"])[-1]
        # The child runs clang itself: if *it* is the one that cannot find it,
        # that is still a missing compiler, not a broken source tree.
        assente = ("FileNotFoundError" in tutto
                   or "No such file or directory: 'clang'" in tutto
                   or "command not found" in tutto)
        if assente:
            return None, "no ARM compiler: " + motivo, True
        return None, "the shipped options sources do not build: " + motivo, False
    for f in sorted((SOURCE / "features/options/prove/testi").iterdir()):
        shutil.copy2(f, uscita / f.name)
    return uscita, None, False


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", type=Path, help="write the counts to this file as well")
    ap.add_argument("--richiedi-compilatore", action="store_true",
                    help="fail if the ARM compiler is missing instead of skipping "
                         "the options-page suite (continuous integration sets SGP_CI=1 "
                         "for the same effect)")
    a = ap.parse_args()
    esigi_compilatore = a.richiedi_compilatore or bool(os.environ.get("SGP_CI"))

    print("Class A tests (no game file needed)\n")
    totale = saltati_tot = metodi_tot = 0
    classe_a_ok = True
    dettaglio = []

    # If a game file is available, the reserve suite must not be allowed to skip
    # T2-T5 quietly: arming SGP_RISERVA_COMPLETA turns a missing ROM into a
    # failure. Without a ROM those eight tests are Class B and skip by design.
    ambiente_riserva = {"SGP_RISERVA_COMPLETA": "1"} if os.environ.get("SGP_RISERVA_ROM") else None

    for nome, cwd, argv, *propri in SUITE:
        ok, n, s, elapsed, methods = esegui(nome, cwd, argv,
                                   env=propri[0] if propri else ambiente_riserva if nome == "ARM9 reserve register" else None)
        classe_a_ok &= ok
        totale += n
        saltati_tot += s
        metodi_tot += methods
        dettaglio.append({"suite": nome, "collected": n, "skipped": s,
                          "executed_methods": methods, "ok": ok,
                          "elapsed_seconds": elapsed})

    with tempfile.TemporaryDirectory(prefix="sgp-class-a-") as d:
        tmp = Path(d)
        ok, n, s, elapsed, methods = esegui("native code (Unicorn)", SOURCE / "features/native-core/test",
                                   ["-m", "unittest", "discover", "-p", "test_*.py"])
        classe_a_ok &= ok
        totale += n
        saltati_tot += s
        metodi_tot += methods
        dettaglio.append({"suite": "native code (Unicorn)", "collected": n,
                          "skipped": s, "executed_methods": methods,
                          "ok": ok, "elapsed_seconds": elapsed})

        compile_started = time.perf_counter()
        build, motivo, compilatore_assente = compila_opzioni(tmp)
        compile_seconds = round(time.perf_counter() - compile_started, 3)
        print("  options payload compilation: %.3fs" % compile_seconds)
        if build is not None:
            ok, n, s, elapsed, methods = esegui("options page (Unicorn)", SOURCE / "features/options/test",
                                       ["-m", "unittest", "discover", "-p", "test_*.py"],
                                       env={"SGP_UI_BUILD": str(build)})
            classe_a_ok &= ok
            totale += n
            saltati_tot += s
            metodi_tot += methods
            dettaglio.append({"suite": "options page (Unicorn)", "collected": n,
                              "skipped": s, "executed_methods": methods,
                              "ok": ok, "elapsed_seconds": elapsed,
                              "compile_seconds": compile_seconds})
        else:
            # The suite still has a line, a count and a JSON entry: it used to
            # disappear from all three, and the run said PASS with 95 tests gone.
            collection_started = time.perf_counter()
            n = conta_soltanto("options page (Unicorn)", SOURCE / "features/options/test")
            collection_seconds = round(time.perf_counter() - collection_started, 3)
            # A missing compiler is a skip (a failure only where CI says every
            # machine must have one). A build that *fails* is never a skip: the
            # shipped sources not compiling is a defect on any machine.
            ok = compilatore_assente and not esigi_compilatore
            print("  %-26s %3d methods ran, %2d skip events   %s   0.000s (collection %.3fs)"
                  % ("options page (Unicorn)", 0, n, "skipped" if ok else "FAILED",
                     collection_seconds))
            print("    " + motivo)
            if not ok and compilatore_assente:
                print("    --richiedi-compilatore / SGP_CI=1: a missing compiler is a failure here")
            elif not compilatore_assente:
                print("    this is a build failure, not a missing tool: it fails everywhere")
            classe_a_ok &= ok
            totale += n
            saltati_tot += n
            dettaglio.append({"suite": "options page (Unicorn)", "collected": n,
                              "skipped": n, "executed_methods": 0,
                              "ok": ok, "motivo": motivo,
                              "compilatore_assente": compilatore_assente,
                              "elapsed_seconds": 0.0, "compile_seconds": compile_seconds,
                              "collection_seconds": collection_seconds})

    print("\nClass A: %d legacy collected, %d methods executed, %d skip events — %s"
          % (totale, metodi_tot, saltati_tot,
             "pass" if classe_a_ok else "FAIL"))

    print("\nClass B suites (need a game file: they skip here and in CI)\n")
    dettaglio_b = []
    classe_b_ok = True
    totale_b = saltati_b = metodi_b = 0
    for nome, cwd, argv, *propri in SUITE_CLASSE_B:
        ok, n, s, elapsed, methods = esegui(nome, cwd, argv,
                                   env=propri[0] if propri else None, classe_b=True)
        classe_b_ok &= ok
        totale_b += n
        saltati_b += s
        metodi_b += methods
        dettaglio_b.append({"suite": nome, "collected": n, "skipped": s,
                            "executed_methods": methods, "ok": ok,
                            "elapsed_seconds": elapsed})
    print("  Class B: %d legacy collected, %d methods executed, %d skip events — %s"
          % (totale_b, metodi_b, saltati_b, "pass" if classe_b_ok else "FAIL"))
    print("  (not counted as Class A coverage: set SGP_ROM_DIR to run them)")

    # ONE verdict, printed after everything, and it counts Class B too. The
    # Class A line above used to be the last word and was printed BEFORE the
    # Class B suites ran: a red Class B suite changed the exit code and the JSON
    # but the run still ended on the word PASS. Whoever read the output instead
    # of the exit code read the wrong answer.
    tutto_ok = classe_a_ok and classe_b_ok
    print("\n%d tests collected in all (Class A %d + Class B %d) — %s"
          % (totale + totale_b, totale, totale_b, "PASS" if tutto_ok else "FAIL"))

    if a.json:
        a.json.write_text(json.dumps({"suites": dettaglio, "classe_b": dettaglio_b,
                                      "collected": totale, "skipped": saltati_tot,
                                      "executed_methods": metodi_tot,
                                      "classe_a_ok": classe_a_ok,
                                      "collected_classe_b": totale_b,
                                      "skipped_classe_b": saltati_b,
                                      "executed_methods_classe_b": metodi_b,
                                      "classe_b_ok": classe_b_ok,
                                      "ok": tutto_ok}, indent=2) + "\n")
    return 0 if tutto_ok else 1


def conta_soltanto(nome, cwd):
    """How many tests the suite would collect, without running it: so a suite
    that cannot run still shows its size instead of vanishing."""
    codice = ("import unittest,sys;"
              "print('COLLECTED', unittest.defaultTestLoader.discover('.', pattern='test_*.py').countTestCases())")
    r = subprocess.run([sys.executable, "-c", codice], cwd=str(cwd),
                       text=True, capture_output=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    for riga in (r.stdout + r.stderr).splitlines():
        if riga.startswith("COLLECTED "):
            return int(riga.split()[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
