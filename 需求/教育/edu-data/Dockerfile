FROM python:3.12-slim

# 安装系统依赖（MySQL 客户端用于健康检查，uv 包管理器）
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-mysql-client && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

WORKDIR /app

# 复制依赖文件并安装（利用 Docker 缓存）
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-dev

# 复制项目源码及启动脚本
COPY . /app
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
