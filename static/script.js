async function loadPrices() {
    // 使用统一的数据接口，包含 CoinGecko 字段和手动填写字段
    const res = await fetch('/api/data');
    const rows = await res.json();

    const tbody = document.querySelector('#token-table tbody');
    tbody.innerHTML = '';

    rows.forEach((r, idx) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${idx + 1}</td>
            <td>${r.coin_name ?? '-'}</td>
            <td>${r.price != null ? ('$' + Number(r.price).toFixed(6)) : '-'}</td>
            <td>${r.current_supply != null ? Number(r.current_supply).toLocaleString() : '-'}</td>
            <td>${r.current_market_cap != null ? ('$' + Number(r.current_market_cap).toLocaleString()) : '-'}</td>
            <td>${r.total_supply != null ? Number(r.total_supply).toLocaleString() : '-'}</td>
            <td>${r.total_market_cap != null ? ('$' + Number(r.total_market_cap).toLocaleString()) : '-'}</td>
            <td>${r.found_raises ?? ''}</td>
            <td>${r.investor_percentage ?? ''}</td>
            <td>${r.financing_valuation ?? ''}</td>
            <td>${r.financing_based_price ?? ''}</td>
            <td>${r.annualized_income ?? ''}</td>
            <td>${r.income_valuation ?? ''}</td>
            <td>${r.income_based_price ?? ''}</td>
            <td>${r.tokenomics ?? ''}</td>
            <td>${r.vesting ?? ''}</td>
            <td>${r.cexs ?? ''}</td>
        `;
        tbody.appendChild(row);
    });
}

loadPrices();
setInterval(loadPrices, 30000);


