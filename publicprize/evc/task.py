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
import re
import werkzeug
import werkzeug.exceptions

from ..debug import pp_t
from . import form as pef
from . import model as pem
from .. import biv
from .. import common
from .. import controller as ppc
from ..auth import model as pam
from ..general import oauth
from ..contest import model as pcm

_template = common.Template('evc')


class E15Contest(ppc.Task):
    """Contest actions"""

    @common.decorator_login_required
    @common.decorator_user_is_registrar
    def action_admin_event_votes(biv_obj):
        return flask.jsonify(biv_obj.admin_event_votes())

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
            submitter = nominee.submitter()
            pp_t('{}', [nominee])
            res.append({
                'biv_id': nominee.biv_id,
                'display_name': nominee.display_name,
                'founders': nominee.founders_as_list(),
                'is_public': nominee.is_public,
                'is_valid': nominee.is_valid,
                'nominee_desc': nominee.nominee_desc,
                'contact_phone': nominee.contact_phone,
                'contact_address': nominee.contact_address,
                'submitter_display_name': submitter.display_name,
                'submitter_email': submitter.user_email,
                'url': nominee.url,
                'youtube_code': nominee.youtube_code,
            })

        return flask.jsonify({
            'nominees': res,
        })

    @common.decorator_login_required
    @common.decorator_user_is_registrar
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
    def action_admin_send_invites(biv_obj):
        query = dict(contest_biv_id=biv_obj.biv_id)
        sent = 0
        force = 'force' in (flask.request.pp_request['path_info'] or '')
        for vae in pem.E15VoteAtEvent.query.filter_by(**query).all():
            sent += int(bool(vae.send_invite(force=force)))
            ppc.db.session.add(vae)
        return flask.jsonify({'sent': sent})

    @common.decorator_login_required
    @common.decorator_user_is_admin
    def action_admin_set_nominee_visibility(biv_obj):
        data = flask.request.get_json()
        nominee_biv_id = data['biv_id']
        is_public = data['is_public']
        nominee = pem.E15Nominee.query.filter_by(
            biv_id=nominee_biv_id,
        ).first_or_404()
        assert nominee.is_valid, \
            '{}: invalid nominee cannot make public'.format(nominee)
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

    def action_event_vote(biv_obj):
        resp = None
        if not biv_obj.is_event_voting():
            resp = 'Live voting is over' if biv_obj.is_expired() else 'Live voting has not yet started'
        else:
            data = flask.request.get_json()
            nominee = E15Contest._lookup_nominee_by_biv_uri(biv_obj, data)
            is_event_voter, vae = pem.E15VoteAtEvent.validate_session(biv_obj)
            if not is_event_voter:
                resp = 'You are not allowed to vote'
            elif vae.nominee_biv_id:
                resp = None
            else:
                vae.nominee_biv_id = nominee.biv_id
                vae.user_biv_id = flask.session.get('user.biv_id', None)
                vae.user_agent = flask.request.headers.get('User-Agent')[:100]
                vae.remote_addr = flask.request.remote_addr
        return flask.jsonify({'message': resp} if resp else {})

    def action_index(biv_obj):
        """Returns angular app home"""
        return _template.render_template(
            biv_obj,
            'index',
            version=ppc.app().config['PUBLICPRIZE']['APP_VERSION'],
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

    def action_new_test_registrar(biv_obj):
        """Creates a new test user and judge models and log in."""
        return pcm.Registrar.new_test_registrar(biv_obj)

    def action_nominee_form_metadata(biv_obj):
        return flask.jsonify(
            form_metadata=pef.Nominate().metadata_and_values(biv_obj),
        )

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
            'founders': nominee.founders_as_list(),
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
        finalists = biv_obj.get_finalists()
        if flask.session.get('user.is_logged_in'):
            random.Random(flask.session.get('user.biv_id')).shuffle(finalists)
        elif flask.request.data:
            data = flask.request.json
            random.Random(data['random_value']).shuffle(finalists)
        else:
            random.shuffle(finalists)
        res = []
        for nominee in finalists:
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

    @common.decorator_user_is_registrar
    def action_register_event_voter(biv_obj):
        import pyisemail
        eop, err = pem.validate_email_or_phone(flask.request.json['emailOrPhone'])
        if err:
            return flask.jsonify({'errors': err})
        vae, created = pem.E15VoteAtEvent.create_unless_exists(biv_obj, eop)
        resp = '{eop} registered successfully and invite sent.' if created \
            else 'Resent invite to {eop}.'
        resp += ' Link: {uri}'
        uri = vae.send_invite(force=True)
        if not uri:
            resp = '{eop} already registered. Have user check their spam'
        return flask.jsonify({
            'message': resp.format(eop=vae.invite_email_or_phone, uri=uri)
        })

    def action_rules(biv_obj):
        return flask.redirect('/static/pdf/20170830-evc-rules.pdf')

    def action_sponsors(biv_obj):
        return flask.jsonify(sponsors=biv_obj.get_sponsors())

    def action_user_state(biv_obj):
        # Relies on session user (ie this person) to calculate these values so is secure
        # and will only work for "self"
        logged_in = True if flask.session.get('user.is_logged_in') else False
        vote = E15Contest._user_vote(biv_obj)
        vote_biv_uri = biv.Id(vote.nominee_biv_id).to_biv_uri() if vote else None
        pp_t('vote {}', [vote_biv_uri])
        is_event_voter, vae = pem.E15VoteAtEvent.validate_session(biv_obj) \
            if biv_obj.is_event_voting() else (False, None)
        return flask.jsonify({
            'canVote': biv_obj.is_public_voting(),
            'displayName': flask.session.get('user.display_name') if logged_in else '',
            'eventVote': vae and vae.nominee_biv_id and biv.Id(vae.nominee_biv_id).to_biv_uri(),
            'isAdmin': pam.Admin.is_admin(),
            'isEventVoter': is_event_voter,
            'isJudge': biv_obj.is_judge(),
            'isLoggedIn': logged_in,
            'isRegistrar': biv_obj.is_registrar(),
            'isSemiFinalistSubmitter': biv_obj.is_semi_finalist_submitter(),
            'vote': vote_biv_uri,
        })

    def get_template():
        return _template

    def _lookup_nominee_by_biv_uri(contest, data):
        nominee_biv_id = biv.URI(data['nominee_biv_id']).biv_id
        # ensure the Nominee is related to this contest
        pam.BivAccess.query.filter_by(
            source_biv_id=contest.biv_id,
            target_biv_id=nominee_biv_id,
        ).first_or_404()
        res = pem.E15Nominee.query.filter_by(
            biv_id=nominee_biv_id,
        ).first_or_404()
        res.assert_is_public_or_404()
        return res

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


class E15Nominee(ppc.Task):
    def action_index(biv_obj):
        """Returns angular app home and sets session"""
        pp_t('obj={}', [biv_obj])
        c = biv_obj.contest()
        pp_t('contest={}', [c])
        return _template.render_template(
            biv_obj,
            'javascript-redirect',
            redirect_uri=c.format_uri(
                # angular route
                anchor=biv_obj.format_uri() + '/contestant',
            ),
            base_template=None,
        )


class E15VoteAtEvent(ppc.Task):
    def action_index(biv_obj):
        """Returns angular app home and sets session"""
        pp_t('obj={} contest={}', [biv_obj, biv_obj.contest_biv_id])
        c = biv.load_obj(biv_obj.contest_biv_id)
        biv_obj.save_to_session()
        pp_t('contest={}', [c])
        flask.session['vote_at_event.invite_nonce'] = biv_obj.invite_nonce
        pp_t('{}', c.format_uri(anchor='/event-voting'));
        return _template.render_template(
            biv_obj,
            'javascript-redirect',
            redirect_uri=c.format_uri(anchor='/event-voting'),
            base_template=None,
        )
