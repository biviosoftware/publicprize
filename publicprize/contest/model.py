# -*- coding: utf-8 -*-
""" The singleton model which handles global tasks.

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
        return Sponsor.get_sponsors_for_biv_id(self.biv_id, randomize);

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


class Sponsor(db.Model, common.ModelWithDates):
    """sponsor database model.

    Fields:
        biv_id: primary ID
        display_name: sponsor name
        website: sponsor website
        sponsor_logo: logo image blob
        logo_type: image type (gif, png, jpeg)
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('sponsor_s', start=1008, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(100))
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


Sponsor.BIV_MARKER = biv.register_marker(8, Sponsor)
Judge.BIV_MARKER = biv.register_marker(9, Judge)
