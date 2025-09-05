import AppConfig from '../config.js';

const API = (p) => `${AppConfig.API_BASE_URL}/api${p}`;

window.loadPage = function(page) {
  const container = document.getElementById('main-content');
  fetch(`${page}.html`)
    .then(r => r.text())
    .then(html => {
      container.innerHTML = html;
      initPage(page);
    });
};

function initPage(page){
  if(page === 'analysis') initAnalysis();
  if(page === 'history') initHistory();
  if(page === 'model_lab') initModelLab();
  if(page === 'sensitivity') initSensitivity();
  if(page === 'cases') initCases();
  if(page === 'help') initHelp();
}

/* -------------------------
   Analysis Page
------------------------- */
function initAnalysis(){
  // load models
  fetch(API('/models')).then(r=>r.json()).then(({models})=>{
    const box = document.getElementById('standardModels');
    if(!box) return;
    models.forEach(m=>{
      const div = document.createElement('div');
      div.className = 'col-md-6 mb-3';
      div.innerHTML = `<div class="card model-card"><div class="card-body">
        <h5 class="card-title">${m.name}</h5><p class="small text-muted">${m.description}</p>
        <span class="badge bg-primary">${m.type}</span></div></div>`;
      box.appendChild(div);
    });
  });

  // dataset select (in-memory + uploaded)
  fetch(API('/datasets')).then(r=>r.json()).then(({datasets})=>{
    const sel = document.getElementById('datasetSelect');
    if(!sel) return;
    sel.innerHTML = datasets.map(d=>`<option value="${d.id}">${d.name} (${d.size})</option>`).join('');
  });

  // file upload
  const up = document.getElementById('customFile');
  if(up){
    up.addEventListener('change', async (e)=>{
      const file = e.target.files[0]; if(!file) return;
      const fd = new FormData(); fd.append('file', file);
      const res = await fetch(API('/upload-custom-data'), { method:'POST', body: fd });
      const json = await res.json(); window.__DATA__ = json.data || [];
      document.getElementById('generateReportBtn')?.removeAttribute('disabled');
      document.getElementById('cleanDataBtn')?.removeAttribute('disabled');
    });
  }

  // clean
  document.getElementById('cleanDataBtn')?.addEventListener('click', async ()=>{
    const res = await fetch(API('/clean-data'), {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({data: window.__DATA__||[], options:{}})
    });
    const json = await res.json(); window.__DATA__ = json.data || window.__DATA__;
  });

  // report
  document.getElementById('generateReportBtn')?.addEventListener('click', async ()=>{
    const res = await fetch(API('/generate-report'), {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({data: window.__DATA__||[]})
    });
    const json = await res.json();
    const el = document.getElementById('reportContent');
    if(el){
      el.innerHTML = `<pre>${JSON.stringify(json.report, null, 2)}</pre>`;
      document.getElementById('reportContainer').style.display='block';
    }
  });
}

/* -------------------------
   History Page
------------------------- */
function initHistory(){
  const container = document.getElementById('historyContent');
  if(!container) return;

  container.innerHTML = `
    <div class="mb-3">
      <label for="historySource" class="form-label">选择数据源</label>
      <select id="historySource" class="form-select">
        <option value="CDC_RAW">CDC Raw Dataset</option>
        <option value="HMD_RAW">HMD Raw Dataset</option>
        <option value="SOA_CASE">SOA Case (CDC raw demo)</option>
      </select>
      <button id="loadHistoryBtn" class="btn btn-primary mt-2">加载数据</button>
    </div>
    <div id="historyResult" class="mt-3"></div>
  `;

  document.getElementById('loadHistoryBtn').addEventListener('click', async ()=>{
    const src = document.getElementById('historySource').value;
    const res = await fetch(API('/fetch-data'), {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({source: src})
    });
    const json = await res.json();
    const target = document.getElementById('historyResult');
    target.innerHTML = `<pre>${JSON.stringify(json.data.slice(0,20), null, 2)}</pre>`;
  });
}

/* -------------------------
   Model Lab Page
------------------------- */
function initModelLab(){
  document.getElementById('modelLabContent').innerHTML = "<em>模型实验室功能开发中…</em>";
}

/* -------------------------
   Sensitivity Page
------------------------- */
function initSensitivity(){
  document.getElementById('sensitivityContent').innerHTML = "<em>敏感性测试功能开发中…</em>";
}

/* -------------------------
   Cases Page
------------------------- */
function initCases(){
  const container = document.getElementById('casesContent');
  if(!container) return;

  container.innerHTML = `
    <div class="mb-3">
      <label for="caseSource" class="form-label">选择案例数据源</label>
      <select id="caseSource" class="form-select">
        <option value="SOA_CASE">SOA Case (CDC raw demo)</option>
        <option value="CDC_RAW">CDC Raw Dataset</option>
        <option value="HMD_RAW">HMD Raw Dataset</option>
      </select>
      <button id="runCaseBtn" class="btn btn-success mt-2">运行案例</button>
    </div>
    <div id="caseResult" class="mt-3"></div>
  `;

  document.getElementById('runCaseBtn').addEventListener('click', async ()=>{
    const src = document.getElementById('caseSource').value;
    const res = await fetch(API('/fetch-data'), {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({source: src})
    });
    const json = await res.json();
    const target = document.getElementById('caseResult');
    target.innerHTML = `<pre>${JSON.stringify(json.data.slice(0,20), null, 2)}</pre>`;
  });
}

/* -------------------------
   Help Page
------------------------- */
function initHelp(){
  const el = document.getElementById('helpContent');
  if(el) el.innerHTML = "<em>帮助文档加载中…</em>";
}

/* -------------------------
   Boot
------------------------- */
document.addEventListener('DOMContentLoaded', ()=>{
  fetch('navigation.html')
    .then(r=>r.text())
    .then(html=>{
      document.getElementById('navigation').innerHTML = html;
      loadPage('index');
    });
});
