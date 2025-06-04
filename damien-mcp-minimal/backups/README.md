# Backups Directory

This directory contains backups created during deployment and configuration changes.

Backups are created automatically by the deployment and rollback scripts:
- `deploy-minimal.sh`: Creates backups before making changes
- `rollback-minimal.sh`: Restores backups

## Backup Format

Backups are stored with the following naming convention:

```
damien_mcp_backup_YYYYMMDD_HHMMSS_file_type
```

Where:
- `YYYYMMDD_HHMMSS` is the timestamp
- `file_type` indicates the type of backup file

## Listing Backups

To list available backups:

```bash
npm run rollback:list
# or
./scripts/rollback-minimal.sh --list
```

## Restoring Backups

To restore the most recent backup:

```bash
npm run rollback
# or 
./scripts/rollback-minimal.sh --latest
```

To restore a specific backup:

```bash
./scripts/rollback-minimal.sh --backup-id YYYYMMDD_HHMMSS
```

This directory is included in the repository, but backup files are excluded via .gitignore.
