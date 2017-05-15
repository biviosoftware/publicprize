# -*- coding: utf-8 -*-
""" Global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import werkzeug
import flask

from . import oauth
from .. import controller
from ..auth import model as pam
from . import model as pgm

class General(controller.Task):
    """Global tasks"""
    def action_index(biv_obj):
        """Site index"""
        redirect = controller.app().config['PUBLICPRIZE']['INDEX_URI']
        return flask.redirect(redirect)

    def action_facebook_login(biv_obj):
        """Login with facebook."""
        return oauth.authorize(
            'facebook',
            biv_obj.format_absolute_uri('facebook-authorized')
        )

    def action_facebook_authorized(biv_obj):
        """Facebook login response"""
        return oauth.authorize_complete('facebook')

    def action_forbidden(biv_obj):
        """Forbidden page"""
        return flask.render_template('general/forbidden.html'), 403

    def action_google_login(biv_obj):
        """Login with google."""
        return oauth.authorize(
            'google',
            biv_obj.format_absolute_uri('google-authorized')
        )

    def action_google_authorized(biv_obj):
        """Google login response"""
        return oauth.authorize_complete('google')

    def action_linkedin_authorized(biv_obj):
        """LinkedIn login response"""
        return oauth.authorize_complete('linkedin')

    def action_linkedin_login(biv_obj):
        """Login with google."""
        return oauth.authorize(
            'linkedin',
            biv_obj.format_absolute_uri('linkedin-authorized')
        )

    def action_login(biv_obj):
        """Show login options."""
        return flask.render_template(
            "general/login.html",
        )

    def action_logout(biv_obj):
        """Logout"""
        oauth.logout()
        flask.flash('You have successfully logged out.')
        return flask.redirect('/')

    def action_not_found(biv_obj):
        """Not found page"""
        return flask.render_template('general/not-found.html'), 404

    def action_new_test_admin(biv_obj):
        """Create a new test user, logs in, sets Admin status."""
        return General._user(biv_obj, pgm.General.new_test_admin)

    def action_new_test_user(biv_obj):
        """Creates a new test user model and log in."""
        return General._user(biv_obj, pgm.General.new_test_user)

    def action_privacy(biv_obj):
        return flask.redirect('/static/pdf/privacy.pdf')

    def action_terms(biv_obj):
        return flask.redirect('/static/pdf/terms.pdf')

    def action_test_login(biv_obj):
        if not controller.app().config['PUBLICPRIZE']['TEST_USER']:
            raise Exception("TEST_USER not enabled")
        return General.action_login(biv_obj)

    def action_vote(biv_obj):
        return flask.redirect('/esprit-venture-challenge#/vote');

    def _user(contest, op):
        user = op(contest)
        oauth.add_user_to_session(user)
        return flask.redirect('/')
