"""Build the included UI runtime using externally supplied LLVM/devkitPro. SPDX-License-Identifier: GPL-2.0-only"""
import os
from pathlib import Path
import json
import subprocess
import hashlib
import sys
import argparse
import shutil
from elf_to_nso import Elf,convert

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'runtime/source'
BUILD=ROOT/'work/build'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--llvm-bin',type=Path,required=True)
parser.add_argument('--devkitpro',type=Path,required=True)
args=parser.parse_args()
LLVM=args.llvm_bin.resolve()
DKP=args.devkitpro.resolve()
A64=DKP/'devkitA64/aarch64-none-elf'
CLANG=next((LLVM/n for n in ('clang-23.exe','clang.exe','clang') if (LLVM/n).is_file()),LLVM/'clang')
LLD=next((LLVM/n for n in ('ld.lld.exe','ld.lld') if (LLVM/n).is_file()),LLVM/'ld.lld')
BUILD.mkdir(parents=True,exist_ok=True)
os.environ.update(TEMP=str(ROOT/'work'),TMP=str(ROOT/'work'),PYTHONDONTWRITEBYTECODE='1')

def run(args):
    p=subprocess.run([str(a) for a in args],capture_output=True,text=True)
    with (BUILD/'build.log').open('a',encoding='utf-8') as f:
        f.write(subprocess.list2cmdline([str(a) for a in args])+'\n'+p.stdout+p.stderr)
    if p.returncode:
        print(p.stdout+p.stderr);raise RuntimeError('Build command failed; see work/build/build.log')

def options():
    versions=sorted((A64/'include/c++').iterdir())
    cxx=versions[-1]
    arch=cxx/'aarch64-none-elf'
    assert arch.is_dir() and (A64/'lib/pic/libsysbase.a').is_file()
    common=['--target=aarch64-none-elf','-march=armv8-a+crc+crypto','-fPIC',
        '-fvisibility=default','-ffunction-sections','-fdata-sections',
        '-D__SWITCH__','-D__RTLD_6XX__','-DEXL_LOAD_KIND=Module','-DEXL_LOAD_KIND_ENUM=2',
        '-DEXL_PROGRAM_ID=0x0100E65002BB8000','-DEXL_USE_FAKEHEAP']
    for d in ['', 'lib','nn','program','rtld','game']:
        common+=['-I',str(SRC/d)]
    cxxflags=['-std=gnu++23','-fno-rtti','-fno-exceptions','-fno-asynchronous-unwind-tables',
        '-fno-unwind-tables','-nostdinc++','-isystem',str(cxx),'-isystem',str(arch)]
    return common,cxxflags

def main():
    (BUILD/'build.log').write_text('',encoding='utf-8')
    common,cxx=options()
    tests=sorted((ROOT/'tests').glob('*.cpp'))
    cinc=['-isystem',str(A64/'include')]
    run([CLANG,*common,*cxx,*cinc,'-fsyntax-only',*tests])
    print('ARM64 compile-time tests passed',flush=True)
    sources=sorted(p for p in SRC.rglob('*') if p.suffix in ('.c','.cpp','.s'))
    objects=[]
    for p in sources:
        obj=BUILD/(str(p.relative_to(SRC)).replace('\\','_').replace('/','_')+'.o')
        run([CLANG,*common,*(cxx if p.suffix=='.cpp' else []),*cinc,'-O2','-c',p,'-o',obj])
        objects.append(obj)
    elf=BUILD/'uiinfosuite2.elf'
    run([LLD,'-shared','-T',ROOT/'runtime/misc/link.ld','--gc-sections',
         '--build-id=sha1','--export-dynamic','-init=exl_module_init','-soname=subsdk9',
         '-Map='+str(BUILD/'uiinfosuite2.map'),'-o',elf,*objects,A64/'lib/pic/libsysbase.a'])
    raw=elf.read_bytes()
    nso=convert(raw)
    (BUILD/'subsdk9').write_bytes(nso)
    report={'compiled_units':len(sources),'compile_time_tests':[p.name for p in tests],
        'source_files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(SRC.rglob('*')) if p.is_file()},
        'module_build_id':Elf(raw).build_id().hex().upper(),
        'subsdk9_sha256':hashlib.sha256(nso).hexdigest(),
        'undefined_imports':Elf(raw).imports(),
        'clang':subprocess.check_output([str(CLANG),'--version'],text=True).splitlines()[0],
        'hardware_tested':False}
    (BUILD/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Built',elf,'and uncompressed NSO',len(nso),'bytes',flush=True)

if __name__=='__main__': main()
