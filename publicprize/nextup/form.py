# -*- coding: utf-8 -*-
""" contest forms: HTTP form processing for contest pages

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import locale
import re
import socket
import sys
import urllib.request

import flask
import flask_wtf
import wtforms
import wtforms.validators as wtfv

from . import model as pnm
from .. import controller as ppc
from ..auth import model as pam

class Nomination(flask_wtf.Form):
    """Plain form that accepts a website nomination.

    A 'Nominator' is created on form submission (see pnm.Nominator)
    If the website is new, then a 'Nominee' is added for that website.

    Fields: Website
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
            nominee, _ = self._update_models(contest)
            url = nominee.url
            if url:
                return flask.redirect(nominee.format_uri('nominate-thank-you'))
        return contest.task_class.get_template().render_template(
            contest,
            'nominate-website',
            form=self,
            selected='website-url'
        )

    def _update_models(self, contest):
        """Creates the Contestant and Founder models
        and adds BivAccess models to join the contest and Founder models"""
        url = self.website.data
        # (mda) get the time here to minimize server processing time
        # interference (just in case of a hangup of some sort)
        if not self._is_already_nominated(url):
            nominee = pnm.Nominee()
            self.populate_obj(nominee)
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
        else:
            nominee = self._get_matching_nominee(url)
        assert nominee is not None
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
            print("Error, failed to record client ip. route: {}. ".format(route),
                  "Recording ip as '{}'".format(nominator.client_ip),
                  file=sys.stderr)
        nominator.nominee = nominee.biv_id
        ppc.db.session.add(nominator)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contest.biv_id,
                target_biv_id=nominator.biv_id
            )
        )
        return nominee, nominator

    def _is_already_nominated(self, url):
        return pnm.Nominee.query.filter(pnm.Nominee.url == url).count() > 0

    def _get_matching_nominee(self, url):
        return pnm.Nominee.query.filter(pnm.Nominee.url == url).first()

    def validate(self):
        """Performs url field validation"""
        super(Nomination, self).validate()
        self._validate_website()
        _log_errors(self)
        return not self.errors

    def _validate_website(self):
        """Ensures the website exists"""
        if self.website.errors:
            return
        if self.website.data:
            if not self._get_url_content(self.website.data):
                self.website.errors = ['Website invalid or unavailable.']

    def _get_url_content(self, url):
        """Performs a HTTP GET on the url.

        Returns False if the url is invalid or not-found"""
        res = None
        if not re.search(r'^http', url):
            url = 'http://' + url
        try:
            req = urllib.request.urlopen(url, None, 30)
            res = req.read().decode(locale.getlocale()[1])
            req.close()
        except urllib.request.URLError:
            return None
        except ValueError:
            return None
        except socket.timeout:
            return None
        return res

def _log_errors(form):
    """Put any form errors in logs as warning"""
    if form.errors:
        ppc.app().logger.warn({
            'data': flask.request.form,
            'errors': form.errors
        })
