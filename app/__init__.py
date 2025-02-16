from flask import Flask, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()  
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)  
    migrate.init_app(app, db)

    from app.routes import main
    from app.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')

    @app.before_request
    def check_user_logged_in():
        # Define which endpoints are accessible without authentication
        open_endpoints = ['auth.login', 'auth.register']  # Add more if needed

        if 'user_id' not in session and request.endpoint not in open_endpoints:
            return redirect(url_for('auth.login'))

    with app.app_context():  
        db.create_all()  

    return app
