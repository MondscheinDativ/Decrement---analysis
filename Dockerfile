# 基础镜像：预装 R + 常用系统依赖
FROM rocker/tidyverse:4.3.0  

# 设置工作目录
WORKDIR /app

# 复制依赖文件到容器
COPY requirements.txt .

# 安装 Python 环境
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# 安装 R 包（用 rocker 镜像已预装的依赖，避免编译问题）
RUN R -e 'install.packages("demography", repos = "https://cran.rstudio.com/")'

# 复制测试文件到容器
COPY test_actuarial_platform.py .

# 定义默认命令：运行测试
CMD ["pytest", "test_actuarial_platform.py", "-v"]
