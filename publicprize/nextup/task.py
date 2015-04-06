# -*- coding: utf-8 -*-
""" controller actions for NUContest

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask

from . import form as pnf
from . import model as pnm
from .. import common
from .. import controller as ppc
from ..auth import model as pam

_template = common.Template('nextup')

class NUContest(ppc.Task):
    """Next Up Contest actions"""

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_nominees(biv_obj):
        """Admin review nominees"""
        return _template.render_template(biv_obj, 'admin-review-nominees')

    def action_index(biv_obj):
        """Contest home, redirect to nominate or vote depending on state"""
        return NUContest.action_vote(biv_obj)

    def action_nominate(biv_obj):
        """Contest nomination page"""
        return pnf.Nomination().execute(biv_obj)

    def action_nominees(biv_obj):
        """Public list of nominated websites"""
        return _template.render_template(biv_obj, 'nominees')

    def action_vote(biv_obj):
        """Vote for a nominee"""
        category = 'pitcher' \
            if (flask.request.args.get('category') or '') == 'pitcher' \
            else 'pint'
        return _template.render_template(
            biv_obj,
            'nominee-voting',
            category=category,
            user_vote=biv_obj.get_vote_for_auth_user(category)
        )

    def get_template():
        return _template


class Nominee(ppc.Task):
    """Nominee actions"""

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_edit_nominee(biv_obj):
        """Admin edit nominees"""
        return pnf.NomineeEdit(obj=biv_obj).execute(biv_obj)

    def action_nominate(biv_obj):
        return _template.render_template(
            biv_obj.get_contest(),
            'nominate-thank-you',
            **_nominated_social_kwargs(biv_obj)
        )

    def action_nominees(biv_obj):
        """Landing page for social media nomination."""
        return _template.render_template(
            biv_obj.get_contest(),
            'nominees',
            **_nominated_social_kwargs(biv_obj)
        )

    @common.decorator_login_required
    def action_override_vote(biv_obj):
        """Change vote confirmation"""
        return _template.render_template(
            biv_obj.get_contest(),
            'voting-override',
            sub_base_template=_template.base_template('nominee-voting'),
            nominee=biv_obj,
            category=biv_obj.category,
            user_vote=biv_obj.get_contest().get_vote_for_auth_user(
                biv_obj.category)
        )

    @common.decorator_login_required
    def action_thank_you(biv_obj):
        """Shows vote page with thank-you popup."""
        return _template.render_template(
            biv_obj.get_contest(),
            'voting-thank-you',
            sub_base_template=_template.base_template('nominee-voting'),
            category=biv_obj.category,
            user_vote=biv_obj.get_contest().get_vote_for_auth_user(
                biv_obj.category),
            **_voted_social_kwargs(biv_obj)
        )

    @common.decorator_login_required
    def action_user_vote(biv_obj):
        """Places vote for the current user with this nominee."""
        vote = biv_obj.get_contest().get_vote_for_auth_user(biv_obj.category)
        if vote:
            if flask.request.args.get('override'):
                biv_obj.get_contest().delete_votes_for_auth_user(
                    biv_obj.category)
            elif vote.nominee == biv_obj.biv_id:
                return flask.redirect(biv_obj.get_contest().format_uri(
                        'vote',
                        query={ 'category': biv_obj.category },
                        anchor='vote'
                        ))
            else:
                return flask.redirect(biv_obj.format_uri(
                        'override-vote',
                        query={'target': biv_obj.biv_id},
                        anchor='vote'))
        vote = pnm.NUVote(
            user=flask.session['user.biv_id'],
            nominee=biv_obj.biv_id
        )
        ppc.db.session.add(vote)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=biv_obj.get_contest().biv_id,
                target_biv_id=vote.biv_id
            )
        )
        return flask.redirect(biv_obj.format_uri(
                'thank-you',
                anchor='vote'
            )
        )

    def action_vote(biv_obj):
        """Landing page for social media voting."""
        return _template.render_template(
            biv_obj.get_contest(),
            'nominee-voting',
            category=biv_obj.category,
            user_vote=biv_obj.get_contest().get_vote_for_auth_user(
                biv_obj.category),
            **_voted_social_kwargs(biv_obj)
        )


def _nextup_icon_url():
    return flask.url_for(
        'static',
        _external=True,
        _scheme=(
            'http' if ppc.app().config['PUBLICPRIZE']['TEST_MODE']
            else 'https'),
        filename='img/nextup-200x200.png')


def _nominated_social_kwargs(nominee):
    return {
        'nominee': nominee,
        'nominee_url': nominee.format_absolute_uri('nominees'),
        'nominee_tweet': "I just nominated " + nominee.display_name,
        'nextup_icon_url': _nextup_icon_url()
    }

def _voted_social_kwargs(nominee):
    return {
        'nominee': nominee,
        'nominee_url': nominee.format_absolute_uri('vote'),
        'nominee_tweet': "I just voted for " + nominee.display_name,
        'nextup_icon_url': _nextup_icon_url()
    }

