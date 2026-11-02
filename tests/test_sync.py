import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name); self.source=base/'source'; self.instance=base/'instance'
        shutil.copytree(ROOT,self.source,ignore=shutil.ignore_patterns('.git','__pycache__','.DS_Store'))
        shutil.copytree(ROOT/'templates/_instance',self.instance)
        subprocess.run(['git','init','-q',str(self.source)],check=True)
        subprocess.run(['git','-C',str(self.source),'add','.'],check=True)
        subprocess.run(['git','-C',str(self.source),'-c','user.name=Synthetic','-c','user.email=test@example.org','commit','-qm','fixture'],check=True)
        self.sha=subprocess.check_output(['git','-C',str(self.source),'rev-parse','HEAD'],text=True).strip()
        (self.instance/'.engine-source').write_text(str(self.source)+'\n')
        (self.instance/'.engine-version').write_text(self.sha+'\n')
        (self.instance/'conference/event.md').write_text('private event state')
        (self.instance/'local').mkdir(); (self.instance/'local/note').write_text('private local state')
        (self.instance/'journal/INDEX.md').write_text('private journal state')

    def run_sync(self,*args):
        return subprocess.run(['bash',str(self.instance/'scripts/sync-engine.sh'),*args],capture_output=True,text=True)

    def test_dry_run_then_sync_preserves_instance_state(self):
        result=self.run_sync('--dry-run'); self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.instance/'.claude/workflows').exists())
        result=self.run_sync(); self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((self.instance/'.claude/workflows/speaker-deep-research.js').exists())
        self.assertEqual((self.instance/'conference/event.md').read_text(),'private event state')
        self.assertEqual((self.instance/'local/note').read_text(),'private local state')
        self.assertEqual((self.instance/'journal/INDEX.md').read_text(),'private journal state')
        self.assertEqual((self.instance/'.engine-version').read_text().strip(),self.sha)

    def test_symlink_destination_refused_before_copy(self):
        outside=self.instance.parent/'outside'; outside.mkdir()
        (self.instance/'.claude').symlink_to(outside,target_is_directory=True)
        result=self.run_sync(); self.assertNotEqual(result.returncode,0)
        self.assertIn('Refusing symlink',result.stderr)
        self.assertEqual(list(outside.iterdir()),[])

if __name__ == '__main__': unittest.main()
