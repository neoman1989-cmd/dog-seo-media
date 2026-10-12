"""Create local-only ephemeral passwords; never overwrite an existing file."""
from pathlib import Path
import secrets
import os
path = Path(__file__).parent / '.env'
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as stream:
    for name in ('LOCAL_DB_PASSWORD', 'LOCAL_DB_ROOT_PASSWORD', 'LOCAL_WP_PASSWORD'):
        stream.write(f'{name}={secrets.token_urlsafe(32)}\n')
# Some cloud checkouts use umask 077; www-data must read the non-secret fixtures/theme.
root = Path(__file__).resolve().parent.parent
for directory in (root / 'wordpress', root / 'wordpress/dog-seo', root / 'validation'):
    directory.chmod(0o755)
for file in [* (root / 'wordpress/dog-seo').glob('*.php'), root / 'wordpress/dog-seo/style.css', root / 'wordpress/comparison-template.html', root / 'validation/seed.sh']:
    file.chmod(0o644)
print('Created ignored validation/.env (values not logged)')
