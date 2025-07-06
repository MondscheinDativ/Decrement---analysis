$(document).ready(function() {
    // Load navigation
    $('#navigation').load('../html/navigation.html');
    
    // Set last updated date
    $('#last-updated').text(new Date().toISOString().split('T')[0]);
    
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Show loading overlay
    window.showLoading = function() {
        $('#loading-overlay').show();
    };
    
    // Hide loading overlay
    window.hideLoading = function() {
        $('#loading-overlay').hide();
    };
    
    // Load default page
    loadPage('index');
});

// Navigation handler
function loadPage(page) {
    showLoading();
    
    // Load page content
    $('#main-content').load(`../html/${page}.html`, function() {
        hideLoading();
        
        // Load page-specific JS
        if (page === 'data-pipeline') {
            $.getScript('../js/data-pipeline.js');
        } else if (page === 'analysis') {
            $.getScript('../js/analysis.js');
        } else if (page === 'results') {
            $.getScript('../js/results.js');
        }
    });
}

// Toggle actuary mode
function toggleActuaryMode() {
    const isActuaryMode = localStorage.getItem('actuaryMode') === 'true';
    localStorage.setItem('actuaryMode', !isActuaryMode);
    
    if (!isActuaryMode) {
        $('body').addClass('actuary-mode');
        showToast('已进入精算师模式', 'success');
    } else {
        $('body').removeClass('actuary-mode');
        showToast('已退出精算师模式', 'info');
    }
}

// Toast notification
function showToast(message, type) {
    const toast = $(`
        <div class="toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `);
    
    $('body').append(toast);
    new bootstrap.Toast(toast[0]).show();
    setTimeout(() => toast.remove(), 5000);
}
