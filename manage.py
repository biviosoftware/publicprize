# -*- coding: utf-8 -*-
""" Database creation and test data loading

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from publicprize.controller import db
import datetime
import flask
import flask_script as fes
import flask_script.commands
import imghdr
import json
import locale
import os
import publicprize.auth.model as pam
import publicprize.contest.model as pcm
import publicprize.controller as ppc
import re
import subprocess
import urllib.request
import werkzeug.serving

# Needs to be explicit
ppc.init()


# TODO(pjm): ugly hack to get user.biv_id in log message
class BetterLogger(werkzeug.serving.BaseRequestHandler):
    """HTTP access logger which includes user_state."""
    _user_state = None
    app = ppc.app()

    @app.teardown_request
    def _teardown(response):
        user_state = '""'
        if 'user.biv_id' in flask.session:
            user_state = 'l'
            if flask.session['user.is_logged_in']:
                user_state += 'i'
            else:
                user_state += 'o'
            user_state += '-' + str(flask.session['user.biv_id'])
        BetterLogger._user_state = user_state

    def log_request(self, code='-', size='-'):
        self.log('info', '%s "%s" %s %s',
                 BetterLogger._user_state, self.requestline, code, size)


class RunServerWithBetterLogger(flask_script.commands.Server):
    """Override default Server command class to add BetterLogger."""
    def __init__(self, **kwargs):
        kwargs['request_handler'] = BetterLogger
        super(RunServerWithBetterLogger, self).__init__(**kwargs)


_MANAGER = fes.Manager(ppc.app())
_MANAGER.add_command('runserver', RunServerWithBetterLogger())


def add_sponsor(contest_id, display_name, website, logo_filename):
    """Create a sponsor to the contest."""
    logo = _read_image_from_file(logo_filename)
    sponsor_id = _add_model(pcm.Sponsor(
        display_name=display_name,
        website=website,
        sponsor_logo=logo,
        logo_type=imghdr.what(None, logo)
        ))
    _add_owner(contest_id, sponsor_id)
    

@_MANAGER.command
def create_db():
    """Create the postgres user, database, and publicprize schema"""
    c = ppc.app().config['PUBLICPRIZE']['DATABASE']
    e = os.environ.copy()
    e['PGPASSWORD'] = c['postgres_pass']
    subprocess.call(
        ['createuser', '--host=' + c['host'], '--user=postgres',
         '--no-superuser', '--no-createdb', '--no-createrole', c['user']],
        env=e)
    p = subprocess.Popen(
        ['psql', '--host=' + c['host'], '--user=postgres', 'template1'],
        env=e,
        stdin=subprocess.PIPE)
    s = u"ALTER USER {user} WITH PASSWORD '{password}'; COMMIT;".format(**c)
    enc = locale.getlocale()[1]
    loc = locale.setlocale(locale.LC_ALL)
    p.communicate(input=bytes(s, enc))
    subprocess.check_call(
        ['createdb', '--host=' + c['host'], '--encoding=' + enc,
         '--locale=' + loc, '--user=postgres',
         '--owner=' + c['user'], c['name']],
        env=e)
    db.create_all()


@_MANAGER.command
def create_prod_db():
    """Populate prod database with subset of data/test_data.json file"""
    _create_database(is_production=True)


@_MANAGER.command
def create_test_db():
    """Recreates the database and loads the test data from
    data/test_data.json"""
    _create_database()


@_MANAGER.command
def drop_db():
    """Destroy the database"""
    if fes.prompt_bool('Drop database?'):
        # db.drop_all()
        c = ppc.app().config['PUBLICPRIZE']['DATABASE']
        e = os.environ.copy()
        e['PGPASSWORD'] = c['postgres_pass']
        subprocess.call(
            ['env', 'dropdb', '--host=' + c['host'],
             '--user=postgres', c['name']],
            env=e)


@_MANAGER.command
def refresh_founder_avatars():
    """Download the User.avatar_url and store in Founder.founder_avatar."""
    count = 0
    for user in pam.User.query.filter(pam.User.avatar_url != None).all():
        founders = _founders_for_user(user, without_avatars=True)
        if len(founders) == 0:
            continue
        image = None
        try:
            req = urllib.request.urlopen(user.avatar_url, None, 30)
            image = req.read()
            req.close()
        except socket.timeout:
            print('socket timeout for url: {}'.format(user.avatar_url))
            continue
        
        for founder in founders:
            _update_founder_avatar(founder, image)
            count += 1
    print('refreshed {} founder avatars'.format(count))


@_MANAGER.option('-u', '--user', help='User biv_id or email')
@_MANAGER.option('-i', '--input_file', help='Image file name')
def replace_founder_avatar(user, input_file):
    """Replace the avatar for the user from the specified image file"""
    if not user:
        raise Exception('missing user')
    if not input_file:
        raise Exception('missing input_file')

    image = _read_image_from_file(input_file)
    users = None
    if re.search(r'\@', user):
        users = pam.User.query.filter_by(user_email=user).all()
    elif re.search(r'^\d+$', user):
        if pam.User.query.filter_by(biv_id=user).first():
            users = [pam.User.query.filter_by(biv_id=user).one()]
        elif pcm.Founder.query.filter_by(biv_id=user).first():
            _update_founder_avatar(
                pcm.Founder.query.filter_by(biv_id=user).one(),
                image
            )
            return
    else:
        raise Exception('invalid user, expecting biv_id or email')
    if len(users) == 0:
        raise Exception('no user found for {}'.format(user))

    for user_model in users:
        for founder in _founders_for_user(user_model):
            _update_founder_avatar(founder, image)


def _add_model(model):
    """Adds a SQLAlchemy model and returns it's biv_id"""
    db.session.add(model)
    # flush() makes biv_id available (executes the db sequence)
    db.session.flush()
    return model.biv_id


def _add_owner(parent_id, child_id):
    """Creates a BivAccess record between the parent and child ids"""
    db.session.add(
        pam.BivAccess(
            source_biv_id=parent_id,
            target_biv_id=child_id
        )
    )


def _create_contest(contest):
    """Creates a SQLAlchemy model Contest with optional logo file"""
    model = pcm.Contest(
        display_name=contest['display_name'],
        tag_line=contest['tag_line'],
        end_date=datetime.datetime.strptime(
            contest['end_date'], '%m/%d/%Y').date()
    )
    if 'logo_filename' in contest:
        model.contest_logo = _read_image_from_file(contest['logo_filename'])
        model.logo_type = imghdr.what(None, model.contest_logo)
    return model


def _create_database(is_production=False):
    """Recreate the database and import data from json data file."""
    drop_db()
    create_db()
    data = json.load(open('data/test_data.json', 'r'))

    for contest in data['Contest']:
        contest_id = _add_model(_create_contest(contest))
        if 'Alias' in contest:
            _add_model(pam.BivAlias(
                biv_id=contest_id,
                alias_name=contest['Alias']['name']
            ))

        for sponsor in contest['Sponsor']:
            add_sponsor(contest_id, sponsor['display_name'],
                        sponsor['website'], sponsor['logo_filename'])

        if is_production:
            break
            
        for contestant in contest['Contestant']:
            contestant_id = _add_model(pcm.Contestant(
                # TODO(pjm): there must be a way to do this in a map()
                display_name=contestant['display_name'],
                youtube_code=contestant['youtube_code'],
                slideshow_code=contestant['slideshow_code'],
                contestant_desc=contestant['contestant_desc'],
                is_public=True,
                is_under_review=False
            ))
            _add_owner(contest_id, contestant_id)

            for founder in contestant['Founder']:
                founder_id = _add_model(_create_founder(founder))
                _add_owner(contestant_id, founder_id)

            for donor in contestant['Donor']:
                donor_id = _add_model(pcm.Donor(
                    amount=donor['amount'],
                    donor_state='executed'
                ))
                _add_owner(contestant_id, donor_id)

    db.session.commit()
    

# TODO(pjm): normalize up binary fields, combine with _create_contest()
def _create_founder(founder):
    """Creates a SQLAlchemy model Founder with optional avatar file"""
    model = pcm.Founder(
        display_name=founder['display_name'],
        founder_desc=founder['founder_desc']
    )
    if 'avatar_filename' in founder:
        model.founder_avatar = _read_image_from_file(
            founder['avatar_filename'])
        model.avatar_type = imghdr.what(None, model.founder_avatar)
    return model


def _founders_for_user(user, without_avatars=None):
    query = pcm.Founder.query.select_from(
        pam.BivAccess
    ).filter(
        pam.BivAccess.source_biv_id == user.biv_id,
        pam.BivAccess.target_biv_id == pcm.Founder.biv_id,
    )
    if without_avatars:
        query = query.filter(pcm.Founder.founder_avatar == None)
    return query.all()

def _read_image_from_file(file_name):
    image_file = open(file_name, 'rb')
    image = image_file.read()
    image_file.close()
    return image


def _update_founder_avatar(founder, image):
    print("replaced image for founder: {}".format(founder.biv_id))
    founder.founder_avatar = image
    founder.avatar_type = imghdr.what(None, image)
    db.session.add(founder)

if __name__ == '__main__':
    _MANAGER.run()
