# Copyright (c) 2014 bivio Software, Inc.  All rights reserved.

from publicprize import biv
from publicprize import controller
from publicprize.controller import db
from sqlalchemy import UniqueConstraint

class BivAccess(db.Model, controller.Model):
    source_biv_id = db.Column(db.Numeric(18), primary_key=True)
    target_biv_id = db.Column(db.Numeric(18), primary_key=True)

class User(db.Model, controller.Model):
    # don't conflict with postgres "user" table
    __tablename__ = 'user_t'
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('user_s', start=1006, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    oauth_type = db.Column(
        db.Enum('facebook', 'linkedin', 'google', 'test', name='oauth_type'),
        nullable=False
    )
    oauth_id = db.Column(db.String(100), nullable=False)
    __table_args__ = (UniqueConstraint('oauth_type', 'oauth_id'),)

BivAccess.BIV_MARKER = biv.register_marker(5, BivAccess)
User.BIV_MARKER = biv.register_marker(6, User)
