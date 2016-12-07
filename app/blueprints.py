from flask import Blueprint

main = Blueprint('main', __name__)
open_id = Blueprint('open_id', __name__)


def register_main_bp(app):
    from app import views
    app.register_blueprint(main, url_prefix='/')


def register_open_id_bp(app):
    from app import views
    app.register_blueprint(open_id, url_prefix='/')
