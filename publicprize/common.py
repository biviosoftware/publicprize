# -*- coding: utf-8 -*-
""" Common model classes and methods.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import decimal
import flask
import functools
import inspect
import locale
import re
import socket
import sqlalchemy
import sys
import urllib.parse
import urllib.request
import werkzeug.exceptions

from . import controller as ppc
from . import biv


def decorator_login_required(func):
    """Method decorator which requires a logged in user."""
    @functools.wraps(func)
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


def decorator_user_is_admin(func):
    """Require the current user is an administrator."""
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        """Forbidden unless allowed."""
        import publicprize.auth.model
        if publicprize.auth.model.Admin.is_admin():
            return func(*args, **kwargs)
        werkzeug.exceptions.abort(403)
    return decorated_function


def decorator_user_is_judge(func):
    """Require the current user is a contest judge."""
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        """Forbidden unless allowed."""
        if args[0].is_judge():
            return func(*args, **kwargs)
        werkzeug.exceptions.abort(403)
    return decorated_function


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
            re.sub(ppc._MODEL_MODULE_RE, ppc._TASK_MODULE, module_name)]
        self.__default_task_class = getattr(module, self.__class__.__name__)
        assert inspect.isclass(self.__default_task_class)
        return self.__default_task_class

    def assert_action_uri(self, action_uri):
        """Verify action_uri is a valid action on self"""
        ppc._action_uri_to_function(action_uri, self)

    def format_absolute_uri(self, action=None):
        """Create an absolute URI for a model action."""
        return flask.url_for(
            '_route',
            path=self.format_uri(action),
            _external=True,
            _scheme=(
                'http' if ppc.app().config['PUBLICPRIZE']['TEST_MODE']
                else 'https')
        )

    def format_uri(
            self, action_uri=None, path_info=None, query=None,
            preserve_next=False, next=None, anchor=None):
        """Creates a URI for this biv_obj appending action and path_info"""
        biv_id = biv.Id(self.biv_id)
        uri = '/' + biv_id.to_biv_uri()
        if action_uri is not None:
            self.assert_action_uri(action_uri)
            uri += '/' + action_uri
        if path_info is not None:
            assert action_uri is not None, path_info \
                + ': path_info requires an action_uri'
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
        if anchor:
            uri += '#' + anchor
        return uri

    def _asdict(self):
        """Called by flask.jsonify to serialize the model."""
        # simplejson must be install for this to get called
        res = {}
        for key in self.__mapper__.c.keys():
            v = getattr(self, key)
            #TODO(pjm): ugly
            if re.search(key, 'biv_id'):
                v = biv.Id(v).to_biv_uri()
            elif isinstance(v, decimal.Decimal):
                v = str(v)
            elif isinstance(v, biv.Id):
                v = biv_id.to_biv_uri()
            elif isinstance(v, bytes):
                continue
            res[key] = v
        return res

    def __repr__(self):
        try:
            n = ''
            if hasattr(self, 'biv_id') and self.biv_id:
                n = str(self.biv_id)
            if hasattr(self, 'display_name') and self.display_name:
                n += (', ' if n else '') + str(self.display_name[:30])
            return '{}.{}({})'.format(
                self.__class__.__module__,
                self.__class__.__name__,
                n)
        except TypeError as e:
            return object.__repr__(self)

    def __str__(self):
        return self.__repr__()

class ModelWithDates(Model):
    """Model superclass with create/update datetime fields.

    Fields:
        creation_date_time: date the record was inserted
        modified_date_time: date the record was last updated
    """

    creation_date_time = ppc.db.Column(
        ppc.db.DateTime,
        nullable=False,
        server_default=sqlalchemy.text('current_timestamp')
    )
    modified_date_time = ppc.db.Column(
        ppc.db.DateTime,
        onupdate=sqlalchemy.text('current_timestamp')
    )

class Template(object):
    """Render html templates based on the template_dir.
    """

    def __init__(self, template_dir):
        self.template_dir = template_dir

    def base_template(self, name):
        """Get base defaults to contest"""
        return ppc.app().jinja_env.get_template(
            self.template_dir + '/' + name + '.html')

    def render_template(self, biv_obj, name, **kwargs):
        """Render the page, putting the selected menu and contest in env"""
        if 'selected_menu_action' not in kwargs:
            kwargs['selected_menu_action'] = name
        return flask.render_template(
            self._template_name(name),
            contest=biv_obj,
            base_template=self.base_template('contest'),
            **kwargs
        )

    def _template_name(self, name):
        """Render template name based on local package"""
        return '{pkg}/{base}.html'.format(base=name, pkg=self.template_dir)


def get_url_content(url, want_decode=True):
    """Performs a HTTP GET on the url, returns the HTML content.

    Returns None if the url is invalid or not-found"""
    res = None
    try:
        res = get_url_request(url).read()
        if want_decode:
            res = res.decode(locale.getlocale()[1])
    except urllib.request.URLError:
        return None
    except ValueError:
        return None
    except socket.timeout:
        return None
    return res


def get_url_request(url):
    """Performs a HTTP GET on the url, returns the response object.

    Throws exceptions URLError, ValueError or socket.timeout on error."""
    url = normalize_url(url);
    # spoof user-agent to prevent robot blocking
    opener = urllib.request.build_opener()
    opener.addheaders = [
        (
            'User-agent',
            'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko'
            ),
        (
            'Accept',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            )]
    return opener.open(url, None, 30)


def log_form_errors(form, is_json=False):
    """Put any form errors in logs as warning"""
    if form.errors:
        ppc.app().logger.warn({
            'data': flask.request.get_json() if is_json else flask.request.form,
            'errors': form.errors,
        })


def normalize_url(url):
    """Adds leading http:// to url if missing."""
    if not re.search(r'^http', url, re.IGNORECASE):
        url = 'http://' + url
    return url


def safe_unicode(str):
    """Strip non-ascii characters out of a unicode string."""
    return str.encode("ascii", "replace").decode("utf-8")


def summary_text(text):
    """Returns the first few sentences of the supplied text."""
    match = re.search(
        r'^(.*?\s[a-z)]{3,}\.\s.*?\s[a-z)]{3,}[.!]+\s)',
        text,
        re.DOTALL
    )
    if match:
        return match.group(1)
    return text
