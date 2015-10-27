# -*- coding: utf-8 -*-
""" Common contest models.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import flask
import math
import pytz
import random
import sqlalchemy.orm

from .. import biv
from .. import common
from ..auth import model as pam
from ..controller import db

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
        if not flask.session.get('user.is_logged_in'):
            return False
        if self.is_expired():
            return False
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        if Judge.query.select_from(pam.BivAccess, access_alias).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == Judge.biv_id,
            pam.BivAccess.target_biv_id == access_alias.target_biv_id,
            access_alias.source_biv_id == flask.session['user.biv_id']
        ).first():
            return True
        return False

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
        """Creates a new test user and judge models and log in."""
        # will raise an exception unless TEST_USER is configured
        flask.g.pub_obj.task_class().action_new_test_user()
        judge = Judge()
        db.session.add(judge)
        db.session.flush()
        db.session.add(pam.BivAccess(
            source_biv_id=flask.session['user.biv_id'],
            target_biv_id=judge.biv_id
        ))
        db.session.add(pam.BivAccess(
            source_biv_id=contest.biv_id,
            target_biv_id=judge.biv_id
        ))
        return flask.redirect('/')


class JudgeRank(db.Model, common.ModelWithDates):
    """Judge's top 10 ranks."""
    MAX_RANKS = 10

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
    nominee_biv_id = db.Column(db.Numeric(18), nullable=False)
    twitter_handle = db.Column(db.String(100))
    vote_status = db.Column(db.Enum('invalid', '1x', '2x', name='vote_status'), nullable=False)


Founder.BIV_MARKER = biv.register_marker(4, Founder)
Sponsor.BIV_MARKER = biv.register_marker(8, Sponsor)
Judge.BIV_MARKER = biv.register_marker(9, Judge)
Vote.BIV_MARKER = biv.register_marker(14, Vote)
Image.BIV_MARKER = biv.register_marker(17, Image)
