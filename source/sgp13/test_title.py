import unittest
from sgp13 import title
from sgp12 import titolo_versione as previous

class TitleTests(unittest.TestCase):
    def input(self):
        g=bytearray(b'g'*3136);g[848:1232]=previous.etichetta()
        m=bytearray(1572);m[1446:1458]=bytes.fromhex('19701a701b701c701d701e70');m[1510:1522]=bytes.fromhex('1f7020702170227023702470')
        return bytes(g),bytes(m)

    def test_only_previous_project_label_pixels_change(self):
        g,m=self.input();new=title.replace_graphics(g,m)
        self.assertEqual(len(new),len(g));self.assertEqual(new[:848],g[:848]);self.assertEqual(new[1232:],g[1232:])
        self.assertNotEqual(new[848:1232],g[848:1232]);self.assertEqual(len(title.pixels()),384)
        self.assertTrue(all((b&15) in (0,4,14) and b>>4 in (0,4,14) for b in title.pixels()))

    def test_unknown_pixels_or_map_are_rejected(self):
        g,m=self.input()
        with self.assertRaises(ValueError):title.replace_graphics(g[:900]+b'X'+g[901:],m)
        with self.assertRaises(ValueError):title.replace_graphics(g,bytes(1572))

if __name__=='__main__':unittest.main()
