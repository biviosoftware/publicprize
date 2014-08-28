# Copyright (c) 2014 bivio Software, Inc.  All rights reserved.

from publicprize import biv
from publicprize import config
from beaker.middleware import SessionMiddleware
import flask
from flask.ext.sqlalchemy import SQLAlchemy
import flask.sessions
import importlib
import inspect
import re
import sys

db = None

def app():
    return _app

def init():
    """Initialize class maps.

    Must be done externally, because of circular import from
    components.
    """
    for cn in ['general', 'contest']:
        cm = 'publicprize.' + cn + '.';
        importlib.import_module(cm + _MODEL_MODULE)
        importlib.import_module(cm + _TASK_MODULE)

def session():
    return flask.request.environ['beaker.session']

class Task(object):

    def __init__(self):
        pass

class Model(object):

    @classmethod
    def load_biv_obj(cls, biv_id):
        return cls.query.filter_by(biv_id=biv_id).first_or_404()

    @property
    def task_class(self):
        if hasattr(self, '__default_task_class'):
            return self.__default_task_class
        mn = self.__module__
        m = sys.modules[re.sub(_MODEL_MODULE_RE, _TASK_MODULE, mn)]
        self.__default_task_class = getattr(m, self.__class__.__name__)
        assert inspect.isclass(self.__default_task_class)
        return self.__default_task_class

    def format_uri(self, path):
        return '/' + biv.id_to_uri(self.biv_id) + '/' + path

class BeakerSessionInterface(flask.sessions.SessionInterface):
    def init_app(app):
        app.wsgi_app = SessionMiddleware(
            app.wsgi_app,
            {
                'session.type': 'ext:database',
                'session.url': app.config['SQLALCHEMY_DATABASE_URI'],
                'session.lock_dir': '/tmp/cache/lock',
            }
        )
        app.session_interface = BeakerSessionInterface()

    def open_session(self, app, request):
        return request.environ.get('beaker.session')

    def save_session(self, app, session, response):
        session.save()

_ACTION_METHOD_PREFIX = 'action_'
_DEFAULT_ACTION_NAME = 'index'
_TASK_MODULE = 'task'
_MODEL_MODULE = 'model'
_MODEL_MODULE_RE = r'(?<=\.)' + _MODEL_MODULE + r'$'
_app = flask.Flask(__name__, template_folder='.')
_app.config.from_object(config.DevConfig)
BeakerSessionInterface.init_app(_app)
db = SQLAlchemy(_app)

def _dispatch_action(name, biv_obj):
    if len(name) == 0:
        name = _DEFAULT_ACTION_NAME
    name = re.sub('\W', '_', name)
    name = _ACTION_METHOD_PREFIX + name
    f = getattr(biv_obj.task_class, name)
    if not inspect.isfunction(f):
        raise ValueError(name + ': action not a method')
    return f(biv_obj)

def _parse_path(path):
    parts = path.split('/', 2)
    biv_uri = parts[0] if len(parts) >= 1 else biv.URI_FOR_NONE
    action = parts[1] if len(parts) >= 2 else _DEFAULT_ACTION_NAME
    path_info = parts[2] if len(parts) >= 3 else None
    return biv.load_obj(biv_uri), action, path_info

@_app.route("/<path:path>")
def _route(path):
    # request_context
    biv_obj, action, path_info = _parse_path(path)
    return _dispatch_action(action, biv_obj)

@_app.errorhandler(404)
def _route_404(e):
    return _route(biv.URI_FOR_ERROR + '/' + 'not-found')

@_app.route("/")
def _route_root():
    return _route('')
