# MongoDB administrator rotation and backups

Applications use their own limited users; never put the administrator URI back in
backend/importer environments. The administrator credential is operational only.

## Backup

Install `ops/mongodb-backup.py` as `/usr/local/sbin/minada-mongodb-backup.py`, owned
by root, mode 0700. Run with Python 3.11+ and Docker administrative access:

```sh
python3 /usr/local/sbin/minada-mongodb-backup.py --directory /var/backups/minada/manual
```

The directory must be mode 0700. The script reads the current database container
credential, writes a temporary mode-0600 tool configuration inside the container,
and removes it on exit. Passwords do not appear in command arguments. The archive
contains `icfj`, its users and custom roles; treat it and its logs as secrets.
A successful backup is renamed atomically and accompanied by a SHA-256 manifest.
A failed dump returns a nonzero status and removes its incomplete archive.
This command does not install a backup schedule or delete historical backups.

## Rotation procedure

1. Save the effective Compose configuration, private environment files, current
   administrator password and a fresh archive under a root-only operation folder.
2. In a disposable database using the same image, restore the archive **with
   indexes and `--db icfj --restoreDbUsersAndRoles`**. Verify collection counts,
   rotate its administrator with `db.changeUserPassword`, reject old credentials,
   and recreate only that test container with its updated bootstrap environment.
3. Back up and restore the rotated test database, then test password rollback.
4. Prepare and privately validate the production Compose environment with the new
   password. Change the existing MongoDB user explicitly; changing only
   `MONGO_INITDB_ROOT_PASSWORD` does not rotate an existing database user.
5. Immediately verify a fresh connection with the new password and reject the old
   one. Recreate only the database service to synchronize its bootstrap environment.
   Preserve the pinned image, existing volumes, private address and localhost port.
   Never use `compose down` or remove production volumes.
6. Repeat the backup and restore test with the actual post-rotation archive.
   Check application permissions, site, APIs and all CSV variants.

Backups and data restore helpers that read the database container environment
use the rotated credential automatically. Keep the previous password solely in
the protected operation folder for emergency rollback. Historical configuration
snapshots contain retired credentials: do not replay them blindly. Old rollback
scripts may reinstate obsolete application administrator credentials; use the
current operation's rollback instead, keeping application users restricted.

For rollback, authenticate with the new credential, explicitly restore the old
administrator password, restore the saved operational environment, and recreate
only the database service. Repeat authentication, data and application checks.
Retire the rollback credential once the rollback window is closed.
