"""Run actual Actions module commands on two clean runners, local Git remote only."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

class MockWorkflowTests(unittest.TestCase):
    def test_actual_commands_restore_and_skip_without_post_or_spend(self):
        source=Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            remote=root/'remote.git'
            def run(args,cwd):
                return subprocess.run(args,cwd=cwd,check=True,capture_output=True,text=True).stdout
            run(['git','init','--bare',str(remote)],root)
            seed=root/'seed'; seed.mkdir()
            for name in ('seo_media','data'):
                shutil.copytree(source/name,seed/name,ignore=shutil.ignore_patterns('__pycache__'))
            run(['git','init','-b','main'],seed)
            run(['git','add','.'],seed)
            run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m','Fixture'],seed)
            run(['git','remote','add','origin',str(remote)],seed)
            run(['git','push','origin','main'],seed)
            for index in (1,2):
                runner=root/f'runner{index}'
                run(['git','clone','--branch','main',str(remote),str(runner)],root)
                run([sys.executable,'-m','seo_media.state',str(runner)],runner)
                result=run([sys.executable,'-m','seo_media.engine','generate','--mode','mock','--state-git-dir',str(runner)],runner)
                ledger=json.loads((runner/'.state/ledger.json').read_text())
                self.assertEqual(len(ledger['articles']),1)
                self.assertEqual(ledger['posts'],{})
                self.assertEqual(ledger['requests'],{})
                self.assertTrue(all('approved_hash' not in a for a in ledger['articles'].values()))
                if index==2: self.assertIn('Already generated; skipped',result)
            saved=json.loads(run(['git','show','editorial-state:ledger.json'],remote))
            self.assertEqual(len(saved['articles']),1)

if __name__=='__main__': unittest.main()
