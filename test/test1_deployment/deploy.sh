#!/bin/bash

# 安装必要软件
sudo yum install -y python3 python3-pip podman

# 创建项目目录
mkdir -p ~/my_webapp
cd ~/my_webapp

# 创建应用文件
cat > app.py << 'EOF'
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "🎉 恭喜！你的网站在 CentOS 上运行成功！"

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# 创建依赖文件
echo "flask" > requirements.txt

# 创建 Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
EOF

# 构建镜像
podman build -t my-web-app .

# 运行容器
podman run -d --name myapp -p 5000:5000 my-web-app

# 开放防火墙端口
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload

# 创建系统服务
cat << EOF | sudo tee /etc/systemd/system/myapp.service
[Unit]
Description=My WebApp Container
After=network.target

[Service]
Type=simple
User=$(whoami)
ExecStart=/usr/bin/podman run --name myapp -p 5000:5000 my-web-app
ExecStop=/usr/bin/podman stop myapp
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable myapp
sudo systemctl start myapp

# 创建测试脚本
cat > test.sh << 'EOF'
#!/bin/bash
echo "=== 网站健康检查 ==="
for i in {1..5}; do
  status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
  if [ "$status" = "200" ]; then
    echo "测试 $i/5: 成功 ✔ (状态码: $status)"
  else
    echo "测试 $i/5: 失败 ✘ (状态码: $status)"
  fi
  sleep 1
done
echo "=== 测试完成 ==="
EOF
chmod +x test.sh

# 创建管理脚本
cat > manage_app.sh << 'EOF'
#!/bin/bash
case "$1" in
  start)
    podman start myapp
    ;;
  stop)
    podman stop myapp
    ;;
  restart)
    podman restart myapp
    ;;
  logs)
    podman logs -f myapp
    ;;
  status)
    podman ps -a | grep myapp
    ;;
  *)
    echo "用法: $0 {start|stop|restart|logs|status}"
    exit 1
esac
EOF
chmod +x manage_app.sh

# 获取公网IP
SERVER_IP=$(curl -s ifconfig.me)

echo "========================================"
echo "🎉 部署完成！"
echo "网站地址: http://${SERVER_IP}:5000"
echo "健康检查: http://${SERVER_IP}:5000/health"
echo "管理命令: ./manage_app.sh [start|stop|restart|logs|status]"
echo "运行测试: ./test.sh"
echo "========================================"
