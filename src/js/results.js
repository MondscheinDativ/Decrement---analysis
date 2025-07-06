// 全局变量
let comparisonResults = null;
let selectedComparisonItems = [];
let selectedMetrics = [];
let currentResultId = null;

$(document).ready(function() {
    // 初始化事件监听
    initEventListeners();
    // 检查是否在精算师模式下
    checkActuaryMode();
});

function initEventListeners() {
    // 对比类型变化
    $('#comparisonType').change(function() {
        loadComparisonItems();
    });

    // 对比指标选择变化
    $('#comparisonMetric').change(function() {
        selectedMetrics = $(this).val();
        $('#runComparisonBtn').prop('disabled', selectedMetrics.length === 0);
    });

    // 运行对比按钮
    $('#runComparisonBtn').click(function() {
        runComparison();
    });

    // 更新图表按钮
    $('#updateChartsBtn').click(function() {
        updateVisualizations();
    });

    // 导出对比按钮
    $('#exportComparisonBtn').click(function() {
        exportComparison();
    });

    // 保存对比按钮
    $('#saveComparisonBtn').click(function() {
        saveComparison();
    });
}

function loadComparisonItems() {
    const comparisonType = $('#comparisonType').val();
    showLoading();
    
    $.ajax({
        url: `/api/comparison-items/${comparisonType}`,
        type: 'GET',
        success: function(response) {
            const $itemsDiv = $('#comparisonItems');
            $itemsDiv.empty();
            
            if (response.items.length === 0) {
                $itemsDiv.append('<div class="alert alert-warning">没有可用的对比项目</div>');
                return;
            }
            
            response.items.forEach(item => {
                $itemsDiv.append(`
                    <div class="form-check mb-2">
                        <input class="form-check-input comparison-item" type="checkbox" 
                               value="${item.id}" id="item-${item.id}">
                        <label class="form-check-label" for="item-${item.id}">
                            ${item.name}
                            <small class="text-muted d-block">${item.description}</small>
                        </label>
                    </div>
                `);
            });
            
            // 添加全选/取消全选按钮
            $itemsDiv.append(`
                <div class="d-flex justify-content-between mt-2">
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="$('.comparison-item').prop('checked', true)">全选</button>
                    <button class="btn btn-sm btn-outline-secondary" 
                            onclick="$('.comparison-item').prop('checked', false)">取消全选</button>
                </div>
            `);
            
            // 监听项目选择变化
            $('.comparison-item').change(function() {
                selectedComparisonItems = $('.comparison-item:checked').map(function() {
                    return $(this).val();
                }).get();
                
                $('#runComparisonBtn').prop('disabled', 
                    selectedComparisonItems.length < 2 || selectedMetrics.length === 0);
            });
            
            hideLoading();
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast('加载对比项目失败: ' + error, 'error');
        }
    });
}

function runComparison() {
    if (selectedComparisonItems.length < 2 || selectedMetrics.length === 0) {
        showToast('请至少选择2个对比项目和1个对比指标', 'warning');
        return;
    }
    
    showLoading();
    
    const comparisonOptions = {
        type: $('#comparisonType').val(),
        items: selectedComparisonItems,
        metrics: selectedMetrics
    };
    
    $.ajax({
        url: '/api/run-comparison',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            options: comparisonOptions
        }),
        success: function(response) {
            comparisonResults = response.results;
            currentResultId = response.resultId;
            
            // 显示对比结果
            displayComparisonResults();
            
            // 启用控件
            $('#updateChartsBtn').prop('disabled', false);
            $('#exportComparisonBtn').prop('disabled', false);
            $('#saveComparisonBtn').prop('disabled', false);
            
            hideLoading();
            showToast('对比完成!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast('对比失败: ' + error, 'error');
        }
    });
}

function displayComparisonResults() {
    if (!comparisonResults) return;
    
    // 摘要
    $('#noComparisonMessage').hide();
    $('#summaryContent').show();
    
    let summaryHtml = '<div class="table-responsive"><table class="table table-bordered"><thead><tr>';
    summaryHtml += '<th>指标</th>';
    
    // 添加表头
    comparisonResults.items.forEach(item => {
        summaryHtml += `<th>${item.name}</th>`;
    });
    
    summaryHtml += '</tr></thead><tbody>';
    
    // 添加指标行
    Object.entries(comparisonResults.metrics).forEach(([metric, values]) => {
        summaryHtml += `<tr><td><strong>${metric}</strong></td>`;
        values.forEach(value => {
            summaryHtml += `<td>${typeof value === 'number' ? value.toFixed(4) : value}</td>`;
        });
        summaryHtml += '</tr>';
    });
    
    summaryHtml += '</tbody></table></div>';
    $('#summaryContent').html(summaryHtml);
    
    // 详细信息
    let detailsHtml = '<div class="accordion" id="detailsAccordion">';
    
    comparisonResults.details.forEach((detail, index) => {
        detailsHtml += `
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading${index}">
                    <button class="accordion-button" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#collapse${index}">
                        ${detail.itemName} (${detail.itemType})
                    </button>
                </h2>
                <div id="collapse${index}" class="accordion-collapse collapse" 
                     data-bs-parent="#detailsAccordion">
                    <div class="accordion-body">
                        <pre><code>${JSON.stringify(detail.data, null, 2)}</code></pre>
                    </div>
                </div>
            </div>
        `;
    });
    
    detailsHtml += '</div>';
    $('#details').html(detailsHtml);
    
    // 可视化
    updateVisualizations();
}

function updateVisualizations() {
    if (!comparisonResults || !comparisonResults.visualizations) return;
    
    let visualizationHtml = '<div class="row">';
    
    comparisonResults.visualizations.forEach((viz, index) => {
        visualizationHtml += `
            <div class="col-12 mb-4">
                <div class="card">
                    <div class="card-header">${viz.title}</div>
                    <div class="card-body">
                        <div id="viz-${index}" style="height: 400px;"></div>
                    </div>
                </div>
            </div>
        `;
    });
    
    visualizationHtml += '</div>';
    $('#visualization').html(visualizationHtml);
    
    // 渲染图表
    comparisonResults.visualizations.forEach((viz, index) => {
        Plotly.newPlot(`viz-${index}`, viz.data, viz.layout, {responsive: true});
    });
}

function exportComparison() {
    if (!currentResultId) {
        showToast('没有可导出的对比结果', 'warning');
        return;
    }
    
    showLoading();
    
    $.ajax({
        url: '/api/export-comparison',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            resultId: currentResultId
        }),
        xhrFields: {
            responseType: 'blob'
        },
        success: function(response) {
            // 创建下载链接
            const url = window.URL.createObjectURL(response);
            const a = document.createElement('a');
            a.href = url;
            a.download = `comparison_results_${new Date().toISOString().slice(0, 10)}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            hideLoading();
            showToast('对比结果导出成功!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast('对比结果导出失败: ' + error, 'error');
        }
    });
}

function saveComparison() {
    if (!comparisonResults) {
        showToast('没有可保存的对比结果', 'warning');
        return;
    }
    
    showLoading();
    
    $.ajax({
        url: '/api/save-comparison',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            results: comparisonResults
        }),
        success: function(response) {
            hideLoading();
            showToast('对比结果已保存!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast('保存对比结果失败: ' + error, 'error');
        }
    });
}
