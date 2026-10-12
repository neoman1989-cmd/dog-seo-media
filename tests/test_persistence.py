"""Real Git integration against a temporary local bare remote; no external API."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from seo_media.state import State, bootstrap_git, git_checkpoint
from seo_media.engine import generate_once, approve_article, post_draft


def git(directory,*args):
    return subprocess.run(['git',*args],cwd=directory,check=True,capture_output=True,text=True).stdout.strip()


class DurableGitTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.remote=self.root/'remote.git'; self.remote.mkdir(); git(self.remote,'init','--bare')
        self.products=json.loads(Path('data/products.json').read_text())
        self.brief=json.loads(Path('data/briefs.json').read_text())[0]

    def runner(self,name):
        path=self.root/name; path.mkdir()
        git(path,'init'); git(path,'remote','add','origin',str(self.remote))
        bootstrap_git(path)
        return path

    def test_restore_across_fresh_runners_and_different_output(self):
        first=self.runner('first')
        with State(first/'.state/ledger.json',git_checkpoint(first)).locked() as state:
            article=generate_once(self.brief,self.products,state)
            approve_article(article,state)
            post_draft(article,self.products,state)
        second=self.runner('second')
        with State(second/'.state/ledger.json',git_checkpoint(second)).locked() as state:
            with patch('seo_media.engine.generate') as generate:
                self.assertIsNone(generate_once(self.brief,self.products,state)); generate.assert_not_called()
            with self.assertRaises(ValueError): post_draft(article,self.products,state)
            self.assertEqual(len(state.data['posts']),1)

    def test_stale_writer_cannot_overwrite_remote_or_send(self):
        first=self.runner('first'); stale=self.runner('stale')
        with State(first/'.state/ledger.json',git_checkpoint(first)).locked() as state:
            generate_once(self.brief,self.products,state)
        with State(stale/'.state/ledger.json',git_checkpoint(stale)).locked() as state, patch('seo_media.engine.generate') as generate:
            with self.assertRaises(subprocess.CalledProcessError): generate_once(self.brief,self.products,state)
            generate.assert_not_called()

    def test_remote_read_failure_never_resets_history(self):
        bad=self.root/'bad'; bad.mkdir(); git(bad,'init'); git(bad,'remote','add','origin',str(self.root/'missing'))
        with self.assertRaises(RuntimeError): bootstrap_git(bad)
        self.assertFalse((bad/'.state/ledger.json').exists())

    def test_corrupt_remote_history_never_reset(self):
        first=self.runner('first')
        (first/'.state/ledger.json').write_text('{"version":999}')
        git_checkpoint(first)()
        second=self.root/'second'; second.mkdir(); git(second,'init'); git(second,'remote','add','origin',str(self.remote))
        with self.assertRaises(ValueError): bootstrap_git(second)
        self.assertEqual(json.loads((second/'.state/ledger.json').read_text())['version'],999)

if __name__=='__main__': unittest.main()
