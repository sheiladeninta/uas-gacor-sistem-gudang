// URL API untuk Logistic Service dan Inventory Service
const logisticServiceUrl = 'http://localhost:5002/graphql';
const inventoryServiceUrl = 'http://localhost:5003/graphql';

// Memuat daftar item dari Inventory Service
document.getElementById('loadItemsBtn').addEventListener('click', () => {
    fetch(inventoryServiceUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: `
                query {
                    allInventory {
                        id
                        itemCode
                        name
                        description
                        unit
                        minStor
                        location
                    }
                }
            `
        })
    })
    .then(response => response.json())
    .then(data => {
        const items = data.data.allInventory;
        const itemsTable = document.getElementById('itemsTable').getElementsByTagName('tbody')[0];
        itemsTable.innerHTML = ''; // Kosongkan tabel sebelumnya

        items.forEach(item => {
            let row = itemsTable.insertRow();
            row.insertCell(0).textContent = item.itemCode;
            row.insertCell(1).textContent = item.name;
            row.insertCell(2).textContent = item.description;
            row.insertCell(3).textContent = item.unit;
            row.insertCell(4).textContent = item.minStor;
            row.insertCell(5).textContent = item.location;
        });
    })
    .catch(error => console.error('Error fetching items:', error));
});

// Menambahkan order baru ke Logistic Service
document.getElementById('createOrderForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const itemId = document.getElementById('orderItemId').value;
    const quantity = document.getElementById('orderQuantity').value;
    const reference = document.getElementById('orderReference').value;

    fetch(logisticServiceUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: `
                mutation {
                    createOrder(itemId: ${itemId}, quantity: ${quantity}, reference: "${reference}") {
                        orderId
                        itemId
                        quantity
                        reference
                        status
                        createdAt
                    }
                }
            `
        })
    })
    .then(response => response.json())
    .then(data => {
        alert('Order created successfully');
        console.log(data);
    })
    .catch(error => console.error('Error creating order:', error));
});

// Memuat daftar order dari Logistic Service
document.getElementById('loadOrdersBtn').addEventListener('click', () => {
    fetch(logisticServiceUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: `
                query {
                    allOrders {
                        orderId
                        itemId
                        quantity
                        reference
                        status
                    }
                }
            `
        })
    })
    .then(response => response.json())
    .then(data => {
        const orders = data.data.allOrders;
        const ordersTable = document.getElementById('ordersTable').getElementsByTagName('tbody')[0];
        ordersTable.innerHTML = ''; // Kosongkan tabel sebelumnya

        orders.forEach(order => {
            let row = ordersTable.insertRow();
            row.insertCell(0).textContent = order.orderId;
            row.insertCell(1).textContent = order.itemId;
            row.insertCell(2).textContent = order.quantity;
            row.insertCell(3).textContent = order.reference;
            row.insertCell(4).textContent = order.status;
        });
    })
    .catch(error => console.error('Error fetching orders:', error));
});
