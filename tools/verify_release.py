"""Read-only structural/integrity checks for public release files.
SPDX-License-Identifier: GPL-2.0-only
"""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'work','outputs','.git','__pycache__'}
def release_files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not set(p.relative_to(ROOT).parts)&EXCLUDED and p.suffix!='.pyc')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def main():
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    expected={x['path']:x for x in manifest['files']}
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'atmosphere').rglob('*') if p.is_file()}
    assert actual==set(expected) and len(actual)==3
    for relative,entry in expected.items():
        raw=(ROOT/relative).read_bytes()
        assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],relative
    reader=module('release_nso',ROOT/'source/fishing/tools/nso_reference.py')
    ui=next(x for x in manifest['files'] if x['path'].endswith('subsdk9'))
    raw=(ROOT/ui['path']).read_bytes();_,bid,_,segments,_=reader.parse_header(raw[:256])
    ub=json.loads((ROOT/'evidence/UI_BUILD.json').read_text())
    assert bid.hex().upper()==ub['module_build_id']
    for segment in segments:
        blob=reader.load_segment(raw,segment)
        assert segment.hash_enabled and hashlib.sha256(blob).digest()==segment.expected_hash
    build=json.loads((ROOT/'evidence/UI_SOURCE_AND_BUILD.json').read_text())
    for relative,digest in build['source_files'].items():
        assert hashlib.sha256((ROOT/'source/ui'/Path(relative.replace('\\','/'))).read_bytes()).hexdigest()==digest,relative
    fmt=module('release_ips',ROOT/'source/fishing/tools/patch_format.py')
    fish=next(x for x in manifest['files'] if x['component']=='Fishing')
    records=fmt.parse_ips((ROOT/fish['path']).read_bytes())
    evidence=json.loads((ROOT/'evidence/FISHING_BUILD.json').read_text())
    assert [(off,data.hex()) for off,data in records]==[(x['ips_offset'],x['replacement_hex']) for x in evidence['records']]
    npdm=module('release_npdm',ROOT/'source/permissions/build_npdm.py')
    permissions=json.loads((ROOT/'source/permissions/npdm.json').read_text())
    assert npdm.build(permissions)==(ROOT/'atmosphere/contents/0100E65002BB8000/exefs/main.npdm').read_bytes()
    source_files=release_files()
    for p in source_files:
        relative=p.relative_to(ROOT)
        assert not set(relative.parts)&{'crash_reports','JKSV','backups'}
        assert p.name not in {'PROJECT_LESSONS.md','INSTALL_REPORT.json','AGENTS.md','prod.keys','title.keys'}
        assert p.suffix.lower() not in {'.jpg','.jpeg','.png','.nsp','.nsz','.xci','.nca','.log','.dmp','.exe','.elf','.o'}
        assert p.name!='main'
        assert not re.search(rb'[A-Za-z]:[\\/]Users[\\/][A-Za-z0-9_ .-]+[\\/]',p.read_bytes()),str(relative)
    assert 'GNU GENERAL PUBLIC LICENSE' in (ROOT/'LICENSE').read_text()
    assert (ROOT/'source/ui/runtime/source/rtld/LICENSE.txt').is_file()
    tests=json.loads((ROOT/'evidence/INSTALLER_TESTS.json').read_text())
    assert tests['status']=='PASSED' and tests['fixtures_only'] and not tests['real_sd_modified']
    shell_results=[]
    for evidence_path in sorted((ROOT/'evidence').glob('INSTALLER_TESTS_*.json')):
        result=json.loads(evidence_path.read_text())
        assert result['status']=='PASSED'
        for name,digest in result['script_sha256'].items():
            assert hashlib.sha256((ROOT/'tools'/name).read_bytes()).hexdigest()==digest,'Installer changed after testing'
        shell_results.append({'runner':result['runner'],'tests':result['tests'],'status':result['status']})
    report=dict(status='PASSED',payload_files=3,ui_runtime_source_files=len(build['source_files']),nso_segments_verified=len(segments),ips_records=len(records),npdm_rebuilt_identically=True,runtime_binaries_unchanged=True,public_files=len(source_files),private_content_scan='passed',installer_tests=tests,shell_results=shell_results,post_fix_ui_hardware_tested=False)
    (ROOT/'evidence/RELEASE_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
