# -*- coding: utf-8 -*-
""" contest models: Contest, Contestant, Donor, and Founder

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import decimal
import flask
import locale
from publicprize.controller import db
from publicprize import common
from publicprize import controller
from publicprize import biv
import publicprize.auth.model as pam
import random
import re
import sqlalchemy.orm


class Contest(db.Model, common.ModelWithDates):
    """contest database model.

    Fields:
        biv_id: primary ID
        display_name: name of the contest
        tag_line: sub-name of the contest
        contest_logo: image blob
        logo_type: image type (gif, png, jpeg)
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('contest_s', start=1002, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    tag_line = db.Column(db.String(500))
    # TODO(pjm): move logo and founder_avatar to separate model BivImage
    contest_logo = db.Column(db.LargeBinary)
    logo_type = db.Column(db.Enum('gif', 'png', 'jpeg', name='logo_type'))
    end_date = db.Column(db.Date, nullable=False)

    def contestant_count(self):
        """Returns the number of contestants for the current contest"""
        return pam.BivAccess.query.select_from(Contestant).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == Contestant.biv_id,
            # not a real ==, Column() overrides __eq__ to generate SQL
            Contestant.is_public == True  # noqa
        ).count()

    def days_remaining(self):
        """Days remaining for this Contest."""
        return (self.end_date - datetime.date.today()).days

    def donor_count(self):
        """Returns the total donor count across all the contestants"""
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        return Donor.query.select_from(pam.BivAccess, access_alias).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == access_alias.source_biv_id,
            access_alias.target_biv_id == Donor.biv_id,
            Donor.donor_state == 'executed'
        ).count()

    def donor_executed_amount(self):
        """Returns the total amount raised for all executed donors"""
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        # TODO(pjm): do sum in sql query
        rows = Donor.query.select_from(pam.BivAccess, access_alias).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == access_alias.source_biv_id,
            access_alias.target_biv_id == Donor.biv_id,
            Donor.donor_state == 'executed'
        ).all()
        total = decimal.Decimal(0)
        for row in rows:
            total += row.amount
        # TODO(pjm): use UI widget to do formatting
        return locale.format('%d', total, grouping=True)

    def get_sponsors(self, randomize=False):
        """Return a list of Sponsor models for this Contest"""
        sponsors = Sponsor.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == Sponsor.biv_id
        ).all()
        if randomize:
            random.shuffle(sponsors)
        return sponsors

    def get_public_contestants(self, randomize=False, userRandomize=False):
        """Return a list of contestants for this Contest. List will be
        randomized if randomize is True. If userRandomize is True, the list
        will be randomized with a seed based on the current user name."""
        contestants = Contestant.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == Contestant.biv_id
        ).filter(Contestant.is_public == True).all()  # noqa
        if randomize:
            random.shuffle(contestants)
        if userRandomize:
            random.Random(flask.session['user.display_name']).shuffle(
                contestants)
        return contestants

    def is_judge(self):
        """Returns True if the current user is a judge for this Contest"""
        if not flask.session.get('user.is_logged_in'):
            return False
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        if Judge.query.select_from(pam.BivAccess, access_alias).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == access_alias.target_biv_id,
            access_alias.source_biv_id == flask.session['user.biv_id']
        ).first():
            return True
        return False


    def user_submission_url(self):
        """Returns the current user's submission url or None.
        Iterates all the contest's contestant's founders, matching with
        the current logged in user.
        """
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        founders = Founder.query.select_from(
            pam.BivAccess, access_alias
        ).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == access_alias.source_biv_id,
            access_alias.target_biv_id == Founder.biv_id
        ).all()

        for founder in founders:
            if Founder.query.select_from(pam.BivAccess).filter(
                    pam.BivAccess.source_biv_id == flask.session['user.biv_id'],
                    pam.BivAccess.target_biv_id == founder.biv_id
            ).first():
                res = Contestant.query.select_from(pam.BivAccess).filter(
                    pam.BivAccess.source_biv_id == Contestant.biv_id,
                    pam.BivAccess.target_biv_id == founder.biv_id,
                ).one()
                if res.is_public:
                    return res.format_uri('contestant')
        return None


class Contestant(db.Model, common.ModelWithDates):
    """contestant database model.

    Fields:
        biv_id: primary ID
        display_name: project name
        youtube_code: the VIDEO_ID for the youtube video
        slideshow_code: the SlideShare ID for the slide deck
        contestant_desc: project description
        tax_id: project EIN
        website: project website
        business_phone: contact by phone
        business_address: contact by mail
        is_public: is the project to be shown on the public contestant list?
        is_under_review: enables review of a non-public submission
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('contestant_s', start=1003, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    youtube_code = db.Column(db.String(500))
    slideshow_code = db.Column(db.String(500))
    contestant_desc = db.Column(db.String)
    tax_id = db.Column(db.String(30))
    website = db.Column(db.String(100))
    business_phone = db.Column(db.String(100))
    business_address = db.Column(db.String(500))
    is_public = db.Column(db.Boolean, nullable=False)
    is_under_review = db.Column(db.Boolean, nullable=False)

    def get_contest(self):
        """Returns the Contest model which owns this Contestant"""
        return Contest.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == Contest.biv_id,
            pam.BivAccess.target_biv_id == self.biv_id
        ).one()

    def get_founders(self):
        """Return a list of Founder models for this Contestant"""
        return Founder.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == Founder.biv_id
        ).all()

    def get_slideshow_code(self):
        """Returns the slideshare or youtube code for the pitch deck"""
        if self.is_youtube_slideshow():
            match = re.search(r'^youtube\:(.*)$', self.slideshow_code)
            return match.group(1)
        return self.slideshow_code

    def get_score_for_judge_user(self):
        """Returns this contestant's score for the current logged in judge"""
        total = 0.0
        for score in self._get_score_info_for_judge_user():
            total += JudgeScore.get_points_for_question(
                score.question_number) * (int(score.judge_score) - 1) / 3
        return total

    def get_summary(self):
        """Returns an excerpt for the Contestant.contestant_desc."""
        summary = self.contestant_desc
        match = re.search(
            r'^(.*?\s[a-z)]{3,}\.\s.*?\s[a-z)]{3,}\.\s)',
            summary,
            re.DOTALL
        )
        if match:
            return match.group(1)
        return summary

    def get_website(self):
        """Returns the contestant website, prepending http:// if necessary."""
        if self.website and not re.search(r'^http', self.website):
            return 'http://{}'.format(self.website)
        return self.website

    def is_judge(self):
        """Returns True if the current user is a judge for this Contest"""
        return self.get_contest().is_judge()

    def is_partial_scored_by_judge_user(self):
        # TODO(pjm): need meta data for question count
        return len(self._get_score_info_for_judge_user()) != 6

    def is_scored_by_judge_user(self):
        return len(self._get_score_info_for_judge_user()) > 0

    def is_youtube_slideshow(self):
        """Returns true if the slideshow is Youtube, not Slideshare."""
        return re.search(r'^youtube\:', self.slideshow_code)

    def _get_score_info_for_judge_user(self):
        return JudgeScore.query.filter(
            JudgeScore.judge_biv_id == flask.session['user.biv_id'],
            JudgeScore.contestant_biv_id == self.biv_id,
            JudgeScore.question_number > 0,
            JudgeScore.judge_score > 0
        ).all()


class Donor(db.Model, common.ModelWithDates):
    """donor database model.

    Fields:
        biv_id: primary ID
        amount: promised amount
        display_name: donor name, from paypal
        donor_email: donor email, from paypal
        donor_state: (submitted, pending_confirmation, executed, canceled)
        paypal_payment_id: payment id, from paypal post
        paypal_payer_id: payer id, from paypal url callback
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('donor_s', start=1007, increment=1000),
        primary_key=True
    )
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    display_name = db.Column(db.String(100))
    donor_email = db.Column(db.String(100))
    donor_state = db.Column(db.Enum(
        'submitted', 'pending_confirmation', 'executed', 'canceled',
        name='donor_state'))
    paypal_payment_id = db.Column(db.String(100))
    paypal_payer_id = db.Column(db.String(100))

    def add_to_session(self):
        """Add the donor to the session by biv_id."""
        controller.db.session.add(self)
        controller.db.session.flush()
        flask.session['donor.biv_id'] = self.biv_id

    def remove_from_session(self):
        """Remove the donor's biv_id from the session, if present."""
        if flask.session.get('donor.biv_id'):
            del flask.session['donor.biv_id']

    @staticmethod
    def unsafe_load_from_session():
        """Loads the donor from the session.
        Returns None if session value is missing or donor does not exist.
        """
        if flask.session.get('donor.biv_id'):
            return Donor.query.filter_by(
                biv_id=flask.session['donor.biv_id']
            ).first()
        return None


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
    founder_avatar = db.Column(db.LargeBinary)
    avatar_type = db.Column(db.Enum('gif', 'png', 'jpeg', name='avatar_type'))


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


class JudgeScore(db.Model, common.ModelWithDates):
    """judge_score database model.

    Fields:
        judge_biv_id: judge's User.biv_id
        contestant_biv_id: contestant ID
        question_number: question
        judge_score: contestant's score
        judge_comment: judge's comment to contestant
    """
    judge_biv_id = db.Column(db.Numeric(18), primary_key=True)
    contestant_biv_id = db.Column(db.Numeric(18), primary_key=True)
    question_number = db.Column(db.Numeric(9), primary_key=True)
    judge_score = db.Column(db.Numeric(9))
    judge_comment = db.Column(db.String)

    @classmethod
    def get_points_for_question(cls, number):
        return [
            10,
            10,
            10,
            5,
            10,
            15
        ][int(number) - 1]


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
        

Contest.BIV_MARKER = biv.register_marker(2, Contest)
Contestant.BIV_MARKER = biv.register_marker(3, Contestant)
Donor.BIV_MARKER = biv.register_marker(7, Donor)
Founder.BIV_MARKER = biv.register_marker(4, Founder)
Sponsor.BIV_MARKER = biv.register_marker(8, Sponsor)
Judge.BIV_MARKER = biv.register_marker(9, Sponsor)
