# -*- coding: utf-8 -*-
""" contest models: NUContest, Nominee, Nominator, NUVote

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
import random

from .. import biv
from .. import common
from .. import controller as ppc
from ..auth import model as pam
from ..contest import model as pcm
from ..controller import db

class NUContest(db.Model, common.ModelWithDates):
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('nucontest_s', start=1013, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)

    def delete_votes_for_auth_user(self, category):
        """Delete the auth user's votes for the specified category."""
        votes = self._votes_for_auth_user(category)
        for vote in votes:
            db.session.delete(vote)

    def get_admin_nominees(self):
        """Returns a list of all admin review nominees."""
        return Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == Nominee.biv_id
        ).all()

    def get_public_nominees(self, randomize=False, category=None):
        """Returns a list of all public websites that haven been nominated
        for this contest"""
        query = Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == Nominee.biv_id,
        ).filter(Nominee.is_public == True)
        if category:
            query = query.filter(Nominee.category == category)
        nominees = query.order_by(Nominee.display_name).all()
        if randomize:
            random.shuffle(nominees)
        return nominees

    def get_sponsors(self, randomize=False):
        """Return a list of Sponsor models for this Contest"""
        return pcm.Sponsor.get_sponsors_for_biv_id(self.biv_id, randomize)

    def get_vote_for_auth_user(self, category):
        """Returns the NUVote model for the current user or None."""
        if not flask.session.get('user.is_logged_in'):
            return None
        votes = self._votes_for_auth_user(category)
        if len(votes) > 1:
            ppc.app().logger.warn('user: {} has too many votes: {}'.format(
                    flask.session['user.biv_id'],
                    votes))
        if len(votes):
            return votes[0]
        return None

    def is_admin(self):
        """Shortcut to Admin.is_admin"""
        return pam.Admin.is_admin()

    def _votes_for_auth_user(self, category):
        return NUVote.query.select_from(pam.BivAccess, Nominee).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == NUVote.biv_id,
            Nominee.biv_id == NUVote.nominee
        ).filter(
            NUVote.user == flask.session['user.biv_id'],
            Nominee.category == category
        ).order_by(NUVote.modified_date_time).all()


class Nominee(db.Model, common.ModelWithDates):
    """nominated website database model.

    Fields:
        biv_id: primary ID
        display_name: nominated project name
        url: nominated website
        is_public: is the project to be shown on the public contestant list?
        is_under_review: enables review of a non-public submission
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('nominee_s', start=1011, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(100), nullable=False)
    is_public = db.Column(db.Boolean, nullable=False)
    is_under_review = db.Column(db.Boolean, nullable=False)
    category = db.Column(
        db.Enum('unknown', 'pint', 'pitcher', name='nominee_category'),
        nullable=False
    )

    def get_contest(self):
        """Returns the Contest model which owns this Nominee"""
        return NUContest.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == NUContest.biv_id,
            pam.BivAccess.target_biv_id == self.biv_id
        ).one()

    def get_vote_count(self):
        """Returns the vote count for this Nominee"""
        return NUVote.query.filter(
            NUVote.nominee == self.biv_id
        ).count()


class Nominator(db.Model, common.ModelWithDates):
    """database model that carries the information of a website nominator

    Fields:
        biv_id: primary ID
        nominee: Foreign key to a Nominee
        display_name: nominator's name
        client_ip: client ip of the user who performed the nomination
        browser_string: user's browser string at time of submission
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('nominator_s', start=1012, increment=1000),
        primary_key=True
    )
    nominee = db.Column(
        db.Numeric(18),
        db.ForeignKey('nominee.biv_id'),
        nullable=False
    )
    display_name = db.Column(db.String(100), nullable=False)
    client_ip = db.Column(db.String(45))
    submission_datetime = db.Column(db.DateTime)
    browser_string = db.Column(db.String(200))


class NUVote(db.Model, common.ModelWithDates):
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('nuvote_s', start=1014, increment=1000),
        primary_key=True
    )
    user = db.Column(
        db.Numeric(18),
        db.ForeignKey('user_t.biv_id'),
        nullable=False
    )
    nominee = db.Column(
        db.Numeric(18),
        db.ForeignKey('nominee.biv_id'),
        nullable=False
    )

    def get_nominee(self):
        """Returns the Nominee for this vote"""
        return Nominee.query.filter(
            Nominee.biv_id == self.nominee
        ).one()


Nominee.BIV_MARKER = biv.register_marker(11, Nominee)
Nominator.BIV_MARKER = biv.register_marker(12, Nominator)
NUContest.BIV_MARKER = biv.register_marker(13, NUContest)
NUVote.BIV_MARKER = biv.register_marker(14, NUVote)
