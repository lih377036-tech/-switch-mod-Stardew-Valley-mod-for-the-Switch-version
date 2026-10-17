"""Read-only verification of a locally exported Stardew Valley main NSO.

Never modifies or distributes the supplied executable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
from build import BID, SITE
from nso_reference import parse_header, load_segment

def inspect_main(path: Path, manifest: dict) -> dict:
    if not 0x100 <= path.stat().st_size <= 1024 * 1024 * 1024:
        raise ValueError("Unexpected NSO file size")
    data = path.read_bytes()
    flags, module_id, _, segments, _ = parse_header(data[:0x100])
    if module_id.hex().upper() != BID:
        raise ValueError(f"Build ID mismatch: {module_id.hex().upper()}; this patch was not made for this build")
    contents, hashes = {}, {}
    for segment in segments:
        if segment.decompressed_size > 512 * 1024 * 1024:
            raise ValueError("Unexpectedly large NSO segment")
        blob = load_segment(data, segment)
        digest = hashlib.sha256(blob).digest()
        if not segment.hash_enabled or digest != segment.expected_hash:
            raise ValueError(f"NSO {segment.name} SHA-256 is disabled or incorrect")
        contents[segment.name] = blob
        hashes[segment.name] = digest.hex()
    def at(offset: int, size: int) -> bytes:
        for segment in segments:
            if segment.memory_offset <= offset and offset + size <= segment.memory_end:
                start = offset - segment.memory_offset
                return contents[segment.name][start:start + size]
        raise ValueError(f"Code address {offset:#x} is outside file-backed NSO segments")
    records = manifest.get("records", [{"memory_offset": SITE, "size": 52, "original_hex": manifest["original_site_hex"]}])
    for record in records:
        if at(record["memory_offset"],record["size"]).hex() != record["original_hex"]:
            raise ValueError(f"Original instructions differ at {record['memory_offset']:#x}: another mod or executable revision may be present")
    entry = struct.pack("<4I",0xD103C3FF,0x6D063BEF,0xF90053F9,0x6D0733ED)
    if at(0x167FA90,16) != entry:
        raise ValueError("BobberBar.update entry fingerprint differs")
    return {"passed":True,"build_id":BID,"path":str(path.resolve()),
            "main_sha256":hashlib.sha256(data).hexdigest(),
            "segments_sha256":hashes,"all_patch_preimages_match":True,
            "verified_ranges":[[r["memory_offset"],r["size"]] for r in records],
            "hardware_test":"not_performed"}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("main",type=Path)
    p.add_argument("--manifest",type=Path,default=Path(__file__).resolve().parents[3] / "evidence" / "FISHING_BUILD.json")
    p.add_argument("--report",type=Path)
    args = p.parse_args()
    try:
        report = inspect_main(args.main,json.loads(args.manifest.read_text(encoding="utf-8")))
    except (ValueError,OSError,KeyError,struct.error) as error:
        print(f"Verification failed: {error}")
        raise SystemExit(2)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
