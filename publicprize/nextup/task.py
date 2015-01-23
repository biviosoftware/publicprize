# -*- coding: utf-8 -*-
""" controller actions for NUContest

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from . import form as pnf
from .. import common
from .. import controller as ppc

_template = common.Template('nextup');

class NUContest(ppc.Task):
    """Next Up Contest actions"""

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

    def action_nominate_thank_you(biv_obj):
        return _template.render_template(
            biv_obj.get_contest(),
            'nominate-thank-you',
            nominee=biv_obj,
            nominees_url=biv_obj.get_contest().format_absolute_uri('nominees'),
            nominee_tweet="I just nominated " + biv_obj.display_name
        );
