"""Package all corresponding source and runtime files; exclude private work/backups.
SPDX-License-Identifier: GPL-2.0-only
"""
from pathlib import Path
import hashlib, json, zipfile
from verify_release import main as verify, release_files, ROOT

if __name__=='__main__':
    verify()
    version=json.loads((ROOT/'manifest.json').read_text())['bundle_version']
    name='Stardew-Switch-1.6.15.3-Portable-v'+version
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    archive=out/(name+'.zip')
    if archive.exists():raise SystemExit('Refusing to overwrite an existing release ZIP.')
    files=[p for p in release_files() if p.name!='SHA256SUMS.txt']
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files)
    (ROOT/'SHA256SUMS.txt').write_text(sums,encoding='utf-8')
    files.append(ROOT/'SHA256SUMS.txt')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(files):
            entry=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2026,10,17,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o100644<<16
            z.writestr(entry,p.read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist())==len(files)
        for p in files:assert z.read(p.relative_to(ROOT).as_posix())==p.read_bytes()
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=digest,files=len(files)),indent=2))
