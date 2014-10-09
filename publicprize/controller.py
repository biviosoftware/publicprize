# -*- coding: utf-8 -*-
""" The controller routes all requests to the appropriate task module.
Also contains superclasses for Task and Model.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from publicprize import biv
import publicprize.config
from beaker.middleware import SessionMiddleware
import flask
from functools import wraps
import flask_mail
import flask_mobility
from flask_sqlalchemy import SQLAlchemy
import flask.sessions
import importlib
import inspect
import os
import re
import sys
import urllib.parse
import werkzeug.exceptions

db = None


def app():
    """Singleton app instance"""
    return _app


def init():
    """Initialize class maps.

    Must be done externally, because of circular import from
    components.
    """
    for name in ['general', 'contest']:
        module_prefix = 'publicprize.' + name + '.'
        importlib.import_module(module_prefix + _MODEL_MODULE)
        importlib.import_module(module_prefix + _TASK_MODULE)


def login_required(func):
    """Method decorator which requires a logged in user."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        """If user is not logged in, redirects to the appropriate oauth task"""
        if not flask.session.get('user.is_logged_in'):
            uri = flask.g.pub_obj.get_login_uri()
            return flask.redirect(
                uri + '?' + urllib.parse.urlencode({
                    'next': flask.request.url
                })
            )
        return func(*args, **kwargs)
    return decorated_function


def mail():
    """Singleton mail instance."""
    return _mail


class Task(object):
    """Provides the actions for a Model"""

    def __init__(self):
        pass


class Model(object):
    """Provides biv support for Models"""

    @classmethod
    def load_biv_obj(cls, biv_id):
        """Load a biv from the db"""
        return cls.query.filter_by(biv_id=biv_id).first_or_404()

    @property
    def task_class(self):
        """Corresponding Task class for this Model"""
        if hasattr(self, '__default_task_class'):
            return self.__default_task_class
        module_name = self.__module__
        module = sys.modules[
            re.sub(_MODEL_MODULE_RE, _TASK_MODULE, module_name)]
        self.__default_task_class = getattr(module, self.__class__.__name__)
        assert inspect.isclass(self.__default_task_class)
        return self.__default_task_class

    def format_absolute_uri(self, action=None):
        """Create an absolute URI for a model action."""
        return flask.url_for(
            '_route',
            path=self.format_uri(action),
            _external=True,
            _scheme=(
                'http' if app().config['PUBLICPRIZE']['TEST_MODE']
                else 'https')
        )

    def format_uri(self, action=None, path_info=None, query=None,
                   preserve_next=False, next=None):
        """Creates a URI for this biv_obj appending action and path_info"""
        biv_id = biv.Id(self.biv_id)
        uri = '/' + biv_id.to_biv_uri()
        if action is not None:
            _action_uri_to_function(action, self)
            uri += '/' + action
        if path_info is not None:
            assert action is not None, path_info \
                + ': path_info requires an action'
            uri += '/' + path_info
        # TODO(pjm): 'next' handling needs to be refactored
        if preserve_next:
            if not query:
                query = {}
            if 'next' in flask.request.args:
                query['next'] = flask.request.args['next']
            else:
                query['next'] = '/'
        elif next:
            if not query:
                query = {}
            query['next'] = next
        if query:
            uri += '?' + urllib.parse.urlencode(query)
        return uri


class BeakerSession(flask.sessions.SessionInterface):
    """Session management replacement for standard flask session.
    Stores session info in the application database in the beaker_cache
    table."""
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)
        else:
            self.app = None

    def init_app(self, app):
        """Register the session manager with flask."""
        app.wsgi_app = SessionMiddleware(
            app.wsgi_app,
            {
                'session.type': 'ext:database',
                'session.url': app.config['SQLALCHEMY_DATABASE_URI'],
                'session.lock_dir': '/tmp/cache/lock',
                # the cookie key
                'session.key': 'pp',
                'session.cookie_expires': False
            }
        )
        app.session_interface = self

    def open_session(self, app, request):
        """Called by flask to create the session"""
        return request.environ.get('beaker.session')

    def save_session(self, app, session, response):
        """Called by flask to save the session"""
        session.save()

_ACTION_METHOD_PREFIX = 'action_'
_DEFAULT_ACTION_NAME = 'index'
_TASK_MODULE = 'task'
_MODEL_MODULE = 'model'
_MODEL_MODULE_RE = r'(?<=\.)' + _MODEL_MODULE + r'$'
_app = flask.Flask(__name__, template_folder='.')
_app.config.from_object(publicprize.config.Config)
BeakerSession(_app)
_mail = flask_mail.Mail(_app)
flask_mobility.Mobility(_app)
db = SQLAlchemy(_app)


def _action_uri_to_function(name, biv_obj):
    """Returns the task function for the uri."""
    name = re.sub(r'\W', '_', name)
    name = _ACTION_METHOD_PREFIX + name
    if not hasattr(biv_obj.task_class, name):
        werkzeug.exceptions.abort(404)
    func = getattr(biv_obj.task_class, name)
    assert inspect.isfunction(func), name + ': no action for ' + biv_obj.biv_id
    return func


def _dispatch_action(name, biv_obj):
    """Returns the task function for the uri. Returns the "index" action if
    there is no uri."""
    if len(name) == 0:
        name = _DEFAULT_ACTION_NAME
    return _action_uri_to_function(name, biv_obj)(biv_obj)


def _parse_path(path):
    """Split the path into the (object, action, path_info) parts."""
    parts = path.split('/', 2)
    biv_uri = parts[0] if len(parts) >= 1 else biv.URI_FOR_NONE
    action = parts[1] if len(parts) >= 2 else _DEFAULT_ACTION_NAME
    path_info = parts[2] if len(parts) >= 3 else None
    return biv.load_obj(biv_uri), action, path_info


def _register_globals():
    """Load globals onto flask's 'g' variable"""
    import publicprize.general.model
    flask.g.pub_obj = publicprize.general.model.General.load_biv_obj(
        publicprize.general.model.PUB_OBJ)


@_app.route("/<path:path>", methods=('GET', 'POST'))
def _route(path):
    """Routes the uri to the appropriate biv_obj"""
    biv_obj, action, path_info = _parse_path(path)
    _register_globals()
    return _dispatch_action(action, biv_obj)


@_app.errorhandler(404)
def _route_404(_):
    """Not found page."""
    return _route(biv.URI_FOR_ERROR + '/' + 'not-found')


@_app.route("/")
def _route_root():
    """Routes to index."""
    return _route('')


@_app.route('/favicon.ico')
def _favicon():
    """Routes to favicon.ico file."""
    return flask.send_from_directory(
        os.path.join(_app.root_path, 'static/img'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )
