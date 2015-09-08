# -*- coding: utf-8 -*-
""" HTTP form processing for contest pages

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import re
import flask
import flask_wtf
import wtforms
import wtforms.validators as wtfv

from . import model as pem
from .. import biv
from .. import common
from .. import controller as ppc
from ..auth import model as pam
from ..contest import model as pcm

class Nominate(flask_wtf.Form):
    """Accept a new nominee."""

    display_name = wtforms.StringField(
        'Company Name',
        validators=[wtfv.DataRequired(), wtfv.Length(max=100)])
    url = wtforms.StringField(
        'Company Website',
        validators=[wtfv.DataRequired(), wtfv.Length(max=100)])
    youtube_url = wtforms.StringField(
        'YouTube Video URL',
        validators=[wtfv.DataRequired(), wtfv.Length(max=500)])
    nominee_desc = wtforms.TextAreaField(
        'Explanation',
        validators=[wtfv.DataRequired(), wtfv.Length(max=10000)])
    founder_name = wtforms.StringField(
        'Founder Name',
        validators=[wtfv.DataRequired(), wtfv.Length(max=100)])
    founder_desc = wtforms.TextAreaField(
        'Founder Bio',
        validators=[wtfv.DataRequired(), wtfv.Length(max=10000)])
    founder2_name = wtforms.StringField(
        'Other Founder Name', validators=[wtfv.Length(max=100)])
    founder2_desc = wtforms.TextAreaField(
        'Other Founder Bio', validators=[wtfv.Length(max=10000)])
    founder3_name = wtforms.StringField(
        'Other Founder Name', validators=[wtfv.Length(max=100)])
    founder3_desc = wtforms.TextAreaField(
        'Other Founder Bio', validators=[wtfv.Length(max=10000)])

    def execute(self, contest):
        """Validates website url and adds it to the database"""
        if self.validate():
            nominee = self._create_models(contest)
            return {
                'nominee_biv_id': biv.Id(nominee.biv_id).to_biv_uri(),
            }
        res = {}
        for field in self:
            if field.errors:
                res[field.name] = field.errors[0]
        return {
            'errors': res,
        }

    def validate(self):
        """Performs superclass wtforms validation followed by url
        field validation"""
        super(Nominate, self).validate()
        self._validate_youtube()
        self._validate_website()
        common.log_form_errors(self)
        return not self.errors

    #TODO(pjm): copied from evc
    def _add_founder(self, nominee, founder):
        """Creates the founder and links it to the nominee."""
        ppc.db.session.add(founder)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=nominee.biv_id,
                target_biv_id=founder.biv_id
            )
        )

    #TODO(pjm): copied from evc
    def _add_founders(self, nominee):
        """Add the current user as a founder and any optional founders."""
        self._add_founder(nominee, pcm.Founder(
            display_name=str(self.founder_name.data),
            founder_desc=str(self.founder_desc.data),
        ))
        if self.founder2_name.data:
            self._add_founder(nominee, pcm.Founder(
                display_name=str(self.founder2_name.data),
                founder_desc=str(self.founder2_desc.data),
            ))
        if self.founder3_name.data:
            self._add_founder(nominee, pcm.Founder(
                display_name=str(self.founder3_name.data),
                founder_desc=str(self.founder3_desc.data),
            ))

    def _create_models(self, contest):
        nominee = pem.E15Nominee()
        self.populate_obj(nominee)
        nominee.youtube_code = self._youtube_code()
        nominee.is_public = False
        ppc.db.session.add(nominee)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contest.biv_id,
                target_biv_id=nominee.biv_id
            )
        )
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=flask.session['user.biv_id'],
                target_biv_id=nominee.biv_id
            )
        )
        self._add_founders(nominee)
        return nominee


    #TODO(pjm): copied from evc
    def _youtube_code(self):
        """Ensure the youtube url contains a VIDEO_ID"""
        value = self.youtube_url.data
        # http://youtu.be/a1Y73sPHKxw
        # or https://www.youtube.com/watch?v=a1Y73sPHKxw
        if re.search(r'\?', value) and re.search(r'v\=', value):
            match = re.search(r'(?:\?|\&)v\=(.*?)(&|$)', value)
            if match:
                return match.group(1)
        else:
            match = re.search(r'\/([^\&\?\/]+)$', value)
            if match:
                return match.group(1)
        return None

    #TODO(pjm): copied from evc
    def _validate_website(self):
        """Ensures the website exists"""
        if self.url.errors:
            return
        if self.url.data:
            if not common.get_url_content(self.url.data):
                self.url.errors = ['Website invalid or unavailable.']

    #TODO(pjm): copied from evc
    def _validate_youtube(self):
        """Ensures the YouTube video exists"""
        if self.youtube_url.errors:
            return
        code = self._youtube_code()
        if code:
            html = common.get_url_content('http://youtu.be/' + code)
            # TODO(pjm): need better detection for not-found page
            if not html or re.search(r'<title>YouTube</title>', html):
                self.youtube_url.errors = [
                    'Unknown YouTube VIDEO_ID: ' + code + '.']
        else:
            self.youtube_url.errors = ['Invalid YouTube URL.']
