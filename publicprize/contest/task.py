# -*- coding: utf-8 -*-
""" controller actions for Contest, Contestand and Founder

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
import io
import publicprize.contest.form as pcf
import publicprize.contest.model as pcm
import publicprize.controller as ppc
import publicprize.auth.model as pam
import werkzeug.exceptions


class Contest(ppc.Task):
    """Contest actions"""
    def action_about(biv_obj):
        """About page"""
        return Contest._render_template(biv_obj, 'about')

    def action_contestants(biv_obj):
        """Public contestant list"""
        return Contest._render_template(
            biv_obj,
            'contestants',
        )

    def action_index(biv_obj):
        """Default to contestant list"""
        return Contest.action_contestants(biv_obj)

    def action_judges(biv_obj):
        """List of judges page"""
        return Contest._render_template(biv_obj, 'judges')

    def action_logo(biv_obj):
        """Contestant logo image"""
        return flask.send_file(
            io.BytesIO(biv_obj.contest_logo),
            'image/{}'.format(biv_obj.logo_type)
        )

    def action_rules(biv_obj):
        return flask.redirect('/static/pdf/rules.pdf')
    
    @ppc.login_required
    def action_submit_contestant(biv_obj):
        """Submit project page"""
        return pcf.Contestant().execute(biv_obj)

    def _render_template(biv_obj, name, **kwargs):
        """Render the page, putting the selected menu and contest in env"""
        return flask.render_template(
            'contest/{}.html'.format(name),
            contest=biv_obj,
            selected=name,
            **kwargs
        )


class Contestant(ppc.Task):
    """Contestant actions"""
    def action_contestant(biv_obj):
        """Project detail page, loads contest owner and project founders"""
        if biv_obj.is_public or biv_obj.is_under_review:
            return pcf.Donate().execute(biv_obj)
        werkzeug.exceptions.abort(404)

    def action_donate_cancel(biv_obj):
        """Return from cancelled payment on paypal site"""
        donor = pcm.Donor.unsafe_load_from_session()
        if donor:
            donor.remove_from_session()
            donor.donor_state = 'canceled'
            ppc.db.session.add(donor)
        form = pcf.Donate()
        form.amount.errors = ['Please resubmit your donation.']
        return form.execute(biv_obj)

    def action_donate_done(biv_obj):
        """Execute the payment after returning from paypal"""
        return pcf.Donate().execute_payment(biv_obj)

    def action_index(biv_obj):
        """Default to contestant page"""
        return Contestant.action_contestant(biv_obj)

    def action_thank_you(biv_obj):
        """Show a Thank you page with social media links for contestant."""
        return flask.render_template(
            'contest/thank-you.html',
            contestant=biv_obj,
            contest=biv_obj.get_contest(),
            founders=biv_obj.get_founders(),
            contestant_url=biv_obj.format_absolute_uri(),
            contestant_tweet="I just backed " + biv_obj.display_name
        )

class Founder(ppc.Task):
    """Founder actions"""
    def action_founder_avatar(biv_obj):
        """Founder avatar image"""
        return flask.send_file(
            io.BytesIO(biv_obj.founder_avatar),
            'image/{}'.format(biv_obj.avatar_type)
        )


class Sponsor(ppc.Task):
    """Sponsor actions"""
    def action_sponsor_logo(biv_obj):
        """Sponsor logo image"""
        return flask.send_file(
            io.BytesIO(biv_obj.sponsor_logo),
            'image/{}'.format(biv_obj.logo_type)
        )
    
