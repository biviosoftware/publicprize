# -*- coding: utf-8 -*-
""" contest models: Contest, Contestant, Donor, and Founder

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask

from .. import biv
from .. import common
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
        website: nominated website
        is_public: is the project to be shown on the public contestant list?
        is_under_review: enables review of a non-public submission
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('nominee_s', start=1011, increment=1000),
        primary_key=True
    )
    #TODO(mda): determine if a display_name is necessary, then add it if so
    url = db.Column(db.String(100), nullable=False)
    is_public = db.Column(db.Boolean, nullable=False)
    is_under_review = db.Column(db.Boolean, nullable=False)

class Nomination(db.Model, common.ModelWithDates):
    """database model that carries the information of a website nomination

    Fields:
        biv_id: primary ID
        nominee: Foreign key to a Nominee
        client_ip: client ip of the user who performed the nomination
        submission_datetime: date and time of the nomination
        browser_string: user's browser string at time of submission
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('nomination_s', start=1012, increment=1000),
        primary_key=True
    )
    nominee = db.Column(
        db.Numeric(18),
        db.ForeignKey('nominee.biv_id'),
        nullable=False
    )
    client_ip = db.Column(db.String(45))
    submission_datetime = db.Column(db.DateTime)
    browser_string = db.Column(db.String(200))

Nominee.BIV_MARKER = biv.register_marker(11, Nominee)
Nomination.BIV_MARKER = biv.register_marker(12, Nomination)
Nomination.BIV_MARKER = biv.register_marker(13, NUContest)
