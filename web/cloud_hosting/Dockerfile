# 微信云托管 Dockerfile
# 使用 Python 3.10 slim 镜像（云托管兼容）
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（用于编译某些 Python 包）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app.py .
COPY models/ ./models/

# 暴露端口（微信云托管要求暴露 80 端口）
EXPOSE 80

# 启动应用
CMD ["python", "app.py"]
