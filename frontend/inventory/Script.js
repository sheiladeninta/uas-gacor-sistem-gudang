// Inisialisasi Apollo Client
const { ApolloClient, InMemoryCache, gql } = ApolloClient;
const client = new ApolloClient({
  uri: 'http://localhost:5003/graphql',  // Ganti dengan URL backend Anda
  cache: new InMemoryCache()
});

// Query untuk mengambil semua inventory items
const GET_ALL_INVENTORY = gql`
  query {
    allInventory {
      id
      itemCode
      name
      quantity
      description
      unit
      minStor
      location
    }
  }
`;

// Mutasi untuk menambah item
const CREATE_INVENTORY_ITEM = gql`
  mutation createInventoryItem(
    $itemCode: String!
    $name: String!
    $quantity: Int!
    $description: String
    $unit: String
    $minStor: Int
    $location: String
  ) {
    createInventoryItem(
      itemCode: $itemCode
      name: $name
      quantity: $quantity
      description: $description
      unit: $unit
      minStor: $minStor
      location: $location
    ) {
      inventoryItem {
        id
        itemCode
        name
        quantity
        description
        unit
        minStor
        location
      }
    }
  }
`;

// Mutasi untuk mengupdate item
const UPDATE_INVENTORY_ITEM = gql`
  mutation updateInventoryItem(
    $id: Int!
    $name: String
    $quantity: Int
    $description: String
    $unit: String
    $minStor: Int
    $location: String
  ) {
    updateInventoryItem(
      id: $id
      name: $name
      quantity: $quantity
      description: $description
      unit: $unit
      minStor: $minStor
      location: $location
    ) {
      inventoryItem {
        id
        itemCode
        name
        quantity
        description
        unit
        minStor
        location
      }
    }
  }
`;

// Mutasi untuk menghapus item
const DELETE_INVENTORY_ITEM = gql`
  mutation deleteInventoryItem($id: Int!) {
    deleteInventoryItem(id: $id) {
      success
    }
  }
`;

// Fungsi untuk menampilkan data inventory
function displayInventory(items) {
  const inventoryDiv = document.getElementById('inventoryItems');
  inventoryDiv.innerHTML = '';  // Clear previous content

  if (items.length === 0) {
    inventoryDiv.innerHTML = "<p>No inventory items found.</p>";
  }

  items.forEach(item => {
    const itemDiv = document.createElement('div');
    itemDiv.classList.add('item');
    
    itemDiv.innerHTML = `
      <h3>${item.name}</h3>
      <p><strong>Code:</strong> ${item.itemCode}</p>
      <p><strong>Quantity:</strong> ${item.quantity}</p>
      <p><strong>Description:</strong> ${item.description || 'No description available'}</p>
      <p><strong>Unit:</strong> ${item.unit}</p>
      <p><strong>Location:</strong> ${item.location}</p>
      <button onclick="openUpdateForm(${item.id})">Update Item</button>
      <button onclick="deleteItem(${item.id})">Delete Item</button>
    `;
    
    inventoryDiv.appendChild(itemDiv);
  });
}

// Menjalankan query untuk mengambil data inventory
function fetchInventory() {
  client.query({
    query: GET_ALL_INVENTORY,
  }).then(result => {
    displayInventory(result.data.allInventory);
  }).catch(error => {
    console.error('Error fetching data:', error);
  });
}

// Fungsi untuk menampilkan form update item
function openUpdateForm(id) {
  // Ambil data item yang ingin di-update berdasarkan id
  const item = getItemById(id);  // Pastikan fungsi getItemById disiapkan untuk mengambil item dengan id tertentu
  document.getElementById('addItemForm').style.display = 'block';  // Tampilkan form

  // Isi form dengan data item yang ada
  document.getElementById('itemCode').value = item.itemCode;
  document.getElementById('name').value = item.name;
  document.getElementById('quantity').value = item.quantity;
  document.getElementById('description').value = item.description;
  document.getElementById('unit').value = item.unit;
  document.getElementById('minStor').value = item.minStor;
  document.getElementById('location').value = item.location;

  // Submit form untuk update item
  document.getElementById('itemForm').onsubmit = function(event) {
    event.preventDefault();

    const updatedItem = {
      id: item.id,
      itemCode: document.getElementById('itemCode').value,
      name: document.getElementById('name').value,
      quantity: parseInt(document.getElementById('quantity').value),
      description: document.getElementById('description').value,
      unit: document.getElementById('unit').value,
      minStor: parseInt(document.getElementById('minStor').value),
      location: document.getElementById('location').value
    };

    client.mutate({
      mutation: UPDATE_INVENTORY_ITEM,
      variables: updatedItem
    }).then(result => {
      console.log('Item updated:', result.data.updateInventoryItem.inventoryItem);
      fetchInventory();  // Refresh data after updating
      document.getElementById('addItemForm').style.display = 'none'; // Hide form after submit
    }).catch(error => {
      console.error('Error updating item:', error);
    });
  };
}

// Fungsi untuk menghapus item
function deleteItem(id) {
  client.mutate({
    mutation: DELETE_INVENTORY_ITEM,
    variables: { id: id }
  }).then(result => {
    console.log('Item deleted:', result.data.deleteInventoryItem.success);
    fetchInventory();  // Refresh data after deleting
  }).catch(error => {
    console.error('Error deleting item:', error);
  });
}

// Fungsi untuk mengambil item berdasarkan id
function getItemById(id) {
  const items = JSON.parse(localStorage.getItem('inventoryItems')) || [];
  return items.find(item => item.id === id);
}

// Event listener untuk tombol "Add Inventory Item"
document.getElementById('addItemButton').addEventListener('click', () => {
  document.getElementById('addItemForm').style.display = 'block';  // Tampilkan form untuk menambah item
});

// Event listener untuk tombol "View Inventory"
document.getElementById('viewInventoryButton').addEventListener('click', fetchInventory);

// Menangani pengiriman form untuk menambah item
document.getElementById('itemForm').addEventListener('submit', function(event) {
  event.preventDefault(); // Mencegah form refresh halaman
  const newItem = {
    itemCode: document.getElementById('itemCode').value,
    name: document.getElementById('name').value,
    quantity: parseInt(document.getElementById('quantity').value),
    description: document.getElementById('description').value,
    unit: document.getElementById('unit').value,
    minStor: parseInt(document.getElementById('minStor').value),
    location: document.getElementById('location').value
  };

  client.mutate({
    mutation: CREATE_INVENTORY_ITEM,
    variables: newItem
  }).then(result => {
    console.log('Item added:', result.data.createInventoryItem.inventoryItem);
    fetchInventory();  // Refresh data after adding a new item
    document.getElementById('addItemForm').style.display = 'none'; // Hide form after submit
  }).catch(error => {
    console.error('Error adding item:', error);
  });
});

// Call fetchInventory() initially to load data
fetchInventory();
