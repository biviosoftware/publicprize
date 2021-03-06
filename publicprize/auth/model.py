# -*- coding: utf-8 -*-
""" Auth models: BivAccess and User

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
from .. import biv
from .. import common
from .. import controller
from ..controller import db
import sqlalchemy
import werkzeug.exceptions

class Admin(db.Model, common.ModelWithDates):
    """Administrative marker.
    Fields:
        biv_id: primary ID
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('admin_s', start=1010, increment=1000),
        primary_key=True
    )

    def is_admin():
        """Returns True if the logged in user is an admin."""
        if not flask.session.get('user.is_logged_in'):
            return False
        if Admin.query.select_from(BivAccess).filter(
            BivAccess.source_biv_id == flask.session['user.biv_id'],
            BivAccess.target_biv_id == Admin.biv_id
        ).first():
            return True
        return False


class BivAccess(db.Model, common.Model):
    """BivAccess links ownership between models. For example, a Contest model
    owns the Contestants and a User also owns their own Contestant submission.
    Fields:
        source_biv_id: the parent (owner) model
        target_biv_id: the child model
    """
    source_biv_id = db.Column(db.Numeric(18), primary_key=True)
    target_biv_id = db.Column(db.Numeric(18), primary_key=True)

    @classmethod
    def load_biv_obj(cls, biv_id):
        """Can not load this model by biv_id directly."""
        werkzeug.exceptions.abort(404)


class BivAlias(db.Model, common.Model):
    """URI Alias for biv_obj.
    Fields:
        biv_id: primary ID
        alias_name: alias name
    """
    biv_id = db.Column(db.Numeric(18), primary_key=True)
    alias_name = db.Column(db.String(100), nullable=False)
    __table_args__ = (sqlalchemy.UniqueConstraint('alias_name'),)


class User(db.Model, common.ModelWithDates):
    """Logged-in User model.
    Fields:
        biv_id: primary ID
        display_name: user's full name
        user_email: user's email addrses
        oauth_type: the oauth server used to authenticate
        oauth_id: the user ID on the oauth server
        avatar_url: user's avatar
    """
    # don't conflict with postgres "user" table
    __tablename__ = 'user_t'
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('user_s', start=1006, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    # TODO(pjm): want unique constraint on email, will need to handle
    # error cases for multiple oauth_type attempts
    user_email = db.Column(db.String(100), nullable=False)
    oauth_type = db.Column(
        db.Enum('facebook', 'linkedin', 'google', 'test', name='oauth_type'),
        nullable=False
    )
    oauth_id = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(100))
    __table_args__ = (sqlalchemy.UniqueConstraint('oauth_type', 'oauth_id'),)

Admin.BIV_MARKER = biv.register_marker(10, Admin)
BivAccess.BIV_MARKER = biv.register_marker(5, BivAccess)
User.BIV_MARKER = biv.register_marker(6, User)
