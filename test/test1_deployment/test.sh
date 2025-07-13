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
