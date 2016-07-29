# -*- coding: utf-8 -*-
""" Database schema and data updates.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from publicprize.controller import db
from sqlalchemy import sql
import publicprize.auth.model as pam
import publicprize.controller as ppc


def add_column(model, column, default_value=None):
    """Adds the column to the database. Sets default_value if column
    is not nullable."""
    engine = db.get_engine(ppc.app())
    params = {
        'colname': column.description,
        'coltype': column.type.compile(engine.dialect),
        'table':  model.__table__.description,
        'default': default_value,
    }
    engine.execute(
        sql.text('ALTER TABLE :table ADD COLUMN :colname :coltype'), **params)
    if not column.nullable:
        assert default_value is not None, \
            '{}.{}: NOT_NULL column missing default value'.format(table, colname)
        stmt = sql.text('UPDATE :table SET :colname = :default')
        stmt.bindparams(sql.bindparam('default', type_=column.type))
        engine.execute(stmt, **params)
        engine.execute(
            sql.text('ALTER TABLE :table ALTER COLUMN :colname SET NOT NULL'), **params)


def add_enum_type(type_name, values):
    """Adds an enum type to the database."""
    #CREATE TYPE bug_status AS ENUM ('new', 'open', 'closed');
    engine = db.get_engine(ppc.app())
    params = {
        'type_name': type_name,
    }
    .execute(
        sql.text('CREATE TYPE {} AS ENUM ({})'.format(
            type_name,
            ','.join(list(map((lambda x: "'{}'".format(x)), values)))))


def upgrade_lowercase_user_email():
    """Lowercases User.user_email"""
    users = pam.User.query.all()
    for user in users:
        user.user_email = user.user_email.lower()
        db.session.add(user)
