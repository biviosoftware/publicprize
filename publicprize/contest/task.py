# -*- coding: utf-8 -*-
""" The singleton model which handles global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""
from .. import biv
from .. import common
from .. import controller
from ..controller import db
from ..debug import pp_t
import flask
import io


class Founder(controller.Task):
    """Founder actions"""
    pass


class Sponsor(controller.Task):
    """Sponsor actions"""
    def action_sponsor_logo(biv_obj):
        """Sponsor logo image"""
        return _send_image_data(biv_obj, 'sponsor_logo', 'logo_type')


def _send_image_data(biv_obj, data, data_type):
    # see SEND_FILE_MAX_AGE_DEFAULT config value
    return flask.send_file(
        io.BytesIO(getattr(biv_obj, data)),
        'image/{}'.format(getattr(biv_obj, data_type))
    )
