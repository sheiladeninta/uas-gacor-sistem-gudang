// API URLs
const API_URL = 'http://localhost:5004';
const INVENTORY_URL = 'http://localhost:5000';
const LOGISTICS_URL = 'http://localhost:5001';

// Dummy Data
const DUMMY_DATA = {
    pending: [
        { id: 'INV001', tanggal: '2024-01-15T08:30:00', nama: 'Daging Sapi' },
        { id: 'INV002', tanggal: '2024-01-15T09:15:00', nama: 'Ayam Potong' },
        { id: 'INV003', tanggal: '2024-01-15T10:00:00', nama: 'Ikan Salmon' }
    ],
    results: [
        { id: 'INV004', tanggal: '2024-01-14T14:30:00', nama: 'Udang Segar', status: 'layak', processed: false },
        { id: 'INV005', tanggal: '2024-01-14T15:45:00', nama: 'Tomat Cherry', status: 'tidak_layak', processed: false },
        { id: 'INV006', tanggal: '2024-01-14T16:20:00', nama: 'Telur Ayam', status: 'layak', processed: true }
    ],
    details: {
        'INV001': { id: 'INV001', tanggal: '2024-01-15T08:30:00', nama: 'Daging Sapi', jumlah: 50, supplier: 'PT Sapi Sehat' },
        'INV002': { id: 'INV002', tanggal: '2024-01-15T09:15:00', nama: 'Ayam Potong', jumlah: 30, supplier: 'PT Ayam Segar' },
        'INV003': { id: 'INV003', tanggal: '2024-01-15T10:00:00', nama: 'Ikan Salmon', jumlah: 15, supplier: 'PT Ikan Prima' },
        'INV004': { id: 'INV004', tanggal: '2024-01-14T14:30:00', nama: 'Udang Segar', status: 'layak', catatan: 'Kondisi segar', processed: false },
        'INV005': { id: 'INV005', tanggal: '2024-01-14T15:45:00', nama: 'Tomat Cherry', status: 'tidak_layak', catatan: 'Ada bintik hitam', processed: false },
        'INV006': { id: 'INV006', tanggal: '2024-01-14T16:20:00', nama: 'Telur Ayam', status: 'layak', catatan: 'Kualitas baik', processed: true }
    }
};

// Update table data
async function updateTable(id) {
    try {
        const data = DUMMY_DATA[id];
        document.querySelector(`#${id} tbody`).innerHTML = data.map(i => {
            let statusCell = '';
            let actionButton = '';

            if (id === 'pending') {
                actionButton = `<button class="btn btn-primary btn-icon" onclick="showDetail('${i.id}')">
                    <i class="fas fa-clipboard-check"></i> Periksa
                </button>`;
            } else {
                const statusClass = i.status === 'layak' ? 'status-layak' : 'status-tidak_layak';
                statusCell = `<td><span class="status-badge ${statusClass}">${i.status}</span></td>`;
                
                if (!i.processed) {
                    actionButton = `<button class="btn btn-primary btn-icon" onclick="showDetail('${i.id}')">
                        <i class="fas fa-cog"></i> Proses
                    </button>`;
                } else {
                    actionButton = `<button class="btn btn-secondary btn-icon" onclick="showDetail('${i.id}')">
                        <i class="fas fa-info-circle"></i> Detail
                    </button>`;
                }
            }

            return `
                <tr>
                    <td>${formatDate(i.tanggal)}</td>
                    <td>${i.id}</td>
                    <td>${i.nama}</td>
                    ${statusCell}
                    <td>${actionButton}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error:', error);
    }
}

// Show item detail
async function showDetail(id) {
    try {
        const item = DUMMY_DATA.details[id];
        if (!item) return;
        
        const modal = document.getElementById('detailModal');
        modal.style.display = 'block';
        
        let actionButton = '';
        if (item.status) {
            if (!item.processed) {
                actionButton = item.status === 'layak' 
                    ? `<button class="btn btn-logistics btn-icon" onclick="sendToLogistics('${item.id}')">
                         <i class="fas fa-truck"></i> Kirim ke Logistik
                       </button>`
                    : `<button class="btn btn-inventory btn-icon" onclick="returnToInventory('${item.id}')">
                         <i class="fas fa-undo"></i> Kembalikan ke Inventory
                       </button>`;
            }
        }

        modal.querySelector('.modal-content').innerHTML = `
            <div class="modal-header">
                <h3>Detail ${item.nama}</h3>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body">
                <p><strong>ID:</strong> ${item.id}</p>
                <p><strong>Tanggal:</strong> ${formatDate(item.tanggal)}</p>
                ${item.status ? 
                    `<p><strong>Status:</strong> <span class="status-badge status-${item.status}">${item.status}</span></p>
                     <p><strong>Catatan:</strong> ${item.catatan}</p>
                     ${item.processed ? '<p class="processed-status"><em>Item telah diproses</em></p>' : ''}` :
                    `<p><strong>Jumlah:</strong> ${item.jumlah}</p>
                     <p><strong>Supplier:</strong> ${item.supplier}</p>`
                }
            </div>
            <div class="modal-footer button-group">
                ${actionButton}
                <button class="btn btn-secondary btn-icon" onclick="closeModal()">
                    <i class="fas fa-times"></i> Tutup
                </button>
            </div>
        `;
    } catch (error) {
        console.error('Error:', error);
    }
}

// Send item to logistics service
async function sendToLogistics(id) {
    try {
        const item = DUMMY_DATA.details[id];
        if (!item) return;

        // Update status processed
        item.processed = true;
        const resultItem = DUMMY_DATA.results.find(i => i.id === id);
        if (resultItem) {
            resultItem.processed = true;
        }

        // Simulasi pengiriman ke logistics service
        console.log('Mengirim ke logistik:', item);
        
        // Di implementasi nyata, akan memanggil API logistics service
        // await fetch(`${LOGISTICS_URL}/receive`, {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify(item)
        // });

        showNotification(`${item.nama} berhasil dikirim ke layanan logistik`, 'success');
        closeModal();
        updateTable('results');
    } catch (error) {
        console.error('Error sending to logistics:', error);
        showNotification('Gagal mengirim ke layanan logistik', 'error');
    }
}

// Return item to inventory
async function returnToInventory(id) {
    try {
        const item = DUMMY_DATA.details[id];
        if (!item) return;

        // Update status processed
        item.processed = true;
        const resultItem = DUMMY_DATA.results.find(i => i.id === id);
        if (resultItem) {
            resultItem.processed = true;
        }

        // Simulasi pengembalian ke inventory
        console.log('Mengembalikan ke inventory:', item);
        
        // Di implementasi nyata, akan memanggil API inventory service
        // await fetch(`${INVENTORY_URL}/return`, {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify(item)
        // });

        showNotification(`${item.nama} berhasil dikembalikan ke inventory`, 'success');
        closeModal();
        updateTable('results');
    } catch (error) {
        console.error('Error returning to inventory:', error);
        showNotification('Gagal mengembalikan ke inventory', 'error');
    }
}

// Submit QC form
async function submitQC(event) {
    event.preventDefault();
    const form = event.target;
    const data = {
        id: form.itemId.value,
        nama: form.itemName.value,
        status: form.status.value,
        catatan: form.notes.value,
        processed: false
    };
    
    try {
        // Update dummy data
        const item = DUMMY_DATA.details[data.id];
        if (item) {
            item.status = data.status;
            item.catatan = data.catatan;
            item.processed = false;
        }

        // Remove from pending
        DUMMY_DATA.pending = DUMMY_DATA.pending.filter(i => i.id !== data.id);
        
        // Add to results
        DUMMY_DATA.results.unshift({
            id: data.id,
            tanggal: item.tanggal,
            nama: item.nama,
            status: data.status,
            processed: false
        });

        showNotification('Pemeriksaan berhasil disimpan', 'success');
        form.reset();
        updateTable('pending');
        updateTable('results');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Gagal menyimpan pemeriksaan', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }, 100);
}

// Helper functions
function formatDate(date) {
    return new Date(date).toLocaleDateString('id-ID', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function closeModal() {
    document.getElementById('detailModal').style.display = 'none';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateTable('pending');
    updateTable('results');
    document.getElementById('qcForm').addEventListener('submit', submitQC);
});