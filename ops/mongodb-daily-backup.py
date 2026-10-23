#!/usr/bin/env python3
"""Daily verified MongoDB backups. Requires root, Docker and Python 3.11+."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import tempfile
import time
from urllib.parse import quote
import uuid

JOB = 'minada-mongodb-daily'
LABEL = 'org.infoamazonia.minada.backup-job'
RUN_LABEL = 'org.infoamazonia.minada.backup-run'
RUN_PATTERN = re.compile(r'\d{8}T\d{12}Z-[a-f0-9]{32}')
PREFIX = 'minada-mongo-restore-'


def private_directory(path):
    if path.is_symlink():
        raise RuntimeError('Symlink directory rejected')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.stat().st_uid != os.geteuid() or path.stat().st_mode & 0o077:
        raise RuntimeError('Directory must be owned by this user with mode 0700')


def write_status(folder, data):
    temporary = folder / 'status.tmp'
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(folder / 'status.json')


def prune(root, state, keep):
    """Only delete recognized completed run folders; never follow symlinks."""
    candidates = []
    for folder in root.iterdir():
        if folder.is_symlink() or not folder.is_dir() or not RUN_PATTERN.fullmatch(folder.name):
            continue
        status = folder / 'status.json'
        if status.is_symlink():
            continue
        try:
            data = json.loads(status.read_text())
        except (OSError, ValueError):
            continue
        if data.get('job') == JOB and data.get('run') == folder.name and data.get('state') == state:
            candidates.append(folder)
    removed = []
    for folder in sorted(candidates, reverse=True)[keep:]:
        shutil.rmtree(folder)
        removed.append(folder.name)
    return removed


def inspect(container):
    return json.loads(subprocess.check_output(['docker', 'inspect', container]))[0]


def mongo(container, username, password, program, log):
    uri = 'mongodb://' + quote(username, safe='') + ':' + quote(password, safe='') + '@127.0.0.1:27017/admin'
    script = ('try {const db=new Mongo(' + json.dumps(uri) + ').getDB("admin");' + program +
              '} catch(e) { const known=["Import is active or requires inspection","Required collection missing","Empty licenses rejected","Database hash failed"]; print(JSON.stringify({code:e.code,name:e.codeName,reason:known.includes(e.message)?e.message:undefined})); quit(1); }')
    result = subprocess.run(['docker', 'exec', '-i', container, 'mongosh', '--quiet', '--nodb',
                             '--file', '/dev/stdin'], input=script, text=True, capture_output=True)
    if result.returncode:
        with log.open('a') as stream:
            stream.write(result.stdout + result.stderr)
        raise RuntimeError('MongoDB command failed; see protected log')
    return result.stdout


SNAPSHOT = '''
const d=db.getSiblingDB("icfj");
const names=d.getCollectionNames().sort();
if(names.some(n=>n.endsWith("_importing")) || d.getCollection("import_locks").countDocuments({})>0)
    throw Error("Import is active or requires inspection");
for(const n of ["licenses","invasions","reserveinvasions","unities","reserves"])
    if(!names.includes(n)) throw Error("Required collection missing");
if(d.getCollection("licenses").countDocuments({})===0) throw Error("Empty licenses rejected");
const hashes=d.runCommand({dbHash:1,collections:names,maxTimeMS:60000});
if(hashes.ok!==1) throw Error("Database hash failed");
const listedUsers=d.runCommand({usersInfo:1,showCredentials:false}).users;
const users=listedUsers.length ? d.runCommand({usersInfo:listedUsers.map(u=>({user:u.user,db:u.db})),showCredentials:false,showPrivileges:true}).users : [];
const listedRoles=d.runCommand({rolesInfo:1,showBuiltinRoles:false}).roles;
const roles=listedRoles.length ? d.runCommand({rolesInfo:listedRoles.map(r=>({role:r.role,db:r.db})),showPrivileges:true}).roles : [];
function selected(object,keys) { return Object.fromEntries(keys.filter(k=>k in object).map(k=>[k,object[k]])); }
const collections=names.map(name=>({name,count:d.getCollection(name).countDocuments({}),hash:hashes.collections[name],indexes:d.getCollection(name).getIndexes().map(i=>({...i,key:Object.entries(i.key)})).sort((a,b)=>a.name.localeCompare(b.name))}));
print("MINADA_RESULT="+JSON.stringify({collections,users:users.map(u=>selected(u,["user","db","roles","inheritedRoles","inheritedPrivileges","mechanisms"])),roles:roles.map(r=>selected(r,["role","db","roles","inheritedRoles","privileges","inheritedPrivileges"]))}));
'''


def canonical_security(value):
    if isinstance(value, list):
        return sorted((canonical_security(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, dict):
        return {key: canonical_security(item) for key, item in value.items()}
    return value


def snapshot(container, username, password, log):
    output = mongo(container, username, password, SNAPSHOT, log)
    data = json.loads(next(line.removeprefix('MINADA_RESULT=') for line in output.splitlines()
                           if line.startswith('MINADA_RESULT=')))
    for key in ['users', 'roles']:
        data[key] = canonical_security(data[key])
    return data


def cleanup_stale():
    """Called only under the global lock; ownership labels and exact names are required."""
    container_ids = subprocess.check_output(['docker', 'ps', '-aq', '--filter', f'label={LABEL}={JOB}'], text=True).split()
    for container_id in container_ids:
        data = inspect(container_id)
        token = data['Config']['Labels'].get(RUN_LABEL, '')
        if re.fullmatch('[a-f0-9]{32}', token) and data['Name'] == '/' + PREFIX + token:
            subprocess.run(['docker', 'rm', '-fv', container_id], check=True, stdout=subprocess.DEVNULL)
    volumes = subprocess.check_output(['docker', 'volume', 'ls', '-q', '--filter', f'label={LABEL}={JOB}'], text=True).split()
    for volume in volumes:
        data = json.loads(subprocess.check_output(['docker', 'volume', 'inspect', volume]))[0]
        token = data['Labels'].get(RUN_LABEL, '')
        if re.fullmatch('[a-f0-9]{32}', token) and volume == PREFIX + token:
            subprocess.run(['docker', 'volume', 'rm', volume], check=True, stdout=subprocess.DEVNULL)


def perform(args, folder, state):
    if shutil.disk_usage(args.root).free < args.min_free_gib * 1024**3:
        raise RuntimeError('Insufficient free space; valid backups retained')
    source = inspect(args.container)
    environment = dict(item.split('=', 1) for item in source['Config']['Env'])
    username = environment['MONGO_INITDB_ROOT_USERNAME']
    password = environment['MONGO_INITDB_ROOT_PASSWORD']
    state['phase'] = 'source-snapshot'
    write_status(folder, state)
    before = snapshot(args.container, username, password, folder / 'source.log')
    (folder / 'source.json').write_text(json.dumps(before, indent=2))
    state['phase'] = 'backup'
    write_status(folder, state)
    result = subprocess.run(['python3', str(args.backup_command), '--container', args.container,
                             '--directory', str(folder)], capture_output=True, text=True)
    (folder / 'backup-command.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Backup command failed; valid backups retained')
    manifest = json.loads(result.stdout)
    archive = Path(manifest['archive'])
    if archive.is_symlink() or archive.parent != folder or archive.stat().st_size != manifest['bytes']:
        raise RuntimeError('Invalid archive manifest')
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != manifest['sha256']:
            raise RuntimeError('Archive checksum mismatch')
    state['phase'] = 'consistency-check'
    write_status(folder, state)
    if snapshot(args.container, username, password, folder / 'source.log') != before:
        raise RuntimeError('Source changed during dump; valid backups retained')
    print('Archive complete and source stable; starting isolated full restore', flush=True)
    state['phase'] = 'restore'
    write_status(folder, state)
    token = state['token']
    name = PREFIX + token
    labels = ['--label', f'{LABEL}={JOB}', '--label', f'{RUN_LABEL}={token}']
    test_password = secrets.token_hex(40)
    test_user = 'minada_restore_test'
    with tempfile.TemporaryDirectory(prefix='minada-backup-', dir='/run') as temporary:
        root_env = Path(temporary) / 'root.env'
        root_env.write_text(f'MONGO_INITDB_ROOT_USERNAME={test_user}\nMONGO_INITDB_ROOT_PASSWORD={test_password}\n')
        subprocess.run(['docker', 'volume', 'create', *labels, name], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['docker', 'run', '-d', '--pull=never', '--name', name, *labels,
                        '--network', 'none', '--cpus', '1', '--memory', '2g', '--pids-limit', '256',
                        '--log-driver', 'local', '--log-opt', 'max-size=5m', '--log-opt', 'max-file=2',
                        '--env-file', str(root_env), '--mount', f'type=volume,src={name},dst=/data/db',
                        '--tmpfs', '/data/configdb:rw,nosuid,nodev,size=16m',
                        '--tmpfs', '/tmp:rw,nosuid,nodev,size=32m',
                        source['Config']['Image'], 'mongod', '--wiredTigerCacheSizeGB', '0.5',
                        '--bind_ip', '127.0.0.1'], check=True, stdout=subprocess.DEVNULL)
        for _ in range(90):
            try:
                mongo(name, test_user, test_password, 'print(db.runCommand({ping:1}).ok);', folder / 'readiness.log')
                break
            except RuntimeError:
                time.sleep(1)
        else:
            raise RuntimeError('Restore test MongoDB did not become ready')
        config = json.dumps({'uri': 'mongodb://127.0.0.1:27017/?authSource=admin', 'password': test_password})
        subprocess.run(['docker', 'exec', '-i', name, 'sh', '-c', 'umask 077; cat > /tmp/restore.json'],
                        input=config.encode(), check=True)
        with archive.open('rb') as data, (folder / 'restore.log').open('wb') as log:
            subprocess.run(['docker', 'exec', '-i', name, 'mongorestore', '--config', '/tmp/restore.json',
                            '--username', test_user, '--db', 'icfj', '--archive', '--gzip', '--drop',
                            '--restoreDbUsersAndRoles'], stdin=data, stdout=log, stderr=subprocess.STDOUT, check=True)
        state['phase'] = 'verify-restored'
        write_status(folder, state)
        restored = snapshot(name, test_user, test_password, folder / 'restored.log')
        (folder / 'restored.json').write_text(json.dumps(restored, indent=2))
        if restored != before:
            raise RuntimeError('Restored content, indexes, users or permissions differ')
    state.update(state='verified', phase='complete', archive=archive.name, sha256=manifest['sha256'],
                 bytes=manifest['bytes'], collections=len(before['collections']),
                 licenses=next(item['count'] for item in before['collections'] if item['name'] == 'licenses'),
                 contentHashesMatch=True, indexesMatch=True, usersAndRolesMatch=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/var/backups/minada/daily'))
    parser.add_argument('--container', default='amazonia-minada-back-database-1')
    parser.add_argument('--backup-command', type=Path, default=Path('/usr/local/sbin/minada-mongodb-backup.py'))
    parser.add_argument('--keep', type=int, default=14)
    parser.add_argument('--failed-keep', type=int, default=3)
    parser.add_argument('--min-free-gib', type=float, default=4)
    args = parser.parse_args()
    if os.geteuid() != 0 or args.keep < 1 or args.failed_keep < 1 or args.min_free_gib <= 0:
        parser.error('Root and positive retention/space values are required')
    os.umask(0o077)
    args.root = args.root.absolute()
    private_directory(args.root)
    lock = open('/run/lock/minada-mongodb-backup.lock', 'a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another Minada backup is running')
    def interrupted(signum, frame):
        raise RuntimeError('Backup interrupted')
    for signum in [signal.SIGTERM, signal.SIGINT]:
        signal.signal(signum, interrupted)
    cleanup_stale()
    token = uuid.uuid4().hex
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + token
    folder = args.root / run_id
    private_directory(folder)
    state = {'schema': 1, 'job': JOB, 'run': run_id, 'token': token, 'state': 'running'}
    write_status(folder, state)
    error = None
    try:
        perform(args, folder, state)
    except Exception as exception:
        error = exception
        state.update(state='failed', errorType=type(exception).__name__)
        # Exception text is written only to the protected file, never the journal.
        (folder / 'failure.log').write_text(str(exception) + '\n')
    finally:
        try:
            cleanup_stale()
        except Exception as exception:
            error = exception
            state.update(state='failed', cleanupFailed=True, errorType=type(exception).__name__)
        state['finishedAt'] = datetime.now(timezone.utc).isoformat()
        write_status(folder, state)
    if state['state'] == 'verified':
        state['removedVerified'] = prune(args.root, 'verified', args.keep)
        (args.root / 'latest-verified.json').write_text(json.dumps(state, indent=2) + '\n')
    state['removedFailed'] = prune(args.root, 'failed', args.failed_keep)
    write_status(folder, state)
    print(json.dumps(state), flush=True)
    if error:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
