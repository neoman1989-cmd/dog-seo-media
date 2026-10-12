"""Locked, atomic ledger. Reserve before side effects; uncertainty is never retried."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess


class State:
    def __init__(self, path, checkpoint=None):
        self.path = Path(path)
        self.checkpoint = checkpoint
        self.data = None

    @contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.data = json.loads(self.path.read_text())
            if self.data.get('version') != 1 or not all(isinstance(self.data.get(k), dict) for k in ('articles','requests','posts')):
                raise ValueError('Invalid state; refusing to reset history')
            yield self

    def save(self):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.data, ensure_ascii=False, indent=2, allow_nan=False))
        os.replace(temporary, self.path)
        if self.checkpoint:
            self.checkpoint()  # must succeed BEFORE a network side effect


def initialize(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump({'version':1,'articles':{},'requests':{},'posts':{}}, stream)


def git_command(args, directory, text=None):
    return subprocess.run(['git', *args], cwd=directory, input=text, text=True,
                          capture_output=True, check=True).stdout.strip()


def git_checkpoint(directory):
    directory = Path(directory).resolve()
    def checkpoint():
        ledger = directory / '.state/ledger.json'
        blob = git_command(['hash-object','-w','--stdin'], directory, ledger.read_text())
        tree = git_command(['mktree'], directory, f'100644 blob {blob}\tledger.json\n')
        parent = subprocess.run(['git','rev-parse','--verify','refs/remotes/origin/editorial-state'], cwd=directory, text=True, capture_output=True)
        if parent.returncode not in (0,128): raise RuntimeError('Cannot read state ref')
        args = ['-c','user.name=dog-media-bot','-c','user.email=bot@users.noreply.github.com','commit-tree',tree]
        if parent.returncode == 0: args += ['-p',parent.stdout.strip()]
        commit = git_command(args, directory, 'Persist editorial ledger\n')
        # Non-fast-forward rejection stops work; never force a competing ledger away.
        git_command(['push','origin',commit + ':refs/heads/editorial-state'], directory)
        git_command(['update-ref','refs/remotes/origin/editorial-state',commit], directory)
    return checkpoint


def bootstrap_git(directory):
    directory = Path(directory).resolve()
    path = directory / '.state/ledger.json'
    if path.exists(): raise ValueError('Bootstrap requires a fresh state directory')
    path.parent.mkdir(parents=True, exist_ok=True)
    remote = subprocess.run(['git','ls-remote','--exit-code','origin','refs/heads/editorial-state'], cwd=directory, text=True, capture_output=True)
    if remote.returncode == 0:
        git_command(['fetch','origin','refs/heads/editorial-state:refs/remotes/origin/editorial-state'], directory)
        contents = git_command(['show','refs/remotes/origin/editorial-state:ledger.json'], directory)
        path.write_text(contents)
        with State(path).locked(): pass  # corrupted history is a blocker, never initialize over it
    elif remote.returncode == 2:
        initialize(path)
        git_checkpoint(directory)()  # first-run creation; no network API work yet
    else:
        raise RuntimeError('Unable to read persistent state; refusing empty history')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    bootstrap_git(parser.parse_args().directory)
