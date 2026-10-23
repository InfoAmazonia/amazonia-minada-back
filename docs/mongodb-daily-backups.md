# Daily MongoDB backups and restore verification

The production timer runs at **04:00 America/Sao_Paulo**, independently of the
server's Europe/Berlin timezone. The normal 00:30 and 01:30 imports run first.
Each successful run retains the **14 most recent verified backups** (normally
14 days). Keep the three most recent failed runs for diagnosis. Failed runs do
not remove verified backups. Existing manual and migration backups are untouched.

## What each run verifies

1. Reject overlapping backup runs using a global `flock`. Reject an active import
   lock, leftover `_importing` collection, missing required data or empty licenses.
2. Capture collection counts, content hashes, ordered index definitions, application
   users and custom roles/privileges. Run the existing private backup command,
   which includes `icfj` users and roles. Validate the archive SHA-256 and compare
   the source snapshot again to reject writes during the dump.
3. Restore the entire archive **including indexes, users and roles** into MongoDB
   using the exact source image, with no network, no published ports, a separate
   labeled volume, random temporary credentials, 1 CPU and 2 GiB RAM. Compare
   restored content hashes, counts, index definitions, users and permissions.
4. Mark the run `verified` only when all checks and test-resource cleanup succeed.
   Then apply retention. Recognized run markers and directory names are required;
   symlinks and unrelated folders are ignored. Only labeled restore-test containers
   and volumes with exact matching names can be cleaned up. A subsequent run cleans
   owned leftovers from an interrupted test under the same global lock.

MongoDB is standalone: this is not an oplog snapshot. The source comparisons
require a quiet dump window; detected writes fail the run and preserve older
verified backups. `dbHash` reads data under database read locks, which can delay
writers; each hash command has a 60-second limit (see the [MongoDB documentation](https://www.mongodb.com/docs/manual/reference/command/dbhash/)). The overnight schedule avoids the application's usual write jobs.

## Installation

Requires root, Docker, Python 3.11+, systemd with timezone-aware calendars, and
`/usr/local/sbin/minada-mongodb-backup.py` from the preceding administrator-rotation
change. Install `ops/mongodb-daily-backup.py` at
`/usr/local/sbin/minada-mongodb-daily.py`, owned by root, mode 0700. Install the
service and timer from `ops/systemd/` under `/etc/systemd/system/` (mode 0644).
Create `/var/backups/minada/daily`, owned by root, mode 0700. Then:

```sh
systemd-analyze verify /etc/systemd/system/minada-mongodb-backup.{service,timer}
systemctl daemon-reload
systemctl start minada-mongodb-backup.service
# Enable only after the first service run reports verified and Result=success.
systemctl enable --now minada-mongodb-backup.timer
```

The service retries failed runs at 30-minute intervals, at most three starts
within three hours. It has a 45-minute timeout, private temporary storage, a
restrictive umask and limited host filesystem writes. The timer persists across
reboots and can catch up a missed execution. Four GiB of free disk space are
required before starting a dump/restore cycle.

## Credentials and results

The scripts read the current administrator credential directly from the local
MongoDB container. No password is stored in the timer/unit, command arguments,
repository or journal. Tool configuration and temporary restore credentials are
root-only and deleted with their temporary directory/container. Archives include
application credential hashes; treat all backups, logs and snapshots as private.
Generated files use mode 0600 inside mode-0700 directories.

Each run directory contains its archive, checksum manifest, protected command and
restore logs, source/restored verification snapshots and `status.json`.
`/var/backups/minada/daily/latest-verified.json` identifies the newest verified run.
A failed run returns a nonzero exit status and does not update that pointer.

```sh
systemctl list-timers minada-mongodb-backup.timer
systemctl show minada-mongodb-backup.service -p Result -p ExecMainStatus
journalctl -u minada-mongodb-backup.service --no-pager -n 30
cat /var/backups/minada/daily/latest-verified.json
# Manual execution uses the same verification, lock and retention policy:
systemctl start minada-mongodb-backup.service
```

No email/chat notification destination is configured. Failures are recorded in
systemd and the protected run logs. These backups are on the same server; copying
them to an independent destination requires a separate storage configuration.

To disable the schedule without deleting backups, stop/disable the timer and stop
the service. The deployment operation saves prior files and includes a rollback
script that restores the previous scheduling state and preserves backup archives.
Restoring application data to production is always a separate explicit operation.

## Validation

Run `python3 ops/test_mongodb_daily_backup.py` for retention and path-safety tests.
Before enabling the timer, run the complete candidate against a separate private
backup directory. Also verify overlap rejection, failure propagation without
changing `latest-verified.json`, cleanup of isolated resources, and a successful
run through the installed systemd service. Confirm the public site, APIs and CSV
before/after installation.
