# -*- coding: utf-8 -*-
""" controller actions for E15Contest and E15Nominee

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import flask
import json
import pytz
import random
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


class E15Contest(ppc.Task):
    """Contest actions"""

    _SCORE_FOR_RANK = {
        '1': 10,
        '2': 5,
        '3': 2.5,
        '4': 1.25,
        '5': 0.625,
    }

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_judges(biv_obj):
        users = pcm.Judge.judge_users_for_contest(biv_obj)
        nominee_ids = {}
        for nominee in E15Contest._public_nominees(biv_obj):
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
                'url': nominee.url,
                'youtube_code': nominee.youtube_code,
                'nominee_desc': nominee.nominee_desc,
                'is_public': nominee.is_public,
                'founders': E15Contest._founder_info_for_nominee(nominee),
                'submitter_display_name': submitter.display_name,
                'submitter_email': submitter.user_email,
            })

        return flask.jsonify({
            'nominees': res,
        })

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_scores(biv_obj):
        res = []
        total_votes = 0
        total_rank_scores = 0
        for nominee in E15Contest._public_nominees(biv_obj):
            ranks = nominee.get_judge_ranks()
            votes = nominee.get_votes()
            vote_score = E15Contest._tally_votes(votes)
            total_votes += vote_score
            rank_score = E15Contest._tally_judge_ranks(ranks)
            total_rank_scores += rank_score
            res.append({
                'biv_id': nominee.biv_id,
                'display_name': nominee.display_name,
                'judge_ranks': '( {} )'.format(', '.join(map(str, ranks))),
                'votes': vote_score,
                'judge_score': rank_score,
            })
        for row in res:
            row['score'] = 40 * row['votes'] / total_votes + 60 * row['judge_score'] / total_rank_scores
        return flask.jsonify({
            'scores': sorted(res, key=lambda nominee: nominee['display_name'])
        })

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_review_votes(biv_obj):
        res = []
        nominee_id_to_name = {}
        for nominee in E15Contest._public_nominees(biv_obj):
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
        tz = pytz.timezone('US/Mountain')
        end_of_day = tz.localize(
            datetime.datetime(
                2015, 10, 14,
                23, 59, 59))
        seconds_remaining = (end_of_day - datetime.datetime.now(tz)).total_seconds()
        return flask.jsonify({
            'allowNominations': seconds_remaining > 0,
            'contestantCount': len(E15Contest._public_nominees(biv_obj)),
        })

    def action_index(biv_obj):
        """Returns angular app home"""
        return _template.render_template(
            biv_obj,
            'index',
            version='20151030',
        )

    @common.decorator_login_required
    @common.decorator_user_is_judge
    def action_judge_ranking(biv_obj):
        data = json.loads(flask.request.data.decode('unicode-escape'))
        nominees = E15Contest._public_nominees(biv_obj)
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
        nominees = E15Contest._public_nominees(biv_obj)
        random.Random(flask.session.get('user.display_name')).shuffle(nominees)
        ranks, comments = E15Contest._judge_ranks_and_comments_for_nominees(flask.session.get('user.biv_id'), nominees)

        res = []
        for nominee in nominees:
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
        data = json.loads(flask.request.data.decode('unicode-escape'))
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
    def action_nominee_tweet(biv_obj):
        data = json.loads(flask.request.data.decode('unicode-escape'))
        nominee = E15Contest._lookup_nominee_by_biv_uri(biv_obj, data)
        twitter_handle = data['twitter_handle']
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
        data = json.loads(flask.request.data.decode('unicode-escape'))
        nominee = E15Contest._lookup_nominee_by_biv_uri(biv_obj, data)
        if E15Contest._user_vote(biv_obj):
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

    def action_public_nominee_list(biv_obj):
        nominees = E15Contest._public_nominees(biv_obj)
        if flask.request.data:
            data = json.loads(flask.request.data.decode('unicode-escape'))
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
            })
        return flask.jsonify({
            'nominees': res,
        })

    def action_rules(biv_obj):
        return flask.redirect('/static/pdf/20150914-evc-rules.pdf')

    def action_sponsors(biv_obj):
        return flask.jsonify(sponsors=biv_obj.get_sponsors())

    def action_user_state(biv_obj):
        logged_in = True if flask.session.get('user.is_logged_in') else False
        vote = E15Contest._user_vote(biv_obj)
        return flask.jsonify(user_state={
            'user_vote': biv.Id(vote.nominee_biv_id).to_biv_uri() if vote else None,
            'is_logged_in': logged_in,
            'is_admin': pam.Admin.is_admin(),
            'is_judge': biv_obj.is_judge(),
            'display_name': flask.session.get('user.display_name') if logged_in else '',
        })

    def get_template():
        return _template

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

    def _public_nominees(contest):
        return pem.E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == contest.biv_id,
            pam.BivAccess.target_biv_id == pem.E15Nominee.biv_id,
            pem.E15Nominee.is_public == True,
        ).all()

    def _tally_judge_ranks(ranks):
        score = 0
        for rank in ranks:
            score += E15Contest._SCORE_FOR_RANK[str(rank)]
        return score

    def _tally_votes(votes):
        count = 0
        for vote in votes:
            if vote.vote_status == '1x':
                count += 1
            elif vote.vote_status == '2x':
                count += 2
        return count

    def _user_vote(contest):
        """ Returns the user's vote or None """
        if not flask.session.get('user.is_logged_in'):
            return False
        nominee_ids = {}
        for nominee in E15Contest._public_nominees(contest):
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
