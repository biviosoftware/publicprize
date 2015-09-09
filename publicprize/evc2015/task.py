# -*- coding: utf-8 -*-
""" controller actions for E15Contest and E15Nominee

    :copyright: Copyright (c) 2015 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
import json
import time
import werkzeug.exceptions

from . import form as pef
from . import model as pem
from .. import biv
from .. import common
from .. import controller as ppc
from ..auth import model as pam
from ..general import oauth

_template = common.Template('evc2015')


class E15Contest(ppc.Task):
    """Contest actions"""
    def action_index(biv_obj):
        """Returns angular app home"""
        return _template.render_template(
            biv_obj,
            'index',
            version='20150908-1',
        )

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

    def action_logout(biv_obj):
        oauth.logout()
        return E15Contest.action_user_state(biv_obj)

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
        ).first_or_404();
        return flask.jsonify(nominee={
            'display_name': nominee.display_name,
        })

    def action_nominee_form_submit(biv_obj):
        #TODO(pjm): need decorator for this
        if not flask.session.get('user.is_logged_in'):
            werkzeug.exceptions.abort(403)
        return flask.jsonify(pef.Nominate().execute(biv_obj))

    def action_sponsors(biv_obj):
        return flask.jsonify(sponsors=biv_obj.get_sponsors(randomize=False))

    def action_user_state(biv_obj):
        return flask.jsonify(user_state={
            'is_logged_in': True if flask.session.get('user.is_logged_in') else False,
            'is_admin': pam.Admin.is_admin(),
            'is_judge': biv_obj.is_judge(),
        })

    def get_template():
        return _template
