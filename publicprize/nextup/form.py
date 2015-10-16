# -*- coding: utf-8 -*-
""" contest forms: HTTP form processing for contest pages

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
import flask_mail
import flask_wtf
import json
import re
import urllib.request
import wtforms
import wtforms.validators as wtfv

from . import model as pnm
from .. import common
from .. import controller as ppc
from ..auth import model as pam
from ..contest import model as pcm

class Judge(flask_wtf.Form):
    """Posted form for saving judge ranking."""

    ranks = wtforms.StringField()

    def execute(self, contest):
        if self.is_submitted():
            ranks = json.loads(self.ranks.data)
            # first item is the category
            contest.delete_judge_ranks_for_auth_user(ranks[0])
            for i in range(1, pcm.JudgeRank.MAX_RANKS + 1):
                if len(ranks) > i and ranks[i]:
                    ppc.db.session.add(
                        pcm.JudgeRank(
                            judge_biv_id=flask.session['user.biv_id'],
                            nominee_biv_id=ranks[i],
                            judge_rank=i)
                        )
            return json.dumps(ranks)
        return ''

class Nomination(flask_wtf.Form):
    """Plain form that accepts a website nomination.

    A 'Nominator' is created on form submission (see pnm.Nominator)
    If the website is new, then a 'Nominee' is added for that website.
    """

    company_name = wtforms.StringField(
        'Company Name', validators=[
            wtfv.DataRequired(), wtfv.Length(max=100)])
    url = wtforms.StringField(
        'Company Website', validators=[
            wtfv.DataRequired(), wtfv.Length(max=100)])
    submitter_name = wtforms.StringField(
        'Your Name', validators=[
            wtfv.DataRequired(), wtfv.Length(max=100)])

    def execute(self, contest):
        """Validates website url and adds it to the database"""
        if self.is_submitted() and self.validate():
            nominee = self._create_models(contest)
            return flask.redirect(nominee.format_uri('nominate'))
        return contest.task_class.get_template().render_template(
            contest,
            'nominate-website',
            form=self,
            selected='website-url'
        )

    def validate(self):
        """Performs url field validation"""
        super(Nomination, self).validate()
        validate_website(self)
        common.log_form_errors(self)
        return not self.errors

    def _create_nominator(self, nominee, contest):
        """Creates the Nominator model"""
        nominator = pnm.Nominator()
        nominator.display_name = self.submitter_name.data
        nominator.browser_string = flask.request.headers.get('User-Agent')
        # TODO(mda): verify that the access route returns correct urls when
        # accessed from remote location (this is hard to test from a local
        # machine)
        route = flask.request.access_route
        # (mda) Trusting the first item in the client ip route is a potential
        # security risk, as the client may spoof this to potentially inject code
        # this shouldn't be a problem in our implementation, as in the worst
        # case, we'll just be recording a bogus value.
        try:
            nominator.client_ip = route[0][:pnm.Nominator.client_ip.type.length]
        except IndexError:
            nominator.client_ip = 'ip unrecordable'
            ppc.app().logger.warn(
                "failed to record client ip. route: {}. ".format(route),
                "Recording ip as '{}'".format(nominator.client_ip))
        nominator.nominee = nominee.biv_id
        ppc.db.session.add(nominator)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contest.biv_id,
                target_biv_id=nominator.biv_id
            )
        )
        if flask.session.get('user.biv_id'):
            ppc.db.session.add(
                pam.BivAccess(
                    source_biv_id=flask.session['user.biv_id'],
                    target_biv_id=nominator.biv_id
                )
            )
        return nominator

    def _create_nominee(self, url, contest):
        """Creates the Nominee model"""
        nominee = pnm.Nominee()
        nominee.url = url
        nominee.display_name = self.company_name.data
        nominee.is_public = True
        nominee.is_under_review = False
        nominee.category = 'unknown'
        ppc.db.session.add(nominee)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contest.biv_id,
                target_biv_id=nominee.biv_id
            )
        )
        return nominee

    def _create_models(self, contest):
        """Creates the Nominee and Nominator models and links them
        with BivAccess models"""
        # (mda) get the time here to minimize server processing time
        # interference (just in case of a hangup of some sort)
        if self._is_already_nominated(self.url.data):
            nominee = self._get_matching_nominee(self.url.data)
        else:
            nominee = self._create_nominee(self.url.data, contest)
        nominator = self._create_nominator(nominee, contest)
        self._send_admin_email(nominee, nominator)
        return nominee

    def _get_matching_nominee(self, url):
        return pnm.Nominee.query.filter(pnm.Nominee.url == url).first()

    def _is_already_nominated(self, url):
        return pnm.Nominee.query.filter(pnm.Nominee.url == url).count() > 0

    def _send_admin_email(self, nominee, nominator):
        ppc.mail().send(flask_mail.Message(
            common.safe_unicode(
                    'Company Nominated: {}'.format(nominee.display_name)),
            recipients=[ppc.app().config['PUBLICPRIZE']['ADMIN_EMAIL']],
            body=common.safe_unicode('{} ({})\nSubmitted by {}'.format(
                    nominee.display_name, nominee.url, nominator.display_name))
            ))


class NomineeEdit(flask_wtf.Form):
    """Update nominee fields."""

    display_name = wtforms.StringField(
        'Company Name', validators=[
            wtfv.DataRequired(), wtfv.Length(max=100)])
    url = wtforms.StringField(
        'Company Website', validators=[
            wtfv.DataRequired(), wtfv.Length(max=100)])
    #TODO(pjm): should get values from model field
    category = wtforms.RadioField('Category', choices=[
            ('unknown', 'unknown'),
            ('pint', 'pint'),
            ('pitcher', 'pitcher')])
    is_public = wtforms.BooleanField('Public')

    def execute(self, nominee):
        """Update nominee info."""
        contest = nominee.get_contest()
        if self.is_submitted() and self.validate():
            self.populate_obj(nominee)
            ppc.db.session.add(nominee)
            return flask.redirect(contest.format_uri('admin-review-nominees'))
        return contest.task_class.get_template().render_template(
            contest,
            'admin-edit-nominee',
            form=self,
            nominee=nominee,
        )

    def validate(self):
        """Performs url field validation"""
        super(NomineeEdit, self).validate()
        validate_website(self)
        common.log_form_errors(self)
        return not self.errors


def validate_website(form):
    """Ensures the website exists"""
    if form.url.errors:
        return
    if form.url.data:
        if not common.get_url_content(form.url.data, want_decode=False):
            form.url.errors = ['Website invalid or unavailable.']
            return
        form.url.data = common.get_url_request(form.url.data).geturl()
