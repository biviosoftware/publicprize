# -*- coding: utf-8 -*-
""" controller actions for Contest, Contestand and Founder

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from . import form as pnf
from .. import common
from .. import controller as ppc

_template = common.Template('nextup');

class NUContest(ppc.Task):
    """Next Up Contest actions"""

    def action_nominate_website(biv_obj):
        """Page where users can nominate websites to be submitted"""
        return pnf.Nomination().execute(biv_obj)

    def action_submitted_websites(biv_obj):
        """Public list of nominated websites"""
        return _template.render_template(biv_obj, 'submitted-websites')

    def action_index(biv_obj):
        """Default to contestant list"""
        print('index biv_obj: ', biv_obj);
        return NUContest.action_nominate_website(biv_obj)

    def get_template():
        return _template
