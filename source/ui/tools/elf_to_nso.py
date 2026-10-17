"""ELF64 AArch64 -> uncompressed NSO0 with SHA256 for all three segments.

Layout follows switchbrew/switch-tools src/elf2nso.c. Compression is optional
in NSO; keeping segments raw avoids compressed-data editing and LZ4 ambiguity.
"""
import hashlib
import struct
from pathlib import Path

class Elf:
    def __init__(self, raw):
        self.raw=raw
        assert raw[:6]==b'\x7fELF\x02\x01'
        assert struct.unpack_from('<H',raw,18)[0]==183, 'Not AArch64'
        phoff,shoff=struct.unpack_from('<QQ',raw,32)
        phsize,phnum,shsize,shnum,shstr=struct.unpack_from('<HHHHH',raw,54)
        assert phsize==56 and shsize==64
        self.ph=[struct.unpack_from('<IIQQQQQQ',raw,phoff+i*phsize) for i in range(phnum)]
        self.sh=[struct.unpack_from('<IIQQQQIIQQ',raw,shoff+i*shsize) for i in range(shnum)]
        names=self.section(self.sh[shstr])
        self.sections={names[h[0]:].split(b'\0',1)[0].decode():h for h in self.sh}
    def section(self,h):
        if h[1]==8: return b''
        assert h[4]+h[5]<=len(self.raw)
        return self.raw[h[4]:h[4]+h[5]]
    def imports(self):
        h=self.sections['.dynsym'];strings=self.section(self.sh[h[6]])
        result=[]
        for i in range(0,h[5],24):
            name,info,other,idx,value,size=struct.unpack_from('<IBBHQQ',self.raw,h[4]+i)
            if name and idx==0:
                result.append(strings[name:].split(b'\0',1)[0].decode())
        return sorted(set(result))
    def build_id(self):
        notes=[self.section(h) for h in self.sh if h[1]==7]
        for note in notes:
            p=0
            while p+12<=len(note):
                n,d,t=struct.unpack_from('<III',note,p);p+=12
                name=note[p:p+n];p+=(n+3)&~3
                desc=note[p:p+d];p+=(d+3)&~3
                if t==3 and name==b'GNU\0': return desc[:32].ljust(32,b'\0')
        raise ValueError('ELF has no GNU Build ID')

def convert(raw):
    elf=Elf(raw)
    loads=[p for p in elf.ph if p[0]==1]
    assert len(loads)==3 and [p[1] for p in loads]==[5,4,6]
    assert loads[0][3]==0
    header=bytearray(256);header[:4]=b'NSO0'
    struct.pack_into('<I',header,12,0x38) # hash all segments, none compressed
    header[0x40:0x60]=elf.build_id()
    parts=[];offset=256;last_end=0
    for i,p in enumerate(loads):
        _,flags,fo,va,pa,fs,ms,align=p
        assert va%0x1000==0 and va>=last_end and ms>=fs
        assert fo+fs<=len(raw) and fs<2**32 and va+ms<2**32
        part=raw[fo:fo+fs]
        struct.pack_into('<IIII',header,0x10+i*16,offset,va,fs,ms-fs if i==2 else 0)
        struct.pack_into('<I',header,0x60+i*4,fs)
        header[0xA0+i*32:0xC0+i*32]=hashlib.sha256(part).digest()
        parts.append(part);offset+=fs;last_end=va+ms
    return bytes(header)+b''.join(parts)

if __name__=='__main__':
    import sys
    Path(sys.argv[2]).write_bytes(convert(Path(sys.argv[1]).read_bytes()))
