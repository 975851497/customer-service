.PHONY: run gen smoke init_db clean

# 启动服务
run:
	uv run python main.py

# 安装依赖
install:
	uv sync

# 清理缓存
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
