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

    @classmethod
    def new_test_admin(cls, contest):
        from ..auth import model as pam

        user = cls.new_test_user(contest)
        admin = pam.Admin()
        pam.db.session.add(admin)
        pam.db.session.flush()
        pam.db.session.add(pam.BivAccess(
            source_biv_id=user.biv_id,
            target_biv_id=admin.biv_id
        ))
        return user

    @classmethod
    def new_test_user(cls, contest):
        """Creates a new test user model"""
        from ..auth import model as pam
        import uuid
        import random
        import string
        from .. import controller

        assert controller.app().config['PUBLICPRIZE']['TEST_USER']
        name = 'F{} Test'.format(
            ''.join(
                random.SystemRandom().choice(string.ascii_lowercase) for _ in range(8),
            ),
        )
        user = pam.User(
            display_name=name,
            user_email='{}@localhost'.format(name.lower().replace(' ', '')),
            oauth_type='test',
            oauth_id=str(uuid.uuid1()),
        )
        pam.db.session.add(user)
        pam.db.session.flush()
        return user


General.BIV_MARKER = biv.register_marker(1, General)
PUB_OBJ = General.BIV_MARKER.to_biv_id(1)
biv.register_alias(biv.URI_FOR_GENERAL_TASKS, PUB_OBJ)
biv.register_alias(biv.URI_FOR_ERROR, General.BIV_MARKER.to_biv_id(2))
biv.register_alias(biv.URI_FOR_STATIC_FILES, General.BIV_MARKER.to_biv_id(3))
biv.register_alias(biv.URI_FOR_NONE, General.BIV_MARKER.to_biv_id(4))
