# -*- coding: utf-8 -*-
""" The singleton model which handles global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import io
import flask

from .. import controller

class Sponsor(controller.Task):
    """Sponsor actions"""
    def action_sponsor_logo(biv_obj):
        """Sponsor logo image"""
        return flask.send_file(
            io.BytesIO(biv_obj.sponsor_logo),
            'image/{}'.format(biv_obj.logo_type)
        )
