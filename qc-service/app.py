from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
import graphene
from datetime import datetime
import os

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# GraphQL Schema
class QualityCheck(graphene.ObjectType):
    id = graphene.Int()
    item_id = graphene.Int()
    check_type = graphene.String()
    condition = graphene.String()
    quantity_checked = graphene.Int()
    batch_number = graphene.String()
    notes = graphene.String()
    status = graphene.String()
    checked_at = graphene.String()

class CreateQualityCheckInput(graphene.InputObjectType):
    item_id = graphene.Int(required=True)
    check_type = graphene.String(required=True)
    condition = graphene.String(required=True)
    quantity_checked = graphene.Int(required=True)
    batch_number = graphene.String()
    notes = graphene.String()

class CreateQualityCheck(graphene.Mutation):
    class Arguments:
        input = CreateQualityCheckInput(required=True)

    quality_check = graphene.Field(QualityCheck)

    def mutate(root, info, input):
        qc = QualityCheck(
            id=1,  # In a real app, this would be generated
            item_id=input.item_id,
            check_type=input.check_type,
            condition=input.condition,
            quantity_checked=input.quantity_checked,
            batch_number=input.batch_number,
            notes=input.notes,
            status="pending",
            checked_at=datetime.now().isoformat()
        )
        return CreateQualityCheck(quality_check=qc)

class ApproveQualityCheck(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    quality_check = graphene.Field(QualityCheck)

    def mutate(root, info, id):
        # In a real app, we would fetch and update the QC
        qc = QualityCheck(
            id=id,
            status="approved",
            checked_at=datetime.now().isoformat()
        )
        return ApproveQualityCheck(quality_check=qc)

class Query(graphene.ObjectType):
    quality_checks = graphene.List(QualityCheck)
    quality_check = graphene.Field(QualityCheck, id=graphene.Int())
    item_history = graphene.List(QualityCheck, item_id=graphene.Int())

    def resolve_quality_checks(root, info):
        # Mock data - in a real app, this would fetch from database
        return [
            QualityCheck(
                id=1,
                item_id=123,
                check_type="kedatangan",
                condition="layak",
                quantity_checked=50,
                batch_number="B123-456",
                notes="Pemeriksaan rutin",
                status="pending",
                checked_at=datetime.now().isoformat()
            )
        ]

    def resolve_quality_check(root, info, id):
        # Mock data - in a real app, this would fetch from database
        return QualityCheck(
            id=id,
            item_id=123,
            check_type="kedatangan",
            condition="layak",
            quantity_checked=50,
            batch_number="B123-456",
            notes="Pemeriksaan rutin",
            status="pending",
            checked_at=datetime.now().isoformat()
        )

    def resolve_item_history(root, info, item_id):
        # Mock data - in a real app, this would fetch from database
        return [
            QualityCheck(
                id=1,
                item_id=item_id,
                check_type="kedatangan",
                condition="layak",
                quantity_checked=50,
                status="approved",
                checked_at=datetime.now().isoformat()
            )
        ]

class Mutation(graphene.ObjectType):
    create_quality_check = CreateQualityCheck.Field()
    approve_quality_check = ApproveQualityCheck.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

# GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enable GraphiQL interface
    )
)

# Root route mengarah ke frontend QC
@app.route('/')
def index():
    return send_from_directory('../frontend/qc', 'index.html')

# Serve static files dari folder frontend/qc
@app.route('/frontend/qc/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend/qc', path)

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
            "item_history": "/api/qc/item/<item_id>/history",
            "graphql": "/graphql"
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
