"""Exhaustive raw candidate supplement to source/compiled closure, not a graph proof."""
import struct
def inventory(image):
    """Exhaustive candidate-edge supplement, not a caller graph proof on its own."""
    rows=[]
    targets=((0x023D4000,0x023D6000,'old-code'),)
    owners=[('arm9:'+hex(a),a,image.raw[o:o+n]) for a,o,n in image.mapped]
    owners += [('overlay:'+str(i),r[1],image.overlay(i)) for i,r in enumerate(image.records)]
    for owner,base,raw in owners:
        words=struct.unpack('<%dH'%(len(raw)//2),raw[:len(raw)//2*2])
        for i,a in enumerate(words[:-1]):
            site=base+2*i
            if owner.startswith('arm9:') and 0x023D4000<=site<0x023D6000:continue
            b=words[i+1]
            candidates=[]
            value=a|(b<<16)
            candidates.append(('literal',value))
            if a&0xf800==0xf000 and b&0xf800 in (0xf800,0xe800):
                d=((a&2047)<<12)|((b&2047)<<1)
                if d&0x400000:d-=0x800000
                candidates.append(('thumb-branch',site+4+d))
            if site%4==0 and value&0x0e000000==0x0a000000:
                d=(value&0xffffff)<<2
                if d&0x2000000:d-=0x4000000
                candidates.append(('arm-branch',site+8+d))
            for kind,target in candidates:
                for lo,hi,label in targets:
                    if lo<=target&~1<hi:rows.append(dict(owner=owner,site=hex(site),kind=kind,target=hex(target),domain=label))
    return rows
