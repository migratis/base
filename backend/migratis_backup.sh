#!/bin/bash
# to place in /var/backups/pg_backups
if ! command -v bzip2 &> /dev/null
then apt-get update && apt-get install bzip2
fi
pg_dump -p 5433 -U postgres -d migratis | bzip2 > /var/backups/pg_backups/pg_dump_migratis_`date +%Y-%m-%d-%H`.sql.bz2
pg_dump -p 5433 -U postgres -d migratis_dev | bzip2 > /var/backups/pg_backups/pg_dump_pg_dump_migratis_dev_`date +%Y-%m-%d-%H`.sql.bz2
