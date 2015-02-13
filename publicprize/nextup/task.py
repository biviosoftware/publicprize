# -*- coding: utf-8 -*-
""" controller actions for NUContest

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask

from . import form as pnf
from .. import common
from .. import controller as ppc

_template = common.Template('nextup')

class NUContest(ppc.Task):
    """Next Up Contest actions"""

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_nominees(biv_obj):
        """Admin review nominees"""
        return _template.render_template(biv_obj, 'admin-review-nominees')

    def action_index(biv_obj):
        """Contest home and nomination page"""
        return pnf.Nomination().execute(biv_obj)

    def action_nominees(biv_obj):
        """Public list of nominated websites"""
        return _template.render_template(biv_obj, 'nominees')

    def get_template():
        return _template

class Nominee(ppc.Task):
    """Nominee actions"""

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_edit_nominee(biv_obj):
        """Admin edit nominees"""
        return pnf.NomineeEdit(obj=biv_obj).execute(biv_obj)

    def action_nominate(biv_obj):
        return _template.render_template(
            biv_obj.get_contest(),
            'nominate-thank-you',
            nominee=biv_obj,
            nominee_url=biv_obj.format_absolute_uri('nominees'),
            nominee_tweet="I just nominated " + biv_obj.display_name
        )

    def action_nominees(biv_obj):
        """Public list of nominated websites, with the current nominee
        for social media meta links."""
        return _template.render_template(
            biv_obj.get_contest(),
            'nominees',
            nominee=biv_obj,
            nominee_url=biv_obj.format_absolute_uri('nominees'),
            nominee_tweet="I just nominated " + biv_obj.display_name,
            nextup_icon_url=flask.url_for(
                'static',
                _external=True,
                _scheme=(
                    'http' if ppc.app().config['PUBLICPRIZE']['TEST_MODE']
                    else 'https'),
                filename='img/nextup-200x200.png')
        )

