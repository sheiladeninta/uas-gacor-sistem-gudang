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
        console.log("Fetched Items:", result);

        if (result && result.data && result.data.items) {
            const items = result.data.items;
            itemsContainer.innerHTML = '';

            items.forEach(item => {
                const itemRow = document.createElement('tr');
                itemRow.innerHTML = `
                    <td>${item.itemCode}</td>
                    <td>${item.name}</td>
                    <td>${item.stockQuantity}</td>
                    <td>${item.description || '-'}</td>
                    <td>${item.category || '-'}</td>
                    <td>${item.unit || '-'}</td>
                    <td>${item.unitPrice || '-'}</td>
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
        createItem(
            itemCode: "${itemCode}",
            name: "${name}",
            stockQuantity: ${stockQuantity},
            description: "${description}",
            category: "${category}",
            unit: "${unit}",
            unitPrice: ${unitPrice}
        ) {
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

    try {
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
    } catch (error) {
        console.error('Error adding item:', error);
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

    try {
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
    } catch (error) {
        console.error('Error deleting item:', error);
    }
}

// Edit Item (for Update)
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

        // Isi form edit sesuai id input di HTML
        document.getElementById('editItemCode').value = item.itemCode;
        document.getElementById('editName').value = item.name;
        document.getElementById('editStockQuantity').value = item.stockQuantity;
        document.getElementById('editDescription').value = item.description;
        document.getElementById('editCategory').value = item.category;
        document.getElementById('editUnit').value = item.unit;
        document.getElementById('editUnitPrice').value = item.unitPrice;

        showPage('edit-item');
    })
    .catch(error => console.error('Error fetching item data for edit:', error));
}

// Update Item (Edit Form)
document.getElementById('editItemForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const itemCode = document.getElementById('editItemCode').value;
    const name = document.getElementById('editName').value;
    const stockQuantity = document.getElementById('editStockQuantity').value;
    const description = document.getElementById('editDescription').value;
    const category = document.getElementById('editCategory').value;
    const unit = document.getElementById('editUnit').value;
    const unitPrice = document.getElementById('editUnitPrice').value;

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

    try {
        const response = await fetch(INVENTORY_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: mutation })
        });

        const result = await response.json();
        if (result.data.updateItem) {
            fetchItems();
            hideEditItemForm();
            alert("Item updated successfully!");
        } else {
            console.error("Error updating item:", result);
            alert("Failed to update item!");
        }
    } catch (error) {
        console.error('Error updating item:', error);
    }
});

// Function to hide the edit item form
function hideEditItemForm() {
    document.getElementById('edit-item').classList.add('hidden');
    showPage('home');
}

// Update Item


// Function to hide the add item form
function hideAddItemForm() {
    document.getElementById('add-item').classList.add('hidden');
    showPage('home');
}

// Function to hide the update item form


// Load inventory items when the page is loaded
document.addEventListener('DOMContentLoaded', () => {
    fetchItems();  // Fetch and display inventory items on page load
    fetchOrderRequests();  // Fetch and display order requests on page load
});

// Function to fetch and display order requests from Order Service
async function fetchOrderRequests() {
    const query = `
    query {
      orderItems {
        id
        itemCode
        itemName
        requestedQuantity
        approvedQuantity
        unit
        notes
        createdAt
        order {
          orderNumber
          status
        }
      }
    }`;

    try {
        const response = await fetch(ORDER_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const result = await response.json();
        console.log("Fetched Order Items:", result);

        if (result && result.data && result.data.orderItems) {
            const orders = result.data.orderItems;
            const orderRequestsContainer = document.getElementById('orderRequestsContainer');
            orderRequestsContainer.innerHTML = '';
            orders.forEach(orderItem => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${orderItem.order ? orderItem.order.orderNumber : '-'}</td>
                    <td>${orderItem.itemCode}</td>
                    <td>${orderItem.itemName}</td>
                    <td>${orderItem.requestedQuantity}</td>
                    <td>${orderItem.approvedQuantity}</td>
                    <td>${orderItem.unit}</td>
                    <td>${orderItem.order ? orderItem.order.status : '-'}</td>
                    <td>
                        <button onclick="sendToQC(${orderItem.order ? orderItem.order.id : 0}, '${orderItem.itemCode}', '${orderItem.itemName}', ${orderItem.requestedQuantity})">
                            Kirim ke QC
                        </button>
                    </td>
            `;
                orderRequestsContainer.appendChild(row);
            });
        } else {
            console.error('No order items found:', result);
        }
    } catch (error) {
        console.error('Error fetching order items:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchItems();
    fetchOrderRequests();
});


// Function to send the selected order to QC service and update inventory
async function sendToQC(orderId, itemCode, itemName, quantity) {
    const mutation = `
    mutation {
        sendToQc(
            orderId: ${orderId},
            itemCode: "${itemCode}",
            itemName: "${itemName}",
            quantity: ${quantity}
        ) {
            success
            message
        }
    }`;

    try {
        const response = await fetch(INVENTORY_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: mutation })
        });

        const result = await response.json();
        console.log("QC Mutation result:", result);

        if (result.errors) {
            alert("GraphQL Error: " + result.errors[0].message);
            return;
        }

        if (result.data && result.data.sendToQc && result.data.sendToQc.success) {
            alert("Order berhasil dikirim ke QC!");
            fetchOrderRequests();
            fetchItems();
        } else {
            alert("Gagal kirim ke QC: " + (result.data && result.data.sendToQc ? result.data.sendToQc.message : "Unknown error"));
        }
    } catch (error) {
        alert("Terjadi error saat mengirim ke QC");
        console.error('Error sending order to QC:', error);
    }
}