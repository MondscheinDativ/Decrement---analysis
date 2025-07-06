// analysis.js - 精算分析平台数据分析模块

// 全局变量
let selectedModel = null;
let selectedDataset = null;
let analysisResults = null;
let variableMappings = {};
let modelCache = {};
let analysisProgressInterval = null;

$(document).ready(function() {
    // 初始化事件监听
    initEventListeners();
    
    // 加载可用数据集
    loadAvailableDatasets();
    
    // 检查是否在精算师模式下
    checkActuaryMode();
    
    // 初始化模型描述
    updateModelDescription();
});

function initEventListeners() {
    // 模型类型变化
    $('#modelType').change(function() {
        if ($(this).val() === 'custom') {
            $('#standardModels').hide();
            $('#customModelOptions').show();
        } else {
            $('#standardModels').show();
            $('#customModelOptions').hide();
            updateModelDescription();
        }
    });

    // 标准模型选择变化
    $('#standardModelSelect').change(function() {
        updateModelDescription();
    });

    // 选择模型按钮
    $('#selectModelBtn').click(function() {
        selectModel();
    });

    // 数据集选择变化
    $('#datasetSelect').change(function() {
        loadDatasetVariables();
    });

    // 加载数据集按钮
    $('#loadDatasetBtn').click(function() {
        loadDataset();
    });

    // 运行分析按钮
    $('#runAnalysisBtn').click(function() {
        runAnalysis();
    });

    // 导出结果按钮
    $('#exportResultsBtn').click(function() {
        exportResults();
    });

    // 保存到对比按钮
    $('#saveToComparisonBtn').click(function() {
        saveToComparison();
    });

    // 复制代码按钮
    $('#copyCodeBtn').click(function() {
        copyCodeToClipboard();
    });
}

// 更新模型描述
function updateModelDescription() {
    const modelId = $('#standardModelSelect').val();
    
    // 检查缓存
    if (modelCache[modelId]) {
        $('#modelDescription').html(modelCache[modelId]);
        return;
    }
    
    showLoading();
    $.ajax({
        url: `/api/model-description/${modelId}`,
        type: 'GET',
        success: function(response) {
            // 缓存模型描述
            modelCache[modelId] = response.description;
            $('#modelDescription').html(response.description);
            hideLoading();
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`无法加载模型描述: ${error}`, 'error');
        }
    });
}

// 选择模型
function selectModel() {
    const modelType = $('#modelType').val();
    
    if (modelType === 'custom') {
        if (!validateCustomModel()) {
            return;
        }
        
        const modelName = $('#customModelName').val();
        const modelFormula = $('#customModelFormula').val();
        
        // 收集参数
        const parameters = [];
        $('#parameterInputs .input-group').each(function() {
            const paramName = $(this).find('.input-group-text').text();
            const initialValue = $(this).find('input').eq(0).val();
            const lowerBound = $(this).find('input').eq(1).val();
            const upperBound = $(this).find('input').eq(2).val();
            
            if (paramName && initialValue) {
                parameters.push({
                    name: paramName,
                    initialValue: parseFloat(initialValue),
                    lowerBound: lowerBound ? parseFloat(lowerBound) : null,
                    upperBound: upperBound ? parseFloat(upperBound) : null
                });
            }
        });
        
        selectedModel = {
            type: 'custom',
            name: modelName,
            formula: modelFormula,
            parameters: parameters,
            advancedOptions: $('#advancedOptions').val()
        };
    } else {
        selectedModel = {
            type: 'standard',
            modelId: $('#standardModelSelect').val(),
            name: $('#standardModelSelect option:selected').text(),
            advancedOptions: $('#advancedOptions').val()
        };
    }
    
    showToast(`已选择模型: ${selectedModel.name}`, 'success');
    
    // 如果已加载数据集，启用运行分析按钮
    if (selectedDataset) {
        $('#runAnalysisBtn').prop('disabled', false);
    }
}

// 验证自定义模型
function validateCustomModel() {
    const modelName = $('#customModelName').val().trim();
    const modelFormula = $('#customModelFormula').val().trim();
    
    if (!modelName) {
        showToast('请输入自定义模型名称', 'warning');
        return false;
    }
    
    if (!modelFormula) {
        showToast('请输入模型公式', 'warning');
        return false;
    }
    
    // 检查是否有参数
    const paramCount = $('#parameterInputs .input-group').length;
    if (paramCount === 0) {
        showToast('请至少添加一个模型参数', 'warning');
        return false;
    }
    
    // 验证参数是否完整
    let paramsValid = true;
    $('#parameterInputs .input-group').each(function() {
        const initialValue = $(this).find('input').eq(0).val();
        if (!initialValue) {
            paramsValid = false;
        }
    });
    
    if (!paramsValid) {
        showToast('请为所有参数填写初始值', 'warning');
        return false;
    }
    
    return true;
}

// 添加参数
function addParameter() {
    const paramCount = $('#parameterInputs .input-group').length;
    const paramLetter = String.fromCharCode(97 + paramCount); // a, b, c, ...
    
    $('#parameterInputs').append(`
        <div class="input-group mb-2">
            <span class="input-group-text">${paramLetter}</span>
            <input type="number" class="form-control" placeholder="初始值" step="0.001" required>
            <input type="number" class="form-control" placeholder="下限" step="0.001">
            <input type="number" class="form-control" placeholder="上限" step="0.001">
            <button class="btn btn-outline-danger" type="button" onclick="$(this).parent().remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `);
}

// 加载可用数据集
function loadAvailableDatasets() {
    showLoading();
    $.ajax({
        url: '/api/available-datasets',
        type: 'GET',
        success: function(response) {
            const $select = $('#datasetSelect');
            $select.empty();
            
            if (response.datasets.length === 0) {
                $select.append('<option value="">无可用的数据集</option>');
            } else {
                response.datasets.forEach(dataset => {
                    $select.append(`<option value="${dataset.id}">${dataset.name} (${dataset.rows}行)</option>`);
                });
                
                // 默认加载第一个数据集的变量
                if (response.datasets.length > 0) {
                    loadDatasetVariables();
                }
            }
            hideLoading();
        },
        error: function(xhr, status, error) {
            $('#datasetSelect').html('<option value="">加载数据集失败</option>');
            hideLoading();
            showToast(`加载可用数据集失败: ${error}`, 'error');
        }
    });
}

// 加载数据集变量
function loadDatasetVariables() {
    const datasetId = $('#datasetSelect').val();
    if (!datasetId) return;
    
    showLoading();
    $.ajax({
        url: `/api/dataset-variables/${datasetId}`,
        type: 'GET',
        success: function(response) {
            const $mappingDiv = $('#variableMapping');
            
            // 清除现有的映射行（保留标题）
            $mappingDiv.children().not(':first').remove();
            
            // 添加变量映射行
            if (response.modelVariables && response.modelVariables.length > 0) {
                response.modelVariables.forEach(variable => {
                    $mappingDiv.append(`
                        <div class="row mb-2">
                            <div class="col-5">
                                <select class="form-select form-select-sm model-variable">
                                    <option value="">不映射</option>
                                    ${response.modelVariables.map(v => `<option value="${v}">${v}</option>`).join('')}
                                </select>
                            </div>
                            <div class="col-7">
                                <select class="form-select form-select-sm dataset-field">
                                    <option value="">不映射</option>
                                    ${response.datasetFields.map(f => `<option value="${f}">${f}</option>`).join('')}
                                </select>
                            </div>
                        </div>
                    `);
                });
                
                // 设置默认映射（如果有明显匹配）
                $('.model-variable').each(function() {
                    const modelVar = $(this).val() || $(this).find('option:eq(1)').val();
                    $(this).val(modelVar);
                    
                    // 尝试自动匹配字段
                    const $datasetField = $(this).closest('.row').find('.dataset-field');
                    const matchingField = response.datasetFields.find(f => 
                        f.toLowerCase().includes(modelVar.toLowerCase()) ||
                        modelVar.toLowerCase().includes(f.toLowerCase())
                    );
                    
                    if (matchingField) {
                        $datasetField.val(matchingField);
                    }
                });
            } else {
                $mappingDiv.append('<div class="alert alert-warning">该数据集没有可用的变量映射</div>');
            }
            
            // 启用加载数据集按钮
            $('#loadDatasetBtn').prop('disabled', false);
            hideLoading();
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`加载数据集变量失败: ${error}`, 'error');
        }
    });
}

// 加载数据集
function loadDataset() {
    const datasetId = $('#datasetSelect').val();
    if (!datasetId) return;
    
    // 收集变量映射
    variableMappings = {};
    $('.row.mb-2').each(function() {
        const modelVariable = $(this).find('.model-variable').val();
        const datasetField = $(this).find('.dataset-field').val();
        
        if (modelVariable && datasetField) {
            variableMappings[modelVariable] = datasetField;
        }
    });
    
    if (Object.keys(variableMappings).length === 0) {
        showToast('请至少设置一个变量映射', 'warning');
        return;
    }
    
    showLoading();
    
    // 添加超时处理
    const timeout = setTimeout(() => {
        showToast('数据集加载时间较长，请稍候...', 'info');
    }, 5000);
    
    $.ajax({
        url: '/api/load-dataset',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            datasetId: datasetId,
            variableMappings: variableMappings
        }),
        success: function(response) {
            selectedDataset = {
                id: datasetId,
                data: response.dataset,
                metadata: response.metadata
            };
            
            // 如果已选择模型，启用运行分析按钮
            if (selectedModel) {
                $('#runAnalysisBtn').prop('disabled', false);
            }
            
            hideLoading();
            clearTimeout(timeout);
            showToast('数据集加载成功!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            clearTimeout(timeout);
            showToast(`加载数据集失败: ${error}`, 'error');
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
    
    // 禁用按钮防止重复点击
    $('#runAnalysisBtn').prop('disabled', true).html('<i class="fas fa-sync fa-spin me-2"></i>分析中...');
    
    const analysisOptions = {
        method: $('#analysisMethod').val(),
        output: {
            estimates: $('#outputEstimates').is(':checked'),
            goodness: $('#outputGoodness').is(':checked'),
            charts: $('#outputCharts').is(':checked'),
            diagnostics: $('#outputDiagnostics').is(':checked')
        }
    };
    
    // 启动进度监控
    startProgressMonitoring();
    
    $.ajax({
        url: '/api/run-analysis',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            model: selectedModel,
            dataset: selectedDataset,
            options: analysisOptions
        }),
        success: function(response) {
            analysisResults = response.results;
            
            // 显示结果
            displayAnalysisResults();
            
            // 生成代码
            generateAnalysisCode();
            
            // 启用导出和保存按钮
            $('#exportResultsBtn').prop('disabled', false);
            $('#saveToComparisonBtn').prop('disabled', false);
            $('#copyCodeBtn').prop('disabled', false);
            
            stopProgressMonitoring();
            hideLoading();
            
            $('#runAnalysisBtn').html('<i class="fas fa-play me-2"></i>运行分析');
            showToast('分析完成!', 'success');
        },
        error: function(xhr, status, error) {
            stopProgressMonitoring();
            hideLoading();
            
            $('#runAnalysisBtn').prop('disabled', false).html('<i class="fas fa-play me-2"></i>运行分析');
            showToast(`分析失败: ${error}`, 'error');
        }
    });
}

// 启动进度监控
function startProgressMonitoring() {
    // 清除现有的定时器
    if (analysisProgressInterval) {
        clearInterval(analysisProgressInterval);
    }
    
    // 每2秒获取一次进度
    analysisProgressInterval = setInterval(() => {
        $.ajax({
            url: '/api/analysis-progress',
            type: 'GET',
            success: function(response) {
                if (response.progress) {
                    const progress = response.progress;
                    $('#runAnalysisBtn').html(`<i class="fas fa-sync fa-spin me-2"></i>分析中: ${progress}%`);
                    
                    // 如果进度达到100%，停止轮询
                    if (progress >= 100) {
                        clearInterval(analysisProgressInterval);
                    }
                }
            },
            error: function() {
                // 忽略进度获取错误
            }
        });
    }, 2000);
}

// 停止进度监控
function stopProgressMonitoring() {
    if (analysisProgressInterval) {
        clearInterval(analysisProgressInterval);
        analysisProgressInterval = null;
    }
}

// 显示分析结果
function displayAnalysisResults() {
    if (!analysisResults) return;
    
    // 参数估计
    if (analysisResults.estimates) {
        $('#noEstimatesMessage').hide();
        $('#estimatesContent').show();
        
        let estimatesHtml = '<div class="table-responsive"><table class="table table-bordered table-hover">';
        estimatesHtml += '<thead class="table-light"><tr>';
        estimatesHtml += '<th>参数</th><th>估计值</th><th>标准误差</th><th>t值</th><th>p值</th><th>95% 置信区间</th>';
        estimatesHtml += '</tr></thead><tbody>';
        
        analysisResults.estimates.forEach(param => {
            estimatesHtml += `
                <tr>
                    <td><strong>${param.name}</strong></td>
                    <td>${param.estimate.toFixed(6)}</td>
                    <td>${param.stdError ? param.stdError.toFixed(6) : '-'}</td>
                    <td>${param.tValue ? param.tValue.toFixed(4) : '-'}</td>
                    <td>${param.pValue ? param.pValue.toFixed(6) : '-'}</td>
                    <td>${param.ci ? `[${param.ci[0].toFixed(4)}, ${param.ci[1].toFixed(4)}]` : '-'}</td>
                </tr>
            `;
        });
        
        estimatesHtml += '</tbody></table></div>';
        $('#estimatesContent').html(estimatesHtml);
    } else {
        $('#estimatesContent').hide();
        $('#noEstimatesMessage').show();
    }
    
    // 拟合优度
    if (analysisResults.goodness) {
        let goodnessHtml = '<div class="table-responsive"><table class="table table-bordered">';
        goodnessHtml += '<thead class="table-light"><tr><th>指标</th><th>值</th></tr></thead><tbody>';
        
        Object.entries(analysisResults.goodness).forEach(([key, value]) => {
            goodnessHtml += `
                <tr>
                    <td><strong>${key}</strong></td>
                    <td>${typeof value === 'number' ? value.toFixed(6) : value}</td>
                </tr>
            `;
        });
        
        goodnessHtml += '</tbody></table></div>';
        $('#goodness').html(goodnessHtml);
    } else {
        $('#goodness').html('<div class="alert alert-info">此分析未生成拟合优度指标</div>');
    }
    
    // 图表
    if (analysisResults.charts && analysisResults.charts.length > 0) {
        let chartsHtml = '<div class="row">';
        
        analysisResults.charts.forEach((chart, index) => {
            chartsHtml += `
                <div class="col-lg-6 mb-4">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span>${chart.title}</span>
                            <button class="btn btn-sm btn-outline-secondary" onclick="exportChart('chart-${index}')">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                        <div class="card-body">
                            <div id="chart-${index}" style="height: 300px;"></div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        chartsHtml += '</div>';
        $('#charts').html(chartsHtml);
        
        // 渲染图表
        analysisResults.charts.forEach((chart, index) => {
            renderChart(`chart-${index}`, chart);
        });
    } else {
        $('#charts').html('<div class="alert alert-info">此分析未生成图表</div>');
    }
    
    // 诊断信息
    if (analysisResults.diagnostics) {
        let diagnosticsHtml = '<div class="table-responsive"><table class="table table-bordered">';
        diagnosticsHtml += '<thead class="table-light"><tr><th>诊断项</th><th>值</th></tr></thead><tbody>';
        
        Object.entries(analysisResults.diagnostics).forEach(([key, value]) => {
            let displayValue = value;
            
            if (typeof value === 'object') {
                displayValue = JSON.stringify(value, null, 2);
            }
            
            diagnosticsHtml += `
                <tr>
                    <td><strong>${key}</strong></td>
                    <td>${displayValue}</td>
                </tr>
            `;
        });
        
        diagnosticsHtml += '</tbody></table></div>';
        $('#diagnostics').html(diagnosticsHtml);
    } else {
        $('#diagnostics').html('<div class="alert alert-info">此分析未生成诊断信息</div>');
    }
}

// 渲染图表
function renderChart(containerId, chartData) {
    try {
        // 添加响应式布局选项
        const layout = {
            ...chartData.layout,
            autosize: true,
            margin: {
                l: 50,
                r: 30,
                b: 50,
                t: 30,
                pad: 4
            },
            legend: {
                orientation: 'h',
                y: -0.2
            }
        };
        
        Plotly.newPlot(containerId, chartData.data, layout, {
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            modeBarButtonsToAdd: [{
                name: '导出图片',
                icon: Plotly.Icons.camera,
                click: function(gd) {
                    Plotly.downloadImage(gd, {
                        format: 'png',
                        filename: '精算分析图表',
                        height: 600,
                        width: 800
                    });
                }
            }]
        });
    } catch (error) {
        console.error('图表渲染错误:', error);
        $(`#${containerId}`).html(`
            <div class="alert alert-danger">
                <p>图表渲染失败: ${error.message}</p>
                <pre>${JSON.stringify(chartData, null, 2)}</pre>
            </div>
        `);
    }
}

// 导出图表
function exportChart(containerId) {
    const gd = document.getElementById(containerId);
    Plotly.downloadImage(gd, {
        format: 'png',
        filename: '精算分析图表',
        height: 600,
        width: 800
    });
}

// 生成分析代码
function generateAnalysisCode() {
    if (!analysisResults || !analysisResults.code) {
        $('#rCode').text('# 无可用R代码');
        $('#pythonCode').text('# 无可用Python代码');
        $('#sasCode').text('/* 无可用SAS代码 */');
        return;
    }
    
    $('#rCode').text(analysisResults.code.r || '# 无可用R代码');
    $('#pythonCode').text(analysisResults.code.python || '# 无可用Python代码');
    $('#sasCode').text(analysisResults.code.sas || '/* 无可用SAS代码 */');
    
    // 重新高亮代码
    Prism.highlightAll();
}

// 导出结果
function exportResults() {
    if (!analysisResults) {
        showToast('没有可导出的结果', 'warning');
        return;
    }
    
    showLoading();
    
    $.ajax({
        url: '/api/export-analysis-results',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            results: analysisResults
        }),
        success: function(response) {
            // 创建下载链接
            const link = document.createElement('a');
            link.href = response.downloadUrl;
            link.download = `精算分析结果_${new Date().toISOString().slice(0, 10)}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            hideLoading();
            showToast('结果导出成功!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`结果导出失败: ${error}`, 'error');
        }
    });
}

// 保存到对比
function saveToComparison() {
    if (!analysisResults) {
        showToast('没有可保存的结果', 'warning');
        return;
    }
    
    showLoading();
    
    $.ajax({
        url: '/api/save-to-comparison',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            model: selectedModel,
            dataset: selectedDataset,
            results: analysisResults
        }),
        success: function(response) {
            hideLoading();
            showToast('结果已保存到对比!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`保存到对比失败: ${error}`, 'error');
        }
    });
}

// 复制代码到剪贴板
function copyCodeToClipboard() {
    const activeTab = $('#codeTabs .nav-link.active').attr('id');
    let code = '';
    
    if (activeTab === 'r-tab') {
        code = $('#rCode').text();
    } else if (activeTab === 'python-tab') {
        code = $('#pythonCode').text();
    } else if (activeTab === 'sas-tab') {
        code = $('#sasCode').text();
    }
    
    if (!code || code.startsWith('# 无可用') || code.startsWith('/* 无可用')) {
        showToast('没有可复制的代码', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(code).then(function() {
        showToast('代码已复制到剪贴板!', 'success');
    }, function() {
        // 备选方案：使用textArea
        const textArea = document.createElement('textarea');
        textArea.value = code;
        document.body.appendChild(textArea);
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                showToast('代码已复制到剪贴板!', 'success');
            } else {
                showToast('复制失败，请手动复制', 'error');
            }
        } catch (err) {
            showToast('复制失败，请手动复制', 'error');
        }
        
        document.body.removeChild(textArea);
    });
}

// 检查精算师模式
function checkActuaryMode() {
    if (localStorage.getItem('actuaryMode') === 'true') {
        enableActuaryMode();
    }
}

// 切换精算师模式
function toggleActuaryMode() {
    if (localStorage.getItem('actuaryMode') === 'true') {
        localStorage.setItem('actuaryMode', 'false');
        disableActuaryMode();
        showToast('已退出精算师模式', 'info');
    } else {
        localStorage.setItem('actuaryMode', 'true');
        enableActuaryMode();
        showToast('已进入精算师模式', 'success');
    }
}

// 启用精算师模式
function enableActuaryMode() {
    $('body').addClass('actuary-mode');
    $('.actuary-only').show();
}

// 禁用精算师模式
function disableActuaryMode() {
    $('body').removeClass('actuary-mode');
    $('.actuary-only').hide();
}

// 显示Toast通知
function showToast(message, type) {
    // 移除现有的toast
    $('.toast').remove();
    
    const toast = $(`
        <div class="toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `);
    
    $('body').append(toast);
    const bsToast = new bootstrap.Toast(toast[0]);
    bsToast.show();
    
    // 自动移除
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// 显示加载动画
function showLoading() {
    $('#loading-overlay').show();
}

// 隐藏加载动画
function hideLoading() {
    $('#loading-overlay').hide();
}
