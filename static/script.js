var nextRefreshEpochMs = null;
var lastRefreshEpochMs = null;

function updateClock() {
    var now = new Date();
    // Show UTC clock to seconds
    var utc = new Date(now.toISOString());
    var hh = String(utc.getUTCHours()).padStart(2, '0');
    var mm = String(utc.getUTCMinutes()).padStart(2, '0');
    var ss = String(utc.getUTCSeconds()).padStart(2, '0');
    var utcNowEl = document.getElementById('utc-now');
    if (utcNowEl) utcNowEl.textContent = `${hh}:${mm}:${ss}`;

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
    // 使用统一的数据接口，包含 CoinGecko 字段和手动填写字段
    var res = await fetch('/api/data');
    var payload = await res.json();
    var rows = (payload && Array.isArray(payload.rows)) ? payload.rows : [];

    var tbody = document.querySelector('#token-table tbody');
    tbody.innerHTML = '';

    var fmtMoney = function(v) {
        if (v == null || isNaN(v)) return '-';
        var n = Number(v);
        return '$' + n.toLocaleString(undefined, { maximumFractionDigits: 6 });
    };
    var fmtNumber = function(v) {
        if (v == null || isNaN(v)) return '-';
        return Number(v).toLocaleString();
    };
    var fmtPercent = function(v) {
        if (v == null || isNaN(v)) return '';
        var n = Number(v);
        var pct = n <= 1 ? n * 100 : n;
        return (Math.round(pct * 100) / 100).toString() + '%';
    };

    // Helper to avoid nullish coalescing (Safari < 13)
    var orElse = function(v, fallback) {
        return (v === null || v === undefined) ? fallback : v;
    };

    rows.forEach(function(r, idx) {
        var row = document.createElement('tr');
        row.innerHTML = `
            <td>${idx + 1}</td>
            <td><a href="https://www.coingecko.com/en/coins/${encodeURIComponent(r.coin_id || '')}" target="_blank" rel="noopener">${orElse(r.coin_name, '-')}</a></td>
            <td style="background:#e6fff2;">${(r.price != null && !isNaN(r.price)) ? ('$' + Number(r.price).toFixed(6)) : '-'}</td>
            <td>${(r.pct_24h != null && !isNaN(r.pct_24h)) ? (Number(r.pct_24h).toFixed(2)+'%') : ''}</td>
            <td>${(r.pct_7d != null && !isNaN(r.pct_7d)) ? (Number(r.pct_7d).toFixed(2)+'%') : ''}</td>
            <td>${fmtNumber(r.current_supply)}</td>
            <td>${fmtMoney(r.current_market_cap)}</td>
            <td>${fmtNumber(r.total_supply)}</td>
            <td>${fmtMoney(r.total_market_cap)}</td>
            <td><a href="https://cryptorank.io/ico/${encodeURIComponent(r.coin_id || '')}" target="_blank" rel="noopener">${fmtMoney(r.found_raises)}</a></td>
            <td>${fmtPercent(r.investor_percentage)}</td>
            <td>${fmtMoney(r.financing_valuation)}</td>
            <td style="background:#e6fff2;">${fmtMoney(r.financing_based_price)}</td>
            <td>${fmtMoney(r.annualized_income)}</td>
            <td>${fmtMoney(r.income_valuation)}</td>
            <td style="background:#e6fff2;">${fmtMoney(r.income_based_price)}</td>
            <td>${orElse(r.tokenomics, '')}</td>
            <td>${orElse(r.vesting, '')}</td>
            <td>${orElse(r.cexs, '')}</td>
            <td>${orElse(r.tags, '')}</td>
        `;
        tbody.appendChild(row);
    });

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
}

loadPrices();
// 5 minutes refresh interval (in ms)
setInterval(loadPrices, 5 * 60 * 1000);
// Update clock every second
setInterval(updateClock, 1000);
updateClock();


