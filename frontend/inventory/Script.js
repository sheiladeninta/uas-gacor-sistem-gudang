// Fetch inventory logs from Inventory Management Service
async function fetchInventoryLogs() {
    const query = `
        query {
            allInventoryLogs {
                id
                itemId
                logType
                quantity
                reference
                createdAt
            }
        }
    `;

    const response = await fetch('http://localhost:5003/graphql', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });

    const result = await response.json();
    displayInventoryLogs(result.data.allInventoryLogs);
}

// Display inventory logs
function displayInventoryLogs(logs) {
    const logList = document.getElementById('inventory-log-list');
    logList.innerHTML = '';  // Clear existing logs
    logs.forEach(log => {
        const logItem = document.createElement('li');
        logItem.textContent = `Item ID: ${log.itemId}, Log Type: ${log.logType}, Quantity: ${log.quantity}, Reference: ${log.reference}, Date: ${log.createdAt}`;
        logList.appendChild(logItem);
    });
}

// Fetch and display logs on page load
window.onload = fetchInventoryLogs;
