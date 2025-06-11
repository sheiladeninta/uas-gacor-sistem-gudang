from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Root route mengarah ke frontend QC
@app.route('/')
def index():
    return send_from_directory('frontend/qc', 'index.html')

# Serve static files dari folder frontend/qc
@app.route('/frontend/qc/<path:path>')
def serve_static(path):
    return send_from_directory('frontend/qc', path)

# API Documentation route
@app.route('/api')
def api_documentation():
    return jsonify({
        "service": "Quality Control Service",
        "description": "Layanan untuk manajemen pemeriksaan kualitas barang di gudang",
        "endpoints": {
            "create_qc": "/api/qc",
            "get_qc": "/api/qc/<qc_id>",
            "list_qc": "/api/qc",
            "approve_qc": "/api/qc/<qc_id>/approve",
            "item_history": "/api/qc/item/<item_id>/history"
        },
        "features": {
            "capabilities": [
                "Pencatatan hasil pemeriksaan kualitas untuk setiap barang",
                "Pelacakan riwayat pemeriksaan per item",
                "Pencatatan detail kondisi penyimpanan (suhu & kelembaban)",
                "Sistem persetujuan hasil pemeriksaan",
                "Pelaporan dan penyaringan hasil pemeriksaan",
                "Integrasi dengan sistem inventori"
            ],
            "quality_check_types": [
                "Pemeriksaan Kedatangan Barang",
                "Audit Stok Berkala",
                "Pemeriksaan Pengiriman"
            ],
            "condition_types": [
                "Layak - Kondisi barang memenuhi standar",
                "Rusak - Terdapat kerusakan pada barang",
                "Kedaluwarsa - Barang sudah melewati masa berlaku"
            ]
        }
    })

# QC Endpoints
@app.route('/api/qc', methods=['GET', 'POST'])
def qc():
    if request.method == 'POST':
        # Handle create QC
        return jsonify({"message": "QC created successfully"})
    else:
        # Handle list QC
        return jsonify([
            {
                "id": 1,
                "item_id": 123,
                "check_type": "kedatangan",
                "condition": "layak",
                "quantity_checked": 50,
                "status": "pending"
            }
        ])

@app.route('/api/qc/<int:qc_id>', methods=['GET'])
def get_qc(qc_id):
    return jsonify({
        "id": qc_id,
        "item_id": 123,
        "check_type": "kedatangan",
        "condition": "layak",
        "quantity_checked": 50,
        "batch_number": "B123-456",
        "notes": "Pemeriksaan rutin",
        "status": "pending"
    })

@app.route('/api/qc/<int:qc_id>/approve', methods=['POST'])
def approve_qc(qc_id):
    return jsonify({"message": f"QC {qc_id} approved successfully"})

@app.route('/api/qc/item/<int:item_id>/history', methods=['GET'])
def item_history(item_id):
    return jsonify([
        {
            "id": 1,
            "check_type": "kedatangan",
            "condition": "layak",
            "quantity_checked": 50,
            "date": "2023-12-01",
            "status": "approved"
        }
    ])

if __name__ == '__main__':
    app.run(debug=True, port=5000) 