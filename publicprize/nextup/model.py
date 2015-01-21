# -*- coding: utf-8 -*-
""" contest models: Contest, Contestant, Donor, and Founder

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask

from .. import biv
from .. import common
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

    def get_nominated_websites(self):
        """Returns a list of all websites that haven been nominated"""
        return Nominee.query.all()

    def get_sponsors(self, randomize=False):
        """Return a list of Sponsor models for this Contest"""
        return pcm.Sponsor.get_sponsors_for_biv_id(self.biv_id, randomize);


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

    def get_contest(self):
        """Returns the Contest model which owns this Contestant"""
        return NUContest.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == NUContest.biv_id,
            pam.BivAccess.target_biv_id == self.biv_id
        ).one()
    

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

Nominee.BIV_MARKER = biv.register_marker(11, Nominee)
Nominator.BIV_MARKER = biv.register_marker(12, Nominator)
NUContest.BIV_MARKER = biv.register_marker(13, NUContest)
