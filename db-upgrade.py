# -*- coding: utf-8 -*-
""" Database schema and data updates.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask_script as fes
from publicprize.controller import db
import publicprize.auth.model as pam
import publicprize.controller as ppc
import publicprize.nextup.model as pnm


# Needs to be explicit
ppc.init()
_MANAGER = fes.Manager(ppc.app())


@_MANAGER.command
def clear_all_sessions():
    """Logs out all users - clears all user session state from db."""
    db.get_engine(ppc.app()).execute('DELETE FROM beaker_cache')


@_MANAGER.command
def nextup_tables():
    """Creates NextUp contest tables."""
    pnm.NUContest.__table__.create(bind=db.get_engine(ppc.app()))
    pnm.Nominee.__table__.create(bind=db.get_engine(ppc.app()))
    pnm.Nominator.__table__.create(bind=db.get_engine(ppc.app()))


@_MANAGER.command
def nextup_data():
    """Creates the NextUp contest data."""
    nucontest = pnm.NUContest(
        display_name="Next Up"
    )
    db.session.add(nucontest)
    db.session.flush()
    db.session.add(pam.BivAlias(
        biv_id=nucontest.biv_id,
        alias_name="next-up"
    ))


@_MANAGER.command
def upgrade_nuvote_table():
    """Adds table for NUVote model."""
    pnm.NUVote.__table__.create(bind=db.get_engine(ppc.app()))


@_MANAGER.command
def upgrade_nextup_nominee():
    """Adds nominee.category"""
    _add_enum_type('nominee_category', ['unknown', 'pint', 'pitcher'])
    _add_column(pnm.Nominee, pnm.Nominee.category, "'unknown'")


def _add_column(model, column, default_value=None):
    """Adds the column to the database. Sets default_value if column
    is not nullable."""
    engine = db.get_engine(ppc.app())
    colname = column.description
    coltype = column.type.compile(engine.dialect)
    table = model.__table__.description
    engine.execute(
        'ALTER TABLE {} ADD COLUMN {} {}'.format(table, colname, coltype))
    if not column.nullable:
        if default_value is None:
            raise Exception('NOT_NULL column missing default value')
        engine.execute(
            'UPDATE {} SET {} = {}'.format(table, colname, default_value))
        engine.execute(
            'ALTER TABLE {} ALTER COLUMN {} SET NOT NULL'.format(
                table, colname))

def _add_enum_type(type_name, values):
    """Adds an enum type to the database."""
    #CREATE TYPE bug_status AS ENUM ('new', 'open', 'closed');
    db.get_engine(ppc.app()).execute('CREATE TYPE {} AS ENUM ({})'.format(
            type_name,
            ','.join(list(map((lambda x: "'{}'".format(x)), values)))))

if __name__ == '__main__':
    _MANAGER.run()
