// 全局变量
let currentDataset = null;
let currentPage = 1;
const pageSize = 10;
let totalPages = 0;
let cleaningOptions = {};
let selectedFields = [];

// 页面加载完成后初始化
$(function() {
    // 初始化事件监听
    initEventListeners();
    
    // 检查是否在精算师模式下
    checkActuaryMode();
});

function initEventListeners() {
    // 数据源选择切换
    $('#dataSourceSelect').change(function() {
        $('.data-credentials').hide();
        $(`#${$(this).val()}Credentials`).show();
    });

    // 表格选择变化时更新字段选项
    $('#tableSelect').change(function() {
        updateFieldOptions();
    });

    // 应用筛选按钮
    $('#applyFiltersBtn').click(function() {
        applyFilters();
    });

    // 清洗数据按钮
    $('#cleanDataBtn').click(function() {
        cleanData();
    });

    // 生成报告按钮
    $('#generateReportBtn').click(function() {
        generateDiagnosticReport();
    });

    // 保存数据集按钮
    $('#saveDatasetBtn').click(function() {
        saveDataset();
    });

    // 分页按钮
    $('#prevPageBtn').click(function() {
        if (currentPage > 1) {
            currentPage--;
            updateDataPreview();
        }
    });

    $('#nextPageBtn').click(function() {
        if (currentPage < totalPages) {
            currentPage++;
            updateDataPreview();
        }
    });
}

// 获取数据函数
function fetchData() {
    const dataSource = $('#dataSourceSelect').val();
    showLoading();
    
    // 根据选择的数据源构造请求数据
    let requestData = {};
    if (dataSource === 'hmd') {
        requestData = {
            source: 'hmd',
            username: $('#hmdUsername').val(),
            password: $('#hmdPassword').val()
        };
    } else if (dataSource === 'cdc') {
        requestData = {
            source: 'cdc',
            apiKey: $('#cdcApiKey').val()
        };
    }
    
    // 向后端API发送请求
    $.ajax({
        url: '/api/fetch-data',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(requestData),
        success: function(response) {
            currentDataset = response.data;
            totalPages = Math.ceil(currentDataset.length / pageSize);
            
            // 更新表格选择
            updateTableOptions(response.tables);
            
            // 启用控件
            $('#tableSelect').prop('disabled', false);
            $('#applyFiltersBtn').prop('disabled', false);
            
            // 更新数据预览
            updateDataPreview();
            hideLoading();
            showToast('数据获取成功!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`数据获取失败: ${error}`, 'error');
        }
    });
}

// 处理自定义数据
function processCustomData() {
    const fileInput = $('#customDataFile')[0];
    if (fileInput.files.length > 0) {
        showLoading();
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        $.ajax({
            url: '/api/upload-custom-data',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                currentDataset = response.data;
                totalPages = Math.ceil(currentDataset.length / pageSize);
                
                // 更新表格选择
                updateTableOptions(response.tables);
                
                // 启用控件
                $('#tableSelect').prop('disabled', false);
                $('#applyFiltersBtn').prop('disabled', false);
                
                // 更新数据预览
                updateDataPreview();
                hideLoading();
                showToast('自定义数据处理成功!', 'success');
            },
            error: function(xhr, status, error) {
                hideLoading();
                showToast(`自定义数据处理失败: ${error}`, 'error');
            }
        });
    } else if ($('#customApiEndpoint').val()) {
        showLoading();
        $.ajax({
            url: '/api/fetch-api-data',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                endpoint: $('#customApiEndpoint').val()
            }),
            success: function(response) {
                currentDataset = response.data;
                totalPages = Math.ceil(currentDataset.length / pageSize);
                
                // 更新表格选择
                updateTableOptions(response.tables);
                
                // 启用控件
                $('#tableSelect').prop('disabled', false);
                $('#applyFiltersBtn').prop('disabled', false);
                
                // 更新数据预览
                updateDataPreview();
                hideLoading();
                showToast('API数据获取成功!', 'success');
            },
            error: function(xhr, status, error) {
                hideLoading();
                showToast(`API数据获取失败: ${error}`, 'error');
            }
        });
    } else {
        showToast('请上传文件或输入API端点', 'warning');
    }
}

// 更新表格选项
function updateTableOptions(tables) {
    const $tableSelect = $('#tableSelect');
    $tableSelect.empty();
    tables.forEach(table => {
        $tableSelect.append(`<option value="${table.value}">${table.label}</option>`);
    });
}

// 更新字段选项
function updateFieldOptions() {
    const table = $('#tableSelect').val();
    if (!table) return;
    
    showLoading();
    $.ajax({
        url: '/api/get-table-fields',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            table: table
        }),
        success: function(response) {
            const $fieldSelect = $('#fieldSelect');
            $fieldSelect.empty();
            response.fields.forEach(field => {
                $fieldSelect.append(`<option value="${field.value}">${field.label}</option>`);
            });
            
            // 启用字段选择
            $fieldSelect.prop('disabled', false);
            $('#startYear').prop('disabled', false);
            $('#endYear').prop('disabled', false);
            hideLoading();
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`获取字段失败: ${error}`, 'error');
        }
    });
}

// 应用筛选
function applyFilters() {
    const table = $('#tableSelect').val();
    selectedFields = $('#fieldSelect').val();
    const startYear = $('#startYear').val();
    const endYear = $('#endYear').val();
    
    if (!table || !selectedFields || selectedFields.length === 0) {
        showToast('请选择表格和至少一个字段', 'warning');
        return;
    }
    
    showLoading();
    $.ajax({
        url: '/api/apply-filters',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            table: table,
            fields: selectedFields,
            startYear: startYear,
            endYear: endYear
        }),
        success: function(response) {
            currentDataset = response.filteredData;
            totalPages = Math.ceil(currentDataset.length / pageSize);
            
            // 启用数据清洗和报告生成
            $('#cleanDataBtn').prop('disabled', false);
            $('#generateReportBtn').prop('disabled', false);
            
            // 更新数据预览
            updateDataPreview();
            hideLoading();
            showToast('筛选应用成功!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`筛选应用失败: ${error}`, 'error');
        }
    });
}

// 更新数据预览
function updateDataPreview() {
    if (!currentDataset || currentDataset.length === 0) {
        $('#dataPreview tbody').html(
            '<tr><td colspan="10" class="text-center text-muted py-5">暂无数据</td></tr>'
        );
        return;
    }
    
    // 计算分页数据
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, currentDataset.length);
    const pageData = currentDataset.slice(startIndex, endIndex);
    
    // 更新表格
    const $tbody = $('#dataPreview tbody');
    $tbody.empty();
    
    // 添加表头
    if ($('#dataPreview thead tr').children().length === 1) {
        const $thead = $('#dataPreview thead tr');
        $thead.empty();
        Object.keys(pageData[0]).forEach(key => {
            $thead.append(`<th>${key}</th>`);
        });
    }
    
    // 添加数据行
    pageData.forEach(row => {
        const $tr = $('<tr>');
        Object.values(row).forEach(value => {
            $tr.append(`<td>${value !== null ? value : '<span class="text-muted">NULL</span>'}</td>`);
        });
        $tbody.append($tr);
    });
    
    // 更新分页信息
    $('#pageInfo').text(`第 ${currentPage} 页 / 共 ${totalPages} 页`);
    
    // 更新分页按钮状态
    $('#prevPageBtn').prop('disabled', currentPage <= 1);
    $('#nextPageBtn').prop('disabled', currentPage >= totalPages);
    
    // 启用保存按钮
    $('#saveDatasetBtn').prop('disabled', false);
}

// 清洗数据
function cleanData() {
    if (!currentDataset || currentDataset.length === 0) {
        showToast('没有可清洗的数据', 'warning');
        return;
    }
    
    // 获取清洗选项
    cleaningOptions = {
        missingValueTreatment: $('#missingValueTreatment').val(),
        outlierTreatment: $('#outlierTreatment').val(),
        normalizationMethod: $('#normalizationMethod').val(),
        removeDuplicates: $('#removeDuplicates').is(':checked'),
        convertDataTypes: $('#convertDataTypes').is(':checked')
    };
    
    showLoading();
    $.ajax({
        url: '/api/clean-data',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            data: currentDataset,
            options: cleaningOptions
        }),
        success: function(response) {
            currentDataset = response.cleanedData;
            totalPages = Math.ceil(currentDataset.length / pageSize);
            
            // 更新数据预览
            updateDataPreview();
            hideLoading();
            showToast('数据清洗完成!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`数据清洗失败: ${error}`, 'error');
        }
    });
}

// 生成诊断报告
function generateDiagnosticReport() {
    if (!currentDataset || currentDataset.length === 0) {
        showToast('没有可分析的数据', 'warning');
        return;
    }
    
    // 获取报告选项
    const reportOptions = {
        summaryStats: $('#summaryStats').is(':checked'),
        missingValueReport: $('#missingValueReport').is(':checked'),
        outlierReport: $('#outlierReport').is(':checked'),
        dataDistribution: $('#dataDistribution').is(':checked'),
        correlationMatrix: $('#correlationMatrix').is(':checked'),
        timeSeriesAnalysis: $('#timeSeriesAnalysis').is(':checked')
    };
    
    showLoading();
    $.ajax({
        url: '/api/generate-report',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            data: currentDataset,
            options: reportOptions
        }),
        success: function(response) {
            // 显示报告
            displayReport(response.report);
            hideLoading();
            showToast('诊断报告生成完成!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`报告生成失败: ${error}`, 'error');
        }
    });
}

// 显示报告
function displayReport(report) {
    const $reportContent = $('#reportContent');
    $reportContent.empty();
    
    // 添加报告各部分
    if (report.summaryStats) {
        $reportContent.append('<h6>汇总统计</h6>');
        $reportContent.append(createReportTable(report.summaryStats));
    }
    
    if (report.missingValueReport) {
        $reportContent.append('<h6 class="mt-4">缺失值报告</h6>');
        $reportContent.append(createReportTable(report.missingValueReport));
    }
    
    if (report.outlierReport) {
        $reportContent.append('<h6 class="mt-4">异常值报告</h6>');
        $reportContent.append(createReportTable(report.outlierReport));
    }
    
    if (report.dataDistribution) {
        $reportContent.append('<h6 class="mt-4">数据分布</h6>');
        report.dataDistribution.forEach(dist => {
            $reportContent.append(`<p><strong>${dist.field}</strong>: ${dist.description}</p>`);
            if (dist.chart) {
                $reportContent.append(`<div id="chart-${dist.field}" class="my-3"></div>`);
                renderChart(`chart-${dist.field}`, dist.chart);
            }
        });
    }
    
    if (report.correlationMatrix) {
        $reportContent.append('<h6 class="mt-4">相关性矩阵</h6>');
        $reportContent.append(`<div id="correlation-matrix-chart" class="my-3"></div>`);
        renderChart('correlation-matrix-chart', report.correlationMatrix);
    }
    
    if (report.timeSeriesAnalysis) {
        $reportContent.append('<h6 class="mt-4">时间序列分析</h6>');
        report.timeSeriesAnalysis.forEach(ts => {
            $reportContent.append(`<p><strong>${ts.field}</strong></p>`);
            $reportContent.append(`<div id="ts-chart-${ts.field}" class="my-3"></div>`);
            renderChart(`ts-chart-${ts.field}`, ts.chart);
        });
    }
    
    // 显示报告容器
    $('#reportContainer').show();
}

// 创建报告表格
function createReportTable(data) {
    if (!data || data.length === 0) return '<p>无数据</p>';
    
    const headers = Object.keys(data[0]);
    let html = '<div class="table-responsive"><table class="table table-bordered table-sm"><thead><tr>';
    
    // 添加表头
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // 添加数据行
    data.forEach(row => {
        html += '<tr>';
        headers.forEach(header => {
            html += `<td>${row[header]}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    return html;
}

// 渲染图表
function renderChart(containerId, chartData) {
    Plotly.newPlot(containerId, chartData.data, chartData.layout, {responsive: true});
}

// 导出报告
function exportReport(format) {
    if (!currentDataset || currentDataset.length === 0) {
        showToast('没有可导出的数据', 'warning');
        return;
    }
    
    showLoading();
    $.ajax({
        url: '/api/export-report',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            data: currentDataset,
            format: format
        }),
        success: function(response) {
            // 创建下载链接
            const link = document.createElement('a');
            link.href = response.downloadUrl;
            link.download = `diagnostic_report.${format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            hideLoading();
            showToast(`报告导出为${format.toUpperCase()}成功!`, 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`报告导出失败: ${error}`, 'error');
        }
    });
}

// 保存数据集
function saveDataset() {
    if (!currentDataset || currentDataset.length === 0) {
        showToast('没有可保存的数据', 'warning');
        return;
    }
    
    showLoading();
    $.ajax({
        url: '/api/save-dataset',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            data: currentDataset,
            fields: selectedFields,
            cleaningOptions: cleaningOptions
        }),
        success: function(response) {
            hideLoading();
            showToast('数据集保存成功!', 'success');
        },
        error: function(xhr, status, error) {
            hideLoading();
            showToast(`数据集保存失败: ${error}`, 'error');
        }
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
