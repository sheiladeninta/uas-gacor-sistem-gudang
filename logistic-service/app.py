from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import requests
from datetime import datetime
import uuid
from flask_graphql import GraphQLView
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType

from models import db, Shipment
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app)

# GraphQL Schema
class ShipmentType(SQLAlchemyObjectType):
    class Meta:
        model = Shipment
        interfaces = (graphene.relay.Node,)

class Query(graphene.ObjectType):
    shipments = graphene.List(ShipmentType, status=graphene.String())
    shipment = graphene.Field(ShipmentType, id=graphene.Int(required=True))

    def resolve_shipments(self, info, status=None):
        query = Shipment.query
        if status:
            query = query.filter_by(status=status)
        return query.all()

    def resolve_shipment(self, info, id):
        return Shipment.query.get(id)

class CreateShipmentInput(graphene.InputObjectType):
    qc_id = graphene.Int(required=True)
    order_id = graphene.Int(required=True)
    shipping_address = graphene.String(required=True)
    shipping_service = graphene.String(required=True)
    weight = graphene.Float(required=True)

class CreateShipment(graphene.Mutation):
    class Arguments:
        input = CreateShipmentInput(required=True)

    shipment = graphene.Field(ShipmentType)

    def mutate(self, info, input):
        # Verify QC check exists and is approved
        qc_response = requests.get(f"{app.config['QC_SERVICE_URL']}/api/qc/{input.qc_id}")
        if qc_response.status_code != 200:
            raise Exception('QC check not found or not approved')

        shipment = Shipment(
            qc_id=input.qc_id,
            order_id=input.order_id,
            shipping_address=input.shipping_address,
            shipping_service=input.shipping_service,
            weight=input.weight,
            status='pending'
        )
        
        db.session.add(shipment)
        db.session.commit()
        
        return CreateShipment(shipment=shipment)

class ShipOrder(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    shipment = graphene.Field(ShipmentType)

    def mutate(self, info, id):
        shipment = Shipment.query.get(id)
        if not shipment:
            raise Exception('Shipment not found')
        
        if shipment.status != 'pending':
            raise Exception('Shipment is not in pending status')
        
        shipment.status = 'shipped'
        shipment.shipping_date = datetime.utcnow()
        db.session.commit()
        
        return ShipOrder(shipment=shipment)

class MarkAsDelivered(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    shipment = graphene.Field(ShipmentType)

    def mutate(self, info, id):
        shipment = Shipment.query.get(id)
        if not shipment:
            raise Exception('Shipment not found')
        
        if shipment.status != 'shipped':
            raise Exception('Shipment is not in shipped status')
        
        shipment.status = 'delivered'
        db.session.commit()
        
        return MarkAsDelivered(shipment=shipment)

class Mutation(graphene.ObjectType):
    create_shipment = CreateShipment.Field()
    ship_order = ShipOrder.Field()
    mark_as_delivered = MarkAsDelivered.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)

# Add GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enable GraphiQL interface
    )
)

# Create database tables
with app.app_context():
    db.create_all()

def generate_tracking_number():
    return f"TRK-{uuid.uuid4().hex[:8].upper()}"

@app.route('/api/shipments', methods=['GET'])
# @jwt_required()
def get_shipments():
    status = request.args.get('status')
    query = Shipment.query
    
    if status:
        query = query.filter_by(status=status)
    
    shipments = query.all()
    return jsonify([shipment.to_dict() for shipment in shipments])

@app.route('/api/shipments/<int:shipment_id>', methods=['GET'])
# @jwt_required()
def get_shipment(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    return jsonify(shipment.to_dict())

@app.route('/api/shipments', methods=['POST'])
# @jwt_required()
def create_shipment():
    data = request.get_json()
    print('Menerima data:', data)  # Debug log

    qc_response = requests.get(f"{app.config['QC_SERVICE_URL']}/api/qc/{data['qc_id']}")
    print('QC response:', qc_response.status_code, qc_response.text)  # Debug log
    if qc_response.status_code != 200:
        return jsonify({'error': 'QC check not found or not approved'}), 400

    try:
        shipment = Shipment(
            qc_id=data['qc_id'],
            order_id=data['order_id'],
            shipping_address=data['shipping_address'],
            shipping_service=data['shipping_service'],
            weight=data['weight'],
            status='pending',
            tracking_number=generate_tracking_number()  # Tambahkan jika field ini wajib
        )
        db.session.add(shipment)
        db.session.commit()
        print('Shipment berhasil disimpan:', shipment.to_dict())  # Debug log
        return jsonify(shipment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print('Error saat menyimpan shipment:', str(e))  # Debug log
        return jsonify({'error': str(e)}), 500

@app.route('/api/shipments/<int:shipment_id>/ship', methods=['POST'])
# @jwt_required()
def ship_order(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    
    if shipment.status != 'pending':
        return jsonify({'error': 'Shipment is not in pending status'}), 400
    
    shipment.status = 'shipped'
    shipment.shipping_date = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(shipment.to_dict())

@app.route('/api/shipments/<int:shipment_id>/deliver', methods=['POST'])
# @jwt_required()
def mark_as_delivered(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    
    if shipment.status != 'shipped':
        return jsonify({'error': 'Shipment is not in shipped status'}), 400
    
    shipment.status = 'delivered'
    db.session.commit()
    
    return jsonify(shipment.to_dict())

@app.route('/api/shipments/<int:shipment_id>/receipt', methods=['GET'])
# @jwt_required()
def get_shipping_receipt(shipment_id):
    shipment = Shipment.query.get_or_404(shipment_id)
    # Generate receipt data tanpa detail order
    receipt = {
        'tracking_number': shipment.tracking_number,
        'shipping_date': shipment.shipping_date.isoformat() if shipment.shipping_date else None,
        'shipping_address': shipment.shipping_address,
        'shipping_service': shipment.shipping_service,
        'weight': shipment.weight,
        'status': shipment.status
    }
    
    return jsonify(receipt)

@app.route('/')
def index():
    return "Shipment Service is running! Use /graphql for GraphQL interface or /api/shipments for API endpoints."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
