"""Private cartridge regression for the real Options launch/teardown path."""
from test_native_search import SearchTests, ROOT, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_HOOK_CODE
from sgp12.rom import Arm9, bl_thumb


class NativeOptionsTests(SearchTests):
    def test_actual_options_launch_captures_before_native_field_shutdown(self):
        # Execute the real Options allocator/caller, tailcall and field shutdown.
        # Heap, overlay-manager allocation and encounter services remain seams.
        from sgp12.rom import Arm9, bl_thumb
        paths=[ROOT.parent/'local/roms/1.2.5'/f'sgp-1.2.5-{lang}.nds' for lang in ('EN','IT')]
        if not all(p.exists() for p in paths):
            self.skipTest('private original EN/IT cartridges required')
        for path in paths:
            with self.subTest(language=path.stem):
                arm=Arm9(path)
                for address,length in ((0x0203EE14,64),(0x0203DFB4,42),(0x0203DF34,8),(0x0203E344,4)):
                    self.u.mem_write(address,arm.leggi(address,length))
                name=self.module.HOOKS['arm9'].get(0x0203EE4A)
                if name:self.u.mem_write(0x0203EE4A,bl_thumb(0x0203EE4A,self.sym[name]))
                self.sym['native_options_launch']=0x0203EE25
                self.put(self.fs+0x6C,1);self.put(0x022C7004,0)
                self.put(0x023CB200+32,293)  # stale cache from the previous map
                self.put(0x022C7100,47)
                events=[]
                def native_services(u,a,size,_):
                    if a==0x0201AACC:
                        self.assertEqual((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)),(11,12))
                        self.ret(0x022CD000)
                    elif a==0x0200724C:
                        self.assertEqual((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1),u.reg_read(UC_ARM_REG_R2)),(0x020FA354,0x022CD000,11))
                        events.append((self.get(self.fs+0x6C),self.get(0x023CB200+32)))
                        self.ret(0x022CE000)
                handle=self.u.hook_add(UC_HOOK_CODE,native_services)
                self.native_options_path=True
                try:self.assertEqual(self.call('native_options_launch',self.fs),0x022CD000)
                finally:self.native_options_path=False;self.u.hook_del(handle)
                self.assertEqual(events,[(0,47)])
                self.assertEqual(self.get(0x022C7004),0x022CE000)
                self.assertEqual(self.get(0x022CD004),self.options)
                self.assertEqual(self.get(0x022CD008),self.fs+0x10C)
                self.assertEqual(self.snapshot()[1][24],1)
                self.assertEqual(self.call('sgp_shiny_candidate',self.app,self.out,0,0),25)


def load_tests(loader, tests, pattern):
    # Reuse the encounter-service bench without counting inherited regressions
    # again or classifying this actual-cartridge case as ROM-free coverage.
    import unittest
    return unittest.TestSuite([NativeOptionsTests(
        'test_actual_options_launch_captures_before_native_field_shutdown')])
