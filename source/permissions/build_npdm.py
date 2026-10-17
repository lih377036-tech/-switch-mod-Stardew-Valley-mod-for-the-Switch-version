"""Rebuild the unsigned homebrew permissions descriptor. SPDX-License-Identifier: GPL-2.0-only"""
import argparse, hashlib, json, struct
from pathlib import Path

def build(config):
    out=bytearray(config['size'])
    def put(offset,data): out[offset:offset+len(data)]=data
    put(0,bytes.fromhex(config['meta_header_hex']))
    a=config['aci_offset'];c=config['acid_offset']
    put(a,bytes.fromhex(config['aci_header_hex']))
    put(c+512,bytes.fromhex(config['acid_header_hex']))
    put(a+64,bytes.fromhex(config['aci_filesystem_policy_hex']))
    put(c+576,bytes.fromhex(config['acid_filesystem_policy_hex']))
    services=b''.join(bytes([len(s.encode('ascii'))-1])+s.encode('ascii') for s in config['services'])
    caps=struct.pack('<'+'I'*len(config['kernel_capabilities']),*[int(x,0) for x in config['kernel_capabilities']])
    for header,base in [(a,a),(c+512,c)]:
        so,ss,ko,ks=struct.unpack_from('<IIII',out,header+0x28)
        assert len(services)==ss and len(caps)==ks
        put(base+so,services);put(base+ko,caps)
    assert hashlib.sha256(out).hexdigest()==config['expected_sha256']
    return bytes(out)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    config=json.loads(Path(__file__).with_name('npdm.json').read_text(encoding='utf-8'))
    raw=build(config);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(raw)
    print(hashlib.sha256(raw).hexdigest())
