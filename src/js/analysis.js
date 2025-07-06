// 全局变量
let selectedModel = null;
let selectedDataset = null;
let analysisResults = null;

$(document).ready(function() {
    // 初始化事件监听
    initEventListeners();
    // 加载可用数据集
    loadAvailableDatasets();
    // 加载标准模型
    loadStandardModels();
});

function initEventListeners() {
    // 模型选择事件
    $('.model-card').click(function() {
        $('.model-card').removeClass('border-primary');
        $(this).addClass('border-primary');
        selectedModel = $(this).data('model-id');
        $('#selectedModelName').text($(this).find('.card-title').text());
        showToast(`已选择模型: ${$(this).find('.card-title').text()}`, 'success');
        
        // 如果已加载数据集，启用运行分析按钮
        if (selectedDataset) {
            $('#runAnalysisBtn').prop('disabled', false);
        }
    });
    
    // 数据集选择事件
    $('#datasetSelect').change(function() {
        selectedDataset = $(this).val();
        if (selectedModel) {
            $('#runAnalysisBtn').prop('disabled', false);
        }
    });
    
    // 运行分析按钮
    $('#runAnalysisBtn').click(function() {
        runAnalysis();
    });
    
    // 精算师模式切换
    $('#actuaryModeToggle').change(function() {
        if ($(this).is(':checked')) {
            $('.actuary-only').show();
            $('body').addClass('actuary-mode');
            showToast('已进入精算师模式', 'success');
        } else {
            $('.actuary-only').hide();
            $('body').removeClass('actuary-mode');
            showToast('已退出精算师模式', 'info');
        }
    });
}

// 加载标准模型
function loadStandardModels() {
    $.ajax({
        url: '/api/models',
        type: 'GET',
        success: function(response) {
            const $container = $('#standardModels');
            response.models.forEach(model => {
                $container.append(`
                    <div class="col-md-6 mb-3">
                        <div class="card model-card" data-model-id="${model.id}">
                            <div class="card-body">
                                <h5 class="card-title">${model.name}</h5>
                                <p class="card-text text-muted small">${model.description}</p>
                                <div class="d-flex justify-content-between">
                                    <span class="badge bg-primary">${model.type}</span>
                                    <button class="btn btn-sm btn-outline-secondary" 
                                            data-bs-toggle="modal" 
                                            data-bs-target="#modelDetailsModal"
                                            data-model-id="${model.id}">
                                        <i class="fas fa-info-circle"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `);
            });
            
            // 绑定模型详情查看事件
            $('[data-bs-target="#modelDetailsModal"]').click(function() {
                const modelId = $(this).data('model-id');
                loadModelDetails(modelId);
            });
        }
    });
}

// 加载模型详情
function loadModelDetails(modelId) {
    $.ajax({
        url: `/api/model/${modelId}`,
        type: 'GET',
        success: function(response) {
            $('#modelDetailsTitle').text(response.name);
            $('#modelDetailsBody').html(`
                <h6>模型公式</h6>
                <p class="formula">${response.formula}</p>
                <h6 class="mt-3">参数说明</h6>
                <ul>
                    ${response.parameters.map(p => `<li><strong>${p.name}</strong>: ${p.description}</li>`).join('')}
                </ul>
                <h6 class="mt-3">适用场景</h6>
                <p>${response.applicability}</p>
                <h6 class="mt-3">SOA参考</h6>
                <p>${response.soaReference}</p>
            `);
        }
    });
}

// 加载可用数据集
function loadAvailableDatasets() {
    $.ajax({
        url: '/api/datasets',
        type: 'GET',
        success: function(response) {
            const $select = $('#datasetSelect');
            $select.empty();
            response.datasets.forEach(dataset => {
                $select.append(`<option value="${dataset.id}">${dataset.name} (${dataset.size})</option>`);
            });
        }
    });
}

// 运行分析
function runAnalysis() {
    if (!selectedModel || !selectedDataset) {
        showToast('请先选择模型和数据集', 'warning');
        return;
    }
    
    showLoading();
    
    const analysisOptions = {
        confidenceLevel: $('#confidenceLevel').val(),
        forecastYears: $('#forecastYears').val(),
        randomSimulations: $('#randomSimulations').val(),
        diagnostics: $('#includeDiagnostics').is(':checked')
    };
    
    $.ajax({
        url: '/api/analyze',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            modelId: selectedModel,
            datasetId: selectedDataset,
            options: analysisOptions
        }),
        success: function(response) {
            analysisResults = response;
            renderAnalysisResults();
            $('#exportResultsBtn').prop('disabled', false);
            $('#saveToComparisonBtn').prop('disabled', false);
            hideLoading();
            showToast('分析完成!', 'success');
        }
    });
}

// 渲染分析结果
function renderAnalysisResults() {
    // 1. 参数估计
    renderParameterEstimates();
    
    // 2. 预测结果
    renderForecastResults();
    
    // 3. 模型诊断
    renderModelDiagnostics();
    
    // 4. 生成代码
    renderAnalysisCode();
}

// 渲染参数估计
function renderParameterEstimates() {
    // 实现参数估计表格渲染
}

// 渲染预测结果
function renderForecastResults() {
    // 实现预测图表渲染
}

// 渲染模型诊断
function renderModelDiagnostics() {
    // 实现诊断信息渲染
}

// 渲染分析代码
function renderAnalysisCode() {
    // 实现代码生成
}

// 显示加载动画
function showLoading() {
    $('#loadingOverlay').show();
}

// 隐藏加载动画
function hideLoading() {
    $('#loadingOverlay').hide();
}

// 显示通知
function showToast(message, type) {
    // 实现toast通知
}
