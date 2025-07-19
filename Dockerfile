# 基础镜像：R + tidyverse + 常用系统依赖
FROM rocker/tidyverse:4.3.0

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
COPY test_actuarial_platform.py .

# 安装 Python 环境和构建工具
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    build-essential \
    liblapack-dev \
    libblas-dev \
    gfortran \
    libffi-dev \
    libssl-dev \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 包
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# 设置 R 用户库路径，避免写入 /usr/local/lib
ENV R_LIBS_USER=/app/.R/library

# 安装 demography 包到用户可写目录
RUN mkdir -p ${R_LIBS_USER} && \
    Rscript -e 'install.packages("demography", lib=Sys.getenv("R_LIBS_USER"), repos="https://cloud.r-project.org")'

# 默认运行测试
CMD ["pytest", "test_actuarial_platform.py", "-v"]
