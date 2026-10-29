"""Host tests call the exact freestanding C consumed by the native builder."""
import ctypes as C
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
U8, U16, U32, U64 = C.c_uint8, C.c_uint16, C.c_uint32, C.c_uint64
A6, A256 = U8 * 6, U8 * 256
OK, INVALID, EGG, NO_CHANGE, PAYMENT, OVERFLOW, IDENTITY, BUSY = range(8)

class Core(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        lib = pathlib.Path(cls.tmp.name) / 'training.so'
        subprocess.run(['clang', '-shared', '-fPIC', '-std=c99', '-Wall', '-Wextra',
                        '-Werror', '-O2', *map(str, sorted((ROOT/'sorgenti').glob('*.c'))),
                        '-o', str(lib)], check=True, capture_output=True)
        cls.c = C.CDLL(str(lib))
        cls.c.sgp_train_ev_delta.argtypes = [C.POINTER(U8), U8, U8, C.c_int32, U8, C.POINTER(U8)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def iv(self, before, kind=0, stat=0, value=31, egg=0, valid=1):
        after, cost = A6(*([99]*6)), U8(99)
        result = self.c.sgp_train_iv_preview(A6(*before), kind, stat, value, egg, valid, after, C.byref(cost))
        return result, list(after), cost.value

    def test_exact_iv_and_silver_gold_cost_only_on_change(self):
        self.assertEqual(self.iv([31]*6, value=0), (OK, [0,31,31,31,31,31], 1))
        self.assertEqual(self.iv([0]*6, kind=1, stat=3), (OK, [0,0,0,31,0,0], 1))
        self.assertEqual(self.iv([1]*6, kind=2), (OK, [31]*6, 1))
        self.assertEqual(self.iv([31]*6, kind=2), (NO_CHANGE, [99]*6, 99))

    def test_iv_invalid_egg_and_bad_data_are_unchanged(self):
        for args, status in [({'egg':1}, EGG), ({'valid':0}, INVALID),
                             ({'value':32}, INVALID), ({'stat':6}, INVALID),
                             ({'kind':3}, INVALID), ({'egg':2}, INVALID)]:
            self.assertEqual(self.iv([0]*6, **args), (status, [99]*6, 99))
        self.assertEqual(self.iv([32,0,0,0,0,0]), (INVALID,[99]*6,99))

    def test_payment_rejects_insufficient_without_mutating(self):
        out = U16(123)
        self.assertEqual(self.c.sgp_train_payment(0,1,C.byref(out)), PAYMENT)
        self.assertEqual(out.value,123)
        self.assertEqual(self.c.sgp_train_payment(999,1,C.byref(out)), OK)
        self.assertEqual(out.value,998)
        self.assertEqual(self.c.sgp_train_payment(0,0,C.byref(out)), OK)
        self.assertEqual(out.value,0)

    def delta(self, before, policy, stat, delta, vitamin=0):
        after=A6(*([99]*6))
        result=self.c.sgp_train_ev_delta(A6(*before),policy,stat,delta,vitamin,after)
        return result,list(after)

    def test_positive_ev_caps_depend_on_policy_and_source(self):
        for before, policy, delta, vitamin, want in [
            ([99,0,0,0,0,0],0,10,1,[100,0,0,0,0,0]),
            ([250,0,0,0,0,0],0,10,0,[255,0,0,0,0,0]),
            ([250,0,0,0,0,0],1,10,1,[252,0,0,0,0,0]),
            ([250,252,6,0,0,0],1,10,0,[252,252,6,0,0,0]),
            ([250,252,252,252,252,252],2,2147483647,0,[252]*6)]:
            self.assertEqual(self.delta(before,policy,0,delta,vitamin),(OK,want))

    def test_negative_ev_does_not_normalize_other_stats_or_underflow(self):
        self.assertEqual(self.delta([252]*6,1,0,-10),(OK,[242,252,252,252,252,252]))
        self.assertEqual(self.delta([255]*6,0,4,-2147483648),(OK,[255,255,255,255,0,255]))
        self.assertEqual(self.delta([255]*6,2,0,1),(NO_CHANGE,[99]*6))
        self.assertEqual(self.delta([0]*6,1,0,-1),(NO_CHANGE,[99]*6))

    def test_ev_rejects_bad_selectors(self):
        for policy,stat,vitamin in [(3,0,0),(1,6,0),(1,0,2)]:
            self.assertEqual(self.delta([0]*6,policy,stat,1,vitamin),(INVALID,[99]*6))

    def test_allocation_is_all_or_nothing_and_mode_switch_preserves_excess(self):
        out=A6(*([99]*6))
        self.assertEqual(self.c.sgp_train_ev_allocate(A6(252,252,7,0,0,0),1,out),INVALID)
        self.assertEqual(list(out),[99]*6)
        self.assertEqual(self.c.sgp_train_ev_allocate(A6(*([252]*6)),2,out),OK)
        self.assertEqual(list(out),[252]*6)
        self.assertEqual(self.c.sgp_train_ev_allocate(A6(253,0,0,0,0,0),0,out),INVALID)
        for evs,policy,want in [([255,255,0,0,0,0],0,1),([255,0,0,0,0,0],1,0),
                               ([252]*6,1,0),([252]*6,2,1),([252,252,6,0,0,0],1,1)]:
            self.assertEqual(self.c.sgp_train_mode_fits(A6(*evs),policy),want)

    def test_ui_order_maps_speed_last(self):
        self.assertEqual([self.c.sgp_train_stat_from_ui(i) for i in range(7)],[0,1,2,4,5,3,255])


class Job(C.Structure):
    _fields_ = [('serial',U32),('personality',U32),('ot',U32),('species',U16),
                ('active',U8),('clock',U8),('kinds',U8),('start_level',U8),
                ('target_level',U8),('stat',U8),('baseline_exp',U32),
                ('steps_at_enrollment',U32),('level_quanta_settled',U32),
                ('anchor',U64),('credited',U64),('baseline_evs',A6),('target_evs',A6),
                ('ev_period',U32),('ev_points',U16),('reserved16',U16),
                ('ev_quanta_settled',U32),('reserved0',U32),('reserved1',U32)]

class Projection(C.Structure):
    _fields_ = [('level',U8),('evs',A6),('remaining_seconds',U32)]

def job(kinds=3):
    j=Job(serial=7,personality=0x12345678,ot=0x98765432,species=25,active=1,
          clock=1,kinds=kinds,start_level=50,target_level=52,stat=0,
          baseline_exp=125123,steps_at_enrollment=654,anchor=1000,
          ev_period=3600,ev_points=32)
    j.target_evs=A6(100,0,0,0,0,0)
    if not kinds & 2:
        j.stat=255
        j.ev_period=j.ev_points=0
        j.target_evs=A6()
    if not kinds & 1:
        j.target_level=j.start_level
    return j

class Courses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Core.setUpClass.__func__(cls)
        cls.c.sgp_train_advance.argtypes=[C.POINTER(Job),U8,U64]
        cls.c.sgp_train_switch_clock.argtypes=[C.POINTER(Job),U8,U64,U8,U64]
        cls.c.sgp_train_identity.argtypes=[C.POINTER(Job),U32,U32,U32,U16]
    tearDownClass=classmethod(Core.tearDownClass.__func__)

    def project(self,j,policy=1):
        p=Projection(level=222,remaining_seconds=999)
        result=self.c.sgp_train_project(C.byref(j),policy,C.byref(p))
        return result,p.level,list(p.evs),p.remaining_seconds

    def test_projection_rates_target_saturation_and_read_only(self):
        j=job()
        j.credited=7200
        before=bytes(j)
        self.assertEqual(self.project(j),(OK,51,[64,0,0,0,0,0],7200))
        self.assertEqual(bytes(j),before)
        j.credited=14400
        self.assertEqual(self.project(j),(OK,52,[100,0,0,0,0,0],0))

    def test_advance_large_jump_saturates_without_unsigned_overflow(self):
        j=job()
        self.assertEqual(self.c.sgp_train_advance(C.byref(j),1,2**64-1),OK)
        self.assertEqual(j.credited,14400)
        self.assertEqual(j.anchor,2**64-1)
        self.assertEqual(self.project(j)[1:],(52,[100,0,0,0,0,0],0))

    def test_backwards_clock_awards_zero_and_reanchors(self):
        j=job()
        j.credited=3599
        self.assertEqual(self.c.sgp_train_advance(C.byref(j),1,100),OK)
        self.assertEqual((j.anchor,j.credited),(100,3599))
        self.assertEqual(self.c.sgp_train_advance(C.byref(j),1,101),OK)
        self.assertEqual(j.credited,3600)
        self.assertEqual(self.c.sgp_train_advance(C.byref(j),1,101),OK)
        self.assertEqual(j.credited,3600)

    def test_clock_switch_retains_fraction_and_settles_old_source(self):
        j=job()
        j.credited=3500
        self.assertEqual(self.c.sgp_train_switch_clock(C.byref(j),1,1050,0,9876543210),OK)
        self.assertEqual((j.clock,j.anchor,j.credited),(0,9876543210,3550))
        self.assertEqual(self.c.sgp_train_advance(C.byref(j),1,9876543260),OK)
        self.assertEqual(self.project(j)[2],[32,0,0,0,0,0])

    def test_invalid_jobs_do_not_mutate_or_project(self):
        for attr,value in [('clock',2),('kinds',4),('species',0),('species',494),
                           ('serial',0),('start_level',0),('target_level',101),
                           ('stat',6),('ev_period',0),('ev_points',0),
                           ('credited',14401),('level_quanta_settled',1),
                           ('ev_quanta_settled',1),('reserved16',1),('reserved0',1)]:
            j=job()
            setattr(j,attr,value)
            before=bytes(j)
            self.assertEqual(self.c.sgp_train_advance(C.byref(j),1,2000),INVALID,attr)
            self.assertEqual(bytes(j),before)
            self.assertEqual(self.project(j)[0],INVALID,attr)

    def test_level_only_preserves_legacy_evs_and_level100(self):
        j=job(1)
        j.baseline_evs=A6(*([255]*6))
        j.start_level=99
        j.target_level=100
        j.credited=7200
        self.assertEqual(self.project(j),(OK,100,[255]*6,0))

    def test_ev_target_must_change_only_selected_stat_and_fit_policy(self):
        j=job(2)
        j.target_evs=A6(252,252,7,0,0,0)
        self.assertEqual(self.project(j)[0],INVALID)
        j.baseline_evs=A6(0,252,7,0,0,0)
        self.assertEqual(self.project(j)[0],INVALID)
        self.assertEqual(self.project(j,2)[0],OK)
        j.target_evs[0]=253
        self.assertEqual(self.project(j,2)[0],INVALID)

    def test_identity_includes_ot_species_and_deposit_serial(self):
        j=job()
        good=(7,0x12345678,0x98765432,25)
        self.assertEqual(self.c.sgp_train_identity(C.byref(j),*good),1)
        for i in range(4):
            bad=list(good)
            bad[i]+=1
            self.assertEqual(self.c.sgp_train_identity(C.byref(j),*bad),0)

    def test_withdraw_compacts_two_jobs_and_rejects_stale_identity(self):
        jobs=(Job*2)(job(),job())
        jobs[1].serial=8
        jobs[1].credited=7200
        stale=job()
        stale.ot+=1
        before=bytes(jobs)
        self.assertEqual(self.c.sgp_train_withdraw(jobs,1,0,C.byref(stale)),IDENTITY)
        self.assertEqual(bytes(jobs),before)
        expected=job()
        self.assertEqual(self.c.sgp_train_withdraw(jobs,1,0,C.byref(expected)),OK)
        self.assertEqual((jobs[0].serial,jobs[0].credited),(8,7200))
        self.assertEqual(bytes(jobs[1]),bytes(Job()))

    def test_withdraw_unenrolled_first_slot_moves_enrolled_second_slot(self):
        jobs=(Job*2)(Job(),job())
        expected=Job()
        self.assertEqual(self.c.sgp_train_withdraw(jobs,1,0,C.byref(expected)),OK)
        self.assertEqual(jobs[0].serial,7)
        self.assertEqual(bytes(jobs[1]),bytes(Job()))

import struct
import zlib

class State(C.Structure):
    _fields_ = [('generation',U32),('main_crc',U16),('flags',U16),('policy',U8),
                ('default_clock',U8),('initialization_version',U8),('reserved',U8),
                ('next_serial',U32),('played',U64),('last_rtc',U64),
                ('claims',U32),('league_seen',U32),('pending_silver',U16),
                ('pending_gold',U16),('jobs',Job*2),
                ('shiny_rng',U32),('shiny_target',U16),('shiny_chain',U8),
                ('shiny_mode',U8),('shiny_initialized',U8),('shiny_reserved',U8*7)]

def record(generation=42, main_crc=0x1234):
    """Independent byte fixture, without production encoder assistance."""
    b=bytearray(256)
    struct.pack_into('<IHHIHHBBBBIQQIIHH',b,0,0x31524e54,1,256,generation,main_crc,
                     0,0,1,1,0,1,0,0,0,0,0,0)
    return crc(b)

def crc(b):
    b=bytearray(b)
    struct.pack_into('<I',b,252,zlib.crc32(b[:252]))
    return bytes(b)

def record_v2(generation=42, main_crc=0x1234, *, rng=0, target=0, chain=0, mode=0, initialized=0):
    b=bytearray(record(generation,main_crc)); b[4]=2
    struct.pack_into('<IHBBB',b,224,rng,target,chain,mode,initialized)
    return crc(b)

ERASED,VALID,CORRUPT,FOREIGN,MISMATCH=range(5)

class Journal(unittest.TestCase):
    setUpClass=classmethod(Core.setUpClass.__func__)
    tearDownClass=classmethod(Core.tearDownClass.__func__)

    def decode(self,b,generation=42,main_crc=0x1234):
        out=State(generation=999)
        result=self.c.sgp_train_decode(A256.from_buffer_copy(b),generation,main_crc,C.byref(out))
        return result,out

    def state(self):
        s=State()
        self.c.sgp_train_defaults(C.byref(s))
        s.generation=42
        s.main_crc=0x1234
        return s

    def test_defaults_and_independent_golden_record(self):
        s=self.state()
        self.assertEqual((s.policy,s.default_clock,s.next_serial),(0,1,1))
        out=A256()
        self.assertEqual(self.c.sgp_train_encode(C.byref(s),out),OK)
        self.assertEqual(bytes(out),record_v2())
        result,d=self.decode(record())
        self.assertEqual(result,VALID)
        self.assertEqual((d.generation,d.main_crc,d.default_clock),(42,0x1234,1))

    def test_version1_migrates_without_changing_jobs_or_training_state(self):
        original=bytearray(record())
        struct.pack_into('<II', original,40,0x12345,9)
        struct.pack_into('<HH', original,48,12,4)
        original=crc(original)
        status,s=self.decode(original)
        self.assertEqual(status,VALID)
        self.assertEqual((s.shiny_rng,s.shiny_target,s.shiny_chain,s.shiny_mode,s.shiny_initialized),(0,0,0,0,0))
        output=A256(); self.assertEqual(self.c.sgp_train_encode(C.byref(s),output),OK)
        self.assertEqual(bytes(output)[8:224],original[8:224])
        self.assertEqual(bytes(output)[4:8],b'\x02\0\0\x01')
        self.assertEqual(bytes(output)[224:252],bytes(28))

    def test_version2_preserves_shiny_progress_and_rejects_noncanonical_state(self):
        raw=record_v2(rng=0x12345678,target=132,chain=40,mode=1,initialized=1)
        status,s=self.decode(raw); self.assertEqual(status,VALID)
        self.assertEqual((s.shiny_rng,s.shiny_target,s.shiny_chain,s.shiny_mode,s.shiny_initialized),
                         (0x12345678,132,40,1,1))
        output=A256(); self.assertEqual(self.c.sgp_train_encode(C.byref(s),output),OK)
        self.assertEqual(bytes(output),raw)
        for offset,value in [(229,2),(230,41),(231,2),(232,2),*[(i,1) for i in range(233,252)]]:
            changed=bytearray(raw); changed[offset]=value
            self.assertEqual(self.decode(crc(changed))[0],CORRUPT,(offset,value))
        for kwargs in [dict(rng=1),dict(target=0,chain=1,mode=1),dict(target=19,chain=1,mode=0)]:
            self.assertEqual(self.decode(record_v2(**kwargs))[0],CORRUPT,kwargs)

    def test_version2_torn_sibling_never_overwrites_valid_version1(self):
        new=bytearray(record_v2(target=19,chain=10,mode=1)); new[230]=20
        status,s,source,writable=self.select(record(),new)
        self.assertEqual((status,source,writable,s.shiny_chain),(VALID,0,0,0))

    def test_v2_shiny_only_flag_preserves_unactivated_training_and_v1_rejects_it(self):
        raw=bytearray(record_v2(target=19,chain=10,mode=1)); raw[14]=1
        status,s=self.decode(crc(raw)); self.assertEqual(status,VALID)
        self.assertEqual((s.flags,s.shiny_target,s.shiny_chain),(1,19,10))
        before=bytes(s)
        self.assertEqual(self.c.sgp_train_queue_reward(C.byref(s),0,2,0,0),INVALID)
        self.assertEqual(bytes(s),before)
        for offset in (16,40,44,48,50):
            bad=bytearray(raw);bad[offset]=1
            self.assertEqual(self.decode(crc(bad))[0],CORRUPT,offset)
        raw[4]=1
        self.assertEqual(self.decode(crc(raw))[0],CORRUPT)

    def test_erased_requires_uniform_zero_or_ff(self):
        for fill in [0,255]:
            status,out=self.decode(bytes([fill])*256)
            self.assertEqual((status,out.generation),(ERASED,999))
        mixed=bytes(128)+bytes([255])*128
        self.assertEqual(self.decode(mixed)[0],FOREIGN)

    def test_every_single_byte_corruption_is_rejected(self):
        golden=record()
        for i in range(256):
            b=bytearray(golden)
            b[i]^=1
            status,out=self.decode(b)
            self.assertIn(status,[CORRUPT,FOREIGN],i)
            self.assertEqual(out.generation,999)

    def test_valid_crc_cannot_hide_reserved_ranges_or_bad_enums(self):
        for index,value in [(14,1),(16,3),(17,2),(18,0),(19,1),(20,0),
                            (42,4),(49,4),(51,4),
                            *[(i,1) for i in range(52,64)],
                            *[(i,1) for i in range(224,252)],(64,1)]:
            b=bytearray(record())
            b[index]=value
            self.assertEqual(self.decode(crc(b))[0],CORRUPT,(index,value))

    def test_job_roundtrip_offsets_and_semantic_validation(self):
        s=self.state()
        s.policy=1
        s.next_serial=8
        s.jobs[0]=job()
        s.jobs[0].credited=7200
        s.played=2**40+3
        out=A256()
        self.assertEqual(self.c.sgp_train_encode(C.byref(s),out),OK)
        b=bytes(out)
        self.assertEqual(struct.unpack_from('<IIIHBBBBBBIIIQQ',b,64),
                         (7,0x12345678,0x98765432,25,1,1,3,50,52,0,125123,654,0,1000,7200))
        self.assertEqual(b[112:124],bytes([0]*6+[100,0,0,0,0,0]))
        self.assertEqual(struct.unpack_from('<IH',b,124),(3600,32))
        status,d=self.decode(b)
        self.assertEqual(status,VALID)
        self.assertEqual(bytes(d.jobs[0]),bytes(s.jobs[0]))
        self.assertEqual(d.played,2**40+3)
        for offset,value in [(78,0),(79,2),(80,4),(130,1),(132,1),(136,1),(140,1)]:
            changed=bytearray(b)
            changed[offset]=value
            self.assertEqual(self.decode(crc(changed))[0],CORRUPT,offset)

    def test_job_duplicate_serial_and_serial_reuse_rejected(self):
        s=self.state()
        s.next_serial=8
        s.jobs[0]=job()
        s.jobs[1]=job()
        out=A256(*([123]*256))
        self.assertEqual(self.c.sgp_train_encode(C.byref(s),out),INVALID)
        self.assertEqual(bytes(out),bytes([123])*256)
        s.jobs[1]=Job()
        s.next_serial=7
        self.assertEqual(self.c.sgp_train_encode(C.byref(s),out),INVALID)

    def test_generation_and_crc_must_both_match_native_save(self):
        for generation,main_crc in [(41,0x1234),(42,0x1235)]:
            status,out=self.decode(record(),generation,main_crc)
            self.assertEqual((status,out.generation),(MISMATCH,999))

    def select(self,a,b,generation=42):
        state=State(generation=999)
        source,writable=U8(88),U8(88)
        status=self.c.sgp_train_select(A256.from_buffer_copy(a),A256.from_buffer_copy(b),
                                      generation,0x1234,C.byref(state),C.byref(source),C.byref(writable))
        return status,state,source.value,writable.value

    def test_power_loss_selects_only_matching_generation(self):
        old,new=record(41),record(42)
        r,s,source,w=self.select(new,old)
        self.assertEqual((r,s.generation,source,w),(VALID,42,0,1))
        r,s,source,w=self.select(new,old,41)
        self.assertEqual((r,s.generation,source,w),(VALID,41,1,1))
        r,s,source,w=self.select(old,old)
        self.assertEqual((r,s.generation,source,w),(MISMATCH,999,255,1))
        corrupt=bytearray(new)
        corrupt[100]^=1
        r,s,source,w=self.select(corrupt,new)
        self.assertEqual((r,s.generation,source,w),(VALID,42,1,0))

    def test_newer_or_foreign_record_is_never_writable(self):
        for offset,value in [(0,0),(4,3),(6,1)]:
            b=bytearray(record())
            b[offset]=value
            newer=crc(b)
            self.assertEqual(self.decode(newer)[0],FOREIGN)
            r,s,source,w=self.select(record(),newer)
            self.assertEqual((r,source,w),(VALID,0,0))
            r,s,source,w=self.select(newer,bytes(256))
            self.assertEqual((r,s.generation,source,w),(FOREIGN,999,255,0))

    def test_missing_defaults_do_not_borrow_a_stale_record(self):
        r,s,source,w=self.select(bytes(256),bytes([255])*256)
        self.assertEqual((r,s.policy,s.default_clock,s.next_serial,source,w),(ERASED,0,1,1,255,1))
        r,s,source,w=self.select(record(41),bytes(256))
        self.assertEqual((r,s.generation,source,w),(MISMATCH,999,255,1))

    def test_claims_queue_atomically_with_no_overflow_or_repeat_claim(self):
        s=self.state()
        s.pending_silver=998
        before=bytes(s)
        self.assertEqual(self.c.sgp_train_queue_reward(C.byref(s),0,2,1,0),OVERFLOW)
        self.assertEqual(bytes(s),before)
        self.assertEqual(self.c.sgp_train_queue_reward(C.byref(s),0,1,1,0),OK)
        self.assertEqual((s.pending_silver,s.pending_gold,s.claims),(999,1,1))
        before=bytes(s)
        self.assertEqual(self.c.sgp_train_queue_reward(C.byref(s),0,1,1,0),NO_CHANGE)
        self.assertEqual(bytes(s),before)
        out=A256()
        self.assertEqual(self.c.sgp_train_encode(C.byref(s),out),OK)
        self.assertEqual(struct.unpack_from('<IIHH',bytes(out),40),(1,0,999,1))

    def test_league_replay_and_delivery_cannot_destroy_pending_rewards(self):
        s=self.state()
        self.assertEqual(self.c.sgp_train_queue_reward(C.byref(s),16,4,2,1),OK)
        self.assertEqual(self.c.sgp_train_queue_reward(C.byref(s),255,4,1,1),NO_CHANGE)
        self.assertEqual(self.c.sgp_train_queue_reward(C.byref(s),255,4,1,2),OK)
        self.assertEqual((s.pending_silver,s.pending_gold,s.league_seen),(8,3,2))
        before=bytes(s)
        self.assertEqual(self.c.sgp_train_reward_delivered(C.byref(s),9,0),PAYMENT)
        self.assertEqual(bytes(s),before)
        self.assertEqual(self.c.sgp_train_reward_delivered(C.byref(s),8,3),OK)
        self.assertEqual((s.pending_silver,s.pending_gold,s.claims),(0,0,1<<16))

if __name__ == '__main__':
    unittest.main()
