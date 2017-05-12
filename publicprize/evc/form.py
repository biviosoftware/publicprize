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

HELP_TEXT = {
    'nominee_desc': 'Explain what your company does, what your plan for success is, and any other details about your company that might impress the judges and general public.',
    'youtube_url': 'A video that tells that story to a general audience (think "Kickstarter")',
}


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
        'Description and "pitch"',
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
        nominee = self._create_or_update_models(contest, is_valid=self.validate())
        nid = biv.Id(nominee.biv_id).to_biv_uri()
        res = {
            'nominee_biv_id': biv.Id(nominee.biv_id).to_biv_uri(),
        }
        if nominee.is_valid:
            return res
        res['errors'] = {}
        for field in self:
            if field.errors:
                res['errors'][field.name] = field.errors[0]
        return res;

    def help_text(self, field):
        return HELP_TEXT.get(field)

    def validate(self):
        """Performs superclass wtforms validation followed by url
        field validation"""
        super(Nominate, self).validate()
        self._validate_youtube()
        self._validate_website()
        common.log_form_errors(self, True)
        return not self.errors

    #TODO(pjm): copied from evc
    def _add_founder(self, nominee, name, desc):
        """Creates the founder and links it to the nominee."""
        if not name.data:
            return
        self._add_founder(nominee, pcm.Founder(
            display_name=str(name.data),
            founder_desc=str(desc.data),
        ))
        ppc.db.session.add(founder)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=nominee.biv_id,
                target_biv_id=founder.biv_id
            )
        )

    #TODO(pjm): copied from evc
    def _add_founders(self, nominee, is_create):
        """Add the current user as a founder and any optional founders."""
        pcm.Founder.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == nominee.biv_id,
            pam.BivAccess.target_biv_id == pcm.Founder.biv_id
        ).all()
        self._add_founder(nominee, is_create, self.founder_name, self_founder_desc)
        self._add_founder(nominee, is_create, self.founder2_name, self_founder2_desc)
        self._add_founder(nominee, is_create, self.founder3_name, self_founder3_desc)

    def _create_or_update_models(self, contest, is_valid):
        nominee = self._unchecked_load_nominee(contest)
        is_create = not nominee
        if is_create:
            nominee = pem.E15Nominee()
        self.populate_obj(nominee)
        nominee.youtube_code = self._youtube_code()
        nominee.is_public = False
        nominee.is_valid = is_valid
        nominee.is_finalist = False
        nominee.is_semi_finalist = False
        nominee.is_winner = False
        ppc.db.session.add(nominee)
        ppc.db.session.flush()
        if is_create:
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
            if not common.get_url_content(self.url.data, want_decode=False):
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
