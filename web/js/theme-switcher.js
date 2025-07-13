// 主题切换功能
function initThemeSwitcher() {
  const themeToggle = document.getElementById('themeToggle');
  const currentTheme = localStorage.getItem('theme') || 'light';
  
  // 应用保存的主题
  document.documentElement.setAttribute('data-theme', currentTheme);
  if (themeToggle) {
    themeToggle.checked = currentTheme === 'dark';
  }
  
  // 切换主题事件
  if (themeToggle) {
    themeToggle.addEventListener('change', function() {
      const newTheme = this.checked ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }
}

// 初始化主题切换
document.addEventListener('DOMContentLoaded', initThemeSwitcher);
