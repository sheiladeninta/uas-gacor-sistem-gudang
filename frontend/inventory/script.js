const INVENTORY_API_URL = 'http://localhost:5000/graphql';  // URL untuk Inventory API
const ORDER_API_URL = 'http://localhost:5002/graphql';  // URL untuk Order Service API
const itemsContainer = document.getElementById('itemsContainer');
const orderRequestsContainer = document.getElementById('orderRequestsContainer');

// Function to show the specific page
function showPage(pageId) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(p => {
        p.classList.remove('active');
        p.classList.add('hidden');
    });
    const activePage = document.getElementById(pageId);
    activePage.classList.add('active');
    activePage.classList.remove('hidden');
}

// Function to fetch and display all inventory items
async function fetchItems() {
    const query = `
    query {
        items {
            id
            itemCode
            name
            stockQuantity
            description
            category
            unit
            unitPrice
        }
    }`;

    try {
        const response = await fetch(INVENTORY_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });

        const result = await response.json();
        console.log("Fetched Items:", result);  // Cek data yang diterima

        if (result && result.data && result.data.items) {
            const items = result.data.items;
            itemsContainer.innerHTML = '';  // Clear existing content

            items.forEach(item => {
                const itemRow = document.createElement('tr');
                itemRow.innerHTML = `
                    <td>${item.itemCode}</td>
                    <td>${item.name}</td>
                    <td>${item.stockQuantity}</td>
                    <td>${item.description}</td>
                    <td>${item.category}</td>
                    <td>${item.unit}</td>
                    <td>$${item.unitPrice}</td>
                    <td>
                        <button onclick="editItem('${item.itemCode}')">Edit</button>
                        <button onclick="deleteItem(${item.id})">Delete</button>
                    </td>
                `;
                itemsContainer.appendChild(itemRow);
            });
        } else {
            console.error('No items found:', result);
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}


// Add Item
document.getElementById('newItemForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const itemCode = document.getElementById('itemCode').value;
    const name = document.getElementById('name').value;
    const stockQuantity = document.getElementById('stockQuantity').value;
    const description = document.getElementById('description').value || '';
    const category = document.getElementById('category').value || '';
    const unit = document.getElementById('unit').value || '';
    const unitPrice = document.getElementById('unitPrice').value || 0;

    const mutation = `
    mutation {
        createItem(itemCode: "${itemCode}", name: "${name}", stockQuantity: ${stockQuantity}, description: "${description}", category: "${category}", unit: "${unit}", unitPrice: ${unitPrice}) {
            item {
                id
                itemCode
                name
                stockQuantity
                description
                category
                unit
                unitPrice
            }
        }
    }`;

    const response = await fetch(INVENTORY_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: mutation })
    });

    const result = await response.json();
    if (result.data.createItem) {
        fetchItems();  // Refresh the inventory table after adding an item
        hideAddItemForm();  // Hide the add item form
    }
});

// Delete Item
async function deleteItem(id) {
    const mutation = `
    mutation {
        deleteItem(id: ${id}) {
            success
        }
    }`;

    const response = await fetch(INVENTORY_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: mutation })
    });

    const result = await response.json();
    if (result.data.deleteItem && result.data.deleteItem.success) {
        fetchItems();  // Refresh the inventory table after deletion
    } else {
        console.error('Failed to delete item:', result);
    }
}

// Edit Item (for Update)
function editItem(itemCode) {
    const query = `
    query {
        item(itemCode: "${itemCode}") {
            id
            itemCode
            name
            stockQuantity
            description
            category
            unit
            unitPrice
        }
    }`;

    fetch(INVENTORY_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query })
    })
    .then(response => response.json())
    .then(result => {
        const item = result.data.item;

        // Fill in the form with item data
        document.getElementById('updateItemCode').value = item.itemCode;
        document.getElementById('updateName').value = item.name;
        document.getElementById('updateStockQuantity').value = item.stockQuantity;
        document.getElementById('updateDescription').value = item.description;
        document.getElementById('updateCategory').value = item.category;
        document.getElementById('updateUnit').value = item.unit;
        document.getElementById('updateUnitPrice').value = item.unitPrice;

        // Show update form
        showPage('update-item');
    })
    .catch(error => console.error('Error fetching item data for edit:', error));
}

// Update Item
document.getElementById('updateItemForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const itemCode = document.getElementById('updateItemCode').value;  // Using itemCode for update
    const name = document.getElementById('updateName').value;
    const stockQuantity = document.getElementById('updateStockQuantity').value;
    const description = document.getElementById('updateDescription').value;
    const category = document.getElementById('updateCategory').value;
    const unit = document.getElementById('updateUnit').value;
    const unitPrice = document.getElementById('updateUnitPrice').value;

    const mutation = `
    mutation {
        updateItem(itemCode: "${itemCode}", name: "${name}", stockQuantity: ${stockQuantity}, description: "${description}", category: "${category}", unit: "${unit}", unitPrice: ${unitPrice}) {
            item {
                id
                itemCode
                name
                stockQuantity
                description
                category
                unit
                unitPrice
            }
        }
    }`;

    const response = await fetch(INVENTORY_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: mutation })
    });

    const result = await response.json();
    if (result.data.updateItem) {
        fetchItems();  // Refresh the inventory table after update
        hideUpdateItemForm();  // Hide the update item form
        alert("Item updated successfully!");
    } else {
        console.error("Error updating item:", result);
        alert("Failed to update item!");
    }
});

// Function to hide the add item form
function hideAddItemForm() {
    document.getElementById('add-item').classList.add('hidden');
    showPage('home');
}

// Function to hide the update item form
function hideUpdateItemForm() {
    document.getElementById('update-item').classList.add('hidden');
    showPage('home');
}

// Load inventory items when the page is loaded
document.addEventListener('DOMContentLoaded', () => {
    fetchItems();  // Fetch and display inventory items on page load
    fetchOrderRequests();  // Fetch and display order requests on page load
});

// Function to fetch and display order requests from Order Service
// Function to fetch and display order requests
async function fetchOrderRequests() {
    const query = `
    query {
        orders {
            id
            orderNumber
            restaurantName
            items {
                id
                itemCode
                itemName
                requestedQuantity
                unit
            }
        }
    }`;

    try {
        const response = await fetch(ORDER_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });

        const result = await response.json();
        console.log("Order Data:", result);

        if (result && result.data && result.data.orders) {
            const orders = result.data.orders;
            orderRequestsContainer.innerHTML = ''; // Clear previous data

            orders.forEach(order => {
                order.items.forEach(item => {
                    const orderRow = document.createElement('tr');
                    orderRow.innerHTML = `
                        <td>${order.orderNumber}</td>
                        <td>${item.itemCode}</td>
                        <td>${item.itemName}</td>
                        <td>${item.requestedQuantity}</td>
                        <td>${item.unit}</td>
                        <td><button onclick="sendToQC(${order.id}, '${item.itemCode}', ${item.requestedQuantity}, '${item.itemName}')">Send to QC</button></td>
                    `;
                    orderRequestsContainer.appendChild(orderRow);
                });
            });
        } else {
            console.error('No orders found:', result);
        }
    } catch (error) {
        console.error('Error fetching order data:', error);
    }
}



// Function to send the selected order to QC service and update inventory
// Function to send the selected order to QC service and update inventory
async function sendToQC(orderId, itemCode, quantity, itemName) {
    // Langkah 1: Update Inventory Service (kurangi stok)
    const updateInventoryMutation = `
    mutation {
        updateInventoryForQC(itemCode: "${itemCode}", quantity: ${quantity}) {
            success
            message
        }
    }`;

    const updateResponse = await fetch(INVENTORY_API_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: updateInventoryMutation })
    });

    const updateResult = await updateResponse.json();
    console.log("Inventory Update Response:", updateResult);

    if (updateResult.data.updateInventoryForQC.success) {
        // Langkah 2: Kirim order ke QC Service
        const sendToQCMutation = `
        mutation {
            sendToQC(orderId: ${orderId}, itemCode: "${itemCode}", itemName: "${itemName}", quantity: ${quantity}) {
                success
                message
            }
        }`;

        const qcResponse = await fetch(ORDER_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: sendToQCMutation })
        });

        const qcResult = await qcResponse.json();
        console.log("QC Service Response:", qcResult);

        if (qcResult.data.sendToQC.success) {
            alert("Order berhasil dikirim ke QC!");
            fetchOrderRequests();  // Refresh daftar order
        } else {
            alert("Gagal mengirim order ke QC!");
        }
    } else {
        alert("Gagal memperbarui inventory!");
    }
}



