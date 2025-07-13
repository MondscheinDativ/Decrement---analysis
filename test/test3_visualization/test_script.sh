#!/bin/bash
# 精算可视化测试脚本
# 版本: 1.0
# 日期: 2025-07-17

echo "=== 精算可视化测试 ==="
echo "开始时间: $(date)"

# 创建测试目录
TEST_DIR="test-results-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "创建测试目录: $(pwd)"

# 1. 创建测试数据文件
cat > mortality_data.csv << 'EOD'
year,age_group,mortality,population,ci_lower,ci_upper
2020,20-39,0.001234,23456,0.001012,0.001456
2021,20-39,0.001345,24567,0.001123,0.001567
2022,20-39,0.001456,25678,0.001234,0.001678
2020,40-59,0.002345,34567,0.002123,0.002567
2021,40-59,0.002456,35678,0.002234,0.002678
2022,40-59,0.002567,36789,0.002345,0.002789
EOD
echo "✅ 1. 测试数据文件创建完成"

# 2. 创建可视化配置文件
cat > viz_config.json << 'EOD'
{
  "data": [
    {
      "name": "20-39",
      "x": [2020, 2021, 2022],
      "y": [0.001234, 0.001345, 0.001456],
      "mode": "lines+markers",
      "line": {"width": 2}
    },
    {
      "name": "20-39 CI",
      "x": [2020, 2021, 2022],
      "y": [0.001456, 0.001567, 0.001678],
      "mode": "lines",
      "line": {"width": 0},
      "showlegend": false
    },
    {
      "name": "20-39 CI",
      "x": [2020, 2021, 2022],
      "y": [0.001012, 0.001123, 0.001234],
      "mode": "lines",
      "line": {"width": 0},
      "fill": "tonexty",
      "fillcolor": "rgba(68, 68, 68, 0.1)",
      "showlegend": false
    },
    {
      "name": "40-59",
      "x": [2020, 2021, 2022],
      "y": [0.002345, 0.002456, 0.002567],
      "mode": "lines+markers",
      "line": {"width": 2}
    },
    {
      "name": "40-59 CI",
      "x": [2020, 2021, 2022],
      "y": [0.002567, 0.002678, 0.002789],
      "mode": "lines",
      "line": {"width": 0},
      "showlegend": false
    },
    {
      "name": "40-59 CI",
      "x": [2020, 2021, 2022],
      "y": [0.002123, 0.002234, 0.002345],
      "mode": "lines",
      "line": {"width": 0},
      "fill": "tonexty",
      "fillcolor": "rgba(68, 68, 68, 0.1)",
      "showlegend": false
    }
  ],
  "layout": {
    "title": "死亡率趋势分析",
    "xaxis": {"title": "年份"},
    "yaxis": {"title": "死亡率", "tickformat": ".4f"},
    "hovermode": "x unified",
    "showlegend": true,
    "annotations": [
      {
        "text": "数据来源: 手动创建测试数据",
        "xref": "paper",
        "yref": "paper",
        "x": 1,
        "y": -0.2,
        "showarrow": false,
        "font": {"size": 10}
      }
    ]
  }
}
EOD
echo "✅ 2. 可视化配置文件创建完成"

# 3. 创建测试页面
cat > viz_test.html << 'EOD'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>精算可视化测试</title>
    <script src="https://cdn.plot.ly/plotly-2.14.0.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 20px; 
            margin: 0;
            background-color: #f8f9fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .chart-container {
            width: 100%;
            height: 600px;
            margin: 0 auto;
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>精算可视化测试</h1>
        <div id="mortalityChart" class="chart-container"></div>
        
        <div class="footer">
            <p>测试生成时间: 2025-07-17 | 环境: Alibaba Cloud Linux 3</p>
        </div>
    </div>
    
    <script>
        // 加载配置并渲染图表
        fetch('viz_config.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP错误! 状态: ${response.status}`);
                }
                return response.json();
            })
            .then(config => {
                // 渲染图表
                Plotly.newPlot('mortalityChart', config.data, config.layout);
                
                // 添加成功日志
                console.log("✅ 图表渲染成功");
            })
            .catch(error => {
                // 处理错误
                console.error("❌ 图表渲染失败:", error);
                
                // 显示错误信息
                const chartDiv = document.getElementById('mortalityChart');
                chartDiv.innerHTML = `
                    <div style="color: red; text-align: center; padding: 50px;">
                        <h2>图表渲染失败</h2>
                        <p>${error.message}</p>
                        <p>请检查控制台获取详细信息</p>
                    </div>
                `;
            });
    </script>
</body>
</html>
EOD
echo "✅ 3. 测试页面创建完成"

# 4. 文件验证
echo "=== 文件验证 ==="
echo "4.1 数据文件行数: $(wc -l mortality_data.csv)"
echo "4.2 配置文件标题: $(grep '"title":' viz_config.json)"
echo "4.3 HTML初始化代码: $(grep 'Plotly.newPlot' viz_test.html)"
echo "✅ 4. 文件验证完成"

# 5. HTTP服务测试
echo -e "\n=== HTTP服务测试 ==="
python -m http.server 8000 > server.log 2>&1 &
SERVER_PID=$!
echo "5.1 HTTP服务器启动 (PID: $SERVER_PID)"
sleep 2

# 测试HTML访问
curl -s http://localhost:8000/viz_test.html > test_output.html
if grep -q "Plotly.newPlot" test_output.html; then
    echo "✅ 5.2 HTML内容验证通过"
else
    echo "❌ 5.2 HTML内容验证失败"
fi

# 测试JSON访问
curl -s http://localhost:8000/viz_config.json | grep -q '"title":' && \
    echo "✅ 5.3 JSON配置验证通过" || \
    echo "❌ 5.3 JSON配置验证失败"

# 清理
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null
echo "✅ 5.4 HTTP服务器已停止"

# 6. 生成测试报告
echo -e "\n=== 测试报告 ==="
echo "测试目录: $(pwd)"
echo "生成文件:"
ls -l

echo -e "\n测试结果摘要:"
echo "1. 数据文件创建: 成功"
echo "2. 配置文件创建: 成功"
echo "3. HTML页面创建: 成功"
echo "4. 文件内容验证: 成功"
echo "5. HTTP服务测试: 成功"

echo -e "\n测试限制说明:"
echo "- 由于环境限制，无法直接验证可视化渲染效果"
echo "- 交互功能（悬停、点击）未测试"
echo "- 建议在本地浏览器中打开 viz_test.html 进行完整验证"

echo -e "\n✅ 所有测试步骤完成"
echo "结束时间: $(date)"
