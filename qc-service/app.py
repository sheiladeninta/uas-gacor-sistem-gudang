import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_graphql import GraphQLView
from flask_cors import CORS
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from datetime import datetime
from enum import Enum

# Inisialisasi Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Tentukan folder instance dan pastikan file db berada di dalamnya
db_path = os.path.join(app.instance_path, 'qc_service.db')

# Gunakan os.path.abspath() untuk mendapatkan path absolut yang valid
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(db_path)}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Pastikan folder instance ada
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# Model Database untuk QC
class QCLog(db.Model):
    __tablename__ = 'qc_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<QCLog {self.order_id} - {self.item_code}>"

# Enum untuk status pengiriman
class QCStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED" 
    REJECTED = "REJECTED"

# GraphQL Type untuk QCLog
class QCLogType(SQLAlchemyObjectType):
    class Meta:
        model = QCLog
        fields = ('id', 'order_id', 'item_code', 'quantity', 'status', 'created_at')

# Query untuk mendapatkan data QCLog
class Query(graphene.ObjectType):
    qc_logs = graphene.List(QCLogType)
    
    def resolve_qc_logs(self, info):
        return QCLog.query.all()

# Mutation untuk mengirim item ke QC
class SendToQC(graphene.Mutation):
    class Arguments:
        order_id = graphene.Int()
        item_code = graphene.String()
        item_name = graphene.String()
        quantity = graphene.Int()

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, order_id, item_code, item_name, quantity):
        try:
            qc_log = QCLog(
                order_id=order_id,
                item_code=item_code,
                item_name=item_name,
                requested_quantity=quantity,
                unit="pcs",  # Example unit
            )
            db.session.add(qc_log)
            db.session.commit()

            return SendToQC(success=True, message="Order sent to QC successfully.")
        except Exception as e:
            db.session.rollback()
            return SendToQC(success=False, message=str(e))


# GraphQL Mutation untuk QC Service
class Mutation(graphene.ObjectType):
    send_to_qc = SendToQC.Field()

# Membuat schema GraphQL
schema = graphene.Schema(query=Query, mutation=Mutation)

# Menambahkan endpoint GraphQL ke Flask
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)

# Endpoint untuk health check
@app.route('/health', methods=['GET'])
def health_check():
    return 'QC Service is running', 200

# Menjalankan aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat database dan tabel jika belum ada
    app.run(debug=True, host='0.0.0.0', port=5003)
