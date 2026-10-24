"""Synthetic tile graphics: catch wrong glyphs, placement and reused live tiles."""
import struct
import unittest
from . import titolo_versione as t
from .rom import Rifiuto


def fixture():
    # NCGR/NSCR-shaped project-owned test buffers, not extracted game assets.
    gfx = bytearray(3136)
    gfx[:4] = b'RGCN'
    gfx[48:48+25*32] = b'\x11' * (25*32)
    tilemap = bytearray(1572)
    tilemap[:4] = b'RCSN'
    # Existing credit and a flipped tile must remain intact.
    struct.pack_into('<H', tilemap, 36+(22*32+20)*2, 0x7001)
    struct.pack_into('<H', tilemap, 36+(23*32+20)*2, 0x7c18)
    struct.pack_into('<H', tilemap, 36+762*2, 0x740d)
    struct.pack_into('<H', tilemap, 36+750*2, 0x700d)
    return bytes(gfx), bytes(tilemap)


class TitleVersionTests(unittest.TestCase):
    def test_version_is_drawn_in_free_top_screen_credit_tiles(self):
        old_g, old_m = fixture()
        g, m = t.disegna(old_g, old_m)
        self.assertEqual((len(g), len(m)), (3136, 1572))
        self.assertEqual(g[:48+25*32], old_g[:48+25*32])
        self.assertEqual(g[48+38*32:], old_g[48+38*32:])
        self.assertEqual(m[:36+705*2], old_m[:36+705*2])
        allowed = set(range(705,711)) | set(range(737,743)) | {762}
        for i in set(range(768))-allowed:
            self.assertEqual(m[36+i*2:38+i*2], old_m[36+i*2:38+i*2])
        # Decode the cells and 4bpp pixels independently of the writer.
        rows=[]
        for y in range(16):
            row=''
            for x in range(48):
                cell=struct.unpack_from('<H',m,36+((22+y//8)*32+1+x//8)*2)[0]
                self.assertEqual(cell >> 12,7)
                tile=cell & 1023
                b=g[48+tile*32+(y%8)*4+(x%8)//2]
                pixel=(b >> (4*(x%2))) & 15
                row += '#' if pixel == 14 else '.'
            rows.append(row[:41])
        self.assertEqual(rows[5], '#...#.........#..........###........#####')
        self.assertEqual(rows[11], '..#....##...#####..##...#####..##...####.')
        self.assertEqual(rows[12], '.'*41)

    def test_refuses_live_tiles_or_nonempty_destination_cells(self):
        g,m=fixture()
        occupied=bytearray(g);occupied[48+25*32]=1
        referenced=bytearray(m);struct.pack_into('<H',referenced,36,0x7419)
        covered=bytearray(m);struct.pack_into('<H',covered,36+705*2,0x7001)
        for gg,mm in ((bytes(occupied),m),(g,bytes(referenced)),(g,bytes(covered)),(g[:-1],m)):
            with self.assertRaises(Rifiuto):t.disegna(gg,mm)

    def test_independent_reader_rejects_missing_graphics_map_and_extra_change(self):
        g,m=fixture();new_g,new_m=t.disegna(g,m)
        self.assertEqual(t.rileggi_membri(g,m,new_g,new_m)['esito'],'VERDE')
        bad=bytearray(new_g);bad[48]^=1
        for gg,mm in ((g,new_m),(new_g,m),(bytes(bad),new_m)):
            with self.assertRaises(Rifiuto):t.rileggi_membri(g,m,gg,mm)

    def test_by_has_descender_without_changing_the_other_use_of_its_tile(self):
        old_g,old_m=fixture();g,m=t.disegna(old_g,old_m)
        self.assertEqual(g[48+13*32:48+14*32],old_g[48+13*32:48+14*32])
        self.assertEqual(struct.unpack_from('<H',m,36+750*2)[0],0x700d)
        self.assertEqual(struct.unpack_from('<H',m,36+762*2)[0],0x7425)
        for pixel in (37,46,47):
            byte=g[48+37*32+pixel//2]
            self.assertEqual((byte >> (4*(pixel%2)))&15,14)
