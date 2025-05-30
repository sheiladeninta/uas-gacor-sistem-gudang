from flask import Flask
from config import Config
from db import db
from flask_graphql import GraphQLView
from schema import schema

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # Tambahkan endpoint GraphQL di sini
    app.add_url_rule(
        '/graphql',
        view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
    )

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5002)

@app.route('/')
def index():
    return 'Inventory Service is Running - Go to /graphql'
