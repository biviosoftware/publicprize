# -*- coding: utf-8 -*-
""" Database schema and data updates.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask_script as fes
from publicprize.controller import db
import publicprize.auth.model as pam
import publicprize.contest.model as pcm
import publicprize.controller as ppc

# Needs to be explicit
ppc.init()
_MANAGER = fes.Manager(ppc.app())


@_MANAGER.command
def add_contest_column():
    """Adds Contest.is_scoring_completed."""
    _add_column(pcm.Contest, pcm.Contest.is_scoring_completed, False)


@_MANAGER.command
def admin_table():
    """Creates database table for Admin model."""
    pam.Admin.__table__.create(bind=db.get_engine(ppc.app()))


@_MANAGER.command
def judge_tables():
    """Creates database tables for Judge and JudgeScore models."""
    pcm.Judge.__table__.create(bind=db.get_engine(ppc.app()))
    pcm.JudgeScore.__table__.create(bind=db.get_engine(ppc.app()))


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

if __name__ == '__main__':
    _MANAGER.run()
