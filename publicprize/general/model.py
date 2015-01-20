# -*- coding: utf-8 -*-
""" The singleton model which handles global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask

from .. import biv
from .. import common

PUB_OBJ = None

class General(common.Model):
    """Singleton model for global tasks."""

    def __init__(self, biv_id):
        super().__init__()
        self.biv_id = biv_id

    def get_login_uri(self):
        """Returns the appropriate login uri, depending on if the
        user.oauth_type is present in the session"""
        task = None

        if 'user.oauth_type' in flask.session:
            task = flask.session['user.oauth_type'] + '-login'
        else:
            task = 'login'
        return self.format_uri(task)

    @classmethod
    def load_biv_obj(cls, biv_id):
        return General(biv_id)

General.BIV_MARKER = biv.register_marker(1, General)
PUB_OBJ = General.BIV_MARKER.to_biv_id(1)
biv.register_alias(biv.URI_FOR_GENERAL_TASKS, PUB_OBJ)
biv.register_alias(biv.URI_FOR_ERROR, General.BIV_MARKER.to_biv_id(2))
biv.register_alias(biv.URI_FOR_STATIC_FILES, General.BIV_MARKER.to_biv_id(3))
biv.register_alias(biv.URI_FOR_NONE, General.BIV_MARKER.to_biv_id(4))
