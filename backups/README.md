# Backups

This directory stores documentation only. Real database dumps and certificates must live outside the repository (object storage, S3, encrypted file server, etc.).

1. Upload every new backup to the external storage first.
2. Record the link and metadata in `BACKUP_QUICK_START.md` (or another docs file).
3. Do not place any binary archives here.

Keeping the repo light avoids shipping sensitive data by mistake.
