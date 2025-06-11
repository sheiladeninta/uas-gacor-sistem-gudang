const client = new Apollo.ApolloClient({
  uri: 'http://127.0.0.1:5000/graphql',  // Pastikan URL ini sesuai dengan aplikasi Flask
  cache: new Apollo.InMemoryCache()
});

// API Base URL
const API_BASE_URL = '/api';

// Fungsi untuk menampilkan loading spinner
function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
}

// Fungsi untuk menyembunyikan loading spinner
function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

// Event listener untuk tombol "Submit Quality Control Check"
document.getElementById('checkConditionBtn').addEventListener('click', async () => {
  const itemId = document.getElementById('itemId').value;
  const checkType = document.getElementById('checkType').value;
  const condition = document.getElementById('condition').value;
  const quantityChecked = document.getElementById('quantityChecked').value;
  const checkedBy = document.getElementById('checkedBy').value;
  const notes = document.getElementById('notes').value;

  // Validasi input
  if (!itemId || !quantityChecked || !checkedBy) {
    alert("Please fill in all required fields.");
    return;
  }

  const ADD_QUALITY_CONTROL = `
    mutation($itemId: Int!, $checkType: String!, $condition: String!, $quantityChecked: Int!, $checkedBy: Int!, $notes: String) {
      addQualityControl(
        itemId: $itemId, 
        checkType: $checkType, 
        condition: $condition, 
        quantityChecked: $quantityChecked, 
        checkedBy: $checkedBy, 
        notes: $notes
      ) {
        success
      }
    }
  `;

  try {
    // Kirim mutasi GraphQL untuk menambahkan hasil quality control
    const response = await client.mutate({
      mutation: Apollo.gql(ADD_QUALITY_CONTROL),
      variables: { 
        itemId: parseInt(itemId), 
        checkType, 
        condition, 
        quantityChecked: parseInt(quantityChecked), 
        checkedBy: parseInt(checkedBy), 
        notes
      }
    });

    // Menampilkan hasil pengiriman
    const resultMessage = response.data.addQualityControl.success 
      ? "Quality control check submitted successfully!" 
      : "Failed to submit quality control check.";
    document.getElementById('resultMessage').innerText = resultMessage;
    document.getElementById('resultContainer').style.display = 'block';

  } catch (error) {
    console.error("Error submitting data:", error);
    alert("Error submitting data. Please try again.");
  }
});

// Event listener untuk form submit
document.getElementById('qcForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = {
        item_id: parseInt(formData.get('item_id')),
        check_type: formData.get('check_type'),
        condition: formData.get('condition'),
        quantity_checked: parseInt(formData.get('quantity_checked')),
        batch_number: formData.get('batch_number'),
        notes: formData.get('notes'),
        action_taken: formData.get('action_taken')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/qc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('Data pemeriksaan berhasil disimpan');
            this.reset();
            refreshData();
        } else {
            throw new Error('Failed to save QC data');
        }
    } catch (error) {
        console.error('Error saving data:', error);
        alert('Gagal menyimpan data. Silakan coba lagi.');
    }
});

// Fungsi untuk memuat data QC
async function refreshData() {
    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}/qc`);
        const data = await response.json();
        
        const tableBody = document.getElementById('qcTableBody');
        tableBody.innerHTML = '';
        
        data.forEach(qc => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${qc.item_id}</td>
                <td>${formatCheckType(qc.check_type)}</td>
                <td>${formatCondition(qc.condition)}</td>
                <td>${qc.quantity_checked}</td>
                <td><span class="status-badge status-${qc.condition}">${formatStatus(qc.status)}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="approveQC(${qc.id})">
                        <i class="fas fa-check me-1"></i> Setujui
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error fetching data:', error);
        alert('Gagal memuat data. Silakan coba lagi.');
    } finally {
        hideLoading();
    }
}

// Fungsi untuk menyetujui QC
async function approveQC(qcId) {
    try {
        const response = await fetch(`${API_BASE_URL}/qc/${qcId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            alert('QC berhasil disetujui');
            refreshData();
        } else {
            throw new Error('Failed to approve QC');
        }
    } catch (error) {
        console.error('Error approving QC:', error);
        alert('Gagal menyetujui QC. Silakan coba lagi.');
    }
}

// Helper functions
function formatCheckType(type) {
    const types = {
        'kedatangan': 'Kedatangan',
        'audit_stok': 'Audit Stok',
        'pengiriman': 'Pengiriman'
    };
    return types[type] || type;
}

function formatCondition(condition) {
    const conditions = {
        'layak': 'Layak',
        'rusak': 'Rusak',
        'kedaluwarsa': 'Kedaluwarsa'
    };
    return conditions[condition] || condition;
}

function formatStatus(status) {
    const statuses = {
        'pending': 'Menunggu',
        'approved': 'Disetujui',
        'rejected': 'Ditolak'
    };
    return statuses[status] || status;
}

// Load data when page loads
document.addEventListener('DOMContentLoaded', refreshData);

// Update current date in header
function updateCurrentDate() {
    const options = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    const currentDate = new Date().toLocaleDateString('id-ID', options);
    document.getElementById('currentDate').textContent = currentDate;
}

// Call immediately and update every minute
updateCurrentDate();
setInterval(updateCurrentDate, 60000);
