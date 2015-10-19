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
            version='20151019-4',
        )

    def action_logout(biv_obj):
        oauth.logout()
        return E15Contest.action_user_state(biv_obj)

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
        nominee_biv_id = biv.URI(data['nominee_biv_id']).biv_id
        # ensure the Nominee is related to this contest
        pam.BivAccess.query.filter_by(
            source_biv_id=biv_obj.biv_id,
            target_biv_id=nominee_biv_id,
        ).first_or_404()
        nominee = pem.E15Nominee.query.filter_by(
            biv_id=nominee_biv_id,
        ).first_or_404()
        return flask.jsonify(nominee={
            'biv_id': nominee.biv_id,
            'display_name': nominee.display_name,
            'url': nominee.url,
            'youtube_code': nominee.youtube_code,
            'nominee_desc': nominee.nominee_desc,
            'founders': E15Contest._founder_info_for_nominee(nominee),
        })

    def action_public_nominee_list(biv_obj):
        data = json.loads(flask.request.data.decode('unicode-escape'))
        nominees = E15Contest._public_nominees(biv_obj)
        random.Random(data['random_value']).shuffle(nominees)
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
        return flask.jsonify(user_state={
            'is_logged_in': True if flask.session.get('user.is_logged_in') else False,
            'is_admin': pam.Admin.is_admin(),
            'is_judge': biv_obj.is_judge(),
            'random_value': random.random(),
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

    def _nominee_submitter(nominee):
        return  pam.User.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == pam.User.biv_id,
            pam.BivAccess.target_biv_id == nominee.biv_id,
        ).first_or_404()

    def _public_nominees(contest):
        return pem.E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == contest.biv_id,
            pam.BivAccess.target_biv_id == pem.E15Nominee.biv_id,
            pem.E15Nominee.is_public == True,
        ).all()
