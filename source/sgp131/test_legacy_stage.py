"""Legacy repairs must participate in the canonical composition and acceptance."""
import unittest
from . import build, mechanics_stages as M


class Registration(unittest.TestCase):
    def test_complete_chain_contains_the_repairs(self):
        self.assertIn('legacy', M.chain_for('identity'))
        self.assertLess(M.ORDER.index('gifts'), M.ORDER.index('legacy'))
        self.assertLess(M.ORDER.index('legacy'), M.ORDER.index('controls'))

    def test_archive_and_native_changes_have_one_registered_owner(self):
        self.assertIn('legacy', M.REGISTRY)
        stage = M.require_stage('legacy')
        self.assertEqual(stage.archive_producers,
                         ('legacy-events', 'legacy-scripts', 'poison-follower-script', 'gs-cup-guard',
                          'safari-scripts',
                          'evolution-fixes', 'fishing-encounters', 'pursuit-script',
                          'status-icon-script', 'pressure-switch-effects',
                          'pressure-switch-subscripts'))
        self.assertFalse(stage.archive_only)
        self.assertIsNone(stage.slot)

    def test_acceptance_extends_rather_than_replaces_previous_checks(self):
        self.assertIn('legacy', build.REQUIRED_CASES)
        prior = build.REQUIRED_CASES['gifts']
        cases = build.REQUIRED_CASES['legacy']
        self.assertEqual(cases[:len(prior)], prior)
        self.assertIn('legacy_old_save_continue_save_cold_en_it', cases)
        self.assertIn('legacy_lullaby_radio_controls', cases)
        self.assertIn('legacy_background_interactions_not_hidden_items', cases)
        self.assertIn('legacy_evolution_feebas_beauty_169_170', cases)
        self.assertIn('legacy_evolution_guide_matches_rules_en_it', cases)
        self.assertIn('legacy_kurt_full_bag_preserves_completed_batch', cases)
        self.assertIn('legacy_plus_options_write_failure_partial_cold', cases)
        self.assertIn('legacy_safari_partner_close_before_unload_en_it', cases)
        self.assertIn('legacy_safari_route47_runtime_third_fourth_duo', cases)
        self.assertIn('legacy_safari_save_cold_en_it', cases)
        self.assertIn('legacy_pursuit_ko_restores_field_and_fainted_battler', cases)
        self.assertIn('legacy_ability_volatile_cure_preserves_status_icon', cases)
        self.assertIn('legacy_pressure_delayed_pp_persists_after_manual_switch', cases)
        self.assertIn('legacy_gs_cup_viewer_guard_movement_en_it', cases)


if __name__ == '__main__':
    unittest.main()
