# -*- coding: utf-8 -*-
""" The singleton model which handles global tasks.

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import flask
import random

from .. import biv
from .. import common
from ..auth import model as pam
from ..controller import db

class Sponsor(db.Model, common.ModelWithDates):
    """sponsor database model.

    Fields:
        biv_id: primary ID
        display_name: sponsor name
        website: sponsor website
        sponsor_logo: logo image blob
        logo_type: image type (gif, png, jpeg)
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('sponsor_s', start=1008, increment=1000),
        primary_key=True
    )
    display_name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(100))
    sponsor_logo = db.Column(db.LargeBinary)
    logo_type = db.Column(db.Enum('gif', 'png', 'jpeg', name='logo_type'))

    def get_sponsors_for_biv_id(biv_id, randomize):
        sponsors = Sponsor.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == biv_id,
            pam.BivAccess.target_biv_id == Sponsor.biv_id
        ).all()
        if randomize:
            random.shuffle(sponsors)
        else:
            sponsors.sort(key=lambda x: x.biv_id)
        return sponsors


Sponsor.BIV_MARKER = biv.register_marker(8, Sponsor)
