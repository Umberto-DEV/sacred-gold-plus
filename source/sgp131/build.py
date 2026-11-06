"""Guarded UI, archive/overlay and mechanical composition with independent replay.

The UI writes archive and module deltas once, seeds the final cartridge, and proves
cold Guide retirement. Reserve grants are freshly derived from that exact image.
Confined owner stages default to inert; explicit immutable options may activate
them only with runtime evidence bound to one complete inert candidate. Publication
checks the common all-inert projection after every independent reader has passed.
No save format or persistent identifier changes are introduced by this pipeline.
"""
from contextlib import contextmanager
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path
from . import activation, archives, baseline, cartridge_deltas, mechanics_stages

# The mechanical stages (4a and, later, c8) are registered once in mechanics_stages; the lists below are derived
# from it so the two can never drift (test_build.MechanicsBuildTests cross-checks literal expectations).
STAGES = ('baseline', 'ui', *mechanics_stages.ORDER)
IMPLEMENTED = ('baseline', 'ui', *mechanics_stages.IMPLEMENTED)
# Stages that consume the explicit UI charmap/configuration: UI itself and the mechanical stages
# composed after it. `through` is a prefix: through='abilities' means
# ui -> moves -> ai -> ai-immunities -> abilities; through='gifts' adds
# the archive-only gifts stage, which runs nothing after the UI (one receipt per WRITER stage, see mechanics_stages.writers).
UI_CHAIN = ('ui', *mechanics_stages.IMPLEMENTED)
UI_CASES = ('ui_normal_entry_exit', 'ui_settings_layout', 'ui_guide_layout_commands',
            'ui_physical_touch_equivalence', 'ui_held_rapid_reopen', 'ui_native_suspend_resume',
            'ui_former_guide_defects', 'ui_former_settings_defects', 'ui_shiny_transaction',
            'ui_training_transaction', 'ui_heap_resource_cleanup', 'ui_before_after_observer',
            'ui_performance_publication', 'ui_audio', 'ui_old_save_no_plus', 'ui_old_save_plus_bag')
# Case names are proposals for the Android campaign (ANDROID-SCENARIOS.md A and C); Codex owns the final list.
MOVES_CASES = ('moves_fuocofatuo_summary_85', 'moves_old_save_pp_continuity', 'moves_battle_controls_unchanged',
               'moves_save_cold_restart')
AI_CASES = ('ai_post_ko_replacement', 'ai_no_overflow_control',
            'ai_dual_immunity_switch_choice',
            'ai_dual_immunity_order_and_single_immunity_controls',
            'ai_battle_no_stall', 'ai_save_cold_restart')
DAMAGE_CASES = ('damage_ghost_dragon_neutral', 'damage_ghost_dark_resisted',
                'damage_ghost_chart_322_other_pairs_unchanged')
AI_IMMUNITY_CASES = ('ai_dry_skin_water_immunity', 'ai_dry_skin_non_water_control',
                     'ai_mold_breaker_and_absorb_controls',
                     'ai_arena_trap_airborne_switch',
                     'ai_arena_trap_grounded_iron_ball_gravity_controls',
                     'ai_trapping_shed_shell_contract',
                     'ai_absorb_switch_dry_skin_motor_drive',
                     'ai_absorb_switch_active_ability_and_rng_controls',
                     'ai_dry_skin_save_cold_restart')
# Proposals from ANDROID-SCENARIOS.md B (B1-B9); the final list is Codex's.
ABILITIES_CASES = ('abilities_evasion_ignored', 'abilities_suppressed_keeps_evasion', 'abilities_unaware_unchanged',
                   'abilities_negative_evasion_semantics', 'abilities_accuracy_drop_protection',
                   'abilities_ability_change_follows_effective', 'abilities_old_save_normal_battles',
                   'abilities_summary_text_en_it', 'abilities_battle_performance', 'abilities_save_cold_restart')
# Proposals from c8 ANDROID-SCENARIOS (gift script fixes); the final list is Codex's.
GIFTS_CASES = ('gifts_ribbon_tails_release_player', 'gifts_ribbon_second_try_same_day', 'gifts_eevee_party_five_unchanged',
               'gifts_eevee_party_full_guard', 'gifts_eevee_after_freeing_a_slot', 'gifts_save_cold_restart')
REQUIRED_CASES = {'baseline': ('byte_identity_v4', 'inputs_unchanged', 'sources_unchanged'), 'ui': UI_CASES,
                  'moves': UI_CASES + MOVES_CASES,
                  'ai': UI_CASES + MOVES_CASES + DAMAGE_CASES + AI_CASES,
                  'ai-immunities': UI_CASES + MOVES_CASES + DAMAGE_CASES + AI_CASES + AI_IMMUNITY_CASES,
                  'abilities': UI_CASES + MOVES_CASES + DAMAGE_CASES + AI_CASES + AI_IMMUNITY_CASES + ABILITIES_CASES,
                  'gifts': UI_CASES + MOVES_CASES + DAMAGE_CASES + AI_CASES + AI_IMMUNITY_CASES + ABILITIES_CASES + GIFTS_CASES}
# Runtime acceptance includes inert forwarding controls and the active feature paths.
CONTROLS_CASES = ('controls_inert_forwarding', 'controls_field_pc_modes_views', 'controls_exclusions_lifetime')
LEGACY_CASES = ('legacy_pickup_quantity_once', 'legacy_friend_loss_retry_no_duplicates',
                'legacy_steven_lati_quest_orders_and_full_bag', 'legacy_lullaby_radio_controls',
                'legacy_fishing_rods_phone_radio_swarm_controls', 'legacy_igt_native_training_boundary',
                'legacy_background_interactions_not_hidden_items',
                'legacy_evolution_feebas_beauty_169_170',
                'legacy_evolution_burmy_female_20_male_control',
                'legacy_evolution_combee_female_21_male_control',
                'legacy_evolution_mantyke_remoraid_not_voltorb',
                'legacy_evolution_guide_matches_rules_en_it',
                'legacy_kurt_full_bag_preserves_completed_batch',
                'legacy_plus_options_write_failure_partial_cold',
                'legacy_bag_allocation_null_and_success_controls',
                'legacy_safari_partner_close_before_unload_en_it',
                'legacy_safari_route47_runtime_third_fourth_duo',
                'legacy_safari_final_admin_loss_whiteout_en_it',
                'legacy_safari_final_admin_loss_save_cold_en_it',
                'legacy_safari_save_cold_en_it',
                'legacy_pursuit_ko_restores_field_and_fainted_battler',
                'legacy_ability_volatile_cure_preserves_status_icon',
                'legacy_pressure_delayed_pp_persists_after_manual_switch',
                'legacy_gs_cup_viewer_guard_movement_en_it',
                'legacy_old_save_continue_save_cold_en_it')
REQUIRED_CASES['legacy'] = REQUIRED_CASES['gifts'] + LEGACY_CASES
LEGENDARY_SCENES_CASES = (
    'legendary_hooh_absent_object_created_once',
    'legendary_hooh_existing_object_not_duplicated',
    'legendary_lugia_and_global_showperson_unchanged',
    'legendary_scene_save_cold_en_it',
)
REQUIRED_CASES['legendary-scenes'] = (REQUIRED_CASES['legacy']
                                      + LEGENDARY_SCENES_CASES)
LEGENDARY_SCENE_VERSION_CASES = (
    'legendary_scene_version_exact_en_it',
    'legendary_scene_version_selector_and_abi',
    'legendary_scene_version_runtime_red_green',
)
REQUIRED_CASES['legendary-scene-version'] = (
    REQUIRED_CASES['legendary-scenes'] + LEGENDARY_SCENE_VERSION_CASES)
TRAINER_FIX_CASES = ('trainer_wade_rematches_increase_46_52_68',
                     'trainer_alternate_forms_stats_all_formats_and_turn_order')
REQUIRED_CASES['trainer-fixes'] = (REQUIRED_CASES['legendary-scene-version']
                                   + TRAINER_FIX_CASES)
POKEATHLON_CASES = ('pokeathlon_friendship_254_255_control',
                    'pokeathlon_friendship_256_257_no_wrap',
                    'pokeathlon_friendship_455_456_493_boundaries',
                    'pokeathlon_trust_direct_path_unchanged',
                    'pokeathlon_summary_sibling_fields_canaries',
                    'pokeathlon_old_save_continue_save_cold_en_it')
REQUIRED_CASES['pokeathlon'] = REQUIRED_CASES['trainer-fixes'] + POKEATHLON_CASES
TRADED_EGG_CASES = ('traded_egg_final_ot_shiny_palette',
                    'traded_egg_normal_and_nontraded_controls',
                    'traded_egg_overlay95_replay_and_mutants',
                    'traded_egg_save_cold_link_acceptance')
REQUIRED_CASES['traded-egg'] = REQUIRED_CASES['pokeathlon'] + TRADED_EGG_CASES
BAG_FOREIGN_CASES = ('bag_foreign_live_extra_blocks_native_commit',
                     'bag_foreign_io_failure_live_extra_blocks_native_commit',
                     'bag_foreign_empty_and_native_cells_commit',
                     'bag_foreign_destination_bytes_preserved',
                     'bag_foreign_save_cold_en_it')
REQUIRED_CASES['bag-foreign'] = REQUIRED_CASES['traded-egg'] + BAG_FOREIGN_CASES
BAG_VIEW_POSITION_CASES = ('bag_view_single_berry_compact_slot',
                           'bag_view_all_pockets_and_single_items_controls',
                           'bag_view_adjacent_flag_setter_callsite',
                           'bag_view_save_cold_en_it')
REQUIRED_CASES['bag-view-position'] = (REQUIRED_CASES['bag-foreign']
                                       + BAG_VIEW_POSITION_CASES)
LOTTERY_ID_CASES = ('lottery_id_setter_halves_en_it',
                    'lottery_id_daily_roll_canaries',
                    'lottery_id_save_cold_en_it')
REQUIRED_CASES['lottery-id'] = REQUIRED_CASES['bag-view-position'] + LOTTERY_ID_CASES
BATTLE_TOWER_WRAP_CASES = ('battle_tower_round_255_256_boundary_en_it',
                           'battle_tower_palmer_and_mode_controls',
                           'battle_tower_save_cold_en_it')
REQUIRED_CASES['battle-tower-wrap'] = (REQUIRED_CASES['lottery-id']
                                        + BATTLE_TOWER_WRAP_CASES)
FACADE_ANIMATION_CASES = ('facade_scale_tasks_10_frame_en_it',
                          'facade_delay_and_sound_10_frame',
                          'facade_rendered_repetition_controls')
REQUIRED_CASES['battle-animation-facade'] = (REQUIRED_CASES['battle-tower-wrap']
                                              + FACADE_ANIMATION_CASES)
DYNAMICPUNCH_ANIMATION_CASES = ('dynamicpunch_shake_scheduler_en_it',
                                'dynamicpunch_delay_4_member_and_replay',
                                'dynamicpunch_rendered_repetition_controls')
REQUIRED_CASES['battle-animation-dynamicpunch'] = (
    REQUIRED_CASES['battle-animation-facade'] + DYNAMICPUNCH_ANIMATION_CASES)
HELPING_HAND_ANIMATION_CASES = ('helping_hand_loop_scheduler_en_it',
                                'helping_hand_delay_inside_loop_member_and_replay',
                                'helping_hand_rendered_repetition_controls')
REQUIRED_CASES['battle-animation-helping-hand'] = (
    REQUIRED_CASES['battle-animation-dynamicpunch'] + HELPING_HAND_ANIMATION_CASES)
STRENGTH_ANIMATION_CASES = ('strength_phase_8_9_10_11_en_it',
                            'strength_member_10_to_8_and_replay',
                            'strength_rendered_repetition_controls')
REQUIRED_CASES['battle-animation-strength'] = (
    REQUIRED_CASES['battle-animation-helping-hand'] + STRENGTH_ANIMATION_CASES)
SPIT_UP_ANIMATION_CASES = ('spit_up_task_cleanup_en_it',
                           'spit_up_mutant_subtract_1_3',
                           'spit_up_rendered_repetition_controls')
REQUIRED_CASES['battle-animation-spit-up'] = (
    REQUIRED_CASES['battle-animation-strength'] + SPIT_UP_ANIMATION_CASES)
GIRATINA_PC_FORM_CASES = ('giratina_pc_item_change_both_directions_en_it',
                          'giratina_pc_non_giratina_and_party_controls',
                          'giratina_pc_save_cold_en_it')
REQUIRED_CASES['giratina-pc-form'] = (
    REQUIRED_CASES['battle-animation-spit-up'] + GIRATINA_PC_FORM_CASES)
INVISIBLE_GRASS_CASES = ('invisible_grass_route43_44_en_it',
                         'invisible_grass_six_words_and_controls',
                         'invisible_grass_archive_replay_and_mutants')
REQUIRED_CASES['invisible-grass'] = (
    REQUIRED_CASES['giratina-pc-form'] + INVISIBLE_GRASS_CASES)
WATERFALL_FACING_CASES = ('waterfall_facing_exact_en_it',
                          'waterfall_facing_order_abi_and_controls',
                          'waterfall_facing_replay_and_mutants')
REQUIRED_CASES['waterfall-facing'] = (
    REQUIRED_CASES['invisible-grass'] + WATERFALL_FACING_CASES)
FOLLOWER_MENU_JUMP_CASES = ('follower_menu_jump_command21_en_it',
                            'follower_menu_jump_0_1_2_3_returns_and_reset',
                            'follower_menu_jump_stationary_and_composed_f02')
REQUIRED_CASES['follower-menu-jump'] = (
    REQUIRED_CASES['waterfall-facing'] + FOLLOWER_MENU_JUMP_CASES)
REQUIRED_CASES['controls'] = (REQUIRED_CASES['follower-menu-jump']
                              + CONTROLS_CASES)
PORTABLE_CASES = ('portable_inert_forwarding', 'portable_r_touch_modes', 'portable_native_operations',
                  'portable_follower_hm_surf_policy', 'portable_denied_contexts',
                  'portable_50_cycles_heap', 'portable_save_cold_restart')
REQUIRED_CASES['portable'] = REQUIRED_CASES['controls'] + PORTABLE_CASES
REMATCHES_CASES = ('rematches_inert_forwarding', 'rematches_phone_dojo_contexts',
                   'rematches_normal_plus_variants', 'rematches_runtime_heap', 'rematches_save_cold_restart')
REQUIRED_CASES['rematches'] = REQUIRED_CASES['portable'] + REMATCHES_CASES
UTURN_FLINCH_CASES = (
    'uturn_outgoing_kings_rock_incoming_empty',
    'uturn_outgoing_empty_incoming_kings_rock',
    'uturn_razor_fang_klutz_embargo_modifiers',
    'uturn_rng_failure_damage_move_target_controls',
    'uturn_shell_bell_life_orb_pursuit_doubles_controls',
    'uturn_same_build_link_save_cold_en_it',
)
REQUIRED_CASES['uturn-flinch'] = (REQUIRED_CASES['rematches']
                                  + UTURN_FLINCH_CASES)
REQUIRED_CASES['identity'] = (REQUIRED_CASES['uturn-flinch']
                              + ('identity_title_and_settings_131',))
UI_SCRATCH_LIMIT = 256 * 1024**2
UI_APPEND_LIMIT = 16 * 1024**2
RECEIPT_LIMIT = 4 * 1024**2
UI_CONFIG_LIMIT = 64 * 1024
CHARMAP_LIMIT = 1024 * 1024


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def _input(path, limit):
    if path is None:
        raise ValueError('explicit UI charmap and configuration required')
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('UI input symlink forbidden')
    if not path.is_file() or not 0 < path.stat().st_size <= limit:
        raise ValueError('UI input size limit or missing file')
    with path.open('rb') as handle:
        data = handle.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise ValueError('UI input size limit')
    return data, {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def snapshot_ui_inputs(charmap, ui_config):
    from . import guide_content, ui_compile
    if charmap is None or ui_config is None:
        raise ValueError('explicit UI charmap and configuration required')
    chars, char_record = _input(charmap, CHARMAP_LIMIT)
    raw, config_record = _input(ui_config, UI_CONFIG_LIMIT)
    if char_record['sha256'] != guide_content.CHARMAP_SHA256:
        raise ValueError('UI charmap identity mismatch')
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('duplicate candidate configuration field')
            value[key] = item
        return value
    config = ui_compile.validate_config(json.loads(raw, object_pairs_hook=pairs))
    return {'records': {'charmap': char_record, 'ui_config': config_record},
            'charmap': chars, 'ui_config': raw, 'config': config}


def refresh_ui_inputs(inputs):
    records = inputs['records']
    fresh = snapshot_ui_inputs(records['charmap']['path'], records['ui_config']['path'])
    if fresh != inputs:
        raise ValueError('UI input changed during operation')


@contextmanager
def ui_workspace(scratch, inputs, directory_fd=None):
    scratch = Path(scratch) if directory_fd is not None else Path(scratch).absolute()
    # Never adopt or prune a pre-existing path, including a symlink.
    if shutil.disk_usage(scratch.parent).free - UI_SCRATCH_LIMIT < 10 * 1024**3:
        raise ValueError('UI scratch disk budget would leave less than ten GiB free')
    parent_fd = -1
    scratch_fd = -1
    created = directory_fd is None
    try:
        if created:
            parent_fd = os.open(scratch.parent, os.O_RDONLY | os.O_DIRECTORY |
                                getattr(os, 'O_NOFOLLOW', 0))
            os.mkdir(scratch.name, 0o700, dir_fd=parent_fd)
            scratch_fd = os.open(scratch.name, os.O_RDONLY | os.O_DIRECTORY |
                                 getattr(os, 'O_NOFOLLOW', 0), dir_fd=parent_fd)
        else:
            scratch_fd = os.dup(directory_fd)
            if os.listdir(scratch_fd):
                raise ValueError('pinned UI scratch must be empty')
        identity = os.fstat(scratch_fd)
        if (not stat.S_ISDIR(identity.st_mode) or identity.st_uid != os.getuid()
                or identity.st_mode & 0o077):
            raise ValueError('UI scratch is not a private owned directory')
        _write_workspace_file(scratch_fd, 'ui-candidate.json', inputs['ui_config'])
        charmap = scratch / 'charmap.txt'
        _write_workspace_file(scratch_fd, 'charmap.txt', inputs['charmap'])
        _require_workspace_path(scratch, identity)
        yield charmap
        for name, expected in (('ui-candidate.json', inputs['ui_config']), ('charmap.txt', inputs['charmap'])):
            actual = _read_workspace_file(scratch_fd, name, len(expected))
            if actual != expected:
                raise ValueError('consumed UI input snapshot changed')
    finally:
        if scratch_fd >= 0:
            _remove_workspace_contents(scratch_fd)
            os.fsync(scratch_fd)
            if created:
                try:
                    current = os.stat(scratch.name, dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    current = None
                if (current is not None and (current.st_dev, current.st_ino)
                        == (os.fstat(scratch_fd).st_dev, os.fstat(scratch_fd).st_ino)):
                    os.rmdir(scratch.name, dir_fd=parent_fd)
                    os.fsync(parent_fd)
            os.close(scratch_fd)
        if parent_fd >= 0:
            os.close(parent_fd)


def _require_workspace_path(path, identity):
    current = os.stat(path, follow_symlinks=False)
    if (not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != (identity.st_dev, identity.st_ino)):
        raise ValueError('UI scratch path identity changed')


def _write_workspace_file(directory_fd, name, data):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                 getattr(os, 'O_NOFOLLOW', 0), 0o600, dir_fd=directory_fd)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError('short UI scratch write')
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_workspace_file(directory_fd, name, limit):
    fd = os.open(name, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory_fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size < 0 or info.st_size > limit:
            raise ValueError('UI scratch input size/type changed')
        data = bytearray()
        while len(data) < info.st_size:
            chunk = os.read(fd, info.st_size - len(data))
            if not chunk:
                raise ValueError('UI scratch input truncated')
            data.extend(chunk)
        if os.read(fd, 1):
            raise ValueError('UI scratch input grew')
        return bytes(data)
    finally:
        os.close(fd)


def _remove_workspace_contents(directory_fd):
    """Recursively remove only entries reached through a pinned directory."""
    for name in os.listdir(directory_fd):
        info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY |
                            getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory_fd)
            try:
                _remove_workspace_contents(child)
                os.fsync(child)
            finally:
                os.close(child)
            os.rmdir(name, dir_fd=directory_fd)
        else:
            os.unlink(name, dir_fd=directory_fd)


def ui_composition(receipt):
    return {'stage': 'ui', 'receipt_sha256': hashlib.sha256(canonical(receipt)).hexdigest(),
            'static_verified': True, 'runtime_acceptance': 'pending'}


def composition_for(receipts):
    """Composition record derived from recorded receipts only: [UI result, wrapped mechanics receipts...]."""
    ui = ui_composition(receipts[0])
    if len(receipts) == 1:
        return ui
    return {'stage': receipts[-1]['stage'], 'ui': ui, 'static_verified': True, 'runtime_acceptance': 'pending',
            'mechanics': [{'stage': r['stage'], 'receipt_sha256': hashlib.sha256(canonical(r)).hexdigest()}
                          for r in receipts[1:]]}


def complete_deltas(base, language, charmap, names, supplied):
    """Caller deltas plus the archive producers the chain needs and the caller did not bring (re-run on the V4)."""
    have = {producer for delta in supplied for producer in delta.producers()}
    archives.register_owner_producers()
    derived = []
    for producer in mechanics_stages.required_producers(names):
        if producer not in have:
            if producer not in archives.PRODUCERS:
                raise ValueError('no registered archive producer: ' + producer)
            derived.append(archives.PRODUCERS[producer](base, language, charmap))
    return archives.normalize((*supplied, *derived))


def complete_overlays(base, language, work_dir, names, supplied):
    needed = mechanics_stages.required_overlay_producers(names)
    supplied = tuple(supplied)
    if supplied and not needed:
        raise ValueError('extra overlay producer outside the stage chain')
    if needed:
        expected = (cartridge_deltas.derive_rematches(base, language, work_dir),)
        if supplied and supplied != expected:
            raise ValueError('supplied overlay producer differs from mandatory owner replay')
        return expected
    return ()


def replay_overlays(base, language, work_dir, names, records):
    needed = mechanics_stages.required_overlay_producers(names)
    if not isinstance(records, list) or [r.get('producer') if isinstance(r, dict) else None for r in records] != list(needed):
        raise ValueError('omitted or extra mandatory overlay producer')
    return cartridge_deltas.rederive(base, language, work_dir, records)


def owner_receipts(receipts):
    return {item['stage']: item['stage_receipt'] for item in receipts[1:]
            if item['stage'] in activation.OWNERS}


def source_snapshot() -> dict[str, str]:
    """Hash all successor/feature sources and legacy installer dependencies.

Scanning every feature directory includes newly added features automatically.
    External inputs actually consumed by future stages must also be pinned in
    their receipts. Baseline consumes no charmap or external script metadata.
    """
    root = Path(__file__).resolve().parents[1]
    paths = {p for folder in ('sgp131', 'sgp13', 'sgp12', 'features',
                              'quality-audit', 'translation', 'native-guide', 'native-eviv')
             for p in (root / folder).rglob('*')
             if p.is_file() and p.suffix in ('.py', '.c', '.h', '.json', '.S', '.s')}
    from . import ui_compile
    paths.update(root / name for name in ui_compile.SOURCE_PINS)
    from sgp13 import admission
    return admission.source_snapshot(root, paths)


def require_stage(through):
    if through not in STAGES:
        raise ValueError('unknown stage: ' + str(through))
    if through not in IMPLEMENTED:
        if through in mechanics_stages.PENDING:
            raise mechanics_stages.StagePending(through, mechanics_stages.PENDING[through])
        raise ValueError('unimplemented stage: ' + through)


def verify_composition(before: bytes, after: bytes, receipts: list[dict], *,
                       through='baseline', ui_inputs=None, scratch=None, scratch_fd=None,
                       archive_deltas=None, overlay_deltas=None, allocation=None, stage_options=None) -> dict:
    """Independently authorize the exact empty change set for baseline.

Whole-byte identity proves ARM7, file IDs, every hook, reserve guard, FAT file,
    overlay and unindexed region unchanged. A receipt cannot widen this policy.
    """
    require_stage(through)
    if through in UI_CHAIN:
        from . import ui_verify
        names = mechanics_stages.chain_for(through)
        activation.validate_for_chain(stage_options, baseline.identify(before), names)
        runs = mechanics_stages.writers(names)       # archive-only stages leave no receipt: their delta is in the UI receipt
        if (not isinstance(receipts, list) or len(receipts) != 1 + len(runs)
                or ui_inputs is None or scratch is None):
            raise ValueError('UI composition requires exactly one receipt and explicit inputs' if not runs else
                             'UI chain composition requires one UI receipt, one receipt per mechanical '
                             'stage and explicit inputs')
        if not len(before) < len(after) <= len(before) + UI_APPEND_LIMIT:
            raise ValueError('UI appended output bound')
        needed = mechanics_stages.required_producers(names)
        sources = source_snapshot()
        language = baseline.identify(before)
        # Restore each declared writer (including shared-overlay peel) before issuing conditional grants.
        # Receipt contents cannot authorize slots: the exact reconstructed cold UI is independently verified.
        stages = [mechanics_stages.require_stage(name) for name in runs]
        declared = [list(stage.regions(after if getattr(stage, 'regions_from_final', False) else before)) for stage in stages]
        cold_ui = mechanics_stages.intermediate_images(before, after, stages, declared)[0] if runs else after
        with ui_workspace(scratch, ui_inputs, scratch_fd) as owned_charmap:
            recorded = receipts[0].get('archive_deltas', []) if isinstance(receipts[0], dict) else None
            named = {name for record in recorded or () if isinstance(record, dict)
                     and isinstance(record.get('producers'), list) for name in record['producers']}
            if set(needed) - named:
                raise ValueError('the stage chain requires archive producer(s) %s in the UI receipt'
                                 % ', '.join(sorted(set(needed) - named)))
            deltas = archives.rederive(before, language, owned_charmap, recorded)
            if archive_deltas is not None and ([d.record() for d in archives.normalize(archive_deltas)]
                                               != [d.record() for d in deltas]):
                raise ValueError('declared archive deltas differ from the producers re-run on the V4')
            overlays = replay_overlays(before, language, scratch, names, receipts[0].get('overlay_deltas', []))
            if overlay_deltas is not None and tuple(overlay_deltas) != overlays:
                raise ValueError('declared overlay deltas differ from owner replay')
            extra = {'archive_deltas': deltas} if deltas else {}
            if overlays:
                extra['overlay_deltas'] = overlays
            rows, _ = mechanics_stages.resolve_allocation(
                before, names, allocation, installed_ui=cold_ui, charmap=owned_charmap,
                work_dir=scratch, archive_deltas=deltas, overlay_deltas=overlays)

            def independent_ui(image):
                return ui_verify.verify(before, image, language, owned_charmap, scratch,
                                        receipt=receipts[0], **extra)
            result = (mechanics_stages.verify_chain(before, after, runs, receipts[1:], independent_ui,
                                                    allocation=rows, charmap=owned_charmap, stage_options=stage_options,
                                                    overlay_deltas=overlays)['ui']
                      if runs else independent_ui(after))
        activation.final_gate(after, stage_options, owner_receipts(receipts), language=language)
        refresh_ui_inputs(ui_inputs)
        if sources != source_snapshot():
            raise ValueError('source changed during UI verification')
        return composition_for([result, *receipts[1:]])
    if stage_options is not None:
        raise ValueError('baseline has no activation options')
    if receipts:
        raise ValueError('unimplemented composition receipt')
    if before != after:
        raise ValueError('baseline composition changed bytes')
    return {'byte_identical': True, 'changed_file_ids': [], 'changed_regions': [],
            'arm7_unchanged': True, 'file_ids_unchanged': True,
            'hooks_and_reserve_unchanged': True}


def compose(base: bytes, through: str, charmap: Path, scratch: Path, *, ui_config=None,
            scratch_fd=None, archive_deltas=(), overlay_deltas=(), allocation=None,
            stage_options=None) -> tuple[bytes, dict]:
    """Compose from V4; production grants follow cold UI verification.

    Optional assignment-row substitutes are confined to legacy abilities tests.
    Active owner options are immutable and independent of reserve authorization.
    """
    language = baseline.identify(base)
    require_stage(through)
    sources = source_snapshot()
    if through in UI_CHAIN:
        from . import ui, ui_verify
        names = mechanics_stages.chain_for(through)
        activation.validate_for_chain(stage_options, language, names)
        runs = mechanics_stages.writers(names)
        if allocation is not None and not any(mechanics_stages.require_stage(name).slot_payload for name in names):
            mechanics_stages.resolve_allocation(base, names, allocation)
        inputs = snapshot_ui_inputs(charmap, ui_config)
        archive_deltas = archives.normalize(archive_deltas)
        with ui_workspace(scratch, inputs, scratch_fd) as owned_charmap:
            archive_deltas = complete_deltas(base, language, owned_charmap, names, archive_deltas)
            overlays = complete_overlays(base, language, scratch, names, overlay_deltas)
            extra = {'archive_deltas': archive_deltas} if archive_deltas else {}   # delta-free calls keep the old signature
            if overlays:
                extra['overlay_deltas'] = overlays
            payload, stage = ui.install(base, language, owned_charmap, scratch, **extra)
            if type(payload) is not bytes or not len(base) < len(payload) <= len(base) + UI_APPEND_LIMIT:
                raise ValueError('UI output size bound')
            independent = ui_verify.verify(base, payload, language, owned_charmap, scratch, receipt=stage, **extra)
            rows, source = mechanics_stages.resolve_allocation(
                base, names, allocation, installed_ui=payload, charmap=owned_charmap,
                work_dir=scratch, archive_deltas=archive_deltas, overlay_deltas=overlays)
            receipts = [stage]
            for name in runs:  # moves, ai, abilities: own writer and reader, confined to declared regions
                payload, wrapped = mechanics_stages.run_stage(name, payload, language, allocation=rows,
                                                              work_dir=scratch, charmap=owned_charmap, stage_options=stage_options,
                                                              overlay_deltas=overlays)
                receipts.append(wrapped)
            if runs:
                mechanics_stages.verify_chain(
                    base, payload, runs, receipts[1:],
                    lambda image: ui_verify.verify(base, image, language, owned_charmap, scratch, receipt=stage,
                                                   **extra), allocation=rows, charmap=owned_charmap,
                    stage_options=stage_options, overlay_deltas=overlays)
            activated = activation.final_gate(payload, stage_options, owner_receipts(receipts), language=language)
        refresh_ui_inputs(inputs)
        if sources != source_snapshot():
            raise ValueError('source changed during composition')
        report = {'schema': 2, 'language': language, 'through': through,
                  'input_sha256': hashlib.sha256(base).hexdigest(),
                  'output_sha256': hashlib.sha256(payload).hexdigest(), 'output_bytes': len(payload),
                  'source_sha256': sources, 'ui_inputs': inputs['records'],
                  'receipts': receipts, 'composition': composition_for([independent, *receipts[1:]]),
                  'required_cases': list(REQUIRED_CASES[through]),
                  'scratch_planning_reserve_bytes': UI_SCRATCH_LIMIT,
                  'validation': ('static UI and mechanics readback; runtime acceptance pending' if runs
                                 else 'static UI readback; runtime acceptance pending')}
        if stage_options is not None:
            report['activation'] = activated
            report['mechanics_options_sha256'] = hashlib.sha256(stage_options.wire).hexdigest()
        if rows is not None:
            report['reserve_allocation'] = {'source': source,
                                            'assignments': rows['assignments'] if isinstance(rows, dict) else rows}
            if isinstance(rows, dict):
                report['reserve_allocation']['receipt'] = rows
        if len(canonical(report)) > RECEIPT_LIMIT:
            raise ValueError('UI receipt size limit')
        return payload, report
    if stage_options is not None:
        raise ValueError('baseline has no activation options')
    composition = verify_composition(base, base, [])
    if sources != source_snapshot():
        raise ValueError('source changed during composition')
    digest = hashlib.sha256(base).hexdigest()
    return base, {'schema': 1, 'language': language, 'through': through,
                  'input_sha256': digest, 'output_sha256': digest,
                  'output_bytes': len(base), 'source_sha256': sources,
                  'receipts': [], 'composition': composition,
                  'required_cases': list(REQUIRED_CASES[through]),
                  'scratch_peak_bytes': 0,
                  'validation': 'static baseline readback; acceptance pending'}
