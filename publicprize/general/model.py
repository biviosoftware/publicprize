# -*- coding: utf-8 -*-
""" The singleton model which handles global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

from publicprize import biv
from publicprize import controller

PUB_OBJ = None


class General(controller.Model):
    """Singleton model for global tasks."""

    def __init__(self, biv_id):
        super().__init__()
        self.biv_id = biv_id

    @classmethod
    def load_biv_obj(cls, biv_id):
        return General(biv_id)

General.BIV_MARKER = biv.register_marker(1, General)
PUB_OBJ = General.BIV_MARKER.to_biv_id(1)
biv.register_alias(biv.URI_FOR_GENERAL_TASKS, PUB_OBJ)
biv.register_alias(biv.URI_FOR_ERROR, General.BIV_MARKER.to_biv_id(2))
biv.register_alias(biv.URI_FOR_STATIC_FILES, General.BIV_MARKER.to_biv_id(3))
biv.register_alias(biv.URI_FOR_NONE, General.BIV_MARKER.to_biv_id(4))
