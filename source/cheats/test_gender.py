"""Generator and catalogue contracts for wild gender/nature cheats."""
import unittest
import xml.etree.ElementTree as ET
from gender import gender_code, nature_code, pid_gender, update_gender_catalogue, legacy_code


class GenderTest(unittest.TestCase):
    def test_every_nature_is_reachable_with_the_requested_low_byte(self):
        for gender in ('male', 'female'):
            reachable = set()
            for upper in range(65536):
                pid = (upper << 16) | (255 if gender == 'male' else 0)
                reachable.add(pid % 25)
                for ratio in (31, 63, 127, 191, 223):
                    self.assertEqual(pid_gender(pid, ratio), gender)
            self.assertEqual(reachable, set(range(25)))

    def test_fixed_gender_and_genderless_remain_biological(self):
        for pid in (0, 255, 0xffffffff):
            self.assertEqual(pid_gender(pid, 0), 'male')
            self.assertEqual(pid_gender(pid, 254), 'female')
            self.assertEqual(pid_gender(pid, 255), 'genderless')

    def test_generated_patch_sites_and_restoration(self):
        for gender in ('male', 'female'):
            for nature in range(25):
                code = gender_code(gender, nature)
                self.assertIn('5206E108 B086B5F8', code)
                self.assertIn('1206E110 00009C0C', code)
                self.assertIn('1206E11A 00001C05', code)
                self.assertIn(f'1206E110 {0x2400+nature:08X}', code)
                self.assertIn('1206E11A '+('000025FF' if gender=='male' else '00002500'),code)
                self.assertNotIn('020D3F60', code)
                self.assertNotIn('023C0D00', code)
                self.assertTrue(code.endswith('D2000000 00000000'))
        for gender,nature in (('none',0),('male',-1),('female',25)):
            with self.assertRaises(ValueError):gender_code(gender,nature)

    def test_catalogue_migrates_only_44_45_46_and_is_idempotent(self):
        r=ET.Element('codelist');g=ET.SubElement(r,'game');ET.SubElement(g,'gameid').text='IPKE 19D1EEBB'
        for number,gender in ((44,None),(45,'male'),(46,'female')):
            f=ET.SubElement(g,'folder');ET.SubElement(f,'name').text=f'{number} - Wild {gender}'
            for n in range(25):
                c=ET.SubElement(f,'cheat');ET.SubElement(c,'name').text=f'Nature {n}'
                ET.SubElement(c,'codes').text=(legacy_code(gender,n) if gender else f'1206E120 {0x2400+n:08X}')
        extra=ET.SubElement(g,'folder');ET.SubElement(extra,'name').text='67 - untouched';ET.SubElement(extra,'codes').text='UNCHANGED'
        migrated=update_gender_catalogue(ET.tostring(r,encoding='unicode'),'EN');out=ET.fromstring(migrated)
        self.assertEqual(out.findtext('game/gameid'),'IPKE 19D1EEBB')
        self.assertEqual(out.findall('game/folder')[3].findtext('codes'),'UNCHANGED')
        self.assertEqual(update_gender_catalogue(migrated,'EN'),migrated)
        for i,gender in enumerate((None,'male','female')):
            for n,c in enumerate(out.findall('game/folder')[i].findall('cheat')):
                self.assertEqual(c.findtext('codes'),gender_code(gender,n) if gender else nature_code(n))
                self.assertIn('restart',c.findtext('note'))

    def test_nature_only_keeps_native_gender_and_random_pid(self):
        for nature in range(25):
            code = nature_code(nature)
            self.assertIn(f'1206E110 {0x2400+nature:08X}',code)
            self.assertIn(f'1206E15E {0x2700+nature:08X}',code)
            self.assertNotIn('000025FF',code)
            self.assertNotIn('00002500',code)
            self.assertNotIn('94000130',code)
            self.assertNotIn('1206E120',code)

    def test_refuses_unknown_layout(self):
        with self.assertRaises(ValueError):
            update_gender_catalogue('<codelist><game><gameid>WRONG</gameid></game></codelist>','EN')


if __name__ == "__main__":
    unittest.main()
