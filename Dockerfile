# 使用Alpine Linux作为基础镜像，确保轻量化和高效率
FROM python:3.12-slim

# 将工作目录设置为/app
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码到容器中
COPY . .

RUN mkdir -p /tmp/logs && chmod 777 /tmp/logs

# 暴露端口
EXPOSE 7860

# 启动服务时直接运行Python命令
CMD ["python", "main.py"]
