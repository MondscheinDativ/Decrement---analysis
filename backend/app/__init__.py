from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import init_extensions
from .routes import register_blueprints


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS for local dev & Github Pages
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    init_extensions(app)
    register_blueprints(app)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app
