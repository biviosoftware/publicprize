# -*- coding: utf-8 -*-
""" The controller routes all requests to the appropriate task module.
Also contains superclasses for Task and Model.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import importlib
import inspect
import locale
import os
import re
import sys

from beaker.middleware import SessionMiddleware
from flask_sqlalchemy import SQLAlchemy
import flask
import flask.sessions
import flask_mail
import flask_mobility
import urllib.parse
import werkzeug.exceptions

from . import biv
from . import config
from . import debug
from .debug import pp_t

db = None

def app():
    """Singleton app instance"""
    return _app


def init():
    """Initialize class maps.

    Must be done externally, because of circular import from
    components.
    """
    for name in ['general', 'contest', 'evc', 'nextup']:
        module_prefix = 'publicprize.' + name + '.'
        importlib.import_module(module_prefix + _MODEL_MODULE)
        importlib.import_module(module_prefix + _TASK_MODULE)


def mail():
    """Singleton mail instance."""
    return _mail


class Task(object):
    """Provides the actions for a Model"""

    def __init__(self):
        pass

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
_app.config.from_object(config.Config)
debug.init(_app)
BeakerSession(_app)
_mail = flask_mail.Mail(_app)
flask_mobility.Mobility(_app)
db = SQLAlchemy(_app)


def _action_uri_to_function(name, biv_obj):
    """Returns the task function for the uri."""
    pp_t('name={}, biv_obj={}', [name, biv_obj])
    name = re.sub(r'\W', '_', name)
    name = _ACTION_METHOD_PREFIX + name
    if not hasattr(biv_obj.task_class, name):
        pp_t('{}: does not exist in {}', [name, biv_obj])
        werkzeug.exceptions.abort(404)
    func = getattr(biv_obj.task_class, name)
    assert inspect.isfunction(func), name + ': action not a function in ' + biv_obj
    return func


def _dispatch_action(name, biv_obj):
    """Returns the task function for the uri. Returns the "index" action if
    there is no uri."""
    if len(name) == 0:
        name = _DEFAULT_ACTION_NAME
    return _action_uri_to_function(name, biv_obj)(biv_obj)


def _parse_path(path):
    """Split the path into the (object, action, path_info) parts."""
    pp_t('path={}', [path])
    parts = path.split('/', 2)
    biv_uri = parts[0] if len(parts) >= 1 else biv.URI_FOR_NONE
    action = parts[1] if len(parts) >= 2 else _DEFAULT_ACTION_NAME
    path_info = parts[2] if len(parts) >= 3 else None
    pp_t('biv_uri={} action={} path_info={}', [biv_uri, action, path_info])
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
    flask.request.pp_request = {
        'biv_obj': biv_obj,
        'action': action,
        'path_info': path_info}
    return _dispatch_action(action, biv_obj)


@_app.errorhandler(403)
def _route_403(_):
    """Forbidden error page."""
    return _route(biv.URI_FOR_ERROR + '/' + 'forbidden')


@_app.errorhandler(404)
def _route_404(_):
    """Not found page."""
    return _route(biv.URI_FOR_ERROR + '/' + 'not-found')


@_app.route('/favicon.ico')
def _route_favicon():
    """Routes to favicon.ico file."""
    return flask.send_from_directory(
        os.path.join(_app.root_path, 'static/img'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )


@_app.route("/")
def _route_root():
    """Routes to index."""
    return _route('')


@_app.template_filter('pp_amount')
def _template_filter_pp_amount(amount, precision):
    """Jinja2 filter for amount format"""
    return locale.format('%.{}f'.format(precision), amount, grouping=True)
