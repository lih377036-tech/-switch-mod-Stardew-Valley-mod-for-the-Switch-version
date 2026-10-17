"""Run the actual PowerShell installer against isolated directory fixtures.
SPDX-License-Identifier: GPL-2.0-only
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, unittest, uuid

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'work'/('installer-tests-'+uuid.uuid4().hex[:10])
RUN.mkdir(parents=True)
MANIFEST=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
FILES={x['component']+('/npdm' if x['path'].endswith('main.npdm') else ''):x['path'] for x in MANIFEST['files']}
SHELL=os.environ.get('SDV_TEST_POWERSHELL',shutil.which('powershell.exe') or shutil.which('pwsh') or 'pwsh')

def quote(s): return "'"+str(s).replace("'","''")+"'"
def snapshot(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.case=RUN/self._testMethodName
        self.sd=self.case/'card with spaces'
        self.backup=self.case/'pc backup'
        (self.sd/'atmosphere').mkdir(parents=True)
        for name in ['config/uiinfosuite2/example.bin','JKSV/Stardew Valley/export.txt','atmosphere/config/system_settings.ini']:
            p=self.sd/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'protected fixture')
    def run_tool(self,script='Install.ps1',*args,root=None,expect=0):
        cmd=[SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str((root or ROOT)/'tools'/script),'-SdRoot',str(self.sd),*map(str,args)]
        if script=='Install.ps1':cmd+=['-BackupRoot',str(self.backup)]
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if expect==0:self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        else:self.assertNotEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        return p
    def report(self):
        return json.loads(next(self.backup.glob('*/INSTALL_REPORT.json')).read_text(encoding='utf-8-sig'))
    def payload(self):
        for f in MANIFEST['files']:
            p=self.sd/f['path'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['path'],p)
    def test_check_only_no_writes(self):
        before=snapshot(self.sd);self.run_tool('Install.ps1','-CheckOnly')
        self.assertEqual(before,snapshot(self.sd));self.assertFalse(self.backup.exists())
    def test_install_restore_fresh_and_preserve_settings(self):
        before=snapshot(self.sd);self.run_tool();r=self.report()
        self.assertFalse(r['device_binding']);self.assertFalse(r['game_main_build_id_verified'])
        for f in MANIFEST['files']:self.assertEqual(hashlib.sha256((self.sd/f['path']).read_bytes()).hexdigest(),f['sha256'])
        self.run_tool('Restore.ps1','-BackupDirectory',r['backup'],'-CheckOnly')
        self.run_tool('Restore.ps1','-BackupDirectory',r['backup'])
        self.assertEqual(before,snapshot(self.sd))
    def test_existing_payload_backup_and_restore(self):
        self.payload();before=snapshot(self.sd);self.run_tool();r=self.report()
        self.assertTrue(all(x['existed'] for x in r['entries']))
        self.run_tool('Restore.ps1','-BackupDirectory',r['backup'])
        self.assertEqual(before,snapshot(self.sd))
    def test_upgrade_legacy_fishing_and_restore(self):
        patch=ROOT/FILES['Fishing'];old=patch.read_bytes()[:63]+b'EEOF'
        self.assertIn(hashlib.sha256(old).hexdigest(),MANIFEST['known_fishing_hashes'])
        dest=self.sd/FILES['Fishing'];dest.parent.mkdir(parents=True);dest.write_bytes(old)
        before=snapshot(self.sd);self.run_tool();r=self.report()
        self.run_tool('Restore.ps1','-BackupDirectory',r['backup'])
        self.assertEqual(before,snapshot(self.sd))
    def test_fishing_only(self):
        self.run_tool('Install.ps1','-Components','Fishing')
        self.assertTrue((self.sd/FILES['Fishing']).exists());self.assertFalse((self.sd/FILES['UI']).exists())
    def test_ui_only_leaves_fishing_absent(self):
        self.run_tool('Install.ps1','-Components','UI')
        self.assertFalse((self.sd/FILES['Fishing']).exists());self.assertTrue((self.sd/FILES['UI']).exists())
    def test_ui_only_preserves_existing_fishing(self):
        dest=self.sd/FILES['Fishing'];dest.parent.mkdir(parents=True);shutil.copyfile(ROOT/FILES['Fishing'],dest)
        before=dest.read_bytes();self.run_tool('Install.ps1','-Components','UI');self.assertEqual(before,dest.read_bytes())
    def rejection(self,relative,data=b'foreign'):
        p=self.sd/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        before=snapshot(self.sd);self.run_tool(expect=1)
        self.assertEqual(before,snapshot(self.sd));self.assertFalse(self.backup.exists())
    def test_foreign_native_module_rejected(self):self.rejection('atmosphere/contents/0100E65002BB8000/exefs/subsdk8')
    def test_unknown_subsdk9_rejected(self):self.rejection(FILES['UI'])
    def test_foreign_npdm_rejected(self):self.rejection(FILES['UI/npdm'])
    def test_exefs_partition_override_rejected(self):self.rejection('atmosphere/contents/0100E65002BB8000/exefs.nsp')
    def test_main_stub_rejected(self):self.rejection('atmosphere/contents/0100E65002BB8000/exefs/main.stub')
    def test_duplicate_same_build_patch_rejected(self):self.rejection('atmosphere/exefs_patches/Other/'+MANIFEST['target']['main_build_id'].rstrip('0')+'.ips')
    def test_unknown_fishing_rejected(self):self.rejection(FILES['Fishing'])
    def test_unrelated_patch_preserved(self):
        p=self.sd/'atmosphere/exefs_patches/Other/1234567890ABCDEF.ips';p.parent.mkdir(parents=True);p.write_bytes(b'other-game fixture')
        self.run_tool();self.assertEqual(p.read_bytes(),b'other-game fixture')
    def main_fixture(self,bid=None):
        p=self.case/'main';raw=bytearray(256);raw[:4]=b'NSO0';raw[64:96]=bytes.fromhex(bid or MANIFEST['target']['main_build_id']);p.write_bytes(raw);return p
    def test_matching_build_id_checked(self):
        self.run_tool('Install.ps1','-GameMain',self.main_fixture());self.assertTrue(self.report()['game_main_build_id_verified'])
    def test_wrong_build_id_rejected(self):
        before=snapshot(self.sd);self.run_tool('Install.ps1','-GameMain',self.main_fixture('00'*32),expect=1);self.assertEqual(before,snapshot(self.sd))
    def test_corrupt_package_rejected(self):
        package=self.case/'package copy'
        for rel in ['tools','atmosphere']:shutil.copytree(ROOT/rel,package/rel)
        shutil.copyfile(ROOT/'manifest.json',package/'manifest.json')
        with (package/FILES['UI']).open('ab') as stream:stream.write(b'corruption')
        before=snapshot(self.sd);self.run_tool(root=package,expect=1);self.assertEqual(before,snapshot(self.sd))
    def test_backup_on_sd_rejected(self):
        self.backup=self.sd/'bad backups';before=snapshot(self.sd);self.run_tool(expect=1);self.assertEqual(before,snapshot(self.sd))
    def test_restore_preserves_later_changes(self):
        self.run_tool();r=self.report();(self.sd/FILES['UI']).write_bytes(b'later mod version')
        before=snapshot(self.sd);self.run_tool('Restore.ps1','-BackupDirectory',r['backup'],expect=1);self.assertEqual(before,snapshot(self.sd))
    def test_corrupt_backup_rejected_before_restore(self):
        self.payload();self.run_tool();r=self.report()
        entry=next(x for x in r['entries'] if x['path']==FILES['UI'])
        (Path(r['backup'])/entry['backup_file']).write_bytes(b'broken backup')
        before=snapshot(self.sd);self.run_tool('Restore.ps1','-BackupDirectory',r['backup'],expect=1);self.assertEqual(before,snapshot(self.sd))
    def test_copy_failure_rolls_back(self):
        before=snapshot(self.sd)
        wrapper=self.case/'inject-copy-failure.ps1'
        wrapper.write_text("$ErrorActionPreference='Stop'\n$global:sdvTestFailOnce=$true\nfunction Copy-Item { param([string]$LiteralPath,[string]$Destination,[switch]$Force)\n"+
            "if ($Destination -eq "+quote(self.sd/FILES['UI'])+" -and $global:sdvTestFailOnce) { $global:sdvTestFailOnce=$false; throw 'simulated copy failure' }\n"+
            "Microsoft.PowerShell.Management\\Copy-Item @PSBoundParameters\n}\n& "+quote(ROOT/'tools/Install.ps1')+
            " -SdRoot "+quote(self.sd)+" -BackupRoot "+quote(self.backup)+"\n",encoding='utf-8-sig')
        p=subprocess.run([SHELL,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(wrapper)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        self.assertNotEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn('simulated copy failure',p.stdout+p.stderr)
        self.assertEqual(before,snapshot(self.sd))
    def test_different_card_path_and_volume_root(self):
        if os.name!='nt':self.skipTest('Windows SUBST fixture')
        letter=next((x+':' for x in 'ZYXWVUTSRQ' if not Path(x+':/').exists()),None)
        if not letter:self.skipTest('No free fixture drive letter')
        subprocess.run(['subst',letter,str(self.sd)],check=True,capture_output=True)
        old=self.sd
        try:
            self.sd=Path(letter+'/');self.run_tool();self.assertTrue((old/FILES['Fishing']).exists())
        finally:
            self.sd=old;subprocess.run(['subst',letter,'/D'],check=True,capture_output=True)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(InstallerTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'PASSED' if result.wasSuccessful() else 'FAILED','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'runner':'Windows PowerShell 5.1' if 'windowspowershell' in SHELL.lower() or Path(SHELL).name.lower()=='powershell.exe' else 'PowerShell 7','fixtures_only':True,'real_sd_modified':False,'sd_or_reader_identity_required':False,'script_sha256':{f:hashlib.sha256((ROOT/'tools'/f).read_bytes()).hexdigest() for f in ['Common.ps1','Install.ps1','Restore.ps1']}}
    (RUN/'RESULT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    if result.wasSuccessful():
        (ROOT/'evidence/INSTALLER_TESTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        (ROOT/'evidence'/('INSTALLER_TESTS_'+('WindowsPS51' if report['runner']=='Windows PowerShell 5.1' else 'PS7')+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not result.wasSuccessful())
