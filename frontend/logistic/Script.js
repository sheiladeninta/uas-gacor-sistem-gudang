// Fungsi untuk muat order
document.getElementById('loadOrdersBtn').addEventListener('click', function() {
    fetch('/api/logistic/requests')  // API untuk mendapatkan requests
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#ordersTable tbody');
            tableBody.innerHTML = '';  // Clear previous data

            data.forEach(order => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${order.orderId}</td>
                    <td>${order.itemId}</td>
                    <td>${order.quantity}</td>
                    <td>${order.reference}</td>
                    <td>${order.status}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching orders:', error));
});

// Fungsi untuk muat requests
document.getElementById('loadRequestsBtn').addEventListener('click', function() {
    fetch('/api/logistic/requests')  // API untuk mendapatkan requests
        .then(response => response.json())
        .then(data => {
            const tableBody = document.querySelector('#requestsTable tbody');
            tableBody.innerHTML = '';  // Clear previous data

            data.forEach(request => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${request.id}</td>
                    <td>${request.itemId}</td>
                    <td>${request.quantity}</td>
                    <td>${request.reference}</td>
                    <td>${request.status}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching requests:', error));
});

// Fungsi untuk membuat order baru
document.getElementById('createOrderForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const newOrder = {
        item_id: document.getElementById('item_id').value,
        quantity: document.getElementById('quantity').value,
        reference: document.getElementById('reference').value
    };

    fetch('/logistic/create-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newOrder)
    })
    .then(response => response.json())
    .then(data => {
        alert('Order created successfully!');
    })
    .catch(error => console.error('Error creating order:', error));
});
