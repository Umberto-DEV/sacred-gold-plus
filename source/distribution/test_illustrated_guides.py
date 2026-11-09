"""Compact lists must preserve changed moves, levels and evolution conditions."""
import unittest

try:
    from distribution.illustrated_guides import (learnset_edits, evolution_edits,
        normalize_text, proofed_paragraphs, species_blocks, evolution_condition,
        fishing_groups, parse_evolution_records)
except ImportError:
    learnset_edits = evolution_edits = None


class IllustratedGuideTests(unittest.TestCase):
    def test_move_changes_keep_multiple_same_level_moves_and_removals(self):
        self.assertIsNotNone(learnset_edits, 'compact guide formatter is missing')
        edits = learnset_edits([(1, 10), (3, 20), (7, 30)],
                               [(1, 10), (5, 20), (5, 40), (9, 40)])
        self.assertEqual(edits, [(20, (3,), (5,)), (30, (7,), ()),
                                 (40, (), (5, 9))])

    def test_evolution_diff_keeps_distinct_targets_and_exact_parameters(self):
        self.assertIsNotNone(evolution_edits, 'evolution formatter is missing')
        before = [(1, 0, 4, 16, 2), (133, 0, 7, 80, 134)]
        current = [(1, 0, 4, 16, 2), (133, 0, 7, 80, 134),
                   (133, 1, 7, 81, 135), (458, 0, 21, 223, 226)]
        self.assertEqual(evolution_edits(before, current), current[2:])

    def test_repeated_move_entries_are_not_deduplicated(self):
        self.assertIsNotNone(learnset_edits)
        self.assertEqual(learnset_edits([(3, 20), (3, 20)], [(3, 20)]),
                         [(20, (3, 3), (3,))])

    def test_punctuation_normalization_is_explicit_and_unknown_glyphs_survive(self):
        self.assertEqual(normalize_text("Pokémon’s HP: 10→20; ♀ ≥20"),
                         'Pokemon’s HP: 10 to 20, female at least 20')
        self.assertIn('☃', normalize_text('Unknown ☃'))

    def test_event_notes_correct_tools_and_champion_requirement_without_mutation(self):
        entry = dict(id=2185, pages=[dict(lines=['- Use Super Rod on the', 'tree blocking Route 36.'])])
        self.assertIn('SquirtBottle', ' '.join(proofed_paragraphs(entry)))
        self.assertIn('Super Rod', ' '.join(entry['pages'][0]['lines']))
        entry = dict(id=3003, pages=[dict(lines=['- At Goldenrod’s Archaeology Center,',
                          'show Cynthia a member of that Sinnoh',
                          'starter family as your first conscious',
                          'party Pokemon.', '- Leave two free party slots. She',
                          'gives you the other two starters.'])])
        result = ' '.join(proofed_paragraphs(entry))
        self.assertIn('Champion', result)
        self.assertIn('two free party slots', result)
        self.assertIn('first conscious', result)

    def test_species_lists_only_changed_learnset_entries_and_names_fairy(self):
        facts = dict(names=dict(pokemon=['none', 'Example'], type=['Normal']*18,
                                 ability=['none', 'First', 'Second'],
                                 move=['none', 'Keep', 'Shift', 'Added']))
        before = dict(id=1, types=(0,0), abilities=(1,0), stats=(10,20,30,40,50,60),
                      learnset=((1,1),(3,2)))
        after = dict(id=1, types=(9,9), abilities=(1,2), stats=(15,20,30,40,50,60),
                     learnset=((1,1),(5,2),(8,3)))
        blocks = species_blocks([before], [after], facts, facts)
        text = ' '.join(value for role,value in blocks)
        self.assertIn('+Type: Normal to Fairy', text)
        self.assertIn('+HP: 10 to 15', text)
        self.assertIn('Shift', text)
        self.assertIn('Added', text)
        self.assertNotIn('Keep', text)
        self.assertNotIn('+Speed', text)

    def test_evolution_conditions_preserve_actual_beauty_gender_and_party_gates(self):
        names = lambda kind,number: {('pokemon',223):'Remoraid',('move',246):'AncientPower'}.get((kind,number),'Item')
        self.assertIn('Beauty at least 170', evolution_condition(15,170,names))
        self.assertIn('female', evolution_condition(23,20,names))
        self.assertIn('20', evolution_condition(23,20,names))
        self.assertIn('21', evolution_condition(23,21,names))
        self.assertIn('Remoraid in the party', evolution_condition(21,223,names))

    def test_retail_location_evolution_methods_are_valid_baseline_rows(self):
        import struct
        records=[bytes(42) for unused in range(494)]
        records[133]=struct.pack('<3H',25,0,470)+bytes(36)
        self.assertEqual(parse_evolution_records(records),[(133,0,25,0,470)])

    def test_fishing_combines_species_weights_and_deduplicates_map_aliases(self):
        rows=[]
        for mid in (1,2):
            for slot,species in enumerate((129,90,170,90,170)):
                rows.append((mid,3,0,3,-1,slot,species,10,10,25))
        facts=dict(encounters=rows,weights=dict(fish=(40,30,15,10,5)),
                   names=dict(map=['','','','New Bark Town']))
        groups=fishing_groups(facts)
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0]['species'],((90,40),(129,40),(170,20)))
        self.assertEqual(groups[0]['map'],'New Bark Town')

    def test_fishing_distinguishes_different_floors_with_the_same_map_name(self):
        rows = []
        for mid, species in ((145, 129), (451, 339)):
            for slot in range(5):
                rows.append((mid, 1, 0, 3, -1, slot, species, 10, 10, 25))
        facts = dict(encounters=rows, weights=dict(fish=(40,30,15,10,5)),
                     names=dict(map=['', 'Cerulean Cave']))
        groups = fishing_groups(facts)
        self.assertEqual({row['map'] for row in groups},
                         {'Cerulean Cave - 1F', 'Cerulean Cave - B1F'})

    def test_fishing_swarm_and_night_replacements_keep_native_slot_weights(self):
        rows=[(1,0,0,4,-1,slot,129,10,10,25) for slot in range(5)]
        rows += [(1,0,0,10,4,0,211,10,10,25),
                 (1,0,0,11,2,3,170,10,10,25)]
        groups=fishing_groups(dict(encounters=rows,weights=dict(fish=(40,30,15,10,5)),
                                   names=dict(map=['Example'])))
        by_condition={row['condition']:row['species'] for row in groups}
        self.assertEqual(by_condition['All times'],((129,100),))
        self.assertEqual(by_condition['Swarm'],((129,60),(211,40)))
        self.assertEqual(by_condition['Night'],((129,90),(170,10)))


if __name__ == '__main__':
    unittest.main()
