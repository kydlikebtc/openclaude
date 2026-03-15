#!/bin/sh
# Redis Sentinel entrypoint：将模板中的环境变量替换为实际值后启动 sentinel
set -e

CONF_FILE="/etc/redis/sentinel.conf"

# 用实际密码替换模板占位符
sed "s/\${REDIS_PASSWORD}/${REDIS_PASSWORD}/g" /etc/redis/sentinel.conf.template > "$CONF_FILE"

exec redis-sentinel "$CONF_FILE"
