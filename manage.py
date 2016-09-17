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
import publicprize.biv as biv
import publicprize.contest.model as pcm
import publicprize.controller as ppc
import publicprize.evc.model as pem
import publicprize.evc2015.model as pe15
import publicprize.nextup.model as pnm
import pytz
import re
import subprocess
import time
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
        """Called before context has been popped"""
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

@_MANAGER.option('-u', '--user', help='User biv_id or email')
def add_admin(user):
    """Link the User model to an Admin model."""
    _add_owner(
        _lookup_user(user).biv_id,
        _add_model(pam.Admin())
    )


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-u', '--user', help='Any email')
@_MANAGER.option('-s', '--nominee', help='Nominee display_name')
def add_event_vote(contest, user, nominee):
    """Add a E15EventVoter record for the specified user/nominee."""
    if not user:
        raise Exception('missing user')
    if not contest:
        raise Exception('missing contest')
    if not nominee:
        raise Exception('missing nominee')
    if not re.search(r'\@', user):
        raise Exception('user must be an email address')
    nominee_biv_id = pe15.E15Nominee.query.filter_by(
        display_name=nominee
    ).one().biv_id
    db.session.add(
        pe15.E15EventVoter(
            contest_biv_id=contest,
            user_email=user.lower(),
            nominee_biv_id=nominee_biv_id,
        ))


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-u', '--user', help='User biv_id or email')
def add_judge(contest, user):
    """Link the User model to a Judge model."""
    user_model = _lookup_user(user)
    judge = pcm.Judge.query.select_from(pam.BivAccess).filter(
        pam.BivAccess.source_biv_id == user_model.biv_id,
        pam.BivAccess.target_biv_id == pcm.Judge.biv_id
    ).first()
    judge_id = None

    if judge:
        judge_id = judge.biv_id
    else:
        judge_id = _add_model(pcm.Judge())
        _add_owner(user_model.biv_id, judge_id)
    _add_owner(contest, judge_id)


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-s', '--name', help='Sponsor name')
@_MANAGER.option('-w', '--website', help='Sponsor website')
@_MANAGER.option('-i', '--input_file', help='Image file name')
def add_sponsor(contest, name, website, input_file):
    """Create a sponsor to the contest."""
    logo = _read_image_from_file(input_file)
    sponsor_id = _add_model(pcm.Sponsor(
        display_name=name,
        website=website,
        sponsor_logo=logo,
        logo_type=imghdr.what(None, logo)
        ))
    _add_owner(contest, sponsor_id)


@_MANAGER.command
def backup_db():
    """Backup the database"""
    c = ppc.app().config['PUBLICPRIZE']['DATABASE']
    now = datetime.datetime.now()
    dump_file = now.strftime('%Y%m%d%H%M%S-pp.pg_dump')
    subprocess.check_call([
        'pg_dump',
        '--clean',
        '--format=c',
        '--blobs',
        '--user=' +  c['user'],
        '--file=' + dump_file,
        c['name'],
    ])
    print('wrote ' + dump_file)


@_MANAGER.option('-uri', help='URI')
def biv_id(uri):
    """Return the biv_id for any uri"""
    print(biv.URI(uri).biv_id)


@_MANAGER.command
def create_db():
    """Create the postgres user, database, and publicprize schema"""
    _init_db()
    db.create_all()


@_MANAGER.command
def create_prod_db():
    """Populate prod database with subset of data/test_data.json file"""
    _create_database(is_production=True)


@_MANAGER.command
@_MANAGER.option('-f', '--force', help='do not prompt before overwriting db')
def create_test_db(force_prompt=False):
    """Recreates the database and loads the test data from
    data/test_data.json"""
    _create_database(is_prompt_forced=bool(force_prompt))


@_MANAGER.option('-d', '--dump_file', help='dump file')
def restore_db(dump_file):
    """Restores db from dump_file"""
    drop_db()
    _init_db()
    c = ppc.app().config['PUBLICPRIZE']['DATABASE']
    subprocess.check_call([
        'pg_restore',
        '--dbname=' + c['name'],
        '--user=' +  c['user'],
        dump_file,
    ])


@_MANAGER.option('-b', '--biv_id', help='biv_id')
def biv_info(biv_id):
    """Dump fields of biv obj."""
    b = biv.load_obj(biv_id)
    print(str(b))
    for k in b.__table__.columns:
        k = k.name
        print('{:>24} = {}'.format(k, getattr(b, k)))


@_MANAGER.command
def drop_db(auto_force=False):
    """Destroy the database"""
    if auto_force:
        confirmed = True
    else:
        confirmed = fes.prompt_bool('Drop database?')
    if confirmed:
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
    for user in pam.User.query.filter(
            pam.User.avatar_url != None).all():  # noqa
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
def remove_admin(user):
    """Remove the User model to an Admin model."""
    user_biv_id = _lookup_user(user).biv_id
    admin = pam.Admin.query.select_from(pam.BivAccess).filter(
        pam.BivAccess.source_biv_id == user_biv_id,
        pam.BivAccess.target_biv_id == pam.Admin.biv_id
    ).one()
    db.session.delete(
        pam.BivAccess.query.filter(
            pam.BivAccess.source_biv_id == user_biv_id,
            pam.BivAccess.target_biv_id == admin.biv_id
        ).one()
    )
    db.session.delete(admin)


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-u', '--user', help='User biv_id or email')
def remove_judge(contest, user):
    """Link the User model to a Judge model."""
    user_biv_id = _lookup_user(user).biv_id
    judge = pcm.Judge.query.select_from(pam.BivAccess).filter(
        pam.BivAccess.source_biv_id == user_biv_id,
        pam.BivAccess.target_biv_id == pcm.Judge.biv_id
    ).one()
    db.session.delete(
        pam.BivAccess.query.filter(
            pam.BivAccess.source_biv_id == contest,
            pam.BivAccess.target_biv_id == judge.biv_id
        ).one()
    )


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-s', '--name', help='Sponsor name')
def remove_sponsor(contest, name):
    """Removed the sponsor from a contest by name."""
    sponsors = pcm.Sponsor.get_sponsors_for_biv_id(contest, False)
    found = False
    for sponsor in sponsors:
        if (sponsor.display_name == name):
            db.session.delete(pam.BivAccess.query.filter_by(
                    source_biv_id=contest,
                    target_biv_id=sponsor.biv_id).one())
            db.session.delete(sponsor)
            print('deleted sponsor {}'.format(name))
            found = True
    if not found:
        print('no sponsor found for name: {}'.format(name))


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


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-d', '--date_time', help='Date/time value')
@_MANAGER.option('-f', '--field', help='Field to set value to')
def set_contest_date_time(contest, date_time, field):
    """Set contest.field to date."""
    c = biv.load_obj(contest)
    assert type(c) == pe15.E15Contest
    dt = _local_date_time_as_utc(c, date_time)
    assert hasattr(c, field), \
        '{}: has no attr {}'.format(c, field)
    setattr(c, field, dt)


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
def twitter_votes(contest):
    """Count tweets and apply to votes for EspritVentureChallenge"""
    import application_only_auth
    import re

    c = biv.load_obj(contest)
    assert type(c) == pe15.E15Contest
    cfg = ppc.app().config['PUBLICPRIZE']['TWITTER']
    client = application_only_auth.Client(**cfg)
    res = client.request(
        'https://api.twitter.com/1.1/search/tweets.json?q=%40BoulderChamber%20%23EspritVentureChallenge&result_type=recent&count=1000',
    )
    strip_re = re.compile(r'[^a-z]')
    def _strip(name):
        return strip_re.sub('', name.lower())[0:5]

    tweet_re = re.compile(r'I.*voted for (.+) in the')
    nominees = {}
    nominees_by_id = {}
    for nominee in c.public_nominees():
        nominees[_strip(nominee.display_name)] = nominee.biv_id
        nominees_by_id[nominee.biv_id] = nominee.display_name
    all_votes = pcm.Vote.query.filter(
        pcm.Vote.nominee_biv_id.in_(list(nominees.values())),
    ).all()
    all_votes = dict([(v.biv_id, v) for v in all_votes if v.twitter_handle])
    #print(all_votes)
    events = {}
    ignore_handles = set()
    for s in reversed(res['statuses']):
        dt = s['created_at'][4:].replace('+0000 ', '')
        dt = datetime.datetime.strptime(dt, '%b %d %H:%M:%S %Y')
        sn = pcm.Vote.strip_twitter_handle(s['user']['screen_name'])
        m = tweet_re.search(s['text'])
        err = None
        #print('https://twitter.com/{}/status/{}'.format(sn, s['id']))
        if s['retweet_count'] > 0:
            err = 'ignore retweet'
            continue
        elif m:
            guess = _strip(m.group(1))
            if guess in nominees:
                votes = pcm.Vote.query.filter_by(
                    nominee_biv_id=nominees[guess],
                    twitter_handle=sn,
                ).all()
                if len(votes) == 1:
                    if votes[0].biv_id in all_votes:
                        votes[0].vote_status = '2x'
                        del all_votes[votes[0].biv_id]
                        _add_model(votes[0])
                        ignore_handles.add(sn)
                        #print('{}: updated'.format(votes[0]))
                        continue
                    else:
                        err = '{}: duplicate vote'.format(votes[0])
                        continue
                elif len(votes) > 1:
                    err = '{}: strange vote count, votes='.format(len(votes), votes)
                else:
                    err = 'miss'
            else:
                err = '{}: guess={} not found in {}'.format(m.group(1), guess, nominees.keys())
        else:
            err = 'tweet did not match {}'.format(s['text'], tweet_re)
        if not sn in ignore_handles:
            events[dt] = '{}\n    {} => {}\n    https://twitter.com/{}/status/{}\n    {}'.format(
                err, m and m.group(1), sn, sn, s['id'], s['text'])

    # print('\nVotes not found')
    for v in all_votes.values():
        if not '!' in v.twitter_handle:
            u = biv.load_obj(biv.Id(v.user).to_biv_uri())
            events[v.creation_date_time] = '{}: {} {} {}'.format(
                v.twitter_handle,
                u.display_name,
                u.user_email,
                nominees_by_id[v.nominee_biv_id],
            )
    for k in reversed(sorted(events.keys())):
        print('{} {}'.format(k.strftime('%d %H:%M'), events[k]))


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-o', '--old', help='old')
@_MANAGER.option('-n', '--new', help='new')
def twitter_handle_update(contest, old, new):
    """update or invalidat"""
    c = biv.load_obj(contest)
    assert type(c) == pe15.E15Contest
    all_nominees = [n.biv_id for n in c.public_nominees()]
    all_votes = pcm.Vote.query.filter(
        pcm.Vote.nominee_biv_id.in_(all_nominees),
    ).all()
    all_votes = dict([(v.biv_id, v) for v in all_votes if v.twitter_handle])
    for v in all_votes.values():
        if old != v.twitter_handle:
            continue
        new = ('!' + old) if new == '!' else pcm.Vote.strip_twitter_handle(new)
        v.twitter_handle = new
        _add_model(v)
        break


@_MANAGER.command
def upgrade_db():
    """Backs up the db and runs an upgrade"""
    backup_db()
    m = pe15.E15Contest.query.filter_by(
        display_name='2016 Esprit Venture Challenge',
    ).one()
    for n in m.public_nominees():
        for v in pcm.Vote.query.filter_by(
            nominee_biv_id=n.biv_id,
        ):
            if v.twitter_handle:
                v.twitter_handle = pcm.Vote.strip_twitter_handle(v.twitter_handle)
                print(v.twitter_handle)
                _add_model(v)
    db.session.commit()


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
    model = pem.Contest(
        display_name=contest['display_name'],
        tag_line=contest['tag_line'],
        end_date=datetime.datetime.strptime(
            contest['end_date'], '%m/%d/%Y').date(),
        is_scoring_completed=False
    )
    return model


def _create_database(is_production=False, is_prompt_forced=False):
    """Recreate the database and import data from json data file."""
    drop_db(auto_force=is_prompt_forced)
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
            contestant_id = _add_model(pem.Contestant(
                # TODO(pjm): there must be a way to do this in a map()
                display_name=contestant['display_name'],
                youtube_code=contestant['youtube_code'],
                slideshow_code=contestant['slideshow_code'],
                contestant_desc=contestant['contestant_desc'],
                website=contestant['website'],
                is_public=True,
                is_under_review=False
            ))
            _add_owner(contest_id, contestant_id)

            for founder in contestant['Founder']:
                founder_id = _add_model(_create_founder(founder))
                _add_owner(contestant_id, founder_id)

            for donor in contestant['Donor']:
                donor_id = _add_model(pem.Donor(
                    amount=donor['amount'],
                    donor_state='executed'
                ))
                _add_owner(contestant_id, donor_id)

    for contest in data['NUContest']:
        contest_id = _add_model(
            pnm.NUContest(
                display_name=contest['display_name'],
                end_date=datetime.datetime.strptime(
                    contest['end_date'], '%m/%d/%Y').date(),
                )
            )
        if 'Alias' in contest:
            _add_model(pam.BivAlias(
                biv_id=contest_id,
                alias_name=contest['Alias']['name']
            ))

        for sponsor in contest['Sponsor']:
            add_sponsor(contest_id, sponsor['display_name'],
                        sponsor['website'], sponsor['logo_filename'])

        for nominee in contest['Nominee']:
            _add_owner(
                contest_id,
                _add_model(pnm.Nominee(
                        display_name=nominee['display_name'],
                        url=nominee['url'],
                        category=nominee['category'],
                        is_public=True,
                        is_under_review=False
                        )))

    for contest in data['E15Contest']:
        contest_id = _add_model(pe15.E15Contest(**(_e15contest_kwargs(contest))))
        _add_model(pam.BivAlias(
            biv_id=contest_id,
            alias_name=contest['Alias']['name']
        ))
        for sponsor in contest['Sponsor']:
            add_sponsor(contest_id, sponsor['display_name'],
                        sponsor['website'], sponsor['logo_filename'])

        for nominee in contest['E15Nominee']:
            founders = nominee['Founder']
            del nominee['Founder']
            votes = nominee['Vote']
            del nominee['Vote']
            nominee.update({
                'is_public': True,
                'is_semi_finalist': True,
                'is_finalist': True,
                'is_winner': True,
            })
            nominee_id = _add_model(pe15.E15Nominee(**nominee))
            _add_owner(
                contest_id,
                nominee_id,
            )
            for founder in founders:
                _add_owner(
                    nominee_id,
                    _add_model(_create_founder(founder)))
            for twitter_handle in votes:
                user_id = _create_user()
                _add_model(
                    pcm.Vote(
                        user=user_id,
                        nominee_biv_id=nominee_id,
                        vote_status='1x',
                        twitter_handle=twitter_handle.lower(),
                    ))

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


def _create_user():
    import werkzeug.security
    name = 'F{} L{}'.format(
        werkzeug.security.gen_salt(6).lower(),
        werkzeug.security.gen_salt(8).lower())
    return _add_model(pam.User(
        display_name=name,
        user_email='{}@localhost'.format(name.lower().replace(' ', '')),
        oauth_type='test',
        oauth_id=werkzeug.security.gen_salt(64)
    ))


def _e15contest_kwargs(contest):
    kwargs = {}

    for k, v in contest.items():
        if re.search('^[A-Z]', k):
            pass
        elif k == 'end_date':
            kwargs[k] = datetime.datetime.strptime(v, '%m/%d/%Y').date()
        elif re.search('_end$|_start$', k):
            kwargs[k] = _local_date_time_as_utc(contest, v)
        else:
            kwargs[k] = v
    return kwargs


def _founders_for_user(user, without_avatars=None):
    """Returns the Founder models associated with the User model."""
    query = pcm.Founder.query.select_from(
        pam.BivAccess
    ).filter(
        pam.BivAccess.source_biv_id == user.biv_id,
        pam.BivAccess.target_biv_id == pcm.Founder.biv_id,
    )
    if without_avatars:
        query = query.filter(pcm.Founder.founder_avatar == None)  # noqa
    return query.all()


def _init_db():
    """Create the database without tables"""
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
    s = u"ALTER USER {user} WITH PASSWORD '{password}'".format(**c)
    enc = locale.getlocale()[1]
    loc = locale.setlocale(locale.LC_ALL)
    p.communicate(input=bytes(s, enc))
    subprocess.check_call(
        ['createdb', '--host=' + c['host'], '--encoding=' + enc,
         '--locale=' + loc, '--user=postgres',
         '--template=template0',
         '--owner=' + c['user'], c['name']],
        env=e)


def _local_date_time_as_utc(contest, date_time):
    tz = contest['time_zone'] if isinstance(contest, dict) else contest.time_zone
    return pytz.timezone(
        tz
    ).localize(
        datetime.datetime.strptime(date_time, '%m/%d/%Y %H:%M:%S')
    ).astimezone(pytz.UTC)


def _lookup_user(user):
    """Returns a User model from a biv_id or user_email"""
    if re.search(r'\@', user):
        return pam.User.query.filter_by(user_email=user).one()
    if re.search(r'^\d+$', user):
        return pam.User.query.filter_by(biv_id=user).one()
    raise Exception('invalid user: {}, expecting biv_id or email'.format(user))


def _read_image_from_file(file_name):
    """Reads the image file and returns data."""
    image_file = open(file_name, 'rb')
    image = image_file.read()
    image_file.close()
    return image


def _update_founder_avatar(founder, image):
    """Update Founder.founder_avatar."""
    print("replaced image for founder: {}".format(founder.biv_id))
    founder.founder_avatar = image
    founder.avatar_type = imghdr.what(None, image)
    db.session.add(founder)

if __name__ == '__main__':
    _MANAGER.run()
