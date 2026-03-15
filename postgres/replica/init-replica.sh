#!/bin/bash
# PostgreSQL Replica 初始化：通过 pg_basebackup 从主节点同步数据
# 在 replica 容器 entrypoint 前调用
set -e

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
REPLPASSWORD="${POSTGRES_REPLICATION_PASSWORD}"
PRIMARY_HOST="${POSTGRES_PRIMARY_HOST:-postgres-primary}"
PRIMARY_PORT="${POSTGRES_PRIMARY_PORT:-5432}"

echo "Waiting for primary PostgreSQL at $PRIMARY_HOST:$PRIMARY_PORT..."
until pg_isready -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$POSTGRES_USER"; do
    sleep 2
done

echo "Primary is ready. Starting base backup..."
rm -rf "$PGDATA"/*

PGPASSWORD="$REPLPASSWORD" pg_basebackup \
    -h "$PRIMARY_HOST" \
    -p "$PRIMARY_PORT" \
    -U replicator \
    -D "$PGDATA" \
    -Fp -Xs -P -R

# -R 自动写入 standby.signal + postgresql.auto.conf 的 primary_conninfo
echo "Base backup complete. Replica initialized."
