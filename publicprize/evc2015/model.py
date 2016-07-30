# -*- coding: utf-8 -*-
""" contest models: Contest, Contestant, Donor, and Founder

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import decimal
import random
import re

import flask
import sqlalchemy.orm

from .. import biv
from .. import common
from .. import controller
from ..contest import model as pcm
from ..auth import model as pam
from ..controller import db
from .. import ppdatetime


def _datetime_column():
    return db.Column(db.DateTime(timezone=False), nullable=False)


class E15Contest(db.Model, pcm.ContestBase):
    """contest database model.
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('e15contest_s', start=1015, increment=1000),
        primary_key=True
    )
    time_zone = db.Column(db.String, nullable=False)
    event_voting_end = _datetime_column()
    event_voting_start = _datetime_column()
    judging_end = _datetime_column()
    judging_start = _datetime_column()
    public_voting_end = _datetime_column()
    public_voting_start = _datetime_column()
    submission_end = _datetime_column()
    submission_start = _datetime_column()

    def is_event_voting(self):
        return ppdatetime.now_in_range(self.event_voting_start, self.event_voting_end)

    def is_judge(self):
        if self.is_judging():
            return super(E15Contest, self).is_judge()
        return False

    def is_judging(self):
        return ppdatetime.now_in_range(self.judging_start, self.judging_end)

    def is_public_voting(self):
        return ppdatetime.now_in_range(self.public_voting_start, self.public_voting_end)

    def is_pre_nomimation(self):
        return ppdatetime.now_before_start(self.submission_start)

    def is_nominating(self):
        return ppdatetime.now_in_range(self.submission_start, self.submission_end)

    def show_all_contestants(self):
        return ppdatetime.now_in_range(self.submission_start, self.judging_start)

    def show_semi_finalists(self):
        return ppdatetime.now_in_range(self.public_voting_end, self.judging_end)

    def show_finalists(self):
        return ppdatetime.now_in_range(self.judging_start, self.event_voting_end)


class E15EventVoter(db.Model, common.ModelWithDates):
    """event voter database mode.
    """
    __tablename__ = 'e15_event_voter'
    contest_biv_id = db.Column(db.Numeric(18), primary_key=True)
    user_email = db.Column(db.String(100), nullable=False, primary_key=True)
    nominee_biv_id = db.Column(db.Numeric(18))


class E15Nominee(db.Model, pcm.NomineeBase):
    """nominatee database model.
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('e15nominee_s', start=1016, increment=1000),
        primary_key=True
    )
    youtube_code = db.Column(db.String(500))
    nominee_desc = db.Column(db.String)
    is_semi_finalist = db.Column(db.Boolean, nullable=False)
    is_finalist = db.Column(db.Boolean, nullable=False)


E15Contest.BIV_MARKER = biv.register_marker(15, E15Contest)
E15Nominee.BIV_MARKER = biv.register_marker(16, E15Nominee)
