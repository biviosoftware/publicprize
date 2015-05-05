# -*- coding: utf-8 -*-
""" controller actions for NUContest

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
import json
import sqlalchemy.orm

from . import form as pnf
from . import model as pnm
from .. import common
from .. import controller as ppc
from ..auth import model as pam
from ..contest import model as pcm

_template = common.Template('nextup')

class NUContest(ppc.Task):
    """Next Up Contest actions"""

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_judges(biv_obj):
        """Admin review judges"""
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        judges = pam.User.query.select_from(
            pam.BivAccess, access_alias, pcm.Judge).filter(
                pam.BivAccess.source_biv_id == pam.User.biv_id,
                pam.BivAccess.target_biv_id == pcm.Judge.biv_id,
                access_alias.source_biv_id == biv_obj.biv_id,
                access_alias.target_biv_id == pcm.Judge.biv_id,
            ).all()
        rank_count = {}
        for judge in judges:
            rank_count[judge.biv_id] = {}
            nominees = pnm.Nominee.query.select_from(
                pam.BivAccess, pnm.JudgeRank).filter(
                    pam.BivAccess.source_biv_id == biv_obj.biv_id,
                    pam.BivAccess.target_biv_id == pnm.Nominee.biv_id,
                    pnm.JudgeRank.nominee_biv_id == pnm.Nominee.biv_id,
                    pnm.JudgeRank.judge_biv_id == judge.biv_id,
                ).all()
            for nominee in nominees:
                if not rank_count[judge.biv_id].get(nominee.category):
                    rank_count[judge.biv_id][nominee.category] = 0;
                rank_count[judge.biv_id][nominee.category] += 1
        return _template.render_template(
            biv_obj,
            'admin-review-judges',
            judges=judges,
            rank_count=rank_count,
        )

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_nominees(biv_obj):
        """Admin review nominees"""
        return _template.render_template(biv_obj, 'admin-review-nominees')

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_scores(biv_obj):
        """Admin review voting and judge ranking"""
        category = NUContest._get_category()
        return _template.render_template(
            biv_obj,
            'admin-review-scores',
            category=category
        )

    def action_index(biv_obj):
        """Contest home, redirect to nominate or vote depending on state"""
        return NUContest.action_vote(biv_obj)

    def action_nominate(biv_obj):
        """Contest nomination page"""
        return pnf.Nomination().execute(biv_obj)

    def action_nominees(biv_obj):
        """Public list of nominated websites"""
        return _template.render_template(biv_obj, 'nominees')

    @common.decorator_login_required
    @common.decorator_user_is_judge
    def action_judging(biv_obj):
        """Rank the nominees (1st to 10th)"""
        category = NUContest._get_category()
        ranks = [None] * pnm.JudgeRank.MAX_RANKS
        ranks.insert(0, category)
        for judge_rank in biv_obj.get_judge_ranks_for_auth_user(category):
            ranks[int(judge_rank.judge_rank)] = str(judge_rank.nominee_biv_id)
        return _template.render_template(
            biv_obj,
            'judging',
            category=category,
            ranks=json.dumps(ranks),
            max_ranks=pnm.JudgeRank.MAX_RANKS
        )

    @common.decorator_login_required
    @common.decorator_user_is_judge
    def action_judge_ranking(biv_obj):
        """Save the judge's ranking"""
        return pnf.Judge().execute(biv_obj)

    def action_new_test_judge(biv_obj):
        """Creates a new test user and judge models and log in."""
        return pcm.Judge.new_test_judge(biv_obj)

    def action_vote(biv_obj):
        """Vote for a nominee"""
        category = NUContest._get_category()
        return _template.render_template(
            biv_obj,
            'nominee-voting',
            category=category,
            user_vote=biv_obj.get_vote_for_auth_user(category)
        )

    def get_template():
        return _template

    def _get_category():
        """Returns the category from the request query, defaults to 'pint'"""
        return 'pitcher' \
            if (flask.request.args.get('category') or '') == 'pitcher' \
            else 'pint'


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
