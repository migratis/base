#!/bin/bash
find /var/backups/pg_backups/pg_migratis_dump_* -mtime +10 -exec rm {} \;
docker exec backend-db-1 bash -c '/var/backups/pg_backups/migratis_backup.sh'
#rsync -a -e 'ssh -p 32768' /var/backups/pg_backups sysbackup@91.167.56.86:~/villa/var/backups
