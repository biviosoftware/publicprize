# -*- coding: utf-8 -*-
""" contest forms: HTTP form processing for contest pages

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import locale
import pytz
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

    A 'Nominition' is created on form submission (see pnm.Nomination)
    If the website is new, then a 'Nominee' is added for that website.

    Fields: Website
    """

    company_name = wtforms.StringField(
        'Company Name', validators=[
            wtfv.DataRequired(), wtfv.Length(max=200)])
    website = wtforms.StringField(
        'Company URL', validators=[
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
                flask.flash('Thank you for submitting {} to {}.'.format(url, contest.display_name))
                return flask.redirect(contest.format_uri('nominate-website'))
                # TODO(mda): Build the thank you page (currently I'm only
                # flashing a thank-you message on the contestants page
                return flask.redirect(contest.format_uri('thank-you-page'))
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
        submission_datetime = self._get_current_time_MST()
        if not self._is_already_nominated(url):
            nominee = pnm.Nominee()
            self.populate_obj(nominee)
            nominee.url = url
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
        nomination = pnm.Nomination()
        # TODO(mda): verify that the access route returns correct urls when
        # accessed from remote location (this is hard to test from a local
        # machine)
        route = flask.request.access_route
        # (mda) Trusting the first item in the client ip route is a potential
        # security risk, as the client may spoof this to potentially inject code
        # this shouldn't be a problem in our implementation, as in the worst
        # case, we'll just be recording a bogus value.
        try:
            nomination.client_ip = route[0][:pnm.Nomination.client_ip.type.length]
        except IndexError:
            nomination.client_ip = 'ip unrecordable'
            print("Error, failed to record client ip. route: {}. ".format(route),
                  "Recording ip as '{}'".format(nomination.client_ip),
                  file=sys.stderr)
        nomination.submission_datetime = submission_datetime
        nomination.nominee = nominee.biv_id
        ppc.db.session.add(nomination)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contest.biv_id,
                target_biv_id=nomination.biv_id
            )
        )
        return nominee, nomination

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

    def _get_current_time_MST(self):
        """Returns a datetime object with the current date in MST"""
        tz = pytz.timezone('US/Mountain')
        current_time = datetime.datetime.now(tz)
        return current_time

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
