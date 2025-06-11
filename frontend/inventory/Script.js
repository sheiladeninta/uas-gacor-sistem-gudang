// Fungsi untuk memuat Inventory
function loadInventory() {
    fetch('/api/inventory')  // Memanggil API untuk mendapatkan data terbaru
        .then(response => response.json())
        .then(data => {
            console.log("Data loaded from API:", data);  // Log data yang diterima untuk debugging

            const tableBody = document.querySelector('#inventoryTable tbody');
            tableBody.innerHTML = '';  // Clear previous data

            if (data.length === 0) {
                const noDataRow = document.createElement('tr');
                noDataRow.innerHTML = '<td colspan="8">No inventory data available.</td>';
                tableBody.appendChild(noDataRow);
            } else {
                data.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${item.id}</td>
                        <td>${item.item_code}</td>
                        <td>${item.name}</td>
                        <td>${item.quantity}</td>
                        <td>${item.description}</td>
                        <td>${item.unit}</td>
                        <td>${item.min_stor}</td>
                        <td>${item.location}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching inventory:', error);
            const tableBody = document.querySelector('#inventoryTable tbody');
            tableBody.innerHTML = '<tr><td colspan="8">Failed to load data. Please try again later.</td></tr>';
        });
}

// Fungsi untuk memuat Inventory Logs
function loadInventoryLogs() {
    fetch('/api/inventory/logs')  // Memanggil API untuk mendapatkan data logs
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#inventoryLogsTable tbody');
            tableBody.innerHTML = '';  // Clear previous data

            if (data.length === 0) {
                const noDataRow = document.createElement('tr');
                noDataRow.innerHTML = '<td colspan="8">No logs available.</td>';
                tableBody.appendChild(noDataRow);
            } else {
                data.forEach(log => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${log.log_id}</td>
                        <td>${log.item_id}</td>
                        <td>${log.log_type}</td>
                        <td>${log.quantity}</td>
                        <td>${log.reference}</td>
                        <td>${log.status}</td>
                        <td>${log.created_at}</td>
                        <td>
                            ${log.status === 'pending' ? `<button onclick="approveRequest(${log.log_id}, ${log.quantity})">Approve</button>` : ''}
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching inventory logs:', error);
            const tableBody = document.querySelector('#inventoryLogsTable tbody');
            tableBody.innerHTML = '<tr><td colspan="8">Failed to load data. Please try again later.</td></tr>';
        });
}

// Memuat Inventory Logs saat tombol ditekan
document.getElementById('loadLogsBtn').addEventListener('click', function() {
    loadInventoryLogs();  // Memanggil fungsi untuk memuat inventory logs
});

// Fungsi untuk approve request
function approveRequest(log_id, quantity) {
    const approvalData = {
        log_id: log_id,
        approved_quantity: quantity
    };

    fetch('/api/inventory/approve', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(approvalData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadInventoryLogs();  // Refresh the inventory logs
    })
    .catch(error => console.error('Error approving request:', error));
}


// Fungsi untuk memuat Inventory Status
function loadInventoryStatus() {
    fetch('/api/inventory/status')  // Memanggil API untuk mendapatkan data status
        .then(response => response.json())
        .then(data => {
            console.log("Inventory Status loaded:", data);

            const tableBody = document.querySelector('#inventoryStatusTable tbody');
            tableBody.innerHTML = '';  // Clear previous data

            if (data.length === 0) {
                const noDataRow = document.createElement('tr');
                noDataRow.innerHTML = '<td colspan="3">No status available.</td>';
                tableBody.appendChild(noDataRow);
            } else {
                data.forEach(status => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${status.item_id}</td>
                        <td>${status.current_stock}</td>
                        <td>${status.last_updated}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching inventory status:', error);
            const tableBody = document.querySelector('#inventoryStatusTable tbody');
            tableBody.innerHTML = '<tr><td colspan="3">Failed to load data. Please try again later.</td></tr>';
        });
}

// Memuat Inventory saat tombol ditekan
document.getElementById('loadInventoryBtn').addEventListener('click', function() {
    loadInventory();  // Memanggil fungsi untuk memuat inventory
});

// Menambahkan Item
document.getElementById('addItemForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const newItem = {
        item_code: document.getElementById('item_code').value,
        name: document.getElementById('name').value,
        quantity: document.getElementById('quantity').value,
        description: document.getElementById('description').value,
        unit: document.getElementById('unit').value,
        min_stor: document.getElementById('min_stor').value,
        location: document.getElementById('location').value,
    };

    fetch('/api/inventory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newItem)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Item added:", data);  // Log data yang ditambahkan untuk debugging
        alert('Item added successfully!');
        
        // Memuat ulang data inventory setelah menambah item
        loadInventory();
        
        // Clear form
        document.getElementById('addItemForm').reset();
    })
    .catch(error => console.error('Error adding item:', error));
});

// Mengupdate Item
document.getElementById('updateItemForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const updateData = {
        id: document.getElementById('update_item_id').value,
        quantity: document.getElementById('update_quantity').value
    };

    fetch(`/api/inventory/${updateData.id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Item updated:", data);  // Log data yang diupdate untuk debugging
        alert('Item updated successfully!');
        
        // Clear form
        document.getElementById('updateItemForm').reset();
        
        // Memuat ulang inventory untuk menampilkan perubahan
        loadInventory();
    })
    .catch(error => console.error('Error updating item:', error));
});

// Memuat Inventory Logs saat tombol ditekan
document.getElementById('loadLogsBtn').addEventListener('click', function() {
    loadInventoryLogs();  // Memanggil fungsi untuk memuat inventory logs
});

// Memuat Inventory Status saat tombol ditekan
document.getElementById('loadStatusBtn').addEventListener('click', function() {
    loadInventoryStatus();  // Memanggil fungsi untuk memuat inventory status
});


// Menyetujui Permintaan Barang
document.getElementById('approveItemForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const approvalData = {
        log_id: document.getElementById('log_id').value,
        approved_quantity: document.getElementById('approved_quantity').value,
    };

    fetch('/api/inventory/approve', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(approvalData)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        // Optionally clear the form
        document.getElementById('approveItemForm').reset();
    })
    .catch(error => console.error('Error approving request:', error));
});

// Fungsi untuk memuat Log Permintaan Barang
document.getElementById('loadLogsBtn').addEventListener('click', function () {
    fetch('/api/inventory/logs')  // Endpoint API untuk log permintaan
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#inventoryLogsTable tbody');
            tableBody.innerHTML = '';  // Clear previous data

            data.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${log.id}</td>
                    <td>${log.item_id}</td>
                    <td>${log.log_type}</td>
                    <td>${log.quantity}</td>
                    <td>${log.reference}</td>
                    <td>${log.created_at}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
            alert('Failed to load data. Please try again later.');
        });
});

// Fungsi untuk memuat Status Stok Barang
document.getElementById('loadStatusBtn').addEventListener('click', function () {
    fetch('/api/inventory/status')  // Endpoint API untuk status stok
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#inventoryStatusTable tbody');
            tableBody.innerHTML = '';  // Clear previous data

            data.forEach(status => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${status.item_id}</td>
                    <td>${status.current_stock}</td>
                    <td>${status.last_updated}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            alert('Failed to load data. Please try again later.');
        });
});
