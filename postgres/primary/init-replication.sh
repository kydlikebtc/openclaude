#!/bin/bash
# PostgreSQL 主节点初始化：创建复制用户并配置 WAL 归档
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- 创建流式复制专用用户
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'replicator') THEN
            CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD '${POSTGRES_REPLICATION_PASSWORD}';
        END IF;
    END
    \$\$;
EOSQL

# pg_hba.conf 允许 replica 节点连接
echo "host replication replicator 0.0.0.0/0 scram-sha-256" >> "$PGDATA/pg_hba.conf"

# postgresql.conf 流式复制参数
cat >> "$PGDATA/postgresql.conf" <<EOF

# Streaming Replication (added by init-replication.sh)
wal_level = replica
max_wal_senders = 5
wal_keep_size = 256MB
wal_log_hints = on
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/wal_archive/%f && cp %p /var/lib/postgresql/wal_archive/%f'
EOF

# 刷新配置（不需要重启，pg_hba 改动需要 reload）
pg_ctl reload -D "$PGDATA" 2>/dev/null || true
