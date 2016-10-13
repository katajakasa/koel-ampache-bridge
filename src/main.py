# -*- coding: utf-8 -*-

from flask import Flask

import mimetypes

from app import route_action
from tables import db
from playback import stream_audio
import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.KOEL_DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = config.DEBUG


# Fix broken implementations :/
@app.route('/server/xml.server.php/server/xml.server.php', methods=['GET'])
def server_dup():
    return route_action()


# Correct server url
@app.route('/server/xml.server.php', methods=['GET'])
def server():
    return route_action()


# Audio streaming functionality
@app.route("/server/custom/play.php", methods=['GET'])
def stream():
    return stream_audio()


def create_app():
    mimetypes.init()
    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.commit()
    return app

if __name__ == '__main__':
    create_app().run()
