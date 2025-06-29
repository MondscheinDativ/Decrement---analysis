// 自定义数据源选项切换
document.querySelectorAll('.border-dashed').forEach(el => {
    el.addEventListener('click', () => {
        document.getElementById('custom-data-source').classList.remove('hidden');
        document.getElementById('file-upload-settings').classList.add('hidden');
        document.getElementById('url-settings').classList.add('hidden');
        document.getElementById('api-settings').classList.add('hidden');
    });
});

// 数据源类型选择
document.querySelectorAll('[data-source-type]').forEach(el => {
    el.addEventListener('click', () => {
        const type = el.getAttribute('data-source-type');
        // 隐藏所有设置
        document.getElementById('file-upload-settings').classList.add('hidden');
        document.getElementById('url-settings').classList.add('hidden');
        document.getElementById('api-settings').classList.add('hidden');
        // 显示选中的设置
        if (type === 'file') {
            document.getElementById('file-upload-settings').classList.remove('hidden');
        } else if (type === 'url') {
            document.getElementById('url-settings').classList.remove('hidden');
        } else if (type === 'api') {
            document.getElementById('api-settings').classList.remove('hidden');
        }
    });
});

// 测试 API 连接按钮
document.getElementById('test-api').addEventListener('click', () => {
    // 模拟 API 测试，显示协议警告模态框
    document.getElementById('protocol-modal').classList.remove('hidden');
});

// 关闭模态框
document.getElementById('close-modal').addEventListener('click', () => {
    document.getElementById('protocol-modal').classList.add('hidden');
});

// 继续按钮
document.getElementById('continue-btn').addEventListener('click', () => {
    document.getElementById('protocol-modal').classList.add('hidden');
    // 这里可以添加继续处理的逻辑
});

// 取消按钮
document.getElementById('cancel-btn').addEventListener('click', () => {
    document.getElementById('protocol-modal').classList.add('hidden');
});

// 模型选择
document.querySelectorAll('.model-option').forEach(el => {
    el.addEventListener('click', () => {
        // 移除其他模型的选中状态
        document.querySelectorAll('.model-option').forEach(option => {
            option.classList.remove('bg-blue-50', 'border-blue-200');
        });
        // 添加当前模型的选中状态
        el.classList.add('bg-blue-50', 'border-blue-200');
        // 显示变量定义区域
        document.getElementById('variable-definition').classList.remove('hidden');
    });
});

// 添加变量
document.getElementById('add-variable').addEventListener('click', () => {
    const varName = document.getElementById('var-name').value;
    const varLabel = document.getElementById('var-label').value;
    const varType = document.getElementById('var-type').value;

    if (!varName || !varLabel) {
        alert('请输入变量名和标签描述');
        return;
    }

    const variablesBody = document.getElementById('variables-body');
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">${varName}</td>
        <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">${varLabel}</td>
        <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">${varType}</td>
        <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
            <button class="text-red-600 hover:text-red-900 delete-variable">删除</button>
        </td>
    `;
    variablesBody.appendChild(newRow);

    // 清空输入框
    document.getElementById('var-name').value = '';
    document.getElementById('var-label').value = '';

    // 绑定删除按钮事件
    newRow.querySelector('.delete-variable').addEventListener('click', function() {
        newRow.remove();
    });
});

// 保存变量设置
document.getElementById('save-variables').addEventListener('click', () => {
    const rows = document.querySelectorAll('#variables-body tr');
    if (rows.length === 0) {
        alert('请至少定义一个变量');
        return;
    }
    alert('变量设置已保存');
    // 显示数据清洗部分
    document.getElementById('data-cleaning').classList.remove('hidden');
    // 滚动到数据清洗部分
    document.getElementById('data-cleaning').scrollIntoView({ behavior: 'smooth' });
});

// 全选按钮
document.getElementById('select-all').addEventListener('click', () => {
    const checkboxes = document.querySelectorAll('#data-cleaning input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = !checkbox.checked;
    });
});

// 开始清洗数据
document.getElementById('start-cleaning').addEventListener('click', () => {
    const checkboxes = document.querySelectorAll('#data-cleaning input[type="checkbox"]:checked');
    if (checkboxes.length === 0) {
        alert('请至少选择一项数据清洗操作');
        return;
    }
    // 显示加载状态
    document.getElementById('start-cleaning').innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 清洗中...';
    document.getElementById('start-cleaning').disabled = true;

    // 模拟数据清洗过程
    setTimeout(() => {
        // 隐藏数据清洗部分，显示清洗报告
        document.getElementById('data-cleaning').classList.add('hidden');
        document.getElementById('cleaning-report').classList.remove('hidden');
        // 重置按钮状态
        document.getElementById('start-cleaning').innerHTML = '<i class="fa fa-refresh mr-2"></i> 开始清洗数据';
        document.getElementById('start-cleaning').disabled = false;
        // 滚动到清洗报告部分
        document.getElementById('cleaning-report').scrollIntoView({ behavior: 'smooth' });
    }, 2000);
});

// 下载报告
document.getElementById('download-report').addEventListener('click', () => {
    alert('报告下载已开始');
});

// 下载数据
document.getElementById('download-data').addEventListener('click', () => {
    alert('数据下载已开始');
});

// 进入模型分析
document.getElementById('proceed-analysis').addEventListener('click', () => {
    alert('即将进入模型分析阶段');
});
