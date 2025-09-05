import AppConfig from '../config.js';

const API = (p) => `${AppConfig.API_BASE_URL}/api${p}`;

window.loadPage = function(page) {
  const container = document.getElementById('main-content');
  fetch(`${page}.html`).then(r=>r.text()).then(html=>{ container.innerHTML = html; initPage(page); });
};

function initPage(page){
  if(page === 'analysis') initAnalysis();
}

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

  // dataset select
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
    const res = await fetch(API('/clean-data'), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({data: window.__DATA__||[], options:{}})});
    const json = await res.json(); window.__DATA__ = json.data || window.__DATA__;
  });

  // report
  document.getElementById('generateReportBtn')?.addEventListener('click', async ()=>{
    const res = await fetch(API('/generate-report'), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({data: window.__DATA__||[]})});
    const json = await res.json();
    const el = document.getElementById('reportContent');
    if(el){ el.innerHTML = `<pre>${JSON.stringify(json.report, null, 2)}</pre>`; document.getElementById('reportContainer').style.display='block'; }
  });
}

// boot
document.addEventListener('DOMContentLoaded', ()=>{
  // load nav then index
  fetch('navigation.html').then(r=>r.text()).then(html=>{ document.getElementById('navigation').innerHTML = html; loadPage('index'); });
});
