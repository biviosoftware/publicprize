# -*- coding: utf-8 -*-
""" contest forms: HTTP form processing for contest pages

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
import flask_wtf
import re
import urllib.request
import wtforms
import wtforms.validators as wtfv

from . import model as pnm
from .. import common
from .. import controller as ppc
from ..auth import model as pam

class Nomination(flask_wtf.Form):
    """Plain form that accepts a website nomination.

    A 'Nominator' is created on form submission (see pnm.Nominator)
    If the website is new, then a 'Nominee' is added for that website.
    """

    company_name = wtforms.StringField(
        'Company Name', validators=[
            wtfv.DataRequired(), wtfv.Length(max=200)])
    website = wtforms.StringField(
        'Company Website', validators=[
            wtfv.DataRequired(), wtfv.Length(max=200)])
    submitter_name = wtforms.StringField(
        'Your Name', validators=[
            wtfv.DataRequired(), wtfv.Length(max=200)])

    def execute(self, contest):
        """Validates website url and adds it to the database"""
        if self.is_submitted() and self.validate():
            nominee = self._create_models(contest)
            return flask.redirect(nominee.format_uri('nominate-thank-you'))
        return contest.task_class.get_template().render_template(
            contest,
            'nominate-website',
            form=self,
            selected='website-url'
        )

    def validate(self):
        """Performs url field validation"""
        super(Nomination, self).validate()
        self._validate_website()
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
        nominee.is_public = \
            ppc.app().config['PUBLICPRIZE']['ALL_PUBLIC_CONTESTANTS']
        nominee.is_under_review = False
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
        url = self._follow_url_and_redirects(self.website.data)
        # (mda) get the time here to minimize server processing time
        # interference (just in case of a hangup of some sort)
        if self._is_already_nominated(url):
            nominee = self._get_matching_nominee(url)
        else:
            nominee = self._create_nominee(url, contest)
        self._create_nominator(nominee, contest)
        return nominee

    def _get_matching_nominee(self, url):
        return pnm.Nominee.query.filter(pnm.Nominee.url == url).first()

    def _is_already_nominated(self, url):
        return pnm.Nominee.query.filter(pnm.Nominee.url == url).count() > 0

    def _follow_url_and_redirects(self, url):
        initial_normalized_url = self._normalize_url(url)
        response = urllib.request.urlopen(initial_normalized_url)
        response_url = response.geturl()
        response.close()
        return response_url

    def _normalize_url(self, url):
        if not re.search(r'^http', url):
            url = 'http://' + url
        return url.lower()

    def _validate_website(self):
        """Ensures the website exists"""
        if self.website.errors:
            return
        if self.website.data:
            if not common.get_url_content(self.website.data):
                self.website.errors = ['Website invalid or unavailable.']
