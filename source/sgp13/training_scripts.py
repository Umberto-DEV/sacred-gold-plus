"""Native field-script service menus. Existing entry IDs and body bytes survive."""
import struct

class Script:
    def __init__(self, messages): self.data=bytearray();self.labels={};self.fix=[];self.messages=messages
    def emit(self,op,*args):
        self.data.extend(struct.pack('<H',op))
        for value,size in args:self.data.extend(int(value).to_bytes(size,'little'))
    def label(self,name):
        if name in self.labels:raise ValueError('duplicate label '+name)
        self.labels[name]=len(self.data)
    def set(self,var,value):self.emit(41,(var,2),(value,2))
    def copy(self,to,fr):self.emit(43,(to,2),(fr,2))
    def jump(self,label,condition=None):
        self.emit(22 if condition is None else 28,*([] if condition is None else [(condition,1)]))
        self.fix.append((len(self.data),label));self.data.extend(bytes(4))
    def eq(self,var,value,label):self.emit(17,(var,2),(value,2));self.jump(label,1)
    def msg(self,key,wait=False):
        self.emit(45,(self.messages[key],1))
        if wait:self.emit(50);self.emit(53)
    def buffer(self,index,var):self.emit(198,(index,1),(var,2))
    def call(self,op):self.set(0x8006,op);self.emit(490,(0xF13A,2))
    def menu(self,keys,var=0x800C,values=None):
        # The native touch grid supports at most seven choices. Longer digit
        # lists use the game's scrolling Move Tutor list on the upper screen.
        scrolling=len(keys)>7
        self.emit(69 if scrolling else 750,(1,1),(1,1),(0,1),(1,1),(var,2))
        for key,value in zip(keys,range(len(keys)) if values is None else values):
            self.emit(70 if scrolling else 751,(self.messages[key],2),(255,2),(255 if scrolling and value==65534 else value,2))
        self.emit(71 if scrolling else 752)
        if scrolling:self.eq(var,255,'main')
    def yes(self,cancel='main'):self.emit(63,(0x800C,2));self.eq(0x800C,1,cancel)
    def finish(self):
        for off,label in self.fix:
            if label not in self.labels:raise ValueError('undefined label '+label)
            struct.pack_into('<i',self.data,off,self.labels[label]-off-4)
        return bytes(self.data)

def append_script(member,script):
    """Add one ScrDef, shifting the opaque old body equally with its table."""
    n=0
    while n*4+2<=len(member) and member[n*4:n*4+2]!=b'\x13\xfd':n+=1
    end=n*4+2
    if end>len(member) or n>512:raise ValueError('invalid script entry table')
    offsets=[struct.unpack_from('<I',member,i*4)[0] for i in range(n)]
    if any(not end<=i*4+4+v<len(member) for i,v in enumerate(offsets)):raise ValueError('script target outside member')
    table=b''.join(struct.pack('<I',v+4) for v in offsets)
    result=table+struct.pack('<I',len(member)-4*n)+member[n*4:]+script
    if result[end+4:len(member)+4]!=member[end:]:raise ValueError('old script body changed')
    return result,n+1

def service_script(messages,kind="mart"):
    if kind not in ("mart","daycare"):raise ValueError("service kind")
    s=Script(messages)
    s.emit(96);s.emit(104);s.emit(746)
    s.label('main');s.msg('welcome_'+kind)
    choices=['iv','buy','claim','settings','info','leave'] if kind=='mart' else ['ev','courses','settings','info','leave']
    s.menu(choices)
    for i,label in enumerate(choices):s.eq(0x800C,i,'exit' if label=='leave' else label)
    s.jump('exit')
    s.label('info');s.msg('information_'+kind,True);s.jump('main')
    s.label('exit');s.call(10);s.emit(53);s.emit(747);s.emit(97);s.emit(2)
    s.label('result');s.eq(0x800B,0,'success');s.eq(0x800B,3,'noop');s.eq(0x800B,4,'payment');s.eq(0x800B,7,'busy');s.eq(0x800B,8,'storage');s.msg('invalid',True);s.jump('main')
    for label,key in [('success','done'),('noop','unchanged'),('payment','cannot_pay'),('busy','blocked'),('storage','storage_blocked')]:s.label(label);s.msg(key,True);s.jump('main')
    s.label('settings');s.msg('settings_prompt')
    choices=['legacy','back'] if kind=='mart' else ['classic','unlimited','legacy','rtc','play','back']
    s.menu(choices)
    for i,label in enumerate(choices):s.eq(0x800C,i,'main' if label=='back' else label)
    s.jump('main')
    for label,mode in [('classic',1),('unlimited',2),('legacy',0)]:
        s.label(label);s.msg('warning_'+label);s.yes();s.set(0x8008,mode);s.call(1);s.jump('result')
    for label,mode in [('rtc',1),('play',0)]:
        s.label(label);s.msg('clock_'+label);s.yes();s.set(0x8008,mode);s.call(7);s.jump('result')
    s.label('claim');s.call(6);s.jump('result')
    s.label('buy');s.msg('buy_prompt');s.menu(['silver_price','gold_price','back']);s.eq(0x800C,0,'buy_silver');s.eq(0x800C,1,'buy_gold');s.jump('main')
    for label,gold in [('buy_silver',0),('buy_gold',1)]:
        s.label(label);s.set(0x8008,gold);s.msg('confirm_'+('gold' if gold else 'silver'));s.yes();s.call(5);s.jump('result')
    for label in ('iv','ev'):
        s.label(label);s.emit(53);s.emit(747)
        s.emit(174,(6,2),(1,2),(0,2),(0,2));s.emit(175)
        s.emit(349);s.emit(351,(0x8007,2));s.emit(150)
        s.emit(174,(6,2),(1,2),(1,2),(0,2));s.emit(175);s.emit(746);s.eq(0x8007,255,'main')
        s.set(0x800A,0 if label=='iv' else 1);s.call(11);s.eq(0x800B,0,label+'_choose');s.jump('result')
        s.label(label+'_choose')
        for i,stat in enumerate((0,1,2,4,5,3)):s.buffer(i,0x8000+stat)
        s.msg('current_'+label,True)
        if label=='iv':
            s.msg('iv_prompt');s.menu(['silver','gold','exact','back']);s.eq(0x800C,0,'silver');s.eq(0x800C,1,'gold');s.eq(0x800C,2,'exact');s.jump('main')
        else:
            s.msg('ev_prompt');s.menu(['choose_stat','reset','back']);s.eq(0x800C,0,'ev_stat');s.eq(0x800C,1,'ev_reset');s.jump('main')
    s.label('gold');s.set(0x800A,2);s.set(0x8008,0);s.set(0x8009,31);s.jump('iv_preview')
    s.label('silver');s.set(0x800A,1);s.jump('iv_stat')
    s.label('exact');s.set(0x800A,0)
    s.label('iv_stat');s.msg('stat_prompt');s.menu(['hp','attack','defense','spattack','spdefense','speed','back'],0x8008,[0,1,2,4,5,3,255]);s.eq(0x8008,255,'main');s.eq(0x8008,65534,'main');s.eq(0x800A,0,'iv_number');s.set(0x8009,31);s.jump('iv_preview')
    s.label('iv_number');s.msg('number_prompt');s.menu(['n0','n10','n20','n30','back'],0x8009,[0,10,20,30,255]);s.eq(0x8009,255,'main');s.eq(0x8009,65534,'main');s.eq(0x8009,30,'iv_units30');s.menu(['n'+str(i) for i in range(10)]+['back'],0x800C,list(range(10))+[255]);s.jump('iv_units_add')
    s.label('iv_units30');s.menu(['n0','n1','back'],0x800C,[0,1,255])
    s.label('iv_units_add');s.eq(0x800C,255,'main');s.eq(0x800C,65534,'main');s.emit(39,(0x8009,2),(0x800C,2))
    s.label('iv_preview');s.call(2);s.eq(0x800B,0,'iv_confirm');s.jump('result')
    s.label('iv_confirm')
    for i,stat in enumerate((0,1,2,4,5,3)):s.buffer(i,0x8000+stat)
    s.msg('target_iv');s.yes();s.call(4);s.jump('result')
    s.label('ev_reset');s.set(0x8008,255);s.set(0x8009,0);s.jump('ev_preview')
    s.label('ev_stat');s.msg('stat_prompt');s.menu(['hp','attack','defense','spattack','spdefense','speed','back'],0x8008,[0,1,2,4,5,3,255]);s.eq(0x8008,255,'main');s.eq(0x8008,65534,'main')
    s.label('ev_number');s.msg('ev_number');s.menu(['n0','n100','n200','back'],0x8009,[0,100,200,65534]);s.eq(0x8009,65534,'main')
    for digit,values in [('tens',list(range(0,100,10))),('units',list(range(10)))]:
        s.menu(['n'+str(i) for i in values]+['back'],0x800C,values+[65534]);s.eq(0x800C,65534,'main');s.emit(39,(0x8009,2),(0x800C,2))
    s.label('ev_preview');s.call(3);s.eq(0x800B,0,'ev_confirm');s.jump('result')
    s.label('ev_confirm')
    for i,stat in enumerate((0,1,2,4,5,3)):s.buffer(i,0x8000+stat)
    s.buffer(6,0x800C);s.msg('target_ev');s.yes();s.call(4);s.jump('result')
    s.label('courses');s.msg('courses_prompt');s.menu(['enroll','status','back']);s.eq(0x800C,0,'enroll');s.eq(0x800C,1,'status');s.jump('main')
    for label in ('enroll','status'):
        s.label(label);s.msg('slot_prompt');s.menu(['slot1','slot2','back'],0x8007,[0,1,255]);s.eq(0x8007,255,'main');s.eq(0x8007,65534,'main')
        if label=='status':
            s.call(9);s.eq(0x800B,0,'course_show');s.jump('result')
        else:
            s.msg('course_kind');s.menu(['level_only','level_ev','back']);s.eq(0x800C,0,'enroll_level');s.eq(0x800C,1,'enroll_ev');s.jump('main')
    s.label('enroll_level');s.set(0x8008,255);s.set(0x8009,0);s.jump('enroll_confirm')
    s.label('enroll_ev');s.msg('stat_prompt');s.menu(['hp','attack','defense','spattack','spdefense','speed','back'],0x8008,[0,1,2,4,5,3,255]);s.eq(0x8008,255,'main');s.eq(0x8008,65534,'main')
    s.msg('ev_number');s.menu(['n0','n100','n200','back'],0x8009,[0,100,200,65534]);s.eq(0x8009,65534,'main')
    for values in (list(range(0,100,10)),list(range(10))):
        s.menu(['n'+str(i) for i in values]+['back'],0x800C,values+[65534]);s.eq(0x800C,65534,'main');s.emit(39,(0x8009,2),(0x800C,2))
    s.buffer(0,0x8009);s.msg('course_target');s.yes()
    s.label('enroll_confirm');s.call(0);s.eq(0x8001,0,'enroll_play');s.msg('enroll_rtc');s.jump('enroll_yes')
    s.label('enroll_play');s.msg('enroll_play')
    s.label('enroll_yes');s.yes();s.call(8);s.jump('result')
    s.label('course_show');s.buffer(0,0x8000);s.buffer(2,0x8002);s.buffer(3,0x8003);s.buffer(4,0x800C);s.eq(0x8001,255,'course_level');s.emit(658,(1,1),(0x8001,2));s.eq(0x8004,0,'course_ev_play');s.msg('course_ev_rtc',True);s.jump('main')
    s.label('course_ev_play');s.msg('course_ev_play',True);s.jump('main')
    s.label('course_level');s.eq(0x8004,0,'course_level_play');s.msg('course_level_rtc',True);s.jump('main')
    s.label('course_level_play');s.msg('course_level_play',True);s.jump('main')
    return s.finish()
