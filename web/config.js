// Picks API from env override or default localhost; supports Pages via window.__API_BASE__
const AppConfig = {
  API_BASE_URL: (window.__API_BASE__ || '').replace(/\/$/, '') || 'http://localhost:5000',
  CHART_CONFIG: { displayModeBar: true, responsive: true, displaylogo: false }
};
export default AppConfig;
