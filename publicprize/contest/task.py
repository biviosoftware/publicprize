# -*- coding: utf-8 -*-
""" The singleton model which handles global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""
from .. import biv
from .. import common
from .. import controller
from ..controller import db
from ..debug import pp_t
import flask
import io


class Founder(controller.Task):
    """Founder actions"""
    def action_founder_avatar(biv_obj):
        """Founder avatar image"""
        return _send_image_data(biv_obj, 'founder_avatar', 'avatar_type')


class Sponsor(controller.Task):
    """Sponsor actions"""
    def action_sponsor_logo(biv_obj):
        """Sponsor logo image"""
        return _send_image_data(biv_obj, 'sponsor_logo', 'logo_type')


class VoteAtEvent(controller.Task):
    def action_index(biv_obj):
        """Returns angular app home and sets session"""
        pp_t('obj={} contest={}', [biv_obj, biv_obj.contest_biv_id])
        c = biv.load_obj(biv_obj.contest_biv_id)
        biv_obj.save_to_session()
        pp_t('contest={}', [c])
        flask.session['vote_at_event.invite_nonce'] = biv_obj.invite_nonce
        return flask.redirect(c.format_uri(
            #action_uri='/',
            anchor='/event-vote',
        ))


def _send_image_data(biv_obj, data, data_type):
    # see SEND_FILE_MAX_AGE_DEFAULT config value
    return flask.send_file(
        io.BytesIO(getattr(biv_obj, data)),
        'image/{}'.format(getattr(biv_obj, data_type))
    )
