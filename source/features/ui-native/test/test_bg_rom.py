"""Prepared native BG tests. DMA/cache and post-wait dispatch are explicit seams."""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from bg_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
from test_heap_rom import NativeHeapBench, ROM_PINS, PINS as HEAP_PINS
BG_PINS=(
    (0x0209E00C,0x3F8,'6de14145bd25ba854940e23c7ec295b4806a1773b5c0f74b731a314ef96d602e'),
    (0x020D3D30,0x148,'d7e39df2685b8a2e8a4dfa4c57cfcaf4e496777124cc2703986be0cea63069f3'),
    (0x020CEC70,0x20,'e64e76337ebf11dd70c549da38b23ffa96596aaf57b64b1d1f5a94add5c1d72f'),
    (0x020CECC4,0x20,'7d11a09fe6c330d76f44c223ef86b846c1350f68ee3d039f76593a82756caa6b'),
    (0x020CEF08,0x20,'1d3ad0fe427de922e031abb1b93facaec320ef755228eb0caf51908efc789cc8'),
    (0x020CEF5C,0x20,'5c57156c16c24ba6cd211ecdb9c476188f4c99c9f3a41e02c200d977a314cd8e'),
    (0x020CFF84,0x60,'0e36c5e3eb8781fc149a946a37b8ec14fa2f9d08e17c985d6e739ebd37ff9ed3'),
    (0x020D0044,0x60,'3d9c0df26e93a2ba3f0c0951c5aca7b87cd40860acf1a9739a28a45178a76423'),
    (0x020D0284,0x60,'5eb08364dbcdb27889140e59a2da43488d0c328daad55595ce2cf56cf49e974f'),
    (0x020D0344,0x60,'f62e3f9971e786c496fd92ba09e7c423723765e27153bd2039a4201b6a96a79e'),
    (0x02000CA4,0x1C8,'93e8e14312d7d21bf0cab24ffbdb659fb17b80d5355688501c8f44e69e057803'),
    (0x0201A0FC,0xB8,'1da318c8da165154e00aae289a3aa1df1bf9209316c9bdccca7a452688f6dae0'),
    (0x0201A0FC,0xC,'d510f796a3f3b5e0f156e07c10ca76ae9c621f3221b216dc644d2fe963e3785e'),
    (0x0201ACB0,0x3C,'b9d80d68c2e02803ce09a95b65562c8c4eca95ee73c4ef49ee728287732d9345'),
    (0x0201AD0C,0x4D8,'015de400261c6e6b0a2d7e8bfc12a95129a745780e52e572dd1df6fa89de8508'),
    (0x0201BA88,0x3420,'40f407b81204449857ec25b278bc9eaea6039362d31e3894da6071f102a9a7b2'),
    (0x0200E6B4,0x2E4,'cb7de802b5bd17091d03a15e0780fc3c3e28f8885f5664cbda0dc95bc73064b6'),
    (0x02022BE8,0x158,'560471e9070ad8eaa4fb1530a6c71dbd850bc619bfbb4abf28d75fcd8b1eb07b'),
    (0x02022C9C,0x20,'4d6141b881877df24ed50a8810517041aea42d7170e66ace61b5b0390f67dc60'),
    (0x02022D04,0x24,'545739636af29bb0d19549c72e99ad214c73dbe169f99e92471c5277405f30e8'),
    (0x020CD9FC,0x16B0,'de0adca326d5803d3256da30373c9da1a9adcbaf520f7dd61c3aaa85c64e7e37'),
    (0x020CFC6C,0x798,'ccabee5e95e1f02427cdc785cd0c4c54d4a326658fe0f58dcffeea199ced52af'),
    (0x020D2894,0x24,'afafd34da03d3444cf60b68f45b2e6eab2e36b9a31a7dde8bf3d12187467e843'),
    (0x020D28B8,0xC,'c27ce0bc897baa92f297f607f9677de717c8702b912841eeb8cfc4a5d7d4a16c'),
    (0x020D3FF4,0xE0,'03ac1d0860668394dd676de002954a8193d165fe8a1c20a47e47e6ae8b179feb'),
    (0x020D4394,0x54,'139d96709b86ba0e7dce9b554c4ebcd5e2a99011063a85fce04811bc8a36ec62'),
    (0x01FF8488,0x70,'e1f99d3191b03109129165957b7a1567af55331ff71aabee35d6697ef6b78e13'),
    (0x020D4790,0x17C,'df32c9dbd51b8dcbfc39ce840a13264f7e16df8ab44f3e5a5e35d8bf83f287af'),
    (0x020D3A38,0x30,'8799c41ae2d67d6eb1339acba651c4cf9fb8a06ceae96794f5f1a7cd0256c552'),
    (0x0200FBDC,0x140,'60699f6019b3bba70eade291813a4d923d2530e5d68f5504a15d28555a2efa00'),
    (0x020131F4,0x2C,'07f10fa261f3419bcb38210d5e33e3d21212bf24765f610318188e2f6ecfc9a4'),
    (0x020CD910,0x38,'a2fb7ade796e779cf577b71729d981de2943f54e9dc7a38cc5334cdb1d882e05'),
    (0x020D1004,0x240,'45674e13865a9430836a2d71dfe52c8ece7a1e87544f8a3bf64780451d780b2a'),
    (0x02110C7C,0x8,'30656bde983020b4a04d4fb8027463ad8cd15d89d4b953f961654b1d6579b9b9'),
)
# Fixed admitted instruction ranges, frozen from the independently asserted
# finite native campaign; every instruction width/state is checked. Identity
# envelopes above remain broader and never grant execution permission.
NATIVE_CODE=(
    (0x0201bd4e,0x0201bd7a,2,1),
    (0x020cec70,0x020cec8c,4,0),
    (0x020cecc4,0x020cece0,4,0),
    (0x020cef08,0x020cef24,4,0),
    (0x020cef5c,0x020cef78,4,0),
    # Guide BG4/5: audited zero-buffer template + SUB-only GX copy branches; no pools.
    (0x0201af3c,0x0201af40,2,1),
    (0x0201af40,0x0201af44,4,1),
    (0x0201af44,0x0201af80,2,1),
    (0x0201af8a,0x0201af98,2,1),
    (0x0201af98,0x0201af9c,4,1),
    (0x0201af9c,0x0201afd8,2,1),
    (0x0201afe2,0x0201afec,2,1),
    (0x02022cc8,0x02022ccc,2,1),
    (0x02022cd6,0x02022cde,2,1),
    (0x02022cf6,0x02022cf8,2,1),
    (0x0201c076,0x0201c07c,2,1),
    (0x0201c07c,0x0201c080,4,1),
    (0x0201c080,0x0201c088,2,1),
    (0x0201c088,0x0201c08c,4,1),
    (0x0201c08c,0x0201c08e,2,1),
    (0x0201c192,0x0201c198,2,1),
    (0x0201c198,0x0201c19c,4,1),
    (0x0201c19c,0x0201c1a4,2,1),
    (0x0201c1a4,0x0201c1a8,4,1),
    (0x0201c1a8,0x0201c1aa,2,1),
    (0x020cff84,0x020cffe0,4,0),
    (0x020d0044,0x020d00a0,4,0),
    (0x020d0284,0x020d02e0,4,0),
    (0x020d0344,0x020d03a0,4,0),
    # CPU fallback branches and full bounded copy16 body (same pinned guards).
    (0x020d47b8,0x020d47ec,4,0),
    (0x020cffe4,0x020d0040,4,0),
    (0x020d00a4,0x020d0100,4,0),
    (0x020d02e4,0x020d0340,4,0),
    (0x020d03a4,0x020d0400,4,0),
    (0x01ff8488,0x01ff84d4,4,0),
    (0x01ff84e8,0x01ff84f0,4,0),
    (0x0200e6b4,0x0200e6e8,2,1),
    (0x0200e6e8,0x0200e6ec,4,1),
    (0x0200e6ec,0x0200e714,2,1),
    (0x0200e714,0x0200e718,4,1),
    (0x0200e718,0x0200e736,2,1),
    (0x0200e736,0x0200e73a,4,1),
    (0x0200e73a,0x0200e762,2,1),
    (0x0200e762,0x0200e766,4,1),
    (0x0200e766,0x0200e78a,2,1),
    (0x0200e78a,0x0200e78e,4,1),
    (0x0200e78e,0x0200e7b2,2,1),
    (0x0200e7b2,0x0200e7b6,4,1),
    (0x0200e7b6,0x0200e7d4,2,1),
    (0x0200e7d4,0x0200e7d8,4,1),
    (0x0200e7d8,0x0200e7f6,2,1),
    (0x0200e7f6,0x0200e7fa,4,1),
    (0x0200e7fa,0x0200e81a,2,1),
    (0x0200e81a,0x0200e81e,4,1),
    (0x0200e81e,0x0200e83e,2,1),
    (0x0200e83e,0x0200e842,4,1),
    (0x0200e842,0x0200e862,2,1),
    (0x0200e862,0x0200e866,4,1),
    (0x0200e866,0x0200e88c,2,1),
    (0x0200e88c,0x0200e890,4,1),
    (0x0200e890,0x0200e8b0,2,1),
    (0x0200e8b0,0x0200e8b4,4,1),
    (0x0200e8b4,0x0200e8d4,2,1),
    (0x0200e8d4,0x0200e8d8,4,1),
    (0x0200e8d8,0x0200e8f8,2,1),
    (0x0200e8f8,0x0200e8fc,4,1),
    (0x0200e8fc,0x0200e91c,2,1),
    (0x0200e91c,0x0200e920,4,1),
    (0x0200e920,0x0200e93e,2,1),
    (0x0200e93e,0x0200e942,4,1),
    (0x0200e942,0x0200e946,2,1),
    (0x0200e948,0x0200e952,2,1),
    (0x0200e952,0x0200e956,4,1),
    (0x0200e956,0x0200e95a,2,1),
    (0x0200e95a,0x0200e95e,4,1),
    (0x0200e95e,0x0200e962,2,1),
    (0x0200e962,0x0200e966,4,1),
    (0x0200e966,0x0200e96a,2,1),
    (0x0200e96a,0x0200e96e,4,1),
    (0x0200e96e,0x0200e972,2,1),
    (0x0200e972,0x0200e976,4,1),
    (0x0200e976,0x0200e98e,2,1),
    (0x0200e98e,0x0200e992,4,1),
    (0x0200e992,0x0200e996,2,1),
    (0x0201a0fc,0x0201a104,2,1),
    (0x0201a108,0x0201a10c,2,1),
    (0x0201a10c,0x0201a110,4,1),
    (0x0201a110,0x0201a11a,2,1),
    (0x0201a16c,0x0201a17e,2,1),
    (0x0201a17e,0x0201a182,4,1),
    (0x0201a182,0x0201a184,2,1),
    (0x0201a184,0x0201a188,4,1),
    (0x0201a188,0x0201a18a,2,1),
    (0x0201a1a0,0x0201a1aa,2,1),
    (0x0201acb0,0x0201acba,2,1),
    (0x0201acba,0x0201acbe,4,1),
    (0x0201acbe,0x0201acc0,2,1),
    (0x0201acc0,0x0201acc4,4,1),
    (0x0201acc4,0x0201acd8,2,1),
    (0x0201acd8,0x0201ace0,4,1),
    (0x0201ace0,0x0201ace2,2,1),
    (0x0201ad0c,0x0201ad1e,2,1),
    (0x0201ad1e,0x0201ad22,4,1),
    (0x0201ad22,0x0201ad2a,2,1),
    (0x0201ad2c,0x0201ad38,2,1),
    (0x0201ada0,0x0201ada4,2,1),
    (0x0201ada4,0x0201ada8,4,1),
    (0x0201ada8,0x0201ade4,2,1),
    (0x0201adee,0x0201adfc,2,1),
    (0x0201adfc,0x0201ae00,4,1),
    (0x0201ae00,0x0201ae06,2,1),
    (0x0201ae0e,0x0201ae30,2,1),
    (0x0201ae72,0x0201ae86,2,1),
    (0x0201ae90,0x0201ae9a,2,1),
    (0x0201b14c,0x0201b16e,2,1),
    (0x0201b194,0x0201b1bc,2,1),
    (0x0201b1c4,0x0201b1cc,2,1),
    (0x0201b1cc,0x0201b1d0,4,1),
    (0x0201b1d0,0x0201b1d8,2,1),
    (0x0201b1d8,0x0201b1dc,4,1),
    (0x0201b1dc,0x0201b1e0,2,1),
    (0x0201ba88,0x0201ba8c,2,1),
    (0x0201ba96,0x0201ba9e,2,1),
    (0x0201bafc,0x0201bb0c,2,1),
    (0x0201bb20,0x0201bb28,2,1),
    (0x0201bc8c,0x0201bca2,2,1),
    (0x0201bca2,0x0201bca6,4,1),
    (0x0201bca6,0x0201bcb0,2,1),
    (0x0201bcb2,0x0201bcbe,2,1),
    (0x0201bce4,0x0201bd1a,2,1),
    (0x0201be38,0x0201be48,2,1),
    (0x0201be54,0x0201be58,2,1),
    (0x0201be68,0x0201be6c,2,1),
    (0x0201bf7c,0x0201bf8c,2,1),
    (0x0201bf8c,0x0201bf90,4,1),
    (0x0201bf90,0x0201bf92,2,1),
    (0x0201bf94,0x0201bfa4,2,1),
    (0x0201c002,0x0201c00a,2,1),
    (0x0201c00a,0x0201c00e,4,1),
    (0x0201c00e,0x0201c012,2,1),
    (0x0201c014,0x0201c022,2,1),
    (0x0201c022,0x0201c026,4,1),
    (0x0201c026,0x0201c036,2,1),
    (0x0201c052,0x0201c058,2,1),
    (0x0201c058,0x0201c05c,4,1),
    (0x0201c05c,0x0201c064,2,1),
    (0x0201c064,0x0201c068,4,1),
    (0x0201c068,0x0201c06a,2,1),
    (0x0201c0c0,0x0201c0d6,2,1),
    (0x0201c0d6,0x0201c0da,4,1),
    (0x0201c0da,0x0201c0de,2,1),
    (0x0201c0ec,0x0201c0f8,2,1),
    (0x0201c124,0x0201c12a,2,1),
    (0x0201c12a,0x0201c12e,4,1),
    (0x0201c12e,0x0201c13e,2,1),
    (0x0201c13e,0x0201c142,4,1),
    (0x0201c142,0x0201c152,2,1),
    (0x0201c16e,0x0201c174,2,1),
    (0x0201c174,0x0201c178,4,1),
    (0x0201c178,0x0201c180,2,1),
    (0x0201c180,0x0201c184,4,1),
    (0x0201c184,0x0201c186,2,1),
    (0x0201c2f0,0x0201c308,2,1),
    (0x0201c32e,0x0201c332,2,1),
    (0x0201c336,0x0201c33a,2,1),
    (0x0201c33e,0x0201c348,2,1),
    (0x0201c8c4,0x0201c8f0,2,1),
    (0x0201c8f0,0x0201c8f4,4,1),
    (0x0201c8f4,0x0201c8f8,2,1),
    (0x0201c914,0x0201c930,2,1),
    (0x0201c930,0x0201c934,4,1),
    (0x0201c934,0x0201c982,2,1),
    (0x0201c982,0x0201c986,4,1),
    (0x0201c986,0x0201c98a,2,1),
    (0x0201c992,0x0201c996,2,1),
    (0x0201c9a8,0x0201c9ce,2,1),
    (0x0201d650,0x0201d6a6,2,1),
    (0x0201d6a6,0x0201d6aa,4,1),
    (0x0201d6aa,0x0201d6ce,2,1),
    (0x0201d978,0x0201d9aa,2,1),
    (0x0201d9aa,0x0201d9ae,4,1),
    (0x0201d9ae,0x0201d9b0,2,1),
    (0x0201ee8c,0x0201eea0,2,1),
    (0x02022be8,0x02022bec,2,1),
    (0x02022bec,0x02022c14,4,1),
    (0x02022c14,0x02022c16,2,1),
    (0x02022c16,0x02022c1a,4,1),
    (0x02022c1a,0x02022c1c,2,1),
    (0x02022c1c,0x02022c20,4,1),
    (0x02022c20,0x02022c22,2,1),
    (0x02022c22,0x02022c26,4,1),
    (0x02022c26,0x02022c28,2,1),
    (0x02022c28,0x02022c2c,4,1),
    (0x02022c2c,0x02022c2e,2,1),
    (0x02022c2e,0x02022c32,4,1),
    (0x02022c32,0x02022c34,2,1),
    (0x02022c34,0x02022c38,4,1),
    (0x02022c38,0x02022c3a,2,1),
    (0x02022c3a,0x02022c3e,4,1),
    (0x02022c3e,0x02022c40,2,1),
    (0x02022c40,0x02022c44,4,1),
    (0x02022c44,0x02022c46,2,1),
    (0x02022c46,0x02022c4a,4,1),
    (0x02022c4a,0x02022c4c,2,1),
    (0x02022c4c,0x02022c50,4,1),
    (0x02022c50,0x02022c52,2,1),
    (0x02022c54,0x02022c5c,2,1),
    (0x02022c60,0x02022c64,2,1),
    (0x02022c6e,0x02022c76,2,1),
    (0x02022c90,0x02022c92,2,1),
    (0x02022c9c,0x02022cb2,2,1),
    (0x02022cbc,0x02022cc4,2,1),
    (0x02022d04,0x02022d18,2,1),
    (0x020b4b68,0x020b4c00,4,0),
    (0x020b4cb4,0x020b4d2c,4,0),
    (0x020b4d40,0x020b4dcc,4,0),
    (0x020b4dd0,0x020b4e44,4,0),
    (0x020b4e4c,0x020b4f80,4,0),
    (0x020b4f88,0x020b4fe8,4,0),
    (0x020b5008,0x020b5058,4,0),
    (0x020b5060,0x020b5100,4,0),
    (0x020b5108,0x020b5184,4,0),
    (0x020b518c,0x020b51bc,4,0),
    (0x020b526c,0x020b5358,4,0),
    (0x020b535c,0x020b539c,4,0),
    (0x020b53a0,0x020b53c4,4,0),
    (0x020b5530,0x020b556c,4,0),
    (0x020cd910,0x020cd930,4,0),
    (0x020cd9fc,0x020cda58,4,0),
    (0x020cda64,0x020cda7c,4,0),
    (0x020cdb4c,0x020cdbe0,4,0),
    (0x020cdc04,0x020cdc48,4,0),
    (0x020cdc50,0x020cdc54,4,0),
    (0x020cdc5c,0x020cdc60,4,0),
    (0x020cdd1c,0x020cdd2c,4,0),
    (0x020cdd78,0x020cdd88,4,0),
    (0x020cde64,0x020cde74,4,0),
    (0x020cde94,0x020cdec0,4,0),
    (0x020cdefc,0x020cdf28,4,0),
    (0x020cdfa4,0x020cdfcc,4,0),
    (0x020cdfe4,0x020ce024,4,0),
    (0x020ce0b8,0x020ce0d8,4,0),
    (0x020ce0e4,0x020ce110,4,0),
    (0x020ce164,0x020ce184,4,0),
    (0x020ce190,0x020ce1ec,4,0),
    (0x020ce1fc,0x020ce200,4,0),
    (0x020ce324,0x020ce34c,4,0),
    (0x020ce368,0x020ce3b0,4,0),
    (0x020ce424,0x020ce440,4,0),
    (0x020ce650,0x020ce6a0,4,0),
    (0x020ce6b0,0x020ce6c0,4,0),
    (0x020ce6cc,0x020ce6e8,4,0),
    (0x020ce6f8,0x020ce740,4,0),
    (0x020ce74c,0x020ce75c,4,0),
    (0x020ce768,0x020ce794,4,0),
    (0x020ce7bc,0x020ce7dc,4,0),
    (0x020ce7e8,0x020ce814,4,0),
    (0x020ce83c,0x020ce85c,4,0),
    (0x020ce868,0x020ce898,4,0),
    (0x020ce89c,0x020ce8a8,4,0),
    (0x020ce8b0,0x020ce8bc,4,0),
    (0x020ce8c4,0x020ce8e0,4,0),
    (0x020ce8e8,0x020ce904,4,0),
    (0x020ce90c,0x020ce918,4,0),
    (0x020ce920,0x020ce92c,4,0),
    (0x020ce948,0x020ce954,4,0),
    (0x020ce95c,0x020ce968,4,0),
    (0x020ce970,0x020ce98c,4,0),
    (0x020ce998,0x020ce9b4,4,0),
    (0x020cec90,0x020cecc0,4,0),
    (0x020cece4,0x020ced14,4,0),
    (0x020ced18,0x020ced1c,4,0),
    (0x020ced34,0x020ced40,4,0),
    (0x020cef28,0x020cef58,4,0),
    (0x020cef7c,0x020cef94,4,0),
    (0x020cef9c,0x020cefc4,4,0),
    (0x020cffe4,0x020d002c,4,0),
    (0x020d00a4,0x020d00ec,4,0),
    (0x020d02e4,0x020d0340,4,0),
    (0x020d03a4,0x020d0400,4,0),
    (0x020d1204,0x020d1230,4,0),
    (0x020d2894,0x020d28c4,4,0),
    (0x020d3a38,0x020d3a64,4,0),
    (0x020d3ff4,0x020d40d0,4,0),
    (0x020d4394,0x020d43a0,4,0),
    (0x020d4808,0x020d4830,4,0),
    (0x020d4858,0x020d48a4,4,0),
    (0x020d48a8,0x020d48b4,4,0),
)
NATIVE_INSTRUCTIONS={p:(n,t) for a,z,n,t in NATIVE_CODE for p in range(a,z,n)}
NATIVE_STARTS={
    0x020cec70:'ptr-sub-bg0-map',0x020cecc4:'ptr-sub-bg1-map',
    0x020cef08:'ptr-sub-bg0-char',0x020cef5c:'ptr-sub-bg1-char',
    0x020cff84:'gx-sub-bg0-map',0x020d0044:'gx-sub-bg1-map',
    0x020d0284:'gx-sub-bg0-char',0x020d0344:'gx-sub-bg1-char',0x02022cc8:'planes-B-toggle',
    CREATE:'heap-create',ALLOC:'heap-alloc',FREE:'heap-free',DESTROY:'heap-destroy',DISABLE:'irq-disable',RESTORE:'irq-restore',
    0x0201a0fc:'callback-set',0x0201a108:'hblank-disable',0x0201a16c:'hblank-internal',
    0x0201acb0:'modes',0x0201ad0c:'bg-ex',0x0201ba88:'translate',0x0201bafc:'dimensions',
    0x0201bc8c:'bg-pos',0x0201be38:'bg-pos-internal',0x0201bf7c:'map-commit',0x0201bf94:'map-range',
    0x0201c014:'map-load',0x0201c0c0:'char-tiles',0x0201c0ec:'char-pixels',0x0201c130:'char-load',
    0x0201c2f0:'map-index',0x0201c8c4:'map-fill',0x0201c914:'map-fill-text',0x0201d650:'put-window-map',
    0x0201d978:'pixel-fill',0x0200e948:'frame-wrapper',0x0200e6b4:'frame-ring',
    0x0201ee8c:'get-bg',0x0201ee90:'get-width',0x0201ee94:'get-height',0x0201ee98:'get-x',0x0201ee9c:'get-y',
    0x02022be8:'banks',0x02022c60:'planes-toggle',0x02022c9c:'planes-A',0x02022d04:'planes-B',
    0x020cec90:'ptr-bg1-map',0x020cece4:'ptr-bg2-map',0x020cef28:'ptr-bg1-char',0x020cef7c:'ptr-bg2-char',
    0x020cffe4:'gx-bg1-map',0x020d00a4:'gx-bg2-map',0x020d02e4:'gx-bg1-char',0x020d03a4:'gx-bg2-char',
    0x020d2894:'cache-flush',0x020d28b8:'write-drain',0x020d3ff4:'dma32',0x020d4064:'dma16',
    0x020d4394:'dma-source-check',0x01ff8488:'dma-itcm',0x020d47b8:'cpu-copy16',0x020d4808:'cpu-copy32',0x020d4858:'cpu-clear-fast'}
class NativeBgBench(NativeHeapBench):
    def __init__(self,compiled,sections):
        self.native_counts={};self.ex_return=None;self.ex_outputs=[];self.highwater=0;self.peak_bg=0;self.publication_sample=None;self.publish_intervals=[];self.publish_masked_max=0;self.operation=None;self.operation_args=();self.fail_stage=None;self.acquisitions=0;self.inject_irq=False;self.irq_waiting=False;self.executed=set();self.masked=0;self.masked_max=0;self.irq_attempts=[]
        super().__init__(compiled,[(p,d) for p,d in sections if 0x02000000<=p<0x02400000])
        self.u.mem_map(0x01ff8000,0x2000)
        self.u.mem_map(0x04001000,0x1000)
        self.u.mem_map(0x05000000,0x1000)
        self.u.mem_map(0x06000000,0x20000)
        self.u.mem_map(0x06200000,0x20000)
        for p,d in sections:
            if p<0x02000000:self.u.mem_write(p,d)
        self.allowed.extend(((STATE,STATE+176),(0x021d110c,0x021d111c),(0x021d21fc,0x021d2204),
            (0x021e15bc,0x021e15da),(0x02110c78,0x02110c80),
            (0x04000000,0x04000004),(0x04000004,0x04000006),(0x04000008,0x04000020),
            (0x04000050,0x04000056),(0x04000060,0x04000062),(0x04000064,0x04000068),(0x0400006c,0x0400006e),
            (0x04001000,0x04001004),(0x04001008,0x04001018),(0x04001050,0x04001056),(0x0400106c,0x0400106e),
            (0x04000208,0x0400020c),(0x04000210,0x04000218),(0x04000240,0x0400024a),
            (0x04000304,0x04000306),(0x05000000,0x05000002),(0x05000400,0x05000420),
            (0x050001a0,0x05000200),(0x050005a0,0x050005c0),(0x06000000,0x06000020),(0x06010000,0x06010020)))
        self.cp15=[];self.clean=set();self.dma=[];self.dma_pending=None;self.upload=None;self.services=[]
        self.allowed.extend(((0x040000d4,0x040000e0),(0x06000020,0x060052a0),
            (0x06010020,0x060152a0),(0x06007b80,0x06007dc0),(0x06017b80,0x06017dc0),
            (0x0600f000,0x06010000),(0x06200000,0x06200020),(0x06210000,0x06210020),
            (0x06200020,0x062052a0),(0x06210020,0x062152a0),(0x0620f000,0x06210000)))
        from unicorn import UC_HOOK_MEM_READ
        self.u.hook_add(UC_HOOK_MEM_READ,self.read)
        self.put(0x04000304,0x203,2)
        self.put(0x02110c7c,1)
        self.put(0x02110c80,3)
        self.u.mem_write(0x021e15c0,bytes(32))
        self.u.mem_write(0x021d110c,bytes(16))
        self.u.mem_write(0x02210000,bytes(range(32)))
    def native_allowed(self,p):return p in NATIVE_INSTRUCTIONS
    def address(self,p,*args):
        bg_stack_arguments(self,args)
        previous=self.operation
        if p&~1==self.symbols.get('bg_callback',0)&~1:self.operation='bg_callback'
        self.masked=0
        try:
            result=super().address(p,*args)
            assert self.u.reg_read(UC_ARM_REG_CPSR)&32,'Thumb return state at caller sentinel'
            return result
        finally:self.operation=previous
    def call(self,name,*args):
        self.operation=name;self.operation_args=args
        try:return super().call(name,*args)
        finally:self.operation=None
    def read(self,u,access,p,n,v,data):
        if 0x04000000<=p<0x04002000:
            assert any(a<=p<p+n<=z for a,z in (
                (0x04000000,0x04000020),(0x04000050,0x04000056),(0x04000060,0x04000070),
                (0x040000b0,0x040000b4),(0x040000b8,0x040000bc),(0x040000c4,0x040000c8),
                (0x040000d0,0x040000e0),(0x04000208,0x0400020c),(0x04000210,0x04000218),
                (0x04000240,0x0400024a),(0x04000304,0x04000306),(0x04001000,0x04001018))),f'unknown MMIO read {p:08x}'
        if p==0x04000006:self.publication_sample=self.instructions
        if p==0x04000006 and self.inject_irq:
            self.irq_attempts.append(('sample',bool(u.reg_read(UC_ARM_REG_CPSR)&128)))
            if u.reg_read(UC_ARM_REG_CPSR)&128:self.irq_waiting=True
            else:self.put(0x04000006,241,2);self.irq_attempts.append(('delivered-before-write',False))
    def store(self,u,access,p,n,v,data):
        super().store(u,access,p,n,v,data)
        if p==BASE+340+76:self.highwater=max(self.highwater,v)
        if p==STATE+8:self.peak_bg=max(self.peak_bg,sum(size for i,size in enumerate((360,2048,2048,21120,21120,2048,2048,21120,21120)) if v&(1<<i)))
        if p in (0x04000000,0x04001000) and self.operation in ('ui_bg_publish','bg_callback') and self.publication_sample is not None:
            self.publish_intervals.append(self.instructions-self.publication_sample)
        if self.operation in ('ui_bg_begin','ui_bg_begin_retained','ui_bg_begin_guide_retained','ui_bg_invalidate_rows','ui_bg_lower_invalidate_rows','ui_bg_lower_fill','ui_bg_fill','ui_bg_rows','ui_bg_lower_rows','ui_bg_unframed','ui_bg_frame','ui_bg_ready') and PARENT<=p<PARENT+0x100000:
            index=self.operation_args[3] if self.operation in ('ui_bg_begin','ui_bg_begin_retained','ui_bg_begin_guide_retained') else self.get(STATE+88)
            assert index in (0,1),'no pending/front heap writes'
            roots=[(self.get(STATE+20+4*index),2048),(self.get(STATE+28+4*index),21120)]
            if self.get(STATE+172):roots += [(self.get(STATE+120+4*index),2048),(self.get(STATE+128+4*index),21120)]
            assert any(a<=p<p+n<=a+size for a,size in roots),'write outside hidden map/pixels'
        if self.get(STATE+12)==2 and self.get(STATE+76)<2 and self.operation not in ('ui_bg_retire',):
            front=self.get(STATE+76)
            immutable=[(0x06000000+front*0x10000,0x8000),(0x0600f000+front*2048,2048),(0x050001c0+32*front,32),
                       (self.get(STATE+20+front*4),2048),(self.get(STATE+28+front*4),21120)]
            if self.get(STATE+172):immutable += [(0x06200000+front*0x10000,0x8000),(0x0620f000+front*2048,2048),
                                                (self.get(STATE+120+front*4),2048),(self.get(STATE+128+front*4),21120)]
            for a,size in immutable:
                assert not (p<a+size and a<p+n),'immutable front write'
        if self.operation in ('ui_bg_publish','bg_callback'):
            if STATE<=p<STATE+176:assert p in (STATE+76,STATE+80) and n==4,'publication state store order/extent'
            assert not PARENT<=p<PARENT+0x100000,'publication cannot touch heap'
            assert p<0x04000000 or p in ((0x04000000,0x0400006c,0x04001000,0x0400106c) if self.get(STATE+172) or self.get(STATE+168)==0x42414c4c else (0x04000000,0x0400006c)),'publication writes only owned planes/first brightness'
        if 0x06000000<=p<0x06020000 or 0x06200000<=p<0x06220000:
            entry=self.symbols.get('ui_bg_install_ball',0)&~1
            end=min((a&~1 for name,a in self.symbols.items() if not name.startswith('$') and a&~1>entry),default=0)
            pc=u.reg_read(UC_ARM_REG_PC)
            static_copy=entry<=pc<end and n==2 and any(a<=p<p+n<=z for a,z in ((0x06200000,0x062005c0),(0x0620f000,0x0620f800)))
            if static_copy:
                assert self.get(STATE+12)==2 and self.get(STATE+76)==2 and self.get(STATE+80)==2
                assert self.get(STATE+168)==0 and self.get(0x0400106c,2)==0x8010
            else:assert self.upload and self.upload[2]<=p<p+n<=self.upload[2]+self.upload[1],f'wrong physical upload {p:08x}'
        if p==0x040000dc and v&0x80000000:
            assert n==4 and v&0x7fe00000 in (0,0x04000000),'unsupported DMA mode'
            self.dma_pending=v
    def hook(self,u,p,n,data):
        check_compiled(self.code,p,n)
        if p in NATIVE_STARTS:self.native_counts[p]=self.native_counts.get(p,0)+1
        if p<0x02200000:assert NATIVE_INSTRUCTIONS.get(p)==(n,1 if u.reg_read(UC_ARM_REG_CPSR)&32 else 0),f'undeclared native instruction {p:08x}'
        self.executed.add(p)
        if self.ex_return and p==self.ex_return[0]:
            _,config,bg=self.ex_return;self.ex_return=None
            output=bytes(u.mem_read(config+8+44*bg,44))
            assert struct.unpack_from('<3I',output)==(0,0,0),'native Ex output map remains NULL before attach'
            assert output[20:24]==bytes((0,1,0,32)) and struct.unpack_from('<2I',output,28)==(4096,4096),'native Ex descriptor output'
            self.ex_outputs.append((bg,output))
        if self.operation in ('ui_bg_begin','ui_bg_begin_retained','ui_bg_begin_guide_retained','ui_bg_invalidate_rows','ui_bg_lower_invalidate_rows','ui_bg_lower_fill','ui_bg_fill','ui_bg_rows','ui_bg_lower_rows','ui_bg_unframed','ui_bg_frame','ui_bg_ready','ui_bg_publish'):
            assert p not in (CREATE,ALLOC,FREE,DESTROY),'allocation during rendering/publication'
        if p==self.symbols.get('ui_alloc38',0)&~1:
            self.acquisitions+=1
            if self.fail_stage==self.acquisitions:
                self.fault_roots=[self.get(TOKEN+28+4*j) for j in range(16) if self.get(TOKEN+28+4*j)]
                self.ret(0);return
        if self.irq_waiting and not u.reg_read(UC_ARM_REG_CPSR)&128:
            self.irq_waiting=False;self.put(0x04000006,241,2);self.irq_attempts.append(('delivered-after-restore',False))
        if u.reg_read(UC_ARM_REG_CPSR)&128:
            self.masked+=1;self.masked_max=max(self.masked_max,self.masked)
            if self.operation in ('ui_bg_publish','bg_callback'):self.publish_masked_max=max(self.publish_masked_max,self.masked)
        else:self.masked=0
        if getattr(self,'dma_pending',None) is not None:
            control=self.dma_pending;self.dma_pending=None
            src=self.get(0x040000d4);dest=self.get(0x040000d8);unit=4 if control&0x04000000 else 2
            count=(control&0x1fffff)*unit
            assert self.upload==(src,count,dest),'DMA source/count/destination semantic'
            assert src%unit==0 and dest%unit==0 and count,'DMA alignment/count'
            assert all(q in self.clean for q in range(src&~31,(src+count+31)&~31,32)),'DMA cache clean coverage'
            for offset in range(0,count,unit):
                value=self.get(src+offset,unit)
                self.store(u,0,dest+offset,unit,value,None)
                self.put(dest+offset,value,unit)
            self.put(0x040000dc,control&~0x80000000);self.dma.append((src,dest,count,unit))
        if p in (0x0201ad0c,0x0201c0c0,0x0201bf7c,0x0201d978,0x0200e948,0x02022c9c,0x02022d04,0x0201a0fc,0x0201d650):
            args=tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3))
            self.services.append((p,args,self.get(u.reg_read(UC_ARM_REG_SP))))
            assert u.reg_read(UC_ARM_REG_SP)%8==0,'native BG ABI alignment'
        if p==0x0201ad0c:
            config,bg,t,kind=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            assert bg in ((1,2,4,5) if self.get(STATE+172) else (1,2)) and kind==0 and self.get(u.reg_read(UC_ARM_REG_SP))==0,'Ex fifth EABI enable zero'
            assert bytes(u.mem_read(t,28))==struct.pack('<4I8BI',0,0,0,0,1,0,30+(bg-4 if bg>=4 else bg-1),4*(bg-4 if bg>=4 else bg-1),0,1,0,0,0),'exact zero-buffer native template'
            self.ex_return=(u.reg_read(UC_ARM_REG_LR)&~1,config,bg)
        if p==0x0200e948:assert self.get(u.reg_read(UC_ARM_REG_R0)+12)==0,'frame geometry has no pixels'
        if p==0x0201c0c0:
            bg=u.reg_read(UC_ARM_REG_R1);src=u.reg_read(UC_ARM_REG_R2);size=u.reg_read(UC_ARM_REG_R3);tile=self.get(u.reg_read(UC_ARM_REG_SP))
            assert bg in ((1,2,4,5) if self.get(STATE+172) else (1,2)) and size>0,'nonzero owned char upload'
            self.upload=(src,size,(0x06200000+(bg-4)*0x10000 if bg>=4 else 0x06000000+(bg-1)*0x10000)+tile*32)
        if p==0x0201bf7c:
            config=u.reg_read(UC_ARM_REG_R0);bg=u.reg_read(UC_ARM_REG_R1)
            assert bg in ((1,2,4,5) if self.get(STATE+172) else (1,2))
            self.upload=(self.get(config+8+44*bg),2048,(0x0620f000+2048*(bg-4) if bg>=4 else 0x0600f000+2048*(bg-1)))
        if p==0x020d2894:self.clean=set()
        if p in (0x020d28a0,0x020d28a4,0x020d28bc):
            # Cache effects are logged over coherent prepared RAM; no DS timing.
            self.cp15.append((p,u.reg_read(UC_ARM_REG_R0)))
            if p==0x020d28a4:self.clean.add(u.reg_read(UC_ARM_REG_R0))
            u.reg_write(UC_ARM_REG_PC,p+4)
        super().hook(u,p,n,data)
    def bgcreate(self):return self.call('ui_bg_create',TOKEN,STATE,1)
    def bgdestroy(self):return self.call('ui_bg_destroy',TOKEN,STATE,1)
class BgRomTests(unittest.TestCase):
    def test_copy_front_to_hidden_checks_dma_and_preserves_all_front_storage(self):
        self.assertIn('ui_bg_begin_copy',self.compiled[1])
        for b in self.benches():
            b.create();b.bgcreate();self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
            self.assertTrue(b.call('ui_bg_begin',TOKEN,STATE,1,0))
            self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,5),1)
            b.u.mem_write(0x02211000,struct.pack('<2I',0,22))
            self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02211000),1)
            self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),1)
            self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),1)
            b.put(0x04000006,192,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
            source=bytes(b.u.mem_read(b.get(STATE+28),21120));mapping=bytes(b.u.mem_read(b.get(STATE+20),2048))
            front=bytes(b.u.mem_read(0x06000000,0x10000)),bytes(b.u.mem_read(0x05000000,512))
            map_address=b.get(STATE+20);old=b.get(map_address,2);b.put(map_address,0xe3dc,2)
            before=bytes(b.u.mem_read(STATE,176)),bytes(b.u.mem_read(b.get(STATE+32),21120))
            self.assertEqual(b.call('ui_bg_begin_copy',TOKEN,STATE,1,1,3),0,'native ring maps cannot be copied as unframed')
            self.assertEqual((bytes(b.u.mem_read(STATE,176)),bytes(b.u.mem_read(b.get(STATE+32),21120))),before)
            b.put(map_address,old,2)
            for address,value in ((0x040000dc,0x80000000),(0x02110c80,2)):
                old=b.get(address);b.put(address,value);before=bytes(b.u.mem_read(STATE,176)),bytes(b.u.mem_read(b.get(STATE+32),21120))
                self.assertEqual(b.call('ui_bg_begin_copy',TOKEN,STATE,1,1,3),0)
                self.assertEqual((bytes(b.u.mem_read(STATE,176)),bytes(b.u.mem_read(b.get(STATE+32),21120))),before)
                b.put(address,old)
            self.assertTrue(b.call('ui_bg_begin_copy',TOKEN,STATE,1,1,3))
            self.assertEqual(bytes(b.u.mem_read(b.get(STATE+32),21120)),source)
            self.assertEqual(bytes(b.u.mem_read(b.get(STATE+24),2048)),mapping)
            self.assertEqual(bytes(b.u.mem_read(0x06010020,21120)),source)
            self.assertEqual((bytes(b.u.mem_read(0x06000000,0x10000)),bytes(b.u.mem_read(0x05000000,512))),front)
            self.assertEqual(b.get(STATE+92),0x3ffffc)
            self.assertEqual((b.get(STATE+68),b.get(STATE+72)),(1,0))
            self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,2),0,'dirty rows still require upload')
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_wvr_owner_change_blocks_publication_without_touching_d_or_pending(self):
        for b in self.benches():
            b.u.mem_write(0x02211000,struct.pack('<10I',4,0,128,0,96,0,256,0,3,16))
            b.address(0x02022be9,0x02211000);prepare_retired_wvr(b)
            b.create();b.bgcreate()
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
            self.prepare(b);self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),1)
            b.put(0x04000006,192,2)
            for p,v,n in ((0x021d4138,1,4),(0x021e1a08,8,4),(0x021e1a12,0x43,2),
                          (0x021d43be,8,2),(0x027fffb0,0xffffffff,4),(0x04000243,0x8a,1)):
                old=b.get(p,n);b.put(p,v,n);before=retired_wvr_snapshot(b);start=len(b.writes)
                self.assertEqual(b.call('ui_bg_publish',STATE,1,240),0)
                self.assertEqual(b.get(STATE+80),0)
                self.assertEqual(retired_wvr_snapshot(b),before)
                self.assertFalse(any(a>=0x04000000 for a,z,value in b.writes[start:]))
                b.put(p,old,n)
            self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
            self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)

    def test_retired_wvr_d_unchanged_through_entry_publish_refresh_and_retire(self):
        for b in self.benches():
            b.u.mem_write(0x02211000,struct.pack('<10I',4,0,128,0,96,0,256,0,3,16))
            b.address(0x02022be9,0x02211000)
            prepare_retired_wvr(b);before=retired_wvr_snapshot(b)
            b.create();b.bgcreate();start=len(b.writes)
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
            for index in (0,1):
                self.prepare(b,index,index+1)
                self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,index+1),1)
                b.put(0x04000006,192,2)
                self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
                self.assertEqual(retired_wvr_snapshot(b),before)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
            self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
            self.assertEqual(retired_wvr_snapshot(b),before)
            protected=((0x04000243,1),(0x021d43bc,12),(0x021d4138,4),
                       (0x021e1a08,22),(0x027fffb0,8))
            self.assertFalse(any(p<a+z and a<p+n for p,n,v in b.writes[start:] for a,z in protected))

    @classmethod
    def setUpClass(cls):
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        paths={l:Path(os.environ.get('SGP_UI_BG_'+l,str(canonical/f'candidate-v4-{l}.nds'))) for l in ROM_PINS}
        missing=[l for l,p in paths.items() if not p.is_file()]
        if missing:
            message='canonical V4 BG native inputs missing: '+','.join(missing)
            if os.environ.get('SGP_UI_BG_REQUIRE_INPUTS')=='1':raise AssertionError(message)
            raise unittest.SkipTest(message)
        import ndspy.rom
        cls.sections={};cls.native_balls={}
        for lang,p in paths.items():
            digest=hashlib.sha256()
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            assert (p.stat().st_size,digest.hexdigest())==ROM_PINS[lang],f'V4 {lang} identity'
            rom=ndspy.rom.NintendoDSRom.fromFile(p);ss=ndspy_load_arm9_sicuro(rom).sections
            for a,n,want in BG_PINS+HEAP_PINS:
                s=next(s for s in ss if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(bytes(s.data[a-s.ramAddress:a-s.ramAddress+n])).hexdigest()==want,f'{lang} native pin {a:08x}'
            cls.sections[lang]=[(s.ramAddress,bytes(s.data)) for s in ss]
            from sgp131.ui_resource import _native_ball
            cls.native_balls[lang]=_native_ball(bytes(rom.files[136]))
            del rom,ss
        cls.temp=tempfile.TemporaryDirectory(prefix='bg-b-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_bg(Path(cls.temp.name))
    def benches(self):
        for l,s in self.sections.items():yield NativeBgBench(self.compiled,s)
    def test_maximum_resource_caps_fit_existing_guide_heap_with_native_headers(self):
        for b in self.benches():
            self.assertEqual(b.create(0x40000),1)
            roots=[b.alloc(n) for n in (4996,69632,131072,1024)]
            self.assertTrue(all(roots));self.assertEqual(b.bgcreate(),1)
            h=b.get(TOKEN+16);node=b.get(h+0x24);free=[]
            while node:
                self.assertLess(len(free),16);free.append(b.get(node+4));node=b.get(node+12)
            self.assertEqual(free,[8364],'both resource maxima + five BG roots + all native headers fit')
            self.assertEqual(b.get(b.counts+76,2),9)
            self.assertEqual(b.bgdestroy(),1)
            for root in reversed(roots):self.assertEqual(b.free(root),1)
            self.assertEqual(b.destroy(),1)

    def test_static_ball_both_upper_buffers_refusal_palette_ownership_and_retirement(self):
        for lang,sections in self.sections.items():
            for role in (0,1):
                b=NativeBgBench(self.compiled,sections);b.create(0x40000)
                self.assertEqual(b.call('ui_bg_create_guide' if role else 'ui_bg_create',TOKEN,STATE,1),1)
                self.assertEqual(b.call('ui_bg_enter_backdrop',TOKEN,STATE,1,0x02210000,0x564c),1)
                src=0x02370000;ball=self.native_balls[lang];b.u.mem_write(src,ball)
                def lower():return (bytes(b.u.mem_read(0x06200000,1472))+bytes(b.u.mem_read(0x0620f000,2048))+bytes(b.u.mem_read(0x05000400,32)))
                def owned():return (bytes(b.u.mem_read(STATE,176)),lower(),bytes(b.u.mem_read(0x04001000,0x80)))
                for address,size in ((src,3551),(src+2,3552),(STATE,3552)):
                    before=owned();self.assertEqual(b.call('ui_bg_install_ball',TOKEN,STATE,1,address,size),0);self.assertEqual(owned(),before)
                for offset in (0,1472,3520):
                    b.u.mem_write(src+offset,bytes([ball[offset]^1]));before=owned()
                    self.assertEqual(b.call('ui_bg_install_ball',TOKEN,STATE,1,src,3552),0);self.assertEqual(owned(),before)
                    b.u.mem_write(src,ball)
                self.assertEqual(b.call('ui_bg_install_ball',TOKEN,STATE,1,src,3552),1)
                self.assertEqual(b.get(STATE+168),0x42414c4c);self.assertEqual(lower(),ball)
                self.assertEqual(b.get(0x04001000)&0x1f00,0,'remain hidden until upper ready')
                for index in (0,1,0):
                    self.assertTrue(b.call('ui_bg_begin',TOKEN,STATE,1,index))
                    self.assertEqual(b.call('ui_bg_lower_window',TOKEN,STATE,1),0)
                    self.assertEqual(b.call('ui_bg_lower_fill',TOKEN,STATE,1,3),0)
                    self.assertEqual(b.call('ui_bg_lower_invalidate_rows',TOKEN,STATE,1,1),0)
                    self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),1)
                    self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),0,'static admission never substitutes upper completion')
                    for row in range(22):
                        b.u.mem_write(0x02212000,struct.pack('<2I',row,1));self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02212000),1)
                    version=max(b.get(STATE+68),b.get(STATE+72))+1
                    self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,version),1)
                    b.put(0x04000006,192,2)
                    for address,value,size in ((0x05000402,0,2),(0x04001010,1,4),(0x04001008,0x1f01,2),(0x04000242,0x81,1)):
                        old=b.get(address,size);b.put(address,value,size);before=owned()
                        self.assertEqual(b.call('ui_bg_publish',STATE,1,240),0);self.assertEqual(owned(),before)
                        b.put(address,old,size)
                    self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
                    self.assertEqual(lower(),ball);self.assertEqual(b.get(0x04001000)&0x1f00,256)
                self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
                self.assertEqual(b.get(0x04001000)&0x1f00,0);self.assertEqual(b.get(0x05000400,2),0)
                self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)

    def test_owned_backdrop_entry_refuses_before_mutation_and_keeps_sub_black(self):
        for language,sections in self.sections.items():
            b=NativeBgBench(self.compiled,sections);b.create();b.bgcreate()
            def snapshot():return tuple(bytes(b.u.mem_read(p,n)) for p,n in ((STATE,176),(TOKEN,92),(0x04000000,0x1000),(0x04001000,0x1000),(0x05000000,0x1000)))
            for generation,palette,color in ((1,0x02210000,0x8000),(1,0x02210000,0xffffffff),(2,0x02210000,0x564c),(1,STATE,0x564c)):
                before=snapshot();self.assertEqual(b.call('ui_bg_enter_backdrop',TOKEN,STATE,generation,palette,color),0);self.assertEqual(snapshot(),before)
            b.u.reg_write(UC_ARM_REG_CPSR,0xdf);before=snapshot()
            self.assertEqual(b.call('ui_bg_enter_backdrop',TOKEN,STATE,1,0x02210000,0x564c),0);self.assertEqual(snapshot(),before)
            b.u.reg_write(UC_ARM_REG_CPSR,0x5f)
            self.assertEqual(b.call('ui_bg_enter_backdrop',TOKEN,STATE,1,0x02210000,0x564c),1)
            self.assertEqual(b.get(0x05000000,2),0x564c);self.assertEqual(b.get(0x05000400,2),0);self.assertEqual(b.get(0x04001000)&0x1f00,0)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1)
            b.bgcreate();self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1);self.assertEqual(b.get(0x05000000,2),0)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_guide_partial_entry_and_failed_retirement_hold_until_repair(self):
        class BrokenLowerEntry(NativeBgBench):
            def hook(self,u,p,n,data):
                returning=self.ex_return
                super().hook(u,p,n,data)
                if returning and p==returning[0] and returning[2]==4:
                    # Actual native Ex completed; corrupt its mode output at the
                    # returned-output seam, before the component can attach it.
                    self.put(returning[1]+8+44*4+20,1,1)
        for lang,sections in self.sections.items():
            b=BrokenLowerEntry(self.compiled,sections);before=b.totals(),b.registry();b.create(0x40000)
            self.assertEqual(b.call('ui_bg_create_guide',TOKEN,STATE,1),1)
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),0)
            self.assertEqual(b.get(STATE+108),3)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
            self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
            self.assertEqual((b.totals(),b.registry()),before)
            b=NativeBgBench(self.compiled,sections);b.create(0x40000);b.call('ui_bg_create_guide',TOKEN,STATE,1)
            b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);b.call('ui_bg_register',STATE,1,240)
            config=b.get(STATE+16);map_ptr=config+8+44*5;old=b.get(map_ptr);b.put(map_ptr,old+4)
            snapshot=bytes(b.u.mem_read(STATE,176));callback=b.get(0x021d110c)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),0)
            self.assertEqual(b.bgdestroy(),0)
            self.assertEqual(bytes(b.u.mem_read(STATE,176)),snapshot)
            self.assertEqual(b.get(0x021d110c),callback);self.assertEqual(b.get(b.counts+76,2),9)
            b.put(map_ptr,old);self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
            # Refused free must preserve the complete remaining ledger/state.
            b.put(b.counts+76,0,2);snapshot=bytes(b.u.mem_read(STATE,176))
            self.assertEqual(b.bgdestroy(),0);self.assertEqual(bytes(b.u.mem_read(STATE,176)),snapshot)
            b.put(b.counts+76,9,2);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_guide_actual_native_null_at_all_nine_positions_and_fragmentation(self):
        sizes=(360,2048,2048,21120,21120,2048,2048,21120,21120)
        for lang,sections in self.sections.items():
            for failure in range(9):
                with self.subTest(lang=lang,failure=failure):
                    b=NativeBgBench(self.compiled,sections);before=b.totals(),b.registry();b.create(0x40000)
                    heap=b.get(TOKEN+16);freebytes=b.get(b.get(heap+0x24)+4)
                    remaining=sum(v+32 for v in sizes[:failure])+16
                    filler=b.alloc(freebytes-32-remaining);self.assertTrue(filler)
                    start=len(b.calls);self.assertEqual(b.call('ui_bg_create_guide',TOKEN,STATE,1),0)
                    self.assertEqual(len([a for p,a in b.calls[start:] if p==ALLOC]),failure+1)
                    self.assertEqual(len([a for p,a in b.calls[start:] if p==FREE]),failure)
                    self.assertEqual(b.get(b.counts+76,2),1)
                    self.assertEqual(bytes(b.u.mem_read(STATE,176)),bytes(176))
                    self.assertEqual(b.free(filler),1);self.assertEqual(b.destroy(),1)
                    self.assertEqual((b.totals(),b.registry()),before)
            b=NativeBgBench(self.compiled,sections);before=b.totals(),b.registry();b.create(0x40000)
            blocks=[b.alloc(18000) for _ in range(13)];self.assertTrue(all(blocks))
            for block in blocks[1::2]:self.assertEqual(b.free(block),1)
            self.assertEqual(b.call('ui_bg_create_guide',TOKEN,STATE,1),0)
            self.assertEqual(b.get(b.counts+76,2),7)
            for block in blocks[::2]:self.assertEqual(b.free(block),1)
            self.assertEqual(b.destroy(),1);self.assertEqual((b.totals(),b.registry()),before)
    def test_guide_lower_alias_role_descriptor_and_lease_guards(self):
        for b in self.benches():
            b.create(0x40000);self.assertEqual(b.call('ui_bg_create_guide',TOKEN,STATE,1),1)
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
            bad=((STATE+172,2,4),(STATE+120,b.get(STATE+20),4),(STATE+128,b.get(STATE+32),4),
                 (STATE+136,b.get(STATE+16)+4,4),(STATE+140,5,1),(STATE+143,29,1),
                 (STATE+148,b.get(STATE+28),4),(b.get(STATE+120)-28,16,4),(0x04001008,0x1e05,2))
            for ptr,val,n in bad:
                old=b.get(ptr,n);b.put(ptr,val,n);start=len(b.services);writes=len(b.writes)
                self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),0)
                self.assertEqual(b.call('ui_bg_lower_window',TOKEN,STATE,1),0)
                self.assertEqual(len(b.services),start)
                self.assertTrue(all(STACK-1024<=p<p+n<=STACK for p,n,v in b.writes[writes:]))
                b.put(ptr,old,n)
            self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),STATE+36)
            pattern=bytes((j*7+j//960)%256 for j in range(21120));pixels=b.get(STATE+128)
            b.u.mem_write(pixels,pattern)
            for mode in (3,0xffffffff):
                b.put(0x02110c80,mode)
                for row,count in ((0,1),(21,1),(3,2)):
                    b.u.mem_write(0x02211000,struct.pack('<2I',row,count))
                    self.assertEqual(b.call('ui_bg_lower_rows',TOKEN,STATE,1,0x02211000),1)
                    self.assertEqual(bytes(b.u.mem_read(0x06200020+row*960,count*960)),pattern[row*960:(row+count)*960])
            b.put(0x02110c80,3)
            self.assertEqual(b.call('ui_bg_lower_fill',TOKEN,STATE,1,15),1)
            self.assertEqual(b.get(STATE+168),0)
            self.assertEqual(bytes(b.u.mem_read(pixels,21120)),b'\xff'*21120)
            self.assertEqual(b.call('ui_bg_lower_invalidate_rows',TOKEN,STATE,1,1),1)
            for ptr in (0,STATE,0xfffffff0,b.get(STATE+120)):
                self.assertEqual(b.call('ui_bg_lower_rows',TOKEN,STATE,1,ptr),0)
            self.assertEqual(b.call('ui_bg_lower_fill',TOKEN,STATE,1,16),0)
            self.assertEqual(b.call('ui_bg_lower_invalidate_rows',TOKEN,STATE,1,1<<22),0)
            self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,1,1),0)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1)
            b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);b.call('ui_bg_begin',TOKEN,STATE,1,0)
            for api,args in (('ui_bg_lower_window',()),('ui_bg_lower_fill',(0,)),('ui_bg_lower_rows',(0x02211000,)),('ui_bg_lower_invalidate_rows',(1,))):
                self.assertEqual(b.call(api,TOKEN,STATE,1,*args),0)
            b.u.mem_write(0x02211000,struct.pack('<3I',1,1,1))
            self.assertEqual(b.call('ui_bg_begin_guide_retained',TOKEN,STATE,1,1,0x02211000),0)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_guide_full_retained_pair_and_coupled_late_publication(self):
        # Catch a missing SUB surface/upload, independent versions or early plane swap.
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=NativeBgBench(self.compiled,sections)
                b.u.mem_write(0x02211000,struct.pack('<10I',4,0,128,0,96,0,256,0,3,16))
                b.address(0x02022be9,0x02211000);prepare_retired_wvr(b)
                wvr_before=retired_wvr_snapshot(b);b.create(0x40000)
                self.assertEqual(b.call('ui_bg_create_guide',TOKEN,STATE,1),1)
                self.assertEqual(b.peak_bg,93032);self.assertEqual(b.get(b.counts+76,2),9)
                self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
                self.assertEqual([v[0] for v in b.ex_outputs],[1,2,4,5])
                self.assertEqual(b.get(0x04001008,2),0x1e01);self.assertEqual(b.get(0x0400100a,2),0x1f11)
                self.assertEqual(bytes(b.u.mem_read(0x050005a0,32)),bytes(range(32)))
                plans=[[],[]];versions=[1,2]
                for index in (0,1):
                    self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,index),STATE+36+16*index)
                    self.assertEqual(b.call('ui_bg_lower_window',TOKEN,STATE,1),STATE+136+16*index)
                    self.assertEqual(b.call('ui_bg_lower_fill',TOKEN,STATE,1,0),1)
                    for lower in (0,1):
                        pixels=b.get(STATE+(128 if lower else 28)+4*index)
                        pattern=bytes((j//960+lower*50+index*25)%256 for j in range(21120))
                        plans[lower].append(pattern);b.u.mem_write(pixels,pattern)
                        b.u.mem_write(0x02211000,struct.pack('<2I',0,21 if lower else 22))
                        api='ui_bg_lower_rows' if lower else 'ui_bg_rows'
                        self.assertEqual(b.call(api,TOKEN,STATE,1,0x02211000),1)
                    self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),1)
                    self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,index+1),0)
                    b.u.mem_write(0x02211000,struct.pack('<2I',21,1))
                    self.assertEqual(b.call('ui_bg_lower_rows',TOKEN,STATE,1,0x02211000),1)
                    start=len(b.services);self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,index+1),1)
                    self.assertEqual([args[1] for p,args,fifth in b.services[start:] if p==0x0201bf7c],[index+1,index+4])
                    self.assertEqual(b.call('ui_bg_lower_window',TOKEN,STATE,1),0)
                    self.assertEqual(b.call('ui_bg_lower_fill',TOKEN,STATE,1,1),0)
                    before=(b.get(0x04000000),b.get(0x04001000),b.get(STATE+80));writes=len(b.writes)
                    b.put(0x04000006,241,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),0)
                    self.assertEqual((b.get(0x04000000),b.get(0x04001000),b.get(STATE+80)),before)
                    self.assertFalse(any(p in (0x04000000,0x04001000) for p,n,v in b.writes[writes:]))
                    b.put(0x04000006,192,2);b.inject_irq=True
                    self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1);b.inject_irq=False
                    plane_stores=[(p,cpsr) for p,n,v,pc,cpsr in b.store_contexts if p in (0x04000000,0x04001000)][-2:]
                    self.assertEqual([p for p,cpsr in plane_stores],[0x04000000,0x04001000])
                    self.assertTrue(all(cpsr&128 for p,cpsr in plane_stores))
                    self.assertEqual(b.get(0x04000000)&0x1f00,(2<<index)<<8)
                    self.assertEqual(b.get(0x04001000)&0x1f00,(1<<index)<<8)
                    self.assertEqual(b.get(0x0400106c,2),0)
                for desc in ((0,1,1),(2,1,1),(1,0,0),(1,1<<22,0),(1,0,1<<22)):
                    b.u.mem_write(0x02211000,struct.pack('<3I',*desc));snapshot=bytes(b.u.mem_read(STATE,176));services=len(b.services)
                    self.assertEqual(b.call('ui_bg_begin_guide_retained',TOKEN,STATE,1,0,0x02211000),0)
                    self.assertEqual(bytes(b.u.mem_read(STATE,176)),snapshot);self.assertEqual(len(b.services),services)
                for ptr in (STATE,b.get(STATE+120),0xfffffff0):
                    self.assertEqual(b.call('ui_bg_begin_guide_retained',TOKEN,STATE,1,0,ptr),0)
                for index,version,upper,lower in ((0,3,1,1<<21),(1,4,1<<3,0),(0,5,0,1<<4)):
                    before=[bytes(b.u.mem_read(base,0x20000)) for base in (0x06000000,0x06200000)]
                    palette=bytes(b.u.mem_read(0x05000000,0x1000));services=len(b.services);dma=len(b.dma)
                    b.u.mem_write(0x02211000,struct.pack('<3I',versions[index],upper,lower))
                    self.assertEqual(b.call('ui_bg_begin_guide_retained',TOKEN,STATE,1,index,0x02211000),STATE+36+16*index)
                    self.assertEqual(len(b.services),services)
                    # Invalid retained descriptor cannot reopen a partial lease.
                    self.assertEqual(b.call('ui_bg_begin_guide_retained',TOKEN,STATE,1,index,0x02211000),0)
                    self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),0)
                    for islower,mask in enumerate((upper,lower)):
                        plan=bytearray(plans[islower][index])
                        for row in range(22):
                            if not mask&(1<<row):continue
                            pattern=bytes([version*20+row])*960;plan[row*960:(row+1)*960]=pattern
                            b.u.mem_write(b.get(STATE+(128 if islower else 28)+4*index)+row*960,pattern)
                            b.u.mem_write(0x02211000,struct.pack('<2I',row,1))
                            self.assertEqual(b.call('ui_bg_lower_rows' if islower else 'ui_bg_rows',TOKEN,STATE,1,0x02211000),1)
                        plans[islower][index]=bytes(plan)
                    self.assertEqual(sum(n for src,d,n,u in b.dma[dma:]),960*(upper.bit_count()+lower.bit_count()))
                    if version==3:
                        self.assertEqual(b.call('ui_bg_lower_invalidate_rows',TOKEN,STATE,1,1<<21),1)
                        self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,version),0)
                        b.u.mem_write(0x02211000,struct.pack('<2I',21,1))
                        self.assertEqual(b.call('ui_bg_lower_rows',TOKEN,STATE,1,0x02211000),1)
                    self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,version),1)
                    for islower,base in enumerate((0x06000000,0x06200000)):
                        expected=bytearray(before[islower]);expected[index*0x10000+32:index*0x10000+32+21120]=plans[islower][index]
                        self.assertEqual(bytes(b.u.mem_read(base,0x20000)),bytes(expected))
                    self.assertEqual(bytes(b.u.mem_read(0x05000000,0x1000)),palette)
                    b.put(0x04000006,192,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1);versions[index]=version
                self.assertEqual(b.call('ui_bg_register',STATE,1,240),1)
                callback=b.get(0x021d110c);self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
                self.assertEqual(b.get(0x021d110c),0)
                for bg in (1,2,4,5):self.assertEqual(b.get(b.get(STATE+16)+8+44*bg),0)
                self.assertEqual(b.get(0x04001000)&0x1f00,0)
                start=len(b.calls);self.assertEqual(b.bgdestroy(),1)
                self.assertEqual(b.get(b.counts+76,2),0);self.assertEqual(b.destroy(),1)
                writes=len(b.writes);b.address(callback,STATE)
                self.assertFalse(any(p in (0x04000000,0x04001000) for p,n,v in b.writes[writes:]))
                self.assertEqual(retired_wvr_snapshot(b),wvr_before)
                self.assertFalse(any(p<=0x04000243<p+n for p,n,v in b.writes))
    def test_unframed_native_preserves_all_660_font_tiles_and_frame_transitions(self):
        for b in self.benches():
            b.create();b.bgcreate();self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
            for index,framed,version in ((0,True,1),(1,False,2),(0,False,3),(1,True,4)):
                self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,index),STATE+36+16*index)
                self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,version),1);self.upload_row(b,0,22)
                if framed:
                    b.u.mem_write(0x02212000,b'F'*576);b.u.mem_write(0x02213000,b'P'*32)
                    b.u.mem_write(0x02211000,struct.pack('<8I',3,2,25,20,0x02212000,576,0x02213000,32))
                    self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),1)
                else:
                    services=len(b.services);palette=bytes(b.u.mem_read(0x05000000,0x1000))
                    self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),1)
                    self.assertEqual(len(b.services),services)
                    self.assertEqual(bytes(b.u.mem_read(0x05000000,0x1000)),palette)
                    self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),0)
                    mapping=struct.unpack('<1024H',bytes(b.u.mem_read(b.get(STATE+20+4*index),2048)))
                    for row in range(32):
                        for col in range(32):self.assertEqual(mapping[32*row+col],0xd001+(row-1)*30+col-1 if 1<=row<=22 and 1<=col<=30 else 0)
                self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,version),1)
                b.put(0x04000006,192,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
                self.assertEqual(b.get(0x04001000)&0x1f00,0);self.assertEqual(b.get(0x05000400,2),0)
    def retained_pair(self,b):
        """Two distinct complete plans; bytes are synthetic caller-painted tile data."""
        b.create();b.bgcreate();self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
        plans=[]
        for index,selection,counter in ((0,4,1),(1,7,2)):
            plan=[bytes([0x10+row])*960 for row in range(22)]
            plan[selection]=bytes([0xe0+selection])*960;plan[0]=bytes([counter])*960
            plans.append(plan)
            self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,index),STATE+36+16*index)
            self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,0),1)
            b.u.mem_write(b.get(STATE+28+4*index),b''.join(plan))
            start=len(b.dma);self.upload_row(b,0,22)
            self.assertEqual([n for src,dest,n,unit in b.dma[start:]],[21120])
            b.u.mem_write(0x02212000,bytes([0x40+index])*576)
            b.u.mem_write(0x02213000,bytes([0x60+index])*32)
            b.u.mem_write(0x02211000,struct.pack('<8I',3,2,25,20,0x02212000,576,0x02213000,32))
            self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),1)
            self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,index+1),1)
            b.put(0x04000006,192,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
        return plans
    def upload_row(self,b,row,count=1):
        b.u.mem_write(0x02211000,struct.pack('<2I',row,count))
        self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02211000),1)
    def test_retained_three_alternating_histories_exact_dirty_union_and_unchanged_assets(self):
        for lang,sections in self.sections.items():
            for selections in ((10,13,16),(7,4,10),(4,7,4)):
                with self.subTest(lang=lang,selections=selections):
                    b=NativeBgBench(self.compiled,sections);plans=self.retained_pair(b)
                    old_selection=[4,7];versions=[1,2]
                    for index,version,selection in zip((0,1,0),(3,4,5),selections):
                        dirty=sorted({0,old_selection[index],selection});mask=sum(1<<r for r in dirty)
                        vram=bytes(b.u.mem_read(0x06000000,0x20000));palette=bytes(b.u.mem_read(0x05000000,0x1000))
                        maps=[bytes(b.u.mem_read(b.get(STATE+20+4*i),2048)) for i in range(2)]
                        pixels=[bytes(b.u.mem_read(b.get(STATE+28+4*i),21120)) for i in range(2)]
                        services=len(b.services);dma=len(b.dma)
                        self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,index,versions[index],mask),STATE+36+16*index)
                        self.assertEqual(b.get(STATE+92),0x3fffff^mask)
                        self.assertEqual(len(b.services),services);self.assertEqual(len(b.dma),dma)
                        for i in range(2):
                            self.assertEqual(bytes(b.u.mem_read(b.get(STATE+20+4*i),2048)),maps[i])
                            self.assertEqual(bytes(b.u.mem_read(b.get(STATE+28+4*i),21120)),pixels[i])
                        plans[index][old_selection[index]]=bytes([0x10+old_selection[index]])*960
                        plans[index][selection]=bytes([0xe0+selection])*960;plans[index][0]=bytes([version])*960
                        for row in dirty:
                            b.u.mem_write(b.get(STATE+28+4*index)+960*row,plans[index][row]);self.upload_row(b,row)
                        row_dma=b.dma[dma:]
                        self.assertEqual([(d,n) for src,d,n,u in row_dma],[(0x06000020+0x10000*index+960*r,960) for r in dirty])
                        self.assertEqual(sum(n for src,d,n,u in row_dma),960*len(dirty));self.assertLess(960*len(dirty),21120)
                        self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,version),1)
                        expected=bytearray(vram)
                        for row in dirty:expected[index*0x10000+32+960*row:index*0x10000+32+960*(row+1)]=plans[index][row]
                        self.assertEqual(bytes(b.u.mem_read(0x06000000,0x20000)),bytes(expected))
                        self.assertEqual(bytes(b.u.mem_read(0x05000000,0x1000)),palette)
                        self.assertEqual(bytes(b.u.mem_read(0x06000020+0x10000*index,21120)),b''.join(plans[index]))
                        self.assertFalse(any(p in (0x0201d650,0x0200e948) for p,args,fifth in b.services[services:]))
                        b.put(0x04000006,241,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),0)
                        self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,1-index,versions[1-index],1),0)
                        self.assertEqual(b.call('ui_bg_invalidate_rows',TOKEN,STATE,1,1),0)
                        b.put(0x04000006,192,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
                        versions[index]=version;old_selection[index]=selection
                    self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_retained_refuses_uninitialized_stale_malformed_front_and_partial_leases(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=NativeBgBench(self.compiled,sections);b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
                self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,0,1),0)
                self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,1,1),0)
                b=NativeBgBench(self.compiled,sections);self.retained_pair(b)
                for generation,index,previous,mask in ((2,0,1,1),(1,2,1,1),(1,1,2,1),(1,0,0,1),(1,0,2,1),
                                                       (1,0,1,0),(1,0,1,1<<22),(1,0,1,0xffffffff)):
                    state=bytes(b.u.mem_read(STATE,120));services=len(b.services);writes=len(b.writes)
                    self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,generation,index,previous,mask),0)
                    self.assertEqual(bytes(b.u.mem_read(STATE,120)),state);self.assertEqual(len(b.services),services)
                    self.assertTrue(all(STACK-960<=p<p+n<=STACK for p,n,v in b.writes[writes:]))
                for address,value,width in ((STATE+96,0,4),(STATE+100,0,4),(STATE+92,0x3ffffe,4),
                                             (STATE+36,0,4),(STATE+20,b.get(STATE+24),4),
                                             (0x04000000,0x10600,4),(0x04000240,0x82,1)):
                    old=b.get(address,width);b.put(address,value,width);services=len(b.services)
                    self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,1,1),0)
                    self.assertEqual(len(b.services),services);b.put(address,old,width)
                self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,1,1),STATE+36)
                for mask in (0,1<<22,0xffffffff):
                    old=b.get(STATE+92);self.assertEqual(b.call('ui_bg_invalidate_rows',TOKEN,STATE,1,mask),0);self.assertEqual(b.get(STATE+92),old)
                self.assertEqual(b.call('ui_bg_invalidate_rows',TOKEN,STATE,2,1),0)
                self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),0,'retained frame cannot be replaced')
                self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),0,'no implicit cancellation')
                self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,1,1),0,'partial old version cannot be reused')
                for address,value in ((0x02110c80,2),(0x040000dc,0x80000000)):
                    old=b.get(address);b.put(address,value);b.u.mem_write(0x02211000,struct.pack('<2I',0,1))
                    self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02211000),0);b.put(address,old)
                self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_retained_invalidate_after_upload_duplicate_and_full_fill_cannot_publish_partial(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=NativeBgBench(self.compiled,sections);self.retained_pair(b)
                self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,1,3),STATE+36)
                self.upload_row(b,0);self.upload_row(b,0)
                self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,3),0,'duplicate upload cannot cover missing row')
                self.upload_row(b,1)
                self.assertEqual(b.call('ui_bg_invalidate_rows',TOKEN,STATE,1,2),1)
                b.u.mem_write(b.get(STATE+28)+960,b'Z'*960)
                self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,3),0,'invalidation revokes previous upload')
                self.upload_row(b,1)
                self.assertEqual(bytes(b.u.mem_read(0x06000020+960,960)),b'Z'*960)
                for stale in (0,1,2):self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,stale),0)
                self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,3),1)
                self.upload_row(b,0,2)
                self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,3),0,'full fill invalidates all rows')
                self.upload_row(b,2,20)
                self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,3),1)
                self.assertEqual(bytes(b.u.mem_read(0x06000020,21120)),bytes([0x33])*21120)
    def test_retained_invalidate_normal_preparation_revokes_completed_upload(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=NativeBgBench(self.compiled,sections);b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b)
                vram=bytes(b.u.mem_read(0x06000000,0x20000));pixels=bytes(b.u.mem_read(b.get(STATE+28),21120))
                services=len(b.services)
                self.assertEqual(b.call('ui_bg_invalidate_rows',TOKEN,STATE,1,1<<21),1)
                self.assertEqual(b.call('ui_bg_invalidate_rows',TOKEN,STATE,1,1<<21),1)
                self.assertEqual(bytes(b.u.mem_read(0x06000000,0x20000)),vram)
                self.assertEqual(bytes(b.u.mem_read(b.get(STATE+28),21120)),pixels);self.assertEqual(len(b.services),services)
                self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),0)
                self.upload_row(b,21);self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),1)
    def test_native_faults_real_exhaustion_fragmentation_and_topology_restore(self):
        for lang,sections in self.sections.items():
            for failure in range(1,6):
                b=NativeBgBench(self.compiled,sections);before=b.totals(),b.registry();b.create();b.fail_stage=failure
                start=len(b.calls);self.assertEqual(b.bgcreate(),0)
                allocated=[args for p,args in b.calls[start:] if p==ALLOC]
                freed=[args for p,args in b.calls[start:] if p==FREE]
                self.assertEqual(len(allocated),failure-1);self.assertEqual(len(freed),failure-1)
                self.assertEqual([args[1]+16 for args in freed],b.fault_roots[::-1])
                self.assertEqual(b.get(b.counts+76,2),0);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
                self.assertEqual((b.totals(),b.registry()),before)
                self.assertFalse(any(p>=0x04000000 for p,n,v in b.writes))
            b=NativeBgBench(self.compiled,sections);before=b.totals(),b.registry();b.create()
            huge=b.alloc(0x2f000);self.assertTrue(huge);self.assertEqual(b.bgcreate(),0);self.assertEqual(b.free(huge),1)
            blocks=[b.alloc(18000) for _ in range(10)];self.assertTrue(all(blocks))
            for p in blocks[1::2]:self.assertEqual(b.free(p),1)
            self.assertEqual(b.bgcreate(),0)
            self.assertEqual(b.get(b.counts+76,2),5)
            for p in blocks[::2]:self.assertEqual(b.free(p),1)
            self.assertEqual(b.destroy(),1);self.assertEqual((b.totals(),b.registry()),before)
    def test_descriptor_alias_extent_and_generation_refuse_before_native_mutation(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            config=b.get(STATE+16);pixels=b.get(STATE+28);map0=b.get(STATE+20)
            bad=((STATE+36,config+4,4),(STATE+40,5,1),(STATE+41,0,1),(STATE+43,31,1),
                 (STATE+45,14,1),(STATE+46,0x8001,2),(STATE+48,0xfffffff0,4),
                 (STATE+28,b.get(STATE+32),4),(STATE+20,b.get(STATE+24),4),
                 (config+52,map0+4,4),(config+56,0,4),(config+72,1,1),(pixels-28,16,4))
            for address,value,width in bad:
                old=b.get(address,width);b.put(address,value,width);start=len(b.services);writes=len(b.writes)
                self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),0)
                self.assertEqual(len(b.services),start)
                self.assertTrue(all(STACK-1024<=p<p+n<=STACK for p,n,v in b.writes[writes:]))
                b.put(address,old,width)
            self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,2,0),0)
            self.assertEqual(b.call('ui_bg_begin',TOKEN,0xfffffff0,1,0),0)
    def test_state_prefix_alias_refuses_before_native_free_then_boundary_cleanup(self):
        # Guide's storage windows need not yet be initialized. Place the complete
        # native/GF prefix inside those unchecked fields, preserving all roots.
        for lang,sections in self.sections.items():
            with self.subTest(language=lang):
                b=NativeBgBench(self.compiled,sections);before=b.totals(),b.registry()
                self.assertEqual(b.create(0x40000),1);caller=b.alloc(176);self.assertTrue(caller)
                self.assertEqual(b.call('ui_bg_create_guide',TOKEN,STATE,1),1);root=b.get(STATE+16)
                self.assertEqual(caller+176,root-32)
                original=bytes(b.u.mem_read(STATE,176));prefix=bytes(b.u.mem_read(root-32,32))
                moved=root-168;b.u.mem_write(moved,original[:136]);b.put(moved+172,1)
                b.u.mem_write(STATE,bytes(176))
                self.assertEqual(bytes(b.u.mem_read(root-32,32)),prefix)
                raw=b.get(TOKEN+12);snapshot=(bytes(b.u.mem_read(raw,0x40000)),b.token(),b.metadata())
                calls=len(b.calls);writes=len(b.writes)
                self.assertEqual(b.call('ui_bg_destroy',TOKEN,moved,1),0,'state/native-prefix overlap must refuse before freeing')
                self.assertEqual((bytes(b.u.mem_read(raw,0x40000)),b.token(),b.metadata()),snapshot)
                self.assertEqual(len(b.calls),calls)
                self.assertTrue(all(STACK-1024<=p<p+n<=STACK for p,n,v in b.writes[writes:]))
                # Move the authoritative original to its live176B caller block,
                # restore the touched config word, and end exactly at the prefix.
                b.u.mem_write(caller,original);b.put(root+4,0)
                self.assertEqual(b.call('ui_bg_retire',TOKEN,caller,1),1)
                self.assertEqual(b.call('ui_bg_destroy',TOKEN,caller,1),1)
                self.assertEqual(bytes(b.u.mem_read(caller,176)),bytes(176))
                self.assertEqual(b.get(b.counts+76,2),1)
                self.assertEqual(b.free(caller),1);self.assertEqual(b.destroy(),1)
                self.assertEqual((b.totals(),b.registry()),before)
    def test_token_prefix_alias_refuses_before_retire_then_authoritative_cleanup(self):
        # Removing the token-prefix exclusion admits STORAGE retirement with an
        # overlapping token. Its last ledger word is the preserved NNS signature;
        # retire must reject the overlap itself, before any native free is attempted.
        for lang,sections in self.sections.items():
            with self.subTest(language=lang):
                b=NativeBgBench(self.compiled,sections);before=b.totals(),b.registry()
                self.assertEqual(b.create(),1);caller=b.alloc(92);self.assertTrue(caller)
                self.assertEqual(b.bgcreate(),1);root=b.get(STATE+16)
                self.assertEqual(caller+92,root-32)
                original=b.token();prefix=bytes(b.u.mem_read(root-32,32));moved=caller+4
                b.u.mem_write(moved,original[:88]);b.u.mem_write(TOKEN,bytes(92))
                self.assertEqual(bytes(b.u.mem_read(root-32,32)),prefix)
                raw=int.from_bytes(original[12:16],'little')
                snapshot=(bytes(b.u.mem_read(raw,0x30000)),bytes(b.u.mem_read(STATE,120)),b.metadata())
                calls=len(b.calls);writes=len(b.writes)
                self.assertEqual(b.call('ui_bg_retire',moved,STATE,1),0,'token/native-prefix overlap must refuse')
                self.assertEqual(b.call('ui_bg_destroy',moved,STATE,1),0)
                self.assertEqual((bytes(b.u.mem_read(raw,0x30000)),bytes(b.u.mem_read(STATE,120)),b.metadata()),snapshot)
                self.assertEqual(len(b.calls),calls)
                self.assertTrue(all(STACK-1024<=p<p+n<=STACK for p,n,v in b.writes[writes:]))
                # Correct the location and unused ledger word using the saved
                # authoritative image; no native header is reset or rebuilt.
                b.u.mem_write(caller,original)
                self.assertEqual(b.call('ui_bg_retire',caller,STATE,1),1)
                self.assertEqual(b.call('ui_bg_destroy',caller,STATE,1),1)
                self.assertEqual(bytes(b.u.mem_read(root-32,4)),bytes.fromhex('52460000'))
                self.assertEqual(b.get(b.counts+76,2),1)
                b.u.mem_write(TOKEN,bytes(b.u.mem_read(caller,92)))
                self.assertEqual(b.free(caller),1);self.assertEqual(b.destroy(),1)
                self.assertEqual((b.totals(),b.registry()),before)
    def test_frame_geometry_bounds_bad_lengths_sources_and_rows_no_side_effects(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);b.call('ui_bg_begin',TOKEN,STATE,1,0)
            frame=[3,2,25,20,0x02212000,576,0x02213000,32]
            for field,value in ((0,1),(0,29),(0,0xffffffff),(1,0),(1,22),(2,0),(2,26),(2,257),(3,0),(3,21),(4,0xfffffff0),(4,b.get(STATE+28)),(5,0),(5,575),(6,0x050001a0),(7,512)):
                request=frame.copy();request[field]=value;b.u.mem_write(0x02211000,struct.pack('<8I',*request));start=len(b.services)
                self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),0)
                self.assertEqual(len(b.services),start)
            for first,count in ((22,1),(0,0),(21,2),(0,0xffffffff),(0xffffffff,1)):
                b.u.mem_write(0x02211000,struct.pack('<2I',first,count));start=len(b.services)
                self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02211000),0);self.assertEqual(len(b.services),start)
    def test_three_alternating_complete_patterns_missed_swap_and_front_isolation(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            front=None
            for index,version,color in ((0,1,1),(1,2,15),(0,3,0)):
                snapshots=None if front is None else (bytes(b.u.mem_read(0x06000000+0x10000*front,0x8000)),bytes(b.u.mem_read(0x0600f000+2048*front,2048)),bytes(b.u.mem_read(0x050001c0+32*front,32)))
                self.prepare(b,index,color);self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,version),1)
                if snapshots is not None:
                    self.assertEqual((bytes(b.u.mem_read(0x06000000+0x10000*front,0x8000)),bytes(b.u.mem_read(0x0600f000+2048*front,2048)),bytes(b.u.mem_read(0x050001c0+32*front,32))),snapshots)
                b.put(0x04000006,241,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),0)
                self.assertEqual(b.get(STATE+80),index)
                self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,1-index),0)
                b.put(0x04000006,240,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
                self.assertEqual(b.get(0x04000000)&0x1f00,0x200<<index);self.assertEqual(b.get(0x04001000)&0x1f00,0)
                self.assertEqual(bytes(b.u.mem_read(0x06000020+0x10000*index,21120)),bytes([color*17])*21120)
                self.assertEqual(bytes(b.u.mem_read(0x050001a0,32)),bytes(range(32)))
                self.assertEqual(b.get(STATE+68+4*index),version);front=index
    def test_irq_injection_and_ime_preserved_with_explicit_deadline(self):
        for lang,sections in self.sections.items():
            for mask in (0,128):
                for ime in (0,1):
                    b=NativeBgBench(self.compiled,sections);b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b);b.call('ui_bg_ready',TOKEN,STATE,1,1)
                    b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime);b.put(0x04000006,192,2);b.inject_irq=True
                    self.assertEqual(b.call('ui_bg_publish',STATE,1,240),1)
                    self.assertEqual(b.irq_attempts[0],('sample',True))
                    self.assertEqual(b.get(0x04000000)&0x1f00,0x200)
                    if mask:self.assertTrue(b.irq_waiting)
                    else:self.assertEqual(b.irq_attempts[-1],('delivered-after-restore',False))
    def test_incomplete_stale_retire_and_unknown_callback_hold(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);b.call('ui_bg_begin',TOKEN,STATE,1,0)
            self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),0)
            self.assertEqual(b.call('ui_bg_register',STATE,1,240),1)
            actual=b.get(0x021d1110);b.put(0x021d1110,actual+4)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),0);self.assertEqual(b.bgdestroy(),0)
            self.assertEqual(b.get(b.counts+76,2),5);b.put(0x021d1110,actual)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1)
    def test_request_descriptors_can_live_in_admitted_caller_dtcm(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);b.call('ui_bg_begin',TOKEN,STATE,1,0)
            request=0x027e3500;b.u.mem_write(request,struct.pack('<2I',0,22))
            self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,request),1)
            b.u.mem_write(request,struct.pack('<8I',3,2,25,20,0x02212000,576,0x02213000,32))
            self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,request),1)
    def test_authoritative_heap_token_move_to_admitted_high_dtcm_frame(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            moved=0x027e3600;b.u.mem_write(moved,b.token());b.u.mem_write(TOKEN,bytes(92))
            self.assertEqual(b.call('ui_bg_begin',moved,STATE,1,0),STATE+36)
            self.assertEqual(b.call('ui_bg_retire',moved,STATE,1),1)
            self.assertEqual(b.call('ui_bg_destroy',moved,STATE,1),1)
            self.assertEqual(b.call('ui_heap38_destroy',moved),1)
    def test_hidden_preparation_refuses_unexpected_visible_plane_or_bank(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            for address,value,width in ((0x04000000,0x10600,4),(0x04000240,0x82,1),(0x04000304,0x8000,2)):
                old=b.get(address,width);b.put(address,value,width)
                self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),0)
                b.put(address,old,width)
    def test_entry_admission_refusals_and_unrelated_power_bits_preserved(self):
        for b in self.benches():
            b.create();b.bgcreate()
            for address,value,width in ((IME,0,4),(0x04000304,3,2),(0x02110c7c,0,4),(0x02110c80,2,4),
                    (0x040000b8,0x80000000,4),(0x040000dc,0x80000000,4),(0x04000064,0x80000000,4),
                    (0x021d110c,0x02000001,4),(0x021d1114,0x02000001,4)):
                old=b.get(address,width);b.put(address,value,width);start=len(b.services);writes=len(b.writes)
                self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),0);self.assertEqual(len(b.services),start)
                self.assertFalse(any(p>=0x04000000 for p,n,v in b.writes[writes:]));b.put(address,old,width)
            b.u.reg_write(UC_ARM_REG_CPSR,0xdf);self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),0)
            b.u.reg_write(UC_ARM_REG_CPSR,0x5f);b.put(0x04000304,0x25b,2)
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1);self.assertEqual(b.get(0x04000304,2),0x825b)
    def test_actual_free_refusal_retains_ownership_until_authoritative_metadata_repaired(self):
        for b in self.benches():
            b.create();b.bgcreate();before=bytes(b.u.mem_read(STATE,120)),b.token()
            b.put(b.counts+76,0,2)
            self.assertEqual(b.bgdestroy(),0);self.assertEqual((bytes(b.u.mem_read(STATE,120)),b.token()),before)
            b.put(b.counts+76,5,2);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_cpu_sentinel_complete_second_canvas_and_halfword_map(self):
        for b in self.benches():
            b.put(0x02110c80,0xffffffff);b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            self.prepare(b,1,15);self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),1)
            self.assertEqual(bytes(b.u.mem_read(0x0600f800,2048)),bytes(b.u.mem_read(b.get(STATE+24),2048)))
            self.assertEqual(bytes(b.u.mem_read(0x06010020,21120)),b'\xff'*21120)
            self.assertEqual(bytes(b.u.mem_read(0x050001e0,32)),bytes([15])*32)
            self.assertEqual(b.dma,[])
            self.assertIn(0x020d47b8,b.executed)
    def test_native_frame_min_max_internal_rectangles_and_reserved_canaries(self):
        for lang,sections in self.sections.items():
            for x,y,w,h in ((3,2,1,1),(3,2,25,20),(8,5,12,8),(27,21,1,1)):
                b=NativeBgBench(self.compiled,sections);b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);b.call('ui_bg_begin',TOKEN,STATE,1,0)
                original=list(struct.unpack('<1024H',b.u.mem_read(b.get(STATE+20),2048)));expected=original.copy()
                for dx,tile in ((-2,0),(-1,1),(w,3),(w+1,4),(w+2,5)):
                    expected[32*(y-1)+x+dx]=0xe3dc+tile;expected[32*(y+h)+x+dx]=0xe3e8+tile
                for dx in range(w):expected[32*(y-1)+x+dx]=0xe3de;expected[32*(y+h)+x+dx]=0xe3ea
                for dy in range(h):
                    for dx,tile in ((-2,6),(-1,7),(w,9),(w+1,10),(w+2,11)):expected[32*(y+dy)+x+dx]=0xe3dc+tile
                b.u.mem_write(0x06007dc0,b'Z'*576)
                b.u.mem_write(0x02211000,struct.pack('<8I',x,y,w,h,0x02212000,576,0x02213000,32))
                self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),1)
                self.assertEqual(list(struct.unpack('<1024H',b.u.mem_read(b.get(STATE+20),2048))),expected)
                self.assertEqual(bytes(b.u.mem_read(0x06007dc0,576)),b'Z'*576)
    def test_native_callback_dispatch_and_retire_at_prepare_pending_front(self):
        for lang,sections in self.sections.items():
            for stage in ('prepare','pending','front'):
                b=NativeBgBench(self.compiled,sections);before=b.totals(),b.registry();b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b)
                if stage!='prepare':self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),1)
                self.assertEqual(b.call('ui_bg_register',STATE,1,240),1)
                if stage=='front':
                    b.put(0x04000006,192,2);callback=b.get(0x021d110c)
                    b.address(callback,b.get(0x021d1110)) # declared post-wait dispatch seam
                    self.assertEqual(b.get(STATE+76),0)
                self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
                self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
                self.assertEqual((b.totals(),b.registry()),before)
    def test_registered_callback_rejects_changed_lifecycle_generation(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b);b.call('ui_bg_ready',TOKEN,STATE,1,1)
            b.call('ui_bg_register',STATE,1,240);b.put(STATE+4,2);b.put(0x04000006,192,2)
            b.address(b.get(0x021d110c),STATE)
            self.assertEqual(b.get(STATE+76),2,'registered generation stays bound')
            self.assertEqual(b.get(STATE+80),0)
    def test_publication_stale_generation_version_and_deadline_refuse(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b);b.call('ui_bg_ready',TOKEN,STATE,1,1);b.put(0x04000006,192,2)
            for off,value in ((4,2),(12,3),(68,2),(80,2),(84,0)):
                old=b.get(STATE+off);b.put(STATE+off,value);before=b.get(0x04000000)
                self.assertEqual(b.call('ui_bg_publish',STATE,1,240),0);self.assertEqual(b.get(0x04000000),before)
                b.put(STATE+off,old)
            for deadline in (0,191,262,0xffffffff):self.assertEqual(b.call('ui_bg_publish',STATE,1,deadline),0)
    def test_second_frame_in_one_preparation_refused_without_old_ring_residue(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b)
            previous=bytes(b.u.mem_read(b.get(STATE+20),2048));start=len(b.services)
            b.u.mem_write(0x02211000,struct.pack('<8I',8,5,12,8,0x02212000,576,0x02213000,32))
            self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),0)
            self.assertEqual(bytes(b.u.mem_read(b.get(STATE+20),2048)),previous);self.assertEqual(len(b.services),start)
    def test_semantic_mutants_require_green_baseline_and_specific_failure(self):
        mutants=(
            ('early-pending','unsigned line=B_REG16(0x04000006);','b->pending=UI_BG_NONE;unsigned line=B_REG16(0x04000006);','late pending retained'),
            ('plane','B_A(2u<<i);','B_A(1u<<i);','exact MAIN plane'),
            ('lower','bg_barrier();b->front=i;','B_B(1);bg_barrier();b->front=i;','publication writes only owned'),
            ('irq','unsigned irq=B_DISABLE(),ok=0;','unsigned irq=0,ok=0;','IRQ deferred'),
            ('zero','i+1,(const unsigned char *)b->roots[i+3]+960*r->first,960*r->count,1+30*r->first','i+1,(const unsigned char *)b->roots[i+3]+960*r->first,0,1+30*r->first','nonzero owned char upload'),
            ('geometry','f->width>28-f->x','(unsigned char)f->width>28-f->x','widened geometry refusal'),
            ('copy-after-ring','B_RING(&geometry,0x3DC,14+i);','B_RING(&geometry,0x3DC,14+i);((void (*)(UiNativeWindow16 *))0x0201D651)(&b->windows[i]);','frame ring retained'),
            ('vram','t.charBase=4*index;','t.charBase=2*index;','exact zero-buffer native template|wrong physical upload'),
            ('palette','bg_palette(0x050001C0+32*i,f->palette);','bg_palette(0x050001A0,f->palette);','font palette immutable'),
            ('version','b->version[i]=version;','b->version[i]=version+1;','complete version published'))
        for kind,old,new,reason in mutants:
            for lang,sections in self.sections.items():
                with self.subTest(kind=kind,lang=lang):
                    self.mutation_scenario(kind,self.compiled,sections)
                    with tempfile.TemporaryDirectory(prefix='bg-mutant-') as d:
                        compiled=compile_bg(Path(d),(old,new))
                        with self.assertRaisesRegex(AssertionError,reason):self.mutation_scenario(kind,compiled,sections)
    def mutation_scenario(self,kind,compiled,sections):
        b=NativeBgBench(compiled,sections);b.create();b.bgcreate()
        self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
        if kind=='vram':return
        if kind=='geometry':
            b.call('ui_bg_begin',TOKEN,STATE,1,0)
            b.u.mem_write(0x02211000,struct.pack('<8I',3,2,257,1,0x02212000,576,0x02213000,32))
            self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),0,'widened geometry refusal');return
        self.prepare(b)
        self.assertEqual(b.get(b.get(STATE+20)+66,2),0xe3dc,'frame ring retained')
        self.assertEqual(bytes(b.u.mem_read(0x050001a0,32)),bytes(range(32)),'font palette immutable')
        b.call('ui_bg_ready',TOKEN,STATE,1,1)
        b.put(0x04000006,241 if kind=='early-pending' else 192,2)
        if kind=='irq':b.inject_irq=True
        result=b.call('ui_bg_publish',STATE,1,240)
        if kind=='early-pending':self.assertEqual(b.get(STATE+80),0,'late pending retained');return
        self.assertEqual(result,1,'IRQ deferred' if kind=='irq' else 'complete version published')
        self.assertEqual(b.get(0x04000000)&0x1f00,0x200,'exact MAIN plane')
    def prepare(self,b,index=0,color=1):
        self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,index),STATE+36+16*index)
        self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,color),1)
        b.u.mem_write(0x02211000,struct.pack('<2I',0,22))
        self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02211000),1)
        b.u.mem_write(0x02212000,bytes([color])*576);b.u.mem_write(0x02213000,bytes([color])*32)
        b.u.mem_write(0x02211000,struct.pack('<8I',3,2,25,20,0x02212000,576,0x02213000,32))
        self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),1)
    def test_ready_commits_final_map_before_pending_then_immutable(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b)
            start=len(b.writes);self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,7),1)
            writes=b.writes[start:];pending=max(i for i,(p,n,v) in enumerate(writes) if p==STATE+80)
            self.assertGreater(pending,max(i for i,(p,n,v) in enumerate(writes) if 0x0600f000<=p<0x0600f800))
            self.assertEqual([p for p,n,v in writes if STATE<=p<STATE+176][-1],STATE+80)
            self.assertEqual(b.get(STATE+80),0)
            self.assertEqual(bytes(b.u.mem_read(0x0600f000,2048)),bytes(b.u.mem_read(b.get(STATE+20),2048)))
            self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,1),0)
            self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,15),0)
            start=len(b.services)
            self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02211000),0)
            self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),0)
            self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,8),0)
            self.assertEqual(len(b.services),start)
    def test_publication_preserves_late_pending_and_saved_irq(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000);self.prepare(b)
            # Fixture metadata isolates publication until ready is implemented.
            b.put(STATE+68,7);b.put(STATE+80,0);b.put(STATE+84,7);b.put(STATE+88,2)
            for line,want in ((191,0),(241,0),(262,0),(0,0),(192,1)):
                b.put(0x04000006,line,2)
                start=len(b.writes);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),want)
                if want:
                    writes=b.writes[start:]
                    plane=next(i for i,(p,n,v) in enumerate(writes) if p==0x04000000)
                    front=next(i for i,(p,n,v) in enumerate(writes) if p==STATE+76)
                    pending=next(i for i,(p,n,v) in enumerate(writes) if p==STATE+80)
                    self.assertLess(plane,front);self.assertLess(plane,pending)
                self.assertEqual(b.get(STATE+80),2 if want else 0)
                self.assertEqual(b.get(0x04000000)&0x1f00,0x200 if want else 0)
    def test_retire_clears_callback_before_reverse_frees_and_rejects_delayed_callback(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            self.assertEqual(b.call('ui_bg_register',STATE,1,240),1)
            self.assertNotEqual(b.get(0x021d110c),0)
            self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
            self.assertEqual(b.get(0x021d110c),0)
            self.assertEqual(b.bgdestroy(),1)
            self.assertEqual(b.call('ui_bg_publish',STATE,1,240),0)
            self.assertEqual(b.destroy(),1)
    def test_actual_rows_first_last_multi_dma_and_cpu_exact_destinations(self):
        for b in self.benches():
            for dma in (3,0xffffffff):
                if not b.get(TOKEN):b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
                b.put(0x02110c80,dma)
                if b.get(STATE+88)==2:b.call('ui_bg_begin',TOKEN,STATE,1,0)
                pixels=b.get(STATE+28)
                pattern=bytes((j*17+j//960)%256 for j in range(21120));b.u.mem_write(pixels,pattern)
                for row,count in ((0,1),(21,1),(5,3),(0,22)):
                    b.u.mem_write(0x02211000,struct.pack('<2I',row,count))
                    self.assertEqual(b.call('ui_bg_rows',TOKEN,STATE,1,0x02211000),1)
                    self.assertEqual(bytes(b.u.mem_read(0x06000020+960*row,960*count)),pattern[960*row:960*(row+count)])
    def test_native_frame_ring_matches_independent_geometry_and_exact_uploads(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            b.call('ui_bg_begin',TOKEN,STATE,1,0)
            tiles=bytes(j%251 for j in range(576));palette=bytes(range(32))
            b.u.mem_write(0x02212000,tiles);b.u.mem_write(0x02213000,palette)
            b.u.mem_write(0x02211000,struct.pack('<8I',3,2,25,20,0x02212000,576,0x02213000,32))
            self.assertEqual(b.call('ui_bg_frame',TOKEN,STATE,1,0x02211000),1)
            self.assertEqual(bytes(b.u.mem_read(0x06007b80,576)),tiles)
            self.assertEqual(bytes(b.u.mem_read(0x050001c0,32)),palette)
            values=struct.unpack('<1024H',b.u.mem_read(b.get(STATE+20),2048))
            self.assertEqual(values[33:39],(0xe3dc,0xe3dd,0xe3de,0xe3de,0xe3de,0xe3de))
            self.assertEqual(values[32*22+28:32*22+31],(0xe3eb,0xe3ec,0xe3ed))
            self.assertEqual(values[32*2+3],0xd021)
    def test_actual_fill_nibbles_without_pixel_overrun(self):
        for b in self.benches():
            b.create();b.bgcreate();b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000)
            b.call('ui_bg_begin',TOKEN,STATE,1,0)
            pixels=b.get(STATE+28)
            for color,byte in ((0,0),(1,0x11),(15,0xff)):
                self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,color),1)
                self.assertEqual(bytes(b.u.mem_read(pixels,21120)),bytes([byte])*21120)
            self.assertEqual(b.call('ui_bg_fill',TOKEN,STATE,1,16),0)
    def test_coherent_native_field_banks_admitted_but_mismatched_register_refused(self):
        for b in self.benches():
            b.u.mem_write(0x02211000,struct.pack('<10I',4,0,128,0,96,0,256,0,3,16))
            b.address(0x02022be9,0x02211000)
            b.put(0x04000000,0x80);b.put(0x04001000,0x10080)
            b.create();b.bgcreate();b.put(0x04000242,0x82,1)
            before=len(b.writes)
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),0)
            self.assertFalse(any(p>=0x04000000 for p,n,v in b.writes[before:]))
            b.put(0x04000242,0x81,1)
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
    def test_hidden_map_has_660_tiles_and_364_blanks(self):
        for b in self.benches():
            b.create();b.bgcreate();self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
            self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),STATE+36)
            values=struct.unpack('<1024H',b.u.mem_read(b.get(STATE+20),2048))
            self.assertEqual(sum(v==0 for v in values),364)
            self.assertEqual(values[33:63],tuple(range(0xd001,0xd01f)))
            self.assertEqual(values[705:735],tuple(range(0xd277,0xd295)))
    def test_actual_native_storage_and_descriptors_before_plane_enable(self):
        for b in self.benches():
            self.assertEqual(b.create(),1);self.assertEqual(b.bgcreate(),1)
            for address in (0x06000000,0x06010000):b.u.mem_write(address,b'Z'*64)
            self.assertEqual(b.call('ui_bg_enter',TOKEN,STATE,1,0x02210000),1)
            for address in (0x06000000,0x06010000):
                self.assertEqual(bytes(b.u.mem_read(address,32)),bytes(32))
                self.assertEqual(bytes(b.u.mem_read(address+32,32)),b'Z'*32)
            self.assertEqual(b.get(0x0400000a,2),0x1e01)
            self.assertEqual(b.get(0x0400000c,2),0x1f11)
            self.assertEqual(b.get(0x04000000)&0x1f00,0)
            self.assertEqual(b.get(0x04001000)&0x1f00,0)
            self.assertEqual(b.get(0x04001000)&0x1ff87,0x10000,'SUB normal graphics with blank backdrop')
if __name__=='__main__':
    import json
    records=[];original_init=NativeBgBench.__init__;original_address=NativeBgBench.address
    def record_init(self,*args):
        self.receipt={}
        original_init(self,*args)
        if args[0][0]==BgRomTests.compiled[0]:records.append(self.receipt)
    def record_address(self,*args):
        result=original_address(self,*args)
        if hasattr(self,'receipt'):
            names={address:name for name,address in self.symbols.items()};api={}
            for address,stack,instructions in self.metrics:
                key=names.get(address,f'{address:08x}')
                entry=api.setdefault(key,[0,0,0]);entry[0]+=1;entry[1]=max(entry[1],stack);entry[2]=max(entry[2],instructions)
            self.receipt.update(api=api,

                max_stack=max((stack for p,stack,n in self.metrics),default=0),
                max_instructions=max((n for p,stack,n in self.metrics),default=0),
                max_irq_masked=self.masked_max,max_publish_irq_masked=self.publish_masked_max,
                max_sample_to_plane_store=max(self.publish_intervals,default=0),
                highwater=self.highwater,peak_bg=self.peak_bg,
                native_counts={f'{p:08x} {NATIVE_STARTS[p]}':v for p,v in self.native_counts.items()},
                native_metrics=list(self.native_metrics),
                dma=list(getattr(self,'dma',())),cp15=len(getattr(self,'cp15',())),
                uploads=[(p,args[3] if p==0x0201c0c0 else 2048) for p,args,fifth in getattr(self,'services',()) if p in (0x0201c0c0,0x0201bf7c)])
        return result
    NativeBgBench.__init__=record_init;NativeBgBench.address=record_address
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(BgRomTests))
    if not result.wasSuccessful():raise SystemExit(1)
    totals={};api={}
    for record in records:
        for service,count in record['native_counts'].items():totals[service]=totals.get(service,0)+count
        for name,values in record['api'].items():
            entry=api.setdefault(name,[0,0,0]);entry[0]+=values[0];entry[1]=max(entry[1],values[1]);entry[2]=max(entry[2],values[2])
    summary={'native_prepared_benches':len(records),'native_instruction_entries':len(NATIVE_INSTRUCTIONS),
             'maxima':{key:max((r[key] for r in records),default=0) for key in ('max_stack','max_instructions','max_irq_masked','max_publish_irq_masked','max_sample_to_plane_store','highwater','peak_bg')},
             'api_calls_count_maxstack_maxinstructions':api,'native_service_counts':totals,'dma_transfers':sum(len(r['dma']) for r in records),
             'dma_bytes':sum(t[2] for r in records for t in r['dma']),
             'cp15_operations':sum(r['cp15'] for r in records),
             'char_upload_calls_bytes':(sum(p==0x0201c0c0 for r in records for p,n in r['uploads']),sum(n for r in records for p,n in r['uploads'] if p==0x0201c0c0)),
             'map_upload_calls_bytes':(sum(p==0x0201bf7c for r in records for p,n in r['uploads']),sum(n for r in records for p,n in r['uploads'] if p==0x0201bf7c))}
    print(json.dumps(summary,indent=2))
