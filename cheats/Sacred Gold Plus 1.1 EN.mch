# Sacred Gold Plus 1.1 EN.nds
# ROM SHA-256: 281c2d68e442479e679d8b7e36566ade614d236151c65c9684bad6985461827d
# melonDS identifier: IPKE 09697109
# Seven optional codes, all OFF. Try one at a time on a TEST copy.
# Compatibility checked statically against 1.1: the 1.04 functional proofs do not carry over.
# Turning a code off does not undo writes already made: restart without modified savestates.

CAT Optional cheats

CODE 0 Fast text
DESC Speeds up dialogue text. Address-compatible with 1.1 (pre-images identical to 1.04); the in-game proof was made on 1.04, not on 1.1. Restart without the cheat to restore the original code.
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
DESC Shortens map-change fades; it is not an FPS unlock. Address-compatible with 1.1; the in-game proof was made on 1.04, not on 1.1.
9200FA78 00009A0C
1200FA78 00002200
1200FA9C 00002200
D2000000 00000000

CODE 0 Fast healing
DESC Shortens Pokemon Center healing animations; HP, status and PP are restored as usual. Address-compatible with 1.1; the in-game proof was made on 1.04, not on 1.1. It only acts while the Center overlay is loaded.
9206325E 0000F7FC
1206325E 0000E000
1206327A 0000E000
D2000000 00000000
9224BDCC 00002000
1224BDCC 00002001
D2000000 00000000

CODE 0 Hide 3D outlines
DESC Disables 3D edge marking and keeps the existing DS anti-aliasing; it does not raise the resolution. Address-compatible with 1.1; the in-game proof was made on 1.04, not on 1.1. Enter and leave a building after enabling it.
521FBC38 20204001
221FBC3A 00000010
D2000000 00000000

CODE 0 Rename traded Pokemon
DESC Lets the Name Rater rename Pokemon from other Trainers; the name persists if you save. Address-compatible with 1.1; the in-game proof was made on 1.04, not on 1.1.
9204D240 00002001
1204D240 00002000
D2000000 00000000

CODE 0 Money 999999 (Select)
DESC Press Select in game to set 999999. The value persists in the save; turning the cheat off does not undo it. It writes game RAM, it does not patch code. The save-block address cannot be checked statically: the in-game proof was made on 1.04, not on 1.1.
94000130 FFFB0000
6211186C 00000000
B211186C 00000000
0000D068 000F423F
D2000000 00000000

CODE 0 Classic camera
DESC Returns the camera to HeartGold's original angles. It replaces the former 'Normal Angle' build. It takes effect at the next map change. The guard checks the 1.1 module signature before writing: on a different ROM the code writes nothing. Address-compatible (bit OBSERVED at 0x023DFFFC, value 1 in the 1.1 ROM); the on-screen effect has not been proved in game yet.
523DEE60 002EB570
223DFFFC 00000000
D2000000 00000000
