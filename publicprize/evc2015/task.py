# -*- coding: utf-8 -*-
""" controller actions for E15Contest and E15Nominee

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import flask
import functools
import json
import pytz
import random
import werkzeug
import werkzeug.exceptions

from . import form as pef
from . import model as pem
from .. import biv
from .. import common
from .. import controller as ppc
from ..auth import model as pam
from ..general import oauth
from ..contest import model as pcm

_template = common.Template('evc2015')


def decorator_user_is_event_voter(func):
    """Require the current user is an E15EventVoter."""
    @functools.wraps(func)
    def decorated_function(*args, **kwargs):
        """Forbidden unless allowed."""
        if E15Contest.is_event_voter(args[0]):
            return func(*args, **kwargs)
        werkzeug.exceptions.abort(403)
    return decorated_function


class E15Contest(ppc.Task):
    """Contest actions"""

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_judges(biv_obj):
        users = pcm.Judge.judge_users_for_contest(biv_obj)
        nominee_ids = {}
        for nominee in biv_obj.public_nominees():
            nominee_ids[nominee.biv_id] = True
        res = []

        for user in users:
            count = 0
            for rank in pcm.JudgeRank.judge_ranks_for_user(user.biv_id):
                if rank.nominee_biv_id in nominee_ids:
                    count += 1
            res.append({
                'display_name': user.display_name,
                'user_email': user.user_email,
                'rank_count': count,
            })
        return flask.jsonify({
            'judges': sorted(res, key=lambda user: user['display_name'])
        })

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_nominees(biv_obj):
        nominees = pem.E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == biv_obj.biv_id,
            pam.BivAccess.target_biv_id == pem.E15Nominee.biv_id
        ).all()
        nominees = sorted(nominees, key=lambda nominee: nominee.display_name)
        res = []
        for nominee in nominees:
            submitter = E15Contest._nominee_submitter(nominee)
            res.append({
                'biv_id': nominee.biv_id,
                'display_name': nominee.display_name,
                'founders': E15Contest._founder_info_for_nominee(nominee),
                'is_public': nominee.is_public,
                'nominee_desc': nominee.nominee_desc,
                'submitter_display_name': submitter.display_name,
                'submitter_email': submitter.user_email,
                'url': nominee.url,
                'youtube_code': nominee.youtube_code,
            })

        return flask.jsonify({
            'nominees': res,
        })

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_scores(biv_obj):
        scores = biv_obj.tally_all_scores();
        return flask.jsonify({
            'scores': sorted(scores, key=lambda nominee: nominee['display_name'])
        })

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_votes(biv_obj):
        res = []
        nominee_id_to_name = {}
        for nominee in biv_obj.public_nominees():
            nominee_id_to_name[nominee.biv_id] = nominee.display_name

        for vote in pcm.Vote.query.select_from(pam.User).filter(
                pcm.Vote.nominee_biv_id.in_(nominee_id_to_name.keys()),
        ).all():
            user = pam.User.query.filter_by(
                biv_id=vote.user
            ).one()
            res.append({
                'biv_id': vote.biv_id,
                'creation_date_time': vote.creation_date_time,
                'user_display_name': '{} ({})'.format(user.display_name, user.user_email),
                'twitter_handle': vote.twitter_handle,
                'nominee_display_name': nominee_id_to_name[vote.nominee_biv_id],
                'vote_status': vote.vote_status,
            })
        res = sorted(res, key=lambda vote: vote['creation_date_time'])
        res.reverse()
        return flask.jsonify({
            'votes':  res
        })

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_set_nominee_visibility(biv_obj):
        data = flask.request.get_json()
        nominee_biv_id = data['biv_id']
        is_public = data['is_public']
        nominee = pem.E15Nominee.query.filter_by(
            biv_id=nominee_biv_id,
        ).first_or_404()
        nominee.is_public = is_public
        ppc.db.session.add(nominee)
        return '{}'

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_set_vote_status(biv_obj):
        data = flask.request.get_json()
        vote = pcm.Vote.query.filter_by(
            biv_id=data['biv_id'],
        ).one()
        vote.vote_status = data['vote_status']
        ppc.db.session.add(vote)
        return '{}'

    def action_contest_info(biv_obj):
        return flask.jsonify(biv_obj.contest_info())

    @common.decorator_login_required
    @decorator_user_is_event_voter
    def action_event_vote(biv_obj):
        data = flask.request.json
        if not biv_obj.is_event_voting():
            return '{}'
        vote = E15Contest._event_vote(biv_obj)
        if vote.nominee_biv_id:
            return '{}'
        nominee = E15Contest._lookup_nominee_by_biv_uri(biv_obj, data)
        vote.nominee_biv_id = nominee.biv_id
        ppc.db.session.add(vote)
        ppc.app().logger.warn('event vote: {}'.format({
            'user_id': flask.session.get('user.biv_id'),
            'nominee': nominee.biv_id,
            'user-agent': flask.request.headers.get('User-Agent'),
            'route': flask.request.access_route[0][:100],
        }))
        return '{}'

    def action_index(biv_obj):
        """Returns angular app home"""
        return _template.render_template(
            biv_obj,
            'index',
            version='20160629',
            base_template=None,
        )

    @common.decorator_login_required
    @common.decorator_user_is_judge
    def action_judge_ranking(biv_obj):
        data = flask.request.json
        nominees = biv_obj.public_nominees()
        ranks, comments = E15Contest._judge_ranks_and_comments_for_nominees(flask.session.get('user.biv_id'), nominees)

        for biv_id in ranks:
            ppc.db.session.delete(ranks[biv_id])

        for biv_id in comments:
            ppc.db.session.delete(comments[biv_id])

        for nominee in data['nominees']:
            if 'rank' in nominee and nominee['rank']:
                ppc.db.session.add(
                    pcm.JudgeRank(
                        judge_biv_id=flask.session['user.biv_id'],
                        nominee_biv_id=biv.URI(nominee['biv_id']).biv_id,
                        judge_rank=nominee['rank'])
                )
            if 'comment' in nominee and nominee['comment']:
                ppc.db.session.add(
                    pcm.JudgeComment(
                        judge_biv_id=flask.session['user.biv_id'],
                        nominee_biv_id=biv.URI(nominee['biv_id']).biv_id,
                        judge_comment=nominee['comment'])
                )
        return ''

    @common.decorator_login_required
    @common.decorator_user_is_judge
    def action_judging(biv_obj):
        nominees = biv_obj.public_nominees()
        random.Random(flask.session.get('user.display_name')).shuffle(nominees)
        ranks, comments = E15Contest._judge_ranks_and_comments_for_nominees(flask.session.get('user.biv_id'), nominees)

        res = []
        for nominee in nominees:
            if nominee.is_semi_finalist:
                biv_id = str(nominee.biv_id)
                res.append({
                    'biv_id': biv.Id(nominee.biv_id).to_biv_uri(),
                    'display_name': nominee.display_name,
                    'rank': ranks[biv_id].judge_rank if biv_id in ranks else None,
                    'comment': comments[biv_id].judge_comment if biv_id in comments else None,
                })
        return flask.jsonify({
            'judging': res,
        })

    def action_logout(biv_obj):
        oauth.logout()
        return E15Contest.action_user_state(biv_obj)

    def action_new_test_judge(biv_obj):
        """Creates a new test user and judge models and log in."""
        return pcm.Judge.new_test_judge(biv_obj)

    def action_nominee_form_metadata(biv_obj):
        form = pef.Nominate()
        res = []
        for field in form:
            res.append({
                'name': field.name,
                'type': field.type,
                'label': field.label.text,
                'helpText': form.help_text(field.name),
            })
        return flask.jsonify(form_metadata=res)

    def action_nominee_form_submit(biv_obj):
        #TODO(pjm): need decorator for this
        if not flask.session.get('user.is_logged_in'):
            werkzeug.exceptions.abort(403)
        return flask.jsonify(pef.Nominate().execute(biv_obj))

    def action_nominee_info(biv_obj):
        data = flask.request.json
        nominee = E15Contest._lookup_nominee_by_biv_uri(biv_obj, data)
        return flask.jsonify(nominee={
            'biv_id': biv.Id(nominee.biv_id).to_biv_uri(),
            'display_name': nominee.display_name,
            'url': nominee.url,
            'youtube_code': nominee.youtube_code,
            'nominee_desc': nominee.nominee_desc,
            'founders': E15Contest._founder_info_for_nominee(nominee),
        })

    @common.decorator_login_required
    def action_nominee_comments(biv_obj):
        # only nominee submitters will receive rows
        res = []
        for nominee in biv_obj.semi_finalist_nominees_for_user():
            for comment in pcm.JudgeComment.query.filter_by(
                nominee_biv_id=nominee.biv_id,
            ).all():
                res.append({
                    'display_name': nominee.display_name,
                    'judge_comment': comment.judge_comment,
                })
        return flask.jsonify({
            'comments': res,
        })

    @common.decorator_login_required
    def action_nominee_tweet(biv_obj):
        data = flask.request.json
        nominee = E15Contest._lookup_nominee_by_biv_uri(biv_obj, data)
        #TODO(pjm): move to form which does proper validation
        # and checkes if valid twitter handle format
        twitter_handle = pcm.Vote.strip_twitter_handle(data['twitter_handle'])
        vote = E15Contest._user_vote(biv_obj)
        if not vote:
            ppc.app().logger.warn('tweet with no vote: {}'.format(data))
            return '{}'
        if vote.twitter_handle and (twitter_handle != vote.twitter_handle):
            ppc.app().logger.warn('replacing twitter handle from {} to {}'.format(
                vote.twitter_handle, data))
        vote.twitter_handle = twitter_handle
        return '{}'

    @common.decorator_login_required
    def action_nominee_vote(biv_obj):
        data = flask.request.json
        nominee = E15Contest._lookup_nominee_by_biv_uri(biv_obj, data)
        if biv_obj.is_expired() or E15Contest._user_vote(biv_obj):
            return '{}'
        vote = pcm.Vote(
            user=flask.session.get('user.biv_id'),
            nominee_biv_id=nominee.biv_id,
            vote_status='1x',
        )
        ppc.db.session.add(vote)
        ppc.app().logger.warn('user vote: {}'.format({
            'user_id': flask.session.get('user.biv_id'),
            'nominee': nominee.biv_id,
            'user-agent': flask.request.headers.get('User-Agent'),
            'route': flask.request.access_route[0][:100],
        }))
        return '{}'

    def action_finalist_list(biv_obj):
        finalists = pem.E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == biv_obj.biv_id,
            pam.BivAccess.target_biv_id == pem.E15Nominee.biv_id,
            pem.E15Nominee.is_finalist == True,
        ).all()
        if flask.session.get('user.is_logged_in'):
            random.Random(flask.session.get('user.biv_id')).shuffle(finalists)
        elif flask.request.data:
            data = flask.request.json
            random.Random(data['random_value']).shuffle(finalists)
        else:
            random.shuffle(finalists)
        votes_by_nominee_id = {}

        if pam.Admin.is_admin():
            votes = pem.E15EventVoter.query.filter(
                pem.E15EventVoter.contest_biv_id == biv_obj.biv_id,
                pem.E15EventVoter.nominee_biv_id != None,
            ).all()
            for vote in votes:
                if vote.nominee_biv_id not in votes_by_nominee_id:
                    votes_by_nominee_id[vote.nominee_biv_id] = 0
                votes_by_nominee_id[vote.nominee_biv_id] += 1
        res = []
        for nominee in finalists:
            res.append({
                'biv_id': biv.Id(nominee.biv_id).to_biv_uri(),
                'display_name': nominee.display_name,
                'vote_count': votes_by_nominee_id[nominee.biv_id] if nominee.biv_id in votes_by_nominee_id else 0,
            })
        return flask.jsonify({
            'finalists': res,
        })

    def action_public_nominee_list(biv_obj):
        nominees = biv_obj.public_nominees()
        if flask.request.data:
            data = flask.request.json
            random.Random(data['random_value']).shuffle(nominees)
        else:
            random.shuffle(nominees)
        res = []
        for nominee in nominees:
            res.append({
                'biv_id': biv.Id(nominee.biv_id).to_biv_uri(),
                'display_name': nominee.display_name,
                'youtube_code': nominee.youtube_code,
                'nominee_summary': common.summary_text(nominee.nominee_desc),
                'is_finalist': nominee.is_finalist,
                'is_semi_finalist': nominee.is_semi_finalist,
                'is_winner': nominee.is_winner,
            })
        return flask.jsonify({
            'nominees': res,
        })

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def old_action_register_event_email(biv_obj):
        email = flask.request.json['email'].lower()
        if pem.E15EventVoter.query.filter_by(
                user_email=email,
        ).first():
            return '{}'
        ppc.db.session.add(pem.E15EventVoter(
            contest_biv_id=biv_obj.biv_id,
            user_email=email,
        ))
        ppc.app().logger.warn('event register: {}'.format({
            'email': email,
            'user-agent': flask.request.headers.get('User-Agent'),
            'route': flask.request.access_route[0][:100],
        }))
        return '{}'

    def old_action_register_voter(biv_obj):
        #TODO: problem
        #if flask.session.get('user.is_logged_in') and E15Contest.is_event_voter(biv_obj):
        #    return flask.redirect('/esprit-venture-challenge')
        email = flask.request.json['email'].lower()
        user = pam.User(
            display_name=email,
            user_email=email,
            oauth_type='test',
            oauth_id=werkzeug.security.gen_salt(64)
        )
        ppc.db.session.add(pem.E15EventVoter(
            contest_biv_id=biv_obj.biv_id,
            user_email=email,
        ))
        oauth.add_user_to_session(user)
        return '{}'

    def action_rules(biv_obj):
        return flask.redirect('/static/pdf/20160829-evc-rules.pdf')

    def action_sponsors(biv_obj):
        return flask.jsonify(sponsors=biv_obj.get_sponsors())

    def action_user_state(biv_obj):
        # Relies on session user (ie this person) to calculate these values so is secure
        # and will only work for "self"
        logged_in = True if flask.session.get('user.is_logged_in') else False
        vote = E15Contest._user_vote(biv_obj)
        event_vote = E15Contest._event_vote(biv_obj)
        return flask.jsonify({
            'isLoggedIn': logged_in,
            'isAdmin': pam.Admin.is_admin(),
            'isJudge': biv_obj.is_judge(),
            'isSemiFinalistSubmitter': biv_obj.is_semi_finalist_submitter(),
            'displayName': flask.session.get('user.display_name') if logged_in else '',
            'vote': biv.Id(vote.nominee_biv_id).to_biv_uri() if vote else None,
            'canVote': biv_obj.is_public_voting(),
            'isEventVoter': bool(event_vote),
            'eventVote': biv.Id(event_vote.nominee_biv_id).to_biv_uri() if event_vote and event_vote.nominee_biv_id else None,
        })

    def get_template():
        return _template

    def is_event_voter(contest):
        vote = E15Contest._event_vote(contest)
        return bool(vote)

    def _event_vote(contest):
        return flask.session.get('user.is_logged_in') and pem.E15EventVoter.query.select_from(pam.User).filter(
                pam.User.biv_id == flask.session.get('user.biv_id'),
                pem.E15EventVoter.user_email == pam.User.user_email,
                pem.E15EventVoter.contest_biv_id == contest.biv_id,
        ).first()

    def _founder_info_for_nominee(nominee):
        founders = pcm.Founder.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == nominee.biv_id,
            pam.BivAccess.target_biv_id == pcm.Founder.biv_id
        ).all()
        res = []
        for founder in founders:
            res.append({
                'biv_id': founder.biv_id,
                'display_name': founder.display_name,
                'founder_desc': founder.founder_desc,
            })
        return res

    def _lookup_nominee_by_biv_uri(contest, data):
        nominee_biv_id = biv.URI(data['nominee_biv_id']).biv_id
        # ensure the Nominee is related to this contest
        pam.BivAccess.query.filter_by(
            source_biv_id=contest.biv_id,
            target_biv_id=nominee_biv_id,
        ).first_or_404()
        return pem.E15Nominee.query.filter_by(
            biv_id=nominee_biv_id,
        ).first_or_404()

    def _nominee_submitter(nominee):
        return  pam.User.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == pam.User.biv_id,
            pam.BivAccess.target_biv_id == nominee.biv_id,
        ).first_or_404()

    def _judge_ranks_and_comments_for_nominees(user_id, nominees):
        nominee_ids = []
        for nominee in nominees:
            nominee_ids.append(nominee.biv_id)

        ranks = {}
        for rank in (pcm.JudgeRank.query.filter(
                pcm.JudgeRank.nominee_biv_id.in_(nominee_ids)
        ).filter_by(
                judge_biv_id=user_id,
        ).all()):
            ranks[str(rank.nominee_biv_id)] = rank

        comments = {}
        for comment in (pcm.JudgeComment.query.filter(
                pcm.JudgeComment.nominee_biv_id.in_(nominee_ids)
        ).filter_by(
                judge_biv_id=user_id,
        ).all()):
            comments[str(comment.nominee_biv_id)] = comment
        return (ranks, comments)

    def _user_vote(contest):
        """ Returns the user's vote or None """
        if not flask.session.get('user.is_logged_in'):
            return False
        nominee_ids = {}
        for nominee in contest.public_nominees():
            nominee_ids[nominee.biv_id] = True
        user_vote = None

        for vote in pcm.Vote.query.filter_by(
                user=flask.session.get('user.biv_id'),
        ).all():
            if vote.nominee_biv_id in nominee_ids:
                if user_vote:
                    raise Exception('user has multiple votes: {}'.format(flask.session.get('user.biv_id')))
                user_vote = vote
        return user_vote
