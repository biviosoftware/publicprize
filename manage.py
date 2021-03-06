# -*- coding: utf-8 -*-
""" Database creation and test data loading

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from publicprize.controller import db
from publicprize.debug import pp_t
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
    nominee_biv_id = pem.E15Nominee.query.filter_by(
        display_name=nominee
    ).one().biv_id
    db.session.add(
        pem.E15EventVoter(
            contest_biv_id=contest,
            user_email=user.lower(),
            nominee_biv_id=nominee_biv_id,
        ))

@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-u', '--user', help='User biv_id or email')
def add_judge(contest, user):
    """Link the User model to a Judge model."""
    _add_role(contest, user, pcm.Judge)


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-u', '--user', help='User biv_id or email')
def add_registrar(contest, user):
    """Link the User model to a Registrar model."""
    _add_role(contest, user, pcm.Registrar)


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


@_MANAGER.option('-b', '--biv_id', help='biv_id')
def biv_info(biv_id):
    """Dump fields of biv obj."""
    b = biv.load_obj(biv_id)
    print(str(b))
    for k in b.__table__.columns:
        k = k.name
        print('{:>24} = {}'.format(k, getattr(b, k)))


@_MANAGER.option('-j', '--json_file', help='contest.json')
def create_evc_contest(json_file):
    """Create a contest from json"""
    data = json.load(open(json_file, 'r'))
    contest = pem.E15Contest(**(_e15contest_kwargs(data)))
    contest_id = _add_model(contest)
    db.session.flush()
    a = pam.BivAlias.query.filter(
        pam.BivAlias.alias_name == data['Alias']['name'],
    ).first()
    if a:
        db.session.delete(a)
        db.session.flush()
    _add_model(pam.BivAlias(
        biv_id=contest_id,
        alias_name=data['Alias']['name'],
    ))


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


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
def list_nominees(contest):
    """Set contest.field to date."""
    c = biv.load_obj(contest)
    assert type(c) == pem.E15Contest
    import csv
    f = open('nominees.csv', 'w', newline='')
    w = csv.writer(f)
    w.writerow(['Contestant', 'Link', 'Submitter', 'Email', 'Phone', 'Address', 'Public?', 'Valid?', 'Id'])
    for n in pem.E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == c.biv_id,
            pam.BivAccess.target_biv_id == pem.E15Nominee.biv_id,
        ).all():
        submitter = n.submitter()
        w.writerow([
            n.display_name,
            n.url,
            submitter.display_name,
            submitter.user_email,
            n.contact_phone,
            n.contact_address,
            'Y' if n.is_public else 'N',
            'Y' if n.is_valid else 'N',
            biv.Id(n.biv_id).to_biv_uri(),
        ])
    f.close()
    print('wrote nominees.csv')


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-f', '--field', help='votes or judge_score')
def list_scores(contest, field):
    """list scores as csv """
    c, scores = _scores(contest, field)
    import csv
    f = open('scores.csv', 'w', newline='')
    w = csv.writer(f)
    w.writerow(['Contestant', 'Votes', 'Judge Rank', 'URL'])
    for n in scores:
        w.writerow([
            n['display_name'],
            n['votes'],
            n['judge_score'],
            '2pp.us/' + biv.Id(n['biv_id']).to_biv_uri(),
        ])
    f.close()
    print('wrote scores.csv')



@_MANAGER.option('-n', '--nominee', help='Nominee biv_id')
def nominee_comments(nominee):
    """Output comments for nominee"""
    n = biv.load_obj(nominee)
    assert type(n) == pem.E15Nominee
    print('\n\n'.join(n.get_comments_only()))


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


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-i', '--input_file', help='input file')
def register_event_voters(contest, input_file):
    """Load voter emails/phones from a file; invites NOT sent"""
    c = biv.load_obj(contest)
    assert type(c) == pem.E15Contest
    _add_model(c)
    with open(input_file) as f:
        for l in f:
            l = l.rstrip()
            eop, err = pem.validate_email_or_phone(l)
            if err:
                print('{}: invalid email or phone'.format(l))
            else:
                vae, created = pem.E15VoteAtEvent.create_unless_exists(c, eop)
                if created:
                    _add_model(vae)
                else:
                    print('{}: already registered'.format(vae.invite_email_or_phone))



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
    _remove_role(contest, user, pcm.Judge)


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-u', '--user', help='User biv_id or email')
def remove_registrar(contest, user):
    """Link the User model to a Registrar model."""
    _remove_role(contest, user, pcm.Registrar)


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


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-d', '--date_time', help='Date/time value')
@_MANAGER.option('-f', '--field', help='Field to set value to')
def set_contest_date_time(contest, date_time, field):
    """Set contest.field to date."""
    c = biv.load_obj(contest)
    assert type(c) == pem.E15Contest
    dt = _local_date_time_as_utc(c, date_time)
    assert hasattr(c, field), \
        '{}: has no attr {}'.format(c, field)
    setattr(c, field, dt)
    _add_model(c)


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
def setup_finalists(contest):
    """Set as finalist for top scores."""
    c, scores = _scores(contest, 'judge_score')
    _setup_xxx_ists(c, scores, 3, 'is_finalist')


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
def setup_semi_finalists(contest):
    """List semi finalists and potentially update"""
    c, scores = _scores(contest, 'votes')
    _setup_xxx_ists(c, scores, 10, 'is_semi_finalist')


@_MANAGER.option('-n', '--nominee', help='Nominee biv_id')
@_MANAGER.option('-f', '--field', help='Field to toggle')
def toggle_nominee_flag(nominee, field):
    """Set contest.field to date."""
    n = biv.load_obj(nominee)
    assert type(n) == pem.E15Nominee
    assert hasattr(n, field), \
        '{}: has no attr {}'.format(n, field)
    v = getattr(n, field)
    assert type(v) == bool, \
        '{}.{}: is not boolean {}'.format(n, field, type(n.field))
    setattr(n, field, not v)
    _add_model(n)


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
def twitter_votes(contest):
    """Count tweets and apply to votes for EspritVentureChallenge"""
    import application_only_auth
    import re

    #TODO(robnagler) Add ability to count tweets for non-matching
    # that is assign the tweet to a contestant manually
    c = biv.load_obj(contest)
    assert type(c) == pem.E15Contest
    cfg = ppc.app().config['PUBLICPRIZE']['TWITTER']
    ignore_list = ppc.app().config['PUBLICPRIZE']['TWEETS']['ignore_list']
    client = application_only_auth.Client(**cfg)
    res = client.request(
        'https://api.twitter.com/1.1/search/tweets.json?q=%40BoulderChamber%20%23EspritVentureChallenge&result_type=recent&count=1000',
    )
    strip_re = re.compile(r'[^a-z]')
    def _strip(name):
        return strip_re.sub('', name.lower())[0:5]

    tweet_re = re.compile(r'for (.+) in')
    tweet_re2 = re.compile(r'2pp.us/(\w+)')
    nominees = {}
    nominees_by_id = {}
    for nominee in c.public_nominees():
        nominees[_strip(nominee.display_name)] = nominee.biv_id
        nominees_by_id[nominee.biv_id] = nominee.display_name
    all_votes = pcm.Vote.query.filter(
        pcm.Vote.nominee_biv_id.in_(list(nominees.values())),
    ).all()
    votes_map = dict([(v.biv_id, v) for v in all_votes if v.twitter_handle])
    vote_not_found = {}
    #print(all_votes)
    events = {}
    ignore_handles = set()
    for s in reversed(res['statuses']):
        sn = pcm.Vote.strip_twitter_handle(s['user']['screen_name'])
        if sn in ignore_list:
            continue
        dt = s['created_at'][4:].replace('+0000 ', '')
        dt = datetime.datetime.strptime(dt, '%b %d %H:%M:%S %Y')
        err = None
        m = tweet_re2.search(s['text'])
        nominee_id = None
        if m:
            guess = m.group(1)
            try:
                nominee_id = nominees_by_id[biv.URI(guess).biv_id]
            except Exception:
                m = None
        #print('https://twitter.com/{}/status/{}'.format(sn, s['id']))
        if not nominee_id:
            m2 = tweet_re.search(s['text'])
            if m2:
                guess = _strip(m2.group(1))
                nominee_id = nominees.get(guess)
                m = m2
            else:
                err = 'tweet did not match regexes'
        if nominee_id:
            votes = pcm.Vote.query.filter_by(
                nominee_biv_id=nominee_id,
                twitter_handle=sn,
            ).all()
            if len(votes) == 1:
                if votes[0].biv_id in votes_map:
                    if votes[0].vote_status != '2x':
                        votes[0].vote_status = '2x'
                        _add_model(votes[0])
                    del votes_map[votes[0].biv_id]
                    ignore_handles.add(sn)
                    #print('{}: updated'.format(votes[0]))
                    continue
                else:
                    err = '{}: duplicate vote'.format(votes[0])
                    continue
            elif len(votes) > 1:
                err = '{}: strange vote count, votes='.format(len(votes), votes)
            else:
                err = 'vote not found'
                vote_not_found[dt.replace(microsecond=0)] = dict(nominee_id=nominee_id, sn=sn)
        elif m:
            err = '{}: guess={} not found in nominees'.format(m.group(1), guess)
        else:
            err = '{}: does not match regexes'.format(s['text'])
        if not s['text'].startswith('RT '):
            events[dt] = '{}\n    {} => {}\n    https://twitter.com/{}/status/{}\n    {}'.format(
                err, sn, m and m.group(1), sn, s['id'], s['text'])

    sec = datetime.timedelta(seconds=1)
    # print('\nVotes not found')
    for v in votes_map.values():
        # Ignore invalidated handles and already counted votes
        if not ('!' in v.twitter_handle or v.vote_status == '2x' or v.twitter_handle in ignore_list):
            u = biv.load_obj(biv.Id(v.user).to_biv_uri())
            events[v.creation_date_time] = '{} {} {} {} {}: no tweet'.format(
                v.twitter_handle,
                u.display_name,
                u.user_email,
                v.nominee_biv_id,
                nominees_by_id[v.nominee_biv_id],
            )
            vdt = v.creation_date_time.replace(microsecond=0)
            vnf = None
            for i in range(120):
                vnf = vote_not_found.get(vdt)
                if vnf and vnf['nominee_id'] == v.nominee_biv_id:
                    events[v.creation_date_time] += '\npython manage.py twitter_handle_update -c {} -o {} -n {}'.format(
                        biv.Id(c.biv_id).to_biv_uri(), v.twitter_handle, vnf['sn'])
                    break
                vdt += sec
    for k in reversed(sorted(events.keys())):
        print('{} {}'.format(k.strftime('%d %H:%M:%S'), events[k]))


@_MANAGER.option('-c', '--contest', help='Contest biv_id')
@_MANAGER.option('-o', '--old', help='old')
@_MANAGER.option('-n', '--new', help='new')
def twitter_handle_update(contest, old, new):
    """update or invalidat"""
    c = biv.load_obj(contest)
    assert type(c) == pem.E15Contest
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
    import publicprize.db_upgrade

    backup_db()
    for field, date in (
        ("submission_start", "6/16/2017 12:0:0"),
        ("submission_end", "9/7/2017 12:0:0"),
        ("public_voting_start", "9/8/2017 12:0:0"),
        ("public_voting_end", "9/15/2017 12:0:0"),
        ("judging_start", "9/27/2017 12:0:0"),
        ("judging_end", "9/27/2017 19:0:0"),
    ):
        set_contest_date_time('esprit-venture-challenge', date, field)
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


def _add_role(contest, user, role_class):
    contest = biv.load_obj(contest)
    user_model = _lookup_user(user)
    role = role_class.query.select_from(pam.BivAccess).filter(
        pam.BivAccess.source_biv_id == user_model.biv_id,
        pam.BivAccess.target_biv_id == role_class.biv_id
    ).first()
    role_id = None

    if role:
        role_id = role.biv_id
    else:
        role_id = _add_model(role_class())
        _add_owner(user_model.biv_id, role_id)
    _add_owner(contest.biv_id, role_id)


def _create_database(is_production=False, is_prompt_forced=False):
    """Recreate the database and import data from json data file."""
    import publicprize.general.model as pgm

    drop_db(auto_force=is_prompt_forced)
    create_db()
    data = json.load(open('data/test_data.json', 'r'))

    for contest in data['E15Contest']:
        contest_m = pem.E15Contest(**(_e15contest_kwargs(contest)))
        contest_id = _add_model(contest_m)
        _add_model(pam.BivAlias(
            biv_id=contest_id,
            alias_name=contest['Alias']['name']
        ))
        for sponsor in contest['Sponsor']:
            add_sponsor(contest_id, sponsor['display_name'],
                        sponsor['website'], sponsor['logo_filename'])

        for nominee in contest['E15Nominee']:
            user_id = _add_model(pgm.General.new_test_user(contest_m))
            founders = nominee['Founder']
            del nominee['Founder']
            votes = nominee['Vote']
            del nominee['Vote']
            nominee.update({
                'is_public': True,
                'is_valid': True,
                'is_semi_finalist': False,
                'is_finalist': False,
                'is_winner': False,
            })
            nominee_id = _add_model(pem.E15Nominee(**nominee))
            db.session.flush()
            _add_owner(
                contest_id,
                nominee_id,
            )
            db.session.flush()
            _add_owner(user_id, nominee_id)
            db.session.flush()
            for founder in founders:
                f = _add_model(_create_founder(founder))
                _add_owner(
                    nominee_id,
                    f)
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


def _remove_role(contest, user, role_class):
    """Link the User model to a Role model."""
    user_biv_id = _lookup_user(user).biv_id
    role = role_class.query.select_from(pam.BivAccess).filter(
        pam.BivAccess.source_biv_id == user_biv_id,
        pam.BivAccess.target_biv_id == role_class.biv_id
    ).one()
    db.session.delete(
        pam.BivAccess.query.filter(
            pam.BivAccess.source_biv_id == contest,
            pam.BivAccess.target_biv_id == role.biv_id
        ).one()
    )


def _scores(contest, sorted_by):
    c = biv.load_obj(contest)
    assert type(c) == pem.E15Contest
    scores = sorted(
        c.tally_all_scores(),
        key=lambda x: x[sorted_by],
        reverse=True,
    )
    return c, scores


def _setup_xxx_ists(c, scores, num, attr_name):
    print('setting {} for:'.format(attr_name))
    for n in scores[0:num]:
        nm = biv.load_obj(n['biv_id'])
        print(nm.biv_id, nm.display_name)
        setattr(nm, attr_name, True)
        _add_model(nm)


def _update_founder_avatar(founder, image):
    """Update Founder.founder_avatar."""
    print("replaced image for founder: {}".format(founder.biv_id))
    founder.founder_avatar = image
    founder.avatar_type = imghdr.what(None, image)
    db.session.add(founder)

if __name__ == '__main__':
    _MANAGER.run()
