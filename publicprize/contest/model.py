# -*- coding: utf-8 -*-
""" Common contest models.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import flask
import math
import pytz
import re
import random
import sqlalchemy.orm
import string
import werkzeug.exceptions

from .. import biv
from .. import common
from ..auth import model as pam
from ..controller import db
from ..debug import pp_t


_NONCE_ATTR = 'vote_at_event.invite_nonce'


class ContestBase(common.ModelWithDates):
    """Contest base class. Contains the contest end_date field for calculating
    the remaining time left."""

    display_name = db.Column(db.String(100), nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    def days_remaining(self):
        """Days remaining for this Contest."""
        time_left = self._time_remaining()
        if time_left.days > 0:
            return time_left.days
        return 0

    def get_contest(self):
        """Returns self"""
        return self

    def get_sponsors(self, randomize=False):
        """Return a list of Sponsor models for this Contest"""
        return Sponsor.get_sponsors_for_biv_id(self.biv_id, randomize)

    def get_timezone(self):
        """Returns the timezone used by this contest."""
        # TODO(pjm): either store in config or per contest
        return pytz.timezone('US/Mountain')

    def hours_remaining(self):
        """Hours remaining for this Contest."""
        hours = math.floor(self._time_remaining().total_seconds() / (60 * 60))
        if hours > 0:
            return hours
        return 0

    def is_admin(self):
        """Shortcut to Admin.is_admin"""
        return pam.Admin.is_admin()

    def is_expired(self):
        """Returns True if the contest has expired."""
        return self._time_remaining().total_seconds() <= 0

    def is_judge(self):
        """Returns True if the current user is a judge for this Contest"""
        return self._user_is(Judge)

    def is_registrar(self):
        """Returns True if the current user is a registrar for this Contest"""
        return self._user_is(Registrar)

    def minutes_remaining(self):
        """Minutes remaining for this Contest."""
        minutes = math.floor(self._time_remaining().total_seconds() / 60)
        if minutes > 0:
            return minutes
        return 0

    def _time_remaining(self):
        """Returns the time remaining using the contest time zone."""
        tz = self.get_timezone()
        end_of_day = tz.localize(
            datetime.datetime(
                self.end_date.year, self.end_date.month, self.end_date.day,
                23, 59, 59))
        return end_of_day - datetime.datetime.now(tz)

    def _user_is(self, clazz):
        if not flask.session.get('user.is_logged_in'):
            return False
        if self.is_expired():
            return False
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        if clazz.query.select_from(pam.BivAccess, access_alias).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == clazz.biv_id,
            pam.BivAccess.target_biv_id == access_alias.target_biv_id,
            access_alias.source_biv_id == flask.session['user.biv_id']
        ).first():
            return True
        return False


class Founder(db.Model, common.ModelWithDates):
    """founder database model.

    Fields:
        biv_id: primary ID
        display_name: donor full name
        fouder_desc: founder's short bio
        founder_avatar: avatar image blob
        avatar_type: image type (gif, png, jpeg)
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('founder_s', start=1004, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    founder_desc = db.Column(db.String)
    image_biv_id = db.Column(db.Numeric(18))
    #TODO(pjm): remove these fields after next release
    founder_avatar = db.Column(db.LargeBinary)
    avatar_type = db.Column(db.Enum('gif', 'png', 'jpeg', name='avatar_type'))


class Image(db.Model, common.Model):
    """Image file"""
    biv_id = db.Column(
        db.Numeric(18),
        #TODO(robnagler) start=1017
        db.Sequence('image_s', start=1004, increment=1000),
        primary_key=True
    )
    image_data = db.Column(db.LargeBinary)
    image_type = db.Column(db.Enum('gif', 'png', 'jpeg', name='image_type'))


class Judge(db.Model, common.ModelWithDates):
    """judge database model.

    Fields:
        biv_id: primary ID
        judge_company: judge's company
        judge_title: judge's title within the company
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('judge_s', start=1009, increment=1000),
        primary_key=True
    )
    judge_company = db.Column(db.String(100))
    judge_title = db.Column(db.String(100))

    def judge_users_for_contest(contest):
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        return pam.User.query.select_from(
            pam.BivAccess, access_alias, Judge).filter(
                pam.BivAccess.source_biv_id == pam.User.biv_id,
                pam.BivAccess.target_biv_id == Judge.biv_id,
                access_alias.source_biv_id == contest.biv_id,
                access_alias.target_biv_id == Judge.biv_id,
            ).all()

    def new_test_judge(contest):
        return _test_role(contest, Judge)


class JudgeRank(db.Model, common.ModelWithDates):
    """Judge's top 5 ranks."""
    MAX_RANKS = 5

    judge_biv_id = db.Column(db.Numeric(18), primary_key=True)
    nominee_biv_id = db.Column(db.Numeric(18), primary_key=True)
    judge_rank = db.Column(db.Numeric(2))

    def judge_ranks_for_user(user_biv_id):
        return JudgeRank.query.filter_by(
            judge_biv_id=user_biv_id,
        ).all()


class JudgeComment(db.Model, common.ModelWithDates):
    judge_biv_id = db.Column(db.Numeric(18), primary_key=True)
    nominee_biv_id = db.Column(db.Numeric(18), primary_key=True)
    judge_comment = db.Column(db.String)


class NomineeBase(common.ModelWithDates):
    """nominee base class.
    """
    display_name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    is_public = db.Column(db.Boolean, nullable=False)

    def get_judge_ranks(self):
        ranks = JudgeRank.query.filter_by(
            nominee_biv_id=self.biv_id
        ).all()
        res = []
        for rank in ranks:
            res.append(rank.judge_rank)
        return res

    def get_vote_count(self):
        """Returns the vote count for this Nominee"""
        return Vote.query.filter(
            Vote.nominee_biv_id == self.biv_id
        ).count()

    def get_votes(self):
        return Vote.query.filter(
            Vote.nominee_biv_id == self.biv_id
        ).all()


class Registrar(db.Model, common.ModelWithDates):
    """Registrar database model.

    Fields:
        biv_id: primary ID
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('registrar_s', start=1018, increment=1000),
        primary_key=True
    )
    def new_test_registrar(contest):
        return _test_role(contest, Registrar)


class Sponsor(db.Model, common.ModelWithDates):
    """sponsor database model.

    Fields:
        biv_id: primary ID
        display_name: sponsor name
        website: sponsor website
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('sponsor_s', start=1008, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(100))
    image_biv_id = db.Column(db.Numeric(18))
    #TODO(pjm): remove these fields after next release
    sponsor_logo = db.Column(db.LargeBinary)
    logo_type = db.Column(db.Enum('gif', 'png', 'jpeg', name='logo_type'))

    def get_sponsors_for_biv_id(biv_id, randomize):
        sponsors = Sponsor.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == biv_id,
            pam.BivAccess.target_biv_id == Sponsor.biv_id
        ).all()
        if randomize:
            random.shuffle(sponsors)
        else:
            sponsors.sort(key=lambda x: x.biv_id)
        return sponsors


class Vote(db.Model, common.ModelWithDates):
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('vote_s', start=1014, increment=1000),
        primary_key=True
    )
    user = db.Column(
        db.Numeric(18),
        db.ForeignKey('user_t.biv_id'),
        nullable=False
    )

    @staticmethod
    def strip_twitter_handle(value):
        value = value.lower()
        value = value.replace('https://twitter.com/', '')
        value = value.replace('@gmail.com', '')
        value = value.replace('@twitter.com', '')
        value = value.replace('@yahoo.com', '')
        value = value.replace('twitter@', '')
        return value.replace('@', '')[:100]

    nominee_biv_id = db.Column(db.Numeric(18), nullable=False)
    twitter_handle = db.Column(db.String(100))
    vote_status = db.Column(db.Enum('invalid', '1x', '2x', name='vote_status'), nullable=False)


def _invite_nonce():
    # SystemRandom is cryptographically secure
    return ''.join(
        random.SystemRandom().choice(string.ascii_lowercase) for _ in range(24)
    )


def _test_role(contest, clazz):
    """Creates a new test user and clazz models and log in."""
    # will raise an exception unless TEST_USER is configured
    flask.g.pub_obj.task_class().action_new_test_user()
    role = clazz()
    db.session.add(role)
    db.session.flush()
    db.session.add(pam.BivAccess(
        source_biv_id=flask.session['user.biv_id'],
        target_biv_id=role.biv_id
    ))
    db.session.add(pam.BivAccess(
        source_biv_id=contest.biv_id,
        target_biv_id=role.biv_id
    ))
    return flask.redirect('/')


class VoteAtEvent(db.Model, common.ModelWithDates):
    """An event vote token
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('voteatevent_s', start=1019, increment=1000),
        primary_key=True
    )
    contest_biv_id = db.Column(db.Numeric(18), nullable=False)
    invite_email_or_phone = db.Column(db.String(100), nullable=False)
    # Bit larger than _invite_nonce()
    invite_nonce = db.Column(db.String(32), unique=True, default=_invite_nonce)
    nominee_biv_id = db.Column(db.Numeric(18), nullable=True)
    remote_addr = db.Column(db.String(32), nullable=True)
    user_agent = db.Column(db.Numeric(18), nullable=True)
    # Logged in user at the time of vote, may be meaningless
    user_biv_id = db.Column(db.Numeric(18), nullable=True)

    @classmethod
    def validate_session(cls, contest):
        i = flask.session.get(_NONCE_ATTR)
        if not i:
            pp_t('no invite_nonce')
            werkzeug.exceptions.abort(404)
        self = cls.query.filter_by(invite_nonce=i).first_or_404()
        if self.contest_biv_id != contest.biv_id:
            pp_t(
                'nonce={} expect_contest={} actual_contest={}',
                [i, contest.biv_id, self.contest_biv_id],
            )
            werkzeug.exceptions.abort(404)

    def save_to_session(self):
        flask.session[_NONCE_ATTR] = self.invite_nonce


Founder.BIV_MARKER = biv.register_marker(4, Founder)
Image.BIV_MARKER = biv.register_marker(17, Image)
Judge.BIV_MARKER = biv.register_marker(9, Judge)
Registrar.BIV_MARKER = biv.register_marker(18, Registrar)
Sponsor.BIV_MARKER = biv.register_marker(8, Sponsor)
Vote.BIV_MARKER = biv.register_marker(14, Vote)
VoteAtEvent.BIV_MARKER = biv.register_marker(19, VoteAtEvent)
