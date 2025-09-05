from flask import Blueprint
from .datasets import bp as datasets_bp
from .data_sources import bp as sources_bp
from .cleaning import bp as cleaning_bp
from .models import bp as models_bp
from .report import bp as report_bp
from .compare import bp as compare_bp


def register_blueprints(app):
    app.register_blueprint(datasets_bp, url_prefix="/api")
    app.register_blueprint(sources_bp, url_prefix="/api")
    app.register_blueprint(cleaning_bp, url_prefix="/api")
    app.register_blueprint(models_bp, url_prefix="/api")
    app.register_blueprint(compare_bp, url_prefix="/api")
    app.register_blueprint(report_bp, url_prefix="/api")
