async function loadPrices() {
    // 使用统一的数据接口，包含 CoinGecko 字段和手动填写字段
    const res = await fetch('/api/data');
    const rows = await res.json();

    const tbody = document.querySelector('#token-table tbody');
    tbody.innerHTML = '';

    const fmtMoney = (v) => {
        if (v == null || isNaN(v)) return '-';
        const n = Number(v);
        return '$' + n.toLocaleString(undefined, { maximumFractionDigits: 6 });
    };
    const fmtNumber = (v) => {
        if (v == null || isNaN(v)) return '-';
        return Number(v).toLocaleString();
    };
    const fmtPercent = (v) => {
        if (v == null || isNaN(v)) return '';
        const n = Number(v);
        const pct = n <= 1 ? n * 100 : n;
        return (Math.round(pct * 100) / 100).toString() + '%';
    };

    rows.forEach((r, idx) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${idx + 1}</td>
            <td>${r.coin_name ?? '-'}</td>
            <td>${r.price != null ? ('$' + Number(r.price).toFixed(6)) : '-'}</td>
            <td>${fmtNumber(r.current_supply)}</td>
            <td>${fmtMoney(r.current_market_cap)}</td>
            <td>${fmtNumber(r.total_supply)}</td>
            <td>${fmtMoney(r.total_market_cap)}</td>
            <td>${fmtMoney(r.found_raises)}</td>
            <td>${fmtPercent(r.investor_percentage)}</td>
            <td>${fmtMoney(r.financing_valuation)}</td>
            <td>${fmtMoney(r.financing_based_price)}</td>
            <td>${fmtMoney(r.annualized_income)}</td>
            <td>${fmtMoney(r.income_valuation)}</td>
            <td>${fmtMoney(r.income_based_price)}</td>
            <td>${r.tokenomics ?? ''}</td>
            <td>${r.vesting ?? ''}</td>
            <td>${r.cexs ?? ''}</td>
        `;
        tbody.appendChild(row);
    });
}

loadPrices();
setInterval(loadPrices, 30000);


