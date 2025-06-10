// Service configuration for logistic service
const SERVICES = {
    'view-items': {
        url: 'http://localhost:5003/graphql',  // Change to your logistic service URL
        path: '/logistic/view-items'
    },
    'create-order': {
        url: 'http://localhost:5003/graphql',  // Same as above
        path: '/logistic/create-order'
    }
};

// Function to navigate to a specific service's page
// Navigasi ke halaman yang sesuai berdasarkan kartu yang diklik
function navigateToService(serviceName) {
    if (serviceName === 'view-items') {
        // Arahkan ke halaman untuk melihat semua item
        window.location.href = 'view-items.html';
    } else if (serviceName === 'create-order') {
        // Arahkan ke halaman untuk membuat order
        window.location.href = 'create-order.html';
    }
}

// Function untuk handle create order
async function createOrder() {
    // Ambil data yang diperlukan dari form atau input
    const item_id = document.getElementById('item_id').value;
    const quantity = document.getElementById('quantity').value;
    const reference = document.getElementById('reference').value;

    const mutation = `
    mutation {
        createOrder(itemId: ${item_id}, quantity: ${quantity}, reference: "${reference}") {
            order {
                orderId
                itemId
                quantity
                reference
                status
                createdAt
            }
        }
    }
    `;
    
    try {
        const response = await axios.post('http://localhost:5003/graphql', {
            query: mutation
        });

        console.log('Order created:', response.data);
        alert('Order created successfully!');
    } catch (error) {
        console.error('Error creating order:', error);
        alert('Error creating order');
    }
}



// This function can also be expanded to fetch real-time data from your service for "view-items" or "create-order".
