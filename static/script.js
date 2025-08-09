async function loadPrices() {
    const res = await fetch('/api/prices');
    const tokens = await res.json();

    const tbody = document.querySelector("#token-table tbody");
    tbody.innerHTML = "";

    tokens.forEach(token => {
        const row = document.createElement("tr");
        const currentPrice = token.current_price != null ? token.current_price.toFixed(6) : '-';
        const buyPrice = token.buy_price != null ? token.buy_price : '-';
        const amount = token.amount != null ? token.amount : '-';
        const profitStr = token.profit != null ? token.profit.toFixed(2) : '0.00';
        const color = token.profit >= 0 ? 'green' : 'red';
        row.innerHTML = `
            <td>${token.name}</td>
            <td>$${currentPrice}</td>
            <td>$${buyPrice}</td>
            <td>${amount}</td>
            <td style="color:${color};">$${profitStr}</td>
        `;
        tbody.appendChild(row);
    });
}

loadPrices();
setInterval(loadPrices, 30000);


