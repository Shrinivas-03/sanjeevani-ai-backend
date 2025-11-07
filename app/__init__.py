from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from config import Config
from supabase import create_client

supabase = None
mail = None


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    CORS(app)

    global supabase, mail
    supabase = create_client(app.config["SUPABASE_URL"], app.config["SUPABASE_KEY"])
    mail = Mail(app)

    # Register blueprints here
    from .routes.auth import auth_bp

    app.register_blueprint(auth_bp)

    from .routes.rag import rag_bp

    app.register_blueprint(rag_bp)

    return app
