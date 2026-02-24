FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run.py .

# 创建数据目录
RUN mkdir -p data

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "run.py"]
