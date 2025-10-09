var nextRefreshEpochMs = null;
var lastRefreshEpochMs = null;
var allData = []; // 存储所有数据用于过滤

// 主题管理
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// 搜索和过滤功能
function applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const priceFilter = document.getElementById('price-filter').value;
    const marketCapFilter = document.getElementById('market-cap-filter').value;
    
    let filteredData = allData.filter(row => {
        // 搜索过滤
        if (searchTerm) {
            const nameMatch = (row.coin_name || '').toLowerCase().includes(searchTerm);
            const idMatch = (row.coin_id || '').toLowerCase().includes(searchTerm);
            if (!nameMatch && !idMatch) return false;
        }
        
        // 价格变化过滤
        if (priceFilter) {
            const pct24h = parseFloat(row.pct_24h) || 0;
            switch (priceFilter) {
                case 'gain':
                    if (pct24h <= 0) return false;
                    break;
                case 'loss':
                    if (pct24h >= 0) return false;
                    break;
                case 'stable':
                    if (Math.abs(pct24h) > 2) return false; // 变化超过2%认为不稳定
                    break;
            }
        }
        
        // 市值过滤
        if (marketCapFilter) {
            const marketCap = parseFloat(row.current_market_cap) || 0;
            switch (marketCapFilter) {
                case 'large':
                    if (marketCap < 10e9) return false; // 10B
                    break;
                case 'mid':
                    if (marketCap < 1e9 || marketCap >= 10e9) return false; // 1B-10B
                    break;
                case 'small':
                    if (marketCap >= 1e9) return false; // <1B
                    break;
            }
        }
        
        return true;
    });
    
    renderTable(filteredData);
}

function renderTable(data) {
    var tbody = document.querySelector('#token-table tbody');
    tbody.innerHTML = '';

    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="20" style="text-align: center; padding: 20px; color: var(--text-muted);">没有找到匹配的数据</td></tr>';
        return;
    }

    var fmtMoney = function(v) {
        if (v == null || isNaN(v)) return '-';
        var n = Number(v);
        if (n >= 1e9) return '$' + (n/1e9).toFixed(2) + 'B';
        if (n >= 1e6) return '$' + (n/1e6).toFixed(2) + 'M';
        if (n >= 1e3) return '$' + (n/1e3).toFixed(2) + 'K';
        return '$' + n.toLocaleString(undefined, { maximumFractionDigits: 6 });
    };
    
    var fmtNumber = function(v) {
        if (v == null || isNaN(v)) return '-';
        var n = Number(v);
        if (n >= 1e9) return (n/1e9).toFixed(2) + 'B';
        if (n >= 1e6) return (n/1e6).toFixed(2) + 'M';
        if (n >= 1e3) return (n/1e3).toFixed(2) + 'K';
        return n.toLocaleString();
    };
    
    var fmtPercent = function(v) {
        if (v == null || isNaN(v)) return '-';
        var n = Number(v);
        // CoinGecko已经返回百分比格式，不需要转换
        var formatted = (Math.round(n * 100) / 100).toFixed(2) + '%';
        // 添加颜色指示
        if (n > 0) return '<span style="color: var(--success-color);">+' + formatted + '</span>';
        if (n < 0) return '<span style="color: var(--error-color);">' + formatted + '</span>';
        return formatted;
    };

    // Helper to avoid nullish coalescing (Safari < 13)
    var orElse = function(v, fallback) {
        return (v === null || v === undefined) ? fallback : v;
    };

    data.forEach(function(r, idx) {
        var row = document.createElement('tr');
        var priceVal = (r.price != null && !isNaN(r.price)) ? Number(r.price) : null;
        var fbpVal = (r.financing_based_price != null && !isNaN(r.financing_based_price)) ? Number(r.financing_based_price) : null;
        var ibpVal = (r.income_based_price != null && !isNaN(r.income_based_price)) ? Number(r.income_based_price) : null;
        
        // 价格比较样式
        var fbpStyle = (priceVal != null && fbpVal != null && fbpVal > priceVal) ? 'color:var(--error-color);font-weight:bold;' : '';
        var ibpStyle = (priceVal != null && ibpVal != null && ibpVal > priceVal) ? 'color:var(--error-color);font-weight:bold;' : '';
        
        // 移动端友好的文本截断
        var truncateText = function(text, maxLength) {
            if (!text) return '';
            if (text.length <= maxLength) return text;
            return text.substring(0, maxLength) + '...';
        };
        
        row.innerHTML = `
            <td class="important-col">${idx + 1}</td>
            <td class="important-col">
                <a href="https://www.coingecko.com/en/coins/${encodeURIComponent(r.coin_id || '')}" 
                   target="_blank" rel="noopener" 
                   title="${orElse(r.coin_name, '-')}">
                    ${truncateText(orElse(r.coin_name, '-'), 15)}
                </a>
            </td>
            <td class="price-col important-col" style="${priceVal ? 'font-weight: bold;' : ''}">
                ${(r.price != null && !isNaN(r.price)) ? ('$' + Number(r.price).toFixed(6)) : '-'}
            </td>
            <td>${fmtPercent(r.pct_24h)}</td>
            <td>${fmtPercent(r.pct_7d)}</td>
            <td title="${orElse(r.current_supply, '-')}">${fmtNumber(r.current_supply)}</td>
            <td title="${orElse(r.current_market_cap, '-')}">${fmtMoney(r.current_market_cap)}</td>
            <td title="${orElse(r.total_supply, '-')}">${fmtNumber(r.total_supply)}</td>
            <td title="${orElse(r.total_market_cap, '-')}">${fmtMoney(r.total_market_cap)}</td>
            <td>
                <a href="https://cryptorank.io/ico/${encodeURIComponent(r.coin_id || '')}" 
                   target="_blank" rel="noopener">
                    ${fmtMoney(r.found_raises)}
                </a>
            </td>
            <td>${fmtPercent(r.investor_percentage)}</td>
            <td title="${orElse(r.financing_valuation, '-')}">${fmtMoney(r.financing_valuation)}</td>
            <td class="price-col" style="${fbpStyle}">${fmtMoney(r.financing_based_price)}</td>
            <td title="${orElse(r.annualized_income, '-')}">${fmtMoney(r.annualized_income)}</td>
            <td title="${orElse(r.income_valuation, '-')}">${fmtMoney(r.income_valuation)}</td>
            <td class="price-col" style="${ibpStyle}">${fmtMoney(r.income_based_price)}</td>
            <td title="${orElse(r.tokenomics, '')}">${truncateText(orElse(r.tokenomics, ''), 20)}</td>
            <td title="${orElse(r.vesting, '')}">${truncateText(orElse(r.vesting, ''), 20)}</td>
            <td title="${orElse(r.cexs, '')}">${truncateText(orElse(r.cexs, ''), 15)}</td>
            <td title="${orElse(r.tags, '')}">${truncateText(orElse(r.tags, ''), 15)}</td>
        `;
        tbody.appendChild(row);
    });
}

// 导出功能
function exportData() {
    const data = allData;
    if (data.length === 0) {
        alert('没有数据可导出');
        return;
    }
    
    // 准备CSV数据
    const headers = ['代币名称', '当前价格', '24h变化%', '7d变化%', '流通供应量', '流通市值', '总供应量', '总市值', '融资轮次', '投资者比例', '融资估值', '融资价格', '年化收入', '收入估值', '收入价格', '代币经济学', '锁仓', '交易所', '标签'];
    const csvContent = [
        headers.join(','),
        ...data.map(row => [
            `"${(row.coin_name || '').replace(/"/g, '""')}"`,
            row.price || '',
            row.pct_24h || '',
            row.pct_7d || '',
            row.current_supply || '',
            row.current_market_cap || '',
            row.total_supply || '',
            row.total_market_cap || '',
            row.found_raises || '',
            row.investor_percentage || '',
            row.financing_valuation || '',
            row.financing_based_price || '',
            row.annualized_income || '',
            row.income_valuation || '',
            row.income_based_price || '',
            `"${(row.tokenomics || '').replace(/"/g, '""')}"`,
            `"${(row.vesting || '').replace(/"/g, '""')}"`,
            `"${(row.cexs || '').replace(/"/g, '""')}"`,
            `"${(row.tags || '').replace(/"/g, '""')}"`
        ].join(','))
    ].join('\n');
    
    // 下载文件
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `crypto_data_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function updateClock() {
    var now = new Date();
    // Show UTC date time: YYYY-MM-DD HH:mm:ss
    var utc = new Date(now.toISOString());
    var YYYY = utc.getUTCFullYear();
    var MM = String(utc.getUTCMonth() + 1).padStart(2, '0');
    var DD = String(utc.getUTCDate()).padStart(2, '0');
    var hh = String(utc.getUTCHours()).padStart(2, '0');
    var mm = String(utc.getUTCMinutes()).padStart(2, '0');
    var ss = String(utc.getUTCSeconds()).padStart(2, '0');
    var utcNowEl = document.getElementById('utc-now');
    if (utcNowEl) utcNowEl.textContent = `${YYYY}-${MM}-${DD} ${hh}:${mm}:${ss}`;

    var lastEl = document.getElementById('last-refresh');
    if (lastEl && lastRefreshEpochMs) {
        lastEl.textContent = new Date(lastRefreshEpochMs).toISOString().replace('T',' ').replace('Z',' UTC');
    }
    var nextEl = document.getElementById('next-refresh');
    if (nextEl && nextRefreshEpochMs) {
        nextEl.textContent = new Date(nextRefreshEpochMs).toISOString().replace('T',' ').replace('Z',' UTC');
    }
}

async function loadPrices() {
    try {
        // 添加加载状态
        var table = document.querySelector('#token-table');
        if (table) table.classList.add('loading');
        
        // 使用统一的数据接口，包含 CoinGecko 字段和手动填写字段
        var res = await fetch('/api/data');
        
        if (!res.ok) {
            throw new Error('网络请求失败: ' + res.status);
        }
        
        var payload = await res.json();
        var rows = (payload && Array.isArray(payload.rows)) ? payload.rows : [];

        // 移除之前的错误信息
        var existingError = document.querySelector('.error');
        if (existingError) existingError.remove();

        // 存储所有数据用于过滤
        allData = rows;
        
        // 应用当前过滤条件
        applyFilters();

        // Mark timestamps
        if (payload && payload.last_refresh_epoch) {
            lastRefreshEpochMs = payload.last_refresh_epoch * 1000;
        } else {
            lastRefreshEpochMs = Date.now();
        }
        if (payload && payload.next_refresh_epoch) {
            nextRefreshEpochMs = payload.next_refresh_epoch * 1000;
        } else {
            nextRefreshEpochMs = lastRefreshEpochMs + 5 * 60 * 1000;
        }
        
    } catch (error) {
        console.error('加载价格数据失败:', error);
        
        // 显示错误信息
        var errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.innerHTML = '数据加载失败: ' + error.message + '<br>请刷新页面重试';
        
        var timebar = document.querySelector('#timebar');
        if (timebar && timebar.nextSibling) {
            timebar.parentNode.insertBefore(errorDiv, timebar.nextSibling);
        } else {
            document.body.appendChild(errorDiv);
        }
        
        // 在表格中显示错误状态
        var tbody = document.querySelector('#token-table tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="20" style="text-align: center; padding: 20px; color: var(--error-color);">数据加载失败，请刷新页面</td></tr>';
        }
    } finally {
        // 移除加载状态
        if (table) table.classList.remove('loading');
    }
}

// 初始化
initTheme();
loadPrices();
updateClock();

// 添加事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 搜索功能
    const searchInput = document.getElementById('search-input');
    const clearSearch = document.getElementById('clear-search');
    
    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }
    
    if (clearSearch) {
        clearSearch.addEventListener('click', function() {
            searchInput.value = '';
            applyFilters();
        });
    }
    
    // 过滤功能
    const priceFilter = document.getElementById('price-filter');
    const marketCapFilter = document.getElementById('market-cap-filter');
    
    if (priceFilter) {
        priceFilter.addEventListener('change', applyFilters);
    }
    
    if (marketCapFilter) {
        marketCapFilter.addEventListener('change', applyFilters);
    }
    
    // 导出功能
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportData);
    }
});

// 5 minutes refresh interval (in ms)
setInterval(loadPrices, 5 * 60 * 1000);
// Update clock every second
setInterval(updateClock, 1000);


