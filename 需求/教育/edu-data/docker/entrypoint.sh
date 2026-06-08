#!/bin/bash
set -e

echo "=== 等待 MySQL 就绪 ==="
until mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" --silent 2>/dev/null; do
  >&2 echo "MySQL 未就绪，等待 2 秒..."
  sleep 2
done

echo "MySQL 已就绪"

# 检查数据库是否已有数据（通过检查表是否存在）
TABLE_COUNT=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" \
  -N -B -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" = "0" ]; then
  echo "=== 初始化数据库 ==="
  uv run init_db.py

  echo "=== 生成业务数据 ==="
  uv run -m generate.main --profile full

  echo "=== 数据初始化完成 ==="
else
  echo "数据库已存在，跳过初始化"
fi

echo "=== 启动 FastAPI 服务 ==="
exec uv run -m app.main
