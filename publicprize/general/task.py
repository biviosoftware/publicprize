# -*- coding: utf-8 -*-
""" Global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
from publicprize import controller
from publicprize.auth.model import User
import publicprize.contest.model
import publicprize.general.oauth as oauth
import werkzeug


class General(controller.Task):
    """Global tasks"""
    def action_index(biv_obj):
        """Site index"""
        return flask.render_template(
            "general/index.html",
            contests=publicprize.contest.model.Contest.query.all()
        )

    def action_facebook_login(biv_obj):
        """Login with facebook."""
        return oauth.authorize(
            'facebook',
            biv_obj.format_absolute_uri('facebook-authorized')
        )

    def action_facebook_authorized(biv_obj):
        """Facebook login response"""
        return oauth.authorize_complete('facebook')

    def action_google_login(biv_obj):
        """Login with google."""
        return oauth.authorize(
            'google',
            biv_obj.format_absolute_uri('google-authorized')
        )

    def action_google_authorized(biv_obj):
        """Google login response"""
        return oauth.authorize_complete('google')

    def action_logout(biv_obj):
        """Logout"""
        return oauth.logout()

    def action_privacy_policy(biv_obj):
        return flask.render_template(
            "general/privacy-policy.html"
        )

    def action_not_found(biv_obj):
        """Not found page"""
        return flask.render_template('general/not-found.html'), 404

    def action_new_test_user(biv_obj):
        """Creates a new test user model and log in."""
        if not controller.app().config['PP_TEST_USER']:
            raise Error("PP_TEST_USER not enabled")
        name = 'F{} L{}'.format(
            werkzeug.security.gen_salt(6).lower(),
            werkzeug.security.gen_salt(8).lower())
        user = User(
            display_name=name,
            user_email='{}@localhost'.format(name.lower()),
            oauth_type='test',
            oauth_id=werkzeug.security.gen_salt(64)
        )
        oauth.add_user_to_session(user)
        return flask.redirect('/')

    def action_terms_of_use(biv_obj):
        return flask.render_template(
            "general/terms-of-use.html"
        )
