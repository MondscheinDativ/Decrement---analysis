# CentOS Flask 网站部署套件

这是一个在 CentOS 服务器上快速部署 Flask 网站的工具包，使用 Podman 容器化技术。

## 功能特点

- 一键部署 Flask 网站
- 容器化运行应用
- 自动配置系统服务（开机自启）
- 健康检查脚本
- 应用管理工具
- 防火墙自动配置

## 快速开始

### 前提条件
- CentOS 7/8 服务器
- SSH 访问权限

### 部署步骤

1. 将项目上传到服务器
   ```bash
   scp -r my_webapp/ 用户名@服务器IP地址:~
   ```

2. 连接到服务器
   ```bash
   ssh 用户名@服务器IP地址
   ```

3. 进入项目目录
   ```bash
   cd ~/my_webapp
   ```

4. 授予执行权限
   ```bash
   chmod +x deploy.sh
   ```

5. 执行部署脚本
   ```bash
   ./deploy.sh
   ```

### 验证部署

1. 检查容器状态
   ```bash
   ./manage_app.sh status
   ```

2. 运行健康检查
   ```bash
   ./test.sh
   ```

3. 访问网站
   ```
   http://服务器IP地址:5000
   ```

## 管理命令

| 操作       | 命令                     |
|------------|--------------------------|
| 启动应用   | `./manage_app.sh start`  |
| 停止应用   | `./manage_app.sh stop`   |
| 重启应用   | `./manage_app.sh restart`|
| 查看日志   | `./manage_app.sh logs`   |
| 检查状态   | `./manage_app.sh status` |
| 健康检查   | `./test.sh`              |

## 常见问题解决

### 端口冲突
```bash
# 检查端口占用
sudo netstat -tulnp | grep :5000

# 终止占用进程
sudo kill -9 <PID>
```

### 防火墙问题
```bash
# 开放5000端口
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

### SELinux 阻止访问
```bash
# 临时禁用（测试用）
sudo setenforce 0
```

## 备份与恢复

1. 备份应用
   ```bash
   tar -czvf webapp_backup_$(date +%Y%m%d).tar.gz ~/my_webapp
   ```

2. 恢复应用
   ```bash
   tar -xzvf webapp_backup_YYYYMMDD.tar.gz -C ~/
   ```

## 贡献指南

欢迎提交 Issue 或 Pull Request 改进本项目！

## 许可证

MIT License
````

## 使用说明

1. 将上述所有文件保存到本地 `my_webapp` 目录中
2. 上传整个目录到 GitHub 仓库
3. 在 CentOS 服务器上克隆仓库：
   ```bash
   git clone https://github.com/yourusername/my_webapp.git
   ```
4. 进入项目目录并运行部署脚本：
   ```bash
   cd my_webapp
   chmod +x deploy.sh
   ./deploy.sh
