# Sacred Gold Plus 1.2 EN.nds
# ROM SHA-256: b631e2a10593ad9cfcfe50ddbba0aff92488f63028ec19adc1d3ece4d6567fac
# melonDS identifier: IPKE 19D1EEBB
# Seven optional codes, all OFF. Try one at a time on a TEST copy.
# These codes are for Sacred Gold Plus 1.2 only. A 1.1 catalogue cannot pair with this
# game: melonDS matches cheats by game code AND header checksum, and the 1.2 header differs.
# Import THIS file; do not reuse the 1.1 one.
# The 1.2 options -- Plus difficulty, wild levels, battle motion, NPC cap, online server --
# have NO cheat: open the Options page in game with SELECT.
# Turning a code off does not undo writes already made: restart without modified savestates.

CAT Optional cheats

CODE 0 Fast text
DESC Speeds up dialogue text. Guard checked byte for byte against the 1.2 ARM9 image on 12 September 2026; the in-game proof was made on 1.04 and has not been repeated on 1.2. Restart without the cheat to restore the original code.
92002346 00000E41
12002346 00002100
D2000000 00000000
920202EE 00004819
120202EE 00001C0C
120202F0 00004818
1202031E 0000BD10
02020320 E7E53C2D
1202032E 0000D0DF
1202033A 0000E7F1
D2000000 00000000

CODE 0 Fast transitions
DESC Shortens map-change fades; it is not an FPS unlock. Guard checked byte for byte against the 1.2 ARM9 image on 12 September 2026; the in-game proof was made on 1.04 and has not been repeated on 1.2.
9200FA78 00009A0C
1200FA78 00002200
1200FA9C 00002200
D2000000 00000000

CODE 0 Fast healing
DESC Shortens Pokemon Center healing animations; HP, status and PP are restored as usual. It only acts while the Center overlay is loaded. Guard checked byte for byte against the 1.2 ARM9 image on 12 September 2026; the in-game proof was made on 1.04 and has not been repeated on 1.2. Its second guard is in that overlay and is not statically verifiable.
9206325E 0000F7FC
1206325E 0000E000
1206327A 0000E000
D2000000 00000000
9224BDCC 00002000
1224BDCC 00002001
D2000000 00000000

CODE 0 Hide 3D outlines
DESC Disables 3D edge marking and keeps the existing DS anti-aliasing; it does not raise the resolution. Enter and leave a building after enabling it. Its guard lives in a map overlay, so it cannot be checked against the static ARM9 image: neither a static nor an in-game proof exists for 1.2.
521FBC38 20204001
221FBC3A 00000010
D2000000 00000000

CODE 0 Rename traded Pokemon
DESC Lets the Name Rater rename Pokemon from other Trainers; the name persists if you save. Guard checked byte for byte against the 1.2 ARM9 image on 12 September 2026; the in-game proof was made on 1.04 and has not been repeated on 1.2.
9204D240 00002001
1204D240 00002000
D2000000 00000000

CODE 0 Money 999999 (Select)
DESC Press Select in game to set 999999. The value persists in the save; turning the cheat off does not undo it. It writes game RAM, it does not patch code. The save-block address cannot be checked statically: the in-game proof was made on 1.04, not on 1.2.
94000130 FFFB0000
6211186C 00000000
B211186C 00000000
0000D068 000F423F
D2000000 00000000

CODE 0 Classic camera
DESC Returns the camera to HeartGold's original angles everywhere. In 1.2 the indoor camera is already native in eight maps, so this code is only for players who want the original angles outdoors as well. It takes effect at the next map change; the guard checks the module signature first, so on a different ROM the code writes nothing. Guard checked byte for byte against the 1.2 ARM9 image on 12 September 2026; the in-game proof was made on 1.04 and has not been repeated on 1.2. The on-screen effect has still not been proved in game.
523DEBE0 002EB570
223DFFFC 00000000
D2000000 00000000
