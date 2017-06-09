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

from ..debug import pp_t
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


# See _empty_to_none()
_EMPTY_FIELD = ' '

class Nominate(flask_wtf.Form):
    """Accept a new nominee."""

    display_name = wtforms.StringField(
        'Company Name',
        validators=[wtfv.DataRequired(), wtfv.Length(max=100)])
    url = wtforms.StringField(
        'Company Website',
        validators=[wtfv.DataRequired(), wtfv.Length(max=100)])
    contact_phone = wtforms.StringField(
        'Contact phone',
        validators=[wtfv.DataRequired(), wtfv.Length(max=20)])
    contact_address = wtforms.StringField(
        'Contact address',
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

    def metadata_and_values(self, contest):
        fv = None
        nominee = None
        if flask.session.get('user.is_logged_in'):
            nominee, ok = contest.nominee_pending_for_user()
            if ok:
                founders = nominee.founders_as_list()
            else:
                nominee = None

        def _value(n):
            if n == 'youtube_url':
                if not nominee.youtube_code:
                    return None
                return 'https://youtu.be/' + nominee.youtube_code
            if hasattr(nominee, n):
                return getattr(nominee, n)
            m = re.search(r'^founder(\d*)_(?:desc|name)$', n)
            if m:
                i = int(m.group(1) or 1) - 1
                if i >= len(founders):
                    return None
                n = 'display_name' if 'name' in n else 'founder_desc'
                return founders[i][n]
            if n in ('csrf_token'):
                return None
            raise AssertionError('{}: unknown field name'.format(n))

        def _empty_to_none(v):
            # POSIT _EMPTY_FIELD is white space
            if not v or not v.strip():
                return None
            return v

        res = []
        value = _value if nominee else lambda x: None
        for field in self:
            res.append({
                'helpText': self.help_text(field.name),
                'label': field.label.text,
                'name': field.name,
                'type': field.type,
                'value': _empty_to_none(value(field.name)),
            })
        return res


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

    def _add_founder(self, nominee, name, desc):
        """Creates the founder and links it to the nominee."""
        if not (name.data or desc.data):
            return
        founder = pcm.Founder(
            display_name=name.data or _EMPTY_FIELD,
            founder_desc=desc.data or _EMPTY_FIELD,
        )
        ppc.db.session.add(founder)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=nominee.biv_id,
                target_biv_id=founder.biv_id
            )
        )

    def _add_founders(self, nominee):
        """Add the current user as a founder and any optional founders."""
        nominee.delete_all_founders()
        self._add_founder(nominee, self.founder_name, self.founder_desc)
        self._add_founder(nominee, self.founder2_name, self.founder2_desc)
        self._add_founder(nominee, self.founder3_name, self.founder3_desc)

    def _create_or_update_models(self, contest, is_valid):
        nominee, is_update = contest.nominee_pending_for_user()
        self.populate_obj(nominee)
        if not nominee.display_name:
            nominee.display_name = _EMPTY_FIELD
        if not nominee.url:
            nominee.url = _EMPTY_FIELD
        nominee.youtube_code = self._youtube_code()
        nominee.is_public = False
        nominee.is_valid = is_valid
        nominee.is_finalist = False
        nominee.is_semi_finalist = False
        nominee.is_winner = False
        ppc.db.session.add(nominee)
        ppc.db.session.flush()
        self._add_founders(nominee)
        if not is_update:
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
        return nominee

    def _youtube_code(self):
        """Ensure the youtube url contains a VIDEO_ID"""
        value = self.youtube_url.data
        # http://youtu.be/a1Y73sPHKxw
        # or https://www.youtube.com/watch?v=a1Y73sPHKxw
        if not value:
            return None
        if re.search(r'\?', value) and re.search(r'v\=', value):
            match = re.search(r'(?:\?|\&)v\=(.*?)(&|$)', value)
            if match:
                return match.group(1)
        else:
            match = re.search(r'\/([^\&\?\/]+)$', value)
            if match:
                return match.group(1)
        return None

    def _validate_website(self):
        """Ensures the website exists"""
        if self.url.errors:
            return
        if self.url.data:
            if not common.get_url_content(self.url.data, want_decode=False):
                self.url.errors = ['Website invalid or unavailable.']


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
