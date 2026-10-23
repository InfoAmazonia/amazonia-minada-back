#!/usr/bin/env python3
"""Back up the application and its MongoDB users/roles using the container credential.
Run as a Docker administrator. Output contains credentials/hashes: store it privately.
No password is passed in process arguments or written to the repository.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--container', default='amazonia-minada-back-database-1')
parser.add_argument('--directory', required=True)
args = parser.parse_args()
os.umask(0o077)
directory = Path(args.directory)
directory.mkdir(parents=True, exist_ok=True)
if directory.stat().st_mode & 0o077:
    raise SystemExit('Backup directory must have mode 0700')
container = json.loads(subprocess.check_output(['docker', 'inspect', args.container]))[0]
environment = dict(item.split('=', 1) for item in container['Config']['Env'])
config = json.dumps({'uri': 'mongodb://127.0.0.1:27017/?authSource=admin',
                     'password': environment['MONGO_INITDB_ROOT_PASSWORD']})
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
archive = directory / ('icfj-' + stamp + '.archive.gz')
partial = archive.with_suffix(archive.suffix + '.partial')
log = directory / ('icfj-' + stamp + '.log')
# JSON is valid YAML. The short-lived configuration is private and removed on exit.
script = '''set -eu
umask 077
config=$(mktemp /tmp/minada-backup.XXXXXX)
trap 'rm -f "$config"' EXIT HUP INT TERM
cat > "$config"
mongodump --config "$config" --username "$MONGO_INITDB_ROOT_USERNAME" --db icfj --dumpDbUsersAndRoles --archive --gzip
'''
with partial.open('xb') as output, log.open('xb') as errors:
    result = subprocess.run(['docker', 'exec', '-i', args.container, 'sh', '-c', script],
                            input=config.encode(), stdout=output, stderr=errors)
if result.returncode:
    partial.unlink(missing_ok=True)
    raise SystemExit('Backup failed; inspect private log: ' + str(log))
if partial.stat().st_size == 0:
    partial.unlink()
    raise SystemExit('Empty backup rejected')
partial.rename(archive)
digest = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
manifest = {'archive': str(archive), 'bytes': archive.stat().st_size,
            'sha256': digest, 'database': 'icfj', 'usersAndRoles': True,
            'image': container['Image']}
archive.with_suffix(archive.suffix + '.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest))
