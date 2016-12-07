from flask import Flask, g, session
from login import LoginHandler
import config
from flask_mongoengine import MongoEngine
from app.whopenid import OpenId
from flask_openid import OpenID
from openid.extensions import pape
from app.blueprints import register_main_bp, register_open_id_bp
from app.models import Users
from mongoengine import connection
from flask_socketio import SocketIO, emit
from gevent import monkey
import os
import sys

app = Flask(__name__)
oid = OpenID(app, safe_roots=[],
             extension_responses=[pape.Response])
login_manager = LoginHandler()
socket_io = SocketIO(app, async_mode='threading')
monkey.patch_all()


def create_app():
    register_main_bp(app)
    app.config.from_object(config.DevelopmentConfig)
    app.before_request(register_db())
    login_manager.init(app)
    app.teardown_request(close_database)
    return app


def register_db():
    def load():
        MongoEngine(app)
    return load


def close_database(exception):
    def disconnect():
        connection.disconnect()
    return disconnect


@login_manager.load_user
def load_user(user_id):
    g.user = None
    if user_id:
        g.user = Users.objects(id=user_id).first()
    if 'open_id' in session and not g.user:
        g.user = Users.objects(open_id=session['open_id']).first()








