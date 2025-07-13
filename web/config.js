// 前端配置
const AppConfig = {
  // API 端点
  API_BASE_URL: process.env.NODE_ENV === 'production' 
    ? 'https://api.actuarial-platform.com' 
    : 'http://localhost:5000',
  
  // 图表配置
  CHART_CONFIG: {
    displayModeBar: true,
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: 'actuarial_chart',
      height: 800,
      width: 1200,
      scale: 2
    }
  },
  
  // 默认模型参数
  DEFAULT_MODEL_PARAMS: {
    forecastYears: 5,
    confidenceLevel: 95,
    simulations: 1000
  },
  
  // 主题配置
  THEMES: {
    light: {
      primary: '#2c3e50',
      secondary: '#f1c40f',
      background: '#ecf0f1',
      text: '#34495e'
    },
    dark: {
      primary: '#3498db',
      secondary: '#f39c12',
      background: '#2c3e50',
      text: '#ecf0f1'
    }
  },
  
  // 精算师模式快捷键
  ACTUARY_SHORTCUTS: {
    'F1': 'toggleSOAStandards',
    'Ctrl+E': 'exportReport',
    'Alt+V': 'validateModel'
  }
};

export default AppConfig;
