# -*- coding: utf-8 -*-
""" Database schema and data updates.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask_script as fes
from publicprize.controller import db
import publicprize.auth.model as pam
import publicprize.controller as ppc
import publicprize.contest.model as pcm
import publicprize.evc2015.model as pe15


# Needs to be explicit
ppc.init()
_MANAGER = fes.Manager(ppc.app())


@_MANAGER.command
def upgrade_common_vote():
    engine = db.get_engine(ppc.app())
    engine.execute('ALTER TABLE nu_vote DROP CONSTRAINT nu_vote_nominee_fkey')
    engine.execute('ALTER TABLE nu_vote RENAME TO vote')
    engine.execute('ALTER SEQUENCE nuvote_s RENAME TO vote_s')
    engine.execute('ALTER TABLE vote RENAME COLUMN nominee TO nominee_biv_id')


@_MANAGER.command
def upgrade_e15_tables():
    pe15.E15Contest.__table__.create(bind=db.get_engine(ppc.app()))
    pe15.E15Nominee.__table__.create(bind=db.get_engine(ppc.app()))


@_MANAGER.command
def upgrade_e15_data():
    old_contest = pam.BivAlias.query.filter_by(
        alias_name='esprit-venture-challenge'
    ).first()
    old_contest.alias_name = 'esprit-venture-challenge-2014'
    db.session.add(old_contest)
    contest = pe15.E15Contest(
        display_name='Exprit Venture Challenge',
        end_date='2015-11-07',
    )
    db.session.add(contest)
    db.session.flush()
    db.session.add(pam.BivAlias(
        biv_id=contest.biv_id,
        alias_name='esprit-venture-challenge',
    ))


@_MANAGER.command
def upgrade_image_schema():
    engine = db.get_engine(ppc.app())
    engine.execute('ALTER TABLE contest DROP COLUMN contest_logo')
    engine.execute('ALTER TABLE contest DROP COLUMN logo_type')
    pcm.Image.__table__.create(bind=engine)
    _add_column(pcm.Founder, pcm.Founder.image_biv_id)
    _add_column(pcm.Sponsor, pcm.Sponsor.image_biv_id)
    for sponsor in pcm.Sponsor.query.all():
        print('sponsor ', sponsor.biv_id, ' ', sponsor.display_name)
        image = pcm.Image(
            image_data=sponsor.sponsor_logo,
            image_type=sponsor.logo_type,
        )
        db.session.add(image)
        db.session.flush()
        sponsor.image_biv_id = image.biv_id
        db.session.add(sponsor)

    for founder in pcm.Founder.query.all():
        print('founder ', founder.biv_id, ' ', founder.display_name)
        image = pcm.Image(
            image_data=founder.founder_avatar,
            image_type=founder.avatar_type,
        )
        db.session.add(image)
        db.session.flush()
        founder.image_biv_id = image.biv_id
        db.session.add(founder)


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
