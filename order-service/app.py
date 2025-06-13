import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_graphql import GraphQLView
from flask_cors import CORS
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///D:/Telkom University/kuliah smester 6/IAE/TUBES/TUGAS BESAR/uas-gacor-sistem-gudang-1/order-service/order_service.db'  # Store in instance folder
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

db = SQLAlchemy(app)
CORS(app)

# Models
class QCLog(db.Model):
    __tablename__ = 'qc_logs'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    requested_quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QCLog {self.item_code}: {self.item_name}>'

class QCLogType(SQLAlchemyObjectType):
    class Meta:
        model = QCLog

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
                unit="pcs"  # Default unit
            )
            db.session.add(qc_log)
            db.session.commit()

            return SendToQC(success=True, message="Order sent to QC successfully.")
        except Exception as e:
            db.session.rollback()
            return SendToQC(success=False, message=str(e))

class Query(graphene.ObjectType):
    qc_logs = graphene.List(QCLogType)
    
    def resolve_qc_logs(self, info):
        return QCLog.query.all()

class Mutation(graphene.ObjectType):
    send_to_qc = SendToQC.Field()

# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)

# Adding GraphQL View
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)

# Running the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure the tables are created
    app.run(debug=True)
