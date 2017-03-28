import os
import asyncio

from flask import Flask
from xanmel import Xanmel

from .map_rating import map_rating


def create_app():
    app = Flask(__name__)
    env_type = os.environ.get('XANMEL_WEB_ENV', 'Dev')
    app.config.from_object('xanmel_web.config.' + env_type)
    app.xanmel = Xanmel(asyncio.get_event_loop(), app.config['XANMEL_CONFIG'])
    app.register_blueprint(map_rating)
    app.servers = {}
    for i in app.xanmel.config['modules']['xanmel.modules.xonotic.XonoticModule']['servers']:
        app.servers[i['unique_id']] = i['name']
    return app


app = create_app()
