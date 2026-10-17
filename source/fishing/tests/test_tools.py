"""Negative and compatibility checks using synthetic NSO/SD inputs."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools"))
from build import BID,SITE,TREASURE_SITE,OUTPUT_NAME
from patch_format import parse_ips,write_ips32
from verify_game import inspect_main
from check_sd import check
from reassemble_reference import BASE

class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = ROOT / "work" / "tool-tests" / str(time.time_ns())
        cls.work.mkdir(parents=True)
        cls.manifest = json.loads((ROOT / "outputs" / OUTPUT_NAME / "BUILD_INFO.json").read_text(encoding="utf-8"))
        text = (ROOT / "work" / "validation" / "reference.bin").read_bytes()
        cls.segments = [text,b"synthetic-rodata",b"synthetic-data"]

    def make_nso(self, name="main", corrupt=False, bid=BID, patched=False, treasure_modified=False):
        header = bytearray(0x100); header[:4] = b"NSO0"
        struct.pack_into("<I",header,0xC,0x38)
        header[0x40:0x60] = bytes.fromhex(bid)
        offset = 0x100; content = bytearray()
        for i,blob in enumerate(self.segments):
            if i==0 and patched:
                blob=bytearray(blob); blob[SITE-BASE]=0; blob=bytes(blob)
            if i==0 and treasure_modified:
                blob=bytearray(blob); blob[TREASURE_SITE-BASE]=0; blob=bytes(blob)
            struct.pack_into("<III",header,0x10+i*0x10,offset,BASE+i*0x3000,len(blob))
            struct.pack_into("<I",header,0x60+i*4,len(blob))
            header[0xA0+i*32:0xC0+i*32]=hashlib.sha256(blob).digest()
            content+=blob; offset+=len(blob)
        if corrupt: content[-1]^=1
        path=self.work/name; path.write_bytes(header+content); return path

    def test_correct_build_and_all_hashes(self):
        self.assertTrue(inspect_main(self.make_nso(),self.manifest)["passed"])
    def test_wrong_build_rejected(self):
        with self.assertRaisesRegex(ValueError,"Build ID mismatch"):
            inspect_main(self.make_nso("wrong",bid="00"*32),self.manifest)
    def test_corrupted_segment_rejected(self):
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            inspect_main(self.make_nso("corrupt",corrupt=True),self.manifest)
    def test_changed_code_rejected_even_with_valid_hash(self):
        with self.assertRaisesRegex(ValueError,"instructions differ"):
            inspect_main(self.make_nso("modded",patched=True),self.manifest)
    def test_bad_magic_rejected(self):
        path=self.work/"bad"; path.write_bytes(b"?"*256)
        with self.assertRaises(ValueError): inspect_main(path,self.manifest)
    def test_changed_treasure_instruction_rejected(self):
        with self.assertRaisesRegex(ValueError,"instructions differ"):
            inspect_main(self.make_nso("modded-treasure",treasure_modified=True),self.manifest)
    def test_ips32_roundtrip(self):
        records=[(SITE+0x100,b"1234")]
        self.assertEqual(parse_ips(write_ips32(records)),records)
    def test_malformed_patches_rejected(self):
        for data in [b"",b"IPS32",b"IPS32EEOFx",b"IPS32\x01\x67\xfc\xd4\x00\x10xEEOF"]:
            with self.subTest(data=data):
                with self.assertRaises(ValueError): parse_ips(data)
    def test_overlapping_records_rejected(self):
        with self.assertRaisesRegex(ValueError,"Overlapping"):
            write_ips32([(0x100,b"1234"),(0x102,b"56")])
    def test_sd_existing_native_module_rejected(self):
        root=self.work/"sd-native"; folder=root/"atmosphere"/"contents"/"0100E65002BB8000"/"exefs"
        folder.mkdir(parents=True); (folder/"subsdk9").write_bytes(b"test")
        self.assertFalse(check(root)["passed"])
    def test_sd_patch_overlap_rejected(self):
        root=self.work/"sd-overlap"; folder=root/"atmosphere"/"exefs_patches"/"OtherMod"
        folder.mkdir(parents=True)
        (folder/(BID+".ips")).write_bytes(write_ips32([(SITE+0x100,b"1234")]))
        self.assertFalse(check(root)["passed"])
    def test_sd_unrelated_patch_allowed(self):
        root=self.work/"sd-safe"; folder=root/"atmosphere"/"exefs_patches"/"OtherMod"
        folder.mkdir(parents=True)
        (folder/(BID+".ips")).write_bytes(write_ips32([(0x101,b"1234")]))
        self.assertTrue(check(root)["passed"])
    def test_sd_treasure_patch_overlap_rejected(self):
        root=self.work/"sd-treasure-overlap"; folder=root/"atmosphere"/"exefs_patches"/"OtherMod"
        folder.mkdir(parents=True)
        (folder/(BID+".ips")).write_bytes(write_ips32([(TREASURE_SITE+0x100,b"1234")]))
        self.assertFalse(check(root)["passed"])

if __name__=="__main__":
    program=unittest.main(verbosity=2,exit=False)
    result=program.result
    report={"passed":result.wasSuccessful(),"tests":result.testsRun,
            "failures":len(result.failures),"errors":len(result.errors),
            "inputs":"synthetic NSO and SD fixtures; no console data modified"}
    (ROOT/"work"/"validation"/"TOOL_TESTS.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
